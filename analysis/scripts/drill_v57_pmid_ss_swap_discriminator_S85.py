"""
Session 85 Phase B+ — discriminator drill for LOW × PMID_SS_MAXTOP swap choices.

CONTEXT (Phase B in same session)
---------------------------------
S85 Phase B drill showed: under PRODUCTION v57, LOW × PMID_SS_MAXTOP has
$15.33/1000h whole-grid residual leak (vs $25.16 under v44_dt; only 39% of
v44's leak closed by v52 — *much less* than S84's PMID_DS_MAXTOP cell where
v52 closed 78%). The cell passes the early-out ceiling check.

v57 places PAIR 100% in MID on this cell. The dominant mismatches are:
  STRUCTURE bucket:
    v57=PMID_tmax_SS → oracle=PBOT_tmax_SS_mu  : 6,508 hands  $2.84/1000h
    v57=PMID_tmax_SS → oracle=PBOT_tmax_SS_ms  : 5,566 hands  $2.79
    v57=PMID_tmax_SS → oracle=PMID_tnomax_31   : 6,295 hands  $2.64
    v57=PMID_tmax_SS → oracle=PMID_tnomax_SS   : 4,130 hands  $1.70
    v57=PMID_tmax_SS → oracle=PBOT_tnomax_SS_ms: 2,044 hands  $1.22
    ...

Two structural swap directions worth probing:

  DIRECTION 1 — SWAP_TO_PBOT_SS:
    v57 keeps PMID_tmax_SS but oracle wants pair-in-bot with SS bot.
    Variants: PBOT_tmax_SS_mu, PBOT_tmax_SS_ms, PBOT_tnomax_SS_ms.
    Combined: ~14,000 hands, ~$6.85/1000h whole-grid.

  DIRECTION 2 — SWAP_TO_PMID_TNOMAX:
    v57 keeps PMID_tmax_SS but oracle wants pair-in-mid with NON-max on top.
    Variants: PMID_tnomax_31 (mixed bot suits), PMID_tnomax_SS.
    Combined: ~10,400 hands, ~$4.34/1000h.

The PBOT side-channel is the larger lever, but might be harder to discriminate
(requires recognizing when pair-in-bot's flush+pair structure beats keeping
mid-pair). The TNOMAX side might have a sharper feature (analogous to S84's
top_alt_rank).

POPULATIONS
-----------
  KEEP_PMID_TMAX        : v57=PMID_tmax_SS AND oracle=PMID_tmax_SS
  SWAP_TO_PBOT_SS       : v57=PMID_tmax_SS AND oracle starts with "PBOT_*_SS_"
                          (combines _mu and _ms, tmax and tnomax)
  SWAP_TO_PMID_TNOMAX   : v57=PMID_tmax_SS AND oracle starts with "PMID_tnomax_"
                          (combines _SS and _31)
  OTHER                 : any other combination

CANDIDATE DISCRIMINATORS
------------------------
  pair_rank, max_sing, second_max, third_max, max_gap (max-second_max)
  best_pmid_ss_bph_tmax    : best PMID_tmax_SS bot_pair_high
  best_pmid_ss_bph_tnomax  : best PMID_tnomax_SS bot_pair_high (-1 if none)
  best_pmid_31_bph_tnomax  : best PMID_tnomax_31 bot_pair_high (-1 if none)
  best_pbot_ss_bph_tmax    : best PBOT_SS_tmax bot_pair_high (-1 if none)
  best_pbot_ss_bph_tmax_ms : same restricted to mid same-suited
  pbot_advantage           : best_pbot_ss_bph_tmax - best_pmid_ss_bph_tmax
  tnomax_advantage         : best of (pmid_ss_bph_tnomax, pmid_31_bph_tnomax)
                             minus best_pmid_ss_bph_tmax
  n_sing_in_pair_suit      : how many of 5 singletons share suit with pair
  max_sing_in_pair_suit    : is max_sing's suit one of pair's two suits?
  top_alt_rank             : rank of best 2nd-singleton (would-be top under tnomax)

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v57_pmid_ss_swap_discriminator_S85.py
"""
from __future__ import annotations

