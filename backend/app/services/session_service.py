"""Session service wrapping MongoDB access."""
from __future__ import annotations
from backend.app.models.response import SessionDetailResponse, SessionSummaryResponse
from backend.utils.db import (
    create_session,
    delete_session,
    get_all_sessions,
    load_session,
    save_session,
)


class SessionService:
    """Service layer for session CRUD."""

    def create(self, session_id: str | None = None) -> str:
        """Create and persist a session."""
        return create_session(session_id)

    def get(self, session_id: str) -> SessionDetailResponse:
        """Fetch a single session."""
        session = load_session(session_id)
        return SessionDetailResponse(**session)

    def list(self) -> list[SessionSummaryResponse]:
        """List sessions sorted by last update."""
        sessions = get_all_sessions()
        return [
            SessionSummaryResponse(
                session_id=session["session_id"],
                title=session.get("title", "新的对话"),
                updated_at=session.get("updated_at"),
                created_at=session.get("created_at"),
            )
            for session in sessions
        ]

    def save(
        self,
        session_id: str,
        messages: list[dict],
        input_tokens: int,
        output_tokens: int,
    ) -> str:
        """Persist a full session snapshot."""
        return save_session(
            session_id=session_id,
            messages=messages,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        return delete_session(session_id)
