"""S92 — Phase C grader: pre-committed-threshold verdict on two_pair + trips
v65 candidates from the chain audit.

This script LOCKS thresholds in code BEFORE evaluation. The S92 chain audit
(audit_v64_two_pair_chain_S92.py + audit_v64_trips_chain_S92.py) surfaced a
structural finding: v55_two_pair_hybrid blanket-routes ALL two_pair → v44_dt,
and v56_trips_hybrid blanket-routes ALL trips → v44_dt. Therefore:

  * Production v64 ≡ v44_dt on every two_pair hand.
  * Production v64 ≡ v44_dt on every trips hand.
  * Δ(v64 − v44_dt) = $0.00 on every (cell × sub-cell) within two_pair
    and trips.

There are NO chain-residual sub-cells where the chain layer bleeds vs
v44_dt under production picks — because production picks ARE v44_dt's
picks. The chain-audit pattern (find a layer that bleeds vs v44_dt, gate
it out) cannot produce a SHIP candidate within these categories.

  ZERO chain-audit v65 candidates exist for two_pair OR trips.

PRE-COMMITTED THRESHOLDS (LOCKED, identical to S91):
  * SHIP:  prefix lift ≥ $5/1000h AND full lift ≥ $5/1000h (both grids,
           same direction)
  * MIXED: one grid clears $5, other does not
  * NULL:  neither grid clears $5 OR grids disagree on direction

EFFECT-SIZE-DOMINANCE exception (S87-S90) does NOT apply — these cells
are prefix-COVERED.

This script formalizes the structural NULL verdict for the record.

Important distinction: there IS still a within-two_pair $80.82/1000h leak
and within-trips $65.18/1000h leak (v44_dt vs oracle). That leak is the
"ML champion ceiling" — recovering it would require BEATING v44_dt on a
sub-cell, which is the rule-extraction pattern (Option D-revised), NOT
chain audit. S69 + S70 (the design rationale for v55 + v56) explicitly
tested catalog candidates and confirmed v44 dominates every two_pair and
trips cell at the aggregate. Within-category headroom for rule
extraction is therefore considered SATURATED at v44_dt for two_pair and
trips. (Option C N=1000 oracle would refine the picture, but is
deferred.)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

# === PRE-COMMITTED THRESHOLDS (LOCKED, identical to S91) ===
SHIP_THRESHOLD_PREFIX_USD = 5.00  # /1000h
SHIP_THRESHOLD_FULL_USD = 5.00    # /1000h
NULL_THRESHOLD_USD = 1.00         # /1000h


def mechanical_verdict(prefix_lift_usd: float, full_lift_usd: float) -> str:
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


# === STRUCTURAL FINDING (S92) ===
# Chain-audit candidate set is EMPTY for both two_pair and trips because
# v55 / v56 blanket routing has collapsed the chain to v44_dt.
CHAIN_AUDIT_CANDIDATES = []


def main() -> int:
    print("=" * 100)
    print("S92 Phase C grader — two_pair + trips chain-audit candidates")
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
    print()
    print("CHAIN-AUDIT CANDIDATE SET FOR TWO_PAIR + TRIPS:")
    print(f"  {len(CHAIN_AUDIT_CANDIDATES)} candidates")
    print()
    print("STRUCTURAL FINDING (S92 audits):")
    print()
    print("  TWO_PAIR (audit_v64_two_pair_chain_S92.py):")
    print("    Production picks: v64 ≡ v44_dt on every two_pair hand")
    print("                      (confirmed empirically on all 1,338,480 hands;")
    print("                      mismatch count = 0).")
    print("    Δ(v64 − v44_dt) on every (cell × hi_pair × max_sing): $0.00.")
    print("    Chain layer (v44_RULE13) DOES bleed vs v44_dt, but v55's blanket")
    print("    routing absorbs 100% of that bleed.")
    print()
    print("  TRIPS (audit_v64_trips_chain_S92.py):")
    print("    Production picks: v64 ≡ v44_dt on every trips hand")
    print("                      (sample-verified on all 4 cells).")
    print("    Δ(v64 − v44_dt) on every (cell × max_kicker): $0.00.")
    print("    Chain layer (v44_RULE13) bleeds vs v44_dt; v56's blanket routing")
    print("    absorbs 100% of that bleed.")
    print()
    print("  IMPLICATION: There are NO sub-cells where production bleeds vs")
    print("  v44_dt. The chain-audit pattern (gate out a chain layer that")
    print("  bleeds) has nothing to gate.")
    print()
    print("=" * 100)
    print("AGGREGATE S92 CHAIN-AUDIT VERDICT")
    print("=" * 100)
    print()
    print("  STRUCTURAL NULL — zero candidates exist for the chain-audit")
    print("  pattern within two_pair and trips. Production v64 remains unchanged.")
    print()
    print("  The methodology produced an honest answer in <10 min of compute by")
    print("  pre-flight code trace (which predicted v64 ≡ v44_dt) followed by")
    print("  empirical confirmation on all 1.34M two_pair hands.")
    print()
    print("  WHY THIS IS USEFUL DESPITE THE NULL:")
    print()
    print("  1. CHAIN-AUDIT APPLICABILITY MAP REFINEMENT (NEW S92).")
    print("     The chain-audit pattern requires that production picks DIFFER")
    print("     from v44_dt on the audited cells. For two_pair and trips, this")
    print("     is NOT the case — v55/v56 blanket-route to v44_dt unconditionally.")
    print("     Adding to S91's applicability test:")
    print("       (a) target cells are prefix-SILENT → EFFECT-SIZE-DOMINANCE")
    print("           applies (S87-S90), OR")
    print("       (b) per-sub-cell residual ≥ $5/1000h on BOTH grids (S91), OR")
    print("       (c) production picks must differ from v44_dt on at least some")
    print("           audit cells — NEW prerequisite that pre-empts (a) and (b)")
    print("           when production has been collapsed to v44_dt by a prior")
    print("           router (NEW S92).")
    print()
    print("  2. V44_RULE13 CHAIN BLEED MAGNITUDE on two_pair + trips quantified.")
    print("     Architectural snapshot: how much would production bleed if we")
    print("     UNDID v55/v56 blanket routing? (Answer in audit logs.)")
    print("     This re-confirms v55 + v56 as LOAD-BEARING infrastructure.")
    print()
    print("  3. CHAIN-AUDIT WORK ON CATEGORIES (single-pair, two_pair, trips,")
    print("     HIGH_ONLY) IS NOW COMPLETE. The pattern has been applied to all")
    print("     four major hand-categories. Findings:")
    print("       HIGH_ONLY (S87-S90): 4 SHIPS, $214.83/1000h recovered.")
    print("       LOW single-pair (S91): NULL (population-divergence noise).")
    print("       Two_pair (S92): structural NULL (v55 blanket absorbed chain).")
    print("       Trips (S92): structural NULL (v56 blanket absorbed chain).")
    print()
    print("     Remaining open question for future work: are there sub-cells")
    print("     within HIGH_ONLY × max ≤ 7 (the 'super weak' zone) that have")
    print("     NOT been audited? S90 closed the structurally-non-empty")
    print("     HIGH_ONLY × max ≥ 8 zone. The chain-audit work is essentially")
    print("     complete; further ML retrain / Option C N=1000 infra / rule-")
    print("     extraction-from-oracle patterns are the natural next levers.")
    print()
    print("  4. PRE-FLIGHT CODE-TRACE AS A NEW PIVOT-GATE PATTERN.")
    print("     The S92 audit cost ~5 min total compute because we did a")
    print("     pre-flight code trace (read v55 + v56) BEFORE writing the audit.")
    print("     The trace correctly predicted the structural NULL. The audit")
    print("     then served as empirical confirmation + architectural snapshot.")
    print("     This pre-flight pattern should be standard for future chain-")
    print("     audit work: before running a $5-30 min drill, code-trace the")
    print("     chain layers and verify the audit can theoretically produce a")
    print("     non-trivial Δ at the production picks.")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
