"""
Session 53 OVERNIGHT P2 alternative — v51 = v47 + defensive rules for
high_only with max ∈ {J, T, 9, 8, 7}.

Mini-drill (Session 53) found that for low-max high_only:
  - max=J: oracle picks J-on-top only 27% (vs 73% something else, mostly
    defensive 2-on-top at 28% + lower-rank top at 45%)
  - max=T: 14.55% T-on-top
  - max=9: 6.83% 9-on-top
  - max=8: 2.94% 8-on-top
  - max=7: ~similar low %

For these sub-pops, defensive lowest-on-top should DOMINATE, not be a
niche override. v48 (HIMID for J-7) likely regresses heavily on these
because oracle wants max-on-top only 3-27% of the time.

v51 instead applies defensive structure for ALL max ∈ {J, T, 9, 8, 7}
no-pair hands (no 2nd-high gate — defensive is the default for low max):
  TRIGGER: cat=high_only AND max ∈ {7,8,9,10,11}
  SETTING:
    TOP = lowest-rank singleton
    MID = max-card + highest other singleton (HIMID-style for 2 highest)
    BOT = 4 middle/low cards (DS or SS preferred)
    Use DS-bot HIMID tie-break among defensive options.

This is the no-pair analog of Rule 10's J-low pair defensive structure.

If v51 ships better than v48, replace HIMID for low-max with defensive.
If neither ships cleanly, the right answer is probably hand-by-hand
adaptive (separate trigger for offensive vs defensive based on more
features).
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

DEFENSIVE_MAX_RANKS = {7, 8, 9, 10, 11}  # J, T, 9, 8, 7


def _detect_defensive_max_le_J(hand: np.ndarray) -> Optional[int]:
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


def strategy_v51_defensive_max_le_J(hand: np.ndarray) -> int:
    chosen = _detect_defensive_max_le_J(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v47_rule16_Qhigh_DS(hand))
