# 前后端分离迁移方案

## 1. 当前项目结构分析

### 1.1 现有架构

```
当前项目 (Streamlit + LangGraph)
├── main.py                    # Streamlit 入口
├── config.py                  # 配置管理
├── ui/                        # Streamlit UI 模块
│   ├── chat.py
│   ├── sidebar.py
│   └── stop_injection.py
├── agent/                     # LangGraph Agent 核心
│   ├── agent_core.py          # Agent 工厂 & 流式执行
│   ├── state.py               # 状态定义 (SharedState)
│   ├── nodes.py               # 节点函数 (input/search/price/review/currency/recommend/output)
│   ├── graph.py               # StateGraph 构建器
│   ├── prompt.py              # Prompt 模板
│   ├── compressed_checkpointer.py  # MongoDB 记忆持久化
│   ├── memory_manager.py      # 内存管理
│   ├── factory.py             # Agent 工厂
│   └── registry.py            # 工具注册
├── tools/                     # 工具模块
│   ├── search_tool.py         # 产品搜索 (SerpAPI)
│   ├── price_tool.py          # 价格获取
│   ├── review_tool.py         # 评论摘要
│   ├── currency_exchange_tool.py  # 货币转换
│   └── tavily_tool.py         # 实时搜索
├── utils/
│   └── db.py                  # 数据库工具
├── assets/
│   └── style.css              # 样式文件
└── test/                      # 测试模块
```

### 1.2 当前技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit (Python) |
| 后端 | LangGraph + LangChain |
| Agent | ReAct 模式 |
| 记忆 | MongoDB (CompressedCheckpointer) |
| LLM | Qwen (API) |
| 搜索 | SerpAPI, Tavily |

### 1.3 现有功能模块

| 模块 | 功能 |
|------|------|
| 产品搜索 | 多平台搜索 (Google Shopping, Amazon, eBay) |
| 价格获取 | 获取各平台价格 |
| 评论摘要 | 汇总用户评论 |
| 货币转换 | 多币种转换 |
| 实时搜索 | Tavily 实时信息 |
| 购买推荐 | 基于分析生成推荐报告 |

---

## 2. 迁移目标架构

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Chat UI   │  │   Sidebar   │  │   History   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Agent API  │  │  Session    │  │   Health    │              │
│  │  (Streaming)│  │  Management │  │   Check     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LangGraph Agent Engine                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Nodes     │  │   Tools     │  │  Checkpointer│             │
│  │ (ReAct)     │  │ (search/etc)│  │  (MongoDB)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 项目目录结构

```
sales-agent/
├── frontend/                          # React 前端 (新建)
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatTimeline.tsx
│   │   │   │   └── index.ts
│   │   │   ├── Sidebar/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── SessionList.tsx
│   │   │   │   └── index.ts
│   │   │   ├── Hero/
│   │   │   │   ├── Hero.tsx
│   │   │   │   └── index.ts
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── Loading.tsx
│   │   │       └── index.ts
│   │   ├── hooks/
│   │   │   ├── useChat.ts           # 聊天 Hook
│   │   │   ├── useSession.ts        # 会话管理 Hook
│   │   │   └── useStreaming.ts      # 流式响应 Hook
│   │   ├── services/
│   │   │   ├── api.ts               # API 客户端
│   │   │   └── websocket.ts          # WebSocket 客户端
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript 类型
│   │   ├── styles/
│   │   │   └── global.css           # 全局样式
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── index.html
│
├── backend/                           # FastAPI 后端 (重构)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置管理
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── chat.py           # 聊天 API
│   │   │   │   ├── session.py        # 会话管理 API
│   │   │   │   └── health.py         # 健康检查 API
│   │   │   └── dependencies.py       # API 依赖
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py     # Agent 服务封装
│   │   │   └── session_service.py    # 会话服务
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── request.py            # 请求模型
│   │       └── response.py           # 响应模型
│   │
│   ├── agent/                        # 移动自项目根目录
│   │   ├── __init__.py
│   │   ├── agent_core.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── graph.py
│   │   ├── prompt.py
│   │   ├── compressed_checkpointer.py
│   │   ├── memory_manager.py
│   │   ├── factory.py
│   │   └── registry.py
│   │
│   ├── tools/                       # 移动自项目根目录
│   │   ├── __init__.py
│   │   ├── search_tool.py
│   │   ├── price_tool.py
│   │   ├── review_tool.py
│   │   ├── currency_exchange_tool.py
│   │   └── tavily_tool.py
│   │
│   ├── utils/                       # 移动自项目根目录
│   │   └── db.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── test/                            # 测试 (保持或迁移)
│   └── ...
│
├── README.md
├── requirements.txt                 # 旧版 Streamlit 依赖 (可删除)
└── CLAUDE.md
```

