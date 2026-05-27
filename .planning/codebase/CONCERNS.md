# Codebase Concerns

**Analysis Date:** 2026-05-27

## Tech Debt

**Stop/cancel event propagation (Severity: High):**
- Issue: The real `stream_agent()` consumes the `"stopped"` queue item and breaks without yielding it to `AgentService.stream()`. `AgentService.stream()` only sets `stopped = True` when it receives `kind == "stopped"`, so a stopped run can fall through and yield `"done"` as if completed.
- Files: `backend/agent/agent_core.py`, `backend/app/services/agent_service.py`, `frontend/src/hooks/useChat.ts`
- Evidence: `backend/agent/agent_core.py:366` drains and breaks on `"stopped"` before `yield item`; `backend/app/services/agent_service.py:105` depends on receiving `"stopped"`; `backend/app/services/agent_service.py:121` emits `"done"` when `stopped` remains false.
- Impact: The UI can miss the stopped state, persist a partial assistant message as a completed exchange, and hide cancellation failures.
- Fix approach: Yield a stopped event once from `stream_agent()` before draining, or make `AgentService.stream()` detect stop via the `stop_event` in `finally`.
- Suggested next checks: Add a backend unit test using the real `stream_agent()` path, not only `_FakeAgentService`, and assert `/api/v1/chat/stream` emits `stopped` without `done` after `/api/v1/chat/stop`.

**Duplicate API clients and environment variable names (Severity: Medium):**
- Issue: The frontend has both fetch-based service APIs and an Axios client with different environment variables.
- Files: `frontend/src/services/api.ts`, `frontend/src/api/client.ts`, `frontend/src/api/auth.ts`, `frontend/src/api/user.ts`, `README.md`, `frontend/src/vite-env.d.ts`
- Evidence: `frontend/src/services/api.ts:23` reads `VITE_API_BASE_URL`; `frontend/src/api/client.ts:4` reads `VITE_API_URL`; `README.md:72` documents `VITE_API_BASE_URL`; `frontend/src/vite-env.d.ts:4` only types `VITE_API_BASE_URL`.
- Impact: Auth/profile requests can target `http://localhost:8000/api/v1` while chat/session requests use a configured base URL, causing split-backend behavior in non-local environments.
- Fix approach: Standardize on one API client and one env var, preferably `VITE_API_BASE_URL`, then remove or adapt the duplicate client.
- Suggested next checks: Run a frontend grep for `VITE_API_URL`, `VITE_API_BASE_URL`, `api.post`, and `request<` before changing the client layer.

**Ignored backend tests (Severity: High):**
- Issue: `.gitignore` ignores the entire `test/` directory, and `git ls-files test` reports zero tracked backend tests.
- Files: `.gitignore`, `test/test_api_backend.py`, `test/test_compressed_checkpointer.py`, `test/test_session_service_unit.py`
- Evidence: `.gitignore:45` labels tests and `.gitignore:46` ignores `test/`; `test/test_api_backend.py` and other backend tests exist in the workspace but are not tracked.
- Impact: Critical backend regressions can be missed by collaborators and CI because the Python test suite is local-only.
- Fix approach: Stop ignoring `test/`, force-add intended backend tests, and keep generated caches ignored.
- Suggested next checks: Verify `git ls-files test` after unignoring, then run `conda activate py_ai && pytest test/ -q`.

**Tracked TypeScript build metadata (Severity: Low):**
- Issue: TypeScript incremental build output is tracked.
- Files: `frontend/tsconfig.app.tsbuildinfo`, `frontend/tsconfig.node.tsbuildinfo`, `.gitignore`
- Evidence: `git ls-files frontend/tsconfig.app.tsbuildinfo frontend/tsconfig.node.tsbuildinfo` returns both files; `.gitignore` has no `*.tsbuildinfo` entry.
- Impact: Builds create noisy diffs and possible cross-machine cache churn.
- Fix approach: Add `*.tsbuildinfo` to `.gitignore` and remove tracked build info from version control.
- Suggested next checks: Run `cd frontend && npm run build` after cleanup and confirm no build metadata appears in `git status`.

