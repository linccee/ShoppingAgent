# Codebase Structure

**Analysis Date:** 2026-05-27

## Directory Layout

```text
1-agent/
├── AGENTS.md                 # Agent/developer instructions for this repo
├── README.md                 # Product overview, setup, stack, and high-level structure
├── backend/                  # FastAPI backend, LangGraph agent, tools, requirements
│   ├── app/                  # Active FastAPI application package
│   │   ├── api/              # API dependencies and route modules
│   │   ├── core/             # Auth/security dependencies and JWT helpers
│   │   ├── models/           # Pydantic request/response/user models
│   │   ├── services/         # Backend use-case services
│   │   ├── utils/            # Logging configuration and app utilities
│   │   ├── config.py         # Environment-backed backend configuration
│   │   └── main.py           # Active backend entrypoint: `backend.app.main:app`
│   ├── agent/                # LangGraph agent runtime, memory, registry, StateGraph option
│   ├── tools/                # LangChain tools used by the shopping agent
│   ├── tiktoken-cache/       # Local tiktoken cache location
│   └── requirements.txt      # Backend Python dependencies
├── frontend/                 # React 18 + TypeScript + Vite frontend
│   ├── public/               # Public i18n locale assets
│   ├── src/                  # Frontend source code
│   ├── package.json          # Frontend scripts and dependencies
│   └── vite.config.ts        # Vite/Vitest config
├── scripts/                  # Maintenance scripts
├── test/                     # Python test directory required by AGENTS.md
├── logs/                     # Runtime log output directory
├── docs/                     # Project documentation assets
├── assets/                   # Legacy/static backup assets
├── ui/                       # Legacy UI backup files
└── .planning/codebase/       # Generated codebase intelligence documents
```

## Directory Purposes

**`backend/app/`:**
- Purpose: Active FastAPI application.
- Contains: App entrypoint, route modules, dependency providers, services, Pydantic models, config, security helpers, and logging setup.
- Key files: `backend/app/main.py`, `backend/app/config.py`, `backend/app/utils/logging_config.py`

**`backend/app/api/`:**
- Purpose: HTTP API boundary and FastAPI dependency factories.
- Contains: `backend/app/api/dependencies.py` plus route modules under `backend/app/api/routes/`.
- Key files: `backend/app/api/routes/chat.py`, `backend/app/api/routes/session.py`, `backend/app/api/routes/auth.py`, `backend/app/api/routes/users.py`, `backend/app/api/routes/health.py`

**`backend/app/core/`:**
- Purpose: Cross-route auth/security dependencies.
- Contains: JWT bearer dependency and password/JWT utilities.
- Key files: `backend/app/core/deps.py`, `backend/app/core/security.py`

**`backend/app/models/`:**
- Purpose: Backend request/response contracts.
- Contains: Pydantic models for chat, stop, health, sessions, auth, users, and errors.
- Key files: `backend/app/models/request.py`, `backend/app/models/response.py`, `backend/app/models/user.py`

**`backend/app/services/`:**
- Purpose: Backend use-case orchestration.
- Contains: Session CRUD, agent streaming/cancellation, auth registration/login, and user profile operations.
- Key files: `backend/app/services/agent_service.py`, `backend/app/services/session_service.py`, `backend/app/services/auth_service.py`, `backend/app/services/user_service.py`

**`backend/app/utils/`:**
- Purpose: Backend application utilities shared across modules.
- Contains: Unified logging configuration and logger exports.
- Key files: `backend/app/utils/logging_config.py`

**`backend/agent/`:**
- Purpose: Shopping agent runtime and optional structured graph workflow.
- Contains: Active ReAct agent runtime, prompt, registry/factory abstractions, StateGraph builder/nodes, memory compression, retry/degradation logic, and checkpoint wrappers.
- Key files: `backend/agent/agent_core.py`, `backend/agent/prompt.py`, `backend/agent/compressed_checkpointer.py`, `backend/agent/memory_manager.py`, `backend/agent/graph.py`, `backend/agent/nodes.py`, `backend/agent/factory.py`, `backend/agent/state.py`, `backend/agent/registry.py`

**`backend/tools/`:**
- Purpose: LangChain tools available to agent workflows.
- Contains: Search, price, review, currency exchange, and Tavily tools.
- Key files: `backend/tools/search_tool.py`, `backend/tools/price_tool.py`, `backend/tools/review_tool.py`, `backend/tools/currency_exchange_tool.py`, `backend/tools/tavily_tool.py`

