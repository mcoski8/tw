"""
Session 58 — Drill HO5+HO6+HO7 (consolidated): exhaustive high_only deep-dive
on v43_dt's residuals.

PURPOSE
-------
Per the user's S57 review: characterize WHAT oracle picks for the Omaha (bot)
hand vs the Hold'em (mid) hand across EVERY max-rank x structural-achievability
cell, then identify the deepest residual axis.

This single script consolidates three drills (one sweep over all 1.226M
high_only hands):

  HO5 — per-max_rank residual stratification.
        For each max_rank in {A,K,Q,J,T,9,8}:
          * total v43 vs oracle mismatch contribution ($/1000h whole-grid)
          * top-10 mismatch classes (v43_pick -> oracle_pick)
          * v43 pick distribution (top x bot_suit x mid_suited)
          * oracle pick distribution (same)
          * pct_opt within max_rank class

  HO6 — full structural achievability cross-tabulation per hand:
          1. n_DS_bot_configs       (count of 4-card subsets that are 2+2)
          2. n_DS_bot_with_max_top  (subsets where max-rank is in leftover)
          3. n_ms_mid_configs       (top, mid_pair) splits with mid 2 cards
                                     suited (across all C(7,1)*C(6,2)=105)
          4. n_joint_DS_ms_max_top  (the ho_v3 count: top=max-rank,
                                     bot 2+2, mid 2 suited)
          5. best_DS_bot_pair_high  (max higher-card-of-suited-pair across
                                     ALL DS bot configs)
          6. best_ms_mid_high       (max higher-card-of-suited-mid across
                                     all (top, mid_pair) splits with
                                     ms mid AND top=max-rank)
          7. bot_mid_quality_gap    (within joint configs, max gap between
                                     best_bot_pair_high and best_mid_high)

  HO7 — what oracle ACTUALLY picks per (max_rank x structural cell):
        For each cell, characterize oracle's chosen setting:
          * TOP rank distribution (always max? sometimes defensive 2-on-top?)
          * BOT (suit profile, sum/max/min ranks, longest run, suit pair high)
          * MID (suit_match status, sum/max/min ranks)
        Same for v43's pick. Mismatches surface the per-cell DELTA.

OUTPUTS
-------
1. Console: per-max_rank tables + per-cell oracle-vs-v43 pick distributions
2. data/drill_ho_v43_per_hand_structural.parquet — per-hand structural
   counts + oracle/v43 pick details. Re-used by HO8/HO9 drills.
3. data/drill_ho_v43_summary.json — aggregate stats keyed by
   (max_rank, structural_cell) for downstream analysis.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v43_deepdive.py
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
from strategy_v43_dt import strategy_v43_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
OUT_PARQUET = ROOT / "data" / "drill_ho_v43_per_hand_structural.parquet"
OUT_JSON = ROOT / "data" / "drill_ho_v43_summary.json"

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


def classify_pick(hand_bytes, feats, idx: int):
    """Return (top_rank, bot_suit_profile_label, mid_suited?, top_label, full_label)."""
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = pos[1:3]
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    top_rank = int(ranks[top_pos])
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_lbl = "ms" if mid_suits[0] == mid_suits[1] else "mu"
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    full = f"t{RANK_CHAR[top_rank]}_{suit_lbl}_{mid_lbl}"
    return top_rank, suit_lbl, mid_lbl, RANK_CHAR[top_rank], full


def longest_run(ranks):
    """Longest run of consecutive distinct ranks among a list."""
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


def suit_pair_high(card_ranks, card_suits):
    """For a 4-card bot, return the higher-of-pair rank for the LARGER (or
    only) suited pair. For DS bots there are two suited pairs; we return
    the max of (higher-of-pair) across both suited groups."""
    by_suit = defaultdict(list)
    for r, s in zip(card_ranks, card_suits):
        by_suit[s].append(r)
    best = 0
    for s, rs in by_suit.items():
        if len(rs) >= 2:
            top = max(rs)
            if top > best:
                best = top
    return best


def compute_hand_structural(hand_bytes):
    """Compute per-hand structural achievability counts and quality
    metrics. Returns a dict.

    Specifically:
      n_DS_bot_configs           : count C(7,4)=35 subsets that are 2+2
      n_DS_bot_with_max_top      : DS bot subsets where max-rank is leftover
      n_ms_mid_configs           : (top_pos, mid_pair) where mid suited
                                     (across all 105 settings = 7*15)
      n_joint_DS_ms_max_top      : top=max-rank AND bot 2+2 AND mid 2 suited
                                     (the ho_v3 count)
      best_DS_bot_pair_high      : across all DS bot configs (any top),
                                     max of (higher-card-of-suited-pair)
                                     considering both suited pairs in the
                                     bot — captures suit-pair quality
      best_ms_mid_high           : across all (top, mid_pair) splits where
                                     mid is suited AND top=max-rank,
                                     max of (higher-of-mid-pair-rank)
      best_ms_mid_high_anytop    : across all (top, mid_pair) splits where
                                     mid is suited (any top), the max
                                     higher-of-mid-pair-rank
      bot_mid_quality_gap        : in JOINT (top=max, DS bot, ms mid)
                                     configs, the MAX gap between
                                     best_bot_pair_high and best_mid_high
                                     across all such configs
                                     (captures trade-off magnitude)
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    max_rank = max(int_ranks)
    # high_only has 7 distinct ranks → max position is unique
    max_pos = int_ranks.index(max_rank)

    n_DS = 0
    n_DS_with_max_top = 0
    n_joint = 0
    best_DS_pair_high = 0
    bot_mid_quality_gap = 0
    joint_best_bot_high = 0
    joint_best_mid_high = 0

    # Enumerate all C(7,4)=35 candidate bot subsets.
    for bot_idx in combinations(range(7), 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        n_DS += 1
        bot_ranks = [int_ranks[i] for i in bot_idx]
        bot_pair_high = suit_pair_high(bot_ranks, bot_suits)
        if bot_pair_high > best_DS_pair_high:
            best_DS_pair_high = bot_pair_high

        leftover_pos = [i for i in range(7) if i not in bot_idx]
        # Is max-rank in the leftover (i.e., not in the bot)?
        if max_pos in leftover_pos:
            n_DS_with_max_top += 1
            # For joint: top=max_pos, mid = the other 2 leftovers.
            mid_pos = [j for j in leftover_pos if j != max_pos]
            mid_ranks = [int_ranks[mid_pos[0]], int_ranks[mid_pos[1]]]
            mid_suits = [int_suits[mid_pos[0]], int_suits[mid_pos[1]]]
            if mid_suits[0] == mid_suits[1]:
                n_joint += 1
                mid_high = max(mid_ranks)
                if mid_high > joint_best_mid_high:
                    joint_best_mid_high = mid_high
                gap = bot_pair_high - mid_high
                if gap > bot_mid_quality_gap:
                    bot_mid_quality_gap = gap
                if bot_pair_high > joint_best_bot_high:
                    joint_best_bot_high = bot_pair_high

    # Enumerate all 105 settings — count ms_mid + ms_mid_with_max_top.
    n_ms_mid = 0
    n_ms_mid_max_top = 0
    best_ms_mid_high = 0
    best_ms_mid_high_anytop = 0
    for top_pos in range(7):
        rest = [i for i in range(7) if i != top_pos]
        for mid_a, mid_b in combinations(rest, 2):
            sa = int_suits[mid_a]
            sb = int_suits[mid_b]
            if sa != sb:
                continue
            n_ms_mid += 1
            mh = max(int_ranks[mid_a], int_ranks[mid_b])
            if mh > best_ms_mid_high_anytop:
                best_ms_mid_high_anytop = mh
            if top_pos == max_pos:
                n_ms_mid_max_top += 1
                if mh > best_ms_mid_high:
                    best_ms_mid_high = mh

    return {
        "max_rank": max_rank,
        "n_DS_bot_configs": n_DS,
        "n_DS_bot_with_max_top": n_DS_with_max_top,
        "n_ms_mid_configs": n_ms_mid,
        "n_ms_mid_with_max_top": n_ms_mid_max_top,
        "n_joint_DS_ms_max_top": n_joint,
        "best_DS_bot_pair_high": best_DS_pair_high,
        "best_ms_mid_high": best_ms_mid_high,
        "best_ms_mid_high_anytop": best_ms_mid_high_anytop,
        "bot_mid_quality_gap": bot_mid_quality_gap,
        "joint_best_bot_pair_high": joint_best_bot_high,
        "joint_best_mid_high": joint_best_mid_high,
    }


def characterize_pick(hand_bytes, feats, idx):
    """Detailed characterization of a chosen setting for HO7 aggregates."""
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    top_rank = int(ranks[top_pos])
    mid_ranks = sorted([int(ranks[mid_pos[0]]), int(ranks[mid_pos[1]])], reverse=True)
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]
    bot_ranks_sorted = sorted([int(ranks[p]) for p in bot_pos], reverse=True)
    bot_suits_arr = [int(suits[p]) for p in bot_pos]
    bot_suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    bot_run = longest_run([int(ranks[p]) for p in bot_pos])
    bot_pair_h = suit_pair_high([int(ranks[p]) for p in bot_pos], bot_suits_arr)
    return {
        "top_rank": top_rank,
        "mid_high": mid_ranks[0],
        "mid_low": mid_ranks[1],
        "mid_sum": mid_ranks[0] + mid_ranks[1],
        "mid_suited": mid_suited,
        "bot_suit": bot_suit_lbl,
        "bot_max": bot_ranks_sorted[0],
        "bot_min": bot_ranks_sorted[3],
        "bot_sum": sum(bot_ranks_sorted),
        "bot_run": bot_run,
        "bot_pair_high": bot_pair_h,
    }


