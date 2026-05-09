"""
Session 47 — v43 = v42 + Rule 12 (J-low two_pair both-intact + DS-bot).

Drill F findings (J-low two_pair, n=262,080, full grid):
  - DS achievable with both pairs intact: 46.2% of pop (120,960 hands)
  - V_HH_BOT (HH-to-bot tie-break) lift vs v42: +$1,808/1000h within fires
    → +$22.75/1000h whole-grid full lift
  - V_LL_BOT (LL-to-bot tie-break) lift vs v42: +$1,044/1000h within fires
    → +$13.14/1000h whole-grid full lift
  - HYBRID (HH preferred, LL fallback): estimated +$30/1000h whole-grid full

Rule 12 design — trigger:
  cat == two_pair       AND
  max_rank ≤ J          AND
  DS-bot achievable with both pairs intact (HH or LL to bot)

Setting builder:
  Both pairs stay intact. Try HH-to-bot first; if no DS achievable, try
  LL-to-bot. If neither achievable, fall through to v42.

  Pair-to-bot: 2 pair-cards + 2 singletons.
    DS achievable iff suit pattern of (pair_suit_a, pair_suit_b,
    sing_x_suit, sing_y_suit) is 2+2.
      Case A: pair members same suit X
        → need 2 singletons of same non-X suit Y
      Case B: pair members different suits X, Y
        → need 1 singleton of suit X + 1 of suit Y
    Among multiple valid (sing_x, sing_y) options, pick the lowest-rank
    pair (preserves mid + top strength).

  TOP = the leftover singleton (the 1 not picked for bot).
  MID = the OTHER pair (the one not in bot).
  BOT = the chosen pair + 2 chosen singletons.

If neither HH-to-bot nor LL-to-bot has DS achievable, fall through to v42.

Validation: full grid (N=200) and prefix grid (N=1000). Two_pair has
prefix coverage; expect both grids positive.
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

from strategy_v42_rule11_jpair_pbot_ds import strategy_v42_rule11_jpair_pbot_ds  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _try_pair_to_bot_DS(hand: np.ndarray, pair_to_bot_rank: int,
                         pair_to_mid_rank: int) -> Optional[int]:
    """Try to build a both-intact + DS-bot setting with the given
    pair-to-bot rank. Returns setting_idx or None.
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_in_bot = sorted(j for j in range(7) if int(ranks[j]) == pair_to_bot_rank)
    pos_in_mid = sorted(j for j in range(7) if int(ranks[j]) == pair_to_mid_rank)
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) not in
                        (pair_to_bot_rank, pair_to_mid_rank)],
                        key=lambda j: int(ranks[j]))  # ascending by rank

    # Enumerate (sa, sb) pairs that complete DS bot.
    # Tie-break: lowest sum of ranks (preserves mid/top strength).
    bot_pair_suits = [int(suits[p]) for p in pos_in_bot]
    best = None
    best_sum = None
    for sa, sb in combinations(sing_pos, 2):
        bot_suits = bot_pair_suits + [int(suits[sa]), int(suits[sb])]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt[:2] != [2, 2]:
            continue
        rsum = int(ranks[sa]) + int(ranks[sb])
        if best_sum is None or rsum < best_sum:
            best_sum = rsum
            best = (sa, sb)

    if best is None:
        return None

    sa, sb = best
    # Top = the leftover singleton (3 - 2 used = 1 left)
    top_pos = next(j for j in sing_pos if j != sa and j != sb)
    mid_a, mid_b = sorted(pos_in_mid)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _detect_rule12_two_pair_DS_intact(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 0 or n_pairs != 2:
        return None
    if int(ranks.max()) > 11:
        return None
    pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
    PH, PL = pairs[0], pairs[1]

    # Try HH-to-bot (Drill F: V_HH_BOT lift = +$1,808/1000h within fires)
    chosen = _try_pair_to_bot_DS(hand, pair_to_bot_rank=PH,
                                   pair_to_mid_rank=PL)
    if chosen is not None:
        return chosen

    # Fallback: LL-to-bot (Drill F: V_LL_BOT lift = +$1,044/1000h within fires)
    chosen = _try_pair_to_bot_DS(hand, pair_to_bot_rank=PL,
                                   pair_to_mid_rank=PH)
    if chosen is not None:
        return chosen

    return None


def strategy_v43_rule12_two_pair_DS_intact(hand: np.ndarray) -> int:
    chosen = _detect_rule12_two_pair_DS_intact(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v42_rule11_jpair_pbot_ds(hand))
