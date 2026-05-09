"""
Session 42 overnight — v39 = v38 + Rule 9 (plain quads + TT E3a + T2P boundary).

Three new structural rules discovered in the overnight rule-mining pipeline:

  ── Rule 9a: Plain quads (4+1+1+1 = 1 quad + 3 singletons, 0.238% of hands)
    Lift: +$15.31/1000h whole-grid (full N=200) + +$11.78/1000h whole-prefix
    Mirror of Rule 8 QP — same suit-aware structural insight:
      TOP = the highest singleton
      MID = the 2 quad cards whose SUITS are NOT used by any of the 3 singletons
      BOT = the other 2 quads + the 2 lower singletons
    100% deterministic. Captures 73% of the +$21.02 oracle ceiling.

  ── Rule 9b: TT (3+3+1 = 2 trips + singleton, 0.071% of hands)
    Lift: +$3.57/1000h whole-grid (full) + +$2.79/1000h whole-prefix
    E3a structure (split-the-high-trip-to-top):
      TOP = a HIGH-trip card whose suit IS in the LOW-trip's suits
      MID = the FULL LOW-trip pair (2 of 3 L-trip cards)
      L-BOT = the L-trip card whose suit best matches the bot's H-trip suits
              + singleton's suit (DS-aware tiebreaker)
      BOT = 2 H-trip cards + 1 L-trip card + singleton
    Captures 60% of the +$5.98 oracle ceiling.

  ── Rule 9c: T2P (3+2+2 = 1 trip + 2 pairs, 0.114% of hands)
    Lift: +$2.81/1000h whole-grid (full) + +$13.48/1000h whole-prefix
    Boundary: if trip-rank <= 4, F3 (mid=LO pair, bot=2T+HI pair);
              else F2 (mid=HI pair, bot=2T+LO pair).
    Suit-aware top-T pick: a T-member whose suit is NOT shared with either
    pair if possible.
      TOP = a trip-member at the suit ∉ pair-suits (else first trip-member)
      MID = the LOW pair (if trip-rank <= 4) OR the HIGH pair (if trip-rank >= 5)
      BOT = 2 trip-leftovers + the OTHER pair (4 cards = trips-on-bot + pair)
    Why: when the trip is very low (2-4), the bot's "trips-on-board" anchor is
    weak; better to put the HIGH pair on bot for a stronger 2-pair Omaha.
    When the trip is 5+, mid Hold'em strength of HH outweighs bot value of HH.

Combined v39 lift over v38: ~+$21.7/1000h whole-grid (full) + ~+$28/1000h (prefix).
All three rules both-grid positive — clean both-grid ship.

The two_pair Rule 8 candidate from Session 42 morning (+$197 full / -$512 prefix)
remains DEFERRED.

Run:
  python3 -c "from strategy_v39_rule9 import strategy_v39_rule9; ..."
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

from strategy_v38_rule8_qp import strategy_v38_rule8_qp  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule9a_plain_quads(hand: np.ndarray) -> Optional[int]:
    """Plain quads: 1 quad + 3 singletons, no second pair, no trips.
    Mirror of Rule 8 QP's suit-aware mid-pick."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 0b11
    rank_counts = np.bincount(ranks, minlength=15)
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    if n_quads != 1 or n_pairs != 0 or n_trips != 0:
        return None

    quad_rank = next(r for r in range(2, 15) if rank_counts[r] >= 4)
    sing_ranks = sorted(
        [r for r in range(2, 15) if rank_counts[r] == 1], reverse=True)
    pos_quad = sorted(j for j in range(7) if int(ranks[j]) == quad_rank)
    pos_s_hi = next(j for j in range(7) if int(ranks[j]) == sing_ranks[0])

    sing_suits = {int(suits[j]) for j in range(7)
                  if int(ranks[j]) in sing_ranks}

    non_sing_quads = sorted(
        j for j in pos_quad if int(suits[j]) not in sing_suits)
    if len(non_sing_quads) >= 2:
        mid_a, mid_b = non_sing_quads[0], non_sing_quads[1]
    else:
        # All 4 suits used by singletons (rare: 3 singletons cover 3 suits +
        # the quads' missing-suit equals one singleton-suit). Fall back to
        # the canonical first 2 quads for a deterministic pick.
        mid_a, mid_b = pos_quad[0], pos_quad[1]

    return int(_setting_index_from_tmb(pos_s_hi, mid_a, mid_b))


