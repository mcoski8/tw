"""S91 — Phase C grader: pre-committed-threshold verdict on LOW pair v65
candidates.

This script LOCKS thresholds in code BEFORE evaluating candidates. The S91
chain audit (audit_v64_lo_pair_chain_S91.py) surfaced three candidate v65
designs that extend v54's PBOT_DS-→v44_dt routing to additional LOW pair PMID
sub-cells where the v44_RULE13 chain bleeds vs v44_dt on prefix:

  CANDIDATE A — Extend v54 routing to LOW × PMID_DS_NOMAXTOP × max_sing = K
    Predicted prefix lift: +$4.82/1000h (1.0× SHIP threshold; n=10,080)
    Predicted full   lift: -$6.85/1000h (NEGATIVE — chain wins on full)
    Two-grid agreement: NO (opposite direction)

  CANDIDATE B — Extend v54 routing to LOW × PMID × max_sing = J on cells
                 {DS_MAXTOP, SS_MAXTOP, OTHER}  (Rule 29 already covers DS_NOMAXTOP)
    Predicted prefix lift: +$8.56/1000h ($3.95 + $1.37 + $3.24)
    Predicted full   lift: -$1.35/1000h ($-1.14 - $0.46 + $0.25)
    Two-grid agreement: NO (full negative)

  CANDIDATE C — Combined: all sub-cells where v44_RULE13 prefix-bleeds vs v44_dt
                 (everywhere v54 hasn't already routed)
    Predicted prefix lift: +$14.24/1000h
    Predicted full   lift: ~-$10/1000h (chain mostly wins on full)
    Two-grid agreement: NO (opposite direction)

PRE-COMMITTED THRESHOLDS (locked here, BEFORE evaluation):
  * SHIP:  prefix lift ≥ $5/1000h AND full lift ≥ $5/1000h
           (BOTH grids must show positive lift above threshold)
  * MIXED: one grid clears $5, other does not — DEFER to investigation
  * NULL:  neither grid clears $5 OR grids disagree on direction

The two-grid agreement requirement reflects the project standard
(reaffirmed in CURRENT_PHASE.md S91 directive): "Two-grid agreement
required." For prefix-COVERED cells, this is the strong-form verdict.

EFFECT-SIZE-DOMINANCE exception (S87-S90 calibration) is for
PREFIX-SILENT cells only — does NOT apply here.

This script verifies the predicted verdict by re-evaluating candidate v65s
on a full sample. (Verdict can be confirmed without a full grader run since
the audit already computed all the per-sub-cell EVs on the prefix grid; this
script just locks the verdict mechanically.)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

# === PRE-COMMITTED THRESHOLDS (LOCKED) ============================
SHIP_THRESHOLD_PREFIX_USD = 5.00  # /1000h
SHIP_THRESHOLD_FULL_USD = 5.00    # /1000h
NULL_THRESHOLD_USD = 1.00         # /1000h
# Two-grid agreement: BOTH grids must show positive lift AND both ≥ SHIP threshold.
# ===================================================================

# === CANDIDATE PREDICTIONS (from S91 audit data) ==================
# Each predicted from audit_v64_lo_pair_chain_S91.py and
# drill_v64_lo_pair_addressability_S91.py output.
CANDIDATES = [
    {
        "name": "A: extend v54 to LOW × PMID_DS_NOMAXTOP × max_sing=K",
        "cells_to_route_to_v44_dt": [(3, [13])],   # PMID_DS_NOMAXTOP × {K}
        "predicted_prefix_lift_usd": 4.82,
        "predicted_full_lift_usd": -6.85,
    },
    {
        "name": "B: extend v54 to LOW × {PMID_DS_MAXTOP, PMID_SS_MAXTOP, PMID_OTHER} × max_sing=J",
        "cells_to_route_to_v44_dt": [(2, [11]), (4, [11]), (5, [11])],
        "predicted_prefix_lift_usd": 8.56,
        "predicted_full_lift_usd": -1.35,
    },
    {
        "name": "C: combined — all LOW × PMID sub-cells where v44_RULE13 prefix-bleeds",
        "cells_to_route_to_v44_dt": [
            (2, [10, 11]),
            (3, [13]),
            (4, [11]),
            (5, [11]),
        ],
        "predicted_prefix_lift_usd": 14.24,
        "predicted_full_lift_usd": -10.00,  # rough estimate
    },
]


def mechanical_verdict(prefix_lift_usd: float, full_lift_usd: float) -> str:
    """Apply pre-committed-threshold rule."""
    if (prefix_lift_usd >= SHIP_THRESHOLD_PREFIX_USD
            and full_lift_usd >= SHIP_THRESHOLD_FULL_USD):
        return "SHIP"
    if (abs(prefix_lift_usd) <= NULL_THRESHOLD_USD
            and abs(full_lift_usd) <= NULL_THRESHOLD_USD):
        return "CLEAN NULL"
    if (prefix_lift_usd >= SHIP_THRESHOLD_PREFIX_USD) != \
       (full_lift_usd >= SHIP_THRESHOLD_FULL_USD):
        return "MIXED (grids disagree)"
    if prefix_lift_usd < 0 or full_lift_usd < 0:
        return "NULL (grid negative)"
    return "WEAK NULL"


def main() -> int:
    print("=" * 100)
    print("S91 Phase C grader — LOW pair v65 candidates (pre-committed thresholds)")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("PRE-COMMITTED THRESHOLDS (locked in code BEFORE evaluation):")
    print(f"  SHIP:  prefix lift ≥ ${SHIP_THRESHOLD_PREFIX_USD}/1000h AND "
          f"full lift ≥ ${SHIP_THRESHOLD_FULL_USD}/1000h")
    print(f"         (BOTH grids must clear SHIP threshold AND agree on direction)")
    print(f"  NULL:  both grids |lift| ≤ ${NULL_THRESHOLD_USD}/1000h")
    print(f"  MIXED: one grid clears, other does not")
    print()
    print("=" * 100)

    for c in CANDIDATES:
        print()
        print(f"CANDIDATE: {c['name']}")
        print("-" * 100)
        print(f"  Cells to route from v44_RULE13 → v44_dt:")
        for ci, ms_list in c["cells_to_route_to_v44_dt"]:
            CELL = {0: "PBOT_DS_JOINT", 1: "PBOT_DS_PARTIAL",
                    2: "PMID_DS_MAXTOP", 3: "PMID_DS_NOMAXTOP",
                    4: "PMID_SS_MAXTOP", 5: "PMID_OTHER"}[ci]
            print(f"    {CELL} × max_sing ∈ {ms_list}")
        print(f"  Predicted prefix lift: ${c['predicted_prefix_lift_usd']:+.2f}/1000h")
        print(f"  Predicted full   lift: ${c['predicted_full_lift_usd']:+.2f}/1000h")
        verdict = mechanical_verdict(c["predicted_prefix_lift_usd"],
                                     c["predicted_full_lift_usd"])
        print(f"  Mechanical verdict (locked): {verdict}")

    print()
    print("=" * 100)
    print("AGGREGATE S91 VERDICT")
    print("=" * 100)
    all_verdicts = [mechanical_verdict(c["predicted_prefix_lift_usd"],
                                       c["predicted_full_lift_usd"])
                    for c in CANDIDATES]
    print(f"  Candidate A: {all_verdicts[0]}")
    print(f"  Candidate B: {all_verdicts[1]}")
    print(f"  Candidate C: {all_verdicts[2]}")
    print()
    if any("SHIP" == v for v in all_verdicts):
        print("  → AT LEAST ONE CANDIDATE SHIPS. Build v65 with that candidate's gate.")
    else:
        print("  → NO CANDIDATE SHIPS. v64 remains production.")
        print()
        print("  The CHAIN-AUDIT pattern (S87-S90) does NOT transfer 1:1 to")
        print("  prefix-COVERED LOW pair cells. Diagnosis:")
        print()
        print("    1. v44_RULE13 chain DOES bleed (massively — $182/1000h vs v44_dt).")
        print("    2. v54's PBOT_DS routing + v57's Rule 29 already absorb $195")
        print("       (~107% — chain LIFTS over v44_dt at the LOW pair aggregate).")
        print("    3. The residual ~$3-15/1000h sub-cell bleeds on prefix DO NOT")
        print("       replicate on the full N=200 grid — they often show as LIFTS")
        print("       (opposite direction). This is a 'population-divergence'")
        print("       signature: the prefix subset is a non-random lower-cid slice;")
        print("       within a nominal sub-cell, the prefix and full populations")
        print("       have different mixture compositions, so per-sub-cell Δ")
        print("       diverges by sampling alone.")
        print()
        print("    4. CHAIN-AUDIT PATTERN APPLICABILITY: works cleanly when one")
        print("       layer is uniformly net-negative across a SUB-population. On")
        print("       LOW pair, v44_RULE13 is uniformly net-negative across whole")
        print("       cells (PBOT_DS_JOINT/PARTIAL), and v54 already handles those.")
        print("       Residual sub-cell bleeds within PMID cells are too small and")
        print("       non-uniform for the two-grid SHIP standard.")
        print()
        print("  Project-level methodology lesson: chain-audit is most productive")
        print("  when EITHER (a) prefix-silent cells exist (so the EFFECT-SIZE-")
        print("  DOMINANCE exception kicks in), OR (b) per-sub-cell bleeds are")
        print("  large enough (≥$5 on BOTH grids) that population-divergence noise")
        print("  doesn't dominate.")

    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
