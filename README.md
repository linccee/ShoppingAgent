# 镜澜导购 · Sales Agent

> 智能多平台购物决策助手 — 连接 Google Shopping、Amazon 与 eBay，一轮对话完成比价、评论归纳与购买建议。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-green.svg)](https://langchain.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.15+-orange.svg)](https://www.mongodb.com/)

## 核心功能

| 功能 | 说明 |
|------|------|
| **多平台搜索** | 并行搜索 Google Shopping、Amazon、eBay，返回真实商品数据 |
| **评论洞察** | AI 归纳用户评论，提炼核心优缺点与情感倾向 |
| **汇率换算** | 自动识别用户货币（CNY/USD/EUR），完成预算换算 |
| **智能推荐** | 综合价格、评分、评论给出结构化购买建议 |
| **会话记忆** | MongoDB 持久化记忆，跨重启保持上下文 |

## 当前状态

当前受支持的运行入口已经切换为 `backend.app.main` 和新的 `frontend/` React 应用。

- 后端：FastAPI + LangGraph + MongoDB
- 前端：React 18 + TypeScript + Vite
- 旧版 Streamlit 运行文件已下线

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│            React Frontend / 任意 HTTP Client                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     FastAPI Backend                          │
│        /api/v1/chat/*  /api/v1/sessions  /api/v1/health      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Agent / Tool Layer                      │
│                   LangGraph ReAct Agent                      │
│            (MongoDBSaver 持久化 Checkpointer)                │
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

创建 `.env` 文件：

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
```

### 启动

后端：

```bash
uvicorn backend.app.main:app --reload
```

前端：

```bash
cd frontend
npm run dev
```

- 后端默认运行在 `http://127.0.0.1:8000`
- 前端默认运行在 `http://127.0.0.1:5173`

### API 概览

- `POST /api/v1/chat/stream`: SSE 流式聊天
- `POST /api/v1/chat/stop`: 停止生成
- `POST /api/v1/sessions`: 创建会话
- `GET /api/v1/sessions`: 列出会话
- `GET /api/v1/sessions/{session_id}`: 获取会话详情
- `DELETE /api/v1/sessions/{session_id}`: 删除会话
- `GET /api/v1/health`: 健康检查

## 项目结构

```
1-agent/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置管理
│   │   ├── api/routes/     # chat / session / health 路由
│   │   ├── models/         # Pydantic 请求/响应模型
│   │   └── services/       # AgentService / SessionService
│   ├── agent/              # LangGraph agent 核心
│   ├── tools/              # 搜索/价格/评论/汇率/Tavily 工具
│   ├── utils/db.py         # MongoDB 会话与压缩状态
│   └── requirements.txt
├── frontend/
│   ├── src/                # React 前端源码
│   ├── package.json
│   └── vite.config.ts
├── test/                   # Python 单元测试
└── *.backup                # 迁移前备份文件
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
| 前端 | React 18 + TypeScript + Vite |
| Agent | LangGraph 1.1, LangChain Core |
| 记忆 | MongoDB + LangGraph Checkpointer |
| 搜索 | SerpAPI, Tavily API |
| LLM | OpenAI 兼容 API (默认 Qwen) |

## License

MIT
