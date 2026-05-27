<!-- refreshed: 2026-05-27 -->
# Architecture

**Analysis Date:** 2026-05-27

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    React / Vite Frontend                    │
├──────────────────┬──────────────────┬───────────────────────┤
│  Auth & Profile  │ Chat Shell State │  Presentational UI    │
│ `frontend/src/api`│`frontend/src/hooks`│`frontend/src/components`│
│ `frontend/src/pages`│`frontend/src/context`│                     │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │ REST JSON        │ SSE stream          │ JWT bearer
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                        │
│ `backend/app/main.py` + `backend/app/api/routes/*.py`        │
├──────────────────┬──────────────────┬───────────────────────┤
│ Auth/User Routes │ Session Routes   │ Chat Streaming Route  │
│ `backend/app/api/routes/auth.py`                             │
│ `backend/app/api/routes/session.py`                          │
│ `backend/app/api/routes/chat.py`                             │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service / Agent Layer                    │
│ `backend/app/services/*.py` + `backend/agent/agent_core.py`  │
└────────┬──────────────────┬─────────────────────┬────────────┘
         │ Mongo collections │ LangGraph checkpoints│ Tool calls
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 MongoDB + External AI/Search APIs            │
│ `backend/utils/db.py`, `backend/tools/*.py`, LLM API         │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app | Creates the ASGI app, attaches CORS, request logging middleware, and `/api/v1` routers. | `backend/app/main.py` |
| Auth routes | Register, login, refresh, and logout users through `AuthService`. | `backend/app/api/routes/auth.py` |
| User routes | Read and mutate the authenticated user's profile and preferences. | `backend/app/api/routes/users.py` |
| Session routes | Create, list, fetch, and delete user-owned chat sessions. | `backend/app/api/routes/session.py` |
| Chat routes | Expose authenticated SSE generation and stop endpoints. | `backend/app/api/routes/chat.py` |
| Dependency providers | Cache shared `SessionService` and `AgentService` instances for FastAPI dependency injection. | `backend/app/api/dependencies.py` |
| Auth dependency | Decode JWT bearer tokens and load active users before protected routes run. | `backend/app/core/deps.py` |
| Security utilities | Hash/verify passwords and create/decode JWT tokens. | `backend/app/core/security.py` |
| Services | Keep route handlers thin and centralize Mongo-backed auth, user, session, and agent orchestration. | `backend/app/services/*.py` |
| Agent runtime | Builds the active LangGraph ReAct agent, streams callbacks through a queue, and handles stop/retry cleanup. | `backend/agent/agent_core.py` |
| Memory checkpointer | Wraps LangGraph `MongoDBSaver` with compressed-memory reads and async compression writes. | `backend/agent/compressed_checkpointer.py` |
| Alternate StateGraph workflow | Defines a typed shopping workflow graph and node functions; available through `backend/agent/factory.py`, not the default FastAPI path. | `backend/agent/graph.py`, `backend/agent/nodes.py`, `backend/agent/factory.py` |
| Mongo helpers | Own module-level Mongo client, collections, and CRUD helpers for sessions, users, checkpoints, and compression state. | `backend/utils/db.py` |
| Tool layer | LangChain tools for product search, price lookup, review analysis, currency exchange, and Tavily search/extract. | `backend/tools/*.py` |
| React app shell | Composes providers, private routes, sidebar, hero, chat timeline, and composer. | `frontend/src/App.tsx` |
| Frontend app state | Stores chat/session/runtime UI state in a reducer-backed React Context. | `frontend/src/context/AppContext.tsx`, `frontend/src/context/appReducer.ts` |
| Frontend session hook | Bootstraps health/session state and manages session CRUD. | `frontend/src/hooks/useSessions.ts` |
| Frontend chat hook | Sends chat prompts, consumes SSE events, dispatches stream state updates, and stops generation. | `frontend/src/hooks/useChat.ts` |
| Frontend transport | Uses fetch for chat/session REST and SSE, and axios for auth/profile APIs. | `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, `frontend/src/api/client.ts` |

## Pattern Overview

**Overall:** Layered client/server application with a service-oriented FastAPI backend and a LangGraph ReAct agent behind the chat service.

**Key Characteristics:**
- Keep HTTP route functions in `backend/app/api/routes/*.py` focused on request validation, auth dependencies, response models, and service calls.
- Put business operations in `backend/app/services/*.py`; services call Mongo helpers in `backend/utils/db.py` or agent runtime functions in `backend/agent/agent_core.py`.
- Stream chat as server-sent events from `backend/app/api/routes/chat.py` to `frontend/src/services/sse.ts`, then reduce each event into UI state in `frontend/src/context/appReducer.ts`.
- Persist two forms of conversation state: user-visible session transcripts in `sessions_col` and LangGraph checkpoint/memory state through `CompressedCheckpointer`.
- Use module-level singletons deliberately for Mongo collections, cached FastAPI services, the shared agent instance, and compression workers.

## Layers

**Frontend Routing and Providers:**
- Purpose: Compose router, auth, language, toast, and chat state providers.
- Location: `frontend/src/App.tsx`
- Contains: `BrowserRouter`, `Routes`, `PrivateRoute`, provider nesting, and the `Shell` layout.
- Depends on: `frontend/src/context/*.tsx`, `frontend/src/hooks/*.ts`, `frontend/src/components/**`, `frontend/src/pages/*.tsx`
- Used by: React entrypoint `frontend/src/main.tsx`

**Frontend State and Hooks:**
- Purpose: Centralize bootstrapping, session CRUD, chat streaming, token usage, and UI error state.
- Location: `frontend/src/context/`, `frontend/src/hooks/`
- Contains: `AppProvider`, `appReducer`, `useSessions`, `useChat`, `AuthProvider`, `LanguageProvider`.
- Depends on: `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, `frontend/src/api/*.ts`, `frontend/src/types/index.ts`
- Used by: `frontend/src/App.tsx`, pages, and protected UI components.

**Frontend Transport:**
- Purpose: Normalize backend URL configuration, auth headers, REST errors, and SSE frame parsing.
- Location: `frontend/src/services/`, `frontend/src/api/`
- Contains: fetch-based session/chat clients and axios-based auth/profile clients.
- Depends on: browser `localStorage`, `import.meta.env`, and `frontend/src/utils/auth.ts`.
- Used by: `frontend/src/hooks/useSessions.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/context/AuthContext.tsx`, `frontend/src/pages/Profile.tsx`

**FastAPI Routing:**
- Purpose: Define public backend HTTP/SSE contract.
- Location: `backend/app/api/routes/`
- Contains: `/health`, `/auth/*`, `/users/me`, `/sessions/*`, `/chat/stream`, `/chat/stop`.
- Depends on: Pydantic models in `backend/app/models/`, dependencies in `backend/app/core/deps.py`, and services in `backend/app/services/`.
- Used by: router registration in `backend/app/main.py`.

**Backend Services:**
- Purpose: Own use-case behavior and keep route modules thin.
- Location: `backend/app/services/`
- Contains: `AgentService`, `SessionService`, `AuthService`, `UserService`.
- Depends on: `backend/utils/db.py`, `backend/agent/agent_core.py`, `backend/app/core/security.py`, Pydantic response models.
- Used by: FastAPI route modules and cached providers in `backend/app/api/dependencies.py`.

**Agent Runtime:**
- Purpose: Execute the active shopping ReAct agent, stream tokens/tool lifecycle events, and isolate memory by session ID.
- Location: `backend/agent/agent_core.py`
- Contains: `create_shopping_agent`, `stream_agent`, `run_agent`, callback queue bridge, stop handling, corrupted-checkpoint retry cleanup.
- Depends on: LangGraph `create_react_agent`, `ChatOpenAI`, `CompressedCheckpointer`, Mongo client, `backend/tools/*.py`, `backend/agent/prompt.py`, and `backend/app/config.py`.
- Used by: `backend/app/services/agent_service.py`.

**Agent Memory and Compression:**
- Purpose: Preserve raw LangGraph checkpoints while supplying compressed message histories when token thresholds are exceeded.
- Location: `backend/agent/compressed_checkpointer.py`, `backend/agent/memory_manager.py`, `backend/agent/compression_retry.py`, `backend/agent/tool_output_compressor.py`
- Contains: `CompressedCheckpointer`, compression task queue, retry/degradation state, tiktoken-aware token counting, tool-call sequence validation.
- Depends on: Mongo collections exposed by `backend/utils/db.py` and Lite LLM settings from `backend/app/config.py`.
- Used by: `backend/agent/agent_core.py` and `backend/agent/factory.py`.

**Persistence:**
- Purpose: Own MongoDB client and collection-level data access.
- Location: `backend/utils/db.py`
- Contains: `sessions_col`, `users_col`, compressed state, failed retry, degradation collections, session CRUD, health ping.
- Depends on: `backend/app/config.py`.
- Used by: service layer, agent memory layer, health route, and LangGraph checkpointer setup.

**Tool Integrations:**
- Purpose: Provide LangChain-callable product/search/review/currency capabilities to the shopping agent.
- Location: `backend/tools/`
- Contains: `search_products`, `prices`, `analyze_reviews`, `currency_exchange`, `tavily_search`, `tavily_extract`.
- Depends on: `Config` API keys and external HTTP/SDK clients.
- Used by: `backend/agent/agent_core.py`, `backend/agent/registry.py`, and StateGraph nodes in `backend/agent/nodes.py`.

## Data Flow

### Primary Chat Streaming Path

1. User submits text through `ChatInput`; `Shell` wires the submit handler to `sendMessage` (`frontend/src/App.tsx:23`, `frontend/src/App.tsx:72`).
2. `useChat.sendMessage` appends a user/assistant pair to local state and opens an authenticated SSE POST to `/chat/stream` (`frontend/src/hooks/useChat.ts:16`, `frontend/src/services/sse.ts:86`).
3. `stream_chat` authenticates the bearer token with `get_current_user`, starts `AgentService.stream`, and yields SSE frames with `_encode_sse` (`backend/app/api/routes/chat.py:29`, `backend/app/core/deps.py:12`, `backend/app/api/routes/chat.py:19`).
4. `AgentService.stream` creates or reuses a user-owned session, registers a stop event, lazily creates the shared agent, and iterates `stream_agent` events (`backend/app/services/agent_service.py:46`, `backend/app/services/session_service.py:19`, `backend/agent/agent_core.py:275`).
5. `stream_agent` runs the LangGraph ReAct agent in a background thread, bridges callback events through a queue, and yields `token`, `tool_start`, `tool_end`, `token_usage`, or `error` tuples (`backend/agent/agent_core.py:170`, `backend/agent/agent_core.py:275`).
6. `create_shopping_agent` configures `ChatOpenAI`, shopping tools, system prompt, and `CompressedCheckpointer(MongoDBSaver(client))` (`backend/agent/agent_core.py:70`, `backend/agent/agent_core.py:63`).
7. Each frontend SSE event is parsed by `createSseChunkParser`, normalized by `normalizeChatEvent`, and reduced by `appReducer` into chat messages, tool steps, token counts, or errors (`frontend/src/services/sse.ts:15`, `frontend/src/services/sse.ts:40`, `frontend/src/context/appReducer.ts:84`).
8. On stream completion or error, `AgentService.stream` compresses persisted tool output and saves the transcript snapshot through `SessionService.save` (`backend/app/services/agent_service.py:101`, `backend/app/services/session_service.py:89`, `backend/utils/db.py:32`).

### Authenticated Session Path

1. `AuthProvider.login` calls `authApi.login`, stores `access_token` and user data in `localStorage`, and syncs language preference (`frontend/src/context/AuthContext.tsx:22`, `frontend/src/api/auth.ts:28`).
2. `backend/app/api/routes/auth.py` delegates credential validation to `AuthService.authenticate` and emits a JWT through `AuthService.create_token` (`backend/app/api/routes/auth.py:64`, `backend/app/services/auth_service.py:105`, `backend/app/services/auth_service.py:141`).
3. Protected frontend routes pass through `PrivateRoute`, which redirects unauthenticated users to `/login` (`frontend/src/components/PrivateRoute.tsx:5`).
4. Protected backend routes depend on `get_current_user`, which decodes the JWT and reloads the user from MongoDB with `UserService.get_user_by_id` (`backend/app/core/deps.py:12`, `backend/app/services/user_service.py:14`).
5. `useSessions.initializeApp` fetches `/health` and `/sessions`, loads the preferred session from `localStorage`, or creates a new session (`frontend/src/hooks/useSessions.ts:87`, `frontend/src/services/api.ts:64`).

### Stop Generation Path

1. `ChatInput` invokes `useChat.stopGeneration`; the hook aborts the active fetch and POSTs `/chat/stop` (`frontend/src/hooks/useChat.ts:100`, `frontend/src/services/api.ts:80`).
2. `stop_chat` calls `AgentService.stop` for the current authenticated user request (`backend/app/api/routes/chat.py:83`, `backend/app/services/agent_service.py:37`).
3. `AgentService.stop` sets the per-session `threading.Event`; `_QueueCallback` checks it before LLM tokens and tool starts (`backend/app/services/agent_service.py:37`, `backend/agent/agent_core.py:170`).
4. `stream_agent` joins the worker thread briefly and removes the session-specific log handler during cleanup (`backend/agent/agent_core.py:275`).

### Memory Compression Path

1. LangGraph writes checkpoints through `CompressedCheckpointer.put` (`backend/agent/compressed_checkpointer.py:336`).
2. Tool messages are compressed, message history is validated, and the raw checkpoint is immediately persisted through wrapped `MongoDBSaver` (`backend/agent/compressed_checkpointer.py:354`, `backend/agent/tool_output_compressor.py`).
3. Short histories are stored as ready compressed state; longer histories enqueue `_CompressionTask` for the background worker (`backend/agent/compressed_checkpointer.py:377`, `backend/agent/compressed_checkpointer.py:244`).
4. Future `get` and `get_tuple` calls prefer ready compressed state and sanitize damaged tool-call histories when needed (`backend/agent/compressed_checkpointer.py:313`, `backend/agent/compressed_checkpointer.py:390`, `backend/agent/memory_manager.py:113`).

**State Management:**
- Frontend UI state is reducer state in `frontend/src/context/appReducer.ts` exposed through `AppProvider` and `useAppStore`.
- Frontend auth state is `AuthProvider` plus `localStorage` keys `access_token` and `user` in `frontend/src/context/AuthContext.tsx`.
- Frontend active session preference is `localStorage` key `mirror-curation.active-session-id` in `frontend/src/hooks/useSessions.ts` and `frontend/src/hooks/useChat.ts`.
- Backend session transcripts are MongoDB documents in `sessions_col` created and updated by `backend/utils/db.py`.
- Backend users are MongoDB documents in `users_col` accessed through `AuthService` and `UserService`.
- LangGraph memory is persisted by `MongoDBSaver` and compressed-memory collections behind `CompressedCheckpointer`.
- Runtime cancellation state is in-memory per process in `AgentService._active_stop_events`.

## Key Abstractions

**Route Module:**
- Purpose: Declare request/response shape and FastAPI dependencies for each endpoint group.
- Examples: `backend/app/api/routes/chat.py`, `backend/app/api/routes/session.py`, `backend/app/api/routes/auth.py`
- Pattern: `APIRouter(prefix=..., tags=[...])` plus Pydantic `response_model` and dependency-injected services/users.

**Service Class:**
- Purpose: Encapsulate use cases and data-access orchestration.
- Examples: `backend/app/services/agent_service.py`, `backend/app/services/session_service.py`, `backend/app/services/auth_service.py`, `backend/app/services/user_service.py`
- Pattern: Small classes with explicit methods called by routes; use logging from `backend/app/utils/logging_config.py`.

**Pydantic Contract:**
- Purpose: Define request/response validation and serialization boundaries.
- Examples: `backend/app/models/request.py`, `backend/app/models/response.py`, `backend/app/models/user.py`
- Pattern: `BaseModel` classes with field constraints and datetime encoders for Mongo-backed timestamps.

**SSE Chat Event:**
- Purpose: Carry backend stream events to the reducer without coupling React components to raw event frames.
- Examples: `backend/app/api/routes/chat.py`, `frontend/src/services/sse.ts`, `frontend/src/types/index.ts`
- Pattern: Backend emits `data: {"type","data","session_id"}` frames; frontend normalizes to the `ChatEvent` union.

**LangGraph ReAct Agent:**
- Purpose: Combine LLM, system prompt, tools, and persisted memory for shopping assistance.
- Examples: `backend/agent/agent_core.py`, `backend/tools/*.py`, `backend/agent/prompt.py`
- Pattern: `create_react_agent(model=..., tools=..., prompt=..., checkpointer=...)` with `thread_id=session_id`.

**Compressed Checkpointer:**
- Purpose: Preserve correctness of raw checkpoints while lowering future context size.
- Examples: `backend/agent/compressed_checkpointer.py`, `backend/agent/memory_manager.py`, `backend/agent/compression_retry.py`
- Pattern: Wrapper around `MongoDBSaver` that synchronously saves raw messages and asynchronously computes compressed alternatives.

**Frontend Hook Orchestrator:**
- Purpose: Keep components presentational by moving async workflows into hooks.
- Examples: `frontend/src/hooks/useSessions.ts`, `frontend/src/hooks/useChat.ts`
- Pattern: Hooks call transport functions, dispatch reducer actions, persist lightweight preferences, and surface toasts.

## Entry Points

**Backend ASGI App:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn backend.app.main:app --reload`
- Responsibilities: Configure logging, CORS, HTTP middleware, route registration, and local `main()` server startup.

**Frontend App:**
- Location: `frontend/src/main.tsx`
- Triggers: Vite dev server or production bundle loading `frontend/index.html`.
- Responsibilities: Mount React under `#root`, load i18n/global CSS, and render `App` inside `Suspense`.

**React Router Root:**
- Location: `frontend/src/App.tsx`
- Triggers: Browser navigation.
- Responsibilities: Define `/login`, `/register`, protected `/chat`, protected `/profile`, and `/` redirect.

**Chat Stream Endpoint:**
- Location: `backend/app/api/routes/chat.py`
- Triggers: Frontend POST `/api/v1/chat/stream`.
- Responsibilities: Authenticate user, stream agent events as SSE, stop on disconnect, and encode stream errors.

**Agent Factory:**
- Location: `backend/agent/agent_core.py`
- Triggers: First `AgentService.stream` call.
- Responsibilities: Instantiate the active ReAct shopping agent and checkpointer.

**Alternate Agent Factory:**
- Location: `backend/agent/factory.py`
- Triggers: Direct imports/tests or future callers choosing `use_stategraph=True`.
- Responsibilities: Build either the registry-based ReAct agent or the explicit `StateGraphBuilder` workflow.

**Database Module Import:**
- Location: `backend/utils/db.py`
- Triggers: Import by services, health route, or agent memory.
- Responsibilities: Instantiate `MongoClient`, expose collections, and provide CRUD helpers.

**User DB Init Script:**
- Location: `scripts/init_user_db.py`
- Triggers: Manual script execution.
- Responsibilities: Initialize MongoDB user-related indexes/data as a maintenance script.

## Architectural Constraints

- **Threading:** FastAPI request handlers call synchronous services; chat generation uses a background `threading.Thread` and `queue.Queue` in `backend/agent/agent_core.py`, while memory compression uses a daemon worker thread in `backend/agent/compressed_checkpointer.py`.
- **Global state:** Mongo `client` and collections are module-level in `backend/utils/db.py`; FastAPI services are `@lru_cache(maxsize=1)` singletons in `backend/app/api/dependencies.py`; `AgentService` lazily stores one shared agent instance; compression queues/caches/workers are module-level in `backend/agent/compressed_checkpointer.py`.
- **Session isolation:** Use authenticated `user_id` for API session ownership in `backend/app/services/session_service.py`; use LangGraph `thread_id=session_id` for agent memory isolation in `backend/agent/agent_core.py`.
- **Auth boundary:** All chat, session, user, and token refresh/logout routes depend on `get_current_user`; `/auth/register`, `/auth/login`, and `/health` are public.
- **Environment configuration:** Runtime configuration is centralized in `backend/app/config.py` and frontend base URLs are split between `frontend/src/services/api.ts` (`VITE_API_BASE_URL`) and `frontend/src/api/client.ts` (`VITE_API_URL`).
- **Secret handling:** `.env` and `.env.*` files exist and must not be read or quoted; document only variable names from source references.
- **Circular imports:** No explicit circular import chain is required for the active FastAPI path. The agent package exports many modules from `backend/agent/__init__.py`; prefer importing concrete modules directly in new backend code.
- **Python environment:** Per `AGENTS.md`, run Python commands through `conda activate py_ai`.

## Anti-Patterns

### Bypassing Service Ownership

**What happens:** Route modules can instantiate services directly, as in `AuthService()` in `backend/app/api/routes/auth.py` and `UserService()` in `backend/app/api/routes/users.py`.
**Why it's wrong:** It bypasses the cached provider style used by `backend/app/api/dependencies.py` and makes lifecycle/state management inconsistent.
**Do this instead:** For new route groups, define dependency providers in `backend/app/api/dependencies.py` and inject services into route functions, matching `get_agent_service` and `get_session_service`.

### Creating New Mongo Clients Outside `backend/utils/db.py`

**What happens:** Mongo collections are intentionally centralized at module scope in `backend/utils/db.py`.
**Why it's wrong:** Additional clients/collections make session ownership, compression state, and health checks inconsistent.
**Do this instead:** Add collection handles and helper functions in `backend/utils/db.py`, then call them from `backend/app/services/*.py` or `backend/agent/*.py`.

### Mixing Frontend HTTP Clients for the Same Domain

**What happens:** Session/chat clients use `fetch` under `frontend/src/services/`, while auth/profile use axios under `frontend/src/api/`.
**Why it's wrong:** Base URL env names, error shapes, and auth invalidation behavior can diverge.
**Do this instead:** For new chat/session features, extend `frontend/src/services/api.ts` or `frontend/src/services/sse.ts`; for auth/profile features, extend `frontend/src/api/*.ts` until the transport layers are unified.

### Using the Alternate StateGraph as the Active Path by Assumption

**What happens:** `backend/agent/graph.py` and `backend/agent/nodes.py` define a structured workflow, but `AgentService` imports `create_shopping_agent` and `stream_agent` from `backend/agent/agent_core.py`.
**Why it's wrong:** Changes to StateGraph nodes do not affect the current `/chat/stream` behavior unless the service wiring changes.
**Do this instead:** Modify `backend/agent/agent_core.py` for active ReAct-agent behavior, or explicitly route through `backend/agent/factory.py` with `use_stategraph=True` as a separate architecture change.

## Error Handling

**Strategy:** Convert route-level validation/auth failures to `HTTPException`, stream generation failures as SSE `error` events, and use best-effort logging/recovery for agent checkpoint and compression failures.

**Patterns:**
- Raise `HTTPException` with structured `detail` dictionaries for auth/user/session failures in `backend/app/api/routes/*.py`.
- Return empty `SessionDetailResponse` from `SessionService.get_for_user` to trigger route-level 404 handling for unauthorized/missing sessions.
- Catch chat stream exceptions inside the SSE generator and emit an `"error"` event in `backend/app/api/routes/chat.py`.
- Treat stop/disconnect as cancellation by setting per-session `threading.Event` instances in `backend/app/services/agent_service.py`.
- Detect corrupted LangGraph histories and delete/sanitize checkpoints in `backend/agent/agent_core.py` and `backend/agent/memory_manager.py`.
- Invalidate frontend auth state on HTTP 401 in both `frontend/src/services/api.ts` and `frontend/src/api/client.ts`.

## Cross-Cutting Concerns

**Logging:** Use named loggers from `backend/app/utils/logging_config.py` for all backend modules. Agent streaming also attaches per-session file handlers under `logs/agent/{date}/` from `backend/agent/agent_core.py`. Frontend modules use `frontend/src/utils/logger.ts` plus toast notifications for user-visible failures.

**Validation:** Backend uses Pydantic models in `backend/app/models/*.py`, FastAPI dependency validation, JWT decoding in `backend/app/core/deps.py`, and LangGraph history validation in `backend/agent/memory_manager.py`. Frontend uses TypeScript interfaces in `frontend/src/types/index.ts` and request-specific API interfaces in `frontend/src/api/*.ts`.

**Authentication:** JWT bearer tokens are created in `backend/app/core/security.py`, validated in `backend/app/core/deps.py`, stored by `frontend/src/context/AuthContext.tsx`, and attached by `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, and `frontend/src/api/client.ts`.

---

*Architecture analysis: 2026-05-27*
