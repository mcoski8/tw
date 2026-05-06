#!/usr/bin/env python3
"""Grade v31c (v30 features at depth=32 ml=3) vs v30 on full+prefix.

v31c uses the same 79 features as v30 but with higher capacity. Tests
whether trips routing decisions need MORE LEAVES rather than smarter
features. If v31c beats v30 by a notable margin, capacity is still the
binding constraint.
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

    # v31c reuses v30's strategy harness — same 79 features, just a different model file
    import strategy_v30_dt as harness

    harness._MODEL_CACHE = None
    harness.MODEL_PATH = REPO / "data" / "v30_dt_model.npz"
    harness.load_model()
    print("\nGrading v30 ...", flush=True)
    res_v30 = grade_strategy(harness.strategy_v30_dt, grid, ch,
                             label="v30 (depth=30 ml=5)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v30.summary(), flush=True)

    # Reload model cache for v31c
    harness._MODEL_CACHE = None
    harness.MODEL_PATH = REPO / "data" / "v31c_dt_model.npz"
    harness.load_model()
    print("\nGrading v31c ...", flush=True)
    res_v31c = grade_strategy(harness.strategy_v30_dt, grid, ch,
                              label="v31c (v30 features, depth=32 ml=3)",
                              progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v31c.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v30, res_v31c))
    delta = res_v30.mean_regret - res_v31c.mean_regret
    print(f"\nv31c vs v30: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
