#!/usr/bin/env python3
"""Grade v54 (cell-routed hybrid: v44 on pair PBOT cells, v53 elsewhere)
vs v53 head-to-head."""
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

    from strategy_v53_qpair_joint_pbot import strategy_v53_qpair_joint_pbot
    from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid

    print("\nGrading v53 (current production) ...", flush=True)
    res_v53 = grade_strategy(strategy_v53_qpair_joint_pbot, grid, ch,
                              label="v53 (current production)",
                              progress_every=progress_every)
    print(res_v53.summary(), flush=True)

    print("\nGrading v54 (cell-routed hybrid v44-on-PBOT + v53-elsewhere) ...", flush=True)
    res_v54 = grade_strategy(strategy_v54_pair_hybrid, grid, ch,
                              label="v54 (pair hybrid)",
                              progress_every=progress_every)
    print(res_v54.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v54 vs v53 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v53, res_v54))
    delta = res_v53.mean_regret - res_v54.mean_regret
    print(f"\nv54 vs v53: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
