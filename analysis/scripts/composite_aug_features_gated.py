"""
Session 31 — composite-gated aug features.

The composite category — quads_pair / quads_trip / two_trips /
trips_two_pair — is rare (~14k of 6M canonical hands, 0.245%) but bleeds
the most per-hand on v20 ($2,100/1000h). The composite_v20_residual
diagnostic showed a clean per-archetype split where v20 most often
splits the dominant trip/quad rather than keeping it together on bot.

The 4 archetypes (n_quads, n_trips, n_pairs):
  trips_two_pair  (0, 1, 2): 6,864 hands
  two_trips       (0, 2, 0): 4,290 hands
  quads_pair      (1, 0, 1): 3,432 hands
  quads_trip      (1, 1, 0):   156 hands

Existing baseline features expose pair_high_rank, pair_low_rank,
trips_rank, quads_rank — but the DT (308K leaves) does not develop
composite-specific subtrees because composite is too small to drive
global MSE reduction. Gated features fix this: a composite-only split
on `comp_archetype_g` and `comp_lower_trip_rank_g` can carve composite
finely without affecting the rest of the tree.

Four features, all gated to composite hands; zeros elsewhere:

  comp_archetype_g          1=trips_two_pair, 2=two_trips, 3=quads_pair,
                            4=quads_trip; 0 if not composite
  comp_lower_trip_rank_g    rank of the LOWER trip in two_trips; 0 else
                            (this is the unique missing piece — baseline
                             trips_rank only carries the higher one)
  comp_singleton_rank_g     rank of the lone singleton in two_trips or
                            quads_pair; 0 if no singleton or non-comp
  comp_higher_pair_rank_g   rank of the higher pair in trips_two_pair;
                            0 elsewhere (mirrors pair_high_rank but
                            zeroed off-archetype to avoid leakage)

Note `pair_low_rank` already covers trips_two_pair's lower pair, and
`pair_high_rank` covers quads_pair's pair. These features are
composite-archetype-specific signals the DT can use after carving the
composite subtree via `comp_archetype_g`.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)


def compute_composite_aug_gated_for_hand(hand: np.ndarray) -> tuple[int, int, int, int]:
    """Return (comp_archetype_g, comp_lower_trip_rank_g,
    comp_singleton_rank_g, comp_higher_pair_rank_g) — zeros for any
    hand that is not in the composite category.
    """
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    counts = Counter(int(r) for r in ranks)
    n_quads = sum(1 for c in counts.values() if c == 4)
    n_trips = sum(1 for c in counts.values() if c == 3)
    n_pairs = sum(1 for c in counts.values() if c == 2)
    n_singles = sum(1 for c in counts.values() if c == 1)

    if n_quads == 0 and n_trips == 1 and n_pairs == 2:
        archetype = 1  # trips_two_pair
        higher_pair = max(r for r, c in counts.items() if c == 2)
        return (1, 0, 0, int(higher_pair))
    if n_quads == 0 and n_trips == 2 and n_pairs == 0:
        trip_ranks = sorted([r for r, c in counts.items() if c == 3])
        lower_trip = trip_ranks[0]
        singleton = next(r for r, c in counts.items() if c == 1)
        return (2, int(lower_trip), int(singleton), 0)
    if n_quads == 1 and n_trips == 0 and n_pairs == 1:
        pair_rank = next(r for r, c in counts.items() if c == 2)
        singleton = next(r for r, c in counts.items() if c == 1)
        return (3, 0, int(singleton), int(pair_rank))
    if n_quads == 1 and n_trips == 1 and n_pairs == 0 and n_singles == 0:
        return (4, 0, 0, 0)
    return (0, 0, 0, 0)


def compute_composite_aug_gated_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)
    b = np.zeros(N, dtype=np.int8)
    c = np.zeros(N, dtype=np.int8)
    d = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_composite_aug_gated_for_hand(h)
        a[i] = v1; b[i] = v2; c[i] = v3; d[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  composite_aug_gated {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "comp_archetype_g": a,
        "comp_lower_trip_rank_g": b,
        "comp_singleton_rank_g": c,
        "comp_higher_pair_rank_g": d,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        ("Ac Ad As Kh Kd Qs Js", "AAA + KK + QJ — trips_two_pair"),
        ("Ac Ad As Kc Kd Kh 7s", "AAA + KKK — two_trips, singleton 7"),
        ("Ac Ad Ah As Kc Kd 7s", "AAAA + KK + 7 — quads_pair"),
        ("Ac Ad Ah As Kc Kd Kh", "AAAA + KKK — quads_trip"),
        ("Ac Ad Kh Qs Js Th 9d", "high_only — zeros"),
        ("Ac Ad As Kh Kd Qs 7c", "AAA + KK + Q + 7 — but n_pairs=1, so trips_pair (not composite)"),
    ]
    for s, label in cases:
        feats = compute_composite_aug_gated_for_hand(hh(*s.split()))
        print(f"{s}  {label}\n  -> {feats}")
