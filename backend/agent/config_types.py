"""Agent configuration types for the registry system."""
from typing import TypedDict, Callable, NotRequired, Literal
from langgraph.checkpoint.base import BaseCheckpointSaver


class LLMConfig(TypedDict):
    """LLM configuration for an agent."""
    model: str
    api_key: str
    base_url: str
    temperature: float
    max_tokens: int
    streaming: bool


class ToolDefinition(TypedDict):
    """Tool definition for agent registration."""
    name: str
    func: Callable  # The tool function reference
    description: str


class AgentConfig(TypedDict):
    """Agent configuration."""
    name: str
    description: str
    tools: list[ToolDefinition]
    system_prompt: str
    llm_config: LLMConfig
    max_iterations: int
    enable_memory: bool
    checkpointer: NotRequired[BaseCheckpointSaver]


# Agent type literals for type safety
AgentType = Literal["shopping", "research", "comparison", "qa", "custom"]

# Default agent type
DEFAULT_AGENT_TYPE: AgentType = "shopping"
