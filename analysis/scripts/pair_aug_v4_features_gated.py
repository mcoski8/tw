"""
Session 54 — pair_aug_v4_gated: 2 features for the pair-bot-DS blind spot
identified in Drill P (v36_dt diagnostic).

Diagnostic origin:
  v36_dt picks pair-mid + SS bot when oracle wants pair-bot + DS bot
  on 162,551 single-pair hands ($100/1000h whole-grid contribution).
  Hand-level inspection (Drill P2) confirmed: 100% of mismatch hands
  have pair with 2 distinct suits AND ≥2 singletons matching pair-suits.
  v36_dt's 83 features include `pair_r4_*` (pair-mid bot info) but NO
  features for "what pair-BOT bot would look like".

Two new gated features (zero outside single-pair hands):

  pair_aug_v4_bot_DS_achievable_g   0/1 — boolean: can pair-in-bot DS bot
                                    be constructed? Computed as:
                                      - pair has 2 distinct suits → need
                                        ≥1 singleton of each pair-suit
                                      - pair single-suited → need ≥2
                                        singletons of same non-pair suit
                                    If achievable, bot = pair + 2 sings
                                    forms suit pattern 2+2 = DS.

  pair_aug_v4_n_sings_in_pair_suits_g  0..5 — count of singletons whose
                                    suit appears in the pair's suit
                                    set. Tells the model "how flexible
                                    is the pair-bot configuration".

Both features are zero for any hand that is not single-pair (cat ≠ pair).

These features should let v36_dt (or its retrain v38_dt) distinguish
"pair-mid SS is right" from "pair-bot DS is right" — the dominant
mismatch in the pair zone diagnostic.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)


def compute_pair_v4_features_for_hand(hand: np.ndarray) -> tuple[int, int]:
    """Return (bot_DS_achievable, n_sings_in_pair_suits) for a single hand.
    Both zero for non-single-pair hands.
    """
    if hand.shape[0] != 7:
        return (0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 1 or n_trips != 0 or n_quads != 0:
        return (0, 0)

    pair_rank = next(r for r, c in rank_count.items() if c == 2)
    pair_pos = [i for i in range(7) if int(ranks[i]) == pair_rank]
    sing_pos = [i for i in range(7) if int(ranks[i]) != pair_rank]
    pair_suits = sorted(int(suits[i]) for i in pair_pos)  # [s_lo, s_hi]
    pair_suit_set = set(pair_suits)

    # Count singletons in pair suits
    n_match = sum(1 for sp in sing_pos if int(suits[sp]) in pair_suit_set)

    # DS-achievability
    if pair_suits[0] != pair_suits[1]:
        # Case A: pair has 2 distinct suits {a, b}
        # Need >= 1 sing of suit a AND >= 1 sing of suit b
        a, b = pair_suits[0], pair_suits[1]
        n_a = sum(1 for sp in sing_pos if int(suits[sp]) == a)
        n_b = sum(1 for sp in sing_pos if int(suits[sp]) == b)
        ds_achievable = 1 if (n_a >= 1 and n_b >= 1) else 0
    else:
        # Case B: pair single-suited (both members same suit)
        a = pair_suits[0]
        # Need >= 2 sings of the same non-a suit
        sing_suit_counts = Counter(int(suits[sp]) for sp in sing_pos)
        # Check any non-a suit has count >= 2
        ds_achievable = 0
        for s, c in sing_suit_counts.items():
            if s != a and c >= 2:
                ds_achievable = 1
                break

    return (ds_achievable, n_match)


def compute_pair_v4_features_batch(hands: np.ndarray,
                                     log_every: int = 500_000
                                     ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_ds = np.zeros(N, dtype=np.int8)
    out_n_match = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2 = compute_pair_v4_features_for_hand(h)
        out_ds[i] = v1
        out_n_match[i] = v2
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_v4 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "pair_aug_v4_bot_DS_achievable_g": out_ds,
        "pair_aug_v4_n_sings_in_pair_suits_g": out_n_match,
    }


if __name__ == "__main__":
    # Sanity tests
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)
    cases = [
        # Drill P2 example: 2♠ 3♥ 4♦ 9♠ K♦ A♥ A♦  pair=AA suits ♥♦, sings 2♠3♥4♦9♠K♦
        # n_sings_in_pair_suits: 3♥, 4♦, K♦ = 3 (♥+♦+♦)
        # DS achievable: pair has 2 distinct suits {♥,♦}; need ≥1 of each in sings
        # ♥ count = 1 (3♥), ♦ count = 2 (4♦, K♦). Both ≥1 → DS achievable
        ("2s 3h 4d 9s Kd Ah Ad", "AA pair, 2 distinct suits, 3 match → expect (1, 3)"),
        # Same-suit pair: 2♣ 3♣ 5♥ 7♠ 9♦ J♣ Q♣ — pair? no this has all distinct ranks
        # Try: 2♣ 2♣ ... but a pair requires 2 cards of same rank, can be same OR diff suits
        # Actually all canonical hands have distinct cards (no duplicate cards).
        # So a "pair" rank with 2 same-suit copies is IMPOSSIBLE — pair always has 2 distinct suits.
        # Just verify the same-suit edge case logic works (it shouldn't trigger in practice).
        # Non-pair hand: should return (0, 0)
        ("2c 3c 4d 5h 6s 7c 8d", "no pair → expect (0, 0)"),
        # KK pair, only 1 sing matches K-suits
        ("Kc Kd 4h 5h 6h 7s Js", "KK pair (♣♦), sings have only Js matching ♠—wait no, K-suits are ♣♦. Sings are 4h5h6h7sJs. None match ♣♦. → expect (0, 0)"),
        # Trips_pair (cat=4): should return (0, 0) because n_trips=1
        ("2c 2d 2h 5s 6c 7d 8h", "trips, no single pair → expect (0, 0)"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2 = compute_pair_v4_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2})  {desc}")
