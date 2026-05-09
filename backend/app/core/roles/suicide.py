"""🤦🏼 Suicide (Suidsid) — kunduzi osilsa yutadi, tunda o'lsa yutqizadi."""

from app.core.roles.base import BaseRole
from app.core.state import Team


class SuicideRole(BaseRole):
    code = "suicide"
    team = Team.CITIZENS  # tomon ko'rinishi
    has_night_action = False
    night_message_key = None

    def night_prompt_key(self) -> str | None:
        return None
