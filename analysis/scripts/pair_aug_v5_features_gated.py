"""
Session 54 — pair_aug_v5_gated: 4 rank-valued features for the pair-bot-DS
zone, addressing v38's "boolean features are redundant" failure.

Phase 2 v1 (v38_dt with 2 booleans) shipped $0 because the features were
derivable from existing suit-distribution features. v5 features are
rank-valued and CONDITIONAL on the pair-bot DS configuration — they
encode info that's NOT derivable from existing features.

Four new gated features (zero outside single-pair hands):

  pair_aug_v5_bot_DS_n_configs_g       0..N — count of distinct
                                       (sing_a, sing_b) pairs that
                                       yield 2+2 DS bot when pair is
                                       in bot. 0 if not achievable.

  pair_aug_v5_bot_DS_max_top_rank_g    0..14 — across all DS configs,
                                       the highest possible top-card
                                       rank among the 3 leftover
                                       singletons. (Best top rank
                                       achievable while keeping pair-bot
                                       DS structure.)

  pair_aug_v5_bot_DS_min_top_rank_g    0..14 — symmetrically, the
                                       lowest top-rank achievable.

  pair_aug_v5_bot_DS_max_mid_sum_g     0..28 — best sum of the 2
                                       remaining sings (after picking
                                       top), across DS configs. Proxy
                                       for "how strong is the mid
                                       Hold'em part if we go pair-bot
                                       DS?".

These features encode the QUALITY of the pair-bot DS option, not just
its achievability. Should let the DT distinguish "pair-bot DS with
high mid rank-sum" from "pair-bot DS with low mid rank-sum".
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


def compute_pair_v5_features_for_hand(hand: np.ndarray) -> tuple[int, int, int, int]:
    """Return (n_configs, max_top_rank, min_top_rank, max_mid_sum)."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 1 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    pair_rank = next(r for r, c in rank_count.items() if c == 2)
    pair_pos = [i for i in range(7) if int(ranks[i]) == pair_rank]
    sing_pos = [i for i in range(7) if int(ranks[i]) != pair_rank]
    pair_suits = [int(suits[p]) for p in pair_pos]

    # Find all (sing_a, sing_b) pairs that yield DS bot
    n_configs = 0
    max_top = 0
    min_top = 99  # placeholder
    max_mid_sum = 0

    for sa, sb in combinations(sing_pos, 2):
        # Bot suits = pair_suits + (suits[sa], suits[sb])
        bot_suits = pair_suits + [int(suits[sa]), int(suits[sb])]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt[:2] != [2, 2]:
            continue
        # DS achieved
        n_configs += 1
        # Leftover sings (3 of them) for top + mid
        leftover = [p for p in sing_pos if p != sa and p != sb]
        leftover_ranks = sorted([int(ranks[p]) for p in leftover], reverse=True)
        # Top can be any of these 3; max top = highest, min top = lowest
        cfg_max_top = leftover_ranks[0]
        cfg_min_top = leftover_ranks[-1]
        # Mid sum = sum of remaining 2 after top (best case: highest 2 if low top)
        # For "best mid", pick top=lowest, mid=highest 2: mid_sum = leftover_ranks[0] + leftover_ranks[1]
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


def compute_pair_v5_features_batch(hands: np.ndarray,
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
        v1, v2, v3, v4 = compute_pair_v5_features_for_hand(h)
        out_n[i] = v1
        out_max_top[i] = v2
        out_min_top[i] = v3
        out_max_mid_sum[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_v5 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "pair_aug_v5_bot_DS_n_configs_g": out_n,
        "pair_aug_v5_bot_DS_max_top_rank_g": out_max_top,
        "pair_aug_v5_bot_DS_min_top_rank_g": out_min_top,
        "pair_aug_v5_bot_DS_max_mid_sum_g": out_max_mid_sum,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)
    cases = [
        # Drill P2 hand 13: 2♠ 3♥ 4♦ 9♠ K♦ A♥ A♦  AA pair
        # Pair suits ♥♦. Sings in pair-suits: 3♥, 4♦, K♦. Not in: 2♠, 9♠.
        # DS configs: (3♥, 4♦), (3♥, K♦) = 2 configs (need 1 ♥ + 1 ♦)
        # Config 1: bot=AA+3♥+4♦, leftover=2♠,9♠,K♦ → top∈{2,9,K}, max=13, min=2
        # Config 2: bot=AA+3♥+K♦, leftover=2♠,4♦,9♠ → top∈{2,4,9}, max=9, min=2
        # max_top across configs = 13, min_top = 2
        # max_mid_sum = max of (9+K=22) and (4+9=13) = 22
        ("2s 3h 4d 9s Kd Ah Ad", "AA pair: expect (2, 13, 2, 22)"),
        # Drill P2 hand 8: 2♠ 3♠ 3♥ 4♦ 5♥ 6♦ 8♣  33 pair
        # Pair suits ♠♥. Sings: 2♠, 4♦, 5♥, 6♦, 8♣
        # DS configs: need 1 ♠ + 1 ♥. ♠ sings = 2♠. ♥ sings = 5♥.
        # Only config: bot=33+2♠+5♥, leftover=4♦,6♦,8♣ → top∈{4,6,8}
        # max_top = 8, min_top = 4, max_mid_sum = 6+8 = 14
        ("2s 3s 3h 4d 5h 6d 8c", "33 pair: expect (1, 8, 4, 14)"),
        # No pair: should return (0,0,0,0)
        ("2c 3c 4d 5h 6s 7c 8d", "no pair: expect (0,0,0,0)"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_pair_v5_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
