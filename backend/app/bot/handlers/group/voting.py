"""Voting UI: inline tugmali ovoz + hanging confirm (👍/👎)."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from app.core.state import GameState, Phase, Vote
from app.db.models import User
from app.services import game_service
from app.services.i18n_service import Translator, get_translator
from app.services.messaging import _safe_send, player_mention

router = Router(name="group_voting")


def build_voting_keyboard(state: GameState, _: Translator) -> InlineKeyboardMarkup:
    """Inline tugmali voting — har tirik o'yinchi tugma + 'Hech kim'."""
    rows: list[list[InlineKeyboardButton]] = []
    for p in state.alive_players():
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{p.join_order} {p.first_name}",
                    callback_data=f"vote:cast:{p.user_id}",
                )
            ]
        )
    if state.settings.get("gameplay", {}).get("allow_skip_day_vote", True):
        rows.append([InlineKeyboardButton(text=_("vote-skip-button"), callback_data="vote:cast:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_confirm_keyboard(target_user_id: int, _: Translator) -> InlineKeyboardMarkup:
    """👍/👎 tasdiqlash."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("hanging-yes"),
                    callback_data=f"hangconfirm:yes:{target_user_id}",
                ),
                InlineKeyboardButton(
                    text=_("hanging-no"),
                    callback_data=f"hangconfirm:no:{target_user_id}",
                ),
            ]
        ]
    )


@router.callback_query(F.data.startswith("vote:cast:"))
async def callback_vote_cast(query: CallbackQuery, user: User, _: Translator) -> None:
    if query.data is None or query.message is None:
        await query.answer()
        return
    try:
        target_id = int(query.data.split(":")[2])
    except (IndexError, ValueError):
        await query.answer("Invalid", show_alert=True)
        return

    chat_id = query.message.chat.id
    state = await game_service.load_state(chat_id)
    if state is None or state.phase != Phase.VOTING:
        await query.answer(_("vote-not-in-voting"), show_alert=True)
        return

    voter = state.get_player(user.id)
    if voter is None or not voter.alive:
        await query.answer(_("vote-not-alive"), show_alert=True)
        return

    # Self-vote blocked
    if target_id == user.id:
        await query.answer(_("vote-cannot-self"), show_alert=True)
        return

    # Validate target
    if target_id != 0:
        target = state.get_player(target_id)
        if target is None or not target.alive:
            await query.answer(_("vote-target-invalid"), show_alert=True)
            return

    # Mayor 2x weight
    weight = 2 if voter.role == "mayor" else 1

    # Crook (Aferist) proxy vote — uses target_user's name from previous night
    voter_id = user.id
    if voter.role == "crook":
        proxy_target_id = voter.extra.get("proxy_target")
        if proxy_target_id is not None:
            proxy_target = state.get_player(proxy_target_id)
            if proxy_target is not None and proxy_target.alive:
                # Cast vote AS proxy_target (their name appears, but it's Crook's choice)
                voter_id = proxy_target_id
                # Mayor weight uses proxy_target's role
                weight = 2 if proxy_target.role == "mayor" else 1

    state.current_votes[user.id] = Vote(voter_id=voter_id, target_id=target_id, weight=weight)
    await game_service.save_state(state)

    show_anon = state.settings.get("display", {}).get("anonymous_voting", False)
    if show_anon:
        await query.answer(_("vote-recorded-anon"), show_alert=False)
    else:
        if target_id == 0:
            await query.answer(_("vote-skipped-toast"), show_alert=False)
            # Broadcast abstention to group (mirrors @MafiaAzBot format)
            try:
                voter_name = _safe_html(voter.first_name)
                await query.bot.send_message(
                    chat_id,
                    _("vote-broadcast-abstain", voter=voter_name),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.debug(f"Vote broadcast failed: {e}")
        else:
            target = state.get_player(target_id)
            if target is not None:
                await query.answer(
                    _("vote-recorded-toast", target=target.first_name),
                    show_alert=False,
                )
                # Broadcast individual vote to group
                try:
                    voter_name = _safe_html(voter.first_name)
                    target_name = _safe_html(target.first_name)
                    await query.bot.send_message(
                        chat_id,
                        _(
                            "vote-broadcast",
                            voter=voter_name,
                            target=target_name,
                        ),
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.debug(f"Vote broadcast failed: {e}")


def _safe_html(text: str) -> str:
    return (text or "").replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


@router.callback_query(F.data.startswith("hangconfirm:"))
async def callback_hanging_confirm(query: CallbackQuery, user: User, _: Translator) -> None:
    """👍/👎 — hanging tasdiqlash."""
    if query.data is None or query.message is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid", show_alert=True)
        return
    decision = parts[1]
    try:
        target_id = int(parts[2])
    except ValueError:
        await query.answer("Invalid", show_alert=True)
        return

    chat_id = query.message.chat.id
    state = await game_service.load_state(chat_id)
    if state is None or state.phase != Phase.HANGING_CONFIRM:
        await query.answer(_("hanging-confirm-expired"), show_alert=True)
        return

    voter = state.get_player(user.id)
    if voter is None or not voter.alive:
        await query.answer(_("vote-not-alive"), show_alert=True)
        return

    # Mayor 2x
    weight = 2 if voter.role == "mayor" else 1

    confirm_data: dict = state.current_round().__dict__.setdefault(
        "hanging_confirm",
        {"target_id": target_id, "yes": {}, "no": {}},
    )
    if decision == "yes":
        confirm_data["yes"][str(user.id)] = weight
        confirm_data["no"].pop(str(user.id), None)
        await query.answer("👍", show_alert=False)
    else:
        confirm_data["no"][str(user.id)] = weight
        confirm_data["yes"].pop(str(user.id), None)
        await query.answer("👎", show_alert=False)

    await game_service.save_state(state)


# === Helpers called from PhaseManager hook ===


async def announce_voting(bot: Bot, state: GameState) -> None:
    """Voting fazasi boshlanganda inline tugmali xabar."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    keyboard = build_voting_keyboard(state, _)
    text = _("voting-prompt", count=len(state.alive_players()))
    try:
        await bot.send_message(state.chat_id, text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Could not send voting prompt: {e}")


async def announce_hanging_confirm(bot: Bot, state: GameState, target_id: int) -> None:
    """Eng ko'p ovoz olgan o'yinchi uchun 👍/👎 tasdiqlash."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    target = state.get_player(target_id)
    if target is None:
        return

    keyboard = build_confirm_keyboard(target_id, _)
    text = _(
        "hanging-confirm-prompt",
        target=player_mention(target_id, target.first_name),
    )
    await _safe_send(bot, state.chat_id, text)
    try:
        await bot.send_message(state.chat_id, text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Hanging confirm message failed: {e}")
