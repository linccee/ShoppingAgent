"""
记忆管理器 - 摘要压缩与历史校验

压缩后的 LLM 上下文必须保持合法的工具调用序列，
因此压缩和读取都基于完整对话轮次处理，而不是按消息条数切片。
"""
import os
from typing import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from backend.app.config import Config
from backend.app.utils.logging_config import agent_logger as _log


class InvalidCompressedHistoryError(ValueError):
    """压缩历史不满足 LangChain / OpenAI 工具调用序列约束。"""


def _rough_count_tokens(text: str) -> int:
    """在 tiktoken 不可用时使用保守估算，避免网络或缓存问题中断请求。"""
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)


def _ensure_tiktoken_cache_dir() -> None:
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", Config.TIKTOKEN_CACHE_DIR)
    os.makedirs(Config.TIKTOKEN_CACHE_DIR, exist_ok=True)


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    估算文本的 token 数量。
    使用 tiktoken（OpenAI 官方）进行准确计量。
    """
    try:
        _ensure_tiktoken_cache_dir()
        import tiktoken

        encoding = encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        _log.warning("tiktoken not installed, using rough estimation")
        return _rough_count_tokens(text)
    except Exception as exc:
        _log.warning("tiktoken unavailable or cache missing, using rough estimation: %s", exc)
        return _rough_count_tokens(text)


def encoding_for_model(model: str):
    """获取指定模型的编码器，回退到 cl100k_base"""
    _ensure_tiktoken_cache_dir()
    import tiktoken

    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_messages_tokens(messages: Sequence[BaseMessage]) -> int:
    """计算消息列表的总 token 数。"""
    total = 3  # messages 数组本身

    for msg in messages:
        role_overhead = 4
        total += count_tokens(str(msg.content)) + role_overhead + 2

    return total


def validate_message_history(messages: Sequence[BaseMessage]) -> None:
    """
    验证消息序列是否满足工具调用约束。

    约束：
    - ToolMessage 必须对应紧邻之前某个 AIMessage 的 tool_calls
    - tool_call_id 不可为空
    - 在未消费完所有 pending tool_call_id 前，不能出现新的非 ToolMessage
    """
    pending_tool_call_ids: set[str] = set()

    for index, msg in enumerate(messages):
        if isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None)
            if not tool_call_id:
                raise InvalidCompressedHistoryError(
                    f"ToolMessage at index {index} is missing tool_call_id"
                )
            if not pending_tool_call_ids:
                raise InvalidCompressedHistoryError(
                    f"Orphan ToolMessage at index {index} without pending tool_calls"
                )
            if tool_call_id not in pending_tool_call_ids:
                raise InvalidCompressedHistoryError(
                    f"ToolMessage at index {index} references unknown tool_call_id={tool_call_id}"
                )
            pending_tool_call_ids.remove(tool_call_id)
            continue

        if pending_tool_call_ids:
            raise InvalidCompressedHistoryError(
                f"Non-tool message at index {index} appeared before completing pending tool calls"
            )

        if isinstance(msg, AIMessage) and msg.tool_calls:
            next_pending: set[str] = set()
            for tool_call in msg.tool_calls:
                tool_call_id = tool_call.get("id")
                if not tool_call_id:
                    raise InvalidCompressedHistoryError(
                        f"AIMessage at index {index} contains tool call without id"
                    )
                if tool_call_id in next_pending:
                    raise InvalidCompressedHistoryError(
                        f"AIMessage at index {index} contains duplicate tool_call_id={tool_call_id}"
                    )
                next_pending.add(tool_call_id)
            pending_tool_call_ids = next_pending

    if pending_tool_call_ids:
        raise InvalidCompressedHistoryError("History ends with unresolved tool calls")


def sanitize_tool_calls_from_checkpoint(checkpoint: dict) -> dict:
    """
    从 checkpoint 的 channel_values.messages 中移除未完成的 tool_calls。

    当用户点击停止按钮时，LangGraph checkpoint 可能包含一个 AIMessage
    带有 tool_calls 但没有对应的 ToolMessage（因为 stop 阻断了工具调用链）。
    这种损坏的 checkpoint 会导致下次加载时 LangGraph 抛出 INVALID_CHAT_HISTORY。

    本函数找到最后一条带有未完成 tool_calls 的 AIMessage，清除其 tool_calls
    字段（保留 content），使历史变得合法。
    """
    import copy

    if not checkpoint:
        return checkpoint

    channel_values = checkpoint.get("channel_values", {})
    if not channel_values or "messages" not in channel_values:
        return checkpoint

    messages = channel_values["messages"]
    if not isinstance(messages, list):
        return checkpoint

    # 检测 pending tool_call_ids（与 validate_message_history 相同逻辑）
    pending: set[str] = set()
    last_ai_with_tool_calls = None
    last_ai_with_tool_calls_index = -1

    for i, msg in enumerate(messages):
        if isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None) or ""
            if tool_call_id in pending:
                pending.remove(tool_call_id)
            continue

        if pending:
            # Non-tool message appeared before resolving pending tool calls
            pending = set()
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                last_ai_with_tool_calls = msg
                last_ai_with_tool_calls_index = i

        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            next_pending: set[str] = set()
            for tc in msg.tool_calls:
                tc_id = tc.get("id")
                if tc_id:
                    next_pending.add(tc_id)
            if next_pending:
                pending = next_pending
                last_ai_with_tool_calls = msg
                last_ai_with_tool_calls_index = i

    # 如果有未解决的 tool_calls，清理最后一条 AIMessage 的 tool_calls
    if pending and last_ai_with_tool_calls is not None:
        _log.warning(
            "[SANITIZE] Removing %d unresolved tool_calls from AIMessage at index %d",
            len(pending),
            last_ai_with_tool_calls_index,
        )

        # 创建深拷贝以避免修改原始 checkpoint
        checkpoint = copy.deepcopy(checkpoint)
        messages = checkpoint["channel_values"]["messages"]
        msg = messages[last_ai_with_tool_calls_index]

        # 清除 tool_calls（保留 content）
        if hasattr(msg, "tool_calls"):
            msg.tool_calls = []
        if hasattr(msg, "type"):
            # AIMessage 的 dict 表示
            msg["tool_calls"] = []

    return checkpoint


def _format_messages_for_summary(messages: Sequence[BaseMessage]) -> str:
    """将消息格式化为易读的文本，用于 LLM 摘要"""
    lines = []

    for i, msg in enumerate(messages):
        role = getattr(msg, "type", "user")
        role_display = {
            "human": "用户",
            "user": "用户",
            "ai": "助手",
            "assistant": "助手",
            "system": "系统",
            "tool": "工具",
        }.get(role, role)

        content = str(msg.content)
        display_content = content[:200] + "..." if len(content) > 200 else content
        lines.append(f"{i + 1}. [{role_display}]: {display_content}")

    return "\n".join(lines)


def summarize_messages(
    messages: Sequence[BaseMessage],
    llm: BaseChatModel,
    max_retries: int = 3,
) -> str:
    """调用 LLM 将消息列表压缩为摘要，支持指数退避重试。"""
    if not messages:
        return ""

    formatted = _format_messages_for_summary(messages)
    summary_prompt = f"""请简洁总结以下对话的要点，包括：
