"""
Investigate UNANIMOUS misses: hands where all 4 profiles agree on the answer
but our rule disagrees. ~273K hands. These are pure rule-logic failures
(not opponent-dependent).

For each miss, classify what's wrong about my prediction:
  * Wrong top tier (e.g., highest singleton not picked)
  * Wrong mid tier (e.g., pair not in mid)
  * Wrong bot composition (forced when top+mid match)

Then bucket by hand category and feature signatures.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

from tw_analysis import read_canonical_hands  # noqa: E402
from tw_analysis.features import decode_tier_positions  # noqa: E402
from encode_rules import strategy_hi_only_search  # noqa: E402


def shape(hand, setting):
    t, m, b = decode_tier_positions(int(setting))
    ranks = (hand // 4) + 2
    return (
        int(ranks[t]),
        tuple(sorted(int(ranks[i]) for i in m)),
        tuple(sorted(int(ranks[i]) for i in b)),
    )


def main() -> int:
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    cards = canonical.hands
    df = pq.read_table(
        ROOT / "data" / "feature_table.parquet",
        columns=[
            "category", "agreement_class", "multiway_robust",
            "n_pairs", "n_trips", "n_quads",
            "pair_high_rank", "pair_low_rank", "trips_rank", "quads_rank",
            "top_rank", "second_rank", "third_rank",
            "suit_max", "suit_2nd", "n_broadway", "n_low",
            "robust_top_rank", "robust_mid_is_pair",
            "robust_mid_high_rank", "robust_mid_low_rank",
            "robust_bot_pair_high", "robust_bot_is_double_suited",
        ],
    ).to_pandas()

    una = df[df["agreement_class"] == "unanimous"].reset_index(drop=True)
    una_idx = df[df["agreement_class"] == "unanimous"].index.values
    una_hands = cards[una_idx]
    n_una = len(una)
    print(f"Unanimous hands: {n_una:,}")

    # Compute predictions on the unanimous subset.
    print("Computing hi_only_search predictions on unanimous subset…")
    preds = np.empty(n_una, dtype=np.uint8)
    for i in range(n_una):
        if i % 100000 == 0:
            print(f"  {i:,}/{n_una:,}")
        preds[i] = strategy_hi_only_search(una_hands[i])
    print(f"  done")

    # Shape match.
    print("Computing shape matches…")
    shape_match = np.zeros(n_una, dtype=bool)
    for i in range(n_una):
        if shape(una_hands[i], int(preds[i])) == shape(una_hands[i], int(una.iloc[i]["multiway_robust"])):
            shape_match[i] = True
    miss = ~shape_match
    n_miss = int(miss.sum())
    print(f"\nUNANIMOUS shape-misses: {n_miss:,}  ({100*n_miss/n_una:.2f}%)")

    # Bucket by category.
    print("\nBy category (share of unanimous misses, miss-rate within category):")
    for cat in ("high_only", "pair", "two_pair", "three_pair", "trips",
                 "trips_pair", "quads"):
        mcat = (una["category"] == cat).values
        cat_n = int(mcat.sum())
        cat_miss = int((mcat & miss).sum())
        if cat_n == 0:
            continue
        print(f"  {cat:<14} n={cat_n:>9,}  misses={cat_miss:>8,}  "
              f"share_of_misses={100*cat_miss/max(n_miss,1):5.1f}%  "
              f"miss_rate_in_cat={100*cat_miss/cat_n:5.1f}%")

    # For each major missed category, look at robust top vs my top, mid composition.
    print("\n--- 30 example unanimous misses (across categories) ---")
    rng = np.random.default_rng(0)
    miss_indices = np.where(miss)[0]
    sample = rng.choice(miss_indices, min(30, len(miss_indices)), replace=False)
    for i in sample:
        h = una_hands[i]
        ranks_h = list((h // 4) + 2)
        suits_h = list(h % 4)
        suit_str = ["c", "d", "h", "s"]
        cardstr = " ".join(f"{r}{suit_str[s]}" for r, s in zip(ranks_h, suits_h))
        rs = shape(h, int(una.iloc[i]["multiway_robust"]))
        ms = shape(h, int(preds[i]))
        cat = una.iloc[i]["category"]
        print(f"  [{cat:<11}] {cardstr}")
        print(f"    robust top={rs[0]:>2} mid={rs[1]!s:>10} bot={rs[2]!s:>16}")
        print(f"    mine   top={ms[0]:>2} mid={ms[1]!s:>10} bot={ms[2]!s:>16}")

    # Mining: for unanimous miss in `pair` category, check what's special.
    print("\n--- Pair category unanimous-miss feature stats ---")
    pair_miss = una[(una["category"] == "pair") & miss]
    pair_match = una[(una["category"] == "pair") & shape_match]
    if len(pair_miss):
        print(f"  pair_high_rank distribution (miss vs match):")
        for r in range(2, 15):
            mr = int((pair_miss["pair_high_rank"] == r).sum())
            mt = int((pair_match["pair_high_rank"] == r).sum())
            tot = mr + mt
            if tot < 100:
                continue
            print(f"    rank={r:>2}: miss={mr:>5} match={mt:>5} miss_rate={100*mr/tot:5.1f}%")

        print(f"\n  Robust mid is pair (in misses)?")
        print(f"    pair → mid : {100*pair_miss['robust_mid_is_pair'].mean():.1f}%")
        pair_in_bot = (pair_miss["robust_bot_pair_high"] == pair_miss["pair_high_rank"]).mean()
        print(f"    pair → bot : {100*pair_in_bot:.1f}%")

    # high_only unanimous miss feature stats.
    print("\n--- High_only category unanimous-miss feature stats ---")
    ho_miss = una[(una["category"] == "high_only") & miss]
    ho_match = una[(una["category"] == "high_only") & shape_match]
    if len(ho_miss):
        print(f"  ho_miss n={len(ho_miss):,}, ho_match n={len(ho_match):,}")
        for col in ("top_rank", "second_rank", "n_broadway", "n_low",
                     "suit_max", "suit_2nd"):
            print(f"  {col:<14}: miss_mean={ho_miss[col].mean():.2f}  "
                  f"match_mean={ho_match[col].mean():.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
