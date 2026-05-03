#!/usr/bin/env python3
"""For every canonical hand of a given hand category, compute v8_hybrid's
(or any other strategy's) regret vs the oracle argmax. Print the top-N
hands with the biggest regret — these are the archetypes the next rule
should target.

Same first-step methodology as Session 25's q4_inspect_top10.py, but
generalized via --category and --strategy flags.

Usage:
    python3 -u analysis/scripts/find_worst_v8_two_pair.py --category high_only
    python3 -u analysis/scripts/find_worst_v8_two_pair.py --category trips --strategy v10
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))
sys.path.insert(0, str(REPO / "trainer" / "src"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import categorize_hands, CATEGORY_NAMES
from tw_analysis.oracle_grid import read_oracle_grid
from tw_analysis.query import setting_features_from_bytes, SUIT_PROFILE_LABELS
from tw_analysis.settings import Card, decode_setting

GRID_PATH = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"

DEFAULT_CATEGORY = "two_pair"
DEFAULT_STRATEGY = "v8"
TOP_N = 15


def _resolve_strategy(name: str):
    if name == "v8":
        from strategy_v8_hybrid import strategy_v8_hybrid as fn
        return ("v8_hybrid", fn)
    if name == "v9.1":
        from strategy_v9_1_pair_to_bot_ds import strategy_v9_1_pair_to_bot_ds as fn
        return ("v9.1", fn)
    if name == "v10":
        from strategy_v10_two_pair_no_split import strategy_v10_two_pair_no_split as fn
        return ("v10", fn)
    raise ValueError(f"unknown strategy: {name}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default=DEFAULT_CATEGORY,
                        choices=CATEGORY_NAMES)
    parser.add_argument("--strategy", default=DEFAULT_STRATEGY)
    parser.add_argument("--top-n", type=int, default=TOP_N)
    args = parser.parse_args()

    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    n = len(grid)

    print(f"Categorizing all {n:,} canonical hands ...")
    cats = categorize_hands(np.asarray(ch.hands, dtype=np.uint8))
    target_code = CATEGORY_NAMES.index(args.category)
    target_mask = cats == target_code
    print(f"  {args.category}: {int(target_mask.sum()):,} hands")

    strat_label, strat_fn = _resolve_strategy(args.strategy)
    target_indices = np.flatnonzero(target_mask)
    print(f"\nGrading {strat_label} on {len(target_indices):,} {args.category} hands ...")

    regrets = np.empty(len(target_indices), dtype=np.float32)
    v8_picks = np.empty(len(target_indices), dtype=np.int16)
    oracle_picks = np.empty(len(target_indices), dtype=np.int16)
    t0 = time.time()
    for k, i in enumerate(target_indices):
        hb = np.asarray(ch.hands[int(i)], dtype=np.uint8)
        ev_row = grid.evs[int(i)]
        v8_idx = int(strat_fn(hb))
        oracle_idx = int(ev_row.argmax())
        v8_picks[k] = v8_idx
        oracle_picks[k] = oracle_idx
        regrets[k] = float(ev_row[oracle_idx]) - float(ev_row[v8_idx])
        if (k + 1) % 200_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            print(f"  {k+1:>8,}/{len(target_indices):,}  rate={rate:>5.0f}/s")

    # Top-N by regret
    order = np.argsort(-regrets)
    print(f"\nTop-{args.top_n} {args.category} hands where {strat_label} bleeds the most:\n")
    for rank, k in enumerate(order[:args.top_n], start=1):
        i = int(target_indices[k])
        hb = np.asarray(ch.hands[i], dtype=np.uint8)
        hand = [Card(int(b)) for b in hb]
        v8_idx = int(v8_picks[k])
        oracle_idx = int(oracle_picks[k])
        v8_setting = decode_setting(hand, v8_idx)
        oracle_setting = decode_setting(hand, oracle_idx)
        feats = setting_features_from_bytes(hb)

        # Hand-level features
        rank_counts: dict[int, int] = {}
        for c in hand:
            rank_counts[c.rank] = rank_counts.get(c.rank, 0) + 1
        pairs = sorted([(r, n) for r, n in rank_counts.items() if n >= 2], reverse=True)
        suit_counts = [0, 0, 0, 0]
        for c in hand:
            suit_counts[c.suit] += 1

        print(f"#{rank}  canonical_id {i}  regret = {float(regrets[k]):+.3f}  ≈ ${float(regrets[k])*10*1000:+,.0f}/1000h")
        print(f"   hand: {' '.join(str(c) for c in hand)}")
        print(f"   pairs: {pairs}   suits (♣♦♥♠): {tuple(suit_counts)}")
        print(f"   {strat_label}: setting {v8_idx}  EV={float(grid.evs[i][v8_idx]):+.3f}")
        print(f"     {v8_setting}")
        sprof = int(feats.bot_suit_profile[v8_idx])
        smp = bool(feats.mid_is_pair[v8_idx])
        print(f"     bot suit: {SUIT_PROFILE_LABELS.get(sprof, '?')}, mid_is_pair={smp}, top_rank={int(feats.top_rank[v8_idx])}")
        print(f"   ORACLE:    setting {oracle_idx}  EV={float(grid.evs[i][oracle_idx]):+.3f}")
        print(f"     {oracle_setting}")
        oracle_profile = int(feats.bot_suit_profile[oracle_idx])
        oracle_mid_pair = bool(feats.mid_is_pair[oracle_idx])
        print(f"     bot suit: {SUIT_PROFILE_LABELS.get(oracle_profile, '?')}, mid_is_pair={oracle_mid_pair}, top_rank={int(feats.top_rank[oracle_idx])}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
