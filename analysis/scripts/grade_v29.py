#!/usr/bin/env python3
"""Grade v29 (v27 + 4 pair-gated v2 features) vs v27 on full+prefix.

Pair-gated v2 features (`pair_r4_*_g`) target the v27→Rule-4 KK/AA gap
identified by the Session-35 distill. Diagnostic predicted up to
$62/1000h whole-grid available on KK/AA alone.
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

    import strategy_v27_dt as v27m
    import strategy_v29_dt as v29m

    v27m._MODEL_CACHE = None
    v27m.MODEL_PATH = REPO / "data" / "v27_dt_model.npz"
    v27m.load_model()

    print("\nGrading v27 ...", flush=True)
    res_v27 = grade_strategy(v27m.strategy_v27_dt, grid, ch,
                             label="v27 (v26 + high_only gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v27.summary(), flush=True)

    v29m._MODEL_CACHE = None
    v29m.MODEL_PATH = REPO / "data" / "v29_dt_model.npz"
    v29m.load_model()

    print("\nGrading v29 ...", flush=True)
    res_v29 = grade_strategy(v29m.strategy_v29_dt, grid, ch,
                             label="v29 (v27 + pair_r4 gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v29.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v27, res_v29))
    delta = res_v27.mean_regret - res_v29.mean_regret
    print(f"\nv29 vs v27: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
