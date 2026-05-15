"""Group `/settings` command — admin-only.

Forwards the admin to a private DM with the full settings menu
(inline keyboard + WebApp deeplink button).
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.bot.filters.group_admin import IsGroupAdmin
from app.bot.handlers.private.group_settings import build_settings_home_message
from app.db.models import Group, GroupSettings, User
from app.services.i18n_service import Translator

router = Router(name="group_settings")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.message(Command("settings", prefix="/!"), IsGroupAdmin())
async def cmd_settings_admin(message: Message, user: User, bot: Bot, _: Translator) -> None:
    """Admin chaqirgan /settings — DM orqali sozlamalar menyusini ochish."""
    group = await Group.get_or_none(id=message.chat.id)
    if group is None:
        await message.reply(_("settings-group-not-configured"))
        return
    s = await GroupSettings.get_or_none(group_id=group.id)
    if s is None:
        await message.reply(_("settings-group-not-configured"))
        return

    text, kb = await build_settings_home_message(group, s, _)
    try:
        await bot.send_message(user.id, text, reply_markup=kb, parse_mode="HTML")
        await message.reply(_("settings-sent-to-dm"))
    except TelegramForbiddenError:
        await message.reply(_("settings-cannot-dm"))
    except Exception as e:
        logger.warning(f"/settings DM failed for user {user.id}: {e}")
        await message.reply(_("settings-dm-failed"))


@router.message(Command("settings", prefix="/!"))
async def cmd_settings_non_admin(message: Message, _: Translator) -> None:
    """Admin emas — kichik xato xabari."""
    await message.reply(_("settings-admin-only"))
