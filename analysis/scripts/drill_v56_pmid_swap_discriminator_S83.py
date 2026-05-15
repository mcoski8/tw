"""
Session 83 Phase B+ — feature discriminator for the LOW pair PMID-swap rule.

CONTEXT (from Phase B in same session):
  In LOW × PMID_DS_NOMAXTOP, v56 picks PMID_tmax_SS or PMID_tmax_31 on
  ~228k hands. Oracle agrees on 118k (MATCH) but wants PMID_tnomax_DS
  on ~63k (the swap target, $40/1000h leak). A blind "always swap" rule
  would break the 80k MATCH hands where v52's max-on-top is correct.

QUESTION:
  What per-hand feature DISCRIMINATES the swap-target hands (Pop B+C)
  from the keep-v52 hands (Pop A, MATCH bucket within v56_class =
  PMID_tmax_SS or PMID_tmax_31 where oracle agrees)?

POPULATIONS:
  Pop A  (KEEP):  v56=PMID_tmax_SS or PMID_tmax_31  AND  oracle_class = v56_class
                  (oracle agrees with v52's max-on-top pick)
  Pop B  (SWAP):  v56=PMID_tmax_SS or PMID_tmax_31  AND  oracle=PMID_tnomax_DS
                  (oracle wants the DS-bot swap; v56 loses regret)

CANDIDATE DISCRIMINATORS (computed per-hand from S66's pair_structural):
  D1 — best_PMID_DS_bot_pair_high (rank of the best bot-pair-high in the
                                   PMID_DS-with-max-in-bot config)
  D2 — max_sing_rank (the max non-pair singleton)
  D3 — second_max_sing_rank (the 2nd-highest non-pair singleton)
  D4 — pair_rank (2..7)
  D5 — max_sing_rank − second_max_sing_rank (gap)
  D6 — best_PMID_DS_bot_pair_high − second_max_sing_rank (DS-bot upgrade
                                                          quality relative
                                                          to alternative top)

For each candidate, report Pop A vs Pop B distribution (mean/median/histogram).
The discriminator that maximally separates the two populations is the rule gate.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v56_pmid_swap_discriminator_S83.py
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
    cell_for_pair_hand,
    classify_pick_pair,
    CELLS_ORDER,
    RANK_CHAR,
)

from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session83"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "drill_v56_pmid_swap_discriminator_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}
CELL_IDX_PMID_DS_NOMAXTOP = CELLS_ORDER.index("PMID_DS_NOMAXTOP")  # 3


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx", "regret"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_DS_NOMAXTOP) & np.isin(
        df["pair_rank"], list(LOW_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    target_pair_rank = df["pair_rank"][mask].astype(np.int64)
    n = len(target_canonical_ids)
    print(f"  LOW × PMID_DS_NOMAXTOP: {n:,} hands", flush=True)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs

    # --- Iterate, classify, accumulate features per hand. ---
    print(f"running v56 + classifying + extracting features ...", flush=True)
    t0 = time.time()

    pop_records = []  # each item: {pop, features dict, regret}
    for i in range(n):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        or_pick = int(target_oracle_idx[i])
        v56_pick = int(strategy_v56_trips_hybrid(hand_bytes))

        struct = compute_pair_structural(hand_bytes)
        feats = setting_features_from_bytes(hand_bytes)
        v56_det = classify_pick_pair(hand_bytes, feats, v56_pick, struct)
        or_det = classify_pick_pair(hand_bytes, feats, or_pick, struct)
        v56_lbl = v56_det["class_label"]
        or_lbl = or_det["class_label"]

        # Filter to populations of interest.
        if v56_lbl not in ("PMID_tmax_SS", "PMID_tmax_31"):
            continue  # outside the dominant v56-pick zone
        evs_row = evs[cid]
        regret = max(0.0, float(evs_row[or_pick]) - float(evs_row[v56_pick]))

        if or_lbl == v56_lbl:
            pop = "KEEP"  # Pop A — oracle agrees with v52 default
        elif or_lbl == "PMID_tnomax_DS":
            pop = "SWAP"  # Pop B — oracle wants DS-bot swap
        else:
            pop = "OTHER"  # different mismatch, not our target swap

        # Extract candidate discriminator features
        max_sing = int(struct["max_sing_rank"])
        sing_ranks = list(struct["sing_ranks"])
        sorted_sing = sorted(sing_ranks, reverse=True)
        second_max_sing = int(sorted_sing[1]) if len(sorted_sing) > 1 else 0
        third_max_sing = int(sorted_sing[2]) if len(sorted_sing) > 2 else 0
        ds_bot_pair_high = int(struct["best_PMID_DS_bot_pair_high"])
        pair_rank = int(struct["pair_rank"])
        max_gap = max_sing - second_max_sing
        ds_upgrade = ds_bot_pair_high - second_max_sing
        ds_upgrade_vs_max = ds_bot_pair_high - max_sing

        # Suit profile of bot in v56's tmax_SS pick: bot has 4 singletons,
        # SS = 2+1+1 pattern. The "pair-high" of the SS bot is its
        # max-suited rank-pair.
        # For v56 = tmax_SS: top is max_sing; bot is 4 non-max-sing singletons.
        # For v56 = tmax_31: similar (top max, bot 3+1 suit).
        # The leak signal is: oracle prefers DS-bot config, which means
        # max_sing goes in BOT (not top), and a non-max-singleton goes on top.

        pop_records.append({
            "pop": pop,
            "v56_lbl": v56_lbl,
            "regret": regret,
            "pair_rank": pair_rank,
            "max_sing": max_sing,
            "second_max_sing": second_max_sing,
            "third_max_sing": third_max_sing,
            "ds_bot_pair_high": ds_bot_pair_high,
            "max_gap": max_gap,
            "ds_upgrade": ds_upgrade,
            "ds_upgrade_vs_max": ds_upgrade_vs_max,
        })

        if (i + 1) % 30_000 == 0:
            print(f"  scanned {i+1:,}/{n:,}", flush=True)

    print(f"  done in {time.time()-t0:.1f}s", flush=True)
    print(f"  records in dominant v56 pick zone: {len(pop_records):,}", flush=True)

    # --- Build pop tables ---
    n_keep = sum(1 for r in pop_records if r["pop"] == "KEEP")
    n_swap = sum(1 for r in pop_records if r["pop"] == "SWAP")
    n_other = sum(1 for r in pop_records if r["pop"] == "OTHER")
    wg_swap = sum(r["regret"] for r in pop_records if r["pop"] == "SWAP")
    wg_keep_inflicted = sum(r["regret"] for r in pop_records if r["pop"] == "KEEP")
    wg_swap_dollars = wg_swap / N_TOTAL_GRID * EV_TO_DOL * 1000
    print(f"\nPopulation summary (within PMID_tmax_SS / PMID_tmax_31):")
    print(f"  KEEP  (oracle = v56 pick):                  {n_keep:>8,} hands  (target: rule must NOT fire)")
    print(f"  SWAP  (oracle = PMID_tnomax_DS):            {n_swap:>8,} hands  (target leak: ${wg_swap_dollars:.2f}/1000h)")
    print(f"  OTHER (different mismatch, e.g., PBOT):     {n_other:>8,} hands  (ignored — not the target rule)")
    print()

    # --- Discriminator histograms (KEEP vs SWAP) ---
    feature_names = ["pair_rank", "max_sing", "second_max_sing",
                     "third_max_sing", "ds_bot_pair_high",
                     "max_gap", "ds_upgrade", "ds_upgrade_vs_max"]
    discriminator_tables = {}
    for fname in feature_names:
        keep_vals = [r[fname] for r in pop_records if r["pop"] == "KEEP"]
        swap_vals = [r[fname] for r in pop_records if r["pop"] == "SWAP"]
        keep_arr = np.array(keep_vals) if keep_vals else np.array([0])
        swap_arr = np.array(swap_vals) if swap_vals else np.array([0])
        keep_hist = Counter(keep_vals)
        swap_hist = Counter(swap_vals)
        all_vals = sorted(set(keep_hist) | set(swap_hist))
        table_rows = []
        for v in all_vals:
            k = keep_hist.get(v, 0)
            s = swap_hist.get(v, 0)
            tot = k + s
            swap_pct = s / max(tot, 1) * 100
            table_rows.append({
                "val": v,
                "keep_n": k,
                "swap_n": s,
                "swap_pct_within_val": swap_pct,
            })
        discriminator_tables[fname] = {
            "keep_mean": float(keep_arr.mean()),
            "keep_median": float(np.median(keep_arr)),
            "swap_mean": float(swap_arr.mean()),
            "swap_median": float(np.median(swap_arr)),
            "rows": table_rows,
        }

    # Print top candidates: features where KEEP-mean and SWAP-mean differ most
    print(f"Discriminator candidates (KEEP-mean vs SWAP-mean):\n")
    print(f"  {'feature':<22}{'keep_mean':>12}{'swap_mean':>12}{'Δ':>10}")
    sep_scored = []
    for fname in feature_names:
        d = discriminator_tables[fname]
        delta = d["swap_mean"] - d["keep_mean"]
        sep_scored.append((fname, delta, d))
        print(f"  {fname:<22}{d['keep_mean']:>12.2f}{d['swap_mean']:>12.2f}{delta:>+10.2f}")
    print()

    # For top 3 features by |Δ|, print the per-value histogram
    sep_scored.sort(key=lambda x: -abs(x[1]))
    print(f"Top-3 discriminators by |Δ|: per-value distribution")
    for fname, delta, d in sep_scored[:3]:
        print(f"\n  === {fname}  (Δ = {delta:+.2f}) ===")
        print(f"  {'value':>6}{'keep_n':>10}{'swap_n':>10}{'swap_pct':>10}")
        for r in d["rows"]:
            print(f"  {r['val']:>6}{r['keep_n']:>10,}{r['swap_n']:>10,}"
                  f"{r['swap_pct_within_val']:>9.1f}%")

    # --- Persist ---
    out = {
        "session": 83,
        "phase": "B+",
        "n_pop_records_total": len(pop_records),
        "n_pop_keep": n_keep,
        "n_pop_swap": n_swap,
        "n_pop_other": n_other,
        "wg_swap_target_dollars_per_1000h": wg_swap_dollars,
        "discriminator_tables": discriminator_tables,
        "low_pair_ranks": sorted(LOW_PAIR_RANKS),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
