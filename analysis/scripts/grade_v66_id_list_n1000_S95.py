"""S95 Phase C — grade v66 candidates via sparse N=1000 grid.

PRE-COMMITTED THRESHOLDS (locked BEFORE the N=1000 grid is read):
  SHIP   = N=200 lift ≥ $5 AND N=1000 lift ≥ $5
  NULL   = N=200 lift ≤ $1 AND N=1000 lift ≤ $1
  MIXED  = otherwise

N=200 PRE-DRILL RESULTS (S95 Phase B):
  NARROW: $+4.59/1000h  (sr=85.2%, n_changed=8,751)
  MEDIUM: $+2.95/1000h  (sr=65.9%, n_changed=18,734)
  WIDE:   $+0.36/1000h  (sr=57.2%, n_changed=51,531)

Verdict expectations (locked from N=200):
  NARROW: cannot ship (4.59 < 5.0). Verdict = MIXED unless N=1000 ≤ $1.
  MEDIUM: cannot ship (2.95 < 5.0). Verdict = MIXED unless N=1000 ≤ $1.
  WIDE:   cannot ship. Could land NULL if N=1000 ≤ $1.

USAGE:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v66_id_list_n1000_S95.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
for p in (str(SRC),):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

DATA = ROOT / "data"
PICKS_NPZ = DATA / "session95" / "v66_per_hand_picks.npz"
N200_BASELINE = DATA / "session95" / "phaseB_prepare_summary.json"
GRID_FULL_N200 = DATA / "oracle_grid_full_realistic_n200.bin"
GRID_SPARSE_N1000 = DATA / "session95" / "v66_n1000_sparse.bin"
OUT_JSON = DATA / "session95" / "grade_v66_n1000_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
GATES = ["NARROW", "MEDIUM", "WIDE"]

# --- PRE-COMMITTED THRESHOLDS (locked) ---
SHIP_LIFT_DOL_PER_1000H = 5.0
NULL_LIFT_DOL_PER_1000H = 1.0


def verdict_two_grid(lift_n200: float, lift_n1000: float) -> str:
    n200_ship = lift_n200 >= SHIP_LIFT_DOL_PER_1000H
    n1000_ship = lift_n1000 >= SHIP_LIFT_DOL_PER_1000H
    n200_null = lift_n200 <= NULL_LIFT_DOL_PER_1000H
    n1000_null = lift_n1000 <= NULL_LIFT_DOL_PER_1000H
    if n200_ship and n1000_ship:
        return "SHIP"
    if n200_null and n1000_null:
        return "NULL"
    return "MIXED"


def main() -> int:
    print("loading per-hand picks ...", flush=True)
    picks = np.load(PICKS_NPZ)
    canonical_ids = picks["canonical_id"].astype(np.int64)
    v65_pick = picks["v65_pick"].astype(np.int64)
    v66_by_gate = {
        "NARROW": picks["v66_pick_narrow"].astype(np.int64),
        "MEDIUM": picks["v66_pick_medium"].astype(np.int64),
        "WIDE": picks["v66_pick_wide"].astype(np.int64),
    }
    n_cell = len(canonical_ids)
    print(f"  cell hands: {n_cell:,}", flush=True)

    print("loading N=200 full grid ...", flush=True)
    grid_n200 = read_oracle_grid(GRID_FULL_N200, mode="memmap")
    evs_n200 = grid_n200.evs

    print("loading N=1000 sparse grid ...", flush=True)
    grid_n1000 = read_oracle_grid(GRID_SPARSE_N1000, mode="memmap")
    print(
        f"  N=1000 sparse: {len(grid_n1000):,} rows, "
        f"samples={grid_n1000.header.samples}, "
        f"base_seed={hex(grid_n1000.header.base_seed)}, "
        f"opp={grid_n1000.header.opp_label}"
    )
    if grid_n1000.header.samples != 1000:
        print(
            f"  WARNING: N=1000 sparse header.samples={grid_n1000.header.samples} "
            "(expected 1000)"
        )

    sparse_id_to_row = {
        int(cid): k for k, cid in enumerate(grid_n1000.canonical_ids)
    }
    n_n1000 = len(sparse_id_to_row)
    print(f"  sparse id-to-row dict: {n_n1000:,} entries")

    # All changed canonical_ids across all gates should be covered (WIDE is superset)
    wide_changed_mask = v66_by_gate["WIDE"] != v65_pick
    wide_changed_ids = canonical_ids[wide_changed_mask]
    missing = [int(c) for c in wide_changed_ids if int(c) not in sparse_id_to_row]
    print(f"  WIDE changed ids: {len(wide_changed_ids):,} (sparse covers {len(wide_changed_ids) - len(missing):,}, missing {len(missing):,})")
    if missing:
        print(f"  ERROR: {len(missing)} ids missing from N=1000 sparse grid")
        print(f"  first missing: {missing[:5]}")
        return 1

    # Per-gate evaluation
    print("\ncomputing N=1000 lifts per gate ...", flush=True)
    per_gate = {}
    t0 = time.time()
    for g in GATES:
        v66_pick_g = v66_by_gate[g]
        changed_mask = v66_pick_g != v65_pick
        idx_changed = np.where(changed_mask)[0]
        n_chg = int(changed_mask.sum())

        sum_delta_n200 = 0.0
        sum_delta_n1000 = 0.0
        n_v66_better_n200 = 0
        n_v66_worse_n200 = 0
        n_v66_better_n1000 = 0
        n_v66_worse_n1000 = 0
        n_sign_agree = 0
        n_sign_disagree = 0

        for i in idx_changed:
            cid = int(canonical_ids[i])
            row_idx = sparse_id_to_row[cid]
            evs_n200_row = evs_n200[cid]
            evs_n1000_row = grid_n1000.records[row_idx]["evs"]

            p65 = int(v65_pick[i])
            p66 = int(v66_pick_g[i])

            d200 = float(evs_n200_row[p66]) - float(evs_n200_row[p65])
            d1000 = float(evs_n1000_row[p66]) - float(evs_n1000_row[p65])
            sum_delta_n200 += d200
            sum_delta_n1000 += d1000

            if d200 > 0: n_v66_better_n200 += 1
            elif d200 < 0: n_v66_worse_n200 += 1
            if d1000 > 0: n_v66_better_n1000 += 1
            elif d1000 < 0: n_v66_worse_n1000 += 1

            if (d200 > 0) == (d1000 > 0) and (d200 < 0) == (d1000 < 0):
                n_sign_agree += 1
            else:
                n_sign_disagree += 1

        lift_n200 = sum_delta_n200 / N_TOTAL_GRID * EV_TO_DOL * 1000
        lift_n1000 = sum_delta_n1000 / N_TOTAL_GRID * EV_TO_DOL * 1000
        v = verdict_two_grid(lift_n200, lift_n1000)

        print(f"\n=== Gate {g} ===")
        print(f"  n_changed:                     {n_chg:>8,}")
        print(f"  N=200 lift:                    ${lift_n200:+9.2f}/1000h")
        print(f"  N=1000 lift (S95 NEW):         ${lift_n1000:+9.2f}/1000h")
        print(f"  abs diff (|N=200 − N=1000|):   ${abs(lift_n200 - lift_n1000):+9.2f}/1000h")
        print(f"  N=200 v66_better/changed:      {n_v66_better_n200:>5,}/{n_chg:,} = {n_v66_better_n200/max(n_chg,1)*100:.1f}%")
        print(f"  N=1000 v66_better/changed:     {n_v66_better_n1000:>5,}/{n_chg:,} = {n_v66_better_n1000/max(n_chg,1)*100:.1f}%")
        print(f"  sign agreement N=200 vs N=1000: {n_sign_agree:>5,}/{n_chg:,} = {n_sign_agree/max(n_chg,1)*100:.1f}%")
        print(f"  >>> VERDICT (two-grid): {v}")

        per_gate[g] = {
            "gate": g,
            "n_changed": n_chg,
            "sum_delta_ev_n200": sum_delta_n200,
            "sum_delta_ev_n1000": sum_delta_n1000,
            "lift_dol_per_1000h_n200": lift_n200,
            "lift_dol_per_1000h_n1000": lift_n1000,
            "abs_diff_n200_n1000_dol_per_1000h": abs(lift_n200 - lift_n1000),
            "n_v66_better_n200": n_v66_better_n200,
            "n_v66_worse_n200": n_v66_worse_n200,
            "n_v66_better_n1000": n_v66_better_n1000,
            "n_v66_worse_n1000": n_v66_worse_n1000,
            "n_sign_agree": n_sign_agree,
            "n_sign_disagree": n_sign_disagree,
            "verdict_two_grid": v,
        }

    elapsed = time.time() - t0
    print(f"\nwall: {elapsed:.1f}s", flush=True)

    summary = {
        "session": 95,
        "phase": "C-grade",
        "ship_threshold_dol_per_1000h": SHIP_LIFT_DOL_PER_1000H,
        "null_threshold_dol_per_1000h": NULL_LIFT_DOL_PER_1000H,
        "standard": "two-grid: both N=200 and N=1000 ≥ $5 for SHIP, both ≤ $1 for NULL, MIXED otherwise",
        "per_gate": per_gate,
        "best_gate_by_n1000": max(per_gate.values(), key=lambda d: d["lift_dol_per_1000h_n1000"]),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nsummary -> {OUT_JSON.relative_to(ROOT)}", flush=True)

    print("\n" + "=" * 70)
    best = summary["best_gate_by_n1000"]
    print(f"BEST GATE by N=1000 lift: {best['gate']}")
    print(f"  N=200  lift: ${best['lift_dol_per_1000h_n200']:+.2f}/1000h")
    print(f"  N=1000 lift: ${best['lift_dol_per_1000h_n1000']:+.2f}/1000h")
    print(f"  Two-grid verdict: {best['verdict_two_grid']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
