"""Game model — finished games stored here. Live state in Redis."""

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class GameStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class WinnerTeam(StrEnum):
    CITIZENS = "citizens"
    MAFIA = "mafia"
    SINGLETON = "singleton"  # specific singleton role won (see history)


class Game(Model):
    """A single Mafia game session.

    Live state is in Redis (`mafia:game:{group_id}` JSON).
    DB record is created when game is finished, with full history JSON.
    """

    id = fields.UUIDField(pk=True)
    group = fields.ForeignKeyField("models.Group", related_name="games", on_delete=fields.CASCADE)

    status = fields.CharEnumField(GameStatus, default=GameStatus.WAITING)
    started_at = fields.DatetimeField(auto_now_add=True)
    finished_at = fields.DatetimeField(null=True)

    winner_team = fields.CharEnumField(WinnerTeam, null=True)

    # Bounty (`/game 50` rejimi)
    bounty_per_winner = fields.IntField(null=True)
    bounty_pool = fields.IntField(null=True)
    bounty_initiator = fields.ForeignKeyField(
        "models.User",
        related_name="bounty_games",
        null=True,
        on_delete=fields.SET_NULL,
    )

    # Snapshot of group settings at game start
    settings_snapshot: dict = fields.JSONField(default=dict)

    # Full game history (players, rounds, actions, votes, deaths)
    history: dict = fields.JSONField(default=dict)
    # {
    #   "players": [...],
    #   "rounds": [...],
    #   "final_alive": [...]
    # }

    class Meta:
        table = "games"
        indexes = [("group_id", "started_at")]

    def __str__(self) -> str:
        return f"Game({self.id}, group={self.group_id}, status={self.status})"
