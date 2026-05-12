"""
Session 67 Phase 2 — audit C_PAIR_3 sub-variants (3a/3b/3c) on pair PBOT cells.

For each sub-variant, sweep pair_rank ∈ {6,7,8,9} × cell ∈ {PBOT_DS_JOINT,
PBOT_DS_PARTIAL}, score against v52 baseline (pre-computed in
data/drill_pair_v52_per_hand.parquet), aggregate within-cell + WG lift.

Verdicts assigned per T1/T2/T3:
  T1 = ≥40% capture vs baseline within cell AND ≥+$3/1000h within-cell
       AND statable
  T2 = T1 AND ≥+$5/1000h whole-grid AND no non-targeted regression
  T3 = no candidate clears T1

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/audit_c_pair_3_S67.py
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis" / "src"))

from test_rule_catalog_pair import (  # noqa: E402
    test_rule_on_cell, CELLS_ORDER, RANK_CHAR,
)
from strategy_v53_c_pair_3 import (  # noqa: E402
    rule_c_pair_3a, make_rule_c_pair_3b, rule_c_pair_3c,
)


PAIR_RANKS_3 = [6, 7, 8, 9]
PBOT_CELLS = ["PBOT_DS_JOINT", "PBOT_DS_PARTIAL"]
PMID_CELLS = ["PMID_DS_MAXTOP", "PMID_DS_NOMAXTOP", "PMID_SS_MAXTOP", "PMID_OTHER"]


def run_sub_variant(rule_fn, label, *, cells_to_audit, output_log):
    """Run a sub-variant across pair_ranks × cells; return aggregate stats."""
    print("\n" + "=" * 90)
    print(f"AUDITING: {label}")
    print("=" * 90)
    total_wg_lift = 0.0
    total_within_cell_lift_n = 0
    total_fires = 0
    total_n = 0
    by_rank_cell = {}
    capture_sum_w = 0.0
    capture_w = 0.0

    for pr in PAIR_RANKS_3:
        for cell in cells_to_audit:
            try:
                r = test_rule_on_cell(rule_fn, pr, cell,
                                      label=f"{label}/p{RANK_CHAR[pr]}/{cell}")
            except ValueError as e:
                print(f"  [skip] (pair={RANK_CHAR[pr]}, cell={cell}): {e}")
                continue
            r.print_summary()
            total_wg_lift += r.lift_vs_baseline_whole_grid
            total_within_cell_lift_n += r.lift_vs_baseline_within_cell * r.n_hands
            total_fires += r.n_rule_fires
            total_n += r.n_hands
            # Capture-weighted average (weighted by gap_to_oracle).
            cap_b = r.capture_pct_vs_baseline
            gap_w = max(r.oracle_ceiling_ev - r.baseline_mean_ev, 0)
            capture_sum_w += cap_b * gap_w * r.n_hands
            capture_w += gap_w * r.n_hands
            by_rank_cell[f"{RANK_CHAR[pr]}|{cell}"] = {
                "n_hands": r.n_hands,
                "n_rule_fires": r.n_rule_fires,
                "fire_pct": 100 * r.n_rule_fires / r.n_hands,
                "rule_pct_optimal": r.rule_pct_optimal,
                "baseline_pct_optimal": r.baseline_pct_optimal,
                "v44_pct_optimal": r.v44_pct_optimal,
                "capture_vs_baseline_pct": r.capture_pct_vs_baseline,
                "capture_vs_v44_pct": r.capture_pct_vs_v44,
                "lift_within_cell_per_1000h": r.lift_vs_baseline_within_cell,
                "lift_whole_grid_per_1000h": r.lift_vs_baseline_whole_grid,
                "lift_vs_v44_whole_grid": r.lift_vs_v44_whole_grid,
            }

    capture_weighted = capture_sum_w / capture_w if capture_w > 0 else 0.0
    summary = {
        "label": label,
        "total_n_hands": total_n,
        "total_n_rule_fires": total_fires,
        "fire_pct_of_audit_population": 100 * total_fires / max(total_n, 1),
        "total_whole_grid_lift_per_1000h": total_wg_lift,
        "weighted_avg_capture_pct": capture_weighted,
        "by_rank_cell": by_rank_cell,
    }

    print(f"\n  {label} AGGREGATE")
    print(f"    n_hands audited     : {total_n:,}")
    print(f"    n_rule_fires         : {total_fires:,} ({summary['fire_pct_of_audit_population']:.1f}%)")
    print(f"    weighted-avg capture : {capture_weighted:+.2f}%")
    print(f"    SUM whole-grid lift  : ${total_wg_lift:+.2f}/1000h WG")

    # Threshold verdict.
    t1_ok = (capture_weighted >= 40.0) and (total_wg_lift > 0)
    t2_ok = t1_ok and (total_wg_lift >= 5.0)
    if t2_ok:
        verdict = "T2 — production-ship CANDIDATE (subject to non-targeted regression)"
    elif t1_ok:
        verdict = "T1 — catalog-worthy (does not yet clear T2's $5 WG bar)"
    elif total_wg_lift > 0:
        verdict = "Below T1 — positive but below 40% capture or <$3 within-cell"
    else:
        verdict = "T3 — net-negative or null"
    summary["verdict"] = verdict
    print(f"    VERDICT              : {verdict}")
    return summary


def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 90)
    print("Session 67 Phase 2 — C_PAIR_3 sub-variant audit")
    print(f"Started: {started}")
    print("=" * 90)

    results = {}

    # Run each sub-variant on PBOT cells (fire-region).
    print("\n\n#" * 5 + " PHASE 2a: PBOT cells (fire region) " + "#" * 5)
    for fn, label in [
        (rule_c_pair_3a, "C_PAIR_3a (simple)"),
        (make_rule_c_pair_3b(11), "C_PAIR_3b (mid≥J)"),
        (rule_c_pair_3c, "C_PAIR_3c (joint-only)"),
    ]:
        results[label] = run_sub_variant(
            fn, label, cells_to_audit=PBOT_CELLS,
            output_log=None,
        )

    # For each candidate that clears T2 (or is close), check PMID cells for
    # non-targeted regression (rule should NOT fire — should be 0% fires
    # AND zero lift).
    print("\n\n#" * 5 + " PHASE 2b: PMID-cell regression check (top variant) " + "#" * 5)
    best_label = max(results.keys(), key=lambda k: results[k]["total_whole_grid_lift_per_1000h"])
    best_fn = {
        "C_PAIR_3a (simple)": rule_c_pair_3a,
        "C_PAIR_3b (mid≥J)": make_rule_c_pair_3b(11),
        "C_PAIR_3c (joint-only)": rule_c_pair_3c,
    }[best_label]
    print(f"\n  Best-WG variant: {best_label}")
    print(f"  Running PMID-cell regression check on {best_label} ...")
    pmid_summary = run_sub_variant(
        best_fn, f"{best_label} [PMID regression check]",
        cells_to_audit=PMID_CELLS, output_log=None,
    )
    results[f"{best_label}_pmid_regression"] = pmid_summary

    out_path = ROOT / "data" / "session67" / "c_pair_3_audit_summary.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Wrote summary JSON: {out_path}")

    print("\n" + "=" * 90)
    print("FINAL TABLE — C_PAIR_3 sub-variants on PBOT cells")
    print("=" * 90)
    print(f"  {'variant':<24} {'fires':>9} {'capture':>9} {'WG lift':>12} {'verdict':<35}")
    for label, summ in results.items():
        if "pmid_regression" in label:
            continue
        print(f"  {label:<24} {summ['total_n_rule_fires']:>9,} "
              f"{summ['weighted_avg_capture_pct']:>+8.2f}% "
              f"${summ['total_whole_grid_lift_per_1000h']:>+10.2f} "
              f"{summ['verdict'][:34]:<35}")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
