"""Response models for the FastAPI backend."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SessionCreateResponse(BaseModel):
    """Created session payload."""

    session_id: str


class SessionSummaryResponse(BaseModel):
    """Session summary payload."""

    session_id: str
    title: str
    updated_at: datetime | None = None
    created_at: datetime | None = None


class SessionDetailResponse(BaseModel):
    """Full session payload."""

    session_id: str
    title: str
    messages: list[dict[str, Any]]
    input_tokens: int
    output_tokens: int
    updated_at: datetime | None = None
    created_at: datetime | None = None


class StopChatResponse(BaseModel):
    """Stop-generation response."""

    accepted: bool
    session_id: str


class HealthResponse(BaseModel):
    """Health response payload."""

    status: str
    mongo: str