def cell_for_hand(struct):
    """Coarse structural cell key from per-hand counts.

    Cells:
      JOINT_HIGH    : n_joint > 0 and best_ms_mid_high >= J(11)
      JOINT_MED     : n_joint > 0 and 8 <= best_ms_mid_high <= 10
      JOINT_LOW     : n_joint > 0 and best_ms_mid_high <= 7
      DS_NO_JOINT   : n_DS_bot_with_max_top > 0 and n_joint == 0
                      (DS achievable with max on top, but mid would be
                      unsuited)
      DS_NO_MAXTOP  : n_DS > 0 but n_DS_bot_with_max_top == 0
                      (DS achievable only if you sacrifice your max-rank
                      to the bot)
      MS_ONLY       : n_DS == 0 but n_ms_mid_with_max_top > 0
                      (no DS, but there's a suited mid available with
                      max on top)
      NEITHER       : n_DS == 0 and n_ms_mid_with_max_top == 0
    """
    if struct["n_joint_DS_ms_max_top"] > 0:
        h = struct["best_ms_mid_high"]
        if h >= 11:
            return "JOINT_HIGH"
        if h >= 8:
            return "JOINT_MED"
        return "JOINT_LOW"
    if struct["n_DS_bot_with_max_top"] > 0:
        return "DS_NO_JOINT"
    if struct["n_DS_bot_configs"] > 0:
        return "DS_NO_MAXTOP"
    if struct["n_ms_mid_with_max_top"] > 0:
        return "MS_ONLY"
    return "NEITHER"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample hands to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true",
                    help="Skip writing per-hand parquet (debug).")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 58 — Drill HO5+HO6+HO7: high_only deep-dive on v43_dt")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]
    n_ho = len(ho_idx)
    print(f"  high_only hands: {n_ho:,}")

    if args.sample > 0 and n_ho > args.sample:
        rng = np.random.default_rng(args.seed)
        ho_idx = np.sort(rng.choice(ho_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(ho_idx)
    # Per-hand arrays for parquet output + downstream drills.
    arr_cid = np.zeros(n, dtype=np.uint32)
    arr_max = np.zeros(n, dtype=np.int8)
    arr_n_DS = np.zeros(n, dtype=np.int8)
    arr_n_DS_max_top = np.zeros(n, dtype=np.int8)
    arr_n_ms_mid = np.zeros(n, dtype=np.int8)
    arr_n_ms_mid_max_top = np.zeros(n, dtype=np.int8)
    arr_n_joint = np.zeros(n, dtype=np.int8)
    arr_best_DS_pair_high = np.zeros(n, dtype=np.int8)
    arr_best_ms_mid_high = np.zeros(n, dtype=np.int8)
    arr_best_ms_mid_high_anytop = np.zeros(n, dtype=np.int8)
    arr_bot_mid_gap = np.zeros(n, dtype=np.int8)
    arr_v43_idx = np.zeros(n, dtype=np.int16)
    arr_oracle_idx = np.zeros(n, dtype=np.int16)
    arr_regret = np.zeros(n, dtype=np.float32)
    arr_v43_top = np.zeros(n, dtype=np.int8)
    arr_v43_bot_suit = np.zeros(n, dtype=np.int8)  # SUIT_PROFILE codes
    arr_v43_mid_suited = np.zeros(n, dtype=np.bool_)
    arr_v43_bot_pair_high = np.zeros(n, dtype=np.int8)
    arr_v43_mid_high = np.zeros(n, dtype=np.int8)
    arr_v43_mid_sum = np.zeros(n, dtype=np.int8)
    arr_v43_bot_run = np.zeros(n, dtype=np.int8)
    arr_v43_bot_max = np.zeros(n, dtype=np.int8)
    arr_v43_bot_min = np.zeros(n, dtype=np.int8)
    arr_v43_bot_sum = np.zeros(n, dtype=np.int8)
    arr_or_top = np.zeros(n, dtype=np.int8)
    arr_or_bot_suit = np.zeros(n, dtype=np.int8)
    arr_or_mid_suited = np.zeros(n, dtype=np.bool_)
    arr_or_bot_pair_high = np.zeros(n, dtype=np.int8)
    arr_or_mid_high = np.zeros(n, dtype=np.int8)
    arr_or_mid_sum = np.zeros(n, dtype=np.int8)
    arr_or_bot_run = np.zeros(n, dtype=np.int8)
    arr_or_bot_max = np.zeros(n, dtype=np.int8)
    arr_or_bot_min = np.zeros(n, dtype=np.int8)
    arr_or_bot_sum = np.zeros(n, dtype=np.int8)

    # Aggregations — keyed by (max_rank, structural_cell).
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_match": 0,
        "v43_class_dist": Counter(),
        "oracle_class_dist": Counter(),
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
        # HO7 aggregates: distributions of TOP/BOT/MID for oracle and v43
        "or_top_rank_dist": Counter(),
        "or_bot_suit_dist": Counter(),
        "or_mid_suited_n": 0,
        "or_bot_run_dist": Counter(),
        "or_bot_pair_high_dist": Counter(),
        "or_mid_high_dist": Counter(),
        "or_bot_sum_total": 0,
        "or_mid_sum_total": 0,
        "v43_top_rank_dist": Counter(),
        "v43_bot_suit_dist": Counter(),
        "v43_mid_suited_n": 0,
        "v43_bot_run_dist": Counter(),
        "v43_bot_pair_high_dist": Counter(),
        "v43_mid_high_dist": Counter(),
        "v43_bot_sum_total": 0,
        "v43_mid_sum_total": 0,
    })
    # Per-max-rank-only aggregates (HO5).
    rank_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_match": 0,
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
        "v43_class_dist": Counter(),
        "oracle_class_dist": Counter(),
    })
    # Distribution of structural cells per max-rank
    rank_cell_n = defaultdict(lambda: Counter())
    rank_cell_regret = defaultdict(lambda: defaultdict(float))

    print("\n[3/4] sweeping per-hand v43 vs oracle + structural counts ...",
          flush=True)
    t0 = time.time()
    for k, cid in enumerate(ho_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v43_idx = int(strategy_v43_dt(h))
        regret = float(rowf[oracle_idx]) - float(rowf[v43_idx])

        struct = compute_hand_structural(h)
        cell = cell_for_hand(struct)
        max_rank = struct["max_rank"]

        v43_top, v43_suit, v43_midlbl, _, v43_class = classify_pick(h, feats, v43_idx)
        or_top, or_suit, or_midlbl, _, or_class = classify_pick(h, feats, oracle_idx)

        v43_det = characterize_pick(h, feats, v43_idx)
        or_det = characterize_pick(h, feats, oracle_idx)

        # Fill per-hand arrays
        arr_cid[k] = cid
        arr_max[k] = max_rank
        arr_n_DS[k] = struct["n_DS_bot_configs"]
        arr_n_DS_max_top[k] = struct["n_DS_bot_with_max_top"]
        arr_n_ms_mid[k] = struct["n_ms_mid_configs"]
        arr_n_ms_mid_max_top[k] = struct["n_ms_mid_with_max_top"]
        arr_n_joint[k] = struct["n_joint_DS_ms_max_top"]
        arr_best_DS_pair_high[k] = struct["best_DS_bot_pair_high"]
        arr_best_ms_mid_high[k] = struct["best_ms_mid_high"]
        arr_best_ms_mid_high_anytop[k] = struct["best_ms_mid_high_anytop"]
        arr_bot_mid_gap[k] = struct["bot_mid_quality_gap"]
        arr_v43_idx[k] = v43_idx
        arr_oracle_idx[k] = oracle_idx
        arr_regret[k] = regret
        arr_v43_top[k] = v43_det["top_rank"]
        arr_v43_bot_suit[k] = int(feats.bot_suit_profile[v43_idx])
        arr_v43_mid_suited[k] = v43_det["mid_suited"]
        arr_v43_bot_pair_high[k] = v43_det["bot_pair_high"]
        arr_v43_mid_high[k] = v43_det["mid_high"]
        arr_v43_mid_sum[k] = v43_det["mid_sum"]
        arr_v43_bot_run[k] = v43_det["bot_run"]
        arr_v43_bot_max[k] = v43_det["bot_max"]
        arr_v43_bot_min[k] = v43_det["bot_min"]
        arr_v43_bot_sum[k] = v43_det["bot_sum"]
        arr_or_top[k] = or_det["top_rank"]
        arr_or_bot_suit[k] = int(feats.bot_suit_profile[oracle_idx])
        arr_or_mid_suited[k] = or_det["mid_suited"]
        arr_or_bot_pair_high[k] = or_det["bot_pair_high"]
        arr_or_mid_high[k] = or_det["mid_high"]
        arr_or_mid_sum[k] = or_det["mid_sum"]
        arr_or_bot_run[k] = or_det["bot_run"]
        arr_or_bot_max[k] = or_det["bot_max"]
        arr_or_bot_min[k] = or_det["bot_min"]
        arr_or_bot_sum[k] = or_det["bot_sum"]

        # Cell aggregates
        st = cell_stats[(max_rank, cell)]
        st["n"] += 1
        st["sum_regret"] += regret
        st["v43_class_dist"][v43_class] += 1
        st["oracle_class_dist"][or_class] += 1
        if v43_idx == oracle_idx:
            st["n_match"] += 1
        if v43_class != or_class:
            st["mismatch"][(v43_class, or_class)] += 1
            st["mismatch_regret"][(v43_class, or_class)] += regret
        st["or_top_rank_dist"][or_det["top_rank"]] += 1
        st["or_bot_suit_dist"][or_det["bot_suit"]] += 1
        st["or_mid_suited_n"] += int(or_det["mid_suited"])
        st["or_bot_run_dist"][or_det["bot_run"]] += 1
        st["or_bot_pair_high_dist"][or_det["bot_pair_high"]] += 1
        st["or_mid_high_dist"][or_det["mid_high"]] += 1
        st["or_bot_sum_total"] += or_det["bot_sum"]
        st["or_mid_sum_total"] += or_det["mid_sum"]
        st["v43_top_rank_dist"][v43_det["top_rank"]] += 1
        st["v43_bot_suit_dist"][v43_det["bot_suit"]] += 1
        st["v43_mid_suited_n"] += int(v43_det["mid_suited"])
        st["v43_bot_run_dist"][v43_det["bot_run"]] += 1
        st["v43_bot_pair_high_dist"][v43_det["bot_pair_high"]] += 1
        st["v43_mid_high_dist"][v43_det["mid_high"]] += 1
        st["v43_bot_sum_total"] += v43_det["bot_sum"]
        st["v43_mid_sum_total"] += v43_det["mid_sum"]

        # Per-max-rank aggregates
        rs = rank_stats[max_rank]
        rs["n"] += 1
        rs["sum_regret"] += regret
        if v43_idx == oracle_idx:
            rs["n_match"] += 1
        if v43_class != or_class:
            rs["mismatch"][(v43_class, or_class)] += 1
            rs["mismatch_regret"][(v43_class, or_class)] += regret
        rs["v43_class_dist"][v43_class] += 1
        rs["oracle_class_dist"][or_class] += 1
        rank_cell_n[max_rank][cell] += 1
        rank_cell_regret[max_rank][cell] += regret

        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ===========================================================
    # HO5 — per-max-rank residual stratification
    # ===========================================================
    print("=" * 100)
    print("HO5: PER-MAX-RANK RESIDUAL STRATIFICATION (v43_dt vs oracle)")
    print("=" * 100)
    print(f"  {'max':>3} {'n_hands':>9} {'pct_opt':>8} {'mean_reg':>10} "
          f"{'wg_contrib':>12}")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if rs["n"] == 0:
            continue
        pct_opt = 100 * rs["n_match"] / rs["n"]
        mean_reg = rs["sum_regret"] / rs["n"] * EV_TO_DOL * 1000
        wg = rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {RANK_CHAR[max_rank]:>3} {rs['n']:>9,} {pct_opt:>7.2f}% "
              f"${mean_reg:>+8.1f} ${wg:>+10.2f}")

    print("\n  Per-max-rank top-10 mismatch classes:")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if not rs["mismatch_regret"]:
            continue
        print(f"\n  ── max_rank = {RANK_CHAR[max_rank]} ──")
        ranked = sorted(rs["mismatch_regret"].items(), key=lambda x: -x[1])
        for (vc, oc), reg in ranked[:10]:
            n = rs["mismatch"][(vc, oc)]
            mean_reg = reg / n * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"    {vc:<22} -> {oc:<22} n={n:>7,} mean=${mean_reg:>+7.1f} "
                  f"wg=${wg:>+7.2f}")

    print("\n  Per-max-rank class distribution (v43 pick % vs oracle pick %):")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if rs["n"] == 0:
            continue
        print(f"\n  ── max_rank = {RANK_CHAR[max_rank]}  (n={rs['n']:,}) ──")
        all_classes = sorted(set(rs["v43_class_dist"].keys()) |
                              set(rs["oracle_class_dist"].keys()),
                              key=lambda c: -(rs["v43_class_dist"][c] +
                                              rs["oracle_class_dist"][c]))
        print(f"    {'class':<22} {'v43_pct':>9} {'oracle_pct':>11} {'delta':>9}")
        for c in all_classes[:15]:
            vp = 100 * rs["v43_class_dist"][c] / rs["n"]
            op = 100 * rs["oracle_class_dist"][c] / rs["n"]
            print(f"    {c:<22} {vp:>8.2f}% {op:>10.2f}% {(vp-op):>+8.2f}%")

    # ===========================================================
    # HO6 — structural achievability cross-tabulation per max_rank
    # ===========================================================
    print("\n" + "=" * 100)
    print("HO6: STRUCTURAL CELL CROSS-TABULATION (per max_rank x cell)")
    print("=" * 100)
    print(f"  {'max':>3} {'cell':<14} {'n_hands':>9} {'pct_of_max':>11} "
          f"{'wg_contrib':>12} {'mean_reg':>10}")
    cells_order = ["JOINT_HIGH", "JOINT_MED", "JOINT_LOW",
                    "DS_NO_JOINT", "DS_NO_MAXTOP", "MS_ONLY", "NEITHER"]
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        n_total = rank_stats[max_rank]["n"]
        for cell in cells_order:
            n_in_cell = rank_cell_n[max_rank].get(cell, 0)
            if n_in_cell == 0:
                continue
            reg = rank_cell_regret[max_rank].get(cell, 0.0)
            pct_of_max = 100 * n_in_cell / n_total
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            mean_reg = reg / n_in_cell * EV_TO_DOL * 1000
            print(f"  {RANK_CHAR[max_rank]:>3} {cell:<14} {n_in_cell:>9,} "
                  f"{pct_of_max:>10.1f}% ${wg:>+10.2f} ${mean_reg:>+8.1f}")

    # ===========================================================
    # HO7 — what oracle actually picks per cell
    # ===========================================================
    print("\n" + "=" * 100)
    print("HO7: ORACLE'S PICK PROFILE PER (max_rank x cell)")
    print("=" * 100)
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        for cell in cells_order:
            st = cell_stats.get((max_rank, cell), None)
            if st is None or st["n"] == 0:
                continue
            n = st["n"]
            mean_reg = st["sum_regret"] / n * EV_TO_DOL * 1000
            pct_match = 100 * st["n_match"] / n
            print(f"\n  ── max_rank={RANK_CHAR[max_rank]}  cell={cell}  n={n:,}  "
                  f"pct_opt={pct_match:.1f}%  mean_reg=${mean_reg:+.1f} ──")
            # Oracle's TOP rank distribution
            top_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/n:.0f}%"
                for r, c in sorted(st["or_top_rank_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    oracle TOP:        {top_summary}")
            # Oracle's BOT suit distribution
            bot_suit_summary = ", ".join(
                f"{s}:{100*c/n:.0f}%"
                for s, c in sorted(st["or_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle BOT_suit:   {bot_suit_summary}")
            # Oracle BOT longest_run distribution
            run_summary = ", ".join(
                f"r{r}:{100*c/n:.0f}%"
                for r, c in sorted(st["or_bot_run_dist"].items())
            )
            print(f"    oracle BOT_run:    {run_summary}  bot_sum_avg={st['or_bot_sum_total']/n:.1f}")
            # Oracle MID
            ms_pct = 100 * st["or_mid_suited_n"] / n
            mid_high_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/n:.0f}%"
                for r, c in sorted(st["or_mid_high_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    oracle MID_suited: {ms_pct:.1f}%  mid_sum_avg={st['or_mid_sum_total']/n:.1f}")
            print(f"    oracle MID_high:   {mid_high_summary}")
            # v43 same
            v43_top_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/n:.0f}%"
                for r, c in sorted(st["v43_top_rank_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    v43    TOP:        {v43_top_summary}")
            v43_bot_suit_summary = ", ".join(
                f"{s}:{100*c/n:.0f}%"
                for s, c in sorted(st["v43_bot_suit_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v43    BOT_suit:   {v43_bot_suit_summary}")
            v43_run_summary = ", ".join(
                f"r{r}:{100*c/n:.0f}%"
                for r, c in sorted(st["v43_bot_run_dist"].items())
            )
            print(f"    v43    BOT_run:    {v43_run_summary}  bot_sum_avg={st['v43_bot_sum_total']/n:.1f}")
            v43_ms_pct = 100 * st["v43_mid_suited_n"] / n
            v43_mid_high_summary = ", ".join(
                f"{RANK_CHAR.get(r, r)}:{100*c/n:.0f}%"
                for r, c in sorted(st["v43_mid_high_dist"].items(), key=lambda x: -x[1])[:5]
            )
            print(f"    v43    MID_suited: {v43_ms_pct:.1f}%  mid_sum_avg={st['v43_mid_sum_total']/n:.1f}")
            print(f"    v43    MID_high:   {v43_mid_high_summary}")
            # Top mismatch within cell
            if st["mismatch_regret"]:
                ranked = sorted(st["mismatch_regret"].items(), key=lambda x: -x[1])
                print("    top mismatch within cell:")
                for (vc, oc), reg in ranked[:3]:
                    nn = st["mismatch"][(vc, oc)]
                    mr = reg / nn * EV_TO_DOL * 1000
                    wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
                    print(f"      {vc:<22} -> {oc:<22} n={nn:>6,} "
                          f"mean=${mr:>+7.1f} wg=${wg:>+6.2f}")

    # ===========================================================
    # Persist per-hand structural data + summary JSON
    # ===========================================================
    if not args.no_parquet:
        print(f"\n[4/4] writing per-hand parquet to {OUT_PARQUET} ...", flush=True)
        table = pa.table({
            "canonical_id": pa.array(arr_cid, type=pa.uint32()),
            "max_rank": pa.array(arr_max, type=pa.int8()),
            "n_DS_bot_configs": pa.array(arr_n_DS, type=pa.int8()),
            "n_DS_bot_with_max_top": pa.array(arr_n_DS_max_top, type=pa.int8()),
            "n_ms_mid_configs": pa.array(arr_n_ms_mid, type=pa.int8()),
            "n_ms_mid_with_max_top": pa.array(arr_n_ms_mid_max_top, type=pa.int8()),
            "n_joint_DS_ms_max_top": pa.array(arr_n_joint, type=pa.int8()),
            "best_DS_bot_pair_high": pa.array(arr_best_DS_pair_high, type=pa.int8()),
            "best_ms_mid_high": pa.array(arr_best_ms_mid_high, type=pa.int8()),
            "best_ms_mid_high_anytop": pa.array(arr_best_ms_mid_high_anytop, type=pa.int8()),
            "bot_mid_quality_gap": pa.array(arr_bot_mid_gap, type=pa.int8()),
            "v43_idx": pa.array(arr_v43_idx, type=pa.int16()),
            "oracle_idx": pa.array(arr_oracle_idx, type=pa.int16()),
            "regret": pa.array(arr_regret, type=pa.float32()),
            "v43_top": pa.array(arr_v43_top, type=pa.int8()),
            "v43_bot_suit": pa.array(arr_v43_bot_suit, type=pa.int8()),
            "v43_mid_suited": pa.array(arr_v43_mid_suited, type=pa.bool_()),
            "v43_bot_pair_high": pa.array(arr_v43_bot_pair_high, type=pa.int8()),
            "v43_mid_high": pa.array(arr_v43_mid_high, type=pa.int8()),
            "v43_mid_sum": pa.array(arr_v43_mid_sum, type=pa.int8()),
            "v43_bot_run": pa.array(arr_v43_bot_run, type=pa.int8()),
            "v43_bot_max": pa.array(arr_v43_bot_max, type=pa.int8()),
            "v43_bot_min": pa.array(arr_v43_bot_min, type=pa.int8()),
            "v43_bot_sum": pa.array(arr_v43_bot_sum, type=pa.int8()),
            "or_top": pa.array(arr_or_top, type=pa.int8()),
            "or_bot_suit": pa.array(arr_or_bot_suit, type=pa.int8()),
            "or_mid_suited": pa.array(arr_or_mid_suited, type=pa.bool_()),
            "or_bot_pair_high": pa.array(arr_or_bot_pair_high, type=pa.int8()),
            "or_mid_high": pa.array(arr_or_mid_high, type=pa.int8()),
            "or_mid_sum": pa.array(arr_or_mid_sum, type=pa.int8()),
            "or_bot_run": pa.array(arr_or_bot_run, type=pa.int8()),
            "or_bot_max": pa.array(arr_or_bot_max, type=pa.int8()),
            "or_bot_min": pa.array(arr_or_bot_min, type=pa.int8()),
            "or_bot_sum": pa.array(arr_or_bot_sum, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3, write_statistics=True)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
