#!/usr/bin/env python3
"""Grade v14 vs v22 (v14 + tightened Rule 5: msphr>=11 AND msplr>=9)
on full grid. Tests whether tightening saves Rule 5 from over-firing.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    print("loading grid ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}", flush=True)

    from strategy_v14_combined import strategy_v14_combined
    from strategy_v22_combined import strategy_v22_combined

    strategies = [
        ("v14 (Rules 1+2+3 + v8 fallback w/Rule 4)", strategy_v14_combined),
        ("v22 (v14 + Rule 5 TIGHT msphr>=11 msplr>=9)", strategy_v22_combined),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label, progress_every=1_000_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print("SUMMARY (full grid)")
    print("=" * 70)
    print(compare_grades(*results))
    delta = results[0].mean_regret - results[1].mean_regret
    print(f"\nv22 vs v14: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
