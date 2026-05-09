"""👨🏻‍⚕ Doctor — heals one player per night, self-heal once."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class DoctorRole(BaseRole):
    code = "doctor"
    team = Team.CITIZENS
    has_night_action = True
    night_action_priority = 40  # heal cancels kills
    night_message_key = "night-action-msg-doctor"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-doctor"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        # Doctor can target self ONLY ONCE per game
        if not target.alive:
            return False
        if target.user_id == actor.user_id:
            return not actor.extra.get("self_heal_used", False)
        return True
