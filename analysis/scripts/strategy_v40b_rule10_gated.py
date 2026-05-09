"""
Session 43 — v40b = v39 + Rule 10 (J-low pair defensive, GATED variant).

Same as v40 but with a refined gate that excludes the per-cell regression
zone (pair_rank in (max-4, max-1)).

Refined gate: max_rank <= J  AND  category == pair  AND
              (pair_rank <= 6  OR  pair_rank == max_rank)

The drill_low_pair_J_high_defense.py per-cell breakdown showed the rule
regresses on cells where pair_rank is in (max-4, max-1), e.g.:
  - 9h_p7,8 (regress); 9h_p9 = pair==max (wins)
  - Th_p7,8,9 (regress); Th_pT = pair==max (wins)
  - Jh_p7-T (regress); Jh_pJ = pair==max (wins)

By gating these out, the rule fires on a smaller population but the per-hand
lift is bigger. Estimated whole-grid lift: ~+$48/1000h full (vs +$22.73 in
the unrestricted version) by avoiding the localized regressions.

Run:
  python3 analysis/scripts/grade_v40b_rule10_gated.py --grid {full,prefix}
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

from strategy_v39_rule9 import strategy_v39_rule9  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule10_jlow_pair_gated(hand: np.ndarray) -> Optional[int]:
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
    # Gate: pair_rank <= 6 OR pair_rank == max_rank
    if not (P <= 6 or P == max_r):
        return None
    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == P)
    sings_pos = sorted([j for j in range(7) if int(ranks[j]) != P],
                        key=lambda j: (-int(ranks[j]), j))
    top_pos = sings_pos[-1]
    mid_a, mid_b = sorted(pos_pair)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def strategy_v40b_rule10_gated(hand: np.ndarray) -> int:
    chosen = _detect_rule10_jlow_pair_gated(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v39_rule9(hand))
