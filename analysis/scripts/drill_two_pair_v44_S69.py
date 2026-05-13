"""
Session 69 Phase 1 — Two_pair category deep-dive: structural cell
classification + oracle/v44 pick distribution per (max_pair_rank, cell).
Analog of `drill_pair_v44_S66.py`, scoped to category=two_pair (cat=2,
n=1,338,480 canonical hands = 22.3% of canonical-grid).

Output:
  data/drill_two_pair_v44_per_hand_structural.parquet
  data/drill_two_pair_v44_summary.json
  Console: per-max_pair_rank residual tables, structural cell cross-tab,
           and oracle pick profile per (max_pair_rank, cell).

Two_pair structural axes (informed by v44's t2p_v2_* feature family,
Sessions 33 + 55):

  Two_pair = 2 pair ranks (high pair `H`, low pair `L`) + 3 singletons.

  Layouts (where the pairs go):
    Layout A — both pairs in bot (= 4-card bot is HHLL = "two pair").
               Bot suit profile is determined by pair suits:
                 - DS iff hi_pair_suits == lo_pair_suits (suits match).
                 - RB otherwise (always 4 distinct suits, no SS possible).
               Always achievable; mid+top use the 3 singletons.
    Layout B — low pair in bot + 2 of 3 singletons. High pair in mid.
               Bot suits = lo_pair_suits ∪ 2 sing_suits.
               DS achievable iff ∃ singleton-pair forming bot 2+2.
    Layout C — high pair in bot + 2 of 3 singletons. Low pair in mid.
               Bot suits = hi_pair_suits ∪ 2 sing_suits.
               DS achievable iff ∃ singleton-pair forming bot 2+2.
    Layout SPLIT — pair cards split (one pair card in top etc.).
                   Almost never oracle-optimal; included for accounting.

  Cell taxonomy (priority order, first match wins; mirrors S66 6-cell
  scheme with two_pair-specific structural axes):

    LAYOUT_A_DS         — Layout A is DS-bot (HH+LL pair-suits FULLY
                          match). Bot is "two pair DS" — strongest A play.
    LAYOUT_C_DS         — Not (1), but Layout C DS achievable (≥1 of 3
                          C-routings yields 2+2 bot).
    LAYOUT_B_DS         — Not (1) or (2), but Layout B DS achievable.
    LAYOUT_A_SS         — Not above, but Layout A is SS-bot (HH and LL
                          share exactly 1 suit; bot has 2+1+1).
    LAYOUT_C_SS_ONLY    — No DS layout, no Layout A SS; Layout C SS
                          achievable.
    LAYOUT_B_SS_ONLY    — No DS, no A_SS, no C_SS; Layout B SS achievable.
    LAYOUT_OTHER        — None of the above (Layout A is RB; B/C only have
                          31 or RB routings).

Pick classification (oracle / v44):
  layout:        A / B / C / SPLIT
  bot_suit:      DS / SS / 31 / RB / 4f
  top_type:      SING_MAX / SING_MID / SING_LOW / PAIR (rare on top)
  mid_suited:    bool
  Compact label: e.g. "C_DS_tmax", "B_SS_tmid", "A_RB_tmax", "SPLIT_*"

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_v44_S69.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_v44_S69.py --sample 5000
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
OUT_PARQUET = ROOT / "data" / "drill_two_pair_v44_per_hand_structural.parquet"
OUT_JSON = ROOT / "data" / "drill_two_pair_v44_summary.json"

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
    "LAYOUT_A_DS",
    "LAYOUT_C_DS",
    "LAYOUT_B_DS",
    "LAYOUT_A_SS",
    "LAYOUT_C_SS_ONLY",
    "LAYOUT_B_SS_ONLY",
    "LAYOUT_OTHER",
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
    return "RB"  # [1, 1, 1, 1]


def compute_two_pair_structural(hand_bytes):
    """Compute two_pair structural achievability counts and indices.

    Returns dict with:
      hi_pair_rank, lo_pair_rank,
      hi_pair_pos (tuple 2), lo_pair_pos (tuple 2),
      hi_pair_suits, lo_pair_suits,
      sing_pos (tuple 3), sing_ranks (tuple 3), sing_suits (tuple 3),
      max_sing_rank, max_sing_pos,
      layout_A_DS_achievable      — bool (HH and LL share suits)
      n_layout_C_DS               — count of (sa,sb) C-bot routings yielding 2+2
      n_layout_B_DS               — count of B-bot routings yielding 2+2
      n_layout_C_SS               — count of C-bot routings yielding 2+1+1
      n_layout_B_SS               — count of B-bot routings yielding 2+1+1
      best_layout_C_DS_top_rank   — max top-card rank among C-DS routings
      best_layout_B_DS_top_rank   — max top-card rank among B-DS routings
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    rc = Counter(int_ranks)
    pair_ranks_sorted = sorted(
        [r for r, c in rc.items() if c == 2], reverse=True
    )
    assert len(pair_ranks_sorted) == 2, "Not a two_pair hand!"
    hi_pair_rank, lo_pair_rank = pair_ranks_sorted

    hi_pair_pos = tuple(i for i in range(7) if int_ranks[i] == hi_pair_rank)
    lo_pair_pos = tuple(i for i in range(7) if int_ranks[i] == lo_pair_rank)
    hi_pair_suits = tuple(sorted(int_suits[p] for p in hi_pair_pos))
    lo_pair_suits = tuple(sorted(int_suits[p] for p in lo_pair_pos))

    sing_pos = tuple(
        i for i in range(7) if i not in hi_pair_pos and i not in lo_pair_pos
    )
    assert len(sing_pos) == 3
    sing_ranks = tuple(int_ranks[i] for i in sing_pos)
    sing_suits = tuple(int_suits[i] for i in sing_pos)

    max_sing_rank = max(sing_ranks)
    max_sing_local = sing_ranks.index(max_sing_rank)
    max_sing_pos = sing_pos[max_sing_local]

    # Layout A: both pairs in bot. Bot suits are determined by pair-suit
    # overlap:
    #   |hi ∩ lo| == 2 → DS (full match: e.g. AcAd + KcKd)
    #   |hi ∩ lo| == 1 → SS (partial: e.g. AcAd + KcKh, suit c shared)
    #   |hi ∩ lo| == 0 → RB (disjoint: e.g. AcAd + KhKs)
    # No 31 possible — each pair contributes 2 distinct suits.
    hi_set = set(hi_pair_suits)
    lo_set = set(lo_pair_suits)
    n_shared = len(hi_set & lo_set)
    layout_A_DS_achievable = (n_shared == 2)
    layout_A_SS_achievable = (n_shared == 1)

    # Layouts B and C: enumerate C(3,2) = 3 routings (which 2 sings to bot,
    # leftover singleton is top).
    n_layout_C_DS = 0
    n_layout_B_DS = 0
    n_layout_C_SS = 0
    n_layout_B_SS = 0
    best_layout_C_DS_top_rank = 0
    best_layout_B_DS_top_rank = 0
    for sa_i, sb_i in combinations(range(3), 2):
        leftover_i = [j for j in range(3) if j != sa_i and j != sb_i][0]
        top_rank = sing_ranks[leftover_i]

        # Layout C: bot = HH + sing_a + sing_b
        bot_C_suits = list(hi_pair_suits) + [sing_suits[sa_i], sing_suits[sb_i]]
        bot_C_kind = _bot_suit_kind(bot_C_suits)
        if bot_C_kind == "DS":
            n_layout_C_DS += 1
            if top_rank > best_layout_C_DS_top_rank:
                best_layout_C_DS_top_rank = top_rank
        elif bot_C_kind == "SS":
            n_layout_C_SS += 1

        # Layout B: bot = LL + sing_a + sing_b
        bot_B_suits = list(lo_pair_suits) + [sing_suits[sa_i], sing_suits[sb_i]]
        bot_B_kind = _bot_suit_kind(bot_B_suits)
        if bot_B_kind == "DS":
            n_layout_B_DS += 1
            if top_rank > best_layout_B_DS_top_rank:
                best_layout_B_DS_top_rank = top_rank
        elif bot_B_kind == "SS":
            n_layout_B_SS += 1

    return {
        "hi_pair_rank": hi_pair_rank,
        "lo_pair_rank": lo_pair_rank,
        "hi_pair_pos": hi_pair_pos,
        "lo_pair_pos": lo_pair_pos,
        "hi_pair_suits": hi_pair_suits,
        "lo_pair_suits": lo_pair_suits,
        "sing_pos": sing_pos,
        "sing_ranks": sing_ranks,
        "sing_suits": sing_suits,
        "max_sing_rank": max_sing_rank,
        "max_sing_pos": max_sing_pos,
        "layout_A_DS_achievable": layout_A_DS_achievable,
        "layout_A_SS_achievable": layout_A_SS_achievable,
        "n_layout_C_DS": n_layout_C_DS,
        "n_layout_B_DS": n_layout_B_DS,
        "n_layout_C_SS": n_layout_C_SS,
        "n_layout_B_SS": n_layout_B_SS,
        "best_layout_C_DS_top_rank": best_layout_C_DS_top_rank,
        "best_layout_B_DS_top_rank": best_layout_B_DS_top_rank,
    }


