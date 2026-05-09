"""Private chat keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.i18n_service import Translator


def main_menu_keyboard(_: Translator) -> InlineKeyboardMarkup:
    """Bot bilan private chatdagi asosiy menyu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("btn-profile"), callback_data="profile")],
            [InlineKeyboardButton(text=_("btn-inventory"), callback_data="inventory")],
            [InlineKeyboardButton(text=_("btn-buy-diamonds"), callback_data="buy_diamonds")],
            [InlineKeyboardButton(text=_("btn-help"), callback_data="help")],
        ]
    )
