"""
自定义 Checkpointer - 异步持久化压缩消息历史

设计目标：
1. 原始 LangGraph checkpoint 立即落库，保证正确性
2. 压缩后的 LLM 上下文异步持久化到独立集合，供后续请求快速读取
3. 同一 thread 仅以最新快照为准，过期压缩结果丢弃
4. lite_llm 调用严格限制在 1 req/s（API 速率限制）
"""
import logging
import queue
import threading
import time
import uuid
from typing import Optional

from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.checkpoint.mongodb import MongoDBSaver

from backend.agent.memory_manager import (
    InvalidCompressedHistoryError,
    compress_history,
    count_messages_tokens,
    validate_message_history,
)
from backend.app.config import Config
from backend.utils.db import load_compressed_state, save_compressed_state

_log = logging.getLogger("compressed_checkpointer")

_lite_llm = None


def _get_lite_llm():
    """获取轻量 LLM 用于摘要生成"""
    global _lite_llm
    if _lite_llm is None:
        from langchain_openai import ChatOpenAI

        _lite_llm = ChatOpenAI(
            model=Config.LITE_MODEL,
            api_key=Config.LITE_API_KEY,
            base_url=Config.LITE_BASE_URL,
            temperature=0.3,
        )
    return _lite_llm


class _CompressionTask:
    """单个压缩任务的描述符。"""

    def __init__(self, thread_id: str, messages: list[BaseMessage], source_checkpoint_id: str):
        self.thread_id = thread_id
        self.messages = messages
        self.source_checkpoint_id = source_checkpoint_id


_compression_queue: queue.Queue[_CompressionTask] = queue.Queue()
_compression_worker_thread: Optional[threading.Thread] = None
_stop_compression_worker = threading.Event()

_compressed_state_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()

# ── 全局 LITE_LLM 速率限制器：确保调用间隔 ≥ 1 秒 ──────────────────────────
_llm_rate_limit_lock = threading.Lock()
_last_llm_call_time: float = 0.0
_MIN_CALL_INTERVAL: float = 1.5  # 秒


def _enforce_rate_limit() -> None:
    """
    强制确保两次 lite_llm 调用之间至少间隔 1.5 秒。
    线程安全，使用全局锁保护。
    """
    global _last_llm_call_time
    with _llm_rate_limit_lock:
        now = time.monotonic()
        elapsed = now - _last_llm_call_time
        if elapsed < _MIN_CALL_INTERVAL:
            sleep_duration = _MIN_CALL_INTERVAL - elapsed
            _log.debug("[RATE_LIMIT] Sleeping %.2fs to respect 1 req/s limit", sleep_duration)
            time.sleep(sleep_duration)
        _last_llm_call_time = time.monotonic()


def _cache_state(state: dict | None) -> None:
    if not state:
        return
    with _cache_lock:
        _compressed_state_cache[state["thread_id"]] = dict(state)


def _get_persisted_state(thread_id: str, *, refresh: bool = False) -> dict | None:
    with _cache_lock:
        if not refresh and thread_id in _compressed_state_cache:
            return dict(_compressed_state_cache[thread_id])

    state = load_compressed_state(thread_id)
    if state:
        _cache_state(state)
        return dict(state)
    return None


def _persist_state(
    thread_id: str,
    source_checkpoint_id: str,
    compressed_messages: list[dict] | None,
    status: str,
    error: str | None = None,
) -> None:
    save_compressed_state(
        thread_id=thread_id,
        source_checkpoint_id=source_checkpoint_id,
        compressed_messages=compressed_messages,
        status=status,
        error=error,
    )
    _cache_state(
        {
            "thread_id": thread_id,
            "source_checkpoint_id": source_checkpoint_id,
            "compressed_messages": compressed_messages,
            "status": status,
            "error": error,
        }
    )


def _replace_checkpoint_messages(checkpoint: dict, messages: list[BaseMessage]) -> dict:
    patched_checkpoint = dict(checkpoint)
    patched_checkpoint["channel_values"] = dict(patched_checkpoint.get("channel_values", {}))
    patched_checkpoint["channel_values"]["messages"] = messages
    return patched_checkpoint


def _deserialize_persisted_messages(state: dict) -> list[BaseMessage]:
    payload = state.get("compressed_messages") or []
    messages = messages_from_dict(payload)
    validate_message_history(messages)
    return messages


