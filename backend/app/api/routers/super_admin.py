"""Super admin API — Telegram-ID-authenticated endpoints.

Mount at `/api/sa/*`. Every endpoint requires `get_current_super_admin` —
the caller must present a valid X-Telegram-Init-Data header AND their
Telegram user_id must be in SUPER_ADMIN_TELEGRAM_IDS env.

Provides:
  GET  /api/sa/me                       — identity + i18n locale
  GET  /api/sa/global-stats             — KPIs (users/games/groups + winrates)
  GET  /api/sa/role-stats               — per-role aggregate stats
  GET  /api/sa/top-players              — leaderboard (sortable)
  GET  /api/sa/groups                   — all groups + meta
  GET  /api/sa/groups/{group_id}/games  — games history for a group
  GET  /api/sa/groups/{group_id}/settings — read any group's settings
  POST /api/sa/groups/{group_id}/settings — modify any group's settings
  GET  /api/sa/system-settings          — global pricing/rewards/exchange
  POST /api/sa/system-settings          — update SystemSettings
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from tortoise.functions import Avg, Count

from app.api.deps import SuperAdminContext, get_current_super_admin
from app.db.models import (
    Game,
    GameResult,
    Group,
    GroupSettings,
    GroupUserStats,
    User,
    UserStats,
)
from app.services import pricing_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/api/sa", tags=["super-admin"])


# === Identity ===


@router.get("/me")
async def me(sa: SuperAdminContext = Depends(get_current_super_admin)) -> dict:
    """Return identity + UI locale for client-side personalization."""
    return {
        "telegram_id": sa.telegram_id,
        "first_name": sa.first_name,
        "username": sa.username,
        "language_code": sa.language_code,
    }


# === Global stats / dashboard ===


@router.get("/global-stats")
async def global_stats(sa: SuperAdminContext = Depends(get_current_super_admin)) -> dict:
    """All KPIs in one call — for SuperAdmin dashboard."""
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    users_total = await User.all().count()
    users_premium = await User.filter(is_premium=True).count()
    users_banned = await User.filter(is_banned=True).count()
    users_active_24h = await User.filter(updated_at__gte=day_ago).count()
    users_active_7d = await User.filter(updated_at__gte=week_ago).count()
    users_active_30d = await User.filter(updated_at__gte=month_ago).count()

    groups_total = await Group.filter(is_active=True).count()
    groups_blocked = await Group.filter(is_blocked=True).count()
    groups_onboarded = await Group.filter(onboarding_completed=True).count()

    games_total = await Game.all().count()
    games_finished = await Game.filter(status="finished").count()
    games_running = await Game.filter(status="running").count()
    games_cancelled = await Game.filter(status="cancelled").count()
    games_24h = await Game.filter(finished_at__gte=day_ago).count()
    games_7d = await Game.filter(finished_at__gte=week_ago).count()

    # Winrates per team (from GameResult)
    total_results = await GameResult.all().count()
    citizen_wins = await GameResult.filter(team="citizens", won=True).count()
    mafia_wins = await GameResult.filter(team="mafia", won=True).count()
    singleton_wins = await GameResult.filter(team="singleton", won=True).count()

    def _pct(n: int) -> float:
        return round(n / total_results * 100, 1) if total_results else 0.0

    return {
        "generated_at": now.isoformat(),
        "users": {
            "total": users_total,
            "premium": users_premium,
            "banned": users_banned,
            "active_24h": users_active_24h,
            "active_7d": users_active_7d,
            "active_30d": users_active_30d,
        },
        "groups": {
            "total_active": groups_total,
            "blocked": groups_blocked,
            "onboarded": groups_onboarded,
        },
        "games": {
            "total": games_total,
            "finished": games_finished,
            "running": games_running,
            "cancelled": games_cancelled,
            "last_24h": games_24h,
            "last_7d": games_7d,
        },
        "winrates": {
            "total_player_games": total_results,
            "citizen_wins": citizen_wins,
            "mafia_wins": mafia_wins,
            "singleton_wins": singleton_wins,
            "citizen_pct": _pct(citizen_wins),
            "mafia_pct": _pct(mafia_wins),
            "singleton_pct": _pct(singleton_wins),
        },
    }


# === Role stats ===


@router.get("/role-stats")
async def role_stats(sa: SuperAdminContext = Depends(get_current_super_admin)) -> dict:
    """Aggregate stats for every role: games played, wins, win-rate, avg ELO delta."""
    # Aggregate games + average ELO/XP per role
    rows = (
        await GameResult.all()
        .group_by("role")
        .annotate(
            games=Count("id"),
            avg_elo_change=Avg("elo_change"),
            avg_xp=Avg("xp_earned"),
        )
        .values("role", "games", "avg_elo_change", "avg_xp")
    )

    # Wins per role — separate query (Sum on bool isn't portable across DB backends)
    wins_per_role: dict[str, int] = {}
    for r in await GameResult.filter(won=True).all().values("role"):
        wins_per_role[r["role"]] = wins_per_role.get(r["role"], 0) + 1

    out = []
    for row in rows:
        games = row["games"] or 0
        wins = wins_per_role.get(row["role"], 0)
        out.append(
            {
                "role": row["role"],
                "games_played": games,
                "wins": wins,
                "winrate_pct": round(wins / games * 100, 1) if games else 0.0,
                "avg_elo_change": round(row["avg_elo_change"] or 0, 2),
                "avg_xp_earned": round(row["avg_xp"] or 0, 1),
            }
        )

    out.sort(key=lambda x: x["games_played"], reverse=True)
    return {"roles": out}


# === Top players ===


SortKey = Literal["elo", "games_won", "games_total", "longest_win_streak", "level"]


@router.get("/top-players")
async def top_players(
    sa: SuperAdminContext = Depends(get_current_super_admin),
    sort: SortKey = "elo",
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    """Global leaderboard, sortable."""
    stats = await UserStats.all().order_by(f"-{sort}").limit(limit).prefetch_related("user")
    out = []
    for i, s in enumerate(stats, start=1):
        u = s.user
        winrate = round(s.games_won / s.games_total * 100, 1) if s.games_total else 0.0
        out.append(
            {
                "rank": i,
                "user_id": u.id,
                "first_name": u.first_name,
                "username": u.username,
                "is_premium": u.is_premium,
                "level": u.level,
                "xp": s.xp,
                "elo": s.elo,
                "games_total": s.games_total,
                "games_won": s.games_won,
                "winrate_pct": winrate,
                "longest_win_streak": s.longest_win_streak,
                "citizen_wins": s.citizen_wins,
                "mafia_wins": s.mafia_wins,
                "singleton_wins": s.singleton_wins,
            }
        )
    return {"sort": sort, "items": out}


# === Groups + games history ===


@router.get("/groups")
async def list_groups(
    sa: SuperAdminContext = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    """All groups, paginated. Includes onboarding + recent game count."""
    total = await Group.all().count()
    rows = await Group.all().order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
    items = []
    for g in rows:
        games_total = await Game.filter(group_id=g.id).count()
        last_game = await Game.filter(group_id=g.id).order_by("-started_at").first()
        items.append(
            {
                "id": g.id,
                "title": g.title,
                "is_active": g.is_active,
                "is_blocked": g.is_blocked,
                "onboarding_completed": g.onboarding_completed,
                "games_total": games_total,
                "last_game_at": (
                    last_game.started_at.isoformat() if last_game and last_game.started_at else None
                ),
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
        )
    return {"total": total, "page": page, "items": items}


@router.get("/groups/{group_id}/games")
async def group_games(
    group_id: int,
    sa: SuperAdminContext = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    """Games history for a single group."""
    qs = Game.filter(group_id=group_id)
    total = await qs.count()
    rows = await qs.order_by("-started_at").offset((page - 1) * page_size).limit(page_size)
    items = []
    for g in rows:
        history = g.history or {}
        players_count = len(history.get("players", []))
        items.append(
            {
                "id": str(g.id),
                "status": g.status,
                "winner_team": g.winner_team,
                "started_at": g.started_at.isoformat() if g.started_at else None,
                "finished_at": g.finished_at.isoformat() if g.finished_at else None,
                "duration_seconds": (
                    int((g.finished_at - g.started_at).total_seconds())
                    if g.started_at and g.finished_at
                    else None
                ),
                "players_count": players_count,
                "bounty_per_winner": g.bounty_per_winner,
            }
        )
    return {"group_id": group_id, "total": total, "page": page, "items": items}


@router.get("/groups/{group_id}/leaderboard")
async def group_leaderboard(
    group_id: int,
    sa: SuperAdminContext = Depends(get_current_super_admin),
    limit: int = Query(30, ge=1, le=100),
) -> dict:
    """Per-group top players (group-specific ELO)."""
    rows = await GroupUserStats.filter(group_id=group_id).order_by("-elo").limit(limit)
    items = []
    for i, s in enumerate(rows, start=1):
        u = await User.get_or_none(id=s.user_id)  # type: ignore[attr-defined]
        if u is None:
            continue
        items.append(
            {
                "rank": i,
                "user_id": u.id,
                "first_name": u.first_name,
                "username": u.username,
                "elo": s.elo,
                "games_total": s.games_total,
                "games_won": s.games_won,
                "winrate_pct": round(s.games_won / s.games_total * 100, 1)
                if s.games_total
                else 0.0,
            }
        )
    return {"group_id": group_id, "items": items}


# === Group settings remote control ===


@router.get("/groups/{group_id}/settings")
async def get_group_settings(
    group_id: int, sa: SuperAdminContext = Depends(get_current_super_admin)
) -> dict:
    """Read any group's settings (super admin override)."""
    s = await GroupSettings.get_or_none(group_id=group_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {
        "group_id": group_id,
        "language": s.language,
        "roles": s.roles,
        "timings": s.timings,
        "silence": s.silence,
        "items_allowed": s.items_allowed,
        "afk": s.afk,
        "permissions": s.permissions,
        "gameplay": s.gameplay,
        "display": s.display,
        "messages": s.messages,
        "atmosphere_media": s.atmosphere_media,
    }


class UpdateGroupSettingsRequest(BaseModel):
    section: str
    value: Any


@router.post("/groups/{group_id}/settings")
async def update_group_settings(
    group_id: int,
    payload: UpdateGroupSettingsRequest,
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    """Update any group's settings without needing to be an admin in that group."""
    s = await GroupSettings.get_or_none(group_id=group_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Settings not found")

    valid_sections = {
        "language",
        "roles",
        "timings",
        "silence",
        "items_allowed",
        "afk",
        "permissions",
        "gameplay",
        "display",
        "messages",
        "atmosphere_media",
    }
    if payload.section not in valid_sections:
        raise HTTPException(status_code=400, detail=f"Invalid section: {payload.section}")

    from app.services.group_settings_helper import save_settings_fields

    await save_settings_fields(s, **{payload.section: payload.value})

    await log_action(
        action=f"sa.group.settings.{payload.section}",
        target_type="group",
        target_id=str(group_id),
        payload={"section": payload.section, "by_tg_id": sa.telegram_id},
    )
    return {"ok": True, "section": payload.section}


# === System settings (global pricing/rewards/exchange) ===


@router.get("/system-settings")
async def get_system_settings(
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    s = await pricing_service.get_settings(force=True)
    return {
        "item_prices": s.item_prices,
        "rewards": s.rewards,
        "exchange": s.exchange,
        "premium": s.premium,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "updated_by_tg_id": s.updated_by_tg_id,
    }


class UpdateSystemSettingRequest(BaseModel):
    section: Literal["item_prices", "rewards", "exchange", "premium"]
    key: str  # for item_prices, "shield.dollars"
    value: Any


@router.post("/system-settings")
async def update_system_settings(
    payload: UpdateSystemSettingRequest,
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    try:
        await pricing_service.update_setting(
            payload.section, payload.key, payload.value, by_tg_id=sa.telegram_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await log_action(
        action="sa.system.settings.update",
        target_type="system",
        target_id=payload.section,
        payload={"key": payload.key, "value": payload.value, "by_tg_id": sa.telegram_id},
    )
    return {"ok": True, "section": payload.section, "key": payload.key, "value": payload.value}


# === Roles config (which roles are globally enabled by default) ===


@router.get("/role-defaults")
async def get_role_defaults(
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    """Default roles enabled in new groups (from app.db.models.group.DEFAULT_ROLES_ENABLED)."""
    from app.db.models.group import DEFAULT_ROLES_ENABLED

    return {"defaults": DEFAULT_ROLES_ENABLED}


# === Charts ===


@router.get("/charts/elo")
async def chart_elo_distribution(
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    """Global ELO histogram, 7 bins."""
    elo_values: list[int] = await UserStats.all().values_list("elo", flat=True)  # type: ignore[assignment]
    bins = {
        "<800": 0,
        "800-999": 0,
        "1000-1199": 0,
        "1200-1399": 0,
        "1400-1599": 0,
        "1600-1799": 0,
        "1800+": 0,
    }
    for elo in elo_values:
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


@router.get("/charts/games-per-day")
async def chart_games_per_day(
    sa: SuperAdminContext = Depends(get_current_super_admin),
    days: int = Query(30, ge=1, le=90),
) -> dict:
    """Games per day for the last N days. Backfills zero entries."""
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


@router.get("/charts/cohort")
async def chart_cohort_retention(
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    """7d/30d retention for users joined in last 30 days."""
    now = datetime.now(UTC)
    thirty_ago = now - timedelta(days=30)
    seven_ago = now - timedelta(days=7)

    new_users = await User.filter(joined_at__gte=thirty_ago).count()
    if new_users == 0:
        return {
            "new_users": 0,
            "active_7d": 0,
            "active_30d": 0,
            "retention_7d": 0,
            "retention_30d": 0,
        }

    active_7d = await User.filter(joined_at__gte=thirty_ago, updated_at__gte=seven_ago).count()
    active_30d = await User.filter(joined_at__gte=thirty_ago, updated_at__gte=thirty_ago).count()

    return {
        "new_users": new_users,
        "active_7d": active_7d,
        "active_30d": active_30d,
        "retention_7d": round(active_7d / new_users, 3),
        "retention_30d": round(active_30d / new_users, 3),
    }


@router.get("/charts/role-winrates")
async def chart_role_winrates(
    sa: SuperAdminContext = Depends(get_current_super_admin),
) -> dict:
    """Role winrate breakdown for a stacked bar / radar chart.

    Returns top-12 roles by games_played with winrate%. Frontend can
    visualize as horizontal bars sorted by winrate.
    """
    wins_per_role: dict[str, int] = {}
    games_per_role: dict[str, int] = {}
    for r in await GameResult.all().values("role", "won"):
        games_per_role[r["role"]] = games_per_role.get(r["role"], 0) + 1
        if r["won"]:
            wins_per_role[r["role"]] = wins_per_role.get(r["role"], 0) + 1

    items: list[dict[str, Any]] = []
    for role, games in games_per_role.items():
        wins = wins_per_role.get(role, 0)
        items.append(
            {
                "role": role,
                "games": games,
                "wins": wins,
                "winrate_pct": round(wins / games * 100, 1) if games else 0.0,
            }
        )
    items.sort(key=lambda x: x["games"], reverse=True)
    return {"items": items[:12]}
