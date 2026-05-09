"""User and UserInventory models."""

from tortoise import fields
from tortoise.models import Model


class User(Model):
    """Telegram user.

    Primary key = Telegram user_id (BigInt).
    """

    id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=64, null=True)
    first_name = fields.CharField(max_length=128)
    last_name = fields.CharField(max_length=128, null=True)
    language_code = fields.CharField(max_length=8, default="uz")

    # Currencies
    diamonds = fields.IntField(default=0)
    dollars = fields.IntField(default=100)
    xp = fields.IntField(default=0)
    level = fields.IntField(default=1)

    # Premium
    is_premium = fields.BooleanField(default=False)
    premium_expires_at = fields.DatetimeField(null=True)

    # Ban
    is_banned = fields.BooleanField(default=False)
    banned_until = fields.DatetimeField(null=True)
    ban_reason = fields.CharField(max_length=256, null=True)

    # AFK tracking
    afk_warnings = fields.IntField(default=0)

    # 1 user = 1 game (active)
    # FK emas — User ↔ Game cycle (Game.bounty_initiator → User)
    # ni sindirish uchun. Manual lookup: Game.get_or_none(id=user.active_game_id)
    active_game_id = fields.UUIDField(null=True)

    # Stats joining time (for cohort analysis)
    joined_at = fields.DatetimeField(auto_now_add=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Reverse relation: inventory (OneToOne)
    inventory: fields.ReverseRelation["UserInventory"]

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"User({self.id}, @{self.username})"

    @property
    def display_name(self) -> str:
        return self.first_name or self.username or str(self.id)


class UserInventory(Model):
    """Foydalanuvchining qurol va himoyalari."""

    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User",
        related_name="inventory",
        pk=True,
        on_delete=fields.CASCADE,
    )

    # Quantities (sotib olingan miqdorlar)
    shield = fields.IntField(default=0)  # 🛡 Himoya
    killer_shield = fields.IntField(default=0)  # ⛑ Qotildan himoya
    vote_shield = fields.IntField(default=0)  # ⚖️ Ovoz himoyasi
    rifle = fields.IntField(default=0)  # 🔫 Miltiq
    mask = fields.IntField(default=0)  # 🎭 Maska
    fake_document = fields.IntField(default=0)  # 📁 Soxta hujjat
    special_role = fields.IntField(default=0)  # 🃏 Maxsus rol

    # User settings — per-item enabled/disabled
    settings: dict = fields.JSONField(default=dict)
    # {
    #   "shield": {"enabled": true},
    #   "killer_shield": {"enabled": true},
    #   "vote_shield": {"enabled": true},
    #   "rifle": {"enabled": false},
    #   "mask": {"enabled": true},
    #   "fake_document": {"enabled": true},
    #   "special_role": {"enabled": false, "chosen_role": null}
    # }

    class Meta:
        table = "user_inventories"
