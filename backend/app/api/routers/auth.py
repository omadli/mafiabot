"""Admin auth endpoints — login (username+password) + 1-time token."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel, Field

from app.api.auth.jwt_helpers import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.db.models import AdminAccount, OneTimeToken, User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class OneTimeLoginRequest(BaseModel):
    token: str = Field(..., min_length=8, max_length=64)


# === Login (username + password) ===


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(payload: LoginRequest, request: Request) -> TokenResponse:
    admin = await AdminAccount.get_or_none(username=payload.username)
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    admin.last_login_at = datetime.now(UTC)
    await admin.save(update_fields=["last_login_at"])

    token = create_access_token(str(admin.id), role=admin.role)
    logger.info(
        f"Admin login: {admin.username} from {request.client.host if request.client else '?'}"
    )

    return TokenResponse(access_token=token, role=admin.role, username=admin.username)


# === 1-time token login (Telegram bot → admin panel) ===


@router.post("/admin/login/one-time", response_model=TokenResponse)
async def admin_login_one_time(payload: OneTimeLoginRequest, request: Request) -> TokenResponse:
    """Login via 1-time token issued by bot to whitelisted Telegram user."""
    one_time = await OneTimeToken.get_or_none(token=payload.token)
    if one_time is None:
        raise HTTPException(status_code=400, detail="Invalid token")
    if one_time.used:
        raise HTTPException(status_code=400, detail="Token already used")
    if one_time.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Token expired")

    await one_time.fetch_related("user")
    user = one_time.user

    # Find linked AdminAccount or create one
    admin = await AdminAccount.get_or_none(telegram_id=user.id)
    if admin is None:
        raise HTTPException(status_code=403, detail="No admin account linked to this user")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account inactive")

    one_time.used = True
    one_time.used_ip = request.client.host if request.client else None
    await one_time.save(update_fields=["used", "used_ip"])

    admin.last_login_at = datetime.now(UTC)
    await admin.save(update_fields=["last_login_at"])

    token = create_access_token(str(admin.id), role=admin.role)
    logger.info(f"Admin one-time login: {admin.username} (user_id={user.id})")
    return TokenResponse(access_token=token, role=admin.role, username=admin.username)


# === Default admin account seeding ===


async def seed_default_admin() -> None:
    """Create default admin from .env if no admins exist."""
    count = await AdminAccount.all().count()
    if count > 0:
        return
    username = settings.admin_default_username
    password = settings.admin_default_password.get_secret_value()
    await AdminAccount.create(
        username=username,
        password_hash=hash_password(password),
        role="superadmin",
        is_active=True,
    )
    logger.warning(f"Seeded default admin: {username} (CHANGE PASSWORD IN PRODUCTION!)")


# === 1-time token issuance from bot side ===


async def issue_one_time_token(user: User, ttl_seconds: int = 300) -> str:
    """Generate a 1-time login token for a user (called by bot's /admin command)."""
    token_value = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
    await OneTimeToken.create(
        token=token_value,
        user=user,
        expires_at=expires,
        used=False,
    )
    return token_value
