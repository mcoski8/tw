#!/usr/bin/env python3
"""Grade v23 (v20 + trips_pair gated aug) vs v20 on full+prefix.

v23 adds 6 gated features that fire only on trips_pair hands (~2.86% of
canonical population). Per the gating rule, prefix tripwire should pass
trivially since the new features can fire on at most the trips_pair
fraction of prefix hands and any change to non-trips_pair routing
indicates over-fit.
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

    # v20 inference uses strategy_v19_gated_dt with v20 model.
    import strategy_v19_gated_dt as v19g
    import strategy_v23_dt as v23m

    # Hard-reset module caches so they don't leak across calls.
    v19g._MODEL_CACHE = None
    v19g.MODEL_PATH = REPO / "data" / "v20_dt_model.npz"
    v19g.load_model()
    cached_v20 = v19g._MODEL_CACHE
    v19g._MODEL_CACHE = cached_v20

    def fn_v20(hand):
        v19g._MODEL_CACHE = cached_v20
        return v19g.strategy_v19_gated_dt(hand)

    print("\nGrading v20 ...", flush=True)
    res_v20 = grade_strategy(fn_v20, grid, ch, label="v20 (champion, 308K leaves)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v20.summary(), flush=True)

    v23m._MODEL_CACHE = None
    v23m.MODEL_PATH = REPO / "data" / "v23_dt_model.npz"
    v23m.load_model()

    print("\nGrading v23 ...", flush=True)
    res_v23 = grade_strategy(v23m.strategy_v23_dt, grid, ch,
                             label="v23 (v20 + trips_pair gated)",
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
    print(res_v23.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v20, res_v23))
    delta = res_v20.mean_regret - res_v23.mean_regret
    print(f"\nv23 vs v20: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
