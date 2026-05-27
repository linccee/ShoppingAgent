# Testing Patterns

**Analysis Date:** 2026-05-27

## Test Framework

**Runner:**
- Frontend: Vitest `^3.0.8` from `frontend/package.json`.
- Frontend config: `frontend/vite.config.ts` configures `test.environment = "jsdom"`, `setupFiles = "./src/test/setup.ts"`, and `css = true`.
- Backend: pytest `9.0.2` is listed in `backend/requirements.txt`, but most Python tests are written with `unittest.TestCase`.
- Backend config: Not detected. No `pytest.ini`, `pyproject.toml`, `setup.cfg`, or `tox.ini` was found.

**Assertion Library:**
- Frontend: Vitest `expect` plus `@testing-library/jest-dom/vitest` loaded by `frontend/src/test/setup.ts`.
- Frontend DOM testing: `@testing-library/react` and `@testing-library/user-event` in tests such as `frontend/src/components/Chat/ChatInput.test.tsx`.
- Backend: `unittest` assertions such as `self.assertEqual`, `self.assertTrue`, and `self.assertRaises` in `test/test_memory_manager_unit.py` and `test/test_api_backend.py`.
- Backend API testing: `fastapi.testclient.TestClient` in `test/test_api_backend.py`.

**Run Commands:**
```bash
cd frontend && npm run test       # Run all frontend Vitest tests
cd frontend && npm run test:watch # Watch frontend tests
cd frontend && npm run typecheck  # TypeScript validation
cd frontend && npm run build      # TypeScript build plus Vite production build
conda activate py_ai && pytest test/ -v # Run backend Python tests from repo root
```

## Test File Organization

**Location:**
- Frontend tests are colocated under `frontend/src/` beside implementation files: `frontend/src/components/Chat/ChatInput.test.tsx`, `frontend/src/services/sse.test.ts`, `frontend/src/context/appReducer.test.ts`.
- Backend tests live in root `test/`, matching project instructions: `test/test_api_backend.py`, `test/test_agent_core_unit.py`, `test/test_search.py`.
- Ad hoc/manual backend scripts also live in `test/`: `test/test_price_tool.py`, `test/test_review_tool.py`, `test/test_currency_exchange_tool.py`, and `test/test_agent_memory.py`.

**Naming:**
- Frontend: use `*.test.ts` for pure TypeScript units and `*.test.tsx` for React components.
- Backend: use `test_*.py` under `test/`.
- Backend unit-style test files often end with `_unit.py`: `test/test_session_service_unit.py`, `test/test_memory_manager_unit.py`, `test/test_agent_core_unit.py`.

**Structure:**
```
frontend/src/
├── components/**/[Component].test.tsx
├── services/*.test.ts
├── pages/*.test.tsx
└── context/*.test.ts

test/
├── test_*_unit.py
├── test_api_backend.py
├── test_search.py
└── test_*_tool.py
```

## Test Structure

**Suite Organization:**
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ChatInput } from './ChatInput';

describe('ChatInput', () => {
  it('submits content and resets the textarea', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <ChatInput
        isStreaming={false}
        isStopping={false}
        onSubmit={onSubmit}
        onStop={vi.fn()}
      />,
    );

    await user.type(screen.getByRole('textbox'), '帮我选一台笔记本');
    await user.click(screen.getByRole('button', { name: '发送' }));

    expect(onSubmit).toHaveBeenCalledWith('帮我选一台笔记本');
  });
});
```

```python
import unittest
from unittest.mock import patch

from backend.app.services.session_service import SessionService


class SessionServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = SessionService()

    @patch("backend.app.services.session_service.create_session", return_value="session-1")
    def test_create_returns_session_id(self, create_session_mock):
        session_id = self.service.create()

        self.assertEqual(session_id, "session-1")
        create_session_mock.assert_called_once_with(None, None)
