"""agent-api: POST /ask through common/llm.py with a forecast tool, plus a chat page, on port 8105."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import agent
from common import llm

PORT = 8105
SERVICE = "agent-api"
app = FastAPI(title="Agent API", version="2.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")

EXAMPLES = [
    "Forecast sales for Bob's Diner for the next 14 days",
    "Which model won and what were the scores?",
    "Explain in one sentence why Friday sales matter for staffing",
]


class Query(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


@app.get("/health")
def health():
    p = llm.provider()
    return {"ok": True, "service": SERVICE, "model_loaded": p != "offline", "provider": p, "model": llm.model(), "port": PORT}


@app.post("/ask")
def ask(q: Query):
    try:
        return agent.run(q.text)
    except Exception as e:  # noqa: BLE001 - any provider SDK error (bad key, network) becomes a readable 502
        raise HTTPException(502, f"{type(e).__name__}: {e}")


@app.get("/")
def index(request: Request):
    p = llm.provider()
    return templates.TemplateResponse(request, "chat.html", {"port": PORT, "provider": p, "model": llm.model(),
                                                             "online": p != "offline", "examples": EXAMPLES})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=PORT)
