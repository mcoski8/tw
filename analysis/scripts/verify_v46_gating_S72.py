#!/usr/bin/env python3
"""Session 72 — surgical-gating sanity for v46_dt vs v44_dt.

For ho_v3/v4 the gating was surgical: v44 was byte-identical to v43 on
the 7 non-high_only categories. ho_v6 inherits the same gating shape
(returns (0,0) on any non-high_only hand). Expectation: v46_dt produces
identical settings to v44_dt on every non-high_only hand.

This script samples N hands per category and checks setting equality.
Cheap (~5 min) and gives an early read on whether the model picks up
splits on the new features outside high_only (which would suggest leaf
restructuring across the whole tree, not just high_only).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v46_dt import strategy_v46_dt  # noqa: E402

GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = REPO / "data" / "canonical_hands.bin"

CAT_NAMES = [
    "high_only", "pair", "two_pair", "three_pair",
    "trips", "trips_pair", "quads",
]


def _categorize(hand: np.ndarray) -> int:
    """0=high_only, 1=pair, 2=two_pair, 3=three_pair, 4=trips,
    5=trips_pair, 6=quads. Mirrors tw_analysis.features.categorize_hands.
    """
    ranks = (np.asarray(hand, dtype=np.uint8) // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    # priority chain matching tw_analysis.features.categorize (lines 439-445)
    cat = 0  # high_only
    if n_pairs == 1:
        cat = 1
    elif n_pairs == 2:
        cat = 2
    elif n_pairs == 3:
        cat = 3
    if n_trips >= 1:
        cat = 4
    if n_trips >= 1 and n_pairs >= 1:
        cat = 5
    if n_quads >= 1:
        cat = 6
    return cat


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cat", type=int, default=2000,
                    help="hands per category to sample (default 2000)")
    args = ap.parse_args()

    rng = np.random.default_rng(42)
    ch = read_canonical_hands(CANON, mode="memmap")
    N = len(ch.hands)
    print(f"Loaded {N:,} canonical hands.", flush=True)

    # Bucket canonical_ids by category (one pass).
    buckets: dict[int, list[int]] = defaultdict(list)
    BATCH = 200_000
    for start in range(0, N, BATCH):
        end = min(start + BATCH, N)
        for i in range(start, end):
            cat = _categorize(ch.hands[i])
            buckets[cat].append(i)
        if (start // BATCH) % 5 == 0:
            print(f"  categorized {end:,}/{N:,}", flush=True)

    print(f"\nCategory counts:")
    for c in range(7):
        print(f"  {c} {CAT_NAMES[c]:<12} {len(buckets[c]):>10,}")

    mismatches = Counter()
    samples_per_cat = {}
    for c in range(7):
        ids = buckets[c]
        if not ids:
            continue
        take = min(args.per_cat, len(ids))
        sel = rng.choice(len(ids), size=take, replace=False)
        samples_per_cat[c] = take
        for j in sel:
            cid = ids[j]
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            s44 = strategy_v44_dt(h)
            s46 = strategy_v46_dt(h)
            if s44 != s46:
                mismatches[c] += 1
        print(f"  cat={c} ({CAT_NAMES[c]:<12}) sampled={take:<6,}  "
              f"mismatches={mismatches[c]:>5}  "
              f"({100*mismatches[c]/max(1,take):.2f}%)", flush=True)

    print("\nSummary:")
    print(f"  high_only mismatches expected to be > 0 (the ship signal).")
    print(f"  Other 6 categories should be ZERO mismatches if gating is surgical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