**Duplicate locale sources (Severity: Medium):**
- Issue: Locale JSON exists in three trees, while runtime loading only uses the public path.
- Files: `frontend/public/locales/`, `frontend/src/locales/`, `frontend/src/i18n/locales/`, `frontend/src/i18n/index.ts`
- Evidence: `frontend/src/i18n/index.ts:26` to `frontend/src/i18n/index.ts:27` loads `/locales/{{lng}}/{{ns}}.json`; duplicate copies exist under `frontend/src/locales/` and `frontend/src/i18n/locales/`.
- Impact: Translators and feature work can update the wrong copy, producing stale or missing UI strings.
- Fix approach: Keep one source of truth, or add a script that syncs generated copies from one canonical directory.
- Suggested next checks: Compare hashes for each language/namespace before deletion to avoid losing divergent translations.

## Known Bugs

**README backend startup command uses stale module path (Severity: Medium):**
- Symptoms: The documented command can fail depending on current working directory because it starts `app.main:app` from `backend/`, while the effective entry point is `backend.app.main:app`.
- Files: `README.md`, `AGENTS.md`, `backend/app/main.py`, `项目介绍.md`
- Evidence: `AGENTS.md:12` and `AGENTS.md:21` identify `backend.app.main`; `backend/app/main.py:64` runs `"backend.app.main:app"`; `README.md:79`, `README.md:150`, and `项目介绍.md:536` document `uvicorn app.main:app`.
- Trigger: Follow `README.md` from repo root or use code paths that rely on `backend.*` absolute imports.
- Workaround: Start with `uvicorn backend.app.main:app --reload` from the repo root.
- Suggested next checks: Run the documented README backend command and the AGENTS command in a clean shell with `conda activate py_ai` to confirm expected behavior.

**Account deletion leaves sessions and checkpoints orphaned (Severity: High):**
- Symptoms: Deleting a user only removes the user document, not that user's chat sessions or LangGraph checkpoints.
- Files: `backend/app/api/routes/users.py`, `backend/app/services/user_service.py`, `backend/utils/db.py`, `backend/agent/agent_core.py`
- Evidence: `backend/app/api/routes/users.py:87` exposes account deletion; `backend/app/services/user_service.py:115` to `backend/app/services/user_service.py:124` only calls `users_col.delete_one`; session deletion helpers in `backend/utils/db.py:296` only delete by session id.
- Trigger: A user calls `DELETE /api/v1/users/me`.
- Workaround: Manually delete that user's `sessions`, `compressed_agent_states`, and LangGraph checkpoint records from MongoDB.
- Suggested next checks: Add an integration test that creates a user-owned session, deletes the account, and verifies no session or checkpoint data remains addressable.

**Stopped stream tests do not exercise real cancellation logic (Severity: Medium):**
- Symptoms: Backend API tests can pass even if real `stream_agent()` swallows stopped events.
- Files: `test/test_api_backend.py`, `backend/agent/agent_core.py`
- Evidence: `test/test_api_backend.py:128` uses `_FakeAgentService`; `_FakeAgentService.stream()` yields `"stopped"` at `test/test_api_backend.py:147`, but real `backend/agent/agent_core.py:368` does not yield the stopped item.
- Trigger: Changes to `backend/agent/agent_core.py` cancellation behavior.
- Workaround: None beyond manual testing with the real agent stack.
- Suggested next checks: Add a unit test around `stream_agent()` with a fake executor and real callback queue behavior.

## Security Considerations

**Bearer tokens are logged on both backend and frontend (Severity: Critical):**
- Risk: Access tokens can leak into browser consoles and backend log files.
- Files: `backend/app/main.py`, `backend/app/core/deps.py`, `frontend/src/api/client.ts`, `logs/`
- Evidence: `backend/app/main.py:39` to `backend/app/main.py:40` logs the first 50 characters of the `Authorization` header; `backend/app/core/deps.py:18` to `backend/app/core/deps.py:19` logs the first 50 characters of the token; `frontend/src/api/client.ts:31` logs a token prefix in the browser.
- Current mitigation: Token values are truncated, but JWT prefixes still reveal header/payload material and correlate sessions.
- Recommendations: Remove token logging entirely; log request ids, user ids after validation, and token presence only.
- Suggested next checks: Inspect current `logs/auth/` and `logs/api/` for leaked token fragments before sharing logs.

