"""Agent service for session-aware streaming and cancellation."""
from __future__ import annotations

import threading
from typing import Generator

from backend.agent.agent_core import create_shopping_agent, stream_agent
from backend.agent.tool_output_compressor import compress_tool_output
from backend.app.services.session_service import SessionService
from backend.app.utils.logging_config import agent_logger


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
        user_id: str | None = None,
    ) -> Generator[tuple[str, object], None, None]:
        """Stream agent events and persist the session transcript."""
        agent_logger.info(f"[AGENT] Starting stream for message={message[:50]}..., session_id={session_id}")
        resolved_session_id = self._session_service.create(session_id, user_id=user_id)
        session = (
            self._session_service.get_for_user(resolved_session_id, user_id)
            if user_id
            else self._session_service.get(resolved_session_id)
        )
        if user_id and session.created_at is None:
            raise ValueError("Session not found")

        messages = list(session.messages)
        total_input_tokens = session.input_tokens
        total_output_tokens = session.output_tokens

        user_message = {"role": "user", "content": message}
        assistant_message = {"role": "assistant", "content": "", "steps": []}
        messages.append(user_message)
        messages.append(assistant_message)

        stop_event = self._register_stop_event(resolved_session_id)
        agent_logger.info(f"[AGENT] Stream started, session_id={resolved_session_id}")
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
                    agent_logger.debug(f"[AGENT] Tool started: {data.get('tool')}")
                    assistant_message["steps"].append(
                        {
                            "type": "tool",
                            "tool": data["tool"],
                            "input": data["input"],
                            "output": "",
                        }
                    )
                elif kind == "tool_end":
                    agent_logger.debug(f"[AGENT] Tool ended")
                    if assistant_message["steps"]:
                        assistant_message["steps"][-1]["output"] = data
                elif kind == "token_usage":
                    total_input_tokens += int(data.get("input_tokens", 0))
                    total_output_tokens += int(data.get("output_tokens", 0))
                    agent_logger.debug(f"[AGENT] Token usage: input={data.get('input_tokens')}, output={data.get('output_tokens')}")
                elif kind == "stopped":
                    stopped = True
                    agent_logger.info(f"[AGENT] Stream stopped for session {resolved_session_id}")

                yield (kind, data)
        finally:
            compressed_messages = _compress_messages(messages)
            self._session_service.save(
                session_id=resolved_session_id,
                messages=compressed_messages,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )
            self._clear_stop_event(resolved_session_id)
            agent_logger.info(f"[AGENT] Session {resolved_session_id} saved, total_tokens: input={total_input_tokens}, output={total_output_tokens}")

        if not stopped:
            agent_logger.info(f"[AGENT] Stream completed for session {resolved_session_id}")
            yield ("done", {"message": "completed"})


# ─── Tool Output Compression ─────────────────────────────────────────────────

def _compress_tool_output(tool_name: str, raw_output: str) -> str:
    """按工具类型压缩冗余字段，保留关键信息用于 session 持久化。"""
    return compress_tool_output(tool_name, raw_output, force_json=False)


def _compress_messages(messages: list[dict]) -> list[dict]:
    """遍历消息列表，对 assistant 消息中的 tool steps 进行压缩。"""
    result = []
    for msg in messages:
        msg = dict(msg)
        if msg.get("role") == "assistant" and msg.get("steps"):
            for step in msg["steps"]:
                if step.get("type") == "tool":
                    step["output"] = _compress_tool_output(
                        step.get("tool", ""), step.get("output", "")
                    )
        result.append(msg)
    return result
