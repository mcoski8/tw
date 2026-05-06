"""
Session 35 — pair_aug_v2_gated: 4 new features for the single-pair category
targeting the Rule-4-bot-suit-profile axis identified by the v27 distillation.

Diagnostic origin (Session 35, `distill_v27_pair.py`):

  Rule 4 alone on KK/AA   : $949/1000h regret = $68/1000h whole-grid
  v27 actual on KK/AA     : $1,236/1000h regret = $89/1000h whole-grid
  Oracle (R4 OR DS-bot)   : $362/1000h regret = $26/1000h whole-grid

v27 is $20/1000h WORSE than Rule 4 on KK/AA. v27 picks Rule-4 84.6% of
the time, DS-bot 7.8%, "other" 7.6%. The 15.4% non-Rule-4 picks are
systematically incorrect — v27 overgeneralizes v25's pair-gated features
to KK/AA hands where Rule 4 was correct.

The missing signal: **the suit profile of Rule 4's resulting bot.** When
Rule-4-bot is rainbow, DS-bot is the right swap (43.6% strict-wins).
When Rule-4-bot is single-suited, DS-bot wins only 20.4%. When already
DS, DS-bot rarely better. v27 has no direct feature for this — v25's
existing pair-gated features encode kickers-in-pair-suit and alt-routing
quality, but not the SHAPE of Rule-4's leftover bot.

Four features, all gated to single-pair hands; zeros elsewhere. Prefix
`pair_r4_*_g` (collision-checked: distinct from `pair_*_g`, `tp_*_g`,
`comp_*_g`, `t2p_*_g`, `ho_*_g`):

  pair_r4_bot_suit_profile_g    Rule-4 bot suit shape, encoded:
                                0 = invalid (non-pair)
                                1 = rainbow (1+1+1+1)
                                2 = single-suited (2+1+1)
                                3 = double-suited (2+2)
                                4 = three-of-a-suit (3+1)
                                5 = four-of-a-suit (4)

  pair_r4_bot_max_rank_g        Highest rank in Rule-4 bot
                                (= 2nd-highest non-pair rank). 0..14.

  pair_r4_n_broadway_kickers_g  Count of T-A among the 5 non-pair cards.
                                0..5. Captures "premium kickers prop up
                                paired-mid" pattern.

  pair_r4_n_low_kickers_g       Count of 2-5 among the 5 non-pair cards.
                                0..5. Captures "lots of low cards make
                                DS-bot more attractive" pattern.

Note: n_broadway and n_low (base features) include the pair cards. The
new features deliberately EXCLUDE the pair to give the DT a clean
non-pair-body signal independent of pair_high_rank.
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

# Suit-profile encoding (matches the SUIT_PROFILE_* constants from
# tw_analysis.query but for hand-level clarity we encode locally).
SP_INVALID = 0
SP_RAINBOW = 1
SP_SINGLE_SUITED = 2
SP_DOUBLE_SUITED = 3
SP_THREE_OF_SUIT = 4
SP_FOUR_OF_SUIT = 5


def _bot_suit_profile_code(suit_counts: list[int]) -> int:
    """suit_counts is a list of 4 nonneg ints summing to 4 (the bot has 4
    cards). Return the SP_* code for the suit profile."""
    counts = sorted(suit_counts, reverse=True)
    if counts == [1, 1, 1, 1]:
        return SP_RAINBOW
    if counts == [2, 1, 1, 0]:
        return SP_SINGLE_SUITED
    if counts == [2, 2, 0, 0]:
        return SP_DOUBLE_SUITED
    if counts == [3, 1, 0, 0]:
        return SP_THREE_OF_SUIT
    if counts == [4, 0, 0, 0]:
        return SP_FOUR_OF_SUIT
    return SP_INVALID


def compute_pair_r4_features_for_hand(hand: np.ndarray) -> tuple[int, int, int, int]:
    """Return the 4 gated features for a single 7-card hand.
    Zeros for any non-single-pair hand (n_pairs != 1, or any trips/quads).
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
    pair_positions = [i for i in range(7) if int(ranks[i]) == pair_rank]
    sing_indices = [i for i in range(7) if i not in pair_positions]
    # Rule-4 routing: top = highest non-pair, bot = remaining 4 non-pair.
    sing_ranked_desc = sorted(sing_indices, key=lambda i: int(ranks[i]), reverse=True)
    top_idx_in_hand = sing_ranked_desc[0]
    bot_indices = sing_ranked_desc[1:5]  # 4 cards

    # Feature 1: Rule-4 bot suit profile
    bot_suit_counts = [0, 0, 0, 0]
    for i in bot_indices:
        bot_suit_counts[int(suits[i])] += 1
    suit_code = _bot_suit_profile_code(bot_suit_counts)

    # Feature 2: highest rank in Rule-4 bot (= 2nd-highest non-pair rank)
    bot_max_rank = int(ranks[bot_indices[0]])  # already sorted desc

    # Feature 3: count of T-A among the 5 non-pair cards
    sing_ranks = [int(ranks[i]) for i in sing_indices]
    n_broadway_kickers = sum(1 for r in sing_ranks if r >= 10)

    # Feature 4: count of 2-5 among the 5 non-pair cards
    n_low_kickers = sum(1 for r in sing_ranks if r <= 5)

    return (
        int(suit_code),
        int(bot_max_rank),
        int(n_broadway_kickers),
        int(n_low_kickers),
    )


