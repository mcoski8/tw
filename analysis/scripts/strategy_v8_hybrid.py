"""
v8_hybrid: v7_regression + v3 fallback for high_only and pair categories.

Empirical motivation (50K-grid analysis):
  - v7 LOSES to v3 on high_only hands by -$203/1000h × 21% share = -$42/1000h.
  - v7 LOSES to v3 on pair hands by -$50/1000h × 49% share = -$24/1000h.
  - v7 WINS handsomely on two_pair / three_pair / trips / trips_pair / quads.
  - The win comes from multi-pair routing decisions; v7 doesn't beat v3 on
    the simple cases.

So for high_only and one-pair hands, fall back to v3's hand-coded chain.
For everything else, use v7's learned tree.

Two variants:
  v8_high_only_only: v3 for high_only, v7 for everything else.
  v8_hybrid:         v3 for high_only AND pair, v7 for everything else.
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

from encode_rules import strategy_v3, hand_decompose  # noqa: E402
from strategy_v7_regression import strategy_v7_regression  # noqa: E402
from strategy_v7_patched import is_aakk  # noqa: E402


def is_high_only(hand: np.ndarray) -> bool:
    d = hand_decompose(hand)
    return not d["pairs"] and not d["trips"] and not d["quads"]


def is_one_pair(hand: np.ndarray) -> bool:
    d = hand_decompose(hand)
    return len(d["pairs"]) == 1 and not d["trips"] and not d["quads"]


def strategy_v8_high_only_only(hand: np.ndarray) -> int:
    """v7 except use v3 for high_only hands."""
    if is_high_only(hand):
        return int(strategy_v3(hand))
    if is_aakk(hand):
        return int(strategy_v3(hand))
    return int(strategy_v7_regression(hand))


def strategy_v8_hybrid(hand: np.ndarray) -> int:
    """v7 except use v3 for high_only and one_pair hands; AAKK exception."""
    if is_aakk(hand):
        return int(strategy_v3(hand))
    if is_high_only(hand) or is_one_pair(hand):
        return int(strategy_v3(hand))
    return int(strategy_v7_regression(hand))


if __name__ == "__main__":
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards), dtype=np.uint8)
    high = hh("Ah","Kc","Qd","Jh","7d","5d","3c")  # high_only
    pair = hh("8h","8d","Ks","Qs","7d","5h","Ac")  # one_pair
    twop = hh("Ac","Ad","Kc","Kh","7s","5d","2h")  # two_pair AAKK
    print(f"high_only: hybrid={strategy_v8_hybrid(high)} v7={strategy_v7_regression(high)} v3={strategy_v3(high)}")
    print(f"one_pair:  hybrid={strategy_v8_hybrid(pair)} v7={strategy_v7_regression(pair)} v3={strategy_v3(pair)}")
    print(f"two_pair:  hybrid={strategy_v8_hybrid(twop)} v7={strategy_v7_regression(twop)} v3={strategy_v3(twop)}")
