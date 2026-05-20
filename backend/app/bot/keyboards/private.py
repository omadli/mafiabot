"""Private chat keyboards — /start main menu, language picker, etc."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.services.i18n_service import Translator


def main_menu_keyboard(_plain: Translator) -> InlineKeyboardMarkup:
    """Bot bilan private chatdagi asosiy menyu.

    Layout (rendered with i18n labels):
      [Profile]  [Premium groups]
      [Shop]     [Buy Diamonds]
      [Add to group]              (URL button)
      [Help]
      [Language] [Game rules]

    Button labels go through `_plain` because Telegram renders inline-button
    text as plain text — `<tg-emoji>` HTML from `<e:…>` markers would
    otherwise leak as raw text.
    """
    add_to_group_url = f"https://t.me/{settings.bot_username}?startgroup=true"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_plain("btn-profile"), callback_data="menu:profile"),
                InlineKeyboardButton(
                    text=_plain("btn-premium-groups"), callback_data="premiumgroups:open"
                ),
            ],
            [
                InlineKeyboardButton(text=_plain("btn-shop"), callback_data="shop:open"),
                InlineKeyboardButton(
                    text=_plain("btn-buy-diamonds"), callback_data="shop:diamonds"
                ),
            ],
            [InlineKeyboardButton(text=_plain("btn-add-to-group"), url=add_to_group_url)],
            [InlineKeyboardButton(text=_plain("btn-help"), callback_data="menu:help")],
            [
                InlineKeyboardButton(text=_plain("btn-language"), callback_data="menu:lang"),
                InlineKeyboardButton(text=_plain("btn-rules"), callback_data="menu:rules"),
            ],
        ]
    )


def language_picker_keyboard(_: Translator) -> InlineKeyboardMarkup:
    """3 ta til + back tugmasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="menu:lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="menu:lang:ru"),
            ],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="menu:lang:en")],
            [InlineKeyboardButton(text=_("btn-back"), callback_data="menu:home")],
        ]
    )


def back_to_menu_keyboard(_: Translator) -> InlineKeyboardMarkup:
    """Faqat 'Orqaga' tugmasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("btn-back"), callback_data="menu:home")],
        ]
    )
