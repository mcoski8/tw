"""
Session 56 — high_only_aug_v2_gated: 4 rank-valued features for the
high_only zone, mirroring pair_aug_v5 / trips_pair_v2 / two_pair_v2.

Drill HO (Session 56 Phase 1) showed v41_dt's largest high_only blind
spot is suit-routing: v41 picks SS bot 48.4% vs oracle 33.5% and picks
DS bot 34.6% vs oracle 51.9% (−17.3% absolute under-routing of DS).
Top-mismatch class: tA_SS_mu → {tA_SS_ms, tA_DS_ms, tA_DS_mu}. Existing
high_only features (ho_n_broadway_in_2nd_suit_g and family) describe
broadway distribution but never expose "what bot configurations yield
DS while preserving an A/K/Q top."

For high_only, no anchor exists — all 7 ranks are distinct singletons.
The bot is any 4 of 7 cards, leaving 3 for top + mid. We enumerate
C(7,4)=35 candidate bot subsets, filter to those whose suit profile is
DS (2+2), and characterize the achievable top + mid quality.

Four new gated features (zero outside high_only hands):

  ho_v2_bot_DS_n_configs_g       0..N — count of 4-card bot subsets
                                  whose suit profile is DS (2+2). Direct
                                  achievability signal — analog of
                                  pair_aug_v5_bot_DS_n_configs_g.

  ho_v2_bot_DS_max_top_rank_g    0..14 — across all DS configs, the
                                  highest leftover-max rank (= best top
                                  achievable while keeping bot DS). 0 if
                                  no DS config exists.

  ho_v2_bot_DS_min_top_rank_g    0..14 — symmetrically, lowest top-rank
                                  achievable across DS configs. Captures
                                  "must we give up our highest card to
                                  get DS?". 0 if no DS config.

  ho_v2_bot_DS_max_mid_sum_g     0..28 — best mid rank-sum across DS
                                  configs (mid = 2 of the 3 leftover
                                  cards, top = lowest of the 3). Proxy
                                  for "how strong is the mid Hold'em
                                  part if we go DS bot?". 0 if no DS.

All zeros for any non-high_only hand (n_pairs > 0 or n_trips > 0 or
n_quads > 0).
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


def _is_ds(suits) -> bool:
    """True iff the 4-card suit multiset is exactly 2+2."""
    c = Counter(suits)
    sv = sorted(c.values(), reverse=True)
    return sv == [2, 2]


def compute_high_only_v2_features_for_hand(hand: np.ndarray
                                             ) -> tuple[int, int, int, int]:
    """Return (n_configs, max_top_rank, min_top_rank, max_mid_sum)."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 0 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    n_configs = 0
    max_top = 0
    min_top = 99
    max_mid_sum = 0

    for bot_idx in combinations(range(7), 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        if not _is_ds(bot_suits):
            continue
        n_configs += 1
        leftover_idx = [i for i in range(7) if i not in bot_idx]
        leftover_ranks = sorted([int_ranks[i] for i in leftover_idx], reverse=True)
        # max_top: leftover's highest rank (best top achievable for this DS bot)
        cfg_max_top = leftover_ranks[0]
        # min_top: leftover's lowest rank (top= lowest of 3, mid = top 2)
        cfg_min_top = leftover_ranks[2]
        # max_mid_sum: top= lowest, mid = sum of top 2
        cfg_max_mid_sum = leftover_ranks[0] + leftover_ranks[1]
        if cfg_max_top > max_top:
            max_top = cfg_max_top
        if cfg_min_top < min_top:
            min_top = cfg_min_top
        if cfg_max_mid_sum > max_mid_sum:
            max_mid_sum = cfg_max_mid_sum

    if n_configs == 0:
        return (0, 0, 0, 0)
    return (n_configs, max_top, min_top, max_mid_sum)


def compute_high_only_v2_features_batch(hands: np.ndarray,
                                         log_every: int = 500_000
                                         ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_n = np.zeros(N, dtype=np.int8)
    out_max_top = np.zeros(N, dtype=np.int8)
    out_min_top = np.zeros(N, dtype=np.int8)
    out_max_mid_sum = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_high_only_v2_features_for_hand(h)
        out_n[i] = v1
        out_max_top[i] = v2
        out_min_top[i] = v3
        out_max_mid_sum[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  ho_v2 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_v2_bot_DS_n_configs_g": out_n,
        "ho_v2_bot_DS_max_top_rank_g": out_max_top,
        "ho_v2_bot_DS_min_top_rank_g": out_min_top,
        "ho_v2_bot_DS_max_mid_sum_g": out_max_mid_sum,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Test 1: AKQJT 5 2 with two clean 2+2 splits — Ac Kd Qc Jd Th 5h 2s
    # Suits: c,d,c,d,h,h,s = {c:2, d:2, h:2, s:1}
    # 4-card bot subsets that are 2+2:
    #   - {Ac,Qc,Kd,Jd}: leftover Th 5h 2s, max_top=10, min_top=2, mid_sum=10+5=15
    #   - {Ac,Qc,Th,5h}: leftover Kd Jd 2s, max_top=13, min_top=2, mid_sum=13+11=24
    #   - {Ac,Qc,Kd,Jd}: dup of #1
    #   - need 2 of {c}, 2 of {d}, 2 of {h}: enumerate properly...
    # cc-pairs: (Ac,Qc) only
    # dd-pairs: (Kd,Jd) only
    # hh-pairs: (Th,5h) only
    # s-pairs: none (only 2s alone)
    # 2+2 bot needs picking 2 pairs from {c-pair, d-pair, h-pair, ss-pair}.
    # Available pairs: cc, dd, hh.
    # C(3,2)=3 DS configs:
    #   bot={Ac,Qc,Kd,Jd}: leftover Th 5h 2s, max_top=10,min_top=2,mid_sum=10+5=15
    #   bot={Ac,Qc,Th,5h}: leftover Kd Jd 2s, max_top=13,min_top=2,mid_sum=13+11=24
    #   bot={Kd,Jd,Th,5h}: leftover Ac Qc 2s, max_top=14,min_top=2,mid_sum=14+12=26
    # Aggregate: n=3, max_top=14, min_top=2, max_mid_sum=26
    cases = [
        ("Ac Kd Qc Jd Th 5h 2s", "AKQJT5/2 split: expect (3, 14, 2, 26)"),
        # No DS achievable: rainbow Ac Kd Qh Js Th 5d 2c
        # Suits: c,d,h,s,h,d,c → {c:2, d:2, h:2, s:1}
        # Same as above structurally. Skip and test something else.
        # Test 2: 4-flush only: Ac Kc Qc Jc Tc 5h 2s — only c=5, h=1, s=1
        # Pairs of same suit: cc combinations C(5,2)=10. Other: hh? no (only 1 h). s? no.
        # So 2+2 needs cc-pair + cc-pair? Can't, that's 4 c's = 4-flush not 2+2.
        # So no DS possible.
        ("Ac Kc Qc Jc Tc 5h 2s", "5-flush + 1+1: expect (0,0,0,0) (no 2+2 possible)"),
        # Pair → all zeros
        ("Ac Ad Kh Qs Js Th 9d", "pair AA: expect (0,0,0,0)"),
        # Trips → all zeros
        ("Ac Ad As Kh Ks 7d 2c", "trips_pair: expect (0,0,0,0)"),
        # All-rainbow with single 2+2 possible: Ac Kd Qh Js 9c 5d 2h
        # Suits: c,d,h,s,c,d,h = {c:2,d:2,h:2,s:1}
        # cc-pairs: (Ac,9c). dd-pairs: (Kd,5d). hh-pairs: (Qh,2h). ss: none.
        # DS bots: C(3,2)=3 options:
        #   bot={Ac,9c,Kd,5d}: leftover Qh,Js,2h → max_top=12,min_top=2,mid_sum=12+11=23
        #   bot={Ac,9c,Qh,2h}: leftover Kd,Js,5d → max_top=13,min_top=5,mid_sum=13+11=24
        #   bot={Kd,5d,Qh,2h}: leftover Ac,Js,9c → max_top=14,min_top=9,mid_sum=14+11=25
        # n=3, max_top=14, min_top=2, max_mid_sum=25
        ("Ac Kd Qh Js 9c 5d 2h", "AKQJ9/52 ccddhh: expect (3, 14, 2, 25)"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_high_only_v2_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
