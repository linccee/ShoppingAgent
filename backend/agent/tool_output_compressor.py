"""Utilities for shrinking bulky tool outputs before persistence."""
from __future__ import annotations

import copy
import json
from typing import Any, Sequence

from langchain_core.messages import BaseMessage, ToolMessage

_MAX_REVIEW_LEN = 300
_MAX_CONTENT_LEN = 500
_MAX_TEXT_PREVIEW_LEN = 500


def compress_tool_output(tool_name: str, raw_output: Any, *, force_json: bool = False) -> str:
    """Compress a tool output while preserving a stable string representation."""
    if isinstance(raw_output, str):
        text = raw_output
    else:
        try:
            text = json.dumps(raw_output, ensure_ascii=False)
        except (TypeError, ValueError):
            text = str(raw_output)

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return _compress_non_json_output(tool_name, text, force_json=force_json)

    compressed = _compress_structured_output(tool_name, data)

    if isinstance(compressed, str):
        if force_json:
            return json.dumps({"content": compressed}, ensure_ascii=False)
        return compressed

    return json.dumps(compressed, ensure_ascii=False)


def compress_tool_messages(
    messages: Sequence[BaseMessage],
    *,
    force_json: bool = True,
) -> list[BaseMessage]:
    """Return a deep-copied message list with compressed ToolMessage payloads."""
    compressed_messages = copy.deepcopy(list(messages))

    for message in compressed_messages:
        if not isinstance(message, ToolMessage):
            continue

        tool_name = getattr(message, "name", "") or ""
        message.content = compress_tool_output(
            tool_name,
            message.content,
            force_json=force_json,
        )

    return compressed_messages


def _compress_structured_output(tool_name: str, data: Any) -> Any:
    if tool_name == "search_products":
        return _compress_search_products(data)
    if tool_name == "prices":
        return _compress_prices(data)
    if tool_name == "analyze_reviews":
        return _compress_analyze_reviews(data)
    if tool_name == "tavily_search":
        return _compress_tavily_search(data)
    if tool_name == "tavily_extract":
        return _compress_tavily_extract(data)
    if tool_name == "currency_exchange":
        return data
    return data


def _compress_non_json_output(tool_name: str, text: str, *, force_json: bool) -> str:
    limit = _MAX_CONTENT_LEN if tool_name.startswith("tavily") else _MAX_TEXT_PREVIEW_LEN
    trimmed = text[:limit] + ("…" if len(text) > limit else "")
    if force_json:
        return json.dumps({"content": trimmed}, ensure_ascii=False)
    return trimmed


def _compress_search_products(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    if not data.get("success") or not data.get("results"):
        return data

    kept = []
    for item in data["results"]:
        product_sku = item.get("product_sku")
        if not product_sku:
            continue
        kept.append(
            {
                "title": item.get("title", ""),
                "platform": item.get("platform", ""),
                "product_sku": product_sku,
            }
        )

    return {
        "success": True,
        "query": data.get("query", ""),
        "total": len(kept),
        "results": kept,
    }


def _compress_prices(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
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


def _compress_analyze_reviews(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    if not data.get("success", True):
        return data

    reviews = data.get("reviews", [])
    compressed_reviews = []
    for review in reviews:
        content = review.get("content", "")
        compressed_reviews.append(
            {
                "title": review.get("title", ""),
                "content": content[:_MAX_REVIEW_LEN] + ("…" if len(content) > _MAX_REVIEW_LEN else ""),
                "rating": review.get("rating", ""),
                "author": review.get("author", ""),
                "verified": review.get("verified", False),
            }
        )

    return {
        "platform": data.get("platform"),
        "product_id": data.get("product_id"),
        "overall_rating": data.get("overall_rating"),
        "reviews_count": data.get("reviews_count"),
        "summary_text": data.get("summary_text"),
        "reviews_summary": data.get("reviews_summary"),
        "reviews": compressed_reviews,
    }


def _compress_tavily_search(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    if data.get("success") is False:
        return data

    answer = data.get("answer")
    compressed_results = []
    for result in data.get("results", []):
        content = result.get("content", "")
        compressed_results.append(
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": content[:_MAX_CONTENT_LEN] + ("…" if len(content) > _MAX_CONTENT_LEN else ""),
                "score": result.get("score"),
            }
        )

    out: dict[str, Any] = {"results": compressed_results}
    if answer:
        out["answer"] = answer
    if data.get("response_time") is not None:
        out["response_time"] = data.get("response_time")
    return out


def _compress_tavily_extract(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    compressed_results = []
    for result in data.get("results", []):
        raw_content = result.get("raw_content", "")
        compressed_results.append(
            {
                "url": result.get("url", ""),
                "content": raw_content[:_MAX_CONTENT_LEN] + ("…" if len(raw_content) > _MAX_CONTENT_LEN else ""),
            }
        )

    out: dict[str, Any] = {"results": compressed_results}
    failed_results = data.get("failed_results")
    if failed_results:
        out["failed_results"] = failed_results
    if data.get("response_time") is not None:
        out["response_time"] = data.get("response_time")
    return out
