# Coding Conventions

**Analysis Date:** 2026-05-27

## Naming Patterns

**Files:**
- Backend modules use snake_case Python filenames: `backend/app/services/session_service.py`, `backend/app/core/security.py`, `backend/agent/memory_manager.py`.
- Backend route modules are grouped by resource under `backend/app/api/routes/`: `backend/app/api/routes/auth.py`, `backend/app/api/routes/session.py`, `backend/app/api/routes/users.py`.
- Backend tests live in `test/` and use `test_*.py`: `test/test_api_backend.py`, `test/test_memory_manager_unit.py`, `test/test_session_service_unit.py`.
- Frontend React components use PascalCase component filenames with adjacent CSS modules: `frontend/src/components/Chat/ChatInput.tsx` and `frontend/src/components/Chat/ChatInput.module.css`.
- Frontend tests are colocated with implementation and use `*.test.ts` or `*.test.tsx`: `frontend/src/components/Chat/ChatInput.test.tsx`, `frontend/src/context/appReducer.test.ts`.
- API/client utility files use lower camel words or feature names: `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, `frontend/src/api/client.ts`.

**Functions:**
- Python functions and methods use snake_case: `validate_message_history` in `backend/agent/memory_manager.py`, `get_current_user_profile` in `backend/app/api/routes/users.py`, `create_access_token` in `backend/app/core/security.py`.
- FastAPI route handlers use verb/resource names and return typed response models where practical: `create_session_route` in `backend/app/api/routes/session.py`, `stream_chat` in `backend/app/api/routes/chat.py`.
- React components and providers use PascalCase named exports: `ChatInput` in `frontend/src/components/Chat/ChatInput.tsx`, `AuthProvider` in `frontend/src/context/AuthContext.tsx`, `Button` in `frontend/src/components/common/Button.tsx`.
- React hooks use `use*` names: `useChat` in `frontend/src/hooks/useChat.ts`, `useSessions` in `frontend/src/hooks/useSessions.ts`, `useAuth` in `frontend/src/context/AuthContext.tsx`.
- Frontend event handlers use `handle*` names and local helpers use intent names: `handleSubmit`, `handleKeyDown`, and `submitValue` in `frontend/src/components/Chat/ChatInput.tsx`.

**Variables:**
- Python constants and config attributes use UPPER_SNAKE_CASE: `JWT_SECRET`, `CORS_ORIGINS`, `TIKTOKEN_CACHE_DIR` in `backend/app/config.py`.
- Python private helpers use leading underscore: `_encode_sse` in `backend/app/api/routes/chat.py`, `_compress_messages` in `backend/app/services/agent_service.py`, `_rough_count_tokens` in `backend/agent/memory_manager.py`.
- TypeScript constants use UPPER_SNAKE_CASE for stable keys and defaults: `DEFAULT_API_BASE_URL` in `frontend/src/services/api.ts`, `ACTIVE_SESSION_KEY` in `frontend/src/hooks/useChat.ts`, `LOG_PREFIX` in `frontend/src/utils/logger.ts`.
- Frontend state variables use `is*` booleans for UI state: `isStreaming`, `isStopping`, and `isBootstrapping` in `frontend/src/context/appReducer.ts`.

**Types:**
- Python Pydantic models use PascalCase nouns ending with the payload role: `ChatStreamRequest` in `backend/app/models/request.py`, `SessionDetailResponse` in `backend/app/models/response.py`, `UserCreate` in `backend/app/models/user.py`.
- TypeScript interfaces use PascalCase nouns: `AppState`, `SessionSummary`, `ChatEvent`, and `HealthResponse` in `frontend/src/types/index.ts`.
- TypeScript discriminated unions use string literal `type` fields: `ChatEvent` in `frontend/src/types/index.ts`, `AppAction` in `frontend/src/context/appReducer.ts`.
- Frontend props interfaces use the component name plus `Props`: `ChatInputProps` in `frontend/src/components/Chat/ChatInput.tsx`, `ButtonProps` in `frontend/src/components/common/Button.tsx`.

## Code Style

**Formatting:**
- Frontend uses TypeScript with strict compiler checks from `frontend/tsconfig.app.json`: `strict`, `noUnusedLocals`, `noUnusedParameters`, and `noFallthroughCasesInSwitch` are enabled.
- Frontend JSX uses the React 17+ automatic runtime via `jsx: "react-jsx"` in `frontend/tsconfig.app.json`.
- Frontend code uses single quotes, semicolons, named exports, and two-space indentation in files such as `frontend/src/services/sse.ts` and `frontend/src/components/Chat/ChatInput.tsx`.
- Frontend CSS is module-scoped for components and pages: `frontend/src/components/common/Button.module.css`, `frontend/src/pages/Login.module.css`, `frontend/src/App.module.css`.
- Backend code uses Python 3.11+ style type hints, including `str | None`, `list[dict]`, and `dict[str, Any]`: examples are `backend/app/services/agent_service.py` and `backend/app/models/response.py`.
- Backend modules should keep `from __future__ import annotations` in route/service files that already use it: `backend/app/api/routes/chat.py`, `backend/app/services/agent_service.py`, `backend/app/services/session_service.py`.
- No Prettier, Ruff, Black, mypy, or pytest configuration files are detected in the repo root or `frontend/`; rely on existing local style and configured TypeScript/ESLint checks.

**Linting:**
- Frontend linting uses ESLint flat config in `frontend/eslint.config.js`.
- ESLint extends `@eslint/js` recommended and `typescript-eslint` recommended rules in `frontend/eslint.config.js`.
- React hook rules and React refresh export checks are enforced by `eslint-plugin-react-hooks` and `eslint-plugin-react-refresh` in `frontend/eslint.config.js`.
- The frontend lint command is `cd frontend && npm run lint` from `frontend/package.json`.
- Backend linting is not configured. Follow PEP 8, project skill guidance from `.agents/skills/python-patterns/SKILL.md`, and current code style in `backend/app/` and `backend/agent/`.

## Import Organization

**Order:**
1. Standard library imports first: `json`, `threading`, `datetime`, `pathlib`, and `typing` in files such as `backend/app/services/agent_service.py` and `test/test_api_backend.py`.
2. Third-party imports next: `fastapi`, `pydantic`, `langchain_core`, `axios`, `react`, `vitest`, and Testing Library imports in files such as `backend/app/api/routes/chat.py` and `frontend/src/components/Chat/ChatInput.test.tsx`.
3. Local application imports last: `backend.app.*` in backend files and relative `../` or `./` imports in frontend files.
4. Type-only TypeScript imports use `import type`: `frontend/src/components/Chat/ChatInput.tsx`, `frontend/src/services/sse.ts`, and `frontend/src/types/index.ts`.

**Path Aliases:**
- No TypeScript path aliases are configured in `frontend/tsconfig.app.json`; use relative imports such as `../types`, `./api`, and `../../context/AuthContext`.
- Backend imports use absolute package paths from the repository root, such as `backend.app.utils.logging_config` in `backend/app/services/agent_service.py`.
- Tests sometimes add the repo root manually with `sys.path.insert(0, ".")` or a parent path in `test/test_agent_core_unit.py`, `test/test_memory_manager_unit.py`, and `test/test_review_tool.py`; keep new backend tests in `test/` and prefer imports that work from the repository root.

## Error Handling

**Patterns:**
- FastAPI routes raise `HTTPException` with proper HTTP status codes and concise detail payloads: `backend/app/api/routes/auth.py`, `backend/app/api/routes/session.py`, `backend/app/api/routes/users.py`.
- Service methods return explicit success tuples for expected business failures: `AuthService.register` and `AuthService.authenticate` in `backend/app/services/auth_service.py`; keep error codes stable, such as `AUTH_USER_EXISTS` and `AUTH_INVALID_CREDENTIALS`.
- Streaming routes catch broad stream exceptions inside the generator and emit an SSE `error` event instead of crashing the response: `backend/app/api/routes/chat.py`.
- Frontend service calls convert failed HTTP responses to thrown errors: `ApiError` in `frontend/src/services/api.ts` and `streamChat` errors in `frontend/src/services/sse.ts`.
- Frontend hooks convert unknown caught values with `error instanceof Error ? error.message : '...'`: `frontend/src/hooks/useChat.ts` and `frontend/src/hooks/useSessions.ts`.
- Frontend 401 handling must invalidate local auth session through `invalidateAuthSession`: `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, and `frontend/src/api/client.ts`.

