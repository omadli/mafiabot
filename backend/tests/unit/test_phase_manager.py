"""PhaseManager deadline-gating tests.

The auto-advance decision is isolated in the pure `_deadline_elapsed`
helper so the `/extend` contract can be proven deterministically without
Redis or asyncio timing:

  registration started → timer running → `/extend` (phase_ends_at=None)
  → the game must NOT auto-start; it waits for a manual `/start`.
"""

from app.core.phases.manager import PhaseManager
from app.core.state import GameState, Phase


def _waiting(deadline: int | None) -> GameState:
    return GameState(group_id=-1, chat_id=-1, phase=Phase.WAITING, phase_ends_at=deadline)


def test_extended_registration_never_auto_advances():
    """`/extend` clears phase_ends_at — indefinite registration must never
    elapse on its own, so the timer loop must not auto-start the game."""
    assert PhaseManager._deadline_elapsed(_waiting(None), now=1_000_000) is False


def test_future_deadline_not_elapsed():
    assert PhaseManager._deadline_elapsed(_waiting(1_000_100), now=1_000_000) is False


def test_past_deadline_elapsed():
    assert PhaseManager._deadline_elapsed(_waiting(1_000_000), now=1_000_050) is True


def test_exact_deadline_counts_as_elapsed():
    assert PhaseManager._deadline_elapsed(_waiting(1_000_000), now=1_000_000) is True
