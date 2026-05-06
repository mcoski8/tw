"""
Session 37 — v33 = v28_rule5_rainbow + Rule 6 (Trips: mid is always paired).

Rule 6 fires on pure trips (one rank with count 3, no other pairs/quads).

The empirical finding (Session 37 verify_rule6_v14_trips probe):
  - v14 picks "mid is pair-of-trip-rank" on only 94.3% of pure trips.
  - The 5.43% B-routings (3rd trip card on bot) systematically lose ~$3,609
    /1000h within-trips ($197/1000h whole-grid).
  - v14's A-vs-C choice (top is highest-rank kicker vs top is trip-rank) is
    already correct on the 94.3% it gets right. The bug is the 5.43% B-bleed.

Rule 6 = "On pure trips, the third trip card never goes to bot."
       = "Mid is always 2 of the 3 trip-rank cards."
       = "Top is either the third trip card OR the highest-rank kicker."

Implementation: enumerate the A∪C settings, score by a heuristic that
captures the empirical optimum:

  * If trip_rank > max_kicker_rank → C variant (top = trip-rank). Mid = pair
    of trip-rank. Bot = 4 kickers. (1 candidate; suit-symmetric.)

  * Else → A variant (top = highest kicker). Bot = 1 trip + 3 lower kickers.
    Mid = the 2 trip cards not used in bot.
    Among the 3 ways to pick which trip goes to bot, choose the one that
    maximizes bot DS-ness (then bot rank-sum, then connectivity).

Rule 6's A-vs-C choice mirrors what v14 already does empirically (~94.3%
correct), so the gain from the rule is mostly the elimination of B-bleed.
Realistic ship: ~$160-180/1000h whole-grid (heuristic captures most of the
$197 oracle ceiling).
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


def _bot_suit_profile_score(bot_suits: list[int]) -> int:
    """Higher = better for Omaha 2+3. DS=4, SS=3, rainbow=2, 3+1=1, 4-flush=0."""
    counts = [0, 0, 0, 0]
    for s in bot_suits:
        counts[s] += 1
    counts.sort(reverse=True)
    if counts[0] == 2 and counts[1] == 2:
        return 4  # DS
    if counts[0] == 2 and counts[1] == 1:
        return 3  # SS (2+1+1)
    if counts[0] == 1:
        return 2  # rainbow
    if counts[0] == 3:
        return 1  # 3+1
    return 0  # 4-flush


def _bot_longest_run(bot_ranks: list[int]) -> int:
    distinct = sorted(set(bot_ranks))
    longest = 1
    cur = 1
    for k in range(1, len(distinct)):
        if distinct[k] == distinct[k - 1] + 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1
    return longest


def _detect_rule6_trips_setting(hand: np.ndarray) -> Optional[int]:
    """Detect pure trips and return the Rule 6 setting index, else None."""
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
        key=lambda j: -int(ranks[j]),  # descending by rank
    )
    if len(trip_idx) != 3 or len(kicker_idx) != 4:
        return None

    max_kicker_rank = int(ranks[kicker_idx[0]])

    # Decision tree (matches v14's empirical A-vs-C boundary):
    #   * If trip_rank > max_kicker_rank → C variant (top = trip-rank wins
    #     the top tier vs every kicker option).
    #   * Else → A variant (top = highest kicker > trip-rank dominates).
    # This A-vs-C split is what v14 already does ~94.3% correctly. The
    # gain from Rule 6 over v14 is the elimination of the 5.4% B routings,
    # not better A-vs-C decisions. (A joint-scoring heuristic was tested
    # and lost ~$30/1000h due to bot_profile dominating top_rank.)
    if trip_rank > max_kicker_rank:
        # C variant: top = trip-rank, mid = other 2 trips, bot = 4 kickers.
        # Suit-symmetric across the 3 trip cards: pick lowest-byte trip on top.
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


def strategy_v33_rule6_trips(hand: np.ndarray) -> int:
    """v33 = v28_rule5_rainbow + Rule 6 (trips routing override).

    On pure trips, override v28 with the Rule 6 heuristic (always pick A or
    C with the bot-routing optimizer). Empirical comparison on 30K trips:
        override-everything: $+111/1000h whole-grid (56% of $197 oracle ceiling)
        override-only-when-B: $+37/1000h (just removes the 5.4% B bleed)
    The override-everything version wins because the heuristic's bot-DS
    optimization beats v14/v8_hybrid's learned routing on the A variant.
    """
    chosen = _detect_rule6_trips_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v28_rule5_rainbow(hand))


if __name__ == "__main__":
    # Smoke tests on a few canonical-form trips hands.
    from tw_analysis.canonical import canonicalize
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards),
                        dtype=np.uint8)

    cases = [
        ("3c 3d 3h 4s 5s 7c Qd",
         "Trip 3, max kicker Q → A variant (top=Q, bot has 3+suits)"),
        ("Kc Kd Kh 4s 5s 7c Qd",
         "Trip K, max kicker Q < K → C variant (top=K)"),
        ("Ac Ad Ah 4s 5s 7c Qd",
         "Trip A → C variant (top=A)"),
        ("Kc Kd Kh As 5s 7c Qd",
         "Trip K, max kicker A > K → A variant (top=A)"),
        ("Jc Jd Jh As Ks Qc 2d",
         "Trip J, max kicker A > J → A variant (top=A)"),
        ("Jc Jd Jh 9s 8s 6c 2d",
         "Trip J, max kicker 9 < J → C variant (top=J)"),
    ]
    print(f"{'hand':<28}{'expected':<55}-> v14    v28    v33")
    for s, label in cases:
        h = canonicalize(hh(*s.split()))
        from strategy_v14_combined import strategy_v14_combined
        v14 = strategy_v14_combined(h)
        v28 = strategy_v28_rule5_rainbow(h)
        v33 = strategy_v33_rule6_trips(h)
        marker = "*" if v33 != v28 else " "
        print(f"  {s:<26}{label:<55}-> {v14:>3d}{marker}  {v28:>3d}{marker}  {v33:>3d}")
