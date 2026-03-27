"""Authentication service for user registration and login."""
from datetime import datetime, timezone
import re

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.config import Config
from backend.utils.db import users_col
from backend.app.utils.logging_config import auth_logger


class AuthService:
    """Service for authentication operations."""

    WEAK_PASSWORDS = [
        "password", "12345678", "qwerty", "abc123", "password123",
        "admin", "letmein", "welcome", "monkey", "1234567890",
    ]

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength. Returns (is_valid, error_message)."""
        if len(password) < Config.PASSWORD_MIN_LENGTH:
            return False, f"密码长度至少{Config.PASSWORD_MIN_LENGTH}字符"

        if Config.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"

        if Config.PASSWORD_REQUIRE_LETTER and not any(c.isalpha() for c in password):
            return False, "密码必须包含字母"

        if password.lower() in self.WEAK_PASSWORDS:
            return False, "密码太弱，请使用更强的密码"

        return True, ""

    def register(
        self,
        username: str,
        email: str,
        password: str,
        browser_language: str | None = None,
    ) -> tuple[bool, str, str | None]:
        """
        Register a new user.
        Returns (success, error_code, user_id).
        """
        auth_logger.info(f"[AUTH] Registration attempt for username={username}, email={email}")

        # Check password strength
        is_valid, error_msg = self.validate_password_strength(password)
        if not is_valid:
            auth_logger.warning(f"[AUTH] Registration failed for {username}: weak password")
            return False, "AUTH_WEAK_PASSWORD", None

        # Check if user exists
        if users_col.find_one({"username": username}):
            auth_logger.warning(f"[AUTH] Registration failed for {username}: username exists")
            return False, "AUTH_USER_EXISTS", None

        if users_col.find_one({"email": email}):
            auth_logger.warning(f"[AUTH] Registration failed for {username}: email exists")
            return False, "AUTH_USER_EXISTS", None

        # Determine language preference from browser language
        SUPPORTED_LANGS = {"zh-CN", "zh", "en-US", "en", "en-GB"}
        lang_pref = "auto"
        if browser_language:
            if browser_language in SUPPORTED_LANGS:
                lang_pref = "zh-CN" if browser_language.startswith("zh") else "en-US"
            elif browser_language.startswith("zh"):
                lang_pref = "zh-CN"
            elif browser_language.startswith("en"):
                lang_pref = "en-US"

        # Create user
        now = datetime.now(timezone.utc)
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "created_at": now,
            "updated_at": now,
            "last_login": None,
            "is_active": True,
            "role": "user",
            "preferences": {
                "default_currency": "CNY",
                "favorite_platforms": [],
                "budget_range": {"min": 0, "max": 0},
                "notification_enabled": False,
                "language_preference": lang_pref,
            },
        }

        try:
            result = users_col.insert_one(user_doc)
            auth_logger.info(f"[AUTH] User {username} registered successfully, user_id={result.inserted_id}")
            return True, "", str(result.inserted_id)
        except DuplicateKeyError:
            auth_logger.warning(f"[AUTH] Registration failed for {username}: duplicate key error")
            return False, "AUTH_USER_EXISTS", None

    def authenticate(self, username: str, password: str) -> tuple[bool, str, dict | None]:
        """
        Authenticate a user by username/email and password.
        Returns (success, error_code, user_doc).
        """
        auth_logger.debug(f"[AUTH] Authentication attempt for {username}")

        # Find user by username or email
        user = users_col.find_one({
            "$or": [
                {"username": username},
                {"email": username},
            ]
        })

        if not user:
            auth_logger.warning(f"[AUTH] Authentication failed for {username}: user not found")
            return False, "AUTH_INVALID_CREDENTIALS", None

        if not verify_password(password, user["password_hash"]):
            auth_logger.warning(f"[AUTH] Authentication failed for {username}: invalid password")
            return False, "AUTH_INVALID_CREDENTIALS", None

        if not user.get("is_active", True):
            auth_logger.warning(f"[AUTH] Authentication failed for {username}: user inactive")
            return False, "AUTH_FORBIDDEN", None

        # Update last login
        users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )

        auth_logger.info(f"[AUTH] Authentication successful for {username}, user_id={user['_id']}")
        return True, "", user

    def create_token(self, user_id: str, username: str) -> str:
        """Create an access token for a user."""
        return create_access_token(user_id, username)