def _mark_failed_if_current(thread_id: str, source_checkpoint_id: str, error: str) -> None:
    current_state = _get_persisted_state(thread_id, refresh=True)
    if not current_state:
        return
    if current_state.get("source_checkpoint_id") != source_checkpoint_id:
        _log.debug(
            "[COMPRESSION_WORKER] Skip failure update for stale task: thread_id=%s expected=%s current=%s",
            thread_id,
            source_checkpoint_id,
            current_state.get("source_checkpoint_id"),
        )
        return
    _persist_state(thread_id, source_checkpoint_id, None, "failed", error)


def _persist_compressed_if_current(task: _CompressionTask, compressed_messages: list[BaseMessage]) -> None:
    current_state = _get_persisted_state(task.thread_id, refresh=True)
    if not current_state:
        _log.debug("[COMPRESSION_WORKER] No persisted state exists for thread_id=%s", task.thread_id)
        return
    if current_state.get("source_checkpoint_id") != task.source_checkpoint_id:
        _log.debug(
            "[COMPRESSION_WORKER] Discarding stale compressed result: thread_id=%s expected=%s current=%s",
            task.thread_id,
            task.source_checkpoint_id,
            current_state.get("source_checkpoint_id"),
        )
        return

    serialized_messages = messages_to_dict(compressed_messages)
    _persist_state(task.thread_id, task.source_checkpoint_id, serialized_messages, "ready", None)
    _log.debug("[COMPRESSION_WORKER] Persisted compressed state for thread_id=%s", task.thread_id)


def _process_compression_task(task: _CompressionTask) -> None:
    _log.debug(
        "[COMPRESSION_WORKER] Processing task for thread_id=%s source_checkpoint_id=%s",
        task.thread_id,
        task.source_checkpoint_id,
    )

    try:
        # 速率限制：确保 lite_llm 调用不超过 1 req/s
        _enforce_rate_limit()
        compressed_messages = compress_history(
            task.messages,
            threshold=Config.COMPRESSION_THRESHOLD,
            llm=_get_lite_llm(),
        )
        validate_message_history(compressed_messages)
        _persist_compressed_if_current(task, compressed_messages)
    except InvalidCompressedHistoryError as exc:
        _log.error("[COMPRESSION_WORKER] Invalid compressed history: %s", exc)
        _mark_failed_if_current(task.thread_id, task.source_checkpoint_id, str(exc))
    except Exception as exc:
        _log.error("[COMPRESSION_WORKER] Compression failed: %s", exc)
        _mark_failed_if_current(task.thread_id, task.source_checkpoint_id, str(exc))


def _compression_worker():
    """后台工作线程：消费压缩任务并持久化最新有效结果。"""
    _log.debug("[COMPRESSION_WORKER] Started")
    while not _stop_compression_worker.is_set():
        try:
            task = _compression_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        try:
            _process_compression_task(task)
        finally:
            _compression_queue.task_done()

    _log.debug("[COMPRESSION_WORKER] Stopped")


def _ensure_compression_worker():
    """确保压缩工作线程已启动。"""
    global _compression_worker_thread
    if _compression_worker_thread is None or not _compression_worker_thread.is_alive():
        _stop_compression_worker.clear()
        _compression_worker_thread = threading.Thread(target=_compression_worker, daemon=True)
        _compression_worker_thread.start()
        _log.debug("[COMPRESSION_WORKER] Started new worker thread")


