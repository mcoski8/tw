#!/usr/bin/env python3
"""Grade v48_dt vs v44_dt (added H6/H7/H8 pair features)."""
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

    from strategy_v44_dt import strategy_v44_dt
    from strategy_v48_dt import strategy_v48_dt

    res_v44 = grade_strategy(strategy_v44_dt, grid, ch,
                              label="v44_dt (baseline)",
                              progress_every=progress_every)
    print(res_v44.summary(), flush=True)

    res_v48 = grade_strategy(strategy_v48_dt, grid, ch,
                              label="v48_dt (+ H6/H7/H8)",
                              progress_every=progress_every)
    print(res_v48.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v48_dt vs v44_dt ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v44, res_v48))
    delta = res_v44.mean_regret - res_v48.mean_regret
    print(f"\nv48_dt vs v44_dt: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
