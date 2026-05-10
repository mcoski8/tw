"""
Session 53 OVERNIGHT — v55 = v52 + Rule 18 v2 (HIBOT tie-break).

v54 (Rule 18 with HITOP tie-break) regressed −$5/1000h vs v52.
Hypothesis: for AA/KK/QQ pair, mid is so strong that bot kicker matters
more than top equity. So TOP = LOWEST singleton (HIBOT) might win.

v55 = v52 + Rule 18 v2:
  TRIGGER: cat=pair AND pair_rank ∈ {12, 13, 14} AND max == pair_rank
  SETTING:
    MID = pair
    Try each of 5 singletons as TOP.
    Among DS-bot achievable picks, pick TOP = LOWEST rank (HIBOT).
    If no DS achievable: fall through to v52.

Note: this is parallel to Rule 10 v3 (J-low pair HIBOT) — same HIBOT
tie-break for J-low pair. Whether it works for high pair (AA/KK/QQ)
is the open question.
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

from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

HIGH_PAIRS = {12, 13, 14}


def _detect_rule18_v2(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) != 0: return None
    if int((rc == 3).sum()) != 0: return None
    if int((rc == 2).sum()) != 1: return None
    pair_rank = next(r for r in range(2, 15) if rc[r] == 2)
    if pair_rank not in HIGH_PAIRS:
        return None
    if int(ranks.max()) != pair_rank:
        return None

    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
    sings_pos = [j for j in range(7) if int(ranks[j]) != pair_rank]
    if len(sings_pos) != 5:
        return None

    candidates = []
    for top_idx in sings_pos:
        bot_pos = [j for j in sings_pos if j != top_idx]
        bot_suits = [int(suits[p]) for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt == [2, 2]:
            candidates.append((int(ranks[top_idx]), top_idx))

    if not candidates:
        return None

    # Tie-break: LOWEST top rank (HIBOT — keeps highest 4 sings in bot)
    candidates.sort(key=lambda x: x[0])  # ascending = lowest first
    top_pos = candidates[0][1]
    mid_a, mid_b = sorted(pos_pair)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def strategy_v55_rule18_hibot(hand: np.ndarray) -> int:
    chosen = _detect_rule18_v2(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v52_full_high_only_handler(hand))
