"""
Session 70 Phase 1 — Trips category deep-dive: structural cell
classification + oracle/v44 pick distribution per (trip_rank, cell).

Analog of `drill_two_pair_v44_S69.py`, scoped to category=trips (cat=3,
n=328,185 canonical hands = 5.46% of canonical-grid).

Output:
  data/drill_trips_v44_per_hand_structural.parquet
  data/drill_trips_v44_summary.json
  Console: per-trip_rank residual tables, structural cell cross-tab,
           and oracle pick profile per (trip_rank, cell).

Trips structural axes (informed by v44's trips_*_g + trips_v2_*_g feature
families, Session 36):

  Trips = 1 trip rank (3 cards, 3 distinct suits, 1 missing suit) + 4
  kickers (distinct ranks, suit-flexible).

  Canonical layouts (where the 3 trip cards go):
    A_paired_mid : top=kicker, mid=2 trips (paired), bot=1 trip + 3 kickers
    B_paired_bot : top=trip|kicker, mid=2 cards, bot=2 trips + 2 kickers
                   (paired bot; DS achievable iff ≥1 kicker in each of 2
                    trip-suits {a,b} so bot becomes 2-a + 2-b)
    C_top_trip   : top=trip, mid=2 trips (paired), bot=4 kickers
    SPLIT        : trips otherwise distributed (rare oracle pick)

  Cell taxonomy (4-cell scheme; priority order, first match wins):
    B_DS_AVAIL_HKR : trips_b_ds_avail_g == 1 AND best B-DS bot's 2nd-rank
                     kicker in trip-suits >= T (≥10) — strong B-DS bot
                     anchored by a broadway 2nd-kicker.
    B_DS_AVAIL_LKR : trips_b_ds_avail_g == 1 AND best B-DS 2nd-kicker < T
                     — B-DS bot anchored by mid/low kicker.
    NO_BDS_CTOP    : B-DS not avail AND trip_rank > max_kicker_rank
                     (C-top advantage cell).
    NO_BDS_AKDOM   : B-DS not avail AND there exists a kicker >= trip_rank
                     (A's top is competitive — kicker outranks trip).

  These 4 cells partition the population. Per-trip_rank stratification
  (12 ranks: 3..A) crosses with the 4 cells for a 4×12 matrix.

Pick classification (oracle / v44):
  layout:        'A' | 'B' | 'C' | 'SPLIT'
  bot_suit:      'DS' | 'SS' | '31' | 'RB' | '4f'
  top_type:      'TRIP' | 'KICKER_MAX' | 'KICKER_MID' | 'KICKER_LOW'
  mid_paired:    bool (mid is 2-trip-cards paired)
  Compact label: e.g. "A_RB_tkmax", "B_DS_ttrip", "C_RB_ttrip"

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_v44_S70.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_v44_S70.py --sample 5000
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
)
from strategy_v44_dt import strategy_v44_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
OUT_PARQUET = ROOT / "data" / "drill_trips_v44_per_hand_structural.parquet"
OUT_JSON = ROOT / "data" / "drill_trips_v44_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
BROADWAY_THRESH = 10  # T+ (10..A) = broadway tier for cell taxonomy

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

CELLS_ORDER = [
    "B_DS_AVAIL_HKR",
    "B_DS_AVAIL_LKR",
    "NO_BDS_CTOP",
    "NO_BDS_AKDOM",
]


def _bot_suit_kind(suits):
    """Return 'DS', 'SS', '31', 'RB', or '4f' for a 4-card suit list."""
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


def compute_trips_structural(hand_bytes):
    """Compute trips structural achievability counts and bookkeeping.

    Returns dict with:
      trip_rank, trip_pos (tuple 3), trip_suits (tuple 3, sorted),
      missing_suit (int 0..3),
      kicker_pos (tuple 4), kicker_ranks (tuple 4), kicker_suits (tuple 4),
      kicker_ranks_sorted (4-tuple desc),
      max_kicker_rank,
      b_ds_avail, n_b_ds_routings,
      best_b_ds_kicker_max_rank, best_b_ds_kicker_2nd_rank,
      kickers_max_suit_count, n_kickers_in_trip_suits,
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    rc = Counter(int_ranks)
    trip_rank = next(r for r, c in rc.items() if c == 3)
    trip_pos = tuple(i for i in range(7) if int_ranks[i] == trip_rank)
    assert len(trip_pos) == 3
    trip_suits = tuple(sorted(int_suits[p] for p in trip_pos))
    assert len(set(trip_suits)) == 3, "trip cards must occupy 3 distinct suits"
    missing_suit = ({0, 1, 2, 3} - set(trip_suits)).pop()

    kicker_pos = tuple(i for i in range(7) if i not in trip_pos)
    assert len(kicker_pos) == 4
    kicker_ranks = tuple(int_ranks[p] for p in kicker_pos)
    kicker_suits = tuple(int_suits[p] for p in kicker_pos)
    kicker_ranks_sorted = tuple(sorted(kicker_ranks, reverse=True))
    max_kicker_rank = kicker_ranks_sorted[0]

    # B-DS: bot = 2 trips (suits a,b) + 2 kickers. DS iff kickers contribute
    # 1 in suit a AND 1 in suit b.
    n_b_ds_routings = 0
    best_b_ds_kicker_max = 0
    best_b_ds_kicker_2nd = 0
    for a, b in combinations(trip_suits, 2):
        # Find kickers in suit a and suit b
        kickers_in_a = [
            (kicker_ranks[i], kicker_pos[i]) for i in range(4)
            if kicker_suits[i] == a
        ]
        kickers_in_b = [
            (kicker_ranks[i], kicker_pos[i]) for i in range(4)
            if kicker_suits[i] == b
        ]
        if not kickers_in_a or not kickers_in_b:
            continue
        # At least one routing exists: pick best kicker in a, best in b
        n_b_ds_routings += 1
        # Best 2-kicker pair (max rank, 2nd max rank among the chosen pair)
        # For this routing, the bot has the (rank of a-kicker, rank of
        # b-kicker). Track the best pair by sum of ranks (proxy for bot
        # quality after board).
        for ra, _ in kickers_in_a:
            for rb, _ in kickers_in_b:
                rk_max = max(ra, rb)
                rk_2nd = min(ra, rb)
                # "Best" by max first, then 2nd
                if (rk_max, rk_2nd) > (best_b_ds_kicker_max,
                                       best_b_ds_kicker_2nd):
                    best_b_ds_kicker_max = rk_max
                    best_b_ds_kicker_2nd = rk_2nd
    b_ds_avail = 1 if n_b_ds_routings > 0 else 0

    kicker_suit_counts = Counter(kicker_suits)
    kickers_max_suit_count = max(kicker_suit_counts.values())
    n_kickers_in_trip_suits = sum(
        1 for s in kicker_suits if s in trip_suits
    )

    return {
        "trip_rank": trip_rank,
        "trip_pos": trip_pos,
        "trip_suits": trip_suits,
        "missing_suit": missing_suit,
        "kicker_pos": kicker_pos,
        "kicker_ranks": kicker_ranks,
        "kicker_suits": kicker_suits,
        "kicker_ranks_sorted": kicker_ranks_sorted,
        "max_kicker_rank": max_kicker_rank,
        "b_ds_avail": b_ds_avail,
        "n_b_ds_routings": n_b_ds_routings,
        "best_b_ds_kicker_max_rank": best_b_ds_kicker_max,
        "best_b_ds_kicker_2nd_rank": best_b_ds_kicker_2nd,
        "kickers_max_suit_count": kickers_max_suit_count,
        "n_kickers_in_trip_suits": n_kickers_in_trip_suits,
    }


