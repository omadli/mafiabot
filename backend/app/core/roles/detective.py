"""🕵🏻‍♂ Detective (Komissar Kattani) — check or shoot."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class DetectiveRole(BaseRole):
    code = "detective"
    team = Team.CITIZENS
    has_night_action = True
    night_action_priority = 50  # check after kills
    night_message_key = "night-action-msg-detective-check"  # default; -shoot for kill

    def night_prompt_key(self) -> str | None:
        return "night-prompt-detective"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        # Detective sees the Sergeant as a teammate and never targets them.
        if target.role == "sergeant":
            return False
        return target.alive and target.user_id != actor.user_id
