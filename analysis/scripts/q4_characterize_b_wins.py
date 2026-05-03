#!/usr/bin/env python3
"""Characterize the full Q4 B-wins cluster (~906K hands where breaking a
pair to keep a DS bot beats keeping the pair in mid).

Hypothesis (from top-10 inspection):
    B-wins hands all share:
      1. A non-premium pair (rank ≤ Q)
      2. An Ace singleton
      3. The pair + 2 kickers can form a DS bot (pair contributes both
         suits to the DS structure)

This script tests that hypothesis at the population level by computing
per-hand features for every B-wins hand and aggregating.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import categorize_hands, CATEGORY_NAMES
from tw_analysis.oracle_grid import read_oracle_grid
from tw_analysis.query import (
    SUIT_PROFILE_DS,
    SUIT_PROFILE_LABELS,
    setting_features_from_bytes,
)

GRID_PATH = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    print(f"Loading grid (memmap) ...")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    print(f"Loading canonical hands (memmap) ...")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")

    print(f"Categorizing all {len(ch):,} canonical hands ...")
    cats = categorize_hands(np.asarray(ch.hands, dtype=np.uint8))

    n = len(grid)
    evs_arr = grid.evs
    hands_arr = ch.hands

    # B-wins detection: scan all hands, identify those where the EV-best
    # setting in B's class > EV-best setting in A's class. While doing
    # this, accumulate hand features.

    # Hand-level features
    pair_rank_max = np.zeros(n, dtype=np.int8)        # highest pair rank (0 if no pair)
    has_ace_singleton = np.zeros(n, dtype=bool)       # ace appears exactly once
    has_ace_at_all = np.zeros(n, dtype=bool)
    bot_ds_with_pair_feasible = np.zeros(n, dtype=bool)  # DS-with-pair candidate exists

    # Per-hand B-wins identification (revisit Q4 logic but record per-hand)
    is_b_win = np.zeros(n, dtype=bool)
    is_a_win = np.zeros(n, dtype=bool)
    delta_ab = np.full(n, np.nan, dtype=np.float32)
    only_a_avail = np.zeros(n, dtype=bool)
    only_b_avail = np.zeros(n, dtype=bool)

    t0 = time.time()
    for i in range(n):
        hand_bytes = np.asarray(hands_arr[i], dtype=np.uint8)
        ranks = (hand_bytes // 4 + 2)
        suits = (hand_bytes & 0b11)

        # Hand-level features
        bincount = np.bincount(ranks, minlength=15)
        pairs = [r for r in range(2, 15) if bincount[r] >= 2]
        if pairs:
            pair_rank_max[i] = max(pairs)
        has_ace_at_all[i] = bincount[14] >= 1
        has_ace_singleton[i] = bincount[14] == 1

        # DS-with-pair feasibility: is there a 4-card subset {pair_member1,
        # pair_member2, kicker1, kicker2} where {pair_member1, kicker_X}
        # share suit_a and {pair_member2, kicker_Y} share suit_b? In other
        # words: do at least 2 distinct suits each have >= 2 occurrences
        # AND the pair has both suits represented?
        # Simpler proxy: at least 2 distinct suits with count >= 2 in the
        # full hand. (If true, a 4-card DS bot is generally achievable.)
        suit_count = np.bincount(suits, minlength=4)
        ds_feasible_proxy = (suit_count >= 2).sum() >= 2
        bot_ds_with_pair_feasible[i] = ds_feasible_proxy

        # Q4 B-wins (re-derive)
        feats = setting_features_from_bytes(hand_bytes)
        mask_a = feats.mid_is_pair & (feats.bot_suit_profile != SUIT_PROFILE_DS)
        mask_b = (~feats.mid_is_pair) & (feats.bot_suit_profile == SUIT_PROFILE_DS)
        ev_row = evs_arr[i]
        a_avail = mask_a.any()
        b_avail = mask_b.any()
        if a_avail and b_avail:
            ev_a = float(np.where(mask_a, ev_row, -np.inf).max())
            ev_b = float(np.where(mask_b, ev_row, -np.inf).max())
            d = ev_a - ev_b
            delta_ab[i] = d
            if d < 0:
                is_b_win[i] = True
            elif d > 0:
                is_a_win[i] = True
        elif a_avail:
            only_a_avail[i] = True
        elif b_avail:
            only_b_avail[i] = True

        if (i + 1) % 1_000_000 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (n - i - 1) / rate
            print(f"  {i+1:>10,}/{n:,}  rate={rate:>5.0f} hands/s  ETA={eta:>5.0f}s")

    # Now characterize the B-wins set.
    print(f"\nTotal B-wins: {int(is_b_win.sum()):,}")
    print(f"Total A-wins: {int(is_a_win.sum()):,}")
    print(f"Only A available: {int(only_a_avail.sum()):,}")
    print(f"Only B available: {int(only_b_avail.sum()):,}")

    bw = is_b_win
    print(f"\n--- Hand-level features within B-wins (N={int(bw.sum()):,}) ---")

    # Hypothesis check 1: pair rank distribution
    pair_dist = np.bincount(pair_rank_max[bw], minlength=15)
    print("\nPair rank distribution (max pair in hand):")
    for r in range(2, 15):
        if pair_dist[r] > 0:
            pct = 100.0 * pair_dist[r] / int(bw.sum())
            label = "A" if r == 14 else "K" if r == 13 else "Q" if r == 12 else str(r)
            print(f"  pair_rank={label:>2}  count={pair_dist[r]:>10,}  {pct:>5.2f}%")
    print(f"  no pair    count={pair_dist[0]:>10,}  {100.0 * pair_dist[0] / int(bw.sum()):>5.2f}%")

    # Hypothesis check 2: ace singleton
    ace_singleton_pct = 100.0 * has_ace_singleton[bw].sum() / bw.sum()
    ace_at_all_pct = 100.0 * has_ace_at_all[bw].sum() / bw.sum()
    print(f"\nAce-singleton in B-wins: {ace_singleton_pct:.2f}%")
    print(f"Ace anywhere   in B-wins: {ace_at_all_pct:.2f}%")

    # Hypothesis check 3: DS-feasibility proxy
    ds_feas_pct = 100.0 * bot_ds_with_pair_feasible[bw].sum() / bw.sum()
    print(f"DS-bot feasibility (≥2 suits with ≥2 cards): {ds_feas_pct:.2f}%")

    # Combined: pair (rank ≤ Q) + ace singleton + DS-feasible
    hypothesis_mask = (
        (pair_rank_max <= 12) & (pair_rank_max >= 2)  # has a pair, rank ≤ Q
        & has_ace_singleton
        & bot_ds_with_pair_feasible
    )
    in_b_win_and_hypothesis = (bw & hypothesis_mask).sum()
    in_b_win_not_hypothesis = (bw & ~hypothesis_mask).sum()
    print(f"\n--- Combined hypothesis: pair (rank 2-12) + Ace singleton + DS-feasible ---")
    print(f"  B-wins matching hypothesis:        {int(in_b_win_and_hypothesis):>10,}  "
          f"({100.0 * in_b_win_and_hypothesis / bw.sum():.2f}% of B-wins)")
    print(f"  B-wins NOT matching hypothesis:    {int(in_b_win_not_hypothesis):>10,}")

    in_hyp_total = int(hypothesis_mask.sum())
    in_hyp_b_win_pct = 100.0 * in_b_win_and_hypothesis / in_hyp_total if in_hyp_total else 0.0
    print(f"  Hypothesis hands total:            {in_hyp_total:>10,}")
    print(f"  Of hypothesis hands, B-wins rate:  {in_hyp_b_win_pct:.2f}%")
    in_hyp_a_win_pct = 100.0 * (is_a_win & hypothesis_mask).sum() / in_hyp_total if in_hyp_total else 0.0
    print(f"  Of hypothesis hands, A-wins rate:  {in_hyp_a_win_pct:.2f}%")

    # Mean delta on hypothesis hands (where both A and B available).
    both_avail_hyp = hypothesis_mask & ~np.isnan(delta_ab)
    if both_avail_hyp.any():
        mean_delta_hyp = float(delta_ab[both_avail_hyp].mean())
        print(f"  Mean Δ (A − B) on hypothesis hands: {mean_delta_hyp:+.4f}  "
              f"≈ ${mean_delta_hyp * 10 * 1000:+,.0f}/1000h")

    # Hand category breakdown of B-wins
    print(f"\n--- Hand category breakdown of B-wins ---")
    for code, name in enumerate(CATEGORY_NAMES):
        in_cat = (cats == code) & bw
        cat_count = int(in_cat.sum())
        if cat_count == 0:
            continue
        in_cat_total = int((cats == code).sum())
        pct_of_b_wins = 100.0 * cat_count / int(bw.sum())
        cat_b_win_rate = 100.0 * cat_count / in_cat_total if in_cat_total else 0.0
        print(f"  {name:<14}  in_b_wins={cat_count:>10,}  "
              f"share={pct_of_b_wins:>5.2f}%  cat_b_win_rate={cat_b_win_rate:>5.2f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
