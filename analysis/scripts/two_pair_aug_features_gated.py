"""
Session 33 — two_pair_aug_gated: 6 new features for the two_pair category.

Two_pair is the biggest fully-untouched lever after Session 32 (v25):
22.3% population × $1,458/1000h regret = $325/1000h share.

Three two_pair-specific aug features have existed since Session 19
(default_bot_is_ds_tp, n_routings_yielding_ds_bot_tp,
swap_high_pair_to_bot_ds_compatible). The Session 33 audit confirmed
they are STRICTLY zero on every non-two_pair canonical row — i.e.,
already category-gated despite the inconsistent naming. Same shape as
the pair audit at the start of Session 32.

The existing 3 features lump Layout B (high pair → mid) and Layout C
(low pair → mid) together via `n_routings_yielding_ds_bot_tp`. The
Session 19 mining notes called out exactly this distinction:
    "structural pattern across the dominant top miss-leaves is
     high-pair-on-mid (DT default) vs high-pair-on-bot (BR swap)"

The 6 new features split B from C and add rank/suit information so
the DT can split on combinations such as:
    "t2p_layout_a_bot_is_ds_g==1" → both pairs in bot, ace on top
    "t2p_n_layout_b_routings_ds_g>=2 AND t2p_high_pair_rank_g>=12" → B
    "t2p_n_layout_b_routings_ds_g==0 AND swap_high_pair_to_bot_ds_compatible==1"
        → only Layout C is DS — must demote high pair to bot
    "t2p_singletons_max_suit_count_g>=2" → suited-mid possible

Six features, all gated to two_pair hands; zeros elsewhere.
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


def _is_ds(suits_arr) -> bool:
    counts = [0, 0, 0, 0]
    for s in suits_arr:
        counts[int(s)] += 1
    counts.sort()
    return counts[3] == 2 and counts[2] == 2


def compute_two_pair_aug_gated_for_hand(hand: np.ndarray) -> tuple[int, int, int, int, int, int]:
    """Return the 6 gated two_pair features for a single 7-card hand.
    Zeros for any non-two_pair hand (n_pairs != 2 OR any trips/quads).
    """
    if hand.shape[0] != 7:
        return (0, 0, 0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    n_singles = sum(1 for c in rank_count.values() if c == 1)
    if n_pairs != 2 or n_trips != 0 or n_quads != 0 or n_singles != 3:
        return (0, 0, 0, 0, 0, 0)

    pair_ranks = sorted([r for r, c in rank_count.items() if c == 2], reverse=True)
    high_pair_rank, low_pair_rank = pair_ranks[0], pair_ranks[1]
    high_pair_positions = [i for i in range(7) if int(ranks[i]) == high_pair_rank]
    low_pair_positions = [i for i in range(7) if int(ranks[i]) == low_pair_rank]
    singleton_indices = [i for i in range(7) if i not in high_pair_positions and i not in low_pair_positions]
    singleton_indices.sort(key=lambda i: int(ranks[i]), reverse=True)
    top_sing_rank = int(ranks[singleton_indices[0]])
    low_sing_rank = int(ranks[singleton_indices[2]])

    high_pair_suits = sorted(int(suits[p]) for p in high_pair_positions)
    low_pair_suits = sorted(int(suits[p]) for p in low_pair_positions)
    layout_a_is_ds = int(high_pair_suits == low_pair_suits)

    n_layout_b_ds = 0
    for top_idx in range(3):
        bot_singletons = [singleton_indices[j] for j in range(3) if j != top_idx]
        bot_positions = low_pair_positions + bot_singletons
        if _is_ds(suits[bot_positions]):
            n_layout_b_ds += 1

    sing_suits = [int(suits[i]) for i in singleton_indices]
    suit_counts = [0, 0, 0, 0]
    for s in sing_suits:
        suit_counts[s] += 1
    sing_max_suit = max(suit_counts)

    return (
        int(layout_a_is_ds),
        int(n_layout_b_ds),
        int(top_sing_rank),
        int(low_sing_rank),
        int(sing_max_suit),
        int(high_pair_rank),
    )


def compute_two_pair_aug_gated_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_a = np.zeros(N, dtype=np.int8)
    out_nb = np.zeros(N, dtype=np.int8)
    out_top = np.zeros(N, dtype=np.int8)
    out_low = np.zeros(N, dtype=np.int8)
    out_sm = np.zeros(N, dtype=np.int8)
    out_hp = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4, v5, v6 = compute_two_pair_aug_gated_for_hand(h)
        out_a[i] = v1
        out_nb[i] = v2
        out_top[i] = v3
        out_low[i] = v4
        out_sm[i] = v5
        out_hp[i] = v6
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  two_pair_aug_gated {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "t2p_layout_a_bot_is_ds_g": out_a,
        "t2p_n_layout_b_routings_ds_g": out_nb,
        "t2p_top_singleton_rank_g": out_top,
        "t2p_low_singleton_rank_g": out_low,
        "t2p_singletons_max_suit_count_g": out_sm,
        "t2p_high_pair_rank_g": out_hp,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        ("Ac Ad Kc Kd 8h 5d 2c", "AA(cd)+KK(cd)+misc — Layout A IS DS, B count?"),
        ("Ac Ad Kh Ks Jd 6c 2c", "AA(cd)+KK(hs)+J,6,2 — Layout A NOT DS"),
        ("2c 6c Td Kc Kh Ah As", "high_only-ish? actually KK + AA + T,6,2"),
        ("7c 7d 8c 8d Jh Ks As", "STRATEGY_GUIDE Rule 2 worked example: 77+88+J,K,A"),
        ("Ac Ad Kh Qs Js Th 9d", "AA + 5 singletons — single pair, should be all zeros"),
        ("Ac Ad As Kh Kd Qs Js", "trips_two_pair — should be all zeros"),
        ("2c 3d 4h 5s 6c Ah As", "high_only-ish + AA — single pair, all zeros"),
    ]
    print(f"{'hand':<32}{'label':<55}-> a nb top low sm hp")
    for s, label in cases:
        feats = compute_two_pair_aug_gated_for_hand(hh(*s.split()))
        print(f"{s:<32}{label:<55}-> {feats}")
