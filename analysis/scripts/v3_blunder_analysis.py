"""
v3 blunder analysis (Gemini's 3 hypothesis tests).

Loads data/v3_evloss_records.parquet (produced by v3_evloss_baseline.py
with --save) and runs three structured tests on the per-hand records:

1. ISOLATE BLUNDERS:
   blunder := hand whose worst per-profile EV-loss > 2.0.
   Report counts and base rate.

2. FALL-THROUGH HYPOTHESIS:
   Are blunders disproportionately settled to setting 102 or 104 (v3's
   naive defaults)? Compute the proportion in blunder vs non-blunder
   subsets and the odds ratio.

3. STRUCTURAL PATTERN HYPOTHESIS:
   Within blunders, is the failure concentrated on:
     (a) two_pair / three_pair hands with an Ace singleton?
     (b) trips_pair hands with an Ace singleton?
   Compare these conditional rates to non-blunder baselines.

Usage:
    python3 analysis/scripts/v3_blunder_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.features import (  # noqa: E402
    hand_features_scalar,
    CATEGORY_ORDER,
)

RECORDS_PATH = ROOT / "data" / "v3_evloss_records.parquet"
BLUNDER_THRESHOLD = 2.0
DEFAULT_SETTINGS = {102, 104}


def odds_ratio(a: int, b: int, c: int, d: int) -> float:
    """
    a = blunders matching condition
    b = blunders not matching
    c = non-blunders matching
    d = non-blunders not matching
    Returns (a*d) / (b*c) with 0.5 continuity correction if any cell is 0.
    """
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return (a * d) / (b * c)


def main() -> int:
    if not RECORDS_PATH.exists():
        print(f"ERROR: {RECORDS_PATH} not found.")
        print("Run: python3 analysis/scripts/v3_evloss_baseline.py "
              "--hands 2000 --save data/v3_evloss_records.parquet")
        return 1

    df = pd.read_parquet(RECORDS_PATH)
    n = len(df)
    print(f"Loaded {n} per-hand records from {RECORDS_PATH}\n")

    # Compute structural features per record.
    features_rows = [hand_features_scalar(row) for row in df["hand_bytes"]]
    feat_df = pd.DataFrame(features_rows)
    df = pd.concat([df.reset_index(drop=True), feat_df], axis=1)

    # Map category_id (int) back to category name (str) for filtering.
    df["category"] = df["category_id"].map(
        {i: c for i, c in enumerate(CATEGORY_ORDER)}
    )

    # Useful derived columns.
    df["is_blunder"] = df["max_loss"] > BLUNDER_THRESHOLD
    df["v3_is_default"] = df["v3_idx"].isin(DEFAULT_SETTINGS)
    df["has_ace_singleton"] = (
        (df["top_rank"] == 14)
        & (df["pair_high_rank"] != 14)
        & (df["trips_rank"] != 14)
        & (df["quads_rank"] != 14)
    )

    # ------------------------------------------------------------------
    # Test 1: Blunder isolation summary.
    # ------------------------------------------------------------------
    n_blunder = int(df["is_blunder"].sum())
    n_clean = n - n_blunder
    print("=" * 78)
    print("TEST 1 — Blunder isolation")
    print("=" * 78)
    print(f"  Threshold: max_loss > {BLUNDER_THRESHOLD} (across all 4 profiles)")
    print(f"  Blunders:     {n_blunder:>5} / {n}  ({100*n_blunder/n:.1f}%)")
    print(f"  Non-blunders: {n_clean:>5} / {n}  ({100*n_clean/n:.1f}%)")
    print(f"  Mean max_loss (blunders):     {df.loc[df.is_blunder, 'max_loss'].mean():.3f}")
    print(f"  Mean max_loss (non-blunders): {df.loc[~df.is_blunder, 'max_loss'].mean():.3f}")
    print()

    if n_blunder == 0:
        print("No blunders identified — cannot proceed with hypothesis tests.")
        return 0

    # ------------------------------------------------------------------
    # Test 2: Fall-through hypothesis.
    # ------------------------------------------------------------------
    print("=" * 78)
    print("TEST 2 — Fall-through hypothesis: v3 picks setting 102 or 104")
    print("=" * 78)
    blunder_default = int(((df.is_blunder) & (df.v3_is_default)).sum())
    blunder_other = n_blunder - blunder_default
    clean_default = int(((~df.is_blunder) & (df.v3_is_default)).sum())
    clean_other = n_clean - clean_default

    p_blunder = blunder_default / n_blunder if n_blunder else 0
    p_clean = clean_default / n_clean if n_clean else 0
    or_ = odds_ratio(blunder_default, blunder_other, clean_default, clean_other)

    print(f"  Blunders → setting 102/104:   "
          f"{blunder_default}/{n_blunder} ({100*p_blunder:.1f}%)")
    print(f"  Non-blunders → setting 102/104: "
          f"{clean_default}/{n_clean} ({100*p_clean:.1f}%)")
    print(f"  Odds ratio (blunder : non-blunder): {or_:.2f}")
    if or_ >= 3.0:
        print("  → STRONG support for fall-through hypothesis")
    elif or_ >= 1.5:
        print("  → Moderate support for fall-through hypothesis")
    else:
        print("  → Weak / no support for fall-through hypothesis")
    print()

    # Breakdown by which default
    bl_104 = int(((df.is_blunder) & (df.v3_idx == 104)).sum())
    bl_102 = int(((df.is_blunder) & (df.v3_idx == 102)).sum())
    print(f"  Blunders → setting 104 only: {bl_104} ({100*bl_104/n_blunder:.1f}% of blunders)")
    print(f"  Blunders → setting 102 only: {bl_102} ({100*bl_102/n_blunder:.1f}% of blunders)")
    print()

    # ------------------------------------------------------------------
    # Test 3: Structural pattern hypothesis.
    # ------------------------------------------------------------------
    print("=" * 78)
    print("TEST 3 — Structural pattern hypothesis")
    print("=" * 78)

    print("\n  3a. Two-pair / three-pair hands with Ace singleton")
    print("  " + "-" * 60)
    target_categories = ["two_pair", "three_pair"]
    cat_mask = df["category"].isin(target_categories)
    bl_cat = df[df.is_blunder & cat_mask]
    cl_cat = df[~df.is_blunder & cat_mask]
    bl_cat_w_ace = int(bl_cat.has_ace_singleton.sum())
    cl_cat_w_ace = int(cl_cat.has_ace_singleton.sum())

    print(f"    Blunders with category in {target_categories}: {len(bl_cat)}")
    print(f"      ...of which has Ace singleton: {bl_cat_w_ace} "
          f"({100*bl_cat_w_ace/len(bl_cat) if len(bl_cat) else 0:.1f}%)")
    print(f"    Non-blunders with category in {target_categories}: {len(cl_cat)}")
    print(f"      ...of which has Ace singleton: {cl_cat_w_ace} "
          f"({100*cl_cat_w_ace/len(cl_cat) if len(cl_cat) else 0:.1f}%)")
    if len(bl_cat) and len(cl_cat):
        or_pair_ace = odds_ratio(
            bl_cat_w_ace, len(bl_cat) - bl_cat_w_ace,
            cl_cat_w_ace, len(cl_cat) - cl_cat_w_ace,
        )
        print(f"    Odds ratio (blunder : non-blunder | category=2-/3-pair): "
              f"{or_pair_ace:.2f}")

    print("\n  3b. Trips_pair hands with Ace singleton")
    print("  " + "-" * 60)
    cat_mask = df["category"] == "trips_pair"
    bl_cat = df[df.is_blunder & cat_mask]
    cl_cat = df[~df.is_blunder & cat_mask]
    bl_cat_w_ace = int(bl_cat.has_ace_singleton.sum())
    cl_cat_w_ace = int(cl_cat.has_ace_singleton.sum())
    print(f"    Blunders with category=trips_pair: {len(bl_cat)}")
    print(f"      ...of which has Ace singleton: {bl_cat_w_ace} "
          f"({100*bl_cat_w_ace/len(bl_cat) if len(bl_cat) else 0:.1f}%)")
    print(f"    Non-blunders with category=trips_pair: {len(cl_cat)}")
    print(f"      ...of which has Ace singleton: {cl_cat_w_ace} "
          f"({100*cl_cat_w_ace/len(cl_cat) if len(cl_cat) else 0:.1f}%)")
    if len(bl_cat) and len(cl_cat):
        or_tp_ace = odds_ratio(
            bl_cat_w_ace, len(bl_cat) - bl_cat_w_ace,
            cl_cat_w_ace, len(cl_cat) - cl_cat_w_ace,
        )
        print(f"    Odds ratio (blunder : non-blunder | category=trips_pair): "
              f"{or_tp_ace:.2f}")

    # ------------------------------------------------------------------
    # Bonus: full category breakdown of blunders
    # ------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("Category breakdown of blunders vs non-blunders")
    print("=" * 78)
    print(f"  {'category':<14}{'blunders':>10}{'%blunders':>11}"
          f"{'nonblund':>10}{'%nonblund':>11}{'or':>8}")
    for cat in df["category"].value_counts().index:
        bl = int(((df.is_blunder) & (df.category == cat)).sum())
        cl = int(((~df.is_blunder) & (df.category == cat)).sum())
        pct_bl = 100 * bl / n_blunder if n_blunder else 0
        pct_cl = 100 * cl / n_clean if n_clean else 0
        or_cat = odds_ratio(bl, n_blunder - bl, cl, n_clean - cl)
        print(f"  {cat:<14}{bl:>10}{pct_bl:>10.1f}%"
              f"{cl:>10}{pct_cl:>10.1f}%{or_cat:>8.2f}")

    # Bonus: ace-singleton breakdown
    print("\n" + "=" * 78)
    print("Ace-singleton (top_rank=14, no ace pair/trips/quads) breakdown")
    print("=" * 78)
    bl_ace = int(((df.is_blunder) & (df.has_ace_singleton)).sum())
    cl_ace = int(((~df.is_blunder) & (df.has_ace_singleton)).sum())
    print(f"  Blunders with Ace singleton:     {bl_ace}/{n_blunder} "
          f"({100*bl_ace/n_blunder:.1f}%)")
    print(f"  Non-blunders with Ace singleton: {cl_ace}/{n_clean} "
          f"({100*cl_ace/n_clean:.1f}%)")
    or_ace = odds_ratio(bl_ace, n_blunder - bl_ace, cl_ace, n_clean - cl_ace)
    print(f"  Odds ratio: {or_ace:.2f}")

    # Bonus: blunder + ace + multi-pair joint
    print("\n" + "=" * 78)
    print("Joint: blunder ∩ has_ace_singleton ∩ category-pattern")
    print("=" * 78)
    multi_pair_cats = ["two_pair", "three_pair", "trips_pair"]
    target = (
        df.is_blunder
        & df.has_ace_singleton
        & df.category.isin(multi_pair_cats)
    )
    n_target = int(target.sum())
    print(f"  Blunder ∩ Ace-singleton ∩ category∈{{{','.join(multi_pair_cats)}}}:")
    print(f"    {n_target}/{n_blunder} blunders ({100*n_target/n_blunder:.1f}%)")
    print(f"    {n_target}/{n} of all hands ({100*n_target/n:.2f}%)")

    # The hands themselves — for inspection
    print("\n" + "=" * 78)
    print("Worst 15 blunders (by max_loss) — full feature snapshot")
    print("=" * 78)
    worst = df.sort_values("max_loss", ascending=False).head(15)
    cols_show = ["hand_str", "v3_idx", "max_loss", "category",
                 "n_pairs", "pair_high_rank", "n_trips", "trips_rank",
                 "top_rank", "has_ace_singleton"]
    print(worst[cols_show].to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