---

## 3. 迁移方案详解

### 3.1 后端 FastAPI 设计

#### 3.1.1 API 端点设计

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/chat/stream` | 流式聊天 (SSE) |
| POST | `/api/chat/stop` | 停止生成 |
| GET | `/api/session/{session_id}` | 获取会话 |
| POST | `/api/session` | 创建会话 |
| DELETE | `/api/session/{session_id}` | 删除会话 |
| GET | `/api/sessions` | 列出所有会话 |
| GET | `/api/health` | 健康检查 |

#### 3.1.2 流式响应实现

```python
# backend/app/api/routes/chat.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.models.request import ChatRequest
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    async def event_generator():
        async for kind, data in agent_service.stream(request.message, request.session_id):
            if kind == "token":
                yield f"data: {json.dumps({'type': 'token', 'content': data})}\n\n"
            elif kind == "tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': data})}\n\n"
            # ...

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

#### 3.1.3 CORS 配置

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.2 前端 React 设计

#### 3.2.1 技术栈

| 类别 | 技术选择 |
|------|----------|
| 框架 | React 18 + TypeScript |
| 构建 | Vite |
| 状态管理 | React Context + useReducer |
| 样式 | CSS Modules / Styled Components |
| HTTP | Axios |
| 流式 | EventSource / WebSocket |
| UI组件 | 自建 (保持现有设计语言) |

#### 3.2.2 核心 Hook 设计

```typescript
// frontend/src/hooks/useChat.ts
import { useState, useCallback, useRef } from 'react';
import { api } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  steps?: ToolStep[];
}

export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    setIsGenerating(true);
    abortControllerRef.current = new AbortController();

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content }]);

    // 添加占位消息
    setMessages(prev => [...prev, { role: 'assistant', content: '', steps: [] }]);

    try {
      const response = await api.streamChat({
        message: content,
        session_id: sessionId,
      }, abortControllerRef.current.signal);

      // 处理流式响应
      for await (const event of response) {
        // 更新消息状态
      }
    } finally {
      setIsGenerating(false);
    }
  }, [sessionId]);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  return { messages, sendMessage, stopGeneration, isGenerating };
}
```

#### 3.2.3 样式迁移

现有 `assets/style.css` 需要转换为 React 兼容的 CSS 模块或 Styled Components。

### 3.3 状态迁移

#### 3.3.1 SharedState 适配

现有的 `SharedState` 需要序列化为 JSON 通过 API 传输：

```python
# backend/app/models/response.py
from pydantic import BaseModel
from typing import Optional, Any

class ChatResponse(BaseModel):
    kind: str  # "token" | "tool_start" | "tool_end" | "error" | "token_usage"
    data: Any
    session_id: str
```

---

## 4. 实施步骤

### 4.1 阶段一：后端搭建 (第 1-3 天)

| 任务 | 描述 | 预估工时 |
|------|------|----------|
| 4.1.1 | 创建 `backend/` 目录结构 | 0.5h |
| 4.1.2 | 迁移 `agent/` 模块到 backend | 2h |
| 4.1.3 | 迁移 `tools/` 模块到 backend | 1h |
| 4.1.4 | 迁移 `utils/` 模块到 backend | 0.5h |
| 4.1.5 | 创建 FastAPI 基础框架 | 1h |
| 4.1.6 | 实现健康检查 API | 0.5h |
| 4.1.7 | 实现会话管理 API | 2h |
| 4.1.8 | 实现流式聊天 API | 3h |
| 4.1.9 | 添加 CORS 配置 | 0.5h |
| 4.1.10 | 配置环境变量 | 0.5h |

**里程碑**: 后端可独立启动，所有 Agent 功能通过 API 可访问

### 4.2 阶段二：前端搭建 (第 4-7 天)

