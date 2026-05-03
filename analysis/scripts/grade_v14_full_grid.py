#!/usr/bin/env python3
"""Grade v14 (v12 + v9.2 widened pair gate) on full 6M grid."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))
sys.path.insert(0, str(REPO / "trainer" / "src"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid


def main() -> int:
    grid = read_oracle_grid(REPO / "data" / "oracle_grid_full_realistic_n200.bin", mode="memmap")
    ch = read_canonical_hands(REPO / "data" / "canonical_hands.bin", mode="memmap")
    print(f"Grid: {len(grid):,}  Canonical: {len(ch):,}")

    from strategy_v8_hybrid import strategy_v8_hybrid
    from strategy_v12_trips_pair import strategy_v12_trips_pair
    from strategy_v14_combined import strategy_v14_combined

    strategies = [
        ("v8_hybrid", strategy_v8_hybrid),
        ("v12 (trips_pair + two_pair + v9.1)", strategy_v12_trips_pair),
        ("v14 (v12 + v9.2 widened pair gate)", strategy_v14_combined),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...")
        res = grade_strategy(fn, grid, ch, label=label, progress_every=1_000_000)
        print(res.summary())
        results.append(res)

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(compare_grades(*results))
    v8 = results[0]; v12 = results[1]; v14 = results[2]
    print(f"\nv14 vs v12 (incremental): {v12.mean_regret - v14.mean_regret:+.4f}  ≈ ${(v12.mean_regret - v14.mean_regret) * 10 * 1000:+,.0f}/1000h")
    print(f"v14 vs v8  (cumulative):  {v8.mean_regret - v14.mean_regret:+.4f}  ≈ ${(v8.mean_regret - v14.mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
