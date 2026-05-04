#!/usr/bin/env python3
"""Grade v20b (depth=32) vs v20 (depth=30) on full + prefix.

Both use the 43-feature gated set. v20b is one extra capacity step.
Saturation check after the v18 sweep.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np

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

    import strategy_v19_gated_dt as v19g

    def make_strategy(model_path):
        v19g.MODEL_PATH = model_path
        v19g._MODEL_CACHE = None
        # Force load by calling once.
        v19g.load_model()
        cached = v19g._MODEL_CACHE

        def fn(hand):
            v19g._MODEL_CACHE = cached
            return v19g.strategy_v19_gated_dt(hand)
        return fn

    # Sequential: load v20, grade, then load v20b, grade. Avoids cache pollution.
    print("\nGrading v20 ...", flush=True)
    fn_v20 = make_strategy(REPO / "data" / "v20_dt_model.npz")
    res_v20 = grade_strategy(fn_v20, grid, ch, label="v20 (d=30, 308K leaves)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v20.summary(), flush=True)

    print("\nGrading v20b ...", flush=True)
    fn_v20b = make_strategy(REPO / "data" / "v20b_dt_model.npz")
    res_v20b = grade_strategy(fn_v20b, grid, ch, label="v20b (d=32, 308K leaves)",
                              progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v20b.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v20, res_v20b))
    delta = res_v20.mean_regret - res_v20b.mean_regret
    print(f"\nv20b vs v20: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
