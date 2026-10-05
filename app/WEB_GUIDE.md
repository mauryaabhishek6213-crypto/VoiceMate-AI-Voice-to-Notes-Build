# VoiceMate Web · final-phase guide

## Running and testing

Install the project requirements in the project Python environment, then use `reflex run` from the project root. Use HTTPS (or localhost) for microphone, clipboard and sharing support. The existing separate FastAPI companion can be started with `python -m uvicorn app.ai_api:api --host 127.0.0.1 --port 8001`. It is not required to start a second service for the Reflex UI.

Run the complete supplied suite with `python -m pytest -q app/test_notes.py app/test_record.py app/test_ai.py app/test_final_features.py`. Tests use injected SDK responses and never send audio or notes to a live provider. The final-phase tests cover allowed audio formats, size boundaries, MIME/container validation, consent and availability, SDK transcription contract, invalid responses, API authentication and size rejection, stale import callbacks, Unicode text export, filename sanitization, share fallback decisions, settings validation and clear verification.

No execution tool was available during this editing turn. These new tests and the complete existing suite have not been executed here; historical passing AI tests are not evidence that the expanded suite passes.

## Audio import

Open **Import audio** in the header. Select one MP3, M4A, WAV, WebM or MP4 file up to 20 MB (20,000,000 bytes). Selection does not upload. Read the disclosure, check consent, then explicitly choose **Send audio & transcribe**. Every retry requires fresh consent. Review and edit an actual returned transcript before saving it as a browser-local note. A failed transcription never creates fabricated text or a note.

Transcription is optional and disabled until the operator explicitly enables supported audio transcription and supplies a transcription model in the server environment. Chat-completion support alone is not proof of transcription support. The server uses the actual OpenAI-compatible audio transcription endpoint, existing server credentials, bounded requests and no automatic provider retries. Disabled, missing configuration, unsupported endpoint, quota, timeout and connectivity errors are shown without claiming a successful provider connection. The previously observed chat quota failure does not establish audio availability.

Audio is sent as a raw request body, not multipart upload: bounded streaming into temporary memory avoids framework disk-spooling. No audio files are written to the upload directory, assets, database or server disk by this code. The server and provider necessarily receive the approved audio; external provider processing and retention policies still apply. Temporary memory is not a zero-retention guarantee for hosting/proxy infrastructure. Operators should not enable request-body logging or disk buffering for audio requests.

The companion exposes the same transcription workflow as a raw-body POST with a consent header, encoded original filename, media content type and English/Hindi language hint. Its existing authentication and basic rate controls apply to audio too. Clients must collect real human consent before sending; a header alone cannot prove consent. Do not embed service credentials in browser code.

## Export, sharing and preferences

Open a saved note. Copy, Download text and Share use its last saved title and content, never unsaved editor changes or AI results. Plain-text export preserves Unicode and line breaks and strips unsafe filename characters. Download feedback says only that a download was requested; it cannot verify the user's final file location. Share invokes the browser Web Share API. Unsupported or failed sharing offers **Copy instead**; it never silently copies. Cancellation is distinct from failure. Clipboard denial offers manual copying.

Settings is a header action, leaving the existing mobile bottom navigation unchanged. Save light/dark, English/Hindi interface and default speech preferences explicitly. Storage read-back verifies saving. Speech capture applies the saved default at the start of each new session; selecting a language for one capture does not silently alter preferences.

Clear-all requires confirmation and verifies both note and AI-result browser storage. Preferences are retained. Failure does not claim success and may mean a partial clear; retry before leaving. Concurrent tabs use last-write-wins storage, so close other editing tabs before clearing. This action does not remove downloaded backups, another browser's data or provider-side retention.

## Privacy and manual checks

This is a browser-based Reflex application, not native Flutter/Android. Browser storage holds notes, results and preferences, not audio. Text passes through Reflex server state to power the workspace; browser-local persistence does not mean on-device-only processing, encryption, cloud backup or guaranteed offline operation. Browser speech recognition may use its own external recognition service. AI and imported audio require explicit approval before provider content transmission.

Manual checks: switch English/Hindi and light/dark on every primary screen; reload and check preferences; check speech default; select invalid/empty/oversize audio and confirm no upload; select valid audio but omit consent and verify no request; cancel, retry and confirm fresh consent; exercise unavailable/quota/timeout states; when transcription is supported and funded, review actual text and verify local save after reload. Save a note, make unsaved edits and check exports still contain the saved version; deny clipboard, cancel share and test chosen fallback. Block local storage and verify saving/clearing does not report success. Clear with confirmation and reload to verify notes and attached results are absent while preferences remain. Browser interaction tests are manual; static script assertions do not replace these checks.
