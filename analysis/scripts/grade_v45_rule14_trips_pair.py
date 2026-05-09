#!/usr/bin/env python3
"""Grade v45 (v44 + Rule 14 trips_pair pair-bot DS) vs v44 head-to-head."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.grade_strategy import compare_grades, grade_strategy  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", choices=["full", "prefix"], default="prefix")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS
    from strategy_v45_rule14_trips_pair_DS import strategy_v45_rule14_trips_pair_DS

    print("\nGrading v44 (current production) ...", flush=True)
    res_v44 = grade_strategy(strategy_v44_rule13_three_pair_DS, grid, ch,
                              label="v44 (current production)",
                              progress_every=progress_every)
    print(res_v44.summary(), flush=True)

    print("\nGrading v45 (v44 + Rule 14 trips_pair) ...", flush=True)
    res_v45 = grade_strategy(strategy_v45_rule14_trips_pair_DS, grid, ch,
                              label="v45 (v44 + Rule 14)",
                              progress_every=progress_every)
    print(res_v45.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v45 vs v44 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v44, res_v45))
    delta = res_v44.mean_regret - res_v45.mean_regret
    print(f"\nv45 vs v44: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
