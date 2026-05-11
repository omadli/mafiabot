"""/start handler — welcomes user, handles deeplink (join_<group_id>)."""

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from app.bot.handlers.shared.registration import (
    build_registration_keyboard,
    format_registration_text,
)
from app.bot.keyboards.private import main_menu_keyboard
from app.config import settings
from app.core.state import Phase
from app.db.models import Game, Group, User
from app.services import game_service
from app.services.i18n_service import Translator

router = Router(name="private_start")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(
    message: Message, command: CommandObject, user: User, _: Translator
) -> None:
    """Handle /start join_<group_id> deeplink."""
    payload = command.args or ""

    if payload.startswith("join_"):
        try:
            group_id = int(payload.removeprefix("join_"))
        except ValueError:
            await message.answer(_("deeplink-invalid"))
            return
        await _handle_join(message, user, group_id, _)
        return

    if payload.startswith("admin_"):
        # Super admin 1-time login token
        await message.answer(_("admin-login-deeplink-todo"))
        return

    # Deeplink had unknown payload — show welcome with menu
    await message.answer(
        _("start-welcome", username=user.first_name),
        reply_markup=main_menu_keyboard(_),
        parse_mode="HTML",
    )


@router.message(CommandStart())
async def start_default(message: Message, user: User, _: Translator) -> None:
    """Plain /start (no payload)."""
    await message.answer(
        _("start-welcome", username=user.first_name),
        reply_markup=main_menu_keyboard(_),
        parse_mode="HTML",
    )


async def _handle_join(message: Message, user: User, group_id: int, _: Translator) -> None:
    """Foydalanuvchi guruhga qo'shilmoqchi (deeplink orqali)."""
    # Banned check
    if user.is_banned:
        await message.answer(
            _(
                "join-banned",
                until=user.banned_until.strftime("%Y-%m-%d %H:%M") if user.banned_until else "—",
                reason=user.ban_reason or "—",
            )
        )
        return

    # Roast: already in this game?
    if user.active_game_id is not None:
        active_game = await Game.get_or_none(id=user.active_game_id)
        if active_game is not None:
            await active_game.fetch_related("group")
            if active_game.group_id == group_id:
                await message.answer(_("join-already-in-this-game"))
                return
            await message.answer(
                _("join-already-in-other-group", group_title=active_game.group.title)
            )
            return

    # Find group
    group = await Group.get_or_none(id=group_id)
    if group is None or not group.is_active:
        await message.answer(_("join-group-not-found"))
        return

    # Load live state
    state = await game_service.load_state(group_id)
    if state is None or state.phase != Phase.WAITING:
        await message.answer(_("join-no-active-registration"))
        return

    # Register
    try:
        await game_service.register_player(state, user)
    except game_service.GameError as e:
        await message.answer(_(str(e)))
        return

    logger.info(f"User {user.id} joined game {state.id} in group {group_id}")

    # Refresh group registration message
    bot: Bot = message.bot  # type: ignore[assignment]
    if state.registration_message_id:
        try:
            text = format_registration_text(state, _)
            keyboard = build_registration_keyboard(state, settings.bot_username, _)
            await bot.edit_message_text(
                text,
                chat_id=state.chat_id,
                message_id=state.registration_message_id,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.debug(f"Could not refresh registration message: {e}")

    # Confirm to user
    group_link = group.invite_link or f"tg://resolve?domain={settings.bot_username}"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn-back-to-group"), url=group_link)]]
    )
    await message.answer(_("join-success"), reply_markup=keyboard)
