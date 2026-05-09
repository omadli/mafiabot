"""Transaction, Giveaway, GiveawayClick models."""

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class TransactionType(StrEnum):
    BUY_DIAMONDS = "buy_diamonds"  # Telegram Stars → diamonds
    SPEND_DIAMONDS = "spend_diamonds"  # premium item purchase
    SPEND_DOLLARS = "spend_dollars"  # stats reset
    GIFT_SEND = "gift_send"  # /give reply
    GIFT_RECEIVE = "gift_receive"
    ADMIN_GRANT = "admin_grant"  # super admin grant (system)
    GAME_BOUNTY_ESCROW = "game_bounty_escrow"
    GAME_BOUNTY_PAYOUT = "game_bounty_payout"
    GAME_BOUNTY_REFUND = "game_bounty_refund"
    GIVEAWAY_PAYOUT = "giveaway_payout"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Transaction(Model):
    """All currency movements (Telegram Stars, diamonds, dollars)."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="transactions", on_delete=fields.CASCADE
    )
    type = fields.CharEnumField(TransactionType)

    stars_amount = fields.IntField(null=True)
    diamonds_amount = fields.IntField(null=True)
    dollars_amount = fields.IntField(null=True)

    item = fields.CharField(max_length=64, null=True)
    counterparty = fields.ForeignKeyField(
        "models.User",
        related_name="counterparty_transactions",
        null=True,
        on_delete=fields.SET_NULL,
    )
    related_game = fields.ForeignKeyField("models.Game", null=True, on_delete=fields.SET_NULL)
    related_giveaway = fields.ForeignKeyField(
        "models.Giveaway", null=True, on_delete=fields.SET_NULL
    )

    telegram_payment_charge_id = fields.CharField(max_length=128, null=True)
    status = fields.CharEnumField(TransactionStatus, default=TransactionStatus.PENDING)
    note = fields.CharField(max_length=256, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "transactions"
        indexes = [("user_id", "created_at"), ("type", "created_at")]


class GiveawayStatus(StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Giveaway(Model):
    """`/give 50` (group giveaway with inline button)."""

    id = fields.UUIDField(pk=True)
    sender = fields.ForeignKeyField(
        "models.User", related_name="giveaways_sent", on_delete=fields.CASCADE
    )
    group = fields.ForeignKeyField(
        "models.Group", related_name="giveaways", null=True, on_delete=fields.SET_NULL
    )
    chat_id = fields.BigIntField()
    message_id = fields.BigIntField()

    total_diamonds = fields.IntField()
    expires_at = fields.DatetimeField()
    max_clicks = fields.IntField(default=10)
    status = fields.CharEnumField(GiveawayStatus, default=GiveawayStatus.ACTIVE)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "giveaways"


class GiveawayClick(Model):
    """Each click on a giveaway button — harmonic distribution."""

    id = fields.UUIDField(pk=True)
    giveaway = fields.ForeignKeyField(
        "models.Giveaway", related_name="clicks", on_delete=fields.CASCADE
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="giveaway_clicks", on_delete=fields.CASCADE
    )
    click_order = fields.IntField()
    diamonds_received = fields.IntField()
    clicked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "giveaway_clicks"
        unique_together = (("giveaway", "user"),)  # 1 user 1 click per giveaway
