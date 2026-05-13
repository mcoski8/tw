"""
Session 71 — high_only_aug_v6_gated: 2 rank-valued features for the
SS-bot + suited-mid route in the high_only zone, conditional on
top = max-rank-of-hand.

Direct SS-axis counterpart to ho_v3's DS-axis enumeration. The S71
diagnostic (drill_v44_high_only_S71.py) found that v44's STRUCTURE-
bucket residual ($147.59 WG, 38.7% of high_only's $381.39 total
high_only WG) is dominated by the **`SS_mu → SS_ms`** mismatch family:

  Cell × bucket                         Top mismatch                 $ WG
  K × DS_NO_JOINT × STRUCTURE           tK_SS_mu → tK_SS_ms           3.40
  A × DS_NO_JOINT × STRUCTURE           tA_SS_mu → tA_SS_ms           5.47
  Q × DS_NO_JOINT × STRUCTURE           tQ_SS_mu → tQ_SS_ms           1.12
  J × DS_NO_JOINT × STRUCTURE           tJ_SS_mu → tJ_SS_ms           0.15

In every case: same top rank (= max-rank), same SS bot suit profile —
the only difference is whether the mid pair shares a suit. v44 has
no hand-level aggregate over (top=max ∧ bot=SS ∧ mid=suited)
configurations; the only SS info v44 sees is the per-setting
bot_suit_profile (105-dim per hand), which the DT can't aggregate at
depth=36 ml=1 saturation.

ho_v6 fills this gap with the SS-axis twin of ho_v3 (which shipped
+$79/1000h in S57 at the DS axis). For each high_only hand, fix
top = max-rank-of-hand. Enumerate C(6,4)=15 candidate bots from the
remaining 6 cards. For each: check (a) bot is SS (2+1+1 suit
distribution), (b) the 2 leftover (mid) cards share a suit. If both,
count + track mid quality.

  ho_v6_topMax_SS_ms_n_configs_g       0..15 — count of (top=max-rank,
                                       SS bot, ms mid) configurations.

  ho_v6_topMax_SS_ms_max_mid_high_g    0..14 — across all SS-joint configs,
                                       best higher-of-suited-mid rank.
                                       0 if no SS-joint config.

All zeros for any non-high_only hand (n_pairs > 0 or n_trips > 0 or
n_quads > 0).

Why non-derivable from v44's 107 features:
  * v44's `bot_suit_profile` is per-setting (105 values per hand); the
    HAND-LEVEL count of SS-bot configurations is not a linear or
    bounded combination of any subset of v44's features.
  * No ho_v* feature mentions SS in its name; the SS axis is genuinely
    absent from v44's gated-feature taxonomy.
  * At depth=36 ml=1 with 2.7 rows per leaf (S59 saturation), the DT
    cannot derive this count via multi-depth splits on the 105
    per-setting suit-profile values.
  * S57's ho_v3 (the DS twin) shipped +$79/1000h with the same
    enumeration shape, proving the structural pattern is liftable.

This is the S71 Phase 2 deliverable per CURRENT_PHASE.md. Smoke-test
in `__main__`. Full retrain (v46_dt) queued for S72.
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


def _is_ss(suits) -> bool:
    """True iff the 4-card suit multiset is exactly 2+1+1
    (single-suited bot: one pair of suits + two singletons of different
    suits)."""
    c = Counter(suits)
    sv = sorted(c.values(), reverse=True)
    return sv == [2, 1, 1]


def compute_high_only_v6_features_for_hand(hand: np.ndarray
                                             ) -> tuple[int, int]:
    """Return (n_configs, max_mid_high) for the (top=max-rank, SS bot,
    ms mid) enumeration. (0, 0) for any non-high_only hand or when no
    such configuration exists."""
    if hand.shape[0] != 7:
        return (0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 0 or n_trips != 0 or n_quads != 0:
        return (0, 0)

    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    max_rank = max(int_ranks)
    top_pos = int_ranks.index(max_rank)
    rest_pos = [i for i in range(7) if i != top_pos]  # 6 cards

    n_configs = 0
    max_mid_high = 0

    for bot_idx in combinations(rest_pos, 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        if not _is_ss(bot_suits):
            continue
        mid_pos = [i for i in rest_pos if i not in bot_idx]  # 2 cards
        if int_suits[mid_pos[0]] != int_suits[mid_pos[1]]:
            continue
        n_configs += 1
        mid_high = max(int_ranks[mid_pos[0]], int_ranks[mid_pos[1]])
        if mid_high > max_mid_high:
            max_mid_high = mid_high

    if n_configs == 0:
        return (0, 0)
    return (n_configs, max_mid_high)


def compute_high_only_v6_features_batch(hands: np.ndarray,
                                          log_every: int = 500_000
                                          ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_n = np.zeros(N, dtype=np.int8)
    out_max_high = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2 = compute_high_only_v6_features_for_hand(h)
        out_n[i] = v1
        out_max_high[i] = v2
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  ho_v6 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_v6_topMax_SS_ms_n_configs_g": out_n,
        "ho_v6_topMax_SS_ms_max_mid_high_g": out_max_high,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Test 1 — non-high_only (pair AA): expect (0, 0).
    # Hand: Ac Ad Kh Qs Js Th 9d  (has a pair AA → gated out).
    case1_h = hh("Ac", "Ad", "Kh", "Qs", "Js", "Th", "9d")
    case1_exp = (0, 0)

    # Test 2 — rest suit dist 2+2+2 (after top removed): SS+ms
    # impossible.
    # Hand: 2s 5h 6d Jh Qd Ks As.  top=As(=14, suit s).
    # rest = {2s, 5h, 6d, Jh, Qd, Ks}. Suit comp: s=2(2s,Ks), h=2(5h,Jh), d=2(6d,Qd).
    # For SS (2+1+1): take 2 of one suit + 1 of each other.
    #   "2" from s = {2s, Ks}: bot adds 1 from h + 1 from d (4 choices).
    #     leftover (mid) = 1 of h + 1 of d → different suits → never ms.
    #   "2" from h = {5h, Jh}: bot adds 1 from s + 1 from d. mid = 1s + 1d → not ms.
    #   "2" from d = {6d, Qd}: bot adds 1 from s + 1 from h. mid = 1s + 1h → not ms.
    # All SS bots yield unsuited mid. n_configs=0.
    case2_h = hh("2s", "5h", "6d", "Jh", "Qd", "Ks", "As")
    case2_exp = (0, 0)

    # Test 3 — rest suit dist 4+1+1+0 (after top removed): SS+ms
    # achievable via single config.
    # Hand: As 2s 3s 5s Th Jd 9c.  top=As. (Note: max=A, suit=s.)
    # rest = {2s, 3s, 5s, Th, Jd, 9c}. Suit comp: s=3, h=1, d=1, c=1.
    # SS bot needs 2+1+1 from rest.
    #   "2" from s (3 ways: pick 2 of {2s,3s,5s}).
    #     "1+1" from any 2 of {h, d, c} (3 choices: hd, hc, dc).
    #     leftover (mid) = 1 of the "non-chosen" s + 1 of the "non-chosen" suit.
    #       mid suits: 1×s + 1×(remaining-singleton). Different suits → NOT ms.
    #   "2" from h: only 1 h card, impossible.
    #   "2" from d: only 1 d card, impossible.
    #   "2" from c: only 1 c card, impossible.
    # So n_configs=0.
    case3_h = hh("As", "2s", "3s", "5s", "Th", "Jd", "9c")
    case3_exp = (0, 0)

    # Test 4 — rest suit dist 2+2+1+1: SS+ms achievable.
    # Hand: As Kh Qd Jh Td 5s 2c.  top=As. (max=A, suit=s.)
    # rest = {Kh, Qd, Jh, Td, 5s, 2c}. Suit comp: h=2(Kh,Jh), d=2(Qd,Td), s=1(5s), c=1(2c).
    # SS bot (2+1+1):
    #   "2" from h = {Kh, Jh}: 1+1 picks from {d,s,c}, 3 choices: ds,dc,sc.
    #     ds: bot = {Kh,Jh,Qd,5s} (pick Qd from d, 5s from s)  → mid={Td,2c} d/c not ms.
    #         bot = {Kh,Jh,Qd,2c} → mid={Td,5s} d/s not ms.
    #         bot = {Kh,Jh,Td,5s} → mid={Qd,2c} d/c not ms.
    #         bot = {Kh,Jh,Td,2c} → mid={Qd,5s} d/s not ms.
    #     dc: bot needs Qd or Td + 2c. mid = leftover (h's: Kh or Jh gone? No — h leftover is empty since both went to bot.)
    #         Wait, "2" from h means both Kh & Jh go to bot. After bot has Kh+Jh, we pick 1 from d
    #         and 1 from c: e.g. Qd + 2c. bot = {Kh,Jh,Qd,2c}. mid = {Td, 5s} d/s not ms.
    #         OR Td + 2c. bot = {Kh,Jh,Td,2c}. mid = {Qd, 5s} d/s not ms.
    #     sc: pick 5s + 2c. bot = {Kh,Jh,5s,2c}. mid = {Qd, Td} both d → SUITED ✓
    #       mid_high = Q = 12. n_configs += 1.
    #   "2" from d = {Qd, Td}: 1+1 picks from {h, s, c}.
    #     hs: pick (Kh or Jh) + 5s. mid = remaining h + 2c = h/c not ms.
    #     hc: pick (Kh or Jh) + 2c. mid = remaining h + 5s = h/s not ms.
    #     sc: pick 5s + 2c. bot = {Qd,Td,5s,2c}. mid = {Kh, Jh} both h → SUITED ✓
    #       mid_high = K = 13. n_configs += 1.
    #   "2" from s: only 1 s card, impossible.
    #   "2" from c: only 1 c card, impossible.
    # n_configs=2, max_mid_high = K=13.
    case4_h = hh("As", "Kh", "Qd", "Jh", "Td", "5s", "2c")
    case4_exp = (2, 13)

    # Test 5 — multiple SS+ms configs with varying mid_high.
    # Hand: As Kh Jd Qh Td 9c 5s. top=As.
    # rest = {Kh, Jd, Qh, Td, 9c, 5s}. Suit comp: h=2(Kh,Qh), d=2(Jd,Td), c=1(9c), s=1(5s).
    # SS bots:
    #   "2" from h = {Kh, Qh}: pick (1 of d, 1 of c, 1 of s) two-at-a-time → 3 combos.
    #     dc: bot picks (Jd or Td) + 9c. mid = leftover_d + 5s = d/s not ms.
    #     ds: pick (Jd or Td) + 5s. mid = leftover_d + 9c = d/c not ms.
    #     cs: pick 9c + 5s. bot = {Kh,Qh,9c,5s}. mid = {Jd,Td} → SUITED ✓
    #       mid_high = J = 11. n_configs += 1.
    #   "2" from d = {Jd, Td}: similar.
    #     hc: pick (Kh or Qh) + 9c. mid = leftover_h + 5s = h/s not ms.
    #     hs: pick (Kh or Qh) + 5s. mid = leftover_h + 9c = h/c not ms.
    #     cs: pick 9c + 5s. bot = {Jd,Td,9c,5s}. mid = {Kh,Qh} → SUITED ✓
    #       mid_high = K = 13. n_configs += 1.
    # n_configs=2, max_mid_high = K=13.
    case5_h = hh("As", "Kh", "Qh", "Jd", "Td", "9c", "5s")
    case5_exp = (2, 13)

    cases = [
        (case1_h, "pair AA → gated", case1_exp),
        (case2_h, "rest 2+2+2 (As|2s5h6d Jh Qd Ks)", case2_exp),
        (case3_h, "rest 3+1+1+1 (As|2s3s5s Th Jd 9c)", case3_exp),
        (case4_h, "rest 2+2+1+1 (As|Kh Qd Jh Td 5s 2c)", case4_exp),
        (case5_h, "rest 2+2+1+1 var (As|Kh Qh Jd Td 9c 5s)", case5_exp),
    ]

    print("ho_v6 smoke tests:")
    all_pass = True
    for hand, desc, exp in cases:
        v1, v2 = compute_high_only_v6_features_for_hand(hand)
        actual = (v1, v2)
        ok = "✓" if actual == exp else "✗ FAIL"
        if actual != exp:
            all_pass = False
        print(f"  [{ok}] {desc:<40} actual=({v1},{v2})  exp={exp}")
    print()
    if all_pass:
        print("All smoke tests passed.")
    else:
        print("SMOKE TEST FAILED — fix before persisting to parquet.")
        sys.exit(1)
