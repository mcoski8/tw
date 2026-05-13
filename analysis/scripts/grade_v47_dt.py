#!/usr/bin/env python3
"""Grade v47_dt vs v44_dt — H2 isolation experiment (v44 + ho_v7 route-tradeoff
comparator at depth=36 ml=1, v44's saturating regime)."""
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
    ap.add_argument("--baseline", choices=["v44", "v45", "v46", "v46b"], default="v44")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    if args.baseline == "v44":
        from strategy_v44_dt import strategy_v44_dt as baseline_fn
        baseline_label = "v44_dt"
    elif args.baseline == "v45":
        from strategy_v45_dt import strategy_v45_dt as baseline_fn
        baseline_label = "v45_dt"
    elif args.baseline == "v46":
        from strategy_v46_dt import strategy_v46_dt as baseline_fn
        baseline_label = "v46_dt"
    else:
        from strategy_v46b_dt import strategy_v46b_dt as baseline_fn
        baseline_label = "v46b_dt"
    from strategy_v47_dt import strategy_v47_dt

    res_base = grade_strategy(baseline_fn, grid, ch,
                                label=f"{baseline_label} (baseline)",
                                progress_every=progress_every)
    print(res_base.summary(), flush=True)

    res_v47 = grade_strategy(strategy_v47_dt, grid, ch,
                             label="v47_dt (+ ho_v7 route-tradeoff @ depth=36 ml=1)",
                             progress_every=progress_every)
    print(res_v47.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v47_dt vs {baseline_label} ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_base, res_v47))
    delta = res_base.mean_regret - res_v47.mean_regret
    print(f"\nv47_dt vs {baseline_label}: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
