"""S88 — addressability pre-drill for the next-largest prefix-silent
HIGH_ONLY cells under v61 (production after S87).

Target cells (all 100% prefix-silent — canonical_id >= 590,502, prefix ends
at 499,999):
  - HIGH_ONLY x DS_NO_MAXTOP x {K, A}: 133,056 hands, $15.30 v44 STR
  - HIGH_ONLY x MS_ONLY x {J, Q, K, A}: 107,520 hands, $13.53 v44 STR
  - HIGH_ONLY x JOINT_HIGH x {K, A}: 116,928 hands, $4.95 v44 STR

Combined: 357,504 hands, $33.78 v44 STR / $95.62 cell-wide v44 leak.

The PIVOT GATE pattern (S87): measure v61 leak on each cell before designing
any new rule. If v61 leaks ~$8/1000h or more vs v44 — same as S87's v57 vs
v44 chain bleed — then the v47/v48/v52 chain is also net-negative on these
cells and we extend the v61 gate-out.

This script mirrors `drill_v57_high_only_addressability_S87.py` but
evaluates v61 (NOT v57) so any S87 ship is accounted for. Outside the v61
gate (which fires only on DS_NO_JOINT x J-A), v61 == v57 by construction
and a v61-vs-v44 bleed indicates fresh attribution work for S88.
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
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
from strategy_v61_high_only_ds_no_joint_fix import (  # noqa: E402
    strategy_v61_high_only_ds_no_joint_fix,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PARQUET_S71 = ROOT / "data" / "drill_v44_high_only_S71_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_SETTINGS = 105

# Cell taxonomy index from S71:
#   CELLS_ORDER = [JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT,
#                  DS_NO_MAXTOP, MS_ONLY, NEITHER]
CELL_NAMES = {0: "JOINT_HIGH", 1: "JOINT_MED", 2: "JOINT_LOW",
              3: "DS_NO_JOINT", 4: "DS_NO_MAXTOP", 5: "MS_ONLY",
              6: "NEITHER"}

TARGETS = [
    (4, (13, 14)),          # DS_NO_MAXTOP × {K, A}
    (5, (11, 12, 13, 14)),  # MS_ONLY × {J, Q, K, A}
    (0, (13, 14)),          # JOINT_HIGH × {K, A}
]
RANK_CHAR = {11: "J", 12: "Q", 13: "K", 14: "A"}


def rank_bucket(rank: int) -> str:
    if rank == 1:
        return "MATCH"
    if rank <= 3:
        return "NOISE"
    if rank <= 9:
        return "MID"
    return "STRUCTURE"


def main() -> int:
    print("=" * 100)
    print("S88 addressability pre-drill — DS_NO_MAXTOP / MS_ONLY / JOINT_HIGH under v61")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/4] loading S71 per-hand parquet ...", flush=True)
    table = pq.read_table(PARQUET_S71,
                          columns=["canonical_id", "max_rank", "cell_idx",
                                   "v44_idx", "oracle_idx", "v44_rank",
                                   "regret", "ev_best", "ev_v44"])
    df = table.to_pandas()
    print(f"  loaded {len(df):,} rows")

    target_mask = np.zeros(len(df), dtype=bool)
    for cidx, ranks in TARGETS:
        target_mask |= (df["cell_idx"] == cidx) & (df["max_rank"].isin(ranks))
    sub = df[target_mask].copy().reset_index(drop=True)
    print(f"  filtered to S88 target cells: {len(sub):,} hands")
    print()

    print("[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] evaluating v61 on {len(sub):,} hands ...", flush=True)
    n = len(sub)
    v61_idx = np.zeros(n, dtype=np.int16)
    v61_ev = np.zeros(n, dtype=np.float32)
    v61_rank = np.zeros(n, dtype=np.int16)

    cids = sub["canonical_id"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        idx = int(strategy_v61_high_only_ds_no_joint_fix(h))
        ev = float(rowf[idx])
        rnk = int((rowf > ev).sum()) + 1
        v61_idx[k] = idx
        v61_ev[k] = ev
        v61_rank[k] = rnk
        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>7,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed={elapsed:>5.0f}s  ETA={eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    sub["v61_idx"] = v61_idx
    sub["v61_ev"] = v61_ev
    sub["v61_rank"] = v61_rank
    sub["v61_regret"] = sub["ev_best"] - sub["v61_ev"]
    sub["v61_bucket"] = sub["v61_rank"].apply(rank_bucket)
    sub["v44_bucket"] = sub["v44_rank"].apply(rank_bucket)
    sub["v61_overrides_v44"] = sub["v61_idx"] != sub["v44_idx"]

    # === Headline: per-cell v61 leak vs v44 leak (the bombshell metric) ===
    print("[4/4] results")
    print("=" * 110)
    print("HEADLINE — v61 vs v44_dt on next-target HIGH_ONLY cells (per cell × rank)")
    print("=" * 110)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} {'v61=v44 %':>10} "
          f"{'v44 leak $':>11} {'v61 leak $':>11} "
          f"{'Δ (v61−v44)':>13} {'STR-only Δ':>11}")

    grand_v44 = 0.0
    grand_v61 = 0.0
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            agree_pct = 100 * (~seg["v61_overrides_v44"]).mean()
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v61_leak = seg["v61_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v61_leak - v44_leak
            seg_str = seg[seg["v61_bucket"] == "STRUCTURE"]
            v61_str = seg_str["v61_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            seg_str_v44 = seg[seg["v44_bucket"] == "STRUCTURE"]
            v44_str = seg_str_v44["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            str_delta = v61_str - v44_str
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"{agree_pct:>9.1f}% "
                  f"${v44_leak:>+9.2f} ${v61_leak:>+9.2f} "
                  f"${delta:>+11.2f} ${str_delta:>+9.2f}")
            grand_v44 += v44_leak
            grand_v61 += v61_leak
    print(f"  {'TOTAL':>15} {' ':>4} {len(sub):>8,} {' ':>9}  "
          f"${grand_v44:>+9.2f} ${grand_v61:>+9.2f} "
          f"${grand_v61-grand_v44:>+11.2f}")

    # === Per-cell rolled up ===
    print()
    print("=" * 110)
    print("ROLLED UP per cell (across all target ranks)")
    print("=" * 110)
    print(f"{'cell':>15} {'n':>8} {'v44 leak $':>11} {'v61 leak $':>11} {'Δ (v61−v44)':>13}")
    for cidx, ranks in TARGETS:
        seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"].isin(ranks))]
        if len(seg) == 0:
            continue
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v61_leak = seg["v61_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        delta = v61_leak - v44_leak
        print(f"{CELL_NAMES[cidx]:>15} {len(seg):>8,} ${v44_leak:>+9.2f} "
              f"${v61_leak:>+9.2f} ${delta:>+11.2f}")

    # === Gate diagnostic ===
    print()
    print("=" * 110)
    print("ADDRESSABILITY GATE — per cell × rank")
    print("=" * 110)
    print("  Gate criteria for SHIPPING a v62 chain gate-out extension:")
    print("    (a) Δ (v61−v44) >= $1/1000h on the cell (chain is net-negative)")
    print("    (b) Cell's v44 leak >= $1/1000h (still has addressable residual)")
    print("    (c) Combined cell leak >= $5/1000h for cumulative ship-threshold")
    print()
    print("  If Δ negative or near zero: chain is already neutral/better than v44 on")
    print("  this cell — DON'T gate out (would regress).")
    print("  If Δ positive: chain bleeds — extend gate-out.")
    print()

    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v61_leak = seg["v61_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v61_leak - v44_leak
            gate_a = delta >= 1.0
            gate_b = v44_leak >= 1.0
            verdict = "GATE-OUT" if (gate_a and gate_b) else ("PASS" if delta < 0 else "WEAK")
            print(f"  {CELL_NAMES[cidx]:>15} × {RANK_CHAR[r]} (n={len(seg):>6,}): "
                  f"v44=${v44_leak:>+6.2f}, v61=${v61_leak:>+6.2f}, "
                  f"Δ=${delta:>+6.2f}  → {verdict}")
    print()

    # === v61 override activity per cell ===
    print("=" * 110)
    print("v61 OVERRIDE ACTIVITY (sanity — does v61 differ from v44 on these cells?)")
    print("=" * 110)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} {'n_override':>11} {'pct_override':>13}")
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            n_over = int(seg["v61_overrides_v44"].sum())
            pct = 100 * n_over / len(seg)
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"{n_over:>11,} {pct:>12.1f}%")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
