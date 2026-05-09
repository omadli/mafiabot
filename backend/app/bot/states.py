"""FSM states for bot conversations."""

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    waiting_language = State()
    waiting_admin_perms = State()


class RegistrationStates(StatesGroup):
    """Foydalanuvchi o'yinga ro'yxatdan o'tayotganida."""

    joined = State()


class RoleActionStates(StatesGroup):
    """Tundagi rol harakatlari uchun."""

    waiting_target = State()
    confirming = State()


class LastWordsState(StatesGroup):
    """O'lgan o'yinchi so'nggi so'z yozayotganida."""

    waiting_message = State()
