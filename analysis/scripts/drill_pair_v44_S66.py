"""
Session 66 Phase 1 — Pair category deep-dive: structural cell classification +
oracle/v44 pick distribution per (pair_rank x cell). Analog to S58's
high_only decision matrix, scoped to category=pair (cat=1).

Output:
  data/drill_pair_v44_per_hand_structural.parquet
  data/drill_pair_v44_summary.json
  Console: per-pair_rank residual tables, structural cell cross-tab, and
           oracle pick profile per (pair_rank, cell).

Cell taxonomy (S66 fresh design — pair-specific, NOT a copy of S58):

  PBOT_DS_JOINT       — pair-to-bot DS achievable AND ms_mid achievable AND
                        max non-pair singleton on top achievable
                        (= "joint pair-to-bot": pair+kickers in bot, ms_mid
                         from 2 remaining singletons, max sing on top)
  PBOT_DS_PARTIAL     — pair-to-bot DS achievable but no ms_mid+maxtop combo
  PMID_DS_MAXTOP      — Not PBOT_DS_achievable AND PMID + DS bot from 5
                        singletons (taking 4) + max sing on top achievable
  PMID_DS_NOMAXTOP    — Not PBOT_DS AND PMID DS achievable only with max
                        sing in bot
  PMID_SS_MAXTOP      — Not PBOT_DS AND no PMID DS AND PMID + SS bot +
                        max sing on top achievable
  PMID_OTHER          — none of the above (PMID with only 31/RB/4f bot)

Pick classification (oracle / v44):
  pair_placement: PMID (both pair in mid), PBOT (both in bot), SPLIT
  top_type:       PAIR / SING_MAX / SING_NOMAX
  bot_suit_profile: DS / SS / 31 / RB / 4f
  mid_suited:     bool (NOTE: PMID picks always mid_suited=False since the
                  two pair cards have different suits by construction)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_pair_v44_S66.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_pair_v44_S66.py --sample 5000
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
OUT_PARQUET = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
OUT_JSON = ROOT / "data" / "drill_pair_v44_summary.json"

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


def compute_pair_structural(hand_bytes):
    """Compute pair-hand structural achievability counts and indices.

    Returns dict with:
      pair_rank, pair_pos (tuple of 2 ints), pair_suits (tuple of 2 ints)
      sing_pos (list of 5 ints), sing_ranks (list of 5 ints),
      max_sing_rank, max_sing_pos
      n_PBOT_DS, n_PBOT_DS_w_msmid_maxtop
      n_PMID_DS, n_PMID_DS_w_maxtop, n_PMID_SS_w_maxtop
      best_PBOT_DS_mid_high, best_PMID_DS_bot_pair_high

    Notes:
      - PBOT_DS: pair (2 suits a,b) + 2 of 5 singletons such that bot suits
                 are exactly (a,a,b,b). Requires one singleton of suit a and
                 one of suit b joining the pair.
      - PMID_DS: 4 of 5 singletons have 2+2 suit pattern.
      - "_maxtop": the leftover (= top position) is the max-rank singleton.
      - "ms_mid" for PBOT: the 2 singletons NOT used in bot must have the
                           same suit AND not include max_sing (max_sing must
                           be on top).
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    # Identify pair: the rank with 2 occurrences.
    rc = Counter(int_ranks)
    pair_rank = None
    for r, c in rc.items():
        if c == 2:
            pair_rank = r
            break
    assert pair_rank is not None, "Not a pair hand!"

    pair_pos = tuple(i for i in range(7) if int_ranks[i] == pair_rank)
    pair_suits = (int_suits[pair_pos[0]], int_suits[pair_pos[1]])
    assert pair_suits[0] != pair_suits[1], "Pair cards must have different suits"

    sing_pos = [i for i in range(7) if i not in pair_pos]
    sing_ranks = [int_ranks[i] for i in sing_pos]
    sing_suits = [int_suits[i] for i in sing_pos]
    assert len(sing_pos) == 5

    max_sing_rank = max(sing_ranks)
    max_sing_local = sing_ranks.index(max_sing_rank)
    max_sing_pos = sing_pos[max_sing_local]

    sa, sb = pair_suits  # pair's two distinct suits

    # ---- PBOT_DS enumeration: bot = {pair[0], pair[1], sing_i, sing_j} ----
    # Require sing_i.suit == sa AND sing_j.suit == sb (or vice versa), so
    # bot suits are (sa, sa, sb, sb) = DS.
    pbot_ds_configs = []  # list of (kicker_a_local, kicker_b_local)
    sing_by_suit_a = [k for k, s in enumerate(sing_suits) if s == sa]
    sing_by_suit_b = [k for k, s in enumerate(sing_suits) if s == sb]
    sing_other = [k for k, s in enumerate(sing_suits) if s not in (sa, sb)]
    for ka in sing_by_suit_a:
        for kb in sing_by_suit_b:
            if ka == kb:
                continue
            pbot_ds_configs.append((ka, kb))

    n_PBOT_DS = len(pbot_ds_configs)

    # PBOT_DS_w_msmid_maxtop: among PBOT_DS configs, does there exist a
    # split of the remaining 3 singletons into (top=max_sing, mid={2 others
    # same-suit})?
    n_PBOT_DS_w_msmid_maxtop = 0
    best_PBOT_DS_mid_high = 0
    for ka, kb in pbot_ds_configs:
        remaining = [k for k in range(5) if k not in (ka, kb)]
        if max_sing_local not in remaining:
            continue  # max_sing is in bot
        mid_locals = [k for k in remaining if k != max_sing_local]
        assert len(mid_locals) == 2
        if sing_suits[mid_locals[0]] != sing_suits[mid_locals[1]]:
            continue
        n_PBOT_DS_w_msmid_maxtop += 1
        mh = max(sing_ranks[mid_locals[0]], sing_ranks[mid_locals[1]])
        if mh > best_PBOT_DS_mid_high:
            best_PBOT_DS_mid_high = mh

    # ---- PMID enumeration: bot = 4 of 5 singletons ----
    # PMID = pair both in mid.
    # n_PMID_DS: # of 4-subsets of 5 singletons with 2+2 suit pattern.
    # n_PMID_DS_w_maxtop: same AND the leftover (top) is max_sing.
    # n_PMID_SS_w_maxtop: # 4-subsets with 2+1+1 suit pattern AND top=max_sing.
    n_PMID_DS = 0
    n_PMID_DS_w_maxtop = 0
    n_PMID_SS_w_maxtop = 0
    best_PMID_DS_bot_pair_high = 0
    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
        is_DS = (cnt == [2, 2])
        is_SS = (cnt == [2, 1, 1])
        if is_DS:
            n_PMID_DS += 1
            # bot_pair_high under PMID = max-of-(higher-of-each-suited-pair)
            by_suit = defaultdict(list)
            for k in bot_locals:
                by_suit[sing_suits[k]].append(sing_ranks[k])
            local_pair_high = 0
            for sgrp, rs in by_suit.items():
                if len(rs) >= 2:
                    hi = max(rs)
                    if hi > local_pair_high:
                        local_pair_high = hi
            if local_pair_high > best_PMID_DS_bot_pair_high:
                best_PMID_DS_bot_pair_high = local_pair_high
            if top_local == max_sing_local:
                n_PMID_DS_w_maxtop += 1
        if is_SS and top_local == max_sing_local:
            n_PMID_SS_w_maxtop += 1

    return {
        "pair_rank": pair_rank,
        "pair_pos": pair_pos,
        "pair_suits": pair_suits,
        "sing_pos": tuple(sing_pos),
        "sing_ranks": tuple(sing_ranks),
        "max_sing_rank": max_sing_rank,
        "max_sing_pos": max_sing_pos,
        "n_PBOT_DS": n_PBOT_DS,
        "n_PBOT_DS_w_msmid_maxtop": n_PBOT_DS_w_msmid_maxtop,
        "n_PMID_DS": n_PMID_DS,
        "n_PMID_DS_w_maxtop": n_PMID_DS_w_maxtop,
        "n_PMID_SS_w_maxtop": n_PMID_SS_w_maxtop,
        "best_PBOT_DS_mid_high": best_PBOT_DS_mid_high,
        "best_PMID_DS_bot_pair_high": best_PMID_DS_bot_pair_high,
    }


