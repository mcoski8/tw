"""
Session 52 — v47 = v46 + Rule 16 (Q-high no-pair, Q-on-top + DS/SS HIMID).

Same structure as Rule 14 (A-high) and Rule 15 (K-high) but for Q-high.

Drill N findings (n=150,150 Q-high no-pair):
  - Mean regret $4,488/1000h within Q-high → $112/1000h whole-grid contribution
  - v46 puts Q on top 100% (oracle 49%); over-DS, picks rainbow 37× too often
  - Best-in-DS vs v46 = +$3,604/1000h within fires (+$82 wg ceiling)
  - Best-in-SS vs v46 = +$2,196/1000h within fires (+$50 wg ceiling)

Rule 16 design — same as Rules 14/15 but for Q-high:
  TRIGGER:
    cat == high_only           AND
    max_rank == 12 (Queen)     AND
    DS-bot OR SS-bot achievable with Q on top

  SETTING BUILDER:
    TOP = the Queen (always — Rule 16 v1 doesn't address non-Q top picks).
    Try DS-bot first (HIMID — mid keeps highest 2 non-Q cards).
    Else try SS-bot (HIMID).
    Else fall through to v46.

Note on Q-on-top coverage: oracle picks Q on top only 49% of the time
for Q-high hands (vs A 93%, K 66%). The 51% non-Q-on-top sub-zone
(including 16% defensive 2-on-top) is a known gap.

Even when oracle prefers non-Q on top, Rule 16 still improves the bot
configuration vs v46's suit-blind pick. Estimated whole-grid lift:
+$20-50/1000h.

Note on prefix coverage: high_only category has ZERO prefix coverage.
Rule 16 fires on 0 prefix hands → prefix unchanged.
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

from strategy_v46_rule15_Khigh_DS import strategy_v46_rule15_Khigh_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

QUEEN = 12


def _detect_rule16_Qhigh_DS(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 0 or n_pairs != 0:
        return None
    if int(ranks.max()) != QUEEN:
        return None
    queen_pos = next(j for j in range(7) if int(ranks[j]) == QUEEN)
    others = [j for j in range(7) if j != queen_pos]

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
        return int(_setting_index_from_tmb(queen_pos, mid_a, mid_b))

    if ss_options:
        ss_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ss_options[0]
        return int(_setting_index_from_tmb(queen_pos, mid_a, mid_b))

    return None


def strategy_v47_rule16_Qhigh_DS(hand: np.ndarray) -> int:
    chosen = _detect_rule16_Qhigh_DS(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v46_rule15_Khigh_DS(hand))
