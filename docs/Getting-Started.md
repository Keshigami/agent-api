# Getting started

## What you need
- [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just). On a Mac: `brew install uv just`.
- Python 3.11 is installed by uv.
- No API key is required: without one the app runs in a deterministic offline mode and says so on screen. Set `ANTHROPIC_API_KEY` (or `LLM_PROVIDER=openai` with `OPENAI_API_KEY`, or `gemini` with `GOOGLE_API_KEY`) in your shell for real model answers.

## Three commands
```bash
git clone https://github.com/Keshigami/agent-api.git && cd agent-api
just setup
just up           # http://127.0.0.1:8105/  (just down to stop)
```
Everything the app needs is in the repo (synthetic sample data where a dataset is used).

## Commands
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

## What you see
1. `just up` here and in `../capstone3-sales-forecast`, open http://127.0.0.1:8105/. The badge shows the provider.
2. Click "Forecast sales for Bob's Diner for the next 14 days": the reply quotes about 6,400 units and the amber line under
   it shows `tool forecast({"store":"Bob's Diner","days":14}) → live model on :8104`.
3. Click "Which model won and what were the scores?": the `metrics` tool reads the trained scores (XGBoost, RMSE 59.9 in quick mode).
4. Stop the forecast service (`just down` there) and ask the forecast question again: the source changes to `metrics.json fallback`.
5. `export ANTHROPIC_API_KEY=...` and restart: same page, the badge turns on, the replies are written by the model.

## Try this
Try it: ask which model won.
