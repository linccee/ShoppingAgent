"""Session routes with user isolation."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.api.dependencies import get_session_service
from backend.app.core.deps import get_current_user
from backend.app.models.response import (
    SessionCreateResponse,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from backend.app.services.session_service import SessionService
from backend.app.utils.logging_config import session_logger

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session_route(
    current_user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
) -> SessionCreateResponse:
    """Create a session for the current user."""
    session_logger.info(f"[SESSION] User {current_user.get('username')} creating new session")
    session_id = session_service.create(user_id=current_user["id"])
    session_logger.info(f"[SESSION] Session created: {session_id} for user {current_user.get('username')}")
    return SessionCreateResponse(session_id=session_id)


@router.get("", response_model=list[SessionSummaryResponse])
def list_sessions(
    current_user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
) -> list[SessionSummaryResponse]:
    """List sessions for the current user only."""
    session_logger.info(f"[SESSION] User {current_user.get('username')} listing sessions")
    sessions = session_service.list_by_user(current_user["id"])
    session_logger.info(f"[SESSION] Found {len(sessions)} sessions for user {current_user.get('username')}")
    return sessions


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_route(
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
) -> SessionDetailResponse:
    """Fetch a single session belonging to the current user."""
    session_logger.info(f"[SESSION] User {current_user.get('username')} getting session {session_id}")
    session = session_service.get_for_user(session_id, current_user["id"])
    if not session.messages and session.created_at is None:
        session_logger.warning(f"[SESSION] Session {session_id} not found for user {current_user.get('username')}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_route(
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
) -> Response:
    """Delete a session belonging to the current user."""
    session_logger.info(f"[SESSION] User {current_user.get('username')} deleting session {session_id}")
    deleted = session_service.delete_for_user(session_id, current_user["id"])
    if not deleted:
        session_logger.warning(f"[SESSION] Session {session_id} not found for deletion by user {current_user.get('username')}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session_logger.info(f"[SESSION] Session {session_id} deleted by user {current_user.get('username')}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