import json
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402

from drill_pair_v44_S66 import (  # noqa: E402
    compute_pair_structural,
    classify_pick_pair,
    CELLS_ORDER,
    RANK_CHAR,
)

from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session85"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "drill_v57_pmid_ss_swap_discriminator_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}
CELL_IDX_PMID_SS_MAXTOP = CELLS_ORDER.index("PMID_SS_MAXTOP")  # 4


def compute_pmid_ss_swap_features(hand_bytes, struct):
    """Enumerate alternative configs and compute discriminator features.

    The cell PMID_SS_MAXTOP precondition guarantees:
      - n_PBOT_DS == 0   (no DS bot from pair-in-bot)
      - n_PMID_DS == 0   (no DS bot from pair-in-mid)
      - n_PMID_SS_w_maxtop > 0  (PMID with SS bot and max on top exists)

    We enumerate:
      - All PMID variants (top = each of 5 singletons), classify bot suit
        pattern (DS / SS / 31 / RB / 4f), record bot_pair_high.
        For SS bot: bot_pair_high is the rank of the higher of the suited pair.
        For DS bot: max(higher_of_each_suit_pair). But n_PMID_DS==0 here.
        For 31 bot: the rank of the higher card in the suited triple.

      - All PBOT variants (bot = pair + 2 singletons). Classify bot suit
        pattern. For PBOT_SS: bot_pair_high is the higher of the suited pair.
        Also record whether mid (2 remaining singletons) is same-suited.

    Returns dict with:
      best_pmid_ss_bph_tmax     : best PMID_tmax_SS bot_pair_high
      best_pmid_ss_bph_tnomax   : best PMID_tnomax_SS bot_pair_high (-1)
      best_pmid_31_bph_tnomax   : best PMID_tnomax_31 bot_pair_high (-1)
      best_pmid_31_bph_tmax     : best PMID_tmax_31 bot_pair_high (-1)
      best_pbot_ss_bph_tmax     : best PBOT_SS_tmax bot_pair_high
      best_pbot_ss_bph_tmax_ms  : best PBOT_SS_tmax_ms bot_pair_high
      pbot_advantage            : best_pbot_ss_bph_tmax - best_pmid_ss_bph_tmax
      tnomax_advantage          : best of tnomax PMID bphs - best_pmid_ss_bph_tmax
      top_alt_rank              : second-highest singleton's rank (would-be top
                                  under tnomax)
      n_sing_in_pair_suit       : count of singletons sharing pair's suits
      max_sing_in_pair_suit     : 1 if max_sing's suit is one of pair's suits
      n_pbot_ss_tmax_ms         : count of PBOT_SS configs with max-on-top + mid_ms
      n_pbot_ss_tmax_mu         : count of PBOT_SS configs with max-on-top + mid_mu
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    sing_pos = list(struct["sing_pos"])
    sing_ranks = [int(ranks[p]) for p in sing_pos]
    sing_suits = [int(suits[p]) for p in sing_pos]
    pair_suits = struct["pair_suits"]
    sa, sb = pair_suits
    pair_rank = int(struct["pair_rank"])
    max_sing_rank = int(struct["max_sing_rank"])
    max_sing_local = sing_ranks.index(max_sing_rank)

    # PMID enumeration: for each top_local, classify bot suit pattern.
    best_pmid_ss_bph_tmax = -1
    best_pmid_ss_bph_tnomax = -1
    best_pmid_31_bph_tnomax = -1
    best_pmid_31_bph_tmax = -1

    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
        is_DS = (cnt == [2, 2])
        is_SS = (cnt == [2, 1, 1])
        is_31 = (cnt == [3, 1])
        # is_4f = (cnt == [4]); is_RB = (cnt == [1,1,1,1])  # unused below

        if is_SS:
            # Find the suited-pair (the suit appearing twice).
            by_suit = defaultdict(list)
            for k in bot_locals:
                by_suit[sing_suits[k]].append(sing_ranks[k])
            for s, rs in by_suit.items():
                if len(rs) == 2:
                    bph = max(rs)
                    if top_local == max_sing_local:
                        best_pmid_ss_bph_tmax = max(best_pmid_ss_bph_tmax, bph)
                    else:
                        best_pmid_ss_bph_tnomax = max(best_pmid_ss_bph_tnomax, bph)
        elif is_31:
            # Find the triple suit.
            by_suit = defaultdict(list)
            for k in bot_locals:
                by_suit[sing_suits[k]].append(sing_ranks[k])
            for s, rs in by_suit.items():
                if len(rs) == 3:
                    bph = max(rs)  # rank of higher of triple is "pair_high"
                    if top_local == max_sing_local:
                        best_pmid_31_bph_tmax = max(best_pmid_31_bph_tmax, bph)
                    else:
                        best_pmid_31_bph_tnomax = max(best_pmid_31_bph_tnomax, bph)
        # is_DS impossible here (cell precondition).

    # PBOT enumeration: bot = pair + sing_i + sing_j. Top = one of remaining,
    # mid = the other two remaining. We want PBOT_SS specifically (2+1+1
    # bot suit pattern).
    best_pbot_ss_bph_tmax = -1
    best_pbot_ss_bph_tmax_ms = -1
    n_pbot_ss_tmax_ms = 0
    n_pbot_ss_tmax_mu = 0

    for i in range(5):
        for j in range(i + 1, 5):
            # bot suits: (sa, sb, suit_i, suit_j)
            bot_suit_arr = [sa, sb, sing_suits[i], sing_suits[j]]
            cnt = sorted(Counter(bot_suit_arr).values(), reverse=True)
            if cnt != [2, 1, 1]:
                continue
            # PBOT_SS achievable. Find the suited pair to compute bph.
            by_suit = defaultdict(list)
            for r, s in [(pair_rank, sa), (pair_rank, sb),
                         (sing_ranks[i], sing_suits[i]),
                         (sing_ranks[j], sing_suits[j])]:
                by_suit[s].append(r)
            local_bph = -1
            for s, rs in by_suit.items():
                if len(rs) == 2:
                    local_bph = max(local_bph, max(rs))

            remaining = [k for k in range(5) if k not in (i, j)]
            assert len(remaining) == 3

            # Iterate top choice over remaining
            for t_idx in range(3):
                top_local = remaining[t_idx]
                mid_locals = [remaining[k] for k in range(3) if k != t_idx]
                mid_ms = sing_suits[mid_locals[0]] == sing_suits[mid_locals[1]]
                if top_local == max_sing_local:
                    # tmax variant
                    best_pbot_ss_bph_tmax = max(best_pbot_ss_bph_tmax, local_bph)
                    if mid_ms:
                        best_pbot_ss_bph_tmax_ms = max(
                            best_pbot_ss_bph_tmax_ms, local_bph
                        )
                        n_pbot_ss_tmax_ms += 1
                    else:
                        n_pbot_ss_tmax_mu += 1

    # top_alt_rank: second-highest singleton (would be top under tnomax)
    sorted_ranks = sorted(sing_ranks, reverse=True)
    top_alt_rank = int(sorted_ranks[1]) if len(sorted_ranks) > 1 else 0

    # Singletons in pair-suit count
    n_sing_in_pair_suit = sum(1 for s in sing_suits if s in (sa, sb))
    max_sing_in_pair_suit = 1 if sing_suits[max_sing_local] in (sa, sb) else 0

    pbot_advantage = (best_pbot_ss_bph_tmax - best_pmid_ss_bph_tmax
                      if best_pbot_ss_bph_tmax >= 0 else -99)
    best_tnomax_bph = max(best_pmid_ss_bph_tnomax, best_pmid_31_bph_tnomax)
    tnomax_advantage = (best_tnomax_bph - best_pmid_ss_bph_tmax
                        if best_tnomax_bph >= 0 else -99)

    return {
        "best_pmid_ss_bph_tmax": int(best_pmid_ss_bph_tmax),
        "best_pmid_ss_bph_tnomax": int(best_pmid_ss_bph_tnomax),
        "best_pmid_31_bph_tnomax": int(best_pmid_31_bph_tnomax),
        "best_pmid_31_bph_tmax": int(best_pmid_31_bph_tmax),
        "best_pbot_ss_bph_tmax": int(best_pbot_ss_bph_tmax),
        "best_pbot_ss_bph_tmax_ms": int(best_pbot_ss_bph_tmax_ms),
        "pbot_advantage": int(pbot_advantage),
        "tnomax_advantage": int(tnomax_advantage),
        "top_alt_rank": int(top_alt_rank),
        "n_sing_in_pair_suit": int(n_sing_in_pair_suit),
        "max_sing_in_pair_suit": int(max_sing_in_pair_suit),
        "n_pbot_ss_tmax_ms": int(n_pbot_ss_tmax_ms),
        "n_pbot_ss_tmax_mu": int(n_pbot_ss_tmax_mu),
    }


def classify_pop(v57_lbl, or_lbl):
    """Map (v57_class, oracle_class) to one of the target populations."""
    if v57_lbl != "PMID_tmax_SS":
        # v57 didn't pick the default config — bucket as OTHER
        return "OTHER"
    if or_lbl == "PMID_tmax_SS":
        return "KEEP_PMID_TMAX"
    # PBOT_*_SS_* (any PBOT with SS bot)
    parts = or_lbl.split("_")
    if parts[0] == "PBOT" and len(parts) >= 3 and parts[2] == "SS":
        return "SWAP_TO_PBOT_SS"
    # PMID_tnomax_* (any tnomax variant under PMID)
    if or_lbl.startswith("PMID_tnomax_"):
        return "SWAP_TO_PMID_TNOMAX"
    return "OTHER"


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx", "regret"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_SS_MAXTOP) & np.isin(
        df["pair_rank"], list(LOW_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    target_pair_rank = df["pair_rank"][mask].astype(np.int64)
    n = len(target_canonical_ids)
    print(f"  LOW × PMID_SS_MAXTOP: {n:,} hands", flush=True)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs

    print(f"running v57 + classifying + extracting features ...", flush=True)
    t0 = time.time()

    pop_records = []
    pop_n = Counter()
    pop_wg = defaultdict(float)

    # Track PBOT swap sub-distribution to know how big each variant is.
    pbot_swap_class_counter = Counter()
    pmid_tnomax_swap_class_counter = Counter()

    for i in range(n):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        or_pick = int(target_oracle_idx[i])
        v57_pick = int(strategy_v57_lo_pair_defensive(hand_bytes))

        struct = compute_pair_structural(hand_bytes)
        feats = setting_features_from_bytes(hand_bytes)
        v57_det = classify_pick_pair(hand_bytes, feats, v57_pick, struct)
        or_det = classify_pick_pair(hand_bytes, feats, or_pick, struct)
        v57_lbl = v57_det["class_label"]
        or_lbl = or_det["class_label"]

        evs_row = evs[cid]
        regret = max(0.0, float(evs_row[or_pick]) - float(evs_row[v57_pick]))

        pop = classify_pop(v57_lbl, or_lbl)
        pop_n[pop] += 1
        pop_wg[pop] += regret

        if pop == "SWAP_TO_PBOT_SS":
            pbot_swap_class_counter[or_lbl] += 1
        elif pop == "SWAP_TO_PMID_TNOMAX":
            pmid_tnomax_swap_class_counter[or_lbl] += 1

        if pop == "OTHER":
            continue

        swap_feats = compute_pmid_ss_swap_features(hand_bytes, struct)

        max_sing = int(struct["max_sing_rank"])
        sing_ranks_list = list(struct["sing_ranks"])
        sorted_sing = sorted(sing_ranks_list, reverse=True)
        second_max = int(sorted_sing[1]) if len(sorted_sing) > 1 else 0
        third_max = int(sorted_sing[2]) if len(sorted_sing) > 2 else 0
        pair_rank = int(struct["pair_rank"])
        max_gap = max_sing - second_max

        rec = {
            "pop": pop,
            "v57_lbl": v57_lbl,
            "or_lbl": or_lbl,
            "regret": regret,
            "pair_rank": pair_rank,
            "max_sing": max_sing,
            "second_max": second_max,
            "third_max": third_max,
            "max_gap": max_gap,
        }
        rec.update(swap_feats)
        pop_records.append(rec)

        if (i + 1) % 20_000 == 0:
            print(f"  scanned {i+1:,}/{n:,}", flush=True)

    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    # --- Population summary ---
    print()
    print(f"=" * 80)
    print(f"Population summary (within LOW × PMID_SS_MAXTOP, n={n:,}):")
    print(f"=" * 80)
    print(f"  {'pop':<24}{'n':>10}{'pct':>8}{'$/1000h':>12}")
    pop_order = ["KEEP_PMID_TMAX", "SWAP_TO_PBOT_SS",
                 "SWAP_TO_PMID_TNOMAX", "OTHER"]
    for pop in pop_order:
        n_p = pop_n.get(pop, 0)
        wg_p = pop_wg.get(pop, 0.0) / N_TOTAL_GRID * EV_TO_DOL * 1000
        print(f"  {pop:<24}{n_p:>10,}{n_p/n*100:>7.1f}%{wg_p:>11.2f}")

    print()
    print(f"PBOT swap sub-distribution (oracle classes):")
    for cls, cnt in pbot_swap_class_counter.most_common():
        print(f"  {cls:<28}{cnt:>10,}")
    print()
    print(f"PMID_tnomax swap sub-distribution (oracle classes):")
    for cls, cnt in pmid_tnomax_swap_class_counter.most_common():
        print(f"  {cls:<28}{cnt:>10,}")

    # --- Discriminator means per population ---
    feature_names = ["pair_rank", "max_sing", "second_max", "third_max",
                     "max_gap", "best_pmid_ss_bph_tmax",
                     "best_pmid_ss_bph_tnomax", "best_pmid_31_bph_tnomax",
                     "best_pmid_31_bph_tmax", "best_pbot_ss_bph_tmax",
                     "best_pbot_ss_bph_tmax_ms", "pbot_advantage",
                     "tnomax_advantage", "top_alt_rank",
                     "n_sing_in_pair_suit", "max_sing_in_pair_suit",
                     "n_pbot_ss_tmax_ms", "n_pbot_ss_tmax_mu"]
    target_pops = ["KEEP_PMID_TMAX", "SWAP_TO_PBOT_SS", "SWAP_TO_PMID_TNOMAX"]
    discriminator_tables = {}
    for fname in feature_names:
        means = {}
        medians = {}
        per_pop_vals = {}
        for pop in target_pops:
            vals = [r[fname] for r in pop_records if r["pop"] == pop]
            arr = np.array(vals) if vals else np.array([0])
            means[pop] = float(arr.mean()) if vals else 0.0
            medians[pop] = float(np.median(arr)) if vals else 0.0
            per_pop_vals[pop] = vals
        all_vals = sorted(set().union(*[set(v) for v in per_pop_vals.values()]))
        rows = []
        for v in all_vals:
            row = {"val": v}
            for pop in target_pops:
                row[pop + "_n"] = sum(1 for x in per_pop_vals[pop] if x == v)
            rows.append(row)
        discriminator_tables[fname] = {
            "means": means,
            "medians": medians,
            "rows": rows,
        }

    print()
    print(f"Discriminator candidates — means per population:")
    print(f"  {'feature':<28}" + "".join(f"{p:>20}" for p in target_pops))
    for fname in feature_names:
        d = discriminator_tables[fname]
        print(f"  {fname:<28}" + "".join(
            f"{d['means'][p]:>20.2f}" for p in target_pops))

    # --- Deltas: which feature best separates SWAP from KEEP? ---
    print()
    print(f"Δ(SWAP_TO_PBOT_SS − KEEP_PMID_TMAX): "
          f"signal that v57 should swap to PBOT_SS")
    print(f"  {'feature':<28}{'KEEP':>14}{'SWAP_PBOT':>14}{'Δ':>10}")
    deltas_pbot = []
    for fname in feature_names:
        d = discriminator_tables[fname]
        a = d["means"]["KEEP_PMID_TMAX"]
        b = d["means"]["SWAP_TO_PBOT_SS"]
        delta = b - a
        deltas_pbot.append((fname, delta))
        print(f"  {fname:<28}{a:>14.2f}{b:>14.2f}{delta:>+10.2f}")

    print()
    print(f"Δ(SWAP_TO_PMID_TNOMAX − KEEP_PMID_TMAX): "
          f"signal that v57 should swap to PMID_tnomax")
    print(f"  {'feature':<28}{'KEEP':>14}{'SWAP_TNOMAX':>14}{'Δ':>10}")
    deltas_tnomax = []
    for fname in feature_names:
        d = discriminator_tables[fname]
        a = d["means"]["KEEP_PMID_TMAX"]
        b = d["means"]["SWAP_TO_PMID_TNOMAX"]
        delta = b - a
        deltas_tnomax.append((fname, delta))
        print(f"  {fname:<28}{a:>14.2f}{b:>14.2f}{delta:>+10.2f}")

    # --- Top-3 features per direction: per-value swap rate ---
    deltas_pbot.sort(key=lambda x: -abs(x[1]))
    deltas_tnomax.sort(key=lambda x: -abs(x[1]))

    print()
    print(f"Top-3 features for SWAP_TO_PBOT_SS (per-value distribution):")
    for fname, delta in deltas_pbot[:3]:
        print(f"\n  === {fname}  (Δ = {delta:+.2f}) ===")
        d = discriminator_tables[fname]
        print(f"  {'val':>6}{'KEEP':>12}{'SWAP_PBOT':>12}{'swap_pct':>10}")
        for r in d["rows"]:
            keep = r["KEEP_PMID_TMAX_n"]
            swap = r["SWAP_TO_PBOT_SS_n"]
            tot = keep + swap
            swap_pct = swap / max(tot, 1) * 100
            print(f"  {r['val']:>6}{keep:>12,}{swap:>12,}{swap_pct:>9.1f}%")

    print()
    print(f"Top-3 features for SWAP_TO_PMID_TNOMAX (per-value distribution):")
    for fname, delta in deltas_tnomax[:3]:
        print(f"\n  === {fname}  (Δ = {delta:+.2f}) ===")
        d = discriminator_tables[fname]
        print(f"  {'val':>6}{'KEEP':>12}{'SWAP_TNOMAX':>12}{'swap_pct':>10}")
        for r in d["rows"]:
            keep = r["KEEP_PMID_TMAX_n"]
            swap = r["SWAP_TO_PMID_TNOMAX_n"]
            tot = keep + swap
            swap_pct = swap / max(tot, 1) * 100
            print(f"  {r['val']:>6}{keep:>12,}{swap:>12,}{swap_pct:>9.1f}%")

    # --- Persist ---
    out = {
        "session": 85,
        "phase": "B+",
        "cell": "LOW × PMID_SS_MAXTOP",
        "n_cell_hands": n,
        "pop_n": dict(pop_n),
        "pop_wg_dollars_per_1000h": {
            k: v / N_TOTAL_GRID * EV_TO_DOL * 1000 for k, v in pop_wg.items()
        },
        "pbot_swap_class_dist": dict(pbot_swap_class_counter.most_common()),
        "pmid_tnomax_swap_class_dist": dict(
            pmid_tnomax_swap_class_counter.most_common()),
        "n_pop_records_classified": len(pop_records),
        "discriminator_tables": discriminator_tables,
        "deltas_for_swap_to_pbot": deltas_pbot,
        "deltas_for_swap_to_tnomax": deltas_tnomax,
        "low_pair_ranks": sorted(LOW_PAIR_RANKS),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
