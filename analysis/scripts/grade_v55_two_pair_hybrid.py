#!/usr/bin/env python3
"""Grade v55 (v54 + blanket two_pair → v44_dt) vs v54 head-to-head.

Per TWO_PAIR_DECISION_MATRIX.md Phase 2 finding: v54 leaks $634/1000h
WG vs v44 on two_pair (canonical-equal framing). v55 closes the entire
gap by routing two_pair → v44.

Expected lift (harness prediction): $634 WG full-grid; ~$300 WG prefix.
If realized, this is the LARGEST single production ship in project
history (1.7× S68's record $382).
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

    from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid
    from strategy_v55_two_pair_hybrid import strategy_v55_two_pair_hybrid

    print("\nGrading v54 (current production: pair-hybrid + v53-fallthrough) ...", flush=True)
    res_v54 = grade_strategy(strategy_v54_pair_hybrid, grid, ch,
                              label="v54 (pair hybrid)",
                              progress_every=progress_every)
    print(res_v54.summary(), flush=True)

    print("\nGrading v55 (v54 + blanket two_pair → v44_dt) ...", flush=True)
    res_v55 = grade_strategy(strategy_v55_two_pair_hybrid, grid, ch,
                              label="v55 (two_pair hybrid)",
                              progress_every=progress_every)
    print(res_v55.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v55 vs v54 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v54, res_v55))
    delta = res_v54.mean_regret - res_v55.mean_regret
    print(f"\nv55 vs v54: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
