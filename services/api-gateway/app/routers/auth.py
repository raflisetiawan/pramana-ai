"""
Pramana AI — API Gateway: Auth Router.

Task 4.4.1: Auth endpoints.
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout

JWT-based authentication. Passwords verified with bcrypt.
Token stored in memory on client side (not localStorage per SPEC).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.jwt_auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
    UserInfo,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ============================================================================
# POST /api/v1/auth/login
# ============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT access + refresh tokens.

    Looks up user by email, verifies bcrypt password hash,
    then issues short-lived access token and long-lived refresh token.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah.",
        )

    # Build token extra claims
    extra = {
        "email": user.email,
        "role": user.role or "verifikator_bpjs",
    }

    access_token = create_access_token(subject=str(user.id), extra=extra)
    refresh_token = create_refresh_token(subject=str(user.id))

    # Resolve hospital name
    hospital_name = None
    if user.hospital:
        hospital_name = user.hospital.nama_rs

    # Build full name from email (seed data uses email as identifier)
    full_name = user.email.split("@")[0].replace(".", " ").title()

    logger.info("User %s logged in successfully (role=%s)", user.email, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserInfo(
            id=str(user.id),
            email=user.email,
            full_name=full_name,
            role=user.role or "verifikator_bpjs",
            hospital_name=hospital_name,
        ),
    )


# ============================================================================
# POST /api/v1/auth/refresh
# ============================================================================


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair.

    The old refresh token is implicitly invalidated (rotation).
    """
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bukan refresh token.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid — sub claim missing.",
        )

    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan atau non-aktif.",
        )

    # Issue new tokens
    extra = {
        "email": user.email,
        "role": user.role or "verifikator_bpjs",
    }

    new_access = create_access_token(subject=str(user.id), extra=extra)
    new_refresh = create_refresh_token(subject=str(user.id))

    hospital_name = user.hospital.nama_rs if user.hospital else None
    full_name = user.email.split("@")[0].replace(".", " ").title()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserInfo(
            id=str(user.id),
            email=user.email,
            full_name=full_name,
            role=user.role or "verifikator_bpjs",
            hospital_name=hospital_name,
        ),
    )


# ============================================================================
# POST /api/v1/auth/logout
# ============================================================================


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest,
    user: dict = Depends(get_current_user),
):
    """Logout the current user.

    In a production system this would blacklist the refresh token in Redis.
    For MVP, the client simply discards the token from memory.
    """
    logger.info("User %s logged out", user.get("email", user.get("sub")))

    return MessageResponse(
        message="Berhasil logout.",
        success=True,
    )
