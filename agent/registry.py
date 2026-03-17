"""Agent Registry - Singleton pattern for managing agent configurations."""
from typing import TypeVar, Callable

from agent.config_types import (
    AgentConfig,
    AgentType,
    ToolDefinition,
    LLMConfig,
    DEFAULT_AGENT_TYPE,
)
from config import Config


T = TypeVar('T')


class AgentRegistry:
    """
    Agent 注册表 - 单例模式，动态注册和管理 Agent 类型。

    支持功能:
        - 按 Agent 类型配置不同工具集
        - 按 Agent 类型配置不同 LLM 参数
        - 延迟加载工具，提高启动速度
        - 内置默认购物 Agent 配置

    使用示例:
        registry = AgentRegistry.get_instance()

        # 获取 Agent 配置
        config = registry.get_config("shopping")

        # 获取工具列表
        tools = registry.get_tools("shopping")

        # 创建 LLM 实例
        llm = registry.create_llm("shopping")

        # 列出所有已注册的 Agent 类型
        agent_types = registry.list_agent_types()
    """

    _instance: "AgentRegistry | None" = None

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._configs: dict[AgentType, AgentConfig] = {}
        self._tool_loaders: dict[str, Callable[[], list[ToolDefinition]]] = {}
        self._initialized = True

        # 注册默认工具加载器
        self._register_default_tool_loaders()

        # 注册默认 Agent 配置
        self._register_default_agents()

    def _register_default_tool_loaders(self) -> None:
        """注册默认工具加载器"""

        def load_shopping_tools() -> list[ToolDefinition]:
            from tools.search_tool import search_products
            from tools.price_tool import prices
            from tools.review_tool import analyze_reviews
            from tools.currency_exchange_tool import currency_exchange

            return [
                {
                    "name": "search_products",
                    "func": search_products,
                    "description": search_products.description,
                },
                {
                    "name": "prices",
                    "func": prices,
                    "description": prices.description,
                },
                {
                    "name": "analyze_reviews",
                    "func": analyze_reviews,
                    "description": analyze_reviews.description,
                },
                {
                    "name": "currency_exchange",
                    "func": currency_exchange,
                    "description": currency_exchange.description,
                },
            ]

        self._tool_loaders["shopping"] = load_shopping_tools

    def _register_default_agents(self) -> None:
        """注册默认 Agent 配置"""

        # 购物 Agent (默认)
        self._configs[DEFAULT_AGENT_TYPE] = {
            "name": "shopping",
            "description": "购物推荐 Agent - 帮助用户做出明智的购物决策",
            "tools": [],  # 延迟加载
            "system_prompt": self._get_shopping_prompt(),
            "llm_config": {
                "model": Config.MODEL,
                "api_key": Config.API_KEY,
                "base_url": Config.BASE_URL,
                "temperature": Config.TEMPERATURE,
                "max_tokens": Config.MAX_TOKENS,
                "streaming": True,
            },
            "max_iterations": Config.MAX_ITERATIONS,
            "enable_memory": True,
        }

    def _get_shopping_prompt(self) -> str:
        """获取购物 Agent 的系统提示词"""
        from agent.prompt import SYSTEM_PROMPT

        return SYSTEM_PROMPT

    # ---- Public API ----

    def register(
        self,
        agent_type: AgentType,
        config: AgentConfig,
        tool_loader_key: str | None = None,
    ) -> None:
        """
        注册新的 Agent 类型。

        Args:
            agent_type: Agent 类型标识
            config: Agent 配置
            tool_loader_key: 可选的工具加载器 key
        """
        if agent_type in self._configs:
            raise ValueError(f"Agent type '{agent_type}' already registered")

        self._configs[agent_type] = config

    def register_tool_loader(
        self,
        key: str,
        loader: Callable[[], list[ToolDefinition]],
    ) -> None:
        """
        注册工具加载器。

        Args:
            key: 加载器标识
            loader: 返回工具列表的函数
        """
        self._tool_loaders[key] = loader

    def get_config(self, agent_type: AgentType) -> AgentConfig:
        """获取 Agent 配置"""
        if agent_type not in self._configs:
            raise KeyError(f"Agent type '{agent_type}' not found")
        return self._configs[agent_type]

    def list_agent_types(self) -> list[AgentType]:
        """列出所有已注册的 Agent 类型"""
        return list(self._configs.keys())

    def get_tools(self, agent_type: AgentType) -> list:
        """获取指定 Agent 类型的工具列表"""
        config = self.get_config(agent_type)

        if config.get("tools"):
            return [t["func"] for t in config["tools"]]

        # 尝试使用工具加载器
        tool_loader = self._tool_loaders.get(agent_type)
        if tool_loader:
            return [t["func"] for t in tool_loader()]

        raise ValueError(f"No tools configured for agent type '{agent_type}'")

    def get_llm_config(self, agent_type: AgentType) -> LLMConfig:
        """获取 Agent 的 LLM 配置"""
        return self.get_config(agent_type)["llm_config"]

    def create_llm(self, agent_type: AgentType) -> "ChatOpenAI":
        """根据配置创建 LLM 实例"""
        from langchain_openai import ChatOpenAI

        llm_config = self.get_llm_config(agent_type)

        return ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            streaming=llm_config.get("streaming", True),
            stream_usage=True,
        )

    def get_system_prompt(self, agent_type: AgentType) -> str:
        """获取 Agent 的系统提示词"""
        return self.get_config(agent_type)["system_prompt"]

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        """获取单例实例"""
        return cls()