def cell_for_two_pair_hand(struct):
    """Map two_pair structural counts to a 7-cell taxonomy.

    Priority (first match wins):
      LAYOUT_A_DS       : layout_A_DS_achievable (HH+LL fully suit-matched)
      LAYOUT_C_DS       : n_layout_C_DS > 0
      LAYOUT_B_DS       : n_layout_B_DS > 0
      LAYOUT_A_SS       : layout_A_SS_achievable (HH+LL share 1 suit)
      LAYOUT_C_SS_ONLY  : n_layout_C_SS > 0
      LAYOUT_B_SS_ONLY  : n_layout_B_SS > 0
      LAYOUT_OTHER      : otherwise (Layout A is RB; B/C only 31/RB)
    """
    if struct["layout_A_DS_achievable"]:
        return "LAYOUT_A_DS"
    if struct["n_layout_C_DS"] > 0:
        return "LAYOUT_C_DS"
    if struct["n_layout_B_DS"] > 0:
        return "LAYOUT_B_DS"
    if struct["layout_A_SS_achievable"]:
        return "LAYOUT_A_SS"
    if struct["n_layout_C_SS"] > 0:
        return "LAYOUT_C_SS_ONLY"
    if struct["n_layout_B_SS"] > 0:
        return "LAYOUT_B_SS_ONLY"
    return "LAYOUT_OTHER"