| 任务 | 描述 | 预估工时 |
|------|------|----------|
| 4.2.1 | 初始化 React + Vite 项目 | 1h |
| 4.2.2 | 配置 TypeScript | 0.5h |
| 4.2.3 | 创建 API 客户端 | 1h |
| 4.2.4 | 实现 Chat 组件 | 3h |
| 4.2.5 | 实现 Sidebar 组件 | 2h |
| 4.2.6 | 实现 Hero 区域 | 1h |
| 4.2.7 | 迁移样式 (CSS Modules) | 2h |
| 4.2.8 | 实现流式响应处理 | 2h |
| 4.2.9 | 实现会话管理 | 2h |

**里程碑**: 前端可连接后端，基本聊天功能可用

### 4.3 阶段三：功能完善 (第 8-10 天)

| 任务 | 描述 | 预估工时 |
|------|------|----------|
| 4.3.1 | 完善错误处理 | 1h |
| 4.3.2 | 添加加载状态 | 1h |
| 4.3.3 | 优化 UI 交互 | 2h |
| 4.3.4 | 添加 Token 统计显示 | 1h |
| 4.3.5 | 完善会话列表 | 1h |
| 4.3.6 | 添加停止生成功能 | 1h |
| 4.3.7 | 响应式布局适配 | 2h |

**里程碑**: 功能完整，用户体验接近旧版

### 4.4 阶段四：测试与部署 (第 11-12 天)

| 任务 | 描述 | 预估工时 |
|------|------|----------|
| 4.4.1 | 编写后端单元测试 | 2h |
| 4.4.2 | 编写前端组件测试 | 2h |
| 4.4.3 | E2E 测试 | 2h |
| 4.4.4 | 性能优化 | 2h |
| 4.4.5 | 文档更新 | 1h |
| 4.4.6 | 部署配置 | 1h |

---

## 5. 关键决策点

### 5.1 通信协议选择

| 方案 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| SSE (Server-Sent Events) | 简单，单向流 | 仅服务端→客户端 | **推荐** |
| WebSocket | 双向通信 | 复杂度高 | 未来扩展 |
| Polling | 简单 | 延迟高，资源浪费 | 不推荐 |

**决策**: 优先使用 SSE，后续需要双向通信时再迁移到 WebSocket

### 5.2 状态管理策略

| 方案 | 适用场景 | 推荐 |
|------|----------|------|
| React Context | 中小规模 | **推荐** |
| Redux | 大规模 | 过度 |
| Zustand | 中等规模 | 可选 |

**决策**: 使用 React Context + useReducer，复杂度可控

### 5.3 样式方案

| 方案 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| CSS Modules | 原生支持，简单 | 无运行时开销 | **推荐** |
| Styled Components | 灵活 | 运行时开销 | 可选 |
| Tailwind CSS | 快速开发 | 学习曲线 | 不推荐 |

**决策**: CSS Modules，保持与现有 CSS 的兼容性

---

## 6. 兼容性考虑

### 6.1 环境变量统一

| 旧变量 | 新变量 | 说明 |
|--------|--------|------|
| `api_key` | `LLM_API_KEY` | LLM API 密钥 |
| `base_url` | `LLM_BASE_URL` | LLM API 地址 |
| `QWEN_MODEL_ID` | `LLM_MODEL_ID` | 模型 ID |
| `SERPAPI_API_KEY` | `SERPAPI_API_KEY` | 搜索 API |
| `TAVILY_API_KEY` | `TAVILY_API_KEY` | 实时搜索 API |
| `MONGO_URI` | `MONGO_URI` | MongoDB 连接 |



---

## 附录：文件对照表

| 原路径 | 新路径 (后端) | 新路径 (前端) |
|--------|---------------|---------------|
| `main.py` | `backend/app/main.py` | - |
| `config.py` | `backend/app/config.py` | - |
| `agent/*` | `backend/agent/*` | - |
| `tools/*` | `backend/tools/*` | - |
| `utils/db.py` | `backend/utils/db.py` | - |
| `ui/chat.py` | - | `frontend/src/components/Chat/*` |
| `ui/sidebar.py` | - | `frontend/src/components/Sidebar/*` |
| `assets/style.css` | - | `frontend/src/styles/global.css` |