```

**Patterns:**
- Frontend component tests render the component, interact through Testing Library queries, and assert accessible roles/text: `frontend/src/components/Chat/ChatInput.test.tsx`, `frontend/src/components/Sidebar/Sidebar.test.tsx`.
- Frontend pure logic tests call reducers/parsers directly: `frontend/src/context/appReducer.test.ts`, `frontend/src/services/sse.test.ts`.
- Frontend tests prefer `userEvent.setup()` for user interactions and `vi.fn()` for callbacks.
- Backend tests use `unittest.TestCase` classes, `setUp`/`tearDown`, local fake classes, and `unittest.mock.patch`.
- Backend API tests override FastAPI dependencies with `app.dependency_overrides` and clear them in `tearDown`: `test/test_api_backend.py`.
- Backend streaming tests collect SSE `data:` lines into JSON payloads using helper functions: `_parse_sse_response` and `_iter_sse_events` in `test/test_api_backend.py`.

## Mocking

**Framework:** Frontend uses Vitest `vi`; backend uses `unittest.mock.patch`, `patch.object`, and `patch.dict`.

**Patterns:**
```typescript
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'demo-user', email: 'demo@example.com' },
    logout: vi.fn(),
  }),
}));
```

```typescript
vi.stubGlobal(
  'fetch',
  vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Token expired' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    }),
  ),
);
```

```python
with patch.object(Config, "RECENT_HISTORY_TOKEN_BUDGET", 1):
    compressed = compress_history(messages, threshold=1, llm=_FakeLLM())
```

```python
app.dependency_overrides[get_session_service] = lambda: self.session_service
app.dependency_overrides[get_agent_service] = lambda: self.agent_service
app.dependency_overrides[get_current_user] = lambda: {
    "id": "test-user-id",
    "username": "tester",
    "is_active": True,
}
```

**What to Mock:**
- Mock browser globals and storage when testing auth/session behavior: `frontend/src/services/api.test.ts`, `frontend/src/services/sse.test.ts`, `frontend/src/pages/Profile.test.tsx`.
- Mock network transport with `vi.stubGlobal('fetch', ...)` for fetch-based frontend services: `frontend/src/services/api.test.ts`, `frontend/src/services/sse.test.ts`.
- Mock React context or router hooks for focused page/component tests: `frontend/src/components/Sidebar/Sidebar.test.tsx`, `frontend/src/pages/Profile.test.tsx`.
- Mock database access functions in service unit tests: `test/test_session_service_unit.py`.
- Mock external SDK modules and config keys for tool tests: `test/test_search.py` patches `sys.modules["serpapi"]` and `Config.SERPAPI_KEY`.
- Mock compression storage, workers, and config thresholds for checkpoint tests: `test/test_compressed_checkpointer.py`.

**What NOT to Mock:**
- Do not mock the reducer under test in `frontend/src/context/appReducer.test.ts`; construct actions and assert resulting state.
- Do not mock Testing Library DOM behavior; use roles, visible text, dialogs, links, and form controls.
- Do not call real external shopping, exchange-rate, LLM, or MongoDB services in automated unit tests. Keep networked/manual checks separate from deterministic tests.
- Do not read `.env` or secret files in tests. Patch config attributes directly, as in `test/test_search.py` and `test/test_memory_manager_unit.py`.

## Fixtures and Factories

**Test Data:**
```python
class _FakeExecutor:
    def __init__(self):
        self.calls = []

    def invoke(self, payload, config):
        self.calls.append((payload, config))
        return {"messages": [AIMessage(content="好的")]}
```

```python
def _tool_ai_message(*tool_call_ids: str) -> AIMessage:
    return AIMessage(
        content="调用工具",
        tool_calls=[
            {
                "name": f"tool_{index}",
                "args": {"index": index},
                "id": tool_call_id,
                "type": "tool_call",
            }
            for index, tool_call_id in enumerate(tool_call_ids, start=1)
        ],
    )
