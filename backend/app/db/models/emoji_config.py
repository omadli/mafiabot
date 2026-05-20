"""EmojiConfig — global registry of bot-message emojis (scene / item /
action / status), each editable by super admins and overridable per group.

Mirror of `RoleConfig` for non-role visual elements: night/day transitions,
death announcements, inventory items, action confirmations, etc. The bot
references them via translator keys like `emoji-scene-night`,
`emoji-item-shield`, `emoji-action-kill`.
"""

from __future__ import annotations

from typing import ClassVar

from tortoise import fields
from tortoise.models import Model

# Seed data. `code` shape: `{category}-{slug}`.
# Names are short labels for the admin dashboard, not user-facing strings.
DEFAULT_EMOJI_CONFIGS: list[dict] = [
    # --- Scene / phase transitions ---
    {
        "code": "scene-game-start",
        "category": "scene",
        "order_idx": 10,
        "name_uz": "O'yin boshlanishi",
        "name_ru": "Начало игры",
        "name_en": "Game start",
        "static_emoji": "🃏",
        "custom_emoji_id": "",
    },
    {
        "code": "scene-night",
        "category": "scene",
        "order_idx": 20,
        "name_uz": "Tun",
        "name_ru": "Ночь",
        "name_en": "Night",
        "static_emoji": "🌙",
        "custom_emoji_id": "",
    },
    {
        "code": "scene-day",
        "category": "scene",
        "order_idx": 30,
        "name_uz": "Kun",
        "name_ru": "День",
        "name_en": "Day",
        "static_emoji": "☀️",
        "custom_emoji_id": "",
    },
    {
        "code": "scene-voting",
        "category": "scene",
        "order_idx": 40,
        "name_uz": "Ovoz berish",
        "name_ru": "Голосование",
        "name_en": "Voting",
        "static_emoji": "🗳",
        "custom_emoji_id": "",
    },
    {
        "code": "scene-hanging",
        "category": "scene",
        "order_idx": 50,
        "name_uz": "Osishni tasdiqlash",
        "name_ru": "Подтверждение казни",
        "name_en": "Hanging confirm",
        "static_emoji": "⚖️",
        "custom_emoji_id": "",
    },
    {
        "code": "scene-last-words",
        "category": "scene",
        "order_idx": 60,
        "name_uz": "So'nggi so'z",
        "name_ru": "Последние слова",
        "name_en": "Last words",
        "static_emoji": "💬",
        "custom_emoji_id": "",
    },
    {
        "code": "scene-finished",
        "category": "scene",
        "order_idx": 70,
        "name_uz": "O'yin tugadi",
        "name_ru": "Игра окончена",
        "name_en": "Game finished",
        "static_emoji": "🏁",
        "custom_emoji_id": "",
    },
    # --- Status / outcomes ---
    {
        "code": "status-death",
        "category": "status",
        "order_idx": 110,
        "name_uz": "O'lim",
        "name_ru": "Смерть",
        "name_en": "Death",
        "static_emoji": "💀",
        "custom_emoji_id": "",
    },
    {
        "code": "status-trophy",
        "category": "status",
        "order_idx": 120,
        "name_uz": "Yutuq",
        "name_ru": "Победа",
        "name_en": "Trophy",
        "static_emoji": "🏆",
        "custom_emoji_id": "",
    },
    {
        "code": "status-saved",
        "category": "status",
        "order_idx": 130,
        "name_uz": "Saqlandi",
        "name_ru": "Спасён",
        "name_en": "Saved",
        "static_emoji": "🛡",
        "custom_emoji_id": "",
    },
    {
        "code": "status-spark",
        "category": "status",
        "order_idx": 140,
        "name_uz": "Uchqun",
        "name_ru": "Искра",
        "name_en": "Spark",
        "static_emoji": "💫",
        "custom_emoji_id": "",
    },
    # --- Inventory items ---
    {
        "code": "item-shield",
        "category": "item",
        "order_idx": 210,
        "name_uz": "Qalqon",
        "name_ru": "Щит",
        "name_en": "Shield",
        "static_emoji": "🛡",
        "custom_emoji_id": "",
    },
    {
        "code": "item-killer-shield",
        "category": "item",
        "order_idx": 215,
        "name_uz": "Qotil qalqoni",
        "name_ru": "Щит от убийцы",
        "name_en": "Killer shield",
        "static_emoji": "⛑",
        "custom_emoji_id": "",
    },
    {
        "code": "item-vote-shield",
        "category": "item",
        "order_idx": 220,
        "name_uz": "Ovoz qalqoni",
        "name_ru": "Щит от голосования",
        "name_en": "Vote shield",
        "static_emoji": "⚖️",
        "custom_emoji_id": "",
    },
    {
        "code": "item-rifle",
        "category": "item",
        "order_idx": 230,
        "name_uz": "Miltiq",
        "name_ru": "Винтовка",
        "name_en": "Rifle",
        "static_emoji": "🔫",
        "custom_emoji_id": "",
    },
    {
        "code": "item-mask",
        "category": "item",
        "order_idx": 240,
        "name_uz": "Niqob",
        "name_ru": "Маска",
        "name_en": "Mask",
        "static_emoji": "🎭",
        "custom_emoji_id": "",
    },
    {
        "code": "item-fake-document",
        "category": "item",
        "order_idx": 250,
        "name_uz": "Soxta hujjat",
        "name_ru": "Поддельный документ",
        "name_en": "Fake document",
        "static_emoji": "📁",
        "custom_emoji_id": "",
    },
    {
        "code": "item-special-role",
        "category": "item",
        "order_idx": 260,
        "name_uz": "Maxsus rol",
        "name_ru": "Особая роль",
        "name_en": "Special role",
        "static_emoji": "🃏",
        "custom_emoji_id": "",
    },
    # --- Action verbs (used in night-result / DM confirmations) ---
    {
        "code": "action-kill",
        "category": "action",
        "order_idx": 310,
        "name_uz": "Hujum",
        "name_ru": "Атака",
        "name_en": "Attack",
        "static_emoji": "🔪",
        "custom_emoji_id": "",
    },
    {
        "code": "action-check",
        "category": "action",
        "order_idx": 320,
        "name_uz": "Tekshirish",
        "name_ru": "Проверка",
        "name_en": "Check",
        "static_emoji": "🔍",
        "custom_emoji_id": "",
    },
    {
        "code": "action-heal",
        "category": "action",
        "order_idx": 330,
        "name_uz": "Davolash",
        "name_ru": "Лечение",
        "name_en": "Heal",
        "static_emoji": "💊",
        "custom_emoji_id": "",
    },
    {
        "code": "action-visit",
        "category": "action",
        "order_idx": 340,
        "name_uz": "Tashrif",
        "name_ru": "Визит",
        "name_en": "Visit",
        "static_emoji": "🚶",
        "custom_emoji_id": "",
    },
    {
        "code": "action-sleep",
        "category": "action",
        "order_idx": 350,
        "name_uz": "Uxlatish",
        "name_ru": "Усыпление",
        "name_en": "Sleep",
        "static_emoji": "💤",
        "custom_emoji_id": "",
    },
    {
        "code": "action-reveal",
        "category": "action",
        "order_idx": 360,
        "name_uz": "Oshkor qilish",
        "name_ru": "Раскрытие",
        "name_en": "Reveal",
        "static_emoji": "👁",
        "custom_emoji_id": "",
    },
    # --- Currency / economy ---
    {
        "code": "currency-diamond",
        "category": "currency",
        "order_idx": 410,
        "name_uz": "Olmos",
        "name_ru": "Алмаз",
        "name_en": "Diamond",
        "static_emoji": "💎",
        "custom_emoji_id": "",
    },
    {
        "code": "currency-dollar",
        "category": "currency",
        "order_idx": 420,
        "name_uz": "Dollar",
        "name_ru": "Доллар",
        "name_en": "Dollar",
        "static_emoji": "💵",
        "custom_emoji_id": "",
    },
    {
        "code": "currency-xp",
        "category": "currency",
        "order_idx": 430,
        "name_uz": "XP",
        "name_ru": "XP",
        "name_en": "XP",
        "static_emoji": "⭐",
        "custom_emoji_id": "",
    },
    {
        "code": "currency-stars",
        "category": "currency",
        "order_idx": 440,
        "name_uz": "Telegram Stars",
        "name_ru": "Telegram Stars",
        "name_en": "Telegram Stars",
        "static_emoji": "⭐",
        "custom_emoji_id": "",
    },
]


class EmojiConfig(Model):
    """Per-code display config for non-role bot-message emojis.

    Read constantly during games — always go through cached `emoji_config_service`,
    never hit this model directly from a handler.
    """

    code = fields.CharField(pk=True, max_length=64)  # e.g. "scene-night"
    category = fields.CharField(max_length=16)  # scene | status | item | action | currency
    name_uz = fields.CharField(max_length=64)
    name_ru = fields.CharField(max_length=64)
    name_en = fields.CharField(max_length=64)
    static_emoji = fields.CharField(max_length=32)
    custom_emoji_id = fields.CharField(max_length=32, default="")
    order_idx = fields.IntField(default=0)
    updated_at = fields.DatetimeField(auto_now=True)
    updated_by_tg_id = fields.BigIntField(null=True)

    class Meta:
        table = "emoji_configs"
        ordering = ["order_idx"]

    DEFAULTS: ClassVar[list[dict]] = DEFAULT_EMOJI_CONFIGS
