"""
Session 66 Phase 2 — Sweep v52_full_high_only_handler over all 2.8M pair
hands; aggregate v52→oracle residual per (pair_rank x cell). Reuses
data/drill_pair_v44_per_hand_structural.parquet for cell tags + oracle picks,
and computes v52 picks per hand for the comparison.

Output:
  data/drill_pair_v52_per_hand.parquet — adds v52_idx, v52_regret to the
                                          parquet schema (joined on canonical_id)
  data/drill_pair_v52_summary.json
  Console: per-(pair_rank, cell) v52→oracle residual table

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/sweep_v52_on_pair_S66.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
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
PAIR_PARQUET = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
OUT_PARQUET = ROOT / "data" / "drill_pair_v52_per_hand.parquet"
OUT_JSON = ROOT / "data" / "drill_pair_v52_summary.json"

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
    "PBOT_DS_JOINT", "PBOT_DS_PARTIAL",
    "PMID_DS_MAXTOP", "PMID_DS_NOMAXTOP",
    "PMID_SS_MAXTOP", "PMID_OTHER",
]


def classify_v52_pick_pair(hand_bytes, feats, idx, pair_pos_set, max_sing_pos):
    """Minimal classifier that returns the pair-specific label of a v52 pick."""
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    suits = hand_bytes & 3
    n_pair_in_mid = sum(1 for p in mid_pos if p in pair_pos_set)
    n_pair_in_bot = sum(1 for p in bot_pos if p in pair_pos_set)

    if n_pair_in_mid == 2:
        placement = "PMID"
    elif n_pair_in_bot == 2:
        placement = "PBOT"
    else:
        placement = "SPLIT"

    if top_pos in pair_pos_set:
        top_type = "PAIR"
    elif top_pos == max_sing_pos:
        top_type = "SING_MAX"
    else:
        top_type = "SING_NOMAX"

    top_lbl_short = {"PAIR": "tpair", "SING_MAX": "tmax", "SING_NOMAX": "tnomax"}[top_type]
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]
    ms_lbl = "ms" if mid_suited else "mu"
    if placement == "PMID":
        return placement, top_type, f"PMID_{top_lbl_short}_{suit_lbl}"
    return placement, top_type, f"{placement}_{top_lbl_short}_{suit_lbl}_{ms_lbl}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 66 Phase 2 — v52 sweep on pair category")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading pair parquet (cell tags + oracle picks) ...", flush=True)
    df = pq.read_table(PAIR_PARQUET).to_pandas()
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
    pair_rank_arr = df["pair_rank"].to_numpy()

    arr_v52_idx = np.zeros(n, dtype=np.int16)
    arr_v52_regret = np.zeros(n, dtype=np.float32)
    arr_v52_placement = np.zeros(n, dtype=np.int8)
    arr_v52_top_type = np.zeros(n, dtype=np.int8)
    arr_v52_class = np.empty(n, dtype=object)
    _PAIR_PLACEMENT_CODE = {"PMID": 0, "PBOT": 1, "SPLIT": 2}
    _TOP_TYPE_CODE = {"PAIR": 0, "SING_MAX": 1, "SING_NOMAX": 2}

    # Aggregates by (pair_rank, cell).
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "v52_sum_regret": 0.0,
        "v52_n_match_oracle": 0,
        "v52_class_dist": Counter(),
        "v52_placement_dist": Counter(),
        "v44_v52_match": 0,
    })
    rank_stats = defaultdict(lambda: {
        "n": 0,
        "v52_sum_regret": 0.0,
        "v52_n_match_oracle": 0,
    })

    v44_idxs = df["v44_idx"].to_numpy()

    print("\n[3/4] computing v52 picks for each pair hand ...", flush=True)
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        v52_idx = int(strategy_v52_full_high_only_handler(h))
        rowf = gf.evs[cid]
        oracle_ev = float(rowf[int(oracle_idxs[k])])
        v52_ev = float(rowf[v52_idx])
        regret = oracle_ev - v52_ev

        # Compute pair_pos and max_sing_pos from the hand
        ranks = (h // 4) + 2
        rc = Counter(int(r) for r in ranks)
        pair_rank = None
        for r, c in rc.items():
            if c == 2:
                pair_rank = r
                break
        pair_pos = tuple(i for i in range(7) if int(ranks[i]) == pair_rank)
        pair_pos_set = set(pair_pos)
        sing_pos = [i for i in range(7) if i not in pair_pos_set]
        sing_ranks = [int(ranks[i]) for i in sing_pos]
        max_sing_rank = max(sing_ranks)
        max_sing_local = sing_ranks.index(max_sing_rank)
        max_sing_pos = sing_pos[max_sing_local]

        placement, top_type, v52_class = classify_v52_pick_pair(
            h, feats, v52_idx, pair_pos_set, max_sing_pos
        )

        arr_v52_idx[k] = v52_idx
        arr_v52_regret[k] = regret
        arr_v52_placement[k] = _PAIR_PLACEMENT_CODE[placement]
        arr_v52_top_type[k] = _TOP_TYPE_CODE[top_type]
        arr_v52_class[k] = v52_class

        cell = CELLS_ORDER[int(cell_idx_arr[k])]
        pr = int(pair_rank_arr[k])
        st = cell_stats[(pr, cell)]
        st["n"] += 1
        st["v52_sum_regret"] += regret
        if v52_idx == int(oracle_idxs[k]):
            st["v52_n_match_oracle"] += 1
        st["v52_class_dist"][v52_class] += 1
        st["v52_placement_dist"][placement] += 1
        if v52_idx == int(v44_idxs[k]):
            st["v44_v52_match"] += 1

        rs = rank_stats[pr]
        rs["n"] += 1
        rs["v52_sum_regret"] += regret
        if v52_idx == int(oracle_idxs[k]):
            rs["v52_n_match_oracle"] += 1

        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ===========================================================
    # Per-pair-rank residual table (v52 vs oracle)
    # ===========================================================
    print("=" * 100)
    print("v52 PER-PAIR-RANK RESIDUAL (canonical-equal weighting)")
    print("=" * 100)
    print(f"  {'pair':>4} {'n_hands':>9} {'v52_pct_opt':>11} {'v52_mean_reg':>14} "
          f"{'v52_wg':>10}")
    for pr in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[pr]
        if rs["n"] == 0:
            continue
        pct_opt = 100 * rs["v52_n_match_oracle"] / rs["n"]
        mean_reg = rs["v52_sum_regret"] / rs["n"] * EV_TO_DOL * 1000
        wg = rs["v52_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {RANK_CHAR[pr]:>4} {rs['n']:>9,} {pct_opt:>10.2f}% "
              f"${mean_reg:>+12.1f} ${wg:>+8.2f}")

    # ===========================================================
    # Per-cell v52→oracle residual table
    # ===========================================================
    print("\n" + "=" * 100)
    print("v52 PER-(pair_rank, cell) RESIDUAL")
    print("=" * 100)
    print(f"  {'pair':>4} {'cell':<18} {'n':>9} {'pct_opt':>8} "
          f"{'v52_mean':>11} {'v52_wg':>10}")
    for pr in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((pr, cell), None)
            if st is None or st["n"] == 0:
                continue
            pct_opt = 100 * st["v52_n_match_oracle"] / st["n"]
            mean_reg = st["v52_sum_regret"] / st["n"] * EV_TO_DOL * 1000
            wg = st["v52_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"  {RANK_CHAR[pr]:>4} {cell:<18} {st['n']:>9,} "
                  f"{pct_opt:>7.2f}% ${mean_reg:>+9.1f} ${wg:>+8.2f}")

    # ===========================================================
    # Save augmented parquet + summary JSON
    # ===========================================================
    if not args.no_parquet:
        print(f"\n[4/4] writing v52 parquet to {OUT_PARQUET} ...", flush=True)
        table = pa.table({
            "canonical_id": pa.array(cids, type=pa.uint32()),
            "pair_rank": pa.array(pair_rank_arr, type=pa.int8()),
            "cell_idx": pa.array(cell_idx_arr, type=pa.int8()),
            "v52_idx": pa.array(arr_v52_idx, type=pa.int16()),
            "v52_regret": pa.array(arr_v52_regret, type=pa.float32()),
            "v52_placement": pa.array(arr_v52_placement, type=pa.int8()),
            "v52_top_type": pa.array(arr_v52_top_type, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        summary = {
            "n_pair_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "rank_stats": {},
            "cell_stats": {},
        }
        for pr, rs in rank_stats.items():
            summary["rank_stats"][str(pr)] = {
                "n": int(rs["n"]),
                "v52_sum_regret": float(rs["v52_sum_regret"]),
                "v52_n_match_oracle": int(rs["v52_n_match_oracle"]),
                "v52_mean_regret_dollars": float(rs["v52_sum_regret"] / rs["n"] * EV_TO_DOL * 1000),
                "v52_wg_dollars": float(rs["v52_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v52_pct_opt": float(100 * rs["v52_n_match_oracle"] / rs["n"]),
            }
        for (pr, cell), st in cell_stats.items():
            summary["cell_stats"][f"{pr}|{cell}"] = {
                "n": int(st["n"]),
                "v52_sum_regret": float(st["v52_sum_regret"]),
                "v52_n_match_oracle": int(st["v52_n_match_oracle"]),
                "v52_mean_regret_dollars": float(st["v52_sum_regret"] / st["n"] * EV_TO_DOL * 1000),
                "v52_wg_dollars": float(st["v52_sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "v52_pct_opt": float(100 * st["v52_n_match_oracle"] / st["n"]),
                "v52_class_dist": dict(st["v52_class_dist"].most_common(15)),
                "v52_placement_dist": dict(st["v52_placement_dist"]),
                "v44_v52_match_pct": float(100 * st["v44_v52_match"] / st["n"]),
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
