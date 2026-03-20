"""Agent service for session-aware streaming and cancellation."""
from __future__ import annotations

import json
import threading
from typing import Generator

from backend.agent.agent_core import create_shopping_agent, stream_agent
from backend.app.services.session_service import SessionService
from backend.app.utils.logging_config import agent_logger

_MAX_REVIEW_LEN = 300      # 单条评论最大字符数
_MAX_CONTENT_LEN = 500    # tavily 抓取内容最大字符数
_MAX_SEARCH_RESULTS = 9   # search_products 最多保留结果数


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
        agent_logger.info(f"[AGENT] Starting stream for message={message[:50]}..., session_id={session_id}")
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
    try:
        data = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        return raw_output

    compressed: dict | list | str

    if tool_name == "search_products":
        compressed = _compress_search_products(data)
    elif tool_name == "prices":
        compressed = _compress_prices(data)
    elif tool_name == "analyze_reviews":
        compressed = _compress_analyze_reviews(data)
    elif tool_name == "tavily_search":
        compressed = _compress_tavily_search(data)
    elif tool_name == "tavily_extract":
        compressed = _compress_tavily_extract(data)
    elif tool_name == "currency_exchange":
        compressed = data  # 已是精简字段
    else:
        compressed = data

    return json.dumps(compressed, ensure_ascii=False)


def _compress_search_products(data: dict) -> dict:
    """search_products：每平台最多 3 条，只保留核心字段。"""
    if not data.get("success") or not data.get("results"):
        return data

    kept = []
    platform_count = {}
    for item in data["results"]:
        platform = item.get("platform", "")
        count = platform_count.get(platform, 0)
        if count >= 3:
            continue
        platform_count[platform] = count + 1
        kept.append({
            "title": item.get("title", ""),
            "price": item.get("price", ""),
            "rating": item.get("rating", ""),
            "url": item.get("url", ""),
            "platform": platform,
            "product_sku": item.get("product_sku"),
        })

    return {
        "success": True,
        "query": data.get("query", ""),
        "total": len(kept),
        "results": kept,
    }


def _compress_prices(data: dict) -> dict:
    """prices：去除 delivery 详情。"""
    if not data.get("success"):
        return data
    return {
        "success": True,
        "price": data.get("price"),
        "platform": data.get("platform"),
        "product_id": data.get("product_id"),
        "title": data.get("title"),
        "url": data.get("url"),
    }


def _compress_analyze_reviews(data: dict) -> dict:
    """analyze_reviews：评论内容截断，保留摘要和评分。"""
    if isinstance(data, dict) and not data.get("success", True):
        return data

    if not isinstance(data, dict):
        return data

    reviews = data.get("reviews", [])
    compressed_reviews = []
    for r in reviews:
        content = r.get("content", "")
        compressed_reviews.append({
            "title": r.get("title", ""),
            "content": content[:_MAX_REVIEW_LEN] + ("…" if len(content) > _MAX_REVIEW_LEN else ""),
            "rating": r.get("rating", ""),
            "author": r.get("author", ""),
            "verified": r.get("verified", False),
        })

    return {
        "platform": data.get("platform"),
        "product_id": data.get("product_id"),
        "overall_rating": data.get("overall_rating"),
        "reviews_count": data.get("reviews_count"),
        "summary_text": data.get("summary_text"),
        "reviews_summary": data.get("reviews_summary"),
        "reviews": compressed_reviews,
    }


def _compress_tavily_search(data: dict) -> dict:
    """tavily_search：answer 保留，results 截断 content。"""
    if isinstance(data, dict) and data.get("success") is False:
        return data

    if not isinstance(data, dict):
        return data

    answer = data.get("answer")
    compressed_results = []
    for result in data.get("results", []):
        content = result.get("content", "")
        compressed_results.append({
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": content[:_MAX_CONTENT_LEN] + ("…" if len(content) > _MAX_CONTENT_LEN else ""),
            "score": result.get("score"),
        })

    response_time = data.get("response_time")
    out: dict = {
        "results": compressed_results,
    }
    if answer:
        out["answer"] = answer
    if response_time is not None:
        out["response_time"] = response_time

    return out


def _compress_tavily_extract(data: dict) -> dict:
    """tavily_extract：每个 URL 的 content 截断。"""
    if not isinstance(data, dict):
        return data

    compressed_results = []
    for result in data.get("results", []):
        raw = result.get("raw_content", "")
        compressed_results.append({
            "url": result.get("url", ""),
            "content": raw[:_MAX_CONTENT_LEN] + ("…" if len(raw) > _MAX_CONTENT_LEN else ""),
        })

    response_time = data.get("response_time")
    out: dict = {"results": compressed_results}
    if response_time is not None:
        out["response_time"] = response_time

    return out


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
