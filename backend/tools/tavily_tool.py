"""Tavily 搜索工具 - 使用 Tavily API 进行网络搜索。"""
from datetime import datetime
import logging
from typing import Any

import requests
from langchain_core.tools import tool

from backend.app.config import Config

_log = logging.getLogger("agent_stream")


def _preview_text(value: str, limit: int = 120) -> str:
    """生成适合日志的短文本预览。"""
    normalized = value.replace("\n", "\\n").strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}...(+{len(normalized) - limit} chars)"


def _normalize_domains(domains: list[str] | None, field_name: str, max_count: int) -> list[str] | None:
    """标准化 include/exclude domains 参数。"""
    if domains is None:
        return None

    if not isinstance(domains, list):
        raise ValueError(f"{field_name} 必须是字符串列表")

    normalized = [domain.strip() for domain in domains if isinstance(domain, str) and domain.strip()]
    if len(normalized) > max_count:
        raise ValueError(f"{field_name} 最多允许 {max_count} 个域名")

    return normalized


def _validate_date(value: str, field_name: str) -> str:
    """校验 YYYY-MM-DD 日期格式。"""
    normalized = value.strip()
    if not normalized:
        return ""

    try:
        datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须是 YYYY-MM-DD 格式") from exc

    return normalized


@tool
def tavily_search(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    topic: str = "general",
    time_range: str = "",
    start_date: str = "",
    end_date: str = "",
    include_answer: bool | str = False,
    include_raw_content: bool | str = False,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    country: str = "",
    safe_search: bool = False,
    **kwargs,
) -> str:
    """
    使用 Tavily API 进行网络搜索，获取时效性信息（新闻、最新价格、最新产品等）。
    注意：搜索关键词中禁止添加年份、日期或时间范围，直接使用核心关键词即可。

    参数：
        query: 搜索关键词（必填，禁止添加年份或日期）
        search_depth: 搜索深度，默认 basic，可选 basic/advanced/fast
        max_results: 返回结果数量，默认 5，范围 0-20
        topic: 搜索主题，默认 general，可选 general/news/finance
        time_range: 时间范围，可选 day/week/month/year
        start_date/end_date: 日期范围，格式 YYYY-MM-DD
        include_answer: 是否包含答案，默认 False
        include_raw_content: 是否包含原始正文，默认 False
        include_domains/exclude_domains: 域名白名单/黑名单
        country: 优先国家结果
        safe_search: 是否过滤不安全内容
    """
    if not Config.TAVILY_KEY:
        return "未配置 Tavily API Key，请设置 TAVILY_API_KEY 环境变量"

    normalized_query = query.strip()
    if not normalized_query:
        return "参数错误: query 不能为空"

    if search_depth not in {"advanced", "basic", "fast"}:
        return "参数错误: search_depth 只能是 'advanced'、'basic' 或 'fast'"

    if not 0 <= max_results <= 20:
        return "参数错误: max_results 必须在 0 到 20 之间"

    if topic not in {"general", "news", "finance"}:
        return "参数错误: topic 只能是 'general'、'news' 或 'finance'"

    if include_answer not in {False, True, "basic", "advanced"}:
        return "参数错误: include_answer 只能是 False、True、'basic' 或 'advanced'"

    if include_raw_content not in {False, True, "markdown", "text"}:
        return "参数错误: include_raw_content 只能是 False、True、'markdown' 或 'text'"

    if time_range and time_range not in {"day", "week", "month", "year", "d", "w", "m", "y"}:
        return "参数错误: time_range 只能是 day/week/month/year 或 d/w/m/y"

    if safe_search and search_depth == "fast":
        return "参数错误: safe_search 不支持 fast 搜索深度"

    normalized_country = country.strip().lower()
    if normalized_country and topic != "general":
        return "参数错误: country 仅在 topic='general' 时有效"

    try:
        normalized_start_date = _validate_date(start_date, "start_date")
        normalized_end_date = _validate_date(end_date, "end_date")
        normalized_include_domains = _normalize_domains(include_domains, "include_domains", 300)
        normalized_exclude_domains = _normalize_domains(exclude_domains, "exclude_domains", 150)
    except ValueError as exc:
        return f"参数错误: {exc}"

    payload: dict[str, Any] = {
        "query": normalized_query,
        "search_depth": search_depth,
        "max_results": max_results,
        "topic": topic,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "safe_search": safe_search,
    }
    if time_range:
        payload["time_range"] = time_range
    if normalized_start_date:
        payload["start_date"] = normalized_start_date
    if normalized_end_date:
        payload["end_date"] = normalized_end_date
    if normalized_include_domains:
        payload["include_domains"] = normalized_include_domains
    if normalized_exclude_domains:
        payload["exclude_domains"] = normalized_exclude_domains
    if normalized_country:
        payload["country"] = normalized_country

    _log.debug(
        "[TAVILY_SEARCH] request query=%r depth=%s topic=%s max_results=%s include_answer=%r "
        "include_raw_content=%r domains_in=%s domains_out=%s safe_search=%s",
        _preview_text(normalized_query),
        search_depth,
        topic,
        max_results,
        include_answer,
        include_raw_content,
        len(normalized_include_domains or []),
        len(normalized_exclude_domains or []),
        safe_search,
    )

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            headers={
                "Authorization": f"Bearer {Config.TAVILY_KEY}",
                "Content-Type": "application/json",
            },
            timeout=35.0,
        )
    except requests.RequestException as exc:
        _log.error("[TAVILY_SEARCH] request failed: %s", exc)
        return f"Tavily Search 请求失败: {exc}"

    if not response.ok:
        error_message = _extract_error_message(response)
        _log.error(
            "[TAVILY_SEARCH] http_error status=%s error=%r",
            response.status_code,
            _preview_text(error_message),
        )
        return f"Tavily Search 请求失败（HTTP {response.status_code}）: {error_message}"

    try:
        response_payload = response.json()
    except ValueError:
        _log.error("[TAVILY_SEARCH] invalid_json status=%s", response.status_code)
        return "Tavily Search 返回了无法解析的响应"

    _log.debug(
        "[TAVILY_SEARCH] response status=%s results=%s answer=%s response_time=%s request_id=%s",
        response.status_code,
        len(response_payload.get("results") or []),
        bool(response_payload.get("answer")),
        response_payload.get("response_time"),
        response_payload.get("request_id"),
    )

    formatted_results = []

    answer = response_payload.get("answer")
    if answer:
        formatted_results.append(f"答案:\n{answer}")

    for index, result in enumerate(response_payload.get("results", []), start=1):
        lines = [
            f"{index}. {result.get('title', 'No title')}",
            f"URL: {result.get('url', 'No URL')}",
        ]

        content = result.get("content", "")
        lines.append(f"内容: {content}" if content else "内容: 未返回摘要")

        score = result.get("score")
        if score is not None:
            lines.append(f"相关性: {score}")

        if include_raw_content:
            raw_content = result.get("raw_content")
            if raw_content:
                lines.append(f"原始内容:\n{raw_content}")

        formatted_results.append("\n".join(lines))

    response_time = response_payload.get("response_time")
    if response_time is not None:
        formatted_results.append(f"响应时间: {response_time}s")

    return "\n\n".join(formatted_results) if formatted_results else "未找到相关结果"


