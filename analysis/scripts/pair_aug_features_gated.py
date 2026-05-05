"""
Session 32 — pair_aug_gated: 6 new features for the single-pair category.

The pair category is the largest residual on v24 — population share 46.6%
× $1,873/1000h regret = **$873/1000h share**. Three pair-specific aug
features have existed since Session 17 (default_bot_is_ds /
n_top_choices_yielding_ds_bot / pair_to_bot_alt_is_ds), and the audit at
the start of Session 32 confirmed they are STRICTLY zero on every
non-pair canonical row — i.e., already category-gated despite the
inconsistent naming. They are not the v19 leakage pattern.

But they're narrow: three booleans that ask "is the bot DS under this
routing?". They tell the DT WHETHER, not WHY/HOW. The 6 new features
encode rank- and mid-quality signal so the DT can split on
combinations such as:

  - "default_bot_is_ds==1 AND default_top_rank_g>=13" — Rule-1-like
    trigger refined by top strength.
  - "pair_to_bot_alt_is_ds==1 AND alt_mid_suited_g==1
    AND alt_mid_n_broadway_g==2" — alt routing with strong mid.
  - "kickers_in_pair_suit_max_g==2 AND _min_g==2" — Rule 1's (2,2)
    perfect balance, distinguished from (3,1) / (1,1) / (2,1).

Six features, all gated to single-pair hands; zero elsewhere:

  pair_kickers_in_pair_suit_max_g   max count of non-pair cards
                                    matching either pair-suit
  pair_kickers_in_pair_suit_min_g   min of same
                                    (together fully specifies the
                                    (n_pair_suit_a, n_pair_suit_b) split)
  pair_default_top_rank_g           rank of highest non-pair card
                                    (= top under v3-default routing)
  pair_alt_top_rank_g               rank of 3rd-highest non-pair card
                                    (= top under pair-to-bot alt routing)
  pair_alt_mid_suited_g             top-2 non-pair cards same-suit (0/1)
  pair_alt_mid_n_broadway_g         broadway (T-A) count among top-2
                                    non-pair cards (0..2)
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


def compute_pair_aug_gated_for_hand(hand: np.ndarray) -> tuple[int, int, int, int, int, int]:
    """Return the 6 gated features for a single 7-card hand. Zeros for any
    non-pair hand (n_pairs != 1, or n_trips/n_quads >= 1).
    """
    if hand.shape[0] != 7:
        return (0, 0, 0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 1 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0, 0, 0)

    pair_rank = next(r for r, c in rank_count.items() if c == 2)
    pair_positions = [i for i in range(7) if int(ranks[i]) == pair_rank]
    pair_suits = {int(suits[pair_positions[0]]), int(suits[pair_positions[1]])}
    if len(pair_suits) != 2:
        return (0, 0, 0, 0, 0, 0)
    suit_a, suit_b = sorted(pair_suits)

    sing_indices = [i for i in range(7) if i not in pair_positions]
    sing_ranked = sorted(sing_indices, key=lambda i: int(ranks[i]), reverse=True)

    n_in_a = sum(1 for i in sing_indices if int(suits[i]) == suit_a)
    n_in_b = sum(1 for i in sing_indices if int(suits[i]) == suit_b)
    kickers_max = max(n_in_a, n_in_b)
    kickers_min = min(n_in_a, n_in_b)

    default_top_rank = int(ranks[sing_ranked[0]])
    alt_top_rank = int(ranks[sing_ranked[2]])

    mid_a_idx, mid_b_idx = sing_ranked[0], sing_ranked[1]
    alt_mid_suited = int(int(suits[mid_a_idx]) == int(suits[mid_b_idx]))
    alt_mid_n_broadway = int(int(ranks[mid_a_idx]) >= 10) + int(int(ranks[mid_b_idx]) >= 10)

    return (
        int(kickers_max),
        int(kickers_min),
        int(default_top_rank),
        int(alt_top_rank),
        int(alt_mid_suited),
        int(alt_mid_n_broadway),
    )


def compute_pair_aug_gated_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_max = np.zeros(N, dtype=np.int8)
    out_min = np.zeros(N, dtype=np.int8)
    out_dtop = np.zeros(N, dtype=np.int8)
    out_atop = np.zeros(N, dtype=np.int8)
    out_msu = np.zeros(N, dtype=np.int8)
    out_mbr = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4, v5, v6 = compute_pair_aug_gated_for_hand(h)
        out_max[i] = v1
        out_min[i] = v2
        out_dtop[i] = v3
        out_atop[i] = v4
        out_msu[i] = v5
        out_mbr[i] = v6
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_aug_gated {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "pair_kickers_in_pair_suit_max_g": out_max,
        "pair_kickers_in_pair_suit_min_g": out_min,
        "pair_default_top_rank_g": out_dtop,
        "pair_alt_top_rank_g": out_atop,
        "pair_alt_mid_suited_g": out_msu,
        "pair_alt_mid_n_broadway_g": out_mbr,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        ("3c 4d 8d 9c Qc Qd Ac",       "Rule 1 ideal: QQ + A, kickers (2,2)"),
        ("Qc Qd Ah 3c 5c 4d 9s",       "QQ + A, kickers (2,1) lopsided"),
        ("4c 6d 8h Js Qd Kc Ks",       "KK with broadway body — Rule 4"),
        ("4c 6d 8h Qd Kc Ks Ah",       "KK + Ace — Rule 4"),
        ("9c Td Jh Qs Kc Ad As",       "AA + broadway — Rule 4"),
        ("Ac Ad Kh Qs Js Th 9d",       "high_only — should be all zeros"),
        ("Ac Ad As Kh Kd Qs Js",       "trips_two_pair — should be all zeros"),
        ("2c 3d 4h 5s 6c Ah As",       "AA wheel body"),
    ]
    print(f"{'hand':<32}{'label':<48}-> kmax kmin dtop atop msu mbr")
    for s, label in cases:
        feats = compute_pair_aug_gated_for_hand(hh(*s.split()))
        print(f"{s:<32}{label:<48}-> {feats}")