**JWT and required runtime config are not validated at startup (Severity: High):**
- Risk: The app can start with missing `JWT_SECRET`, model settings, Mongo URI, or tool keys and fail later inside auth, agent, or tool calls.
- Files: `backend/app/config.py`, `backend/app/core/security.py`, `backend/utils/db.py`, `backend/agent/agent_core.py`
- Evidence: `backend/app/config.py:14` to `backend/app/config.py:27` and `backend/app/config.py:56` to `backend/app/config.py:65` read optional env vars; `backend/app/core/security.py:43` to `backend/app/core/security.py:57` uses `Config.JWT_SECRET`; `backend/utils/db.py:15` to `backend/utils/db.py:17` creates a `MongoClient` at import time.
- Current mitigation: Some tools return friendly missing-key messages, such as `backend/tools/search_tool.py:58` to `backend/tools/search_tool.py:64`.
- Recommendations: Add a startup validation layer that fails fast for required auth/database/LLM config, and classify optional tool keys separately.
- Suggested next checks: Run the backend with an empty environment and verify `/api/v1/auth/login`, `/api/v1/chat/stream`, and `/api/v1/health` fail predictably.

**Client-side token persistence is XSS-sensitive (Severity: Medium):**
- Risk: Access tokens are stored in `localStorage`, so any script execution bug can read them.
- Files: `frontend/src/context/AuthContext.tsx`, `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, `frontend/src/api/client.ts`
- Evidence: `frontend/src/context/AuthContext.tsx:66` stores `access_token`; API calls read it at `frontend/src/services/api.ts:28`, `frontend/src/services/sse.ts:92`, and `frontend/src/api/client.ts:30`.
- Current mitigation: React escapes normal content, and markdown is rendered through `react-markdown`, but token storage remains exposed to XSS.
- Recommendations: Prefer secure, httpOnly cookies for production auth, or explicitly document localStorage as a development-only tradeoff with short token lifetimes.
- Suggested next checks: Audit `frontend/src/components/Chat/MarkdownContent.tsx` and any `dangerouslySetInnerHTML` use before enabling untrusted rich content.

**Hard-coded migration account password (Severity: Medium):**
- Risk: The migration script creates an active built-in user with a fixed password.
- Files: `scripts/init_user_db.py`
- Evidence: `scripts/init_user_db.py:40` creates `user_inline`; `scripts/init_user_db.py:50` to `scripts/init_user_db.py:54` hashes the fixed password `user_inline_pass`; `scripts/init_user_db.py:64` sets `is_active` to true.
- Current mitigation: The account is only created when the script is run.
- Recommendations: Generate a random disabled migration owner, store only an internal marker, or require an explicit admin-provided password.
- Suggested next checks: Query production/staging MongoDB for `username=user_inline` and disable login if present.

**Profile update parameters are query parameters (Severity: Low):**
- Risk: Usernames and emails updated through query strings can leak through proxies and server access logs.
- Files: `backend/app/api/routes/users.py`
- Evidence: `backend/app/api/routes/users.py:40` to `backend/app/api/routes/users.py:44` declares `username` and `email` scalar parameters without a body model.
- Current mitigation: Authentication is required.
- Recommendations: Use a Pydantic request body model for profile updates.
- Suggested next checks: Review frontend `frontend/src/api/user.ts` and `frontend/src/pages/Profile.tsx` before changing the API shape.

## Performance Bottlenecks

**Blocking agent stream work inside async route (Severity: Medium):**
- Problem: `stream_chat()` is async, but iterates over a synchronous generator that can block while waiting for agent/thread queue items.
- Files: `backend/app/api/routes/chat.py`, `backend/app/services/agent_service.py`, `backend/agent/agent_core.py`
- Cause: `backend/app/api/routes/chat.py:41` defines an async generator, then `backend/app/api/routes/chat.py:50` uses a normal `for` loop over `agent_service.stream()`; `backend/agent/agent_core.py:363` blocks on `q.get()`.
- Improvement path: Move blocking iteration to a worker thread with async queue bridging, or expose a true async streaming API.
- Suggested next checks: Load test two concurrent `/api/v1/chat/stream` calls under Uvicorn and measure event-loop responsiveness for `/api/v1/health`.

**Unbounded compression and compressed-state memory cache (Severity: Medium):**
- Problem: Compression work uses an unbounded queue and process-local cache keyed by thread id.
- Files: `backend/agent/compressed_checkpointer.py`
- Cause: `backend/agent/compressed_checkpointer.py:67` creates `queue.Queue()` without max size; `backend/agent/compressed_checkpointer.py:71` stores `_compressed_state_cache` without eviction.
- Improvement path: Add queue size/backpressure, cache eviction, and metrics for pending compression tasks.
- Suggested next checks: Simulate many long sessions and inspect memory growth plus `compression_failed_tasks` volume.

**Verbose/full-output logging can amplify disk I/O and privacy exposure (Severity: Medium):**
- Problem: Agent logging is forced to DEBUG and writes full model/tool output to per-session files.
- Files: `backend/agent/agent_core.py`, `backend/app/utils/logging_config.py`, `logs/`
- Cause: `backend/agent/agent_core.py:12` sets `_log` to DEBUG; `backend/agent/agent_core.py:232` to `backend/agent/agent_core.py:234` logs full LLM output; `backend/agent/agent_core.py:268` to `backend/agent/agent_core.py:272` logs tool output; `backend/app/utils/logging_config.py:36` keeps 168 hourly rotations.
- Improvement path: Gate full-output logs behind an explicit debug env var and redact user/token/tool payloads by default.
- Suggested next checks: Run a multi-turn chat and inspect `logs/agent/` size and content sensitivity.

**External search loops can be slow under one chat request (Severity: Low):**
- Problem: Product search queries multiple SerpApi engines sequentially.
- Files: `backend/tools/search_tool.py`
- Cause: `backend/tools/search_tool.py:68` to `backend/tools/search_tool.py:100` loops platforms one at a time; the comment says parallel search but execution is sequential.
- Improvement path: Parallelize platform calls with bounded concurrency and per-call timeout support if the SerpApi client allows it.
- Suggested next checks: Time `search_products()` with valid API credentials for each platform and capture p95 latency.

## Fragile Areas

**LangGraph checkpoint mutation and private API use (Severity: High):**
- Files: `backend/agent/agent_core.py`, `backend/agent/compressed_checkpointer.py`, `backend/agent/memory_manager.py`
- Why fragile: The implementation mutates checkpoint message history and reaches through wrapper internals.
- Evidence: `backend/agent/agent_core.py:123` calls `memory_saver._saver.delete_thread(session_id)`; `backend/agent/compressed_checkpointer.py:140` to `backend/agent/compressed_checkpointer.py:144` replaces checkpoint `channel_values["messages"]`; `backend/agent/compressed_checkpointer.py:409` rebuilds `CheckpointTuple`.
- Safe modification: Add tests around valid/invalid tool-call histories before changing compression, stop, or checkpoint code.
- Test coverage: `test/test_compressed_checkpointer.py` exists but is ignored by `.gitignore`; cancellation corruption needs real-agent coverage.

**Global singleton services and module-level clients (Severity: Medium):**
- Files: `backend/app/api/dependencies.py`, `backend/app/services/agent_service.py`, `backend/utils/db.py`, `backend/agent/agent_core.py`
- Why fragile: Shared process state affects concurrency, tests, and multi-worker deployment behavior.
- Evidence: `backend/app/api/dependencies.py:8` and `backend/app/api/dependencies.py:14` cache services globally; `backend/app/services/agent_service.py:18` stores one shared agent; `backend/utils/db.py:17` creates `MongoClient` at import; `backend/agent/agent_core.py:60` stores global `_memory_saver`.
- Safe modification: Keep process-local state behind dependency providers and reset hooks for tests; avoid adding new module-level mutable state.
- Test coverage: Concurrency tests exist in `test/test_concurrent_sessions.py` but are not tracked by git.

**Session ownership has legacy no-user APIs (Severity: Medium):**
- Files: `backend/app/services/session_service.py`, `backend/utils/db.py`
- Why fragile: Authenticated routes use user-scoped methods, but legacy methods can list or delete all sessions if called from new code.
- Evidence: `backend/app/services/session_service.py:51` to `backend/app/services/session_service.py:63` lists all sessions; `backend/app/services/session_service.py:101` to `backend/app/services/session_service.py:104` deletes without user filtering; `backend/utils/db.py:280` to `backend/utils/db.py:307` has all-session list/delete helpers.
- Safe modification: Do not call `list()` or `delete()` from authenticated routes; prefer `list_by_user()` and `delete_for_user()`.
- Test coverage: Existing tests cover some user isolation through fake services, but real Mongo queries need integration coverage.

**Profile and auth validation are split between frontend and backend (Severity: Low):**
- Files: `frontend/src/pages/Register.tsx`, `backend/app/services/auth_service.py`, `backend/app/models/user.py`
- Why fragile: Frontend requires uppercase/lowercase/special-character strength hints, while backend only requires length, digit, letter, and a weak-password list.
- Evidence: `frontend/src/pages/Register.tsx:36` to `frontend/src/pages/Register.tsx:40` checks uppercase, lowercase, digit, and special; `backend/app/services/auth_service.py:22` to `backend/app/services/auth_service.py:36` enforces a different policy.
- Safe modification: Define password policy in backend response/config and render that policy on the frontend.
- Test coverage: No tracked backend auth policy tests are present.

## Scaling Limits

**Single-process stop registry (Severity: Medium):**
- Current capacity: Stop events are stored in memory for the current Python process.
- Files: `backend/app/services/agent_service.py`
- Limit: `backend/app/services/agent_service.py:19` stores `_active_stop_events` in a dict, so `/chat/stop` only works when routed to the same process handling `/chat/stream`.
- Scaling path: Use sticky sessions, a shared cancellation store, or a queue/pubsub mechanism before deploying multiple workers.
- Suggested next checks: Run two Uvicorn workers and verify a stop request can cancel a stream consistently.

**Lite-LLM compression throughput is globally serialized per process (Severity: Low):**
- Current capacity: One compression worker with a minimum 1.5-second interval between summary calls.
- Files: `backend/agent/compressed_checkpointer.py`
- Limit: `backend/agent/compressed_checkpointer.py:74` to `backend/agent/compressed_checkpointer.py:93` applies a global process lock and sleep; `backend/agent/compressed_checkpointer.py:264` to `backend/agent/compressed_checkpointer.py:270` starts one worker thread.
- Scaling path: Add metrics and shard compression workers only if the external LLM rate limits allow it.
- Suggested next checks: Measure backlog growth in `_compression_queue` during many active long sessions.

## Dependencies at Risk

**React Router runtime and type package versions are mismatched (Severity: Medium):**
- Risk: `@types/react-router-dom` v5 is installed alongside `react-router-dom` v7, even though v7 ships its own types.
- Impact: TypeScript can accept or reject APIs based on stale v5 definitions, especially route/navigation components.
- Files: `frontend/package.json`
- Evidence: `frontend/package.json:25` pins `react-router-dom` `^7.13.1`; `frontend/package.json:36` pins `@types/react-router-dom` `^5.3.3`.
- Migration plan: Remove `@types/react-router-dom` and rely on package-provided types, then run `cd frontend && npm run typecheck`.

**Streamlit remains in backend runtime dependencies (Severity: Low):**
- Risk: An unused legacy UI dependency remains in the backend runtime install.
- Impact: Larger install surface and potential vulnerability/maintenance load.
- Files: `backend/requirements.txt`, `ui/`
- Evidence: `backend/requirements.txt:5` to `backend/requirements.txt:6` includes `streamlit==1.55.0`; active project instructions identify FastAPI and `frontend/` as effective entry points; legacy files exist as `ui/*.backup`.
- Migration plan: Remove Streamlit if no supported command imports `ui/`, or move it to a separate optional requirements file.

## Missing Critical Features

**No visible rate limiting or lockout for auth endpoints (Severity: High):**
- Problem: Login and register endpoints have no application-level throttling.
- Files: `backend/app/api/routes/auth.py`, `backend/app/services/auth_service.py`
- Blocks: Safe exposure of `/api/v1/auth/login` and `/api/v1/auth/register` to the public internet.
- Evidence: `backend/app/api/routes/auth.py:57` to `backend/app/api/routes/auth.py:79` authenticates without rate limiting; `backend/app/services/auth_service.py:105` to `backend/app/services/auth_service.py:139` performs direct credential checks without lockout counters.
- Suggested next checks: Add IP/user throttling middleware or reverse-proxy rate limits and test repeated failed logins.

**No CI pipeline detected (Severity: Medium):**
- Problem: No workflow file is present under tracked `.github/workflows/`.
- Files: `.github/`, `.gitignore`, `frontend/package.json`, `backend/requirements.txt`
- Blocks: Automatic enforcement of `npm run test`, `npm run typecheck`, backend tests, and lint checks.
- Evidence: `.gitignore:41` ignores `.github/`; no tracked workflow evidence was found during repository scan.
- Suggested next checks: Add a minimal CI workflow that runs frontend checks and `conda activate py_ai && pytest test/ -q` once backend tests are tracked.

**No startup health check for required external services (Severity: Medium):**
- Problem: `/api/v1/health` checks Mongo but not model, JWT config, or optional tool readiness.
- Files: `backend/app/api/routes/health.py`, `backend/app/config.py`
- Blocks: Operators cannot distinguish a running API shell from a working agent service.
- Evidence: Health route references `ping_mongo` and config values, while required LLM/JWT config is only consumed later in `backend/agent/agent_core.py` and `backend/app/core/security.py`.
- Suggested next checks: Add `/api/v1/health/ready` or structured readiness fields for Mongo, JWT secret presence, LLM config presence, and optional tool keys.

## Test Coverage Gaps

**Security/auth behavior lacks tracked backend tests (Priority: High):**
- What's not tested: Missing `JWT_SECRET`, expired/invalid tokens, token refresh, profile update validation, account deletion cleanup, rate limiting/lockout.
- Files: `backend/app/core/security.py`, `backend/app/core/deps.py`, `backend/app/api/routes/auth.py`, `backend/app/api/routes/users.py`, `test/`
- Risk: Auth regressions can reach runtime without CI signal.
- Priority: High

**Real Mongo/session integration is mostly abstracted behind fakes (Priority: Medium):**
- What's not tested: Index assumptions, orphan cleanup, ownership queries against real Mongo documents, and `save_session()` preserving `user_id` on updates.
- Files: `backend/utils/db.py`, `backend/app/services/session_service.py`, `test/test_api_backend.py`
- Risk: Fake services can drift from Mongo behavior.
- Priority: Medium

**Stop/disconnect behavior needs end-to-end coverage (Priority: High):**
- What's not tested: Browser abort order, backend disconnect cleanup, real stopped-event propagation, and persistence of partial messages after cancellation.
- Files: `frontend/src/hooks/useChat.ts`, `frontend/src/services/sse.ts`, `backend/app/api/routes/chat.py`, `backend/agent/agent_core.py`
- Risk: Users see completed state after cancellation or leave invalid checkpoints.
- Priority: High

**Locale and API configuration drift lacks automated checks (Priority: Low):**
- What's not tested: All supported locale files exist in the runtime directory and environment variable names match code/docs.
- Files: `frontend/public/locales/`, `frontend/src/locales/`, `frontend/src/i18n/locales/`, `frontend/src/services/api.ts`, `frontend/src/api/client.ts`, `README.md`
- Risk: Internationalization or deployment config silently breaks after text/API changes.
- Priority: Low

---

*Concerns audit: 2026-05-27*
