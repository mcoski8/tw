"""
Probe two_pair: where does the LOW pair vs HIGH pair go in robust?
SIMPLE assumes high → mid; unanimous-miss inspection suggests low → mid
is common.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

def pct(x): return f"{100*x:5.2f}%"


def main():
    df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
    sub = df[df["category"] == "two_pair"].reset_index(drop=True)
    n = len(sub)
    print(f"two_pair: {n:,} hands ({pct(n/len(df))})")

    high = sub["pair_high_rank"]
    low = sub["pair_low_rank"]
    rmh = sub["robust_mid_high_rank"]
    is_pair_mid = sub["robust_mid_is_pair"]

    high_in_mid = is_pair_mid & (rmh == high)
    low_in_mid = is_pair_mid & (rmh == low)
    no_pair_mid = ~is_pair_mid

    print("\nOverall:")
    print(f"  high pair → mid : {pct(high_in_mid.mean())}")
    print(f"  low pair  → mid : {pct(low_in_mid.mean())}")
    print(f"  no pair in mid  : {pct(no_pair_mid.mean())}")

    print("\nBy (high_pair, low_pair) rank cut:")
    print(f"  {'hi':>3} {'lo':>3} {'n':>9} {'high→mid':>10} {'low→mid':>10} {'noPair':>10}")
    for hi in range(2, 15):
        for lo in range(2, hi):
            s = sub[(high == hi) & (low == lo)]
            if len(s) < 200:
                continue
            h_in_m = (s["robust_mid_is_pair"] & (s["robust_mid_high_rank"] == hi)).mean()
            l_in_m = (s["robust_mid_is_pair"] & (s["robust_mid_high_rank"] == lo)).mean()
            np_m = (~s["robust_mid_is_pair"]).mean()
            print(f"  {hi:>3} {lo:>3} {len(s):>9,} {pct(h_in_m):>10} {pct(l_in_m):>10} {pct(np_m):>10}")


if __name__ == "__main__":
    main()
