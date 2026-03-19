"""Agent service for session-aware streaming and cancellation."""
from __future__ import annotations

import threading
from typing import Generator

from backend.agent.agent_core import create_shopping_agent, stream_agent
from backend.app.services.session_service import SessionService


class AgentService:
    """Wrap the shared agent instance and active stop signals."""

    def __init__(self, session_service: SessionService):
        self._session_service = session_service
        self._agent = None
        self._active_stop_events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def _get_agent(self):
        if self._agent is None:
            self._agent = create_shopping_agent()
        return self._agent

    def _register_stop_event(self, session_id: str) -> threading.Event:
        with self._lock:
            stop_event = threading.Event()
            self._active_stop_events[session_id] = stop_event
            return stop_event

    def _clear_stop_event(self, session_id: str) -> None:
        with self._lock:
            self._active_stop_events.pop(session_id, None)

    def stop(self, session_id: str) -> bool:
        """Request cancellation for a running session."""
        with self._lock:
            stop_event = self._active_stop_events.get(session_id)
            if stop_event is None:
                return False
            stop_event.set()
            return True

    def stream(
        self,
        message: str,
        session_id: str | None = None,
    ) -> Generator[tuple[str, object], None, None]:
        """Stream agent events and persist the session transcript."""
        resolved_session_id = self._session_service.create(session_id)
        session = self._session_service.get(resolved_session_id)
        messages = list(session.messages)
        total_input_tokens = session.input_tokens
        total_output_tokens = session.output_tokens

        user_message = {"role": "user", "content": message}
        assistant_message = {"role": "assistant", "content": "", "steps": []}
        messages.append(user_message)
        messages.append(assistant_message)

        stop_event = self._register_stop_event(resolved_session_id)
        yield ("session", {"session_id": resolved_session_id})

        stopped = False
        try:
            agent = self._get_agent()
            for kind, data in stream_agent(
                agent,
                message,
                session_id=resolved_session_id,
                stop_event=stop_event,
            ):
                if kind == "token":
                    assistant_message["content"] += str(data)
                elif kind == "tool_start":
                    assistant_message["steps"].append(
                        {
                            "type": "tool",
                            "tool": data["tool"],
                            "input": data["input"],
                            "output": "",
                        }
                    )
                elif kind == "tool_end":
                    if assistant_message["steps"]:
                        assistant_message["steps"][-1]["output"] = data
                elif kind == "token_usage":
                    total_input_tokens += int(data.get("input_tokens", 0))
                    total_output_tokens += int(data.get("output_tokens", 0))
                elif kind == "stopped":
                    stopped = True

                yield (kind, data)
        finally:
            self._session_service.save(
                session_id=resolved_session_id,
                messages=messages,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )
            self._clear_stop_event(resolved_session_id)

        if not stopped:
            yield ("done", {"message": "completed"})
