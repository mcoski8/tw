"""
Session 53 OVERNIGHT P2 — v49 = v48 + Rule 22 (Q-high defensive top inversion).

Drill O (Session 53) found that for Q-high no-pair, oracle picks Q on top
only 49.37%. The non-Q-on-top sub-zone breaks down with 32% defensive
(oracle picks 2-7 on top, $5,329/1000h regret in zone).

Per-2nd-high breakdown showed defensive picks dominate when 2nd-high ≤ 8:
  - 2nd=8: 38% Q-on-top, 62% else (defensive)
  - 2nd=7: 22% Q-on-top, 78% else (mostly defensive)

Rule 22 v1 — defensive top inversion for weak Q-high hands:
  TRIGGER: cat=high_only AND max=12 (Queen) AND second-highest ≤ 8
  SETTING:
    TOP = lowest-rank singleton (defensive)
    Try DS-bot among settings with TOP=lowest, HIMID tie-break.
    Else try SS-bot HIMID.
    Else fall through to Rule 16 (which would put Q on top).

This is the no-pair analog of Rule 10 (J-low pair defensive).

Note on prefix coverage: high_only zero prefix coverage, same as Rules 14-16.
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

QUEEN = 12


def _detect_rule22_Qhigh_defensive(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) != 0: return None
    if int((rc == 3).sum()) != 0: return None
    if int((rc == 2).sum()) != 0: return None
    if int(ranks.max()) != QUEEN:
        return None
    sorted_ranks = sorted(int(r) for r in ranks)
    if sorted_ranks[-2] > 8:  # 2nd-high must be 2-8
        return None

    # Find lowest-rank position
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


def strategy_v49_rule22_Qhigh_defensive(hand: np.ndarray) -> int:
    chosen = _detect_rule22_Qhigh_defensive(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v48_rules17_21_high_only_HIMID(hand))
