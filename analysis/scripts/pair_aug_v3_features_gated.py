"""
Session 36 — pair_aug_v3_gated: 4 new features for the KK/AA pair subset
targeting the single-suited Rule-4-bot stratum identified by the v29
distill (Session 36 round 2 of pair).

Diagnostic origin (`distill_v29_pair.py`):
  v29 KK/AA whole-grid : $82/1000h
  Rule-4 alone          : $68/1000h  (v29 is $14 WORSE)
  Oracle (R4∪DS-bot)    : $26/1000h
  Single-suited Rule-4-bot stratum = 52.9% of KK/AA, leaks $51/1000h
  within-stratum (v29 = $51, Rule-4 = $38, oracle = $14).

v29's `pair_r4_bot_suit_profile_g` encodes the categorical suit shape
of Rule-4-bot (rainbow / SS / DS / 3-of-suit / 4-flush). It captures
the rainbow stratum well (where Rule 5 lives) but not single-suited.
The single-suited stratum needs FINER encoding: which suit is dominant,
its rank composition, and pair-suit alignment.

Four new features, all zero outside KK/AA pair hands. Prefix
`pair_r4v3_*_g` (collision-checked: distinct from `pair_r4_*_g`,
`pair_*_g`, `_g`/`comp_*_g`/`tp_*_g`/`t2p_*_g`/`ho_*_g`/`trips_*_g`):

  pair_r4v3_kkaa_dom_suit_count_g   0..4 — count of cards in the
                                    dominant suit of Rule-4-bot. 0 if
                                    non-KK/AA. Distinguishes SS (count=2)
                                    from 3-of-suit (count=3) etc.

  pair_r4v3_kkaa_dom_suit_max_rank_g  0..14 — max rank in the dominant
                                    suit of Rule-4-bot. The dominant
                                    suit's "quality".

  pair_r4v3_kkaa_n_high_kickers_g   0..5 — count of T-A among non-pair
                                    cards. KK/AA-gated only (overlaps
                                    with v29 `pair_r4_n_broadway_kickers_g`
                                    but tighter gating may help tree
                                    use the signal differently).

  pair_r4v3_kkaa_pair_suit_alignment_g  0..2 — count of pair-suits
                                    that appear in the 5 non-pair
                                    kickers. (Pair has 2 suits; kickers
                                    can share 0/1/2 of those suits.)
                                    Captures DS-bot feasibility within
                                    KK/AA (need ≥1 kicker each in BOTH
                                    K-suits for DS-bot).
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


def compute_pair_r4v3_features_for_hand(hand: np.ndarray) -> tuple[int, int, int, int]:
    """Return the 4 KK/AA-gated features for a single 7-card hand.
    Zeros for any hand that is not single-pair KK or AA.
    """
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
    if pair_rank not in (13, 14):
        return (0, 0, 0, 0)

    pair_positions = [i for i in range(7) if int(ranks[i]) == pair_rank]
    pair_suits = sorted(int(suits[i]) for i in pair_positions)
    sing_indices = [i for i in range(7) if i not in pair_positions]
    sing_ranked_desc = sorted(sing_indices, key=lambda i: int(ranks[i]), reverse=True)
    bot_indices = sing_ranked_desc[1:5]  # Rule-4 bot = 4 cards (omit highest singleton, which goes to top)

    # Feature 1: dominant suit count in Rule-4-bot
    bot_suit_counts = Counter(int(suits[i]) for i in bot_indices)
    counts_sorted = sorted(bot_suit_counts.values(), reverse=True)
    dom_suit_count = counts_sorted[0] if counts_sorted else 0
    # Identify dominant suit
    dom_suit = bot_suit_counts.most_common(1)[0][0]

    # Feature 2: max rank in dominant suit of Rule-4-bot
    dom_suit_ranks = [int(ranks[i]) for i in bot_indices if int(suits[i]) == dom_suit]
    dom_suit_max_rank = max(dom_suit_ranks) if dom_suit_ranks else 0

    # Feature 3: count of T-A among non-pair kickers
    sing_ranks = [int(ranks[i]) for i in sing_indices]
    n_high_kickers = sum(1 for r in sing_ranks if r >= 10)

    # Feature 4: count of pair-suits represented in 5 non-pair kickers
    sing_suits = [int(suits[i]) for i in sing_indices]
    pair_suit_alignment = sum(1 for ps in pair_suits if ps in sing_suits)

    return (
        int(dom_suit_count),
        int(dom_suit_max_rank),
        int(n_high_kickers),
        int(pair_suit_alignment),
    )


def compute_pair_r4v3_features_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_dom_count = np.zeros(N, dtype=np.int8)
    out_dom_max = np.zeros(N, dtype=np.int8)
    out_n_high = np.zeros(N, dtype=np.int8)
    out_pair_align = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_pair_r4v3_features_for_hand(h)
        out_dom_count[i] = v1
        out_dom_max[i] = v2
        out_n_high[i] = v3
        out_pair_align[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_r4v3 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "pair_r4v3_kkaa_dom_suit_count_g":     out_dom_count,
        "pair_r4v3_kkaa_dom_suit_max_rank_g":  out_dom_max,
        "pair_r4v3_kkaa_n_high_kickers_g":     out_n_high,
        "pair_r4v3_kkaa_pair_suit_alignment_g": out_pair_align,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        # KK with rainbow Rule-4-bot — bot is Tc9h5d3s, all different suits
        ("Ks Kd 3s 5d 9h Tc Js", "KK + JT9 + 53. Rule-4 top=J, bot=Tc9h5d3s rainbow"),
        # KK with single-suited Rule-4-bot (the leak stratum)
        ("Ks Kd 8c 7c 5h 4s Js", "KK + J + 8c7c5h4s. Rule-4 bot has 2 clubs = single-suited"),
        # AA with broadway kickers
        ("Ac Ad Kh Qs Js Th 9d", "AA + KQJT9. Rule-4 top=K, bot=QsJsTh9d"),
        # QQ — should return zeros (not KK/AA)
        ("Qc Qd Kh Js Th 9d 5s", "QQ + Kh broadway — non-KK/AA, all zeros"),
        # KK two-pair — should return zeros (not single-pair)
        ("Ks Kd As Ac Jh Th 9d", "KK + AA + Jh — two-pair, zeros"),
    ]
    print(f"{'hand':<32}{'label':<70}-> (dom_count, dom_max, n_high, pair_align)")
    for s, label in cases:
        feats = compute_pair_r4v3_features_for_hand(hh(*s.split()))
        print(f"{s:<32}{label:<70}-> {feats}")
