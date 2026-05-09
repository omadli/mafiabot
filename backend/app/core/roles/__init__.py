"""Role registry — all 21 roles."""

from app.core.roles.arsonist import ArsonistRole
from app.core.roles.base import BaseRole
from app.core.roles.citizen import CitizenRole
from app.core.roles.crook import CrookRole
from app.core.roles.detective import DetectiveRole
from app.core.roles.doctor import DoctorRole
from app.core.roles.don import DonRole
from app.core.roles.hobo import HoboRole
from app.core.roles.hooker import HookerRole
from app.core.roles.journalist import JournalistRole
from app.core.roles.kamikaze import KamikazeRole
from app.core.roles.killer import KillerRole
from app.core.roles.lawyer import LawyerRole
from app.core.roles.lucky import LuckyRole
from app.core.roles.mafia import MafiaRole
from app.core.roles.mage import MageRole
from app.core.roles.maniac import ManiacRole
from app.core.roles.mayor import MayorRole
from app.core.roles.sergeant import SergeantRole
from app.core.roles.snitch import SnitchRole
from app.core.roles.suicide import SuicideRole
from app.core.roles.werewolf import WerewolfRole

ROLE_REGISTRY: dict[str, type[BaseRole]] = {
    # Civilians (10)
    "citizen": CitizenRole,
    "detective": DetectiveRole,
    "sergeant": SergeantRole,
    "mayor": MayorRole,
    "doctor": DoctorRole,
    "hooker": HookerRole,
    "hobo": HoboRole,
    "lucky": LuckyRole,
    "suicide": SuicideRole,
    "kamikaze": KamikazeRole,
    # Mafia (5)
    "don": DonRole,
    "mafia": MafiaRole,
    "lawyer": LawyerRole,
    "journalist": JournalistRole,
    "killer": KillerRole,
    # Singletons (6)
    "maniac": ManiacRole,
    "werewolf": WerewolfRole,
    "mage": MageRole,
    "arsonist": ArsonistRole,
    "crook": CrookRole,
    "snitch": SnitchRole,
}


def get_role(code: str) -> BaseRole:
    role_cls = ROLE_REGISTRY.get(code)
    if role_cls is None:
        raise ValueError(f"Unknown role: {code}")
    return role_cls()


__all__ = ["ROLE_REGISTRY", "BaseRole", "get_role"]
