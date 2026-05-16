"""S87 — addressability pre-drill for HIGH_ONLY x DS_NO_JOINT cells under v57.

Reuses S71's per-hand parquet (which has cell_idx, v44_idx, oracle_idx, plus the
oracle EV row metrics) and re-evaluates each hand under v57 to measure:
  - v57 vs v44 agreement on the cell (does v52 already partially fix it?)
  - v57 STRUCTURE-bucket leak (the v44-baseline leak survives or not)
  - Single-direction-concentrated residual under v57 (the SHIP gate)

If v57 leaks ~ same as v44 with the same dominant mismatch direction, the
addressability gate PASSES and we can commit to the pivot. If v57 has already
collapsed the leak (large v57 vs v44 swap-right toward oracle), the cell is
mostly fixed and the pivot value is smaller.

Scope: J/Q/K/A-high x DS_NO_JOINT (the four big cells, n=755,978).
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
from strategy_v57_lo_pair_defensive import strategy_v57_lo_pair_defensive  # noqa: E402

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PARQUET_S71 = ROOT / "data" / "drill_v44_high_only_S71_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_SETTINGS = 105

# Cell taxonomy index from S71: CELLS_ORDER = [JOINT_HIGH, JOINT_MED, JOINT_LOW,
#   DS_NO_JOINT(3), DS_NO_MAXTOP, MS_ONLY, NEITHER]
DS_NO_JOINT = 3
TARGET_RANKS = (11, 12, 13, 14)
RANK_CHAR = {11: "J", 12: "Q", 13: "K", 14: "A"}


def rank_bucket(rank: int) -> str:
    if rank == 1:
        return "MATCH"
    if rank <= 3:
        return "NOISE"
    if rank <= 9:
        return "MID"
    return "STRUCTURE"


BUCKETS_ORDER = ("MATCH", "NOISE", "MID", "STRUCTURE")


def main() -> int:
    print("=" * 90)
    print("S87 addressability pre-drill — HIGH_ONLY x DS_NO_JOINT under v57")
    print("=" * 90)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/4] loading S71 per-hand parquet ...", flush=True)
    table = pq.read_table(PARQUET_S71,
                          columns=["canonical_id", "max_rank", "cell_idx",
                                   "v44_idx", "oracle_idx", "v44_rank",
                                   "regret", "ev_best", "ev_v44"])
    df = table.to_pandas()
    print(f"  loaded {len(df):,} rows")
    mask = (df["cell_idx"] == DS_NO_JOINT) & (df["max_rank"].isin(TARGET_RANKS))
    sub = df[mask].copy()
    print(f"  filtered to HIGH_ONLY x DS_NO_JOINT x rank in {{J,Q,K,A}}: "
          f"{len(sub):,} hands")
    print()

    print("[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] evaluating v57 on {len(sub):,} hands ...", flush=True)
    n = len(sub)
    v57_idx = np.zeros(n, dtype=np.int16)
    v57_ev = np.zeros(n, dtype=np.float32)
    v57_rank = np.zeros(n, dtype=np.int16)

    cids = sub["canonical_id"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        idx = int(strategy_v57_lo_pair_defensive(h))
        ev = float(rowf[idx])
        rnk = int((rowf > ev).sum()) + 1
        v57_idx[k] = idx
        v57_ev[k] = ev
        v57_rank[k] = rnk
        if (k + 1) % 100_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>7,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed={elapsed:>5.0f}s  ETA={eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    sub["v57_idx"] = v57_idx
    sub["v57_ev"] = v57_ev
    sub["v57_rank"] = v57_rank
    sub["v57_regret"] = sub["ev_best"] - sub["v57_ev"]
    sub["v57_bucket"] = sub["v57_rank"].apply(rank_bucket)
    sub["v44_bucket"] = sub["v44_rank"].apply(rank_bucket)
    sub["v57_overrides_v44"] = sub["v57_idx"] != sub["v44_idx"]

    # === Headline: v57 vs v44 agreement + leak per cell ===
    print("[4/4] results")
    print("=" * 110)
    print("HEADLINE — v57 vs v44 on HIGH_ONLY x DS_NO_JOINT (per max_rank)")
    print("=" * 110)
    print(f"{'rank':>4} {'n':>9} {'v57=v44 %':>10} "
          f"{'v44_leak $':>11} {'v57_leak $':>11} "
          f"{'v57_STR $':>10} {'v44_STR $':>10}")
    for r in TARGET_RANKS:
        seg = sub[sub["max_rank"] == r]
        if len(seg) == 0:
            continue
        agree_pct = 100 * (~seg["v57_overrides_v44"]).mean()
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v57_leak = seg["v57_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v57_str = (seg[seg["v57_bucket"] == "STRUCTURE"]["v57_regret"].sum()
                   * EV_TO_DOL * 1000 / N_TOTAL_GRID)
        v44_str = (seg[seg["v44_bucket"] == "STRUCTURE"]["regret"].sum()
                   * EV_TO_DOL * 1000 / N_TOTAL_GRID)
        print(f"{RANK_CHAR[r]:>4} {len(seg):>9,} {agree_pct:>9.1f}% "
              f"${v44_leak:>+9.2f} ${v57_leak:>+9.2f} "
              f"${v57_str:>+8.2f} ${v44_str:>+8.2f}")

    print()
    print("=" * 110)
    print("ADDRESSABILITY GATE — for each cell, the v57 STRUCTURE residual")
    print("=" * 110)
    print("  Gate criteria:")
    print("    (a) v57 STRUCTURE leak >= $15/1000h ON THE CELL "
          "(addressable headroom for rule)")
    print("    (b) Single dominant v57->oracle direction concentrates "
          "majority of STRUCTURE residual")
    print()

    for r in TARGET_RANKS:
        seg = sub[(sub["max_rank"] == r) & (sub["v57_bucket"] == "STRUCTURE")]
        if len(seg) == 0:
            continue
        v57_str = seg["v57_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  -- {RANK_CHAR[r]}-high x DS_NO_JOINT: STRUCTURE-bucket "
              f"n={len(seg):,}, v57 leak=${v57_str:.2f}/1000h --")

        # Direction concentration: group by (v57_idx oracle direction)
        # We use raw setting indices as the proxy class label
        pairs = seg.groupby(["v57_idx", "oracle_idx"]).agg(
            n=("v57_idx", "size"),
            sum_regret=("v57_regret", "sum")
        ).reset_index().sort_values("sum_regret", ascending=False)
        pairs["wg"] = pairs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"    Top 5 (v57_setting -> oracle_setting) directions:")
        for _, row in pairs.head(5).iterrows():
            pct_of_str = 100 * row["sum_regret"] / seg["v57_regret"].sum()
            print(f"      v57={int(row['v57_idx']):>3} -> "
                  f"oracle={int(row['oracle_idx']):>3}  n={int(row['n']):>5,}  "
                  f"wg=${row['wg']:>+6.2f}/1000h  "
                  f"({pct_of_str:>4.1f}% of STR residual)")

        # Top-direction concentration: how much of STR leak is in top-1 / top-5
        # of directions
        top1 = pairs.head(1)["sum_regret"].sum()
        top5 = pairs.head(5)["sum_regret"].sum()
        top20 = pairs.head(20)["sum_regret"].sum()
        total = seg["v57_regret"].sum()
        print(f"    Concentration: top-1={100*top1/total:.1f}%, "
              f"top-5={100*top5/total:.1f}%, top-20={100*top20/total:.1f}%")
        # Cell-wide v57 leak (all buckets)
        seg_all = sub[sub["max_rank"] == r]
        v57_total = seg_all["v57_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        addressable_str_total = v57_str  # already-STRUCTURE-only
        # Gate pass/fail
        print(f"    cell-wide v57 leak: ${v57_total:.2f}/1000h, "
              f"STR-bucket: ${addressable_str_total:.2f}/1000h")
        gate_a = addressable_str_total >= 15.0
        gate_b = (top5 / total) >= 0.30 if total > 0 else False
        print(f"    Gate (a) STR>=$15: {'PASS' if gate_a else 'FAIL'}; "
              f"Gate (b) top-5 conc>=30%: {'PASS' if gate_b else 'FAIL'}")
        print()

    print("=" * 110)
    print("v52 HIGH_ONLY HANDLER ACTIVITY (sanity)")
    print("=" * 110)
    activity = sub.groupby("max_rank")["v57_overrides_v44"].agg(
        n=("size"), n_override=("sum"))
    activity["pct_override"] = (100 * activity["n_override"] /
                                activity["n"]).round(1)
    print(activity)
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
