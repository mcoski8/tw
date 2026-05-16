"""S89 — addressability pre-drill for the REMAINING prefix-silent HIGH_ONLY
cells under v62 (production after S88).

Target cells (all 100% prefix-silent — canonical_id >= 590,709, prefix ends
at 499,999):
  - HIGH_ONLY x JOINT_MED x {J, Q, K, A}: 44,562 hands
  - HIGH_ONLY x JOINT_LOW x {J, Q, K, A}:  3,570 hands

(NEITHER × {J-A} is structurally empty in S71 — drop from target set.)

Combined target: 48,132 hands. Combined v44_dt baseline leak per S71 parquet:
~$6.37/1000h on full grid (much smaller per-cell than S87's $5.43 or S88's
$95.62, but the chain bleed magnitude is the open question).

The PIVOT GATE pattern (S87/S88): measure v62 leak on each cell before
designing any new rule. If v62 leaks materially MORE than v44 — same as
S87/S88's chain-bleed finding — the v47/v48/v52 chain is also net-negative
on these cells and we extend the v62 gate-out to a v63.

This script mirrors `drill_v61_high_only_addressability_S88.py` but
evaluates v62 (NOT v61) so the S88 ship is accounted for. Outside the v62
gate (which fires on the four S87+S88 cells), v62 == v57 by construction
and a v62-vs-v44 bleed indicates fresh attribution work for S89.
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
from strategy_v62_high_only_chain_fix import (  # noqa: E402
    strategy_v62_high_only_chain_fix,
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
    (1, (11, 12, 13, 14)),  # JOINT_MED × {J, Q, K, A}
    (2, (11, 12, 13, 14)),  # JOINT_LOW × {J, Q, K, A}
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
    print("S89 addressability pre-drill — JOINT_MED / JOINT_LOW under v62")
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
    print(f"  filtered to S89 target cells: {len(sub):,} hands")
    print()

    print("[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] evaluating v62 on {len(sub):,} hands ...", flush=True)
    n = len(sub)
    v62_idx = np.zeros(n, dtype=np.int16)
    v62_ev = np.zeros(n, dtype=np.float32)
    v62_rank = np.zeros(n, dtype=np.int16)

    cids = sub["canonical_id"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        idx = int(strategy_v62_high_only_chain_fix(h))
        ev = float(rowf[idx])
        rnk = int((rowf > ev).sum()) + 1
        v62_idx[k] = idx
        v62_ev[k] = ev
        v62_rank[k] = rnk
        if (k + 1) % 10_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>7,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed={elapsed:>5.0f}s  ETA={eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    sub["v62_idx"] = v62_idx
    sub["v62_ev"] = v62_ev
    sub["v62_rank"] = v62_rank
    sub["v62_regret"] = sub["ev_best"] - sub["v62_ev"]
    sub["v62_bucket"] = sub["v62_rank"].apply(rank_bucket)
    sub["v44_bucket"] = sub["v44_rank"].apply(rank_bucket)
    sub["v62_overrides_v44"] = sub["v62_idx"] != sub["v44_idx"]

    # === Headline: per-cell v62 leak vs v44 leak (the bombshell metric) ===
    print("[4/4] results")
    print("=" * 110)
    print("HEADLINE — v62 vs v44_dt on next-target HIGH_ONLY cells (per cell × rank)")
    print("=" * 110)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} {'v62=v44 %':>10} "
          f"{'v44 leak $':>11} {'v62 leak $':>11} "
          f"{'Δ (v62−v44)':>13} {'STR-only Δ':>11}")

    grand_v44 = 0.0
    grand_v62 = 0.0
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            agree_pct = 100 * (~seg["v62_overrides_v44"]).mean()
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v62_leak = seg["v62_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v62_leak - v44_leak
            seg_str = seg[seg["v62_bucket"] == "STRUCTURE"]
            v62_str = seg_str["v62_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            seg_str_v44 = seg[seg["v44_bucket"] == "STRUCTURE"]
            v44_str = seg_str_v44["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            str_delta = v62_str - v44_str
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"{agree_pct:>9.1f}% "
                  f"${v44_leak:>+9.2f} ${v62_leak:>+9.2f} "
                  f"${delta:>+11.2f} ${str_delta:>+9.2f}")
            grand_v44 += v44_leak
            grand_v62 += v62_leak
    print(f"  {'TOTAL':>15} {' ':>4} {len(sub):>8,} {' ':>9}  "
          f"${grand_v44:>+9.2f} ${grand_v62:>+9.2f} "
          f"${grand_v62-grand_v44:>+11.2f}")

    # === Per-cell rolled up ===
    print()
    print("=" * 110)
    print("ROLLED UP per cell (across all target ranks)")
    print("=" * 110)
    print(f"{'cell':>15} {'n':>8} {'v44 leak $':>11} {'v62 leak $':>11} {'Δ (v62−v44)':>13}")
    for cidx, ranks in TARGETS:
        seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"].isin(ranks))]
        if len(seg) == 0:
            continue
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v62_leak = seg["v62_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        delta = v62_leak - v44_leak
        print(f"{CELL_NAMES[cidx]:>15} {len(seg):>8,} ${v44_leak:>+9.2f} "
              f"${v62_leak:>+9.2f} ${delta:>+11.2f}")

    # === Gate diagnostic ===
    print()
    print("=" * 110)
    print("ADDRESSABILITY GATE — per cell × rank")
    print("=" * 110)
    print("  Gate criteria for SHIPPING a v63 chain gate-out extension:")
    print("    (a) Δ (v62−v44) >= $1/1000h on the cell (chain is net-negative)")
    print("    (b) Cell's v44 leak >= $0.05/1000h (still has addressable residual;")
    print("        threshold relaxed from $1 because these cells are tiny)")
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
            v62_leak = seg["v62_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v62_leak - v44_leak
            gate_a = delta >= 1.0
            gate_b = v44_leak >= 0.05
            verdict = "GATE-OUT" if (gate_a and gate_b) else ("PASS" if delta < 0 else "WEAK")
            print(f"  {CELL_NAMES[cidx]:>15} × {RANK_CHAR[r]} (n={len(seg):>6,}): "
                  f"v44=${v44_leak:>+6.2f}, v62=${v62_leak:>+6.2f}, "
                  f"Δ=${delta:>+6.2f}  → {verdict}")
    print()

    # === v62 override activity per cell ===
    print("=" * 110)
    print("v62 OVERRIDE ACTIVITY (sanity — does v62 differ from v44 on these cells?)")
    print("=" * 110)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} {'n_override':>11} {'pct_override':>13}")
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            n_over = int(seg["v62_overrides_v44"].sum())
            pct = 100 * n_over / len(seg)
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"{n_over:>11,} {pct:>12.1f}%")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
