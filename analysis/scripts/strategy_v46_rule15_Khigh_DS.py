"""
Session 51 — v46 = v45 + Rule 15 (K-high no-pair, K-on-top + DS/SS HIMID).

Same structure as Rule 14 (A-high) but for K-high.

Drill M findings (n=330,330 K-high no-pair hands):
  - Mean regret $4,114/1000h within K-high → $226/1000h whole-grid contribution
  - v45 puts K on top 100% (oracle 66%); over-DS, picks rainbow 24× too often
  - Best-in-DS vs v45 = +$2,999/1000h within fires (+$150 wg ceiling)
  - Best-in-SS vs v45 = +$1,790/1000h within fires (+$90 wg ceiling)

Rule 15 design — same as Rule 14 but for K-high:
  TRIGGER:
    cat == high_only           AND
    max_rank == 13 (King)      AND
    DS-bot OR SS-bot achievable with K on top

  SETTING BUILDER:
    TOP = the King.
    Try DS-bot first (HIMID — mid keeps highest 2 non-K cards).
    Else try SS-bot (HIMID).
    Else fall through to v45.

Note on K-on-top coverage: oracle picks K on top only 66% of the time
for K-high hands. The 34% where oracle prefers Q/J/lower on top is a
known gap; Rule 15 v1 doesn't address it (would require a separate
trigger condition). Estimated: Rule 15 fires on ~95% of K-high hands
(DS or SS achievable) but only captures the K-on-top sub-zone optimally.

Note on prefix coverage: high_only category has ZERO prefix coverage.
Rule 15 fires on 0 prefix hands → prefix unchanged.

Expected lift: TBD via grade. The drill's "Best-in-DS vs v45 = +$2,999"
is the upper bound; HIMID heuristic captured ~60% of the analogous DS
upper bound in A-high, so estimated +$80-100/1000h whole-grid full.
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

from strategy_v45_rule14_Ahigh_DS import strategy_v45_rule14_Ahigh_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

KING = 13


def _detect_rule15_Khigh_DS(hand: np.ndarray) -> Optional[int]:
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
        return None  # not high_only
    if int(ranks.max()) != KING:
        return None  # not K-high
    king_pos = next(j for j in range(7) if int(ranks[j]) == KING)
    others = [j for j in range(7) if j != king_pos]

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
        return int(_setting_index_from_tmb(king_pos, mid_a, mid_b))

    if ss_options:
        ss_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ss_options[0]
        return int(_setting_index_from_tmb(king_pos, mid_a, mid_b))

    return None


def strategy_v46_rule15_Khigh_DS(hand: np.ndarray) -> int:
    chosen = _detect_rule15_Khigh_DS(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v45_rule14_Ahigh_DS(hand))
