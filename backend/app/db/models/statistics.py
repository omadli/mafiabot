"""Statistics models — Data Warehouse approach."""

from tortoise import fields
from tortoise.models import Model


class GameResult(Model):
    """★ Data warehouse: 1 row per (game, user). Source of truth for all analytics."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="game_results", on_delete=fields.CASCADE
    )
    game = fields.ForeignKeyField("models.Game", related_name="results", on_delete=fields.CASCADE)
    group = fields.ForeignKeyField(
        "models.Group", related_name="game_results", null=True, on_delete=fields.SET_NULL
    )

    role = fields.CharField(max_length=32)  # 'detective', 'don', etc
    team = fields.CharField(max_length=16)  # 'citizens', 'mafia', 'singleton'
    won = fields.BooleanField()
    survived = fields.BooleanField()

    death_round = fields.IntField(null=True)
    death_phase = fields.CharField(max_length=16, null=True)
    death_reason = fields.CharField(max_length=64, null=True)

    actions_count = fields.IntField(default=0)
    successful_actions = fields.IntField(default=0)
    received_votes = fields.IntField(default=0)
    cast_votes = fields.IntField(default=0)
    afk_turns = fields.IntField(default=0)

    # ELO/XP/$ deltas
    elo_before = fields.IntField()
    elo_after = fields.IntField()
    elo_change = fields.IntField()
    xp_earned = fields.IntField(default=0)
    dollars_earned = fields.IntField(default=0)

    game_duration_seconds = fields.IntField()
    game_player_count = fields.IntField()
    played_at = fields.DatetimeField()

    class Meta:
        table = "game_results"
        indexes = [
            ("user_id", "played_at"),
            ("user_id", "role"),
            ("group_id", "played_at"),
            ("user_id", "group_id", "played_at"),
        ]


class UserStats(Model):
    """Denormalized global aggregate per user — fast lookup for /stats."""

    user = fields.OneToOneField(
        "models.User", related_name="stats", pk=True, on_delete=fields.CASCADE
    )

    games_total = fields.IntField(default=0)
    games_won = fields.IntField(default=0)
    games_lost = fields.IntField(default=0)

    # By team
    citizen_games = fields.IntField(default=0)
    citizen_wins = fields.IntField(default=0)
    mafia_games = fields.IntField(default=0)
    mafia_wins = fields.IntField(default=0)
    singleton_games = fields.IntField(default=0)
    singleton_wins = fields.IntField(default=0)

    # Per-role JSON
    role_stats: dict = fields.JSONField(default=dict)

    # Rating
    elo = fields.IntField(default=1000)
    xp = fields.IntField(default=0)
    level = fields.IntField(default=1)

    # Survival
    times_survived = fields.IntField(default=0)
    times_killed_at_night = fields.IntField(default=0)
    times_voted_out = fields.IntField(default=0)

    # Streaks
    current_win_streak = fields.IntField(default=0)
    longest_win_streak = fields.IntField(default=0)
    current_loss_streak = fields.IntField(default=0)

    # Behavior
    afk_count = fields.IntField(default=0)
    leave_count = fields.IntField(default=0)
    average_game_duration = fields.FloatField(default=0)

    last_played_at = fields.DatetimeField(null=True)
    last_reset_at = fields.DatetimeField(null=True)

    class Meta:
        table = "user_stats"

    @property
    def winrate(self) -> float:
        return self.games_won / self.games_total if self.games_total else 0.0


class GroupUserStats(Model):
    """User stats within a specific group — for per-group leaderboard."""

    user = fields.ForeignKeyField(
        "models.User", related_name="group_stats", on_delete=fields.CASCADE
    )
    group = fields.ForeignKeyField(
        "models.Group", related_name="player_stats", on_delete=fields.CASCADE
    )

    games_total = fields.IntField(default=0)
    games_won = fields.IntField(default=0)
    role_stats: dict = fields.JSONField(default=dict)

    elo = fields.IntField(default=1000)  # per-group ELO
    xp = fields.IntField(default=0)

    rank = fields.IntField(null=True)
    last_played_at = fields.DatetimeField(null=True)

    class Meta:
        table = "group_user_stats"
        unique_together = (("user", "group"),)
        indexes = [("group_id", "elo"), ("group_id", "xp"), ("group_id", "games_won")]


class StatsPeriodSnapshot(Model):
    """Daily/weekly/monthly snapshot — populated by cron from GameResult."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="period_stats", on_delete=fields.CASCADE
    )
    group = fields.ForeignKeyField(
        "models.Group", related_name="period_stats", null=True, on_delete=fields.SET_NULL
    )
    period = fields.CharField(max_length=8)  # 'daily', 'weekly', 'monthly'
    period_start = fields.DateField()
    period_end = fields.DateField()

    games_total = fields.IntField()
    games_won = fields.IntField()
    role_stats: dict = fields.JSONField(default=dict)
    elo_change = fields.IntField(default=0)
    xp_earned = fields.IntField(default=0)

    class Meta:
        table = "stats_period_snapshots"
        unique_together = (("user", "group", "period", "period_start"),)
        indexes = [("group_id", "period", "period_start")]


class GroupStats(Model):
    """Group-level aggregate (balance, retention, activity)."""

    group = fields.OneToOneField(
        "models.Group", related_name="aggregate", pk=True, on_delete=fields.CASCADE
    )

    total_games = fields.IntField(default=0)
    total_unique_players = fields.IntField(default=0)
    active_players_30d = fields.IntField(default=0)

    avg_game_duration_seconds = fields.FloatField(default=0)
    avg_player_count = fields.FloatField(default=0)

    citizens_winrate = fields.FloatField(default=0)
    mafia_winrate = fields.FloatField(default=0)
    singleton_winrate = fields.FloatField(default=0)

    most_played_role = fields.CharField(max_length=32, null=True)
    last_game_at = fields.DatetimeField(null=True)

    class Meta:
        table = "group_stats"
