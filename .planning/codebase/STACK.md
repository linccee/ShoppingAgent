# Technology Stack

**Analysis Date:** 2026-05-27

## Languages

**Primary:**
- Python 3.10+ - Backend API, LangGraph agent, tools, persistence, and tests under `backend/` and `test/`. The code uses modern type syntax such as `str | None` in `backend/utils/db.py`.
- TypeScript 5.8.2 - Frontend React application under `frontend/src/`, compiled by `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, and `frontend/tsconfig.node.json`.

**Secondary:**
- JavaScript ES modules - Frontend build and lint configuration in `frontend/vite.config.ts`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`, and `frontend/eslint.config.js`.
- Markdown - Project and generated planning documentation in `README.md`, `项目介绍.md`, and `.planning/`.

## Runtime

**Environment:**
- Python runtime - Backend runs via `uvicorn backend.app.main:app --reload` using the project-required Conda environment `py_ai`.
- Node.js runtime - Frontend uses Vite and npm scripts from `frontend/package.json`.
- Browser runtime - React 18 app calls the backend API through `fetch` in `frontend/src/services/api.ts` and `frontend/src/services/sse.ts`, plus Axios in `frontend/src/api/client.ts`.

**Package Manager:**
- pip - Backend dependencies are pinned in `backend/requirements.txt`.
- npm - Frontend dependencies and scripts are defined in `frontend/package.json`.
- Lockfile: `frontend/package-lock.json` present; backend lockfile not detected.

## Frameworks

**Core:**
- FastAPI 0.116.1 - Backend HTTP API in `backend/app/main.py` with route modules under `backend/app/api/routes/`.
- Uvicorn 0.35.0 - ASGI development server invoked by `backend/app/main.py`.
- LangGraph 1.1.1 - ReAct shopping agent and checkpoint integration in `backend/agent/agent_core.py`.
- LangChain 1.2.12 / LangChain Core 1.2.19 - LLM/tool abstractions across `backend/agent/` and `backend/tools/`.
- langchain-openai 0.3.35 - OpenAI-compatible `ChatOpenAI` client in `backend/agent/agent_core.py`, `backend/agent/compressed_checkpointer.py`, and `backend/agent/registry.py`.
- React 18.3.1 - Frontend UI in `frontend/src/`.
- React Router DOM 7.13.1 - Frontend navigation package declared in `frontend/package.json`.
- Vite 6.2.0 - Frontend dev server, build, and Vitest config in `frontend/vite.config.ts`.

**Testing:**
- pytest 9.0.2 - Backend test runner declared in `backend/requirements.txt`; tests belong under `test/`.
- Vitest 3.0.8 - Frontend test runner configured in `frontend/vite.config.ts`.
- Testing Library React 16.3.0 / jest-dom 6.6.3 / user-event 14.6.1 - Frontend component testing stack declared in `frontend/package.json`.
- jsdom 26.0.0 - Browser-like frontend test environment configured in `frontend/vite.config.ts`.

**Build/Dev:**
- TypeScript 5.8.2 - Frontend typechecking via `npm run typecheck` from `frontend/package.json`.
- ESLint 9.21.0 with `typescript-eslint`, `eslint-plugin-react-hooks`, and `eslint-plugin-react-refresh` - Frontend linting in `frontend/eslint.config.js`.
- Tailwind CSS 3.4.19 - Utility CSS scanning `frontend/index.html` and `frontend/src/**/*.{js,ts,jsx,tsx}` via `frontend/tailwind.config.js`.
- PostCSS 8.5.8 and Autoprefixer 10.4.27 - CSS processing configured by `frontend/postcss.config.js`.
- Streamlit 1.55.0 - Legacy or auxiliary UI/runtime dependency declared in `backend/requirements.txt`; the current backend entrypoint is `backend/app/main.py`.

## Key Dependencies

