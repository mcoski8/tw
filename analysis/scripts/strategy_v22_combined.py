"""
v22 — combined chain: Rule 3 → Rule 2 → Rule 1 → Rule 5 (TIGHTENED:
msphr >= 11 AND msplr >= 9) → v8 fallback (Rule 4 implicit).

Tightening the gate vs v21 (where the rule fired on msphr >= 9) to
test whether a more selective Rule 5 actually beats v14_combined.
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
from strategy_rule5_tight_suited_mid import _detect_rule5_tight_setting  # noqa: E402


def strategy_v22_combined(hand: np.ndarray) -> int:
    chosen = _detect_v12_trips_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v10_two_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v9_2_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_rule5_tight_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))
