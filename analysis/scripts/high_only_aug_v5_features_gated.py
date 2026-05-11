"""
Session 59 — high_only_aug_v5_gated: 4 rank-valued features for the
high_only zone's 4TH-PASS collapse, targeting the K/Q × DS_NO_JOINT
residual that ho_v4 partially captured but didn't fully encode.

S58 decision matrix surfaced that v44_dt's `ho_v4_topNonMax_DS_ms_n_configs_g`
and `ho_v4_topNonMax_DS_ms_max_top_rank_g` give the DT a count + best-top
signal for the non-max-top joint route, BUT not the mid_high QUALITY in
those joints. Oracle's choice between (top=2nd-rank, DS bot, ms mid)
configs depends on the mid_high quality at each candidate top — a
trade-off v44 can't see.

ho_v5 adds 4 features:

  ho_v5_topNonMax_DS_ms_max_mid_high_g       0..13 — across all
    (top!=max, DS bot, ms mid) joint configs, the best higher-of-mid
    pair rank. The missing quality counterpart to v44's max_top_rank.

  ho_v5_topNonMax_DS_ms_best_combined_q_g    0..26 — best
    (top_rank + mid_high) across non-max joints. A "joint quality"
    scalar that lets the DT route on (top, mid) trade-off.

  ho_v5_topNonMax_DS_max_in_bot_pair_n_g     0..15 — count of (top!=max,
    DS bot) configs where max-rank is paired in the bot's suited pair
    (i.e., max-rank is the higher-of-suited-pair for one of the two
    suited pairs in the DS bot). The "max-pair-in-bot" signature that
    HO9 found correlates strongly with oracle abandoning JOINT_PICK in
    favor of DS_NONJOINT.

  ho_v5_topMax_4f_ms_n_configs_g             0..15 — count of (top=max,
    bot 4-flush, mid suited) configs. v44 has best_mid_high in this
    route; this adds the count signal — analog to how v3 paired count
    with max_mid_high.

All zeros for any non-high_only hand (n_pairs > 0 or n_trips > 0 or
n_quads > 0).
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
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


def compute_high_only_v5_features_for_hand(hand: np.ndarray
                                             ) -> tuple[int, int, int, int]:
    """Return (max_mid_high_nonmax, best_combined_q_nonmax,
                n_max_in_bot_pair_nonmax, n_4f_ms_topmax)."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    rank_count: Counter[int] = Counter(int_ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 0 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    max_rank = max(int_ranks)
    max_pos = int_ranks.index(max_rank)
    max_suit = int_suits[max_pos]

    max_mid_high_nonmax = 0
    best_combined_q_nonmax = 0
    n_max_in_bot_pair_nonmax = 0
    n_4f_ms_topmax = 0

    # Enumerate all 105 settings.
    for top_pos in range(7):
        rest = [i for i in range(7) if i != top_pos]
        top_rank = int_ranks[top_pos]
        for mid_a, mid_b in combinations(rest, 2):
            bot_pos = [i for i in rest if i != mid_a and i != mid_b]
            bs = [int_suits[i] for i in bot_pos]
            cnt = sorted(Counter(bs).values(), reverse=True)
            mid_suited = int_suits[mid_a] == int_suits[mid_b]

            if cnt == [2, 2] and mid_suited:  # DS bot + ms mid (joint)
                if top_pos != max_pos:
                    # non-max-top joint
                    mid_high = max(int_ranks[mid_a], int_ranks[mid_b])
                    if mid_high > max_mid_high_nonmax:
                        max_mid_high_nonmax = mid_high
                    combined = top_rank + mid_high
                    if combined > best_combined_q_nonmax:
                        best_combined_q_nonmax = combined

                    # Is max-rank paired in the bot's suited pair?
                    # max-rank is in bot iff max_pos in bot_pos.
                    if max_pos in bot_pos:
                        br = [int_ranks[i] for i in bot_pos]
                        by_suit: dict[int, list[int]] = defaultdict(list)
                        for r, s in zip(br, bs):
                            by_suit[s].append(r)
                        if (len(by_suit[max_suit]) >= 2
                                and max(by_suit[max_suit]) == max_rank):
                            n_max_in_bot_pair_nonmax += 1
            elif cnt == [4] and mid_suited:  # 4-flush bot + ms mid
                if top_pos == max_pos:
                    n_4f_ms_topmax += 1

    return (max_mid_high_nonmax, best_combined_q_nonmax,
            n_max_in_bot_pair_nonmax, n_4f_ms_topmax)


