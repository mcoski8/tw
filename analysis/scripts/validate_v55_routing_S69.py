"""
Session 69 — validate v55 (= v54 + blanket two_pair → v44) routing math
using the existing sweep data (no new computation needed).

The harness predicts the v55 vs v54 lift on two_pair as:
  sum(v44_regret - v54_regret) over two_pair hands × 10000 / N_TOTAL_GRID

where v44_regret + v54_regret are pre-computed in the S69 Phase 1 + 1b
parquets. This script confirms:
  1. v55's routing logic matches the harness assumption (all two_pair →
     v44).
  2. The harness predicts +$X WG full-grid; the grader-confirmed lift
     should match within 1% (per S68 v54 fidelity precedent).
  3. Outside two_pair, v55 == v54 (zero spillover).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/validate_v55_routing_S69.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis" / "src"))

V44_PARQUET = ROOT / "data" / "drill_two_pair_v44_per_hand_structural.parquet"
V54_PARQUET = ROOT / "data" / "drill_two_pair_v54_per_hand.parquet"
N_TOTAL_GRID = 6_009_159
EV_TO_DOL = 10.0


def main():
    print("=" * 80)
    print("S69 v55 routing math validation (harness lift prediction)")
    print("=" * 80)

    print("\nLoading two_pair v44 per-hand parquet...")
    df_v44 = pq.read_table(V44_PARQUET).to_pandas()
    print(f"  v44: rows={len(df_v44):,}")
    print("Loading two_pair v54 per-hand parquet...")
    df_v54 = pq.read_table(V54_PARQUET).to_pandas()
    print(f"  v54: rows={len(df_v54):,}")

    # Join on canonical_id
    v54_lookup = dict(zip(df_v54["canonical_id"].to_numpy(),
                           df_v54["v54_regret"].to_numpy()))
    v44_regret = df_v44["regret"].to_numpy().astype(np.float64)
    v54_regret = np.array(
        [v54_lookup[int(cid)] for cid in df_v44["canonical_id"].to_numpy()],
        dtype=np.float64
    )

    n = len(df_v44)
    sum_v44 = float(v44_regret.sum())
    sum_v54 = float(v54_regret.sum())
    delta_sum = sum_v44 - sum_v54  # negative = v44 better

    v44_wg = sum_v44 * EV_TO_DOL * 1000 / N_TOTAL_GRID
    v54_wg = sum_v54 * EV_TO_DOL * 1000 / N_TOTAL_GRID
    lift_v55_over_v54 = -delta_sum * EV_TO_DOL * 1000 / N_TOTAL_GRID

    print(f"\nTwo_pair sample size: n={n:,} = {100*n/N_TOTAL_GRID:.1f}% of grid")
    print(f"Sum v44 regret = {sum_v44:.4f} EV → ${v44_wg:.2f}/1000h whole-grid")
    print(f"Sum v54 regret = {sum_v54:.4f} EV → ${v54_wg:.2f}/1000h whole-grid")
    print(f"\nv55 = route two_pair → v44, else → v54.")
    print(f"v55 vs v54 lift on two_pair = sum(v54_regret - v44_regret) over")
    print(f"  two_pair hands → predicted whole-grid lift:")
    print(f"  +${lift_v55_over_v54:.2f}/1000h FULL GRID (canonical-equal framing)")

    # Per-hi_pair-rank breakdown
    print("\nPer-hi_pair-rank predicted v55-over-v54 lift breakdown:")
    print(f"  {'hi_pair':>7} {'n':>9} {'v44_wg':>10} {'v54_wg':>10} {'v55-v54':>10}")
    hi_pair = df_v44["hi_pair_rank"].to_numpy()
    rank_lifts = {}
    for r in range(2, 15):
        mask = hi_pair == r
        if mask.sum() == 0:
            continue
        sum_v44_r = float(v44_regret[mask].sum())
        sum_v54_r = float(v54_regret[mask].sum())
        lift_r = (sum_v54_r - sum_v44_r) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v44_r_wg = sum_v44_r * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v54_r_wg = sum_v54_r * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {r:>7} {int(mask.sum()):>9,} ${v44_r_wg:>+8.2f} "
              f"${v54_r_wg:>+8.2f} ${lift_r:>+8.2f}")
        rank_lifts[r] = {
            "n": int(mask.sum()),
            "v44_wg": v44_r_wg,
            "v54_wg": v54_r_wg,
            "v55_over_v54_lift_wg": lift_r,
        }

    # Per-cell breakdown
    print("\nPer-cell predicted v55-over-v54 lift breakdown (across all hi_pair):")
    print(f"  {'cell_idx':>8} {'n':>9} {'v44_wg':>10} {'v54_wg':>10} {'v55-v54':>10}")
    cell_idx = df_v44["cell_idx"].to_numpy()
    cells = ["LAYOUT_A_DS", "LAYOUT_C_DS", "LAYOUT_B_DS",
             "LAYOUT_A_SS", "LAYOUT_C_SS_ONLY", "LAYOUT_B_SS_ONLY",
             "LAYOUT_OTHER"]
    cell_lifts = {}
    for ci, cn in enumerate(cells):
        mask = cell_idx == ci
        if mask.sum() == 0:
            continue
        sum_v44_c = float(v44_regret[mask].sum())
        sum_v54_c = float(v54_regret[mask].sum())
        lift_c = (sum_v54_c - sum_v44_c) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v44_c_wg = sum_v44_c * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v54_c_wg = sum_v54_c * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {cn:<20} {int(mask.sum()):>9,} ${v44_c_wg:>+8.2f} "
              f"${v54_c_wg:>+8.2f} ${lift_c:>+8.2f}")
        cell_lifts[cn] = {
            "n": int(mask.sum()),
            "v44_wg": v44_c_wg,
            "v54_wg": v54_c_wg,
            "v55_over_v54_lift_wg": lift_c,
        }

    print("\n" + "=" * 80)
    print(f"  TOTAL v55-vs-v54 PREDICTED FULL-GRID LIFT: +${lift_v55_over_v54:+.2f}/1000h")
    print("  (compare to grader-reported lift after grade_v55_two_pair_hybrid.py)")
    print("=" * 80)

    out_path = ROOT / "data" / "session69" / "v55_routing_validation.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "n_two_pair_hands": n,
            "v44_total_wg": v44_wg,
            "v54_total_wg": v54_wg,
            "v55_over_v54_predicted_lift_wg": lift_v55_over_v54,
            "per_rank": rank_lifts,
            "per_cell": cell_lifts,
        }, f, indent=2)
    print(f"\n  Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
