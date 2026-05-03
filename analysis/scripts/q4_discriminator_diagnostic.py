#!/usr/bin/env python3
"""Within the v9 hypothesis class (single pair rank 2-12 + Ace singleton +
DS-bot feasibility), identify what features discriminate B-wins from
A-wins.

The Q4 characterization showed 75% of these hands are A-wins (pair-in-mid
beats pair-to-bot-DS) — so my v9, which fires on ALL hypothesis hands,
over-fires. Find a tighter gate.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.oracle_grid import read_oracle_grid
from tw_analysis.query import (
    SUIT_PROFILE_DS,
    setting_features_from_bytes,
)


GRID_PATH = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    n = len(grid)
    evs_arr = grid.evs
    hands_arr = ch.hands

    # Hypothesis-hand features per row, plus delta_ab.
    # We collect: pair_rank, max_kicker_rank, has_broadway_kicker, suit_alignment.
    keep_pair_rank = []
    keep_max_kicker = []
    keep_min_kicker = []
    keep_has_broadway_kicker = []
    keep_kicker_count_pair_suit_a = []
    keep_kicker_count_pair_suit_b = []
    keep_n_distinct_suits = []
    keep_delta_ab = []
    keep_canonical_id = []

    t0 = time.time()
    for i in range(n):
        hand_bytes = np.asarray(hands_arr[i], dtype=np.uint8)
        ranks = (hand_bytes // 4) + 2
        suits = hand_bytes & 0b11
        rank_counts = np.bincount(ranks, minlength=15)

        # v9 strict gate
        total_multis = int(sum(rank_counts[r] >= 2 for r in range(2, 15)))
        if total_multis != 1:
            continue
        pair_rank = next(r for r in range(2, 15) if rank_counts[r] >= 2)
        if pair_rank > 12 or rank_counts[pair_rank] != 2:
            continue
        if rank_counts[14] != 1:  # exactly one ace
            continue

        # Pair must have two distinct suits
        pair_idx = [j for j in range(7) if ranks[j] == pair_rank]
        suit_a = int(suits[pair_idx[0]])
        suit_b = int(suits[pair_idx[1]])
        if suit_a == suit_b:
            continue

        # 4 non-pair, non-ace cards: at least one each of suit_a and suit_b
        ace_idx = next(j for j in range(7) if ranks[j] == 14)
        other = [j for j in range(7) if j not in (ace_idx, pair_idx[0], pair_idx[1])]
        kickers_suits = [int(suits[j]) for j in other]
        n_a = sum(1 for s in kickers_suits if s == suit_a)
        n_b = sum(1 for s in kickers_suits if s == suit_b)
        if n_a == 0 or n_b == 0:
            continue

        # OK, hand is in hypothesis class. Compute delta_ab.
        feats = setting_features_from_bytes(hand_bytes)
        mask_a = feats.mid_is_pair & (feats.bot_suit_profile != SUIT_PROFILE_DS)
        mask_b = (~feats.mid_is_pair) & (feats.bot_suit_profile == SUIT_PROFILE_DS)
        if not (mask_a.any() and mask_b.any()):
            continue
        ev_row = evs_arr[i]
        ev_a = float(np.where(mask_a, ev_row, -np.inf).max())
        ev_b = float(np.where(mask_b, ev_row, -np.inf).max())
        delta = ev_a - ev_b

        # Hand-level features
        kicker_ranks = [int(ranks[j]) for j in other]
        max_kicker = max(kicker_ranks)
        min_kicker = min(kicker_ranks)
        has_broadway = any(r >= 10 for r in kicker_ranks)
        n_distinct_suits = int(len(set(int(s) for s in suits)))

        keep_pair_rank.append(pair_rank)
        keep_max_kicker.append(max_kicker)
        keep_min_kicker.append(min_kicker)
        keep_has_broadway_kicker.append(has_broadway)
        keep_kicker_count_pair_suit_a.append(n_a)
        keep_kicker_count_pair_suit_b.append(n_b)
        keep_n_distinct_suits.append(n_distinct_suits)
        keep_delta_ab.append(delta)
        keep_canonical_id.append(i)

        if (i + 1) % 1_000_000 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            print(f"  {i+1:>10}/{n:,}  hyp_count={len(keep_pair_rank):>10}  rate={rate:>5.0f}")

    pair_rank_arr = np.array(keep_pair_rank, dtype=np.int8)
    max_kicker_arr = np.array(keep_max_kicker, dtype=np.int8)
    min_kicker_arr = np.array(keep_min_kicker, dtype=np.int8)
    has_broadway_arr = np.array(keep_has_broadway_kicker, dtype=bool)
    n_a_arr = np.array(keep_kicker_count_pair_suit_a, dtype=np.int8)
    n_b_arr = np.array(keep_kicker_count_pair_suit_b, dtype=np.int8)
    n_suits_arr = np.array(keep_n_distinct_suits, dtype=np.int8)
    delta_arr = np.array(keep_delta_ab, dtype=np.float32)
    cid_arr = np.array(keep_canonical_id, dtype=np.uint32)

    n_h = len(delta_arr)
    print(f"\nHypothesis hands: {n_h:,}  ({100.0 * n_h / n:.2f}% of all canonical hands)")
    print(f"Mean Δ (A − B):  {float(delta_arr.mean()):+.4f}")
    print(f"Median Δ:        {float(np.median(delta_arr)):+.4f}")
    n_b_wins = int((delta_arr < 0).sum())
    n_a_wins = int((delta_arr > 0).sum())
    print(f"B wins: {n_b_wins:,} ({100.0 * n_b_wins / n_h:.2f}%)")
    print(f"A wins: {n_a_wins:,} ({100.0 * n_a_wins / n_h:.2f}%)")

    # Cross-tab by pair_rank
    print(f"\n--- Δ by pair_rank ---")
    print(f"{'pair_rank':>10}{'count':>10}{'mean Δ':>10}{'A-win%':>10}{'B-win%':>10}{'$/1000h pair-bot':>20}")
    for r in range(2, 13):
        m = pair_rank_arr == r
        if not m.any():
            continue
        d = delta_arr[m]
        b_pct = 100.0 * (d < 0).sum() / len(d)
        a_pct = 100.0 * (d > 0).sum() / len(d)
        # Mean EV gain from forcing pair-to-bot (relative to pair-mid)
        mean_pair_bot_delta = -float(d.mean())  # negative of (A − B) = (B − A) gain
        label = "Q" if r == 12 else "J" if r == 11 else "T" if r == 10 else str(r)
        print(
            f"{label:>10}{len(d):>10,}{float(d.mean()):>+10.3f}{a_pct:>9.1f}%{b_pct:>9.1f}%"
            f"{mean_pair_bot_delta * 10 * 1000:>+19,.0f}"
        )

    # Cross-tab by has_broadway_kicker (T/J/Q in mid alternative)
    print(f"\n--- Δ by has_broadway_kicker ---")
    for hb in [True, False]:
        m = has_broadway_arr == hb
        d = delta_arr[m]
        if len(d) == 0:
            continue
        b_pct = 100.0 * (d < 0).sum() / len(d)
        a_pct = 100.0 * (d > 0).sum() / len(d)
        mean_pair_bot_delta = -float(d.mean())
        print(
            f"  has_broadway_kicker={hb}  count={len(d):>10,}  mean Δ={float(d.mean()):>+8.3f}  "
            f"A-win%={a_pct:>5.1f}  B-win%={b_pct:>5.1f}  "
            f"pair-bot $/1000h={mean_pair_bot_delta * 10 * 1000:>+8,.0f}"
        )

    # Combined: pair_rank × has_broadway_kicker
    print(f"\n--- Δ by (pair_rank, has_broadway_kicker) ---")
    print(f"{'pair_rank':>10}{'has_BW':>8}{'count':>10}{'mean Δ':>10}{'$/1000h pair-bot':>20}")
    for r in range(2, 13):
        for hb in [True, False]:
            m = (pair_rank_arr == r) & (has_broadway_arr == hb)
            d = delta_arr[m]
            if len(d) < 1000:
                continue
            mean_pair_bot_delta = -float(d.mean())
            label = "Q" if r == 12 else "J" if r == 11 else "T" if r == 10 else str(r)
            print(
                f"{label:>10}{str(hb):>8}{len(d):>10,}{float(d.mean()):>+10.3f}"
                f"{mean_pair_bot_delta * 10 * 1000:>+19,.0f}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
