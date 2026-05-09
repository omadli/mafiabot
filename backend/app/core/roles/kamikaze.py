"""💣 Kamikaze (Afsungar) — Civilians ko'rinishi, lekin yakka g'olib sharti.

- Tunda o'ldirilsa: o'ldirganni o'zi bilan jahannamga olib ketadi.
- Kunduz osilsa: 1 kishini tanlaydi olib ketishga.
- G'olib: faqat mafia/maniak/ninza olib ketsa.
"""

from app.core.roles.base import BaseRole
from app.core.state import Team


class KamikazeRole(BaseRole):
    code = "kamikaze"
    team = Team.CITIZENS  # paydo bo'lish — Komissar "Tinch aholi" ko'radi
    has_night_action = False  # passive — reaction-only at death
    night_message_key = "night-action-msg-kamikaze"  # subtle hint

    def night_prompt_key(self) -> str | None:
        return None
