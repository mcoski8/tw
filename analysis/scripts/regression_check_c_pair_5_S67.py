"""
Session 67 — non-targeted regression check for C_PAIR_5_joint (Q-pair only).

Verifies the rule fires ONLY on Q-pair × PBOT_DS_JOINT hands across the
full pair category, and never on non-pair canonical hands. Then sweeps
all 13 pair_ranks × all 6 cells through the harness to confirm:
  - WG lift is concentrated at Q-pair × PBOT_DS_JOINT
  - All other (pair_rank, cell) combos have rule_fires=0 (= no change
    from v52 baseline)

Final aggregate WG = sum of per-(pair_rank, cell) WG. Should equal +$8.50.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/regression_check_c_pair_5_S67.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis" / "src"))

from test_rule_catalog_pair import test_rule_on_cell, CELLS_ORDER, RANK_CHAR  # noqa: E402
from audit_c_pair_fallback_S67 import rule_c_pair_5_qpair_joint  # noqa: E402


def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 90)
    print("Session 67 — non-targeted regression check for C_PAIR_5_joint")
    print(f"Started: {started}")
    print("=" * 90)

    grand_total_wg = 0.0
    grand_total_fires = 0
    grand_total_n = 0
    by_rank_cell = {}

    for pr in range(2, 15):
        for cell in CELLS_ORDER:
            try:
                r = test_rule_on_cell(
                    rule_c_pair_5_qpair_joint, pr, cell,
                    label=f"regression/p{RANK_CHAR[pr]}/{cell}",
                    progress=False,
                )
            except ValueError as e:
                continue
            grand_total_wg += r.lift_vs_baseline_whole_grid
            grand_total_fires += r.n_rule_fires
            grand_total_n += r.n_hands
            if r.n_rule_fires > 0 or abs(r.lift_vs_baseline_whole_grid) > 0.01:
                print(f"  p{RANK_CHAR[pr]}/{cell:<18} n={r.n_hands:>7,}  "
                      f"fires={r.n_rule_fires:>7,} ({100*r.n_rule_fires/r.n_hands:>5.1f}%)  "
                      f"WG lift=${r.lift_vs_baseline_whole_grid:>+7.2f}/1000h  "
                      f"capture={r.capture_pct_vs_baseline:>+6.2f}%")
            by_rank_cell[f"p{RANK_CHAR[pr]}|{cell}"] = {
                "n_hands": r.n_hands,
                "n_rule_fires": r.n_rule_fires,
                "lift_whole_grid": r.lift_vs_baseline_whole_grid,
                "capture_vs_baseline_pct": r.capture_pct_vs_baseline,
            }

    print("\n" + "=" * 90)
    print(f"  Pair-category total audit:  n={grand_total_n:,}  fires={grand_total_fires:,}")
    print(f"  Pair-category total WG lift: ${grand_total_wg:+.2f}/1000h")
    print(f"  Expected (audit_c_pair_fallback) at Q-pair-JOINT:  $+8.50/1000h")
    print(f"  Delta: ${grand_total_wg - 8.50:+.2f} (should be near zero)")
    print("=" * 90)

    summary = {
        "rule": "C_PAIR_5_qpair_joint",
        "total_n_hands_in_pair_cat": grand_total_n,
        "total_n_rule_fires_in_pair_cat": grand_total_fires,
        "total_wg_lift_in_pair_cat": grand_total_wg,
        "by_rank_cell": by_rank_cell,
    }
    out_path = ROOT / "data" / "session67" / "regression_check_c_pair_5.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Wrote: {out_path}")
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
