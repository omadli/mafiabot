"""Role action service — send private prompts at night, handle inline target picks."""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from app.core.roles import get_role
from app.core.state import GameState, PlayerState
from app.services.i18n_service import get_translator


async def send_night_prompts(bot: Bot, state: GameState) -> None:
    """Send private prompts to all alive players with night actions."""
    locale = state.settings.get("language", "uz")

    coros = [
        _send_prompt_to_player(bot, state, player, locale)
        for player in state.alive_players()
        if get_role(player.role).has_night_action
    ]
    await asyncio.gather(*coros, return_exceptions=True)


async def _send_prompt_to_player(
    bot: Bot, state: GameState, actor: PlayerState, locale: str
) -> None:
    role = get_role(actor.role)
    _ = get_translator(locale)
    prompt_key = role.night_prompt_key()
    if prompt_key is None:
        return

    targets = role.valid_targets(state, actor)
    if not targets and actor.role != "arsonist":
        return

    # Special: Arsonist — uses its own keyboard with "Oxirgi tun" button
    if actor.role == "arsonist":
        from app.bot.handlers.private.special_actions import build_arsonist_keyboard

        keyboard = build_arsonist_keyboard(state, _)
        try:
            await bot.send_message(actor.user_id, _("night-prompt-arsonist"), reply_markup=keyboard)
        except TelegramForbiddenError:
            logger.warning(f"Cannot DM user {actor.user_id} (bot blocked)")
        return

    # Build keyboard with target buttons
    rows: list[list[InlineKeyboardButton]] = []
    for target in targets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{target.first_name} (#{target.join_order})",
                    callback_data=f"night:{actor.role}:{target.user_id}",
                )
            ]
        )

    # Skip option (if allowed)
    if state.settings.get("gameplay", {}).get("allow_skip_night_action", True):
        rows.append(
            [InlineKeyboardButton(text=_("btn-skip"), callback_data=f"night:{actor.role}:0")]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    # Detective has 2 actions: check OR shoot (1-night = check only)
    if actor.role == "detective":
        if state.round_num == 1:
            text = _("night-prompt-detective-check-only")
        else:
            # Provide both choices
            check_rows = [
                [
                    InlineKeyboardButton(
                        text=f"🔍 {t.first_name}",
                        callback_data=f"night:detective:check:{t.user_id}",
                    )
                ]
                for t in targets
            ]
            shoot_rows = [
                [
                    InlineKeyboardButton(
                        text=f"🔫 {t.first_name}",
                        callback_data=f"night:detective:kill:{t.user_id}",
                    )
                ]
                for t in targets
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=check_rows + shoot_rows)
            text = _("night-prompt-detective-both")

            try:
                await bot.send_message(actor.user_id, text, reply_markup=keyboard)
            except TelegramForbiddenError:
                logger.warning(f"Cannot DM user {actor.user_id} (bot blocked)")
            return
    else:
        text = _(prompt_key)

    try:
        await bot.send_message(actor.user_id, text, reply_markup=keyboard)
    except TelegramForbiddenError:
        logger.warning(f"Cannot DM user {actor.user_id} (bot blocked)")
    except Exception as e:
        logger.exception(f"Failed to send night prompt to {actor.user_id}: {e}")


def role_action_type(role_code: str) -> str:
    """Map role → default action type."""
    return {
        "detective": "check",
        "doctor": "heal",
        "don": "kill",
        "hooker": "sleep",
        "mafia": "kill",
        "killer": "kill",
        "maniac": "kill",
        "hobo": "visit",
    }.get(role_code, "visit")
