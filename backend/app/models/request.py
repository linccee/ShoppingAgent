"""Request models for the FastAPI backend."""
from pydantic import BaseModel, Field


class ChatStreamRequest(BaseModel):
    """Streaming chat request."""

    message: str = Field(..., min_length=1)
    session_id: str | None = None


class StopChatRequest(BaseModel):
    """Stop-generation request."""

    session_id: str = Field(..., min_length=1)