def _detect_rule9b_tt(hand: np.ndarray) -> Optional[int]:
    """TT (two_trips): 2 trips + 1 singleton, no quads/pairs.
    E3a structure with suit-aware top + L-bot picks."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 0b11
    rank_counts = np.bincount(ranks, minlength=15)
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    if n_trips != 2 or n_quads != 0 or n_pairs != 0:
        return None

    trips = sorted([r for r in range(2, 15) if rank_counts[r] == 3],
                   reverse=True)
    H, L = trips[0], trips[1]
    S = next(r for r in range(2, 15) if rank_counts[r] == 1)
    pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
    pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
    pos_S = next(j for j in range(7) if int(ranks[j]) == S)
    s_suit = int(suits[pos_S])
    L_suits = sorted(int(suits[j]) for j in pos_L)
    L_set = set(L_suits)

    # TOP = an H-trip card at suit ∈ L_suits (per the heuristic hunt).
    top_pos = None
    for k in range(3):
        if int(suits[pos_H[k]]) in L_set:
            top_pos = pos_H[k]
            break
    if top_pos is None:
        top_pos = pos_H[0]  # fallback (no H-suit overlaps L-suits)

    # L-bot: pick the L-trip card whose suit maximizes DS-aware score.
    # Bot has 2 H (the non-top H-trip cards) + 1 L + 1 S. DS bot wants
    # 2-of-suit-X + 2-of-suit-Y. For each L-bot candidate, score by:
    #   (1 if L-suit matches a remaining-H-suit) + (1 if L-suit == s_suit)
    rem_h_suits = [int(suits[j]) for j in pos_H if j != top_pos]
    best_score = -1
    L_bot = pos_L[0]
    for k in range(3):
        l_suit = int(suits[pos_L[k]])
        score = (1 if l_suit in rem_h_suits else 0) + (1 if l_suit == s_suit else 0)
        if score > best_score:
            best_score = score
            L_bot = pos_L[k]
    mid_a, mid_b = sorted(j for j in pos_L if j != L_bot)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _detect_rule9c_t2p(hand: np.ndarray) -> Optional[int]:
    """T2P (trips_two_pair): 1 trip + 2 pairs, no quads/singletons.
    Boundary: F3 if T<=4 else F2, with suit-aware top-T pick."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 0b11
    rank_counts = np.bincount(ranks, minlength=15)
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    if n_trips != 1 or n_pairs != 2 or n_quads != 0:
        return None

    T = next(r for r in range(2, 15) if rank_counts[r] == 3)
    pair_ranks = sorted(
        [r for r in range(2, 15) if rank_counts[r] == 2], reverse=True)
    H, L = pair_ranks
    pos_T = sorted(j for j in range(7) if int(ranks[j]) == T)
    pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
    pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
    pair_suits = (set(int(suits[j]) for j in pos_H)
                  | set(int(suits[j]) for j in pos_L))
    # Top = a trip-member whose suit is NOT in pair_suits if possible
    outside = [j for j in pos_T if int(suits[j]) not in pair_suits]
    top_T = outside[0] if outside else pos_T[0]
    if T <= 4:
        # F3: mid = LOW pair, bot = 2T + HIGH pair
        return int(_setting_index_from_tmb(top_T, pos_L[0], pos_L[1]))
    # F2: mid = HIGH pair, bot = 2T + LOW pair
    return int(_setting_index_from_tmb(top_T, pos_H[0], pos_H[1]))


def strategy_v39_rule9(hand: np.ndarray) -> int:
    """v39 = v38 + Rule 9 (plain quads + TT E3a + T2P boundary)."""
    chosen = _detect_rule9a_plain_quads(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_rule9b_tt(hand)
    if chosen is not None:
        return int(chosen)
    chosen = _detect_rule9c_t2p(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v38_rule8_qp(hand))
