"""Fake-ID allocation + range guards for the super-admin sandbox.

Sandbox-only entities (fake users, fake groups) must never collide with
real Telegram IDs and must be cheap to detect at runtime so service-layer
guards can skip DB writes for them.

Ranges (signed 64-bit BigInt, deliberately far from any real Telegram band):

    user_id    range:   -2**62           .. -2**61 - 1     (≈ -4.6 * 10**18)
    group_id   range:   -2**61           .. -2**60 - 1     (≈ -2.3 * 10**18)
    sandbox-id boundary: anything < -2**60 is "a sandbox id of some kind"

Real Telegram facts (as of 2026):
  - user IDs are positive, bounded by ~10**10
  - supergroup chat IDs are negative, bounded by ~-10**13
The 10**18 gap to our band makes collisions structurally impossible.

The constants are deliberately *named* (no magic numbers in callers) and
the helpers below are the only API: do not pattern-match on raw numbers
elsewhere — go through `is_sandbox_user_id` / `is_sandbox_group_id`.
"""

from __future__ import annotations

# Range boundaries — exposed so tests + check-constraint generators agree
SANDBOX_BOUNDARY = -(2**60)  # anything strictly below is sandbox-owned
USER_RANGE_START = -(2**62)
USER_RANGE_END = -(2**61) - 1  # inclusive
GROUP_RANGE_START = -(2**61)
GROUP_RANGE_END = -(2**60) - 1  # inclusive

# Max sequence numbers per range (defensive — far beyond any practical use)
MAX_USERS_PER_RANGE = USER_RANGE_END - USER_RANGE_START + 1
MAX_GROUPS_PER_RANGE = GROUP_RANGE_END - GROUP_RANGE_START + 1


def is_sandbox_id(x: int) -> bool:
    """True for any sandbox-owned ID (user OR group)."""
    return x < SANDBOX_BOUNDARY


def is_sandbox_user_id(x: int) -> bool:
    """True only for fake user IDs allocated by `alloc_user_id`."""
    return USER_RANGE_START <= x <= USER_RANGE_END


def is_sandbox_group_id(x: int) -> bool:
    """True only for fake group/chat IDs allocated by `alloc_group_id`."""
    return GROUP_RANGE_START <= x <= GROUP_RANGE_END


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
