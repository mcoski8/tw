"""
Session 53 OVERNIGHT P2 — v50 = v48 + Rules 22-23 (high_only A/K/Q-high
defensive top inversion when 2nd-high ≤ 8).

Drill O (Session 53) found that for Q-high no-pair, oracle picks defensive
2-on-top on 16% of hands with $5,565 regret per hand.

Drill K showed A-high oracle 2-on-top at only 0.30% (tiny defensive zone).
Drill M showed K-high oracle 2-on-top at 6.69% (small defensive zone).

This strategy bundles defensive rules for Q-high (Rule 22) and K-high +
A-high (Rule 23) using the same trigger pattern. Triggering only when
2nd-high ≤ 8 (= the rest of the hand is also weak) ensures we fire on
the defensive sub-zone where oracle wants low-card-on-top.

Rule numbering:
  Rule 22 = Q-high defensive (max=Q AND 2nd-high ≤ 8)
  Rule 23 = K-high + A-high defensive (max ∈ {K, A} AND 2nd-high ≤ 8)

Setting builder for both rules: TOP = lowest singleton, MID + BOT chosen
to maximize DS-bot achievability with HIMID tie-break.

Note: high_only zero prefix coverage, same as Rules 14-16.
"""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v48_rules17_21_high_only_HIMID import strategy_v48_rules17_21_high_only_HIMID  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

DEFENSIVE_MAX_RANKS = {11, 12, 13, 14}  # J, Q, K, A
DEFENSIVE_S2_GATE = 8  # 2nd-highest must be ≤ 8


def _detect_high_only_defensive(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) != 0: return None
    if int((rc == 3).sum()) != 0: return None
    if int((rc == 2).sum()) != 0: return None
    max_r = int(ranks.max())
    if max_r not in DEFENSIVE_MAX_RANKS:
        return None
    sorted_ranks = sorted(int(r) for r in ranks)
    if sorted_ranks[-2] > DEFENSIVE_S2_GATE:
        return None  # not defensive zone

    lowest_pos = min(range(7), key=lambda j: int(ranks[j]))
    others = [j for j in range(7) if j != lowest_pos]

    ds_options = []
    ss_options = []
    for mid_a, mid_b in combinations(others, 2):
        bot_pos = sorted(j for j in others if j not in (mid_a, mid_b))
        bot_suits = [int(suits[p]) for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        mid_rank_sum = int(ranks[mid_a]) + int(ranks[mid_b])
        if cnt == [2, 2]:
            ds_options.append((mid_rank_sum, mid_a, mid_b))
        elif cnt == [2, 1, 1]:
            ss_options.append((mid_rank_sum, mid_a, mid_b))

    if ds_options:
        ds_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ds_options[0]
        return int(_setting_index_from_tmb(lowest_pos, mid_a, mid_b))

    if ss_options:
        ss_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ss_options[0]
        return int(_setting_index_from_tmb(lowest_pos, mid_a, mid_b))

    return None


def strategy_v50_rules22_23_high_only_defensive(hand: np.ndarray) -> int:
    chosen = _detect_high_only_defensive(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v48_rules17_21_high_only_HIMID(hand))
