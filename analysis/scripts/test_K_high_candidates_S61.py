"""
Session 61 — Test S61 K-high candidate rules against v52 baseline.

Mirrors test_A_high_candidates_S60.py exactly. Runs each candidate from
candidates_K_high_S61 through the test_rule_catalog harness on its
target cell. Reports T1/T2/T3 verdicts:

  T1 (Catalog-worthy): gap_closure_pct >= 40% AND lift_within_cell >= $3/1000h
  T2 (Production):     T1 + lift_whole_grid >= $5/1000h
  T3 (ML-only):        no candidate clears T1 for a cell
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_rule_catalog import test_rule_on_cell  # noqa: E402
from candidates_K_high_S61 import CANDIDATES  # noqa: E402
from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402

OUT_JSON = ROOT / "data" / "session_61_candidate_results.json"
KING = 13


def verdict(gap_closure_pct: float, lift_within: float, lift_wg: float) -> str:
    t1 = (gap_closure_pct >= 40.0) and (lift_within >= 3.0)
    t2 = t1 and (lift_wg >= 5.0)
    if t2:
        return "T2_SHIP"
    if t1:
        return "T1_CATALOG"
    return "T3_BELOW_T1"


def main() -> int:
    print("=" * 88)
    print("Session 61 — K-high candidate sweep vs v52 baseline")
    print("=" * 88)

    all_results = []
    for name, (fn, cell) in CANDIDATES.items():
        print(f"\n>>> CANDIDATE {name} on cell={cell}")
        try:
            r = test_rule_on_cell(
                rule_fn=fn, max_rank=KING, cell=cell,
                baseline_fn=strategy_v52_full_high_only_handler,
                label=name, progress=False,
            )
            r.print_summary()
            v = verdict(r.capture_pct_vs_baseline,
                        r.lift_vs_baseline_within_cell,
                        r.lift_vs_baseline_whole_grid)
            print(f"  VERDICT: {v}")
            all_results.append({
                "name": name, "cell": cell, "n_hands": r.n_hands,
                "n_rule_fires": r.n_rule_fires,
                "rule_pct_optimal": r.rule_pct_optimal,
                "baseline_pct_optimal": r.baseline_pct_optimal,
                "v44_pct_optimal": r.v44_pct_optimal,
                "rule_mean_ev": r.rule_mean_ev,
                "baseline_mean_ev": r.baseline_mean_ev,
                "v44_mean_ev": r.v44_mean_ev,
                "oracle_ceiling_ev": r.oracle_ceiling_ev,
                "capture_pct_vs_baseline": r.capture_pct_vs_baseline,
                "capture_pct_vs_v44": r.capture_pct_vs_v44,
                "lift_vs_baseline_within_cell": r.lift_vs_baseline_within_cell,
                "lift_vs_baseline_whole_grid": r.lift_vs_baseline_whole_grid,
                "lift_vs_v44_within_cell": r.lift_vs_v44_within_cell,
                "lift_vs_v44_whole_grid": r.lift_vs_v44_whole_grid,
                "verdict": v,
            })
        except Exception as e:
            print(f"  FAILED: {e}")
            all_results.append({"name": name, "cell": cell, "error": str(e)})

    print("\n" + "=" * 88)
    print("FINAL SCOREBOARD")
    print("=" * 88)
    print(f"{'name':<38} {'cell':<14} {'fires':>9} {'cap_b':>7} {'lift_$':>9} {'wg_$':>8} {'verdict'}")
    for res in all_results:
        if "error" in res:
            print(f"{res['name']:<38} {res['cell']:<14} ERROR: {res['error']}")
            continue
        fires_pct = 100 * res["n_rule_fires"] / max(res["n_hands"], 1)
        print(f"{res['name']:<38} {res['cell']:<14} {fires_pct:>7.1f}% "
              f"{res['capture_pct_vs_baseline']:>+6.2f}% "
              f"${res['lift_vs_baseline_within_cell']:>+8.2f} "
              f"${res['lift_vs_baseline_whole_grid']:>+7.2f} "
              f"{res['verdict']}")

    OUT_JSON.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults written to {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
