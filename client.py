#!/usr/bin/env python3
"""CLI client, same loop as the original test_agent.py but pointed at :8105 and showing which tool ran."""
import os
import sys

import requests

URL = os.getenv("AGENT_URL", "http://localhost:8105/ask")


def ask_agent(question: str) -> dict:
    """Send a question to the agent and return its JSON (response, provider, model, tool_calls)."""
    try:
        r = requests.post(URL, json={"text": question}, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        return {"response": f"Error: {e}", "provider": "?", "model": "?", "tool_calls": []}


def main():
    if len(sys.argv) > 1:  # one-shot: python client.py "question"
        d = ask_agent(" ".join(sys.argv[1:]))
        print(d["response"])
        return
    print("Agent client (type quit to exit)\n")
    while True:
        try:
            q = input("Ask me anything: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue
        d = ask_agent(q)
        tools = ", ".join(c["name"] for c in d.get("tool_calls", [])) or "none"
        print("-" * 50)
        print(d["response"])
        print(f"-- {d.get('provider')} / {d.get('model')} · tools: {tools}")
        print()


if __name__ == "__main__":
    main()