def cell_for_pair_hand(struct):
    """Map pair-hand structural counts to a 6-cell taxonomy.

    Priority (first match wins):
      PBOT_DS_JOINT     : n_PBOT_DS_w_msmid_maxtop > 0
      PBOT_DS_PARTIAL   : n_PBOT_DS > 0 (but no msmid+maxtop)
      PMID_DS_MAXTOP    : n_PMID_DS_w_maxtop > 0
      PMID_DS_NOMAXTOP  : n_PMID_DS > 0 (but no maxtop)
      PMID_SS_MAXTOP    : n_PMID_SS_w_maxtop > 0
      PMID_OTHER        : otherwise
    """
    if struct["n_PBOT_DS_w_msmid_maxtop"] > 0:
        return "PBOT_DS_JOINT"
    if struct["n_PBOT_DS"] > 0:
        return "PBOT_DS_PARTIAL"
    if struct["n_PMID_DS_w_maxtop"] > 0:
        return "PMID_DS_MAXTOP"
    if struct["n_PMID_DS"] > 0:
        return "PMID_DS_NOMAXTOP"
    if struct["n_PMID_SS_w_maxtop"] > 0:
        return "PMID_SS_MAXTOP"
    return "PMID_OTHER"


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


def classify_pick_pair(hand_bytes, feats, idx, struct):
    """Classify a chosen setting for a pair hand into pair-specific labels.

    Returns dict with:
      pair_placement: 'PMID' | 'PBOT' | 'SPLIT'
      top_type:       'PAIR' | 'SING_MAX' | 'SING_NOMAX'
      top_rank, mid_high, mid_low, mid_sum, mid_suited
      bot_suit (DS/SS/31/RB/4f), bot_max, bot_min, bot_sum, bot_run,
      bot_pair_high, bot_has_pair (true if both pair cards in bot)
      class_label: compact composite label
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3

    pair_pos_set = set(struct["pair_pos"])
    max_sing_pos = struct["max_sing_pos"]

    n_pair_in_mid = sum(1 for p in mid_pos if p in pair_pos_set)
    n_pair_in_bot = sum(1 for p in bot_pos if p in pair_pos_set)

    if n_pair_in_mid == 2:
        pair_placement = "PMID"
    elif n_pair_in_bot == 2:
        pair_placement = "PBOT"
    else:
        pair_placement = "SPLIT"

    if top_pos in pair_pos_set:
        top_type = "PAIR"
    elif top_pos == max_sing_pos:
        top_type = "SING_MAX"
    else:
        top_type = "SING_NOMAX"

    top_rank = int(ranks[top_pos])
    mid_ranks_sorted = sorted([int(ranks[mid_pos[0]]), int(ranks[mid_pos[1]])], reverse=True)
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]

    bot_ranks_sorted = sorted([int(ranks[p]) for p in bot_pos], reverse=True)
    bot_suits_arr = [int(suits[p]) for p in bot_pos]
    bot_suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    bot_run = longest_run([int(ranks[p]) for p in bot_pos])
    by_suit = defaultdict(list)
    for r, s in zip([int(ranks[p]) for p in bot_pos], bot_suits_arr):
        by_suit[s].append(r)
    bot_pair_h = 0
    for s, rs in by_suit.items():
        if len(rs) >= 2:
            top = max(rs)
            if top > bot_pair_h:
                bot_pair_h = top

    # Compact class label: e.g. "PMID_tmax_SS", "PBOT_tmax_DS_ms",
    # "SPLIT_tpair_DS_ms"
    top_lbl_short = {"PAIR": "tpair", "SING_MAX": "tmax", "SING_NOMAX": "tnomax"}[top_type]
    ms_lbl = "ms" if mid_suited else "mu"
    if pair_placement == "PMID":
        # Mid is always unsuited under PMID (pair has 2 different suits).
        class_label = f"PMID_{top_lbl_short}_{bot_suit_lbl}"
    else:
        class_label = f"{pair_placement}_{top_lbl_short}_{bot_suit_lbl}_{ms_lbl}"

    return {
        "pair_placement": pair_placement,
        "top_type": top_type,
        "top_rank": top_rank,
        "mid_high": mid_ranks_sorted[0],
        "mid_low": mid_ranks_sorted[1],
        "mid_sum": mid_ranks_sorted[0] + mid_ranks_sorted[1],
        "mid_suited": mid_suited,
        "bot_suit": bot_suit_lbl,
        "bot_max": bot_ranks_sorted[0],
        "bot_min": bot_ranks_sorted[3],
        "bot_sum": sum(bot_ranks_sorted),
        "bot_run": bot_run,
        "bot_pair_high": bot_pair_h,
        "class_label": class_label,
    }


_PAIR_PLACEMENT_CODE = {"PMID": 0, "PBOT": 1, "SPLIT": 2}
_TOP_TYPE_CODE = {"PAIR": 0, "SING_MAX": 1, "SING_NOMAX": 2}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample hands to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-parquet", action="store_true",
                    help="Skip writing per-hand parquet (debug).")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 66 Phase 1 — Pair deep-dive (oracle + v44_dt vs structural cell)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    pair_idx = np.where(cats == 1)[0]
    n_pair = len(pair_idx)
    print(f"  pair hands: {n_pair:,}")

    if args.sample > 0 and n_pair > args.sample:
        rng = np.random.default_rng(args.seed)
        pair_idx = np.sort(rng.choice(pair_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(pair_idx)
    # Per-hand arrays for parquet output + downstream drills.
    arr_cid = np.zeros(n, dtype=np.uint32)
    arr_pair_rank = np.zeros(n, dtype=np.int8)
    arr_max_sing = np.zeros(n, dtype=np.int8)
    arr_n_PBOT_DS = np.zeros(n, dtype=np.int8)
    arr_n_PBOT_DS_w_msmid_maxtop = np.zeros(n, dtype=np.int8)
    arr_n_PMID_DS = np.zeros(n, dtype=np.int8)
    arr_n_PMID_DS_w_maxtop = np.zeros(n, dtype=np.int8)
    arr_n_PMID_SS_w_maxtop = np.zeros(n, dtype=np.int8)
    arr_best_PBOT_mid_high = np.zeros(n, dtype=np.int8)
    arr_best_PMID_bot_pair_high = np.zeros(n, dtype=np.int8)
    arr_cell = np.zeros(n, dtype=np.int8)  # 0..5 index into CELLS_ORDER
    arr_v44_idx = np.zeros(n, dtype=np.int16)
    arr_oracle_idx = np.zeros(n, dtype=np.int16)
    arr_regret = np.zeros(n, dtype=np.float32)
    arr_v44_placement = np.zeros(n, dtype=np.int8)
    arr_v44_top_type = np.zeros(n, dtype=np.int8)
    arr_v44_top_rank = np.zeros(n, dtype=np.int8)
    arr_v44_bot_suit = np.zeros(n, dtype=np.int8)
    arr_v44_mid_suited = np.zeros(n, dtype=np.bool_)
    arr_v44_mid_high = np.zeros(n, dtype=np.int8)
    arr_v44_bot_pair_high = np.zeros(n, dtype=np.int8)
    arr_v44_bot_run = np.zeros(n, dtype=np.int8)
    arr_or_placement = np.zeros(n, dtype=np.int8)
    arr_or_top_type = np.zeros(n, dtype=np.int8)
    arr_or_top_rank = np.zeros(n, dtype=np.int8)
    arr_or_bot_suit = np.zeros(n, dtype=np.int8)
    arr_or_mid_suited = np.zeros(n, dtype=np.bool_)
    arr_or_mid_high = np.zeros(n, dtype=np.int8)
    arr_or_bot_pair_high = np.zeros(n, dtype=np.int8)
    arr_or_bot_run = np.zeros(n, dtype=np.int8)

    # Aggregations — keyed by (pair_rank, cell).
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_match": 0,
        "v44_class_dist": Counter(),
        "oracle_class_dist": Counter(),
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
        "or_top_rank_dist": Counter(),
        "or_top_type_dist": Counter(),
        "or_placement_dist": Counter(),
        "or_bot_suit_dist": Counter(),
        "or_mid_suited_n": 0,
        "or_bot_pair_high_dist": Counter(),
        "or_mid_high_dist": Counter(),
        "or_bot_run_dist": Counter(),
        "v44_top_rank_dist": Counter(),
        "v44_top_type_dist": Counter(),
        "v44_placement_dist": Counter(),
        "v44_bot_suit_dist": Counter(),
        "v44_mid_suited_n": 0,
        "v44_bot_pair_high_dist": Counter(),
        "v44_mid_high_dist": Counter(),
        "v44_bot_run_dist": Counter(),
    })
    # Per-pair-rank aggregates.
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
    for k, cid in enumerate(pair_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v44_idx = int(strategy_v44_dt(h))
        regret = float(rowf[oracle_idx]) - float(rowf[v44_idx])

        struct = compute_pair_structural(h)
        cell = cell_for_pair_hand(struct)
        pair_rank = struct["pair_rank"]
        max_sing_rank = struct["max_sing_rank"]

        v44_det = classify_pick_pair(h, feats, v44_idx, struct)
        or_det = classify_pick_pair(h, feats, oracle_idx, struct)

        v44_class = v44_det["class_label"]
        or_class = or_det["class_label"]

        # Fill per-hand arrays
        arr_cid[k] = cid
        arr_pair_rank[k] = pair_rank
        arr_max_sing[k] = max_sing_rank
        arr_n_PBOT_DS[k] = struct["n_PBOT_DS"]
        arr_n_PBOT_DS_w_msmid_maxtop[k] = struct["n_PBOT_DS_w_msmid_maxtop"]
        arr_n_PMID_DS[k] = struct["n_PMID_DS"]
        arr_n_PMID_DS_w_maxtop[k] = struct["n_PMID_DS_w_maxtop"]
        arr_n_PMID_SS_w_maxtop[k] = struct["n_PMID_SS_w_maxtop"]
        arr_best_PBOT_mid_high[k] = struct["best_PBOT_DS_mid_high"]
        arr_best_PMID_bot_pair_high[k] = struct["best_PMID_DS_bot_pair_high"]
        arr_cell[k] = CELLS_ORDER.index(cell)
        arr_v44_idx[k] = v44_idx
        arr_oracle_idx[k] = oracle_idx
        arr_regret[k] = regret
        arr_v44_placement[k] = _PAIR_PLACEMENT_CODE[v44_det["pair_placement"]]
        arr_v44_top_type[k] = _TOP_TYPE_CODE[v44_det["top_type"]]
        arr_v44_top_rank[k] = v44_det["top_rank"]
        arr_v44_bot_suit[k] = int(feats.bot_suit_profile[v44_idx])
        arr_v44_mid_suited[k] = v44_det["mid_suited"]
        arr_v44_mid_high[k] = v44_det["mid_high"]
        arr_v44_bot_pair_high[k] = v44_det["bot_pair_high"]
        arr_v44_bot_run[k] = v44_det["bot_run"]
        arr_or_placement[k] = _PAIR_PLACEMENT_CODE[or_det["pair_placement"]]
        arr_or_top_type[k] = _TOP_TYPE_CODE[or_det["top_type"]]
        arr_or_top_rank[k] = or_det["top_rank"]
        arr_or_bot_suit[k] = int(feats.bot_suit_profile[oracle_idx])
        arr_or_mid_suited[k] = or_det["mid_suited"]
        arr_or_mid_high[k] = or_det["mid_high"]
        arr_or_bot_pair_high[k] = or_det["bot_pair_high"]
        arr_or_bot_run[k] = or_det["bot_run"]

        st = cell_stats[(pair_rank, cell)]
        st["n"] += 1
        st["sum_regret"] += regret
        st["v44_class_dist"][v44_class] += 1
        st["oracle_class_dist"][or_class] += 1
        if v44_idx == oracle_idx:
            st["n_match"] += 1
        if v44_class != or_class:
            st["mismatch"][(v44_class, or_class)] += 1
            st["mismatch_regret"][(v44_class, or_class)] += regret
        st["or_top_rank_dist"][or_det["top_rank"]] += 1
        st["or_top_type_dist"][or_det["top_type"]] += 1
        st["or_placement_dist"][or_det["pair_placement"]] += 1
        st["or_bot_suit_dist"][or_det["bot_suit"]] += 1
        st["or_mid_suited_n"] += int(or_det["mid_suited"])
        st["or_bot_pair_high_dist"][or_det["bot_pair_high"]] += 1
        st["or_mid_high_dist"][or_det["mid_high"]] += 1
        st["or_bot_run_dist"][or_det["bot_run"]] += 1
        st["v44_top_rank_dist"][v44_det["top_rank"]] += 1
        st["v44_top_type_dist"][v44_det["top_type"]] += 1
        st["v44_placement_dist"][v44_det["pair_placement"]] += 1
        st["v44_bot_suit_dist"][v44_det["bot_suit"]] += 1
        st["v44_mid_suited_n"] += int(v44_det["mid_suited"])
        st["v44_bot_pair_high_dist"][v44_det["bot_pair_high"]] += 1
        st["v44_mid_high_dist"][v44_det["mid_high"]] += 1
        st["v44_bot_run_dist"][v44_det["bot_run"]] += 1

        rs = rank_stats[pair_rank]
        rs["n"] += 1
        rs["sum_regret"] += regret
        if v44_idx == oracle_idx:
            rs["n_match"] += 1
        if v44_class != or_class:
            rs["mismatch"][(v44_class, or_class)] += 1
            rs["mismatch_regret"][(v44_class, or_class)] += regret
        rs["v44_class_dist"][v44_class] += 1
        rs["oracle_class_dist"][or_class] += 1
        rank_cell_n[pair_rank][cell] += 1
        rank_cell_regret[pair_rank][cell] += regret

        if (k + 1) % 100_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ===========================================================
    # Per-pair-rank residual stratification
    # ===========================================================
    print("=" * 100)
    print("PAIR1: PER-PAIR-RANK RESIDUAL STRATIFICATION (v44_dt vs oracle)")
    print("=" * 100)
    print(f"  {'pair':>4} {'n_hands':>9} {'pct_opt':>8} {'mean_reg':>10} "
          f"{'wg_contrib':>12}")
    for pair_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[pair_rank]
        if rs["n"] == 0:
            continue
        pct_opt = 100 * rs["n_match"] / rs["n"]
        mean_reg = rs["sum_regret"] / rs["n"] * EV_TO_DOL * 1000
        wg = rs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {RANK_CHAR[pair_rank]:>4} {rs['n']:>9,} {pct_opt:>7.2f}% "
              f"${mean_reg:>+8.1f} ${wg:>+10.2f}")

    print("\n  Per-pair-rank top-10 mismatch classes:")
    for pair_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[pair_rank]
        if not rs["mismatch_regret"]:
            continue
        print(f"\n  ── pair_rank = {RANK_CHAR[pair_rank]} ──")
        ranked = sorted(rs["mismatch_regret"].items(), key=lambda x: -x[1])
        for (vc, oc), reg in ranked[:10]:
            nn = rs["mismatch"][(vc, oc)]
            mean_reg = reg / nn * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"    {vc:<22} -> {oc:<22} n={nn:>7,} mean=${mean_reg:>+7.1f} "
                  f"wg=${wg:>+7.2f}")

    print("\n  Per-pair-rank class distribution (v44 pick % vs oracle pick %):")
    for pair_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[pair_rank]
        if rs["n"] == 0:
            continue
        print(f"\n  ── pair_rank = {RANK_CHAR[pair_rank]}  (n={rs['n']:,}) ──")
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
    print("PAIR2: STRUCTURAL CELL CROSS-TABULATION (per pair_rank x cell)")
    print("=" * 100)
    print(f"  {'pair':>4} {'cell':<18} {'n_hands':>9} {'pct_of_rank':>12} "
          f"{'wg_contrib':>12} {'mean_reg':>10}")
    for pair_rank in sorted(rank_stats.keys(), reverse=True):
        n_total = rank_stats[pair_rank]["n"]
        for cell in CELLS_ORDER:
            n_in_cell = rank_cell_n[pair_rank].get(cell, 0)
            if n_in_cell == 0:
                continue
            reg = rank_cell_regret[pair_rank].get(cell, 0.0)
            pct_of_rank = 100 * n_in_cell / n_total
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            mean_reg = reg / n_in_cell * EV_TO_DOL * 1000
            print(f"  {RANK_CHAR[pair_rank]:>4} {cell:<18} {n_in_cell:>9,} "
                  f"{pct_of_rank:>11.1f}% ${wg:>+10.2f} ${mean_reg:>+8.1f}")

    # ===========================================================
    # Oracle's pick profile per (pair_rank x cell)
    # ===========================================================
    print("\n" + "=" * 100)
    print("PAIR3: ORACLE'S PICK PROFILE PER (pair_rank x cell)")
    print("=" * 100)
    for pair_rank in sorted(rank_stats.keys(), reverse=True):
        for cell in CELLS_ORDER:
            st = cell_stats.get((pair_rank, cell), None)
            if st is None or st["n"] == 0:
                continue
            nn = st["n"]
            mean_reg = st["sum_regret"] / nn * EV_TO_DOL * 1000
            pct_match = 100 * st["n_match"] / nn
            print(f"\n  ── pair_rank={RANK_CHAR[pair_rank]}  cell={cell}  "
                  f"n={nn:,}  pct_opt={pct_match:.1f}%  mean_reg=${mean_reg:+.1f} ──")
            placement_summary = ", ".join(
                f"{p}:{100*c/nn:.0f}%"
                for p, c in sorted(st["or_placement_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    oracle PLACEMENT:  {placement_summary}")
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
            # v44 same
            v44_placement_summary = ", ".join(
                f"{p}:{100*c/nn:.0f}%"
                for p, c in sorted(st["v44_placement_dist"].items(), key=lambda x: -x[1])
            )
            print(f"    v44    PLACEMENT:  {v44_placement_summary}")
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
            "pair_rank": pa.array(arr_pair_rank, type=pa.int8()),
            "max_sing_rank": pa.array(arr_max_sing, type=pa.int8()),
            "n_PBOT_DS": pa.array(arr_n_PBOT_DS, type=pa.int8()),
            "n_PBOT_DS_w_msmid_maxtop": pa.array(arr_n_PBOT_DS_w_msmid_maxtop, type=pa.int8()),
            "n_PMID_DS": pa.array(arr_n_PMID_DS, type=pa.int8()),
            "n_PMID_DS_w_maxtop": pa.array(arr_n_PMID_DS_w_maxtop, type=pa.int8()),
            "n_PMID_SS_w_maxtop": pa.array(arr_n_PMID_SS_w_maxtop, type=pa.int8()),
            "best_PBOT_mid_high": pa.array(arr_best_PBOT_mid_high, type=pa.int8()),
            "best_PMID_bot_pair_high": pa.array(arr_best_PMID_bot_pair_high, type=pa.int8()),
            "cell_idx": pa.array(arr_cell, type=pa.int8()),
            "v44_idx": pa.array(arr_v44_idx, type=pa.int16()),
            "oracle_idx": pa.array(arr_oracle_idx, type=pa.int16()),
            "regret": pa.array(arr_regret, type=pa.float32()),
            "v44_placement": pa.array(arr_v44_placement, type=pa.int8()),
            "v44_top_type": pa.array(arr_v44_top_type, type=pa.int8()),
            "v44_top_rank": pa.array(arr_v44_top_rank, type=pa.int8()),
            "v44_bot_suit": pa.array(arr_v44_bot_suit, type=pa.int8()),
            "v44_mid_suited": pa.array(arr_v44_mid_suited, type=pa.bool_()),
            "v44_mid_high": pa.array(arr_v44_mid_high, type=pa.int8()),
            "v44_bot_pair_high": pa.array(arr_v44_bot_pair_high, type=pa.int8()),
            "v44_bot_run": pa.array(arr_v44_bot_run, type=pa.int8()),
            "or_placement": pa.array(arr_or_placement, type=pa.int8()),
            "or_top_type": pa.array(arr_or_top_type, type=pa.int8()),
            "or_top_rank": pa.array(arr_or_top_rank, type=pa.int8()),
            "or_bot_suit": pa.array(arr_or_bot_suit, type=pa.int8()),
            "or_mid_suited": pa.array(arr_or_mid_suited, type=pa.bool_()),
            "or_mid_high": pa.array(arr_or_mid_high, type=pa.int8()),
            "or_bot_pair_high": pa.array(arr_or_bot_pair_high, type=pa.int8()),
            "or_bot_run": pa.array(arr_or_bot_run, type=pa.int8()),
        })
        pq.write_table(table, OUT_PARQUET, compression="zstd",
                       compression_level=3, write_statistics=True)
        sz = OUT_PARQUET.stat().st_size / 1024 / 1024
        print(f"  wrote {sz:.2f} MB")

        # Summary JSON: aggregate stats keyed by (pair_rank, cell).
        summary = {
            "n_pair_hands": int(n),
            "n_total_grid": N_TOTAL_GRID,
            "cells_order": CELLS_ORDER,
            "rank_stats": {},
            "cell_stats": {},
            "rank_cell_n": {},
            "rank_cell_regret_wg": {},
        }
        for pair_rank, rs in rank_stats.items():
            summary["rank_stats"][str(pair_rank)] = {
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
        for (pair_rank, cell), st in cell_stats.items():
            key = f"{pair_rank}|{cell}"
            summary["cell_stats"][key] = {
                "n": int(st["n"]),
                "sum_regret": float(st["sum_regret"]),
                "n_match": int(st["n_match"]),
                "wg_contrib_dollars": float(st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                "mean_regret_dollars": float(st["sum_regret"] / st["n"] * EV_TO_DOL * 1000),
                "pct_opt": float(100 * st["n_match"] / st["n"]),
                "or_placement_dist": dict(st["or_placement_dist"]),
                "or_top_type_dist": dict(st["or_top_type_dist"]),
                "or_top_rank_dist": dict(st["or_top_rank_dist"]),
                "or_bot_suit_dist": dict(st["or_bot_suit_dist"]),
                "or_mid_suited_pct": float(100 * st["or_mid_suited_n"] / st["n"]),
                "or_mid_high_dist": dict(st["or_mid_high_dist"]),
                "v44_placement_dist": dict(st["v44_placement_dist"]),
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
        for pair_rank, cell_n in rank_cell_n.items():
            summary["rank_cell_n"][str(pair_rank)] = dict(cell_n)
            summary["rank_cell_regret_wg"][str(pair_rank)] = {
                cell: float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                for cell, reg in rank_cell_regret[pair_rank].items()
            }
        with open(OUT_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