## Logging

**Framework:** Python `logging` via `backend/app/utils/logging_config.py`; frontend `console.*` wrapped by `frontend/src/utils/logger.ts`.

**Patterns:**
- New backend modules must import a category logger from `backend/app/utils/logging_config.py`: `auth_logger`, `chat_logger`, `session_logger`, `user_logger`, `tools_logger`, `db_logger`, `agent_logger`, or `api_logger`.
- Backend logs are written under `logs/{module}/{date}/{module}_{HH}h.log` with hourly rotation configured in `backend/app/utils/logging_config.py`.
- Backend log messages commonly include an uppercase domain prefix such as `[AUTH]`, `[SESSION]`, `[TOOLS]`, or `[AGENT]`: examples are `backend/app/services/auth_service.py` and `backend/tools/search_tool.py`.
- Frontend application code should use `logger.debug/info/warn/error(message, context, data)` from `frontend/src/utils/logger.ts`, as in `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useSessions.ts`, `frontend/src/pages/Login.tsx`, and `frontend/src/pages/Register.tsx`.
- Avoid new direct `console.log` calls in frontend application code. `frontend/src/api/client.ts` currently has direct request-interceptor logging; follow `frontend/src/utils/logger.ts` for new code.
- Avoid logging raw credentials, full tokens, or request bodies. Existing auth/token logs appear in `backend/app/main.py`, `backend/app/core/deps.py`, and `frontend/src/api/client.ts`; new code should log IDs/statuses and redact secrets.
- Log files and generated reports belong in `logs/`; `test/test_concurrent_sessions.py` writes its runtime logs and JSON report under `logs/`.

