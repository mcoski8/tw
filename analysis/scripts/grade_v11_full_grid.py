#!/usr/bin/env python3
"""Grade v11 (high_only omaha-first) alongside v8, v9.1, v10 on full grid."""
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
    from strategy_v10_two_pair_no_split import strategy_v10_two_pair_no_split
    from strategy_v11_high_only_omaha_first import strategy_v11_high_only_omaha_first

    strategies = [
        ("v8_hybrid", strategy_v8_hybrid),
        ("v10 (v9.1 + two_pair no-split)", strategy_v10_two_pair_no_split),
        ("v11 (v10 + high_only omaha-first)", strategy_v11_high_only_omaha_first),
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

    v8 = results[0]
    v10 = results[1]
    v11 = results[2]
    print(f"\nv11 vs v10 (incremental): {v10.mean_regret - v11.mean_regret:+.4f}  ≈ ${(v10.mean_regret - v11.mean_regret) * 10 * 1000:+,.0f}/1000h")
    print(f"v11 vs v8  (cumulative):  {v8.mean_regret - v11.mean_regret:+.4f}  ≈ ${(v8.mean_regret - v11.mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
