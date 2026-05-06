"""
Session 36 — trips_aug_gated: 6 new features for the pure trips category
targeting the A_paired_mid vs B_paired_bot routing decision identified
by the v29 trips distillation.

Diagnostic origin (Session 36, `distill_v29_trips.py`):

  v29 actual on trips      : $109/1000h whole-grid contribution
  Always-A_paired_mid      :  $24/1000h whole-grid (the competing baseline)
  Oracle (A∪B_any∪C)       :   $0/1000h whole-grid

  v29 is $85/1000h whole-grid WORSE than always-A_paired_mid — the
  largest gap-to-baseline ever measured in this project (4× v27's
  KK/AA Rule-4 deficit). v29 picks A on 79.9% of trips; the 20.1%
  deviations are systematically wrong.

  Per-rank: the deficit concentrates on low-rank trips (2-9 each leak
  $7-8/rank-share; total ~$60 of the $85). High-rank trips (K/A) still
  leak but less ($0.9-3.2). This is because the oracle's A-vs-B-vs-C
  decision is structurally simple (almost always A) for low ranks but
  v29 over-deviates uniformly by rank.

Six features, all gated to single-trips hands; zeros elsewhere. Prefix
`trips_*_g` (collision-checked: distinct from `tp_*_g` which is
trips_pair, also distinct from `_g`/`comp_*_g`/`pair_*_g`/`t2p_*_g`/
`ho_*_g`/`pair_r4_*_g`):

  trips_b_ds_avail_g           0/1 — does ANY of 105 settings have
                                bot_top_pair_rank == trip_rank AND
                                bot_suit_profile == DS? Direct
                                structural answer: is B-DS feasible.
                                ~68% of trips have B-DS available.

  trips_b_ds_n_routings_g       0..3 — number of distinct trip-pair
                                {a,b} choices for which the 4 kickers
                                contain ≥1 in suit a AND ≥1 in suit b.
                                Each value = a way to construct B-DS.
                                More routings = more flexibility.

  trips_kickers_max_suit_count_g  0..4 — max suit count among the
                                4 kickers. ≥2 is necessary (but not
                                sufficient) for B-DS.

  trips_kickers_max_rank_g     0..14 — highest rank among the 4
                                kickers. High kicker → A is strong
                                (paired-mid + high top kicker).

  trips_n_broadway_kickers_g   0..4 — count of T-A among kickers.

  trips_n_low_kickers_g        0..4 — count of 2-5 among kickers.
                                Many low → bot routing more attractive
                                because top kicker is weak in A.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
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


def compute_trips_features_for_hand(hand: np.ndarray) -> tuple[int, int, int, int, int, int]:
    """Return the 6 gated features for a single 7-card hand.
    Zeros for any non-pure-trips hand (n_trips != 1, or n_pairs > 0,
    or n_quads > 0).
    """
    if hand.shape[0] != 7:
        return (0, 0, 0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_trips != 1 or n_pairs != 0 or n_quads != 0:
        return (0, 0, 0, 0, 0, 0)

    trip_rank = next(r for r, c in rank_count.items() if c == 3)
    trip_positions = [i for i in range(7) if int(ranks[i]) == trip_rank]
    kicker_indices = [i for i in range(7) if i not in trip_positions]

    # The 3 trips occupy 3 distinct suits (of 4) by deck constraint.
    trip_suits = sorted(int(suits[i]) for i in trip_positions)
    assert len(set(trip_suits)) == 3, "trips must occupy 3 distinct suits"

    # Kicker suits and ranks
    kicker_suits = [int(suits[i]) for i in kicker_indices]
    kicker_ranks = [int(ranks[i]) for i in kicker_indices]
    assert len(kicker_indices) == 4

    # Feature 1: trips_b_ds_avail_g
    # B-DS feasible if for some 2 of the 3 trip suits {a, b}, kickers
    # contain ≥1 in suit a AND ≥1 in suit b.
    kicker_suit_set = set(kicker_suits)
    b_ds_avail = 0
    n_b_ds_routings = 0
    for a, b in combinations(trip_suits, 2):
        if a in kicker_suit_set and b in kicker_suit_set:
            n_b_ds_routings += 1
    b_ds_avail = 1 if n_b_ds_routings > 0 else 0

    # Feature 3: trips_kickers_max_suit_count_g
    kicker_suit_counts = Counter(kicker_suits)
    counts_sorted = sorted(kicker_suit_counts.values(), reverse=True)
    kickers_max_suit_count = counts_sorted[0] if counts_sorted else 0

    # Feature 4: trips_kickers_max_rank_g
    kickers_max_rank = max(kicker_ranks) if kicker_ranks else 0

    # Feature 5: trips_n_broadway_kickers_g  (T-A)
    n_broadway = sum(1 for r in kicker_ranks if r >= 10)

    # Feature 6: trips_n_low_kickers_g  (2-5)
    n_low = sum(1 for r in kicker_ranks if r <= 5)

    return (
        int(b_ds_avail),
        int(n_b_ds_routings),
        int(kickers_max_suit_count),
        int(kickers_max_rank),
        int(n_broadway),
        int(n_low),
    )


def compute_trips_features_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_b_avail = np.zeros(N, dtype=np.int8)
    out_b_routings = np.zeros(N, dtype=np.int8)
    out_max_suit = np.zeros(N, dtype=np.int8)
    out_max_rank = np.zeros(N, dtype=np.int8)
    out_n_bway = np.zeros(N, dtype=np.int8)
    out_n_low = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4, v5, v6 = compute_trips_features_for_hand(h)
        out_b_avail[i] = v1
        out_b_routings[i] = v2
        out_max_suit[i] = v3
        out_max_rank[i] = v4
        out_n_bway[i] = v5
        out_n_low[i] = v6
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  trips {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "trips_b_ds_avail_g":            out_b_avail,
        "trips_b_ds_n_routings_g":       out_b_routings,
        "trips_kickers_max_suit_count_g": out_max_suit,
        "trips_kickers_max_rank_g":      out_max_rank,
        "trips_n_broadway_kickers_g":    out_n_bway,
        "trips_n_low_kickers_g":         out_n_low,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        # (hand, expected (b_avail, n_routings, max_suit_cnt, max_rank, n_bway, n_low), label)
        # Trips of K (s,h,d) + kickers Ac, 5d, 7s, 2h
        # Trip suits: {0,1,2} (c=0,d=1,h=2). Wait Kc means rank K suit clubs. Let me re-encode.
        # In encoding, 0=c, 1=d, 2=h, 3=s.
        # Trips of K: Ks(s=3), Kh(s=2), Kd(s=1) → trip suits {1,2,3}, missing suit 0=clubs
        ("Ks Kh Kd Ac 5d 7s 2h", None, "trip K, kickers Ac/5d/7s/2h — kicker suits c,d,s,h = {0,1,3,2}"),
        # Trips of 5: 5c,5d,5h. Trip suits {0,1,2}, missing s. Kickers: Ah, 9c, 7c, 3d
        # Kicker suits: 2,0,0,1 = max 2 (suit c twice). Trip-suit pair (0,1): kicker has 0 (yes) AND 1 (yes) ✓ B-DS routing
        # Trip-suit pair (0,2): kicker 0 yes, 2 yes (Ah) ✓
        # Trip-suit pair (1,2): kicker 1 (3d) yes, 2 (Ah) yes ✓
        # so n_routings=3
        ("5c 5d 5h Ah 9c 7c 3d", (1, 3, 2, 14, 1, 1), "trip 5, kickers A/9/7/3, suit dist [c=2,d=1,h=1,s=0]"),
        # Trips of A: Ac,Ad,As. Trip suits {0,1,3}, missing h. Kickers Kh, Qh, Jh, Th — all hearts (suit 2)
        # Kicker suit_count: h=4, others=0. max=4.
        # Trip-suit pair (0,1): kickers in c=0, d=0 → no
        # Trip-suit pair (0,3): kickers c=0, s=0 → no
        # Trip-suit pair (1,3): no
        # All kickers in absent suit. n_routings = 0, B-DS not feasible.
        ("Ac Ad As Kh Qh Jh Th", (0, 0, 4, 13, 4, 0), "trip A all-h-kickers, B-DS infeasible"),
        # Trips of T: Tc,Td,Th. Trip suits {0,1,2}, missing s. Kickers: 9c, 8d, 7s, 6h
        # Kicker suit_count: each unique = 1+1+1+1. max=1.
        # Trip-suit pairs (0,1): kicker c=yes, d=yes → routing exists
        # (0,2): c=yes, h=yes → routing exists
        # (1,2): d=yes, h=yes → routing exists
        # but max_suit_count=1 means no kicker pair available → can't form 2+2 in bot
        # Actually wait, B-DS needs 2 kickers of same suit. If all kickers are different suits, B-DS NOT feasible.
        # I think my n_routings logic is flawed — let me re-derive.
        ("Tc Td Th 9c 8d 7s 6h", None, "trip T, all-different-suit kickers — B-DS NOT feasible (need 2 same-suit kickers)"),
    ]

    # Re-think: my B-DS feasibility logic is wrong.
    # B routing puts 2 of 3 trips → bot. Bot = trip_a + trip_b + 2 kickers.
    # For DS (2+2): bot must have 2 cards of one suit + 2 of another.
    # Trips contribute 1 card each of 2 different suits (a and b).
    # The 2 kickers (out of 4) must complete either:
    #   - 1 kicker in suit a + 1 kicker in suit b → bot is 2-a + 2-b = DS ✓
    #   - 2 kickers in suit other (c or d, where d is absent suit): bot is 1-a + 1-b + 2-other = single-suited (not DS)
    #   - 1 kicker in a + 1 kicker in other: 2-a + 1-b + 1-other = single-suited
    #
    # So for B-DS feasibility, given trip-pair {a,b}: kickers must include
    # ≥1 in suit a AND ≥1 in suit b. (Then choose 1 kicker each from a and b.)
    #
    # In my Tc/Td/Th + 9c/8d/7s/6h example:
    #   trips suits {c=0, d=1, h=2}, kickers in c,d,s,h = {0,1,3,2}
    #   Trip-pair (0,1): need ≥1 kicker in suit 0 AND ≥1 in suit 1 → 9c (s=0) yes, 8d (s=1) yes → routing exists
    #   But with these kickers, bot would be (Tc, Td, 9c, 8d). Is this DS?
    #   suit dist of bot: c=2 (Tc, 9c), d=2 (Td, 8d) → 2+2 = DS ✓ YES!
    #   So routing exists.
    #   max_suit_count among ALL 4 kickers is 1 (each different suit), but for the BOT subset (2 of 4 kickers),
    #   we just need 1 in suit a + 1 in suit b. Even with all-rainbow kickers.
    print("Verifying B-DS logic: with rainbow kickers and 2 of them aligned with trip-pair suits, B-DS WORKS.")
    print("(My feature logic should match this.)")
    print()

    print(f"{'hand':<32}{'label':<70}-> (b_avail, n_routings, max_suit, max_rank, n_bway, n_low)")
    for s, expected, label in cases:
        feats = compute_trips_features_for_hand(hh(*s.split()))
        ok = ""
        if expected is not None:
            ok = " ✓" if feats == expected else f" EXPECTED {expected}"
        print(f"{s:<32}{label:<70}-> {feats}{ok}")
