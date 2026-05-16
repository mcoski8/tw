"""S89 grader for strategy_v63 vs strategy_v62 (current production) on the full grid.

By construction v63 only differs from v62 on the EXTRA cells added in S89:
    HIGH_ONLY × JOINT_MED × {J-A}
    HIGH_ONLY × JOINT_LOW × {J-A}
(48,132 hands total in S71 parquet).

On the S87 cell (DS_NO_JOINT × J-A) and S88 cells (DS_NO_MAXTOP/MS_ONLY/JOINT_HIGH × J-A),
v63 == v62 by construction (both gate-out to v44_dt). Outside the v63 gate,
v63 == v62 == v57.

Therefore:
    whole_grid_lift($/1000h) = (Σ v63_ev − Σ v62_ev) on the S89-extra cells × 10 × 1000 / 6,009,159
                             = cell_lift_normalized_to_full_grid

Grader steps:
  1. Load S71 parquet, filter to S89-extra cells.
  2. Re-evaluate v62 + v63 on each hand (fresh).
  3. Compute lift + per-cell × rank breakdown.
  4. Sanity-check v63 == v62 on a 50K-hand random sample OUTSIDE the S89-extra cells.
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
from strategy_v62_high_only_chain_fix import (  # noqa: E402
    strategy_v62_high_only_chain_fix,
)
from strategy_v63_high_only_chain_fix_full import (  # noqa: E402
    strategy_v63_high_only_chain_fix_full,
    _is_v63_gated_cell,
    _classify_high_only_cell,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PARQUET_S71 = ROOT / "data" / "drill_v44_high_only_S71_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

CELL_NAMES = {0: "JOINT_HIGH", 1: "JOINT_MED", 2: "JOINT_LOW",
              3: "DS_NO_JOINT", 4: "DS_NO_MAXTOP", 5: "MS_ONLY",
              6: "NEITHER"}
S89_EXTRA_TARGETS = [
    (1, (11, 12, 13, 14)),  # JOINT_MED × {J, Q, K, A}
    (2, (11, 12, 13, 14)),  # JOINT_LOW × {J, Q, K, A}
]
RANK_CHAR = {11: "J", 12: "Q", 13: "K", 14: "A"}

# Pre-committed verdict thresholds (LOCKED before grader runs)
# Reflects S89's smaller target population (48K hands vs S88's 357K hands).
# Pre-drill predicted ~$10/1000h; SHIP threshold $5 per the resume prompt;
# NULL threshold $1.
SHIP_THRESHOLD = 5.0    # whole-grid lift $/1000h
NULL_THRESHOLD = 1.0
# MIXED if NULL < lift < SHIP

SAMPLE_OUTSIDE = 50_000   # hands outside cell for v63==v62 sanity check
SAMPLE_SEED = 89


def main() -> int:
    print("=" * 90)
    print("S89 grade — strategy_v63 vs strategy_v62 (current production) on full grid")
    print("=" * 90)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()
    print(f"Pre-committed thresholds:")
    print(f"  SHIP if whole_grid_lift >= ${SHIP_THRESHOLD:.0f}/1000h")
    print(f"  NULL if whole_grid_lift <= ${NULL_THRESHOLD:.0f}/1000h")
    print(f"  MIXED in between")
    print()

    print("[1/4] loading S71 parquet + filtering to S89-extra cells ...",
          flush=True)
    df = pq.read_table(PARQUET_S71,
                       columns=["canonical_id", "max_rank", "cell_idx",
                                "ev_best"]).to_pandas()
    target_mask = np.zeros(len(df), dtype=bool)
    for cidx, ranks in S89_EXTRA_TARGETS:
        target_mask |= (df["cell_idx"] == cidx) & (df["max_rank"].isin(ranks))
    in_cell = df[target_mask].copy().reset_index(drop=True)
    print(f"  S89-extra cells: {len(in_cell):,} hands")
    print()

    print("[2/4] loading canonical hands + oracle grid (memmap) ...",
          flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    # === IN-CELL: re-evaluate v62 + v63 ===
    print(f"[3/4] evaluating v62 + v63 on {len(in_cell):,} in-cell hands ...",
          flush=True)
    n = len(in_cell)
    v62_ev = np.zeros(n, dtype=np.float32)
    v63_ev = np.zeros(n, dtype=np.float32)
    cids = in_cell["canonical_id"].to_numpy()
    in_cell_gate_check = np.zeros(n, dtype=bool)
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        in_cell_gate_check[k] = _is_v63_gated_cell(h)
        v62_ev[k] = float(rowf[int(strategy_v62_high_only_chain_fix(h))])
        v63_ev[k] = float(rowf[int(strategy_v63_high_only_chain_fix_full(h))])
        if (k + 1) % 10_000 == 0:
            elapsed = time.time() - t0
            print(f"    {k+1:>7,}/{n:,} ({elapsed:.1f}s)", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  v63 gate-match (S71 cell vs v63 detector): "
          f"{in_cell_gate_check.mean()*100:.2f}% "
          f"(should be 100% — sanity check)")
    print()

    in_cell["v62_ev"] = v62_ev
    in_cell["v63_ev"] = v63_ev
    in_cell["lift_per_hand"] = v63_ev - v62_ev  # positive = v63 wins
    cell_lift_ev = in_cell["lift_per_hand"].sum()
    cell_lift_dollars_per_1000h = cell_lift_ev * EV_TO_DOL * 1000 / N_TOTAL_GRID

    print("=" * 110)
    print("IN-CELL RESULT — v62 -> v63 lift (whole-grid normalized)")
    print("=" * 110)
    print(f"  cell hands: {n:,}")
    print(f"  total EV lift: {cell_lift_ev:.4f}")
    print(f"  whole-grid lift: ${cell_lift_dollars_per_1000h:+.2f}/1000h")
    print()
    print(f"  Per cell × rank breakdown:")
    print(f"  {'cell':>15} {'rank':>4} {'n':>9} {'cell_lift $':>13} "
          f"{'avg_lift_per_hand':>18}")
    for cidx, ranks in S89_EXTRA_TARGETS:
        for r in ranks:
            seg = in_cell[(in_cell["cell_idx"] == cidx)
                          & (in_cell["max_rank"] == r)]
            if len(seg) == 0:
                continue
            seg_lift = seg["lift_per_hand"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            avg_per_hand = seg["lift_per_hand"].mean() * EV_TO_DOL
            print(f"  {CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>9,} "
                  f"${seg_lift:>+11.2f} ${avg_per_hand:>+15.2f}")
    print()
    print(f"  Rolled up per cell:")
    print(f"  {'cell':>15} {'n':>9} {'cell_lift $':>13}")
    for cidx, ranks in S89_EXTRA_TARGETS:
        seg = in_cell[(in_cell["cell_idx"] == cidx)
                      & (in_cell["max_rank"].isin(ranks))]
        if len(seg) == 0:
            continue
        seg_lift = seg["lift_per_hand"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {CELL_NAMES[cidx]:>15} {len(seg):>9,} ${seg_lift:>+11.2f}")
    print()

    n_v63_changed = int((in_cell["v63_ev"] != in_cell["v62_ev"]).sum())
    n_v63_better = int((in_cell["v63_ev"] > in_cell["v62_ev"]).sum())
    n_v63_worse = int((in_cell["v63_ev"] < in_cell["v62_ev"]).sum())
    n_v63_same = n - n_v63_changed
    print(f"  Per-hand v62 -> v63 effect:")
    print(f"    v63 same as v62: {n_v63_same:>7,} ({100*n_v63_same/n:.1f}%)")
    print(f"    v63 BETTER:     {n_v63_better:>7,} ({100*n_v63_better/n:.1f}%)")
    print(f"    v63 WORSE:      {n_v63_worse:>7,} ({100*n_v63_worse/n:.1f}%)")
    swap_right_pct = 100 * n_v63_better / max(n_v63_changed, 1)
    print(f"    swap-right rate (of changed): {swap_right_pct:.1f}%")
    print()

    # === OUT-OF-CELL: sanity check that v63 == v62 ===
    print(f"[4/4] sanity check on {SAMPLE_OUTSIDE:,} out-of-cell hands ...",
          flush=True)
    rng = np.random.default_rng(SAMPLE_SEED)
    # Use random canonical_ids NOT in the S89-extra cells. Since the parquet only
    # covers HIGH_ONLY hands (1.2M of 6M), we sample from the full canonical_id
    # range and skip any that fall into the S89-extra cells.
    sample_ids_raw = rng.choice(N_TOTAL_GRID,
                                size=min(SAMPLE_OUTSIDE * 2, N_TOTAL_GRID),
                                replace=False)
    sample_ids_raw.sort()
    n_disagree = 0
    n_v63_gated_in_sample = 0
    n_checked = 0
    t0 = time.time()
    for cid_int in sample_ids_raw:
        cid = int(cid_int)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        if _is_v63_gated_cell(h):
            n_v63_gated_in_sample += 1
            continue  # in-gate hands are expected to potentially differ
        v62_pick = int(strategy_v62_high_only_chain_fix(h))
        v63_pick = int(strategy_v63_high_only_chain_fix_full(h))
        if v62_pick != v63_pick:
            n_disagree += 1
        n_checked += 1
        if n_checked >= SAMPLE_OUTSIDE:
            break
    print(f"  done in {time.time()-t0:.1f}s")
    print()
    print(f"  Out-of-gate sample: {n_checked:,} checked "
          f"(+{n_v63_gated_in_sample} skipped as in-gate)")
    print(f"    v63 != v62 disagreements outside gate: {n_disagree} "
          f"(SHOULD BE 0 — v63 == v62 outside the new S89 gate-out cells)")
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
        new_prod = 1610.04 + cell_lift_dollars_per_1000h
        print(f"  Implied production: $1,610.04 -> ${new_prod:.2f}/1000h "
              f"(+${cell_lift_dollars_per_1000h:.2f})")
        v44_baseline_full = 1081.0
        new_divergence = new_prod - v44_baseline_full
        print(f"  Implied production vs v44_dt: "
              f"${new_divergence:.2f}/1000h (was $529)")
        old_remaining_gap = 135.16
        new_remaining_gap = old_remaining_gap - cell_lift_dollars_per_1000h
        print(f"  Implied remaining gap to oracle ceiling: "
              f"${new_remaining_gap:.2f}/1000h (was $135.16)")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
