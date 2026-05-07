"""
Session 39 — v35 = v33 with a sharper Rule 6 boundary, tuned for human play.

The rewrite is motivated by Session 38's per-cell oracle probe
(`probe_rule6_c_variant.py`), which mapped best-A vs best-C oracle EV
across (trip_rank, max_kicker_rank). The empirical map:

  trip A       : C wins 100% of cells (every max_kicker)            → C
  trip K       : C wins 95-100% unless max_kicker = A               → C if no Ace, else A
  trip Q       : C wins ≥56% at max_kicker ≤ T; LOSES at maxK = J,K,A → C unless J/K/A kicker, else A
  trip J       : C narrowly wins at max_kicker ∈ {6,7,8} (small);   → A always (sharper, sacrifices ~$2/1000h trips)
                 LOSES at maxK 5,9,T (and at all higher maxK)
  trip ≤ T     : A wins in every cell with non-trivial sample size   → A

v33's boundary was "trip_rank > max_kicker_rank → C, else A". That works
correctly for trip A (always C) and trip K (C unless A kicker), but is
SUB-OPTIMAL at trip Q (when max_kicker = J, v33 picks C, oracle says A)
and at trip ≤ J with low kickers (v33 picks C, oracle says A).

v35's boundary captures the oracle map cleanly:

  trip rank == A          → C variant (top = third A)
  trip rank == K          → C unless A in kickers (then A: top = A)
  trip rank == Q          → C unless any of {J, K, A} in kickers (then A)
  trip rank ≤ J           → A variant always (top = highest non-trip card)

Equivalent statement for human play:
  "Trip cards almost always pair the mid. The third trip goes ON TOP only
   when no kicker outranks 'trip rank − 1' (a kicker one notch below the
   trip rank), i.e. only when the trip rank itself is the strongest top
   the hand can produce."

The A-variant body (which trip card joins the bot) keeps v33's
(suit_profile, rank_sum, longest_run) optimizer for now. Session 39 will
also rewrite the strategy guide's prose for that step into a hand-traceable
2-step suit-matching rule, but the production heuristic is unchanged.

Why ship v35 in the strategy guide even though the heuristic-A bot-DS
optimizer is the rate-limiting step (see Decision 070): the human reading
the guide can choose ANY A-variant pick, including the oracle-best one,
which v33's prose currently does not steer them toward. The sharper
boundary is for the human; the production bot keeps both rules to be
graded back-to-back on the live grid (run-time evaluation expected to be
within noise per Session 38's sweep, since heuristic-A ≪ oracle-A).
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
    counts = [0, 0, 0, 0]
    for s in bot_suits:
        counts[s] += 1
    counts.sort(reverse=True)
    if counts[0] == 2 and counts[1] == 2:
        return 4
    if counts[0] == 2 and counts[1] == 1:
        return 3
    if counts[0] == 1:
        return 2
    if counts[0] == 3:
        return 1
    return 0


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


def _v35_pick_c(trip_rank: int, kicker_ranks: list[int]) -> bool:
    """v35 boundary. Returns True iff Rule 6 should fire C variant.

    trip A           → C always
    trip K           → C unless an A kicker
    trip Q           → C unless any of {J, K, A} kicker
    trip ≤ J         → A always
    """
    if trip_rank == 14:
        return True
    if trip_rank == 13:
        return 14 not in kicker_ranks
    if trip_rank == 12:
        return not any(k >= 11 for k in kicker_ranks)
    return False


def _detect_rule6_v3_setting(hand: np.ndarray) -> Optional[int]:
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

    kicker_ranks = [int(ranks[j]) for j in kicker_idx]

    if _v35_pick_c(trip_rank, kicker_ranks):
        # C variant: top = trip-rank, mid = other 2 trips, bot = 4 kickers.
        return _setting_index_from_tmb(trip_idx[0], trip_idx[1], trip_idx[2])

    # A variant: top = highest kicker. Bot = 1 trip + 3 lower kickers.
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


def strategy_v35_rule6_v3(hand: np.ndarray) -> int:
    """v35 = v28_rule5_rainbow + Rule 6 v3 (sharper A-vs-C boundary)."""
    chosen = _detect_rule6_v3_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v28_rule5_rainbow(hand))


if __name__ == "__main__":
    from tw_analysis.canonical import canonicalize
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards),
                        dtype=np.uint8)

    cases = [
        # Trip A — always C
        ("Ac Ad Ah Ks Qs Jc 2d", "Trip A → C (top=A) always"),
        # Trip K — C unless A kicker
        ("Kc Kd Kh Qs Js 7c 2d", "Trip K, no Ace → C (top=K)"),
        ("Kc Kd Kh As Qs 7c 2d", "Trip K, with Ace → A (top=A)"),
        # Trip Q — C unless J/K/A kicker
        ("Qc Qd Qh Ts 8s 6c 2d", "Trip Q, kickers ≤ T → C (top=Q)"),
        ("Qc Qd Qh Js 8s 6c 2d", "Trip Q, with J → A (top=J)  [v33 picks C, sharper rule picks A]"),
        ("Qc Qd Qh Ks 8s 6c 2d", "Trip Q, with K → A (top=K)"),
        ("Qc Qd Qh As 8s 6c 2d", "Trip Q, with A → A (top=A)"),
        # Trip J or lower — always A
        ("Jc Jd Jh Ts 9s 8c 2d", "Trip J, kickers low → A (top=T)  [v33 picks C, sharper picks A]"),
        ("Jc Jd Jh As 9s 7c 2d", "Trip J, with A → A (top=A)"),
        ("Tc Td Th 9s 8s 6c 2d", "Trip T, all low → A (top=9)  [v33 picks C, sharper picks A]"),
        ("7c 7d 7h 6s 5s 4c 2d", "Trip 7, all lower → A (top=6)  [v33 picks C, sharper picks A]"),
    ]
    print(f"{'hand':<28}{'expected':<70}{'v33':>5}  {'v35':>5}  diff")
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips
    for s, label in cases:
        h = canonicalize(hh(*s.split()))
        v33 = strategy_v33_rule6_trips(h)
        v35 = strategy_v35_rule6_v3(h)
        marker = "*" if v33 != v35 else ""
        print(f"  {s:<26}{label:<70}{v33:>5d}  {v35:>5d}  {marker}")
