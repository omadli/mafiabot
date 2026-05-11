"""Aiogram filters."""

from app.bot.filters.group_admin import IsGroupAdmin
from app.bot.filters.super_admin import IsSuperAdmin

__all__ = ["IsGroupAdmin", "IsSuperAdmin"]
