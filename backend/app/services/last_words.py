"""Last words mechanic — DM dead players, broadcast their final message."""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from app.core.redis_state import get_state_backend
from app.core.state import GameState
from app.services.i18n_service import get_translator
from app.services.messaging import player_mention, role_emoji_name


# Redis key: pending last-words player → game_id (for matching incoming messages)
def _pending_key(user_id: int) -> str:
    return f"mafia:last_words:{user_id}"


async def request_last_words(
    bot: Bot, state: GameState, user_id: int, hanged: bool = False
) -> None:
    """DM the dead user inviting them to write last words.

    Skipped if game has ended (winner already determined).
    """
    if state.winner_team is not None:
        return

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    prompt_key = "last-words-prompt-hanged" if hanged else "last-words-prompt-killed-night"
    try:
        await bot.send_message(user_id, _(prompt_key))
    except TelegramForbiddenError:
        logger.warning(f"Cannot DM user {user_id} for last words")
        return

    # Mark as pending in Redis
    backend = get_state_backend()
    timeout = state.settings.get("timings", {}).get("last_words", 20)
    await backend.set(_pending_key(user_id), str(state.group_id))

    # Schedule cleanup after timeout (store reference to prevent GC)
    _task = asyncio.create_task(_clear_pending_after(user_id, timeout))
    _task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)


async def _clear_pending_after(user_id: int, delay: int) -> None:
    await asyncio.sleep(delay + 5)
    backend = get_state_backend()
    await backend.delete(_pending_key(user_id))


async def is_last_words_pending(user_id: int) -> int | None:
    """Returns group_id if user has pending last-words slot, else None."""
    backend = get_state_backend()
    raw = await backend.get(_pending_key(user_id))
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


async def consume_last_words(user_id: int) -> None:
    """Mark last-words as used (one shot)."""
    backend = get_state_backend()
    await backend.delete(_pending_key(user_id))


async def broadcast_last_words(bot: Bot, state: GameState, user_id: int, message_text: str) -> None:
    """Send last words to group chat."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    player = state.get_player(user_id)
    if player is None:
        return

    # Limit length
    if len(message_text) > 500:
        message_text = message_text[:497] + "..."

    show_role_on_death = state.settings.get("display", {}).get("show_role_on_death", True)
    role_label = role_emoji_name(player.role, locale) if show_role_on_death else "?"
    role_parts = role_label.split(" ", 1)
    role_emoji = role_parts[0] if role_parts else "❓"
    role_name = role_parts[1] if len(role_parts) > 1 else player.role

    text = _(
        "last-words-broadcast",
        role_emoji=role_emoji,
        role_name=role_name,
        mention=player_mention(user_id, player.first_name),
        message=message_text,
    )
    try:
        await bot.send_message(state.chat_id, text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not broadcast last words: {e}")

    # Persist to round log
    if state.rounds:
        state.rounds[-1].last_words[user_id] = message_text
