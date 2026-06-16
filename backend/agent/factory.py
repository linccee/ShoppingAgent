"""Agent factory functions - Create ReAct agent instances via registry."""
from typing import Generator

from backend.agent.config_types import AgentType
from backend.agent.registry import AgentRegistry

from backend.agent.agent_core import (
    run_agent as _run_react_agent,
    stream_agent as _stream_react_agent,
)


def create_shopping_agent(agent_type: AgentType = "shopping") -> any:
    """
    创建 ReAct Agent 实例。

    Args:
        agent_type: Agent 类型 (当前支持 "shopping")

    Returns:
        LangGraph ReAct Agent 执行器
    """
    return _create_react_agent(agent_type)


def _create_react_agent(agent_type: AgentType):
    """使用 create_react_agent 创建 Agent。"""
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage

    from backend.agent.agent_core import _get_memory_saver

    registry = AgentRegistry.get_instance()
    config = registry.get_config(agent_type)
    tools = registry.get_tools(agent_type)
    llm = registry.create_llm(agent_type)

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SystemMessage(content=config["system_prompt"]),
        checkpointer=_get_memory_saver(),
    )


def run_agent(
    agent_executor,
    user_input: str,
    session_id: str = "default",
) -> dict:
    """
    执行 Agent，返回结果字典。

    Returns:
        {
            'output': '最终推荐报告',
            'steps': [{'tool': ..., 'input': ..., 'output': ...}]
        }
    """
    return _run_react_agent(agent_executor, user_input, session_id)


def stream_agent(
    agent_executor,
    user_input: str,
    session_id: str = "default",
) -> Generator:
    """
    流式执行 Agent，产出事件元组。

    Yields:
        (kind, data) 元组:
            - ("token", str): LLM 输出 token
            - ("tool_start", dict): {tool, input, output}
            - ("tool_end", str): 截断的工具输出
            - ("token_usage", dict): token 用量统计
            - ("error", str): 异常消息
    """
    return _stream_react_agent(agent_executor, user_input, session_id)
