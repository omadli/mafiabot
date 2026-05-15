"""Messaging service — broadcast atmospheric and result messages to group chat."""

from __future__ import annotations

import asyncio
import random
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile
from loguru import logger

from app.core.actions import NightOutcome
from app.core.roles import get_role
from app.core.state import GameState, Phase
from app.services.i18n_service import get_translator

# Bundled default atmosphere GIFs (committed alongside the code). Used
# whenever a group hasn't configured its own atmosphere_media file_id
# for the given phase. Regenerate via scripts/generate_atmosphere_gifs.py.
_ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets" / "atmosphere"
DEFAULT_ATMOSPHERE_PATHS: dict[Phase, Path] = {
    Phase.NIGHT: _ASSETS_DIR / "night.gif",
    Phase.DAY: _ASSETS_DIR / "day.gif",
}

# Cache the resolved Telegram file_id after the first upload per (bot, phase)
# so repeated phase transitions reuse it instead of re-uploading the file.
_DEFAULT_FILE_ID_CACHE: dict[tuple[int, Phase], str] = {}


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
    """Send day-start messages: deaths, shields, transformations, special role events."""
    from app.core.win_conditions import check_winner
    from app.services.last_words import request_last_words

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    show_role_on_death = state.settings.get("display", {}).get("show_role_on_death", True)

    # Send last-words prompts (only if game not over)
    if check_winner(state) is None:
        for user_id in outcome.deaths:
            await request_last_words(bot, state, user_id, hanged=False)

    # Werewolf transformations (anonim — Bo'rining ismi YASHIRILADI, faqat yangi roli oshkor)
    for trans in outcome.transformations:
        await asyncio.sleep(1.5)
        target_player = state.get_player(trans.user_id)
        if target_player is None:
            continue
        key = f"transform-werewolf-to-{trans.new_role}"
        # No `mention` param — keeps werewolf identity hidden (gameplay UX)
        text = _(key)
        await _safe_send(bot, state.chat_id, text)

    # Kamikaze take-with-me (anonimiy + jabrlanuvchi roli oshkor qilinadi)
    for take in outcome.kamikaze_takes:
        await asyncio.sleep(1.5)
        kp = state.get_player(take.kamikaze_id)
        vp = state.get_player(take.victim_id)
        if kp is None or vp is None:
            continue
        victim_role_label = role_emoji_name(vp.role, locale) if show_role_on_death else "?"
        # role-specific emoji + name (split on first space if combined)
        role_parts = victim_role_label.split(" ", 1)
        victim_role_emoji = role_parts[0] if role_parts else "❓"
        victim_role_name = role_parts[1] if len(role_parts) > 1 else vp.role
        text = _(
            "kamikaze-took-victim",
            victim=player_mention(take.victim_id, vp.first_name),
            victim_role_emoji=victim_role_emoji,
            victim_role=victim_role_name,
        )
        await _safe_send(bot, state.chat_id, text)

    # Snitch reveals (oshkor xabarlar)
    for reveal in outcome.snitch_reveals:
        await asyncio.sleep(1.5)
        text = _(
            "snitch-reveal-broadcast",
            target=player_mention(reveal.target_id, reveal.target_name),
            role=role_emoji_name(reveal.revealed_role, locale),
        )
        await _safe_send(bot, state.chat_id, text)

    # Deaths — har biri ALOHIDA xabar, orasida pauza (reference: @MafiaAzBot)
    if outcome.deaths:
        first = True
        for user_id in outcome.deaths:
            if not first:
                await asyncio.sleep(1.2)
            first = False

            target = state.get_player(user_id)
            if target is None:
                continue

            # Arsonist self-burn — special public-reveal message
            if _is_arsonist_self_kill(state, target):
                text = _(
                    "arsonist-self-burn",
                    name=player_mention(target.user_id, target.first_name),
                )
                await _safe_send(bot, state.chat_id, text)
                continue

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
        await _safe_send(bot, state.chat_id, _("night-result-no-deaths"))

    # Doctor saves → "shield used" (anonymous)
    if any(r.saved for r in outcome.doctor_results):
        await asyncio.sleep(1.5)
        await _safe_send(bot, state.chat_id, _("night-result-shield-used"))


def _killer_role_label(state: GameState, outcome: NightOutcome, target_id: int, locale: str) -> str:
    """Find which role killed the target — based on actions.

    Detective/Don/Killer with `used_item == "rifle"` are still labeled by their
    actor role (e.g. Detective with rifle → killer_role = "Komissar katani").
    """
    for action in state.current_round().night_actions:
        if action.action_type in ("kill", "final_night") and action.target_id == target_id:
            return role_emoji_name(action.role, locale)
    return "?"


