# 镜澜导购 · Sales Agent

> 智能多平台购物决策助手 — 连接 Google Shopping、Amazon 与 eBay，一轮对话完成比价、评论归纳与购买建议。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-red.svg)](https://streamlit.io/)
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

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         UI 层                               │
│                    Streamlit 前端                           │
│               (玻璃态设计 + 流式输出 + 时间线追踪)            │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Agent 层                                │
│                   LangGraph ReAct Agent                      │
│            (MongoDBSaver 持久化 Checkpointer)                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      工具层                                  │
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

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```bash
# 主模型 (支持 OpenAI 兼容 API)
api_key=your_api_key
base_url=your_api_base_url
QWEN_MODEL_ID=your_model_id

# 搜索服务
SERPAPI_API_KEY=your_serpapi_key      # https://serpapi.com/
TAVILY_API_KEY=your_tavily_key        # https://tavily.com/

# MongoDB (用于会话记忆持久化)
MONGO_URI=mongodb://localhost:27017

# 汇率 API (可选)
EXCHANGE_RATE_API_KEY=your_exchange_rate_key
```

### 启动

```bash
streamlit run main.py
```

应用默认运行在 `http://localhost:8501`

## 项目结构

```
1-agent/
├── main.py                 # Streamlit 入口
├── config.py               # 配置管理
├── agent/
│   ├── agent_core.py       # Agent 工厂与流式执行器
│   ├── state.py            # SharedState TypedDict
│   ├── graph.py            # StateGraph 构建器
│   ├── nodes.py            # 状态节点实现
│   ├── prompt.py           # System Prompt
│   ├── memory_manager.py   # 记忆管理器
│   ├── compressed_checkpointer.py  # 记忆压缩检查点
│   └── ...
├── tools/
│   ├── search_tool.py      # 商品搜索 (SerpAPI)
│   ├── price_tool.py       # 实时价格
│   ├── review_tool.py      # 评论分析
│   ├── currency_exchange_tool.py  # 汇率转换
│   └── tavily_tool.py      # 网页搜索与信息提取
├── ui/
│   ├── chat.py             # 聊天组件
│   ├── sidebar.py          # 侧边栏
│   └── stop_injection.py   # 停止按钮注入
├── utils/
│   └── db.py               # MongoDB 会话管理
├── test/                   # 单元测试
└── assets/
    └── style.css           # 自定义样式
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
| 前端 | Streamlit 1.55, Custom CSS |
| Agent | LangGraph 1.1, LangChain Core |
| 记忆 | MongoDB + LangGraph Checkpointer |
| 搜索 | SerpAPI, Tavily API |
| LLM | OpenAI 兼容 API (默认 Qwen) |

## License

MIT
