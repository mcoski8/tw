"""
Session 55 — two_pair_aug_v2_gated: 4 rank-valued features for the
Layout C (Hbot_Lmid) DS routing alternative in the two_pair zone.

Drill T2P (Session 55 Phase 1) showed v39_dt's largest two_pair mismatch:
v39 picks Hbot_Lmid_SS, oracle picks Hmid_Lbot_SS — 56,206 hands at
$2,655 mean regret = $24.84/1000h whole-grid contribution. Second
largest: Hbot_Lmid_SS → Hbot_Lmid_DS ($12.77/1000h).

Drill T2P2 (Phase 1b hand-level inspection) showed:
  - 72% of mismatch hands have pair-suit overlap ≥ 1
  - Layout C (Hbot_Lmid) has DS routings in 34% of mismatch hands
  - v39 has features for Layout B DS routings (t2p_n_layout_b_routings_ds_g)
    but NO equivalent for Layout C — asymmetric blind spot

Existing two_pair features (6, from S33):
  t2p_layout_a_bot_is_ds_g, t2p_n_layout_b_routings_ds_g,
  t2p_top_singleton_rank_g, t2p_low_singleton_rank_g,
  t2p_singletons_max_suit_count_g, t2p_high_pair_rank_g

Missing: any Layout C feature. The 4 new gated features fill this asymmetry:

  t2p_v2_layout_C_DS_n_configs_g     0..3 — count of (high pair + 2 sings)
                                       4-card-bot configs yielding DS in
                                       Layout C (Hbot_Lmid). Analog of the
                                       existing layout_B feature.

  t2p_v2_layout_C_max_top_rank_g     0..14 — best leftover-singleton rank
                                       (= top card) across all DS or SS
                                       routings in Layout C.

  t2p_v2_layout_B_max_top_rank_g     0..14 — best leftover-singleton rank
                                       across all DS or SS routings in
                                       Layout B (parallel feature to make
                                       the comparison explicit).

  t2p_v2_layout_C_DS_max_top_rank_g  0..14 — best top rank specifically
                                       when Layout C is DS. 0 if Layout C
                                       DS unachievable.

All zeros for any non-two_pair hand (gated on n_pairs==2, no trips/quads).
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
    c = Counter(suits)
    sv = sorted(c.values(), reverse=True)
    return sv[:2] == [2, 2]


def _is_ss_or_ds(suits) -> bool:
    c = Counter(suits)
    sv = sorted(c.values(), reverse=True)
    # SS = 2+1+1 or DS = 2+2
    return sv[0] == 2


def compute_two_pair_v2_features_for_hand(hand: np.ndarray
                                           ) -> tuple[int, int, int, int]:
    """Return (C_DS_n_configs, C_max_top, B_max_top, C_DS_max_top)."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 2 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    pair_ranks = sorted([r for r, c in rank_count.items() if c == 2], reverse=True)
    hi_pair, lo_pair = pair_ranks[0], pair_ranks[1]
    hi_pos = [i for i in range(7) if int(ranks[i]) == hi_pair]
    lo_pos = [i for i in range(7) if int(ranks[i]) == lo_pair]
    sing_pos = [i for i in range(7) if i not in hi_pos and i not in lo_pos]
    if len(sing_pos) != 3:
        return (0, 0, 0, 0)

    hi_suits = [int(suits[p]) for p in hi_pos]
    lo_suits = [int(suits[p]) for p in lo_pos]
    sing_suits = [int(suits[p]) for p in sing_pos]
    sing_ranks = [int(ranks[p]) for p in sing_pos]

    C_DS_n = 0
    C_DS_max_top = 0
    C_max_top = 0
    B_max_top = 0

    # Enumerate C(3,2) = 3 choices for which 2 of 3 singletons go to bot
    for sa_i, sb_i in combinations(range(3), 2):
        leftover_i = [j for j in range(3) if j != sa_i and j != sb_i][0]
        top_rank = sing_ranks[leftover_i]

        # Layout C: bot = hi-pair + sing_a + sing_b
        bot_C_suits = hi_suits + [sing_suits[sa_i], sing_suits[sb_i]]
        if _is_ds(bot_C_suits):
            C_DS_n += 1
            if top_rank > C_DS_max_top:
                C_DS_max_top = top_rank
        if _is_ss_or_ds(bot_C_suits):
            if top_rank > C_max_top:
                C_max_top = top_rank

        # Layout B: bot = lo-pair + sing_a + sing_b
        bot_B_suits = lo_suits + [sing_suits[sa_i], sing_suits[sb_i]]
        if _is_ss_or_ds(bot_B_suits):
            if top_rank > B_max_top:
                B_max_top = top_rank

    return (C_DS_n, C_max_top, B_max_top, C_DS_max_top)


def compute_two_pair_v2_features_batch(hands: np.ndarray,
                                        log_every: int = 500_000
                                        ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_a = np.zeros(N, dtype=np.int8)
    out_b = np.zeros(N, dtype=np.int8)
    out_c = np.zeros(N, dtype=np.int8)
    out_d = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_two_pair_v2_features_for_hand(h)
        out_a[i] = v1
        out_b[i] = v2
        out_c[i] = v3
        out_d[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  t2p_v2 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "t2p_v2_layout_C_DS_n_configs_g": out_a,
        "t2p_v2_layout_C_max_top_rank_g": out_b,
        "t2p_v2_layout_B_max_top_rank_g": out_c,
        "t2p_v2_layout_C_DS_max_top_rank_g": out_d,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                         dtype=np.uint8)
    # Drill T2P2 Hand 1: 2s 2h 4d 6s Ts Tc Qc, hi=T(s,c) lo=2(s,h)
    #   sings: 4d, 6s, Qc with suits d, s, c
    # Layout C (bot = TT + 2 sings):
    #   sings(4d,6s): bot=TT+4d+6s suits=s,c,d,s={s:2,c:1,d:1}=SS, leftover=Qc top=12
    #   sings(4d,Qc): bot=TT+4d+Qc suits=s,c,d,c={c:2,s:1,d:1}=SS, leftover=6s top=6
    #   sings(6s,Qc): bot=TT+6s+Qc suits=s,c,s,c={s:2,c:2}=DS, leftover=4d top=4
    # C_DS_n = 1 (the (6s,Qc) routing), C_DS_max_top = 4
    # C_max_top = max(12,6,4) = 12
    # Layout B (bot = 22 + 2 sings):
    #   sings(4d,6s): bot=22+4d+6s suits=s,h,d,s={s:2,h:1,d:1}=SS top=12
    #   sings(4d,Qc): bot=22+4d+Qc suits=s,h,d,c=rainbow top=6
    #   sings(6s,Qc): bot=22+6s+Qc suits=s,h,s,c={s:2,h:1,c:1}=SS top=4
    # B_max_top = max of SS/DS only: max(12, 4) = 12 (4d,Qc rainbow excluded)
    # Expect: (1, 12, 12, 4)
    cases = [
        ("2s 2h 4d 6s Ts Tc Qc", "TT+22+sings: expect (1, 12, 12, 4)"),
        # No two_pair → zeros
        ("As Kh Qd Jc Ts 9h 4s", "no pair: expect (0,0,0,0)"),
        # Trips_pair → zeros
        ("Ac Ad As Kh Ks 7d 2c", "trips_pair: expect (0,0,0,0)"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_two_pair_v2_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
