#!/usr/bin/env python3
"""Grade v25 (v24 + 6 pair-gated aug features) vs v24 on full+prefix.

The 6 new pair-gated features fire only on the single-pair category
(46.6% population share). Both grids should see the change concentrate
in the pair category, with all other categories bit-identical or
within N=200 noise.
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

    import strategy_v24_dt as v24m
    import strategy_v25_dt as v25m

    v24m._MODEL_CACHE = None
    v24m.MODEL_PATH = REPO / "data" / "v24_dt_model.npz"
    v24m.load_model()

    print("\nGrading v24 ...", flush=True)
    res_v24 = grade_strategy(v24m.strategy_v24_dt, grid, ch,
                             label="v24 (v23 + composite gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v24.summary(), flush=True)

    v25m._MODEL_CACHE = None
    v25m.MODEL_PATH = REPO / "data" / "v25_dt_model.npz"
    v25m.load_model()

    print("\nGrading v25 ...", flush=True)
    res_v25 = grade_strategy(v25m.strategy_v25_dt, grid, ch,
                             label="v25 (v24 + pair gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v25.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v24, res_v25))
    delta = res_v24.mean_regret - res_v25.mean_regret
    print(f"\nv25 vs v24: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
