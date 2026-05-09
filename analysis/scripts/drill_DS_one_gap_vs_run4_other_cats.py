"""
Session 45 — Drill C: DS one-gap-4 vs DS run-4 across hand categories.

S44 produced a counterintuitive finding (within-hand pairwise on J-low
no-pair):

  DS one-gap-4 BEATS DS run-4 by +$376/1000h within-hand.

Hypothesized mechanism: a missing internal rank in the bot creates board-
bridging straight equity (board-card fills the inside), while consecutive-
rank already maxes its internal-straight contribution. A 1-gap straight
draw (5-7-8-9) is satisfied by ANY of the missing rank cards on board (4
of 6 outs, plus open-ended on either end), whereas 4-card-run (5-6-7-8)
is open-ended on two ends only.

This drill tests whether the finding generalizes across hand categories,
not just J-low no-pair. We test:

  - all hands (no max-rank restriction): does the +$376 hold for the full
    population?
  - by category: high_only, pair, two_pair, trips, trips_pair, three_pair,
    quads
  - by max_rank stratum: ≤J, ≤Q, ≤K, all (for high_only and pair only,
    since other cats have small populations)

For each hand:
  1. Find best EV among settings where bot-suit=DS AND bot-conn=run-4
  2. Find best EV among settings where bot-suit=DS AND bot-conn=one-gap-4
  3. If both achievable, accumulate within-hand lift = EV(one-gap-4) − EV(run-4)
  4. Aggregate across hands.

Sample mode: per-category sampling for tractability on large pops.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_DS_one_gap_vs_run4_other_cats.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_DS_one_gap_vs_run4_other_cats.py --sample 20000
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands, CATEGORY_NAMES  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS,
)
from drill_bot_suit_run_priority import (  # noqa: E402
    compute_connectivity_classes,
    CONN_RUN_4,
    CONN_ONE_GAP_4,
)

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=20000,
                    help="Per-category sample cap (0=all). Default 20K each.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 45 Drill C: DS one-gap-4 vs DS run-4 across categories")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    print(f"  total hands: {n_total:,}")
    cat_counts = np.bincount(cats, minlength=8)
    for c in range(7):
        print(f"    cat={c} ({CATEGORY_NAMES[c]:<11}): {cat_counts[c]:>10,}  "
              f"({100*cat_counts[c]/n_total:>5.2f}%)")

    # Compute max_rank per hand for stratification
    print("\n[2/4] computing max_rank per hand (for stratification) ...", flush=True)
    t0 = time.time()
    hands_arr = np.asarray(ch.hands[:], dtype=np.uint8)
    ranks_arr = (hands_arr // 4) + 2  # (N, 7)
    max_rank = ranks_arr.max(axis=1).astype(np.int8)
    print(f"  done in {time.time()-t0:.1f}s")

    # Per-category sample (or all)
    rng = np.random.default_rng(args.seed)
    cat_indices = {}
    for c in range(7):
        idx = np.where(cats == c)[0]
        if args.sample > 0 and len(idx) > args.sample:
            idx = np.sort(rng.choice(idx, size=args.sample, replace=False))
        cat_indices[c] = idx
        print(f"  cat={c} ({CATEGORY_NAMES[c]:<11}) sampled: {len(idx):>10,}")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Per-category accumulators
    # n_co: count of co-achievable (both DS run-4 AND DS one-gap-4 present)
    # sum_lift: sum of EV(one-gap-4) − EV(run-4)
    # sum_lift_pref / n_co_pref: prefix counterparts
    # n_run4: count of hands with DS run-4 achievable (any subset)
    # n_onegap: count of hands with DS one-gap-4 achievable
    stats = {}
    for c in range(7):
        stats[c] = {
            "n_processed": 0,
            "n_run4_full": 0, "n_onegap_full": 0,
            "n_co_full": 0, "sum_lift_full": 0.0,
            "n_processed_pref": 0,
            "n_run4_pref": 0, "n_onegap_pref": 0,
            "n_co_pref": 0, "sum_lift_pref": 0.0,
            # Stratify by max_rank ≤ J / Q / K / A (for some cats)
            "by_maxr": {mr: {"n_co_full": 0, "sum_lift_full": 0.0,
                              "n_co_pref": 0, "sum_lift_pref": 0.0}
                          for mr in (11, 12, 13, 14)},
        }

    print("\n[4/4] per-hand within-hand pairwise ...", flush=True)
    t0 = time.time()
    total_to_process = sum(len(v) for v in cat_indices.values())
    processed = 0

    for c in range(7):
        for cid_int in cat_indices[c]:
            cid = int(cid_int)
            mr = int(max_rank[cid])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            feats = setting_features_from_bytes(h)
            conn = compute_connectivity_classes(h)
            is_ds = feats.bot_suit_profile == SUIT_PROFILE_DS

            mask_run4 = is_ds & (conn == CONN_RUN_4)
            mask_onegap = is_ds & (conn == CONN_ONE_GAP_4)

            stats[c]["n_processed"] += 1
            if mask_run4.any():
                stats[c]["n_run4_full"] += 1
            if mask_onegap.any():
                stats[c]["n_onegap_full"] += 1

            if mask_run4.any() and mask_onegap.any():
                rowf = np.asarray(gf.evs[cid], dtype=np.float64)
                ev_run4 = float(rowf[mask_run4].max())
                ev_onegap = float(rowf[mask_onegap].max())
                lift = ev_onegap - ev_run4
                stats[c]["n_co_full"] += 1
                stats[c]["sum_lift_full"] += lift
                if mr in stats[c]["by_maxr"]:
                    stats[c]["by_maxr"][mr]["n_co_full"] += 1
                    stats[c]["by_maxr"][mr]["sum_lift_full"] += lift

                if cid < 500_000:
                    rowp = np.asarray(gp.evs[cid], dtype=np.float64)
                    ev_run4_p = float(rowp[mask_run4].max())
                    ev_onegap_p = float(rowp[mask_onegap].max())
                    lift_p = ev_onegap_p - ev_run4_p
                    stats[c]["n_processed_pref"] += 1
                    stats[c]["n_co_pref"] += 1
                    stats[c]["sum_lift_pref"] += lift_p
                    if mr in stats[c]["by_maxr"]:
                        stats[c]["by_maxr"][mr]["n_co_pref"] += 1
                        stats[c]["by_maxr"][mr]["sum_lift_pref"] += lift_p
            elif cid < 500_000:
                stats[c]["n_processed_pref"] += 1
                if mask_run4.any():
                    stats[c]["n_run4_pref"] += 1
                if mask_onegap.any():
                    stats[c]["n_onegap_pref"] += 1

            processed += 1
            if processed % 20000 == 0:
                rate = processed / (time.time() - t0)
                print(f"    progress {processed:>7,}/{total_to_process:,}  "
                      f"rate={rate:.0f}/s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # ── Reporting ──
    print("=" * 100)
    print("DS one-gap-4 vs DS run-4 (within-hand pairwise lift = EV(one-gap-4) − EV(run-4))")
    print("=" * 100)
    print(f"  Per category, sampled n={args.sample if args.sample > 0 else 'all'}/cat")
    print(f"\n  {'cat':<13} {'n_proc':>8}  {'n_run4':>8}  {'n_onegap':>9}  "
          f"{'n_co':>8}  {'lift_full($/1000h)':>20}  {'n_co_p':>8}  "
          f"{'lift_pref($/1000h)':>20}")
    print("-" * 110)
    for c in range(7):
        s = stats[c]
        if s["n_processed"] == 0:
            continue
        lift_full = (s["sum_lift_full"] / s["n_co_full"] * EV_TO_DOL * 1000
                     if s["n_co_full"] > 0 else float('nan'))
        lift_pref = (s["sum_lift_pref"] / s["n_co_pref"] * EV_TO_DOL * 1000
                     if s["n_co_pref"] > 0 else float('nan'))
        if np.isnan(lift_full):
            lift_full_str = "       n/a"
        else:
            lift_full_str = f"${lift_full:>+11.1f}"
        if np.isnan(lift_pref):
            lift_pref_str = "       n/a"
        else:
            lift_pref_str = f"${lift_pref:>+11.1f}"
        print(f"  {CATEGORY_NAMES[c]:<13} {s['n_processed']:>8,}  "
              f"{s['n_run4_full']:>8,}  {s['n_onegap_full']:>9,}  "
              f"{s['n_co_full']:>8,}  {lift_full_str:>20}  "
              f"{s['n_co_pref']:>8,}  {lift_pref_str:>20}")

    # ── max_rank stratification (only for cats with sufficient signal) ──
    print("\n── BY max_rank STRATA (full grid) — DS one-gap-4 minus DS run-4 ──")
    print(f"  {'cat':<13} {'max≤J':>20}  {'max≤Q':>20}  {'max≤K':>20}  {'max=A':>20}")
    print("-" * 100)
    for c in range(7):
        s = stats[c]
        line = f"  {CATEGORY_NAMES[c]:<13} "
        for mr in (11, 12, 13, 14):
            cell = s["by_maxr"][mr]
            if cell["n_co_full"] >= 50:
                lift = cell["sum_lift_full"] / cell["n_co_full"] * EV_TO_DOL * 1000
                cell_str = f"n={cell['n_co_full']:>5,} ${lift:>+9.1f}"
            else:
                cell_str = f"n={cell['n_co_full']:>5,} (sparse)"
            line += f"{cell_str:>22}"
        print(line)

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
