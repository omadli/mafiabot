"""Achievement, AuditLog, AdminAccount, OneTimeToken models."""

from tortoise import fields
from tortoise.models import Model


class Achievement(Model):
    """Static achievement catalog."""

    code = fields.CharField(max_length=64, pk=True)
    name_i18n: dict = fields.JSONField(default=dict)  # {"uz": "...", "ru": "...", "en": "..."}
    description_i18n: dict = fields.JSONField(default=dict)
    icon = fields.CharField(max_length=8, default="🏆")
    diamonds_reward = fields.IntField(default=0)
    xp_reward = fields.IntField(default=0)

    class Meta:
        table = "achievements"


class UserAchievement(Model):
    """Which user unlocked which achievement."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="achievements", on_delete=fields.CASCADE
    )
    achievement = fields.ForeignKeyField(
        "models.Achievement", related_name="users", on_delete=fields.CASCADE
    )
    unlocked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_achievements"
        unique_together = (("user", "achievement"),)


class AuditLog(Model):
    """Super admin actions audit trail."""

    id = fields.UUIDField(pk=True)
    actor = fields.ForeignKeyField(
        "models.User",
        related_name="audit_actions",
        null=True,
        on_delete=fields.SET_NULL,
    )
    actor_admin = fields.ForeignKeyField(
        "models.AdminAccount",
        related_name="audit_actions",
        null=True,
        on_delete=fields.SET_NULL,
    )
    action = fields.CharField(max_length=64)  # 'user.ban', 'group.block', 'diamonds.grant'
    target_type = fields.CharField(max_length=32, null=True)
    target_id = fields.CharField(max_length=64, null=True)
    payload: dict = fields.JSONField(default=dict)
    ip_address = fields.CharField(max_length=64, null=True)
    user_agent = fields.CharField(max_length=256, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
        indexes = [("action", "created_at"), ("actor_id", "created_at")]


class AdminAccount(Model):
    """Super admin accounts (login + password OR Telegram-linked)."""

    id = fields.UUIDField(pk=True)
    username = fields.CharField(max_length=64, unique=True)
    password_hash = fields.CharField(max_length=256)
    telegram_id = fields.BigIntField(null=True, unique=True)
    role = fields.CharField(max_length=32, default="superadmin")  # superadmin | support | analyst
    is_active = fields.BooleanField(default=True)
    last_login_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "admin_accounts"


class OneTimeToken(Model):
    """1-time login token (Telegram bot → admin panel)."""

    token = fields.CharField(max_length=64, pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="login_tokens", on_delete=fields.CASCADE
    )
    expires_at = fields.DatetimeField()
    used = fields.BooleanField(default=False)
    used_ip = fields.CharField(max_length=64, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "one_time_tokens"
