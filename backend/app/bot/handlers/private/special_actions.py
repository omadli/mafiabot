"""Maxsus rol UI handlerlari: Mage reaksiyasi, Arsonist final, Kamikaze hang choice."""

from __future__ import annotations

import contextlib

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from app.core.state import DeathReason, GameState, Phase
from app.db.models import User
from app.services import game_service
from app.services.i18n_service import Translator, get_translator
from app.services.messaging import _safe_send, player_mention, role_emoji_name

router = Router(name="private_special_actions")


# === Mage reactive ===


async def send_mage_reaction_prompt(
    bot: Bot, mage_user_id: int, attacker_role: str, attacker_id: int, locale: str
) -> None:
    """When Mage attacked at night, send choice prompt to lichka."""
    _ = get_translator(locale)
    role_label = role_emoji_name(attacker_role, locale)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("mage-forgive"),
                    callback_data=f"mage:forgive:{attacker_id}",
                ),
                InlineKeyboardButton(
                    text=_("mage-kill"),
                    callback_data=f"mage:kill:{attacker_id}",
                ),
            ]
        ]
    )
    try:
        await bot.send_message(
            mage_user_id,
            _("mage-attacked", attacker_role=role_label),
            reply_markup=keyboard,
        )
    except TelegramForbiddenError:
        logger.warning(f"Cannot DM Mage {mage_user_id}")


@router.callback_query(F.data.startswith("mage:"))
async def callback_mage_reaction(query: CallbackQuery, user: User, _: Translator) -> None:
    if query.data is None or query.message is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer()
        return

    decision = parts[1]
    try:
        attacker_id = int(parts[2])
    except ValueError:
        await query.answer("Invalid", show_alert=True)
        return

    if user.active_game_id is None:
        await query.answer(_("night-not-in-active-game"), show_alert=True)
        return

    state = await _find_state(user.active_game_id)
    if state is None:
        await query.answer("Game not found", show_alert=True)
        return

    mage = state.get_player(user.id)
    if mage is None or mage.role != "mage":
        await query.answer(_("night-cannot-act"), show_alert=True)
        return

    attacker = state.get_player(attacker_id)
    if attacker is None:
        await query.answer(_("night-target-invalid"), show_alert=True)
        return

    if decision == "forgive":
        await query.answer(_("mage-forgive-confirm"), show_alert=False)
        if query.message:
            with contextlib.suppress(Exception):
                await query.message.edit_text(_("mage-forgive-confirm-text"))
    else:  # kill
        if attacker.alive:
            attacker.alive = False
            attacker.died_at_round = state.round_num
            attacker.died_at_phase = Phase.NIGHT
            attacker.died_reason = DeathReason.KILLED_AFSUNGAR  # close enough
            await game_service.save_state(state)
        await query.answer(_("mage-kill-confirm"), show_alert=False)
        if query.message:
            with contextlib.suppress(Exception):
                await query.message.edit_text(
                    _("mage-kill-confirm-text", target=attacker.first_name)
                )


# === Arsonist "Oxirgi tun" ===


def build_arsonist_keyboard(state: GameState, _: Translator) -> InlineKeyboardMarkup:
    """Arsonist tunlik tugmalar — har tun + 'Oxirgi tun'."""
    rows = []
    for p in state.alive_players():
        if p.role == "arsonist":
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{p.join_order} {p.first_name}",
                    callback_data=f"night:arsonist:queue:{p.user_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("arsonist-final-night-button"),
                callback_data="night:arsonist:final:0",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("night:arsonist:"))
