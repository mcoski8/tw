"""
Probe `pair` hands (single-pair, no trips/quads): what are robust's
top + bot structure preferences? The current SIMPLE rule fixes mid =
the pair, top = highest singleton, bot = the other 4. But the pair
category has 35.0% miss rate — something is wrong.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis import read_canonical_hands  # noqa: E402


def pct(x): return f"{100*x:5.2f}%"


def main():
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    cards = canonical.hands
    df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()

    sub = df[df["category"] == "pair"].reset_index(drop=True)
    n = len(sub)
    print(f"pair: {n:,} hands ({pct(n/len(df))})")

    # 1. Robust mid is the pair?
    mid_is_pair = sub["robust_mid_is_pair"]
    mid_eq_pair_high = (sub["robust_mid_high_rank"] == sub["pair_high_rank"]) & mid_is_pair
    print(f"\n  robust mid is the pair                 : {pct(mid_eq_pair_high.mean())}")
    print(f"  robust mid is some pair (any)          : {pct(mid_is_pair.mean())}")

    # 2. Pair -> bot rate (when robust pair lands in bot)
    pair_in_bot = sub["robust_bot_pair_high"] == sub["pair_high_rank"]
    print(f"  pair lands in bot                       : {pct(pair_in_bot.mean())}")

    # 3. Robust top — is it the highest singleton (= top_rank when top_rank != pair_rank)?
    # Singleton highest = top_rank if top_rank != pair_high_rank, else second_rank
    expected_top = sub["top_rank"].copy()
    mask_skip = sub["top_rank"] == sub["pair_high_rank"]
    expected_top[mask_skip] = sub.loc[mask_skip, "second_rank"]
    top_match = (sub["robust_top_rank"] == expected_top)
    print(f"\n  robust top == highest singleton         : {pct(top_match.mean())}")

    # When NOT highest singleton — what is robust top?
    not_match = sub[~top_match]
    if len(not_match):
        print(f"  When robust top != highest singleton ({len(not_match):,} hands):")
        print(f"    robust top is pair-rank             : {pct((not_match['robust_top_rank'] == not_match['pair_high_rank']).mean())}  (broken pair → top)")
        print(f"    robust top < highest singleton      : {pct((not_match['robust_top_rank'] < expected_top.loc[not_match.index]).mean())}")

    # 4. Bot DS rate
    print(f"\n  robust bot is DS                        : {pct(sub['robust_bot_is_double_suited'].mean())}")
    can_ds = sub["suit_2nd"] >= 2
    print(f"  hands where DS feasible (suit_2nd≥2)    : {pct(can_ds.mean())}")
    if can_ds.any():
        print(f"  DS-feasible hands: robust picked DS    : {pct(sub.loc[can_ds,'robust_bot_is_double_suited'].mean())}")

    # 5. Pair_high_rank stratification
    print(f"\n  pair_high_rank stratification:")
    print(f"  {'pair':>5} {'n':>9} {'mid=pair':>10} {'top=hi-sing':>12} {'bot DS':>9}")
    for r in range(2, 15):
        s = sub[sub["pair_high_rank"] == r]
        if len(s) < 1000:
            continue
        m = ((s["robust_mid_high_rank"] == r) & s["robust_mid_is_pair"]).mean()
        et = s["top_rank"].copy()
        msk = s["top_rank"] == r
        et[msk] = s.loc[msk, "second_rank"]
        t = (s["robust_top_rank"] == et).mean()
        d = s["robust_bot_is_double_suited"].mean()
        print(f"  {r:>5} {len(s):>9,} {pct(m):>10} {pct(t):>12} {pct(d):>9}")


if __name__ == "__main__":
    main()
