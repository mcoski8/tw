"""
Per-category breakdown: where does v7 beat v3, by hand type?

Reads:
  data/v3_evloss_records.parquet
  data/v7_regression_records.parquet
Both are 2000-hand × 4-profile records on the same hands (seed=42, post-bugfix).

Computes:
  - For each hand, hand category (high_only / pair / two_pair / three_pair /
    trips / trips_pair / quads).
  - Per category × per profile: mean v3 EV, mean v7 EV, $/1000h delta.
  - Per category: aggregate $/1000h delta across all 4 profiles.
  - Per category: how often v7 picks a different setting than v3.
  - Identify the categories where v7's gain is largest.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.features import (  # noqa: E402
    CATEGORY_HIGH_ONLY, CATEGORY_PAIR, CATEGORY_TWO_PAIR, CATEGORY_THREE_PAIR,
    CATEGORY_TRIPS, CATEGORY_TRIPS_PAIR, CATEGORY_QUADS,
    hand_features_scalar,
)


def categorize(hand_bytes: list) -> str:
    arr = np.array(hand_bytes, dtype=np.uint8)
    feats = hand_features_scalar(arr)
    if feats["n_quads"] >= 1:
        return CATEGORY_QUADS
    if feats["n_trips"] >= 1 and feats["n_pairs"] >= 1:
        return CATEGORY_TRIPS_PAIR
    if feats["n_trips"] >= 1:
        return CATEGORY_TRIPS
    if feats["n_pairs"] == 3:
        return CATEGORY_THREE_PAIR
    if feats["n_pairs"] == 2:
        return CATEGORY_TWO_PAIR
    if feats["n_pairs"] == 1:
        return CATEGORY_PAIR
    return CATEGORY_HIGH_ONLY


PROFILE_IDS = ("mfsuitaware", "omaha", "topdef", "weighted")


def main() -> int:
    v3 = pq.read_table(ROOT / "data" / "v3_evloss_records.parquet").to_pandas()
    v7 = pq.read_table(ROOT / "data" / "v7_regression_records.parquet").to_pandas()
    assert (v3["hand_str"].values == v7["hand_str"].values).all()
    n = len(v3)
    print(f"Loaded {n} hands from v3 + v7 records (post-bugfix).")

    # Categorize each hand.
    v3["category"] = v3["hand_bytes"].apply(categorize)
    v7["category"] = v3["category"]  # same hands

    # Per-category aggregates.
    print(f"\n{'='*120}")
    print(f"{'PER-CATEGORY PER-PROFILE EV BREAKDOWN (mean EV, post-bugfix)':<110}")
    print(f"{'='*120}\n")
    print(f"{'category':<14}{'n':>6}  {'profile':<14}"
          f"{'v3_ev':>10}{'v7_ev':>10}{'delta':>10}{'$/1000h':>10}{'v7≠v3':>10}")
    print("-" * 110)

    cat_order = [CATEGORY_HIGH_ONLY, CATEGORY_PAIR, CATEGORY_TWO_PAIR,
                 CATEGORY_THREE_PAIR, CATEGORY_TRIPS, CATEGORY_TRIPS_PAIR,
                 CATEGORY_QUADS]
    cat_summary = []
    for cat in cat_order:
        mask = v3["category"] == cat
        cnt = int(mask.sum())
        if cnt == 0:
            continue
        cat_v3 = v3[mask]
        cat_v7 = v7[mask]
        diff_pct = 100 * (cat_v3["v3_idx"].values != cat_v7["v3_idx"].values).mean()
        cat_total_delta = 0.0
        for p in PROFILE_IDS:
            v3_ev = cat_v3[f"v3_ev_{p}"].mean()
            v7_ev = cat_v7[f"v3_ev_{p}"].mean()
            delta = v7_ev - v3_ev
            cat_total_delta += delta
            print(f"{cat:<14}{cnt:>6}  {p:<14}"
                  f"{v3_ev:>+10.4f}{v7_ev:>+10.4f}"
                  f"{delta:>+10.4f}{delta*10000:>+10.0f}"
                  f"{(diff_pct if p == PROFILE_IDS[0] else 0):>9.1f}%"
                  if p == PROFILE_IDS[0] else
                  f"{cat:<14}{cnt:>6}  {p:<14}"
                  f"{v3_ev:>+10.4f}{v7_ev:>+10.4f}"
                  f"{delta:>+10.4f}{delta*10000:>+10.0f}{'':>10}")
        mean_delta = cat_total_delta / 4
        per_hand_per_1000 = mean_delta * 10000
        cat_summary.append({
            "category": cat, "n": cnt,
            "mean_delta_ev": mean_delta,
            "per_1000h": per_hand_per_1000,
            "v7_neq_v3_pct": diff_pct,
            "share_of_total_n": cnt / n,
        })
        print(f"{'':<14}{'':>6}  {'AVERAGE':<14}"
              f"{'':>10}{'':>10}{mean_delta:>+10.4f}{per_hand_per_1000:>+10.0f}")
        print()

    print(f"\n{'='*80}")
    print(f"SUMMARY — v7 vs v3 by category (sorted by impact)")
    print(f"{'='*80}\n")
    print(f"{'category':<14}{'n':>6}{'share':>8}{'v7≠v3':>10}{'mean Δ EV':>14}{'$/1000h':>14}{'$ contrib':>14}")
    print("-" * 80)
    cat_summary.sort(key=lambda r: -abs(r["per_1000h"] * r["share_of_total_n"]))
    for row in cat_summary:
        contrib = row["per_1000h"] * row["share_of_total_n"]
        print(f"{row['category']:<14}{row['n']:>6}{row['share_of_total_n']*100:>7.1f}%"
              f"{row['v7_neq_v3_pct']:>9.1f}%{row['mean_delta_ev']:>+14.4f}"
              f"{row['per_1000h']:>+14.0f}{contrib:>+14.0f}")
    total_contrib = sum(r["per_1000h"] * r["share_of_total_n"] for r in cat_summary)
    print("-" * 80)
    print(f"{'TOTAL':<14}{'':>6}{'':>8}{'':>10}{'':>14}{'':>14}{total_contrib:>+14.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