**Critical:**
- `fastapi==0.116.1` - API framework for auth, user, session, health, and chat routes in `backend/app/api/routes/`.
- `langgraph==1.1.1` and `langgraph-prebuilt==1.0.8` - Agent orchestration and prebuilt ReAct agent in `backend/agent/agent_core.py`.
- `langgraph-checkpoint-mongodb==0.3.1` - MongoDB-backed LangGraph checkpoints via `MongoDBSaver` in `backend/agent/agent_core.py` and `backend/agent/compressed_checkpointer.py`.
- `pymongo==4.15.5` - Direct MongoDB client and collections in `backend/utils/db.py`.
- `langchain-openai==0.3.35` - OpenAI-compatible chat model client configured by `backend/app/config.py`.
- `pyjwt==2.12.1` and `bcrypt==5.0.0` - JWT access tokens and password hashing in `backend/app/core/security.py`.
- `react==18.3.1`, `react-dom==18.3.1`, and `vite==6.2.0` - Frontend runtime and build system in `frontend/`.

**Infrastructure:**
- `python-dotenv==1.1.0` - Loads environment configuration in `backend/app/config.py`.
- `requests==2.32.5` - HTTP client for Tavily and exchange-rate integrations in `backend/tools/tavily_tool.py` and `backend/tools/currency_exchange_tool.py`.
- `serpapi==0.1.5` - Shopping, product, price, and review API access in `backend/tools/search_tool.py`, `backend/tools/price_tool.py`, and `backend/tools/review_tool.py`.
- `tavily-python==0.7.23` - Declared dependency for Tavily integration; current implementation uses direct `requests.post` calls in `backend/tools/tavily_tool.py`.
- `axios==1.13.6` - Frontend API client in `frontend/src/api/client.ts`.
- `i18next`, `i18next-browser-languagedetector`, `i18next-http-backend`, and `react-i18next` - Frontend internationalization stack declared in `frontend/package.json`.
- `react-markdown` and `remark-gfm` - Markdown rendering stack declared in `frontend/package.json`.
- `lucide-react` - Icon library declared in `frontend/package.json`.

## Configuration

**Environment:**
- Backend configuration is centralized in `backend/app/config.py` through `python-dotenv` and `os.getenv`.
- `.env` and `.env.example` are present and must not be read or quoted; use them only as environment configuration files.
- LLM settings: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_ID`, fallback lowercase names `api_key` and `base_url`, and fallback `QWEN_MODEL_ID`.
- Lite/compression LLM settings: `zhipu_api_key`, `zhipu_base_url`, and `zhipu_module_id`.
- Search/tool settings: `SERPAPI_API_KEY`, `TAVILY_API_KEY`, and `EXCHANGE_RATE_API_KEY`.
- Data/auth settings: `MONGO_URI`, `JWT_SECRET`, `CORS_ORIGINS`, and optional `TIKTOKEN_CACHE_DIR`.
- Frontend API base URL is configured through `VITE_API_BASE_URL` in `frontend/src/services/api.ts` and `VITE_API_URL` in `frontend/src/api/client.ts`; prefer aligning new frontend API code to the existing `frontend/src/services/api.ts` helper.

**Build:**
- Backend dependency manifest: `backend/requirements.txt`.
- Frontend dependency manifest and scripts: `frontend/package.json`.
- Frontend lockfile: `frontend/package-lock.json`.
- Vite/Vitest config: `frontend/vite.config.ts`.
- TypeScript project references: `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, and `frontend/tsconfig.node.json`.
- ESLint config: `frontend/eslint.config.js`.
- Tailwind config: `frontend/tailwind.config.js`.
- PostCSS config: `frontend/postcss.config.js`.

## Platform Requirements

**Development:**
- Use `conda activate py_ai` before running Python commands for this repository.
- Backend setup: `pip install -r backend/requirements.txt`, then run `uvicorn backend.app.main:app --reload`.
- Frontend setup: run npm commands inside `frontend/`, starting with `npm install`.
- MongoDB must be reachable through `MONGO_URI`; README documents MongoDB 4.15+ as the expected database family.
- Keep tiktoken cache local by default at `backend/tiktoken-cache/` unless `TIKTOKEN_CACHE_DIR` is explicitly configured.

**Production:**
- Deployment target not detected in repository configuration; no `Dockerfile`, `docker-compose*.yml`, `render.yaml`, `vercel.json`, or `netlify.toml` was detected.
- CI pipeline not detected as application workflow files; `.github/` contains GSD templates, skills, agents, and workflow documentation rather than runtime CI configuration.
- Production requires configured environment variables from `backend/app/config.py`, a MongoDB instance, an OpenAI-compatible LLM endpoint, and reachable external tool APIs.

---

*Stack analysis: 2026-05-27*
