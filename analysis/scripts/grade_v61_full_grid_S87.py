"""S87 grader for strategy_v61 vs strategy_v57 on the full 6M-hand grid.

By construction v61 only differs from v57 on the target cell
(HIGH_ONLY x DS_NO_JOINT x max in {J,Q,K,A}, ~756K hands).
Outside that gate v61 == v57, so:
  whole_grid_lift($/1000h) = (v61_total_ev - v57_total_ev) * 10 * 1000 / 6_009_159
                           = cell_lift_normalized (since the divisor is N_TOTAL_GRID either way)

This grader:
  1. Loads the target-cell hands (756K) via S71 parquet filter.
  2. Re-evaluates v57 AND v61 on each (fresh, not relying on prior runs).
  3. Computes cell lift + per-rank breakdown.
  4. Sanity-checks v61 == v57 on a 50K-hand random sample OUTSIDE the cell.
  5. Pre-committed verdict via SHIP_THRESHOLD.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from strategy_v57_lo_pair_defensive import strategy_v57_lo_pair_defensive  # noqa: E402
from strategy_v61_high_only_ds_no_joint_fix import (  # noqa: E402
    strategy_v61_high_only_ds_no_joint_fix,
    _is_high_only_ds_no_joint,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PARQUET_S71 = ROOT / "data" / "drill_v44_high_only_S71_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
DS_NO_JOINT = 3
TARGET_RANKS = (11, 12, 13, 14)
RANK_CHAR = {11: "J", 12: "Q", 13: "K", 14: "A"}

# Pre-committed verdict thresholds (LOCKED before grader runs)
SHIP_THRESHOLD = 30.0   # whole-grid lift $/1000h
NULL_THRESHOLD = 5.0
# MIXED if NULL < lift < SHIP

SAMPLE_OUTSIDE = 50_000   # hands outside cell for v61==v57 sanity check
SAMPLE_SEED = 42


def main() -> int:
    print("=" * 90)
    print("S87 grade — strategy_v61 vs strategy_v57 on full grid")
    print("=" * 90)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()
    print(f"Pre-committed thresholds:")
    print(f"  SHIP if whole_grid_lift >= ${SHIP_THRESHOLD:.0f}/1000h")
    print(f"  NULL if whole_grid_lift <= ${NULL_THRESHOLD:.0f}/1000h")
    print(f"  MIXED in between")
    print()

    print("[1/4] loading S71 parquet + filtering to target cell ...", flush=True)
    df = pq.read_table(PARQUET_S71,
                       columns=["canonical_id", "max_rank", "cell_idx",
                                "ev_best"]).to_pandas()
    mask = (df["cell_idx"] == DS_NO_JOINT) & (df["max_rank"].isin(TARGET_RANKS))
    in_cell = df[mask].copy().reset_index(drop=True)
    print(f"  target cell: {len(in_cell):,} hands")
    print()

    print("[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    # === IN-CELL: re-evaluate both v57 and v61, compute lift ===
    print(f"[3/4] evaluating v57 + v61 on {len(in_cell):,} in-cell hands ...",
          flush=True)
    n = len(in_cell)
    v57_ev = np.zeros(n, dtype=np.float32)
    v61_ev = np.zeros(n, dtype=np.float32)
    cids = in_cell["canonical_id"].to_numpy()
    in_cell_double_check = np.zeros(n, dtype=bool)
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        in_cell_double_check[k] = _is_high_only_ds_no_joint(h)
        v57_ev[k] = float(rowf[int(strategy_v57_lo_pair_defensive(h))])
        v61_ev[k] = float(rowf[int(strategy_v61_high_only_ds_no_joint_fix(h))])
        if (k + 1) % 100_000 == 0:
            elapsed = time.time() - t0
            print(f"    {k+1:>7,}/{n:,} ({elapsed:.1f}s)", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  v61 gate match (S71 cell vs v61 detector): "
          f"{in_cell_double_check.mean()*100:.2f}% "
          f"(should be 100% — sanity check)")
    print()

    in_cell["v57_ev"] = v57_ev
    in_cell["v61_ev"] = v61_ev
    in_cell["lift_per_hand"] = v61_ev - v57_ev  # positive = v61 wins
    cell_lift_ev = in_cell["lift_per_hand"].sum()
    cell_lift_dollars_per_1000h = cell_lift_ev * EV_TO_DOL * 1000 / N_TOTAL_GRID

    print("=" * 110)
    print("IN-CELL RESULT — v57 -> v61 lift (whole-grid normalized)")
    print("=" * 110)
    print(f"  cell hands: {n:,}")
    print(f"  total EV lift: {cell_lift_ev:.4f}")
    print(f"  whole-grid lift: ${cell_lift_dollars_per_1000h:+.2f}/1000h")
    print()
    print(f"  Per max_rank breakdown:")
    print(f"  {'rank':>4} {'n':>9} {'cell_lift $':>13} "
          f"{'avg_lift_per_hand':>18}")
    for r in TARGET_RANKS:
        seg = in_cell[in_cell["max_rank"] == r]
        if len(seg) == 0:
            continue
        seg_lift = seg["lift_per_hand"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        avg_per_hand = seg["lift_per_hand"].mean() * EV_TO_DOL
        print(f"  {RANK_CHAR[r]:>4} {len(seg):>9,} "
              f"${seg_lift:>+11.2f} ${avg_per_hand:>+15.2f}")
    n_v61_changed = int((in_cell["v61_ev"] != in_cell["v57_ev"]).sum())
    n_v61_better = int((in_cell["v61_ev"] > in_cell["v57_ev"]).sum())
    n_v61_worse = int((in_cell["v61_ev"] < in_cell["v57_ev"]).sum())
    print()
    print(f"  Per-hand v57 -> v61 effect:")
    print(f"    v61 same as v57: {n - n_v61_changed:>7,} ({100*(n - n_v61_changed)/n:.1f}%)")
    print(f"    v61 BETTER:     {n_v61_better:>7,} ({100*n_v61_better/n:.1f}%)")
    print(f"    v61 WORSE:      {n_v61_worse:>7,} ({100*n_v61_worse/n:.1f}%)")
    swap_right_pct = 100 * n_v61_better / max(n_v61_changed, 1)
    print(f"    swap-right rate (of changed): {swap_right_pct:.1f}%")
    print()

    # === OUT-OF-CELL: sanity check that v61 == v57 ===
    print(f"[4/4] sanity check on {SAMPLE_OUTSIDE:,} out-of-cell hands ...",
          flush=True)
    rng = np.random.default_rng(SAMPLE_SEED)
    # Pick canonical_ids NOT in cell
    out_of_cell_ids = df[~mask]["canonical_id"].to_numpy()
    sample_ids = rng.choice(out_of_cell_ids,
                            size=min(SAMPLE_OUTSIDE, len(out_of_cell_ids)),
                            replace=False)
    sample_ids.sort()
    n_disagree = 0
    n_in_cell_detected = 0
    t0 = time.time()
    for k, cid in enumerate(sample_ids):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        if _is_high_only_ds_no_joint(h):
            n_in_cell_detected += 1
            # v61 detector should not fire here (we filtered out by S71)
            # except possibly for non-HIGH_ONLY cells where _is_high_only..
            # could be true (it shouldn't be)
            continue
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        v61_pick = int(strategy_v61_high_only_ds_no_joint_fix(h))
        if v57_pick != v61_pick:
            n_disagree += 1
        if (k + 1) % 25_000 == 0:
            print(f"    {k+1:>7,}/{len(sample_ids):,}", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()
    print(f"  Out-of-cell sample: {len(sample_ids):,}")
    print(f"    v61 cell-detector unexpectedly fired: {n_in_cell_detected}")
    print(f"    v57 != v61 disagreements outside cell: {n_disagree} "
          f"(SHOULD BE 0)")
    print()

    # === Verdict ===
    print("=" * 110)
    print("VERDICT")
    print("=" * 110)
    print(f"  Whole-grid lift: ${cell_lift_dollars_per_1000h:+.2f}/1000h")
    if cell_lift_dollars_per_1000h >= SHIP_THRESHOLD:
        verdict = "SHIP"
    elif cell_lift_dollars_per_1000h >= NULL_THRESHOLD:
        verdict = "MIXED"
    else:
        verdict = "NULL"
    print(f"  Mechanical verdict: {verdict} "
          f"(SHIP >= ${SHIP_THRESHOLD:.0f}, NULL <= ${NULL_THRESHOLD:.0f})")
    if verdict == "SHIP":
        new_prod = 1412.53 + cell_lift_dollars_per_1000h
        print(f"  Implied production: $1,412.53 -> ${new_prod:.2f}/1000h "
              f"(+${cell_lift_dollars_per_1000h:.2f})")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
