# Agent API · carousel

Spec: film/specs/agent-api.json · 8 slides, 1080x1350.

## 1/8 Hook

- The agent asked the forecast service itself.

## 2/8 The question

- The course version shipped a key in source.
- Can an agent run with no key at all?
- course version 1 key in source → here 0 keys · 3 providers

## 3/8 What it does

- Agent API
- Capstone · Applied AI
- One LLM door, one real tool, no key in source
- max@baluyot ~ $ curl -s localhost:8105/ask -H 'content-type: application/json' -d "{\"text\":\"Forecast sales for Bob's Diner for the next 14 days\"}"

## 4/8 How it is built

- 1. Two tools — requests
- 2. common/llm.py — anthropic · openai · google-genai
- 3. decide → tool → answer — complete_json · complete
- 4. POST /ask — FastAPI
- 5. Chat page — HTML + ui.css
- Service down? Fall back, and say so.

## 5/8 The result

- Course version → here
- Provider · Gemini only · Anthropic · OpenAI · Gemini · offline (highlighted)
- Shape · proxy: text in, text out · agent: pick a tool, run it, answer
- Reply · {response} · {response, provider, model, tool_calls}
- Tests · a CLI loop called test_agent.py · 9 offline tests, backend mocked

## 6/8 The proof

- Forecast question: the tool call, shown
- screen: agent-api/demo/poster.png

## 7/8 The answer and the limit

- 0
- API keys in source · three providers behind one door
- One tool round, no memory. Replies are summaries.
- And it ships.

## 8/8 Try it

- Try it: ask which model won.
- max@baluyot ~ $ git clone https://github.com/Keshigami/agent-api.git
- max@baluyot ~ $ just setup
- max@baluyot ~ $ just up
- github.com/Keshigami/agent-api
- Maximus Friedrich Baluyot
- AI & ML Specialist · Applied AI · ML Engineering · Automation

_Maximus Friedrich Baluyot · Caltech CTME · PGC AIML_
