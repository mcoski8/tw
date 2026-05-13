"""
Session 69 Phase 1b — Sweep v54 (= v52 on two_pair, since the v54 hybrid
gate excludes two_pair AND Rule 19 in v53 is single-pair-only) over all
1.3M two_pair hands; aggregate v54→oracle residual per (hi_pair x cell).
Reuses data/drill_two_pair_v44_per_hand_structural.parquet for cell tags
+ oracle picks, and computes v54 picks per hand for the comparison.

This is the analog of `sweep_v52_on_pair_S66.py`. Output:
  data/drill_two_pair_v54_per_hand.parquet
  data/drill_two_pair_v54_summary.json
  Console: per-(hi_pair, cell) v54→oracle residual table; v54 vs v44 per
           cell delta; v54 placement distribution per cell

NOTE: For two_pair specifically, v54_pair_hybrid routes through v53,
which routes through v52 (Rule 19 doesn't fire on two_pair). So
strategy_v52_full_high_only_handler is the correct choice to sweep here.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/sweep_v54_on_two_pair_S69.py
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
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)
from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
TP_PARQUET = ROOT / "data" / "drill_two_pair_v44_per_hand_structural.parquet"
OUT_PARQUET = ROOT / "data" / "drill_two_pair_v54_per_hand.parquet"
OUT_JSON = ROOT / "data" / "drill_two_pair_v54_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}
SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS",
    SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "RB",
    SUIT_PROFILE_THREE_ONE: "31",
    SUIT_PROFILE_FOUR_FLUSH: "4f",
}
CELLS_ORDER = [
    "LAYOUT_A_DS", "LAYOUT_C_DS", "LAYOUT_B_DS",
    "LAYOUT_A_SS", "LAYOUT_C_SS_ONLY", "LAYOUT_B_SS_ONLY",
    "LAYOUT_OTHER",
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


def classify_v54_pick_two_pair(hand_bytes, idx, hi_pair_set, lo_pair_set,
                                sing_ranks_sorted):
    """Return (layout, bot_suit, top_type, class_label) for a v54 pick."""
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3

    n_hi_in_bot = sum(1 for p in bot_pos if p in hi_pair_set)
    n_hi_in_mid = sum(1 for p in mid_pos if p in hi_pair_set)
    n_lo_in_bot = sum(1 for p in bot_pos if p in lo_pair_set)
    n_lo_in_mid = sum(1 for p in mid_pos if p in lo_pair_set)

    if n_hi_in_bot == 2 and n_lo_in_bot == 2:
        layout = "A"
    elif n_hi_in_mid == 2 and n_lo_in_bot == 2:
        layout = "B"
    elif n_hi_in_bot == 2 and n_lo_in_mid == 2:
        layout = "C"
    else:
        layout = "SPLIT"

    bot_suit_kind = _bot_suit_kind([int(suits[p]) for p in bot_pos])

    top_rank = int(ranks[top_pos])
    if top_pos in hi_pair_set or top_pos in lo_pair_set:
        top_type = "PAIR"
    elif top_rank == sing_ranks_sorted[0]:
        top_type = "SING_MAX"
    elif top_rank == sing_ranks_sorted[2]:
        top_type = "SING_LOW"
    else:
        top_type = "SING_MID"

    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]

    top_lbl_short = {
        "SING_MAX": "tmax", "SING_MID": "tmid",
        "SING_LOW": "tlow", "PAIR": "tpair",
    }[top_type]
    ms_lbl = "ms" if mid_suited else "mu"
    if layout in ("A", "B", "C"):
        class_label = f"{layout}_{bot_suit_kind}_{top_lbl_short}_{ms_lbl}"
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
    print("Session 69 Phase 1b — v54 (= v52 on two_pair) sweep on two_pair category")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading two_pair parquet (cell tags + oracle picks) ...",
          flush=True)
    df = pq.read_table(TP_PARQUET).to_pandas()
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
    hi_pair_arr = df["hi_pair_rank"].to_numpy()
    lo_pair_arr = df["lo_pair_rank"].to_numpy()
    v44_idxs = df["v44_idx"].to_numpy()
    v44_regret = df["regret"].to_numpy()

    arr_v54_idx = np.zeros(n, dtype=np.int16)
    arr_v54_regret = np.zeros(n, dtype=np.float32)
    arr_v54_layout = np.zeros(n, dtype=np.int8)
    arr_v54_bot_suit = np.zeros(n, dtype=np.int8)
    arr_v54_top_type = np.zeros(n, dtype=np.int8)
    arr_v54_class = np.empty(n, dtype=object)
    _LAYOUT_CODE = {"A": 0, "B": 1, "C": 2, "SPLIT": 3}
    _BOT_SUIT_CODE = {"DS": 0, "SS": 1, "31": 2, "RB": 3, "4f": 4}
    _TOP_TYPE_CODE = {"SING_MAX": 0, "SING_MID": 1, "SING_LOW": 2, "PAIR": 3}

    # Aggregates by (hi_pair, cell).
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "v54_sum_regret": 0.0,
        "v54_n_match_oracle": 0,
        "v54_class_dist": Counter(),
        "v54_layout_dist": Counter(),
        "v44_v54_match": 0,
        "v44_sum_regret": 0.0,
    })
    rank_stats = defaultdict(lambda: {
        "n": 0,
        "v54_sum_regret": 0.0,
        "v54_n_match_oracle": 0,
        "v44_sum_regret": 0.0,
    })

    print("\n[3/4] computing v54 picks for each two_pair hand ...", flush=True)
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        v54_idx = int(strategy_v52_full_high_only_handler(h))
        rowf = gf.evs[cid]
        oracle_ev = float(rowf[int(oracle_idxs[k])])
        v54_ev = float(rowf[v54_idx])
        regret = oracle_ev - v54_ev

        # Compute pair positions from the hand for layout classification
        ranks = (h // 4) + 2
        hi_pair = int(hi_pair_arr[k])
        lo_pair = int(lo_pair_arr[k])
        hi_pair_set = set(i for i in range(7) if int(ranks[i]) == hi_pair)
        lo_pair_set = set(i for i in range(7) if int(ranks[i]) == lo_pair)
        sing_pos = [i for i in range(7) if i not in hi_pair_set and i not in lo_pair_set]
        sing_ranks_sorted = sorted([int(ranks[i]) for i in sing_pos], reverse=True)

        layout, bot_suit_kind, top_type, v54_class = classify_v54_pick_two_pair(
            h, v54_idx, hi_pair_set, lo_pair_set, sing_ranks_sorted
        )

        arr_v54_idx[k] = v54_idx
        arr_v54_regret[k] = regret
        arr_v54_layout[k] = _LAYOUT_CODE[layout]
        arr_v54_bot_suit[k] = _BOT_SUIT_CODE.get(bot_suit_kind, 4)
        arr_v54_top_type[k] = _TOP_TYPE_CODE[top_type]
        arr_v54_class[k] = v54_class

        cell = CELLS_ORDER[int(cell_idx_arr[k])]
        st = cell_stats[(hi_pair, cell)]
        st["n"] += 1
        st["v54_sum_regret"] += regret
        st["v44_sum_regret"] += float(v44_regret[k])
        if v54_idx == int(oracle_idxs[k]):
            st["v54_n_match_oracle"] += 1
        st["v54_class_dist"][v54_class] += 1
        st["v54_layout_dist"][layout] += 1
        if v54_idx == int(v44_idxs[k]):
            st["v44_v54_match"] += 1

        rs = rank_stats[hi_pair]
        rs["n"] += 1
        rs["v54_sum_regret"] += regret
        rs["v44_sum_regret"] += float(v44_regret[k])
        if v54_idx == int(oracle_idxs[k]):
            rs["v54_n_match_oracle"] += 1

        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ============================================================
    # Per-hi_pair-rank residual table (v54 vs oracle, with v44 ref)
    # ============================================================
    print("=" * 100)
    print("v54 PER-HI_PAIR-RANK RESIDUAL (canonical-equal weighting); v44 ref")
    print("=" * 100)
    print(f"  {'hi_pair':>7} {'n_hands':>9} {'v44_pct_opt':>11} "
          f"{'v54_pct_opt':>11} {'v44_wg':>10} {'v54_wg':>10} "
          f"{'v54-v44':>10}")
    total_n = 0
    total_v44_reg = 0.0
    total_v54_reg = 0.0
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[hi_pair]
        if rs["n"] == 0:
            continue
        v54_pct_opt = 100 * rs["v54_n_match_oracle"] / rs["n"]
        v44_wg = rs["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v54_wg = rs["v54_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        # v44 pct_opt comes from the v44 sweep (recomputed from regret==0):
        # but we don't have it directly here. We can derive from cell stats
        # but the simpler proxy is to display only v54 pct_opt + WG diffs.
        v44_pct_opt_hint = "—"  # leave blank; full diff in T2P5 below
        print(f"  {RANK_CHAR[hi_pair]:>7} {rs['n']:>9,} "
              f"{v44_pct_opt_hint:>11} {v54_pct_opt:>10.2f}% "
              f"${v44_wg:>+8.2f} ${v54_wg:>+8.2f} ${v54_wg-v44_wg:>+8.2f}")
        total_n += rs["n"]
        total_v44_reg += rs["v44_sum_regret"]
        total_v54_reg += rs["v54_sum_regret"]
    total_v44_wg = total_v44_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
    total_v54_wg = total_v54_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
    print(f"\n  TOTAL: n={total_n:,}  v44_wg=${total_v44_wg:+.2f}  "
          f"v54_wg=${total_v54_wg:+.2f}  Δ=${total_v54_wg-total_v44_wg:+.2f}")

    # ============================================================
    # Per-(hi_pair, cell) v54 vs v44 residual table
    # ============================================================
    print("\n" + "=" * 100)
    print("v54 PER-(hi_pair, cell) RESIDUAL — v44 reference + v54-v44 delta")
    print("=" * 100)
    print(f"  {'hi_pair':>7} {'cell':<20} {'n':>9} {'v54_pct_opt':>11} "
          f"{'v44_wg':>10} {'v54_wg':>10} {'v54-v44':>10}")
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((hi_pair, cell), None)
            if st is None or st["n"] == 0:
                continue
            v54_pct_opt = 100 * st["v54_n_match_oracle"] / st["n"]
            v44_wg = st["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v54_wg = st["v54_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"  {RANK_CHAR[hi_pair]:>7} {cell:<20} {st['n']:>9,} "
                  f"{v54_pct_opt:>10.2f}% ${v44_wg:>+8.2f} "
                  f"${v54_wg:>+8.2f} ${v54_wg-v44_wg:>+8.2f}")

    # ============================================================
    # Per-cell aggregates across hi_pair (cell totals)
    # ============================================================
    print("\n" + "=" * 100)
    print("v54 PER-CELL AGGREGATE (across all hi_pair_ranks)")
    print("=" * 100)
    print(f"  {'cell':<20} {'n':>9} {'v44_wg':>10} {'v54_wg':>10} "
          f"{'v54-v44':>10}")
    for cell in CELLS_ORDER:
        n_cell = sum(cell_stats[(hp, cell)]["n"] for hp in rank_stats.keys()
                     if (hp, cell) in cell_stats)
        v44_reg = sum(cell_stats[(hp, cell)]["v44_sum_regret"]
                       for hp in rank_stats.keys() if (hp, cell) in cell_stats)
        v54_reg = sum(cell_stats[(hp, cell)]["v54_sum_regret"]
                       for hp in rank_stats.keys() if (hp, cell) in cell_stats)
        if n_cell == 0:
            continue
        v44_wg = v44_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v54_wg = v54_reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {cell:<20} {n_cell:>9,} ${v44_wg:>+8.2f} "
              f"${v54_wg:>+8.2f} ${v54_wg-v44_wg:>+8.2f}")

    # ============================================================
    # v54 placement distribution per (hi_pair, cell) — find ML-only fingerprints
    # ============================================================
    print("\n" + "=" * 100)
    print("v54 LAYOUT DISTRIBUTION per (hi_pair, cell)")
    print("=" * 100)
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((hi_pair, cell), None)
            if st is None or st["n"] == 0:
                continue
            layout_summary = ", ".join(
                f"{p}:{100*c/st['n']:.0f}%"
                for p, c in sorted(st["v54_layout_dist"].items(), key=lambda x: -x[1])
            )
            v44_v54_pct = 100 * st["v44_v54_match"] / st["n"]
            print(f"  {RANK_CHAR[hi_pair]} {cell:<20}  v54_LAYOUT: {layout_summary:<40}  "
                  f"v44==v54: {v44_v54_pct:5.1f}%")

    # ============================================================
    # Save augmented parquet + summary JSON
    # ============================================================
    if not args.no_parquet:
        print(f"\n[4/4] writing v54 parquet to {OUT_PARQUET} ...", flush=True)
        table = pa.table({
            "canonical_id": pa.array(cids, type=pa.uint32()),
            "hi_pair_rank": pa.array(hi_pair_arr, type=pa.int8()),
            "cell_idx": pa.array(cell_idx_arr, type=pa.int8()),
            "v54_idx": pa.array(arr_v54_idx, type=pa.int16()),
            "v54_regret": pa.array(arr_v54_regret, type=pa.float32()),
            "v54_layout": pa.array(arr_v54_layout, type=pa.int8()),
            "v54_bot_suit": pa.array(arr_v54_bot_suit, type=pa.int8()),
            "v54_top_type": pa.array(arr_v54_top_type, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        summary = {
            "n_two_pair_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "rank_stats": {},
            "cell_stats": {},
            "totals": {
                "v44_wg": float(total_v44_wg),
                "v54_wg": float(total_v54_wg),
                "v54_v44_delta_wg": float(total_v54_wg - total_v44_wg),
            },
        }
        for hp, rs in rank_stats.items():
            summary["rank_stats"][str(hp)] = {
                "n": int(rs["n"]),
                "v44_sum_regret": float(rs["v44_sum_regret"]),
                "v54_sum_regret": float(rs["v54_sum_regret"]),
                "v54_n_match_oracle": int(rs["v54_n_match_oracle"]),
                "v44_wg": float(rs["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v54_wg": float(rs["v54_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v54_pct_opt": float(100 * rs["v54_n_match_oracle"] / rs["n"]),
            }
        for (hp, cell), st in cell_stats.items():
            summary["cell_stats"][f"{hp}|{cell}"] = {
                "n": int(st["n"]),
                "v44_sum_regret": float(st["v44_sum_regret"]),
                "v54_sum_regret": float(st["v54_sum_regret"]),
                "v54_n_match_oracle": int(st["v54_n_match_oracle"]),
                "v44_wg": float(st["v44_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v54_wg": float(st["v54_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v54_pct_opt": float(100 * st["v54_n_match_oracle"] / st["n"]),
                "v54_class_dist": dict(st["v54_class_dist"].most_common(15)),
                "v54_layout_dist": dict(st["v54_layout_dist"]),
                "v44_v54_match_pct": float(100 * st["v44_v54_match"] / st["n"]),
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
