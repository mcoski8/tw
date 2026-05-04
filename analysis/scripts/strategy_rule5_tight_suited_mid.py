"""
Session 31 — Rule 5 (tighter variant). Original `strategy_rule5_suited_mid`
graded -$680/1000h vs v14 because it fires on 1.21M high_only hands but
only 12% of those benefit from a suited-mid swap. This variant tightens
the gate to msphr >= 11 AND msplr >= 9 (the suited pair must contain a
broadway card with a 9+ partner).
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from strategy_v8_hybrid import strategy_v8_hybrid  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

RULE5T_MIN_MAX_RANK = 11   # max-rank threshold (J)
RULE5T_MIN_MIN_RANK = 9    # min-rank threshold (9)


def _detect_rule5_tight_setting(hand_bytes: np.ndarray) -> int | None:
    if hand_bytes.shape[0] != 7:
        return None
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11
    if len(set(int(r) for r in ranks)) != 7:
        return None
    best = None
    for i in range(7):
        for j in range(i + 1, 7):
            if suits[i] == suits[j]:
                ri, rj = int(ranks[i]), int(ranks[j])
                hi = ri if ri > rj else rj
                lo = ri if ri < rj else rj
                if hi >= RULE5T_MIN_MAX_RANK and lo >= RULE5T_MIN_MIN_RANK:
                    cand = (hi, lo, i, j)
                    if best is None or cand > best:
                        best = cand
    if best is None:
        return None
    _, _, i, j = best
    rest = [k for k in range(7) if k != i and k != j]
    top_idx = rest[-1]
    return _setting_index_from_tmb(top_idx, i, j)


def strategy_rule5_tight_suited_mid(hand: np.ndarray) -> int:
    chosen = _detect_rule5_tight_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))
