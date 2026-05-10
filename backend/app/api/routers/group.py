"""Group settings API — for Telegram WebApp (group admins only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.config import settings
from app.db.models import Group
from app.services.audit_service import log_action
from app.utils.webapp_auth import validate_init_data

router = APIRouter()


class WebAppAuthData(BaseModel):
    user_id: int
    chat_id: int


async def validate_webapp(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_chat_id: int | None = Header(default=None, alias="X-Chat-Id"),
) -> WebAppAuthData:
    """Validate Telegram WebApp initData. In DEBUG mode, X-Chat-Id alone is enough."""
    if not x_telegram_init_data:
        if settings.debug and x_chat_id is not None:
            return WebAppAuthData(user_id=0, chat_id=x_chat_id)
        raise HTTPException(status_code=401, detail="Missing init data")
    if x_chat_id is None:
        raise HTTPException(status_code=400, detail="Missing X-Chat-Id header")

    parsed = validate_init_data(x_telegram_init_data)
    if parsed is None:
        raise HTTPException(status_code=401, detail="Invalid init data")

    user_obj = parsed.get("user", {})
    if not isinstance(user_obj, dict) or "id" not in user_obj:
        raise HTTPException(status_code=400, detail="Invalid user payload")

    return WebAppAuthData(user_id=user_obj["id"], chat_id=x_chat_id)


async def require_group_admin(
    auth: WebAppAuthData = Depends(validate_webapp),
) -> WebAppAuthData:
    """Verify the authenticated user is admin in the target group via Bot API."""
    if auth.user_id == 0:
        return auth  # dev mode

    from app.main import bot

    if bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    try:
        member = await bot.get_chat_member(auth.chat_id, auth.user_id)
        if member.status not in ("creator", "administrator"):
            raise HTTPException(status_code=403, detail="Group admin required")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Group admin check failed: {e}")
        raise HTTPException(status_code=403, detail="Could not verify admin status")
    return auth


@router.get("/group/{group_id}/settings")
async def get_group_settings(group_id: int) -> dict:
    """Public read — anyone can view group settings."""
    group = await Group.get_or_none(id=group_id).prefetch_related("settings")
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    s = group.settings
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {
        "group_id": group.id,
        "title": group.title,
        "language": s.language,
        "roles": s.roles,
        "timings": s.timings,
        "silence": s.silence,
        "items_allowed": s.items_allowed,
        "role_distribution": s.role_distribution,
        "afk": s.afk,
        "permissions": s.permissions,
        "gameplay": s.gameplay,
        "display": s.display,
        "messages": s.messages,
        "atmosphere_media": s.atmosphere_media,
    }


class UpdateSettingsRequest(BaseModel):
    section: str = Field(
        ...,
        pattern="^(roles|timings|silence|items_allowed|role_distribution|afk|permissions|gameplay|display|messages|atmosphere_media|language)$",
    )
    value: dict | str


@router.post("/group/{group_id}/settings")
async def update_group_settings(
    group_id: int,
    payload: UpdateSettingsRequest,
    auth: WebAppAuthData = Depends(require_group_admin),
) -> dict:
    """Update a settings section. Requires group admin via WebApp initData."""
    if auth.chat_id != group_id:
        raise HTTPException(status_code=403, detail="Chat ID mismatch")

    group = await Group.get_or_none(id=group_id).prefetch_related("settings")
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    s = group.settings
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")

    if payload.section == "language":
        if not isinstance(payload.value, str) or len(payload.value) > 8:
            raise HTTPException(status_code=400, detail="Invalid language code")
        s.language = payload.value
        await s.save(update_fields=["language"])
    else:
        setattr(s, payload.section, payload.value)
        await s.save(update_fields=[payload.section])

    await log_action(
        action=f"group.settings.{payload.section}",
        target_type="group",
        target_id=str(group_id),
        payload={"section": payload.section, "user_id": auth.user_id},
    )
    return {"ok": True, "section": payload.section}


@router.get("/group/{group_id}/leaderboard")
async def group_leaderboard(group_id: int, limit: int = 10) -> dict:
    from app.db.models import GroupUserStats

    rows = (
        await GroupUserStats.filter(group_id=group_id).order_by("-elo").limit(min(limit, 100)).all()
    )

    items = []
    for r in rows:
        await r.fetch_related("user")
        items.append(
            {
                "user_id": r.user.id,
                "first_name": r.user.first_name,
                "username": r.user.username,
                "elo": r.elo,
                "games_total": r.games_total,
                "games_won": r.games_won,
                "winrate": (round(r.games_won / r.games_total, 3) if r.games_total else 0),
            }
        )
    return {"items": items}
