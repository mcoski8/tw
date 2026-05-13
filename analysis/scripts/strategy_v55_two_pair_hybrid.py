"""
v55 — v54 + blanket two_pair routing to v44_dt.

Path B (hybrid chain extension) per TWO_PAIR_DECISION_MATRIX.md:
  - two_pair hands → route to strategy_v44_dt
  - All other hands → route to strategy_v54_pair_hybrid (which itself
    routes pair PBOT cells → v44, all else → v53 → v52)

Rationale (S69 finding): v54 (= v52 on two_pair, since the v54 pair-hybrid
gate is single-pair-only and Rule 19 in v53 is single-pair-only too)
underperforms v44 by $634/1000h whole-grid on two_pair. UNLIKE pair, every
single two_pair structural cell favors v44 — there is NO PMID-style
counter-headroom. So the routing simplifies to a single binary check:
"is hand two_pair? → v44; else → v54".

Expected impact (per TWO_PAIR_DECISION_MATRIX.md Phase 2 sizing):
  - Within-two_pair full-grid lift: $634 WG (canonical-equal framing).
  - Predicted v55 vs v54 lift: $634 WG full-grid; ~$300 WG prefix-grid.
  - Within-two_pair pct_opt: 44% → 83% (+39 pp).
  - Two-track divergence v55 vs v44_dt: closes another ~$634 WG of the
    $1,027 WG gap remaining post-S68.
  - **NEW PROJECT RECORD:** ~1.7× S68's v54 ship of $382.

Trade-off accepted: production rule chain now COMMITS to v44_dt for
two_pair (in addition to pair PBOT cells from v54). Future ML retrain
shifts both v44 and v55.

Routing gate (single binary check):
  exactly_two_distinct_pairs AND no_quads AND no_trips
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

from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid  # noqa: E402
from strategy_v44_dt import strategy_v44_dt  # noqa: E402


def _is_two_pair(hand_bytes: np.ndarray) -> bool:
    """Return True iff hand is a two_pair hand (exactly 2 pairs, no
    trips/quads).
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) != 0:
        return False
    if int((rc == 3).sum()) != 0:
        return False
    if int((rc == 2).sum()) != 2:
        return False
    return True


def strategy_v55_two_pair_hybrid(hand: np.ndarray) -> int:
    """v55 — v54 + two_pair routing to v44_dt."""
    if _is_two_pair(hand):
        return int(strategy_v44_dt(hand))
    return int(strategy_v54_pair_hybrid(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    test_cases = [
        # Two_pair → expect v44
        ("Ac Ad Kh Ks 8h 5d 2c", "v44 (AAKK two_pair)"),
        ("8c 8d 9h 9s 2c 5d Tc", "v44 (8899 two_pair)"),
        ("Tc Td 2h 2s Ah 5d Qc", "v44 (TT22 two_pair)"),
        # Single-pair PBOT → v54 (which routes to v44 via pair gate)
        ("Qc Qd 2h 3h 4d Jc Kh", "v54 (Q-pair PBOT_DS) → v44 inside v54"),
        # Single-pair PMID-only → v54 (which routes to v53 → v52 → v47…)
        ("9c 9h 4d 5d Td Jd Qd", "v54 (9-pair no PBOT_DS)"),
        # High_only → v54 → v52
        ("As Kh Qd Jc 8s 5h 2c", "v54 (high_only)"),
        # Trips → v54 → v52
        ("Ac Ad As Kh 8d 5c 2h", "v54 (trips)"),
        # Three_pair → v54 → v52
        ("Ac Ad Kh Ks 7d 7s 2c", "v54 (three_pair) — gated out of two_pair"),
    ]
    for s, expected in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        is_tp = _is_two_pair(h)
        v54_pick = strategy_v54_pair_hybrid(h)
        v55_pick = strategy_v55_two_pair_hybrid(h)
        v44_pick = strategy_v44_dt(h) if is_tp else None
        print(f"  hand={s}")
        print(f"    expected route: {expected}")
        print(f"    is_two_pair: {is_tp}")
        print(f"    v54 pick: {v54_pick}  v55 pick: {v55_pick}  "
              f"v44 pick: {v44_pick if v44_pick is not None else '-'}")
        if is_tp:
            assert v55_pick == v44_pick, f"routing bug: v55 != v44 on two_pair hand"
        else:
            assert v55_pick == v54_pick, f"routing bug: v55 != v54 on non-two_pair hand"
        print(f"    routing: OK")
    print("\nAll smoke tests passed.")
