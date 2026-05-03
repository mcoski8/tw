"""
v11 — for high_only hands (no pair/trip/quad), play omaha-first style:
maximize the 4-card bot's strength, then put the LOWEST remaining card on
top (sacrifice the top tier) and the other 2 in mid.

Top-15 v10 misses on high_only showed v8/v10 instinctively puts the
highest card on top + a suited-low-pair in mid, leaving rainbow weak
bots. Oracle plays the inverse: high cards → bot for DS, low card → top.
Per-hand bleed: $25-27K/1000h.

The bot scorer is a Python port of `engine/src/opp_models.rs::omaha_bot_score`
— same weights for high cards, suit profile (DS=14 / SS=7 / rainbow=0 /
3+1=-4 / 4-flush=-8), connectivity (longest run × 8), wheel draws, and
pair/trip bonuses.

Falls back to v10 on non-high_only hands.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from strategy_v10_two_pair_no_split import strategy_v10_two_pair_no_split  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _omaha_bot_score(bot_ranks: list[int], bot_suits: list[int]) -> int:
    """Python port of `engine/src/opp_models.rs::omaha_bot_score`."""
    score = 0
    # High-card value: each rank > 8 adds (rank - 8) × 2.
    for r in bot_ranks:
        if r > 8:
            score += (r - 8) * 2
    # Pair/trip bonuses.
    rank_counts = [0] * 15
    for r in bot_ranks:
        rank_counts[r] += 1
    for r in range(2, 15):
        c = rank_counts[r]
        if c == 2:
            score += 15 + r
        elif c == 3:
            score += 30 + r * 2
        elif c == 4:
            score += 60 + r * 3
    # Connectivity: longest run of consecutive distinct ranks.
    distinct = sorted(set(bot_ranks))
    longest = 1
    cur = 1
    for i in range(1, len(distinct)):
        if distinct[i] == distinct[i - 1] + 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1
    score += longest * 8
    # Wheel draws.
    wheel_count = sum(1 for r in bot_ranks if r == 14 or 2 <= r <= 5)
    if wheel_count >= 3:
        score += 6
    elif wheel_count >= 2:
        score += 3
    # Suit pattern.
    sc = [0, 0, 0, 0]
    for s in bot_suits:
        sc[s] += 1
    sorted_sc = sorted(sc, reverse=True)
    if sorted_sc[0] == 2 and sorted_sc[1] == 2:
        score += 14
    elif sorted_sc[0] == 2 and sorted_sc[1] == 1:
        score += 7
    elif sorted_sc[0] == 1 and sorted_sc[1] == 1:
        score += 0
    elif sorted_sc[0] == 3 and sorted_sc[1] == 1:
        score -= 4
    elif sorted_sc[0] == 4:
        score -= 8
    return score


def _detect_v11_high_only_setting(hand_bytes: np.ndarray) -> int | None:
    ranks_arr = (hand_bytes // 4) + 2
    suits_arr = hand_bytes & 0b11
    rank_counts = np.bincount(ranks_arr, minlength=15)

    # high_only = no pair/trip/quad anywhere.
    if any(rank_counts[r] >= 2 for r in range(2, 15)):
        return None

    ranks = [int(r) for r in ranks_arr]
    suits = [int(s) for s in suits_arr]

    # Best 4-card bot via omaha_bot_score.
    best_bot_idx = (0, 1, 2, 3)
    best_score = -10**9
    for combo in combinations(range(7), 4):
        b_ranks = [ranks[i] for i in combo]
        b_suits = [suits[i] for i in combo]
        s = _omaha_bot_score(b_ranks, b_suits)
        if s > best_score or (s == best_score and combo < best_bot_idx):
            best_score = s
            best_bot_idx = combo

    rem3_idx = [i for i in range(7) if i not in best_bot_idx]
    # Top = LOWEST-rank card of the 3 remaining (sacrifice top).
    top_idx = min(rem3_idx, key=lambda i: hand_bytes[int(i)])
    mid_indices = [i for i in rem3_idx if i != top_idx]
    if len(mid_indices) != 2:
        return None
    return _setting_index_from_tmb(top_idx, mid_indices[0], mid_indices[1])


def strategy_v11_high_only_omaha_first(hand: np.ndarray) -> int:
    """v11: omaha-first sacrifice-top routing for high_only hands. Falls
    back to v10 on hands with any pair/trip/quad."""
    chosen = _detect_v11_high_only_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v10_two_pair_no_split(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    test_cases = [
        # Top-15 v10 misses on high_only — should match oracle on most.
        ("2c 3c 4d 7h 9s Jc Qd", 9, "#1: top=2c, mid=9s7h, bot=QdJc4d3c"),
        ("4c 5d 7d 9h Jc Qs Kh", 88, "#7: top=Qs, mid=Kh9h, bot=Jc7d5d4c"),
        ("2c 5c 6d 7h 9c Ts Jd", 10, "#4: top=2c, mid=Ts7h, bot=Jd9c6d5c"),
    ]
    for s, expected, note in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        chosen = _detect_v11_high_only_setting(h)
        match = "✓" if chosen == expected else "✗"
        print(f"{match} {s}  detected={chosen}  expected={expected}  ({note})")
