"""
Session 68 — validate v54 cell-routing across the pair category via the
S67 catalog harness.

For each (pair_rank, cell) combo, run v54 as the rule_fn against v53
baseline. The expected pattern:
  - PBOT_DS_JOINT, PBOT_DS_PARTIAL cells: v54 fires 100% (routes to v44).
    Lift vs v53 = (v44_evs - v53_evs).mean(); within-cell pct_opt should
    match v44's pct_opt (≥v53's pct_opt; bigger improvement at K, Q, J).
  - PMID_* cells: v54 fires 0% (rule_fn returns same as baseline).
    Lift = $0. pct_opt = baseline pct_opt.

Aggregate v54 - v53 WG lift on pair = sum across cells. This is the
fast pre-grader estimate of v54's expected lift, to <5% of the actual
grader result (per S67 harness validation against Rule 11/19).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/validate_v54_routing_S68.py
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
from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid  # noqa: E402
from strategy_v53_qpair_joint_pbot import strategy_v53_qpair_joint_pbot  # noqa: E402


def rule_fn_v54(hand: np.ndarray):
    """Wrap v54 as a rule_fn for the catalog harness: return None when
    v54 == v53 (= no effective fire), else return v54's pick.

    The harness's "rule fires" semantics: rule_fn returns None means
    use baseline; returns int means override. To get clean fire counts
    we test if v54's pick differs from v53's pick — if equal, fire = no-op.
    """
    v53_pick = int(strategy_v53_qpair_joint_pbot(hand))
    v54_pick = int(strategy_v54_pair_hybrid(hand))
    if v54_pick == v53_pick:
        return None
    return v54_pick


def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 90)
    print("Session 68 — v54 cell-routing validation via S67 harness")
    print(f"Started: {started}")
    print("=" * 90)

    pbot_cells = ["PBOT_DS_JOINT", "PBOT_DS_PARTIAL"]
    pmid_cells = ["PMID_DS_MAXTOP", "PMID_DS_NOMAXTOP",
                  "PMID_SS_MAXTOP", "PMID_OTHER"]

    by_rank_cell = {}
    pbot_wg_total = 0.0
    pmid_wg_total = 0.0
    total_n = 0
    total_fires = 0

    print("\n## PBOT cells (expect v54 fires, lift positive)")
    for pr in range(2, 15):
        for cell in pbot_cells:
            try:
                r = test_rule_on_cell(
                    rule_fn_v54, pr, cell,
                    baseline_fn=strategy_v53_qpair_joint_pbot,
                    label=f"v54/p{RANK_CHAR[pr]}/{cell}",
                    progress=False,
                )
            except ValueError as e:
                continue
            pbot_wg_total += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
            total_fires += r.n_rule_fires
            print(f"  p{RANK_CHAR[pr]}/{cell:<18} n={r.n_hands:>7,}  "
                  f"fires={r.n_rule_fires:>7,} ({100*r.n_rule_fires/r.n_hands:>5.1f}%)  "
                  f"WG=${r.lift_vs_baseline_whole_grid:>+7.2f}  "
                  f"cap={r.capture_pct_vs_baseline:>+6.1f}%")
            by_rank_cell[f"p{RANK_CHAR[pr]}|{cell}"] = {
                "n_hands": r.n_hands,
                "n_rule_fires": r.n_rule_fires,
                "lift_whole_grid": r.lift_vs_baseline_whole_grid,
                "capture_vs_baseline_pct": r.capture_pct_vs_baseline,
                "lift_vs_v44_whole_grid": r.lift_vs_v44_whole_grid,
            }

    print("\n## PMID cells (expect v54 == v53, $0 lift, 0 fires)")
    for pr in range(2, 15):
        for cell in pmid_cells:
            try:
                r = test_rule_on_cell(
                    rule_fn_v54, pr, cell,
                    baseline_fn=strategy_v53_qpair_joint_pbot,
                    label=f"v54/p{RANK_CHAR[pr]}/{cell}",
                    progress=False,
                )
            except ValueError as e:
                continue
            pmid_wg_total += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
            total_fires += r.n_rule_fires
            # Only emit lines with anomalies (PMID should be 0 fires).
            if r.n_rule_fires > 0 or abs(r.lift_vs_baseline_whole_grid) > 0.01:
                print(f"  p{RANK_CHAR[pr]}/{cell:<18} n={r.n_hands:>7,}  "
                      f"fires={r.n_rule_fires:>7,} ({100*r.n_rule_fires/r.n_hands:>5.1f}%)  "
                      f"WG=${r.lift_vs_baseline_whole_grid:>+7.2f}  "
                      f"!! UNEXPECTED")
            by_rank_cell[f"p{RANK_CHAR[pr]}|{cell}"] = {
                "n_hands": r.n_hands,
                "n_rule_fires": r.n_rule_fires,
                "lift_whole_grid": r.lift_vs_baseline_whole_grid,
                "capture_vs_baseline_pct": r.capture_pct_vs_baseline,
                "lift_vs_v44_whole_grid": r.lift_vs_v44_whole_grid,
            }

    total_wg = pbot_wg_total + pmid_wg_total
    print("\n" + "=" * 90)
    print(f"  PBOT-cell aggregate WG lift (pair only): ${pbot_wg_total:+.2f}/1000h")
    print(f"  PMID-cell aggregate WG lift (pair only): ${pmid_wg_total:+.2f}/1000h "
          f"(should be ~0)")
    print(f"  TOTAL pair-category WG lift vs v53: ${total_wg:+.2f}/1000h")
    print(f"  n_hands audited: {total_n:,}  fires: {total_fires:,} "
          f"({100*total_fires/max(total_n,1):.1f}%)")
    print("=" * 90)

    summary = {
        "pbot_wg_total": pbot_wg_total,
        "pmid_wg_total": pmid_wg_total,
        "total_wg_lift_pair_cat": total_wg,
        "total_n_hands": total_n,
        "total_fires": total_fires,
        "by_rank_cell": by_rank_cell,
    }
    out_path = ROOT / "data" / "session68" / "v54_routing_validation.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Wrote: {out_path}")
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
