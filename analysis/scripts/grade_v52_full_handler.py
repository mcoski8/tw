#!/usr/bin/env python3
"""Grade v52 (v47 + comprehensive high_only handler) vs v47 head-to-head."""
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
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS
    from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler

    res_v47 = grade_strategy(strategy_v47_rule16_Qhigh_DS, grid, ch,
                              label="v47 (current production)",
                              progress_every=progress_every)
    print(res_v47.summary(), flush=True)

    res_v52 = grade_strategy(strategy_v52_full_high_only_handler, grid, ch,
                              label="v52 (v47 + comprehensive high_only)",
                              progress_every=progress_every)
    print(res_v52.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v52 vs v47 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v47, res_v52))
    delta = res_v47.mean_regret - res_v52.mean_regret
    print(f"\nv52 vs v47: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