## Comments

**When to Comment:**
- Use docstrings for public FastAPI routes, services, Pydantic models, and complex backend helpers: `backend/app/api/routes/chat.py`, `backend/app/services/session_service.py`, `backend/agent/memory_manager.py`.
- Use short comments to explain non-obvious protocol or lifecycle details, such as SSE parsing in `frontend/src/services/sse.ts` and compression/history constraints in `backend/agent/memory_manager.py`.
- Keep comments near behavior that has operational constraints, such as tiktoken cache fallback in `backend/agent/memory_manager.py` and log rotation in `backend/app/utils/logging_config.py`.
- Do not add comments that simply restate obvious assignments or JSX structure.

**JSDoc/TSDoc:**
- JSDoc is minimal in frontend source. Prefer clear TypeScript interfaces and named exports over large TSDoc blocks.
- Backend docstrings are the primary documentation style; keep them concise and behavior-focused.

## Function Design

**Size:** Keep route handlers thin and delegate database/agent behavior to services. `backend/app/api/routes/session.py` delegates to `SessionService`, and `backend/app/api/routes/chat.py` delegates streaming and stopping to `AgentService`.

**Parameters:** Use typed parameters and response models in backend route handlers. Use typed props interfaces for React components. Use `RequestInit`, `AbortSignal`, and explicit request/response interfaces in frontend service modules such as `frontend/src/services/api.ts` and `frontend/src/services/sse.ts`.

**Return Values:** Backend route handlers should return Pydantic response models or plain dictionaries for simple messages. Services may return domain tuples for expected failures. Frontend async service functions return `Promise<T>` or async generators such as `AsyncGenerator<ChatEvent>` in `frontend/src/services/sse.ts`.

## Module Design

**Exports:** Use named exports for React components, hooks, reducers, and utilities: `ChatInput`, `appReducer`, `useChat`, `streamChat`, and `logger`. `frontend/src/api/client.ts` exports both `api` and a default client for API resource wrappers.

**Barrel Files:** Backend packages use lightweight `__init__.py` files, including `backend/app/services/__init__.py` and `backend/tools/__init__.py`. Frontend does not use barrel index files for components; import directly from the component or module path.

**Backend idioms:**
- Keep FastAPI dependency providers in `backend/app/api/dependencies.py` and authentication dependencies in `backend/app/core/deps.py`.
- Keep Pydantic request/response/user models under `backend/app/models/`.
- Keep database access in `backend/utils/db.py`; service modules should wrap DB calls rather than embedding route-level database logic.
- Keep LangGraph and memory/checkpoint concerns under `backend/agent/`.
- Keep LangChain tool functions under `backend/tools/` and decorate callable tools with `@tool`, as in `backend/tools/search_tool.py`.

**Frontend idioms:**
- Keep backend API wrappers in `frontend/src/services/` for fetch-based chat/session calls and `frontend/src/api/` for axios resource wrappers.
- Keep global state transitions in `frontend/src/context/appReducer.ts`; avoid duplicating reducer logic inside components.
- Keep side-effecting workflows in hooks such as `frontend/src/hooks/useChat.ts` and `frontend/src/hooks/useSessions.ts`.
- Keep UI components presentational where possible and style with adjacent CSS modules.
- Keep i18n text in locale JSON files under `frontend/src/locales/`, `frontend/src/i18n/locales/`, and `frontend/public/locales/`; tests initialize i18next from `frontend/src/test/setup.ts`.

---

*Convention analysis: 2026-05-27*
