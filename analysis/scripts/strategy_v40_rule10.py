"""
Session 43 — v40 = v39 + Rule 10 (J-low pair defensive).

Rule 10 (J-low single-pair defensive):

  Fires on hands where:
    - category == pair (exactly one pair, no trip/quad)
    - max_rank <= J  (i.e., the J-low defensive zone)
  Setting:
    - TOP = lowest singleton (the WEAKEST card, dumped to top)
    - MID = the pair (mid Hold'em paired anchor)
    - BOT = the 4 HIGHEST non-pair singletons

Discovered in Session 43's drill_low_pair_J_high_defense.py (Q3). The
underlying intuition is the "weak-hand inversion": when even your highest
card can't win the top tier reliably, sacrifice it to top-tier loss and
stack the bot with the strong cards. The pair stays in mid as a Hold'em
pair anchor (still the best mid for these hands by 60-85% of oracle picks).

Lift (drill_low_pair_J_high_defense.py FULL run, 342,720 hands):
    +$22.73/1000h whole-grid (full N=200)
    +$36.70/1000h whole-grid (prefix N=1000)

Both grids positive — passes the Session 42 both-grid validation gate. The
prefix lift is BIGGER than the full lift (+$36.70 > +$22.73), which is the
opposite of the "prefix-regression risk" pattern. Methodology: this is the
only Session 43 candidate that cleared the both-grid gate — Q1 was already
optimized, Q4 (two_pair) confirmed ML-only, Q5 (no-pair) has zero prefix
coverage (full-only).

Note: structurally this rule fires on a subset of v39's existing pair
fallthrough (which routes to v3 via v8_hybrid). It overrides v3's default
"top=hi-singleton, mid=pair, bot=4 lower" with "top=lo-singleton, mid=pair,
bot=4 higher". Rules 1-9 do not interact (Rule 1 fires on pair-rank in
{2-5, T-Q} WITH AN ACE — none of the J-low pair hands have an Ace since
max <= J).

Per-cell breakdown (from drill, full grid):
  - max=7-high cells (pair 2-7): all positive ($0.11-$0.19/cell)
  - max=8-high cells (pair 2-8): positive except pair=7 (-$0.04, marginal)
  - max=9-high cells (pair 2-9): positive except pair=7,8 (small regressions)
  - max=T-high cells (pair 2-T): positive except pair=7,8,9
  - max=J-high cells (pair 2-J): positive except pair=2 (-$0.23, small) and
    pair=7,8,9,T (-$2 to -$8/cell)

The rule fires uniformly across J-low pair (no internal gate) for
human-memorability. A gated variant ("pair_rank ≤ 6 OR pair_rank == max")
captures more of the upside (~+$48/1000h whole-grid full) but at the cost
of an extra condition. Per Session 42 methodology rule "diminishing returns
beyond the natural structural break", the simple version is preferred for
human memorization; the gated version is a future ML refinement.

Run:
  python3 -c "from strategy_v40_rule10 import strategy_v40_rule10; ..."
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

from strategy_v39_rule9 import strategy_v39_rule9  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule10_jlow_pair(hand: np.ndarray) -> Optional[int]:
    """Rule 10: max_rank <= J AND category == pair → top=lo-sing, mid=pair,
    bot=4 highest non-pair singletons.
    Returns the setting_index, or None if hand doesn't match."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 0 or n_pairs != 1:
        return None
    max_r = int(ranks.max())
    if max_r > 11:  # J = 11
        return None
    P = next(r for r in range(2, 15) if rc[r] == 2)
    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == P)
    sings_pos = sorted([j for j in range(7) if int(ranks[j]) != P],
                        key=lambda j: (-int(ranks[j]), j))
    # singletons sorted by rank desc (5 of them)
    top_pos = sings_pos[-1]  # lowest singleton
    mid_a, mid_b = sorted(pos_pair)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def strategy_v40_rule10(hand: np.ndarray) -> int:
    """v40 = v39 + Rule 10 (J-low pair defensive).

    Rule 10 fires BEFORE v39 fallthrough (which would otherwise hit Rule 1
    or v8_hybrid). This is intentional: Rule 10 is structurally a NEW rule
    on a NEW population (J-low pair, no Ace), not a refinement of an
    existing rule. None of Rules 1-9 fire on this population (Rule 1
    requires an Ace; Rules 2-9 require trips/quads/multi-pair).
    """
    chosen = _detect_rule10_jlow_pair(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v39_rule9(hand))


if __name__ == "__main__":
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards),
                         dtype=np.uint8)
    # J-high pair=5: rule should fire
    h1 = hh("Jh", "9c", "7c", "5d", "5c", "3h", "2s")
    print(f"Jh 9c 7c 5d 5c 3h 2s (J-high pair=5): "
           f"v39={strategy_v39_rule9(h1)} v40={strategy_v40_rule10(h1)} "
           f"rule10_fired={_detect_rule10_jlow_pair(h1) is not None}")
    # Q-high pair=5: rule should NOT fire (max > J)
    h2 = hh("Qh", "9c", "7c", "5d", "5c", "3h", "2s")
    print(f"Qh 9c 7c 5d 5c 3h 2s (Q-high pair=5): "
           f"v39={strategy_v39_rule9(h2)} v40={strategy_v40_rule10(h2)} "
           f"rule10_fired={_detect_rule10_jlow_pair(h2) is not None}")
    # J-high two-pair: should NOT fire (n_pairs != 1)
    h3 = hh("Jh", "9c", "7c", "5d", "5c", "3h", "3s")
    print(f"Jh 9c 7c 5d 5c 3h 3s (J-high two-pair): "
           f"v39={strategy_v39_rule9(h3)} v40={strategy_v40_rule10(h3)} "
           f"rule10_fired={_detect_rule10_jlow_pair(h3) is not None}")
