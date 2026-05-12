"""Achievement system — check & unlock medals after each game.

15 achievements covering: first game, milestones, role mastery, streaks, balance.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from loguru import logger
from tortoise.transactions import in_transaction

from app.core.state import GameState, Team
from app.db.models import Achievement, GameResult, User, UserAchievement, UserStats


@dataclass
class AchievementDef:
    code: str
    name: dict[str, str]  # {"uz": ..., "ru": ..., "en": ...}
    description: dict[str, str]
    icon: str
    diamonds: int  # Reserved for rare/grindy achievements only — keep low.
    dollars: int  # Default everyday reward.
    xp: int
    check: Callable[[User, UserStats, GameState, GameResult], Awaitable[bool]]


# === Achievement definitions ===


async def _first_game(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.games_total == 1


async def _first_blood(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    """Win your first game."""
    return stats.games_won == 1 and gr.won


async def _veteran_10(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.games_total >= 10


async def _veteran_50(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.games_total >= 50


async def _veteran_100(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.games_total >= 100


async def _sherlock(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    """Win 5 games as Detective."""
    role_data = stats.role_stats.get("detective", {})
    return role_data.get("wins", 0) >= 5


async def _godfather(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    """Win 5 games as Don."""
    role_data = stats.role_stats.get("don", {})
    return role_data.get("wins", 0) >= 5


async def _streak_3(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.current_win_streak >= 3


async def _streak_5(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.longest_win_streak >= 5


async def _survivor(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.times_survived >= 10


async def _comeback(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    """Win as one of last 3 alive citizens."""
    if not gr.won or gr.team != "citizens":
        return False
    citizens_alive = sum(1 for p in state.players if p.alive and p.team == Team.CITIZENS)
    return citizens_alive <= 3 and gr.survived


async def _solo_king(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.singleton_wins >= 3


async def _elo_master(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.elo >= 1500


async def _elo_legend(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    return stats.elo >= 1800


async def _balance_master(user: User, stats: UserStats, state: GameState, gr: GameResult) -> bool:
    """Win at least once on each team."""
    return stats.citizen_wins >= 1 and stats.mafia_wins >= 1 and stats.singleton_wins >= 1


ACHIEVEMENTS: list[AchievementDef] = [
    # Small/everyday achievements → small $ rewards, no diamonds.
    AchievementDef(
        code="first_game",
        name={"uz": "Birinchi qadam", "ru": "Первый шаг", "en": "First step"},
        description={
            "uz": "Birinchi o'yiningizda qatnashing",
            "ru": "Сыграйте свою первую игру",
            "en": "Play your first game",
        },
        icon="🎮",
        diamonds=0,
        dollars=20,
        xp=20,
        check=_first_game,
    ),
    AchievementDef(
        code="first_blood",
        name={"uz": "Birinchi g'alaba", "ru": "Первая победа", "en": "First blood"},
        description={
            "uz": "Birinchi marta yutib oling",
            "ru": "Выиграйте первую игру",
            "en": "Win your first game",
        },
        icon="🥇",
        diamonds=0,
        dollars=50,
        xp=50,
        check=_first_blood,
    ),
    AchievementDef(
        code="veteran_10",
        name={"uz": "Tajribali", "ru": "Опытный", "en": "Veteran"},
        description={
            "uz": "10 ta o'yinda qatnashing",
            "ru": "Сыграйте 10 игр",
            "en": "Play 10 games",
        },
        icon="🎖",
        diamonds=0,
        dollars=75,
        xp=100,
        check=_veteran_10,
    ),
    AchievementDef(
        code="veteran_50",
        name={"uz": "Faol o'yinchi", "ru": "Активный игрок", "en": "Active player"},
        description={
            "uz": "50 ta o'yinda qatnashing",
            "ru": "Сыграйте 50 игр",
            "en": "Play 50 games",
        },
        icon="🏅",
        diamonds=0,
        dollars=300,
        xp=300,
        check=_veteran_50,
    ),
    # Rare grindy achievement — gets a few diamonds.
    AchievementDef(
        code="veteran_100",
        name={"uz": "Mafia ustasi", "ru": "Мастер мафии", "en": "Mafia master"},
        description={
            "uz": "100 ta o'yinda qatnashing",
            "ru": "Сыграйте 100 игр",
            "en": "Play 100 games",
        },
        icon="👑",
        diamonds=20,
        dollars=500,
        xp=1000,
        check=_veteran_100,
    ),
    AchievementDef(
        code="sherlock",
        name={"uz": "Sherlok", "ru": "Шерлок", "en": "Sherlock"},
        description={
            "uz": "Komissar sifatida 5 ta o'yinda yuting",
            "ru": "Выиграйте 5 игр как Комиссар",
            "en": "Win 5 games as Detective",
        },
        icon="🕵🏼",
        diamonds=0,
        dollars=150,
        xp=200,
        check=_sherlock,
    ),
    AchievementDef(
        code="godfather",
        name={"uz": "Cho'qmor", "ru": "Крёстный отец", "en": "Godfather"},
        description={
            "uz": "Don sifatida 5 ta o'yinda yuting",
            "ru": "Выиграйте 5 игр как Дон",
            "en": "Win 5 games as Don",
        },
        icon="🤵🏻",
        diamonds=0,
        dollars=150,
        xp=200,
        check=_godfather,
    ),
    AchievementDef(
        code="streak_3",
        name={"uz": "Issiq qo'l", "ru": "Горячая полоса", "en": "Hot streak"},
        description={
            "uz": "3 marta ketma-ket yuting",
            "ru": "Выиграйте 3 раза подряд",
            "en": "Win 3 games in a row",
        },
        icon="🔥",
        diamonds=0,
        dollars=100,
        xp=150,
        check=_streak_3,
    ),
    AchievementDef(
        code="streak_5",
        name={"uz": "To'xtatib bo'lmas", "ru": "Неудержимый", "en": "Unstoppable"},
        description={
            "uz": "5 marta ketma-ket yuting",
            "ru": "Выиграйте 5 раз подряд",
            "en": "Win 5 games in a row",
        },
        icon="💥",
        diamonds=5,
        dollars=250,
        xp=400,
        check=_streak_5,
    ),
    AchievementDef(
        code="survivor",
        name={"uz": "Omon qoluvchi", "ru": "Выживший", "en": "Survivor"},
        description={
            "uz": "10 ta o'yinda tirik qoling",
            "ru": "Выживите в 10 играх",
            "en": "Survive 10 games",
        },
        icon="🛡",
        diamonds=0,
        dollars=120,
        xp=200,
        check=_survivor,
    ),
    AchievementDef(
        code="comeback",
        name={"uz": "Qaytish", "ru": "Камбэк", "en": "Comeback king"},
        description={
            "uz": "3 ta tinch aholi qolganda yuting",
            "ru": "Победа когда осталось 3 мирных",
            "en": "Win with 3 or fewer citizens left",
        },
        icon="🦅",
        diamonds=0,
        dollars=200,
        xp=300,
        check=_comeback,
    ),
    AchievementDef(
        code="solo_king",
        name={"uz": "Yakka shoh", "ru": "Король одиночек", "en": "Solo king"},
        description={
            "uz": "3 ta singleton g'alaba",
            "ru": "3 победы за одиночек",
            "en": "Win 3 times as a singleton",
        },
        icon="🃏",
        diamonds=5,
        dollars=200,
        xp=250,
        check=_solo_king,
    ),
    AchievementDef(
        code="elo_master",
        name={"uz": "Reyting ustasi", "ru": "Мастер рейтинга", "en": "Rating master"},
        description={
            "uz": "1500 ELO ga yeting",
            "ru": "Достигните 1500 ELO",
            "en": "Reach 1500 ELO",
        },
        icon="📈",
        diamonds=5,
        dollars=300,
        xp=400,
        check=_elo_master,
    ),
    # Truly rare — diamond drop justified.
    AchievementDef(
        code="elo_legend",
        name={"uz": "Afsona", "ru": "Легенда", "en": "Legend"},
        description={
            "uz": "1800 ELO ga yeting",
            "ru": "Достигните 1800 ELO",
            "en": "Reach 1800 ELO",
        },
        icon="🌟",
        diamonds=25,
        dollars=1000,
        xp=1000,
        check=_elo_legend,
    ),
    AchievementDef(
        code="balance_master",
        name={"uz": "Hamma joyda usta", "ru": "Универсал", "en": "All-rounder"},
        description={
            "uz": "Tinch, Mafia va Singleton sifatida g'alaba",
            "ru": "Победы за каждую сторону",
            "en": "Win as Citizen, Mafia and Singleton",
        },
        icon="⚖️",
        diamonds=10,
        dollars=400,
        xp=500,
        check=_balance_master,
    ),
]


async def seed_achievements() -> None:
    """Idempotent seed — call on app startup."""
    for ach in ACHIEVEMENTS:
        await Achievement.update_or_create(
            code=ach.code,
            defaults={
                "name_i18n": ach.name,
                "description_i18n": ach.description,
                "icon": ach.icon,
                "diamonds_reward": ach.diamonds,
                "xp_reward": ach.xp,
            },
        )
    logger.info(f"Seeded {len(ACHIEVEMENTS)} achievements")


async def notify_unlock(bot, user_id: int, ach: AchievementDef, locale: str) -> None:
    """Send private notification when user unlocks an achievement."""
    from aiogram.exceptions import TelegramForbiddenError

    name = ach.name.get(locale, ach.name.get("uz", ach.code))
    description = ach.description.get(locale, ach.description.get("uz", ""))

    parts: list[str] = []
    if ach.dollars:
        parts.append(f"💵 {ach.dollars}")
    if ach.diamonds:
        parts.append(f"💎 {ach.diamonds}")
    if ach.xp:
        parts.append(f"⭐ {ach.xp} XP")
    reward = " · ".join(parts)

    text = f"{ach.icon} <b>Yangi yutuq!</b>\n\n<b>{name}</b>\n{description}"
    if reward:
        text += f"\n\n🎁 {reward}"

    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except TelegramForbiddenError:
        logger.debug(f"Cannot DM user {user_id} for achievement notification")


async def check_and_unlock(user: User, state: GameState) -> list[AchievementDef]:
    """Check all achievements for user after game finished. Returns newly unlocked ones."""
    stats = await UserStats.get_or_none(user=user)
    if stats is None:
        return []

    # Latest GameResult for this user in this game
    gr = await GameResult.filter(user=user, game_id=state.id).first()
    if gr is None:
        return []

    # Already unlocked codes
    unlocked = await UserAchievement.filter(user=user).values_list("achievement_id", flat=True)
    unlocked_set = set(unlocked)

    new_unlocks: list[AchievementDef] = []

    async with in_transaction():
        for ach in ACHIEVEMENTS:
            if ach.code in unlocked_set:
                continue
            try:
                if not await ach.check(user, stats, state, gr):
                    continue
            except Exception as e:
                logger.warning(f"Achievement check {ach.code} failed: {e}")
                continue

            # Unlock
            await UserAchievement.create(user=user, achievement_id=ach.code)
            user.diamonds += ach.diamonds
            user.dollars += ach.dollars
            user.xp += ach.xp
            await user.save(update_fields=["diamonds", "dollars", "xp"])
            new_unlocks.append(ach)
            logger.info(
                f"User {user.id} unlocked {ach.code} "
                f"(+{ach.dollars}$ +{ach.diamonds}💎 +{ach.xp}xp)"
            )

    return new_unlocks
