"""strategy_v65 — v64 + v60-gate12 (MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q).

Production-chain ship from Session 93.

v64 fires on HIGH_ONLY × max ∈ {8..A} × 6 audited cells, routing those hands
to v44_dt (the chain-audit zone gate from S87-S90).

v60-gate12 fires on MID pair (rank 8-T) × PMID_DS_NOMAXTOP × max_sing ≤ Q
× v57-pick-is-PMID_tmax-style, forcing the best PMID_tnomax_DS configuration.

The two firing zones are DISJOINT by construction:
  - v64's zone requires HIGH_ONLY = no pairs in the hand.
  - v60's zone requires exactly one MID pair (rank 8-T).
So composition is additive: whole-grid lift v65 vs v64 = v60's lift over v57
on its changed-hand subset.

Validation history:
  S86 N=200: gate=12 lift +$6.43/1000h (SHIP by full-grid bar), but prefix
    N=1000 grid silent (cell cid_min 593,072 outside prefix [0, 500K)).
    Status: MIXED-by-methodology, unshipped.
  S93 N=1000 (Option C infrastructure — engine --id-list-file): lift on
    32,304 changed hands at N=1000 = +$6.34/1000h. Two-grid SHIP standard
    cleared (both N=200 and N=1000 ≥ $5).

  Expected v65 production: $1,627.36 + $6.43 ≈ $1,633.79/1000h whole-grid
  N=200. Confirmed by grade_v65_S93.py.

USAGE
-----
    from strategy_v65_mid_pair_chain_extend import (
        strategy_v65_mid_pair_chain_extend,
    )
    idx = strategy_v65_mid_pair_chain_extend(hand_bytes)

Self-test:
    python3 analysis/scripts/strategy_v65_mid_pair_chain_extend.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
for p in (str(SRC), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v64_high_only_chain_fix_zone import (  # noqa: E402
    _is_v64_gated_cell,
)
from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v60_mid_pair_ds_nomaxtop import (  # noqa: E402
    _detect_mid_pair_defensive_pmid_swap,
)

# Gate locked from S93 validation. Do NOT change without re-grading on both
# grids — see Decision 128.
V65_MID_PAIR_GATE = 12


def strategy_v65_mid_pair_chain_extend(hand: np.ndarray) -> int:
    """v65 = v64 (HIGH_ONLY chain-audit zone) + v60-gate12 (MID pair × PMID_DS_NOMAXTOP).

    Order:
      1. If hand falls inside v64's HIGH_ONLY chain-audit gate → v44_dt.
      2. Else, if hand fires v60's MID-pair PMID_DS_NOMAXTOP rule at gate=Q
         AND v57's current pick is PMID_tmax-style → forced PMID_tnomax_DS.
      3. Else → v57 (LOW pair defensive + chain fallthrough).

    Firing zones (1) and (2) are disjoint (HIGH_ONLY has no pair; v60's zone
    requires exactly one MID pair), so order is illustrative only — either
    ordering produces identical picks.
    """
    if _is_v64_gated_cell(hand):
        return int(strategy_v44_dt(hand))
    v57_pick = int(strategy_v57_lo_pair_defensive(hand))
    forced = _detect_mid_pair_defensive_pmid_swap(
        hand, V65_MID_PAIR_GATE, v57_pick=v57_pick
    )
    if forced is not None:
        return int(forced)
    return v57_pick


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand  # noqa: E402

    from strategy_v64_high_only_chain_fix_zone import (
        strategy_v64_high_only_chain_fix_zone,
    )

    cases = [
        # HIGH_ONLY in v64 gate — v65 should match v64 (= v44_dt)
        ("Kc Qd 9c 8h 7h 6d 4s", "v64-gated HIGH_ONLY"),
        # MID pair × PMID_DS_NOMAXTOP × max=J — v65 should match v60-gate12
        ("8c 8d Jh 7h 6s 5s 4c", "MID pair 8, max=J, PMID_DS_NOMAXTOP"),
        # MID pair × PMID_DS_NOMAXTOP × max=A (above gate=12) — v65 falls through to v57
        ("8c 8d Ah 7h 6s 5s 4c", "MID pair 8, max=A (above gate) — v57"),
        # LOW pair — v65 = v57
        ("3c 3d Jh 7h 6s 5s 4c", "LOW pair — v57"),
        # HIGH pair — v65 = v57
        ("Jc Jd 8h 7h 6s 5s 4c", "HIGH pair — v57"),
        # No pair, not in v64 gate
        ("Ah Kh Qh Jh Th 9h 2c", "no pair high-card — likely v57 (Royal flush)"),
    ]
    print("v65 sanity tests:")
    for hstr, desc in cases:
        cards = parse_hand(hstr)
        h = np.array([c.idx for c in cards], dtype=np.uint8)
        v44 = int(strategy_v44_dt(h))
        v57 = int(strategy_v57_lo_pair_defensive(h))
        v64 = int(strategy_v64_high_only_chain_fix_zone(h))
        v65 = int(strategy_v65_mid_pair_chain_extend(h))
        in_v64_gate = _is_v64_gated_cell(h)
        print(
            f"  {desc}:"
            f"\n    v44={v44} v57={v57} v64={v64} v65={v65}"
            f"  v64_gated={in_v64_gate}"
            f"  v64==v65: {v64 == v65}"
        )
