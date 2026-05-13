#!/usr/bin/env python3
"""Grade v56 (v55 + blanket trips → v44_dt) vs v55 head-to-head.

Per TRIPS_DECISION_MATRIX.md Phase 2 finding: v55 leaks $44.61/1000h
WG vs v44 on trips (canonical-equal framing). v56 closes the entire
gap by routing trips → v44.

Expected lift (harness prediction): $44.61 WG full-grid; ~$20 WG prefix.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.grade_strategy import compare_grades, grade_strategy  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

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
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v55_two_pair_hybrid import strategy_v55_two_pair_hybrid
    from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid

    print("\nGrading v55 (current production: two_pair hybrid) ...", flush=True)
    res_v55 = grade_strategy(strategy_v55_two_pair_hybrid, grid, ch,
                              label="v55 (two_pair hybrid)",
                              progress_every=progress_every)
    print(res_v55.summary(), flush=True)

    print("\nGrading v56 (v55 + blanket trips → v44_dt) ...", flush=True)
    res_v56 = grade_strategy(strategy_v56_trips_hybrid, grid, ch,
                              label="v56 (trips hybrid)",
                              progress_every=progress_every)
    print(res_v56.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v56 vs v55 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v55, res_v56))
    delta = res_v55.mean_regret - res_v56.mean_regret
    print(f"\nv56 vs v55: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
