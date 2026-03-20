"""Chat streaming routes with authentication."""
from __future__ import annotations

import json
from typing import Annotated, Generator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from backend.app.api.dependencies import get_agent_service
from backend.app.core.deps import get_current_user
from backend.app.models.request import ChatStreamRequest, StopChatRequest
from backend.app.models.response import StopChatResponse
from backend.app.services.agent_service import AgentService
from backend.app.utils.logging_config import chat_logger

router = APIRouter(prefix="/chat", tags=["chat"])


def _encode_sse(event_type: str, data: object, session_id: str) -> str:
    payload = {
        "type": event_type,
        "data": data,
        "session_id": session_id,
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/stream")
def stream_chat(
    request: ChatStreamRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    agent_service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """Stream chat events as SSE (requires authentication)."""
    chat_logger.info(f"[CHAT] User {current_user.get('username')} starting chat stream, session_id={request.session_id}")

    def event_generator() -> Generator[str, None, None]:
        current_session_id = request.session_id or ""
        try:
            for event_type, data in agent_service.stream(request.message, request.session_id):
                if event_type == "session":
                    current_session_id = data["session_id"]
                    chat_logger.info(f"[CHAT] Session established: {current_session_id}")
                yield _encode_sse(event_type, data, current_session_id)
        except Exception as e:
            chat_logger.error(f"[CHAT] Stream error: {e}")
            yield _encode_sse("error", str(e), current_session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/stop",
    response_model=StopChatResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def stop_chat(
    request: StopChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    agent_service: AgentService = Depends(get_agent_service),
) -> StopChatResponse:
    """Request cancellation for a running generation (requires authentication)."""
    chat_logger.info(f"[CHAT] User {current_user.get('username')} requesting stop for session {request.session_id}")
    accepted = agent_service.stop(request.session_id)
    if accepted:
        chat_logger.info(f"[CHAT] Stop request accepted for session {request.session_id}")
    else:
        chat_logger.warning(f"[CHAT] Stop request rejected for session {request.session_id}")
    return StopChatResponse(accepted=accepted, session_id=request.session_id)
