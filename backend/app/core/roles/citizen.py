"""👨🏼 Citizen — passive, no night action."""

from app.core.roles.base import BaseRole
from app.core.state import Team


class CitizenRole(BaseRole):
    code = "citizen"
    team = Team.CITIZENS
    has_night_action = False
    night_message_key = None  # silent

    def night_prompt_key(self) -> str | None:
        return None
