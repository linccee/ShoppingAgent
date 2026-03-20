"""Security utilities for JWT and password handling."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from backend.app.config import Config

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with work factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    username: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(days=Config.ACCESS_TOKEN_EXPIRE_DAYS)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM,
    )
    logger.info(f"[SECURITY] Created token for user_id={user_id}, username={username}, expires_at={expire}")
    return token


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    payload = jwt.decode(
        token,
        Config.JWT_SECRET,
        algorithms=[Config.JWT_ALGORITHM],
    )
    logger.info(f"[SECURITY] Decoded token: sub={payload.get('sub')}, username={payload.get('username')}")
    return payload
