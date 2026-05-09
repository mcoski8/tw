#!/usr/bin/env python3
"""Grade v37 (v33 + Rule 7 three_pair) head-to-head vs v33 on full + prefix.

Drill probe: +$43.05/1000h whole-grid lift on full 114K three_pair
population. Confirm at full-grid scale.
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

    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v33_rule6_trips import strategy_v33_rule6_trips
    from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair

    print("\nGrading v33 (production baseline) ...", flush=True)
    res_v33 = grade_strategy(strategy_v33_rule6_trips, grid, ch,
                             label="v33 (current production)",
                             progress_every=progress_every)
    print(res_v33.summary(), flush=True)

    print("\nGrading v37 (v33 + Rule 7 three_pair) ...", flush=True)
    res_v37 = grade_strategy(strategy_v37_rule7_three_pair, grid, ch,
                             label="v37 (v33 + Rule 7)",
                             progress_every=progress_every)
    print(res_v37.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v37 vs v33 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v33, res_v37))
    delta = res_v33.mean_regret - res_v37.mean_regret
    print(f"\nv37 vs v33: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    print("  (positive = v37 improves; expected ≈ +$43 full / +$10 prefix")
    print("   given prefix has only 25.6K three_pair hands of 500K total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
