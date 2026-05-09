#!/usr/bin/env python3
"""Grade v38 (v37 + Rule 8 composite-QP) head-to-head vs v37 on full +
prefix. Rule: "for quads_pair (4+2+1), top=singleton, mid=2 quad cards
at non-pair-suits, bot=other 2 quads + pair". 100% deterministic.

Probe headlines:
  Δ vs v33 = +$9.42/1000h whole-grid (full N=200)
  Δ vs v33 = +$18.63/1000h whole-prefix (N=1000)

Note: the original two_pair Rule 8 candidate (probe headline +$197 on
full, but -$512 on prefix) was DEFERRED — see Session 42 entry in the
strategy guide for the full reasoning. v38 ships with the smaller but
both-grid-positive composite QP rule.
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

    from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair
    from strategy_v38_rule8_qp import strategy_v38_rule8_qp

    print("\nGrading v37 (prior production baseline) ...", flush=True)
    res_v37 = grade_strategy(strategy_v37_rule7_three_pair, grid, ch,
                             label="v37 (prior production)",
                             progress_every=progress_every)
    print(res_v37.summary(), flush=True)

    print("\nGrading v38 (v37 + Rule 8 composite-QP) ...", flush=True)
    res_v38 = grade_strategy(strategy_v38_rule8_qp, grid, ch,
                             label="v38 (v37 + Rule 8 QP)",
                             progress_every=progress_every)
    print(res_v38.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v38 vs v37 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v37, res_v38))
    delta = res_v37.mean_regret - res_v38.mean_regret
    print(f"\nv38 vs v37: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    print("  (positive = v38 improves; expected ≈ +$9.42 full / +$18.63 prefix")
    print("   from the deterministic-QP probe headline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
