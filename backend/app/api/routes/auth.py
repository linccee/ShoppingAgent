"""Authentication routes for user registration, login, and logout."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.deps import get_current_user
from backend.app.config import Config
from backend.app.models.user import (
    ErrorResponse,
    RegisterResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPreferences,
    UserResponse,
)
from backend.app.services.auth_service import AuthService
from backend.app.utils.logging_config import auth_logger

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        "400": {"model": ErrorResponse},
    },
)
def register(user_data: UserCreate) -> RegisterResponse:
    """Register a new user account."""
    auth_logger.info(f"[AUTH] Registration attempt for username={user_data.username}, email={user_data.email}")
    auth_service = AuthService()
    success, error_code, user_id = auth_service.register(
        user_data.username,
        user_data.email,
        user_data.password,
        user_data.browser_language,
    )

    if not success:
        error_messages = {
            "AUTH_WEAK_PASSWORD": "密码强度不足",
            "AUTH_USER_EXISTS": "用户名或邮箱已存在",
        }
        auth_logger.warning(f"[AUTH] Registration failed for {user_data.username}: {error_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": error_code, "message": error_messages.get(error_code, "注册失败")},
        )

    auth_logger.info(f"[AUTH] Registration successful for {user_data.username}, user_id={user_id}")
    return RegisterResponse(message="注册成功", user_id=user_id)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        "401": {"model": ErrorResponse},
    },
)
def login(credentials: UserLogin) -> TokenResponse:
    """Login with username/email and password."""
    auth_logger.info(f"[AUTH] Login attempt for username: {credentials.username}")
    auth_service = AuthService()
    success, error_code, user = auth_service.authenticate(credentials.username, credentials.password)

    if not success:
        auth_logger.warning(f"[AUTH] Login failed for {credentials.username}: {error_code}")
        error_messages = {
            "AUTH_INVALID_CREDENTIALS": "用户名或密码错误",
            "AUTH_FORBIDDEN": "账户已被禁用",
        }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": error_code, "message": error_messages.get(error_code, "登录失败")},
        )

    # Create token
    user_id = str(user["_id"])
    auth_logger.info(f"[AUTH] Login success for {credentials.username}, user_id={user_id}")
    token = auth_service.create_token(user_id, user["username"])

    # Build user response
    preferences = user.get("preferences", {})
    user_response = UserResponse(
        id=user_id,
        username=user["username"],
        email=user["email"],
        created_at=user.get("created_at"),
        last_login=user.get("last_login"),
        is_active=user.get("is_active", True),
        role=user.get("role", "user"),
        preferences=UserPreferences(**preferences) if preferences else UserPreferences(),
    )

    auth_logger.info(f"[AUTH] Token created for {credentials.username}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=Config.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600,
        user=user_response,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TokenResponse:
    """Refresh the access token."""
    auth_logger.info(f"[AUTH] Token refresh for user {current_user.get('username')}")
    auth_service = AuthService()
    user_id = current_user["id"]
    token = auth_service.create_token(user_id, current_user["username"])

    preferences = current_user.get("preferences", {})
    user_response = UserResponse(
        id=user_id,
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user.get("created_at"),
        last_login=current_user.get("last_login"),
        is_active=current_user.get("is_active", True),
        role=current_user.get("role", "user"),
        preferences=UserPreferences(**preferences) if preferences else UserPreferences(),
    )

    auth_logger.info(f"[AUTH] Token refreshed for user {current_user.get('username')}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=Config.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600,
        user=user_response,
    )


@router.post("/logout")
def logout(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Logout the current user (client should discard token)."""
    auth_logger.info(f"[AUTH] Logout for user {current_user.get('username')}")
    return {"message": "登出成功"}
