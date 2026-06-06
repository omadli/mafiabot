"""Group settings API — for Telegram WebApp (group admins only)."""

from __future__ import annotations

from uuid import UUID

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
        "language": s.language,  # type: ignore[attr-defined,var-annotated,arg-type]
        "roles": s.roles,  # type: ignore[attr-defined,var-annotated,arg-type]
        "timings": s.timings,  # type: ignore[attr-defined,var-annotated,arg-type]
        "silence": s.silence,  # type: ignore[attr-defined,var-annotated,arg-type]
        "items_allowed": s.items_allowed,  # type: ignore[attr-defined,var-annotated,arg-type]
        "role_distribution": s.role_distribution,  # type: ignore[attr-defined,var-annotated,arg-type]
        "afk": s.afk,  # type: ignore[attr-defined,var-annotated,arg-type]
        "permissions": s.permissions,  # type: ignore[attr-defined,var-annotated,arg-type]
        "gameplay": s.gameplay,  # type: ignore[attr-defined,var-annotated,arg-type]
        "display": s.display,  # type: ignore[attr-defined,var-annotated,arg-type]
        "messages": s.messages,  # type: ignore[attr-defined,var-annotated,arg-type]
        "atmosphere_media": s.atmosphere_media,  # type: ignore[attr-defined,var-annotated,arg-type]
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

    from app.db.models import GroupSettings
    from app.services.group_settings_helper import save_settings_fields

    group = await Group.get_or_none(id=group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    s = await GroupSettings.get_or_none(group_id=group_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")

    if payload.section == "language" and (
        not isinstance(payload.value, str) or len(payload.value) > 8
    ):
        raise HTTPException(status_code=400, detail="Invalid language code")

    await save_settings_fields(s, **{payload.section: payload.value})

    await log_action(
        action=f"group.settings.{payload.section}",
        target_type="group",
        target_id=str(group_id),
        payload={"section": payload.section, "user_id": auth.user_id},
    )
    return {"ok": True, "section": payload.section}


@router.get("/group/{group_id}/leaderboard")
async def group_leaderboard(
    group_id: int,
    page: int = 1,
    page_size: int = 30,
) -> dict:
    """Top players in this group, paginated.

    `total` is returned so the WebApp can render page controls without a
    second round-trip. `page_size` is clamped to [1, 100] to keep payloads
    bounded.
    """
    from app.db.models import GroupUserStats

    page = max(page, 1)
    page_size = max(1, min(page_size, 100))

    total = await GroupUserStats.filter(group_id=group_id).count()

    rows = (
        await GroupUserStats.filter(group_id=group_id)
        .order_by("-elo")
        .offset((page - 1) * page_size)
        .limit(page_size)
        .prefetch_related("user")
        .all()
    )

    base_rank = (page - 1) * page_size
    items = []
    for idx, r in enumerate(rows, start=1):
        items.append(
            {
                "rank": base_rank + idx,
                "user_id": r.user.id,
                "first_name": r.user.first_name,
                "username": r.user.username,
                "elo": r.elo,
                "games_total": r.games_total,
                "games_won": r.games_won,
                "winrate": (round(r.games_won / r.games_total, 3) if r.games_total else 0),
            }
        )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/group/{group_id}/messages")
async def list_group_messages(
    group_id: int,
    auth: WebAppAuthData = Depends(require_group_admin),
) -> dict:
    """Curated overridable message templates for the WebApp editor.

    Returns each key with its default (from .ftl in the group's locale)
    and the current override (from `GroupSettings.messages`). Read uses
    the group's own language so admins see the same text the players do.
    """
    if auth.chat_id != group_id:
        raise HTTPException(status_code=403, detail="Chat ID mismatch")

    from app.services.message_templates import list_templates

    group = await Group.get_or_none(id=group_id).prefetch_related("settings")
    if group is None or group.settings is None:
        raise HTTPException(status_code=404, detail="Group not found")
    locale: str = group.settings.language  # type: ignore[attr-defined]
    overrides: dict = group.settings.messages or {}  # type: ignore[attr-defined]
    return {"locale": locale, "items": list_templates(locale, overrides)}


class MessageOverridesRequest(BaseModel):
    overrides: dict = Field(default_factory=dict)


@router.post("/group/{group_id}/messages")
async def save_group_messages(
    group_id: int,
    payload: MessageOverridesRequest,
    auth: WebAppAuthData = Depends(require_group_admin),
) -> dict:
    """Replace the whole `messages` JSON. Empty string overrides are
    pruned so the default falls through, keeping the JSON minimal."""
    if auth.chat_id != group_id:
        raise HTTPException(status_code=403, detail="Chat ID mismatch")

    from app.db.models import GroupSettings
    from app.services.group_settings_helper import save_settings_fields
    from app.services.message_templates import OVERRIDABLE_MESSAGES

    allowed_keys = {spec["key"] for spec in OVERRIDABLE_MESSAGES}
    cleaned: dict[str, str] = {}
    for k, v in payload.overrides.items():
        if k not in allowed_keys:
            continue
        if not isinstance(v, str):
            raise HTTPException(status_code=400, detail=f"Override for '{k}' must be a string")
        v = v.strip()
        if v:
            cleaned[k] = v

    s = await GroupSettings.get_or_none(group_id=group_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    await save_settings_fields(s, messages=cleaned)

    await log_action(
        action="group.messages.update",
        target_type="group",
        target_id=str(group_id),
        payload={"keys": list(cleaned.keys()), "user_id": auth.user_id},
    )
    return {"ok": True, "overrides": cleaned}


@router.post("/group/{group_id}/atmosphere_media/clear")
async def clear_atmosphere_media(
    group_id: int,
    event: str,
    auth: WebAppAuthData = Depends(require_group_admin),
) -> dict:
    """Clear a single atmosphere-media slot. New uploads still go through
    the bot's `/setatmosphere` command — the WebApp only exposes view +
    clear because Telegram WebApps can't directly attach files to the
    bot's `file_id` namespace."""
    if auth.chat_id != group_id:
        raise HTTPException(status_code=403, detail="Chat ID mismatch")

    from app.db.models import GroupSettings
    from app.services.group_settings_helper import save_settings_fields

    s = await GroupSettings.get_or_none(group_id=group_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    media: dict = dict(s.atmosphere_media or {})  # type: ignore[attr-defined]
    if event not in media:
        return {"ok": True, "cleared": False}
    media.pop(event, None)
    await save_settings_fields(s, atmosphere_media=media)
    await log_action(
        action="group.atmosphere.clear",
        target_type="group",
        target_id=str(group_id),
        payload={"event": event, "user_id": auth.user_id},
    )
    return {"ok": True, "cleared": True}


@router.get("/group/{group_id}/history")
async def group_history(
    group_id: int,
    page: int = 1,
    page_size: int = 20,
    auth: WebAppAuthData = Depends(require_group_admin),
) -> dict:
    """Recent FINISHED games in this group. Admin-only — exposes
    finished-game metadata (winner team, durations, player counts) that
    isn't otherwise visible from the bot.
    """
    if auth.chat_id != group_id:
        raise HTTPException(status_code=403, detail="Chat ID mismatch")

    from app.db.models import Game, GameStatus

    page = max(page, 1)
    page_size = max(1, min(page_size, 50))

    base_qs = Game.filter(group_id=group_id, status=GameStatus.FINISHED)
    total = await base_qs.count()

    rows = (
        await base_qs.order_by("-started_at").offset((page - 1) * page_size).limit(page_size).all()
    )

    items = []
    for g in rows:
        duration_sec: int | None = None
        if g.started_at and g.finished_at:
            duration_sec = int((g.finished_at - g.started_at).total_seconds())
        history = g.history or {}
        players_list = history.get("players") or []
        # `to_history_dict()` doesn't emit a `final_alive` array; survivors
        # are flagged in-place via `alive=True` on each player snapshot.
        alive_count = sum(1 for p in players_list if p.get("alive"))
        items.append(
            {
                "id": str(g.id),
                "winner_team": g.winner_team.value if g.winner_team else None,
                "started_at": g.started_at.isoformat() if g.started_at else None,
                "finished_at": g.finished_at.isoformat() if g.finished_at else None,
                "duration_seconds": duration_sec,
                "player_count": len(players_list),
                "alive_at_end": alive_count,
                "bounty_per_winner": g.bounty_per_winner,
            }
        )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/group/{group_id}/history/{game_id}")
async def group_history_detail(
    group_id: int,
    game_id: UUID,
    auth: WebAppAuthData = Depends(require_group_admin),
) -> dict:
    """Full replay of one finished game in this group.

    Returns the raw `Game.history` JSON (players with roles, per-round night
    actions / deaths / votes / hanged / last words) plus summary metadata.
    Scoped to the group so an admin can only read their own group's games;
    shape mirrors the SA `/sa/games/{id}` replay endpoint so the WebApp can
    reuse the same renderer.
    """
    if auth.chat_id != group_id:
        raise HTTPException(status_code=403, detail="Chat ID mismatch")

    from app.db.models import Game

    game = await Game.get_or_none(id=game_id, group_id=group_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    duration_sec: int | None = None
    if game.started_at and game.finished_at:
        duration_sec = int((game.finished_at - game.started_at).total_seconds())

    return {
        "id": str(game.id),
        "group_id": group_id,
        "status": game.status.value if game.status else None,
        "winner_team": game.winner_team.value if game.winner_team else None,
        "started_at": game.started_at.isoformat() if game.started_at else None,
        "finished_at": game.finished_at.isoformat() if game.finished_at else None,
        "duration_seconds": duration_sec,
        "bounty_per_winner": game.bounty_per_winner,
        "bounty_pool": game.bounty_pool,
        "history": game.history,
    }