def _is_arsonist_self_kill(state: GameState, target) -> bool:
    """True if target is an Arsonist who self-burned via final_night action."""
    if target.role != "arsonist":
        return False
    for action in state.current_round().night_actions:
        if (
            action.action_type == "final_night"
            and action.role == "arsonist"
            and action.actor_id == target.user_id
        ):
            return True
    return False


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
    """Generic phase change announcer (NIGHT/DAY/VOTING start).

    If `atmosphere_media` is configured for this phase, sends the GIF/video first
    (mirrors @MafiaAzBot which uses Baku skyline GIFs at night/day starts).
    """
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    media = state.settings.get("atmosphere_media", {}) or {}
    media_key_map = {
        Phase.NIGHT: "night_start",
        Phase.DAY: "day_start",
    }
    media_key = media_key_map.get(state.phase)
    media_file_id = media.get(media_key) if media_key else None

    # Atmospheric variety: for NIGHT and DAY, pick one of 5 flavored
    # variants at random. Fluent falls back to the base key for any locale
    # that hasn't translated the variant yet.
    variant_count = 5
    if state.phase == Phase.NIGHT:
        key = f"phase-night-start-{random.randint(1, variant_count)}"
        params: dict[str, object] = {"round": state.round_num}
    elif state.phase == Phase.DAY:
        key = f"phase-day-start-{random.randint(1, variant_count)}"
        params = {"round": state.round_num}
    else:
        return

    caption = _(key, **params)

    if media_file_id:
        try:
            await bot.send_animation(state.chat_id, media_file_id, caption=caption)
            return
        except Exception as e:
            logger.debug(f"send_animation failed (falling back to send_video): {e}")
            try:
                await bot.send_video(state.chat_id, media_file_id, caption=caption)
                return
            except Exception as e2:
                logger.warning(f"atmosphere_media send failed for {media_key}: {e2}")

    # No group-configured media — fall back to the bundled default GIF
    # (only for NIGHT and DAY; VOTING has no default art yet).
    default_path = DEFAULT_ATMOSPHERE_PATHS.get(state.phase)
    if default_path and default_path.exists():
        cache_key = (bot.id, state.phase)
        cached_file_id = _DEFAULT_FILE_ID_CACHE.get(cache_key)
        try:
            if cached_file_id:
                msg = await bot.send_animation(state.chat_id, cached_file_id, caption=caption)
            else:
                msg = await bot.send_animation(
                    state.chat_id, FSInputFile(default_path), caption=caption
                )
                # Cache the Telegram-assigned file_id so subsequent sends
                # are zero-bandwidth.
                if msg.animation and msg.animation.file_id:
                    _DEFAULT_FILE_ID_CACHE[cache_key] = msg.animation.file_id
            return
        except Exception as e:
            logger.debug(f"default atmosphere GIF send failed: {e}")

    await _safe_send(bot, state.chat_id, caption)


async def broadcast_game_end(bot: Bot, state: GameState) -> None:
    """Announce game over with winners/losers split + duration.

    Mirrors @MafiaAzBot reference format:
        O'yin tugadi!

        G'oliblar:
        1. <name> - <role_emoji> <role_name>
        ...

        Qolgan o'yinchilar:
        9. <name> - <role_emoji> <role_name>
        ...

        O'yin: 15 minut davom etdi
    """
    from app.core.win_conditions import winner_user_ids

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    if state.winner_team is None:
        # Distinguish "registration timed out" from "/stop or other mid-game cancel"
        from app.core.state import Phase

        if state.phase == Phase.CANCELLED and not state.started_at:
            # Game was cancelled in WAITING phase → never started
            min_players = state.settings.get("gameplay", {}).get("min_players", 4)
            await _safe_send(
                bot,
                state.chat_id,
                _("game-cancelled-not-enough-players", min_players=min_players),
            )
        else:
            await _safe_send(bot, state.chat_id, _("game-cancelled"))
        return

    # Determine individual winners (team + qualifying singletons)
    winners_ids = set(winner_user_ids(state, state.winner_team))

    sorted_players = sorted(state.players, key=lambda x: x.join_order)
    winners = [p for p in sorted_players if p.user_id in winners_ids]
    losers = [p for p in sorted_players if p.user_id not in winners_ids]

    sections: list[str] = [_("game-end-header")]

    if winners:
        winner_lines = [
            f"{p.join_order}. {player_mention(p.user_id, p.first_name)} - {role_emoji_name(p.role, locale)}"
            for p in winners
        ]
        sections.append(_("game-end-winners-section") + "\n" + "\n".join(winner_lines))

    if losers:
        loser_lines = [
            f"{p.join_order}. {player_mention(p.user_id, p.first_name)} - {role_emoji_name(p.role, locale)}"
            for p in losers
        ]
        sections.append(_("game-end-losers-section") + "\n" + "\n".join(loser_lines))

    # Duration in minutes
    if state.started_at and state.finished_at:
        duration_min = max(1, (state.finished_at - state.started_at) // 60)
        sections.append(_("game-end-duration", minutes=duration_min))

    text = "\n\n".join(sections)
    try:
        await bot.send_message(state.chat_id, text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"send_message (game-end) failed: {e}")