def longest_run(ranks):
    s = sorted(set(int(r) for r in ranks))
    if not s:
        return 0
    longest = 1
    cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1
    return longest


def classify_pick_two_pair(hand_bytes, feats, idx, struct):
    """Classify a chosen setting for a two_pair hand into structural labels.

    Returns dict with:
      layout:       'A' | 'B' | 'C' | 'SPLIT'
      bot_suit:     'DS' | 'SS' | '31' | 'RB' | '4f'
      top_type:     'SING_MAX' | 'SING_MID' | 'SING_LOW' | 'PAIR'
      top_rank, mid_high, mid_low, mid_sum, mid_suited
      bot_max, bot_min, bot_sum, bot_run
      class_label:  compact composite label (e.g. "C_DS_tmax")
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3

    hi_pair_set = set(struct["hi_pair_pos"])
    lo_pair_set = set(struct["lo_pair_pos"])
    sing_pos_set = set(struct["sing_pos"])
    sing_ranks = struct["sing_ranks"]
    max_sing_pos = struct["max_sing_pos"]

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

    bot_suits_arr = [int(suits[p]) for p in bot_pos]
    bot_suit_kind = _bot_suit_kind(bot_suits_arr)

    top_rank = int(ranks[top_pos])
    if top_pos in hi_pair_set or top_pos in lo_pair_set:
        top_type = "PAIR"
    else:
        # Compare singleton ranks (sorted high→low) to assign tier label.
        sing_sorted = sorted(sing_ranks, reverse=True)
        if top_rank == sing_sorted[0]:
            top_type = "SING_MAX"
        elif top_rank == sing_sorted[2]:
            top_type = "SING_LOW"
        else:
            top_type = "SING_MID"

    mid_ranks_sorted = sorted(
        [int(ranks[mid_pos[0]]), int(ranks[mid_pos[1]])], reverse=True
    )
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]

    bot_ranks_sorted = sorted([int(ranks[p]) for p in bot_pos], reverse=True)
    bot_run = longest_run([int(ranks[p]) for p in bot_pos])

    top_lbl_short = {
        "SING_MAX": "tmax", "SING_MID": "tmid",
        "SING_LOW": "tlow", "PAIR": "tpair",
    }[top_type]
    ms_lbl = "ms" if mid_suited else "mu"
    if layout in ("A", "B", "C"):
        # Layout A mid is always 2 of the 3 singletons (could be ms or mu).
        # Layouts B/C have a pair in mid (mid_suited usually False since pair
        # cards have distinct suits).
        class_label = f"{layout}_{bot_suit_kind}_{top_lbl_short}_{ms_lbl}"
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
        "mid_suited": mid_suited,
        "bot_max": bot_ranks_sorted[0],
        "bot_min": bot_ranks_sorted[3],
        "bot_sum": sum(bot_ranks_sorted),
        "bot_run": bot_run,
        "class_label": class_label,
    }


_LAYOUT_CODE = {"A": 0, "B": 1, "C": 2, "SPLIT": 3}
_BOT_SUIT_CODE = {"DS": 0, "SS": 1, "31": 2, "RB": 3, "4f": 4}
_TOP_TYPE_CODE = {"SING_MAX": 0, "SING_MID": 1, "SING_LOW": 2, "PAIR": 3}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample hands to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 69 Phase 1 — Two_pair deep-dive (oracle + v44_dt vs structural cell)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tp_idx = np.where(cats == 2)[0]
    n_tp = len(tp_idx)
    print(f"  two_pair hands: {n_tp:,}")

    if args.sample > 0 and n_tp > args.sample:
        rng = np.random.default_rng(args.seed)
        tp_idx = np.sort(rng.choice(tp_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(tp_idx)
    arr_cid = np.zeros(n, dtype=np.uint32)
    arr_hi_pair = np.zeros(n, dtype=np.int8)
    arr_lo_pair = np.zeros(n, dtype=np.int8)
    arr_max_sing = np.zeros(n, dtype=np.int8)
    arr_layout_A_DS = np.zeros(n, dtype=np.bool_)
    arr_layout_A_SS = np.zeros(n, dtype=np.bool_)
    arr_n_C_DS = np.zeros(n, dtype=np.int8)
    arr_n_B_DS = np.zeros(n, dtype=np.int8)
    arr_n_C_SS = np.zeros(n, dtype=np.int8)
    arr_n_B_SS = np.zeros(n, dtype=np.int8)
    arr_best_C_DS_top = np.zeros(n, dtype=np.int8)
    arr_best_B_DS_top = np.zeros(n, dtype=np.int8)
    arr_cell = np.zeros(n, dtype=np.int8)
    arr_v44_idx = np.zeros(n, dtype=np.int16)
    arr_oracle_idx = np.zeros(n, dtype=np.int16)
    arr_regret = np.zeros(n, dtype=np.float32)
    arr_v44_layout = np.zeros(n, dtype=np.int8)
    arr_v44_bot_suit = np.zeros(n, dtype=np.int8)
    arr_v44_top_type = np.zeros(n, dtype=np.int8)
    arr_v44_top_rank = np.zeros(n, dtype=np.int8)
    arr_v44_mid_suited = np.zeros(n, dtype=np.bool_)
    arr_v44_mid_high = np.zeros(n, dtype=np.int8)
    arr_v44_bot_run = np.zeros(n, dtype=np.int8)
    arr_or_layout = np.zeros(n, dtype=np.int8)
    arr_or_bot_suit = np.zeros(n, dtype=np.int8)
    arr_or_top_type = np.zeros(n, dtype=np.int8)
    arr_or_top_rank = np.zeros(n, dtype=np.int8)
    arr_or_mid_suited = np.zeros(n, dtype=np.bool_)
    arr_or_mid_high = np.zeros(n, dtype=np.int8)
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
        "or_top_rank_dist": Counter(),
        "or_bot_suit_dist": Counter(),
        "or_mid_suited_n": 0,
        "or_mid_high_dist": Counter(),
        "or_bot_run_dist": Counter(),
        "v44_layout_dist": Counter(),
        "v44_top_type_dist": Counter(),
        "v44_top_rank_dist": Counter(),
        "v44_bot_suit_dist": Counter(),
        "v44_mid_suited_n": 0,
        "v44_mid_high_dist": Counter(),
        "v44_bot_run_dist": Counter(),
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
    for k, cid in enumerate(tp_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v44_idx = int(strategy_v44_dt(h))
        regret = float(rowf[oracle_idx]) - float(rowf[v44_idx])

        struct = compute_two_pair_structural(h)
        cell = cell_for_two_pair_hand(struct)
        hi_pair = struct["hi_pair_rank"]
        lo_pair = struct["lo_pair_rank"]
        max_sing_rank = struct["max_sing_rank"]

        v44_det = classify_pick_two_pair(h, feats, v44_idx, struct)
        or_det = classify_pick_two_pair(h, feats, oracle_idx, struct)

        v44_class = v44_det["class_label"]
        or_class = or_det["class_label"]

        arr_cid[k] = cid
        arr_hi_pair[k] = hi_pair
        arr_lo_pair[k] = lo_pair
        arr_max_sing[k] = max_sing_rank
        arr_layout_A_DS[k] = struct["layout_A_DS_achievable"]
        arr_layout_A_SS[k] = struct["layout_A_SS_achievable"]
        arr_n_C_DS[k] = struct["n_layout_C_DS"]
        arr_n_B_DS[k] = struct["n_layout_B_DS"]
        arr_n_C_SS[k] = struct["n_layout_C_SS"]
        arr_n_B_SS[k] = struct["n_layout_B_SS"]
        arr_best_C_DS_top[k] = struct["best_layout_C_DS_top_rank"]
        arr_best_B_DS_top[k] = struct["best_layout_B_DS_top_rank"]
        arr_cell[k] = CELLS_ORDER.index(cell)
        arr_v44_idx[k] = v44_idx
        arr_oracle_idx[k] = oracle_idx
        arr_regret[k] = regret
        arr_v44_layout[k] = _LAYOUT_CODE[v44_det["layout"]]
        arr_v44_bot_suit[k] = _BOT_SUIT_CODE.get(v44_det["bot_suit"], 4)
        arr_v44_top_type[k] = _TOP_TYPE_CODE[v44_det["top_type"]]
        arr_v44_top_rank[k] = v44_det["top_rank"]
        arr_v44_mid_suited[k] = v44_det["mid_suited"]
        arr_v44_mid_high[k] = v44_det["mid_high"]
        arr_v44_bot_run[k] = v44_det["bot_run"]
        arr_or_layout[k] = _LAYOUT_CODE[or_det["layout"]]
        arr_or_bot_suit[k] = _BOT_SUIT_CODE.get(or_det["bot_suit"], 4)
        arr_or_top_type[k] = _TOP_TYPE_CODE[or_det["top_type"]]
        arr_or_top_rank[k] = or_det["top_rank"]
        arr_or_mid_suited[k] = or_det["mid_suited"]
        arr_or_mid_high[k] = or_det["mid_high"]
        arr_or_bot_run[k] = or_det["bot_run"]

        st = cell_stats[(hi_pair, cell)]
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
        st["or_top_rank_dist"][or_det["top_rank"]] += 1
        st["or_bot_suit_dist"][or_det["bot_suit"]] += 1
        st["or_mid_suited_n"] += int(or_det["mid_suited"])
        st["or_mid_high_dist"][or_det["mid_high"]] += 1
        st["or_bot_run_dist"][or_det["bot_run"]] += 1
        st["v44_layout_dist"][v44_det["layout"]] += 1
        st["v44_top_type_dist"][v44_det["top_type"]] += 1
        st["v44_top_rank_dist"][v44_det["top_rank"]] += 1
        st["v44_bot_suit_dist"][v44_det["bot_suit"]] += 1
        st["v44_mid_suited_n"] += int(v44_det["mid_suited"])
        st["v44_mid_high_dist"][v44_det["mid_high"]] += 1
        st["v44_bot_run_dist"][v44_det["bot_run"]] += 1

        rs = rank_stats[hi_pair]
        rs["n"] += 1
        rs["sum_regret"] += regret
        if v44_idx == oracle_idx:
            rs["n_match"] += 1
        if v44_class != or_class:
            rs["mismatch"][(v44_class, or_class)] += 1
            rs["mismatch_regret"][(v44_class, or_class)] += regret
        rs["v44_class_dist"][v44_class] += 1
        rs["oracle_class_dist"][or_class] += 1
        rank_cell_n[hi_pair][cell] += 1
        rank_cell_regret[hi_pair][cell] += regret

        if (k + 1) % 100_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ===========================================================
    # Per-hi_pair-rank residual stratification
    # ===========================================================
    print("=" * 100)
    print("T2P1: PER-HI_PAIR-RANK RESIDUAL STRATIFICATION (v44_dt vs oracle)")
    print("=" * 100)
    print(f"  {'hi_pair':>7} {'n_hands':>9} {'pct_opt':>8} {'mean_reg':>10} "
          f"{'wg_contrib':>12}")
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[hi_pair]
        if rs["n"] == 0:
            continue
        pct_opt = 100 * rs["n_match"] / rs["n"]
        mean_reg = rs["sum_regret"] / rs["n"] * EV_TO_DOL * 1000
        wg = rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {RANK_CHAR[hi_pair]:>7} {rs['n']:>9,} {pct_opt:>7.2f}% "
              f"${mean_reg:>+8.1f} ${wg:>+10.2f}")

    print("\n  Per-hi_pair-rank top-10 mismatch classes:")
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[hi_pair]
        if not rs["mismatch_regret"]:
            continue
        print(f"\n  ── hi_pair = {RANK_CHAR[hi_pair]} ──")
        ranked = sorted(rs["mismatch_regret"].items(), key=lambda x: -x[1])
        for (vc, oc), reg in ranked[:10]:
            nn = rs["mismatch"][(vc, oc)]
            mean_reg = reg / nn * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"    {vc:<22} -> {oc:<22} n={nn:>7,} mean=${mean_reg:>+7.1f} "
                  f"wg=${wg:>+7.2f}")

    print("\n  Per-hi_pair-rank class distribution (v44 pick % vs oracle pick %):")
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[hi_pair]
        if rs["n"] == 0:
            continue
        print(f"\n  ── hi_pair = {RANK_CHAR[hi_pair]}  (n={rs['n']:,}) ──")
        all_classes = sorted(set(rs["v44_class_dist"].keys()) |
                              set(rs["oracle_class_dist"].keys()),
                              key=lambda c: -(rs["v44_class_dist"][c] +
                                              rs["oracle_class_dist"][c]))
        print(f"    {'class':<26} {'v44_pct':>9} {'oracle_pct':>11} {'delta':>9}")
        for c in all_classes[:15]:
            vp = 100 * rs["v44_class_dist"][c] / rs["n"]
            op = 100 * rs["oracle_class_dist"][c] / rs["n"]
            print(f"    {c:<26} {vp:>8.2f}% {op:>10.2f}% {(vp-op):>+8.2f}%")

    # ===========================================================
    # Structural cell cross-tab
    # ===========================================================
    print("\n" + "=" * 100)
    print("T2P2: STRUCTURAL CELL CROSS-TABULATION (per hi_pair x cell)")
    print("=" * 100)
    print(f"  {'hi_pair':>7} {'cell':<20} {'n_hands':>9} {'pct_of_rank':>12} "
          f"{'wg_contrib':>12} {'mean_reg':>10}")
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        n_total = rank_stats[hi_pair]["n"]
        for cell in CELLS_ORDER:
            n_in_cell = rank_cell_n[hi_pair].get(cell, 0)
            if n_in_cell == 0:
                continue
            reg = rank_cell_regret[hi_pair].get(cell, 0.0)
            pct_of_rank = 100 * n_in_cell / n_total
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            mean_reg = reg / n_in_cell * EV_TO_DOL * 1000
            print(f"  {RANK_CHAR[hi_pair]:>7} {cell:<20} {n_in_cell:>9,} "
                  f"{pct_of_rank:>11.1f}% ${wg:>+10.2f} ${mean_reg:>+8.1f}")

    # ===========================================================
    # Oracle's pick profile per (hi_pair x cell)
    # ===========================================================
    print("\n" + "=" * 100)
    print("T2P3: ORACLE'S PICK PROFILE PER (hi_pair x cell)")
    print("=" * 100)
    for hi_pair in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((hi_pair, cell), None)
            if st is None or st["n"] == 0:
                continue
            nn = st["n"]
            mean_reg = st["sum_regret"] / nn * EV_TO_DOL * 1000
            pct_match = 100 * st["n_match"] / nn
            print(f"\n  ── hi_pair={RANK_CHAR[hi_pair]}  cell={cell}  "
                  f"n={nn:,}  pct_opt={pct_match:.1f}%  mean_reg=${mean_reg:+.1f} ──")
            layout_summary = ", ".join(
                f"{p}:{100*c/nn:.0f}%"
                for p, c in sorted(st["or_layout_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle LAYOUT:     {layout_summary}")
            top_type_summary = ", ".join(
                f"{t}:{100*c/nn:.0f}%"
                for t, c in sorted(st["or_top_type_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle TOP_TYPE:   {top_type_summary}")
            top_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/nn:.0f}%"
                for r, c in sorted(st["or_top_rank_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    oracle TOP_rank:   {top_summary}")
            bot_suit_summary = ", ".join(
                f"{s}:{100*c/nn:.0f}%"
                for s, c in sorted(st["or_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle BOT_suit:   {bot_suit_summary}")
            ms_pct = 100 * st["or_mid_suited_n"] / nn
            mid_high_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/nn:.0f}%"
                for r, c in sorted(st["or_mid_high_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    oracle MID_suited: {ms_pct:.1f}%")
            print(f"    oracle MID_high:   {mid_high_summary}")
            v44_layout_summary = ", ".join(
                f"{p}:{100*c/nn:.0f}%"
                for p, c in sorted(st["v44_layout_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v44    LAYOUT:     {v44_layout_summary}")
            v44_top_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/nn:.0f}%"
                for r, c in sorted(st["v44_top_rank_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    v44    TOP_rank:   {v44_top_summary}")
            v44_bot_suit_summary = ", ".join(
                f"{s}:{100*c/nn:.0f}%"
                for s, c in sorted(st["v44_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v44    BOT_suit:   {v44_bot_suit_summary}")
            v44_ms_pct = 100 * st["v44_mid_suited_n"] / nn
            v44_mid_high_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/nn:.0f}%"
                for r, c in sorted(st["v44_mid_high_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    v44    MID_suited: {v44_ms_pct:.1f}%")
            print(f"    v44    MID_high:   {v44_mid_high_summary}")
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
            "hi_pair_rank": pa.array(arr_hi_pair, type=pa.int8()),
            "lo_pair_rank": pa.array(arr_lo_pair, type=pa.int8()),
            "max_sing_rank": pa.array(arr_max_sing, type=pa.int8()),
            "layout_A_DS": pa.array(arr_layout_A_DS, type=pa.bool_()),
            "layout_A_SS": pa.array(arr_layout_A_SS, type=pa.bool_()),
            "n_layout_C_DS": pa.array(arr_n_C_DS, type=pa.int8()),
            "n_layout_B_DS": pa.array(arr_n_B_DS, type=pa.int8()),
            "n_layout_C_SS": pa.array(arr_n_C_SS, type=pa.int8()),
            "n_layout_B_SS": pa.array(arr_n_B_SS, type=pa.int8()),
            "best_C_DS_top": pa.array(arr_best_C_DS_top, type=pa.int8()),
            "best_B_DS_top": pa.array(arr_best_B_DS_top, type=pa.int8()),
            "cell_idx": pa.array(arr_cell, type=pa.int8()),
            "v44_idx": pa.array(arr_v44_idx, type=pa.int16()),
            "oracle_idx": pa.array(arr_oracle_idx, type=pa.int16()),
            "regret": pa.array(arr_regret, type=pa.float32()),
            "v44_layout": pa.array(arr_v44_layout, type=pa.int8()),
            "v44_bot_suit": pa.array(arr_v44_bot_suit, type=pa.int8()),
            "v44_top_type": pa.array(arr_v44_top_type, type=pa.int8()),
            "v44_top_rank": pa.array(arr_v44_top_rank, type=pa.int8()),
            "v44_mid_suited": pa.array(arr_v44_mid_suited, type=pa.bool_()),
            "v44_mid_high": pa.array(arr_v44_mid_high, type=pa.int8()),
            "v44_bot_run": pa.array(arr_v44_bot_run, type=pa.int8()),
            "or_layout": pa.array(arr_or_layout, type=pa.int8()),
            "or_bot_suit": pa.array(arr_or_bot_suit, type=pa.int8()),
            "or_top_type": pa.array(arr_or_top_type, type=pa.int8()),
            "or_top_rank": pa.array(arr_or_top_rank, type=pa.int8()),
            "or_mid_suited": pa.array(arr_or_mid_suited, type=pa.bool_()),
            "or_mid_high": pa.array(arr_or_mid_high, type=pa.int8()),
            "or_bot_run": pa.array(arr_or_bot_run, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3, write_statistics=True)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        summary = {
            "n_two_pair_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "rank_stats": {},
            "cell_stats": {},
            "rank_cell_n": {},
            "rank_cell_regret_wg": {},
        }
        for hi_pair, rs in rank_stats.items():
            summary["rank_stats"][str(hi_pair)] = {
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
        for (hi_pair, cell), st in cell_stats.items():
            key = f"{hi_pair}|{cell}"
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
                "or_mid_suited_pct": float(100 * st["or_mid_suited_n"] / st["n"]),
                "or_mid_high_dist": dict(st["or_mid_high_dist"]),
                "v44_layout_dist": dict(st["v44_layout_dist"]),
                "v44_top_type_dist": dict(st["v44_top_type_dist"]),
                "v44_top_rank_dist": dict(st["v44_top_rank_dist"]),
                "v44_bot_suit_dist": dict(st["v44_bot_suit_dist"]),
                "v44_mid_suited_pct": float(100 * st["v44_mid_suited_n"] / st["n"]),
                "v44_mid_high_dist": dict(st["v44_mid_high_dist"]),
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
        for hi_pair, cell_n in rank_cell_n.items():
            summary["rank_cell_n"][str(hi_pair)] = dict(cell_n)
            summary["rank_cell_regret_wg"][str(hi_pair)] = {
                cell: float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                for cell, reg in rank_cell_regret[hi_pair].items()
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
