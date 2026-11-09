# Limits and next steps

- One tool round per question and no conversation memory; a production agent would keep history and allow several rounds.
- Offline replies are summaries, not prose; they exist so the loop is testable without a key.
- The fallback forecast is a flat 28-day mean, labelled as such; it is a safety net, not a model.
- Next: stream replies, add a `history(store)` tool against the EDA tables, and record provider latency in the response.
