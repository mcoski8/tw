#!/usr/bin/env python3
"""Grade v41_dt vs v40_dt (added 4 two_pair_aug_v2 features)."""
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
    ap.add_argument("--baseline", choices=["v39", "v40"], default="v40")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    if args.baseline == "v40":
        from strategy_v40_dt import strategy_v40_dt as baseline_fn
        baseline_label = "v40_dt"
    else:
        from strategy_v39_dt import strategy_v39_dt as baseline_fn
        baseline_label = "v39_dt"
    from strategy_v41_dt import strategy_v41_dt

    res_base = grade_strategy(baseline_fn, grid, ch,
                                label=f"{baseline_label} (baseline)",
                                progress_every=progress_every)
    print(res_base.summary(), flush=True)

    res_v41 = grade_strategy(strategy_v41_dt, grid, ch,
                              label="v41_dt (+ two_pair_aug_v2)",
                              progress_every=progress_every)
    print(res_v41.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v41_dt vs {baseline_label} ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_base, res_v41))
    delta = res_base.mean_regret - res_v41.mean_regret
    print(f"\nv41_dt vs {baseline_label}: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
