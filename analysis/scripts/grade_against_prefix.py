#!/usr/bin/env python3
"""Re-grade v8 / v9.1 / v10 against the N=1000 prefix grid (first 500K
canonical hands at higher MC fidelity). Confirms v10's +$105/1000h gain
isn't N=200 noise.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))
sys.path.insert(0, str(REPO / "trainer" / "src"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid


def main() -> int:
    grid_path = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
    canon_path = REPO / "data" / "canonical_hands.bin"

    print(f"Loading prefix grid (N=1000, 500K hands) from {grid_path} ...")
    grid = read_oracle_grid(grid_path, mode="memmap")
    print(f"  {len(grid):,} records  N={grid.header.samples}  opp={grid.header.opp_label}")
    ch = read_canonical_hands(canon_path, mode="memmap")

    from strategy_v8_hybrid import strategy_v8_hybrid
    from strategy_v9_1_pair_to_bot_ds import strategy_v9_1_pair_to_bot_ds
    from strategy_v10_two_pair_no_split import strategy_v10_two_pair_no_split

    strategies = [
        ("v8_hybrid", strategy_v8_hybrid),
        ("v9.1 (pair-to-bot-DS, tight)", strategy_v9_1_pair_to_bot_ds),
        ("v10 (v9.1 + two_pair no-split)", strategy_v10_two_pair_no_split),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} on prefix N=1000 ...")
        res = grade_strategy(
            fn, grid, ch, label=label,
            max_hands=len(grid),
            progress_every=100_000,
        )
        print(res.summary())
        results.append(res)

    print("\n\n" + "=" * 70)
    print("PREFIX GRID (N=1000, 500K hands) — TIGHTER CONFIRMATION")
    print("=" * 70)
    print(compare_grades(*results))

    v8 = results[0]
    v91 = results[1]
    v10 = results[2]
    for label, cand in [("v9.1", v91), ("v10", v10)]:
        delta = v8.mean_regret - cand.mean_regret
        print(
            f"\n{label} vs v8 on prefix N=1000:  reduction = {delta:+.4f}  "
            f"≈ ${delta * 10 * 1000:+,.0f}/1000h  pct_optimal {cand.pct_optimal - v8.pct_optimal:+.2f} pp"
        )
    print(
        f"\nv10 vs v9.1 incremental: {v91.mean_regret - v10.mean_regret:+.4f}  "
        f"≈ ${(v91.mean_regret - v10.mean_regret) * 10 * 1000:+,.0f}/1000h"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
