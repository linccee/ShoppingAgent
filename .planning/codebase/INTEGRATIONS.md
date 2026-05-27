# External Integrations

**Analysis Date:** 2026-05-27

## APIs & External Services

**LLM Providers:**
- OpenAI-compatible chat completion endpoint - Primary shopping agent model and streaming responses.
  - SDK/Client: `langchain-openai` `ChatOpenAI`
  - Auth: `LLM_API_KEY` or fallback `api_key`
  - Base URL: `LLM_BASE_URL` or fallback `base_url`
  - Model: `LLM_MODEL_ID` or fallback `QWEN_MODEL_ID`
  - Implementation: `backend/agent/agent_core.py`, `backend/agent/registry.py`, `backend/app/config.py`
- OpenAI-compatible lite/compression endpoint - Conversation history summarization and compression.
  - SDK/Client: `langchain-openai` `ChatOpenAI`
  - Auth: `zhipu_api_key`
  - Base URL: `zhipu_base_url`
  - Model: `zhipu_module_id`
  - Implementation: `backend/agent/compressed_checkpointer.py`, `backend/app/config.py`

**Shopping & Search:**
- SerpApi - Product discovery, Amazon/eBay product lookup, prices, and review retrieval.
  - SDK/Client: `serpapi`
  - Auth: `SERPAPI_API_KEY`
  - Implementation: `backend/tools/search_tool.py`, `backend/tools/price_tool.py`, `backend/tools/review_tool.py`
  - Engines used: `google` shopping search, `amazon`, `ebay`, `amazon_product`, and `ebay_product`
- Tavily API - Web search and page extraction for time-sensitive/current information.
  - SDK/Client: `requests` direct HTTP calls; `tavily-python` is installed but not the active client in `backend/tools/tavily_tool.py`
  - Auth: `TAVILY_API_KEY`
  - Endpoints: `https://api.tavily.com/search`, `https://api.tavily.com/extract`
  - Implementation: `backend/tools/tavily_tool.py`
- ExchangeRate API - Currency conversion for non-USD or requested target-currency prices.
  - SDK/Client: `requests`
  - Auth: `EXCHANGE_RATE_API_KEY`
  - Endpoint shape: `https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{base_code}/{target_code}/{amount}`
  - Implementation: `backend/tools/currency_exchange_tool.py`

**Frontend-to-Backend API:**
- Sales Agent Backend API - Browser client for auth, users, sessions, health, and chat.
  - SDK/Client: `fetch` in `frontend/src/services/api.ts` and `frontend/src/services/sse.ts`; Axios wrapper in `frontend/src/api/client.ts`
  - Auth: Browser `localStorage` key `access_token`, sent as `Authorization: Bearer <token>`
  - Base URL: `VITE_API_BASE_URL` for `frontend/src/services/api.ts`; `VITE_API_URL` for `frontend/src/api/client.ts`

## Data Storage

**Databases:**
- MongoDB - Primary persistent store for users, sessions, agent state, compression state, retry state, and LangGraph checkpoints.
  - Connection: `MONGO_URI`
  - Client: `pymongo.MongoClient` in `backend/utils/db.py`
  - LangGraph checkpoint client: `langgraph.checkpoint.mongodb.MongoDBSaver` in `backend/agent/agent_core.py` and `backend/agent/factory.py`
  - Database name: `shop_agent` in `backend/utils/db.py`
  - Collections declared in code: `sessions`, `compressed_agent_states`, `compression_failed_tasks`, `compression_degradation_state`, and `users` in `backend/utils/db.py`

**File Storage:**
- Local filesystem only.
- Agent debug logs are written under `logs/agent/{date}/` by `backend/agent/agent_core.py`.
- Unified application logs use `backend/app/utils/logging_config.py`.
- Tiktoken cache defaults to `backend/tiktoken-cache/` through `backend/app/config.py` and `backend/agent/memory_manager.py`.

**Caching:**
- In-process compressed-state cache in `backend/agent/compressed_checkpointer.py`.
- Local tiktoken cache controlled by `TIKTOKEN_CACHE_DIR`, defaulting to `backend/tiktoken-cache/`.
- No Redis, Memcached, CDN, or external cache service detected.

## Authentication & Identity

