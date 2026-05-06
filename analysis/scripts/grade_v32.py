#!/usr/bin/env python3
"""Grade v32 (v31b features at v31's high capacity) head-to-head vs the
current ML champion v31, plus a delta vs v30 for the cumulative ship size.

v32 = 83 features (79 v30 + 4 trips_v2 round-2) at depth=32 ml=3.
v31 = 79 v30 features at depth=32 ml=3 (current champion).
v30 = 79 features at depth=30 ml=5.
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
    ap.add_argument("--also-vs-v30", action="store_true",
                    help="Also grade v30 for the v32-vs-v30 cumulative delta")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}", flush=True)

    progress_every = 2_000_000 if args.grid == "full" else 200_000

    # v31 — current champion (uses v30's harness with v31 model file)
    import strategy_v30_dt as v30_harness
    import strategy_v31b_dt as v31b_harness
    import strategy_v32_dt as v32_m

    v30_harness._MODEL_CACHE = None
    v30_harness.MODEL_PATH = REPO / "data" / "v31_dt_model.npz"
    v30_harness.load_model()
    print("\nGrading v31 (champion: 79 features, depth=32 ml=3) ...", flush=True)
    res_v31 = grade_strategy(v30_harness.strategy_v30_dt, grid, ch,
                             label="v31 (champion)",
                             progress_every=progress_every)
    print(res_v31.summary(), flush=True)

    # v32 — candidate
    v32_m._MODEL_CACHE = None
    v32_m.MODEL_PATH = REPO / "data" / "v32_dt_model.npz"
    v32_m.load_model()
    print("\nGrading v32 (83 features, depth=32 ml=3) ...", flush=True)
    res_v32 = grade_strategy(v32_m.strategy_v32_dt, grid, ch,
                             label="v32 (candidate)",
                             progress_every=progress_every)
    print(res_v32.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v32 vs v31 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v31, res_v32))
    delta_31 = res_v31.mean_regret - res_v32.mean_regret
    print(f"\nv32 vs v31: {delta_31:+.4f}  ≈ ${delta_31 * 10 * 1000:+,.0f}/1000h",
          flush=True)

    if args.also_vs_v30:
        # Reset cache for v30
        v30_harness._MODEL_CACHE = None
        v30_harness.MODEL_PATH = REPO / "data" / "v30_dt_model.npz"
        v30_harness.load_model()
        print("\nGrading v30 (depth=30 ml=5) ...", flush=True)
        res_v30 = grade_strategy(v30_harness.strategy_v30_dt, grid, ch,
                                 label="v30",
                                 progress_every=progress_every)
        print(res_v30.summary(), flush=True)

        print("\n" + "=" * 70)
        print(f"v32 vs v30 (cumulative since Session 36 start, {args.grid} grid)")
        print("=" * 70)
        print(compare_grades(res_v30, res_v32))
        delta_30 = res_v30.mean_regret - res_v32.mean_regret
        print(f"\nv32 vs v30: {delta_30:+.4f}  ≈ ${delta_30 * 10 * 1000:+,.0f}/1000h",
              flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
