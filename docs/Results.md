# Results

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
