"""Base role abstract class."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.state import GameState, PlayerState, Team


class BaseRole(ABC):
    """Base class for all roles."""

    code: str  # e.g. "detective"
    team: Team
    has_night_action: bool = False  # whether role acts at night
    night_action_priority: int = 100  # lower = earlier (kezuvchi=10, kills=30, heal=40, check=50)
    night_message_key: str | None = None  # i18n key for atmospheric message

    @property
    def name_key(self) -> str:
        """i18n key for role name (e.g. 'role-detective')."""
        return f"role-{self.code}"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        """Default: can target any other alive player."""
        return target.alive and target.user_id != actor.user_id

    def valid_targets(self, state: GameState, actor: PlayerState) -> list[PlayerState]:
        return [p for p in state.alive_players() if self.can_target(state, actor, p)]

    @abstractmethod
    def night_prompt_key(self) -> str | None:
        """i18n key for the prompt sent to actor in private chat at night."""
        ...
