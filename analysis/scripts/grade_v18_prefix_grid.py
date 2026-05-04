#!/usr/bin/env python3
"""Validate v18 on the N=1000 prefix grid (tighter labels, smaller scope).

If v18's win on the full grid (+$158/1000h) is real, it should also
appear on the prefix. If v18 overfit to the noisy N=200 labels, the
prefix grade will regress vs v16."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid


GRID_PREFIX = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    print(f"loading grid {GRID_PREFIX.name} ...", flush=True)
    grid = read_oracle_grid(GRID_PREFIX, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}  Canonical: {len(ch):,}", flush=True)

    from strategy_v8_hybrid import strategy_v8_hybrid
    from strategy_v14_combined import strategy_v14_combined
    from strategy_v16_dt import strategy_v16_dt
    from strategy_v18_dt import strategy_v18_dt

    strategies = [
        ("v8_hybrid", strategy_v8_hybrid),
        ("v14_combined", strategy_v14_combined),
        ("v16_dt", strategy_v16_dt),
        ("v18_dt", strategy_v18_dt),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label, progress_every=200_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print("SUMMARY (prefix N=1000 grid)")
    print("=" * 70)
    print(compare_grades(*results))
    v8, v14, v16, v18 = results
    print(f"\nv18 vs v16:  {v16.mean_regret - v18.mean_regret:+.4f}  ≈ ${(v16.mean_regret - v18.mean_regret) * 10 * 1000:+,.0f}/1000h")
    print(f"v18 vs v14:  {v14.mean_regret - v18.mean_regret:+.4f}  ≈ ${(v14.mean_regret - v18.mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
