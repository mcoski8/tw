"""S92 — addressability pre-drill: two_pair cells under v64.

This pivots OUT of LOW pair (S91 NULL on prefix-COVERED chain audit) into
TWO_PAIR territory. ARCHITECTURAL PREDICTION (confirmed before compute via
strategy code-trace):

  * For two_pair hands, **v55_two_pair_hybrid routes 100% to v44_dt
    (blanket)**. Per v55's design doc, the routing is a single binary check:
    "if hand is two_pair → strategy_v44_dt; else → strategy_v54_pair_hybrid."

  * v56_trips_hybrid does not fire on two_pair (gates on exactly_one_trip).
  * v57_lo_pair_defensive does not fire on two_pair (gates on single LOW pair).
  * v64_high_only_chain_fix_zone does not fire on two_pair (gates on HIGH_ONLY).

  Therefore production v64 pick ≡ v44_dt pick on EVERY two_pair hand.

  Δ(v64 − v44_dt) on every two_pair cell is structurally $0.00.

This means the chain-audit pattern (S87-S91: find a layer that bleeds vs
v44_dt, gate it out) cannot find a SHIP candidate within two_pair —
v55's blanket routing has already collapsed the chain to v44_dt.

This script CONFIRMS that prediction empirically on the full 1.34M-hand
drill, then produces the architectural snapshot for documentation:
  - per-cell n + cid_min + cid_max + prefix coverage
  - per-cell v44_dt leak vs oracle (= v64 leak by structural equivalence)
  - per-cell × max_sing breakdown (full grid)
  - prefix-grid version

PHASE A findings (pre-drill, from parquet metadata):
  cell taxonomy (cell_idx → name, n):
    0  LAYOUT_A_DS         257,400 hands
    1  LAYOUT_C_DS         308,880
    2  LAYOUT_B_DS         231,660
    3  LAYOUT_A_SS         437,580
    4  LAYOUT_C_SS_ONLY    90,090
    5  LAYOUT_B_SS_ONLY    12,870
    (6 LAYOUT_OTHER       0 — structurally empty for canonical two_pair)
    TOTAL                1,338,480 hands (= 22.3% of canonical grid)

  Aggregate v44_dt leak vs oracle: $80.81/1000h (whole-grid).
  This is the within-two_pair OPTIMIZATION CEILING. v64 == v44, so v64
  also leaks $80.81/1000h. The chain-audit pattern cannot recover any of
  this because the chain has been collapsed.

Expected runtime: ~4-5 min at ~5,000 hands/sec (full grid 1.34M).
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
from strategy_v64_high_only_chain_fix_zone import (  # noqa: E402
    strategy_v64_high_only_chain_fix_zone,
)
from strategy_v44_dt import strategy_v44_dt  # noqa: E402

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
PARQUET_TWO_PAIR = ROOT / "data" / "drill_two_pair_v44_per_hand_structural.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_PREFIX = 500_000

CELL_NAMES = {0: "LAYOUT_A_DS", 1: "LAYOUT_C_DS",
              2: "LAYOUT_B_DS", 3: "LAYOUT_A_SS",
              4: "LAYOUT_C_SS_ONLY", 5: "LAYOUT_B_SS_ONLY"}


def main() -> int:
    print("=" * 110)
    print("S92 addressability pre-drill — two_pair cells under v64")
    print("=" * 110)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()
    print("ARCHITECTURAL PREDICTION (from code trace, pre-compute):")
    print("  v55_two_pair_hybrid routes ALL two_pair → v44_dt (blanket).")
    print("  v56/v57/v64 gates don't fire on two_pair.")
    print("  Therefore v64 pick ≡ v44_dt pick on every two_pair hand.")
    print("  Δ(v64 − v44_dt) on every cell is structurally $0.00.")
    print("  This script CONFIRMS empirically + produces architectural snapshot.")
    print()

    print("[1/4] loading two_pair per-hand parquet ...", flush=True)
    table = pq.read_table(
        PARQUET_TWO_PAIR,
        columns=["canonical_id", "hi_pair_rank", "lo_pair_rank",
                 "max_sing_rank", "cell_idx", "v44_idx", "oracle_idx",
                 "regret"]
    )
    df = table.to_pandas()
    print(f"  loaded {len(df):,} two_pair rows")
    print()

    # === Phase A: structural / prefix coverage summary ===
    print("[2/4] Phase A — structural / prefix coverage summary")
    print("=" * 110)
    print(f"{'cell':<22} {'n':>10} {'cid_min':>9} {'cid_max':>10} "
          f"{'v44 leak $':>11} {'prefix_n':>10} {'prefix_v44 $':>13}")
    grand_v44 = 0.0
    grand_v44_p = 0.0
    grand_n_p = 0
    for ci in sorted(CELL_NAMES):
        seg = df[df["cell_idx"] == ci]
        if len(seg) == 0:
            continue
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        prefix_mask = seg["canonical_id"] < N_PREFIX
        seg_p = seg[prefix_mask]
        v44_leak_p = (seg_p["regret"].sum() * EV_TO_DOL * 1000 / N_PREFIX
                      if len(seg_p) > 0 else 0.0)
        print(f"{CELL_NAMES[ci]:<22} {len(seg):>10,} "
              f"{seg['canonical_id'].min():>9,} "
              f"{seg['canonical_id'].max():>10,} "
              f"${v44_leak:>+9.2f} {len(seg_p):>10,} ${v44_leak_p:>+11.2f}")
        grand_v44 += v44_leak
        grand_v44_p += v44_leak_p
        grand_n_p += len(seg_p)
    print(f"{'TOTAL':<22} {len(df):>10,} {'':>9} {'':>10} "
          f"${grand_v44:>+9.2f} {grand_n_p:>10,} ${grand_v44_p:>+11.2f}")
    print()
    print("  All 6 cells prefix-covered (low cid_min). Within-two_pair ceiling")
    print(f"  is ${grand_v44:.2f}/1000h (v44_dt residual leak vs oracle).")
    print()

    # === Phase B: evaluate v64 on every two_pair hand (confirm collapse) ===
    print(f"[3/4] evaluating v64 on {len(df):,} two_pair hands "
          f"(confirming v64 ≡ v44_dt by construction) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    n = len(df)
    v64_idx = np.zeros(n, dtype=np.int16)
    v64_ev = np.zeros(n, dtype=np.float32)
    v64_ev_prefix = np.zeros(n, dtype=np.float32)
    ev_best = np.zeros(n, dtype=np.float32)
    ev_best_prefix = np.zeros(n, dtype=np.float32)
    v44_ev_prefix = np.zeros(n, dtype=np.float32)

    cids = df["canonical_id"].to_numpy()
    v44_idxs = df["v44_idx"].to_numpy()
    t0 = time.time()
    mismatches = 0
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        idx = int(strategy_v64_high_only_chain_fix_zone(h))
        v64_idx[k] = idx
        v64_ev[k] = float(rowf[idx])
        ev_best[k] = float(rowf.max())
        if idx != int(v44_idxs[k]):
            mismatches += 1
        if cid < N_PREFIX:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            v64_ev_prefix[k] = float(rowp[idx])
            v44_ev_prefix[k] = float(rowp[int(v44_idxs[k])])
            ev_best_prefix[k] = float(rowp.max())
        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>9,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed={elapsed:>5.0f}s  ETA={eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  v64 ≠ v44_dt mismatches: {mismatches:,} / {n:,} "
          f"({100*mismatches/n:.4f}%)")
    print()

    df["v64_idx"] = v64_idx
    df["v64_ev"] = v64_ev
    df["v64_ev_prefix"] = v64_ev_prefix
    df["v44_ev_prefix"] = v44_ev_prefix
    df["ev_best"] = ev_best
    df["ev_best_prefix"] = ev_best_prefix
    df["v64_regret"] = df["ev_best"] - df["v64_ev"]
    df["v64_regret_prefix"] = df["ev_best_prefix"] - df["v64_ev_prefix"]
    df["v44_regret_prefix"] = df["ev_best_prefix"] - df["v44_ev_prefix"]
    df["v64_overrides_v44"] = df["v64_idx"] != df["v44_idx"]

    # === Phase B headline: per-cell v64 vs v44 ===
    print("[4/4] results — per cell × max_sing (full grid)")
    print("=" * 120)
    print("HEADLINE — two_pair v64 vs v44_dt (per cell, all hi_pair × max_sing aggregated)")
    print("=" * 120)
    print(f"{'cell':<22} {'n':>10} {'v44=v64 %':>10} "
          f"{'v44 leak $':>11} {'v64 leak $':>11} {'Δ (v64−v44)':>13}")
    grand_v44 = 0.0
    grand_v64 = 0.0
    for ci in sorted(CELL_NAMES):
        seg = df[df["cell_idx"] == ci]
        if len(seg) == 0:
            continue
        agree_pct = 100 * (~seg["v64_overrides_v44"]).mean()
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v64_leak = seg["v64_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        delta = v64_leak - v44_leak
        print(f"{CELL_NAMES[ci]:<22} {len(seg):>10,} {agree_pct:>9.1f}% "
              f"${v44_leak:>+9.2f} ${v64_leak:>+9.2f} ${delta:>+11.2f}")
        grand_v44 += v44_leak
        grand_v64 += v64_leak
    print(f"{'TOTAL':<22} {len(df):>10,} {'':>10} "
          f"${grand_v44:>+9.2f} ${grand_v64:>+9.2f} ${grand_v64-grand_v44:>+11.2f}")
    print()

    print("PREFIX GRID — per cell (cid < 500K)")
    print("=" * 120)
    print(f"{'cell':<22} {'n_prefix':>10} {'v44 prefix $':>13} "
          f"{'v64 prefix $':>13} {'Δ prefix':>10}")
    df_pf = df[df["canonical_id"] < N_PREFIX].copy()
    grand_v44_p = 0.0
    grand_v64_p = 0.0
    for ci in sorted(CELL_NAMES):
        seg = df_pf[df_pf["cell_idx"] == ci]
        if len(seg) == 0:
            continue
        v44_leak_p = seg["v44_regret_prefix"].sum() * EV_TO_DOL * 1000 / N_PREFIX
        v64_leak_p = seg["v64_regret_prefix"].sum() * EV_TO_DOL * 1000 / N_PREFIX
        delta_p = v64_leak_p - v44_leak_p
        print(f"{CELL_NAMES[ci]:<22} {len(seg):>10,} "
              f"${v44_leak_p:>+11.2f} ${v64_leak_p:>+11.2f} ${delta_p:>+8.2f}")
        grand_v44_p += v44_leak_p
        grand_v64_p += v64_leak_p
    print(f"{'TOTAL':<22} {len(df_pf):>10,} "
          f"${grand_v44_p:>+11.2f} ${grand_v64_p:>+11.2f} "
          f"${grand_v64_p-grand_v44_p:>+8.2f}")
    print()

    print("=" * 120)
    print("PER cell × max_sing — v64 vs v44 (two_pair = hi_pair {3-A} × lo_pair {2-K} aggregated)")
    print("=" * 120)
    print(f"{'cell':<22} {'max_sing':>10} {'n':>9} {'v64=v44%':>9} "
          f"{'v44 $':>9} {'v64 $':>9} {'Δ':>9}")
    for ci in sorted(CELL_NAMES):
        for ms in range(4, 15):
            seg = df[(df["cell_idx"] == ci) & (df["max_sing_rank"] == ms)]
            if len(seg) == 0:
                continue
            agree_pct = 100 * (~seg["v64_overrides_v44"]).mean()
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v64_leak = seg["v64_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v64_leak - v44_leak
            mark = " <" if abs(delta) >= 0.5 else ""
            print(f"{CELL_NAMES[ci]:<22} {ms:>10} {len(seg):>9,} "
                  f"{agree_pct:>8.1f}% ${v44_leak:>+7.2f} ${v64_leak:>+7.2f} "
                  f"${delta:>+7.2f}{mark}")

    print()
    print("=" * 120)
    print("ARCHITECTURAL CONFIRMATION (S92)")
    print("=" * 120)
    print(f"  v64 ≠ v44_dt mismatches: {mismatches:,} / {n:,} hands")
    print(f"  Δ(v64 − v44_dt) full grid:   ${grand_v64-grand_v44:>+8.2f}/1000h")
    print(f"  Δ(v64 − v44_dt) prefix grid: ${grand_v64_p-grand_v44_p:>+8.2f}/1000h")
    print()
    print("  STRUCTURAL FINDING: v55_two_pair_hybrid's blanket routing has")
    print("  collapsed the chain to v44_dt for all two_pair hands. No")
    print("  per-cell residual exists for the chain-audit pattern to gate out.")
    print()
    print("  IMPLICATION: chain-audit pattern produces structural NULL on")
    print("  two_pair (and by extension trips, which has identical v56")
    print("  blanket routing). The pattern's productive zone is bounded:")
    print("  it requires a chain layer that has NOT been collapsed by a")
    print("  prior router. See S91 methodology + S92 architectural finding.")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
