"""
Session 45 — v41 = v40b + suit-aware bot construction in Rule 10 (v3).

Rule 10 v40b currently uses:
  TOP = lowest non-pair singleton
  MID = the pair
  BOT = 4 highest non-pair singletons

This is suit-blind. Drill A (J-low pair DS-break) showed:
  - Breaking the pair to enable DS-bot is catastrophic (-$10,304/1000h within-hand).
  - BUT keeping pair-in-mid AND choosing singletons that form DS-bot is
    +$2,756/1000h within-hand vs the best non-DS pair-mid pick (A1−A2).

Rule 10 v3 — same trigger + gate as v40b, but pick the TOP card such that
the remaining 4 singletons form a DS bot when achievable. Tie-break: among
DS-achievable tops, prefer the lowest-rank singleton (preserves v40b's
"weak-hand top inversion" principle as much as possible).

If no top-choice yields a DS bot, fall back to v40b's "TOP = lowest singleton".

Trigger (unchanged from v40b):
  cat == pair                AND
  max_rank ≤ J               AND
  (P ≤ 6 OR P == max_rank)
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

from strategy_v39_rule9 import strategy_v39_rule9  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule10_v3(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 0 or n_pairs != 1:
        return None
    max_r = int(ranks.max())
    if max_r > 11:
        return None
    P = next(r for r in range(2, 15) if rc[r] == 2)
    if not (P <= 6 or P == max_r):
        return None

    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == P)
    sings_pos = sorted([j for j in range(7) if int(ranks[j]) != P],
                        key=lambda j: (-int(ranks[j]), j))
    # sings_pos[0] = highest singleton, sings_pos[4] = lowest

    # Try each singleton as TOP; the remaining 4 go to bot.
    # Bot is DS iff the 4 suits split 2+2.
    ds_candidates = []  # list of (sing_idx, top_pos)
    for ti in range(5):
        top_pos = sings_pos[ti]
        bot_pos = [sings_pos[i] for i in range(5) if i != ti]
        bot_suits = [int(h[p]) & 3 for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt == [2, 2]:
            ds_candidates.append((ti, top_pos))

    if ds_candidates:
        # Tie-break: prefer dropping the lowest-rank singleton (highest ti).
        # This keeps the "weak top + strong bot" intent as much as possible.
        ds_candidates.sort(key=lambda x: -x[0])
        top_pos = ds_candidates[0][1]
    else:
        # Fallback: v40b's pick = lowest singleton on top.
        top_pos = sings_pos[-1]

    mid_a, mid_b = sorted(pos_pair)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def strategy_v41_rule10_v3_ds(hand: np.ndarray) -> int:
    chosen = _detect_rule10_v3(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v39_rule9(hand))
