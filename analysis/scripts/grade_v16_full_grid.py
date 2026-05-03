#!/usr/bin/env python3
"""Grade v16 (DT regression on the Oracle Grid) vs v8/v14 on the full 6M
grid (N=200) and the 500K-prefix grid (N=1000). Ship if v16 beats v14."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))
sys.path.insert(0, str(REPO / "trainer" / "src"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid


GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", choices=["full", "prefix"], default="full")
    args = ap.parse_args()

    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}  Canonical: {len(ch):,}", flush=True)

    # If prefix grid, the canonical_ids list is not necessarily 0..N-1 row-aligned.
    # Pass max_hands=len(grid); grade_strategy will validate row==canonical_id.
    # The prefix file IS canonical-id ordered for the first 500K rows, so this works.

    from strategy_v8_hybrid import strategy_v8_hybrid
    from strategy_v14_combined import strategy_v14_combined
    from strategy_v16_dt import strategy_v16_dt

    strategies = [
        ("v8_hybrid", strategy_v8_hybrid),
        ("v14_combined", strategy_v14_combined),
        ("v16_dt (regression on grid)", strategy_v16_dt),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label, progress_every=1_000_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(*results))
    v8, v14, v16 = results
    print(f"\nv16 vs v14 (incremental): {v14.mean_regret - v16.mean_regret:+.4f}  ≈ ${(v14.mean_regret - v16.mean_regret) * 10 * 1000:+,.0f}/1000h")
    print(f"v16 vs v8  (cumulative):  {v8.mean_regret - v16.mean_regret:+.4f}  ≈ ${(v8.mean_regret - v16.mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