def compute_pair_r4_features_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_suit = np.zeros(N, dtype=np.int8)
    out_botmax = np.zeros(N, dtype=np.int8)
    out_nbway = np.zeros(N, dtype=np.int8)
    out_nlow = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_pair_r4_features_for_hand(h)
        out_suit[i] = v1
        out_botmax[i] = v2
        out_nbway[i] = v3
        out_nlow[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_r4 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "pair_r4_bot_suit_profile_g":   out_suit,
        "pair_r4_bot_max_rank_g":       out_botmax,
        "pair_r4_n_broadway_kickers_g": out_nbway,
        "pair_r4_n_low_kickers_g":      out_nlow,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        # (hand, expected (suit_code, bot_max, n_bway_kickers, n_low_kickers), label)
        ("Ks Kd 3s 5d 9h Tc Js", (1, 10, 2, 2), "USER EXAMPLE: KK + JT9 + 53. Rule-4 top=J, bot=Tc9h5d3s rainbow"),
        ("Ks Kd 8c 7d 5h 4s Js", (1, 8, 1, 2),  "KK + J + 8754. Rule-4 top=J, bot=8c7d5h4s rainbow"),
        ("Ks Kd 8c 7c 5h 4s Js", (2, 8, 1, 2),  "KK + J + 8c7c5h4s. Rule-4 bot has 2 clubs = single-suited"),
        ("Ks Kd 8c 7c 4c 3s Js", (4, 8, 1, 2),  "KK + J + 8c7c4c + 3s. Rule-4 bot has 3 clubs = three-of-suit"),
        ("Ks Kd 8c 7c 4c 3c Js", (5, 8, 1, 2),  "KK + J + 8c7c4c3c. Rule-4 bot is 4-flush"),
        ("Ks Kd 8s 7c 4c 3d Js", (2, 8, 1, 2),  "KK + J + 8s7c4c3d (mixed) — bot=8s7c4c3d single-suited 2c"),
        ("Ac Ad 2c 3d 4h 5s 6h", (1, 5, 0, 4),  "AA wheel: top=6, bot=2c3d4h5s rainbow, n_low=4"),
        ("Ac Ad Kh Qs Js Th 9d", (3, 12, 4, 0), "AA + KQJT9 = bot Q♠J♠T♥9♦ — Q,J ♠+♠ = 2; T♥+9♦ = +1+1 → wait check"),
        ("Ac Ad Kh Qs Js Th 9d", None,           "(rerun above to verify suit profile)"),
        ("Ac As Ks Kd Jc Td 5h", (0, 0, 0, 0),  "Two pairs — should be all zeros"),
        ("Ac Ad As Kh Kd Qs Js", (0, 0, 0, 0),  "trips_two_pair — all zeros"),
        ("9c Td Jh Qs Kc Ad As", None,           "AA + Broadway connectors — let's see what suit profile we get"),
    ]
    print(f"{'hand':<32}{'label':<70}-> (suit, bot_max, n_bway, n_low)")
    for s, expected, label in cases:
        feats = compute_pair_r4_features_for_hand(hh(*s.split()))
        ok = ""
        if expected is not None:
            ok = " ✓" if feats == expected else f" EXPECTED {expected}"
        print(f"{s:<32}{label:<70}-> {feats}{ok}")
