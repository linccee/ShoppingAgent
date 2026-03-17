"""
Agent module - Multi-agent architecture with registry and StateGraph support.

This module provides:
    - AgentRegistry: Singleton registry for managing agent configurations
    - Factory functions: create_shopping_agent, run_agent, stream_agent
    - StateGraph: Multi-node workflow with parallel execution support
    - SharedState: Typed state definition for workflow nodes
"""

# Configuration types
from agent.config_types import (
    AgentConfig,
    AgentType,
    LLMConfig,
    ToolDefinition,
    DEFAULT_AGENT_TYPE,
)

# State definitions
from agent.state import (
    SharedState,
    SearchResult,
    PriceInfo,
    ReviewAnalysis,
    Recommendation,
    WorkflowStep,
)

# Registry and factory
from agent.registry import AgentRegistry
from agent.factory import (
    create_shopping_agent,
    run_agent,
    stream_agent,
)

# StateGraph
from agent.graph import StateGraphBuilder

# Node functions (for custom workflows)
from agent.nodes import (
    input_node,
    search_node,
    price_node,
    review_node,
    currency_node,
    recommend_node,
    output_node,
)

# Legacy exports (backward compatibility)
from agent.agent_core import (
    create_shopping_agent as _legacy_create_shopping_agent,
    run_agent as _legacy_run_agent,
    stream_agent as _legacy_stream_agent,
)

__all__ = [
    # Configuration
    "AgentConfig",
    "AgentType",
    "LLMConfig",
    "ToolDefinition",
    "DEFAULT_AGENT_TYPE",
    # State
    "SharedState",
    "SearchResult",
    "PriceInfo",
    "ReviewAnalysis",
    "Recommendation",
    "WorkflowStep",
    # Registry and factory
    "AgentRegistry",
    "create_shopping_agent",
    "run_agent",
    "stream_agent",
    # StateGraph
    "StateGraphBuilder",
    # Nodes
    "input_node",
    "search_node",
    "price_node",
    "review_node",
    "currency_node",
    "recommend_node",
    "output_node",
    # Legacy (for backward compatibility)
    "_legacy_create_shopping_agent",
    "_legacy_run_agent",
    "_legacy_stream_agent",
]
