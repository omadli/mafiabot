"""Private chat: receive role night action target picks via inline callbacks."""

from __future__ import annotations

import asyncio
import contextlib

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from app.bot.handlers.shared.stale_dm import is_stale_for_phase, notify_and_drop
from app.config import settings as app_settings
from app.core.state import GameState, NightAction, Phase, Team
from app.db.models import Group, User
from app.services import game_service
from app.services.i18n_service import Translator, get_translator
from app.services.role_actions import role_action_type

router = Router(name="private_role_actions")
router.callback_query.filter(F.data.startswith("night:"))


async def _back_to_group_kb(
    state: GameState, _: Translator, _plain: Translator | None = None
) -> InlineKeyboardMarkup:
    """Build a single-button keyboard pointing the user back at the group."""
    group = await Group.get_or_none(id=state.group_id)
    url = (
        group.invite_link
        if group and group.invite_link
        else f"https://t.me/{app_settings.bot_username}"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_plain("btn-back-to-group"), url=url)]]
    )


@router.callback_query(F.data.startswith("night:rfconfirm:"))
async def handle_rifle_confirm(
    query: CallbackQuery, user: User, _: Translator, bot: Bot, _plain: Translator | None = None
) -> None:
    """Two-button "🔫 otishni xohlaysizmi?" gate before a rifle shot fires.

    Callback shapes — single-handler dispatch so we don't depend on
    aiogram's filter-order semantics:

      * `night:rfconfirm:don:<target_id>`        — Don taps 🔫 on target
      * `night:rfconfirm:detective:<target_id>`  — Detective taps 🔫 (kill)
      * `night:rfconfirm:cancel:<role>`          — Don pressed "Yo'q"

    On "Ha" the confirmation message edits to fire the existing rifle
    callback (`night:<role>:<target_id>:rifle` /
    `night:detective:kill:<target_id>:rifle`) which records the action
    and consumes the rifle. "Yo'q" for Don rebuilds the target list
    here; for Detective the No button is wired directly to
    `night:detchoose:kill` (rebuilds the kill list via the existing
    chooser handler).
    """
    if query.data is None or query.message is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 4:
        await query.answer("Invalid", show_alert=True)
        return
    head = parts[2]  # "don" | "detective" | "cancel"

    if user.active_game_id is None:
        await notify_and_drop(query, _plain)
        return
    state = await _find_state_by_game_id(user.active_game_id)
    if is_stale_for_phase(state, Phase.NIGHT):
        await notify_and_drop(query, _plain)
        return
    assert state is not None

    # --- Cancel path (Yo'q tugmasi) ---
    # Single-step roles (don/maniac/killer) ask us to rebuild the target
    # list here. Detective's cancel routes to night:detchoose:kill so we
    # don't even reach this branch for it.
    if head == "cancel":
        role_code = parts[3]
        if role_code not in {"don", "maniac", "killer"}:
            await query.answer("Invalid", show_alert=True)
            return
        actor = state.get_player(user.id)
        if actor is None or not actor.alive or actor.role != role_code:
            await query.answer(_plain("night-cannot-act"), show_alert=True)
            return
        from app.services.role_actions import build_attacker_target_keyboard

        locale = state.settings.get("language", "uz")
        kb = await build_attacker_target_keyboard(state, actor, locale)
        if kb is None:
            await query.answer(_plain("night-no-targets"), show_alert=True)
            return
        text = _(f"night-prompt-{role_code}")
        with contextlib.suppress(Exception):
            await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]
        await query.answer()
        return

    # --- Prompt path (rifle tapped on a specific target) ---
    role_code = head
    if role_code not in ("don", "maniac", "killer", "detective"):
        await query.answer(_plain("night-cannot-act"), show_alert=True)
        return
    try:
        target_id = int(parts[3])
    except ValueError:
        await query.answer("Invalid", show_alert=True)
        return

    actor = state.get_player(user.id)
    if actor is None or not actor.alive or actor.role != role_code:
        await query.answer(_plain("night-cannot-act"), show_alert=True)
        return
    target = state.get_player(target_id)
    if target is None or not target.alive:
        await query.answer(_plain("night-target-invalid"), show_alert=True)
        return

    # Validate the player still owns a rifle. The button was rendered at
    # prompt time; in the meantime they might have spent it on a previous
    # round or had it stripped by stale state.
    from app.db.models import UserInventory

    inv = await UserInventory.get_or_none(user_id=user.id)
    if inv is None or inv.rifle < 1:
        await query.answer(_plain("night-no-rifle"), show_alert=True)
        return

    if role_code in {"don", "maniac", "killer"}:
        yes_cb = f"night:{role_code}:{target_id}:rifle"
        no_cb = f"night:rfconfirm:cancel:{role_code}"
    else:  # detective — kill branch (rifle implies kill)
        yes_cb = f"night:detective:kill:{target_id}:rifle"
        no_cb = "night:detchoose:kill"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_plain("btn-rifle-yes"), callback_data=yes_cb),
                InlineKeyboardButton(text=_plain("btn-rifle-no"), callback_data=no_cb),
            ]
        ]
    )
    text = _("rifle-confirm-prompt", target=target.first_name)
    with contextlib.suppress(Exception):
        await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]
    await query.answer()


