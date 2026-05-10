"""
Session 50 — v45 = v44 + Rule 14 (A-high no-pair, A-on-top + DS/SS HIMID).

Drill K (characterization, n=660,660): A-high no-pair = 11% of grid with
$3,752/1000h regret per hand → $412.5/1000h whole-grid contribution.
Best-in-DS vs v44 = +$1,937/1000h within fires; oracle picks DS 48% but
v44 picks DS 59% (over-suit-blind), and v44 picks rainbow 11% vs oracle's
0.83% (13× too often).

Drill L (Phase 2 heuristic sweep, 50K sample):
  - H2_DS_HIMID lift vs v44: +$1,016/1000h within fires (+$6.56 wg full)
  - HYBRID HIMID (DS-HIMID, SS-HIMID fallback): +$1,245 within fires (+$10.06 wg full)
  - HYBRID ORACLE upper bound: +$2,505 (+$20.26 wg full)
  - HIMID is the right heuristic — keep 2 highest non-A cards in MID
    (strong Hold'em mid). HIBOT (highest 4 in bot) LOSES (-$847).

Rule 14 design — trigger:
  cat == high_only          AND
  max_rank == 14 (Ace)      AND
  DS-bot OR SS-bot achievable with A on top

Setting builder:
  TOP = the Ace.
  Try DS-bot first:
    Among A-on-top settings with DS bot, pick the one whose mid has
    the HIGHEST rank-sum (HIMID = mid keeps the 2 strongest non-A cards).
  Else try SS-bot:
    Same HIMID tie-break among A-on-top settings with SS bot.
  Else fall through to v44.

  MID = the 2 highest-rank non-A cards (subject to suit constraint).
  BOT = the remaining 4 non-A cards.

Note on prefix coverage: high_only category has ZERO prefix coverage
(S43 finding — all canonical IDs > 500K). Rule 14 fires on 0 prefix
hands → prefix score AUTOMATICALLY UNCHANGED (no regression risk).
Same precedent as Rule 11 (J-pair-J zero-prefix-coverage).

Expected lift: +$10/1000h whole-grid full + $0 prefix.
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

from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

ACE = 14


def _detect_rule14_Ahigh_DS(hand: np.ndarray) -> Optional[int]:
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
    if int(ranks.max()) != ACE:
        return None  # not A-high
    # high_only with max=A guaranteed: exactly 1 ace
    ace_pos = next(j for j in range(7) if int(ranks[j]) == ACE)
    others = [j for j in range(7) if j != ace_pos]  # 6 non-A positions

    # Enumerate all A-on-top settings (15 mid-pair choices)
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

    # Try DS first (HIMID tie-break)
    if ds_options:
        ds_options.sort(key=lambda x: -x[0])  # descending mid_rank_sum
        _, mid_a, mid_b = ds_options[0]
        return int(_setting_index_from_tmb(ace_pos, mid_a, mid_b))

    # Fallback: SS (HIMID)
    if ss_options:
        ss_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ss_options[0]
        return int(_setting_index_from_tmb(ace_pos, mid_a, mid_b))

    return None  # neither DS nor SS achievable; fall through


def strategy_v45_rule14_Ahigh_DS(hand: np.ndarray) -> int:
    chosen = _detect_rule14_Ahigh_DS(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v44_rule13_three_pair_DS(hand))
