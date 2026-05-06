#!/usr/bin/env python3
"""Grade v31a (v30 + 4 pair-r4v3 KK/AA-tight features) vs v30 on full+prefix."""
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

    import strategy_v30_dt as v30m
    import strategy_v31a_dt as v31a_m

    v30m._MODEL_CACHE = None
    v30m.MODEL_PATH = REPO / "data" / "v30_dt_model.npz"
    v30m.load_model()
    print("\nGrading v30 ...", flush=True)
    res_v30 = grade_strategy(v30m.strategy_v30_dt, grid, ch,
                             label="v30 (v29 + trips gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v30.summary(), flush=True)

    v31a_m._MODEL_CACHE = None
    v31a_m.MODEL_PATH = REPO / "data" / "v31a_dt_model.npz"
    v31a_m.load_model()
    print("\nGrading v31a ...", flush=True)
    res_v31a = grade_strategy(v31a_m.strategy_v31a_dt, grid, ch,
                              label="v31a (v30 + pair_r4v3 KK/AA-tight)",
                              progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v31a.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v30, res_v31a))
    delta = res_v30.mean_regret - res_v31a.mean_regret
    print(f"\nv31a vs v30: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
