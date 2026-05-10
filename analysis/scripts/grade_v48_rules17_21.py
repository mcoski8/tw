#!/usr/bin/env python3
"""Grade v48 (v47 + Rules 17-21 J-7-high HIMID) vs v47 head-to-head."""
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

    from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS
    from strategy_v48_rules17_21_high_only_HIMID import strategy_v48_rules17_21_high_only_HIMID

    print("\nGrading v47 ...", flush=True)
    res_v47 = grade_strategy(strategy_v47_rule16_Qhigh_DS, grid, ch,
                              label="v47 (current production)",
                              progress_every=progress_every)
    print(res_v47.summary(), flush=True)

    print("\nGrading v48 (v47 + Rules 17-21) ...", flush=True)
    res_v48 = grade_strategy(strategy_v48_rules17_21_high_only_HIMID, grid, ch,
                              label="v48 (v47 + Rules 17-21)",
                              progress_every=progress_every)
    print(res_v48.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v48 vs v47 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v47, res_v48))
    delta = res_v47.mean_regret - res_v48.mean_regret
    print(f"\nv48 vs v47: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
