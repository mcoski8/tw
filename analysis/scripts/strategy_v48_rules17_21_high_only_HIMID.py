"""
Session 53 OVERNIGHT P1 — v48 = v47 + Rules 17-21 (high_only J-high through
7-high, max-on-top + DS/SS HIMID).

Generalizes Rules 14/15/16 (A/K/Q-high HIMID) to all remaining high_only
no-pair sub-pops. Single strategy file wrapping 5 parallel rules with
identical structure, only the max_rank gate differs.

For each max_rank in {11 (J), 10 (T), 9, 8, 7}:
  TRIGGER: cat=high_only AND max_rank == M AND DS-bot OR SS-bot
           achievable with M on top.
  SETTING: TOP=M; try DS-bot first (HIMID), else SS-bot fallback (HIMID),
           else fall through to v47.

Note: J-high through 7-high are smaller pops (collectively ~7% of high_only
≈ 1.4% of grid). Per-rule lift expected $5-15. Combined: $25-75/1000h.

The 6-high and below sub-pops are tiny (<1% of high_only) and have
a defensive top-inversion pattern dominating (oracle prefers 2-on-top
on most of them). Skipped here — would be addressed by P2.

Rule numbering:
  Rule 17 = J-high (max=11) HIMID
  Rule 18 = T-high (max=10) HIMID
  Rule 19 = 9-high (max=9)  HIMID
  Rule 20 = 8-high (max=8)  HIMID
  Rule 21 = 7-high (max=7)  HIMID
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

from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

# Sub-pop max ranks covered by Rules 17-21
COVERED_MAX_RANKS = {11, 10, 9, 8, 7}


def _detect_high_only_HIMID(hand: np.ndarray) -> Optional[int]:
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
    if max_r not in COVERED_MAX_RANKS:
        return None
    max_pos = next(j for j in range(7) if int(ranks[j]) == max_r)
    others = [j for j in range(7) if j != max_pos]

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
        return int(_setting_index_from_tmb(max_pos, mid_a, mid_b))

    if ss_options:
        ss_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ss_options[0]
        return int(_setting_index_from_tmb(max_pos, mid_a, mid_b))

    return None


def strategy_v48_rules17_21_high_only_HIMID(hand: np.ndarray) -> int:
    chosen = _detect_high_only_HIMID(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v47_rule16_Qhigh_DS(hand))
