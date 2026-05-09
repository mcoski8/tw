"""
Session 48 — v44 = v43 + Rule 13 (three_pair all-intact + DS-bot, MM/HH only).

Drill H findings (full three_pair pop, n=114,400):
  - 50% of three_pair hands have ≥1 DS-intact-bot configuration achievable
  - V_MM_MID lift vs v43 = +$2,463/1000h within fires (30% achievability)
  - V_HH_MID lift vs v43 = +$2,227/1000h within fires (30% achievability)
  - V_LL_MID lift vs v43 = -$4,117/1000h within fires (30% achievability — TRAP)

  V_LL_MID is catastrophic because LL in mid is a weak Hold'em hand,
  and the HH+MM bot upgrade can't compensate. Skip LL_mid-only cases.

Rule 13 design — trigger:
  cat == three_pair                             AND
  (MM_mid_DS achievable OR HH_mid_DS achievable)
  (skip when ONLY LL_mid is achievable)

Setting builder (in priority order):
  1. If MM_mid_DS achievable: use it (V_MM_MID)
     mid = MM pair, bot = HH+LL pairs, top = the singleton
  2. Else if HH_mid_DS achievable: use it (V_HH_MID)
     mid = HH pair, bot = MM+LL pairs, top = the singleton
  3. Else: fall through to v43.

If only LL_mid is achievable, fall through (avoid the trap).
If MM_mid AND HH_mid both achievable: prefer MM_mid (higher expected lift).

Expected whole-grid lift: +$13/1000h full + +$35/1000h prefix.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v43_rule12_two_pair_DS_intact import strategy_v43_rule12_two_pair_DS_intact  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _try_three_pair_intact_DS(hand: np.ndarray, mid_pair_rank: int,
                                bot_pair_a_rank: int,
                                bot_pair_b_rank: int) -> Optional[int]:
    """Try to build a three_pair all-intact + DS-bot setting where mid_pair
    goes to mid and the other two pairs go to bot. Returns setting_idx or
    None if DS not achievable (suit sets of bot pairs don't match).
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_mid = sorted(j for j in range(7) if int(ranks[j]) == mid_pair_rank)
    pos_a = sorted(j for j in range(7) if int(ranks[j]) == bot_pair_a_rank)
    pos_b = sorted(j for j in range(7) if int(ranks[j]) == bot_pair_b_rank)
    sing_pos = next(j for j in range(7)
                     if int(ranks[j]) not in (mid_pair_rank, bot_pair_a_rank,
                                               bot_pair_b_rank))
    a_suits = sorted([int(suits[p]) for p in pos_a])
    b_suits = sorted([int(suits[p]) for p in pos_b])
    if a_suits != b_suits:
        return None  # not DS
    mid_a, mid_b = sorted(pos_mid)
    return int(_setting_index_from_tmb(sing_pos, mid_a, mid_b))


def _detect_rule13_three_pair(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 0 or n_pairs != 3:
        return None
    pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
    PH, PM, PL = pairs[0], pairs[1], pairs[2]

    # 1. Try MM_mid (highest expected lift: +$2,463 within fires)
    chosen = _try_three_pair_intact_DS(hand, mid_pair_rank=PM,
                                          bot_pair_a_rank=PH,
                                          bot_pair_b_rank=PL)
    if chosen is not None:
        return chosen

    # 2. Try HH_mid (second-best: +$2,227 within fires)
    chosen = _try_three_pair_intact_DS(hand, mid_pair_rank=PH,
                                          bot_pair_a_rank=PM,
                                          bot_pair_b_rank=PL)
    if chosen is not None:
        return chosen

    # 3. Skip LL_mid (catastrophic: -$4,117 within fires)
    return None


def strategy_v44_rule13_three_pair_DS(hand: np.ndarray) -> int:
    chosen = _detect_rule13_three_pair(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v43_rule12_two_pair_DS_intact(hand))
