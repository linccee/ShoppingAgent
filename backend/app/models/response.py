"""Response models for the FastAPI backend."""
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict


def _utc_datetime(v: datetime) -> str:
    """Serialize datetime as UTC ISO 8601 string.

    Handles both aware and naive datetimes:
    - Aware: strip existing tz and re-attach UTC (isoformat adds Z)
    - Naive: assume it's already UTC (legacy data), just isoformat
    """
    if v.tzinfo is None:
        # Naive datetime — assume UTC (legacy data from MongoDB)
        v = v.replace(tzinfo=timezone.utc)
    else:
        # Aware — convert to UTC
        v = v.astimezone(timezone.utc)
    return v.isoformat()


class SessionCreateResponse(BaseModel):
    """Created session payload."""

    session_id: str


class SessionSummaryResponse(BaseModel):
    """Session summary payload."""

    model_config = ConfigDict(
        json_encoders={datetime: _utc_datetime},
    )

    session_id: str
    title: str
    updated_at: datetime | None = None
    created_at: datetime | None = None


class SessionDetailResponse(BaseModel):
    """Full session payload."""

    model_config = ConfigDict(
        json_encoders={datetime: _utc_datetime},
    )

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
    model: str | None = None
    temperature: float
    max_tokens: int
    memory_turns: int
