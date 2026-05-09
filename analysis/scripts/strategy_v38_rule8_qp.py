"""
Session 42 — v38 = v37 + Rule 8 (composite quads_pair → quad-in-mid).

PRODUCTION SHIP. Replaces v37 as the strategy of record.

The two_pair Rule 8 candidate (boundary search → +$197/1000h whole-grid
on full N=200) was DEFERRED after the prefix grade showed -$512/1000h
regression — every forced-single-pick variant lost on prefix because
v33 splits pairs adaptively on weak hands. See
strategy_v38_rule8_two_pair_DEFERRED.py and the Session 42 entry in
STRATEGY_GUIDE.md for the full reasoning. v38 instead ships the smaller
but consistently-positive composite QP rule below.

quads_pair (4+2+1) is 0.057% of canonical hands. v33 leaves $17,101/1000h
within-st on the table (= $9.77/1000h whole-grid).

Heuristic-realizable rule (verified 100% capture vs oracle-within-constraint):
  TOP = the singleton card.
  MID = the 2 quad cards whose suits are NOT the pair's suits.
  BOT = the other 2 quad cards + both pair cards.

Result: bot is always double-suited (2 pair-suit-quads + 2 pair-suit-pair-cards
= 2 of suit X + 2 of suit Y when pair is suits {X, Y}).

Empirical lift:
  Δ vs v33 = +$9.42/1000h whole-grid (full N=200 grid)
  Δ vs v33 = +$18.63/1000h whole-prefix (prefix N=1000 grid)

100% deterministic-realizable (no oracle / ML). Heuristic capture matches
the oracle-within-constraint exactly: when you commit to "quad-in-mid",
the only EV-distinguishing choice is suit composition, and the structural
heuristic ("mid takes the non-pair-suit quads") nails it.
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

from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule8_qp_setting(hand: np.ndarray) -> Optional[int]:
    """If hand is exactly quads_pair (1 quad + 1 pair + 1 singleton),
    return Rule 8's deterministic pick. Else None (caller falls back to v37)."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 0b11
    rank_counts = np.bincount(ranks, minlength=15)
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    if n_quads != 1 or n_pairs != 1 or n_trips != 0:
        return None

    quad_rank = next(r for r in range(2, 15) if rank_counts[r] >= 4)
    pair_rank = next(r for r in range(2, 15) if rank_counts[r] == 2)
    sing_rank = next(r for r in range(2, 15) if rank_counts[r] == 1)

    pair_suits = sorted(int(suits[j]) for j in range(7)
                        if int(ranks[j]) == pair_rank)
    non_pair_suits = sorted(set(range(4)) - set(pair_suits))
    pos_quad_at_nps = sorted(j for j in range(7)
                              if int(ranks[j]) == quad_rank
                              and int(suits[j]) in non_pair_suits)
    pos_sing = next(j for j in range(7) if int(ranks[j]) == sing_rank)

    # Mid = the 2 quad cards whose suits are NOT the pair's suits.
    return int(_setting_index_from_tmb(pos_sing,
                                       pos_quad_at_nps[0],
                                       pos_quad_at_nps[1]))


def strategy_v38_rule8_qp(hand: np.ndarray) -> int:
    """v38 = v37 + Rule 8 (composite quads_pair → quad-in-mid)."""
    chosen = _detect_rule8_qp_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v37_rule7_three_pair(hand))


if __name__ == "__main__":
    from tw_analysis.canonical import canonicalize
    RANK = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
            "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
    SUIT = {"c": 0, "d": 1, "h": 2, "s": 3}

    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                        dtype=np.uint8)

    cases = [
        ("Ac Ad Ah As Kc Kd 2s",
         "AAAA + KK + 2s — pair_suits={c,d}, mid quads at h+s"),
        ("9c 9d 9h 9s 5c 5d 7s",
         "9999 + 55 + 7s — pair_suits={c,d}, mid quads at h+s"),
        ("2c 2d 2h 2s 7h 7s Qc",
         "2222 + 77 + Qc — pair_suits={h,s}, mid quads at c+d"),
    ]
    print(f"{'hand':<28}{'desc':<60}{'v37':>5}  {'v38':>5}  diff")
    for s, label in cases:
        h_arr = canonicalize(hh(*s.split()))
        v37 = strategy_v37_rule7_three_pair(h_arr)
        v38 = strategy_v38_rule8_qp(h_arr)
        marker = "*" if v37 != v38 else " "
        print(f"  {s:<26}{label:<60}{v37:>5d}  {v38:>5d}  {marker}")
