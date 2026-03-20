"""User models for request/response validation."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Request model for user registration."""

    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Request model for user login."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserPreferences(BaseModel):
    """User preferences settings."""

    default_currency: str = "CNY"
    favorite_platforms: list[str] = []
    budget_range: dict[str, int] = {"min": 0, "max": 0}
    notification_enabled: bool = False


class UserResponse(BaseModel):
    """Response model for user information."""

    id: str
    username: str
    email: str
    created_at: datetime | None = None
    last_login: datetime | None = None
    is_active: bool = True
    role: str = "user"
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class UserInDB(BaseModel):
    """Internal model for user stored in database."""

    username: str
    email: str
    password_hash: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None
    is_active: bool = True
    role: str = "user"
    preferences: dict[str, Any] = Field(default_factory=dict)


class TokenResponse(BaseModel):
    """Response model for authentication token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RegisterResponse(BaseModel):
    """Response model for successful registration."""

    message: str = "注册成功"
    user_id: str


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail
