"""
v21 — combined chain: Rule 3 (trips_pair) → Rule 2 (two_pair) → Rule 1
(single-pair pair-to-bot-DS) → Rule 5 (high_only suited high mid, new
in Session 31) → v8_hybrid fallback (which carries Rule 4: KK/AA-mid).

Same as `strategy_v14_combined` plus Rule 5 inserted before the v8
fallback. Rule 5 fires only on high_only hands, so it cannot collide
with the earlier pair-based rules.
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
from strategy_rule5_suited_mid import _detect_rule5_setting  # noqa: E402


def strategy_v21_combined(hand: np.ndarray) -> int:
    chosen = _detect_v12_trips_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v10_two_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v9_2_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_rule5_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))
