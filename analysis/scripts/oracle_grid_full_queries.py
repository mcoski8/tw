#!/usr/bin/env python3
"""Run the user's locked-in initial questions against the FULL Oracle Grid
(6,009,159 canonical hands at N=200 vs realistic 70/25/5 mixture).

Produced by Session 24. The companion pilot script
``oracle_grid_pilot_validate.py`` was used to validate the harness on the
100K-hand pilot; this script is the headline-results run.

Usage:
    python3 analysis/scripts/oracle_grid_full_queries.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.oracle_grid import read_oracle_grid, validate_oracle_grid
from tw_analysis.query import (
    SUIT_PROFILE_DS,
    SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_SS,
    all_of,
    bot_longest_run_at_least,
    bot_longest_run_at_most,
    bot_suit_profile_eq,
    compare_setting_classes,
    mid_is_pair,
    mid_pair_rank_eq,
)
from tw_analysis.settings import Card, decode_setting

GRID_PATH = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    t0 = time.time()
    print(f"Loading oracle grid (memmap) from {GRID_PATH} ...")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    print(
        f"  header: samples={grid.header.samples} "
        f"opp={grid.header.opp_label} "
        f"base_seed={grid.header.base_seed:#x} "
        f"canonical_total={grid.header.canonical_total}"
    )
    print(f"  records: {len(grid)} (complete={grid.is_complete})")
    if not grid.is_complete:
        print("  WARNING: file is incomplete — proceeding anyway")

    print("\nValidating grid integrity (full pass)...")
    issues = validate_oracle_grid(grid)
    if issues:
        print("  ISSUES:")
        for s in issues:
            print(f"    {s}")
        return 1
    print("  OK — all integrity checks passed.")

    print(f"\nLoading canonical hands from {CANON_PATH} ...")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    print(f"  {len(ch)} canonical hands.")

    # ----- EV summary across all hands -----
    print("\nComputing best-EV statistics across all hands...")
    best_evs = grid.best_ev()
    print(f"  N={len(best_evs):,} hands")
    print(f"  min={best_evs.min():+.3f}  mean={best_evs.mean():+.3f}  max={best_evs.max():+.3f}")
    print(
        f"  std={best_evs.std():.3f}  "
        f"p10={np.percentile(best_evs, 10):+.3f}  "
        f"p50={np.percentile(best_evs, 50):+.3f}  "
        f"p90={np.percentile(best_evs, 90):+.3f}"
    )

    # ----- USER Q1: DS-unconnected vs rainbow-connected bot -----
    print("\n" + "=" * 70)
    print("USER Q1: DS-unconnected bot vs rainbow-connected bot")
    print("=" * 70)
    ds_unconnected = all_of(
        bot_suit_profile_eq(SUIT_PROFILE_DS),
        bot_longest_run_at_most(2),
    )
    rainbow_connected = all_of(
        bot_suit_profile_eq(SUIT_PROFILE_RAINBOW),
        bot_longest_run_at_least(3),
    )
    res1 = compare_setting_classes(
        grid,
        ch,
        filter_a=ds_unconnected,
        filter_b=rainbow_connected,
        label_a="DS bot, longest run <= 2 (e.g. 4s8s-Jh-Kh)",
        label_b="rainbow bot, longest run >= 3 (e.g. JT98 rainbow)",
        max_hands=len(grid),
        progress_every=500_000,
    )
    print(res1.summary())

    # ----- USER Q2: DS-unconnected vs single-suited connected -----
    print("\n" + "=" * 70)
    print("USER Q2: DS-unconnected bot vs SS-connected bot")
    print("=" * 70)
    ss_connected = all_of(
        bot_suit_profile_eq(SUIT_PROFILE_SS),
        bot_longest_run_at_least(3),
    )
    res2 = compare_setting_classes(
        grid,
        ch,
        filter_a=ds_unconnected,
        filter_b=ss_connected,
        label_a="DS bot, longest run <= 2",
        label_b="SS bot, longest run >= 3",
        max_hands=len(grid),
        progress_every=500_000,
    )
    print(res2.summary())

    # ----- USER Q3: DS bot (any) vs rainbow bot (any) -----
    print("\n" + "=" * 70)
    print("USER Q3: DS bot (any connectivity) vs rainbow bot (any connectivity)")
    print("=" * 70)
    res3 = compare_setting_classes(
        grid,
        ch,
        filter_a=bot_suit_profile_eq(SUIT_PROFILE_DS),
        filter_b=bot_suit_profile_eq(SUIT_PROFILE_RAINBOW),
        label_a="DS bot (any connectivity)",
        label_b="rainbow bot (any connectivity)",
        max_hands=len(grid),
        progress_every=500_000,
    )
    print(res3.summary())

    # ----- USER Q4: when does pair-to-mid become a blunder for bot DS preservation? -----
    # We answer by comparing two setting families:
    #   A: any setting where mid IS the highest pair in the hand AND bot is rainbow/SS.
    #   B: any setting where mid is NOT a pair but the bot IS DS.
    # If B beats A by a lot on a particular hand category, that's a "pair-to-mid blunder" —
    # the player would have been better off breaking the pair to keep the bot DS.
    print("\n" + "=" * 70)
    print("USER Q4: pair-to-mid vs DS-bot tradeoff")
    print("       A = pair in mid + rainbow/SS bot")
    print("       B = no pair in mid + DS bot")
    print("=" * 70)
    pair_mid_no_ds = all_of(
        mid_is_pair(),
        lambda f: f.bot_suit_profile != SUIT_PROFILE_DS,
    )
    no_pair_mid_ds_bot = all_of(
        lambda f: ~f.mid_is_pair,
        bot_suit_profile_eq(SUIT_PROFILE_DS),
    )
    res4 = compare_setting_classes(
        grid,
        ch,
        filter_a=pair_mid_no_ds,
        filter_b=no_pair_mid_ds_bot,
        label_a="pair in mid, no-DS bot",
        label_b="no pair in mid, DS bot",
        max_hands=len(grid),
        progress_every=500_000,
    )
    print(res4.summary())

    # ----- Bonus Q5: low-pair-to-bot vs mid (Session 22 finding extension) -----
    # On hands with a small pair (rank 2-5), is bot-routing ever the EV-correct play?
    print("\n" + "=" * 70)
    print("BONUS Q5: small-pair-to-mid vs small-pair-to-bot")
    print("       on hands with pair of rank <= 5")
    print("=" * 70)
    def has_small_pair(hand):
        ranks = [c.rank for c in hand]
        from collections import Counter
        c = Counter(ranks)
        return any(2 <= r <= 5 and n >= 2 for r, n in c.items())

    small_pair_in_mid = all_of(
        mid_is_pair(),
        lambda f: f.mid_pair_rank <= 5,
    )
    # Pair in bot = bot has a pair of rank <= 5, AND mid is not a pair (for this hand).
    small_pair_in_bot = all_of(
        lambda f: ~f.mid_is_pair,
        lambda f: (f.bot_pair_rank >= 2) & (f.bot_pair_rank <= 5),
    )
    res5 = compare_setting_classes(
        grid,
        ch,
        filter_a=small_pair_in_mid,
        filter_b=small_pair_in_bot,
        label_a="small pair (2-5) in mid",
        label_b="small pair (2-5) in bot",
        hand_filter=has_small_pair,
        max_hands=len(grid),
        progress_every=500_000,
    )
    print(res5.summary())

    elapsed = time.time() - t0
    print(f"\nTotal wall: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
