"""
Session 31 — trips_pair-gated aug features.

Per-category v20 bleed: trips_pair = $1,608/1000h on full grid (8.7% of
the population => ~$140/1000h share of the overall residual). Bigger
lever than composite ($5/1000h share). The Session 20 mining doc
(`mine_trips_pair_leaves.py`) calls out the structural axes the existing
28-feature baseline can't expose:

  Decision A — which group on bot:
    trips-on-bot   (3 + 1 singleton):   bot suit profile = (X,X,X,?)
    pair-on-bot    (2 + 2 singletons):  bot suit profile = (P1,P2,?,?)

  Decision B — which singleton goes on top.

For DS-2+2 bot when pair-on-bot, the two singletons must each match a
different pair-suit (P1 and P2). High-rank trip + low-rank pair vs the
inverse changes the routing too.

Six features, all gated to `trips_pair` (n_trips==1 AND n_pairs==1):

  tp_trip_rank_g            rank of the trip (2-14)
  tp_pair_rank_g            rank of the pair (2-14)
  tp_high_singleton_rank_g  rank of the higher singleton
  tp_low_singleton_rank_g   rank of the lower singleton
  tp_singletons_suited_g    1 if both singletons share a suit
  tp_pair_routing_is_ds_g   1 if singletons fill the pair's two suits
                            => pair-on-bot routing yields DS

All zeros for any non-trips_pair hand. Mirrors the gating pattern of
suited_aug_features_gated (Session 30).
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


def compute_trips_pair_aug_gated_for_hand(hand: np.ndarray) -> tuple[int, int, int, int, int, int]:
    """Return the 6 features for a trips_pair hand; zeros otherwise.

    trips_pair = exactly one rank with count 3 AND one rank with count 2
    AND remaining 2 cards are distinct singletons.
    """
    if hand.shape[0] != 7:
        return (0, 0, 0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand & 0b11
    counts = Counter(int(r) for r in ranks)
    trip_ranks = [r for r, c in counts.items() if c == 3]
    pair_ranks = [r for r, c in counts.items() if c == 2]
    quads = [r for r, c in counts.items() if c == 4]
    if quads or len(trip_ranks) != 1 or len(pair_ranks) != 1:
        return (0, 0, 0, 0, 0, 0)
    trip_rank = trip_ranks[0]
    pair_rank = pair_ranks[0]

    singletons = []
    pair_suits = []
    for i in range(7):
        r = int(ranks[i])
        s = int(suits[i])
        if r == pair_rank:
            pair_suits.append(s)
        elif r != trip_rank:
            singletons.append((r, s))
    if len(singletons) != 2 or len(pair_suits) != 2:
        return (0, 0, 0, 0, 0, 0)

    s1_rank, s1_suit = singletons[0]
    s2_rank, s2_suit = singletons[1]
    high_singleton = max(s1_rank, s2_rank)
    low_singleton = min(s1_rank, s2_rank)
    singletons_suited = 1 if s1_suit == s2_suit else 0
    pair_set = set(pair_suits)
    pair_routing_is_ds = 1 if (s1_suit in pair_set and s2_suit in pair_set and s1_suit != s2_suit) else 0

    return (
        int(trip_rank),
        int(pair_rank),
        int(high_singleton),
        int(low_singleton),
        int(singletons_suited),
        int(pair_routing_is_ds),
    )


def compute_trips_pair_aug_gated_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)
    b = np.zeros(N, dtype=np.int8)
    c = np.zeros(N, dtype=np.int8)
    d = np.zeros(N, dtype=np.int8)
    e = np.zeros(N, dtype=np.int8)
    f = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        f1, f2, f3, f4, f5, f6 = compute_trips_pair_aug_gated_for_hand(h)
        a[i] = f1; b[i] = f2; c[i] = f3
        d[i] = f4; e[i] = f5; f[i] = f6
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  trips_pair_aug_gated {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "tp_trip_rank_g": a,
        "tp_pair_rank_g": b,
        "tp_high_singleton_rank_g": c,
        "tp_low_singleton_rank_g": d,
        "tp_singletons_suited_g": e,
        "tp_pair_routing_is_ds_g": f,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        ("Ac Ad As Kh Ks 7d 2c", "AAA + KK + 7d 2c (trips_pair)"),
        ("Ac Ad As Kh Ks 7d 2d", "AAA + KK + 7d 2d (singletons suited)"),
        ("Ac Ad As Kh Ks 7h 2s", "AAA + KK + 7h 2s — singletons fill pair suits => DS"),
        ("Ac Ad Kh Kd 7c 5h 2s", "no trips => zeros"),
    ]
    for s, label in cases:
        feats = compute_trips_pair_aug_gated_for_hand(hh(*s.split()))
        print(f"{s}  {label}\n  -> {feats}")
