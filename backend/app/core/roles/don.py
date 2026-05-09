"""🤵🏻 Don — mafia leader, kills at night."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class DonRole(BaseRole):
    code = "don"
    team = Team.MAFIA
    has_night_action = True
    night_action_priority = 30  # kills before heal
    night_message_key = "night-action-msg-don"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-don"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        # Don cannot target other mafia
        return target.alive and target.user_id != actor.user_id and target.team != Team.MAFIA
