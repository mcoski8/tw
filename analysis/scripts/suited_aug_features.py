"""
Session 29 — suited-broadway aug features.

The Session 28 high_only deep-dive surfaced a class of hands where the
oracle picks a suited middle (e.g. 5d-Kd in `2c 5d 6h 7s Ts Kd Ad`) but
v16/v18's 37-feature set has no way to represent "two cards of the same
suit with one or both being broadway." `suit_max` only encodes the count
of the most-common suit, not the ranks involved.

Six features computed for ALL 6M canonical hands (not gated by category):

  n_suited_pairs_total         (0-21)   count of all (i,j) pairs i<j with
                                         hand[i] same suit as hand[j].
                                         Encodes overall suit clustering.
  max_suited_pair_high_rank    (0,2-14) max(rank_a, rank_b) over all suited
                                         pairs. 0 if no suited pair.
                                         Encodes "is there a high suited card
                                         that has a partner."
  max_suited_pair_low_rank     (0,2-14) max(min(rank_a, rank_b)) over all
                                         suited pairs. 0 if none. Encodes
                                         "are BOTH cards in a suited pair
                                         high" — direct signal for the
                                         high_only suited-mid pattern.
  has_suited_broadway_pair     (0/1)    1 if any suited pair has BOTH cards
                                         rank ≥ T (10).
  has_suited_premium_pair      (0/1)    1 if any suited pair has BOTH cards
                                         rank ≥ J (11).
  n_broadway_in_largest_suit   (0-7)    count of broadway cards in the
                                         most-common suit. Captures
                                         "concentration of high cards in
                                         one suit" without depending on
                                         which suit it is.

These six are sufficient (we hope) to let the DT discover the suited-mid
routing pattern. If v19 doesn't improve, we'll add more.
"""
from __future__ import annotations

import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)


_PAIRS_OF_7 = list(combinations(range(7), 2))  # 21 tuples


def compute_suited_aug_for_hand(hand: np.ndarray) -> tuple[int, int, int, int, int, int]:
    """Returns (n_suited_pairs_total, max_suited_pair_high_rank,
    max_suited_pair_low_rank, has_suited_broadway_pair,
    has_suited_premium_pair, n_broadway_in_largest_suit) for ONE 7-card
    canonical hand."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0, 0, 0)
    ranks = (hand // 4) + 2  # 2..14
    suits = hand % 4

    n_suited_pairs = 0
    max_high = 0
    max_low = 0
    has_bw_pair = 0
    has_prem_pair = 0
    for (i, j) in _PAIRS_OF_7:
        if suits[i] == suits[j]:
            n_suited_pairs += 1
            ra = int(ranks[i])
            rb = int(ranks[j])
            hi = ra if ra > rb else rb
            lo = ra if ra < rb else rb
            if hi > max_high:
                max_high = hi
            if lo > max_low:
                max_low = lo
            if lo >= 10:  # both ≥ T
                has_bw_pair = 1
            if lo >= 11:  # both ≥ J
                has_prem_pair = 1

    # n_broadway_in_largest_suit
    suit_counts = np.zeros(4, dtype=np.int8)
    for s in suits:
        suit_counts[int(s)] += 1
    largest_suit = int(suit_counts.argmax())
    n_bw_in_largest = 0
    for k in range(7):
        if int(suits[k]) == largest_suit and int(ranks[k]) >= 10:
            n_bw_in_largest += 1

    return (
        n_suited_pairs,
        max_high,
        max_low,
        has_bw_pair,
        has_prem_pair,
        n_bw_in_largest,
    )


def compute_suited_aug_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    """Compute the 6 features over the WHOLE hands array."""
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)  # n_suited_pairs_total
    b = np.zeros(N, dtype=np.int8)  # max_suited_pair_high_rank
    c = np.zeros(N, dtype=np.int8)  # max_suited_pair_low_rank
    d = np.zeros(N, dtype=np.int8)  # has_suited_broadway_pair
    e = np.zeros(N, dtype=np.int8)  # has_suited_premium_pair
    f = np.zeros(N, dtype=np.int8)  # n_broadway_in_largest_suit
    t0 = time.time()
    for i in range(N):
        f1, f2, f3, f4, f5, f6 = compute_suited_aug_for_hand(np.asarray(hands[i], dtype=np.uint8))
        a[i] = f1
        b[i] = f2
        c[i] = f3
        d[i] = f4
        e[i] = f5
        f[i] = f6
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  suited_aug {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "n_suited_pairs_total": a,
        "max_suited_pair_high_rank": b,
        "max_suited_pair_low_rank": c,
        "has_suited_broadway_pair": d,
        "has_suited_premium_pair": e,
        "n_broadway_in_largest_suit": f,
    }


if __name__ == "__main__":
    # Spot test.
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    cases = [
        ("2c 5d 6h 7s Ts Kd Ad", "high_only example with 3 diamonds (5,K,A)"),
        ("2c 3c 4c 5d 6h 7s 8c", "4 clubs, no broadway"),
        ("Ac Ad Ah Kc Kd Qc Qd", "trips_pair AAA + KK + QQ, lots of suited"),
        ("Js Qs Kh Ah 2c 5d 9c", "Js-Qs suited (premium), no other strong suited pairs"),
        ("Tc Jc Qd Kd Ah 2s 3s", "Tc-Jc suited broadway, Qd-Kd suited broadway"),
    ]
    for s, label in cases:
        h = hh(*s.split())
        r = compute_suited_aug_for_hand(h)
        print(f"\n  {s}  ({label})")
        print(f"    n_suited_pairs_total={r[0]} max_high={r[1]} max_low={r[2]} has_bw_pair={r[3]} has_prem_pair={r[4]} n_bw_in_largest={r[5]}")