1. 用户的主要需求和提问
2. AI 的关键回复和建议
3. 使用过的工具和结果
4. 任何重要的上下文信息
5. 需要保留的细节（如果有）
6. 不要输出markdown格式，直接纯文本总结，一段话即可

对话内容：
{formatted}

请用 300 字以内（如果内容过多，允许500字以内）概括要点："""

    last_error = None
    for attempt in range(max_retries):
        try:
            response = llm.invoke(summary_prompt)
            summary = response.content if hasattr(response, "content") else str(response)
            _log.debug(f"[SUMMARIZE] Original {len(messages)} messages -> {len(summary)} chars summary")
            return summary
        except Exception as e:
            last_error = e
            _log.warning(f"[SUMMARIZE] Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Simple backoff: 1s, 2s, 4s

    _log.error(f"[SUMMARIZE] All {max_retries} attempts failed: {last_error}")
    return ""


def _split_prefix_and_turns(messages: Sequence[BaseMessage]) -> tuple[list[BaseMessage], list[list[BaseMessage]]]:
    """
    将消息拆为前缀消息和以 HumanMessage 为边界的完整轮次。

    一个轮次从用户消息开始，直到下一条用户消息出现前结束。
    这样工具调用链始终保留在同一轮次内。
    """
    prefix: list[BaseMessage] = []
    turns: list[list[BaseMessage]] = []
    current_turn: list[BaseMessage] = []
    seen_human = False

    for msg in messages:
        if isinstance(msg, HumanMessage):
            if current_turn:
                turns.append(current_turn)
            current_turn = [msg]
            seen_human = True
            continue

        if not seen_human:
            prefix.append(msg)
            continue

        current_turn.append(msg)

    if current_turn:
        turns.append(current_turn)

    return prefix, turns


def _select_recent_turns_by_token_budget(
    turns: Sequence[list[BaseMessage]],
    token_budget: int,
) -> tuple[list[list[BaseMessage]], list[list[BaseMessage]]]:
    """
    按 token 预算保留最近轮次，但始终完整保留最新一轮。

    返回：
        (older_turns, recent_turns)
    """
    if not turns:
        return [], []

    selected_reversed: list[list[BaseMessage]] = []
    for turn in reversed(turns):
        if not selected_reversed:
            selected_reversed.append(turn)
            continue

        candidate_turns = [turn, *list(reversed(selected_reversed))]
        candidate_messages = [msg for candidate_turn in candidate_turns for msg in candidate_turn]
        if count_messages_tokens(candidate_messages) <= token_budget:
            selected_reversed.append(turn)
        else:
            break

    recent_turns = list(reversed(selected_reversed))
    older_turns = list(turns[:-len(recent_turns)]) if recent_turns else list(turns)
    return older_turns, recent_turns


def compress_history(
    messages: Sequence[BaseMessage],
    threshold: int | None = None,
    llm: BaseChatModel | None = None,
) -> list[BaseMessage]:
    """
    如果消息历史超过阈值，压缩早期完整轮次为摘要。
    threshold 参数允许外部传入降级后的阈值。
    """
    if not messages:
        return list(messages)

    effective_threshold = threshold if threshold is not None else Config.COMPRESSION_THRESHOLD

    validate_message_history(messages)

    total_tokens = count_messages_tokens(messages)
    _log.debug(f"[COMPRESS] Total tokens: {total_tokens}, threshold: {effective_threshold}")

    if total_tokens < effective_threshold:
        return list(messages)

    prefix, turns = _split_prefix_and_turns(messages)
    if not turns:
        return list(messages)

    older_turns, recent_turns = _select_recent_turns_by_token_budget(
        turns,
        Config.RECENT_HISTORY_TOKEN_BUDGET,
    )
    older_messages = [msg for turn in older_turns for msg in turn]

    if not older_messages or llm is None:
        if llm is None:
            _log.warning("[COMPRESS] No LLM provided, skipping compression")
        return list(messages)

    summary = summarize_messages(older_messages, llm)
    if not summary:
        return list(messages)

    compressed: list[BaseMessage] = list(prefix)
    compressed.append(SystemMessage(content=f"【之前对话摘要】{summary}"))
    for turn in recent_turns:
        compressed.extend(turn)

    validate_message_history(compressed)
    _log.debug(f"[COMPRESS] Compressed {len(messages)} messages -> {len(compressed)} messages")
    return compressed
