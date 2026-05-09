"""🔪 Maniac (Qotil) — yakka qotil, faqat o'zi tirik qolsa g'olib."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class ManiacRole(BaseRole):
    code = "maniac"
    team = Team.SINGLETON
    has_night_action = True
    night_action_priority = 30  # kills priority
    night_message_key = "night-action-msg-maniac"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-maniac"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id
