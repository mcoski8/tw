"""
Session 53 OVERNIGHT — v54 = v52 + Rule 18 (high-pair AA/KK/QQ suit-aware bot).

Pair gap analysis (Session 53 overnight) found that the biggest residual
cells in v52 are pair hands where pair = max:
  - AA (max=A, pair=A): $57.78/1000h whole-grid contribution (215K hands)
  - KK (max=K, pair=K): $56.52 (126K hands)
  - QQ (max=Q, pair=Q): $49.49 (69K hands)

Rule 4 (existing v3) puts pair in mid + highest singleton on top + 4 lower
singletons in bot. Suit-blind. Rule 18 adds suit-awareness:

  TRIGGER: cat=pair AND pair_rank ∈ {12, 13, 14} AND max_rank == pair_rank
  SETTING:
    MID = the pair (always)
    Try each of 5 non-pair singletons as TOP:
      bot = remaining 4 singletons
      If bot is DS (2+2 suit pattern): candidate
    Among DS-achievable candidates, pick TOP = HIGHEST rank
      (since pair-in-mid is so strong, we want top tier value too)
    If no DS achievable, fall through to v52 (= v3's Rule 4 default)

This is parallel to Rule 10 v3 (J-low pair suit-aware bot) but for high
pairs where TOP=highest is the right tie-break (vs J-low's lowest-on-top).

Note on Rule 5 interaction: Rule 5 (KK/AA rainbow override) fires only
when v3's bot is rainbow. Rule 18 fires when DS is achievable — these
should be complementary (Rule 18 catches DS-achievable, Rule 5 catches
rainbow-only). Test by grading.
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

HIGH_PAIRS = {12, 13, 14}  # Q, K, A


def _detect_rule18(hand: np.ndarray) -> Optional[int]:
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
        return None  # only fire when pair == max

    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
    sings_pos = [j for j in range(7) if int(ranks[j]) != pair_rank]
    if len(sings_pos) != 5:
        return None

    # Try each singleton as TOP; check if remaining 4 form DS bot.
    candidates = []
    for top_idx in sings_pos:
        bot_pos = [j for j in sings_pos if j != top_idx]
        bot_suits = [int(suits[p]) for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt == [2, 2]:
            candidates.append((int(ranks[top_idx]), top_idx))

    if not candidates:
        return None

    # Tie-break: HIGHEST top rank (different from Rule 10 v3)
    candidates.sort(key=lambda x: -x[0])
    top_pos = candidates[0][1]
    mid_a, mid_b = sorted(pos_pair)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def strategy_v54_rule18_high_pair_DS(hand: np.ndarray) -> int:
    chosen = _detect_rule18(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v52_full_high_only_handler(hand))
