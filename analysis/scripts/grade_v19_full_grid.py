#!/usr/bin/env python3
"""Grade v19 (43 features incl. suited-broadway) vs v16/v18 on full + prefix grids."""
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

    from strategy_v16_dt import strategy_v16_dt
    from strategy_v18_dt import strategy_v18_dt
    from strategy_v19_dt import strategy_v19_dt

    strategies = [
        ("v16_dt (28K leaves, 37 feat)", strategy_v16_dt),
        ("v18_dt (60K leaves, 37 feat)", strategy_v18_dt),
        ("v19_dt (73K leaves, 43 feat +suited)", strategy_v19_dt),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label, progress_every=2_000_000 if args.grid == "full" else 200_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(*results))
    v16, v18, v19 = results
    print(f"\nv19 vs v18:  {v18.mean_regret - v19.mean_regret:+.4f}  ≈ ${(v18.mean_regret - v19.mean_regret) * 10 * 1000:+,.0f}/1000h")
    print(f"v19 vs v16:  {v16.mean_regret - v19.mean_regret:+.4f}  ≈ ${(v16.mean_regret - v19.mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
