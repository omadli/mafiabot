"""💃 Hooker (Kezuvchi) — sleeps one player, can't target same twice in a row."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class HookerRole(BaseRole):
    code = "hooker"
    team = Team.CITIZENS
    has_night_action = True
    night_action_priority = 10  # sleep applies first (cancels other actions)
    night_message_key = "night-action-msg-hooker"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-hooker"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        if not target.alive or target.user_id == actor.user_id:
            return False
        # Cannot target same player two nights in a row
        last_target = actor.extra.get("last_target")
        return last_target != target.user_id