class CompressedCheckpointer(BaseCheckpointSaver):
    """
    包装 MongoDBSaver，实现原始 checkpoint + 持久化压缩状态双轨保存。
    """

    def __init__(self, mongodb_saver: MongoDBSaver):
        self._saver = mongodb_saver
        _ensure_compression_worker()

    @staticmethod
    def _make_source_checkpoint_id() -> str:
        return uuid.uuid4().hex

    def _get_preferred_messages(self, thread_id: str) -> list[BaseMessage] | None:
        state = _get_persisted_state(thread_id)
        if not state:
            return None
        if state.get("status") != "ready" or not state.get("compressed_messages"):
            return None

        try:
            messages = _deserialize_persisted_messages(state)
            _log.debug(
                "[CHECKPOINTER] Using persisted compressed state for thread_id=%s source_checkpoint_id=%s",
                thread_id,
                state.get("source_checkpoint_id"),
            )
            return messages
        except InvalidCompressedHistoryError as exc:
            _log.error("[CHECKPOINTER] Invalid persisted compressed state for %s: %s", thread_id, exc)
            _persist_state(
                thread_id,
                state.get("source_checkpoint_id", ""),
                None,
                "failed",
                str(exc),
            )
            return None

    def get(self, config: dict) -> Optional[dict]:
        """获取 checkpoint，优先返回持久化压缩版本。"""
        checkpoint = self._saver.get(config)
        if not checkpoint:
            return None

        thread_id = config.get("configurable", {}).get("thread_id", "default")

        # 尝试用持久化压缩状态替换
        preferred_messages = self._get_preferred_messages(thread_id)
        if preferred_messages:
            return _replace_checkpoint_messages(checkpoint, preferred_messages)

        # 没有压缩状态：检查原始 checkpoint 是否损坏（stop 时可能产生）
        try:
            from backend.agent.memory_manager import sanitize_tool_calls_from_checkpoint

            checkpoint = sanitize_tool_calls_from_checkpoint(checkpoint)
        except Exception as exc:
            _log.warning("[CHECKPOINTER] sanitize_tool_calls_from_checkpoint failed: %s", exc)

        return checkpoint

    def put(
        self,
        config: dict,
        checkpoint: dict,
        metadata: dict,
        new_versions: dict,
        **kwargs,
    ) -> dict:
        """
        保存 checkpoint：
        1. 立即保存原始 LangGraph checkpoint
        2. 同步保存或异步生成对应的持久化 LLM 状态
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        source_checkpoint_id = self._make_source_checkpoint_id()

        result_config = self._saver.put(config, checkpoint, metadata, new_versions)

        channel_values = checkpoint.get("channel_values") if checkpoint else None
        messages = list(channel_values.get("messages", [])) if channel_values and "messages" in channel_values else []

        if not messages:
            _persist_state(thread_id, source_checkpoint_id, [], "ready", None)
            return result_config

        try:
            validate_message_history(messages)
        except InvalidCompressedHistoryError as exc:
            _log.error("[CHECKPOINTER] Raw checkpoint history is invalid for %s: %s", thread_id, exc)
            _persist_state(thread_id, source_checkpoint_id, None, "failed", str(exc))
            return result_config

        total_tokens = count_messages_tokens(messages)
        if total_tokens < Config.COMPRESSION_THRESHOLD:
            _persist_state(
                thread_id,
                source_checkpoint_id,
                messages_to_dict(messages),
                "ready",
                None,
            )
            return result_config

        _persist_state(thread_id, source_checkpoint_id, None, "pending", None)
        _compression_queue.put(_CompressionTask(thread_id, messages, source_checkpoint_id))
        _ensure_compression_worker()
        return result_config

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """获取 checkpoint tuple，优先返回持久化压缩版本。"""
        tuple_result = self._saver.get_tuple(config)
        if not tuple_result:
            return None

        thread_id = config.get("configurable", {}).get("thread_id", "default")
        preferred_messages = self._get_preferred_messages(thread_id)

        if preferred_messages:
            checkpoint = _replace_checkpoint_messages(tuple_result.checkpoint, preferred_messages)
        else:
            # 没有压缩状态：尝试修复损坏的原始 checkpoint
            try:
                from backend.agent.memory_manager import sanitize_tool_calls_from_checkpoint

                checkpoint = sanitize_tool_calls_from_checkpoint(tuple_result.checkpoint)
            except Exception as exc:
                _log.warning("[CHECKPOINTER] get_tuple sanitize failed: %s", exc)
                checkpoint = tuple_result.checkpoint

        return CheckpointTuple(
            config=tuple_result.config,
            checkpoint=checkpoint,
            parent_config=tuple_result.parent_config,
            metadata=tuple_result.metadata,
        )

    def put_writes(self, config: dict, writes: list, task_id: str = None) -> None:
        self._saver.put_writes(config, writes, task_id)

    def list(self, config: dict, *, filter: dict = None, limit: int = None):
        return self._saver.list(config, filter=filter, limit=limit)

    def get_next_version(self, current_version: Optional[str], config: dict) -> str:
        return self._saver.get_next_version(current_version, config)
