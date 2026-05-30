"""Tests for sandbox ID helpers — collision guarantees + range invariants."""

import pytest
from app.core.sandbox_ids import (
    GROUP_RANGE_END,
    GROUP_RANGE_START,
    SANDBOX_BOUNDARY,
    USER_RANGE_END,
    USER_RANGE_START,
    alloc_group_id,
    alloc_user_id,
    is_sandbox_group_id,
    is_sandbox_id,
    is_sandbox_user_id,
)

# Representative real-Telegram IDs — must NEVER look like sandbox.
REAL_TELEGRAM_USER_IDS = [
    1,
    42,
    123456789,
    7_300_000_000,  # near current top of Telegram user_id range
    9_999_999_999,
]
REAL_TELEGRAM_GROUP_IDS = [
    -1,
    -1_001_234_567_890,  # typical supergroup
    -1_002_999_999_999,
    -100_000_000_000_000,  # well beyond current Telegram range
]


@pytest.mark.parametrize("uid", REAL_TELEGRAM_USER_IDS)
def test_real_user_ids_are_not_sandbox(uid):
    assert not is_sandbox_id(uid)
    assert not is_sandbox_user_id(uid)
    assert not is_sandbox_group_id(uid)


@pytest.mark.parametrize("gid", REAL_TELEGRAM_GROUP_IDS)
def test_real_group_ids_are_not_sandbox(gid):
    assert not is_sandbox_id(gid)
    assert not is_sandbox_user_id(gid)
    assert not is_sandbox_group_id(gid)


def test_sandbox_user_range_membership():
    uid = alloc_user_id(session_seq=0, player_idx=0)
    assert is_sandbox_id(uid)
    assert is_sandbox_user_id(uid)
    assert not is_sandbox_group_id(uid)
    assert USER_RANGE_START <= uid <= USER_RANGE_END


def test_sandbox_group_range_membership():
    gid = alloc_group_id(session_seq=0)
    assert is_sandbox_id(gid)
    assert is_sandbox_group_id(gid)
    assert not is_sandbox_user_id(gid)
    assert GROUP_RANGE_START <= gid <= GROUP_RANGE_END


def test_user_and_group_ranges_are_disjoint():
    # Highest user id must be strictly less than lowest group id.
    assert USER_RANGE_END < GROUP_RANGE_START


def test_alloc_user_id_unique_per_slot():
    seen = set()
    for session_seq in range(5):
        for player_idx in range(30):  # max sandbox game size
            uid = alloc_user_id(session_seq, player_idx)
            assert uid not in seen
            assert is_sandbox_user_id(uid)
            seen.add(uid)


def test_alloc_group_id_unique_per_session():
    ids = {alloc_group_id(s) for s in range(100)}
    assert len(ids) == 100
    assert all(is_sandbox_group_id(g) for g in ids)


def test_alloc_user_id_rejects_invalid_player_idx():
    with pytest.raises(ValueError):
        alloc_user_id(session_seq=0, player_idx=-1)
    with pytest.raises(ValueError):
        alloc_user_id(session_seq=0, player_idx=64)


def test_alloc_user_id_rejects_negative_session():
    with pytest.raises(ValueError):
        alloc_user_id(session_seq=-1, player_idx=0)


def test_alloc_group_id_rejects_negative_session():
    with pytest.raises(ValueError):
        alloc_group_id(session_seq=-1)


def test_sandbox_boundary_is_exclusive_lower_bound():
    # Anything at or above SANDBOX_BOUNDARY is NOT sandbox.
    assert not is_sandbox_id(SANDBOX_BOUNDARY)
    assert is_sandbox_id(SANDBOX_BOUNDARY - 1)


def test_zero_is_not_sandbox():
    # Edge — defensive, since DB CHECK constraint will use `users.id > 0`.
    assert not is_sandbox_id(0)
    assert not is_sandbox_user_id(0)
    assert not is_sandbox_group_id(0)


# === JavaScript-safe integer invariant ===
#
# Sandbox IDs are serialised to JSON and consumed by the React dashboard,
# which deserialises numbers as IEEE 754 doubles. Outside ±(2**53 - 1)
# integer precision is lost — multiple fake players would collapse to
# the same JS Number and the dashboard couldn't tell them apart. We
# guard the ranges here so a future "let's bump these for more headroom"
# refactor fails loudly instead of silently aliasing players.

JS_MAX_SAFE_INTEGER = 2**53 - 1


def test_ranges_fit_inside_js_safe_integer():
    assert -JS_MAX_SAFE_INTEGER <= USER_RANGE_START
    assert USER_RANGE_END <= JS_MAX_SAFE_INTEGER
    assert -JS_MAX_SAFE_INTEGER <= GROUP_RANGE_START
    assert GROUP_RANGE_END <= JS_MAX_SAFE_INTEGER


def test_consecutive_player_ids_are_distinct_in_js_doubles():
    """Adjacent fake user IDs must NOT round to the same JavaScript Number.

    Regression: the original ±2**62 ranges collapsed every fake player in
    session 0 to the same Number because IEEE 754 doubles have a 1024-wide
    gap at that magnitude.
    """
    seen_as_double: set[float] = set()
    for player_idx in range(30):  # max sandbox roster
        uid = alloc_user_id(session_seq=0, player_idx=player_idx)
        # Round-trip through Python's float (same precision as JS Number).
        as_double = float(uid)
        # 1. The cast itself must be exact.
        assert (
            int(as_double) == uid
        ), f"player {player_idx} id {uid} not exactly representable as float"
        # 2. No two players may collide on the same double.
        assert as_double not in seen_as_double, f"player {player_idx} aliases {uid} as double"
        seen_as_double.add(as_double)


def test_legacy_sandbox_ids_still_classified():
    """Pre-migration IDs in the ±2**60..62 ranges must still pass the
    `is_sandbox_*` guards so post-mortem rows in the DB don't become
    invisible to the middleware path."""
    legacy_user = -(2**62)  # legacy USER_RANGE_START
    legacy_group = -(2**61)  # legacy GROUP_RANGE_START
    assert is_sandbox_id(legacy_user)
    assert is_sandbox_user_id(legacy_user)
    assert not is_sandbox_group_id(legacy_user)
    assert is_sandbox_id(legacy_group)
    assert is_sandbox_group_id(legacy_group)
    assert not is_sandbox_user_id(legacy_group)


def test_is_sandbox_state_via_group_id():
    """GameState carries the sandbox marker via group_id range — no flag."""
    from app.core.sandbox_ids import is_sandbox_state

    class _S:
        def __init__(self, group_id):
            self.group_id = group_id

    fake_gid = alloc_group_id(0)
    real_gid = -1_001_234_567_890
    assert is_sandbox_state(_S(group_id=fake_gid)) is True
    assert is_sandbox_state(_S(group_id=real_gid)) is False
    # Anything missing/non-int → False (defensive)
    assert is_sandbox_state(_S(group_id=None)) is False
    assert is_sandbox_state(object()) is False
