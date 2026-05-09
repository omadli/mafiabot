"""🎖 Mayor (Janob) — kunduzgi ovozi 2x og'irlikda."""

from app.core.roles.base import BaseRole
from app.core.state import Team


class MayorRole(BaseRole):
    code = "mayor"
    team = Team.CITIZENS
    has_night_action = False
    night_message_key = None
    vote_weight = 2  # 2x kunduzgi ovoz

    def night_prompt_key(self) -> str | None:
        return None
