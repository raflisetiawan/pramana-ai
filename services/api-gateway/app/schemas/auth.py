"""
Pramana AI — Auth Pydantic Schemas.

Request/response models for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login body."""

    email: str = Field(..., min_length=5, max_length=200, examples=["rina@bpjs.go.id"])
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """Response for successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserInfo"


class UserInfo(BaseModel):
    """Minimal user info returned with token."""

    id: str
    email: str
    full_name: str
    role: str
    hospital_name: str | None = None


class RefreshRequest(BaseModel):
    """POST /api/v1/auth/refresh body."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """POST /api/v1/auth/logout body."""

    refresh_token: str | None = None


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    success: bool = True
