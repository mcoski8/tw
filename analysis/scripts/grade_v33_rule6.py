#!/usr/bin/env python3
"""Grade v33 (v28 + Rule 6 trips override) head-to-head vs v28 on full+prefix.

Trips probe (verify_rule6_v14_trips + probe_v33_trips) shows:
  - Always-A∪C oracle ceiling: $+197/1000h whole-grid over v14
  - v33 heuristic: $+111/1000h whole-grid (56% capture) on the trips slice
Expectation: v33 vs v28 full-grid delta ≈ +$110/1000h.
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

    from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips

    print("\nGrading v28 (v14 + Rule 4 + Rule 5) ...", flush=True)
    res_v28 = grade_strategy(strategy_v28_rule5_rainbow, grid, ch,
                             label="v28 (current human champ)",
                             progress_every=progress_every)
    print(res_v28.summary(), flush=True)

    print("\nGrading v33 (v28 + Rule 6 trips) ...", flush=True)
    res_v33 = grade_strategy(strategy_v33_rule6_trips, grid, ch,
                             label="v33 (v28 + Rule 6)",
                             progress_every=progress_every)
    print(res_v33.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v33 vs v28 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v28, res_v33))
    delta = res_v28.mean_regret - res_v33.mean_regret
    print(f"\nv33 vs v28: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
