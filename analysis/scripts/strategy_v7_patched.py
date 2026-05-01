"""
v7_patched: v7_regression + v3's hand-coded AAKK exception.

Drop-in replacement for strategy_v7_regression. For most hands, behaves
identically to v7. For AAKK-shape hands (high pair = AA AND low pair = KK),
overrides v7's pick with v3's hand-coded routing (KK to mid, AA to bot,
low singleton on top).

Empirical motivation: targeted MC on Ac Ad Kc Kh 7s 5d 2h showed v7's pick
loses $361/1000h vs v3's pick on this hand. AAKK is rare (~0.2% of hands)
but the per-hand swing is large enough to matter. The v3 hand-coded rule
ties the oracle on this hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v7_regression import strategy_v7_regression  # noqa: E402
from encode_rules import strategy_v3, hand_decompose  # noqa: E402


def is_aakk(hand: np.ndarray) -> bool:
    """True iff the hand is exactly AAKK + 3 singletons."""
    d = hand_decompose(hand)
    pairs = d["pairs"]
    if len(pairs) != 2:
        return False
    high_rank, _ = pairs[0]
    low_rank, _ = pairs[1]
    return high_rank == 14 and low_rank == 13


def strategy_v7_patched(hand: np.ndarray) -> int:
    """v7_regression for most hands; v3's hand-coded AAKK exception when applicable."""
    if is_aakk(hand):
        return int(strategy_v3(hand))
    return int(strategy_v7_regression(hand))


if __name__ == "__main__":
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards), dtype=np.uint8)

    aakk = hh("Ac","Ad","Kc","Kh","7s","5d","2h")
    not_aakk = hh("Ks","Qs","8h","8d","7d","5h","Ac")
    print(f"AAKK hand:     v7_patched picks {strategy_v7_patched(aakk)} (should match v3's setting)")
    print(f"Not AAKK hand: v7_patched picks {strategy_v7_patched(not_aakk)} (should match v7's setting)")
