"""FastAPI dependencies — auth guards.

Three layers of authentication:
  1. JWT-based admin (web panel): get_current_admin → AdminAccount
  2. Telegram WebApp + Telegram-ID-based super admin: get_current_super_admin
     → reads X-Telegram-Init-Data header, validates HMAC, checks user.id
     against SUPER_ADMIN_TELEGRAM_IDS env
  3. WebApp group admin (existing in routers/group.py): require_group_admin
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from loguru import logger

from app.api.auth.jwt_helpers import decode_token
from app.config import settings
from app.db.models import AdminAccount, User
from app.utils.webapp_auth import validate_init_data


async def get_current_admin(
    authorization: str | None = Header(default=None),
) -> AdminAccount:
    """Bearer JWT → AdminAccount."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    admin_id = payload.get("sub")
    if admin_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")

    admin = await AdminAccount.get_or_none(id=admin_id)
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive"
        )
    return admin


def require_role(*allowed_roles: str):
    """Dependency factory — restrict endpoint to specific admin roles."""

    async def _check(admin: AdminAccount = Depends(get_current_admin)) -> AdminAccount:
        if admin.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return admin

    return _check


# === SuperAdmin (Telegram ID-based, via WebApp initData) ===


@dataclass
class SuperAdminContext:
    """Container for authenticated super admin info."""

    telegram_id: int
    first_name: str
    username: str | None
    language_code: str  # for i18n in API responses


async def get_current_super_admin(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_sa_token: str | None = Header(default=None, alias="X-SA-Token"),
) -> SuperAdminContext:
    """Identify the caller as a super admin via Telegram WebApp initData
    OR fall back to JWT-style X-SA-Token (issued separately, see below).

    Rules:
      1. Parse and validate X-Telegram-Init-Data via HMAC (utils/webapp_auth)
      2. Extract user.id from the parsed payload
      3. Confirm user.id is in settings.super_admin_ids
      4. Optionally: in DEBUG mode, accept X-SA-Token=<dev-secret> for testing

    Returns SuperAdminContext (telegram_id, first_name, username, language_code).
    Raises 401 (missing) / 403 (not a super admin).
    """
    # DEBUG bypass: X-SA-Token with the secret_key value lets local dev curl work
    if settings.debug and x_sa_token == settings.secret_key.get_secret_value():
        # Use the first configured super admin ID as the test identity
        ids = list(settings.super_admin_ids)
        if not ids:
            raise HTTPException(
                status_code=503,
                detail="DEBUG bypass needs at least one SUPER_ADMIN_TELEGRAM_IDS entry",
            )
        tg_id = ids[0]
        user = await User.get_or_none(id=tg_id)
        return SuperAdminContext(
            telegram_id=tg_id,
            first_name=(user.first_name if user else "DevSA"),
            username=(user.username if user else None),
            language_code=(user.language_code if user and user.language_code else "uz"),
        )

    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data header")

    parsed = validate_init_data(x_telegram_init_data)
    if parsed is None:
        raise HTTPException(status_code=401, detail="Invalid or expired init data")

    user_obj = parsed.get("user")
    if not isinstance(user_obj, dict) or "id" not in user_obj:
        raise HTTPException(status_code=400, detail="Invalid user payload in init data")

    tg_id = int(user_obj["id"])
    if tg_id not in settings.super_admin_ids:
        logger.warning(f"Non-super-admin tried to access /api/sa: tg_id={tg_id}")
        raise HTTPException(status_code=403, detail="Super admin access required")

    # Fetch language from User record if available; fallback to initData
    user = await User.get_or_none(id=tg_id)
    lang = (
        (user.language_code if user and user.language_code else None)
        or user_obj.get("language_code")
        or "uz"
    )
    if lang not in ("uz", "ru", "en"):
        lang = "uz"

    return SuperAdminContext(
        telegram_id=tg_id,
        first_name=user_obj.get("first_name", "SuperAdmin"),
        username=user_obj.get("username"),
        language_code=lang,
    )
