"""
Session 28 — strategy_v17: hand-coded rules first (v12 trips_pair → v10
two_pair → v9.2 single-pair), then v16_dt as fallback.

Hypothesis: the v9.2/v10/v12 rules are interpretable and the rules' ranges
are tight; on the firing hands, they may agree with v16, and on
disagreements ground-truth EV will decide via the grader.

If v17 grades at least as good as v16 alone, it's a win for two reasons:
1. Coverage shifts toward the human-memorizable chain on the firing hands.
2. The DT only acts as a fallback for the un-ruled categories.

If v17 grades WORSE than v16, the v16 leaf-EV vec disagrees with the rules
on enough firing hands that the rule's interpretability isn't free. Either
way the result is informative.

Drop-in replacement for v14_combined / v16_dt as a candidate strategy.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v9_2_pair_to_bot_ds import _detect_v9_2_setting  # noqa: E402
from strategy_v10_two_pair_no_split import _detect_v10_two_pair_setting  # noqa: E402
from strategy_v12_trips_pair import _detect_v12_trips_pair_setting  # noqa: E402
from strategy_v16_dt import strategy_v16_dt  # noqa: E402


def strategy_v17_rules_then_dt(hand: np.ndarray) -> int:
    chosen = _detect_v12_trips_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v10_two_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_v9_2_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v16_dt(hand))
