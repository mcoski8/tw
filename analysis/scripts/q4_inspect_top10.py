#!/usr/bin/env python3
"""Quick inspection of Q4's top-10 B-wins canonical IDs to understand
the 'pair-to-mid is a blunder' hand archetype.

For each hand:
  - Show the 7 cards
  - Show the EV of A's best (pair-in-mid + non-DS bot) and B's best (no-pair-mid + DS bot)
  - Show what setting each picked
  - Show the absolute argmax setting (oracle's pick)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.oracle_grid import read_oracle_grid
from tw_analysis.query import (
    SUIT_PROFILE_DS,
    SUIT_PROFILE_LABELS,
    setting_features_from_bytes,
)
from tw_analysis.settings import Card, decode_setting

# Top-10 B-wins canonical IDs from Q4 (oracle_grid_full_queries.log).
B_WINS_TOP10 = [425562, 3546583, 3546584, 2965461, 2835853, 419237, 4104257, 1923068, 44858, 264562]


def main() -> int:
    grid = read_oracle_grid(REPO / "data" / "oracle_grid_full_realistic_n200.bin", mode="memmap")
    ch = read_canonical_hands(REPO / "data" / "canonical_hands.bin", mode="memmap")

    for cid in B_WINS_TOP10:
        hand_bytes = np.asarray(ch.hand_bytes(cid), dtype=np.uint8)
        hand = [Card(int(b)) for b in hand_bytes]
        evs = grid.evs[cid]
        feats = setting_features_from_bytes(hand_bytes)

        # Filters from Q4.
        mask_a = feats.mid_is_pair & (feats.bot_suit_profile != SUIT_PROFILE_DS)
        mask_b = (~feats.mid_is_pair) & (feats.bot_suit_profile == SUIT_PROFILE_DS)

        oracle_idx = int(evs.argmax())
        oracle_ev = float(evs.max())

        ev_a_max = float(np.where(mask_a, evs, -np.inf).max()) if mask_a.any() else float("nan")
        a_idx = int(np.where(mask_a, evs, -np.inf).argmax()) if mask_a.any() else -1

        ev_b_max = float(np.where(mask_b, evs, -np.inf).max()) if mask_b.any() else float("nan")
        b_idx = int(np.where(mask_b, evs, -np.inf).argmax()) if mask_b.any() else -1

        print(f"\n=== canonical_id {cid} ===")
        print(f"  hand: {' '.join(str(c) for c in hand)}")
        # Hand features
        rank_counts: dict[int, int] = {}
        for c in hand:
            rank_counts[c.rank] = rank_counts.get(c.rank, 0) + 1
        pairs = sorted([(r, n) for r, n in rank_counts.items() if n >= 2], reverse=True)
        print(f"  rank profile: {sorted(rank_counts.items(), reverse=True)}")
        print(f"  pairs/trips: {pairs if pairs else '(none)'}")

        # Suit distribution
        suit_counts = [0, 0, 0, 0]
        for c in hand:
            suit_counts[c.suit] += 1
        print(f"  suit counts (♣♦♥♠): {tuple(suit_counts)}")

        print(f"  oracle pick: setting {oracle_idx}  EV={oracle_ev:+.3f}")
        print(f"    {decode_setting(hand, oracle_idx)}")
        oracle_profile = int(feats.bot_suit_profile[oracle_idx])
        oracle_mid_pair = bool(feats.mid_is_pair[oracle_idx])
        print(
            f"    oracle's bot suit profile: {SUIT_PROFILE_LABELS.get(oracle_profile, '?')}, "
            f"mid_is_pair={oracle_mid_pair}, top_rank={int(feats.top_rank[oracle_idx])}"
        )

        if a_idx >= 0:
            print(f"  A best (pair-mid + non-DS): setting {a_idx}  EV={ev_a_max:+.3f}")
            print(f"    {decode_setting(hand, a_idx)}")
        if b_idx >= 0:
            print(f"  B best (no-pair-mid + DS):  setting {b_idx}  EV={ev_b_max:+.3f}")
            print(f"    {decode_setting(hand, b_idx)}")
        print(f"  Δ (A − B) = {ev_a_max - ev_b_max:+.3f}  (negative = B wins)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
