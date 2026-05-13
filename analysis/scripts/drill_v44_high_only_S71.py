"""
Session 71 Phase 1a — high_only diagnostic sweep with a NEW lens beyond
S58/S59: the SETTING-RANK partition.

WHY A NEW LENS
--------------
S58/S59 mined high_only at the CLASS-label level (top_rank × bot_suit ×
mid_suited). That lens identified the K/Q × DS_NO_JOINT cell as the
deepest residual; v45_dt added 4 ho_v5 features targeting it; v45_dt
NULL-graded at $0/1000h vs v44_dt (Decision 094). S59 diagnosed the NULL
as DT saturation at depth=36 ml=1 with 2.25M leaves on 6M rows — the new
features were mathematically REDUNDANT with v4's signals, so the DT
already had enough info to split correctly but couldn't on the
saturation-stressed leaves.

The class-label lens alone cannot distinguish "v44 picked rank-2 (a
near-optimal alternative) — irreducible noise" from "v44 picked rank-10
(structurally wrong) — a missing-signal residual". Both look like a
mismatch in the S58 table. But ONLY the second is closeable with new
features; the first is irreducible against oracle's N=200 noise.

S71 PARTITIONS THE $755 WG HIGH_ONLY RESIDUAL INTO:
  - NOISE LEAK   = v44 picks rank ≤ 3 in oracle's sorted-EV list. The
                   EV gap to best is small; multiple equally-good
                   settings exist; new features can't help.
  - STRUCTURE LEAK = v44 picks rank ≥ 10. v44 is far from the top-3
                   plateau; a feature could re-route to it.
  - MID LEAK     = v44 picks rank 4..9. Marginal feature-engineering
                   potential.

If NOISE LEAK dominates, the S59 NULL was inherent; further ML retrain
on high_only is futile (pivot to rule chain or model class).
If STRUCTURE LEAK dominates, new features CAN ship; the question becomes
which structural signature differentiates the rank-10+ misses.

WHAT THIS SCRIPT PRODUCES
-------------------------
A per-hand parquet (high_only-only, 1.226M rows) with the v44 setting
rank and EV-gap structure. The structural-cell columns from S59 are
re-derived locally (this script is self-contained; it does not depend on
the S59 parquet, but writes the same cell taxonomy so output is
comparable).

Aggregations per (max_rank × structural cell × setting-rank bucket):
  HO_S71_1 — Per (max, cell) noise/structure WG decomposition.
  HO_S71_2 — Per (max, cell) setting-rank histogram + ev_gap_to_best.
  HO_S71_3 — Per (max, cell, rank-bucket) top mismatch CLASSES — what
             does v44 pick when it's rank-10+ vs when it's rank-2-3?
  HO_S71_4 — Per-hand "EV plateau width" — the gap between oracle's
             top EV and oracle's 3rd-best EV. Wide plateau = many
             near-optimal settings = noise zone; narrow plateau = sharp
             optimum = structure zone.

Outputs:
  data/drill_v44_high_only_S71_per_hand.parquet
  data/drill_v44_high_only_S71_summary.json
  data/session71/drill_v44_high_only_S71.log (via stdout redirect)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_high_only_S71.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_high_only_S71.py --sample 50000
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
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SETTING_HAND_INDICES,
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)
from strategy_v44_dt import strategy_v44_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
OUT_PARQUET = ROOT / "data" / "drill_v44_high_only_S71_per_hand.parquet"
OUT_JSON = ROOT / "data" / "drill_v44_high_only_S71_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_SETTINGS = 105

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}
SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS",
    SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "RB",
    SUIT_PROFILE_THREE_ONE: "31",
    SUIT_PROFILE_FOUR_FLUSH: "4f",
}

CELLS_ORDER = ["JOINT_HIGH", "JOINT_MED", "JOINT_LOW",
               "DS_NO_JOINT", "DS_NO_MAXTOP", "MS_ONLY", "NEITHER"]

# Setting-rank bucketing: the NOISE/MID/STRUCTURE partition.
#   rank 1     = match (no leak)
#   rank 2-3   = NOISE leak  (irreducible vs N=200 oracle noise)
#   rank 4-9   = MID leak    (marginal feature potential)
#   rank 10+   = STRUCTURE leak (testable missing-signal hypothesis)
def rank_bucket(rank: int) -> str:
    if rank == 1:
        return "MATCH"
    if rank <= 3:
        return "NOISE"
    if rank <= 9:
        return "MID"
    return "STRUCTURE"

BUCKETS_ORDER = ["MATCH", "NOISE", "MID", "STRUCTURE"]


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


def classify_pick(hand_bytes, idx: int):
    """Compact (top_rank_char, bot_suit_kind, mid_suited?) class label."""
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    top_rank = int(ranks[top_pos])
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_lbl = "ms" if mid_suits[0] == mid_suits[1] else "mu"
    bot_suits_arr = [int(suits[p]) for p in bot_pos]
    bot_suit_lbl = _bot_suit_kind(bot_suits_arr)
    return f"t{RANK_CHAR[top_rank]}_{bot_suit_lbl}_{mid_lbl}"


def compute_hand_structural_minimal(hand_bytes):
    """Same cell taxonomy as S59 (drill_high_only_v44_deepdive.py)."""
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    max_rank = max(int_ranks)
    max_pos = int_ranks.index(max_rank)

    n_DS = 0
    n_DS_with_max_top = 0
    n_joint = 0
    best_ms_mid_high = 0

    for bot_idx in combinations(range(7), 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        n_DS += 1
        leftover_pos = [i for i in range(7) if i not in bot_idx]
        if max_pos in leftover_pos:
            n_DS_with_max_top += 1
            mid_pos = [j for j in leftover_pos if j != max_pos]
            if int_suits[mid_pos[0]] == int_suits[mid_pos[1]]:
                n_joint += 1
                mh = max(int_ranks[mid_pos[0]], int_ranks[mid_pos[1]])
                if mh > best_ms_mid_high:
                    best_ms_mid_high = mh

    n_ms_mid_with_max_top = 0
    for top_pos in range(7):
        if top_pos != max_pos:
            continue
        rest = [i for i in range(7) if i != top_pos]
        for mid_a, mid_b in combinations(rest, 2):
            if int_suits[mid_a] == int_suits[mid_b]:
                n_ms_mid_with_max_top += 1

    if n_joint > 0:
        if best_ms_mid_high >= 11:
            cell = "JOINT_HIGH"
        elif best_ms_mid_high >= 8:
            cell = "JOINT_MED"
        else:
            cell = "JOINT_LOW"
    elif n_DS_with_max_top > 0:
        cell = "DS_NO_JOINT"
    elif n_DS > 0:
        cell = "DS_NO_MAXTOP"
    elif n_ms_mid_with_max_top > 0:
        cell = "MS_ONLY"
    else:
        cell = "NEITHER"

    return {"max_rank": max_rank, "cell": cell,
            "n_DS_bot_configs": n_DS,
            "n_DS_bot_with_max_top": n_DS_with_max_top,
            "n_joint_DS_ms_max_top": n_joint,
            "best_ms_mid_high": best_ms_mid_high,
            "n_ms_mid_with_max_top": n_ms_mid_with_max_top}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample hands to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true")
    args = ap.parse_args()

    print("=" * 90)
    print("Session 71 Phase 1a — high_only setting-rank diagnostic on v44_dt")
    print("=" * 90)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("Goal: partition $755 WG high_only residual into")
    print("      NOISE (rank 2-3) / MID (rank 4-9) / STRUCTURE (rank ≥10)")
    print("      to test the S59 NULL hypothesis: 'feature redundancy at saturation'.\n")

    print("[1/4] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]
    n_ho = len(ho_idx)
    print(f"  high_only hands: {n_ho:,}")

    if args.sample > 0 and n_ho > args.sample:
        rng = np.random.default_rng(args.seed)
        ho_idx = np.sort(rng.choice(ho_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid (memmap) ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(ho_idx)
    arr_cid = np.zeros(n, dtype=np.uint32)
    arr_max = np.zeros(n, dtype=np.int8)
    arr_cell = np.zeros(n, dtype=np.int8)
    arr_v44_idx = np.zeros(n, dtype=np.int16)
    arr_oracle_idx = np.zeros(n, dtype=np.int16)
    arr_v44_rank = np.zeros(n, dtype=np.int16)
    arr_regret = np.zeros(n, dtype=np.float32)
    arr_ev_best = np.zeros(n, dtype=np.float32)
    arr_ev_v44 = np.zeros(n, dtype=np.float32)
    arr_gap_2nd = np.zeros(n, dtype=np.float32)   # ev_best - ev_2nd
    arr_gap_3rd = np.zeros(n, dtype=np.float32)   # ev_best - ev_3rd
    arr_gap_median = np.zeros(n, dtype=np.float32)  # ev_best - ev_median
    arr_n_within_eps = np.zeros(n, dtype=np.int16)  # # of settings within 0.5% of best EV
    arr_bucket = np.zeros(n, dtype=np.int8)
    arr_n_DS = np.zeros(n, dtype=np.int8)
    arr_n_DS_max_top = np.zeros(n, dtype=np.int8)
    arr_n_joint = np.zeros(n, dtype=np.int8)
    arr_best_ms_mid_high = np.zeros(n, dtype=np.int8)
    arr_n_ms_mid_max_top = np.zeros(n, dtype=np.int8)

    # Aggregations.
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_by_bucket": Counter(),
        "regret_by_bucket": defaultdict(float),
        "mismatch_by_bucket": defaultdict(Counter),
        "regret_by_mismatch_bucket": defaultdict(lambda: defaultdict(float)),
        "rank_histogram": Counter(),
        "gap_2nd_by_bucket": defaultdict(list),
        "gap_3rd_by_bucket": defaultdict(list),
    })
    rank_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_by_bucket": Counter(),
        "regret_by_bucket": defaultdict(float),
    })

    EPS_REL = 0.005  # 0.5% of |ev_best|

    print("\n[3/4] sweeping per-hand v44 vs oracle (rank + ev-gap) ...", flush=True)
    t0 = time.time()
    for k, cid in enumerate(ho_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        sort_desc = np.argsort(-rowf)
        oracle_idx = int(sort_desc[0])
        ev_best = float(rowf[oracle_idx])
        ev_2nd = float(rowf[sort_desc[1]])
        ev_3rd = float(rowf[sort_desc[2]]) if N_SETTINGS >= 3 else ev_2nd
        ev_median = float(rowf[sort_desc[N_SETTINGS // 2]])
        v44_idx = int(strategy_v44_dt(h))
        ev_v44 = float(rowf[v44_idx])
        # v44_rank = (# of settings strictly better than v44) + 1
        v44_rank = int((rowf > ev_v44).sum()) + 1
        regret = ev_best - ev_v44
        # # settings within EPS_REL of ev_best (plateau width metric)
        thresh = abs(ev_best) * EPS_REL
        n_within_eps = int((rowf >= ev_best - thresh).sum())

        struct = compute_hand_structural_minimal(h)
        cell = struct["cell"]
        max_rank = struct["max_rank"]
        bucket = rank_bucket(v44_rank)

        arr_cid[k] = cid
        arr_max[k] = max_rank
        arr_cell[k] = CELLS_ORDER.index(cell)
        arr_v44_idx[k] = v44_idx
        arr_oracle_idx[k] = oracle_idx
        arr_v44_rank[k] = v44_rank
        arr_regret[k] = regret
        arr_ev_best[k] = ev_best
        arr_ev_v44[k] = ev_v44
        arr_gap_2nd[k] = ev_best - ev_2nd
        arr_gap_3rd[k] = ev_best - ev_3rd
        arr_gap_median[k] = ev_best - ev_median
        arr_n_within_eps[k] = n_within_eps
        arr_bucket[k] = BUCKETS_ORDER.index(bucket)
        arr_n_DS[k] = struct["n_DS_bot_configs"]
        arr_n_DS_max_top[k] = struct["n_DS_bot_with_max_top"]
        arr_n_joint[k] = struct["n_joint_DS_ms_max_top"]
        arr_best_ms_mid_high[k] = struct["best_ms_mid_high"]
        arr_n_ms_mid_max_top[k] = struct["n_ms_mid_with_max_top"]

        st = cell_stats[(max_rank, cell)]
        st["n"] += 1
        st["sum_regret"] += regret
        st["n_by_bucket"][bucket] += 1
        st["regret_by_bucket"][bucket] += regret
        st["rank_histogram"][min(v44_rank, 20)] += 1
        if bucket != "MATCH":
            v_cls = classify_pick(h, v44_idx)
            o_cls = classify_pick(h, oracle_idx)
            st["mismatch_by_bucket"][bucket][(v_cls, o_cls)] += 1
            st["regret_by_mismatch_bucket"][bucket][(v_cls, o_cls)] += regret
        if len(st["gap_2nd_by_bucket"][bucket]) < 5000:
            st["gap_2nd_by_bucket"][bucket].append(ev_best - ev_2nd)
        if len(st["gap_3rd_by_bucket"][bucket]) < 5000:
            st["gap_3rd_by_bucket"][bucket].append(ev_best - ev_3rd)

        rs = rank_stats[max_rank]
        rs["n"] += 1
        rs["sum_regret"] += regret
        rs["n_by_bucket"][bucket] += 1
        rs["regret_by_bucket"][bucket] += regret

        if (k + 1) % 100_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ===========================================================
    # HO_S71_1 — Per (max, cell) noise/structure WG decomposition
    # ===========================================================
    print("=" * 110)
    print("HO_S71_1: NOISE/MID/STRUCTURE WG DECOMPOSITION (per max_rank × cell)")
    print("=" * 110)
    print("  Interpretation:")
    print("    MATCH     = v44 == oracle  (rank 1)")
    print("    NOISE     = v44 in top 3   (rank 2-3, irreducible vs N=200 oracle noise)")
    print("    MID       = v44 in top 9   (rank 4-9, marginal feature potential)")
    print("    STRUCTURE = v44 rank ≥10   (testable missing-signal hypothesis)\n")

    print(f"  {'max':>3} {'cell':<14} {'n':>9} "
          f"{'MATCH %':>9} {'NOISE %':>9} {'MID %':>9} {'STR %':>9} "
          f"{'NOISE $':>9} {'MID $':>9} {'STR $':>9}  ←wg by bucket")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((max_rank, cell))
            if st is None or st["n"] == 0:
                continue
            nn = st["n"]
            pcts = {b: 100 * st["n_by_bucket"].get(b, 0) / nn for b in BUCKETS_ORDER}
            wgs = {b: st["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
                   for b in BUCKETS_ORDER}
            print(f"  {RANK_CHAR[max_rank]:>3} {cell:<14} {nn:>9,} "
                  f"{pcts['MATCH']:>8.1f}% {pcts['NOISE']:>8.1f}% "
                  f"{pcts['MID']:>8.1f}% {pcts['STRUCTURE']:>8.1f}% "
                  f"${wgs['NOISE']:>+8.2f} ${wgs['MID']:>+8.2f} "
                  f"${wgs['STRUCTURE']:>+8.2f}")

    print("\n  Per max_rank rollup:")
    print(f"    {'max':>3} {'n':>9} {'MATCH':>7} "
          f"{'NOISE $':>9} {'MID $':>9} {'STR $':>9} {'TOTAL $':>9}")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if rs["n"] == 0:
            continue
        nn = rs["n"]
        pct_match = 100 * rs["n_by_bucket"].get("MATCH", 0) / nn
        wgs = {b: rs["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
               for b in BUCKETS_ORDER}
        total_wg = rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"    {RANK_CHAR[max_rank]:>3} {nn:>9,} {pct_match:>6.1f}% "
              f"${wgs['NOISE']:>+8.2f} ${wgs['MID']:>+8.2f} "
              f"${wgs['STRUCTURE']:>+8.2f} ${total_wg:>+8.2f}")

    grand_n = sum(rs["n"] for rs in rank_stats.values())
    grand_buckets = Counter()
    grand_buckets_wg = defaultdict(float)
    for rs in rank_stats.values():
        for b in BUCKETS_ORDER:
            grand_buckets[b] += rs["n_by_bucket"].get(b, 0)
            grand_buckets_wg[b] += rs["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
    print("\n  GRAND TOTAL across high_only:")
    print(f"    {'bucket':<12} {'n':>10} {'pct':>7} {'wg $':>9}")
    total_wg_all = sum(grand_buckets_wg.values())
    for b in BUCKETS_ORDER:
        nc = grand_buckets[b]
        pct = 100 * nc / grand_n if grand_n else 0
        wg = grand_buckets_wg[b]
        pct_wg = 100 * wg / total_wg_all if total_wg_all else 0
        print(f"    {b:<12} {nc:>10,} {pct:>6.1f}% ${wg:>+8.2f}  ({pct_wg:>4.1f}% of WG)")
    print(f"    {'TOTAL':<12} {grand_n:>10,}        ${total_wg_all:>+8.2f}")

    # ===========================================================
    # HO_S71_2 — Setting-rank histogram per cell
    # ===========================================================
    print("\n" + "=" * 110)
    print("HO_S71_2: SETTING-RANK HISTOGRAM PER CELL (top 5 cells by WG)")
    print("=" * 110)
    cell_total_wg = {}
    for (max_rank, cell), st in cell_stats.items():
        wg = st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        cell_total_wg[(max_rank, cell)] = wg
    top_cells = sorted(cell_total_wg.items(), key=lambda x: -x[1])[:8]
    for (max_rank, cell), wg in top_cells:
        st = cell_stats[(max_rank, cell)]
        nn = st["n"]
        print(f"\n  ── max={RANK_CHAR[max_rank]} cell={cell}  n={nn:,}  total_wg=${wg:.2f} ──")
        hist = st["rank_histogram"]
        print(f"    {'rank':>5} {'count':>9} {'pct':>7}  {'cumpct':>7}")
        cum = 0
        for r in range(1, 21):
            c = hist.get(r, 0)
            pct = 100 * c / nn
            cum += pct
            label = "≥20" if r == 20 else str(r)
            print(f"    {label:>5} {c:>9,} {pct:>6.1f}% {cum:>6.1f}%")

    # ===========================================================
    # HO_S71_3 — Mismatch classes per bucket
    # ===========================================================
    print("\n" + "=" * 110)
    print("HO_S71_3: TOP MISMATCH CLASSES PER (cell × bucket)")
    print("=" * 110)
    print("  STRUCTURE-bucket mismatches are the v45_dt+ target population.\n")
    for (max_rank, cell), wg_tot in top_cells[:6]:
        st = cell_stats[(max_rank, cell)]
        for bucket in ("STRUCTURE", "MID", "NOISE"):
            mismatches = st["regret_by_mismatch_bucket"].get(bucket, {})
            if not mismatches:
                continue
            ranked = sorted(mismatches.items(), key=lambda x: -x[1])
            bucket_wg = st["regret_by_bucket"][bucket] * EV_TO_DOL * 1000 / N_TOTAL_GRID
            bucket_n = st["n_by_bucket"][bucket]
            print(f"  ── max={RANK_CHAR[max_rank]} cell={cell} bucket={bucket}  "
                  f"n={bucket_n:,} wg=${bucket_wg:.2f} ──")
            for (vc, oc), reg in ranked[:5]:
                n = st["mismatch_by_bucket"][bucket][(vc, oc)]
                mean_reg = reg / n * EV_TO_DOL * 1000
                wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
                print(f"    {vc:<14} -> {oc:<14} n={n:>7,} mean=${mean_reg:>+7.0f} "
                      f"wg=${wg:>+6.2f}")

    # ===========================================================
    # HO_S71_4 — EV-gap structure: is the optimum sharp or flat?
    # ===========================================================
    print("\n" + "=" * 110)
    print("HO_S71_4: EV-GAP STRUCTURE BY BUCKET (mean & median over sampled hands per cell × bucket)")
    print("=" * 110)
    print("  gap_2nd = ev_best - ev_2nd  (sharpness of optimum)")
    print("  Sharp optimum + v44 rank ≥10 = strong structure-leak signal.")
    print("  Flat optimum (gap_2nd ≈ 0) + v44 rank 2-3 = pure noise.\n")
    for (max_rank, cell), _ in top_cells[:5]:
        st = cell_stats[(max_rank, cell)]
        nn = st["n"]
        print(f"  ── max={RANK_CHAR[max_rank]} cell={cell}  n={nn:,} ──")
        for bucket in BUCKETS_ORDER:
            gaps_2nd = st["gap_2nd_by_bucket"].get(bucket, [])
            gaps_3rd = st["gap_3rd_by_bucket"].get(bucket, [])
            if not gaps_2nd:
                continue
            mean_2 = float(np.mean(gaps_2nd))
            med_2 = float(np.median(gaps_2nd))
            mean_3 = float(np.mean(gaps_3rd))
            print(f"    {bucket:<10} (sampled n={len(gaps_2nd):,})  "
                  f"gap_2nd mean={mean_2:.4f} med={med_2:.4f}   "
                  f"gap_3rd mean={mean_3:.4f}")

    # ===========================================================
    # Persistence
    # ===========================================================
    if not args.no_parquet:
        print(f"\n[4/4] writing per-hand parquet to {OUT_PARQUET} ...", flush=True)
        table = pa.table({
            "canonical_id": pa.array(arr_cid, type=pa.uint32()),
            "max_rank": pa.array(arr_max, type=pa.int8()),
            "cell_idx": pa.array(arr_cell, type=pa.int8()),
            "v44_idx": pa.array(arr_v44_idx, type=pa.int16()),
            "oracle_idx": pa.array(arr_oracle_idx, type=pa.int16()),
            "v44_rank": pa.array(arr_v44_rank, type=pa.int16()),
            "regret": pa.array(arr_regret, type=pa.float32()),
            "ev_best": pa.array(arr_ev_best, type=pa.float32()),
            "ev_v44": pa.array(arr_ev_v44, type=pa.float32()),
            "gap_2nd": pa.array(arr_gap_2nd, type=pa.float32()),
            "gap_3rd": pa.array(arr_gap_3rd, type=pa.float32()),
            "gap_median": pa.array(arr_gap_median, type=pa.float32()),
            "n_within_eps": pa.array(arr_n_within_eps, type=pa.int16()),
            "bucket_idx": pa.array(arr_bucket, type=pa.int8()),
            "n_DS_bot_configs": pa.array(arr_n_DS, type=pa.int8()),
            "n_DS_bot_with_max_top": pa.array(arr_n_DS_max_top, type=pa.int8()),
            "n_joint_DS_ms_max_top": pa.array(arr_n_joint, type=pa.int8()),
            "best_ms_mid_high": pa.array(arr_best_ms_mid_high, type=pa.int8()),
            "n_ms_mid_with_max_top": pa.array(arr_n_ms_mid_max_top, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3, write_statistics=True)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        summary = {
            "n_high_only_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "buckets_order": BUCKETS_ORDER,
            "rank_stats": {},
            "cell_stats": {},
            "grand_buckets": {
                b: {"n": int(grand_buckets[b]),
                    "wg": float(grand_buckets_wg[b])}
                for b in BUCKETS_ORDER
            },
            "grand_n": int(grand_n),
        }
        for max_rank, rs in rank_stats.items():
            summary["rank_stats"][str(max_rank)] = {
                "n": int(rs["n"]),
                "sum_regret": float(rs["sum_regret"]),
                "total_wg": float(rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "n_by_bucket": {b: int(rs["n_by_bucket"].get(b, 0))
                                for b in BUCKETS_ORDER},
                "wg_by_bucket": {b: float(rs["regret_by_bucket"].get(b, 0.0)
                                          * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                                 for b in BUCKETS_ORDER},
            }
        for (max_rank, cell), st in cell_stats.items():
            key = f"{max_rank}|{cell}"
            summary["cell_stats"][key] = {
                "n": int(st["n"]),
                "total_wg": float(st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "n_by_bucket": {b: int(st["n_by_bucket"].get(b, 0))
                                for b in BUCKETS_ORDER},
                "wg_by_bucket": {b: float(st["regret_by_bucket"].get(b, 0.0)
                                          * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                                 for b in BUCKETS_ORDER},
                "rank_histogram": {str(r): int(c)
                                   for r, c in st["rank_histogram"].items()},
                "top_mismatches_by_bucket": {
                    b: [
                        {
                            "v44_class": vc,
                            "oracle_class": oc,
                            "n": int(st["mismatch_by_bucket"][b][(vc, oc)]),
                            "wg_dollars": float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                            "mean_regret_dollars": float(
                                reg / st["mismatch_by_bucket"][b][(vc, oc)]
                                * EV_TO_DOL * 1000),
                        }
                        for (vc, oc), reg in sorted(
                            st["regret_by_mismatch_bucket"].get(b, {}).items(),
                            key=lambda x: -x[1])[:8]
                    ]
                    for b in ("STRUCTURE", "MID", "NOISE")
                    if st["regret_by_mismatch_bucket"].get(b)
                },
                "gap_2nd_stats_by_bucket": {
                    b: {
                        "n_sampled": int(len(st["gap_2nd_by_bucket"].get(b, []))),
                        "mean": float(np.mean(st["gap_2nd_by_bucket"][b]))
                                if st["gap_2nd_by_bucket"].get(b) else 0.0,
                        "median": float(np.median(st["gap_2nd_by_bucket"][b]))
                                  if st["gap_2nd_by_bucket"].get(b) else 0.0,
                    }
                    for b in BUCKETS_ORDER
                    if st["gap_2nd_by_bucket"].get(b)
                },
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
