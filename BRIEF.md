---
title: Agent API
group: capstone
role: Applied AI
port: 8105
status: working
one_liner: A FastAPI chat agent on one provider-agnostic LLM door that can call the sales-forecast service as a tool, with no key in source.
---
# Agent API

## Demo
<!-- demo:auto -->
![demo](demo/demo.gif)

Full walkthrough with captions: [demo/demo.mp4](demo/demo.mp4) (71 s, 1280x800, animated intro and end card). Run it yourself: `just setup && just up`, then open http://localhost:8105/.

Two-minute walkthrough:
1. The capstone agent on common/llm.py: three example questions
2. Forecast question: the agent calls the forecast tool on the sales service
3. The tool call is visible in the reply: forecast(store, days) and where the numbers came from
4. Which model won: answered from the saved metrics
5. A plain reasoning question: no tool, just the model
6. The badge says which provider answered; with no key it is the offline mode
7. How it works
<!-- /demo:auto -->

## Brief
The course exercise was a thin FastAPI wrapper that forwarded text to Gemini, with an API key hardcoded as a fallback.
This version keeps the `POST /ask` contract and the CLI loop, but reads keys from the environment only, runs on
Anthropic, OpenAI or Gemini without code changes, works offline for tests and demos, and does one thing a proxy cannot:
it decides when to call the restaurant sales forecast service and answers from the result.

## Tech stack
| Layer | Choice | Why |
|---|---|---|
| Language and runtime | Python 3.11 via uv | matches every other service in the repo |
| Model or core logic | `common/llm.py` (`complete`, `complete_json`) + a two-step tool loop in `agent.py` | one door for keys and providers; the loop is plain functions, easy to test |
| Interface | FastAPI `POST /ask`, `GET /health`, HTML chat page on `/`, `client.py` CLI | same shape as the original, plus a page an interviewer can click |
| Data | `capstone3-sales-forecast` on :8104 (`/forecast`) and its `models/metrics.json` | the tool has something real to call and a file to fall back on |
| Tests | pytest + TestClient, 9 tests, all offline | the backend is mocked, the metrics file is a temp file |

## Libraries used
`fastapi` (routes and validation), `uvicorn` (server), `jinja2` (chat page), `requests` (tool call to :8104 and the CLI client), `anthropic` / `openai` / `google-genai` (provider SDKs, imported lazily by `common/llm.py` only when that provider is chosen), `pytest` + `httpx` (tests), `ruff` (lint).

## How it was built
1. Read `agent.py`, `test_agent.py` and `Agent.ipynb` from the course folder; noted the hardcoded key and the single Gemini call. The key was not copied anywhere.
2. Replaced the Gemini client with `common/llm.py`: provider and model from env, offline deterministic fallback. Keys from env only, provider-agnostic.
3. Added the tool loop: `decide()` asks for JSON (`tool`, `store`, `days`) through `complete_json`; `forecast()` calls `POST :8104/forecast` with a 15 s timeout and falls back to `metrics.json`; `metrics()` reads the scores; the model is asked again with the result. Offline, `decide()` is a keyword parser so the loop still runs.
4. Kept the CLI loop as `client.py` (port 8105, one-shot mode added, shows which tool ran).
5. Built the chat page on `common/ui.css`: provider badge (`.on` only with a key), message list, three one-click examples, ids `#input`, `#run`, `#result`.
6. Wrote the tests with the backend mocked and `LLM_PROVIDER=offline` forced; `just test` runs ruff then pytest.

## Results
No model is trained here; the tests are the result.

| Test | Proves |
|---|---|
| health | `{"ok": true, "service": "agent-api", "model_loaded": false}` with no key |
| ask offline | a response comes back with provider `offline`, no tool call for a plain question |
| tool loop, mocked backend | the forecast tool is called exactly once with `("Bob's Diner", 5)`; the reply quotes the total (500) |
| backend down | the tool falls back to `metrics.json` and the reply says so |
| metrics tool | the winner and its RMSE are read from the file |
| chat page | badge, examples and stable ids are present |

Live (both services up, offline provider): "Forecast sales for Bob's Diner for the next 14 days" returns about 6,366 units from the XGBoost model on :8104 in under a second.

## Demo details
- Run: `just setup && just up` (and the same in `../capstone3-sales-forecast`), open `http://localhost:8105/`.
- Two-minute walkthrough: click the first example (forecast tool, live source shown under the reply); click the second (metrics tool); type anything else (plain answer); stop :8104 and repeat the first (fallback source).
- Video clip: `demo/clips/agent-api.webm` (recorded by `just demo-video`).
- Sample inputs: the three example buttons on the page; `just demo` runs the same three through `client.py`.

## Limits and next steps
- One tool round per question and no conversation memory; a production agent would keep history and allow several rounds.
- Offline replies are summaries, not prose; they exist so the loop is testable without a key.
- The fallback forecast is a flat 28-day mean, labelled as such; it is a safety net, not a model.
- Next: stream replies, add a `history(store)` tool against the EDA tables, and record provider latency in the response.
