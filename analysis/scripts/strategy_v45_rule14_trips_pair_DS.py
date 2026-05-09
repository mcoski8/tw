"""
Session 49 — v45 = v44 + Rule 14 (trips_pair pair-bot + DS, V_B_TOP_SING_HI).

Drill I + Drill J findings (full trips_pair pop, n=171,600):
  - 75% of trips_pair hands have ≥1 pair-bot + DS configuration achievable.
  - Drill I: best-in-V3 (pair-bot + DS) lifts vs v44 by +$1,992/1000h
    within fires.
  - Drill J: among 7 sub-config × top variants, ONLY V_B_TOP_SING_HI wins
    decisively (+$4,293/1000h within fires; +$42.90 whole-grid full).
    All other variants LOSE vs v44.

V_B_TOP_SING_HI:
  - bot = pair + 1 trip card + low singleton (4 cards, DS pattern 2+2)
  - top = high singleton
  - mid = the other 2 trip cards (super-strong Hold'em "trips on mid")

DS achievability for V_B:
  - Pair has suits {p1, p2}. Bot suits = {p1, p2, t, low_sing_suit}
    where t ∈ {a, b, c} (the trip's suits, 3 of 4).
  - Need 2+2 pattern → {t, low_sing_suit} = {p1, p2} (one match each).

Rule 14 — trigger:
  cat == trips_pair                          AND
  V_B_TOP_SING_HI achievable
  (pair-bot + 1 trip + low_sing forms DS pattern)

Setting builder:
  Try each of the 3 trip cards as the one to put in bot:
    bot = pair (2) + this trip card (1) + low_singleton (1)
    Check if bot is DS (2+2 suit pattern).
  If found: top = high_singleton, mid = other 2 trip cards.
  Else: fall through to v44.

Skip-the-trap design: Drill J showed V_B_TOP_TRIP, V_B_TOP_SING_LO,
all V_A_*, and V_C_TOP_TRIP are all LOSS variants. Only V_B_TOP_SING_HI
wins, so don't fire on hands where it's not achievable.

Expected lift: +$43/1000h whole-grid full + +$14/1000h whole-grid prefix
(estimated from drill).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule14_trips_pair_DS(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 1 or n_pairs != 1:
        return None
    trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
    pair_rank = next(r for r in range(2, 15) if rc[r] == 2)

    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
    pos_trip = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) not in
                        (trip_rank, pair_rank)],
                        key=lambda j: -int(ranks[j]))  # desc by rank
    if len(sing_pos) != 2:
        return None  # malformed (shouldn't happen for trips_pair)
    sing_high, sing_low = sing_pos[0], sing_pos[1]

    pair_suits = [int(suits[p]) for p in pos_pair]
    low_sing_suit = int(suits[sing_low])

    # V_B_TOP_SING_HI: bot = pair + 1 trip + low_sing, top = high_sing
    # DS achievable iff (chosen trip suit, low_sing_suit) covers {p1, p2}
    # i.e., {trip_suit, low_sing_suit} = {pair_suits[0], pair_suits[1]}
    for trip_card_pos in pos_trip:
        trip_suit = int(suits[trip_card_pos])
        bot_suits = pair_suits + [trip_suit, low_sing_suit]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt[:2] != [2, 2]:
            continue
        # DS achieved!
        # top = sing_high; mid = 2 trip cards (the ones not in bot)
        mid_trip_pos = sorted(p for p in pos_trip if p != trip_card_pos)
        return int(_setting_index_from_tmb(sing_high, mid_trip_pos[0],
                                              mid_trip_pos[1]))

    return None


def strategy_v45_rule14_trips_pair_DS(hand: np.ndarray) -> int:
    chosen = _detect_rule14_trips_pair_DS(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v44_rule13_three_pair_DS(hand))
