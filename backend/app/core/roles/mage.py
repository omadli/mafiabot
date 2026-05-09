"""🧙 Mage (Sehrgar) — hujum kelganda kechirish/o'ldirish reaksiyasi.

- Hujum kelganda bot xabar yuboradi: "Sizga {qotil_roli} hujum qildi. Kechirasizmi yoki o'ldirasizmi?"
- 2 inline tugma orqali tanlanadi
- O'yin oxirigacha tirik qolsa g'olib
"""

from app.core.roles.base import BaseRole
from app.core.state import Team


class MageRole(BaseRole):
    code = "mage"
    team = Team.SINGLETON
    has_night_action = False  # reactive only
    night_message_key = None

    def night_prompt_key(self) -> str | None:
        return None
