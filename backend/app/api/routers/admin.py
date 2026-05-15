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


@router.get("/admin/groups/{group_id}/live")
async def get_group_live_state(
    group_id: int, admin: AdminAccount = Depends(get_current_admin)
) -> dict:
    """Live snapshot of whatever game (if any) is in progress in this group.

    Pulls from Redis. Returns 404 if no live game. Pair this with the
    per-group WebSocket `/ws/admin/group/{gid}` for delta updates.
    """
    from app.services import game_service

    state = await game_service.load_state(group_id)
    if state is None:
        raise HTTPException(status_code=404, detail="No active game in this group")
    import json as _json

    return _json.loads(state.to_redis())


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


# === Charts ===


@router.get("/admin/charts/elo")
async def chart_elo_distribution(admin: AdminAccount = Depends(get_current_admin)) -> dict:
    """ELO histogram bins."""
    elo_values = await UserStats.all().values_list("elo", flat=True)
    bins = {
        "<800": 0,
        "800-999": 0,
        "1000-1199": 0,
        "1200-1399": 0,
        "1400-1599": 0,
        "1600-1799": 0,
        "1800+": 0,
    }
    for _elo in elo_values:
        elo: int = _elo  # type: ignore[assignment]
        if elo < 800:
            bins["<800"] += 1
        elif elo < 1000:
            bins["800-999"] += 1
        elif elo < 1200:
            bins["1000-1199"] += 1
        elif elo < 1400:
            bins["1200-1399"] += 1
        elif elo < 1600:
            bins["1400-1599"] += 1
        elif elo < 1800:
            bins["1600-1799"] += 1
        else:
            bins["1800+"] += 1
    return {"bins": [{"label": k, "count": v} for k, v in bins.items()]}


@router.get("/admin/charts/cohort")
async def chart_cohort_retention(admin: AdminAccount = Depends(get_current_admin)) -> dict:
    """Retention for users joined in last 30 days."""
    now = datetime.now(UTC)
    thirty_ago = now - timedelta(days=30)
    seven_ago = now - timedelta(days=7)

    new_users = await User.filter(joined_at__gte=thirty_ago).count()
    if new_users == 0:
        return {"new_users": 0, "retention_7d": 0, "retention_30d": 0}

    active_7d = await User.filter(joined_at__gte=thirty_ago, updated_at__gte=seven_ago).count()
    active_30d = await User.filter(joined_at__gte=thirty_ago, updated_at__gte=thirty_ago).count()

    return {
        "new_users": new_users,
        "active_7d": active_7d,
        "active_30d": active_30d,
        "retention_7d": round(active_7d / new_users, 3),
        "retention_30d": round(active_30d / new_users, 3),
    }


@router.get("/admin/charts/games-per-day")
async def chart_games_per_day(
    admin: AdminAccount = Depends(get_current_admin),
    days: int = Query(30, ge=1, le=90),
) -> dict:
    """Games per day for last N days."""
    now = datetime.now(UTC)
    since = now - timedelta(days=days)
    games = await Game.filter(started_at__gte=since).all()

    by_day: dict[str, int] = {}
    for g in games:
        if g.started_at is None:
            continue
        key = g.started_at.date().isoformat()
        by_day[key] = by_day.get(key, 0) + 1

    series = []
    for i in range(days):
        d = (now - timedelta(days=days - 1 - i)).date()
        key = d.isoformat()
        series.append({"date": key, "count": by_day.get(key, 0)})
    return {"series": series}


# === User extras: transactions, games, achievements ===


@router.get("/admin/users/{user_id}/transactions")
async def user_transactions(
    user_id: int,
    admin: AdminAccount = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    from app.db.models import Transaction

    qs = Transaction.filter(user_id=user_id)
    total = await qs.count()
    rows = await qs.offset((page - 1) * page_size).limit(page_size).order_by("-created_at")

    items = [
        {
            "id": str(t.id),
            "type": t.type,
            "stars_amount": t.stars_amount,
            "diamonds_amount": t.diamonds_amount,
            "dollars_amount": t.dollars_amount,
            "item": t.item,
            "status": t.status,
            "note": t.note,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]
    return {"total": total, "page": page, "items": items}


@router.get("/admin/users/{user_id}/games")
async def user_games(
    user_id: int,
    admin: AdminAccount = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    from app.db.models import GameResult

    qs = GameResult.filter(user_id=user_id)
    total = await qs.count()
    rows = await qs.offset((page - 1) * page_size).limit(page_size).order_by("-played_at")

    items = [
        {
            "id": str(r.id),
            "game_id": str(r.game_id),
            "group_id": r.group_id,
            "role": r.role,
            "team": r.team,
            "won": r.won,
            "survived": r.survived,
            "death_reason": r.death_reason,
            "elo_before": r.elo_before,
            "elo_after": r.elo_after,
            "elo_change": r.elo_change,
            "xp_earned": r.xp_earned,
            "played_at": r.played_at.isoformat(),
        }
        for r in rows
    ]
    return {"total": total, "page": page, "items": items}


@router.get("/admin/users/{user_id}/achievements")
async def user_achievements(user_id: int, admin: AdminAccount = Depends(get_current_admin)) -> dict:
    from app.db.models import UserAchievement

    rows = await UserAchievement.filter(user_id=user_id).order_by("-unlocked_at").all()
    items = []
    for r in rows:
        await r.fetch_related("achievement")
        items.append(
            {
                "code": r.achievement.code,
                "name_i18n": r.achievement.name_i18n,
                "icon": r.achievement.icon,
                "diamonds_reward": r.achievement.diamonds_reward,
                "unlocked_at": r.unlocked_at.isoformat(),
            }
        )
    return {"items": items}


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
