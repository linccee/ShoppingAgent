"""StateGraph builder for multi-agent workflows."""
from typing import Callable

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.agent.state import SharedState
from backend.agent.nodes import (
    input_node,
    search_node,
    price_node,
    review_node,
    currency_node,
    recommend_node,
    output_node,
)


class StateGraphBuilder:
    """
    StateGraph 构建器 - 支持灵活的工作流编排。

    设计特点:
        1. 支持并行执行独立节点
        2. 支持流式输出
        3. 保留会话记忆功能
        4. 可配置的节点执行顺序
    """

    def __init__(self, checkpointer: BaseCheckpointSaver | None = None):
        self._graph = StateGraph(SharedState)
        self._checkpointer = checkpointer
        self._nodes: dict[str, Callable] = {}

    def add_node(self, name: str, func: Callable) -> "StateGraphBuilder":
        """添加节点"""
        self._nodes[name] = func
        self._graph.add_node(name, func)
        return self

    def add_edge(self, from_node: str, to_node: str) -> "StateGraphBuilder":
        """添加边 (串行)"""
        self._graph.add_edge(from_node, to_node)
        return self

    def add_parallel(self, from_node: str, to_nodes: list[str]) -> "StateGraphBuilder":
        """
        添加并行边 - 从一个节点分叉到多个节点。

        Args:
            from_node: 源节点
            to_nodes: 目标节点列表
        """
        for to_node in to_nodes:
            self._graph.add_edge(from_node, to_node)
        return self

    def set_entry(self, node: str) -> "StateGraphBuilder":
        """设置入口节点"""
        self._graph.set_entry_point(node)
        return self

    def set_finish(self, node: str) -> "StateGraphBuilder":
        """设置结束节点"""
        self._graph.set_finish_point(node)
        return self

    def build(self, name: str = "agent_graph") -> "CompiledGraph":
        """
        构建并编译 StateGraph。

        Returns:
            可执行的 StateGraph 实例
        """
        compiled = self._graph.compile(
            checkpointer=self._checkpointer,
            store=None,
        )

        return compiled

    @staticmethod
    def create_default_graph(
        checkpointer: BaseCheckpointSaver | None = None,
        enable_parallel: bool = True,
    ) -> "CompiledGraph":
        """
        创建默认的购物 Agent StateGraph。

        工作流:
            input → search → ┬→ price ─┐
                            ├→ review ─┼→ recommend → output
                            └→ currency─┘

        Args:
            checkpointer: 状态持久化检查点
            enable_parallel: 是否启用并行执行

        Returns:
            编译后的 StateGraph
        """
        builder = StateGraphBuilder(checkpointer)

        # 添加所有节点
        builder.add_node("input", input_node)
        builder.add_node("search", search_node)
        builder.add_node("price", price_node)
        builder.add_node("review", review_node)
        builder.add_node("currency", currency_node)
        builder.add_node("recommend", recommend_node)
        builder.add_node("output", output_node)

        # 设置入口
        builder.set_entry("input")

        # 构建工作流边
        builder.add_edge("input", "search")

        if enable_parallel:
            # 并行执行 price, review, currency
            builder.add_parallel("search", ["price", "review", "currency"])

            # 汇聚到 recommend
            builder.add_edge("price", "recommend")
            builder.add_edge("review", "recommend")
            builder.add_edge("currency", "recommend")
        else:
            # 串行执行
            builder.add_edge("search", "price")
            builder.add_edge("price", "recommend")

        builder.add_edge("recommend", "output")

        # 设置结束
        builder.set_finish("output")

        return builder.build("shopping_graph")

    @staticmethod
    def create_simple_graph(
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> "CompiledGraph":
        """
        创建简化版购物 Agent StateGraph (串行执行)。

        工作流:
            input → search → price → recommend → output

        Returns:
            编译后的 StateGraph
        """
        builder = StateGraphBuilder(checkpointer)

        # 添加节点
        builder.add_node("input", input_node)
        builder.add_node("search", search_node)
        builder.add_node("price", price_node)
        builder.add_node("recommend", recommend_node)
        builder.add_node("output", output_node)

        # 设置入口
        builder.set_entry("input")

        # 串行边
        builder.add_edge("input", "search")
        builder.add_edge("search", "price")
        builder.add_edge("price", "recommend")
        builder.add_edge("recommend", "output")

        # 设置结束
        builder.set_finish("output")

        return builder.build("simple_shopping_graph")
