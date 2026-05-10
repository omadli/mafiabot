"""Group and GroupSettings models."""

from tortoise import fields
from tortoise.models import Model


class Group(Model):
    """Telegram group/supergroup."""

    id = fields.BigIntField(pk=True)  # Telegram chat_id
    title = fields.CharField(max_length=256)

    is_active = fields.BooleanField(default=True)
    is_blocked = fields.BooleanField(default=False)

    # Onboarding
    onboarding_completed = fields.BooleanField(default=False)
    bot_admin_perms: dict = fields.JSONField(default=dict)
    # {"delete_messages": true, "restrict_members": true, "pin_messages": true}

    invite_link = fields.CharField(max_length=256, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    settings: fields.ReverseRelation["GroupSettings"]

    class Meta:
        table = "groups"

    def __str__(self) -> str:
        return f"Group({self.id}, {self.title})"


class GroupSettings(Model):
    """Guruh sozlamalari — har turi alohida JSONField."""

    group: fields.OneToOneRelation[Group] = fields.OneToOneField(
        "models.Group",
        related_name="settings",
        pk=True,
        on_delete=fields.CASCADE,
    )

    language = fields.CharField(max_length=8, default="uz")

    # Roles enabled/disabled (har bir rol uchun bool)
    roles: dict = fields.JSONField(default=dict)

    # Phase timings (sekundlarda)
    timings: dict = fields.JSONField(default=dict)
    # Default: {"registration": 120, "night": 60, "day": 45, "mafia_vote": 25,
    #           "hanging_vote": 25, "hanging_confirm": 15, "last_words": 20,
    #           "afsungar_carry": 15}

    # Silence rules
    silence: dict = fields.JSONField(default=dict)
    # {"dead_players": true, "sleeping_players": true, "non_players": false,
    #  "night_chat": true}

    # Items allowed in this group
    items_allowed: dict = fields.JSONField(default=dict)
    # {"shield": true, "killer_shield": true, ...}

    # Role distribution per player count (4..30)
    role_distribution: dict = fields.JSONField(default=dict)

    # AFK rules
    afk: dict = fields.JSONField(default=dict)
    # {"skip_phases_before_kick": 2, "xp_penalty_on_kick": 50,
    #  "elo_penalty_on_leave": 10, "consecutive_leaves_to_ban": 3,
    #  "ban_duration_hours": 24}

    # Permissions (kim qaysi buyruqni ishlata oladi)
    permissions: dict = fields.JSONField(default=dict)
    # {"who_can_register": "all", "who_can_start": "registrar", ...}

    # Gameplay variants
    gameplay: dict = fields.JSONField(default=dict)
    # {"mafia_ratio": "low", "max_players": 30, "min_players": 4,
    #  "allow_skip_day_vote": true, "allow_skip_night_action": true}

    # Display/UI
    display: dict = fields.JSONField(default=dict)
    # {"show_role_emojis": true, "group_roles_in_list": true,
    #  "anonymous_voting": false, "auto_pin_registration": true,
    #  "show_role_on_death": true}

    # Custom message templates (override i18n)
    messages: dict = fields.JSONField(default=dict)
    # {"leave_message": "...", "style": "formal"}

    # Atmosphere media — admin-uploaded GIF/video file_ids per phase
    atmosphere_media: dict = fields.JSONField(default=dict)
    # {"night_start": "<file_id>", "day_start": "<file_id>",
    #  "voting_start": "<file_id>", "game_end_civilian_win": "<file_id>",
    #  "game_end_mafia_win": "<file_id>"}
    # Each value is a Telegram file_id (sticker/animation/video) uploaded by group admin.

    class Meta:
        table = "group_settings"


# === Default settings ===

DEFAULT_TIMINGS = {
    "registration": 120,
    "night": 60,
    "day": 45,
    "mafia_vote": 25,
    "hanging_vote": 25,
    "hanging_confirm": 15,
    "last_words": 20,
    "afsungar_carry": 15,
}

DEFAULT_SILENCE = {
    "dead_players": True,
    "sleeping_players": True,
    "non_players": False,
    "night_chat": True,
}

DEFAULT_ITEMS_ALLOWED = {
    "shield": True,
    "killer_shield": True,
    "vote_shield": True,
    "rifle": True,
    "mask": True,
    "fake_document": True,
}

DEFAULT_AFK = {
    "skip_phases_before_kick": 2,
    "xp_penalty_on_kick": 50,
    "elo_penalty_on_leave": 10,
    "consecutive_leaves_to_ban": 3,
    "ban_duration_hours": 24,
}

DEFAULT_PERMISSIONS = {
    "who_can_register": "all",
    "who_can_start": "registrar",
    "who_can_extend": "all",
    "who_can_stop": "admins",
    "allow_leave": True,
}

DEFAULT_GAMEPLAY = {
    "mafia_ratio": "low",
    "min_players": 4,
    "max_players": 30,
    "allow_skip_day_vote": True,
    "allow_skip_night_action": True,
}

DEFAULT_DISPLAY = {
    "show_role_emojis": True,
    "group_roles_in_list": True,
    "anonymous_voting": False,
    "auto_pin_registration": True,
    "show_role_on_death": True,
}

DEFAULT_ATMOSPHERE_MEDIA: dict = {
    "night_start": None,
    "day_start": None,
    "voting_start": None,
    "game_end_civilian_win": None,
    "game_end_mafia_win": None,
    "game_end_singleton_win": None,
}

DEFAULT_ROLES_ENABLED = {
    # Civilians (10)
    "citizen": True,
    "detective": True,
    "sergeant": True,
    "mayor": True,
    "doctor": True,
    "hooker": True,
    "hobo": True,
    "lucky": True,
    "suicide": False,  # disabled by default (special)
    "kamikaze": False,
    # Mafia (5)
    "don": True,
    "mafia": True,
    "lawyer": True,
    "journalist": False,
    "killer": False,
    # Singletons (6)
    "maniac": False,
    "werewolf": False,
    "mage": False,
    "arsonist": False,
    "crook": False,
    "snitch": False,
}
