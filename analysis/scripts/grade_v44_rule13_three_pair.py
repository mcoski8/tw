#!/usr/bin/env python3
"""Grade v44 (v43 + Rule 13 three_pair all-intact + DS) vs v43 head-to-head."""
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

    from strategy_v43_rule12_two_pair_DS_intact import strategy_v43_rule12_two_pair_DS_intact
    from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS

    print("\nGrading v43 (current production) ...", flush=True)
    res_v43 = grade_strategy(strategy_v43_rule12_two_pair_DS_intact, grid, ch,
                              label="v43 (current production)",
                              progress_every=progress_every)
    print(res_v43.summary(), flush=True)

    print("\nGrading v44 (v43 + Rule 13 three_pair) ...", flush=True)
    res_v44 = grade_strategy(strategy_v44_rule13_three_pair_DS, grid, ch,
                              label="v44 (v43 + Rule 13)",
                              progress_every=progress_every)
    print(res_v44.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v44 vs v43 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v43, res_v44))
    delta = res_v43.mean_regret - res_v44.mean_regret
    print(f"\nv44 vs v43: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