**`backend/utils/`:**
- Purpose: Backend-wide infrastructure helpers outside the FastAPI package.
- Contains: MongoDB client, collections, and persistence helpers.
- Key files: `backend/utils/db.py`

**`frontend/src/`:**
- Purpose: Active frontend source.
- Contains: React app shell, routes/pages, components, hooks, context, API transports, i18n, styles, types, and tests.
- Key files: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/types/index.ts`

**`frontend/src/components/`:**
- Purpose: Reusable React UI components.
- Contains: Chat UI, sidebar/session list, hero prompt area, private route, buttons/loading/toasts/dialogs/language switcher.
- Key files: `frontend/src/components/Chat/ChatInput.tsx`, `frontend/src/components/Chat/ChatMessage.tsx`, `frontend/src/components/Sidebar/Sidebar.tsx`, `frontend/src/components/common/Button.tsx`, `frontend/src/components/PrivateRoute.tsx`

**`frontend/src/context/`:**
- Purpose: Frontend global state providers and reducer.
- Contains: App reducer/context, auth context, language context, and context access hooks.
- Key files: `frontend/src/context/AppContext.tsx`, `frontend/src/context/appReducer.ts`, `frontend/src/context/AuthContext.tsx`, `frontend/src/context/LanguageContext.tsx`, `frontend/src/context/useAppStore.ts`

**`frontend/src/hooks/`:**
- Purpose: Async workflow orchestration for the chat shell.
- Contains: Session bootstrap/CRUD hook and chat stream/stop hook.
- Key files: `frontend/src/hooks/useSessions.ts`, `frontend/src/hooks/useChat.ts`

**`frontend/src/services/`:**
- Purpose: Fetch-based transport for health, sessions, stop, and SSE chat.
- Contains: REST wrapper, SSE parser/generator, and tests.
- Key files: `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, `frontend/src/services/api.test.ts`, `frontend/src/services/sse.test.ts`

**`frontend/src/api/`:**
- Purpose: Axios-based transport for auth/profile domains.
- Contains: API client with interceptors and auth/user endpoint wrappers.
- Key files: `frontend/src/api/client.ts`, `frontend/src/api/auth.ts`, `frontend/src/api/user.ts`

**`frontend/src/pages/`:**
- Purpose: Route-level screens.
- Contains: Login, register, and profile pages with CSS modules and tests.
- Key files: `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx`, `frontend/src/pages/Profile.tsx`

**`frontend/src/i18n/`, `frontend/src/locales/`, `frontend/public/locales/`:**
- Purpose: Internationalization runtime config and locale JSON resources.
- Contains: i18next setup, constants/types, and locale namespaces for `zh-CN`, `en-US`, `ja-JP`, and `ko-KR`.
- Key files: `frontend/src/i18n/index.ts`, `frontend/src/i18n/constants.ts`, `frontend/public/locales/zh-CN/chat.json`

**`scripts/`:**
- Purpose: Manual maintenance scripts.
- Contains: Mongo user database initialization.
- Key files: `scripts/init_user_db.py`

**`test/`:**
- Purpose: Python test location required for new `test_*.py` files by `AGENTS.md`.
- Contains: Backend/Python tests when present.
- Key files: Not detected

**`logs/`:**
- Purpose: Runtime log output.
- Contains: Application and per-session agent logs.
- Key files: Runtime-generated; do not add source code here.

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: Active FastAPI app imported as `backend.app.main:app`.
- `frontend/src/main.tsx`: React DOM entrypoint.
- `frontend/src/App.tsx`: Router/provider root and chat shell composition.
- `backend/agent/agent_core.py`: Active shopping agent factory and stream runner.
- `scripts/init_user_db.py`: Manual user database initialization script.

**Configuration:**
- `AGENTS.md`: Repository-specific agent/developer constraints.
- `backend/app/config.py`: Backend environment variable mapping, model settings, memory compression thresholds, Mongo URI, JWT, password policy, CORS.
- `backend/requirements.txt`: Backend dependency list.
- `frontend/package.json`: Frontend scripts and dependencies.
- `frontend/vite.config.ts`: Vite/Vitest configuration.
- `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`: TypeScript configuration.
- `frontend/eslint.config.js`: Frontend lint configuration.
- `frontend/tailwind.config.js`, `frontend/postcss.config.js`: Styling tool configuration.
- `.env`, `.env.example`: Environment configuration files are present; never read or quote `.env` contents.

