#!/usr/bin/env python3
"""Grade v43 (v42 + Rule 12 two_pair both-intact + DS) vs v42 head-to-head."""
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

    from strategy_v42_rule11_jpair_pbot_ds import strategy_v42_rule11_jpair_pbot_ds
    from strategy_v43_rule12_two_pair_DS_intact import strategy_v43_rule12_two_pair_DS_intact

    print("\nGrading v42 (current production) ...", flush=True)
    res_v42 = grade_strategy(strategy_v42_rule11_jpair_pbot_ds, grid, ch,
                              label="v42 (current production)",
                              progress_every=progress_every)
    print(res_v42.summary(), flush=True)

    print("\nGrading v43 (v42 + Rule 12 two_pair both-intact + DS) ...", flush=True)
    res_v43 = grade_strategy(strategy_v43_rule12_two_pair_DS_intact, grid, ch,
                              label="v43 (v42 + Rule 12)",
                              progress_every=progress_every)
    print(res_v43.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v43 vs v42 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v42, res_v43))
    delta = res_v42.mean_regret - res_v43.mean_regret
    print(f"\nv43 vs v42: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
