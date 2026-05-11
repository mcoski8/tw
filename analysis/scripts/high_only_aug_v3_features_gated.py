"""
Session 57 — high_only_aug_v3_gated: 4 rank-valued features for the JOINT
(DS bot + suited mid) routing in the high_only zone, conditional on top =
max-rank-of-hand.

Phase 1 (drill HO3) showed that after S56's ho_v2 features collapsed parts
of the high_only zone, the SAME SS->DS pattern is STILL the dominant
residual. v42 over-routes SS bot at 46.07% vs oracle 32.04% (-14.0%
absolute under-routing of DS).

Phase 1b (drill HO4) characterized the dominant single class
(v42=tA_SS_mu, oracle=tA_DS_ms, 28,027 hands @ $7,534 mean regret =
$35.14/1000h whole-grid) and confirmed:
  - 100% of mismatch hands have a (DS bot + suited mid) joint config
    achievable WITH the Ace on top.
  - 18% have 3 joint configs, 82% have 9 joint configs.
  - DS_AND_ms_max_mid_high distribution spans 7..K (when top=max-rank).
  - v42's ho_v2 features ONLY expose DS-bot achievability, not the joint.

Hypothesis: a feature family describing (DS bot + ms mid) JOINT
achievability + quality, conditional on top = max-rank-of-hand, will let
the DT split tA_SS_mu (default play) from tA_DS_ms (joint-routing pick).

For each high_only hand, fix top = max-rank-of-hand. Enumerate the
C(6,4)=15 4-card subsets of the remaining 6 cards as candidate bots.
For each: check (a) bot is 2+2 (DS), (b) the 2 leftover cards (mid)
share a suit. If both, count as a joint config; record mid quality.

Four new gated features (zero outside high_only hands):

  ho_v3_topMax_DS_ms_n_configs_g     0..15 — count of (top=max-rank,
                                       DS bot, ms mid) joint configs.
                                       Direct joint-achievability signal.

  ho_v3_topMax_DS_ms_max_mid_high_g  0..13 — across all joint configs,
                                       best higher-card-of-suited-mid
                                       rank (max-rank is on top, so this
                                       maxes at 13). 0 if no joint config.

  ho_v3_topMax_DS_ms_min_mid_high_g  0..13 — symmetrically, lowest
                                       higher-card-of-suited-mid rank
                                       across joint configs. 0 if none.

  ho_v3_topMax_DS_ms_max_mid_sum_g   0..25 — best sum of the suited mid
                                       pair (max + 2nd) across joint
                                       configs. Proxy for "how strong
                                       is the suited mid Hold'em part?".
                                       0 if no joint config.

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


def compute_high_only_v3_features_for_hand(hand: np.ndarray
                                             ) -> tuple[int, int, int, int]:
    """Return (n_configs, max_mid_high, min_mid_high, max_mid_sum)."""
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

    # Find the max-rank position (high_only has 7 distinct ranks, so unique).
    max_rank = max(int_ranks)
    top_pos = int_ranks.index(max_rank)
    rest_pos = [i for i in range(7) if i != top_pos]  # 6 cards

    n_configs = 0
    max_mid_high = 0
    min_mid_high = 99
    max_mid_sum = 0

    # Enumerate C(6,4)=15 candidate bots from the 6 non-top cards
    for bot_idx in combinations(rest_pos, 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        if not _is_ds(bot_suits):
            continue
        mid_pos = [i for i in rest_pos if i not in bot_idx]  # 2 cards
        # Check mid is suited
        if int_suits[mid_pos[0]] != int_suits[mid_pos[1]]:
            continue
        # Joint config achieved
        n_configs += 1
        mid_ranks_pair = sorted([int_ranks[mid_pos[0]], int_ranks[mid_pos[1]]],
                                  reverse=True)
        mid_high = mid_ranks_pair[0]
        mid_sum = mid_ranks_pair[0] + mid_ranks_pair[1]
        if mid_high > max_mid_high:
            max_mid_high = mid_high
        if mid_high < min_mid_high:
            min_mid_high = mid_high
        if mid_sum > max_mid_sum:
            max_mid_sum = mid_sum

    if n_configs == 0:
        return (0, 0, 0, 0)
    return (n_configs, max_mid_high, min_mid_high, max_mid_sum)


def compute_high_only_v3_features_batch(hands: np.ndarray,
                                          log_every: int = 500_000
                                          ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_n = np.zeros(N, dtype=np.int8)
    out_max_high = np.zeros(N, dtype=np.int8)
    out_min_high = np.zeros(N, dtype=np.int8)
    out_max_sum = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_high_only_v3_features_for_hand(h)
        out_n[i] = v1
        out_max_high[i] = v2
        out_min_high[i] = v3
        out_max_sum[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  ho_v3 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_v3_topMax_DS_ms_n_configs_g": out_n,
        "ho_v3_topMax_DS_ms_max_mid_high_g": out_max_high,
        "ho_v3_topMax_DS_ms_min_mid_high_g": out_min_high,
        "ho_v3_topMax_DS_ms_max_mid_sum_g": out_max_sum,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Hand 1 of Drill HO4: 2s 5h 6d Jh Qd Ks As
    # top = As (max rank). 6 rest = 2s 5h 6d Jh Qd Ks. Suits: s,h,d,h,d,s.
    # C(6,4)=15 candidate bots; need 2+2 DS bot AND mid is suited.
    # Suit composition of rest: s=2 (2s,Ks), h=2 (5h,Jh), d=2 (6d,Qd).
    # 2+2 DS bots from rest: pick 2 suits, take both cards each. 3 options:
    #   bot ss+hh = {2s,Ks,5h,Jh}, mid={6d,Qd} both d → DS+ms ✓
    #     mid_high=Q=12, sum=12+6=18
    #   bot ss+dd = {2s,Ks,6d,Qd}, mid={5h,Jh} both h → DS+ms ✓
    #     mid_high=J=11, sum=11+5=16
    #   bot hh+dd = {5h,Jh,6d,Qd}, mid={2s,Ks} both s → DS+ms ✓ (oracle pick!)
    #     mid_high=K=13, sum=13+2=15
    # n_configs=3, max_mid_high=K=13, min_mid_high=11, max_mid_sum=18
    cases = [
        ("2s 5h 6d Jh Qd Ks As", "Drill HO4 hand 1: expect (3, 13, 11, 18)"),
        # Hand 4 of Drill HO4: 2s 3h 5d 8d Ts Jh As
        # top=As. rest: 2s 3h 5d 8d Ts Jh. Suits: s,h,d,d,s,h.
        # Suit comp: s=2, h=2, d=2. Same as above.
        # 2+2 DS bots:
        #   bot ss+hh={2s,Ts,3h,Jh}, mid={5d,8d} d both → DS+ms ✓ mid_high=8, sum=13
        #   bot ss+dd={2s,Ts,5d,8d}, mid={3h,Jh} h both → DS+ms ✓ mid_high=J=11, sum=14
        #   bot hh+dd={3h,Jh,5d,8d}, mid={2s,Ts} s both → DS+ms ✓ mid_high=T=10, sum=12
        # n=3, max_mid_high=11, min_mid_high=8, max_mid_sum=14
        ("2s 3h 5d 8d Ts Jh As", "Drill HO4 hand 4: expect (3, 11, 8, 14)"),
        # Pair → all zeros
        ("Ac Ad Kh Qs Js Th 9d", "pair AA: expect (0,0,0,0)"),
        # No DS achievable (all-monosuit + 2 broadway):
        # 5 cards of c suit + 2 odd: Ac Kc Qc Jc Tc 5h 2s
        # top=Ac, rest = Kc Qc Jc Tc 5h 2s
        # bot 2+2 DS: need 2 suits with 2 cards each. Suit comp: c=4, h=1, s=1.
        # Can we make 2+2? Pick 2c + 2 of (h+s)? We only have 1h and 1s, so no.
        # Or 4c? That's 4-flush, not 2+2. So no DS bot at all.
        # Expected: (0,0,0,0)
        ("Ac Kc Qc Jc Tc 5h 2s", "5-flush + 1+1: expect (0,0,0,0)"),
        # Hand from ho_v2 sanity test 1: Ac Kd Qc Jd Th 5h 2s
        # top=Ac. rest: Kd Qc Jd Th 5h 2s. Suits: d,c,d,h,h,s. So d=2, h=2, c=1, s=1.
        # 2+2 DS bots: pick {dd, hh}: bot={Kd,Jd,Th,5h}, mid={Qc, 2s} different suits → not ms ✗
        # No other 2+2 (need 2 of one suit + 2 of another, only dd and hh have 2).
        # n_configs = 0
        ("Ac Kd Qc Jd Th 5h 2s", "no joint achievable: expect (0,0,0,0)"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_high_only_v3_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
