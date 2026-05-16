"""strategy_v64 — full HIGH_ONLY × max ≥ 8 chain gate-out (zone-wide).

Project history:
  S87 (v61) gated DS_NO_JOINT × {J-A}: +$98.67/1000h.
  S88 (v62) extended to DS_NO_MAXTOP / MS_ONLY / JOINT_HIGH × {J-A}: +$98.84.
  S89 (v63) closed remaining HIGH_ONLY × {J-A} cells (JOINT_MED + JOINT_LOW): +$10.09.
  S90 (v64) pivots to max ∈ {8, 9, T} and extends the gate further:

  Cell × rank                        n_target   v63→v52 chain bleed (per S90 audit)
  -----------------------------------  --------  -----------------------------------
  HIGH_ONLY × JOINT_MED × {9, T}        3,150    +$1.35/1000h
  HIGH_ONLY × JOINT_LOW × {8, 9, T}       630    +$0.31/1000h
  HIGH_ONLY × DS_NO_JOINT × {8, 9, T}  16,200    +$3.75/1000h
  HIGH_ONLY × DS_NO_MAXTOP × {8, 9, T}  3,456    +$0.92/1000h
  HIGH_ONLY × MS_ONLY × {8, 9, T}       2,304    +$0.90/1000h
  -----------------------------------  --------  -----------------------------------
  TOTAL                                25,740    +$7.23/1000h

S90 layer attribution:
  v44→v47:  +$19.28 (v47 introduces bleed, same as S87/S88/S89)
  v47→v48:  −$2.53  (small improvement)
  v48→v52:  −$9.52  (v52-defensive-low recovers ~50% of v47 bleed, but only partial)
  Net:      +$7.23  (residual bleed v44 lacks)

All 25,740 S90 target hands route through v52-defensive-low (LOW_MAX_DEFENSIVE
= {7,8,9,10}). This is the FIRST audit of v52-defensive-low. Verdict: it
partially mitigates v47's bleed but does not fully recover to v44_dt levels.
Same architectural mechanism as S87/S88/S89; gate-out is the right move.

STRUCTURAL FEASIBILITY (no compute needed):
  - HIGH_ONLY × max=7 × any cell: EMPTY. HIGH_ONLY requires 7 distinct ranks;
    only 6 ranks ≤ 7 exist (2-7). Aces always counted as 14 in the cell taxonomy.
  - HIGH_ONLY × max=8 × JOINT_MED: EMPTY. JOINT_MED needs mid_high ≥ 8 > max-1 = 7.
  - HIGH_ONLY × {8,9,T} × JOINT_HIGH: EMPTY. JOINT_HIGH needs mid_high ≥ J > T-1 = 9.
  - HIGH_ONLY × {8,9,T} × NEITHER: EMPTY (pigeonhole — same as {J-A}).

So v64's gate covers the entire structurally-non-empty HIGH_ONLY × {8,9,T}
population.

Combined with v63's gates on {J-A}, v64 effectively gates the entire
non-trivial HIGH_ONLY zone (max ≥ 8). All HIGH_ONLY hands with addressable
structure route through v44_dt; v52 is fully bypassed on this population.

USAGE
-----
    from strategy_v64_high_only_chain_fix_zone import (
        strategy_v64_high_only_chain_fix_zone,
    )
    idx = strategy_v64_high_only_chain_fix_zone(hand_bytes)

Self-test:
    python3 analysis/scripts/strategy_v64_high_only_chain_fix_zone.py
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

from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v63_high_only_chain_fix_full import (  # noqa: E402
    strategy_v63_high_only_chain_fix_full,
    _classify_high_only_cell,
)
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)

# v64's gate covers:
#   - All of v63's gate (HIGH_ONLY × {J-A} × all 6 non-empty cells)
#   - Plus HIGH_ONLY × {8, 9, T} × {JOINT_MED, JOINT_LOW, DS_NO_JOINT,
#                                   DS_NO_MAXTOP, MS_ONLY}
# JOINT_HIGH and NEITHER are structurally empty for max ≤ T, so listing the
# 5 cells below is exhaustive at max ≤ T.

V64_TARGET_MAX_RANKS = frozenset({8, 9, 10, 11, 12, 13, 14})
V64_TARGET_CELLS = frozenset({"DS_NO_JOINT", "DS_NO_MAXTOP", "MS_ONLY",
                              "JOINT_HIGH", "JOINT_MED", "JOINT_LOW"})


def _is_v64_gated_cell(hand: np.ndarray) -> bool:
    """v64 gate: HIGH_ONLY × max ∈ {8..A} × cell ∈ all 6 audited cells."""
    cell, max_rank = _classify_high_only_cell(hand)
    if cell is None:
        return False
    if max_rank not in V64_TARGET_MAX_RANKS:
        return False
    return cell in V64_TARGET_CELLS


def strategy_v64_high_only_chain_fix_zone(hand: np.ndarray) -> int:
    """Return v44_dt pick when hand is in the v64-gated cell set; else v57.

    Equivalent to: v64 == v44_dt on gated cells; v64 == v57 elsewhere.
    Strict superset of v63's gate (v63 covered max ∈ {J-A}; v64 also covers
    max ∈ {8, 9, T}).
    """
    if _is_v64_gated_cell(hand):
        return int(strategy_v44_dt(hand))
    return int(strategy_v57_lo_pair_defensive(hand))


if __name__ == "__main__":
    # Self-tests
    from tw_analysis.settings import parse_hand  # noqa: E402

    cases = [
        # (hand_str, expected_in_gate, description)
        ("Kc Qd 9c 8h 7h 6d 4s", True,
         "K-high DS_NO_JOINT — v63 gated, still v64 gated"),
        ("Tc 9d 7h 6c 5h 3d 2s", True,
         "T-high — NEW v64 territory (max=T → v52-defensive-low fires; v64 gates)"),
        ("9c 8d 7h 5s 4c 3h 2d", True,
         "9-high — NEW v64 territory (max=9 → v52-defensive-low; v64 gates)"),
        ("8c 7d 6h 5s 4c 3h 2d", True,
         "8-high HIGH_ONLY — NEW v64 territory (max=8 → v52-defensive-low; v64 gates)"),
        ("Kc 5d 5h 9c 8h 7d 4s", False,
         "K-high but has a pair — NOT HIGH_ONLY"),
        ("7c 6d 5h 4c 3h 2d", False,
         "Only 6 cards — not a valid HIGH_ONLY hand"),
    ]
    print("Sanity tests:")
    for hstr, expected, desc in cases:
        cards = parse_hand(hstr)
        h = np.array([c.idx for c in cards], dtype=np.uint8)
        if h.shape[0] != 7:
            in_gate = _is_v64_gated_cell(h)
            marker = "OK " if in_gate == expected else "FAIL"
            print(f"  [{marker}] {desc}")
            print(f"      hand={hstr!r}  size={h.shape[0]} "
                  f"in_v64_gate={in_gate} (expected {expected})")
            continue
        cell, max_rank = _classify_high_only_cell(h)
        in_gate = _is_v64_gated_cell(h)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        v63_pick = int(strategy_v63_high_only_chain_fix_full(h))
        v64_pick = int(strategy_v64_high_only_chain_fix_zone(h))
        v44_pick = int(strategy_v44_dt(h))
        marker = "OK " if in_gate == expected else "FAIL"
        print(f"  [{marker}] {desc}")
        print(f"      hand={hstr!r}  cell={cell} max={max_rank}  "
              f"in_v64_gate={in_gate} (expected {expected})")
        if in_gate:
            same = "v64==v44" if v64_pick == v44_pick else "v64!=v44 (?!)"
            new_vs_v63 = "(NEW gate vs v63)" if (v63_pick != v64_pick) else "(already gated under v63)"
            print(f"      v44={v44_pick} v57={v57_pick} v63={v63_pick} "
                  f"v64={v64_pick}  {same}  {new_vs_v63}")
        else:
            same = "v64==v57" if v64_pick == v57_pick else "v64!=v57 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v63={v63_pick} "
                  f"v64={v64_pick}  {same}")
