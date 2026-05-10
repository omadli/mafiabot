"""Mafia private chat — relay messages between alive Mafia/Don/Lawyer/Killer at night.

Each mafia member writes to bot in private chat → bot relays to all other alive mafia.
Active only during Phase.NIGHT.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from app.core.state import GameState, Phase, Team
from app.services import game_service

MAFIA_ROLES = {"don", "mafia", "lawyer", "journalist", "killer"}


async def relay_mafia_message(bot: Bot, sender_user_id: int, text: str) -> bool:
    """Relay text from sender to other alive mafia teammates if eligible.

    Returns True if relayed, False if not eligible (not in game, not mafia, not night).
    """
    if not text:
        return False

    # Find sender's active game
    if sender_user_id is None:
        return False

    from app.db.models import Game, User

    user = await User.get_or_none(id=sender_user_id)
    if user is None or user.active_game_id is None:
        return False

    db_game = await Game.get_or_none(id=user.active_game_id)
    if db_game is None:
        return False

    state = await game_service.load_state(db_game.group_id)
    if state is None or state.phase != Phase.NIGHT:
        return False

    sender = state.get_player(sender_user_id)
    if sender is None or not sender.alive or sender.team != Team.MAFIA:
        return False

    # Recipients: alive mafia teammates (not sender)
    recipients = [
        p for p in state.alive_players() if p.team == Team.MAFIA and p.user_id != sender_user_id
    ]
    if not recipients:
        return True  # nothing to relay, but still consumed

    # Format with sender's role + name
    role_emoji = _role_emoji(sender.role)
    safe_text = text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
    formatted = f"{role_emoji} <b>{sender.first_name}</b>: {safe_text}"

    # Broadcast
    coros = []
    for recipient in recipients:
        coros.append(_safe_dm(bot, recipient.user_id, formatted))
    await asyncio.gather(*coros, return_exceptions=True)

    logger.debug(f"Mafia chat relay: {sender_user_id} → {len(recipients)} mafia")
    return True


def _role_emoji(role: str) -> str:
    return {
        "don": "🤵🏻",
        "mafia": "🤵🏼",
        "lawyer": "👨‍💼",
        "journalist": "👩🏼‍💻",
        "killer": "🥷",
    }.get(role, "🤵🏼")


async def _safe_dm(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
    except TelegramForbiddenError:
        logger.debug(f"Cannot DM mafia member {user_id}")
    except Exception as e:
        logger.warning(f"Mafia chat DM error for {user_id}: {e}")


async def announce_mafia_chat_open(bot: Bot, state: GameState) -> None:
    """At start of night, notify mafia members they can chat now."""
    from app.services.i18n_service import get_translator

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    mafia_members = [p for p in state.alive_players() if p.team == Team.MAFIA]
    if len(mafia_members) < 2:
        return  # solo Don — no chat needed

    members_list = "\n".join(
        f"  • {_role_emoji(p.role)} <b>{p.first_name}</b>" for p in mafia_members
    )
    text = _("mafia-chat-opened", members=members_list)

    coros = [_safe_dm(bot, p.user_id, text) for p in mafia_members]
    await asyncio.gather(*coros, return_exceptions=True)
