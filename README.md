# 镜澜导购 · Sales Agent

> 智能多平台购物决策助手 — 连接 Google Shopping、Amazon 与 eBay，一轮对话完成比价、评论归纳与购买建议。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-green.svg)](https://langchain.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.15+-orange.svg)](https://www.mongodb.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)

## 核心功能

| 功能 | 说明 |
|------|------|
| **多平台搜索** | 并行搜索 Google Shopping、Amazon、eBay，返回真实商品数据 |
| **评论洞察** | AI 归纳用户评论，提炼核心优缺点与情感倾向 |
| **汇率换算** | 自动识别用户货币（CNY/USD/EUR），完成预算换算 |
| **智能推荐** | 综合价格、评分、评论给出结构化购买建议 |
| **会话记忆** | MongoDB 持久化记忆，跨重启保持上下文 |
| **用户认证** | JWT 认证系统，支持注册/登录/会话隔离 |
| **国际化** | 支持中文、英文、日文、韩文切换 |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│            React Frontend (i18n) / HTTP Client              │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     FastAPI Backend                          │
│  /api/v1/auth/*  /api/v1/users/*  /api/v1/chat/*            │
│  /api/v1/sessions/*  /api/v1/health                        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Agent / Tool Layer                      │
│                   LangGraph ReAct Agent                      │
│            (MongoDBSaver 持久化 Checkpointer)                │
│            (Memory Compression 压缩长对话)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Tool Layer                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ │
│  │ 搜索     │ │ 价格     │ │ 评论     │ │ 汇率    │ │ Tavily│ │
│  │ search   │ │ prices   │ │ reviews  │ │ currency│ │ search│ │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘ └───────┘ │
│                      SerpAPI / Tavily API                    │
└─────────────────────────────────────────────────────────────┘
```

### 工作流

```
input → search → ┬→ price ─┐
                ├→ review ─┼→ recommend → output
                └→ currency─┘
```

- **input**: 接收用户购物需求
- **search**: 串行调用 `search_products` 搜索候选商品
- **price/review/currency**: 并行执行，分别获取价格、分析评论、换算汇率
- **recommend**: 综合所有信息生成推荐报告
- **output**: 结构化输出购买建议

## 快速开始

### 环境要求

- Python 3.11+
- MongoDB 4.15+ (本地或 Atlas)
- Node.js 18+
- API Keys (见下方)

### 安装依赖

后端依赖：

```bash
pip install -r backend/requirements.txt
```

前端依赖：

```bash
cd frontend
npm install
```

### 配置环境变量

创建 `backend/.env` 文件：

```bash
# 主模型 (优先使用新变量名，兼容旧变量)
LLM_API_KEY=your_api_key
LLM_BASE_URL=your_api_base_url
LLM_MODEL_ID=your_model_id

# 搜索服务
SERPAPI_API_KEY=your_serpapi_key      # https://serpapi.com/
TAVILY_API_KEY=your_tavily_key        # https://tavily.com/

# MongoDB (用于会话记忆持久化)
MONGO_URI=mongodb://localhost:27017

# 汇率 API (可选)
EXCHANGE_RATE_API_KEY=your_exchange_rate_key

# TikToken 缓存目录 (可选)
TIKTOKEN_CACHE_DIR=backend/tiktoken-cache

# CORS Origins (可选，逗号分隔)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

前端配置 (`frontend/.env`)：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### 启动

后端：

```bash
uvicorn backend.app.main:app --reload
# 或直接运行
python -m backend.app.main
```

前端：

```bash
cd frontend
npm run dev
```

- 后端默认运行在 `http://127.0.0.1:8000`
- 前端默认运行在 `http://127.0.0.1:5173`

## API 文档

启动后端后访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档。

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/refresh` | 刷新 Token |
| POST | `/api/v1/auth/logout` | 登出 |

### 用户接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/users/me` | 获取当前用户信息 |
| PUT | `/api/v1/users/me/preferences` | 更新用户偏好设置 |

### 聊天接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/stream` | SSE 流式聊天（需认证） |
| POST | `/api/v1/chat/stop` | 停止生成（需认证） |

### 会话接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/sessions` | 创建会话（需认证） |
| GET | `/api/v1/sessions` | 列出会话（需认证，仅本人） |
| GET | `/api/v1/sessions/{session_id}` | 获取会话详情（需认证，仅本人） |
| DELETE | `/api/v1/sessions/{session_id}` | 删除会话（需认证，仅本人） |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 服务健康检查 |

## 项目结构

```
1-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理（支持新旧变量名兼容）
│   │   ├── api/
│   │   │   ├── routes/          # 路由：auth/chat/session/users/health
│   │   │   ├── dependencies.py  # 依赖注入
│   │   │   └── ...
│   │   ├── core/
│   │   │   ├── security.py      # JWT/密码加密
│   │   │   └── deps.py          # 认证依赖
│   │   ├── models/              # Pydantic 请求/响应模型
│   │   ├── services/           # AgentService/SessionService/AuthService
│   │   └── utils/
│   │       └── logging_config.py # 统一日志配置
│   ├── agent/                   # LangGraph Agent 核心
│   │   ├── agent_core.py       # Agent 工厂与流式执行
│   │   ├── compressed_checkpointer.py  # 记忆压缩 Checkpointer
│   │   ├── compression_retry.py # 压缩重试机制
│   │   ├── memory_manager.py   # 记忆管理器
│   │   ├── graph.py            # 状态图构建
│   │   ├── nodes.py            # 节点函数
│   │   ├── state.py            # 状态定义
│   │   └── factory.py          # Agent 工厂
│   ├── tools/                  # 工具：search/price/review/currency/tavily
│   ├── utils/
│   │   └── db.py               # MongoDB 会话与压缩状态
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   ├── components/        # React 组件
│   │   ├── context/           # React Context
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── i18n/              # 国际化配置
│   │   ├── locales/           # 翻译文件 (en/zh/ja/ko)
│   │   ├── pages/             # 页面组件
│   │   ├── services/          # 业务服务
│   │   ├── types/             # TypeScript 类型
│   │   └── App.tsx            # 应用入口
│   ├── package.json
│   └── vite.config.ts
├── test/                       # Python pytest 测试
├── scripts/                    # 工具脚本
└── logs/                       # 日志文件目录
```

## 工具说明

### search_products
搜索候选商品，关键词必须为英文，返回多平台商品列表。

### prices
输入商品 SKU (Amazon ASIN / eBay product_id) 获取精确价格。

### analyze_reviews
分析商品评论，提取优缺点、情感评分与代表性评论。

### currency_exchange
多货币支持，自动识别 CNY/USD/EUR/JPY 等。

### tavily_search / tavily_extract
当用户询问最新产品、时效性信息时，通过 Tavily 从网络获取最新内容。

## 技术栈

| 类别 | 技术 |
|------|------|
| API | FastAPI 0.116, Uvicorn |
| 前端 | React 18 + TypeScript + Vite + TailwindCSS |
| Agent | LangGraph 1.1, LangChain Core |
| 记忆 | MongoDB + LangGraph Checkpointer + 记忆压缩 |
| 搜索 | SerpAPI, Tavily API |
| LLM | OpenAI 兼容 API (默认 Qwen) |
| 认证 | JWT (HS256), bcrypt |
| 国际化 | i18next (en/zh/ja/ko) |
| 日志 | 结构化日志，按小时轮换 |

## 开发命令

### 前端

```bash
cd frontend
npm run dev        # 开发服务器
npm run build      # 生产构建
npm run preview    # 预览构建
npm run test       # 运行测试
npm run lint       # ESLint 检查
npm run typecheck  # TypeScript 类型检查
```

### 后端

```bash
# 启动服务
uvicorn backend.app.main:app --reload

# 运行测试
pytest test/ -v
pytest test/test_search.py  # 单文件测试
```

## License

MIT
