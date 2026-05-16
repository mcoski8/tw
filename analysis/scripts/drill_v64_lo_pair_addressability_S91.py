"""S91 — addressability pre-drill: LOW pair cells under v64.

This pivots OUT of the HIGH_ONLY zone (fully audited through S87/S88/S89/S90)
into LOW pair (rank 2-7) territory. The architectural difference from
S87-S90:

  * LOW pair hands route through the v54/v55/v56 hybrid chain (S82-S83 era):
      v54 — pair PBOT_DS-feasible → v44_dt (selective ML).
            All other pair (PMID) AND non-pair → v53.
      v53 — Q-pair JOINT_PBOT_DS forced setting; else v52.
      v52 — HIGH_ONLY handler (defensive overrides); else v51 → ... → v44_dt.

  * v52, v51, v50, v48, v47, v46, v45 are all HIGH_ONLY-targeted. They do
    NOT fire on pair hands (which is what makes them HIGH_ONLY-specific).

  * v57 (Rule 29, S83) intercepts LOW × PMID_DS_NOMAXTOP × max_sing ≤ Q.

So for LOW pair hands:
  - PBOT_DS_JOINT     → v44_dt (v54 routes)
  - PBOT_DS_PARTIAL   → v44_dt (v54 routes)
  - PMID_DS_MAXTOP    → v44_dt (chain transparent — v52 doesn't fire)
  - PMID_DS_NOMAXTOP × max_sing ≤ Q → Rule 29 (v57 fires)
  - PMID_DS_NOMAXTOP × max_sing > Q → v44_dt (Rule 29 gates out)
  - PMID_SS_MAXTOP    → v44_dt
  - PMID_OTHER        → v44_dt

KEY METHODOLOGICAL ADVANTAGE: All LOW pair cells are PREFIX-COVERED (cid_min
between 61,085 and 62,041; prefix ends at 499,999). The prefix grader is a
REAL second check, unlike S87-S90's prefix-silent ships.

PHASE A findings (from drill_pair_v44_per_hand_structural.parquet):
  - LOW pair total: 1,292,544 hands.
  - All 6 cells prefix-covered.
  - Per-cell v44 leak vs oracle (the optimization ceiling):

    cell                n        cid_min   v44_leak ($/1000h)
    PBOT_DS_JOINT       171,072  61,110    $1.93
    PBOT_DS_PARTIAL     541,728  61,086    $8.37
    PMID_DS_MAXTOP      128,304  62,009    $3.32
    PMID_DS_NOMAXTOP    228,096  61,137    $8.74
    PMID_SS_MAXTOP      85,536   62,041    $2.52
    PMID_OTHER          137,808  61,085    $3.31
    TOTAL               1,292,544          $28.21

  Aggregate ceiling = $28.21/1000h. PMID_DS_NOMAXTOP and PBOT_DS_PARTIAL are
  the largest cells with the largest leaks; Rule 20 (S83, SHIPPED $16.81
  prefix) already addressed part of PMID_DS_NOMAXTOP. The audit question
  reduces to: does v64 RECOVER some of these leaks, or does it BLEED in any
  subset relative to v44?

The CHAIN-AUDIT pattern transferred:
  Compute v64 vs v44 leak per cell × max_sing. Three outcomes:
  (P1) v64 ≈ v44: chain is transparent (most likely for non-PMID_DS_NOMAXTOP
       cells since v52 doesn't fire on pair). Confirms v44 IS production.
  (P2) v64 LIFTS over v44 (v64 leak < v44 leak): Rule 29 is working as
       designed. Quantify the lift.
  (P3) v64 BLEEDS vs v44 (v64 leak > v44 leak): Rule 29 (or another layer)
       is causing regression on some subset. SHIP candidate: gate Rule 29
       on that subset.

This script computes per-cell × max_sing v64 vs v44 leaks on ALL 1.29M LOW
pair hands. Expected runtime ~5-7 min at ~5000 hands/sec.
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
    print("S91 addressability pre-drill — LOW pair (rank 2-7) cells under v64")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/5] loading LOW pair per-hand parquet ...", flush=True)
    table = pq.read_table(
        PARQUET_PAIR,
        columns=["canonical_id", "pair_rank", "max_sing_rank", "cell_idx",
                 "v44_idx", "oracle_idx", "regret"]
    )
    df = table.to_pandas()
    print(f"  loaded {len(df):,} rows")
    df = df[df["pair_rank"].isin(LOW_PAIR_RANKS)].reset_index(drop=True)
    print(f"  filtered to LOW pair: {len(df):,} hands")
    print()

    print("[2/5] loading canonical hands + oracle grids (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")
    print()

    # === Phase A — structural / prefix coverage summary ===
    print("[3/5] Phase A — structural / prefix coverage summary")
    print("=" * 100)
    print(f"{'cell':<20} {'n':>10} {'cid_min':>9} {'cid_max':>9} "
          f"{'v44_leak $':>10} {'prefix_n':>10} {'prefix_v44 $':>13}")
    for ci in range(6):
        seg = df[df["cell_idx"] == ci]
        if len(seg) == 0:
            continue
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        prefix_mask = seg["canonical_id"] < N_PREFIX
        seg_p = seg[prefix_mask]
        v44_leak_p = seg_p["regret"].sum() * EV_TO_DOL * 1000 / N_PREFIX
        print(f"{CELL_NAMES[ci]:<20} {len(seg):>10,} "
              f"{seg['canonical_id'].min():>9,} {seg['canonical_id'].max():>9,} "
              f"${v44_leak:>+8.2f} {len(seg_p):>10,} ${v44_leak_p:>+11.2f}")
    print()

    # === Phase B — evaluate v64 on every LOW pair hand ===
    print(f"[4/5] evaluating v64 on {len(df):,} LOW pair hands "
          f"(this is the heavy step) ...", flush=True)
    n = len(df)
    v64_idx = np.zeros(n, dtype=np.int16)
    v64_ev = np.zeros(n, dtype=np.float32)
    v64_ev_prefix = np.zeros(n, dtype=np.float32)

    # ev_best from grid (the column ev_best isn't in the parquet so compute)
    ev_best = np.zeros(n, dtype=np.float32)
    ev_best_prefix = np.zeros(n, dtype=np.float32)

    cids = df["canonical_id"].to_numpy()
    v44_idxs = df["v44_idx"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        idx = int(strategy_v64_high_only_chain_fix_zone(h))
        v64_idx[k] = idx
        v64_ev[k] = float(rowf[idx])
        ev_best[k] = float(rowf.max())
        if cid < N_PREFIX:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            v64_ev_prefix[k] = float(rowp[idx])
            ev_best_prefix[k] = float(rowp.max())
        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed={elapsed:>5.0f}s  ETA={eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    df["v64_idx"] = v64_idx
    df["v64_ev"] = v64_ev
    df["v64_ev_prefix"] = v64_ev_prefix
    df["ev_best"] = ev_best
    df["ev_best_prefix"] = ev_best_prefix
    df["v64_regret"] = df["ev_best"] - df["v64_ev"]
    df["v64_regret_prefix"] = df["ev_best_prefix"] - df["v64_ev_prefix"]
    df["v64_overrides_v44"] = df["v64_idx"] != df["v44_idx"]

    # === Headline: per-cell v64 vs v44 leak ===
    print("[5/5] results — per cell × max_sing")
    print("=" * 110)
    print("HEADLINE — LOW pair v64 vs v44_dt (per cell, all max_sing aggregated)")
    print("=" * 110)
    print(f"{'cell':<20} {'n':>9} {'v44=v64 %':>10} "
          f"{'v44 leak $':>11} {'v64 leak $':>11} {'Δ (v64−v44)':>13}")

    grand_v44 = 0.0
    grand_v64 = 0.0
    for ci in range(6):
        seg = df[df["cell_idx"] == ci]
        if len(seg) == 0:
            continue
        agree_pct = 100 * (~seg["v64_overrides_v44"]).mean()
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v64_leak = seg["v64_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        delta = v64_leak - v44_leak
        print(f"{CELL_NAMES[ci]:<20} {len(seg):>9,} {agree_pct:>9.1f}% "
              f"${v44_leak:>+9.2f} ${v64_leak:>+9.2f} ${delta:>+11.2f}")
        grand_v44 += v44_leak
        grand_v64 += v64_leak
    print(f"{'TOTAL':<20} {len(df):>9,} {'':>10} "
          f"${grand_v44:>+9.2f} ${grand_v64:>+9.2f} ${grand_v64-grand_v44:>+11.2f}")

    print()
    print("=" * 110)
    print("PER cell × max_sing — v64 vs v44 (LOW pair = rank 2-7 aggregated)")
    print("=" * 110)
    print(f"{'cell':<20} {'max_sing':>10} {'n':>9} {'v64=v44%':>9} "
          f"{'v44 $':>9} {'v64 $':>9} {'Δ':>9}")
    for ci in range(6):
        for ms in range(2, 15):
            seg = df[(df["cell_idx"] == ci) & (df["max_sing_rank"] == ms)]
            if len(seg) == 0:
                continue
            agree_pct = 100 * (~seg["v64_overrides_v44"]).mean()
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v64_leak = seg["v64_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v64_leak - v44_leak
            mark = " <"  if abs(delta) >= 0.5 else ""
            print(f"{CELL_NAMES[ci]:<20} {ms:>10} {len(seg):>9,} "
                  f"{agree_pct:>8.1f}% ${v44_leak:>+7.2f} ${v64_leak:>+7.2f} "
                  f"${delta:>+7.2f}{mark}")

    # === Prefix grid breakdown ===
    print()
    print("=" * 110)
    print("PREFIX GRID — per cell (cid < 500K)")
    print("=" * 110)
    print(f"{'cell':<20} {'n_prefix':>10} {'v44 prefix $':>13} "
          f"{'v64 prefix $':>13} {'Δ prefix':>10}")
    df_pf = df[df["canonical_id"] < N_PREFIX].copy()
    # parquet "regret" is N=200 (full-grid) regret. For the prefix grid we
    # need to recompute v44 regret on N=1000 oracle prefix grid.
    for ci in range(6):
        seg = df_pf[df_pf["cell_idx"] == ci]
        if len(seg) == 0:
            continue
        # We need v44 ev on prefix grid. Read each v44_idx from gp.
        v44_evp = np.zeros(len(seg), dtype=np.float32)
        cids_seg = seg["canonical_id"].to_numpy()
        v44i = seg["v44_idx"].to_numpy()
        for j, c in enumerate(cids_seg):
            v44_evp[j] = float(gp.evs[int(c)][int(v44i[j])])
        v44_regret_p = seg["ev_best_prefix"].to_numpy() - v44_evp
        v44_leak_p = v44_regret_p.sum() * EV_TO_DOL * 1000 / N_PREFIX
        v64_leak_p = seg["v64_regret_prefix"].sum() * EV_TO_DOL * 1000 / N_PREFIX
        delta_p = v64_leak_p - v44_leak_p
        print(f"{CELL_NAMES[ci]:<20} {len(seg):>10,} "
              f"${v44_leak_p:>+11.2f} ${v64_leak_p:>+11.2f} ${delta_p:>+8.2f}")

    print()
    print("=" * 110)
    print("INTERPRETATION GUIDE (S91 audit)")
    print("=" * 110)
    print("  Δ (v64−v44) > 0   → v64 BLEEDS vs v44 on this cell. SHIP candidate:")
    print("                       gate Rule 29 (or other override) on this subset.")
    print("  Δ (v64−v44) < 0   → v64 LIFTS over v44. (Confirms Rule 29 works as")
    print("                       designed. Or another rule is doing useful work.)")
    print("  Δ (v64−v44) ≈ 0   → chain transparent (most likely outside Rule 29's gate).")
    print("                       Confirms v44 IS production for these LOW pair hands.")
    print("  Differs from S87-S90 in that we have a TWO-GRID check now (prefix-")
    print("  COVERED cells). SHIP requires agreement on full AND prefix grids.")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
