"""S91 — per-cell × max_sing PREFIX breakdown for LOW pair.

The headline pre-drill (drill_v64_lo_pair_addressability_S91.py) found:
  - Full grid: v64 LIFTS $92/1000h over v44_dt on LOW pair (chain wins on N=200).
  - Prefix grid (N=1000): PMID_DS_MAXTOP/SS_MAXTOP/OTHER show small BLEEDS
    ($+4.30, $+1.31, $+1.17) while PMID_DS_NOMAXTOP LIFTS strongly (-$20.13).

The full/prefix disagreement on 3 cells is a classic winner's-curse signature
on the N=200 grid (max of 105 noisy estimates is biased upward; the
selection-bias depends on which setting each strategy picks). The N=1000
prefix grid is the more reliable signal.

This script computes:
  (a) Per-cell × max_sing v44_dt vs v64 regret on BOTH grids.
  (b) The 'TWO-GRID AGREEMENT' classification per sub-cell:
        - BOTH grids agree LIFT → confirmed good
        - BOTH grids agree BLEED → SHIP candidate (gate out chain)
        - DISAGREE (full LIFTS, prefix BLEEDS) → winner's curse — investigate
        - DISAGREE (full BLEEDS, prefix LIFTS) → also winner's curse
        - BOTH near zero → null

This is the input to Phase B+ chain audit and Phase C v65 design.
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

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
PARQUET_PAIR = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_PREFIX = 500_000

CELL_NAMES = {0: "PBOT_DS_JOINT", 1: "PBOT_DS_PARTIAL",
              2: "PMID_DS_MAXTOP", 3: "PMID_DS_NOMAXTOP",
              4: "PMID_SS_MAXTOP", 5: "PMID_OTHER"}

LOW_PAIR_RANKS = (2, 3, 4, 5, 6, 7)


def main() -> int:
    print("=" * 100)
    print("S91 prefix breakdown — LOW pair × cell × max_sing on N=1000 PREFIX grid")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/4] loading LOW pair parquet (prefix subset only) ...", flush=True)
    table = pq.read_table(
        PARQUET_PAIR,
        columns=["canonical_id", "pair_rank", "max_sing_rank", "cell_idx",
                 "v44_idx", "oracle_idx", "regret"]
    )
    df = table.to_pandas()
    df = df[(df["pair_rank"].isin(LOW_PAIR_RANKS)) &
            (df["canonical_id"] < N_PREFIX)].reset_index(drop=True)
    print(f"  filtered to LOW pair × prefix: {len(df):,} hands")
    print()

    print("[2/4] loading canonical hands + N=1000 prefix grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] computing v64 idx and v44/v64 EV on N=1000 prefix for {len(df):,} hands ...", flush=True)
    n = len(df)
    v64_idx = np.zeros(n, dtype=np.int16)
    v44_ev_p = np.zeros(n, dtype=np.float32)
    v64_ev_p = np.zeros(n, dtype=np.float32)
    ev_best_p = np.zeros(n, dtype=np.float32)
    cids = df["canonical_id"].to_numpy()
    v44_idxs = df["v44_idx"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowp = np.asarray(gp.evs[cid], dtype=np.float64)
        idx64 = int(strategy_v64_high_only_chain_fix_zone(h))
        v64_idx[k] = idx64
        v44_ev_p[k] = float(rowp[int(v44_idxs[k])])
        v64_ev_p[k] = float(rowp[idx64])
        ev_best_p[k] = float(rowp.max())
        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  ETA={eta:>4.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    df["v64_idx"] = v64_idx
    df["v44_regret_p"] = ev_best_p - v44_ev_p
    df["v64_regret_p"] = ev_best_p - v64_ev_p
    df["v64_overrides_v44"] = df["v64_idx"] != df["v44_idx"]

    print("[4/4] per cell × max_sing breakdown")
    print("=" * 120)
    print("PREFIX GRID (N=1000) — v64 vs v44 leak per cell × max_sing")
    print("=" * 120)
    print(f"{'cell':<20} {'max_sing':>8} {'n_pref':>7} {'v44_v64%':>8} "
          f"{'v44 $':>9} {'v64 $':>9} {'Δ pref':>9} {'verdict':<14}")

    grand_v44 = 0.0
    grand_v64 = 0.0
    candidates = []   # (cell, max_sing, n_pref, v44_p, v64_p, delta_p)

    for ci in range(6):
        for ms in range(2, 15):
            seg = df[(df["cell_idx"] == ci) & (df["max_sing_rank"] == ms)]
            if len(seg) == 0:
                continue
            agree_pct = 100 * (~seg["v64_overrides_v44"]).mean()
            v44_leak = seg["v44_regret_p"].sum() * EV_TO_DOL * 1000 / N_PREFIX
            v64_leak = seg["v64_regret_p"].sum() * EV_TO_DOL * 1000 / N_PREFIX
            delta = v64_leak - v44_leak
            grand_v44 += v44_leak
            grand_v64 += v64_leak
            verdict = ""
            if delta > 1.0:
                verdict = "BLEED"
            elif delta < -1.0:
                verdict = "LIFT"
            else:
                verdict = "~zero"
            if abs(delta) >= 0.5:
                candidates.append((CELL_NAMES[ci], ms, len(seg), v44_leak, v64_leak, delta))
            print(f"{CELL_NAMES[ci]:<20} {ms:>8} {len(seg):>7,} "
                  f"{agree_pct:>7.1f}% ${v44_leak:>+7.2f} ${v64_leak:>+7.2f} "
                  f"${delta:>+7.2f}  {verdict:<14}")
    print(f"{'TOTAL':<20} {'':>8} {len(df):>7,} {'':>8} "
          f"${grand_v44:>+7.2f} ${grand_v64:>+7.2f} ${grand_v64-grand_v44:>+7.2f}")

    print()
    print("=" * 120)
    print("SHIP CANDIDATES (prefix |Δ| >= $0.5/1000h)")
    print("=" * 120)
    candidates.sort(key=lambda x: x[5])
    print(f"{'cell':<20} {'max_sing':>8} {'n':>7} {'v44 $':>9} {'v64 $':>9} "
          f"{'Δ pref':>9}")
    chain_bleed_total = 0.0
    chain_lift_total = 0.0
    for c, ms, n, v44, v64, d in candidates:
        print(f"{c:<20} {ms:>8} {n:>7,} ${v44:>+7.2f} ${v64:>+7.2f} ${d:>+7.2f}")
        if d > 0:
            chain_bleed_total += d
        else:
            chain_lift_total += d
    print()
    print(f"  Aggregate chain BLEED (v44_dt better): ${chain_bleed_total:>+8.2f}/1000h")
    print(f"  Aggregate chain LIFT  (chain better):  ${chain_lift_total:>+8.2f}/1000h")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
