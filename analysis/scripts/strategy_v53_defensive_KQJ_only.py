"""
Session 53 OVERNIGHT — v53 = v48 + defensive K/Q/J only (drops A-high).

v50 (v48 + A/K/Q/J defensive) regressed −$6/1000h. Diagnosis: A-high
defensive forces top=2 on 4,865 hands where oracle wants A-on-top
91-94% of the time — massive per-hand loss.

v53 = v48 + defensive only for max ∈ {J, Q, K} when 2nd-high ≤ 8.
Skip A-high defensive entirely.

This is a clean "remove the hurting part of v50" experiment.
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

DEFENSIVE_MAX_RANKS = {11, 12, 13}  # J, Q, K (NOT A)
DEFENSIVE_S2_GATE = 8


def _detect_v53(hand: np.ndarray) -> Optional[int]:
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
        return None

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


def strategy_v53_defensive_KQJ_only(hand: np.ndarray) -> int:
    chosen = _detect_v53(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v48_rules17_21_high_only_HIMID(hand))
