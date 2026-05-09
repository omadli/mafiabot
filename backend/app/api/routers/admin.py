"""Super admin API — dashboard, users, groups, games, stats, audit."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from tortoise.expressions import Q

from app.api.deps import get_current_admin
from app.db.models import (
    AdminAccount,
    AuditLog,
    Game,
    GameStatus,
    Group,
    GroupStats,
    User,
    UserStats,
)
from app.services.audit_service import log_action

router = APIRouter()


# === Dashboard / KPI ===


@router.get("/admin/dashboard")
async def dashboard(admin: AdminAccount = Depends(get_current_admin)) -> dict:
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = await User.all().count()
    total_groups = await Group.all().count()
    active_groups = await Group.filter(is_active=True, is_blocked=False).count()
    total_games = await Game.all().count()
    finished_games = await Game.filter(status=GameStatus.FINISHED).count()
    running_games = await Game.filter(status__in=[GameStatus.WAITING, GameStatus.RUNNING]).count()

    dau = await User.filter(updated_at__gte=day_ago).count()
    wau = await User.filter(updated_at__gte=week_ago).count()
    mau = await User.filter(updated_at__gte=month_ago).count()

    premium_users = await User.filter(is_premium=True).count()
    banned_users = await User.filter(is_banned=True).count()

    return {
        "users": {
            "total": total_users,
            "premium": premium_users,
            "banned": banned_users,
            "premium_rate": round(premium_users / total_users, 4) if total_users else 0,
        },
        "groups": {"total": total_groups, "active": active_groups},
        "games": {
            "total": total_games,
            "finished": finished_games,
            "running": running_games,
        },
        "activity": {"dau": dau, "wau": wau, "mau": mau},
        "generated_at": now.isoformat(),
    }


# === Users ===


class UserListItem(BaseModel):
    id: int
    username: str | None
    first_name: str
    diamonds: int
    dollars: int
    xp: int
    level: int
    is_premium: bool
    is_banned: bool
    games_total: int = 0
    elo: int = 1000
    created_at: datetime


@router.get("/admin/users")
async def list_users(
    admin: AdminAccount = Depends(get_current_admin),
    search: str | None = None,
    is_banned: bool | None = None,
    is_premium: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    qs = User.all()
    if search:
        qs = qs.filter(Q(username__icontains=search) | Q(first_name__icontains=search))
    if is_banned is not None:
        qs = qs.filter(is_banned=is_banned)
    if is_premium is not None:
        qs = qs.filter(is_premium=is_premium)

    total = await qs.count()
    users = await qs.offset((page - 1) * page_size).limit(page_size).order_by("-id")

    items = []
    for u in users:
        stats = await UserStats.get_or_none(user_id=u.id)
        items.append(
            {
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
                "diamonds": u.diamonds,
                "dollars": u.dollars,
                "xp": u.xp,
                "level": u.level,
                "is_premium": u.is_premium,
                "is_banned": u.is_banned,
                "games_total": stats.games_total if stats else 0,
                "elo": stats.elo if stats else 1000,
                "created_at": u.created_at.isoformat(),
            }
        )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/admin/users/{user_id}")
async def get_user(user_id: int, admin: AdminAccount = Depends(get_current_admin)) -> dict:
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    stats = await UserStats.get_or_none(user_id=user_id)
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code,
        "diamonds": user.diamonds,
        "dollars": user.dollars,
        "xp": user.xp,
        "level": user.level,
        "is_premium": user.is_premium,
        "premium_expires_at": (
            user.premium_expires_at.isoformat() if user.premium_expires_at else None
        ),
        "is_banned": user.is_banned,
        "banned_until": user.banned_until.isoformat() if user.banned_until else None,
        "ban_reason": user.ban_reason,
        "afk_warnings": user.afk_warnings,
        "joined_at": user.joined_at.isoformat(),
        "stats": (
            {
                "games_total": stats.games_total,
                "games_won": stats.games_won,
                "games_lost": stats.games_lost,
                "elo": stats.elo,
                "longest_win_streak": stats.longest_win_streak,
                "role_stats": stats.role_stats,
                "citizen_wins": stats.citizen_wins,
                "mafia_wins": stats.mafia_wins,
                "singleton_wins": stats.singleton_wins,
            }
            if stats
            else None
        ),
    }


class BanRequest(BaseModel):
    reason: str = Field(..., max_length=256)
    duration_hours: int | None = None


@router.post("/admin/users/{user_id}/ban")
async def ban_user(
    user_id: int, payload: BanRequest, admin: AdminAccount = Depends(get_current_admin)
) -> dict:
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = True
    user.ban_reason = payload.reason
    user.banned_until = (
        datetime.now(UTC) + timedelta(hours=payload.duration_hours)
        if payload.duration_hours
        else None
    )
    await user.save(update_fields=["is_banned", "ban_reason", "banned_until"])

    await log_action(
        action="user.ban",
        actor=admin,
        target_type="user",
        target_id=str(user_id),
        payload={"reason": payload.reason, "duration_hours": payload.duration_hours},
    )
    return {"ok": True}


@router.post("/admin/users/{user_id}/unban")
async def unban_user(user_id: int, admin: AdminAccount = Depends(get_current_admin)) -> dict:
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = False
    user.banned_until = None
    user.ban_reason = None
    await user.save(update_fields=["is_banned", "banned_until", "ban_reason"])

    await log_action(
        action="user.unban",
        actor=admin,
        target_type="user",
        target_id=str(user_id),
    )
    return {"ok": True}


class GrantDiamondsRequest(BaseModel):
    amount: int = Field(..., gt=0)
    reason: str = Field("admin grant", max_length=256)


@router.post("/admin/users/{user_id}/grant-diamonds")
async def grant_diamonds(
    user_id: int,
    payload: GrantDiamondsRequest,
    admin: AdminAccount = Depends(get_current_admin),
) -> dict:
    from app.db.models import Transaction, TransactionStatus, TransactionType

    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.diamonds += payload.amount
    await user.save(update_fields=["diamonds"])

    await Transaction.create(
        user=user,
        type=TransactionType.ADMIN_GRANT,
        diamonds_amount=payload.amount,
        status=TransactionStatus.COMPLETED,
        note=f"Admin grant: {payload.reason}",
    )
    await log_action(
        action="diamonds.grant",
        actor=admin,
        target_type="user",
        target_id=str(user_id),
        payload={"amount": payload.amount, "reason": payload.reason},
    )
    return {"ok": True, "new_balance": user.diamonds}


class GrantPremiumRequest(BaseModel):
    days: int = Field(..., gt=0, le=365)


@router.post("/admin/users/{user_id}/grant-premium")
async def grant_premium(
    user_id: int,
    payload: GrantPremiumRequest,
    admin: AdminAccount = Depends(get_current_admin),
) -> dict:
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(UTC)
    if user.premium_expires_at and user.premium_expires_at > now:
        user.premium_expires_at = user.premium_expires_at + timedelta(days=payload.days)
    else:
        user.premium_expires_at = now + timedelta(days=payload.days)
    user.is_premium = True
    await user.save(update_fields=["is_premium", "premium_expires_at"])

    await log_action(
        action="premium.grant",
        actor=admin,
        target_type="user",
        target_id=str(user_id),
        payload={"days": payload.days},
    )
    return {"ok": True, "premium_expires_at": user.premium_expires_at.isoformat()}


# === Groups ===


@router.get("/admin/groups")
async def list_groups(
    admin: AdminAccount = Depends(get_current_admin),
    search: str | None = None,
    is_blocked: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    qs = Group.all()
    if search:
        qs = qs.filter(title__icontains=search)
    if is_blocked is not None:
        qs = qs.filter(is_blocked=is_blocked)

    total = await qs.count()
    groups = await qs.offset((page - 1) * page_size).limit(page_size).order_by("-id")

    items = []
    for g in groups:
        gs = await GroupStats.get_or_none(group_id=g.id)
        items.append(
            {
                "id": g.id,
                "title": g.title,
                "is_active": g.is_active,
                "is_blocked": g.is_blocked,
                "onboarding_completed": g.onboarding_completed,
                "total_games": gs.total_games if gs else 0,
                "created_at": g.created_at.isoformat(),
            }
        )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


class BlockGroupRequest(BaseModel):
    reason: str = Field(..., max_length=256)


@router.post("/admin/groups/{group_id}/block")
async def block_group(
    group_id: int,
    payload: BlockGroupRequest,
    admin: AdminAccount = Depends(get_current_admin),
) -> dict:
    group = await Group.get_or_none(id=group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    group.is_blocked = True
    await group.save(update_fields=["is_blocked"])
    await log_action(
        action="group.block",
        actor=admin,
        target_type="group",
        target_id=str(group_id),
        payload={"reason": payload.reason},
    )
    return {"ok": True}


@router.post("/admin/groups/{group_id}/unblock")
async def unblock_group(group_id: int, admin: AdminAccount = Depends(get_current_admin)) -> dict:
    group = await Group.get_or_none(id=group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    group.is_blocked = False
    await group.save(update_fields=["is_blocked"])
    await log_action(
        action="group.unblock",
        actor=admin,
        target_type="group",
        target_id=str(group_id),
    )
    return {"ok": True}


# === Games ===


@router.get("/admin/games")
async def list_games(
    admin: AdminAccount = Depends(get_current_admin),
    status_filter: str | None = Query(None, alias="status"),
    group_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    qs = Game.all()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if group_id:
        qs = qs.filter(group_id=group_id)

    total = await qs.count()
    games = await qs.offset((page - 1) * page_size).limit(page_size).order_by("-started_at")

    items = [
        {
            "id": str(g.id),
            "group_id": g.group_id,
            "status": g.status,
            "winner_team": g.winner_team,
            "started_at": g.started_at.isoformat() if g.started_at else None,
            "finished_at": g.finished_at.isoformat() if g.finished_at else None,
            "bounty_per_winner": g.bounty_per_winner,
        }
        for g in games
    ]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/admin/games/{game_id}")
async def get_game(game_id: UUID, admin: AdminAccount = Depends(get_current_admin)) -> dict:
    game = await Game.get_or_none(id=game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return {
        "id": str(game.id),
        "group_id": game.group_id,
        "status": game.status,
        "winner_team": game.winner_team,
        "started_at": game.started_at.isoformat() if game.started_at else None,
        "finished_at": game.finished_at.isoformat() if game.finished_at else None,
        "history": game.history,
        "settings_snapshot": game.settings_snapshot,
        "bounty_per_winner": game.bounty_per_winner,
        "bounty_pool": game.bounty_pool,
    }


# === Audit log ===


@router.get("/admin/audit")
async def list_audit(
    admin: AdminAccount = Depends(get_current_admin),
    action: str | None = None,
    actor_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    qs = AuditLog.all()
    if action:
        qs = qs.filter(action__icontains=action)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)

    total = await qs.count()
    logs = await qs.offset((page - 1) * page_size).limit(page_size).order_by("-created_at")

    items = [
        {
            "id": str(log.id),
            "actor_id": log.actor_id,
            "actor_admin_id": str(log.actor_admin_id) if log.actor_admin_id else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "payload": log.payload,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# === Me (current admin info) ===


@router.get("/admin/me")
async def me(admin: AdminAccount = Depends(get_current_admin)) -> dict:
    return {
        "id": str(admin.id),
        "username": admin.username,
        "role": admin.role,
        "is_active": admin.is_active,
        "telegram_id": admin.telegram_id,
        "last_login_at": admin.last_login_at.isoformat() if admin.last_login_at else None,
    }
