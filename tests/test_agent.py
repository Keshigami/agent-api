"""Offline tests: no key, provider 'offline', the tool loop with a mocked forecast backend."""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import agent
from app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "offline")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    b = r.json()
    assert b["ok"] is True and b["service"] == "agent-api" and b["model_loaded"] is False and b["provider"] == "offline"


def test_ask_returns_response_and_offline_provider():
    r = client.post("/ask", json={"text": "Explain in one sentence why Friday sales matter for staffing"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["response"] and b["provider"] == "offline" and b["model"] == "offline" and b["tool_calls"] == []


def test_ask_rejects_empty():
    assert client.post("/ask", json={"text": ""}).status_code == 422


def test_tool_loop_calls_forecast_with_mocked_backend(monkeypatch):
    calls = []

    def fake_backend(store, days):
        calls.append((store, days))
        return {"model": "xgboost", "store": "Bob's Diner", "values": [100.0] * days, "total": 100.0 * days, "mean_per_day": 100.0, "unit": "units"}

    monkeypatch.setattr(agent, "call_forecast_backend", fake_backend)
    r = client.post("/ask", json={"text": "Forecast sales for Bob's Diner for the next 5 days"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert calls == [("Bob's Diner", 5)]
    assert b["tool_calls"][0]["name"] == "forecast" and b["tool_calls"][0]["args"] == {"store": "Bob's Diner", "days": 5}
    assert b["tool_calls"][0]["result"]["source"].startswith("live")
    assert "500" in b["response"] and "Bob's Diner" in b["response"]


def test_forecast_falls_back_to_metrics_when_backend_down(monkeypatch, tmp_path):
    def down(store, days):
        raise ConnectionError("refused")

    m = {"best_tabular": "xgboost", "mode": "quick", "models": {"xgboost": {"daily_total": {"rmse": 60.0, "mae": 45.0, "mape": 0.1}}},
         "baseline": {"last_28_days_mean_units_per_day": {"all": 470.0, "1": 460.0, "4": 0.9}}}
    p = tmp_path / "metrics.json"
    p.write_text(json.dumps(m))
    monkeypatch.setattr(agent, "call_forecast_backend", down)
    monkeypatch.setattr(agent, "METRICS_PATH", p)
    out = agent.run("predict Fou Cher sales for the next 3 days")
    call = out["tool_calls"][0]
    assert call["args"] == {"store": "Fou Cher", "days": 3}
    assert call["result"]["source"].startswith("metrics.json fallback") and call["result"]["values"] == [0.9, 0.9, 0.9]
    assert "metrics.json" in out["response"]


def test_metrics_tool(monkeypatch, tmp_path):
    p = tmp_path / "metrics.json"
    p.write_text(json.dumps({"best_tabular": "random_forest", "mode": "quick",
                             "models": {"random_forest": {"daily_total": {"rmse": 59.9, "mae": 47.5, "mape": 0.08}},
                                        "lstm": {"recursive_184_days": {"rmse": 1000.0, "mae": 800.0, "mape": 0.2}}}}))
    monkeypatch.setattr(agent, "METRICS_PATH", p)
    out = agent.run("Which model won and what were the scores?")
    assert out["tool_calls"][0]["name"] == "metrics"
    assert "random_forest" in out["response"] and "59.9" in out["response"]


def test_offline_router_is_deterministic():
    assert agent.offline_decide("hello there") == {"tool": "none", "args": {}}
    assert agent.offline_decide("forecast next month for Surfs Up") == {"tool": "forecast", "args": {"store": "Surfs Up", "days": 30}}
    assert agent.offline_decide("forecast all stores next week")["args"] == {"store": "all", "days": 7}


def test_chat_page_has_badge_examples_and_ids():
    r = client.get("/")
    assert r.status_code == 200
    h = r.text
    assert 'id="provider"' in h and "offline" in h and 'class="badge "' in h  # badge without .on when no key
    assert 'id="input"' in h and 'id="run"' in h and 'id="result"' in h
    assert h.count('onclick="useExample') == 3 and "Forecast sales for Bob's Diner" in h


def test_client_one_shot(monkeypatch, capsys):
    import client as cli

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": "hi", "provider": "offline", "model": "offline", "tool_calls": []}

    monkeypatch.setattr(cli.requests, "post", lambda *a, **k: R())
    monkeypatch.setattr(sys, "argv", ["client.py", "hello"])
    cli.main()
    assert capsys.readouterr().out.strip() == "hi"
