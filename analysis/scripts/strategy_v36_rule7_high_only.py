"""
**ARCHIVED Session 41 — Rule 7 / high_only attempt FAILED, do not ship.**

Full-grid grade (`grade_v36_rule7.py --grid full`):
  v33 = $2,920/1000h whole-grid (40.68% optimal)
  v36 = $2,926/1000h whole-grid (40.16% optimal)  → −$6/1000h regression

Oracle-bound ceiling on the full 1.2M high_only population:
  +$354/1000h whole-grid would be available if a human could pick the
  oracle-best same-suit mid. The drill (`probe_high_only_suited_mid_drill.py`)
  tested 6 heuristic tiebreakers (rank-sum, connected-first, bot-DS-first,
  broadway-first, composite scores) — ALL regressed vs v33. The within-
  same-suit-mid choice is multivariate and has no clean human-readable
  tiebreaker. high_only is confirmed an ML-only category; v34_dt's gated
  ho_*_g features are the path forward.

This file is retained for history only. Do NOT use for production.

---
ORIGINAL DOCSTRING:

Session 41 — v36 = v33 + Rule 7 (high_only same-suit-mid heuristic).

Rule 7 candidate (per `probe_high_only_suited_mid_drill.py` finding):
  When category is high_only (no pair, no trip, no quad in 7 cards):
    1. top = highest-rank singleton (already what v3/v33 do)
    2. mid = the two cards sharing a suit with the highest combined rank
       sum — IF any same-suit pair exists in the remaining 6 cards
       (otherwise fall back to v33's score-based pick).

Why this form (heuristic H1 from the drill):
  - "highest rank-sum same-suit mid" is the simplest deterministic rule
    that still captures the v3/v33 mid-suited-preference idea
  - The drill's other heuristics (connected-first, broadway-first,
    bot-DS-first) all regressed worse than H1
  - H1 itself regresses $-5.88/1000h whole-grid on the 30K drill — but
    we run a full-grid grade here to confirm at scale before deciding

Expected grade vs v33 (full grid): ~$-6/1000h whole-grid (drill scaled).

NOT a candidate to ship in production unless full-grid disagrees with
the drill. Used here as the production-form companion to a possible
oracle-bound strategy-guide ship.
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


def _detect_rule7_high_only_setting(hand: np.ndarray) -> Optional[int]:
    """If hand is high_only AND a same-suit mid exists, return the H1 pick.
    Otherwise return None (caller falls back to v33)."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 0b11

    rank_counts = np.bincount(ranks, minlength=15)
    if any(rank_counts[r] >= 2 for r in range(2, 15)):
        return None  # not high_only

    # Top = highest-rank singleton (high_only ⇒ unique max).
    positions_by_rank_desc = sorted(range(7), key=lambda j: -int(ranks[j]))
    top_pos = positions_by_rank_desc[0]
    rem = [j for j in range(7) if j != top_pos]

    # Find best same-suit (mid_a, mid_b) by rank-sum.
    best_sum = -1
    best_pair: Optional[tuple[int, int]] = None
    for ai in range(6):
        for bi in range(ai + 1, 6):
            a = rem[ai]
            b = rem[bi]
            if int(suits[a]) != int(suits[b]):
                continue
            rs = int(ranks[a]) + int(ranks[b])
            if rs > best_sum:
                best_sum = rs
                best_pair = (a, b)
    if best_pair is None:
        return None  # no same-suit mid available; v33 fallback

    return int(_setting_index_from_tmb(top_pos, best_pair[0], best_pair[1]))


def strategy_v36_rule7_high_only(hand: np.ndarray) -> int:
    """v36 = v33 + Rule 7 (high_only same-suit mid heuristic H1)."""
    chosen = _detect_rule7_high_only_setting(hand)
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
        ("Ah Kh Qd Jc Ts 9h 2d", "high_only A K(♥) Q J T 9 2 — same-suit AK♥"),
        ("Ah Kc Qs Jd Ts 9h 2d", "high_only A K Q J T 9 2 — multiple same-suit options"),
        ("Ac Kd Qh Jc Ts 9h 2d", "Ace♣, Jack♣ — A♣J♣ should be the mid pick"),
    ]
    print(f"{'hand':<28}{'desc':<60}{'v33':>5}  {'v36':>5}  diff")
    for s, label in cases:
        h = canonicalize(hh(*s.split()))
        v33 = strategy_v33_rule6_trips(h)
        v36 = strategy_v36_rule7_high_only(h)
        marker = "*" if v33 != v36 else " "
        print(f"  {s:<26}{label:<60}{v33:>5d}  {v36:>5d}  {marker}")
