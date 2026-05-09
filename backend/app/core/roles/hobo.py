"""🧙‍♂ Hobo (Daydi) — tunda butilka uchun boradi, qotil rolini ko'radi."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class HoboRole(BaseRole):
    code = "hobo"
    team = Team.CITIZENS
    has_night_action = True
    night_action_priority = 20  # visit before kills
    night_message_key = "night-action-msg-hobo"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-hobo"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id
