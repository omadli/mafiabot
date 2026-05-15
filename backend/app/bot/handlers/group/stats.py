"""Statistics bot commands: /stats, /top, /profile, /group_stats, /global_top."""

from __future__ import annotations

from datetime import UTC

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.db.models import GroupStats, GroupUserStats, User, UserStats
from app.services.i18n_service import Translator
from app.services.messaging import player_mention, role_emoji_name

router = Router(name="stats")


# === /stats — shaxsiy global ===


@router.message(Command("stats", "mystats", prefix="/!"))
async def cmd_stats(message: Message, user: User, _: Translator, command: CommandObject) -> None:
    """Shaxsiy statistika."""
    # Optional filter: /stats role komissar
    args = (command.args or "").strip().lower().split()
    if args and args[0] == "role" and len(args) > 1:
        await _show_role_stats(message, user, args[1], _)
        return
    if args and args[0] in ("day", "week", "month"):
        await _show_period_stats(message, user, args[0], _)
        return

    stats = await UserStats.get_or_none(user=user)
    if stats is None or stats.games_total == 0:
        await message.answer(_("stats-no-games"))
        return

    text = _format_user_stats(user, stats, _)
    await message.answer(text)


async def _show_period_stats(message: Message, user: User, period: str, _: Translator) -> None:
    """Show user's stats for last day / week / month from snapshots + recent results."""
    from datetime import datetime, timedelta

    from app.db.models import GameResult, StatsPeriodSnapshot

    period_map = {"day": "daily", "week": "weekly", "month": "monthly"}
    snap_period = period_map[period]

    # Find most recent snapshot for this period (global)
    snap = (
        await StatsPeriodSnapshot.filter(user=user, group=None, period=snap_period)
        .order_by("-period_start")
        .first()
    )

    if snap is None or snap.games_total == 0:
        # Fallback: compute from GameResult
        now = datetime.now(UTC)
        delta = {"day": timedelta(days=1), "week": timedelta(days=7), "month": timedelta(days=30)}[
            period
        ]
        since = now - delta
        results = await GameResult.filter(user=user, played_at__gte=since).all()
        if not results:
            await message.answer(_("stats-period-empty", period=period))
            return
        games = len(results)
        wins = sum(1 for r in results if r.won)
        elo_change = sum(r.elo_change for r in results)
        xp = sum(r.xp_earned for r in results)
        text = _(
            "stats-period",
            period=period,
            games=games,
            wins=wins,
            winrate=int((wins / games) * 100) if games else 0,
            elo_change=elo_change,
            xp=xp,
        )
    else:
        text = _(
            "stats-period",
            period=period,
            games=snap.games_total,
            wins=snap.games_won,
            winrate=int((snap.games_won / snap.games_total) * 100) if snap.games_total else 0,
            elo_change=snap.elo_change,
            xp=snap.xp_earned,
        )
    await message.answer(text)


async def _show_role_stats(message: Message, user: User, role: str, _: Translator) -> None:
    stats = await UserStats.get_or_none(user=user)
    if stats is None or not stats.role_stats:
        await message.answer(_("stats-no-games"))
        return
    role_data = stats.role_stats.get(role)
    if not role_data:
        await message.answer(_("stats-role-no-data", role=role))
        return
    text = _(
        "stats-role-detail",
        role=role_emoji_name(role, "uz"),
        games=role_data.get("games", 0),
        wins=role_data.get("wins", 0),
        winrate=int(role_data.get("winrate", 0) * 100),
        elo=role_data.get("elo", 1000),
    )
    await message.answer(text)


def _format_user_stats(user: User, stats: UserStats, _: Translator) -> str:
    winrate = int((stats.games_won / stats.games_total) * 100) if stats.games_total else 0

    # Top 3 roles by games
    role_lines = []
    if stats.role_stats:
        sorted_roles = sorted(
            stats.role_stats.items(), key=lambda x: x[1].get("games", 0), reverse=True
        )[:3]
        for role_code, data in sorted_roles:
            wr = int(data.get("winrate", 0) * 100)
            role_lines.append(
                f"  • {role_emoji_name(role_code, 'uz')}: {data.get('games', 0)} ta · WR {wr}%"
            )
    role_section = "\n".join(role_lines) if role_lines else _("stats-no-role-data")

    return _(
        "stats-personal",
        name=user.first_name,
        games=stats.games_total,
        wins=stats.games_won,
        losses=stats.games_lost,
        winrate=winrate,
        elo=stats.elo,
        xp=stats.xp,
        level=stats.level,
        streak=stats.current_win_streak,
        longest=stats.longest_win_streak,
        top_roles=role_section,
        citizen_games=stats.citizen_games,
        citizen_wins=stats.citizen_wins,
        mafia_games=stats.mafia_games,
        mafia_wins=stats.mafia_wins,
        singleton_games=stats.singleton_games,
        singleton_wins=stats.singleton_wins,
    )