**Auth Provider:**
- Custom username/email/password authentication.
  - Implementation: `backend/app/api/routes/auth.py`, `backend/app/services/auth_service.py`, `backend/app/core/security.py`, `backend/app/core/deps.py`
  - Password hashing: `bcrypt` with 12 rounds in `backend/app/core/security.py`
  - Token format: JWT using `PyJWT` in `backend/app/core/security.py`
  - Token auth: FastAPI dependency `get_current_user()` in `backend/app/core/deps.py`
  - Secret: `JWT_SECRET`
  - Algorithm: `HS256` configured in `backend/app/config.py`
  - Expiration: `ACCESS_TOKEN_EXPIRE_DAYS = 1` in `backend/app/config.py`
- Frontend session handling stores the access token in `localStorage` and invalidates sessions on 401 responses in `frontend/src/services/api.ts`, `frontend/src/services/sse.ts`, and `frontend/src/api/client.ts`.

## Monitoring & Observability

**Error Tracking:**
- None detected. No Sentry, OpenTelemetry, Datadog, Rollbar, or similar integration was found in `backend/requirements.txt` or `frontend/package.json`.

**Logs:**
- Backend logging is centralized through `backend/app/utils/logging_config.py`.
- API request logging middleware is in `backend/app/main.py`.
- Agent per-session debug file handlers are created in `backend/agent/agent_core.py`.
- Tool, database, auth, and agent loggers are imported across `backend/tools/`, `backend/utils/db.py`, `backend/app/core/security.py`, and `backend/app/api/routes/auth.py`.
- Frontend logging helper is used by SSE streaming in `frontend/src/services/sse.ts`.

## CI/CD & Deployment

**Hosting:**
- Not detected. No deployment platform configuration found for Docker, Render, Vercel, Netlify, or Procfile-style hosting.

**CI Pipeline:**
- None detected for the application.
- `.github/` contains GSD templates, skills, agents, and workflow documentation such as `.github/get-shit-done/`, not app CI workflow YAML.

## Environment Configuration

**Required env vars:**
- `MONGO_URI` - MongoDB connection string used by `backend/utils/db.py`.
- `JWT_SECRET` - JWT signing secret used by `backend/app/core/security.py`.
- `LLM_API_KEY` or `api_key` - Primary LLM authentication used by `backend/agent/agent_core.py`.
- `LLM_BASE_URL` or `base_url` - Primary OpenAI-compatible endpoint used by `ChatOpenAI`.
- `LLM_MODEL_ID` or `QWEN_MODEL_ID` - Primary LLM model identifier.
- `SERPAPI_API_KEY` - SerpApi shopping, product, price, and review tools.
- `TAVILY_API_KEY` - Tavily search and extraction tools.
- `EXCHANGE_RATE_API_KEY` - Currency conversion tool.
- `zhipu_api_key`, `zhipu_base_url`, and `zhipu_module_id` - Lite LLM compression path in `backend/agent/compressed_checkpointer.py`.
- `CORS_ORIGINS` - Optional comma-separated backend CORS allowlist; defaults to `http://localhost:5173,http://localhost:3000`.
- `TIKTOKEN_CACHE_DIR` - Optional cache override; defaults to `backend/tiktoken-cache/`.
- `VITE_API_BASE_URL` - Preferred frontend API base URL for `frontend/src/services/api.ts`.
- `VITE_API_URL` - Alternate frontend API base URL for `frontend/src/api/client.ts`.

**Secrets location:**
- `.env` file present - contains environment configuration and must not be read or quoted.
- `.env.example` file present - example environment configuration file; do not copy secrets into generated documentation.
- Runtime code loads environment values through `python-dotenv` in `backend/app/config.py`.

## Webhooks & Callbacks

**Incoming:**
- None detected. FastAPI routes under `backend/app/api/routes/` expose normal REST/SSE endpoints, but no webhook-specific callback route was found.
- Chat streaming uses a POST endpoint consumed as server-sent frames by `frontend/src/services/sse.ts`; implementation is under the chat route included by `backend/app/main.py`.

**Outgoing:**
- SerpApi requests from `backend/tools/search_tool.py`, `backend/tools/price_tool.py`, and `backend/tools/review_tool.py`.
- Tavily search and extract POST requests from `backend/tools/tavily_tool.py`.
- ExchangeRate API GET requests from `backend/tools/currency_exchange_tool.py`.
- OpenAI-compatible LLM requests through `ChatOpenAI` in `backend/agent/agent_core.py`, `backend/agent/registry.py`, and `backend/agent/compressed_checkpointer.py`.

---

*Integration audit: 2026-05-27*
