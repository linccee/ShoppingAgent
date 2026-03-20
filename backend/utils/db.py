"""
utils/db.py
MongoDB integration for persistent chat sessions and derived agent state.
"""
from datetime import datetime
import uuid
from typing import Any

from pymongo import MongoClient

from backend.app.config import Config
from backend.app.utils.logging_config import db_logger

# Connect to MongoDB
MONGO_URI = Config.MONGO_URI
db_logger.info(f"[DB] Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
db = client.shop_agent
sessions_col = db.sessions
compressed_states_col = db.compressed_agent_states
users_col = db.users
db_logger.info("[DB] MongoDB connected successfully")


def get_or_create_session_id(session_id: str = None) -> str:
    """Generate a new UUID if none is provided."""
    return session_id if session_id else str(uuid.uuid4())


def save_session(
    session_id: str,
    messages: list,
    input_tokens: int = 0,
    output_tokens: int = 0,
    user_id: str | None = None,
) -> str:
    """
    将对话数据更新插入 MongoDB。
    动态保存当前状态（每次生成后调用）。
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    db_logger.debug(f"[DB] Saving session {session_id}, messages_count={len(messages)}, input_tokens={input_tokens}, output_tokens={output_tokens}")

    # 提取对话标题
    title = "新的对话"
    for msg in messages:
        if msg.get("role") == "user":
            title = msg.get("content", "")[:20]
            if len(msg.get("content", "")) > 20:
                title += "..."
            break

    now = datetime.utcnow()

    update_fields = {
        "title": title,
        "messages": messages,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "updated_at": now,
    }

    if user_id is not None:
        update_fields["user_id"] = user_id

    # 一次 upsert 同时更新运行时字段，并只在首次创建时写入 created_at。
    sessions_col.update_one(
        {"session_id": session_id},
        {
            "$set": update_fields,
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )

    db_logger.debug(f"[DB] Session {session_id} saved successfully")
    return session_id


def create_session(session_id: str | None = None, user_id: str | None = None) -> str:
    """Create an empty session document if it does not already exist."""
    resolved_session_id = get_or_create_session_id(session_id)
    db_logger.info(f"[DB] Creating session {resolved_session_id} for user {user_id}")
    save_session(
        session_id=resolved_session_id,
        messages=[],
        input_tokens=0,
        output_tokens=0,
        user_id=user_id,
    )
    db_logger.info(f"[DB] Session {resolved_session_id} created successfully")
    return resolved_session_id


def save_compressed_state(
    thread_id: str,
    source_checkpoint_id: str,
    compressed_messages: list[dict] | None,
    status: str,
    error: str | None = None,
) -> None:
    """Upsert derived compressed LLM state for a thread."""
    db_logger.debug(f"[DB] Saving compressed state for thread {thread_id}, status={status}")
    compressed_states_col.update_one(
        {"thread_id": thread_id},
        {"$set": {
            "source_checkpoint_id": source_checkpoint_id,
            "compressed_messages": compressed_messages,
            "status": status,
            "error": error,
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )
    db_logger.debug(f"[DB] Compressed state for thread {thread_id} saved successfully")


def load_compressed_state(thread_id: str) -> dict[str, Any] | None:
    """Load persisted compressed LLM state for a thread."""
    db_logger.debug(f"[DB] Loading compressed state for thread {thread_id}")
    result = compressed_states_col.find_one({"thread_id": thread_id})
    if result:
        db_logger.debug(f"[DB] Compressed state for thread {thread_id} found")
    else:
        db_logger.debug(f"[DB] No compressed state found for thread {thread_id}")
    return result


def delete_compressed_state(thread_id: str) -> bool:
    """Delete persisted compressed LLM state for a thread."""
    result = compressed_states_col.delete_one({"thread_id": thread_id})
    return result.deleted_count > 0


def load_session(session_id: str) -> dict:
    """
    根据 ID 从 MongoDB 加载会话。
    返回一个包含 'messages', 'input_tokens', 'output_tokens', 'user_id' 的字典，否则返回空默认值。
    """
    db_logger.debug(f"[DB] Loading session {session_id}")
    doc = sessions_col.find_one({"session_id": session_id})
    if doc:
        return {
            "session_id": doc.get("session_id", session_id),
            "title": doc.get("title", "新的对话"),
            "messages": doc.get("messages", []),
            "input_tokens": doc.get("input_tokens", 0),
            "output_tokens": doc.get("output_tokens", 0),
            "user_id": doc.get("user_id"),
            "updated_at": doc.get("updated_at"),
            "created_at": doc.get("created_at"),
        }
    return {
        "session_id": session_id,
        "title": "新的对话",
        "messages": [],
        "input_tokens": 0,
        "output_tokens": 0,
        "user_id": None,
        "updated_at": None,
        "created_at": None,
    }


def get_all_sessions() -> list:
    """
    获取所有会话的轻量级信息，用于在历史记录中显示。
    按 updated_at 降序排列。
    """
    db_logger.debug("[DB] Fetching all sessions")
    cursor = sessions_col.find(
        {},
        {"session_id": 1, "title": 1, "updated_at": 1, "created_at": 1}
    ).sort("updated_at", -1)

    result = list(cursor)
    db_logger.debug(f"[DB] Fetched {len(result)} sessions")
    return result


def delete_session(session_id: str) -> bool:
    """
    根据 ID 删除 MongoDB 中的特定会话。
    """
    db_logger.info(f"[DB] Deleting session {session_id}")
    result = sessions_col.delete_one({"session_id": session_id})
    deleted = result.deleted_count > 0
    if deleted:
        db_logger.info(f"[DB] Session {session_id} deleted successfully")
    else:
        db_logger.warning(f"[DB] Session {session_id} not found for deletion")
    return deleted


def ping_mongo() -> bool:
    """Check if MongoDB is reachable."""
    try:
        client.admin.command("ping")
        db_logger.debug("[DB] MongoDB ping successful")
        return True
    except Exception as e:
        db_logger.error(f"[DB] MongoDB ping failed: {e}")
        return False
