# How it was built

1. Read `agent.py`, `test_agent.py` and `Agent.ipynb` from the course folder; noted the hardcoded key and the single Gemini call. The key was not copied anywhere.
2. Replaced the Gemini client with `common/llm.py`: provider and model from env, offline deterministic fallback. Keys from env only, provider-agnostic.
3. Added the tool loop: `decide()` asks for JSON (`tool`, `store`, `days`) through `complete_json`; `forecast()` calls `POST :8104/forecast` with a 15 s timeout and falls back to `metrics.json`; `metrics()` reads the scores; the model is asked again with the result. Offline, `decide()` is a keyword parser so the loop still runs.
4. Kept the CLI loop as `client.py` (port 8105, one-shot mode added, shows which tool ran).
5. Built the chat page on `common/ui.css`: provider badge (`.on` only with a key), message list, three one-click examples, ids `#input`, `#run`, `#result`.
6. Wrote the tests with the backend mocked and `LLM_PROVIDER=offline` forced; `just test` runs ruff then pytest.

## Tech stack
| Layer | Choice | Why |
|---|---|---|
| Language and runtime | Python 3.11 via uv | matches every other service in the repo |
| Model or core logic | `common/llm.py` (`complete`, `complete_json`) + a two-step tool loop in `agent.py` | one door for keys and providers; the loop is plain functions, easy to test |
| Interface | FastAPI `POST /ask`, `GET /health`, HTML chat page on `/`, `client.py` CLI | same shape as the original, plus a page an interviewer can click |
| Data | `capstone3-sales-forecast` on :8104 (`/forecast`) and its `models/metrics.json` | the tool has something real to call and a file to fall back on |
| Tests | pytest + TestClient, 9 tests, all offline | the backend is mocked, the metrics file is a temp file |

## Libraries
`fastapi` (routes and validation), `uvicorn` (server), `jinja2` (chat page), `requests` (tool call to :8104 and the CLI client), `anthropic` / `openai` / `google-genai` (provider SDKs, imported lazily by `common/llm.py` only when that provider is chosen), `pytest` + `httpx` (tests), `ruff` (lint).
