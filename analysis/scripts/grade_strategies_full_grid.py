#!/usr/bin/env python3
"""Grade existing strategies (v3, v8_hybrid) against the Full Oracle Grid.

This is the headline run for the Strategy-Grading harness — confirms the
tool works end-to-end on real strategies and gives us a baseline regret
that any v9 candidate must beat.

Usage:
    python3 -u analysis/scripts/grade_strategies_full_grid.py [--max-hands N]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))
sys.path.insert(0, str(REPO / "trainer" / "src"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

GRID_PATH = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-hands", type=int, default=None,
                        help="Cap on hands to grade (default: all 6M)")
    args = parser.parse_args()

    print(f"Loading grid (memmap) from {GRID_PATH} ...")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    print(f"  {len(grid):,} records  opp={grid.header.opp_label}  N={grid.header.samples}")
    print(f"\nLoading canonical hands from {CANON_PATH} ...")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    print(f"  {len(ch):,} canonical hands.")

    # Import strategies. Lazy-imported so the script runs even if pyarrow
    # isn't on the path for unrelated parquet readers.
    from encode_rules import strategy_v3
    from strategy_v8_hybrid import strategy_v8_hybrid

    strategies = [
        ("v3 (production hand-coded)", strategy_v3),
        ("v8_hybrid (v7 + v3 high_only/pair + AAKK)", strategy_v8_hybrid),
    ]

    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...")
        res = grade_strategy(
            fn, grid, ch, label=label,
            max_hands=args.max_hands,
            progress_every=500_000,
            keep_per_hand=False,
        )
        print(res.summary())
        results.append(res)

    print("\n\n" + "=" * 70)
    print("STRATEGY GRADING SUMMARY (vs Full Oracle Grid, N=200, realistic mixture)")
    print("=" * 70)
    print(compare_grades(*results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
