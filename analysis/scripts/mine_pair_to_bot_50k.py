"""
Mine the pair-to-bot routing pattern across the 50K oracle grid.

For each hand with exactly one pair:
  - Determine if the oracle's pick (argmax_mean over 105 settings) routes
    the pair to BOT (i.e., neither pair card is in the mid_pos).
  - Tabulate by pair_high_rank: how often does pair-to-bot win?
  - Compute v3's loss vs oracle on these hands.

Also: for each pair_high_rank, find the FEATURES that best discriminate
between "oracle routes pair to mid" vs "oracle routes pair to bot."
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import Counter

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v5_dt import compute_feature_vector  # noqa: E402
from strategy_v7_regression import load_model  # noqa: E402
from encode_rules import decode_tier_positions, hand_decompose  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"


def main() -> int:
    arr = np.load(GRID_PATH, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]
    ev_grid = arr["ev_grid"]
    n = hands_bytes.shape[0]
    n_profiles = ev_grid.shape[1]

    # Compute per-hand: category, pair rank, oracle choice, v3 choice, v7 choice
    # and "is oracle pair-to-bot"
    print(f"Analyzing {n:,} hands ...")
    pair_hands = []  # list of dicts
    for i in range(n):
        h = hands_bytes[i]
        d = hand_decompose(h)
        if len(d["pairs"]) != 1 or d["trips"] or d["quads"]:
            continue
        pair_rank = d["pairs"][0][0]
        pair_pos = tuple(d["pairs"][0][1])
        # Compute mean-EV per setting
        mean_ev = ev_grid[i].mean(axis=0)
        oracle_idx = int(mean_ev.argmax())
        # Decode oracle's mid positions
        _top, oracle_mid, oracle_bot = decode_tier_positions(oracle_idx)
        # Pair-to-bot iff neither pair position is in oracle_mid
        is_pair_to_bot = (pair_pos[0] not in oracle_mid) and (pair_pos[1] not in oracle_mid)

        pair_hands.append({
            "pair_rank": pair_rank,
            "is_pair_to_bot": is_pair_to_bot,
            "oracle_ev": float(mean_ev[oracle_idx]),
        })
    print(f"  one-pair hands: {len(pair_hands):,}")

    # Per pair_rank: how often does oracle route pair-to-bot?
    print(f"\n{'pair_rank':<12}{'n':>8}{'pair→bot':>14}{'pair→mid':>14}{'%pair→bot':>14}{'mean_oracle_ev':>18}")
    print("-" * 80)
    by_rank: dict[int, list] = {}
    for r in pair_hands:
        by_rank.setdefault(r["pair_rank"], []).append(r)
    for rank in sorted(by_rank.keys()):
        rows = by_rank[rank]
        cnt = len(rows)
        pb = sum(1 for r in rows if r["is_pair_to_bot"])
        pm = cnt - pb
        pct = 100 * pb / cnt
        avg_ev = sum(r["oracle_ev"] for r in rows) / cnt
        print(f"{rank:<12}{cnt:>8}{pb:>14}{pm:>14}{pct:>13.1f}%{avg_ev:>+18.4f}")

    # Aggregate counts
    print(f"\nTotal pair→bot: {sum(1 for r in pair_hands if r['is_pair_to_bot']):,} "
          f"({100*sum(1 for r in pair_hands if r['is_pair_to_bot'])/len(pair_hands):.1f}% of pair hands)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
