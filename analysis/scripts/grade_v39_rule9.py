#!/usr/bin/env python3
"""Grade v39 (v38 + Rule 9 plain-quads + TT E3a) head-to-head vs v38."""
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

    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v38_rule8_qp import strategy_v38_rule8_qp
    from strategy_v39_rule9 import strategy_v39_rule9

    print("\nGrading v38 (prior production) ...", flush=True)
    res_v38 = grade_strategy(strategy_v38_rule8_qp, grid, ch,
                             label="v38 (prior production)",
                             progress_every=progress_every)
    print(res_v38.summary(), flush=True)

    print("\nGrading v39 (v38 + Rule 9 plain-quads + TT E3a) ...", flush=True)
    res_v39 = grade_strategy(strategy_v39_rule9, grid, ch,
                             label="v39 (v38 + Rule 9)",
                             progress_every=progress_every)
    print(res_v39.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v39 vs v38 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v38, res_v39))
    delta = res_v38.mean_regret - res_v39.mean_regret
    print(f"\nv39 vs v38: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    print("  (positive = v39 improves; expected ≈ +$19 full / +$14 prefix)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
