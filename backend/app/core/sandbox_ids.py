"""Fake-ID allocation + range guards for the super-admin sandbox.

Sandbox-only entities (fake users, fake groups) must never collide with
real Telegram IDs AND must round-trip cleanly through JavaScript Number
(the dashboard reads them as JSON). JS Number has 53 bits of integer
precision, so anything outside ±2**53 collapses — multiple fake players
would alias to the same JS number and the dashboard would be unable to
tell them apart (the bug this layout was originally written to avoid).

Ranges (signed 64-bit BigInt, both inside JavaScript's safe-integer
window of ±9_007_199_254_740_991):

    user_id    range:   -9 * 10**15  .. -5 * 10**15 - 1   (≈ -9.0 * 10**15)
    group_id   range:   -5 * 10**15  .. -10**15 - 1       (≈ -5.0 * 10**15)
    sandbox-id boundary: anything < -10**15 is "a sandbox id of some kind"

Real Telegram facts (as of 2026):
  - user IDs are positive, bounded by ~10**10
  - supergroup chat IDs are negative, bounded by ~-10**14
The 10x gap to our boundary keeps collisions structurally impossible
while staying inside JS Number's safe range.

The constants are deliberately *named* (no magic numbers in callers) and
the helpers below are the only API: do not pattern-match on raw numbers
elsewhere — go through `is_sandbox_user_id` / `is_sandbox_group_id`.

`is_sandbox_*` accept both the current ranges and the legacy ±2**60-ish
ranges shipped before the JS-safe migration, so dead sandbox rows still
classify correctly while live operations always allocate in the new
range. The legacy detection only adds two integer comparisons; cost is
negligible on the middleware hot path.
"""

from __future__ import annotations

# Range boundaries — exposed so tests + check-constraint generators agree.
# All values sit within JavaScript's safe-integer window so IDs round-trip
# losslessly through JSON.
SANDBOX_BOUNDARY = -(10**15)  # anything strictly below is sandbox-owned
USER_RANGE_START = -(9 * 10**15)
USER_RANGE_END = -(5 * 10**15) - 1  # inclusive
GROUP_RANGE_START = -(5 * 10**15)
GROUP_RANGE_END = -(10**15) - 1  # inclusive

# Legacy ranges — sandbox rows created before the JS-safe ID migration.
# Kept here so post-mortem session lookups still classify correctly;
# never used for new allocations.
_LEGACY_SANDBOX_BOUNDARY = -(2**60)
_LEGACY_USER_RANGE_START = -(2**62)
_LEGACY_USER_RANGE_END = -(2**61) - 1
_LEGACY_GROUP_RANGE_START = -(2**61)
_LEGACY_GROUP_RANGE_END = -(2**60) - 1

# Max sequence numbers per range (defensive — far beyond any practical use)
MAX_USERS_PER_RANGE = USER_RANGE_END - USER_RANGE_START + 1
MAX_GROUPS_PER_RANGE = GROUP_RANGE_END - GROUP_RANGE_START + 1


def is_sandbox_id(x: int) -> bool:
    """True for any sandbox-owned ID (user OR group), current or legacy."""
    return x < SANDBOX_BOUNDARY or x < _LEGACY_SANDBOX_BOUNDARY


def is_sandbox_user_id(x: int) -> bool:
    """True for fake user IDs in the current OR legacy user range."""
    return (USER_RANGE_START <= x <= USER_RANGE_END) or (
        _LEGACY_USER_RANGE_START <= x <= _LEGACY_USER_RANGE_END
    )


def is_sandbox_group_id(x: int) -> bool:
    """True for fake group/chat IDs in the current OR legacy group range."""
    return (GROUP_RANGE_START <= x <= GROUP_RANGE_END) or (
        _LEGACY_GROUP_RANGE_START <= x <= _LEGACY_GROUP_RANGE_END
    )


def alloc_user_id(session_seq: int, player_idx: int) -> int:
    """Deterministic fake user_id from (session_seq, player_idx).

    `session_seq` is a monotonic per-session integer (typically the count
    of sandbox sessions created so far). `player_idx` is 0..n_players-1
    within the session. We pack them as `session_seq * 64 + player_idx`
    to leave 6 bits for the player slot — sandbox games cap at 30 players
    so 64 slots is comfortable headroom.
    """
    if session_seq < 0:
        raise ValueError(f"session_seq must be >= 0, got {session_seq}")
    if not 0 <= player_idx < 64:
        raise ValueError(f"player_idx must be in [0, 64), got {player_idx}")
    offset = session_seq * 64 + player_idx
    if offset > MAX_USERS_PER_RANGE:
        raise OverflowError(f"sandbox user id space exhausted (session_seq={session_seq})")
    return USER_RANGE_START + offset


def alloc_group_id(session_seq: int) -> int:
    """Deterministic fake group_id from session_seq (one per sandbox)."""
    if session_seq < 0:
        raise ValueError(f"session_seq must be >= 0, got {session_seq}")
    if session_seq > MAX_GROUPS_PER_RANGE:
        raise OverflowError(f"sandbox group id space exhausted (session_seq={session_seq})")
    return GROUP_RANGE_START + session_seq


def is_sandbox_state(state: object) -> bool:
    """True when a `GameState` was created inside a sandbox.

    The structural marker is the `group_id` range: every sandbox game
    is bound to a fake group_id allocated by `alloc_group_id`, which
    sits in `GROUP_RANGE_START..GROUP_RANGE_END`. No real game can ever
    enter that range, so this single check is reliable and stateless.
    """
    gid = getattr(state, "group_id", None)
    return isinstance(gid, int) and is_sandbox_group_id(gid)
