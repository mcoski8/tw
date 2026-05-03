"""
v13 — extend v12 to handle 'trips' (3 of one rank, no other pair).

Top-15 v10/v12 misses on trips hands showed v10 falls through to v3
default (rainbow non-paired-mid junk) — bleed $43-46K/1000h per hand.
Oracle ALWAYS splits trips 2+1: mid = 2 of 3 trip-members (paired mid),
bot = 1 trip-overflow + 3 kickers in DS pattern, top = the remaining
kicker.

v13 enumerates the 12 candidates (3 trip-split positions × 4 top-kicker
choices) and picks by bot suit profile > top rank > archetype-tiebreak.
Falls back to v12 on non-trips hands.
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

from strategy_v10_two_pair_no_split import _bot_suit_profile  # noqa: E402
from strategy_v12_trips_pair import strategy_v12_trips_pair  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_v13_trips_setting(hand_bytes: np.ndarray) -> int | None:
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11
    rank_counts = np.bincount(ranks, minlength=15)

    # Exactly trips: one rank count == 3, no other pairs/trips/quads.
    n_trips = sum(rank_counts[r] == 3 for r in range(2, 15))
    n_pairs = sum(rank_counts[r] == 2 for r in range(2, 15))
    n_quads = sum(rank_counts[r] >= 4 for r in range(2, 15))
    if n_trips != 1 or n_pairs != 0 or n_quads != 0:
        return None
    trip_rank = next(r for r in range(2, 15) if rank_counts[r] == 3)

    trip_idx = sorted(j for j in range(7) if ranks[j] == trip_rank)
    kicker_idx = sorted(j for j in range(7) if j not in trip_idx)
    if len(trip_idx) != 3 or len(kicker_idx) != 4:
        return None

    candidates: list[tuple[int, int]] = []

    for top_pos in range(4):
        top_idx = kicker_idx[top_pos]
        other_kickers = [kicker_idx[i] for i in range(4) if i != top_pos]
        for trip_in_bot_pos in range(3):
            trip_in_bot = trip_idx[trip_in_bot_pos]
            trips_in_mid = [trip_idx[i] for i in range(3) if i != trip_in_bot_pos]
            mid = trips_in_mid
            bot = [trip_in_bot, *other_kickers]
            setting_idx = _setting_index_from_tmb(top_idx, mid[0], mid[1])

            bot_suits = [int(suits[j]) for j in bot]
            bot_profile = _bot_suit_profile(bot_suits)
            top_rank = int(ranks[top_idx])
            bot_ranks = [int(ranks[j]) for j in bot]
            bot_rank_sum = sum(bot_ranks)
            # Connectivity bonus: longest run of consecutive distinct ranks.
            bot_distinct = sorted(set(bot_ranks))
            longest = 1
            cur = 1
            for k in range(1, len(bot_distinct)):
                if bot_distinct[k] == bot_distinct[k - 1] + 1:
                    cur += 1
                    longest = max(longest, cur)
                else:
                    cur = 1

            bot_score_lookup = {2: 4, 1: 3, 0: 2, 3: 1, 4: 0, -1: 0}
            bot_score = bot_score_lookup.get(bot_profile, 0)
            # Priority: DS > SS > rainbow, then maximise BOT rank sum (high cards
            # in bot work harder vs the realistic mixture). Top rank is a
            # final tiebreak only — usually the leftover kicker is fine.
            key = (bot_score * 1_000_000) + (bot_rank_sum * 1000) + (longest * 100) + top_rank
            candidates.append((setting_idx, key))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def strategy_v13_trips(hand: np.ndarray) -> int:
    """v13: trips routing rule. Falls back to v12 on other hands."""
    chosen = _detect_v13_trips_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v12_trips_pair(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    test_cases = [
        ("3c 3d 3h 4s 5s 7c Qd", 76, "#1: trip 3, oracle mid=33 bot=Qd5s4s3d DS"),
        ("3c Td Jd Jh Js Qc Kd", 102, "#6: trip J, oracle mid=JsJh bot=QcJdTd3c DS"),
        ("3c 3d 3h 4c 5d 6c Qs", 91, "#5: trip 3, oracle mid=33 top=Qs bot DS"),
    ]
    for s, expected, note in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        chosen = _detect_v13_trips_setting(h)
        match = "✓" if chosen == expected else "✗"
        print(f"{match} {s}  detected={chosen}  expected={expected}  ({note})")
