#!/usr/bin/env python3
"""Validate the 100K-hand N=200 pilot oracle grid + run the user's first
compare query as an end-to-end smoke test of the harness.

Usage:
    python3 analysis/scripts/oracle_grid_pilot_validate.py

Reads:
    data/pilot/oracle_grid_pilot_n200_100k.bin  (just produced by Session 24)
    data/canonical_hands.bin
"""
from __future__ import annotations

import sys
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
)
from tw_analysis.settings import Card, decode_setting

GRID_PATH = REPO / "data" / "pilot" / "oracle_grid_pilot_n200_100k.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"


def main() -> int:
    print(f"Loading oracle grid from {GRID_PATH} ...")
    grid = read_oracle_grid(GRID_PATH, mode="load")
    print(
        f"  header: samples={grid.header.samples} "
        f"opp={grid.header.opp_label} "
        f"base_seed={grid.header.base_seed:#x} "
        f"canonical_total={grid.header.canonical_total}"
    )
    print(f"  records: {len(grid)} (complete={grid.is_complete})")

    print("\nValidating grid integrity...")
    issues = validate_oracle_grid(grid)
    if issues:
        print("  ISSUES:")
        for s in issues:
            print(f"    {s}")
        return 1
    print("  OK — all integrity checks passed.")

    # Spot-check: print 5 records.
    print(f"\nLoading canonical hands from {CANON_PATH} ...")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    print(f"  {len(ch)} canonical hands.")

    print("\nSpot-check: 5 sample records (canonical_id=0, 1, 50000, 99999):")
    for cid in [0, 1, 100, 50000, 99999]:
        if cid >= len(grid):
            continue
        hand = [Card(int(b)) for b in ch.hand_bytes(cid)]
        evs = grid.evs[cid]
        argmax = int(evs.argmax())
        best = decode_setting(hand, argmax)
        print(
            f"  id={cid:>6}  hand=[{' '.join(str(c) for c in hand)}]  "
            f"argmax_setting_idx={argmax}  best_ev={float(evs[argmax]):+.3f}"
        )
        print(f"          best setting: {best}")

    # EV summary
    best_evs = grid.best_ev()
    print(f"\nBest-EV distribution across {len(grid)} hands:")
    print(f"  min={best_evs.min():+.3f}  mean={best_evs.mean():+.3f}  max={best_evs.max():+.3f}")
    print(f"  std={best_evs.std():.3f}  p10={np.percentile(best_evs, 10):+.3f}  p90={np.percentile(best_evs, 90):+.3f}")

    # ----- User Q1: DS-unconnected vs rainbow-connected bot -----
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
        progress_every=20_000,
    )
    print(res1.summary())

    # ----- User Q2: DS-unconnected vs single-suited connected bot -----
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
        progress_every=20_000,
    )
    print(res2.summary())

    # ----- User Q3: DS bot (any connectivity) vs rainbow bot (any connectivity) -----
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
        progress_every=20_000,
    )
    print(res3.summary())

    return 0


if __name__ == "__main__":
    sys.exit(main())