**Core Logic:**
- `backend/app/api/routes/chat.py`: Chat stream and stop HTTP contract.
- `backend/app/services/agent_service.py`: Session-aware agent stream orchestration and cancellation registry.
- `backend/app/services/session_service.py`: User-isolated session service.
- `backend/app/services/auth_service.py`: User registration, password policy, login, token creation.
- `backend/app/services/user_service.py`: User lookup/profile/preference/delete operations.
- `backend/utils/db.py`: MongoDB collections and persistence helpers.
- `backend/agent/agent_core.py`: Active LangGraph ReAct agent creation and streaming callback bridge.
- `backend/agent/compressed_checkpointer.py`: Checkpoint compression wrapper and worker.
- `backend/agent/memory_manager.py`: Token counting, history validation, summarization, and checkpoint sanitization.
- `backend/agent/graph.py`, `backend/agent/nodes.py`, `backend/agent/state.py`: Alternate typed StateGraph workflow.
- `backend/tools/*.py`: Agent tool implementations.
- `frontend/src/hooks/useChat.ts`: Client-side chat streaming workflow.
- `frontend/src/hooks/useSessions.ts`: Client-side session bootstrap and CRUD workflow.
- `frontend/src/context/appReducer.ts`: Reducer for chat/session/runtime UI state.
- `frontend/src/services/sse.ts`: SSE parser and async generator.
- `frontend/src/services/api.ts`: Fetch REST wrapper for health/sessions/chat stop.
- `frontend/src/api/client.ts`: Axios client for auth/profile APIs.

**Testing:**
- `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx`: Co-located frontend Vitest tests.
- `test/`: Required location for new Python tests matching `test_*.py`.
- `frontend/vite.config.ts`: Frontend test configuration location.

## Naming Conventions

**Files:**
- Backend route modules: lowercase resource names, e.g. `backend/app/api/routes/session.py`, `backend/app/api/routes/chat.py`.
- Backend service modules: `{domain}_service.py`, e.g. `backend/app/services/session_service.py`, `backend/app/services/agent_service.py`.
- Backend model modules: domain or contract group names, e.g. `backend/app/models/response.py`, `backend/app/models/user.py`.
- Backend agent modules: snake_case capability names, e.g. `backend/agent/compressed_checkpointer.py`, `backend/agent/memory_manager.py`.
- Backend tool modules: `{tool_domain}_tool.py`, e.g. `backend/tools/price_tool.py`, `backend/tools/currency_exchange_tool.py`.
- Frontend components: PascalCase `.tsx` plus matching CSS module, e.g. `frontend/src/components/Chat/ChatInput.tsx` and `frontend/src/components/Chat/ChatInput.module.css`.
- Frontend hooks: `use{Name}.ts`, e.g. `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useSessions.ts`.
- Frontend tests: co-located `*.test.ts` or `*.test.tsx`, e.g. `frontend/src/context/appReducer.test.ts`.
- Logs: `*.log` files belong under `logs/` per `AGENTS.md`.
- Python tests: `test_*.py` files belong under `test/` per `AGENTS.md`.

**Directories:**
- Backend API code belongs under `backend/app/api/`.
- Backend business services belong under `backend/app/services/`.
- Backend infrastructure persistence belongs under `backend/utils/`.
- Backend LangGraph runtime and memory belongs under `backend/agent/`.
- Backend LangChain tool implementations belong under `backend/tools/`.
- Frontend route pages belong under `frontend/src/pages/`.
- Frontend reusable UI belongs under `frontend/src/components/`.
- Frontend domain/network clients belong under `frontend/src/services/` for chat/session/fetch and `frontend/src/api/` for auth/profile/axios.
- Frontend global state belongs under `frontend/src/context/`.
- Frontend workflow hooks belong under `frontend/src/hooks/`.

## Where to Add New Code

**New Backend API Feature:**
- Primary route: add or extend `backend/app/api/routes/{resource}.py`.
- Service logic: add or extend `backend/app/services/{resource}_service.py`.
- Request/response models: add to `backend/app/models/request.py`, `backend/app/models/response.py`, or a focused model module under `backend/app/models/`.
- Router registration: include the route in `backend/app/main.py`.
- Service dependency: add provider in `backend/app/api/dependencies.py` when the service should be shared/cached.
- Tests: add Python tests under `test/`.

**New Auth/User Feature:**
- Backend API: extend `backend/app/api/routes/auth.py` or `backend/app/api/routes/users.py`.
- Business logic: extend `backend/app/services/auth_service.py` or `backend/app/services/user_service.py`.
- Security helper: use `backend/app/core/security.py`; route auth dependency should use `backend/app/core/deps.py`.
- Frontend auth/profile API: extend `frontend/src/api/auth.ts` or `frontend/src/api/user.ts`.
- Frontend UI: add route-level work under `frontend/src/pages/` and shared controls under `frontend/src/components/common/`.

