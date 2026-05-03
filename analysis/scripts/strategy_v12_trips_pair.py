"""
v12 — for trips_pair hands (3 of one rank + 2 of another), keep the pair
together, split the trips 2+1, and pick the layout with the strongest
bot DS structure.

Top-15 v10 misses showed v10 picks rainbow non-paired-mid junk on these
hands ($48-$58K/1000h bleed each). Oracle keeps the pair intact and
splits trips 2+1 with DS bot every time.

Two dominant archetypes among top-15 oracle picks:
  A: mid = 2 of 3 trip members (paired mid).
     bot = pair + 1 trip-overflow + 1 kicker.
     top = the other kicker.
  B: mid = 1 trip + 1 kicker.
     bot = pair + 2 trips (4 cards = 2 pairs).
     top = the other kicker.

Both are no-pair-split, trips-split-2-1 layouts. v12 enumerates both
archetypes (× 3 trip-split choices × 2 top-kicker choices = 12 candidate
settings) and picks by:
    (1) bot suit profile (DS > SS > rainbow > 3+1 > 4-flush)
    (2) top rank (tie-break)
    (3) mid kind (pair > broadway-offsuit > suited-connector > other)
    (4) prefer archetype A over B (slight preference for trips-mid)

Falls back to v10 on non-trips_pair hands.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from strategy_v10_two_pair_no_split import strategy_v10_two_pair_no_split  # noqa: E402
from strategy_v10_two_pair_no_split import _bot_suit_profile  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _score_setting(
    hand_bytes: np.ndarray,
    ranks: np.ndarray,
    suits: np.ndarray,
    top_idx: int,
    mid_indices: list[int],
    bot_indices: list[int],
    archetype: int,
) -> tuple[int, int]:
    """Return (setting_idx, priority_key)."""
    setting_idx = _setting_index_from_tmb(top_idx, mid_indices[0], mid_indices[1])

    bot_suits = [int(suits[j]) for j in bot_indices]
    bot_profile = _bot_suit_profile(bot_suits)
    top_rank = int(ranks[top_idx])
    mid_ranks = [int(ranks[j]) for j in mid_indices]
    mid_suits = [int(suits[j]) for j in mid_indices]

    mid_is_pair = mid_ranks[0] == mid_ranks[1]
    mid_is_broadway = mid_ranks[0] >= 10 and mid_ranks[1] >= 10
    mid_is_suited_connector = (mid_suits[0] == mid_suits[1]) and abs(mid_ranks[0] - mid_ranks[1]) <= 2
    if mid_is_pair:
        mid_kind = 3
    elif mid_is_broadway:
        mid_kind = 2
    elif mid_is_suited_connector:
        mid_kind = 1
    else:
        mid_kind = 0

    bot_score_lookup = {2: 4, 1: 3, 0: 2, 3: 1, 4: 0, -1: 0}
    bot_score = bot_score_lookup.get(bot_profile, 0)
    archetype_tiebreak = {1: 1, 2: 0}[archetype]

    key = (bot_score * 100000) + (top_rank * 1000) + (mid_kind * 10) + archetype_tiebreak
    return (setting_idx, key)


def _detect_v12_trips_pair_setting(hand_bytes: np.ndarray) -> int | None:
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11
    rank_counts = np.bincount(ranks, minlength=15)

    # Exactly trips_pair: one rank with count 3, one rank with count 2, no quads.
    n_trips = sum(rank_counts[r] == 3 for r in range(2, 15))
    n_pairs = sum(rank_counts[r] == 2 for r in range(2, 15))
    n_quads = sum(rank_counts[r] >= 4 for r in range(2, 15))
    if n_quads > 0 or n_trips != 1 or n_pairs != 1:
        return None
    trip_rank = next(r for r in range(2, 15) if rank_counts[r] == 3)
    pair_rank = next(r for r in range(2, 15) if rank_counts[r] == 2)

    trip_idx = sorted(j for j in range(7) if ranks[j] == trip_rank)
    pair_idx = sorted(j for j in range(7) if ranks[j] == pair_rank)
    kicker_idx = sorted(j for j in range(7) if j not in (*trip_idx, *pair_idx))
    if len(trip_idx) != 3 or len(pair_idx) != 2 or len(kicker_idx) != 2:
        return None  # malformed

    candidates: list[tuple[int, int]] = []

    for top_pos in (0, 1):
        top_idx = kicker_idx[top_pos]
        other_kicker = kicker_idx[1 - top_pos]

        # Archetype A: mid = 2 of 3 trips (paired mid).
        # bot = pair + 1 trip + other_kicker.
        for trip_in_bot_pos in range(3):
            trip_in_bot = trip_idx[trip_in_bot_pos]
            trips_in_mid = [trip_idx[i] for i in range(3) if i != trip_in_bot_pos]
            mid = trips_in_mid
            bot = [*pair_idx, trip_in_bot, other_kicker]
            candidates.append(_score_setting(hand_bytes, ranks, suits, top_idx, mid, bot, archetype=1))

        # Archetype B: mid = 1 trip + 1 kicker. bot = pair + 2 trips.
        for trip_in_mid_pos in range(3):
            trip_in_mid = trip_idx[trip_in_mid_pos]
            trips_in_bot = [trip_idx[i] for i in range(3) if i != trip_in_mid_pos]
            mid = sorted([trip_in_mid, other_kicker])
            bot = [*pair_idx, *trips_in_bot]
            candidates.append(_score_setting(hand_bytes, ranks, suits, top_idx, mid, bot, archetype=2))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def strategy_v12_trips_pair(hand: np.ndarray) -> int:
    """v12: trips_pair routing rule. Falls back to v10 on other hand types."""
    chosen = _detect_v12_trips_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v10_two_pair_no_split(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    test_cases = [
        ("3c 3d 3h 5c 5d 6c Qs", 91, "#1: trip 3 + pair 5, oracle mid=33 bot=66+5+3+...wait let me check"),
        ("3c 3d 3h 4c 4d 5s 6h", 86, "#2: trip 3 + pair 4, oracle"),
        ("4c Td Th Ts Jc Jd Qd", 99, "#8: trip T + pair J, broadway"),
    ]
    for s, expected, note in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        chosen = _detect_v12_trips_pair_setting(h)
        match = "✓" if chosen == expected else "✗"
        print(f"{match} {s}  detected={chosen}  expected={expected}  ({note})")
