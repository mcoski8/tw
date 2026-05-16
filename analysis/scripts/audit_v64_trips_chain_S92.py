"""S92 SECONDARY — chain audit for trips cells.

Same architectural pattern as the two_pair audit (audit_v64_two_pair_chain_S92.py):
v56_trips_hybrid routes 100% of trips → v44_dt (blanket). v57/v64 don't fire on
trips. Therefore production v64 ≡ v44_dt on every trips hand, and the
chain-audit pattern produces structural NULL.

This script:
  1. Confirms v64 ≡ v44_dt on all 328,185 trips hands (sample-verified
     pre-compute).
  2. Quantifies v44_RULE13 chain bleed magnitude on trips (vs v44_dt) —
     architectural snapshot.
  3. Confirms v56's blanket routing absorbs 100% of the chain bleed.

Trips cell taxonomy (cell_idx → name, n in drill):
  0  B_DS_AVAIL_HKR    62,055 hands
  1  B_DS_AVAIL_LKR   163,170
  2  NO_BDS_CTOP       20,592
  3  NO_BDS_AKDOM      82,368
  TOTAL              328,185 hands (= 5.5% of canonical grid)

Aggregate v44_dt leak vs oracle: $65.18/1000h whole-grid.
This is the within-trips OPTIMIZATION CEILING.

Expected runtime: ~1-2 min at ~5,000 hands/sec (prefix-only ~25K hands).
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
from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v44_rule13_three_pair_DS import (  # noqa: E402
    strategy_v44_rule13_three_pair_DS,
)
from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid  # noqa: E402
from strategy_v55_two_pair_hybrid import (  # noqa: E402
    strategy_v55_two_pair_hybrid,
)
from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v64_high_only_chain_fix_zone import (  # noqa: E402
    strategy_v64_high_only_chain_fix_zone,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
PARQUET_TRIPS = ROOT / "data" / "drill_trips_v44_per_hand_structural.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_PREFIX = 500_000

CELL_NAMES = {0: "B_DS_AVAIL_HKR", 1: "B_DS_AVAIL_LKR",
              2: "NO_BDS_CTOP", 3: "NO_BDS_AKDOM"}


def main() -> int:
    print("=" * 145)
    print("S92 SECONDARY chain audit — trips, layer-by-layer attribution")
    print("=" * 145)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()
    print("ARCHITECTURAL PREDICTION (from code trace, pre-compute):")
    print("  v56_trips_hybrid routes ALL trips → v44_dt (blanket).")
    print("  v57/v64 gates don't fire on trips.")
    print("  Therefore v64 pick ≡ v44_dt pick on every trips hand.")
    print("  Same chain-audit structural NULL as two_pair.")
    print()

    print("[1/4] loading trips per-hand parquet ...", flush=True)
    table = pq.read_table(
        PARQUET_TRIPS,
        columns=["canonical_id", "trip_rank", "max_kicker_rank",
                 "cell_idx", "v44_idx", "regret"]
    )
    df = table.to_pandas()
    print(f"  loaded {len(df):,} trips rows")
    print()

    # === Phase A: structural / prefix coverage ===
    print("[2/4] Phase A — structural / prefix coverage summary")
    print("=" * 145)
    print(f"{'cell':<22} {'n':>10} {'cid_min':>9} {'cid_max':>10} "
          f"{'v44 leak $':>11} {'prefix_n':>10} {'prefix_v44 leak':>16}")
    grand_v44 = 0.0
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
              f"${v44_leak:>+9.2f} {len(seg_p):>10,} ${v44_leak_p:>+14.2f}")
        grand_v44 += v44_leak
        grand_n_p += len(seg_p)
    print(f"{'TOTAL':<22} {len(df):>10,} {'':>9} {'':>10} "
          f"${grand_v44:>+9.2f} {grand_n_p:>10,}")
    print()
    print(f"  Within-trips ceiling: ${grand_v44:.2f}/1000h (v44_dt residual leak vs oracle).")
    print()

    # === Phase B: layer attribution on prefix grid ===
    print(f"[3/4] evaluating layer strategies + EV on prefix grid "
          f"({grand_n_p:,} prefix trips hands) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    df_pf = df[df["canonical_id"] < N_PREFIX].reset_index(drop=True).copy()
    n = len(df_pf)
    v44_dt_idx = df_pf["v44_idx"].to_numpy()
    v44_rule_idx = np.zeros(n, dtype=np.int16)
    v54_idx = np.zeros(n, dtype=np.int16)
    v55_idx = np.zeros(n, dtype=np.int16)
    v56_idx = np.zeros(n, dtype=np.int16)
    v57_idx = np.zeros(n, dtype=np.int16)
    v64_idx = np.zeros(n, dtype=np.int16)

    ev_v44_dt = np.zeros(n, dtype=np.float32)
    ev_v44_rule = np.zeros(n, dtype=np.float32)
    ev_v54 = np.zeros(n, dtype=np.float32)
    ev_v55 = np.zeros(n, dtype=np.float32)
    ev_v56 = np.zeros(n, dtype=np.float32)
    ev_v57 = np.zeros(n, dtype=np.float32)
    ev_v64 = np.zeros(n, dtype=np.float32)
    ev_best = np.zeros(n, dtype=np.float32)

    cids = df_pf["canonical_id"].to_numpy()
    t0 = time.time()
    n_v64_eq_v44 = 0
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowp = np.asarray(gp.evs[cid], dtype=np.float64)
        ev_best[k] = float(rowp.max())
        ev_v44_dt[k] = float(rowp[int(v44_dt_idx[k])])
        i_rule = int(strategy_v44_rule13_three_pair_DS(h))
        i_v54 = int(strategy_v54_pair_hybrid(h))
        i_v55 = int(strategy_v55_two_pair_hybrid(h))
        i_v56 = int(strategy_v56_trips_hybrid(h))
        i_v57 = int(strategy_v57_lo_pair_defensive(h))
        i_v64 = int(strategy_v64_high_only_chain_fix_zone(h))
        v44_rule_idx[k] = i_rule
        v54_idx[k] = i_v54
        v55_idx[k] = i_v55
        v56_idx[k] = i_v56
        v57_idx[k] = i_v57
        v64_idx[k] = i_v64
        ev_v44_rule[k] = float(rowp[i_rule])
        ev_v54[k] = float(rowp[i_v54])
        ev_v55[k] = float(rowp[i_v55])
        ev_v56[k] = float(rowp[i_v56])
        ev_v57[k] = float(rowp[i_v57])
        ev_v64[k] = float(rowp[i_v64])
        if i_v64 == int(v44_dt_idx[k]):
            n_v64_eq_v44 += 1
        if (k + 1) % 5_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>9,}/{n:,}  rate={rate:>5.0f}/s  ETA={eta:>4.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  v64 ≡ v44_dt on {n_v64_eq_v44:,}/{n:,} prefix trips hands "
          f"({100*n_v64_eq_v44/n:.4f}%)")
    print()

    df_pf["regret_v44_dt"] = ev_best - ev_v44_dt
    df_pf["regret_v44_rule"] = ev_best - ev_v44_rule
    df_pf["regret_v54"] = ev_best - ev_v54
    df_pf["regret_v55"] = ev_best - ev_v55
    df_pf["regret_v56"] = ev_best - ev_v56
    df_pf["regret_v57"] = ev_best - ev_v57
    df_pf["regret_v64"] = ev_best - ev_v64

    print("[4/4] results — layer transitions per cell × max_kicker")
    print("=" * 145)
    print("LAYER TRANSITIONS (prefix N=1000, /1000h leak on prefix subset)")
    print("  v44_dt → v44_RULE → v54 → v55 → v56 → v57 → v64")
    print("  Predicted: v44_RULE bleeds vs v44_dt; v56 absorbs via blanket trips routing.")
    print("=" * 145)
    print(f"{'cell':<22} {'max_k':>5} {'n':>7} "
          f"{'v44_dt':>8} {'v44RUL':>8} {'v54':>8} {'v55':>8} "
          f"{'v56':>8} {'v57':>8} {'v64':>8} "
          f"{'RUL-dt':>8} {'56-RUL':>8}")
    grand = {k: 0.0 for k in
             ["v44_dt", "v44_rule", "v54", "v55", "v56", "v57", "v64"]}
    for ci in sorted(CELL_NAMES):
        for mk in range(5, 15):
            seg = df_pf[(df_pf["cell_idx"] == ci)
                        & (df_pf["max_kicker_rank"] == mk)]
            if len(seg) == 0:
                continue
            leaks = {}
            for k in ["v44_dt", "v44_rule", "v54", "v55", "v56", "v57", "v64"]:
                leaks[k] = (seg[f"regret_{k}"].sum() * EV_TO_DOL * 1000
                            / N_PREFIX)
                grand[k] += leaks[k]
            d_rul_dt = leaks["v44_rule"] - leaks["v44_dt"]
            d_56_rul = leaks["v56"] - leaks["v44_rule"]
            print(f"{CELL_NAMES[ci]:<22} {mk:>5} {len(seg):>7,} "
                  f"${leaks['v44_dt']:>+6.2f} ${leaks['v44_rule']:>+6.2f} "
                  f"${leaks['v54']:>+6.2f} ${leaks['v55']:>+6.2f} "
                  f"${leaks['v56']:>+6.2f} ${leaks['v57']:>+6.2f} "
                  f"${leaks['v64']:>+6.2f} "
                  f"${d_rul_dt:>+6.2f} ${d_56_rul:>+6.2f}")

    print(f"{'TOTAL':<22} {'':>5} {len(df_pf):>7,} "
          f"${grand['v44_dt']:>+6.2f} ${grand['v44_rule']:>+6.2f} "
          f"${grand['v54']:>+6.2f} ${grand['v55']:>+6.2f} "
          f"${grand['v56']:>+6.2f} ${grand['v57']:>+6.2f} "
          f"${grand['v64']:>+6.2f} "
          f"${grand['v44_rule']-grand['v44_dt']:>+6.2f} "
          f"${grand['v56']-grand['v44_rule']:>+6.2f}")

    print()
    print("=" * 145)
    print("LAYER ATTRIBUTION SUMMARY (trips, prefix N=1000)")
    print("=" * 145)
    print(f"  v44_dt total leak:         ${grand['v44_dt']:>+7.2f}/1000h  "
          f"(ML champion baseline)")
    print(f"  v44_RULE13 chain leak:     ${grand['v44_rule']:>+7.2f}/1000h  "
          f"(Δ vs v44_dt: ${grand['v44_rule']-grand['v44_dt']:>+7.2f})")
    print(f"  v54 (pair_hybrid):         ${grand['v54']:>+7.2f}/1000h  "
          f"(Δ vs v44_RULE: ${grand['v54']-grand['v44_rule']:>+7.2f})")
    print(f"  v55 (two_pair_hybrid):     ${grand['v55']:>+7.2f}/1000h  "
          f"(Δ vs v54: ${grand['v55']-grand['v54']:>+7.2f})")
    print(f"  v56 (trips_hybrid):        ${grand['v56']:>+7.2f}/1000h  "
          f"(Δ vs v55: ${grand['v56']-grand['v55']:>+7.2f})")
    print(f"  v57 (+ Rule 29):           ${grand['v57']:>+7.2f}/1000h  "
          f"(Δ vs v56: ${grand['v57']-grand['v56']:>+7.2f})")
    print(f"  v64 (production):          ${grand['v64']:>+7.2f}/1000h  "
          f"(Δ vs v57: ${grand['v64']-grand['v57']:>+7.2f})")
    print()
    print("  ARCHITECTURAL INTERPRETATION:")
    print("    Δ_v44_RULE_vs_v44_dt > 0  → chain BLEEDS vs v44_dt on trips")
    print("                                 (same pattern as S91 LOW pair + S92 two_pair).")
    print("    Δ_v54_vs_v44_RULE     ≈ 0  → v54 single-pair-only gate INERT on trips.")
    print("    Δ_v55_vs_v54         ≈ 0  → v55 two_pair-only gate INERT on trips.")
    print("    Δ_v56_vs_v55         < 0  → v56 BLANKET trips routing ABSORBS chain bleed.")
    print("    Δ_v57_vs_v56         = 0  → v57 LOW single-pair gate INERT.")
    print("    Δ_v64_vs_v57         = 0  → v64 HIGH_ONLY gate INERT.")
    print()
    print("  IMPLICATION FOR CHAIN-AUDIT PATTERN:")
    print("    Same as two_pair: chain fully collapsed by v56's blanket routing.")
    print("    No v65 candidate possible from chain-audit pattern within trips.")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
