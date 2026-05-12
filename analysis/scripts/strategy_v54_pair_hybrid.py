"""
v54 — v53 + cell-routed pair PBOT delegation to v44_dt.

Path B (hybrid chain) per PAIR_DECISION_MATRIX.md Recommendation:
  - Pair hands with PBOT_DS achievable (= PBOT_DS_JOINT or PBOT_DS_PARTIAL
    cell in the S66 6-cell taxonomy) → route to v44_dt.
  - All other hands (pair PMID_* cells AND all non-pair categories) →
    route to v53 (= v52 + Rule 19).

Rationale (S67 finding): v52 underperforms v44 by $341/1000h on pair,
concentrated entirely in PBOT cells ($391 WG gap; PMID cells favor v52
by $50). 11 of 12 blanket-PBOT rule candidates tested in S67 are T3
net-negative because the headroom requires v44's selective per-hand
gating (107 features), not a rule-chain decision. The hybrid bypasses
the rule-chain selectivity problem by delegating those cells to v44
directly.

Expected impact (per PAIR_DECISION_MATRIX.md Path B sizing):
  - Hybrid pair residual: v44_PBOT $215 + v52_PMID $246 = $461 WG.
  - v53 pair residual:    $852 WG (= v52 $852 − Rule 19's $9 lift,
                                 but lift is concentrated in Q-pair JOINT).
  - Expected lift vs v53: ~$382 WG on pair = ~+$190-390/1000h whole-grid
    depending on Rule 19 overlap (PBOT_DS_JOINT cells re-routed through
    v44 may differ from Rule 19's pick).

Trade-off accepted: production rule chain now COMMITS to v44_dt for
pair PBOT cells. Future ML retrain shifts both v44 and v54.

Routing gate (single check, no full cell taxonomy needed since PMID + non-pair
share the same target):
  exactly_one_pair AND no_quads AND no_trips AND pair_has_two_distinct_suits
  AND at_least_one_PBOT_DS_config_feasible
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v53_qpair_joint_pbot import strategy_v53_qpair_joint_pbot  # noqa: E402
from strategy_v44_dt import strategy_v44_dt  # noqa: E402


def _is_pair_with_pbot_ds_feasible(hand_bytes: np.ndarray) -> bool:
    """Return True iff hand is a single-pair hand AND at least one pair-to-bot
    DS configuration exists (= bot can be constructed as pair + 1 singleton of
    each pair-suit, yielding a 2+2 DS suit pattern).

    Mirrors the PBOT_DS achievability check in drill_pair_v44_S66's
    compute_pair_structural — but only computes the boolean, not the full
    cell taxonomy. PMID cells route to v53 anyway, so we don't distinguish
    them.
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    # Strict single-pair gate (excludes two_pair, trips, three_pair, quads,
    # trips_pair, composite — those go to v53).
    if int((rc == 4).sum()) != 0:
        return False
    if int((rc == 3).sum()) != 0:
        return False
    if int((rc == 2).sum()) != 1:
        return False
    pair_rank = int(np.argmax(rc == 2))
    pair_pos = [i for i in range(7) if int(ranks[i]) == pair_rank]
    if len(pair_pos) != 2:
        return False
    sa = int(suits[pair_pos[0]])
    sb = int(suits[pair_pos[1]])
    if sa == sb:
        return False  # pair shares suit — cannot anchor a DS bot
    # Need at least one non-pair singleton of suit sa AND at least one of suit sb.
    sing_pos = [i for i in range(7) if i not in pair_pos]
    n_sa = sum(1 for i in sing_pos if int(suits[i]) == sa)
    n_sb = sum(1 for i in sing_pos if int(suits[i]) == sb)
    return n_sa >= 1 and n_sb >= 1


def strategy_v54_pair_hybrid(hand: np.ndarray) -> int:
    """v54 — cell-routed hybrid.

    If hand is a pair with PBOT_DS achievable → v44_dt (selective ML).
    Else → v53 (= v52 + Rule 19 Q-pair JOINT PBOT-DS).
    """
    if _is_pair_with_pbot_ds_feasible(hand):
        return int(strategy_v44_dt(hand))
    return int(strategy_v53_qpair_joint_pbot(hand))


if __name__ == "__main__":
    # Smoke tests covering the three routing paths.
    from tw_analysis.settings import parse_hand
    test_cases = [
        # Pair PBOT_DS-feasible → expect v44 routing
        ("Qc Qd 2h 3h 4d Jc Kh", "v44 (Q-pair PBOT_DS feasible)"),
        # Pair PMID-only (no PBOT_DS — pair shares suit) → expect v53
        ("6c 6h 8c Td Jc Qd Kh", "v44 (PBOT_DS feasible: 6c/6h with suit-c + suit-h sings)"),
        # Pair no PBOT_DS (singletons don't include both pair suits) → expect v53
        ("9c 9h 4d 5d Td Jd Qd", "v53 (9-pair but no suit-c singletons)"),
        # High-only (no pair) → expect v53
        ("As Kh Qd Jc 8s 5h 2c", "v53 (high_only — no pair)"),
        # Two pair → expect v53
        ("8c 8d 9h 9s 2c 5d Tc", "v53 (two_pair — gated out)"),
    ]
    for s, expected in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        is_pbot = _is_pair_with_pbot_ds_feasible(h)
        v53_pick = strategy_v53_qpair_joint_pbot(h)
        v54_pick = strategy_v54_pair_hybrid(h)
        v44_pick = strategy_v44_dt(h) if is_pbot else None
        print(f"  hand={s}")
        print(f"    expected route: {expected}")
        print(f"    is_pair_pbot_ds_feasible: {is_pbot}")
        print(f"    v53 pick: {v53_pick}  v54 pick: {v54_pick}  "
              f"v44 pick: {v44_pick if v44_pick is not None else '-'}")
        if is_pbot:
            assert v54_pick == v44_pick, f"routing bug: v54 != v44 on PBOT-feasible hand"
        else:
            assert v54_pick == v53_pick, f"routing bug: v54 != v53 on non-PBOT hand"
        print(f"    routing: OK")
    print("\nAll smoke tests passed.")