def compute_high_only_v5_features_batch(hands: np.ndarray,
                                          log_every: int = 500_000
                                          ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_mh = np.zeros(N, dtype=np.int8)
    out_q = np.zeros(N, dtype=np.int8)
    out_npair = np.zeros(N, dtype=np.int8)
    out_n4f = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_high_only_v5_features_for_hand(h)
        out_mh[i] = v1
        out_q[i] = v2
        out_npair[i] = v3
        out_n4f[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  ho_v5 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_v5_topNonMax_DS_ms_max_mid_high_g": out_mh,
        "ho_v5_topNonMax_DS_ms_best_combined_q_g": out_q,
        "ho_v5_topNonMax_DS_max_in_bot_pair_n_g": out_npair,
        "ho_v5_topMax_4f_ms_n_configs_g": out_n4f,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Hand 1: 2s 5h 6d Jh Qd Ks As (suits: s,h,d,h,d,s,s)
    # max_rank=A, max_suit=s, max_pos points to As.
    # Suit counts (all 7 cards): s=3, h=2, d=2, c=0.
    # Non-max-top joints:
    #   top=Ks: leftovers {2s,5h,6d,Jh,Qd,As}, suit counts s=2,h=2,d=2.
    #     DS bots: ss+hh = {2s,As,5h,Jh}, mid={6d,Qd} ms ✓ mid_high=Q=12
    #       max-rank=As in bot, suit=s, by_suit[s]={2,14}, max=14=A ✓
    #       → n_max_in_bot_pair_nonmax += 1
    #     DS bots: ss+dd = {2s,As,6d,Qd}, mid={5h,Jh} ms ✓ mid_high=J=11
    #       max-rank=As in bot, suit=s ✓
    #       → n_max_in_bot_pair_nonmax += 1
    #     DS bots: hh+dd = {5h,Jh,6d,Qd}, mid={2s,As} ms ✓ mid_high=A=14
    #       max-rank=As in MID here, not in bot — does NOT count.
    #     So from top=Ks: max_mid_high=14, combined=K+A=27, max_pair_n=2.
    #   top=Qd: leftovers {2s,5h,6d,Jh,Ks,As}, suits s=3,h=2,d=1,c=0.
    #     DS bots: pick 2 of one suit + 2 of another from 3+2+1+0.
    #       ss+hh: pick 2 of {2s,Ks,As}=C(3,2)=3 ways × 1 way for hh.
    #         Each picks 2 spades from {2,K,A}; leftover s goes to mid.
    #         Bot {2s,Ks,5h,Jh}, mid {As, ...} — but mid is 2 cards.
    #         Wait, with bot 4 cards we have 6 leftovers minus 4 = 2 mids.
    #         {2s,Ks} chosen → bot also needs 2 h → {5h,Jh}. mid = {6d, As}.
    #         mid: 6d(d) and As(s) → NOT suited. ms ✗
    #         {2s,As}: bot ss = {2s,As}+ hh = {5h,Jh}. mid = {6d,Ks} d/s, not suited.
    #         {Ks,As}: bot ss = {Ks,As}+ hh = {5h,Jh}. mid = {2s,6d} s/d, not suited.
    #         Hmm none are ms.
    #       ss+dd: only 1 d left ({6d}) — can't pick 2.
    #       hh+dd: only 1 d. No.
    #       So no joint from top=Qd.
    #   top=Jh: leftovers {2s,5h,6d,Qd,Ks,As}, suits s=3,h=1,d=2,c=0.
    #     DS bots: ss+dd. Pick 2 spades from {2,K,A}=C(3,2)=3, 2 d from {6,Q}=1.
    #       Bot {2s,Ks,6d,Qd}, mid {As, 5h}. Suits s,h. NOT suited.
    #       Bot {2s,As,6d,Qd}, mid {Ks, 5h}. s,h NOT suited.
    #       Bot {Ks,As,6d,Qd}, mid {2s, 5h}. s,h NOT suited.
    #     ss+hh: only 1 h. No.
    #     hh+dd: only 1 h. No.
    #     So no joint from top=Jh.
    #   top=6d: leftovers {2s,5h,Jh,Qd,Ks,As}, suits s=3,h=2,d=1,c=0.
    #     DS bots: ss+hh — same logic. Bot picks 2 s + 2 h.
    #       Bot {2s,Ks,5h,Jh}, mid {Qd, As}. d/s NOT suited.
    #       Bot {2s,As,5h,Jh}, mid {Ks, Qd}. s/d NOT suited.
    #       Bot {Ks,As,5h,Jh}, mid {2s, Qd}. s/d NOT suited.
    #     No joint.
    #   top=5h: same logic, only h=1 left after top=5h. No DS bot involving hh.
    #     ss+dd: pick 2 s, 2 d? But d=2 (6d,Qd), s=3.
    #       Bot {2s,Ks,6d,Qd}, mid {Jh, As} h/s NOT suited.
    #       Bot {2s,As,6d,Qd}, mid {Ks, Jh} s/h NOT suited.
    #       Bot {Ks,As,6d,Qd}, mid {2s, Jh} s/h NOT suited.
    #     No.
    #   top=2s: leftovers {5h,6d,Jh,Qd,Ks,As}, suits s=2,h=2,d=2.
    #     ss+hh: {Ks,As,5h,Jh}, mid={6d,Qd} d both ms ✓ mid_high=Q=12
    #       max-rank As in bot, suit=s, by_suit[s]={13,14}, max=14=A ✓
    #       → n_max_in_bot_pair += 1
    #     ss+dd: {Ks,As,6d,Qd}, mid={5h,Jh} h ms ✓ mid_high=J=11
    #       max-rank As in bot ✓ → n_max_in_bot_pair += 1
    #     hh+dd: {5h,Jh,6d,Qd}, mid={Ks,As} s ms ✓ mid_high=A=14
    #       max-rank As in MID, not in bot → doesn't count.
    #
    # Final tally for hand 1:
    #   max_mid_high_nonmax = 14 (from top=Ks hh+dd or top=2s hh+dd)
    #   best_combined_q_nonmax = max(K+A=27, K+J=24, K+Q=25, 2+A=16, 2+Q=14, 2+J=13)
    #                          = 27
    #   n_max_in_bot_pair_nonmax = 4 (top=Ks 2 + top=2s 2)
    #   n_4f_ms_topmax = 0 (no 4-flush from leftovers when top=A)
    cases = [
        ("2s 5h 6d Jh Qd Ks As",
         "expect (14, 27, 4, 0)"),
        # Pair → all zeros
        ("Ac Ad Kh Qs Js Th 9d", "pair AA: expect (0,0,0,0)"),
        # Trips → all zeros
        ("Ac Ad As Kh Ks 7d 2c", "trips_pair AA: expect (0,0,0,0)"),
        # 5 spades + 2 hearts → 4-flush+ms with top=A:
        # As Ks Qs Js 4s 9h 7h.
        # top=As: leftovers {Ks,Qs,Js,4s,9h,7h}, suits s=4,h=2.
        # 4f bot: pick 4 of one suit. 4 spades = {Ks,Qs,Js,4s}. mid={9h,7h} h ms ✓
        #   → n_4f_ms_topmax += 1
        # Only one 4-flush bot (can't pick 4 of h, only 2 there).
        # Non-max-top joints: top != A.
        #   top=Ks: leftovers s=3,h=2,c=0,d=0. ss+hh: pick 2 of {Qs,Js,4s,As}=C(4,2)=6, hh=1.
        #     Bots all contain As in spade-pair. Let's pick a few:
        #     {As,Qs,9h,7h}, mid={Js,4s} both s ms ✓
        #       max=A in bot, by_suit[s]={Q,A}, max=A ✓ → n_max_pair += 1
        #       mid_high=J=11, combined=K+J=24
        #     {As,Js,9h,7h}, mid={Qs,4s} both s ms ✓ → max in bot ✓ +1
        #       mid_high=Q=12 combined=K+Q=25
        #     {As,4s,9h,7h}, mid={Qs,Js} both s ms ✓ → max in bot ✓ +1
        #       mid_high=Q=12 combined=K+Q=25
        #     {Qs,Js,9h,7h}, mid={As,4s} ms s ✓ — max in mid here, not bot.
        #       mid_high=A=14 combined=K+A=27
        #     {Qs,4s,9h,7h}, mid={As,Js} ms s ✓ — max in mid.
        #       mid_high=A=14 combined=27
        #     {Js,4s,9h,7h}, mid={As,Qs} ms s ✓ — max in mid.
        #       mid_high=A=14 combined=27
        #   So from top=Ks: max_mid_high>=14, combined>=27, n_max_pair += 3.
        # Other tops contribute similarly. Expect n_max_pair >> 3, mid_high=14, combined=27.
        ("As Ks Qs Js 4s 9h 7h",
         "5-spades + 2 hearts, expect n_4f_ms=1, big nonmax-joint signals"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_high_only_v5_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
