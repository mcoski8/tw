"""
Session 48 — v43b = v43 + Rule 12 extension to max≤Q (HH-only at max=Q).

Drill G (Session 48) findings:
  - max=Q: V_HH_BOT lift vs v43 = +$1,283/1000h within fires (+$3.06 whole-grid full)
           V_LL_BOT lift vs v43 = -$289 (regresses)
  - max=K: V_HH_BOT lift = -$133 (basically neutral); V_LL_BOT = -$928 (regresses)
  - max=A: V_HH_BOT lift = -$3,744 (catastrophic); even B1 oracle LOSES vs v43
           Reason: at A-high, putting the A on top is more valuable than the
           pair-bot DS Omaha play.

Rule 12 v2 extension:
  - max ≤ J: HH-first, LL-fallback (UNCHANGED from v43 / Rule 12)
  - max == Q: HH-only (LL-fallback skipped because it regresses at Q)
  - max ≥ K: NO extension (marginal at best, regression at A)

Trigger:
  cat == two_pair
  max ≤ Q
  DS-bot achievable with both pairs intact AND (HH-to-bot if max==Q,
    HH-to-bot OR LL-to-bot if max ≤ J)

Setting builder: same as Rule 12.
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
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_in_bot = sorted(j for j in range(7) if int(ranks[j]) == pair_to_bot_rank)
    pos_in_mid = sorted(j for j in range(7) if int(ranks[j]) == pair_to_mid_rank)
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) not in
                        (pair_to_bot_rank, pair_to_mid_rank)],
                        key=lambda j: int(ranks[j]))

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
    top_pos = next(j for j in sing_pos if j != sa and j != sb)
    mid_a, mid_b = sorted(pos_in_mid)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _detect_rule12_v2(hand: np.ndarray) -> Optional[int]:
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
    max_r = int(ranks.max())
    if max_r > 12:  # Extend to max ≤ Q (12); max=K (13) and max=A (14) excluded
        return None
    pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
    PH, PL = pairs[0], pairs[1]

    # Try HH-to-bot first (always)
    chosen = _try_pair_to_bot_DS(hand, pair_to_bot_rank=PH,
                                   pair_to_mid_rank=PL)
    if chosen is not None:
        return chosen

    # LL-fallback ONLY at max ≤ J (NOT at max=Q where LL regresses)
    if max_r <= 11:
        chosen = _try_pair_to_bot_DS(hand, pair_to_bot_rank=PL,
                                       pair_to_mid_rank=PH)
        if chosen is not None:
            return chosen

    return None


def strategy_v43b_rule12_two_pair_extQ(hand: np.ndarray) -> int:
    chosen = _detect_rule12_v2(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v42_rule11_jpair_pbot_ds(hand))
