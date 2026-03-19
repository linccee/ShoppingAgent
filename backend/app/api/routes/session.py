"""Session routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.api.dependencies import get_session_service
from backend.app.models.response import (
    SessionCreateResponse,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from backend.app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session_route(
    session_service: SessionService = Depends(get_session_service),
) -> SessionCreateResponse:
    """Create a session."""
    session_id = session_service.create()
    return SessionCreateResponse(session_id=session_id)


@router.get("", response_model=list[SessionSummaryResponse])
def list_sessions(
    session_service: SessionService = Depends(get_session_service),
) -> list[SessionSummaryResponse]:
    """List sessions."""
    return session_service.list()


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_route(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> SessionDetailResponse:
    """Fetch a single session."""
    session = session_service.get(session_id)
    if not session.messages and session.created_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_route(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> Response:
    """Delete a session."""
    deleted = session_service.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
