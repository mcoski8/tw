"""
Session 38 — v34 = v28_rule5_rainbow + Rule 6 v2 (corrected A-vs-C boundary).

Session 37's v33 implemented Rule 6 with the boundary
    if trip_rank > max_kicker_rank → C variant (top = trip card)
    else                            → A variant (top = highest kicker)

Session 38's probe (probe_rule6_c_variant) revealed:
  * Per-cell C-A breakdown (positive = C beats A):
    - trip A all max_K: C wins by $5k–$14k everywhere
    - trip K max_K ≤ Q: C wins by $2k–$7k everywhere
    - trip Q max_K ≤ T: C wins by $0.8k–$3.8k
    - trip Q max_K = J: A wins by $0.3k (small)
    - trip J max_K = 5,9,T: A wins by $2.6k–$3.7k
    - trip J max_K = 6,7,8: C wins by $0.2k–$1.4k (small + noisy)
    - trip ≤ T max_K < trip: A wins overwhelmingly ($1.7k–$17k)

  v33's boundary "trip > max_kicker → C" is correct at trip {Q, K, A} but
  WRONG at trip ≤ J and at trip Q max_K=J. Empirical loss from those wrong
  C-picks: ~$10/1000h whole-grid (vs an oracle ceiling of +$12.89).

  An initial v34 attempt with "trip ≥ K → C, else A" *over-corrected*: it
  cost the wins at trip Q low max_K, losing $10/1000h vs v33.

Rule 6 v2 boundary (corrected):
    if trip_rank ≥ Q AND trip_rank > max_kicker_rank → C variant
    else                                              → A variant

Memorable statement: "Use the third trip card on top ONLY when the trip is
Q-or-better AND no kicker outranks the trips."

Same A-variant heuristic as v33 (bot DS optimization). Same fallback to v28
when not pure trips.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v33_rule6_trips import (  # noqa: E402
    _bot_suit_profile_score,
    _bot_longest_run,
)


def _detect_rule6_v2_setting(hand: np.ndarray) -> Optional[int]:
    """Detect pure trips and return the Rule 6 v2 setting index, else None."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 0b11

    rank_counts = np.bincount(ranks, minlength=15)
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    if n_trips != 1 or n_pairs != 0 or n_quads != 0:
        return None

    trip_rank = next(r for r in range(2, 15) if rank_counts[r] == 3)
    trip_idx = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
    kicker_idx = sorted(
        (j for j in range(7) if j not in trip_idx),
        key=lambda j: -int(ranks[j]),
    )
    if len(trip_idx) != 3 or len(kicker_idx) != 4:
        return None

    max_kicker_rank = int(ranks[kicker_idx[0]])

    # Rule 6 v2 boundary: C variant only for trip ≥ Q when feasible.
    # (Trip ≥ 12 = Q.)
    use_c = (trip_rank >= 12) and (trip_rank > max_kicker_rank)

    if use_c:
        # C variant: top = trip-rank, mid = other 2 trips, bot = 4 kickers.
        return _setting_index_from_tmb(trip_idx[0], trip_idx[1], trip_idx[2])

    # A variant: top = highest kicker. Bot = 1 trip + 3 lower kickers.
    # Pick which trip → bot to maximize bot DS-ness, then rank-sum, then run.
    top_pos = kicker_idx[0]
    other_kickers = kicker_idx[1:4]
    other_kicker_suits = [int(suits[j]) for j in other_kickers]
    other_kicker_ranks = [int(ranks[j]) for j in other_kickers]
    best_score = -1
    best_setting: Optional[int] = None
    for trip_for_bot_pos_idx in range(3):
        trip_for_bot = trip_idx[trip_for_bot_pos_idx]
        trips_for_mid = [trip_idx[i] for i in range(3) if i != trip_for_bot_pos_idx]
        bot_suits = [int(suits[trip_for_bot])] + other_kicker_suits
        bot_ranks = [int(ranks[trip_for_bot])] + other_kicker_ranks
        profile = _bot_suit_profile_score(bot_suits)
        rank_sum = sum(bot_ranks)
        run = _bot_longest_run(bot_ranks)
        score = profile * 1_000_000 + rank_sum * 1_000 + run * 100
        if score > best_score:
            best_score = score
            best_setting = _setting_index_from_tmb(top_pos, trips_for_mid[0],
                                                  trips_for_mid[1])
    return best_setting


def strategy_v34_rule6_v2(hand: np.ndarray) -> int:
    """v34 = v28 + Rule 6 v2 (C only when trip_rank ≥ Q AND trip > max_kicker)."""
    chosen = _detect_rule6_v2_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v28_rule5_rainbow(hand))


if __name__ == "__main__":
    from tw_analysis.canonical import canonicalize
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips

    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards),
                        dtype=np.uint8)

    cases = [
        ("3c 3d 3h 4s 5s 7c Qd",
         "Trip 3 (low) → A variant ALWAYS now (was A in v33 too)"),
        ("Kc Kd Kh 4s 5s 7c Qd",
         "Trip K, max kicker Q < K → C variant (was C, still C)"),
        ("Ac Ad Ah 4s 5s 7c Qd",
         "Trip A → C variant (was C, still C)"),
        ("Kc Kd Kh As 5s 7c Qd",
         "Trip K, max kicker A > K → A variant (was A, still A)"),
        ("Jc Jd Jh As Ks Qc 2d",
         "Trip J, max kicker A > J → A variant (was A, still A)"),
        ("Jc Jd Jh 9s 8s 6c 2d",
         "Trip J, max kicker 9 < J → v33: C, v34: A (CHANGED)"),
        ("Qc Qd Qh 9s 8s 6c 2d",
         "Trip Q, max kicker 9 < Q → C variant (v33 + v34 agree)"),
        ("Tc Td Th 5s 4s 3c 2d",
         "Trip T, max kicker 5 < T → v33: C, v34: A (CHANGED)"),
        ("Qc Qd Qh Js 8s 6c 2d",
         "Trip Q, max kicker J < Q → v33: C, v34: C (small edge — keep v33)"),
    ]
    print(f"{'hand':<28}{'description':<55}-> v33  v34  match?")
    for s, label in cases:
        h = canonicalize(hh(*s.split()))
        v33 = strategy_v33_rule6_trips(h)
        v34 = strategy_v34_rule6_v2(h)
        marker = "*CHANGED*" if v33 != v34 else "same"
        print(f"  {s:<26}{label:<55}-> {v33:>3d}  {v34:>3d}  {marker}")
