"""
compression_retry.py

重试机制 for 记忆压缩失败。
Implements exponential backoff with MongoDB-backed failed task persistence.
"""
import queue
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional

from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

from backend.app.config import Config
from backend.app.utils.logging_config import agent_logger as _log
from backend.utils import db

if TYPE_CHECKING:
    from backend.agent.compressed_checkpointer import _CompressionTask

# ── Constants ────────────────────────────────────────────────────────────────
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2.0
MAX_RETRY_DELAY = 60.0
BACKOFF_MULTIPLIER = 2.0
RETRY_SCAN_INTERVAL = 10
TASK_MAX_AGE_HOURS = 24
DEGRADATION_THRESHOLD_INCREASE = 1500
DEGRADATION_COOLDOWN_MINUTES = 5

# Thread-safe caches
_failed_tasks_cache: dict[str, dict] = {}
_degradation_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()
_degradation_lock = threading.Lock()

# Background threads
_retry_scanner_thread: Optional[threading.Thread] = None
_stop_retry_scanner = threading.Event()

# Reference to compression queue (set by compressed_checkpointer)
_compression_queue: Optional[queue.Queue] = None


def _set_compression_queue(q: queue.Queue) -> None:
    """Allow compressed_checkpointer to inject the queue reference."""
    global _compression_queue
    _compression_queue = q


# ── Exponential Backoff ────────────────────────────────────────────────────

def calculate_next_retry_delay(attempt_count: int) -> float:
    """
    Calculate exponential backoff delay.
    Sequence: 2, 4, 8, 16, 32, 60 (capped)
    """
    delay = INITIAL_RETRY_DELAY * (BACKOFF_MULTIPLIER ** attempt_count)
    return min(delay, MAX_RETRY_DELAY)


# ── Retry Scheduling ────────────────────────────────────────────────────────