```

```typescript
function createLocalStorageMock(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
  };
}
```

**Location:**
- Backend fake classes are local to the tests that need them: `_FakeSessionService` and `_FakeAgentService` in `test/test_api_backend.py`, `_FakeSaver` in `test/test_compressed_checkpointer.py`.
- Frontend local storage mocks are duplicated in `frontend/src/services/api.test.ts` and `frontend/src/services/sse.test.ts`; new tests can extract a shared helper only if duplication grows.
- Frontend test i18n resources are initialized globally in `frontend/src/test/setup.ts`.

## Coverage

**Requirements:** No enforced coverage threshold or coverage command is configured in `frontend/package.json` or backend config. Project skill guidance in `.agents/skills/python-testing/SKILL.md` recommends 80%+ coverage and 100% for critical paths, but the current repository does not enforce it.

**View Coverage:**
```bash
cd frontend && npx vitest run --coverage # Requires coverage provider setup if not already installed
conda activate py_ai && pytest test/ --cov=backend --cov-report=term-missing # Requires pytest-cov if not already installed
```

## Test Types

**Unit Tests:**
- Backend unit tests cover agent invocation payloads in `test/test_agent_core_unit.py`, memory validation/compression in `test/test_memory_manager_unit.py`, session service DB wrapping in `test/test_session_service_unit.py`, and checkpointer behavior in `test/test_compressed_checkpointer.py`.
- Frontend unit tests cover reducer state transitions in `frontend/src/context/appReducer.test.ts` and SSE frame parsing in `frontend/src/services/sse.test.ts`.

**Integration Tests:**
- Backend API integration-style tests use `TestClient` with fake services and dependency overrides in `test/test_api_backend.py`.
- Backend concurrent streaming behavior is tested with threads and fake agent service streams in `test/test_api_backend.py`.
- Frontend component integration tests cover UI behavior across nested components and contexts: `frontend/src/components/Sidebar/Sidebar.test.tsx`, `frontend/src/pages/Profile.test.tsx`.

**E2E Tests:**
- Not used. No Playwright, Cypress, or browser E2E config is detected.
- `test/test_concurrent_sessions.py` is a manual/concurrency simulation script that creates real agents, writes logs/reports under `logs/`, and is not structured as an automated assertion suite.
- `test/test_agent_memory.py`, `test/test_price_tool.py`, `test/test_review_tool.py`, and `test/test_currency_exchange_tool.py` are manual scripts guarded by `if __name__ == "__main__"` and should not be treated as deterministic CI tests.

## Common Patterns

**Async Testing:**
```typescript
it('confirms session deletion before invoking the removal callback', async () => {
  const user = userEvent.setup();
  const onDeleteSession = vi.fn().mockResolvedValue(undefined);

  render(<Sidebar onDeleteSession={onDeleteSession} /* props omitted */ />);

  await user.click(screen.getByRole('button', { name: '删除' }));
  await user.click(screen.getByRole('button', { name: '确认删除' }));

  expect(onDeleteSession).toHaveBeenCalledWith('session-a');
});
```

```python
def test_chat_stop_interrupts_stream(self):
    events: list[dict] = []
    stream_thread = threading.Thread(target=reader)
    stream_thread.start()
    self.assertTrue(self.agent_service.wait_started("stop-session", timeout=2))

    stop_response = self.client.post("/api/v1/chat/stop", json={"session_id": "stop-session"})
    stream_thread.join(timeout=5)

    self.assertEqual(stop_response.status_code, 202)
    self.assertIn("stopped", [event["type"] for event in events])
```

**Error Testing:**
```typescript
await expect(listSessions()).rejects.toMatchObject<ApiError>({
  status: 401,
  message: 'Token expired',
});
```

```python
with self.assertRaises(InvalidCompressedHistoryError):
    validate_message_history(messages)
```

## Validation Practices

**Frontend validation:**
- For UI, interaction, or state changes, run `cd frontend && npm run test`, `cd frontend && npm run typecheck`, and `cd frontend && npm run build`.
- For narrow TypeScript-only frontend edits, at minimum run `cd frontend && npm run typecheck`.
- Use role/text queries over implementation details: `screen.getByRole('button', { name: '发送' })` in `frontend/src/components/Chat/ChatInput.test.tsx`.

**Backend validation:**
- Activate the required environment before Python commands: `conda activate py_ai`.
- Run focused tests with pytest selectors, for example `conda activate py_ai && pytest test/test_memory_manager_unit.py -v`.
- Use import-level or route-level checks when no test exists for the touched module.
- Avoid external network dependency in automated backend tests; patch SDKs/config and use fake services.

**Gaps:**
- Backend auth/user routes and services have limited deterministic test coverage compared with session/chat/memory modules: `backend/app/api/routes/auth.py`, `backend/app/api/routes/users.py`, `backend/app/services/auth_service.py`, `backend/app/services/user_service.py`.
- Frontend axios resource wrappers are lightly covered compared with fetch services: `frontend/src/api/client.ts`, `frontend/src/api/auth.ts`, `frontend/src/api/user.ts`.
- No automated E2E tests cover the full login/session/chat streaming flow from `frontend/src/App.tsx` through `backend/app/api/routes/chat.py`.
- No coverage enforcement is configured for frontend or backend.
- Several `test/test_*_tool.py` files are executable scripts with prints rather than assertion-based automated tests: `test/test_price_tool.py`, `test/test_review_tool.py`, `test/test_currency_exchange_tool.py`.

---

*Testing analysis: 2026-05-27*
