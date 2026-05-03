#!/usr/bin/env python3
"""Classify high_only hands by what archetype the oracle's argmax setting
falls into, then look at features that predict the archetype.

Archetypes:
    A. obvious_play: top = highest card, no special routing
    B. sacrifice_top: top is NOT in the top-3 ranks of the hand (low top)
    C. mid_broadway: mid uses both broadway cards (T+) when available
    D. ds_bot: bot is double-suited

These are not mutually exclusive — a hand's oracle pick might match multiple.
For each hand we compute v8's regret vs oracle and which archetype-flags
the oracle pick has, then look at how regret distributes across archetype
combinations.

Sample: 200K random high_only hands.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))
sys.path.insert(0, str(REPO / "trainer" / "src"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import categorize_hands, CATEGORY_NAMES
from tw_analysis.oracle_grid import read_oracle_grid
from tw_analysis.query import (
    SUIT_PROFILE_DS,
    SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_SS,
    SUIT_PROFILE_THREE_ONE,
    SUIT_PROFILE_FOUR_FLUSH,
    setting_features_from_bytes,
)


GRID_PATH = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = REPO / "data" / "canonical_hands.bin"
SAMPLE_SIZE = 200_000


def main() -> int:
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")

    print("Categorizing all hands...")
    cats = categorize_hands(np.asarray(ch.hands, dtype=np.uint8))
    high_only_mask = cats == CATEGORY_NAMES.index("high_only")
    high_only_indices = np.flatnonzero(high_only_mask)
    print(f"  {len(high_only_indices):,} high_only hands")

    rng = np.random.default_rng(42)
    sample = rng.choice(len(high_only_indices), size=min(SAMPLE_SIZE, len(high_only_indices)), replace=False)
    sample_idx = np.sort(high_only_indices[sample])
    print(f"  sampling {len(sample_idx):,} for discriminator")

    from strategy_v8_hybrid import strategy_v8_hybrid

    # Per-hand records
    records = []  # list of dicts
    print("Computing per-hand archetype classifications...")
    for i in sample_idx:
        i = int(i)
        hb = np.asarray(ch.hands[i], dtype=np.uint8)
        ranks_arr = (hb // 4) + 2
        suits_arr = hb & 0b11

        ev_row = grid.evs[i]
        v8_idx = int(strategy_v8_hybrid(hb))
        oracle_idx = int(ev_row.argmax())
        regret = float(ev_row[oracle_idx]) - float(ev_row[v8_idx])

        feats = setting_features_from_bytes(hb)
        # Oracle's pick features
        oracle_top_rank = int(feats.top_rank[oracle_idx])
        oracle_bot_profile = int(feats.bot_suit_profile[oracle_idx])
        oracle_bot_run = int(feats.bot_longest_run[oracle_idx])

        # Hand-level features
        sorted_ranks = sorted([int(r) for r in ranks_arr], reverse=True)
        max_rank = sorted_ranks[0]
        broadway_count = sum(1 for r in ranks_arr if r >= 10)
        has_ace = 14 in ranks_arr
        has_king = 13 in ranks_arr
        # Suit distribution
        suit_count = np.bincount(suits_arr, minlength=4)
        suit_dist_sorted = tuple(sorted(suit_count.tolist(), reverse=True))
        # Longest run on full hand
        distinct_ranks = sorted(set(int(r) for r in ranks_arr))
        max_run = 1
        cur = 1
        for k in range(1, len(distinct_ranks)):
            if distinct_ranks[k] == distinct_ranks[k - 1] + 1:
                cur += 1
                max_run = max(max_run, cur)
            else:
                cur = 1

        # Archetype flags on oracle pick
        sacrifice_top = oracle_top_rank < sorted_ranks[2]  # top is not in top-3 ranks
        ds_bot = oracle_bot_profile == SUIT_PROFILE_DS
        connected_bot = oracle_bot_run >= 3

        records.append({
            "id": i,
            "regret": regret,
            "max_rank": max_rank,
            "broadway_count": broadway_count,
            "has_ace": has_ace,
            "has_king": has_king,
            "suit_dist": suit_dist_sorted,
            "hand_max_run": max_run,
            "sacrifice_top": sacrifice_top,
            "ds_bot": ds_bot,
            "connected_bot": connected_bot,
            "oracle_top_rank": oracle_top_rank,
        })

    # Aggregate
    n = len(records)
    print(f"\n--- Across {n:,} sampled high_only hands ---")
    mean_regret = float(np.mean([r["regret"] for r in records]))
    print(f"  mean v8 regret: {mean_regret:+.4f}  ≈ ${mean_regret * 10 * 1000:+,.0f}/1000h")
    print(f"  oracle 'sacrifice top' (top NOT in top-3 ranks): {100 * sum(r['sacrifice_top'] for r in records) / n:.1f}%")
    print(f"  oracle 'DS bot':         {100 * sum(r['ds_bot'] for r in records) / n:.1f}%")
    print(f"  oracle 'connected bot' (run >= 3): {100 * sum(r['connected_bot'] for r in records) / n:.1f}%")

    # By feature: regret of v8 + oracle archetype rates
    print("\n--- Mean v8 regret by feature ---")

    print("\nBy broadway_count:")
    for bc in range(8):
        subset = [r for r in records if r["broadway_count"] == bc]
        if len(subset) < 100:
            continue
        sr = float(np.mean([r["regret"] for r in subset]))
        st_pct = 100 * sum(r["sacrifice_top"] for r in subset) / len(subset)
        ds_pct = 100 * sum(r["ds_bot"] for r in subset) / len(subset)
        print(f"  bc={bc}  n={len(subset):>6}  mean_regret={sr:+.3f}  sacrifice_top={st_pct:>4.1f}%  ds_bot={ds_pct:>4.1f}%")

    print("\nBy hand suit distribution:")
    suit_dist_counts: dict = {}
    for r in records:
        suit_dist_counts.setdefault(r["suit_dist"], []).append(r)
    for sd, subset in sorted(suit_dist_counts.items(), key=lambda x: -len(x[1])):
        if len(subset) < 1000:
            continue
        sr = float(np.mean([r["regret"] for r in subset]))
        st_pct = 100 * sum(r["sacrifice_top"] for r in subset) / len(subset)
        ds_pct = 100 * sum(r["ds_bot"] for r in subset) / len(subset)
        print(f"  suit_dist={sd}  n={len(subset):>6}  mean_regret={sr:+.3f}  sacrifice_top={st_pct:>4.1f}%  ds_bot={ds_pct:>4.1f}%")

    print("\nBy hand_max_run (full-hand longest connected sequence):")
    for mr in range(1, 8):
        subset = [r for r in records if r["hand_max_run"] == mr]
        if len(subset) < 200:
            continue
        sr = float(np.mean([r["regret"] for r in subset]))
        st_pct = 100 * sum(r["sacrifice_top"] for r in subset) / len(subset)
        ds_pct = 100 * sum(r["ds_bot"] for r in subset) / len(subset)
        print(f"  max_run={mr}  n={len(subset):>6}  mean_regret={sr:+.3f}  sacrifice_top={st_pct:>4.1f}%  ds_bot={ds_pct:>4.1f}%")

    # Cross: by (suit_dist, hand_max_run)
    print("\nCross-tab: highest-regret (suit_dist, hand_max_run >= 4) sub-classes:")
    cells: dict = {}
    for r in records:
        key = (r["suit_dist"], r["hand_max_run"])
        cells.setdefault(key, []).append(r)
    cell_stats = []
    for key, subset in cells.items():
        if len(subset) < 200:
            continue
        sr = float(np.mean([r["regret"] for r in subset]))
        cell_stats.append((key, len(subset), sr))
    cell_stats.sort(key=lambda x: -x[2])
    for (sd, mr), n_, sr in cell_stats[:15]:
        print(f"  suit_dist={sd}  max_run={mr}  n={n_:>5}  mean_regret={sr:+.3f}  ≈ ${sr * 10 * 1000:+,.0f}/1000h")

    return 0


if __name__ == "__main__":
    sys.exit(main())
