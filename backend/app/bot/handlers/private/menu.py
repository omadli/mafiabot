"""Private chat main-menu callback handlers (menu:*).

All callbacks acknowledge with answerCallbackQuery and use edit_message_text
to update content in place (no new message spam).

Routes:
  menu:home       — back to main menu
  menu:profile    — open /profile (single-screen layout)
  menu:help       — short help text
  menu:rules      — full game rules + role list
  menu:lang       — language picker (shows 3 lang buttons)
  menu:lang:<uz|ru|en> — switch language, return to main menu
"""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from loguru import logger

from app.bot.keyboards.private import (
    back_to_menu_keyboard,
    language_picker_keyboard,
    main_menu_keyboard,
)
from app.db.models import User, UserInventory
from app.services.i18n_service import Translator, get_translator

router = Router(name="private_menu")


async def _edit(query: CallbackQuery, text: str, markup, parse_mode: str | None = "HTML") -> None:
    """Safely replace the message text + keyboard."""
    if query.message is None:
        return
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_text(text, reply_markup=markup, parse_mode=parse_mode)


@router.callback_query(F.data == "menu:home")
async def cb_home(query: CallbackQuery, user: User, _: Translator) -> None:
    """Asosiy menyuga qaytish."""
    await query.answer()
    text = _("start-welcome", username=user.first_name)
    await _edit(query, text, main_menu_keyboard(_))


@router.callback_query(F.data == "menu:profile")
async def cb_profile(query: CallbackQuery, user: User, _: Translator) -> None:
    """Profil + inventar single-screen ko'rinishini ochish."""
    # Lazy import to avoid circular (inventory.py imports menu indirectly)
    from app.bot.handlers.private.inventory import _build_profile_message

    await query.answer()
    inv, _new = await UserInventory.get_or_create(user=user)
    text, kb = await _build_profile_message(user, inv, _)
    await _edit(query, text, kb)


@router.callback_query(F.data == "menu:help")
async def cb_help(query: CallbackQuery, user: User, _: Translator) -> None:
    """Qisqacha yordam matni."""
    await query.answer()
    text = _("help-text")
    await _edit(query, text, back_to_menu_keyboard(_))


@router.callback_query(F.data == "menu:rules")
async def cb_rules(query: CallbackQuery, user: User, _: Translator) -> None:
    """O'yin qoidalari + rollar ro'yxati."""
    await query.answer()
    text = _("rules-text")
    await _edit(query, text, back_to_menu_keyboard(_))


@router.callback_query(F.data == "menu:lang")
async def cb_lang_picker(query: CallbackQuery, user: User, _: Translator) -> None:
    """Til tanlash menyusi."""
    await query.answer()
    text = _("language-picker-prompt")
    await _edit(query, text, language_picker_keyboard(_))


@router.callback_query(F.data.startswith("menu:lang:"))
async def cb_lang_switch(query: CallbackQuery, user: User, _: Translator) -> None:
    """Tilni o'zgartirish va asosiy menyuga qaytish."""
    if query.data is None:
        await query.answer()
        return
    new_lang = query.data.split(":")[2]
    if new_lang not in ("uz", "ru", "en"):
        await query.answer("Invalid", show_alert=True)
        return

    # Persist user's language
    user.language_code = new_lang
    await user.save(update_fields=["language_code"])

    # Re-translate everything in the new locale
    new_translator = get_translator(new_lang)
    await query.answer(new_translator("language-switched"), show_alert=False)

    text = new_translator("start-welcome", username=user.first_name)
    await _edit(query, text, main_menu_keyboard(new_translator))

    logger.info(f"User {user.id} switched language to {new_lang}")
