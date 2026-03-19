"""Chat streaming routes."""
from __future__ import annotations

import json
from typing import Generator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from backend.app.api.dependencies import get_agent_service
from backend.app.models.request import ChatStreamRequest, StopChatRequest
from backend.app.models.response import StopChatResponse
from backend.app.services.agent_service import AgentService

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
    agent_service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """Stream chat events as SSE."""

    def event_generator() -> Generator[str, None, None]:
        current_session_id = request.session_id or ""
        for event_type, data in agent_service.stream(request.message, request.session_id):
            if event_type == "session":
                current_session_id = data["session_id"]
            yield _encode_sse(event_type, data, current_session_id)

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
    agent_service: AgentService = Depends(get_agent_service),
) -> StopChatResponse:
    """Request cancellation for a running generation."""
    accepted = agent_service.stop(request.session_id)
    return StopChatResponse(accepted=accepted, session_id=request.session_id)
