"""
Session 55 — trips_pair_aug_v2_gated: 4 rank-valued features for the
Pbot_DS routing alternative in the trips_pair zone.

Drill TP (Session 55 Phase 1 diagnostic) showed v39_dt's largest
trips_pair mismatch: v39 picks Pbot_SS, oracle picks Pbot_DS — 10,398
hands at $3,580 mean regret = $6.20/1000h whole-grid contribution.

Drill TP2 (Phase 1b hand-level inspection) confirmed:
  - 100% of mismatch hands have pair with 2 distinct suits
  - The existing tp_pair_routing_is_ds_g feature only captures route R1
    (bot = pair + 2 sings filling pair-suits) — only 0.3% of mismatches
  - Route R2 (bot = pair + 1 trip + 1 sing) is available in 85.7%
  - Route R3 (bot = pair + 2 trip cards) is available in 59.0%
  - v39 is BLIND to R2 and R3

This module adds 4 rank-valued features mirroring pair_aug_v5's design:
encode the QUALITY of the Pbot_DS option across ALL routings (R1+R2+R3),
not just achievability.

For each (pair_in_bot, bot is DS) selection, the remaining 3 cards split
into top (1) + mid (2). The DT can use max_top / min_top / max_mid_sum
to compare alternatives.

Four new gated features (zero outside trips_pair hands):

  tp_v2_bot_DS_n_configs_g       0..N — count of distinct 4-card bot
                                  selections that yield (pair + 2 others,
                                  bot is 2+2 DS). Spans R1, R2, R3.
                                  0 if Pbot_DS unachievable.

  tp_v2_bot_DS_max_top_rank_g    0..14 — across all DS configs, best
                                  achievable top-card rank from the 3
                                  leftover cards.

  tp_v2_bot_DS_min_top_rank_g    0..14 — across all DS configs, lowest
                                  achievable top rank (i.e., the lowest
                                  card any DS config leaves over).

  tp_v2_bot_DS_max_mid_sum_g     0..28 — across all DS configs, best
                                  rank-sum of the 2 remaining cards after
                                  the lowest one is placed on top. Proxy
                                  for "how strong is the mid Hold'em part
                                  if we go Pbot_DS?".

All zeros for any non-trips_pair hand (gated on n_trips==1 AND n_pairs==1).
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


def compute_trips_pair_v2_features_for_hand(hand: np.ndarray
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
    if n_pairs != 1 or n_trips != 1 or n_quads != 0:
        return (0, 0, 0, 0)

    trip_rank = next(r for r, c in rank_count.items() if c == 3)
    pair_rank = next(r for r, c in rank_count.items() if c == 2)
    pair_pos = [i for i in range(7) if int(ranks[i]) == pair_rank]
    non_pair_pos = [i for i in range(7) if int(ranks[i]) != pair_rank]
    pair_suits = [int(suits[p]) for p in pair_pos]

    # Enumerate all C(5,2) = 10 choices of "2 others" to put in bot
    # together with the pair. Bot = pair + 2 of the 5 non-pair cards.
    # Leftover = 3 of the 5 non-pair cards (for top + mid).
    n_configs = 0
    max_top = 0
    min_top = 99
    max_mid_sum = 0

    for sa, sb in combinations(non_pair_pos, 2):
        bot_suits = pair_suits + [int(suits[sa]), int(suits[sb])]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt[:2] != [2, 2]:
            continue
        n_configs += 1
        # Leftover = the 3 non-pair positions not chosen for bot
        leftover = [p for p in non_pair_pos if p != sa and p != sb]
        leftover_ranks = sorted([int(ranks[p]) for p in leftover], reverse=True)
        cfg_max_top = leftover_ranks[0]
        cfg_min_top = leftover_ranks[-1]
        # For best mid: place lowest on top, take top 2 of the remaining for mid
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


def compute_trips_pair_v2_features_batch(hands: np.ndarray,
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
        v1, v2, v3, v4 = compute_trips_pair_v2_features_for_hand(h)
        out_n[i] = v1
        out_max_top[i] = v2
        out_min_top[i] = v3
        out_max_mid_sum[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  trips_pair_v2 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "tp_v2_bot_DS_n_configs_g": out_n,
        "tp_v2_bot_DS_max_top_rank_g": out_max_top,
        "tp_v2_bot_DS_min_top_rank_g": out_min_top,
        "tp_v2_bot_DS_max_mid_sum_g": out_max_mid_sum,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                         dtype=np.uint8)

    # Hand 1 from Drill TP2: 3s 3h 3d 9c Ts Ah Ac, trip=3 pair=A
    # Pair AA in suits {h,c}. Trip 3s,3h,3d. Sings 9c,Ts.
    # Non-pair = {3s, 3h, 3d, 9c, Ts}
    # Enumerate C(5,2) = 10 choices for the 2 "others" in bot:
    #   (3s,3h) bot=AA+3s+3h suits=h,c,s,h={h:2,c:1,s:1}=SS → no
    #   (3s,3d) bot=AA+3s+3d suits=h,c,s,d=rainbow → no
    #   (3s,9c) bot=AA+3s+9c suits=h,c,s,c={c:2,h:1,s:1}=SS → no
    #   (3s,Ts) bot=AA+3s+Ts suits=h,c,s,s={s:2,h:1,c:1}=SS → no
    #   (3h,3d) bot=AA+3h+3d suits=h,c,h,d={h:2,c:1,d:1}=SS → no
    #   (3h,9c) bot=AA+3h+9c suits=h,c,h,c={h:2,c:2}=DS ✓ leftover={3s,3d,Ts} ranks=[10,3,3]
    #     cfg_max_top=10, cfg_min_top=3, cfg_max_mid_sum=10+3=13
    #   (3h,Ts) bot=AA+3h+Ts suits=h,c,h,s={h:2,c:1,s:1}=SS → no
    #   (3d,9c) bot=AA+3d+9c suits=h,c,d,c={c:2,h:1,d:1}=SS → no
    #   (3d,Ts) bot=AA+3d+Ts suits=h,c,d,s=rainbow → no
    #   (9c,Ts) bot=AA+9c+Ts suits=h,c,c,s={c:2,h:1,s:1}=SS → no
    # → n_configs=1, max_top=10, min_top=3, max_mid_sum=13
    cases = [
        ("3s 3h 3d 9c Ts Ah Ac", "AA+3s3h3d+9cTs: expect (1, 10, 3, 13)"),
        # Hand 2: 2s 2h 2d 3s 3c 7c Th, trip=2 pair=3 (suits s,c)
        # Non-pair = {2s, 2h, 2d, 7c, Th}, pair_suits=[s,c]
        # (2s,2h) bot=33+2s+2h suits=s,c,s,h={s:2,c:1,h:1}=SS → no
        # (2s,2d) bot=33+2s+2d suits=s,c,s,d={s:2,c:1,d:1}=SS → no
        # (2s,7c) bot=33+2s+7c suits=s,c,s,c={s:2,c:2}=DS ✓ leftover={2h,2d,Th} ranks=[10,2,2]
        #   cfg_max_top=10, cfg_min_top=2, cfg_max_mid_sum=10+2=12
        # (2s,Th) bot=33+2s+Th suits=s,c,s,h=SS → no
        # (2h,2d) bot=33+2h+2d suits=s,c,h,d=rainbow → no
        # (2h,7c) bot=33+2h+7c suits=s,c,h,c={c:2,s:1,h:1}=SS → no
        # (2h,Th) bot=33+2h+Th suits=s,c,h,h={h:2,s:1,c:1}=SS → no
        # (2d,7c) bot=33+2d+7c suits=s,c,d,c={c:2,s:1,d:1}=SS → no
        # (2d,Th) bot=33+2d+Th suits=s,c,d,h=rainbow → no
        # (7c,Th) bot=33+7c+Th suits=s,c,c,h={c:2,s:1,h:1}=SS → no
        # → n_configs=1, max_top=10, min_top=2, max_mid_sum=12
        ("2s 2h 2d 3s 3c 7c Th", "33+2s2h2d+7cTh: expect (1, 10, 2, 12)"),
        # No trip → all zeros
        ("As Kh Qd Jc Ts 9h 4s", "no trip: expect (0, 0, 0, 0)"),
        # Trips_pair where pair has SAME suit (rare): 5s 5s? Can't — only 1 of each.
        # pair Ks Kh, trip 2s 2h 2d, sing Ac, Th
        # Actually pair always has 2 distinct cards. Same-suit pair would need 2 Ks.
        # Impossible in 52-card deck. Skipping.
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_trips_pair_v2_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
