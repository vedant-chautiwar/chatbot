import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserRegisterRequest(BaseModel):
    """Schema for user registration."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")
    name: Optional[str] = Field(default=None, max_length=100, description="Optional display name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email format")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email format")
        return trimmed


class UserResponse(BaseModel):
    """Public user identity representation."""

    id: str = Field(description="Unique user ID")
    email: str = Field(description="User normalized email")
    name: Optional[str] = Field(default=None, description="Display name")
    role: str = Field(default="user", description="Account role")
    created_at: str = Field(description="ISO 8601 registration timestamp")


class TokenResponse(BaseModel):
    """OAuth2 / Bearer token payload returned upon login or registration."""

    access_token: str = Field(description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(description="Authenticated user profile")