@router.callback_query(F.data.startswith("night:detchoose:"))
async def handle_detective_chooser(
    query: CallbackQuery, user: User, _: Translator, bot: Bot, _plain: Translator | None = None
) -> None:
    """Detective picked 'check' / 'kill' / 'back' — edit the chooser DM to
    show the target keyboard (or jump back to the chooser). The actual
    target selection is then handled by handle_night_pick via callback
    `night:detective:<action>:<target>`."""
    if query.data is None or query.message is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 3 or parts[2] not in ("check", "kill", "back"):
        await query.answer("Invalid", show_alert=True)
        return
    action_kind = parts[2]

    if user.active_game_id is None:
        await notify_and_drop(query, _plain)
        return
    state = await _find_state_by_game_id(user.active_game_id)
    if is_stale_for_phase(state, Phase.NIGHT):
        await notify_and_drop(query, _plain)
        return
    assert state is not None  # narrowed by is_stale_for_phase (False → not None)

    actor = state.get_player(user.id)
    if actor is None or not actor.alive or actor.role != "detective":
        await query.answer(_plain("night-cannot-act"), show_alert=True)
        return

    # "back" → re-render the check/kill chooser. Lets the detective change
    # their mind after accidentally tapping into the wrong branch.
    if action_kind == "back":
        prior_lines: list[str] = []
        check_results: dict = actor.extra.get("check_results", {}) or {}
        if check_results:
            from app.services.messaging import role_emoji_name

            locale = state.settings.get("language", "uz")
            prior_lines.append(_("night-prompt-detective-prior-header"))
            for _uid_str, info in check_results.items():
                role_label = role_emoji_name(info.get("role", "citizen"), locale)
                name = info.get("name", "?")
                prior_lines.append(
                    _("night-prompt-detective-prior-line", name=name, role=role_label)
                )
            prior_lines.append("")

        prior_text = "\n".join(prior_lines)
        chooser_text = _("night-prompt-detective-chooser")
        text = (prior_text + chooser_text) if prior_text else chooser_text

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_plain("btn-detective-check"),
                        callback_data="night:detchoose:check",
                    ),
                    InlineKeyboardButton(
                        text=_plain("btn-detective-kill"),
                        callback_data="night:detchoose:kill",
                    ),
                ]
            ]
        )
        with contextlib.suppress(Exception):
            await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]
        await query.answer()
        return

    from app.services.role_actions import send_detective_target_keyboard

    locale = state.settings.get("language", "uz")
    kb = await send_detective_target_keyboard(bot, state, actor, action_kind, locale)
    if kb is None:
        await query.answer(_plain("night-no-targets"), show_alert=True)
        return

    prompt = _(
        "night-prompt-detective-target-list-check"
        if action_kind == "check"
        else "night-prompt-detective-target-list-kill"
    )
    with contextlib.suppress(Exception):
        await query.message.edit_text(prompt, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]
    await query.answer()


