"""
v14 — combined chain: trips_pair (v12) + two_pair (v10) + single-pair (v9.2)
+ v8 fallback. Replaces v9.1 with v9.2's wider gate.

Design:
    detect_trips_pair(hand) -> use v12's trips_pair routing
    detect_two_pair(hand)   -> use v10's no-split routing
    detect_single_pair(hand) -> use v9.2's pair-to-bot-DS (with (1,3)/(3,1) added)
    else                    -> v8_hybrid fallback
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
from strategy_v9_2_pair_to_bot_ds import _detect_v9_2_setting  # noqa: E402
from strategy_v10_two_pair_no_split import _detect_v10_two_pair_setting  # noqa: E402
from strategy_v12_trips_pair import _detect_v12_trips_pair_setting  # noqa: E402


def strategy_v14_combined(hand: np.ndarray) -> int:
    chosen = _detect_v12_trips_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v10_two_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v9_2_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))
