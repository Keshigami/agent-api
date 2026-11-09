<!-- public-top -->
# Agent API

A FastAPI chat agent on one provider-agnostic LLM door that can call the sales-forecast service as a tool, with no key in source. Caltech CTME PGC AIML, capstone.

**Watch it first:** [the 90-second film](demo/film.mp4) (what it does, how it is built, the proof, the answer) or the [60-second cut](demo/film-60s.mp4). The plain walkthrough with captions is [demo/demo.mp4](demo/demo.mp4).

## Try it in three commands

```bash
git clone https://github.com/Keshigami/agent-api.git && cd agent-api
just setup        # creates the venv with uv (Python 3.11)
just up           # http://127.0.0.1:8105/  (just down to stop)
```

You need [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just) (`brew install uv just` on a Mac). Everything the app needs is in the repo (synthetic sample data where a dataset is used). No API key is required: without one the app runs in a deterministic offline mode and says so on screen. Set `ANTHROPIC_API_KEY` (or `LLM_PROVIDER=openai` with `OPENAI_API_KEY`, or `gemini` with `GOOGLE_API_KEY`) in your shell for real model answers. `just test` runs the lint and the offline tests.

Step by step: [docs/Getting-Started.md](docs/Getting-Started.md), then [how it was built](docs/How-It-Was-Built.md), [results](docs/Results.md), [limits](docs/Limits-and-Next-Steps.md) and [the film](docs/The-Film.md). The same pages are on the [wiki](https://github.com/Keshigami/agent-api/wiki).
<!-- /public-top -->
## Demo walkthrough
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

A FastAPI agent: `POST /ask` sends text through the shared LLM door (`common/llm.py`) and can call one real tool,
the sales forecast service from `capstone3-sales-forecast`, before answering. A chat page sits on `/`.

## What changed from the original

The course version (`agent.py` + `test_agent.py`) was a Gemini proxy: one route, a hardcoded Google API key as the
fallback, `gemini-1.5-flash` baked in, a `requests` loop as the client.

| Original | Here |
|---|---|
| API key in source as a fallback | Keys come from the environment only, and only `common/llm.py` reads them. Nothing in this folder touches a key. |
| Gemini only | Provider-agnostic: `LLM_PROVIDER=anthropic | openai | gemini | offline`, or the first key found, else offline. |
| No fallback without a key | Offline mode is deterministic, so tests and demos run with no network. |
| Proxy: text in, text out | An agent: the model picks a tool as JSON (`complete_json`), the tool runs, the model is asked again with the result. |
| `{"response"}` | `{"response", "provider", "model", "tool_calls"}` so the UI can show what ran. |
| `test_agent.py` CLI on :8000 | `client.py`, same loop, on :8105, plus one-shot `python client.py "question"`. |
| no UI, no health | Chat page with provider badge and three one-click examples; `GET /health`. |

### The tool loop (`agent.py`)

1. `decide(text)` asks the model for `{"tool": "none|forecast|metrics", "store": ..., "days": ...}` via `complete_json`.
   Offline, a keyword parser does the same job deterministically (`offline_decide`).
2. `forecast(store, days)` POSTs to `http://127.0.0.1:8104/forecast`. If that service is down it answers from
   `capstone3-sales-forecast/models/metrics.json` (a flat line at the last 28-day mean, clearly labelled as the fallback).
   `metrics()` reads the trained models and their holdout scores from the same file.
3. The model is asked again with the tool result and writes the reply. Offline, the reply is the one-line summary of the result.

Every answer carries `tool_calls` with the tool name, arguments, and the result source (`live model on :8104` or
`metrics.json fallback`).

## Run

```bash
just setup          # uv sync, copy common/ui.css
just run            # foreground on 8105   (or: just up / just down for background with a pid file)
just test           # ruff + pytest, offline
just demo           # health + three questions through client.py (needs just up)
uv run python client.py                      # interactive loop
uv run python client.py "forecast Surfs Up next week"
```

Switch providers by environment, never by editing code:

```bash
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... just run    # or OPENAI_API_KEY / GOOGLE_API_KEY
LLM_MODEL=claude-haiku-5-5 just run                       # optional model override
FORECAST_URL=http://127.0.0.1:8104/forecast               # where the forecast tool points (default)
```

With no key the badge says `offline`, `/health` reports `model_loaded: false`, and every answer starts with
`[offline <hash>]`.

## Tests (`tests/test_agent.py`, 9, all offline)

- `/health` returns `{"ok": true, "service": "agent-api", "model_loaded": false, "provider": "offline"}` with no key.
- `/ask` returns a response with provider `offline` and no tool call for a plain question; empty text is a 422.
- The tool loop: a forecast question calls the (mocked) backend exactly once with `("Bob's Diner", 5)` and the reply quotes the total.
- Backend down: the tool falls back to a temp `metrics.json` and says so in the result source and the reply.
- The metrics tool reads a temp `metrics.json` and names the winner and its RMSE.
- The offline router is deterministic for three phrasings.
- The chat page has the provider badge (not `.on` without a key), the three examples, and ids `#input`, `#run`, `#result`.
- `client.py` one-shot prints the response.

## Two-minute walkthrough

1. `just up` here and in `../capstone3-sales-forecast`, open http://127.0.0.1:8105/. The badge shows the provider.
2. Click "Forecast sales for Bob's Diner for the next 14 days": the reply quotes about 6,400 units and the amber line under
   it shows `tool forecast({"store":"Bob's Diner","days":14}) → live model on :8104`.
3. Click "Which model won and what were the scores?": the `metrics` tool reads the trained scores (XGBoost, RMSE 59.9 in quick mode).
4. Stop the forecast service (`just down` there) and ask the forecast question again: the source changes to `metrics.json fallback`.
5. `export ANTHROPIC_API_KEY=...` and restart: same page, the badge turns on, the replies are written by the model.

## Limits

- One tool round per question; the planner is a single JSON call, not a multi-step agent.
- Offline answers are deterministic summaries, not language; they prove the loop, not the prose.
- The fallback forecast is a flat mean, not a model. It exists so the agent still answers when :8104 is down.
- No conversation memory: each `/ask` is independent.

## Standalone repo

Exported from Max's `caltech-capstone` workspace. `common/` is vendored (LLM door, UI tokens). Run: `just setup && just test && just up`.
LLM-backed features read `ANTHROPIC_API_KEY` (or `LLM_PROVIDER` + `OPENAI_API_KEY` / `GOOGLE_API_KEY`); with no key they run in a deterministic offline mode.
Film: `demo/film.mp4` (90 s, what it does, how it is built, the proof, the answer) and `demo/film-60s.mp4` (60 s cut); `demo/demo.mp4` is the plain walkthrough.
