"""
Agent module - Multi-agent architecture with registry support.

This module provides:
    - AgentRegistry: Singleton registry for managing agent configurations
    - Factory functions: create_shopping_agent, run_agent, stream_agent
"""

from backend.agent.config_types import (
    AgentConfig,
    AgentType,
    LLMConfig,
    ToolDefinition,
    DEFAULT_AGENT_TYPE,
)
from backend.agent.registry import AgentRegistry
from backend.agent.factory import (
    create_shopping_agent,
    run_agent,
    stream_agent,
)

from backend.agent.agent_core import (
    create_shopping_agent as _legacy_create_shopping_agent,
    run_agent as _legacy_run_agent,
    stream_agent as _legacy_stream_agent,
)

__all__ = [
    "AgentConfig",
    "AgentType",
    "LLMConfig",
    "ToolDefinition",
    "DEFAULT_AGENT_TYPE",
    "AgentRegistry",
    "create_shopping_agent",
    "run_agent",
    "stream_agent",
    "_legacy_create_shopping_agent",
    "_legacy_run_agent",
    "_legacy_stream_agent",
]
