"""Game state schema — Redis JSON.

Live game state stored at `mafia:game:{group_id}` (JSON).
On game finish: serialized into Game.history JSONField in DB.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Phase(StrEnum):
    WAITING = "waiting"  # registration
    NIGHT = "night"
    DAY = "day"  # discussion
    VOTING = "voting"  # day voting
    HANGING_CONFIRM = "hanging_confirm"
    LAST_WORDS = "last_words"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Team(StrEnum):
    CITIZENS = "citizens"
    MAFIA = "mafia"
    SINGLETON = "singleton"


class DeathReason(StrEnum):
    KILLED_MAFIA = "killed_mafia"
    KILLED_DETECTIVE = "killed_detective"
    KILLED_KILLER = "killed_killer"
    KILLED_MANIAC = "killed_maniac"
    KILLED_BORI = "killed_bori"
    KILLED_AFSUNGAR = "killed_afsungar"
    KILLED_GAZABKOR = "killed_gazabkor"
    VOTED_OUT = "voted_out"
    LEFT = "left"
    AFK_KICKED = "afk_kicked"


class PlayerState(BaseModel):
    """O'yinchi holati o'yin paytida (Redis state'da saqlanadi)."""

    user_id: int
    username: str | None = None
    first_name: str
    join_order: int

    role: str  # role code: 'citizen', 'detective', etc
    team: Team
    alive: bool = True

    # Active items (per session — sotib olingan + ishlatilmagan)
    items_active: list[str] = Field(default_factory=list)

    # Death tracking
    died_at_round: int | None = None
    died_at_phase: Phase | None = None
    died_reason: DeathReason | None = None

    # Skip phases tracking (AFK)
    skipped_phases: int = 0

    # Role-specific state
    extra: dict[str, Any] = Field(default_factory=dict)
    # detective: {"checks": [user_id, ...]}
    # doctor: {"self_heal_used": bool}
    # hooker: {"last_target": user_id}


class NightAction(BaseModel):
    """Bir o'yinchining tundagi tanlovi."""

    actor_id: int
    role: str
    action_type: str  # 'kill', 'check', 'heal', 'sleep', 'visit'
    target_id: int | None = None
    used_item: str | None = None  # 'rifle', 'fake_document', etc


class Vote(BaseModel):
    """Kunduzgi ovoz."""

    voter_id: int
    target_id: int  # 0 = "Hech kim" (skip)
    weight: int = 1  # Mayor = 2


class RoundLog(BaseModel):
    """Bitta tun+kun aylanishining tarixi."""

    round_num: int
    night_actions: list[NightAction] = Field(default_factory=list)
    night_deaths: list[int] = Field(default_factory=list)
    night_messages: list[str] = Field(default_factory=list)
    day_votes: list[Vote] = Field(default_factory=list)
    hanged: int | None = None
    last_words: dict[int, str] = Field(default_factory=dict)


class GameState(BaseModel):
    """To'liq o'yin holati (Redis'da saqlanadi)."""

    id: UUID = Field(default_factory=uuid4)
    group_id: int
    chat_id: int  # Telegram chat ID (== group_id for groups)
    registration_message_id: int | None = None

    phase: Phase = Phase.WAITING
    round_num: int = 0  # 0 = before any night
    phase_ends_at: int | None = None  # unix timestamp

    players: list[PlayerState] = Field(default_factory=list)
    current_actions: dict[int, NightAction] = Field(default_factory=dict)
    current_votes: dict[int, Vote] = Field(default_factory=dict)

    # Snapshot of group settings at game creation
    settings: dict[str, Any] = Field(default_factory=dict)

    # Bounty (if /game N)
    bounty_per_winner: int | None = None
    bounty_pool: int | None = None
    bounty_initiator_id: int | None = None

    # Round logs (for history)
    rounds: list[RoundLog] = Field(default_factory=list)

    # Win info
    winner_team: Team | None = None
    winner_user_ids: list[int] = Field(default_factory=list)

    # Timer task (not serialized — runtime only)
    started_at: int | None = None  # unix timestamp
    finished_at: int | None = None

    def get_player(self, user_id: int) -> PlayerState | None:
        return next((p for p in self.players if p.user_id == user_id), None)

    def alive_players(self) -> list[PlayerState]:
        return [p for p in self.players if p.alive]

    def alive_by_team(self, team: Team) -> list[PlayerState]:
        return [p for p in self.players if p.alive and p.team == team]

    def alive_by_role(self, role: str) -> list[PlayerState]:
        return [p for p in self.players if p.alive and p.role == role]

    def current_round(self) -> RoundLog:
        if not self.rounds or self.rounds[-1].round_num != self.round_num:
            self.rounds.append(RoundLog(round_num=self.round_num))
        return self.rounds[-1]

    def to_redis(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_redis(cls, raw: str | bytes) -> GameState:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return cls.model_validate_json(raw)

    def to_history_dict(self) -> dict[str, Any]:
        """For Game.history JSONField on game finish."""
        return {
            "players": [
                {
                    "user_id": p.user_id,
                    "username": p.username,
                    "first_name": p.first_name,
                    "role": p.role,
                    "team": p.team,
                    "alive": p.alive,
                    "join_order": p.join_order,
                    "died_at_round": p.died_at_round,
                    "died_at_phase": p.died_at_phase,
                    "died_reason": p.died_reason,
                }
                for p in self.players
            ],
            "rounds": [json.loads(r.model_dump_json()) for r in self.rounds],
            "winner_team": self.winner_team,
            "winner_user_ids": self.winner_user_ids,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


# Redis key helpers
def game_state_key(group_id: int) -> str:
    return f"mafia:game:{group_id}"


def user_active_game_key(user_id: int) -> str:
    return f"mafia:user_active:{user_id}"
