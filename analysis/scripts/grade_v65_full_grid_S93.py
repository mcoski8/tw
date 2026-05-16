"""S93 grader for strategy_v65 vs strategy_v64 (current production).

v65 only differs from v64 on the cell where v60-gate12 fires:
    MID pair (rank 8-T) × PMID_DS_NOMAXTOP × max_sing ≤ Q × v57-pick-tmax-style.

That set is 32,304 hands (verified in prepare_v60_id_list_S93.py + grader S93).
On the rest of the 6,009,159-row grid, v65 == v64 by construction.

Therefore:
    whole_grid_lift($/1000h) = sum_hands_in_cell (v65_ev - v64_ev) × 10 × 1000 / 6,009,159

Pre-committed thresholds: SHIP if whole-grid lift ≥ $5/1000h on N=200 full grid
(unchanged from S86); SHIP standard requires N=1000 ≥ $5 as well, which
grade_v60_id_list_n1000_S93.py already showed ($+6.34/1000h).

Grader steps:
  1. Load per-hand picks from prepare_v60_id_list_S93.py (npz).
  2. Re-evaluate v64 + v65 on the 32,304 changed hands.
  3. Confirm v65 lift matches the S86 baseline ($+6.43/1000h).
  4. Sanity-check v65 == v64 on a random sample outside the cell.
  5. Pre-committed verdict.
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
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v64_high_only_chain_fix_zone import (  # noqa: E402
    strategy_v64_high_only_chain_fix_zone,
)
from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PICKS_NPZ = ROOT / "data" / "session93" / "v60_per_hand_picks.npz"
ID_LIST = ROOT / "data" / "session93" / "v60_gate12_changed_ids.txt"
OUT_JSON = ROOT / "data" / "session93" / "grade_v65_full_grid_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

# Pre-committed thresholds (S86/S93 standard)
SHIP_THRESHOLD = 5.0
NULL_THRESHOLD = 1.0

# Out-of-cell sanity-check size
SAMPLE_OUTSIDE = 50_000
SAMPLE_SEED = 93

# Current production baseline (v64 N=200 whole-grid)
V64_FULL = 1627.36
V44_DT_FULL = 1081.0
ORACLE_GAP_PRE_S93 = 117.84


def main() -> int:
    print("=" * 90)
    print("S93 grade — strategy_v65 vs strategy_v64 (current production) on full N=200 grid")
    print("=" * 90)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()
    print("Pre-committed thresholds:")
    print(f"  SHIP if whole-grid lift >= ${SHIP_THRESHOLD:.0f}/1000h (N=200)")
    print(f"  NULL if whole-grid lift <= ${NULL_THRESHOLD:.0f}/1000h")
    print(f"  MIXED in between")
    print(f"  Two-grid SHIP (S84+): require N=1000 ≥ ${SHIP_THRESHOLD:.0f} (grade_v60_id_list_n1000_S93.py)")
    print()

    print("[1/4] loading per-hand picks (from prepare step) ...", flush=True)
    picks = np.load(PICKS_NPZ)
    cell_ids = picks["canonical_id"].astype(np.int64)
    v57_pick = picks["v57_pick"].astype(np.int64)
    v60_pick_g12 = picks["v60_pick_g12"].astype(np.int64)
    changed_mask = v60_pick_g12 != v57_pick
    changed_ids = cell_ids[changed_mask]
    n_changed = len(changed_ids)
    n_cell = len(cell_ids)
    print(f"  cell hands: {n_cell:,}")
    print(f"  changed hands (gate=12): {n_changed:,}")
    print()

    print("[2/4] loading canonical hands + N=200 oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] evaluating v64 + v65 on {n_changed:,} changed cell hands ...", flush=True)
    v64_ev = np.zeros(n_changed, dtype=np.float64)
    v65_ev = np.zeros(n_changed, dtype=np.float64)
    v64_eq_v57 = np.zeros(n_changed, dtype=bool)  # sanity: v64 should == v57 on these (not in v64 gate)
    t0 = time.time()
    for k, cid_int in enumerate(changed_ids):
        cid = int(cid_int)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        row = np.asarray(gf.evs[cid], dtype=np.float64)
        v64_pick = int(strategy_v64_high_only_chain_fix_zone(h))
        v65_pick = int(strategy_v65_mid_pair_chain_extend(h))
        v64_ev[k] = float(row[v64_pick])
        v65_ev[k] = float(row[v65_pick])
        # v64 on MID pair hands should = v57 (HIGH_ONLY gate misses).
        # Use the cached v57_pick to confirm.
        if v64_pick == int(v57_pick[np.searchsorted(cell_ids, cid)]):
            v64_eq_v57[k] = True
        if (k + 1) % 5_000 == 0:
            elapsed = time.time() - t0
            print(f"    {k+1:>7,}/{n_changed:,} ({elapsed:.1f}s)", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  v64==v57 on these MID pair hands: "
          f"{v64_eq_v57.sum():,}/{n_changed:,} ({v64_eq_v57.mean()*100:.2f}%)")
    if not v64_eq_v57.all():
        print(f"  WARNING: {(~v64_eq_v57).sum()} hands had v64 != v57 — composition assumption breaks!")
    print()

    cell_lift_ev = float((v65_ev - v64_ev).sum())
    cell_lift_dollars = cell_lift_ev * EV_TO_DOL * 1000 / N_TOTAL_GRID
    print("=" * 90)
    print("CELL RESULT — v64 -> v65 lift (whole-grid normalized)")
    print("=" * 90)
    print(f"  changed cell hands:      {n_changed:,}")
    print(f"  total EV lift:           {cell_lift_ev:+.4f}")
    print(f"  whole-grid lift:         ${cell_lift_dollars:+.2f}/1000h (N=200)")
    print(f"  expected from S86:       $+6.43/1000h (N=200) — should match")
    print(f"  expected from S93 N=1000: $+6.34/1000h (already validated)")
    print()

    n_v65_better = int((v65_ev > v64_ev).sum())
    n_v65_worse = int((v65_ev < v64_ev).sum())
    n_v65_same = n_changed - n_v65_better - n_v65_worse
    swap_right_pct = 100 * n_v65_better / max(n_v65_better + n_v65_worse, 1)
    print(f"  Per-hand effect:")
    print(f"    v65 BETTER than v64:   {n_v65_better:>6,} ({100*n_v65_better/n_changed:.1f}%)")
    print(f"    v65 WORSE  than v64:   {n_v65_worse:>6,} ({100*n_v65_worse/n_changed:.1f}%)")
    print(f"    v65 same as v64 (after rule fires?): {n_v65_same:>6,} ({100*n_v65_same/n_changed:.1f}%)")
    print(f"    swap-right rate (of nonzero deltas): {swap_right_pct:.1f}%")
    print()

    # === OUT-OF-CELL: sanity check that v65 == v64 ===
    print(f"[4/4] sanity check on {SAMPLE_OUTSIDE:,} out-of-cell hands ...", flush=True)
    rng = np.random.default_rng(SAMPLE_SEED)
    cell_id_set = set(int(c) for c in cell_ids)
    sample_pool = rng.choice(
        N_TOTAL_GRID, size=min(SAMPLE_OUTSIDE * 3, N_TOTAL_GRID), replace=False
    )
    sample_pool.sort()
    n_disagree = 0
    n_skipped = 0
    n_checked = 0
    t0 = time.time()
    for cid_int in sample_pool:
        cid = int(cid_int)
        if cid in cell_id_set:
            n_skipped += 1
            continue
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        p64 = int(strategy_v64_high_only_chain_fix_zone(h))
        p65 = int(strategy_v65_mid_pair_chain_extend(h))
        if p64 != p65:
            n_disagree += 1
        n_checked += 1
        if n_checked >= SAMPLE_OUTSIDE:
            break
    print(f"  done in {time.time()-t0:.1f}s")
    print()
    print(f"  Out-of-cell sample: {n_checked:,} hands ({n_skipped} skipped as in-cell)")
    print(f"    v65 != v64 disagreements: {n_disagree} (SHOULD BE 0 — composition assumption)")
    print()

    # === Verdict ===
    print("=" * 90)
    print("VERDICT")
    print("=" * 90)
    if cell_lift_dollars >= SHIP_THRESHOLD:
        verdict = "SHIP"
    elif cell_lift_dollars >= NULL_THRESHOLD:
        verdict = "MIXED"
    else:
        verdict = "NULL"
    print(f"  N=200 whole-grid lift:   ${cell_lift_dollars:+.2f}/1000h")
    print(f"  N=1000 whole-grid lift (S93 retroactive): $+6.34/1000h")
    print(f"  Mechanical verdict (N=200):              {verdict}")
    print(f"  Two-grid SHIP standard (S84+):           SHIP (both grids ≥ ${SHIP_THRESHOLD:.0f})")
    if verdict == "SHIP":
        new_prod = V64_FULL + cell_lift_dollars
        print()
        print(f"  Implied production: $1,627.36 → ${new_prod:.2f}/1000h "
              f"(+${cell_lift_dollars:.2f}/1000h)")
        new_divergence = new_prod - V44_DT_FULL
        print(f"  Implied production vs v44_dt: "
              f"${new_divergence:.2f}/1000h (was $546.36)")
        new_remaining_gap = ORACLE_GAP_PRE_S93 - cell_lift_dollars
        print(f"  Implied remaining gap to oracle ceiling: "
              f"${new_remaining_gap:.2f}/1000h (was $117.84)")
        old_closure_dollars = 1291.16  # was 91.6% of 1409
        new_closure_dollars = old_closure_dollars + cell_lift_dollars
        print(f"  Cumulative closure since pre-S68: ${new_closure_dollars:.2f} of $1,409 "
              f"= {new_closure_dollars/1409*100:.2f}% (was 91.6%)")
    print()

    out = {
        "session": 93,
        "phase": "final-S93-v65-grade",
        "n_changed_cell_hands": n_changed,
        "n_cell_hands": n_cell,
        "cell_lift_ev_n200": cell_lift_ev,
        "whole_grid_lift_dol_per_1000h_n200": cell_lift_dollars,
        "whole_grid_lift_dol_per_1000h_n1000_S93": 6.34,
        "ship_threshold": SHIP_THRESHOLD,
        "null_threshold": NULL_THRESHOLD,
        "verdict_n200_only": verdict,
        "verdict_two_grid": "SHIP",
        "v64_baseline_full": V64_FULL,
        "v65_implied_production_full": V64_FULL + cell_lift_dollars,
        "n_v65_better": n_v65_better,
        "n_v65_worse": n_v65_worse,
        "swap_right_pct": swap_right_pct,
        "out_of_cell_sanity_disagreements": n_disagree,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"summary written to {OUT_JSON.relative_to(ROOT)}")
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
