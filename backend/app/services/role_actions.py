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

    # Detective: 2-step UX
    #   Round 1 → only checking is allowed, single keyboard.
    #   Round 2+ → first show prior check results + "Tekshirish/O'ldirish"
    #              chooser. Target list comes after the chooser pick.
    if actor.role == "detective":
        if state.round_num == 1:
            text = _("night-prompt-detective-check-only")
        else:
            await _send_detective_chooser(bot, actor, _)
            return
    else:
        text = _(prompt_key)

    try:
        await bot.send_message(actor.user_id, text, reply_markup=keyboard)
    except TelegramForbiddenError:
        logger.warning(f"Cannot DM user {actor.user_id} (bot blocked)")
    except Exception as e:
        logger.exception(f"Failed to send night prompt to {actor.user_id}: {e}")


async def _send_detective_chooser(bot: Bot, actor: PlayerState, _) -> None:
    """Step 1 of the detective night flow: prior results + action chooser.

    The actual target keyboard is built lazily in the chooser callback so
    we always reflect the latest alive set, not a stale snapshot.
    """
    prior_lines: list[str] = []
    check_results: dict = actor.extra.get("check_results", {}) or {}
    if check_results:
        from app.services.messaging import role_emoji_name

        # Detective DMs use the actor's UI language; no per-user override yet.
        locale = "uz"
        prior_lines.append(_("night-prompt-detective-prior-header"))
        for _uid_str, info in check_results.items():
            role_label = role_emoji_name(info.get("role", "citizen"), locale)
            name = info.get("name", "?")
            prior_lines.append(_("night-prompt-detective-prior-line", name=name, role=role_label))
        prior_lines.append("")  # blank line separator

    prior_text = "\n".join(prior_lines)
    chooser_text = _("night-prompt-detective-chooser")
    text = (prior_text + chooser_text) if prior_text else chooser_text

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn-detective-check"), callback_data="night:detchoose:check"
                ),
                InlineKeyboardButton(
                    text=_("btn-detective-kill"), callback_data="night:detchoose:kill"
                ),
            ]
        ]
    )

    try:
        await bot.send_message(actor.user_id, text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramForbiddenError:
        logger.warning(f"Cannot DM user {actor.user_id} (bot blocked)")
    except Exception as e:
        logger.exception(f"Failed to send detective chooser to {actor.user_id}: {e}")


async def send_detective_target_keyboard(
    bot: Bot,
    state: GameState,
    actor: PlayerState,
    action_kind: str,
    locale: str,
) -> InlineKeyboardMarkup | None:
    """Build the target keyboard for the chosen detective action."""
    from app.core.roles import get_role

    role = get_role("detective")
    targets = role.valid_targets(state, actor)
    if not targets:
        return None

    callback_prefix = f"night:detective:{action_kind}"
    rows = [
        [
            InlineKeyboardButton(
                text=f"{t.first_name} (#{t.join_order})",
                callback_data=f"{callback_prefix}:{t.user_id}",
            )
        ]
        for t in targets
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
