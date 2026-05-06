"""
Session 36 — trips_aug_v2_gated: 4 round-2 features for the pure trips
category, designed to address signals v30's first-pass features missed.

v30 captured ~16% of trips category regret on prefix ($1,763 → $1,474).
The remaining 80%+ leak comes from imprecise A-vs-B-vs-C routing within
trips. v30's features encode B-DS feasibility but NOT:

  - When C_top_trip beats A_paired_mid (high-rank trips with mediocre
    kickers — e.g. trip K with no kicker > Q means top=K trumps top=Q)
  - The QUALITY of B-DS's would-be bot pair (max rank of in-trip-suit
    kickers, which become bot anchors)
  - The DEPTH of trip-suit kicker representation (4 kickers of which N
    share suits with the 3 trips — drives both B-DS feasibility and
    quality)

Four new features, all zero outside pure trips. Prefix `trips_v2_*_g`
(distinct from v30's `trips_*_g`):

  trips_v2_c_top_advantage_g          0..12 — max(0, trip_rank -
                                       max_kicker_rank). 0 means at
                                       least one kicker ≥ trip rank
                                       (so A's top is competitive).
                                       Positive means trip rank tops
                                       all kickers (C-top advantage).

  trips_v2_b_ds_kicker_max_rank_g     0..14 — max rank of kickers
                                       sharing suit with any trip card.
                                       In B routing, bot is 2-trips +
                                       2-kickers; the 2 kickers join
                                       bot. Higher rank = stronger
                                       Omaha bot post-board.

  trips_v2_b_ds_kicker_2nd_rank_g     0..14 — 2nd-max rank of kickers
                                       in trip-suits. Together with
                                       max_rank, gives the tree the
                                       full top-2 of B-DS bot kickers.

  trips_v2_n_kickers_in_trip_suits_g  0..4 — count of the 4 kickers
                                       whose suit matches any of the 3
                                       trip-suits (vs the 1 absent
                                       suit). Drives B-DS routing count.
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


def compute_trips_v2_features_for_hand(hand: np.ndarray) -> tuple[int, int, int, int]:
    """Return the 4 round-2 trips-gated features. Zeros outside pure trips."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_trips != 1 or n_pairs != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    trip_rank = next(r for r, c in rank_count.items() if c == 3)
    trip_positions = [i for i in range(7) if int(ranks[i]) == trip_rank]
    kicker_indices = [i for i in range(7) if i not in trip_positions]
    trip_suits = set(int(suits[i]) for i in trip_positions)
    assert len(trip_suits) == 3

    kicker_ranks = [int(ranks[i]) for i in kicker_indices]
    kicker_suits = [int(suits[i]) for i in kicker_indices]

    # Feature 1: C_top advantage
    max_kicker_rank = max(kicker_ranks) if kicker_ranks else 0
    c_top_adv = max(0, int(trip_rank) - max_kicker_rank)

    # Features 2 & 3: B-DS kicker max + 2nd-max rank (kickers in trip-suits)
    in_trip_suit_ranks = sorted(
        (int(ranks[kicker_indices[k]]) for k in range(len(kicker_indices))
         if kicker_suits[k] in trip_suits),
        reverse=True,
    )
    b_ds_kicker_max = in_trip_suit_ranks[0] if len(in_trip_suit_ranks) >= 1 else 0
    b_ds_kicker_2nd = in_trip_suit_ranks[1] if len(in_trip_suit_ranks) >= 2 else 0

    # Feature 4: count of kickers in trip-suits
    n_kickers_in_trip_suits = sum(1 for s in kicker_suits if s in trip_suits)

    return (
        int(c_top_adv),
        int(b_ds_kicker_max),
        int(b_ds_kicker_2nd),
        int(n_kickers_in_trip_suits),
    )


def compute_trips_v2_features_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_c_adv = np.zeros(N, dtype=np.int8)
    out_b_ds_max = np.zeros(N, dtype=np.int8)
    out_b_ds_2nd = np.zeros(N, dtype=np.int8)
    out_n_kit = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_trips_v2_features_for_hand(h)
        out_c_adv[i] = v1
        out_b_ds_max[i] = v2
        out_b_ds_2nd[i] = v3
        out_n_kit[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  trips_v2 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "trips_v2_c_top_advantage_g":          out_c_adv,
        "trips_v2_b_ds_kicker_max_rank_g":     out_b_ds_max,
        "trips_v2_b_ds_kicker_2nd_rank_g":     out_b_ds_2nd,
        "trips_v2_n_kickers_in_trip_suits_g":  out_n_kit,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        # Trip K, kickers Ac/5d/7s/2h. trip_rank=13, max_kicker=14 (Ac), c_top_adv=0
        # Trip suits: s,h,d = {3,2,1}, missing c. Kickers in trip-suits: 5d, 7s, 2h (3 kickers)
        # In-trip-suit ranks sorted desc: 7,5,2. max=7, 2nd=5. n_kit=3.
        ("Ks Kh Kd Ac 5d 7s 2h", (0, 7, 5, 3), "trip K, kickers AC/5d/7s/2h"),
        # Trip 5, kickers Ah/9c/7c/3d. trip=5, max_kicker=14 (Ah), c_adv=0
        # Trip suits c,d,h = {0,1,2}, missing s. Kickers: Ah(2),9c(0),7c(0),3d(1) — all in trip-suits.
        # In-trip-suit ranks: 14,9,7,3. max=14, 2nd=9. n_kit=4.
        ("5c 5d 5h Ah 9c 7c 3d", (0, 14, 9, 4), "trip 5, kickers high A"),
        # Trip A, kickers all hearts (suit 2). trip suits c,d,s = {0,1,3}, missing h.
        # Kickers Kh,Qh,Jh,Th — all suit 2 (absent from trips). n_kit=0.
        # In-trip-suit ranks: empty. max=0, 2nd=0.
        ("Ac Ad As Kh Qh Jh Th", (0, 0, 0, 0), "trip A, all kickers in absent suit"),
        # Trip K, kickers Q/J/T/9. trip=13, max_kicker=12 (Q), c_adv=1.
        # Trip suits set up: Ks Kh Kd. Kickers Qc Jh Td 9s. Suits c,h,d,s.
        # Trip suits: s,h,d. Kickers in trip-suits: Jh(2),Td(1),9s(3) — 3 kickers. Qc not.
        # In-trip-suit ranks: 11,10,9. max=11, 2nd=10. n_kit=3.
        ("Ks Kh Kd Qc Jh Td 9s", (1, 11, 10, 3), "trip K, no kicker beats K — C-top advantage"),
        # Non-trips hand (KK two_pair) — should return zeros
        ("Ks Kd As Ac Jh Th 9d", (0, 0, 0, 0), "two-pair, zeros"),
    ]
    print(f"{'hand':<32}{'label':<60}-> (c_adv, b_ds_max, b_ds_2nd, n_kit)")
    for s, expected, label in cases:
        feats = compute_trips_v2_features_for_hand(hh(*s.split()))
        ok = " ✓" if feats == expected else f" EXPECTED {expected}"
        print(f"{s:<32}{label:<60}-> {feats}{ok}")
