#!/usr/bin/env python3
"""Session 38 — grade v32_d34ml2 + v32_d34ml3 vs the v32 (depth=32 ml=3)
champion on full + prefix grids.
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

    # All three models share the v31b harness pipeline.
    import strategy_v32_dt as v32_m

    # v32 (champion: depth=32 ml=3, 731,606 leaves)
    v32_m._MODEL_CACHE = None
    v32_m.MODEL_PATH = REPO / "data" / "v32_dt_model.npz"
    v32_m.load_model()
    print("\nGrading v32 (champion: depth=32 ml=3) ...", flush=True)
    res_v32 = grade_strategy(v32_m.strategy_v32_dt, grid, ch,
                             label="v32 (champion d32ml3)",
                             progress_every=progress_every)
    print(res_v32.summary(), flush=True)

    # v32_d34ml3 (control)
    v32_m._MODEL_CACHE = None
    v32_m.MODEL_PATH = REPO / "data" / "v32_d34ml3_dt_model.npz"
    v32_m.load_model()
    print("\nGrading v32_d34ml3 (control: depth=34 ml=3) ...", flush=True)
    res_v32_d34ml3 = grade_strategy(v32_m.strategy_v32_dt, grid, ch,
                                    label="v32_d34ml3",
                                    progress_every=progress_every)
    print(res_v32_d34ml3.summary(), flush=True)

    # v32_d34ml2 (high capacity candidate)
    v32_m._MODEL_CACHE = None
    v32_m.MODEL_PATH = REPO / "data" / "v32_d34ml2_dt_model.npz"
    v32_m.load_model()
    print("\nGrading v32_d34ml2 (candidate: depth=34 ml=2) ...", flush=True)
    res_v32_d34ml2 = grade_strategy(v32_m.strategy_v32_dt, grid, ch,
                                    label="v32_d34ml2",
                                    progress_every=progress_every)
    print(res_v32_d34ml2.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v32_d34ml3 vs v32 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v32, res_v32_d34ml3))
    delta = res_v32.mean_regret - res_v32_d34ml3.mean_regret
    print(f"\nv32_d34ml3 vs v32: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)

    print("\n" + "=" * 70)
    print(f"v32_d34ml2 vs v32 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v32, res_v32_d34ml2))
    delta = res_v32.mean_regret - res_v32_d34ml2.mean_regret
    print(f"\nv32_d34ml2 vs v32: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)

    print("\n" + "=" * 70)
    print(f"v32_d34ml2 vs v32_d34ml3 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v32_d34ml3, res_v32_d34ml2))
    delta = res_v32_d34ml3.mean_regret - res_v32_d34ml2.mean_regret
    print(f"\nv32_d34ml2 vs v32_d34ml3: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
