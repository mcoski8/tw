#!/usr/bin/env python3
"""Grade v21 (v14 + Rule 5 high_only suited mid) head-to-head with v14
on full grid + prefix grid.

Rule 5 is the human-memorizable distillation of v20's gated suited
features. This script answers: does adding it to the v14 chain
materially improve the human strategy of record?
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
    print(f"  Grid: {len(grid):,}  Canonical: {len(ch):,}", flush=True)

    from strategy_v14_combined import strategy_v14_combined
    from strategy_v21_combined import strategy_v21_combined

    strategies = [
        ("v14 (Rules 1+2+3 + v8 fallback w/Rule 4)", strategy_v14_combined),
        ("v21 (v14 + Rule 5 high_only suited mid)", strategy_v21_combined),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label,
                             progress_every=1_000_000 if args.grid == "full" else 100_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(*results))
    v14 = results[0]; v21 = results[1]
    delta = v14.mean_regret - v21.mean_regret
    print(f"\nv21 vs v14: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
