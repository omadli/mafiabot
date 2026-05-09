"""👨‍💼 Lawyer (Advokat) — Komissardan + osishdan himoya."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class LawyerRole(BaseRole):
    code = "lawyer"
    team = Team.MAFIA
    has_night_action = True
    night_action_priority = 35  # before check (50)
    night_message_key = "night-action-msg-lawyer"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-lawyer"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        # Tunda mafia a'zosini himoya qiladi
        return target.alive and target.team == Team.MAFIA
