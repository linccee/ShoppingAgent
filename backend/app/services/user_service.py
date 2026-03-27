"""User service for user profile operations."""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from backend.utils.db import users_col
from backend.app.utils.logging_config import user_logger


class UserService:
    """Service for user profile operations."""

    def get_user_by_id(self, user_id: str) -> dict | None:
        """Get a user by their ID."""
        try:
            user_logger.debug(f"[USER] Getting user by id={user_id}")
            user = users_col.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                user.pop("_id", None)
                user.pop("password_hash", None)
                user_logger.debug(f"[USER] User found: {user_id}")
            else:
                user_logger.debug(f"[USER] User not found: {user_id}")
            return user
        except Exception as e:
            user_logger.error(f"[USER] Error getting user by id={user_id}: {e}")
            return None

    def get_user_by_username(self, username: str) -> dict | None:
        """Get a user by username."""
        user_logger.debug(f"[USER] Getting user by username={username}")
        user = users_col.find_one({"username": username})
        if user:
            user["id"] = str(user["_id"])
            user.pop("_id", None)
            user.pop("password_hash", None)
            user_logger.debug(f"[USER] User found by username: {username}")
        else:
            user_logger.debug(f"[USER] User not found by username: {username}")
        return user

    def get_user_by_email(self, email: str) -> dict | None:
        """Get a user by email."""
        user_logger.debug(f"[USER] Getting user by email={email}")
        user = users_col.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            user.pop("_id", None)
            user.pop("password_hash", None)
            user_logger.debug(f"[USER] User found by email: {email}")
        else:
            user_logger.debug(f"[USER] User not found by email: {email}")
        return user

    def update_user(
        self,
        user_id: str,
        username: str | None = None,
        email: str | None = None,
    ) -> tuple[bool, str]:
        """Update user profile (username, email)."""
        user_logger.info(f"[USER] Updating user profile user_id={user_id}, username={username}, email={email}")
        update_fields: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}

        if username is not None:
            # Check if username is taken by another user
            existing = users_col.find_one({"username": username, "_id": {"$ne": ObjectId(user_id)}})
            if existing:
                user_logger.warning(f"[USER] Update failed for {user_id}: username {username} already taken")
                return False, "AUTH_USER_EXISTS"
            update_fields["username"] = username

        if email is not None:
            # Check if email is taken by another user
            existing = users_col.find_one({"email": email, "_id": {"$ne": ObjectId(user_id)}})
            if existing:
                user_logger.warning(f"[USER] Update failed for {user_id}: email {email} already taken")
                return False, "AUTH_USER_EXISTS"
            update_fields["email"] = email

        result = users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields},
        )

        success = result.modified_count > 0 or result.matched_count > 0
        if success:
            user_logger.info(f"[USER] User profile updated successfully for user_id={user_id}")
        else:
            user_logger.warning(f"[USER] User profile update had no effect for user_id={user_id}")
        return success, ""

    def update_preferences(self, user_id: str, preferences: dict) -> tuple[bool, str]:
        """Update user preferences."""
        user_logger.info(f"[USER] Updating preferences for user_id={user_id}")
        update_fields = {
            "updated_at": datetime.now(timezone.utc),
            "preferences": preferences,
        }

        result = users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields},
        )

        success = result.modified_count > 0 or result.matched_count > 0
        if success:
            user_logger.info(f"[USER] Preferences updated successfully for user_id={user_id}")
        else:
            user_logger.warning(f"[USER] Preferences update had no effect for user_id={user_id}")
        return success, ""

    def delete_user(self, user_id: str) -> bool:
        """Delete a user account."""
        user_logger.info(f"[USER] Deleting user account user_id={user_id}")
        result = users_col.delete_one({"_id": ObjectId(user_id)})
        deleted = result.deleted_count > 0
        if deleted:
            user_logger.info(f"[USER] User account deleted successfully user_id={user_id}")
        else:
            user_logger.warning(f"[USER] User account deletion failed user_id={user_id}")
        return deleted
