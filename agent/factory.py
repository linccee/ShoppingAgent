"""Agent factory functions - Create agent instances with different architectures."""
from typing import Generator

from agent.config_types import AgentType
from agent.registry import AgentRegistry
from agent.state import SharedState


# 导出 agent_core 中的原始函数用于兼容
from agent.agent_core import (
    run_agent as _run_react_agent,
    stream_agent as _stream_react_agent,
)


def create_shopping_agent(
    agent_type: AgentType = "shopping",
    use_stategraph: bool = False,
) -> any:
    """
    创建 Agent 实例 (向后兼容的工厂函数)。

    Args:
        agent_type: Agent 类型 (当前支持 "shopping")
        use_stategraph: 是否使用新的 StateGraph 架构

    Returns:
        Agent 执行器 (ReAct Agent 或 StateGraph)

    Example:
        # 使用默认 ReAct Agent (保持现有行为)
        agent = create_shopping_agent()

        # 指定类型
        agent = create_shopping_agent(agent_type="shopping")

        # 使用 StateGraph 架构
        agent = create_shopping_agent(use_stategraph=True)
    """
    if use_stategraph:
        return _create_stategraph_agent(agent_type)
    else:
        return _create_react_agent(agent_type)


def _create_react_agent(agent_type: AgentType):
    """
    使用 create_react_agent 创建 Agent (保持现有实现)。
    """
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage

    from agent.agent_core import _get_memory_saver

    registry = AgentRegistry.get_instance()

    # 获取配置
    config = registry.get_config(agent_type)
    tools = registry.get_tools(agent_type)

    # 创建 LLM
    llm = registry.create_llm(agent_type)

    # 创建 Agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SystemMessage(content=config["system_prompt"]),
        checkpointer=_get_memory_saver(),
    )

    return agent


def _create_stategraph_agent(agent_type: AgentType):
    """
    使用 StateGraph 架构创建 Agent。
    """
    from agent.graph import StateGraphBuilder
    from agent.compressed_checkpointer import CompressedCheckpointer
    from langgraph.checkpoint.mongodb import MongoDBSaver
    from utils.db import client

    # 创建 checkpointer
    checkpointer = CompressedCheckpointer(MongoDBSaver(client))

    # 构建 StateGraph
    graph = StateGraphBuilder.create_default_graph(
        checkpointer=checkpointer,
        enable_parallel=True,
    )

    return graph


def run_agent(
    agent_executor,
    user_input: str,
    session_id: str = "default",
    use_stategraph: bool = False,
) -> dict:
    """
    执行 Agent，返回结果字典。

    Args:
        agent_executor: Agent 实例 (来自 create_shopping_agent)
        user_input: 用户输入
        session_id: 会话 ID
        use_stategraph: 是否使用 StateGraph 架构

    Returns:
        {
            'output': '最终推荐报告',
            'steps': [{'tool': ..., 'input': ..., 'output': ...}]
        }
    """
    if use_stategraph:
        return _run_stategraph_agent(agent_executor, user_input, session_id)
    else:
        return _run_react_agent(agent_executor, user_input, session_id)


def _run_stategraph_agent(
    graph,
    user_input: str,
    session_id: str,
) -> dict:
    """执行 StateGraph Agent"""
    config = {"configurable": {"thread_id": session_id}}

    initial_state: SharedState = {
        "user_query": user_input,
        "session_id": session_id,
        "messages": [],
    }

    result = graph.invoke(initial_state, config=config)

    return {
        "output": result.get("final_response", ""),
        "steps": result.get("steps", []),
    }


def stream_agent(
    agent_executor,
    user_input: str,
    session_id: str = "default",
    use_stategraph: bool = False,
) -> Generator:
    """
    流式执行 Agent，产出事件元组。

    Args:
        agent_executor: Agent 实例
        user_input: 用户输入
        session_id: 会话 ID
        use_stategraph: 是否使用 StateGraph 架构

    Yields:
        (kind, data) 元组:
            - ("token", str): LLM 输出 token
            - ("tool_start", dict): {tool, input, output}
            - ("tool_end", str): 截断的工具输出
            - ("token_usage", dict): token 用量统计
            - ("error", str): 异常消息
    """
    if use_stategraph:
        return _stream_stategraph_agent(agent_executor, user_input, session_id)
    else:
        return _stream_react_agent(agent_executor, user_input, session_id)


async def _stream_stategraph_agent(graph, user_input: str, session_id: str):
    """
    流式执行 StateGraph Agent。

    注意: 这是一个异步生成器，需要使用 async for 迭代。
    """
    import asyncio
    from langchain_core.messages import HumanMessage

    config = {"configurable": {"thread_id": session_id}}

    initial_state: SharedState = {
        "user_query": user_input,
        "session_id": session_id,
        "messages": [HumanMessage(content=user_input)],
    }

    async for event in graph.astream(initial_state, config=config):
        for node_name, node_output in event.items():
            yield ("node_event", {"node": node_name, "output": node_output})
