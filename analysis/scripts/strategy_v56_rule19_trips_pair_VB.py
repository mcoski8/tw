"""
Session 53 OVERNIGHT — v56 = v52 + Rule 19 (trips_pair force V_B structure).

Trips_pair gap analysis (Session 53 overnight) found:
  - Trips_pair total residual: $155/1000h whole-grid
  - Top sub-cell: v52 picks bot_DS, oracle picks bot_SS — 24,908 hands
    with $9,578/1000h regret each → $40/1000h whole-grid potential
  - Surprising: oracle's SS bot has LOWER rank-sum (32.11) than v52's
    DS bot (34.40) — oracle wins 67.6% despite worse kickers

Diagnosis (sample hand analysis): oracle prefers V_B structure
(bot=pair+1trip+1sing, mid=2 trip cards paired, top=high sing) over
V_A (bot=pair+2trip = pair-pair in bot, mid=1 trip+1 sing unpaired).

Mid-paired (22 in mid as a pair) is worth more than bot-2nd-pair
(22 in bot alongside the main pair). Mid scores 2 pts/board × 2 boards
= 4 pts max; the bot 2nd pair adds only marginal Omaha equity.

Rule 19 v1 — force V_B structure for trips_pair regardless of suit:
  TRIGGER: cat=trips_pair (cat=4)
  SETTING (V_B_TOP_SING_HI):
    bot = pair (2 cards) + 1 trip card + low singleton (1 card)
    mid = the other 2 trip cards (paired mid!)
    top = the high singleton

This OVERRIDES v52's existing trips_pair logic (which falls through to
v3's Rule 3 = sometimes V_A). Forces V_B always.

If V_B yields DS bot, that's bonus. If V_B yields SS or other, accept it
because mid-pair is more valuable than bot suit profile.

Note: this differs from S49's Rule 14 attempt which only fired when DS
was achievable in V_B. Rule 19 fires REGARDLESS of bot suit.
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

from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule19(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 1 or n_pairs != 1:
        return None  # not trips_pair
    trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
    pair_rank = next(r for r in range(2, 15) if rc[r] == 2)

    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
    pos_trip = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) not in
                        (trip_rank, pair_rank)],
                        key=lambda j: -int(ranks[j]))  # desc by rank
    if len(sing_pos) != 2:
        return None
    sing_high, sing_low = sing_pos[0], sing_pos[1]

    # V_B structure: bot = pair + 1 trip + low_sing, mid = 2 trip, top = high_sing
    # Choose which trip card goes in bot (3 options). Pick the lowest by suit
    # arbitrarily — for deterministic ordering, just pick the first (canonical
    # order). Per S49 analysis, the suit picks don't affect mid rank.
    trip_card_for_bot = pos_trip[0]
    mid_trip_pos = sorted(p for p in pos_trip if p != trip_card_for_bot)
    return int(_setting_index_from_tmb(sing_high, mid_trip_pos[0],
                                          mid_trip_pos[1]))


def strategy_v56_rule19_trips_pair_VB(hand: np.ndarray) -> int:
    chosen = _detect_rule19(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v52_full_high_only_handler(hand))
