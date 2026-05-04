#!/usr/bin/env python3
"""Grade v24 (v23 + composite gated aug) vs v23 on full+prefix.

v24 adds 4 gated features that fire only on composite hands (~0.245%).
Per the gating rule, prefix tripwire should be near-tied since
composite is rare on prefix (~0.5%).
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

    import strategy_v23_dt as v23m
    import strategy_v24_dt as v24m

    v23m._MODEL_CACHE = None
    v23m.MODEL_PATH = REPO / "data" / "v23_dt_model.npz"
    v23m.load_model()

    print("\nGrading v23 ...", flush=True)
    res_v23 = grade_strategy(v23m.strategy_v23_dt, grid, ch,
                             label="v23 (v20 + trips_pair gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v23.summary(), flush=True)

    v24m._MODEL_CACHE = None
    v24m.MODEL_PATH = REPO / "data" / "v24_dt_model.npz"
    v24m.load_model()

    print("\nGrading v24 ...", flush=True)
    res_v24 = grade_strategy(v24m.strategy_v24_dt, grid, ch,
                             label="v24 (v23 + composite gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v24.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v23, res_v24))
    delta = res_v23.mean_regret - res_v24.mean_regret
    print(f"\nv24 vs v23: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
