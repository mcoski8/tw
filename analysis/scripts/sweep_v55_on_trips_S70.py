"""
Session 70 Phase 1b — Sweep v55 (= v54 = v52 on trips, since neither
v55's two_pair gate nor v54's pair gate fires on trips, and Rule 19 in
v53 is single-pair-only) over all 328K trips hands; aggregate v55→oracle
residual per (trip_rank x cell). Reuses
data/drill_trips_v44_per_hand_structural.parquet for cell tags + oracle
picks, and computes v55 picks per hand for the comparison.

Mirror of `sweep_v54_on_two_pair_S69.py`. Output:
  data/drill_trips_v55_per_hand.parquet
  data/drill_trips_v55_summary.json
  Console: per-(trip_rank, cell) v55→oracle residual table; v55 vs v44
           per cell delta; v55 placement distribution per cell

NOTE: For trips specifically, v55 falls through (via v54) to v53 (Rule 19
single-pair-only), which falls through to v52. So strategy_v52 is the
correct entry to sweep — same as the two_pair case.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/sweep_v55_on_trips_S70.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pyarrow as pa
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
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SETTING_HAND_INDICES,
)
from strategy_v55_two_pair_hybrid import strategy_v55_two_pair_hybrid  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
TR_PARQUET = ROOT / "data" / "drill_trips_v44_per_hand_structural.parquet"
OUT_PARQUET = ROOT / "data" / "drill_trips_v55_per_hand.parquet"
OUT_JSON = ROOT / "data" / "drill_trips_v55_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

CELLS_ORDER = [
    "B_DS_AVAIL_HKR",
    "B_DS_AVAIL_LKR",
    "NO_BDS_CTOP",
    "NO_BDS_AKDOM",
]


def _bot_suit_kind(suits):
    counts = sorted(Counter(int(s) for s in suits).values(), reverse=True)
    if counts == [4]:
        return "4f"
    if counts == [2, 2]:
        return "DS"
    if counts == [2, 1, 1]:
        return "SS"
    if counts == [3, 1]:
        return "31"
    return "RB"


def classify_v55_pick_trips(hand_bytes, idx, trip_pos_set, kicker_ranks_sorted):
    """Return (layout, bot_suit, top_type, class_label) for v55's pick.
    Trip-rank canonical layouts: A_paired_mid, B_paired_bot, C_top_trip, SPLIT.
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3

    n_trip_top = 1 if top_pos in trip_pos_set else 0
    n_trip_mid = sum(1 for p in mid_pos if p in trip_pos_set)
    n_trip_bot = sum(1 for p in bot_pos if p in trip_pos_set)

    if n_trip_top == 0 and n_trip_mid == 2 and n_trip_bot == 1:
        layout = "A"
    elif n_trip_bot == 2:
        layout = "B"
    elif n_trip_top == 1 and n_trip_mid == 2 and n_trip_bot == 0:
        layout = "C"
    else:
        layout = "SPLIT"

    bot_suit_kind = _bot_suit_kind([int(suits[p]) for p in bot_pos])

    top_rank = int(ranks[top_pos])
    if top_pos in trip_pos_set:
        top_type = "TRIP"
    elif top_rank == kicker_ranks_sorted[0]:
        top_type = "KICKER_MAX"
    elif top_rank == kicker_ranks_sorted[3]:
        top_type = "KICKER_LOW"
    else:
        top_type = "KICKER_MID"

    top_lbl_short = {
        "TRIP": "ttrip", "KICKER_MAX": "tkmax",
        "KICKER_MID": "tkmid", "KICKER_LOW": "tklow",
    }[top_type]
    if layout in ("A", "B", "C"):
        class_label = f"{layout}_{bot_suit_kind}_{top_lbl_short}"
    else:
        class_label = f"SPLIT_{bot_suit_kind}_{top_lbl_short}"

    return layout, bot_suit_kind, top_type, class_label


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 70 Phase 1b — v55 (= v52 on trips) sweep on trips category")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading trips parquet (cell tags + oracle picks) ...",
          flush=True)
    df = pq.read_table(TR_PARQUET).to_pandas()
    print(f"  rows: {len(df):,}")

    if args.sample > 0 and len(df) > args.sample:
        rng = np.random.default_rng(args.seed)
        sel = np.sort(rng.choice(len(df), size=args.sample, replace=False))
        df = df.iloc[sel].reset_index(drop=True)
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading canonical hands + oracle grid ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(df)
    cids = df["canonical_id"].to_numpy()
    oracle_idxs = df["oracle_idx"].to_numpy()
    cell_idx_arr = df["cell_idx"].to_numpy()
    trip_rank_arr = df["trip_rank"].to_numpy()
    v44_idxs = df["v44_idx"].to_numpy()
    v44_regret = df["regret"].to_numpy()

    arr_v55_idx = np.zeros(n, dtype=np.int16)
    arr_v55_regret = np.zeros(n, dtype=np.float32)
    arr_v55_layout = np.zeros(n, dtype=np.int8)
    arr_v55_bot_suit = np.zeros(n, dtype=np.int8)
    arr_v55_top_type = np.zeros(n, dtype=np.int8)
    arr_v55_class = np.empty(n, dtype=object)
    _LAYOUT_CODE = {"A": 0, "B": 1, "C": 2, "SPLIT": 3}
    _BOT_SUIT_CODE = {"DS": 0, "SS": 1, "31": 2, "RB": 3, "4f": 4}
    _TOP_TYPE_CODE = {"TRIP": 0, "KICKER_MAX": 1, "KICKER_MID": 2, "KICKER_LOW": 3}

    cell_stats = defaultdict(lambda: {
        "n": 0,
        "v55_sum_regret": 0.0,
        "v55_n_match_oracle": 0,
        "v55_class_dist": Counter(),
        "v55_layout_dist": Counter(),
        "v55_bot_suit_dist": Counter(),
        "v44_v55_match": 0,
        "v44_sum_regret": 0.0,
    })
    rank_stats = defaultdict(lambda: {
        "n": 0,
        "v55_sum_regret": 0.0,
        "v55_n_match_oracle": 0,
        "v44_sum_regret": 0.0,
    })

    print("\n[3/4] computing v55 picks for each trips hand ...", flush=True)
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        v55_idx = int(strategy_v55_two_pair_hybrid(h))
        rowf = gf.evs[cid]
        oracle_ev = float(rowf[int(oracle_idxs[k])])
        v55_ev = float(rowf[v55_idx])
        regret = oracle_ev - v55_ev

        ranks = (h // 4) + 2
        trip_rank = int(trip_rank_arr[k])
        trip_pos = [i for i in range(7) if int(ranks[i]) == trip_rank]
        trip_pos_set = set(trip_pos)
        kicker_pos = [i for i in range(7) if i not in trip_pos_set]
        kicker_ranks_sorted = tuple(sorted(
            (int(ranks[i]) for i in kicker_pos), reverse=True
        ))

        layout, bot_suit_kind, top_type, v55_class = classify_v55_pick_trips(
            h, v55_idx, trip_pos_set, kicker_ranks_sorted
        )

        arr_v55_idx[k] = v55_idx
        arr_v55_regret[k] = regret
        arr_v55_layout[k] = _LAYOUT_CODE[layout]
        arr_v55_bot_suit[k] = _BOT_SUIT_CODE.get(bot_suit_kind, 4)
        arr_v55_top_type[k] = _TOP_TYPE_CODE[top_type]
        arr_v55_class[k] = v55_class

        cell = CELLS_ORDER[int(cell_idx_arr[k])]
        st = cell_stats[(trip_rank, cell)]
        st["n"] += 1
        st["v55_sum_regret"] += regret
        st["v44_sum_regret"] += float(v44_regret[k])
        if v55_idx == int(oracle_idxs[k]):
            st["v55_n_match_oracle"] += 1
        st["v55_class_dist"][v55_class] += 1
        st["v55_layout_dist"][layout] += 1
        st["v55_bot_suit_dist"][bot_suit_kind] += 1
        if v55_idx == int(v44_idxs[k]):
            st["v44_v55_match"] += 1

        rs = rank_stats[trip_rank]
        rs["n"] += 1
        rs["v55_sum_regret"] += regret
        rs["v44_sum_regret"] += float(v44_regret[k])
        if v55_idx == int(oracle_idxs[k]):
            rs["v55_n_match_oracle"] += 1

        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ============================================================
    # Per-trip_rank residual table
    # ============================================================
    print("=" * 100)
    print("v55 PER-TRIP_RANK RESIDUAL (canonical-equal weighting); v44 ref")
    print("=" * 100)
    print(f"  {'trip':>5} {'n_hands':>9} {'v55_pct_opt':>11} "
          f"{'v44_wg':>10} {'v55_wg':>10} {'v55-v44':>10}")
    total_n = 0
    total_v44_reg = 0.0
    total_v55_reg = 0.0
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[trip_rank]
        if rs["n"] == 0:
            continue
        v55_pct_opt = 100 * rs["v55_n_match_oracle"] / rs["n"]
        v44_wg = rs["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v55_wg = rs["v55_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {RANK_CHAR[trip_rank]:>5} {rs['n']:>9,} "
              f"{v55_pct_opt:>10.2f}% "
              f"${v44_wg:>+8.2f} ${v55_wg:>+8.2f} ${v55_wg-v44_wg:>+8.2f}")
        total_n += rs["n"]
        total_v44_reg += rs["v44_sum_regret"]
        total_v55_reg += rs["v55_sum_regret"]
    total_v44_wg = total_v44_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
    total_v55_wg = total_v55_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
    print(f"\n  TOTAL: n={total_n:,}  v44_wg=${total_v44_wg:+.2f}  "
          f"v55_wg=${total_v55_wg:+.2f}  Δ=${total_v55_wg-total_v44_wg:+.2f}")

    # ============================================================
    # Per-(trip_rank, cell) v55 vs v44 residual table
    # ============================================================
    print("\n" + "=" * 100)
    print("v55 PER-(trip_rank, cell) RESIDUAL — v44 reference + v55-v44 delta")
    print("=" * 100)
    print(f"  {'trip':>5} {'cell':<18} {'n':>9} {'v55_pct_opt':>11} "
          f"{'v44_wg':>10} {'v55_wg':>10} {'v55-v44':>10}")
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((trip_rank, cell), None)
            if st is None or st["n"] == 0:
                continue
            v55_pct_opt = 100 * st["v55_n_match_oracle"] / st["n"]
            v44_wg = st["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v55_wg = st["v55_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"  {RANK_CHAR[trip_rank]:>5} {cell:<18} {st['n']:>9,} "
                  f"{v55_pct_opt:>10.2f}% ${v44_wg:>+8.2f} "
                  f"${v55_wg:>+8.2f} ${v55_wg-v44_wg:>+8.2f}")

    # ============================================================
    # Per-cell aggregates across trip_ranks
    # ============================================================
    print("\n" + "=" * 100)
    print("v55 PER-CELL AGGREGATE (across all trip_ranks)")
    print("=" * 100)
    print(f"  {'cell':<18} {'n':>9} {'v44_wg':>10} {'v55_wg':>10} "
          f"{'v55-v44':>10}")
    for cell in CELLS_ORDER:
        n_cell = sum(cell_stats[(tr, cell)]["n"] for tr in rank_stats.keys()
                     if (tr, cell) in cell_stats)
        v44_reg = sum(cell_stats[(tr, cell)]["v44_sum_regret"]
                       for tr in rank_stats.keys() if (tr, cell) in cell_stats)
        v55_reg = sum(cell_stats[(tr, cell)]["v55_sum_regret"]
                       for tr in rank_stats.keys() if (tr, cell) in cell_stats)
        if n_cell == 0:
            continue
        v44_wg = v44_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v55_wg = v55_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {cell:<18} {n_cell:>9,} ${v44_wg:>+8.2f} "
              f"${v55_wg:>+8.2f} ${v55_wg-v44_wg:>+8.2f}")

    # ============================================================
    # v55 placement distribution per (trip_rank, cell)
    # ============================================================
    print("\n" + "=" * 100)
    print("v55 LAYOUT + BOT_SUIT distribution per (trip_rank, cell)")
    print("=" * 100)
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((trip_rank, cell), None)
            if st is None or st["n"] == 0:
                continue
            layout_summary = ", ".join(
                f"{p}:{100*c/st['n']:.0f}%"
                for p, c in sorted(st["v55_layout_dist"].items(), key=lambda x: -x[1])
            )
            bot_suit_summary = ", ".join(
                f"{s}:{100*c/st['n']:.0f}%"
                for s, c in sorted(st["v55_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            v44_v55_pct = 100 * st["v44_v55_match"] / st["n"]
            print(f"  {RANK_CHAR[trip_rank]} {cell:<18}  v55_LAYOUT: {layout_summary:<22}  "
                  f"v55_BOT_SUIT: {bot_suit_summary:<36}  v44==v55: {v44_v55_pct:5.1f}%")

    # ============================================================
    # Save augmented parquet + summary JSON
    # ============================================================
    if not args.no_parquet:
        print(f"\n[4/4] writing v55 parquet to {OUT_PARQUET} ...", flush=True)
        table = pa.table({
            "canonical_id": pa.array(cids, type=pa.uint32()),
            "trip_rank": pa.array(trip_rank_arr, type=pa.int8()),
            "cell_idx": pa.array(cell_idx_arr, type=pa.int8()),
            "v55_idx": pa.array(arr_v55_idx, type=pa.int16()),
            "v55_regret": pa.array(arr_v55_regret, type=pa.float32()),
            "v55_layout": pa.array(arr_v55_layout, type=pa.int8()),
            "v55_bot_suit": pa.array(arr_v55_bot_suit, type=pa.int8()),
            "v55_top_type": pa.array(arr_v55_top_type, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        summary = {
            "n_trips_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "rank_stats": {},
            "cell_stats": {},
            "totals": {
                "v44_wg": float(total_v44_wg),
                "v55_wg": float(total_v55_wg),
                "v55_v44_delta_wg": float(total_v55_wg - total_v44_wg),
            },
        }
        for tr, rs in rank_stats.items():
            summary["rank_stats"][str(tr)] = {
                "n": int(rs["n"]),
                "v44_sum_regret": float(rs["v44_sum_regret"]),
                "v55_sum_regret": float(rs["v55_sum_regret"]),
                "v55_n_match_oracle": int(rs["v55_n_match_oracle"]),
                "v44_wg": float(rs["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v55_wg": float(rs["v55_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v55_pct_opt": float(100 * rs["v55_n_match_oracle"] / rs["n"]),
            }
        for (tr, cell), st in cell_stats.items():
            summary["cell_stats"][f"{tr}|{cell}"] = {
                "n": int(st["n"]),
                "v44_sum_regret": float(st["v44_sum_regret"]),
                "v55_sum_regret": float(st["v55_sum_regret"]),
                "v55_n_match_oracle": int(st["v55_n_match_oracle"]),
                "v44_wg": float(st["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v55_wg": float(st["v55_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v55_pct_opt": float(100 * st["v55_n_match_oracle"] / st["n"]),
                "v55_class_dist": dict(st["v55_class_dist"].most_common(15)),
                "v55_layout_dist": dict(st["v55_layout_dist"]),
                "v55_bot_suit_dist": dict(st["v55_bot_suit_dist"]),
                "v44_v55_match_pct": float(100 * st["v44_v55_match"] / st["n"]),
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
