# VoiceMate AI assistant

## What changed

AI is optional and available only after a note is successfully saved. Open a saved note and use **Review AI request**. The eight actions are summarize, key points, suggest title, action items, study questions, simplify, English/Hindi translation, and ask this note. Ask requires a question. The assistant always uses the last saved transcript, not unsaved editor changes, and never overwrites a note title or transcript.

Immediately before every provider request, including retries, a disclosure asks for explicit approval to send the full saved transcript and question through the server to the configured external provider. Cancel makes no provider request. Avoid submitting sensitive content. Provider retention policies still apply; the application does not promise zero retention by an external service.

Generated results are plain text, editable, and attached by note ID. **Save result** saves edits explicitly; **Copy current text** copies the current textarea, including unsaved edits. Results use a separate browser-local storage entry and are verified after saving. Storage failures preserve a visible unsaved result for copying/retry rather than claiming success. Original notes and recording storage are unchanged. Deleting a note removes its attached results; results for missing notes are pruned when the assistant opens. Browser storage is not encrypted or a backup. Clearing browser data removes notes and results. Do not edit concurrently in multiple tabs: browser-local writes use last-write-wins semantics.

The supplied provider probe returned **429 / credit_balance_exhausted**. This implementation does not claim the provider is working. Its UI notes that last observed failure and maps future insufficient-quota errors to an actionable insufficient-credits message. The server owner must replenish credits; there is no fake response or automatic fallback. Note-taking, recording, and existing results remain usable without AI.

## Provider configuration

Use the already configured server environment. Both the Reflex assistant and companion service call the same provider implementation. No provider key, base URL, bearer token, or raw provider error is sent to the browser. Provider failure logging is sanitized: text generation, its deadline handler, audio transcription and its endpoint, and the assistant's external-request error handlers log only static warning/error codes, without exception messages, exception bodies, interpolation, or tracebacks. Do not retain prompts, questions, or outputs in logs. Avoid enabling SDK/HTTP debug logging or request-body logging elsewhere.

The environment names used are `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and optional `OPENAI_MODEL` (default `gpt-4o-mini`). Base URL is optional for standard OpenAI; use the existing compatible provider's value if configured. Keep all credential values server-side. Calls use the real asynchronous OpenAI SDK chat-completions endpoint, a 30-second total deadline, bounded output, and no automatic retries. Empty, partial, and invalid responses are not saved.

`app/ai_example_env.txt` contains empty credential slots and nonsecret defaults; it is a reference, not a populated secret file. Never commit a filled credential file.

## Standalone companion service

From the project root, start the separate service with `python -m uvicorn app.ai_api:api --host 127.0.0.1 --port 8001`. FastAPI, OpenAI, httpx, and pytest are already listed in the project dependencies; uvicorn is provided with the Reflex runtime.

- `GET /health` returns `{"status":"ok","provider":"not_probed"}`. This reports service liveness only, never provider availability and never makes a paid probe.
- `POST /api/v1/ai/summarize`
- `POST /api/v1/ai/key-points`
- `POST /api/v1/ai/title`
- `POST /api/v1/ai/action-items`
- `POST /api/v1/ai/questions`
- `POST /api/v1/ai/rewrite` (simplify)
- `POST /api/v1/ai/translate`
- `POST /api/v1/ai/ask`

All POST bodies have the same strict schema: `text` (nonblank string, at most 20,000 characters), `consent` (boolean, must be true), optional `question` (string up to 1,000 characters; nonblank for ask), and optional `target_language` (`English` or `Hindi`, default English). Unknown fields are rejected. Example nonsecret body: `{"text":"A short note to review.","consent":true,"target_language":"Hindi"}`. The calling client must present its own disclosure and collect genuine consent before setting this field; a boolean alone cannot prove a human saw a disclosure.

Success: `{"action":"summarize","result":"<actual provider output>"}`. Errors: `{"error":{"code":"insufficient_credits","message":"<safe user-facing explanation>","retryable":false}}`. No request text, stack traces, SDK messages, or validation input values are echoed. Validation is 422, unauthorized 401, oversized body 413, quota/rate limits 429, connectivity/configuration 503, provider failure 502, deadline 504. Rate-limit responses include Retry-After. API consumers must not assume all 429s are transient: credit exhaustion needs owner intervention.

Request bodies are limited to 96,000 bytes even when Content-Length is absent or spoofed. Unicode character limits and byte limits both apply. Body arrival and generation have deadlines. Development CORS explicitly permits only `http://localhost:3000` and `http://127.0.0.1:3000`; it is not authentication. No wildcard origins or credentialed CORS are enabled.

The service has a basic per-direct-peer rate limit of 10 requests/minute with bounded process-local bookkeeping. It ignores untrusted forwarded headers. This is intentionally a development/basic limiter, not distributed production abuse protection; multiple workers have independent budgets and a shared reverse proxy may group clients. Put stronger authenticated/distributed enforcement upstream if needed.

`AI_API_BEARER_TOKEN`, when configured, is required for every AI POST even in development. `AI_API_PUBLIC=true` fails closed if that token is absent. Before exposing the standalone API publicly, enable that flag, configure a strong secret token server-side, and use HTTPS plus appropriate gateway/authentication limits. Do not embed a deployment bearer token in a public browser client. Health remains unauthenticated and reveals no credential/configuration information. The Reflex assistant calls the shared provider internally rather than issuing browser requests to the standalone service; the standalone service's bearer token is not a Reflex user login or shared browser credential.

## Tests

Run `python -m pytest app/test_ai.py app/test_notes.py app/test_record.py app/test_final_features.py`. AI tests inject fake providers or mocked SDK failures and never call the live provider. Coverage includes all eight routes, validation and consent, malformed JSON, unknown actions, missing/blank questions, safe error envelopes, captured-log privacy regression checks for mocked rate-limit and insufficient-credit exceptions containing a unique private marker, insufficient credits, rate limits, missing provider, offline, timeout, invalid outputs, public fail-closed authentication, byte bounds, CORS, and separate local-result storage/deletion. Injected test output exists only in tests; production has no fake-output path.

Manual UI checks: save a note; cancel disclosure and confirm no request; confirm an action and check credits failure; retry and verify a new disclosure; save/copy an editable real result when credits are available; reload to verify persistence; simulate browser-storage failure; delete the note and check attached result removal; verify a new unsaved note cannot use AI; ensure original transcript and recording still work. Automated tests are supplied. This editing environment has no command-execution tool, so the expanded suite has not been run here; no passing result is claimed. See WEB_GUIDE.md for the final-phase workflows and browser checks.
