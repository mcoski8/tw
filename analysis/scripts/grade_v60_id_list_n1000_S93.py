"""S93 Phase C-3 — grade v60 candidates using N=1000 sparse oracle grid.

PRE-COMMITTED THRESHOLDS (locked in code BEFORE the N=1000 sparse grid is read):
  SHIP_LIFT_DOL_PER_1000H = 5.0  (each grid; both must clear for SHIP)
  NULL_LIFT_DOL_PER_1000H = 1.0  (each grid; both must clear for NULL)
  MIXED otherwise.

  TWO-GRID SHIP STANDARD (S84+):
    SHIP   = N=200 lift ≥ $5 AND N=1000 lift ≥ $5
    NULL   = N=200 lift ≤ $1 AND N=1000 lift ≤ $1
    MIXED  = otherwise (e.g. N=200 SHIPs but N=1000 doesn't)

WHY THIS UNBLOCKS v60: at S86, the prefix N=1000 grid covered ids 0..500,000
but the v60 cell (MID × PMID_DS_NOMAXTOP) sits at cid_min 593,072 — entirely
outside the prefix. So the prefix grid was silent and v60 stayed MIXED-by-
methodology despite N=200 SHIPping at $+6.43. This grader uses Option C's
--id-list-file infrastructure to compute N=1000 EVs on exactly the 32,304
hands v60-gate12 actually changes, giving a proper N=1000 lift estimate to
pair with the N=200 baseline.

USAGE:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v60_id_list_n1000_S93.py
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

# Inputs
PICKS_NPZ = ROOT / "data" / "session93" / "v60_per_hand_picks.npz"
N200_BASELINE = ROOT / "data" / "session93" / "v60_n200_baseline.json"
GRID_FULL_N200 = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_SPARSE_N1000 = ROOT / "data" / "session93" / "v60_n1000_sparse.bin"

# Output
OUT_JSON = ROOT / "data" / "session93" / "grade_v60_n1000_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
GATES = [10, 11, 12]

# --- PRE-COMMITTED THRESHOLDS (locked) ---
SHIP_LIFT_DOL_PER_1000H = 5.0
NULL_LIFT_DOL_PER_1000H = 1.0
# Two-grid standard: BOTH N=200 and N=1000 must clear $5 for SHIP; both must
# be ≤ $1 for NULL; MIXED otherwise.


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
    print("loading per-hand picks (from prepare step) ...", flush=True)
    picks = np.load(PICKS_NPZ)
    canonical_ids = picks["canonical_id"].astype(np.int64)
    v57_pick = picks["v57_pick"].astype(np.int64)
    v60_by_gate = {
        10: picks["v60_pick_g10"].astype(np.int64),
        11: picks["v60_pick_g11"].astype(np.int64),
        12: picks["v60_pick_g12"].astype(np.int64),
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

    # Build id → row index dict for the sparse grid (records are NOT indexable
    # by canonical_id position in id-list-mode).
    sparse_id_to_row = {
        int(cid): k for k, cid in enumerate(grid_n1000.canonical_ids)
    }
    n_n1000 = len(sparse_id_to_row)
    print(f"  sparse id-to-row dict: {n_n1000:,} entries")

    # Sanity: every id in v60_gate12_changed_ids should appear in sparse grid.
    g12_changed_mask = v60_by_gate[12] != v57_pick
    g12_changed_ids = canonical_ids[g12_changed_mask]
    missing = [int(c) for c in g12_changed_ids if int(c) not in sparse_id_to_row]
    print(
        f"  gate=12 changed ids: {len(g12_changed_ids):,} "
        f"(sparse grid covers {len(g12_changed_ids) - len(missing):,}, missing {len(missing):,})"
    )
    if missing:
        print(f"  ERROR: {len(missing)} ids missing from N=1000 sparse grid")
        print(f"  first missing: {missing[:5]}")
        return 1

    # For each gate, compute N=1000 lift on the changed-hand subset.
    print("\ncomputing N=1000 lifts per gate ...", flush=True)
    per_gate = {}
    t0 = time.time()
    for g in GATES:
        v60_pick_g = v60_by_gate[g]
        changed_mask = v60_pick_g != v57_pick
        idx_changed = np.where(changed_mask)[0]
        n_chg = int(changed_mask.sum())

        sum_delta_n200 = 0.0
        sum_delta_n1000 = 0.0
        n_v60_better_n1000 = 0
        n_v60_worse_n1000 = 0
        n_v60_better_n200 = 0
        n_v60_worse_n200 = 0
        # Sign-agreement: count hands where N=200 and N=1000 deltas agree on
        # sign of (v60 - v57). Disagreement = MC noise candidate.
        n_sign_agree = 0
        n_sign_disagree = 0

        for i in idx_changed:
            cid = int(canonical_ids[i])
            row_idx = sparse_id_to_row[cid]
            evs_n200_row = evs_n200[cid]
            evs_n1000_row = grid_n1000.records[row_idx]["evs"]

            v57_p = int(v57_pick[i])
            v60_p = int(v60_pick_g[i])

            d200 = float(evs_n200_row[v60_p]) - float(evs_n200_row[v57_p])
            d1000 = float(evs_n1000_row[v60_p]) - float(evs_n1000_row[v57_p])
            sum_delta_n200 += d200
            sum_delta_n1000 += d1000

            if d200 > 0: n_v60_better_n200 += 1
            elif d200 < 0: n_v60_worse_n200 += 1
            if d1000 > 0: n_v60_better_n1000 += 1
            elif d1000 < 0: n_v60_worse_n1000 += 1

            # Sign comparison (using > / < to ignore exact zeros from MC quantisation)
            if (d200 > 0) == (d1000 > 0) and (d200 < 0) == (d1000 < 0):
                n_sign_agree += 1
            else:
                n_sign_disagree += 1

        lift_n200 = sum_delta_n200 / N_TOTAL_GRID * EV_TO_DOL * 1000
        lift_n1000 = sum_delta_n1000 / N_TOTAL_GRID * EV_TO_DOL * 1000
        v = verdict_two_grid(lift_n200, lift_n1000)

        print(f"\n=== Gate {g} (max_sing ≤ {g}) ===")
        print(f"  n_changed:                     {n_chg:>8,}")
        print(f"  N=200 lift:                    ${lift_n200:+9.2f}/1000h")
        print(f"  N=1000 lift (NEW S93):         ${lift_n1000:+9.2f}/1000h")
        print(f"  abs diff (|N=200 − N=1000|):   ${abs(lift_n200 - lift_n1000):+9.2f}/1000h")
        print(f"  N=200 v60_better/changed:      {n_v60_better_n200:>5,}/{n_chg:,} = {n_v60_better_n200/n_chg*100:.1f}%")
        print(f"  N=1000 v60_better/changed:     {n_v60_better_n1000:>5,}/{n_chg:,} = {n_v60_better_n1000/n_chg*100:.1f}%")
        print(f"  sign agreement N=200 vs N=1000: {n_sign_agree:>5,}/{n_chg:,} = {n_sign_agree/n_chg*100:.1f}%")
        print(f"  >>> VERDICT (two-grid): {v}")

        per_gate[str(g)] = {
            "gate_max_sing": g,
            "n_changed": n_chg,
            "sum_delta_ev_n200": sum_delta_n200,
            "sum_delta_ev_n1000": sum_delta_n1000,
            "lift_dol_per_1000h_n200": lift_n200,
            "lift_dol_per_1000h_n1000": lift_n1000,
            "abs_diff_n200_n1000_dol_per_1000h": abs(lift_n200 - lift_n1000),
            "n_v60_better_n200": n_v60_better_n200,
            "n_v60_worse_n200": n_v60_worse_n200,
            "n_v60_better_n1000": n_v60_better_n1000,
            "n_v60_worse_n1000": n_v60_worse_n1000,
            "n_sign_agree": n_sign_agree,
            "n_sign_disagree": n_sign_disagree,
            "verdict_two_grid": v,
        }

    elapsed = time.time() - t0
    print(f"\nwall: {elapsed:.1f}s", flush=True)

    summary = {
        "session": 93,
        "phase": "C-3-grade",
        "ship_threshold_dol_per_1000h": SHIP_LIFT_DOL_PER_1000H,
        "null_threshold_dol_per_1000h": NULL_LIFT_DOL_PER_1000H,
        "standard": "two-grid: both N=200 and N=1000 must clear $5 for SHIP, both ≤ $1 for NULL, MIXED otherwise",
        "per_gate": per_gate,
        "best_gate": max(per_gate.values(), key=lambda d: d["lift_dol_per_1000h_n1000"]),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)

    print("\n" + "=" * 70)
    print(f"BEST GATE by N=1000 lift: max_sing ≤ {summary['best_gate']['gate_max_sing']}")
    print(f"  N=200  lift: ${summary['best_gate']['lift_dol_per_1000h_n200']:+.2f}/1000h")
    print(f"  N=1000 lift: ${summary['best_gate']['lift_dol_per_1000h_n1000']:+.2f}/1000h")
    print(f"  Two-grid verdict: {summary['best_gate']['verdict_two_grid']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
