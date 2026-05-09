#!/usr/bin/env python3
"""Grade v40 (v39 + Rule 10 J-low pair defensive) vs v39 head-to-head."""
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
    ap.add_argument("--grid", choices=["full", "prefix"], default="full")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")

    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v39_rule9 import strategy_v39_rule9  # noqa: E402
    from strategy_v40_rule10 import strategy_v40_rule10  # noqa: E402

    print("\nGrading v39 (prior production) ...", flush=True)
    res_v39 = grade_strategy(strategy_v39_rule9, grid, ch,
                              label="v39 (prior production)",
                              progress_every=progress_every)
    print(res_v39.summary(), flush=True)

    print("\nGrading v40 (v39 + Rule 10 J-low pair defensive) ...", flush=True)
    res_v40 = grade_strategy(strategy_v40_rule10, grid, ch,
                              label="v40 (v39 + Rule 10)",
                              progress_every=progress_every)
    print(res_v40.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v40 vs v39 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v39, res_v40))
    delta = res_v39.mean_regret - res_v40.mean_regret
    print(f"\nv40 vs v39: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    print("  (positive = v40 improves; expected ~+$22 full / ~+$36 prefix "
           "from drill_low_pair_J_high_defense.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
