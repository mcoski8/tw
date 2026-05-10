"""
Session 53 OVERNIGHT — v57 = v52 + Rule 19 v2 (trips_pair V_B, GATED to trip≥8).

v56 (Rule 19 unrestricted) shipped +$10 full but REGRESSED -$130 prefix
(13× ratio, fails methodology gate). Diagnosis: V_B is right for high-rank
trips (mid-paired with high trip is strong) but wrong for low-rank trips
(prefix-dominant zone).

v57 v1 — gate trip_rank ≥ 8:
  TRIGGER: cat=trips_pair AND trip_rank ≥ 8 (8, 9, T, J, Q, K, A)
  SETTING: same as v56 (force V_B structure)

Hypothesis: high-rank trip means the mid-pair (2 trip cards) is a strong
Hold'em hand. Low-rank trip (≤ 7) means mid-pair is weak — V_A or other
may win there.

If this still regresses prefix, defer entirely.
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

TRIP_GATE = 8


def _detect_rule19_v2(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 1 or n_pairs != 1:
        return None
    trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
    if trip_rank < TRIP_GATE:
        return None  # Gate: only fire when trip is high-rank
    pair_rank = next(r for r in range(2, 15) if rc[r] == 2)

    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
    pos_trip = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) not in
                        (trip_rank, pair_rank)],
                        key=lambda j: -int(ranks[j]))
    if len(sing_pos) != 2:
        return None
    sing_high, sing_low = sing_pos[0], sing_pos[1]

    trip_card_for_bot = pos_trip[0]
    mid_trip_pos = sorted(p for p in pos_trip if p != trip_card_for_bot)
    return int(_setting_index_from_tmb(sing_high, mid_trip_pos[0],
                                          mid_trip_pos[1]))


def strategy_v57_rule19_trips_pair_gated(hand: np.ndarray) -> int:
    chosen = _detect_rule19_v2(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v52_full_high_only_handler(hand))
