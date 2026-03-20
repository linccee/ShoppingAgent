"""Authentication dependencies for FastAPI routes."""
import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.security import decode_token
from backend.app.services.user_service import UserService

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Extract and validate the current user from JWT token."""
    token = credentials.credentials
    logger.info(f"[AUTH] Received token: {token[:50]}...")

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        username: str = payload.get("username", "")
        logger.info(f"[AUTH] Token decoded successfully. user_id={user_id}, username={username}")
        if user_id is None:
            logger.warning("[AUTH] Token has no 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTH_UNAUTHORIZED", "message": "Invalid token"},
            )
    except jwt.ExpiredSignatureError:
        logger.warning("[AUTH] Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_UNAUTHORIZED", "message": "Token has expired"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"[AUTH] Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_UNAUTHORIZED", "message": "Invalid token"},
        )

    logger.info(f"[AUTH] Looking up user in database: {user_id}")
    user_service = UserService()
    user = user_service.get_user_by_id(user_id)
    if user is None:
        logger.warning(f"[AUTH] User not found in database: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_UNAUTHORIZED", "message": "User not found"},
        )

    if not user.get("is_active", True):
        logger.warning(f"[AUTH] User account is inactive: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_FORBIDDEN", "message": "User account is inactive"},
        )

    logger.info(f"[AUTH] User authenticated successfully: {user.get('username')}")
    return user


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Ensure the current user is active."""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_FORBIDDEN", "message": "Inactive user"},
        )
    return current_user
