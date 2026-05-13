"""
v56 — v55 + blanket trips routing to v44_dt.

Path B (hybrid chain extension) per TRIPS_DECISION_MATRIX.md:
  - trips hands → route to strategy_v44_dt
  - All other hands → route to strategy_v55_two_pair_hybrid (which itself
    routes two_pair → v44, single-pair PBOT → v44 via v54, all else →
    v53 → v52)

Rationale (S70 finding): v55 (= v52 on trips, since neither v55's two_pair
gate nor v54's pair gate fires on trips, and Rule 19 in v53 is
single-pair-only) underperforms v44 by $44.61/1000h whole-grid on trips.
At the cell aggregate, every cell favors v44; tiny counter-headroom of
$0.75 WG exists at B_DS_AVAIL_HKR for ranks {K,J,T,4,3} but is dwarfed
by the $44 WG gain in the other cells. Per S69 lesson, all 4 tested
catalog candidates were DOMINATED BY V44 (3 of 4 lose to v55 too); the
hybrid is the only meaningful ship path.

Expected impact (per TRIPS_DECISION_MATRIX.md Phase 2 sizing):
  - Within-trips full-grid lift: $44.61 WG (canonical-equal framing).
  - Predicted v56 vs v55 lift: $44 WG full-grid; ~$20 WG prefix-grid.
  - Within-trips pct_opt: 36.7% → 57.1% (+20.4 pp).
  - Two-track divergence v56 vs v44_dt: closes another ~$44 WG of the
    $393 WG gap remaining post-S69.
  - NOT a new project record (S69's +$634 still holds). This is the
    smallest hybrid ship of the methodology arc — but cleanly closes
    trips as a production target.

Trade-off accepted: production rule chain now COMMITS to v44_dt for
trips (in addition to two_pair via v55 and pair PBOT cells via v54).
Future ML retrain shifts v44 (and via v54+v55+v56, the whole chain).

Routing gate (single binary check):
  exactly_one_trip AND no_pairs AND no_quads
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

from strategy_v55_two_pair_hybrid import strategy_v55_two_pair_hybrid  # noqa: E402
from strategy_v44_dt import strategy_v44_dt  # noqa: E402


def _is_trips(hand_bytes: np.ndarray) -> bool:
    """Return True iff hand is a pure trips hand (exactly 1 trip rank,
    no pairs, no quads).
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) != 0:
        return False
    if int((rc == 3).sum()) != 1:
        return False
    if int((rc == 2).sum()) != 0:
        return False
    return True


def strategy_v56_trips_hybrid(hand: np.ndarray) -> int:
    """v56 — v55 + trips routing to v44_dt."""
    if _is_trips(hand):
        return int(strategy_v44_dt(hand))
    return int(strategy_v55_two_pair_hybrid(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    test_cases = [
        # Trips → expect v44
        ("Ac Ad As Kh 8d 5c 2h", "v44 (trip A)"),
        ("Tc Td Th 9c 8d 7s 6h", "v44 (trip T)"),
        ("5c 5d 5h Ah 9c 7c 3d", "v44 (trip 5)"),
        # Two_pair → v55 (routes to v44 inside v55's two_pair gate)
        ("Ac Ad Kh Ks 8h 5d 2c", "v55 (AAKK two_pair) → v44 inside v55"),
        # Single-pair PBOT → v55 → v54 → v44 (pair gate)
        ("Qc Qd 2h 3h 4d Jc Kh", "v55 → v54 (Q-pair PBOT_DS) → v44"),
        # Single-pair PMID-only → v55 → v54 → v53 → v52
        ("9c 9h 4d 5d Td Jd Qd", "v55 → v54 (9-pair no PBOT_DS)"),
        # High_only → v55 → v54 → v52
        ("As Kh Qd Jc 8s 5h 2c", "v55 → v54 (high_only)"),
        # Three_pair → v55 → v54 → v52
        ("Ac Ad Kh Ks 7d 7s 2c", "v55 (three_pair — not trips)"),
        # Trips_pair → v55 → v54 → v52 (NOT trips per pure-trips definition)
        ("Ac Ad As Kh Kd 8d 5c", "v55 (trips_pair — has 1 pair, fails _is_trips)"),
    ]
    for s, expected in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        is_tr = _is_trips(h)
        v55_pick = strategy_v55_two_pair_hybrid(h)
        v56_pick = strategy_v56_trips_hybrid(h)
        v44_pick = strategy_v44_dt(h) if is_tr else None
        print(f"  hand={s}")
        print(f"    expected route: {expected}")
        print(f"    is_trips: {is_tr}")
        print(f"    v55 pick: {v55_pick}  v56 pick: {v56_pick}  "
              f"v44 pick: {v44_pick if v44_pick is not None else '-'}")
        if is_tr:
            assert v56_pick == v44_pick, f"routing bug: v56 != v44 on trips hand"
        else:
            assert v56_pick == v55_pick, f"routing bug: v56 != v55 on non-trips hand"
        print(f"    routing: OK")
    print("\nAll smoke tests passed.")
