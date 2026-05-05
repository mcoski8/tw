#!/usr/bin/env python3
"""Grade v27 (v26 + 4 high_only-gated aug features) vs v26 on full+prefix.

The 4 new features fire only on the high_only category (20.4% population
share). Both grids should see the change concentrate in the high_only
category, with all other categories bit-identical or within N=200 noise.
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

    import strategy_v26_dt as v26m
    import strategy_v27_dt as v27m

    v26m._MODEL_CACHE = None
    v26m.MODEL_PATH = REPO / "data" / "v26_dt_model.npz"
    v26m.load_model()

    print("\nGrading v26 ...", flush=True)
    res_v26 = grade_strategy(v26m.strategy_v26_dt, grid, ch,
                             label="v26 (v25 + two_pair gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v26.summary(), flush=True)

    v27m._MODEL_CACHE = None
    v27m.MODEL_PATH = REPO / "data" / "v27_dt_model.npz"
    v27m.load_model()

    print("\nGrading v27 ...", flush=True)
    res_v27 = grade_strategy(v27m.strategy_v27_dt, grid, ch,
                             label="v27 (v26 + high_only gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v27.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v26, res_v27))
    delta = res_v26.mean_regret - res_v27.mean_regret
    print(f"\nv27 vs v26: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
