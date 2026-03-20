"""User routes for profile management."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.deps import get_current_user
from backend.app.models.user import (
    ErrorResponse,
    UserPreferences,
    UserResponse,
)
from backend.app.services.user_service import UserService
from backend.app.utils.logging_config import user_logger

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> UserResponse:
    """Get the current user's profile."""
    user_logger.info(f"[USER] User {current_user.get('username')} fetching profile")
    preferences = current_user.get("preferences", {})
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user.get("created_at"),
        last_login=current_user.get("last_login"),
        is_active=current_user.get("is_active", True),
        role=current_user.get("role", "user"),
        preferences=UserPreferences(**preferences) if preferences else UserPreferences(),
    )


@router.put("/me")
def update_user_profile(
    username: str | None = None,
    email: str | None = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    """Update the current user's profile."""
    user_logger.info(f"[USER] User {current_user.get('username')} updating profile, username={username}, email={email}")
    user_service = UserService()
    success, error_code = user_service.update_user(current_user["id"], username, email)

    if not success:
        user_logger.warning(f"[USER] Profile update failed for {current_user.get('username')}: {error_code}")
        error_messages = {
            "AUTH_USER_EXISTS": "用户名或邮箱已存在",
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": error_code, "message": error_messages.get(error_code, "更新失败")},
        )

    user_logger.info(f"[USER] Profile updated successfully for {current_user.get('username')}")
    return {"message": "更新成功"}


@router.put("/me/preferences")
def update_preferences(
    preferences: UserPreferences,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Update user preferences."""
    user_logger.info(f"[USER] User {current_user.get('username')} updating preferences")
    user_service = UserService()
    preferences_dict = preferences.model_dump()
    success, _ = user_service.update_preferences(current_user["id"], preferences_dict)

    if not success:
        user_logger.warning(f"[USER] Preferences update failed for {current_user.get('username')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPDATE_FAILED", "message": "更新偏好设置失败"},
        )

    user_logger.info(f"[USER] Preferences updated successfully for {current_user.get('username')}")
    return {"message": "偏好设置已更新"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """Delete the current user's account."""
    user_logger.info(f"[USER] User {current_user.get('username')} deleting account")
    user_service = UserService()
    success = user_service.delete_user(current_user["id"])

    if not success:
        user_logger.warning(f"[USER] Account deletion failed for {current_user.get('username')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DELETE_FAILED", "message": "删除账户失败"},
        )

    user_logger.info(f"[USER] Account deleted successfully for {current_user.get('username')}")
