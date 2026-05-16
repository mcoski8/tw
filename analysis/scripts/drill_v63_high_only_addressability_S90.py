"""S90 — addressability pre-drill for HIGH_ONLY × max ∈ {8, 9, T} cells under
v63 (production after S89).

This pivots OUT of the HIGH_ONLY × {J-A} zone (closed S89) into HIGH_ONLY ×
max ≤ T territory. The key architectural difference: max ≤ T hands route
through v52-DEFENSIVE-LOW rather than v52-fallthrough. v52-defensive-low was
specifically designed for these weak-high hands and may NOT carry the v47
chain bleed that drove three consecutive S87/S88/S89 ships.

PHASE A findings (logged in data/session90/phase_a_target_stats.log):
  - HIGH_ONLY × max=7: STRUCTURALLY EMPTY (only 6 ranks ≤ 7, need 7 distinct)
  - HIGH_ONLY × max=8 × JOINT_MED: STRUCTURALLY EMPTY (need mid_high ≥ 8 > max-1=7)
  - HIGH_ONLY × {8,9,T} × JOINT_HIGH: STRUCTURALLY EMPTY (need mid_high ≥ J > T-1=9)
  - HIGH_ONLY × {8,9,T} × NEITHER: STRUCTURALLY EMPTY (pigeonhole — same as {J-A})

  Non-empty target = 11 (rank, cell) combinations:
    rank=8 × {JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY}                    (4 combos)
    rank=9 × {JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY}         (5 combos)
    rank=T × {JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY}         (5 combos)

  Cell sizes (cells_order = JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT,
  DS_NO_MAXTOP, MS_ONLY, NEITHER):
    JOINT_MED          3,150 hands  v44_baseline_leak $0.6483/1000h
    JOINT_LOW            630 hands                    $0.0714/1000h
    DS_NO_JOINT       16,200 hands                    $6.4077/1000h
    DS_NO_MAXTOP       3,456 hands                    $1.4087/1000h
    MS_ONLY            2,304 hands                    $0.7455/1000h
    TOTAL             25,740 hands                    $9.2816/1000h

  All prefix-silent (cid_min ≥ 590,496; prefix ends at 499,999). Whole-grid
  measurement is the only available one until Option C N=1000 oracle is built.

  v44 baseline leak is HIGHER per-hand than S89 ({J-A}): $9.28 on 25.7K vs
  $6.37 on 48.1K. So v44 has more 'room to be worse' on these hands.

The PIVOT-GATE pattern (S87/S88/S89): measure v63 leak on each cell BEFORE
designing any new rule. If v63 leaks materially MORE than v44 — same as the
S87/S88/S89 chain-bleed finding — the chain (v47/v48/v52) is also net-
negative on these cells and we extend the v63 gate-out to a v64.

But the open question is whether v52-defensive-low (which fires for max ≤ T)
carries the v47 chain bleed. v52-defensive-low was designed specifically for
weak-high HIGH_ONLY hands. Possible outcomes:
  (P1) v63 ≈ v44 on these cells: v52-defensive-low is well-designed,
       chain-audit lever is exhausted on HIGH_ONLY zone. CLEAN NULL.
  (P2) v63 leaks MORE than v44: chain bleed extends to max ≤ T. Ship v64.
  (P3) v63 leaks LESS than v44: v52-defensive-low actively IMPROVES on v44
       (chain is net-positive). PASS — don't gate.

This script mirrors `drill_v62_high_only_addressability_S89.py` but
evaluates v63 (NOT v62) and targets the {8,9,T} cells.
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
from strategy_v63_high_only_chain_fix_full import (  # noqa: E402
    strategy_v63_high_only_chain_fix_full,
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

# Target cells (cell_idx) × target ranks. Phase A structural feasibility
# pruning already applied — only non-empty combinations listed.
TARGETS = [
    (1, (9, 10)),               # JOINT_MED × {9, T}     (max=8 structurally empty)
    (2, (8, 9, 10)),            # JOINT_LOW × {8, 9, T}
    (3, (8, 9, 10)),            # DS_NO_JOINT × {8, 9, T}
    (4, (8, 9, 10)),            # DS_NO_MAXTOP × {8, 9, T}
    (5, (8, 9, 10)),            # MS_ONLY × {8, 9, T}
]
RANK_CHAR = {8: "8", 9: "9", 10: "T"}


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
    print("S90 addressability pre-drill — HIGH_ONLY × {8, 9, T} under v63")
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
    print(f"  filtered to S90 target cells: {len(sub):,} hands")
    print()

    print("[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] evaluating v63 on {len(sub):,} hands ...", flush=True)
    n = len(sub)
    v63_idx = np.zeros(n, dtype=np.int16)
    v63_ev = np.zeros(n, dtype=np.float32)
    v63_rank = np.zeros(n, dtype=np.int16)

    cids = sub["canonical_id"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        idx = int(strategy_v63_high_only_chain_fix_full(h))
        ev = float(rowf[idx])
        rnk = int((rowf > ev).sum()) + 1
        v63_idx[k] = idx
        v63_ev[k] = ev
        v63_rank[k] = rnk
        if (k + 1) % 5_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>6,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed={elapsed:>5.0f}s  ETA={eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    sub["v63_idx"] = v63_idx
    sub["v63_ev"] = v63_ev
    sub["v63_rank"] = v63_rank
    sub["v63_regret"] = sub["ev_best"] - sub["v63_ev"]
    sub["v63_bucket"] = sub["v63_rank"].apply(rank_bucket)
    sub["v44_bucket"] = sub["v44_rank"].apply(rank_bucket)
    sub["v63_overrides_v44"] = sub["v63_idx"] != sub["v44_idx"]

    # === Headline: per-cell v63 leak vs v44 leak (the bombshell metric) ===
    print("[4/4] results")
    print("=" * 110)
    print("HEADLINE — v63 vs v44_dt on HIGH_ONLY × {8,9,T} cells (per cell × rank)")
    print("=" * 110)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} {'v63=v44 %':>10} "
          f"{'v44 leak $':>11} {'v63 leak $':>11} "
          f"{'Δ (v63−v44)':>13} {'STR-only Δ':>11}")

    grand_v44 = 0.0
    grand_v63 = 0.0
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            agree_pct = 100 * (~seg["v63_overrides_v44"]).mean()
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v63_leak = seg["v63_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v63_leak - v44_leak
            seg_str = seg[seg["v63_bucket"] == "STRUCTURE"]
            v63_str = seg_str["v63_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            seg_str_v44 = seg[seg["v44_bucket"] == "STRUCTURE"]
            v44_str = seg_str_v44["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            str_delta = v63_str - v44_str
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"{agree_pct:>9.1f}% "
                  f"${v44_leak:>+9.2f} ${v63_leak:>+9.2f} "
                  f"${delta:>+11.2f} ${str_delta:>+9.2f}")
            grand_v44 += v44_leak
            grand_v63 += v63_leak
    print(f"  {'TOTAL':>15} {' ':>4} {len(sub):>8,} {' ':>9}  "
          f"${grand_v44:>+9.2f} ${grand_v63:>+9.2f} "
          f"${grand_v63-grand_v44:>+11.2f}")

    # === Per-cell rolled up ===
    print()
    print("=" * 110)
    print("ROLLED UP per cell (across all target ranks)")
    print("=" * 110)
    print(f"{'cell':>15} {'n':>8} {'v44 leak $':>11} {'v63 leak $':>11} {'Δ (v63−v44)':>13}")
    for cidx, ranks in TARGETS:
        seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"].isin(ranks))]
        if len(seg) == 0:
            continue
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v63_leak = seg["v63_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        delta = v63_leak - v44_leak
        print(f"{CELL_NAMES[cidx]:>15} {len(seg):>8,} ${v44_leak:>+9.2f} "
              f"${v63_leak:>+9.2f} ${delta:>+11.2f}")

    # === Gate diagnostic ===
    print()
    print("=" * 110)
    print("ADDRESSABILITY GATE — per cell × rank")
    print("=" * 110)
    print("  Gate criteria for SHIPPING a v64 chain gate-out extension:")
    print("    (a) Δ (v63−v44) >= $1/1000h on the cell (chain is net-negative)")
    print("    (b) Cell's v44 leak >= $0.05/1000h (still has addressable residual;")
    print("        threshold from S89 — these cells are tiny)")
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
            v63_leak = seg["v63_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v63_leak - v44_leak
            gate_a = delta >= 1.0
            gate_b = v44_leak >= 0.05
            verdict = "GATE-OUT" if (gate_a and gate_b) else ("PASS" if delta < 0 else "WEAK")
            print(f"  {CELL_NAMES[cidx]:>15} × {RANK_CHAR[r]} (n={len(seg):>6,}): "
                  f"v44=${v44_leak:>+6.2f}, v63=${v63_leak:>+6.2f}, "
                  f"Δ=${delta:>+6.2f}  → {verdict}")
    print()

    # === v63 override activity per cell ===
    print("=" * 110)
    print("v63 OVERRIDE ACTIVITY (sanity — does v63 differ from v44 on these cells?)")
    print("=" * 110)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} {'n_override':>11} {'pct_override':>13}")
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            n_over = int(seg["v63_overrides_v44"].sum())
            pct = 100 * n_over / len(seg)
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"{n_over:>11,} {pct:>12.1f}%")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
