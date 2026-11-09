# agent-api: POST /ask + chat page on port 8105, keys from env only (common/llm.py)
set shell := ["bash", "-cu"]
port := "8105"

setup:
    uv sync
    mkdir -p static
    cp common/ui.css static/ui.css

run:
    uv run uvicorn app:app --host 127.0.0.1 --port {{port}}

up:
    @if [ -f .pid ] && kill -0 $(cat .pid) 2>/dev/null; then echo "already up (pid $(cat .pid)) on {{port}}"; exit 0; fi
    nohup uv run uvicorn app:app --host 127.0.0.1 --port {{port}} > .server.log 2>&1 & echo $! > .pid
    for i in $(seq 1 40); do curl -sf http://127.0.0.1:{{port}}/health >/dev/null && break; sleep 0.5; done
    echo "up on http://127.0.0.1:{{port}} (pid $(cat .pid))"

down:
    @if [ -f .pid ]; then kill $(cat .pid) 2>/dev/null || true; rm -f .pid; echo "down"; else echo "not running"; fi

test:
    uv run ruff check .
    uv run pytest -q

# scripted end-to-end: health, a plain question, a question that triggers the forecast tool (just up first)
demo:
    curl -s http://127.0.0.1:{{port}}/health; echo
    uv run python client.py "Explain in one sentence why Friday sales matter for staffing"
    uv run python client.py "Forecast sales for Bob's Diner for the next 14 days"
    uv run python client.py "Which model won and what were the scores?"