**New Chat/Session Feature:**
- Backend chat behavior: extend `backend/app/services/agent_service.py` and active agent logic in `backend/agent/agent_core.py`.
- Backend session behavior: extend `backend/app/services/session_service.py` and persistence helpers in `backend/utils/db.py`.
- Frontend REST calls: extend `frontend/src/services/api.ts`.
- Frontend SSE events: update `backend/app/api/routes/chat.py`, `frontend/src/services/sse.ts`, `frontend/src/types/index.ts`, and reducer handling in `frontend/src/context/appReducer.ts`.
- Frontend hook orchestration: extend `frontend/src/hooks/useChat.ts` or `frontend/src/hooks/useSessions.ts`.

**New Agent Tool:**
- Implementation: add `backend/tools/{domain}_tool.py`.
- Active ReAct registration: import and append the tool in `backend/agent/agent_core.py`.
- Registry registration: add to `backend/agent/registry.py` if it should also work through `backend/agent/factory.py`.
- StateGraph node usage: add/update `backend/agent/nodes.py`, `backend/agent/state.py`, and `backend/agent/graph.py` only when using the alternate StateGraph path.
- Logging: use `tools_logger` from `backend/app/utils/logging_config.py`.

**New Agent Memory/Compression Behavior:**
- Checkpoint wrapper changes: `backend/agent/compressed_checkpointer.py`.
- Token counting/history validity/summarization: `backend/agent/memory_manager.py`.
- Retry/degradation behavior: `backend/agent/compression_retry.py`.
- Persistence helpers: `backend/utils/db.py`.
- Local tiktoken cache assumptions: keep using `backend/tiktoken-cache/` unless `Config.TIKTOKEN_CACHE_DIR` overrides it.

**New Frontend Component:**
- Implementation: place in `frontend/src/components/{Domain}/{Component}.tsx`.
- Styles: colocate `frontend/src/components/{Domain}/{Component}.module.css`.
- Tests: colocate `frontend/src/components/{Domain}/{Component}.test.tsx`.
- Shared primitives: place reusable controls under `frontend/src/components/common/`.
- Types: add cross-component contracts to `frontend/src/types/index.ts` when they are not page-local.

**New Frontend Page:**
- Implementation: `frontend/src/pages/{Page}.tsx`.
- Styles: `frontend/src/pages/{Page}.module.css`.
- Route: add to `frontend/src/App.tsx`.
- Protected pages: nest inside the `PrivateRoute` route in `frontend/src/App.tsx`.

**New Frontend State Transition:**
- State shape: update `frontend/src/types/index.ts`.
- Reducer action: update `frontend/src/context/appReducer.ts`.
- Dispatch call: update the relevant hook in `frontend/src/hooks/`.
- Tests: add/update `frontend/src/context/appReducer.test.ts` and hook/component tests as needed.

**Utilities:**
- Backend logging: use or extend `backend/app/utils/logging_config.py`.
- Frontend logging: use `frontend/src/utils/logger.ts`.
- Frontend auth session invalidation/storage helpers: use `frontend/src/utils/auth.ts`.
- Shared Python persistence helpers: add to `backend/utils/db.py`.

## Special Directories

**`backend/tiktoken-cache/`:**
- Purpose: Local tiktoken cache used by `backend/agent/memory_manager.py`.
- Generated: Yes
- Committed: Contains `.gitkeep`; cache payloads may exist locally.

**`backend/app/backend/tiktoken-cache/`:**
- Purpose: Additional cache-like path present under the app package.
- Generated: Yes
- Committed: A cache file is present; do not add source code here.

**`logs/`:**
- Purpose: Runtime logs, including agent per-session debug logs.
- Generated: Yes
- Committed: Directory may exist; log files should remain runtime artifacts.

**`frontend/src/locales/`, `frontend/src/i18n/locales/`, `frontend/public/locales/`:**
- Purpose: Locale JSON resources are duplicated across source/public paths.
- Generated: No
- Committed: Yes

**`assets/`, `ui/`:**
- Purpose: Backup/legacy files such as `assets/style.css.backup` and `ui/*.py.backup`.
- Generated: No
- Committed: Yes

**`.planning/codebase/`:**
- Purpose: Generated architecture, stack, quality, and concern maps for GSD workflows.
- Generated: Yes
- Committed: Intended to be committed by orchestrator, not by mapper agents.

---

*Structure analysis: 2026-05-27*
