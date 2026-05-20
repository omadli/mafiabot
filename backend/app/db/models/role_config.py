"""RoleConfig — per-role i18n names + emoji configuration.

One row per role slug (citizen / detective / … / snitch). Super admins
edit these from the dashboard at runtime; the game bot reads them through
`role_config_service` (cached). Group settings can later override on top.

Source of truth for slugs/team membership is `app.core.roles.ROLE_REGISTRY`
(this module just stores presentation data — names + emojis).
"""

from __future__ import annotations

from typing import ClassVar

from tortoise import fields
from tortoise.models import Model

# Default seed data — populated on first boot if the table is empty.
# Each entry: {slug, team, name_uz, name_ru, name_en, static_emoji, custom_emoji_id}.
# Names mirror the .ftl `role-*` strings (without the leading emoji);
# custom_emoji_id values come from Telegram's RestrictedEmoji set
# (user-curated, all 21 verified via getCustomEmojiStickers).
DEFAULT_ROLE_CONFIGS: list[dict] = [
    # Civilians (9) — win with the civilian camp
    {
        "role": "citizen",
        "team": "civilians",
        "order_idx": 10,
        "name_uz": "Tinch aholi",
        "name_ru": "Мирный житель",
        "name_en": "Civilian",
        "static_emoji": "👨🏼",
        "custom_emoji_id": "",
    },
    {
        "role": "detective",
        "team": "civilians",
        "order_idx": 20,
        "name_uz": "Komissar Katani",
        "name_ru": "Комиссар Катани",
        "name_en": "Commissioner Catani",
        "static_emoji": "🕵🏻‍♂",
        "custom_emoji_id": "",
    },
    {
        "role": "sergeant",
        "team": "civilians",
        "order_idx": 30,
        "name_uz": "Serjant",
        "name_ru": "Сержант",
        "name_en": "Sergeant",
        "static_emoji": "👮🏻‍♂",
        "custom_emoji_id": "",
    },
    {
        "role": "mayor",
        "team": "civilians",
        "order_idx": 40,
        "name_uz": "Janob",
        "name_ru": "Мэр",
        "name_en": "Mayor",
        "static_emoji": "🎖",
        "custom_emoji_id": "5332547853304734597",
    },
    {
        "role": "doctor",
        "team": "civilians",
        "order_idx": 50,
        "name_uz": "Doktor",
        "name_ru": "Доктор",
        "name_en": "Doctor",
        "static_emoji": "👨🏻‍⚕",
        "custom_emoji_id": "5429363657471434941",
    },
    {
        "role": "hooker",
        "team": "civilians",
        "order_idx": 60,
        "name_uz": "Kezuvchi",
        "name_ru": "Путана",
        "name_en": "Wanderer",
        "static_emoji": "💃",
        "custom_emoji_id": "5190799832159100491",
    },
    {
        "role": "hobo",
        "team": "civilians",
        "order_idx": 70,
        "name_uz": "Daydi",
        "name_ru": "Бомж",
        "name_en": "Tramp",
        "static_emoji": "🧙‍♂",
        "custom_emoji_id": "",
    },
    {
        "role": "lucky",
        "team": "civilians",
        "order_idx": 80,
        "name_uz": "Omadli",
        "name_ru": "Везунчик",
        "name_en": "Lucky",
        "static_emoji": "🤞🏼",
        "custom_emoji_id": "",
    },
    {
        "role": "kamikaze",
        "team": "civilians",
        "order_idx": 90,
        "name_uz": "Afsungar",
        "name_ru": "Камикадзе",
        "name_en": "Kamikaze",
        "static_emoji": "💣",
        "custom_emoji_id": "5469654973308476699",
    },
    # Mafia (5)
    {
        "role": "don",
        "team": "mafia",
        "order_idx": 110,
        "name_uz": "Don",
        "name_ru": "Дон",
        "name_en": "Don",
        "static_emoji": "🤵🏻",
        "custom_emoji_id": "",
    },
    {
        "role": "mafia",
        "team": "mafia",
        "order_idx": 120,
        "name_uz": "Mafiya",
        "name_ru": "Мафия",
        "name_en": "Mafia",
        "static_emoji": "🤵🏼",
        "custom_emoji_id": "",
    },
    {
        "role": "lawyer",
        "team": "mafia",
        "order_idx": 130,
        "name_uz": "Advokat",
        "name_ru": "Адвокат",
        "name_en": "Lawyer",
        "static_emoji": "👨‍💼",
        "custom_emoji_id": "",
    },
    {
        "role": "journalist",
        "team": "mafia",
        "order_idx": 140,
        "name_uz": "Jurnalist",
        "name_ru": "Журналист",
        "name_en": "Journalist",
        "static_emoji": "👩🏼‍💻",
        "custom_emoji_id": "5190736541521025564",
    },
    {
        "role": "killer",
        "team": "mafia",
        "order_idx": 150,
        "name_uz": "Ninza",
        "name_ru": "Ниндзя",
        "name_en": "Ninja",
        "static_emoji": "🥷",
        "custom_emoji_id": "",
    },
    # Singletons (7) — solo win conditions, no team
    {
        "role": "suicide",
        "team": "singletons",
        "order_idx": 210,
        "name_uz": "Suidsid",
        "name_ru": "Суицид",
        "name_en": "Suicide",
        "static_emoji": "🤦🏼",
        "custom_emoji_id": "5282785636363807099",
    },
    {
        "role": "maniac",
        "team": "singletons",
        "order_idx": 220,
        "name_uz": "Qotil",
        "name_ru": "Маньяк",
        "name_en": "Maniac",
        "static_emoji": "🔪",
        "custom_emoji_id": "",
    },
    {
        "role": "werewolf",
        "team": "singletons",
        "order_idx": 230,
        "name_uz": "Bo'ri",
        "name_ru": "Оборотень",
        "name_en": "Werewolf",
        "static_emoji": "🐺",
        "custom_emoji_id": "5276289730256842699",
    },
    {
        "role": "mage",
        "team": "singletons",
        "order_idx": 240,
        "name_uz": "Sehrgar",
        "name_ru": "Колдун",
        "name_en": "Mage",
        "static_emoji": "🧙",
        "custom_emoji_id": "",
    },
    {
        "role": "arsonist",
        "team": "singletons",
        "order_idx": 250,
        "name_uz": "G'azabkor",
        "name_ru": "Берсерк",
        "name_en": "Berserker",
        "static_emoji": "🧟",
        "custom_emoji_id": "5190733157086796387",
    },
    {
        "role": "crook",
        "team": "singletons",
        "order_idx": 260,
        "name_uz": "Aferist",
        "name_ru": "Аферист",
        "name_en": "Trickster",
        "static_emoji": "🤹",
        "custom_emoji_id": "",
    },
    {
        "role": "snitch",
        "team": "singletons",
        "order_idx": 270,
        "name_uz": "Sotqin",
        "name_ru": "Предатель",
        "name_en": "Snitch",
        "static_emoji": "🤓",
        "custom_emoji_id": "5370856771151730818",
    },
]


class RoleConfig(Model):
    """One row per game role. Read constantly during games — always go
    through the cached `role_config_service`, never hit this model directly."""

    role = fields.CharField(pk=True, max_length=32)
    team = fields.CharField(max_length=16)  # civilians | mafia | singletons
    name_uz = fields.CharField(max_length=64)
    name_ru = fields.CharField(max_length=64)
    name_en = fields.CharField(max_length=64)
    static_emoji = fields.CharField(max_length=32)
    custom_emoji_id = fields.CharField(max_length=32, default="")
    order_idx = fields.IntField(default=0)
    updated_at = fields.DatetimeField(auto_now=True)
    updated_by_tg_id = fields.BigIntField(null=True)

    class Meta:
        table = "role_configs"
        ordering = ["order_idx"]

    DEFAULTS: ClassVar[list[dict]] = DEFAULT_ROLE_CONFIGS
