"""
初始化用户数据库和迁移现有数据。

此脚本执行以下操作：
1. 创建 users 集合及索引
2. 创建内置用户 user_inline
3. 将现有所有会话的 user_id 设置为 user_inline 的 ObjectId
4. 在 sessions 集合添加必要的字段索引
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import bcrypt
from pymongo import ASCENDING, DESCENDING
from backend.utils.db import client, db, users_col, sessions_col


def create_indexes():
    """创建必要的数据库索引。"""
    print("创建索引...")

    # users 集合索引
    users_col.create_index("username", unique=True)
    users_col.create_index("email", unique=True)
    print("  - users.username (unique)")
    print("  - users.email (unique)")

    # sessions 集合索引
    sessions_col.create_index("user_id")
    sessions_col.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
    print("  - sessions.user_id")
    print("  - sessions.user_id + sessions.updated_at (compound)")


def create_user_inline():
    """创建内置用户 user_inline 用于存储迁移前的历史数据。"""
    print("\n创建内置用户 user_inline...")

    # 检查是否已存在
    existing = users_col.find_one({"username": "user_inline"})
    if existing:
        print(f"  user_inline 已存在 (ID: {existing['_id']})")
        return existing["_id"]

    # 密码固定为 user_inline_pass
    password_hash = bcrypt.hashpw(
        "user_inline_pass".encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    now = datetime.now(timezone.utc)
    user_inline = {
        "username": "user_inline",
        "email": "user_inline@system.local",
        "password_hash": password_hash,
        "created_at": now,
        "updated_at": now,
        "last_login": now,
        "is_active": True,
        "role": "user",
        "preferences": {
            "default_currency": "CNY",
            "favorite_platforms": [],
            "budget_range": {"min": 0, "max": 0},
            "notification_enabled": False,
        },
    }

    result = users_col.insert_one(user_inline)
    print(f"  user_inline 创建成功 (ID: {result.inserted_id})")
    return result.inserted_id


def migrate_sessions(user_inline_id):
    """将现有所有会话迁移到 user_inline 用户。"""
    print("\n迁移现有会话数据...")

    # 统计
    total = sessions_col.count_documents({})
    no_user_id = sessions_col.count_documents({"user_id": {"$exists": False}})
    user_id_none = sessions_col.count_documents({"user_id": None})

    print(f"  总会话数: {total}")
    print(f"  无 user_id 字段: {no_user_id}")
    print(f"  user_id 为 None: {user_id_none}")

    # 迁移没有 user_id 字段的会话
    if no_user_id > 0:
        result = sessions_col.update_many(
            {"user_id": {"$exists": False}},
            {"$set": {"user_id": str(user_inline_id)}},
        )
        print(f"  已设置 user_id: {result.modified_count} 条")

    # 迁移 user_id 为 None 的会话
    if user_id_none > 0:
        result = sessions_col.update_many(
            {"user_id": None},
            {"$set": {"user_id": str(user_inline_id)}},
        )
        print(f"  已更新 user_id=None: {result.modified_count} 条")

    # 确认迁移完成
    migrated_count = sessions_col.count_documents({"user_id": str(user_inline_id)})
    print(f"\n  最终 user_inline 下的会话数: {migrated_count}")


def verify_migration():
    """验证迁移结果。"""
    print("\n验证迁移结果...")

    # 检查 users 集合
    user_count = users_col.count_documents({})
    print(f"  users 集合文档数: {user_count}")

    # 检查 sessions 集合的 user_id 字段
    sessions_with_user = sessions_col.count_documents({"user_id": {"$exists": True}})
    sessions_without_user = sessions_col.count_documents({"user_id": {"$exists": False}})
    print(f"  sessions 有 user_id: {sessions_with_user}")
    print(f"  sessions 无 user_id: {sessions_without_user}")

    # 列出所有用户
    print("\n  用户列表:")
    for user in users_col.find({}, {"username": 1, "email": 1}):
        print(f"    - {user['username']} ({user['email']})")


def init_user_db():
    """初始化用户数据库并迁移数据。"""
    print("=" * 50)
    print("用户模块数据库初始化")
    print("=" * 50)

    try:
        # 1. 创建索引
        create_indexes()

        # 2. 创建内置用户
        user_inline_id = create_user_inline()

        # 3. 迁移现有会话
        migrate_sessions(user_inline_id)

        # 4. 验证
        verify_migration()

        print("\n" + "=" * 50)
        print("初始化完成!")
        print("=" * 50)

    except Exception as e:
        print(f"\n错误: {e}")
        raise


if __name__ == "__main__":
    init_user_db()
