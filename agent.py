"""The agent: a small tool loop on top of common/llm.py.

    plan  = decide(text)                      -> {"tool": "forecast"|"metrics"|"none", "args": {...}}   (complete_json)
    result = TOOLS[tool](**args)              -> forecast() calls capstone3 on :8104, else answers from its metrics.json
    answer = complete(ANSWER_SYSTEM, result)  -> the model writes the reply from the tool result

Offline (no key): decide() is a deterministic keyword parser and complete() echoes the tool summary, so the loop runs
end to end with no network. Keys are read only by common/llm.py from the environment; nothing here sees them.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(REPO))
from common import llm

FORECAST_URL = os.getenv("FORECAST_URL", "http://127.0.0.1:8104/forecast")
CAPSTONE3 = REPO / "capstone3-sales-forecast" / "models"
METRICS_PATH = Path(os.getenv("METRICS_PATH", CAPSTONE3 / "metrics.json"))
STORES = {1: "Bob's Diner", 2: "Beachfront Bar", 3: "Sweet Shack", 4: "Fou Cher", 5: "Corner Cafe", 6: "Surfs Up"}

PLANNER_SYSTEM = (
    "You route questions for a restaurant sales assistant. Tools: forecast(store, days) predicts units sold per day "
    "for one of these stores or 'all': " + ", ".join(f"{k}={v}" for k, v in STORES.items()) + ". "
    "metrics() returns the trained models and their holdout scores. Pick 'none' for anything else. "
    "days is an integer 1..365 (default 7). store is a name from the list or 'all'."
)
ANSWER_SYSTEM = ("You are a concise analyst. Answer the question from the tool result below in two or three sentences, "
                 "quoting the numbers. Say where the numbers came from (live model or metrics file).")
CHAT_SYSTEM = "You are a helpful, concise assistant for a restaurant sales analytics team. Answer in plain words."


# ---------- tools ----------
def load_metrics() -> dict | None:
    try:
        return json.loads(METRICS_PATH.read_text())
    except (OSError, ValueError):
        return None


def call_forecast_backend(store: str, days: int) -> dict:
    """POST to capstone3's /forecast. Separated so tests can mock it."""
    r = requests.post(FORECAST_URL, json={"store": store, "days": days}, timeout=15)
    r.raise_for_status()
    return r.json()


def forecast(store: str = "all", days: int = 7) -> dict:
    days = max(1, min(int(days or 7), 365))
    store = str(store or "all")
    try:
        r = call_forecast_backend(store, days)
        return {"source": "live model on :8104", "model": r.get("model"), "store": r.get("store"), "days": days,
                "values": r.get("values"), "total": r.get("total"), "mean_per_day": r.get("mean_per_day"), "unit": r.get("unit", "units")}
    except (OSError, ValueError, KeyError) as e:  # requests errors are OSErrors; backend down or refused: fall back to the metrics file
        m = load_metrics()
        if not m:
            return {"source": "none", "store": store, "days": days, "error": f"forecast service unavailable ({type(e).__name__}) and no metrics.json"}
        base = m["baseline"]["last_28_days_mean_units_per_day"]
        sid = _store_id(store)
        mean = base.get(str(sid) if sid else "all", base["all"])
        name = STORES.get(sid, "all stores") if sid else "all stores"
        return {"source": "metrics.json fallback (forecast service down): flat line at the last 28-day mean", "model": "baseline mean",
                "store": name, "days": days, "values": [round(mean, 1)] * days, "total": round(mean * days, 1), "mean_per_day": mean,
                "unit": "units", "best_model_available": m["best_tabular"]}


def metrics() -> dict:
    m = load_metrics()
    if not m:
        return {"source": "none", "error": f"no metrics file at {METRICS_PATH}"}
    out = {"source": str(METRICS_PATH.name), "mode": m["mode"], "best_tabular": m["best_tabular"], "models": {}}
    for k, v in m["models"].items():
        s = v.get("daily_total") or v.get("recursive_184_days") or {}
        out["models"][k] = {kk: s.get(kk) for kk in ("rmse", "mae", "mape")}
    return out


TOOLS = {"forecast": forecast, "metrics": metrics}


# ---------- planning ----------
def _store_id(text: str) -> int | None:
    t = str(text).lower()
    if t.strip().isdigit() and int(t) in STORES:
        return int(t)
    for k, v in STORES.items():
        key = v.lower().replace("'", "")
        if key in t.replace("'", "") or key.split()[0] in t:
            return k
    return None


def offline_decide(text: str) -> dict:
    """Deterministic routing with no model: keywords pick the tool, regexes pull the arguments."""
    t = text.lower()
    if re.search(r"\b(forecast|predict|projection|next \d+ days|next week|next month|how many .* sell|sales for)\b", t):
        m = re.search(r"(\d+)\s*(?:-?\s*day|days)", t)
        days = int(m.group(1)) if m else 30 if "month" in t else 7
        sid = _store_id(t)
        return {"tool": "forecast", "args": {"store": STORES[sid] if sid else "all", "days": days}}
    if re.search(r"\b(model|models|score|scores|rmse|mape|mae|metrics|accuracy|which .* won|best)\b", t):
        return {"tool": "metrics", "args": {}}
    return {"tool": "none", "args": {}}


def decide(text: str) -> dict:
    if llm.provider() == "offline":
        return offline_decide(text)
    raw = llm.complete_json(PLANNER_SYSTEM, text, schema_hint={"tool": "none|forecast|metrics", "store": "all", "days": 7})
    tool = str(raw.get("tool", "none")).lower()
    if tool not in TOOLS:
        return {"tool": "none", "args": {}}
    if tool == "forecast":
        sid = _store_id(str(raw.get("store", "all")))
        try:
            days = int(raw.get("days") or 7)
        except (TypeError, ValueError):
            days = 7
        return {"tool": "forecast", "args": {"store": STORES[sid] if sid else "all", "days": days}}
    return {"tool": "metrics", "args": {}}


# ---------- the loop ----------
def summarise(tool: str, r: dict) -> str:
    """One plain line from a tool result; it is the offline answer and the first line of the online prompt."""
    if r.get("error"):
        return f"Could not run {tool}: {r['error']}"
    if tool == "forecast":
        return (f"{r['store']}: about {r['total']:,.0f} {r['unit']} over the next {r['days']} days "
                f"({r['mean_per_day']:,.1f} a day) from the {r['model']} model; source: {r['source']}.")
    rows = ", ".join(f"{k} RMSE {v['rmse']:.1f}" for k, v in r["models"].items() if v.get("rmse") is not None)
    return f"Best tabular model: {r['best_tabular']} ({r['mode']} mode). Holdout scores: {rows}; source: {r['source']}."


def run(text: str) -> dict:
    text = (text or "").strip()
    plan = decide(text)
    calls = []
    if plan["tool"] in TOOLS:
        result = TOOLS[plan["tool"]](**plan["args"])
        calls.append({"name": plan["tool"], "args": plan["args"], "result": result})
        summary = summarise(plan["tool"], result)
        answer = llm.complete(ANSWER_SYSTEM, f"{summary}\n\nQuestion: {text}\nTool result: {json.dumps(result)}")
    else:
        answer = llm.complete(CHAT_SYSTEM, text)
    return {"response": answer, "provider": llm.provider(), "model": llm.model(), "tool_calls": calls}
