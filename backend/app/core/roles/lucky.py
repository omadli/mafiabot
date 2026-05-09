"""🤞🏼 Lucky (Omadli) — 50% ehtimol bilan tunda o'ldirishdan tirik qoladi."""

from app.core.roles.base import BaseRole
from app.core.state import Team


class LuckyRole(BaseRole):
    code = "lucky"
    team = Team.CITIZENS
    has_night_action = False  # passive
    night_message_key = None

    def night_prompt_key(self) -> str | None:
        return None
