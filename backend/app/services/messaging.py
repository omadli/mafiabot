"""Messaging service — broadcast atmospheric and result messages to group chat."""

from __future__ import annotations

import asyncio
import random

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from app.core.actions import NightOutcome
from app.core.roles import get_role
from app.core.state import GameState, Phase
from app.services.i18n_service import get_translator


def role_emoji_name(role_code: str, locale: str) -> str:
    """Get '{emoji} {name}' for a role using i18n."""
    _ = get_translator(locale)
    return _(f"role-{role_code}")


def player_mention(user_id: int, name: str) -> str:
    """HTML-mention for Telegram."""
    safe_name = name.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'


async def broadcast_night_actions(bot: Bot, state: GameState) -> None:
    """Send atmospheric night messages for each role that acted (random order, 1-2s pause)."""
    locale = state.settings.get("language", "uz")
    show_emojis = state.settings.get("display", {}).get("show_role_emojis", True)
    _ = get_translator(locale)

    # Collect unique role messages (one message per role, even if multiple actors)
    messages: list[str] = []
    seen_roles: set[str] = set()

    for action in state.current_actions.values():
        actor = state.get_player(action.actor_id)
        if actor is None or not actor.alive:
            continue
        role = get_role(actor.role)
        if not role.has_night_action or role.night_message_key is None:
            continue
        # Detective has 2 messages: check vs shoot
        if actor.role == "detective":
            key = (
                "night-action-msg-detective-shoot"
                if action.action_type == "kill"
                else "night-action-msg-detective-check"
            )
        else:
            key = role.night_message_key

        if key in seen_roles:
            continue
        seen_roles.add(key)

        msg = _(key)
        if not show_emojis:
            msg = _strip_emojis(msg)
        messages.append(msg)

    # Shuffle for atmosphere
    random.shuffle(messages)

    for msg in messages:
        try:
            await bot.send_message(state.chat_id, msg)
        except Exception as e:
            logger.warning(f"Could not send night action message: {e}")
        await asyncio.sleep(random.uniform(1.0, 2.0))


async def broadcast_night_results(bot: Bot, state: GameState, outcome: NightOutcome) -> None:
    """Send day-start messages: deaths, shields, no-deaths.

    Also DMs each dead player with last-words prompt (if game not finished).
    """
    from app.core.win_conditions import check_winner
    from app.services.last_words import request_last_words

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    show_role_on_death = state.settings.get("display", {}).get("show_role_on_death", True)

    # Send last-words prompts (only if game not over)
    if check_winner(state) is None:
        for user_id in outcome.deaths:
            await request_last_words(bot, state, user_id, hanged=False)

    # Deaths
    if outcome.deaths:
        if len(outcome.deaths) == 1:
            user_id = outcome.deaths[0]
            target = state.get_player(user_id)
            if target is not None:
                role_label = role_emoji_name(target.role, locale) if show_role_on_death else "?"
                killer_role = _killer_role_label(state, outcome, target.user_id, locale)
                text = _(
                    "night-result-killed-single",
                    role_emoji_name=role_label,
                    mention=player_mention(target.user_id, target.first_name),
                    killer_role_emoji_name=killer_role,
                )
                await _safe_send(bot, state.chat_id, text)
        else:
            # Multiple deaths — list
            lines: list[str] = []
            for user_id in outcome.deaths:
                target = state.get_player(user_id)
                if target is None:
                    continue
                role_label = role_emoji_name(target.role, locale) if show_role_on_death else "?"
                killer_role = _killer_role_label(state, outcome, target.user_id, locale)
                lines.append(
                    f"• {role_label} {player_mention(target.user_id, target.first_name)} — {killer_role}"
                )
            await _safe_send(bot, state.chat_id, "🌅\n" + "\n".join(lines))
    else:
        await _safe_send(bot, state.chat_id, _("night-result-no-deaths"))

    # Doctor saves → "shield used" (anonymous)
    if any(r.saved for r in outcome.doctor_results):
        await asyncio.sleep(1.5)
        await _safe_send(bot, state.chat_id, _("night-result-shield-used"))


def _killer_role_label(state: GameState, outcome: NightOutcome, target_id: int, locale: str) -> str:
    """Find which role killed the target — based on actions."""
    for action in state.current_round().night_actions:
        if action.action_type == "kill" and action.target_id == target_id:
            return role_emoji_name(action.role, locale)
    return "?"


def _strip_emojis(text: str) -> str:
    """Crude emoji stripper — used when group disabled show_role_emojis."""
    import re

    return re.sub(r"[^\w\s,.':!?\-—()«»\"]", "", text, flags=re.UNICODE).strip()


async def _safe_send(bot: Bot, chat_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id, text)
    except TelegramBadRequest as e:
        logger.warning(f"send_message failed for chat {chat_id}: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error sending to {chat_id}: {e}")


async def broadcast_phase_change(bot: Bot, state: GameState) -> None:
    """Generic phase change announcer (NIGHT/DAY/VOTING start)."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    if state.phase == Phase.NIGHT:
        await _safe_send(bot, state.chat_id, _("phase-night-start", round=state.round_num))
    elif state.phase == Phase.DAY:
        await _safe_send(bot, state.chat_id, _("phase-day-start", round=state.round_num))
    elif state.phase == Phase.VOTING:
        await _safe_send(bot, state.chat_id, _("phase-voting-start"))


async def broadcast_game_end(bot: Bot, state: GameState) -> None:
    """Announce winner."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    if state.winner_team is None:
        await _safe_send(bot, state.chat_id, _("game-cancelled"))
        return

    team_key = f"team-{state.winner_team.value}"
    text = _("game-end-winner", team=_(team_key))

    # Reveal all roles
    role_lines: list[str] = []
    for p in sorted(state.players, key=lambda x: x.join_order):
        emoji_role = role_emoji_name(p.role, locale)
        status = "💀" if not p.alive else "✅"
        role_lines.append(f"{status} {emoji_role} — {player_mention(p.user_id, p.first_name)}")
    text += "\n\n" + "\n".join(role_lines)

    await _safe_send(bot, state.chat_id, text)
