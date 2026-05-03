#!/usr/bin/env python3
"""Grade v9_pair_to_bot_ds against the Full Oracle Grid alongside v3 and
v8_hybrid for direct comparison.

Run after the Q4 characterization confirms (or refutes) the archetype the
v9 rule targets. If v9 beats v8_hybrid, the rule captures real EV; if it
loses or ties, the archetype needs more nuance (multi-pair extension,
AA-edge-cases, etc.).
"""
from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-hands", type=int, default=None)
    args = parser.parse_args()

    grid_path = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
    canon_path = REPO / "data" / "canonical_hands.bin"

    print(f"Loading grid (memmap) ...")
    grid = read_oracle_grid(grid_path, mode="memmap")
    print(f"  {len(grid):,} records  opp={grid.header.opp_label}  N={grid.header.samples}")
    print(f"\nLoading canonical hands ...")
    ch = read_canonical_hands(canon_path, mode="memmap")
    print(f"  {len(ch):,} hands.")

    from encode_rules import strategy_v3
    from strategy_v8_hybrid import strategy_v8_hybrid
    from strategy_v9_pair_to_bot_ds import strategy_v9_pair_to_bot_ds
    from strategy_v9_1_pair_to_bot_ds import strategy_v9_1_pair_to_bot_ds

    strategies = [
        ("v3 (production hand-coded)", strategy_v3),
        ("v8_hybrid (v7 + v3 high_only/pair + AAKK)", strategy_v8_hybrid),
        ("v9 (loose: any pair 2-12 + Ace + DS)", strategy_v9_pair_to_bot_ds),
        ("v9.1 (tight: pair 2-5,T-Q + Ace + DS sym)", strategy_v9_1_pair_to_bot_ds),
    ]

    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...")
        res = grade_strategy(
            fn, grid, ch, label=label,
            max_hands=args.max_hands, progress_every=500_000, keep_per_hand=False,
        )
        print(res.summary())
        results.append(res)

    print("\n\n" + "=" * 70)
    print("STRATEGY GRADING SUMMARY")
    print("=" * 70)
    print(compare_grades(*results))

    if len(results) >= 4:
        v8 = results[1]
        v9 = results[2]
        v91 = results[3]
        for label, cand in [("v9 (loose)", v9), ("v9.1 (tight)", v91)]:
            delta = v8.mean_regret - cand.mean_regret  # positive = candidate better
            print(
                f"\n{label} vs v8_hybrid:"
                f"  mean regret reduction = {delta:+.4f}"
                f"  ≈ ${delta * 10 * 1000:+,.0f}/1000h"
                f"  pct_optimal change = {cand.pct_optimal - v8.pct_optimal:+.2f} pp"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
