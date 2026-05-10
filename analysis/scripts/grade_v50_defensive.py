#!/usr/bin/env python3
"""Grade v50 (v48 + Rules 22-24 high_only A/K/Q/J defensive 2nd≤8) vs v48."""
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
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v48_rules17_21_high_only_HIMID import strategy_v48_rules17_21_high_only_HIMID
    from strategy_v50_rules22_23_high_only_defensive import strategy_v50_rules22_23_high_only_defensive

    res_v48 = grade_strategy(strategy_v48_rules17_21_high_only_HIMID, grid, ch,
                              label="v48 (current candidate)",
                              progress_every=progress_every)
    print(res_v48.summary(), flush=True)

    res_v50 = grade_strategy(strategy_v50_rules22_23_high_only_defensive, grid, ch,
                              label="v50 (v48 + Rules 22-24)",
                              progress_every=progress_every)
    print(res_v50.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v50 vs v48 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v48, res_v50))
    delta = res_v48.mean_regret - res_v50.mean_regret
    print(f"\nv50 vs v48: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
