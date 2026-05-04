#!/usr/bin/env python3
"""Grade v17 = v9.2/v10/v12 → v16 fallback against v8/v14/v16 on the full grid."""
from __future__ import annotations
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
    print(f"loading grid {GRID_FULL.name} ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}  Canonical: {len(ch):,}", flush=True)

    from strategy_v8_hybrid import strategy_v8_hybrid
    from strategy_v14_combined import strategy_v14_combined
    from strategy_v16_dt import strategy_v16_dt
    from strategy_v17_rules_then_dt import strategy_v17_rules_then_dt

    strategies = [
        ("v8_hybrid", strategy_v8_hybrid),
        ("v14_combined", strategy_v14_combined),
        ("v16_dt", strategy_v16_dt),
        ("v17_rules_then_dt", strategy_v17_rules_then_dt),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label, progress_every=2_000_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print("SUMMARY (full grid)")
    print("=" * 70)
    print(compare_grades(*results))
    v8, v14, v16, v17 = results
    print(f"\nv17 vs v16:  {v16.mean_regret - v17.mean_regret:+.4f}  ≈ ${(v16.mean_regret - v17.mean_regret) * 10 * 1000:+,.0f}/1000h")
    print(f"v17 vs v14:  {v14.mean_regret - v17.mean_regret:+.4f}  ≈ ${(v14.mean_regret - v17.mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
