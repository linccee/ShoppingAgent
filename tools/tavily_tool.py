"""Tavily 搜索工具 - 使用 Tavily API 进行网络搜索。"""
from datetime import datetime
import logging
from typing import Any

import requests
from langchain_core.tools import tool

from config import Config

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
    chunks_per_source: int = 3,
    time_range: str = "",
    start_date: str = "",
    end_date: str = "",
    include_answer: bool | str = False,
    include_raw_content: bool | str = False,
    include_images: bool = False,
    include_image_descriptions: bool = False,
    include_favicon: bool = False,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    country: str = "",
    auto_parameters: bool = False,
    exact_match: bool = False,
    include_usage: bool = False,
    safe_search: bool = False,
) -> str:
    """
    使用 Tavily API 进行网络搜索。
    当用户询问时效性比较强的信息时，使用此工具从网络上搜索最新的内容，以提供更准确和及时的回答。

    Args:
        query: 搜索查询字符串
        search_depth: 搜索深度，默认 "basic"，可选 "advanced"、"basic"、"fast"、"ultra-fast"
        max_results: 返回结果数量，默认 5，范围 0-20
        topic: 搜索主题，默认 "general"，可选 "general"、"news"、"finance"
        chunks_per_source: advanced 搜索时每个来源返回的内容块数量，默认 3，范围 1-3
        time_range: 时间范围，默认空字符串，可选 day/week/month/year 或 d/w/m/y
        start_date: 起始日期，默认空字符串，格式 YYYY-MM-DD
        end_date: 结束日期，默认空字符串，格式 YYYY-MM-DD
        include_answer: 是否包含答案，默认 False，可选 False、True、"basic"、"advanced"
        include_raw_content: 是否包含原始正文，默认 False，可选 False、True、"markdown"、"text"
        include_images: 是否返回图片搜索结果，默认 False
        include_image_descriptions: 是否返回图片描述，默认 False，仅在 include_images=True 时有效
        include_favicon: 是否包含网站图标，默认 False
        include_domains: 仅包含这些域名，默认 None，最多 300 个
        exclude_domains: 排除这些域名，默认 None，最多 150 个
        country: 优先某个国家的结果，默认空字符串，仅 topic="general" 时有效
        auto_parameters: 是否启用 Tavily 自动参数，默认 False
        exact_match: 是否要求精确匹配引号中的短语，默认 False
        include_usage: 是否包含 credit 使用信息，默认 False
        safe_search: 是否过滤不安全内容，默认 False，不支持 fast/ultra-fast

    Returns:
        格式化的搜索结果字符串
    """
    if not Config.TAVILY_KEY:
        return "未配置 Tavily API Key，请设置 TAVILY_API_KEY 环境变量"

    normalized_query = query.strip()
    if not normalized_query:
        return "参数错误: query 不能为空"

    if search_depth not in {"advanced", "basic", "fast", "ultra-fast"}:
        return "参数错误: search_depth 只能是 'advanced'、'basic'、'fast' 或 'ultra-fast'"

    if not 0 <= max_results <= 20:
        return "参数错误: max_results 必须在 0 到 20 之间"

    if topic not in {"general", "news", "finance"}:
        return "参数错误: topic 只能是 'general'、'news' 或 'finance'"

    if not 1 <= chunks_per_source <= 3:
        return "参数错误: chunks_per_source 必须在 1 到 3 之间"

    if include_answer not in {False, True, "basic", "advanced"}:
        return "参数错误: include_answer 只能是 False、True、'basic' 或 'advanced'"

    if include_raw_content not in {False, True, "markdown", "text"}:
        return "参数错误: include_raw_content 只能是 False、True、'markdown' 或 'text'"

    if time_range and time_range not in {"day", "week", "month", "year", "d", "w", "m", "y"}:
        return "参数错误: time_range 只能是 day/week/month/year 或 d/w/m/y"

    if safe_search and search_depth in {"fast", "ultra-fast"}:
        return "参数错误: safe_search 不支持 fast 或 ultra-fast 搜索深度"

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
        "include_images": include_images,
        "include_image_descriptions": include_image_descriptions,
        "include_favicon": include_favicon,
        "auto_parameters": auto_parameters,
        "exact_match": exact_match,
        "include_usage": include_usage,
        "safe_search": safe_search,
    }
    if search_depth == "advanced":
        payload["chunks_per_source"] = chunks_per_source
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
        "[TAVILY_SEARCH] request query=%r depth=%s topic=%s max_results=%s include_answer=%r include_raw_content=%r "
        "include_images=%s include_favicon=%s include_usage=%s domains_in=%s domains_out=%s auto_parameters=%s "
        "exact_match=%s safe_search=%s",
        _preview_text(normalized_query),
        search_depth,
        topic,
        max_results,
        include_answer,
        include_raw_content,
        include_images,
        include_favicon,
        include_usage,
        len(normalized_include_domains or []),
        len(normalized_exclude_domains or []),
        auto_parameters,
        exact_match,
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
        "[TAVILY_SEARCH] response status=%s results=%s images=%s answer=%s response_time=%s request_id=%s",
        response.status_code,
        len(response_payload.get("results") or []),
        len(response_payload.get("images") or []),
        bool(response_payload.get("answer")),
        response_payload.get("response_time"),
        response_payload.get("request_id"),
    )

    formatted_results = []

    answer = response_payload.get("answer")
    if answer:
        formatted_results.append(f"答案:\n{answer}")

    if include_images:
        images = response_payload.get("images") or []
        if images:
            image_lines = ["图片结果:"]
            for image in images:
                if isinstance(image, dict):
                    image_url = image.get("url", "")
                    description = image.get("description", "")
                    image_lines.append(
                        f"- {image_url}" if not description else f"- {image_url}\n  描述: {description}"
                    )
                else:
                    image_lines.append(f"- {image}")
            formatted_results.append("\n".join(image_lines))

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

        if include_favicon:
            favicon = result.get("favicon")
            if favicon:
                lines.append(f"Favicon: {favicon}")

        formatted_results.append("\n".join(lines))

    auto_parameters_data = response_payload.get("auto_parameters")
    if auto_parameters and auto_parameters_data:
        auto_summary = ", ".join(f"{key}={value}" for key, value in auto_parameters_data.items())
        formatted_results.append(f"自动参数: {auto_summary}")

    metadata_lines = []
    response_time = response_payload.get("response_time")
    if response_time is not None:
        metadata_lines.append(f"响应时间: {response_time}s")

    request_id = response_payload.get("request_id")
    if request_id:
        metadata_lines.append(f"请求ID: {request_id}")

    if include_usage:
        usage = response_payload.get("usage") or {}
        if usage:
            usage_summary = ", ".join(f"{key}={value}" for key, value in usage.items())
            metadata_lines.append(f"用量: {usage_summary}")

    if metadata_lines:
        formatted_results.append("\n".join(metadata_lines))

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
def tavily_extract(urls: str | list[str], query: str = "", chunks_per_source: int = 3, extract_depth: str = "basic", include_images: bool = False, include_favicon: bool = False, format: str = "markdown", timeout: float | None = None, include_usage: bool = False) -> str:
    """
    从指定 URL 提取内容。
    当你需要从特定网页提取原始内容时，使用此工具获取网页正文等信息。

    Args:
        urls: 要提取内容的网页 URL，可以是单个 URL 或多个 URL 列表
        query: 用户意图，用于重排提取的内容块，默认空字符串
        chunks_per_source: 每个源的最大内容块数量，默认 3，范围 1-5
        extract_depth: 提取深度，默认 "basic"，可选 "basic" 或 "advanced"
            - basic：基础提取
            - advanced：提取更多数据，包括表格和嵌入内容
        include_images: 是否包含图片列表，默认 False
        include_favicon: 是否包含 favicon URL，默认 False
        format: 返回格式，默认 "markdown"，可选 "markdown" 或 "text"
        timeout: 超时时间（秒），默认 None，范围 1-60；不传则由 Tavily 按 extract_depth 使用默认值
        include_usage: 是否包含 credit 使用信息，默认 False

    Returns:
        提取的内容
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
    if normalized_query and not 1 <= chunks_per_source <= 5:
        return "参数错误: chunks_per_source 必须在 1 到 5 之间"

    if timeout is not None and not 1 <= timeout <= 60:
        return "参数错误: timeout 必须在 1 到 60 秒之间"

    payload: dict[str, Any] = {
        "urls": normalized_urls,
        "extract_depth": extract_depth,
        "include_images": include_images,
        "include_favicon": include_favicon,
        "format": format,
        "include_usage": include_usage,
    }
    if normalized_query:
        payload["query"] = normalized_query
        payload["chunks_per_source"] = chunks_per_source
    if timeout is not None:
        payload["timeout"] = timeout

    headers = {
        "Authorization": f"Bearer {Config.TAVILY_KEY}",
        "Content-Type": "application/json",
    }
    request_timeout = (timeout if timeout is not None else (30.0 if extract_depth == "advanced" else 10.0)) + 5.0

    url_count = 1 if isinstance(normalized_urls, str) else len(normalized_urls)
    _log.debug(
        "[TAVILY_EXTRACT] request urls=%s depth=%s format=%s query=%r include_images=%s include_favicon=%s "
        "include_usage=%s timeout=%s",
        url_count,
        extract_depth,
        format,
        _preview_text(normalized_query),
        include_images,
        include_favicon,
        include_usage,
        timeout,
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
        payload = response.json()
    except ValueError:
        _log.error("[TAVILY_EXTRACT] invalid_json status=%s", response.status_code)
        return "Tavily Extract 返回了无法解析的响应"

    _log.debug(
        "[TAVILY_EXTRACT] response status=%s results=%s failed=%s response_time=%s request_id=%s",
        response.status_code,
        len(payload.get("results") or []),
        len(payload.get("failed_results") or []),
        payload.get("response_time"),
        payload.get("request_id"),
    )

    formatted_results = []
    for index, result in enumerate(payload.get("results", []), start=1):
        lines = [f"{index}. 来源: {result.get('url', 'Unknown')}"]
        raw_content = result.get("raw_content", "")
        lines.append(f"内容:\n{raw_content}" if raw_content else "内容: 未返回内容")

        if include_images:
            images = result.get("images") or []
            if images:
                lines.append("图片:\n" + "\n".join(images))

        if include_favicon:
            favicon = result.get("favicon")
            if favicon:
                lines.append(f"Favicon: {favicon}")

        formatted_results.append("\n".join(lines))

    failed_results = payload.get("failed_results") or []
    if failed_results:
        failed_lines = ["提取失败的 URL:"]
        for failed in failed_results:
            failed_lines.append(
                f"- {failed.get('url', 'Unknown')}: {failed.get('error', 'Unknown error')}"
            )
        formatted_results.append("\n".join(failed_lines))

    metadata_lines = []
    response_time = payload.get("response_time")
    if response_time is not None:
        metadata_lines.append(f"响应时间: {response_time}s")

    request_id = payload.get("request_id")
    if request_id:
        metadata_lines.append(f"请求ID: {request_id}")

    if include_usage:
        usage = payload.get("usage") or {}
        if usage:
            usage_summary = ", ".join(f"{key}={value}" for key, value in usage.items())
            metadata_lines.append(f"用量: {usage_summary}")

    if metadata_lines:
        formatted_results.append("\n".join(metadata_lines))

    return "\n\n".join(formatted_results) if formatted_results else "未能提取内容"