def _normalize_extract_urls(urls: str | list[str]) -> str | list[str]:
    """标准化 Tavily Extract 的 URLs 输入。"""
    if isinstance(urls, str):
        normalized = urls.strip()
        if not normalized:
            raise ValueError("urls 不能为空")
        return normalized

    if not isinstance(urls, list):
        raise ValueError("urls 必须是字符串或字符串列表")

    normalized = [url.strip() for url in urls if isinstance(url, str) and url.strip()]
    if not normalized:
        raise ValueError("urls 必须包含至少一个有效 URL")
    if len(normalized) > 20:
        raise ValueError("最多只允许 20 个 URL")

    return normalized[0] if len(normalized) == 1 else normalized


def _extract_error_message(response: requests.Response) -> str:
    """从 Tavily 错误响应中提取错误消息。"""
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or "未知错误"

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return detail.get("error", "未知错误")
    if isinstance(detail, str):
        return detail
    return payload.get("error", "未知错误")


@tool
def tavily_extract(urls: str | list[str], query: str = "", extract_depth: str = "basic", format: str = "markdown", **kwargs) -> str:
    """
    从指定 URL 提取网页内容。

    参数：
        urls: 要提取的网页 URL，单个或列表
        query: 用户意图（可选），用于重排内容块
        extract_depth: 提取深度，默认 basic，可选 basic/advanced
        format: 返回格式，默认 markdown，可选 markdown/text
    """
    if not Config.TAVILY_KEY:
        return "未配置 Tavily API Key，请设置 TAVILY_API_KEY 环境变量"

    try:
        normalized_urls = _normalize_extract_urls(urls)
    except ValueError as exc:
        return f"参数错误: {exc}"

    if extract_depth not in {"basic", "advanced"}:
        return "参数错误: extract_depth 只能是 'basic' 或 'advanced'"

    if format not in {"markdown", "text"}:
        return "参数错误: format 只能是 'markdown' 或 'text'"

    normalized_query = query.strip()

    payload: dict[str, Any] = {
        "urls": normalized_urls,
        "extract_depth": extract_depth,
        "format": format,
    }
    if normalized_query:
        payload["query"] = normalized_query

    headers = {
        "Authorization": f"Bearer {Config.TAVILY_KEY}",
        "Content-Type": "application/json",
    }
    request_timeout = 30.0 if extract_depth == "advanced" else 15.0

    url_count = 1 if isinstance(normalized_urls, str) else len(normalized_urls)
    _log.debug(
        "[TAVILY_EXTRACT] request urls=%s depth=%s format=%s query=%r",
        url_count,
        extract_depth,
        format,
        _preview_text(normalized_query),
    )

    try:
        response = requests.post(
            "https://api.tavily.com/extract",
            json=payload,
            headers=headers,
            timeout=request_timeout,
        )
    except requests.RequestException as exc:
        _log.error("[TAVILY_EXTRACT] request failed: %s", exc)
        return f"Tavily Extract 请求失败: {exc}"

    if not response.ok:
        error_message = _extract_error_message(response)
        _log.error(
            "[TAVILY_EXTRACT] http_error status=%s error=%r",
            response.status_code,
            _preview_text(error_message),
        )
        return f"Tavily Extract 请求失败（HTTP {response.status_code}）: {error_message}"

    try:
        response_payload = response.json()
    except ValueError:
        _log.error("[TAVILY_EXTRACT] invalid_json status=%s", response.status_code)
        return "Tavily Extract 返回了无法解析的响应"

    _log.debug(
        "[TAVILY_EXTRACT] response status=%s results=%s failed=%s response_time=%s request_id=%s",
        response.status_code,
        len(response_payload.get("results") or []),
        len(response_payload.get("failed_results") or []),
        response_payload.get("response_time"),
        response_payload.get("request_id"),
    )

    formatted_results = []
    for index, result in enumerate(response_payload.get("results", []), start=1):
        lines = [f"{index}. 来源: {result.get('url', 'Unknown')}"]
        raw_content = result.get("raw_content", "")
        lines.append(f"内容:\n{raw_content}" if raw_content else "内容: 未返回内容")
        formatted_results.append("\n".join(lines))

    failed_results = response_payload.get("failed_results") or []
    if failed_results:
        failed_lines = ["提取失败的 URL:"]
        for failed in failed_results:
            failed_lines.append(
                f"- {failed.get('url', 'Unknown')}: {failed.get('error', 'Unknown error')}"
            )
        formatted_results.append("\n".join(failed_lines))

    response_time = response_payload.get("response_time")
    if response_time is not None:
        formatted_results.append(f"响应时间: {response_time}s")

    return "\n\n".join(formatted_results) if formatted_results else "未能提取内容"