async def callback_arsonist_action(query: CallbackQuery, user: User, _: Translator) -> None:
    """G'azabkor: queue (target qo'shish) yoki final_night."""
    if query.data is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 4:
        await query.answer("Invalid", show_alert=True)
        return

    action_kind = parts[2]  # queue | final
    try:
        target_id = int(parts[3])
    except ValueError:
        await query.answer("Invalid", show_alert=True)
        return

    if user.active_game_id is None:
        await query.answer(_("night-not-in-active-game"), show_alert=True)
        return
    state = await _find_state(user.active_game_id)
    if state is None or state.phase != Phase.NIGHT:
        await query.answer(_("night-not-in-night-phase"), show_alert=True)
        return

    arsonist = state.get_player(user.id)
    if arsonist is None or arsonist.role != "arsonist":
        await query.answer(_("night-cannot-act"), show_alert=True)
        return

    from app.core.state import NightAction

    if action_kind == "queue":
        action = NightAction(
            actor_id=user.id, role="arsonist", action_type="queue", target_id=target_id
        )
        state.current_actions[user.id] = action
        await game_service.save_state(state)
        target = state.get_player(target_id)
        target_name = target.first_name if target else "?"
        await query.answer(_("arsonist-queued", target=target_name), show_alert=False)
    elif action_kind == "final":
        action = NightAction(
            actor_id=user.id, role="arsonist", action_type="final_night", target_id=user.id
        )
        state.current_actions[user.id] = action
        await game_service.save_state(state)
        await query.answer(_("arsonist-final-confirm"), show_alert=True)


# === Kamikaze hang choice ===


def build_kamikaze_choice_keyboard(
    state: GameState, kamikaze_id: int, _: Translator
) -> InlineKeyboardMarkup:
    """Kamikaze osilganda — kim bilan ketishni tanlash."""
    rows = []
    for p in state.alive_players():
        if p.user_id == kamikaze_id:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{p.join_order} {p.first_name}",
                    callback_data=f"kamikaze:take:{p.user_id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_kamikaze_choice(bot: Bot, state: GameState, kamikaze_id: int) -> None:
    """Kamikaze osilganda lichkaga prompt yuborish."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    keyboard = build_kamikaze_choice_keyboard(state, kamikaze_id, _)
    try:
        await bot.send_message(kamikaze_id, _("kamikaze-choose-victim"), reply_markup=keyboard)
    except TelegramForbiddenError:
        logger.warning(f"Cannot DM Kamikaze {kamikaze_id}")


@router.callback_query(F.data.startswith("kamikaze:take:"))
async def callback_kamikaze_take(query: CallbackQuery, user: User, _: Translator, bot: Bot) -> None:
    if query.data is None:
        await query.answer()
        return
    try:
        victim_id = int(query.data.split(":")[2])
    except (IndexError, ValueError):
        await query.answer("Invalid", show_alert=True)
        return

    if user.active_game_id is None:
        await query.answer(_("night-not-in-active-game"), show_alert=True)
        return

    state = await _find_state(user.active_game_id)
    if state is None:
        await query.answer("Game not found", show_alert=True)
        return

    kamikaze = state.get_player(user.id)
    if kamikaze is None or kamikaze.role != "kamikaze":
        await query.answer(_("night-cannot-act"), show_alert=True)
        return

    victim = state.get_player(victim_id)
    if victim is None or not victim.alive:
        await query.answer(_("night-target-invalid"), show_alert=True)
        return

    # Apply
    victim.alive = False
    victim.died_at_round = state.round_num
    victim.died_at_phase = Phase.VOTING
    victim.died_reason = DeathReason.KILLED_AFSUNGAR

    # Track for win condition
    kamikaze.extra["kamikaze_took_role"] = victim.role
    await game_service.save_state(state)

    # Broadcast
    locale = state.settings.get("language", "uz")
    _t = get_translator(locale)
    text = _t(
        "kamikaze-took-victim",
        kamikaze=player_mention(user.id, kamikaze.first_name),
        victim=player_mention(victim_id, victim.first_name),
    )
    await _safe_send(bot, state.chat_id, text)

    await query.answer(_("kamikaze-took-confirm"), show_alert=True)
    if query.message:
        with contextlib.suppress(Exception):
            await query.message.edit_text(_("kamikaze-took-confirm-text", target=victim.first_name))


# === Helpers ===


async def _find_state(game_id) -> GameState | None:
    from app.db.models import Game

    db_game = await Game.get_or_none(id=game_id)
    if db_game is None:
        return None
    return await game_service.load_state(db_game.group_id)
