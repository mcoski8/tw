"""
Session 41 — v37 = v33 + Rule 7 (three_pair: where does each pair go?).

v36_rule7_high_only was archived earlier this session (heuristic regressed
$6/1000h on full grid; high_only resists rule extraction). v37 is the
actual Rule 7 ship — for three_pair, where the always-X probe found
clean, heuristic-realizable structure.

Rule 7 (three_pair): TOP = singleton, then:
  if highest_pair_rank ∈ {T, J, Q, K}:
      mid = MIDDLE pair, bot = HIGHEST pair + LOWEST pair  (RB)
  else  (high = A, or high ≤ 9):
      mid = HIGHEST pair, bot = MIDDLE pair + LOWEST pair  (RA)

Why: a broadway non-Ace pair (T-K) on the bot anchors a strong 2-pair
Omaha hand (the high pair becomes a trips draw on board pairs). Aces
are special — pairing AA in the mid is so dominant in Hold'em that
you don't move it. Below T, the "high" pair isn't strong enough on
the bot to outpace what an opponent might hit, so keep it in mid.

Empirical lift (`probe_three_pair_final_rule.py` on full 114K
three_pair population):
  Always RA:                              +$18.36/1000h whole-grid
  Always RB:                              +$24.94/1000h
  ★ RB if high ∈ {T,J,Q,K} else RA:      +$43.05/1000h whole-grid
  Oracle per-cell ceiling:                +$71.18/1000h

The +$43 captures 60% of the per-cell oracle ceiling on a 1-condition
rule. Fully heuristic-realizable (no oracle / ML at runtime).

Production-ship candidate: replaces v33 as the strategy of record at
runtime.
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

from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule7_three_pair_setting(hand: np.ndarray) -> Optional[int]:
    """If hand is exactly three_pair (3 pairs + 1 singleton, no trips/quads),
    return Rule 7's pick. Else return None (caller falls back to v33)."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2

    rank_counts = np.bincount(ranks, minlength=15)
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    if n_pairs != 3 or n_trips != 0 or n_quads != 0:
        return None

    # Identify the 3 pair ranks (descending) + singleton
    pair_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 2],
                        reverse=True)
    singleton_rank = next(r for r in range(2, 15) if rank_counts[r] == 1)
    hpr, mpr, lpr = pair_ranks  # high, middle, low

    pos_high = sorted(j for j in range(7) if int(ranks[j]) == hpr)
    pos_mid = sorted(j for j in range(7) if int(ranks[j]) == mpr)
    pos_singleton = next(j for j in range(7)
                         if int(ranks[j]) == singleton_rank)

    # Boundary: RB if high ∈ {T (10), J (11), Q (12), K (13)}, else RA.
    # (A = 14, so A-high uses RA; ≤9 also uses RA.)
    if 10 <= hpr <= 13:
        # RB: top=singleton, mid=middle pair, bot=high+low pairs
        return int(_setting_index_from_tmb(pos_singleton,
                                           pos_mid[0], pos_mid[1]))
    # RA: top=singleton, mid=high pair, bot=mid+low pairs
    return int(_setting_index_from_tmb(pos_singleton,
                                       pos_high[0], pos_high[1]))


def strategy_v37_rule7_three_pair(hand: np.ndarray) -> int:
    """v37 = v33 + Rule 7 (three_pair routing override)."""
    chosen = _detect_rule7_three_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v33_rule6_trips(hand))


if __name__ == "__main__":
    from tw_analysis.canonical import canonicalize
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}

    def hh(*cards):
        return np.array(sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards),
                        dtype=np.uint8)

    cases = [
        # high=A → RA
        ("Ah Ad Kh Kc Qd Qc 2s",
         "AKQ pairs (high=A) → RA: mid=AA, bot=KK+QQ"),
        ("Ah Ad 5h 5c 2d 2c 7s",
         "A52 pairs (high=A) → RA: mid=AA, bot=55+22"),
        # high=K → RB
        ("Kh Kd Qh Qc 5d 5c 2s",
         "KQ5 pairs (high=K) → RB: mid=QQ, bot=KK+55"),
        # high=Q → RB
        ("Qh Qd Jh Jc 7d 7c 2s",
         "QJ7 pairs (high=Q) → RB: mid=JJ, bot=QQ+77"),
        # high=J → RB
        ("Jh Jd Th Tc 6d 6c 2s",
         "JT6 pairs (high=J) → RB: mid=TT, bot=JJ+66"),
        # high=T → RB
        ("Th Td 9h 9c 5d 5c 2s",
         "T95 pairs (high=T) → RB: mid=99, bot=TT+55"),
        # high=9 → RA
        ("9h 9d 5h 5c 3d 3c 2s",
         "953 pairs (high=9) → RA: mid=99, bot=55+33"),
        # high=4 → RA
        ("4h 4d 3h 3c 2d 2c Qs",
         "432 pairs (high=4) → RA: mid=44, bot=33+22"),
    ]
    print(f"{'hand':<28}{'desc':<60}{'v33':>5}  {'v37':>5}  diff")
    for s, label in cases:
        h = canonicalize(hh(*s.split()))
        v33 = strategy_v33_rule6_trips(h)
        v37 = strategy_v37_rule7_three_pair(h)
        marker = "*" if v33 != v37 else " "
        print(f"  {s:<26}{label:<60}{v33:>5d}  {v37:>5d}  {marker}")
