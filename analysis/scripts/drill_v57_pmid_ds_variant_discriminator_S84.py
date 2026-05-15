"""
Session 84 Phase B+ — discriminator for the within-PMID-DS variant choice.

CONTEXT (from Phase B in same session):
  In LOW × PMID_DS_MAXTOP, v57 places pair-in-mid 100% of the time (PMID),
  but its choice between PMID_tmax_DS (max on top, DS bot excluding max) and
  PMID_tnomax_DS (max in bot's DS, non-max on top) is suboptimal:

    v57 = PMID_tnomax_DS, oracle = PMID_tmax_DS   :  4,312 hands  $2.41/1000h
    v57 = PMID_tmax_DS,   oracle = PMID_tnomax_DS :  6,054 hands  $2.05/1000h
    v57 = PMID_tmax_DS,   oracle = PBOT_tmax_SS_ms:  1,733 hands  $0.53/1000h

  Within-PMID-DS variant swap-target leak: ~$4.46/1000h whole-grid bidirectional.
  PBOT side-channel: ~$1.5/1000h.
  Total cell leak: $7.24/1000h.

  This is materially different from S83's PMID_DS_NOMAXTOP cell, where the
  swap was unidirectional (tmax_SS → tnomax_DS, $40/1000h leak). Here both
  configs are DS — the choice is which DS to take.

QUESTION:
  What per-hand feature DISCRIMINATES the two swap directions?
    Direction TO_TMAX:    v57 picks tnomax_DS but oracle wants tmax_DS
    Direction TO_TNOMAX:  v57 picks tmax_DS but oracle wants tnomax_DS
    KEEP populations:     v57 = oracle within each variant

POPULATIONS:
  KEEP_TMAX     : v57=PMID_tmax_DS    AND oracle=PMID_tmax_DS
  KEEP_TNOMAX   : v57=PMID_tnomax_DS  AND oracle=PMID_tnomax_DS
  SWAP_TO_TMAX  : v57=PMID_tnomax_DS  AND oracle=PMID_tmax_DS
  SWAP_TO_TNOMAX: v57=PMID_tmax_DS    AND oracle=PMID_tnomax_DS
  OTHER         : any other label combination (PBOT, SPLIT, SS, 31, etc.)

CANDIDATE DISCRIMINATORS:
  D1 — pair_rank (2..7)
  D2 — max_sing (rank of highest non-pair card)
  D3 — second_max (rank of 2nd-highest non-pair card)
  D4 — max_gap = max_sing − second_max
  D5 — best_bph_tmax    : bot_pair_high of best DS config with max in top
  D6 — best_bph_tnomax  : bot_pair_high of best DS config with max in bot
  D7 — bph_advantage    : best_bph_tnomax − best_bph_tmax  (how much better
                          is the DS-bot under max-in-bot vs max-on-top)
  D8 — top_alternative  : rank of the singleton that would sit on top under
                          the best tnomax_DS config (i.e., second-best
                          singleton if max goes to bot)

For each candidate, report KEEP/SWAP distributions (mean, per-value histogram).

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v57_pmid_ds_variant_discriminator_S84.py
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

OUT_DIR = ROOT / "data" / "session84"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "drill_v57_pmid_ds_variant_discriminator_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}
CELL_IDX_PMID_DS_MAXTOP = CELLS_ORDER.index("PMID_DS_MAXTOP")  # 2


def compute_pmid_ds_variant_bphs(struct):
    """Compute the best bot_pair_high under each variant.

    Returns dict with:
      best_bph_tmax     : best bot_pair_high among DS configs where max is on top
                          (-1 if no such config)
      best_bph_tnomax   : best bot_pair_high among DS configs where max is in bot
                          (-1 if no such config)
      top_alt_rank      : rank of leftover (top) singleton under the best
                          tnomax_DS config; the "alternative top" we'd put on
                          top instead of max_sing. (-1 if no tnomax DS config)
      n_ds_tmax         : count of DS configs with max on top
      n_ds_tnomax       : count of DS configs with max in bot
    """
    sing_ranks = list(struct["sing_ranks"])
    # Reconstruct sing_suits from struct (which doesn't store them directly).
    # We can't — struct doesn't expose sing_suits. Recompute from sing_pos
    # would require hand_bytes. The caller must pass them.
    raise NotImplementedError("Use compute_pmid_ds_variant_bphs_from_hand")


def compute_pmid_ds_variant_bphs_from_hand(hand_bytes, struct):
    """Enumerate PMID DS configs and split by tmax vs tnomax.

    For each (top_local, bot_locals) where bot_suits form 2+2 pattern:
      - if top_local == max_sing_local → tmax_DS
      - else → tnomax_DS
    Compute bot_pair_high for each, keep best per variant.
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    sing_pos = list(struct["sing_pos"])
    sing_ranks = [int(ranks[p]) for p in sing_pos]
    sing_suits = [int(suits[p]) for p in sing_pos]
    max_sing_rank = struct["max_sing_rank"]
    max_sing_local = sing_ranks.index(max_sing_rank)

    best_bph_tmax = -1
    best_bph_tnomax = -1
    top_alt_rank = -1  # rank of top under best tnomax_DS
    n_ds_tmax = 0
    n_ds_tnomax = 0

    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        # bot_pair_high
        by_suit = defaultdict(list)
        for k in bot_locals:
            by_suit[sing_suits[k]].append(sing_ranks[k])
        local_pair_high = 0
        for sgrp, rs in by_suit.items():
            if len(rs) >= 2:
                hi = max(rs)
                if hi > local_pair_high:
                    local_pair_high = hi
        if top_local == max_sing_local:
            n_ds_tmax += 1
            if local_pair_high > best_bph_tmax:
                best_bph_tmax = local_pair_high
        else:
            n_ds_tnomax += 1
            if local_pair_high > best_bph_tnomax:
                best_bph_tnomax = local_pair_high
                top_alt_rank = sing_ranks[top_local]

    return {
        "best_bph_tmax": int(best_bph_tmax),
        "best_bph_tnomax": int(best_bph_tnomax),
        "top_alt_rank": int(top_alt_rank),
        "n_ds_tmax": n_ds_tmax,
        "n_ds_tnomax": n_ds_tnomax,
    }


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx", "regret"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_DS_MAXTOP) & np.isin(
        df["pair_rank"], list(LOW_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    target_pair_rank = df["pair_rank"][mask].astype(np.int64)
    n = len(target_canonical_ids)
    print(f"  LOW × PMID_DS_MAXTOP: {n:,} hands", flush=True)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs

    print(f"running v57 + classifying + extracting features ...", flush=True)
    t0 = time.time()

    pop_records = []  # each item: {pop, features dict, regret}
    pop_n = Counter()
    pop_wg = defaultdict(float)

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

        # Population labels
        if v57_lbl == "PMID_tmax_DS" and or_lbl == "PMID_tmax_DS":
            pop = "KEEP_TMAX"
        elif v57_lbl == "PMID_tnomax_DS" and or_lbl == "PMID_tnomax_DS":
            pop = "KEEP_TNOMAX"
        elif v57_lbl == "PMID_tnomax_DS" and or_lbl == "PMID_tmax_DS":
            pop = "SWAP_TO_TMAX"
        elif v57_lbl == "PMID_tmax_DS" and or_lbl == "PMID_tnomax_DS":
            pop = "SWAP_TO_TNOMAX"
        else:
            pop = "OTHER"

        pop_n[pop] += 1
        pop_wg[pop] += regret

        # Skip feature extraction for OTHER (we want to characterize the four
        # focused populations only — but keep n+wg accounting above).
        if pop == "OTHER":
            continue

        variant = compute_pmid_ds_variant_bphs_from_hand(hand_bytes, struct)

        max_sing = int(struct["max_sing_rank"])
        sing_ranks = list(struct["sing_ranks"])
        sorted_sing = sorted(sing_ranks, reverse=True)
        second_max = int(sorted_sing[1]) if len(sorted_sing) > 1 else 0
        third_max = int(sorted_sing[2]) if len(sorted_sing) > 2 else 0
        pair_rank = int(struct["pair_rank"])
        max_gap = max_sing - second_max
        bph_advantage = (variant["best_bph_tnomax"]
                         - variant["best_bph_tmax"])

        pop_records.append({
            "pop": pop,
            "v57_lbl": v57_lbl,
            "or_lbl": or_lbl,
            "regret": regret,
            "pair_rank": pair_rank,
            "max_sing": max_sing,
            "second_max": second_max,
            "third_max": third_max,
            "max_gap": max_gap,
            "best_bph_tmax": variant["best_bph_tmax"],
            "best_bph_tnomax": variant["best_bph_tnomax"],
            "top_alt_rank": variant["top_alt_rank"],
            "n_ds_tmax": variant["n_ds_tmax"],
            "n_ds_tnomax": variant["n_ds_tnomax"],
            "bph_advantage": bph_advantage,
        })

        if (i + 1) % 30_000 == 0:
            print(f"  scanned {i+1:,}/{n:,}", flush=True)

    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    # --- Population summary ---
    print()
    print(f"=" * 80)
    print(f"Population summary (within LOW × PMID_DS_MAXTOP, n={n:,}):")
    print(f"=" * 80)
    print(f"  {'pop':<18}{'n':>10}{'pct':>8}{'$/1000h':>12}")
    for pop in ["KEEP_TMAX", "KEEP_TNOMAX", "SWAP_TO_TMAX",
                "SWAP_TO_TNOMAX", "OTHER"]:
        n_p = pop_n.get(pop, 0)
        wg_p = pop_wg.get(pop, 0.0) / N_TOTAL_GRID * EV_TO_DOL * 1000
        print(f"  {pop:<18}{n_p:>10,}{n_p/n*100:>7.1f}%{wg_p:>11.2f}")

    # --- Discriminator histograms ---
    feature_names = ["pair_rank", "max_sing", "second_max", "third_max",
                     "max_gap", "best_bph_tmax", "best_bph_tnomax",
                     "top_alt_rank", "n_ds_tmax", "n_ds_tnomax",
                     "bph_advantage"]
    target_pops = ["KEEP_TMAX", "KEEP_TNOMAX", "SWAP_TO_TMAX", "SWAP_TO_TNOMAX"]
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
        # Build per-value table
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

    # Print discriminator means
    print()
    print(f"Discriminator candidates — means per population:")
    print(f"  {'feature':<20}" + "".join(f"{p:>14}" for p in target_pops))
    for fname in feature_names:
        d = discriminator_tables[fname]
        print(f"  {fname:<20}" + "".join(
            f"{d['means'][p]:>14.2f}" for p in target_pops))

    # Print delta (SWAP_TO_X − KEEP_X) for both directions: which feature
    # most distinguishes "swap" from "keep" in each direction?
    print()
    print(f"Δ(SWAP_TO_TMAX − KEEP_TNOMAX): "
          f"signal that v57's tnomax pick should be flipped to tmax")
    print(f"  {'feature':<20}{'KEEP_TNOMAX':>14}{'SWAP_TO_TMAX':>14}{'Δ':>10}")
    deltas_tmax = []
    for fname in feature_names:
        d = discriminator_tables[fname]
        a = d["means"]["KEEP_TNOMAX"]
        b = d["means"]["SWAP_TO_TMAX"]
        delta = b - a
        deltas_tmax.append((fname, delta))
        print(f"  {fname:<20}{a:>14.2f}{b:>14.2f}{delta:>+10.2f}")

    print()
    print(f"Δ(SWAP_TO_TNOMAX − KEEP_TMAX): "
          f"signal that v57's tmax pick should be flipped to tnomax")
    print(f"  {'feature':<20}{'KEEP_TMAX':>14}{'SWAP_TO_TNOMAX':>14}{'Δ':>10}")
    deltas_tnomax = []
    for fname in feature_names:
        d = discriminator_tables[fname]
        a = d["means"]["KEEP_TMAX"]
        b = d["means"]["SWAP_TO_TNOMAX"]
        delta = b - a
        deltas_tnomax.append((fname, delta))
        print(f"  {fname:<20}{a:>14.2f}{b:>14.2f}{delta:>+10.2f}")

    # For top-2 feature in each direction, print per-value distribution
    deltas_tmax.sort(key=lambda x: -abs(x[1]))
    deltas_tnomax.sort(key=lambda x: -abs(x[1]))
    print()
    print(f"Top-2 features for SWAP_TO_TMAX (per-value distribution):")
    for fname, delta in deltas_tmax[:2]:
        print(f"\n  === {fname}  (Δ = {delta:+.2f}) ===")
        d = discriminator_tables[fname]
        print(f"  {'val':>6}{'KEEP_TNOMAX':>14}{'SWAP_TO_TMAX':>14}"
              f"{'swap_pct':>10}")
        for r in d["rows"]:
            keep = r["KEEP_TNOMAX_n"]
            swap = r["SWAP_TO_TMAX_n"]
            tot = keep + swap
            swap_pct = swap / max(tot, 1) * 100
            print(f"  {r['val']:>6}{keep:>14,}{swap:>14,}{swap_pct:>9.1f}%")

    print()
    print(f"Top-2 features for SWAP_TO_TNOMAX (per-value distribution):")
    for fname, delta in deltas_tnomax[:2]:
        print(f"\n  === {fname}  (Δ = {delta:+.2f}) ===")
        d = discriminator_tables[fname]
        print(f"  {'val':>6}{'KEEP_TMAX':>14}{'SWAP_TO_TNOMAX':>14}"
              f"{'swap_pct':>10}")
        for r in d["rows"]:
            keep = r["KEEP_TMAX_n"]
            swap = r["SWAP_TO_TNOMAX_n"]
            tot = keep + swap
            swap_pct = swap / max(tot, 1) * 100
            print(f"  {r['val']:>6}{keep:>14,}{swap:>14,}{swap_pct:>9.1f}%")

    # --- Persist ---
    out = {
        "session": 84,
        "phase": "B+",
        "cell": "LOW × PMID_DS_MAXTOP",
        "n_cell_hands": n,
        "pop_n": dict(pop_n),
        "pop_wg_dollars_per_1000h": {
            k: v / N_TOTAL_GRID * EV_TO_DOL * 1000 for k, v in pop_wg.items()
        },
        "n_pop_records_classified": len(pop_records),
        "discriminator_tables": discriminator_tables,
        "deltas_for_swap_to_tmax": deltas_tmax,
        "deltas_for_swap_to_tnomax": deltas_tnomax,
        "low_pair_ranks": sorted(LOW_PAIR_RANKS),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