@router.callback_query(F.data.startswith("night:"))
async def handle_night_pick(
    query: CallbackQuery, user: User, _: Translator, bot: Bot, _plain: Translator | None = None
) -> None:
    if query.data is None:
        await query.answer()
        return

    parts = query.data.split(":")
    # Accepted shapes:
    #   night:<role>:<target_id>
    #   night:<role>:<target_id>:rifle               (attack with rifle)
    #   night:detective:<action>:<target_id>          (detective 2-step)
    #   night:detective:kill:<target_id>:rifle        (detective + rifle)
    use_rifle = parts[-1] == "rifle"
    body = parts[:-1] if use_rifle else parts
    try:
        if body[1] == "detective" and len(body) == 4:
            role_code = "detective"
            action_kind = body[2]  # check | kill
            target_id = int(body[3])
        else:
            role_code = body[1]
            target_id = int(body[2])
            action_kind = role_action_type(role_code)
    except (IndexError, ValueError):
        await query.answer("Invalid", show_alert=True)
        return

    # Find which group this user is in
    if user.active_game_id is None:
        await notify_and_drop(query, _plain)
        return

    state = await _find_state_by_game_id(user.active_game_id)
    if is_stale_for_phase(state, Phase.NIGHT):
        await notify_and_drop(query, _plain)
        return
    assert state is not None  # narrowed by is_stale_for_phase (False → not None)

    actor = state.get_player(user.id)
    if actor is None or not actor.alive or actor.role != role_code:
        await query.answer(_plain("night-cannot-act"), show_alert=True)
        return

    # Skip
    if target_id == 0:
        state.current_actions.pop(user.id, None)
        await game_service.save_state(state)
        await query.answer(_plain("night-skipped"), show_alert=False)
        if query.message:
            back_kb = await _back_to_group_kb(state, _, _plain)
            with contextlib.suppress(Exception):
                await query.message.edit_text(_("night-skipped-confirm"), reply_markup=back_kb)  # type: ignore[union-attr]
        return

    # Validate target
    target = state.get_player(target_id)
    if target is None or not target.alive:
        await query.answer(_plain("night-target-invalid"), show_alert=True)
        return

    # If rifle was requested but the player no longer owns one (race vs
    # purchase), fail loudly so the UX stays honest. The rifle is NOT
    # decremented here — consumption is deferred to the resolver, which
    # only burns it when the shot had to pierce a real defence (shield,
    # killer_shield, or doctor heal). An undefended target dies but the
    # rifle slot survives. See ActionResolver._resolve / NightOutcome.
    if use_rifle:
        from app.db.models import UserInventory

        inv = await UserInventory.get_or_none(user_id=user.id)
        if inv is None or inv.rifle < 1:
            await query.answer(_plain("night-no-rifle"), show_alert=True)
            return

    # Record action
    action = NightAction(
        actor_id=user.id,
        role=role_code,
        action_type=action_kind,
        target_id=target_id,
        used_item=("rifle" if use_rifle else None),
    )
    state.current_actions[user.id] = action
    await game_service.save_state(state)

    await query.answer(
        _plain("night-action-recorded", target=target.first_name),
        show_alert=False,
    )
    if query.message:
        back_kb = await _back_to_group_kb(state, _, _plain)
        with contextlib.suppress(Exception):
            await query.message.edit_text(  # type: ignore[union-attr]
                _("night-action-confirmed", target=target.first_name),
                reply_markup=back_kb,
                parse_mode="HTML",
            )

    # Broadcast to other alive mafia teammates if actor is on the mafia team.
    # Lets the team coordinate / see each other's picks during night.
    if actor.team == Team.MAFIA:
        await _broadcast_to_mafia(bot, state, actor, target, action_kind)

    # Atmospheric per-role broadcast to the GROUP (idempotent per round).
    # Each role posts at most once per night — Mafia + Don share the
    # "Don tanladi" message so the team is treated as one. Detective has
    # two flavors depending on action_type.
    await _broadcast_role_atmosphere(bot, state, actor, action_kind)


_BROADCAST_KEY_OVERRIDES: dict[tuple[str, str], str] = {
    # Detective branches:
    ("detective", "check"): "night-action-msg-detective-check",
    ("detective", "kill"): "night-action-msg-detective-shoot",
    # Whole mafia team shares the "Don is choosing" line:
    ("mafia", "kill"): "night-action-msg-don",
    ("don", "kill"): "night-action-msg-don",
}


def _atmosphere_key(role_code: str, action_kind: str) -> str:
    return _BROADCAST_KEY_OVERRIDES.get((role_code, action_kind), f"night-action-msg-{role_code}")


async def _broadcast_role_atmosphere(
    bot: Bot,
    state: GameState,
    actor: object,  # PlayerState
    action_kind: str,
) -> None:
    """Post the role's atmospheric line to the group, at most once per round."""
    role_code = getattr(actor, "role", None)
    if not role_code:
        return

    key = _atmosphere_key(role_code, action_kind)
    round_log = state.current_round()
    posted: set[str] = set(round_log.extra.setdefault("broadcast_atmosphere_keys", []))
    if key in posted:
        return
    posted.add(key)
    round_log.extra["broadcast_atmosphere_keys"] = list(posted)
    await game_service.save_state(state)

    locale = state.settings.get("language", "uz")
    t = get_translator(locale)
    text = t(key)
    # Fluent returns the key itself when missing — bail silently in that case.
    if text == key:
        return
    with contextlib.suppress(Exception):
        await bot.send_message(state.chat_id, text)


async def _broadcast_to_mafia(
    bot: Bot,
    state: GameState,
    actor,
    target,
    action_kind: str,
) -> None:
    """Notify other alive mafia members of one member's night pick."""
    locale = state.settings.get("language", "uz")
    t = get_translator(locale)
    actor_role_label = t(f"role-{actor.role}")

    text = t(
        "mafia-team-pick-broadcast",
        role=actor_role_label,
        actor=actor.first_name,
        target=target.first_name,
        action=action_kind,
    )

    async def _dm(uid: int) -> None:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
        except TelegramForbiddenError:
            pass
        except Exception as e:
            logger.debug(f"Mafia pick broadcast DM to {uid} failed: {e}")

    targets = [
        p.user_id
        for p in state.alive_players()
        if p.team == Team.MAFIA and p.user_id != actor.user_id
    ]
    if not targets:
        return
    await asyncio.gather(*(_dm(uid) for uid in targets), return_exceptions=True)


async def _find_state_by_game_id(game_id) -> GameState | None:
    """Find live state for a game by game UUID — scan group_ids.

    For MVP simplicity: load Game from DB to get group_id.
    """
    from app.db.models import Game

    db_game = await Game.get_or_none(id=game_id)
    if db_game is None:
        return None
    return await game_service.load_state(db_game.group_id)  # type: ignore[attr-defined]