async def _user_locale(user: User) -> str | None:
    return user.language_code


# === /top — guruh leaderboard ===


@router.message(Command("top", prefix="/!"))
async def cmd_top(message: Message, _: Translator, command: CommandObject) -> None:
    """Guruh leaderboard. Default: ELO. Boshqa: /top wins|xp|winrate."""
    chat_id = message.chat.id
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_("top-group-only"))
        return

    sort_key = (command.args or "elo").strip().lower()
    valid = {"elo", "wins", "xp", "winrate"}
    if sort_key not in valid:
        sort_key = "elo"

    if sort_key == "winrate":
        # Manual: load all and sort by computed winrate
        gus_list = await GroupUserStats.filter(group_id=chat_id, games_total__gte=5).all()
        gus_list.sort(
            key=lambda g: (g.games_won / g.games_total) if g.games_total else 0,
            reverse=True,
        )
        gus_list = gus_list[:10]
    else:
        ordering = f"-{sort_key}" if sort_key != "wins" else "-games_won"
        gus_list = await GroupUserStats.filter(group_id=chat_id).order_by(ordering).limit(10)

    if not gus_list:
        await message.answer(_("top-empty"))
        return

    lines = []
    for idx, gus in enumerate(gus_list, start=1):
        await gus.fetch_related("user")
        u = gus.user
        wr = int((gus.games_won / gus.games_total) * 100) if gus.games_total else 0
        if sort_key == "elo":
            metric = f"ELO {gus.elo}"
        elif sort_key == "wins":
            metric = f"🏆 {gus.games_won}"
        elif sort_key == "xp":
            metric = f"⭐ {gus.xp}"
        else:
            metric = f"{wr}% (WR)"
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        lines.append(f"{medal} {player_mention(u.id, u.first_name)} — {metric}")

    text = _("top-header", sort=sort_key) + "\n\n" + "\n".join(lines)
    await message.answer(text)


# === /global_top — global leaderboard ===


@router.message(Command("global_top", "globaltop", prefix="/!"))
async def cmd_global_top(message: Message, _: Translator) -> None:
    top = await UserStats.all().order_by("-elo").limit(10)
    if not top:
        await message.answer(_("top-empty"))
        return

    lines = []
    for idx, stats in enumerate(top, start=1):
        await stats.fetch_related("user")
        u = stats.user
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        lines.append(f"{medal} {player_mention(u.id, u.first_name)} — ELO {stats.elo}")

    text = _("global-top-header") + "\n\n" + "\n".join(lines)
    await message.answer(text)


# === /profile @user ===


@router.message(Command("profile", prefix="/!"))
async def cmd_profile(message: Message, _: Translator, command: CommandObject) -> None:
    target_user: User | None = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = await User.get_or_none(id=message.reply_to_message.from_user.id)
    elif command.args and command.args.strip().startswith("@"):
        uname = command.args.strip().lstrip("@")
        target_user = await User.get_or_none(username=uname)

    if target_user is None:
        await message.answer(_("profile-target-not-found"))
        return

    stats = await UserStats.get_or_none(user=target_user)
    if stats is None or stats.games_total == 0:
        await message.answer(_("profile-no-games", name=target_user.first_name))
        return

    text = _format_user_stats(target_user, stats, _)
    await message.answer(text)


# === /group_stats ===


@router.message(Command("group_stats", "groupstats", prefix="/!"))
async def cmd_group_stats(message: Message, _: Translator) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_("top-group-only"))
        return

    gs = await GroupStats.get_or_none(group_id=message.chat.id)
    if gs is None or gs.total_games == 0:
        await message.answer(_("group-stats-no-games"))
        return

    text = _(
        "group-stats-message",
        total_games=gs.total_games,
        avg_duration=int(gs.avg_game_duration_seconds // 60),
        avg_players=round(gs.avg_player_count, 1),
        citizens_wr=int(gs.citizens_winrate * 100),
        mafia_wr=int(gs.mafia_winrate * 100),
        singleton_wr=int(gs.singleton_winrate * 100),
    )
    await message.answer(text)
