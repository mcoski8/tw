#!/usr/bin/env python3
"""Grade v28 (v14_combined + Rule 5 Rainbow override) vs v14_combined.

Compares head-to-head on the full 6M canonical grid (N=200 oracle).
Rule 5 fires only on KK/AA hands where Rule 4 would yield a rainbow
bot (~3.7% of KK/AA = ~0.27% of all hands), so the headline change
should be small but non-negative if the rule is correctly tightened.

This is the explicit head-to-head that the Session-31 v21/v22 attempts
failed (those fired on ~26% of high_only hands and lost $473-$680).
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
    print(f"  Grid: {len(grid):,}", flush=True)

    from strategy_v14_combined import strategy_v14_combined
    from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow

    print("\nGrading v14_combined ...", flush=True)
    res_v14 = grade_strategy(strategy_v14_combined, grid, ch,
                             label="v14_combined (rules + Rule 4)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v14.summary(), flush=True)

    print("\nGrading v28 = v14 + Rule 5 (Rainbow override) ...", flush=True)
    res_v28 = grade_strategy(strategy_v28_rule5_rainbow, grid, ch,
                             label="v28 (v14 + Rule 5 rainbow)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v28.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v14, res_v28))
    delta = res_v14.mean_regret - res_v28.mean_regret
    print(f"\nv28 vs v14: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