def schedule_retry(
    thread_id: str,
    source_checkpoint_id: str,
    messages: list[BaseMessage],
    attempt_count: int,
    last_error: str,
) -> bool:
    """
    Schedule a failed task for retry.
    Returns True if retry was scheduled, False if max retries exceeded.
    """
    if attempt_count >= MAX_RETRIES:
        _log.warning(
            "[RETRY] Max retries (%d) exceeded for thread_id=%s, triggering degradation",
            MAX_RETRIES, thread_id
        )
        return False

    next_retry_at = datetime.now(timezone.utc) + timedelta(
        seconds=calculate_next_retry_delay(attempt_count)
    )

    task_doc = {
        "thread_id": thread_id,
        "source_checkpoint_id": source_checkpoint_id,
        "serialized_messages": messages_to_dict(messages),
        "attempt_count": attempt_count,
        "max_attempts": MAX_RETRIES,
        "next_retry_at": next_retry_at,
        "last_error": last_error,
        "status": "pending_retry",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    db.save_failed_task(task_doc)

    cache_key = f"{thread_id}:{source_checkpoint_id}"
    with _cache_lock:
        _failed_tasks_cache[cache_key] = task_doc

    _log.debug(
        "[RETRY] Scheduled retry #%d for thread_id=%s at %s (delay=%.1fs)",
        attempt_count + 1,
        thread_id,
        next_retry_at.isoformat(),
        calculate_next_retry_delay(attempt_count),
    )
    return True


def is_task_stale(thread_id: str, source_checkpoint_id: str) -> bool:
    """
    Check if a retry task is stale (a newer checkpoint exists).
    """
    current_state = db.load_compressed_state(thread_id)
    if not current_state:
        return True
    return current_state.get("source_checkpoint_id") != source_checkpoint_id


def rehydrate_task(task_doc: dict) -> Optional["_CompressionTask"]:
    """
    Convert a MongoDB failed task document back to a _CompressionTask.
    Returns None if task is stale.
    """
    thread_id = task_doc["thread_id"]
    source_checkpoint_id = task_doc["source_checkpoint_id"]

    if is_task_stale(thread_id, source_checkpoint_id):
        _log.debug(
            "[RETRY] Discarding stale task thread_id=%s source_checkpoint_id=%s",
            thread_id, source_checkpoint_id
        )
        db.delete_failed_task(thread_id, source_checkpoint_id)
        return None

    messages = messages_from_dict(task_doc["serialized_messages"])

    # Import here to avoid circular import
    from backend.agent.compressed_checkpointer import _CompressionTask

    return _CompressionTask(
        thread_id=thread_id,
        messages=messages,
        source_checkpoint_id=source_checkpoint_id,
        attempt_count=task_doc["attempt_count"] + 1,
    )


# ── Degradation Management ────────────────────────────────────────────────

def trigger_degradation(thread_id: str) -> None:
    """
    Trigger degradation for a thread_id after max retries exceeded.
    Increases threshold and optionally skips compression temporarily.
    """
    with _degradation_lock:
        current = db.load_degradation_state(thread_id)

        if current and current.get("skip_until"):
            if datetime.now(timezone.utc) < current["skip_until"]:
                return

        level = 1 if not current else min(current.get("degradation_level", 0) + 1, 2)
        new_threshold = Config.COMPRESSION_THRESHOLD + (level * DEGRADATION_THRESHOLD_INCREASE)
        skip_until = datetime.now(timezone.utc) + timedelta(minutes=DEGRADATION_COOLDOWN_MINUTES)

        state = {
            "thread_id": thread_id,
            "degradation_level": level,
            "threshold": new_threshold,
            "skip_until": skip_until,
            "failure_count": (current.get("failure_count", 0) + 1) if current else 1,
            "created_at": current.get("created_at", datetime.now(timezone.utc)) if current else datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        db.save_degradation_state(**state)

        with _degradation_lock:
            _degradation_cache[thread_id] = state

        _log.warning(
            "[DEGRADE] Degradation triggered for thread_id=%s: level=%d threshold=%d skip_until=%s",
            thread_id, level, new_threshold, skip_until.isoformat()
        )


def get_degradation_threshold(thread_id: str) -> Optional[int]:
    """
    Get the current threshold for a thread_id considering degradation.
    Returns None if compression should be skipped entirely.
    """
    with _degradation_lock:
        if thread_id in _degradation_cache:
            state = _degradation_cache[thread_id]
            if state.get("skip_until") and datetime.now(timezone.utc) < state["skip_until"]:
                return None
            return state.get("threshold", Config.COMPRESSION_THRESHOLD)

    state = db.load_degradation_state(thread_id)
    if not state:
        return Config.COMPRESSION_THRESHOLD

    with _degradation_lock:
        _degradation_cache[thread_id] = state

    if state.get("skip_until") and datetime.now(timezone.utc) < state["skip_until"]:
        return None

    return state.get("threshold", Config.COMPRESSION_THRESHOLD)


def check_recovery(thread_id: str) -> bool:
    """
    Check if a thread_id has recovered from degradation.
    Returns True if compression can resume normal operation.
    """
    with _degradation_lock:
        if thread_id not in _degradation_cache:
            return True

        state = _degradation_cache[thread_id]
        if state.get("skip_until") and datetime.now(timezone.utc) >= state["skip_until"]:
            db.clear_degradation_state(thread_id)
            del _degradation_cache[thread_id]
            _log.info("[DEGRADE] Recovery for thread_id=%s, resuming normal operation", thread_id)
            return True

    return False


# ── Retry Scanner Thread ────────────────────────────────────────────────────

def _retry_scanner() -> None:
    """Background thread that scans for tasks ready to retry."""
    _log.debug("[RETRY_SCANNER] Started")

    while not _stop_retry_scanner.is_set():
        try:
            pending_tasks = db.load_pending_retries(limit=50)

            for task_doc in pending_tasks:
                thread_id = task_doc["thread_id"]
                source_checkpoint_id = task_doc["source_checkpoint_id"]

                db.update_failed_task_status(
                    thread_id, source_checkpoint_id,
                    status="processing"
                )

                task = rehydrate_task(task_doc)
                if task and _compression_queue is not None:
                    _compression_queue.put(task)
                    _log.debug(
                        "[RETRY_SCANNER] Re-enqueued task thread_id=%s attempt=%d",
                        thread_id, task_doc["attempt_count"] + 1
                    )

        except Exception as exc:
            _log.error("[RETRY_SCANNER] Error scanning for retries: %s", exc)

        try:
            deleted = db.purge_old_failed_tasks(TASK_MAX_AGE_HOURS)
            if deleted > 0:
                _log.debug("[RETRY_SCANNER] Purged %d old failed tasks", deleted)
        except Exception as exc:
            _log.error("[RETRY_SCANNER] Error purging old tasks: %s", exc)

        _stop_retry_scanner.wait(timeout=RETRY_SCAN_INTERVAL)

    _log.debug("[RETRY_SCANNER] Stopped")


def _ensure_retry_scanner() -> None:
    """Ensure the retry scanner thread is running."""
    global _retry_scanner_thread
    if _retry_scanner_thread is None or not _retry_scanner_thread.is_alive():
        _stop_retry_scanner.clear()
        _retry_scanner_thread = threading.Thread(target=_retry_scanner, daemon=True)
        _retry_scanner_thread.start()
        _log.debug("[RETRY_SCANNER] Started new scanner thread")
