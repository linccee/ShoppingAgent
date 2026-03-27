"""Session service wrapping MongoDB access with user isolation."""
from __future__ import annotations

from backend.app.models.response import SessionDetailResponse, SessionSummaryResponse
from backend.utils.db import (
    create_session,
    delete_session,
    get_all_sessions,
    load_session,
    save_session,
    sessions_col,
)
from backend.app.utils.logging_config import session_logger


class SessionService:
    """Service layer for session CRUD with user isolation."""

    def create(self, session_id: str | None = None, user_id: str | None = None) -> str:
        """Create and persist a session for a user."""
        session_logger.info(f"[SESSION] Creating session, session_id={session_id}, user_id={user_id}")
        result = create_session(session_id, user_id)
        session_logger.info(f"[SESSION] Session created: {result}")
        return result

    def get(self, session_id: str) -> SessionDetailResponse:
        """Fetch a single session."""
        session_logger.debug(f"[SESSION] Getting session {session_id}")
        session = load_session(session_id)
        return SessionDetailResponse(**session)

    def get_for_user(self, session_id: str, user_id: str) -> SessionDetailResponse:
        """Fetch a single session belonging to a user."""
        session_logger.debug(f"[SESSION] Getting session {session_id} for user {user_id}")
        session = load_session(session_id)
        # Verify ownership
        if session.get("user_id") != user_id:
            session_logger.warning(f"[SESSION] Session {session_id} access denied for user {user_id}")
            # Return empty session to trigger 404
            return SessionDetailResponse(
                session_id=session_id,
                title="新的对话",
                messages=[],
                input_tokens=0,
                output_tokens=0,
                updated_at=None,
                created_at=None,
            )
        return SessionDetailResponse(**session)

    def list(self) -> list[SessionSummaryResponse]:
        """List sessions sorted by last update (legacy, no user filter)."""
        session_logger.debug("[SESSION] Listing all sessions")
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

    def list_by_user(self, user_id: str) -> list[SessionSummaryResponse]:
        """List sessions for a specific user only."""
        session_logger.debug(f"[SESSION] Listing sessions for user {user_id}")
        cursor = sessions_col.find(
            {"user_id": user_id},
            {"session_id": 1, "title": 1, "updated_at": 1, "created_at": 1},
        ).sort("updated_at", -1)

        sessions = [
            SessionSummaryResponse(
                session_id=session["session_id"],
                title=session.get("title", "新的对话"),
                updated_at=session.get("updated_at"),
                created_at=session.get("created_at"),
            )
            for session in cursor
        ]
        session_logger.debug(f"[SESSION] Found {len(sessions)} sessions for user {user_id}")
        return sessions

    def save(
        self,
        session_id: str,
        messages: list[dict],
        input_tokens: int,
        output_tokens: int,
    ) -> str:
        """Persist a full session snapshot."""
        session_logger.debug(f"[SESSION] Saving session {session_id}")
        return save_session(
            session_id=session_id,
            messages=messages,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def delete(self, session_id: str) -> bool:
        """Delete a session (legacy, no user filter)."""
        session_logger.info(f"[SESSION] Deleting session {session_id}")
        return delete_session(session_id)

    def delete_for_user(self, session_id: str, user_id: str) -> bool:
        """Delete a session belonging to a user."""
        session_logger.info(f"[SESSION] Deleting session {session_id} for user {user_id}")
        result = sessions_col.delete_one({
            "session_id": session_id,
            "user_id": user_id,
        })
        deleted = result.deleted_count > 0
        if deleted:
            session_logger.info(f"[SESSION] Session {session_id} deleted for user {user_id}")
        else:
            session_logger.warning(f"[SESSION] Session {session_id} not found for user {user_id}")
        return deleted
