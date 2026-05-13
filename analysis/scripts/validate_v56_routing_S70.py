"""
Session 70 — Pre-grader validation of v56's predicted lift.

v56 = strategy_v55_two_pair_hybrid + blanket trips → v44_dt routing.

This script REUSES existing v44 + v55 sweep parquets (data/drill_trips_v44_
and data/drill_trips_v55_) to compute v56's predicted whole-grid lift
vs v55 WITHOUT any new EV computation — the same pre-grader technique
used in validate_v55_routing_S69.py.

Methodology:
  - For two_pair AND non-trips hands, v56 == v55 (the routing gate is
    structurally disjoint).
  - For trips hands, v56 == v44, so v56's regret == v44's regret on trips.
  - Predicted lift = sum(v55_regret - v44_regret) over trips hands
                     × 10 × 1000 / N_TOTAL_GRID

Output:
  data/session70/v56_routing_validation.json
  data/session70/v56_routing_validation.log
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

V44_PARQUET = ROOT / "data" / "drill_trips_v44_per_hand_structural.parquet"
V55_PARQUET = ROOT / "data" / "drill_trips_v55_per_hand.parquet"
OUT_JSON = ROOT / "data" / "session70" / "v56_routing_validation.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

CELLS_ORDER = [
    "B_DS_AVAIL_HKR",
    "B_DS_AVAIL_LKR",
    "NO_BDS_CTOP",
    "NO_BDS_AKDOM",
]


def main() -> int:
    print("=" * 88)
    print("v56 pre-grader validation — predicted lift vs v55 (whole-grid)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading trips v44 parquet (regret = oracle_ev - v44_ev) ...",
          flush=True)
    df44 = pq.read_table(V44_PARQUET).to_pandas()
    print(f"  rows: {len(df44):,}")
    print("\n[2/3] loading trips v55 parquet (regret = oracle_ev - v55_ev) ...",
          flush=True)
    df55 = pq.read_table(V55_PARQUET).to_pandas()
    print(f"  rows: {len(df55):,}")

    # Build per-hand v55_regret on the v44 parquet
    df55_lookup = dict(zip(df55["canonical_id"].to_numpy(),
                            df55["v55_regret"].to_numpy()))
    v55_regret_arr = np.array([df55_lookup[int(cid)]
                                for cid in df44["canonical_id"].to_numpy()],
                                dtype=np.float64)
    v44_regret_arr = df44["regret"].to_numpy().astype(np.float64)
    cell_idxs = df44["cell_idx"].to_numpy()
    trip_ranks = df44["trip_rank"].to_numpy()

    print("\n[3/3] computing predicted v56-v55 lift on trips ...", flush=True)
    # v56 == v44 on trips. So delta_regret = v44_regret - v55_regret (v44 wins
    # when regret is smaller).
    delta_regret_per_hand = v44_regret_arr - v55_regret_arr
    # Whole-grid lift (negative = v56 has less regret = BETTER, so we report
    # as v55_wg - v56_wg = -sum(delta)):
    total_v44_regret = float(v44_regret_arr.sum())
    total_v55_regret = float(v55_regret_arr.sum())
    total_v44_wg = total_v44_regret * EV_TO_DOL * 1000 / N_TOTAL_GRID
    total_v55_wg = total_v55_regret * EV_TO_DOL * 1000 / N_TOTAL_GRID
    # v56's regret on trips = v44's regret on trips. So v56_total_wg = v44 trips wg.
    # Lift = v55_wg - v56_wg
    predicted_lift = total_v55_wg - total_v44_wg

    print(f"\n  v44 trips total regret sum  = {total_v44_regret:.4f} EV")
    print(f"  v55 trips total regret sum  = {total_v55_regret:.4f} EV")
    print(f"  v44 trips WG ($/1000h)      = ${total_v44_wg:+.2f}")
    print(f"  v55 trips WG ($/1000h)      = ${total_v55_wg:+.2f}")
    print(f"\n  PREDICTED v56-v55 LIFT      = ${predicted_lift:+.2f} WG full-grid")
    print(f"    (v56 == v44 on trips, == v55 elsewhere; non-trips delta = 0)")

    # Per-cell breakdown
    print("\n  Per-cell predicted v56-v55 lift:")
    print(f"    {'cell':<18} {'n':>9} {'v44_wg':>10} {'v55_wg':>10} "
          f"{'predicted_lift':>16}")
    cell_breakdown = {}
    for ci, cell in enumerate(CELLS_ORDER):
        mask = cell_idxs == ci
        n_c = int(mask.sum())
        if n_c == 0:
            continue
        v44_wg_c = float(v44_regret_arr[mask].sum()) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v55_wg_c = float(v55_regret_arr[mask].sum()) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        lift_c = v55_wg_c - v44_wg_c
        print(f"    {cell:<18} {n_c:>9,} ${v44_wg_c:>+8.2f} "
              f"${v55_wg_c:>+8.2f} ${lift_c:>+14.2f}")
        cell_breakdown[cell] = {
            "n": n_c,
            "v44_wg": v44_wg_c,
            "v55_wg": v55_wg_c,
            "predicted_lift_wg": lift_c,
        }

    # Per-trip-rank breakdown
    print("\n  Per-trip_rank predicted v56-v55 lift:")
    print(f"    {'trip':>5} {'n':>9} {'v44_wg':>10} {'v55_wg':>10} "
          f"{'predicted_lift':>16}")
    rank_breakdown = {}
    for tr in sorted(set(trip_ranks.tolist()), reverse=True):
        mask = trip_ranks == tr
        n_t = int(mask.sum())
        if n_t == 0:
            continue
        v44_wg_t = float(v44_regret_arr[mask].sum()) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v55_wg_t = float(v55_regret_arr[mask].sum()) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        lift_t = v55_wg_t - v44_wg_t
        print(f"    {RANK_CHAR.get(int(tr), tr):>5} {n_t:>9,} "
              f"${v44_wg_t:>+8.2f} ${v55_wg_t:>+8.2f} ${lift_t:>+14.2f}")
        rank_breakdown[str(int(tr))] = {
            "n": n_t,
            "v44_wg": v44_wg_t,
            "v55_wg": v55_wg_t,
            "predicted_lift_wg": lift_t,
        }

    # Counter-headroom audit
    print("\n  Cells where v55 BEATS v44 (counter-headroom; v56 forfeits these):")
    print(f"    {'trip':>5} {'cell':<18} {'v44_wg':>10} {'v55_wg':>10} "
          f"{'forfeit':>10}")
    total_forfeit = 0.0
    for tr in sorted(set(trip_ranks.tolist()), reverse=True):
        for ci, cell in enumerate(CELLS_ORDER):
            mask = (trip_ranks == tr) & (cell_idxs == ci)
            if mask.sum() == 0:
                continue
            v44_wg_tc = float(v44_regret_arr[mask].sum()) * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v55_wg_tc = float(v55_regret_arr[mask].sum()) * EV_TO_DOL * 1000 / N_TOTAL_GRID
            lift_tc = v55_wg_tc - v44_wg_tc
            if lift_tc < 0:
                forfeit = -lift_tc
                total_forfeit += forfeit
                print(f"    {RANK_CHAR.get(int(tr), tr):>5} {cell:<18} "
                      f"${v44_wg_tc:>+8.2f} ${v55_wg_tc:>+8.2f} "
                      f"${forfeit:>+8.2f}")
    print(f"\n    TOTAL counter-headroom forfeit: ${total_forfeit:+.2f} WG")
    print(f"    Net ship (post-forfeit):       ${predicted_lift:+.2f} WG")

    result = {
        "predicted_v56_v55_lift_wg": predicted_lift,
        "v44_trips_wg": total_v44_wg,
        "v55_trips_wg": total_v55_wg,
        "counter_headroom_forfeit_wg": total_forfeit,
        "net_post_forfeit_wg": predicted_lift,  # blanket already accounts for forfeit
        "cell_breakdown": cell_breakdown,
        "rank_breakdown": rank_breakdown,
        "methodology_note": "v56 == v44 on trips, == v55 elsewhere; sum trips regret deltas",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote summary to {OUT_JSON}")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