def cell_for_trips_hand(struct):
    """Map trips structural counts to a 4-cell taxonomy.

    Priority (first match wins):
      B_DS_AVAIL_HKR : b_ds_avail AND best_b_ds_kicker_2nd_rank >= 10 (T+)
      B_DS_AVAIL_LKR : b_ds_avail AND best_b_ds_kicker_2nd_rank <  10
      NO_BDS_CTOP    : NOT b_ds_avail AND trip_rank > max_kicker_rank
      NO_BDS_AKDOM   : NOT b_ds_avail AND max_kicker_rank >= trip_rank
    """
    if struct["b_ds_avail"]:
        if struct["best_b_ds_kicker_2nd_rank"] >= BROADWAY_THRESH:
            return "B_DS_AVAIL_HKR"
        return "B_DS_AVAIL_LKR"
    if struct["trip_rank"] > struct["max_kicker_rank"]:
        return "NO_BDS_CTOP"
    return "NO_BDS_AKDOM"


def classify_pick_trips(hand_bytes, idx, struct):
    """Classify a chosen setting for a trips hand into structural labels.

    Returns dict with:
      layout:       'A' | 'B' | 'C' | 'SPLIT'
      bot_suit:     'DS' | 'SS' | '31' | 'RB' | '4f'
      top_type:     'TRIP' | 'KICKER_MAX' | 'KICKER_MID' | 'KICKER_LOW'
      top_rank, mid_high, mid_low, mid_sum, mid_paired
      bot_max, bot_min, bot_sum, bot_run
      class_label:  compact composite label
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3

    trip_pos_set = set(struct["trip_pos"])
    kicker_pos_set = set(struct["kicker_pos"])
    kicker_ranks_sorted = struct["kicker_ranks_sorted"]

    n_trip_top = 1 if top_pos in trip_pos_set else 0
    n_trip_mid = sum(1 for p in mid_pos if p in trip_pos_set)
    n_trip_bot = sum(1 for p in bot_pos if p in trip_pos_set)

    # Canonical layouts:
    #   A_paired_mid: trips = 0/2/1  (mid has 2 trips, bot has 1 trip)
    #   B_paired_bot: trips = ?/?/2  (bot has 2 trips, top+mid take 1 trip)
    #   C_top_trip:   trips = 1/2/0  (top has trip, mid has 2 trips, bot 0)
    #   SPLIT:        any other
    if n_trip_top == 0 and n_trip_mid == 2 and n_trip_bot == 1:
        layout = "A"
    elif n_trip_bot == 2:
        layout = "B"
    elif n_trip_top == 1 and n_trip_mid == 2 and n_trip_bot == 0:
        layout = "C"
    else:
        layout = "SPLIT"

    bot_suits_arr = [int(suits[p]) for p in bot_pos]
    bot_suit_kind = _bot_suit_kind(bot_suits_arr)

    top_rank = int(ranks[top_pos])
    if top_pos in trip_pos_set:
        top_type = "TRIP"
    else:
        # Compare to kicker ranks (sorted descending: 4 kickers)
        if top_rank == kicker_ranks_sorted[0]:
            top_type = "KICKER_MAX"
        elif top_rank == kicker_ranks_sorted[3]:
            top_type = "KICKER_LOW"
        else:
            top_type = "KICKER_MID"

    mid_ranks = [int(ranks[mid_pos[0]]), int(ranks[mid_pos[1]])]
    mid_ranks_sorted = sorted(mid_ranks, reverse=True)
    mid_paired = (
        mid_pos[0] in trip_pos_set and mid_pos[1] in trip_pos_set
    )

    bot_ranks_sorted = sorted([int(ranks[p]) for p in bot_pos], reverse=True)

    def _longest_run(rs):
        s = sorted(set(rs))
        longest = cur = 1
        for i in range(1, len(s)):
            if s[i] == s[i - 1] + 1:
                cur += 1
                longest = max(longest, cur)
            else:
                cur = 1
        return longest

    bot_run = _longest_run([int(ranks[p]) for p in bot_pos])

    top_lbl_short = {
        "TRIP": "ttrip", "KICKER_MAX": "tkmax",
        "KICKER_MID": "tkmid", "KICKER_LOW": "tklow",
    }[top_type]
    if layout in ("A", "B", "C"):
        class_label = f"{layout}_{bot_suit_kind}_{top_lbl_short}"
    else:
        class_label = f"SPLIT_{bot_suit_kind}_{top_lbl_short}"

    return {
        "layout": layout,
        "bot_suit": bot_suit_kind,
        "top_type": top_type,
        "top_rank": top_rank,
        "mid_high": mid_ranks_sorted[0],
        "mid_low": mid_ranks_sorted[1],
        "mid_sum": mid_ranks_sorted[0] + mid_ranks_sorted[1],
        "mid_paired": mid_paired,
        "bot_max": bot_ranks_sorted[0],
        "bot_min": bot_ranks_sorted[3],
        "bot_sum": sum(bot_ranks_sorted),
        "bot_run": bot_run,
        "class_label": class_label,
    }


_LAYOUT_CODE = {"A": 0, "B": 1, "C": 2, "SPLIT": 3}
_BOT_SUIT_CODE = {"DS": 0, "SS": 1, "31": 2, "RB": 3, "4f": 4}
_TOP_TYPE_CODE = {"TRIP": 0, "KICKER_MAX": 1, "KICKER_MID": 2, "KICKER_LOW": 3}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample hands to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 70 Phase 1 — Trips deep-dive (oracle + v44_dt vs structural cell)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tr_idx = np.where(cats == 3)[0]
    n_tr = len(tr_idx)
    print(f"  trips hands: {n_tr:,}")

    if args.sample > 0 and n_tr > args.sample:
        rng = np.random.default_rng(args.seed)
        tr_idx = np.sort(rng.choice(tr_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(tr_idx)
    arr_cid = np.zeros(n, dtype=np.uint32)
    arr_trip_rank = np.zeros(n, dtype=np.int8)
    arr_max_kicker = np.zeros(n, dtype=np.int8)
    arr_b_ds_avail = np.zeros(n, dtype=np.bool_)
    arr_n_b_ds_rt = np.zeros(n, dtype=np.int8)
    arr_b_ds_max = np.zeros(n, dtype=np.int8)
    arr_b_ds_2nd = np.zeros(n, dtype=np.int8)
    arr_max_suit_cnt = np.zeros(n, dtype=np.int8)
    arr_n_in_ts = np.zeros(n, dtype=np.int8)
    arr_cell = np.zeros(n, dtype=np.int8)
    arr_v44_idx = np.zeros(n, dtype=np.int16)
    arr_oracle_idx = np.zeros(n, dtype=np.int16)
    arr_regret = np.zeros(n, dtype=np.float32)
    arr_v44_layout = np.zeros(n, dtype=np.int8)
    arr_v44_bot_suit = np.zeros(n, dtype=np.int8)
    arr_v44_top_type = np.zeros(n, dtype=np.int8)
    arr_v44_top_rank = np.zeros(n, dtype=np.int8)
    arr_v44_mid_paired = np.zeros(n, dtype=np.bool_)
    arr_v44_bot_run = np.zeros(n, dtype=np.int8)
    arr_or_layout = np.zeros(n, dtype=np.int8)
    arr_or_bot_suit = np.zeros(n, dtype=np.int8)
    arr_or_top_type = np.zeros(n, dtype=np.int8)
    arr_or_top_rank = np.zeros(n, dtype=np.int8)
    arr_or_mid_paired = np.zeros(n, dtype=np.bool_)
    arr_or_bot_run = np.zeros(n, dtype=np.int8)

    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_match": 0,
        "v44_class_dist": Counter(),
        "oracle_class_dist": Counter(),
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
        "or_layout_dist": Counter(),
        "or_top_type_dist": Counter(),
        "or_bot_suit_dist": Counter(),
        "or_top_rank_dist": Counter(),
        "v44_layout_dist": Counter(),
        "v44_top_type_dist": Counter(),
        "v44_bot_suit_dist": Counter(),
        "v44_top_rank_dist": Counter(),
    })
    rank_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_match": 0,
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
        "v44_class_dist": Counter(),
        "oracle_class_dist": Counter(),
    })
    rank_cell_n = defaultdict(lambda: Counter())
    rank_cell_regret = defaultdict(lambda: defaultdict(float))

    print("\n[3/4] sweeping per-hand v44 vs oracle + structural counts ...",
          flush=True)
    t0 = time.time()
    for k, cid in enumerate(tr_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v44_idx = int(strategy_v44_dt(h))
        regret = float(rowf[oracle_idx]) - float(rowf[v44_idx])

        struct = compute_trips_structural(h)
        cell = cell_for_trips_hand(struct)
        trip_rank = struct["trip_rank"]

        v44_det = classify_pick_trips(h, v44_idx, struct)
        or_det = classify_pick_trips(h, oracle_idx, struct)

        v44_class = v44_det["class_label"]
        or_class = or_det["class_label"]

        arr_cid[k] = cid
        arr_trip_rank[k] = trip_rank
        arr_max_kicker[k] = struct["max_kicker_rank"]
        arr_b_ds_avail[k] = bool(struct["b_ds_avail"])
        arr_n_b_ds_rt[k] = struct["n_b_ds_routings"]
        arr_b_ds_max[k] = struct["best_b_ds_kicker_max_rank"]
        arr_b_ds_2nd[k] = struct["best_b_ds_kicker_2nd_rank"]
        arr_max_suit_cnt[k] = struct["kickers_max_suit_count"]
        arr_n_in_ts[k] = struct["n_kickers_in_trip_suits"]
        arr_cell[k] = CELLS_ORDER.index(cell)
        arr_v44_idx[k] = v44_idx
        arr_oracle_idx[k] = oracle_idx
        arr_regret[k] = regret
        arr_v44_layout[k] = _LAYOUT_CODE[v44_det["layout"]]
        arr_v44_bot_suit[k] = _BOT_SUIT_CODE.get(v44_det["bot_suit"], 4)
        arr_v44_top_type[k] = _TOP_TYPE_CODE[v44_det["top_type"]]
        arr_v44_top_rank[k] = v44_det["top_rank"]
        arr_v44_mid_paired[k] = v44_det["mid_paired"]
        arr_v44_bot_run[k] = v44_det["bot_run"]
        arr_or_layout[k] = _LAYOUT_CODE[or_det["layout"]]
        arr_or_bot_suit[k] = _BOT_SUIT_CODE.get(or_det["bot_suit"], 4)
        arr_or_top_type[k] = _TOP_TYPE_CODE[or_det["top_type"]]
        arr_or_top_rank[k] = or_det["top_rank"]
        arr_or_mid_paired[k] = or_det["mid_paired"]
        arr_or_bot_run[k] = or_det["bot_run"]

        st = cell_stats[(trip_rank, cell)]
        st["n"] += 1
        st["sum_regret"] += regret
        st["v44_class_dist"][v44_class] += 1
        st["oracle_class_dist"][or_class] += 1
        if v44_idx == oracle_idx:
            st["n_match"] += 1
        if v44_class != or_class:
            st["mismatch"][(v44_class, or_class)] += 1
            st["mismatch_regret"][(v44_class, or_class)] += regret
        st["or_layout_dist"][or_det["layout"]] += 1
        st["or_top_type_dist"][or_det["top_type"]] += 1
        st["or_bot_suit_dist"][or_det["bot_suit"]] += 1
        st["or_top_rank_dist"][or_det["top_rank"]] += 1
        st["v44_layout_dist"][v44_det["layout"]] += 1
        st["v44_top_type_dist"][v44_det["top_type"]] += 1
        st["v44_bot_suit_dist"][v44_det["bot_suit"]] += 1
        st["v44_top_rank_dist"][v44_det["top_rank"]] += 1

        rs = rank_stats[trip_rank]
        rs["n"] += 1
        rs["sum_regret"] += regret
        if v44_idx == oracle_idx:
            rs["n_match"] += 1
        if v44_class != or_class:
            rs["mismatch"][(v44_class, or_class)] += 1
            rs["mismatch_regret"][(v44_class, or_class)] += regret
        rs["v44_class_dist"][v44_class] += 1
        rs["oracle_class_dist"][or_class] += 1
        rank_cell_n[trip_rank][cell] += 1
        rank_cell_regret[trip_rank][cell] += regret

        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ===========================================================
    # Per-trip_rank residual stratification
    # ===========================================================
    print("=" * 100)
    print("TR1: PER-TRIP_RANK RESIDUAL STRATIFICATION (v44_dt vs oracle)")
    print("=" * 100)
    print(f"  {'trip':>5} {'n_hands':>9} {'pct_opt':>8} {'mean_reg':>10} "
          f"{'wg_contrib':>12}")
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[trip_rank]
        if rs["n"] == 0:
            continue
        pct_opt = 100 * rs["n_match"] / rs["n"]
        mean_reg = rs["sum_regret"] / rs["n"] * EV_TO_DOL * 1000
        wg = rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {RANK_CHAR[trip_rank]:>5} {rs['n']:>9,} {pct_opt:>7.2f}% "
              f"${mean_reg:>+8.1f} ${wg:>+10.2f}")

    print("\n  Per-trip_rank top-8 mismatch classes:")
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[trip_rank]
        if not rs["mismatch_regret"]:
            continue
        print(f"\n  ── trip = {RANK_CHAR[trip_rank]} ──")
        ranked = sorted(rs["mismatch_regret"].items(), key=lambda x: -x[1])
        for (vc, oc), reg in ranked[:8]:
            nn = rs["mismatch"][(vc, oc)]
            mean_reg = reg / nn * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"    {vc:<22} -> {oc:<22} n={nn:>7,} mean=${mean_reg:>+7.1f} "
                  f"wg=${wg:>+7.2f}")

    print("\n  Per-trip_rank class distribution (v44 pick % vs oracle pick %):")
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[trip_rank]
        if rs["n"] == 0:
            continue
        print(f"\n  ── trip = {RANK_CHAR[trip_rank]}  (n={rs['n']:,}) ──")
        all_classes = sorted(set(rs["v44_class_dist"].keys()) |
                              set(rs["oracle_class_dist"].keys()),
                              key=lambda c: -(rs["v44_class_dist"][c] +
                                              rs["oracle_class_dist"][c]))
        print(f"    {'class':<26} {'v44_pct':>9} {'oracle_pct':>11} {'delta':>9}")
        for c in all_classes[:12]:
            vp = 100 * rs["v44_class_dist"][c] / rs["n"]
            op = 100 * rs["oracle_class_dist"][c] / rs["n"]
            print(f"    {c:<26} {vp:>8.2f}% {op:>10.2f}% {(vp-op):>+8.2f}%")

    # ===========================================================
    # Structural cell cross-tab
    # ===========================================================
    print("\n" + "=" * 100)
    print("TR2: STRUCTURAL CELL CROSS-TABULATION (per trip_rank x cell)")
    print("=" * 100)
    print(f"  {'trip':>5} {'cell':<18} {'n_hands':>9} {'pct_of_rank':>12} "
          f"{'wg_contrib':>12} {'mean_reg':>10}")
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        n_total = rank_stats[trip_rank]["n"]
        for cell in CELLS_ORDER:
            n_in_cell = rank_cell_n[trip_rank].get(cell, 0)
            if n_in_cell == 0:
                continue
            reg = rank_cell_regret[trip_rank].get(cell, 0.0)
            pct_of_rank = 100 * n_in_cell / n_total
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            mean_reg = reg / n_in_cell * EV_TO_DOL * 1000
            print(f"  {RANK_CHAR[trip_rank]:>5} {cell:<18} {n_in_cell:>9,} "
                  f"{pct_of_rank:>11.1f}% ${wg:>+10.2f} ${mean_reg:>+8.1f}")

    print("\n  Cell totals across all trip_ranks:")
    cell_totals_n = Counter()
    cell_totals_reg = defaultdict(float)
    for trip_rank in rank_stats.keys():
        for cell in CELLS_ORDER:
            n_in_cell = rank_cell_n[trip_rank].get(cell, 0)
            cell_totals_n[cell] += n_in_cell
            cell_totals_reg[cell] += rank_cell_regret[trip_rank].get(cell, 0.0)
    total_n_trip = sum(rs["n"] for rs in rank_stats.values())
    print(f"    {'cell':<18} {'n':>9} {'pct':>7} {'wg_contrib':>12}")
    for cell in CELLS_ORDER:
        n_c = cell_totals_n[cell]
        if n_c == 0:
            continue
        pct = 100 * n_c / total_n_trip
        wg = cell_totals_reg[cell] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"    {cell:<18} {n_c:>9,} {pct:>6.1f}% ${wg:>+10.2f}")

    # ===========================================================
    # Oracle's pick profile per (trip_rank x cell)
    # ===========================================================
    print("\n" + "=" * 100)
    print("TR3: ORACLE'S PICK PROFILE PER (trip_rank x cell)")
    print("=" * 100)
    for trip_rank in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((trip_rank, cell), None)
            if st is None or st["n"] == 0:
                continue
            nn = st["n"]
            mean_reg = st["sum_regret"] / nn * EV_TO_DOL * 1000
            pct_match = 100 * st["n_match"] / nn
            print(f"\n  ── trip={RANK_CHAR[trip_rank]}  cell={cell}  "
                  f"n={nn:,}  pct_opt={pct_match:.1f}%  mean_reg=${mean_reg:+.1f} ──")
            layout_summary = ", ".join(
                f"{p}:{100*c/nn:.0f}%"
                for p, c in sorted(st["or_layout_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle LAYOUT:    {layout_summary}")
            top_type_summary = ", ".join(
                f"{t}:{100*c/nn:.0f}%"
                for t, c in sorted(st["or_top_type_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle TOP_TYPE:  {top_type_summary}")
            top_rank_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/nn:.0f}%"
                for r, c in sorted(st["or_top_rank_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    oracle TOP_rank:  {top_rank_summary}")
            bot_suit_summary = ", ".join(
                f"{s}:{100*c/nn:.0f}%"
                for s, c in sorted(st["or_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle BOT_suit:  {bot_suit_summary}")
            v44_layout_summary = ", ".join(
                f"{p}:{100*c/nn:.0f}%"
                for p, c in sorted(st["v44_layout_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v44    LAYOUT:    {v44_layout_summary}")
            v44_top_type_summary = ", ".join(
                f"{t}:{100*c/nn:.0f}%"
                for t, c in sorted(st["v44_top_type_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v44    TOP_TYPE:  {v44_top_type_summary}")
            v44_bot_suit_summary = ", ".join(
                f"{s}:{100*c/nn:.0f}%"
                for s, c in sorted(st["v44_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v44    BOT_suit:  {v44_bot_suit_summary}")
            if st["mismatch_regret"]:
                ranked = sorted(st["mismatch_regret"].items(), key=lambda x: -x[1])
                print("    top mismatch within cell:")
                for (vc, oc), reg in ranked[:3]:
                    nnm = st["mismatch"][(vc, oc)]
                    mr = reg / nnm * EV_TO_DOL * 1000
                    wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
                    print(f"      {vc:<26} -> {oc:<26} n={nnm:>6,} "
                          f"mean=${mr:>+7.1f} wg=${wg:>+6.2f}")

    # ===========================================================
    # Persist per-hand parquet + summary JSON
    # ===========================================================
    if not args.no_parquet:
        print(f"\n[4/4] writing per-hand parquet to {OUT_PARQUET} ...", flush=True)
        table = pa.table({
            "canonical_id": pa.array(arr_cid, type=pa.uint32()),
            "trip_rank": pa.array(arr_trip_rank, type=pa.int8()),
            "max_kicker_rank": pa.array(arr_max_kicker, type=pa.int8()),
            "b_ds_avail": pa.array(arr_b_ds_avail, type=pa.bool_()),
            "n_b_ds_routings": pa.array(arr_n_b_ds_rt, type=pa.int8()),
            "best_b_ds_kicker_max": pa.array(arr_b_ds_max, type=pa.int8()),
            "best_b_ds_kicker_2nd": pa.array(arr_b_ds_2nd, type=pa.int8()),
            "kickers_max_suit_count": pa.array(arr_max_suit_cnt, type=pa.int8()),
            "n_kickers_in_trip_suits": pa.array(arr_n_in_ts, type=pa.int8()),
            "cell_idx": pa.array(arr_cell, type=pa.int8()),
            "v44_idx": pa.array(arr_v44_idx, type=pa.int16()),
            "oracle_idx": pa.array(arr_oracle_idx, type=pa.int16()),
            "regret": pa.array(arr_regret, type=pa.float32()),
            "v44_layout": pa.array(arr_v44_layout, type=pa.int8()),
            "v44_bot_suit": pa.array(arr_v44_bot_suit, type=pa.int8()),
            "v44_top_type": pa.array(arr_v44_top_type, type=pa.int8()),
            "v44_top_rank": pa.array(arr_v44_top_rank, type=pa.int8()),
            "v44_mid_paired": pa.array(arr_v44_mid_paired, type=pa.bool_()),
            "v44_bot_run": pa.array(arr_v44_bot_run, type=pa.int8()),
            "or_layout": pa.array(arr_or_layout, type=pa.int8()),
            "or_bot_suit": pa.array(arr_or_bot_suit, type=pa.int8()),
            "or_top_type": pa.array(arr_or_top_type, type=pa.int8()),
            "or_top_rank": pa.array(arr_or_top_rank, type=pa.int8()),
            "or_mid_paired": pa.array(arr_or_mid_paired, type=pa.bool_()),
            "or_bot_run": pa.array(arr_or_bot_run, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3, write_statistics=True)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        summary = {
            "n_trips_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "broadway_thresh": BROADWAY_THRESH,
            "rank_stats": {},
            "cell_stats": {},
            "rank_cell_n": {},
            "rank_cell_regret_wg": {},
            "cell_totals": {},
        }
        for trip_rank, rs in rank_stats.items():
            summary["rank_stats"][str(trip_rank)] = {
                "n": int(rs["n"]),
                "sum_regret": float(rs["sum_regret"]),
                "n_match": int(rs["n_match"]),
                "mean_regret_dollars_per_1000h": float(
                    rs["sum_regret"] / rs["n"] * EV_TO_DOL * 1000) if rs["n"] else 0.0,
                "wg_contrib_dollars_per_1000h": float(
                    rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "pct_opt": float(100 * rs["n_match"] / rs["n"]) if rs["n"] else 0.0,
                "v44_class_dist": dict(rs["v44_class_dist"].most_common(20)),
                "oracle_class_dist": dict(rs["oracle_class_dist"].most_common(20)),
                "top_mismatch_classes": [
                    {
                        "v44_class": vc,
                        "oracle_class": oc,
                        "n": int(rs["mismatch"][(vc, oc)]),
                        "wg_dollars": float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                        "mean_regret_dollars": float(reg / rs["mismatch"][(vc, oc)] * EV_TO_DOL * 1000),
                    }
                    for (vc, oc), reg in sorted(rs["mismatch_regret"].items(),
                                                key=lambda x: -x[1])[:15]
                ],
            }
        for (trip_rank, cell), st in cell_stats.items():
            key = f"{trip_rank}|{cell}"
            summary["cell_stats"][key] = {
                "n": int(st["n"]),
                "sum_regret": float(st["sum_regret"]),
                "n_match": int(st["n_match"]),
                "wg_contrib_dollars": float(st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "mean_regret_dollars": float(st["sum_regret"] / st["n"] * EV_TO_DOL * 1000),
                "pct_opt": float(100 * st["n_match"] / st["n"]),
                "or_layout_dist": dict(st["or_layout_dist"]),
                "or_top_type_dist": dict(st["or_top_type_dist"]),
                "or_top_rank_dist": dict(st["or_top_rank_dist"]),
                "or_bot_suit_dist": dict(st["or_bot_suit_dist"]),
                "v44_layout_dist": dict(st["v44_layout_dist"]),
                "v44_top_type_dist": dict(st["v44_top_type_dist"]),
                "v44_top_rank_dist": dict(st["v44_top_rank_dist"]),
                "v44_bot_suit_dist": dict(st["v44_bot_suit_dist"]),
                "top_mismatches": [
                    {
                        "v44_class": vc,
                        "oracle_class": oc,
                        "n": int(st["mismatch"][(vc, oc)]),
                        "wg_dollars": float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                        "mean_regret_dollars": float(reg / st["mismatch"][(vc, oc)] * EV_TO_DOL * 1000),
                    }
                    for (vc, oc), reg in sorted(st["mismatch_regret"].items(),
                                                key=lambda x: -x[1])[:10]
                ],
            }
        for trip_rank, cell_n in rank_cell_n.items():
            summary["rank_cell_n"][str(trip_rank)] = dict(cell_n)
            summary["rank_cell_regret_wg"][str(trip_rank)] = {
                cell: float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                for cell, reg in rank_cell_regret[trip_rank].items()
            }
        for cell in CELLS_ORDER:
            summary["cell_totals"][cell] = {
                "n": int(cell_totals_n[cell]),
                "wg": float(cell_totals_reg[cell] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
