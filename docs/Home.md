# Agent API

A FastAPI chat agent on one provider-agnostic LLM door that can call the sales-forecast service as a tool, with no key in source. Caltech CTME PGC AIML, capstone, by Maximus Friedrich Baluyot.

**Watch first:** [the 90-second film](https://github.com/Keshigami/agent-api/blob/main/demo/film.mp4).

## Pages
- [Getting started](Getting-Started.md): run it in three commands, what you see, the API.
- [How it was built](How-It-Was-Built.md): from the brief to a running service, step by step.
- [Results](Results.md): the numbers and what they mean.
- [Limits and next steps](Limits-and-Next-Steps.md): what it cannot do yet.
- [The film](The-Film.md): what the four chapters show.

## The brief
The course exercise was a thin FastAPI wrapper that forwarded text to Gemini, with an API key hardcoded as a fallback.
This version keeps the `POST /ask` contract and the CLI loop, but reads keys from the environment only, runs on
Anthropic, OpenAI or Gemini without code changes, works offline for tests and demos, and does one thing a proxy cannot:
it decides when to call the restaurant sales forecast service and answers from the result.

## The one-line answer
0 · API keys in source · three providers behind one door

## One honest limit
One tool round, no memory. Replies are summaries.
