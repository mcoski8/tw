"""
Session 74 — high_only_aug_v7_gated: 1 signed route-tradeoff comparator
for the JOINT-vs-DS_NONJOINT routing decision in the high_only zone.

H2 hypothesis (SESSION_71_V45_FEATURE_HYPOTHESES.md §6, originally
labeled H3; renumbered in S73 CURRENT_PHASE.md after H1 PARTIAL POSITIVE).

The S71 drill (drill_v44_high_only_S71.py) found a $147.59 WG STRUCTURE-
bucket leak in v44's high_only residual. H1 (ho_v6 SS+ms route quality)
captured ~$24 (16%) at v44's saturating regime (S73). The remaining
~$123 may live in the **JOINT-vs-DS_NONJOINT route trade-off** that
v44 can only "see" through pairs of features that the DT must combine
via multiple splits at saturation.

The drill's binary partition (drill_high_only_v43_threshold.py):
  JOINT_PICK    : top=max AND bot=DS AND mid suited
  DS_NONJOINT   : bot=DS but NOT (top=max AND mid suited)

H2 compresses the route trade-off into one signed scalar:

  best_JOINT_mid_high  = max(mid_high) across (top=max, DS bot, ms mid)
                         configs.  0 if no JOINT achievable.
  best_DS_NONJOINT_top = max(top_rank) across (DS bot, NOT JOINT)
                         configs.  0 if no DS_NONJOINT achievable.

  ho_v7_route_tradeoff_joint_minus_nonjoint_g
    = best_JOINT_mid_high - best_DS_NONJOINT_top

Range: theoretically -14..+14 (each component 0..14); the S71 spec
quoted -13..+13. Stored as int8.

  Negative values: DS_NONJOINT top exceeds JOINT mid_high → the
    alternative route can preserve a higher top rank than the JOINT
    route's suited-mid head. "Keep top high" is the better signal.
  Near-zero: routes are balanced.
  Positive (rare): JOINT mid_high exceeds best DS_NONJOINT top → JOINT
    route's suited mid dominates. "Take JOINT" is the better signal.
    Structurally hard to construct when max_rank=A (see notes in
    SESSION_74 design log).

All zeros for any non-high_only hand (n_pairs > 0 or n_trips > 0 or
n_quads > 0).

Why non-derivable from v44+ho_v3+ho_v4+ho_v6:
  * ho_v3_topMax_DS_ms_max_mid_high_g exposes the JOINT mid_high
    directly (== best_JOINT_mid_high). ✓
  * ho_v4_topNonMax_DS_ms_max_top_rank_g exposes max top rank for
    (DS bot, ms mid, top!=max) ONLY — a strict SUBSET of DS_NONJOINT.
    It excludes (top=max, DS bot, mid unsuited) — which CAN reach
    top=max_rank in the broad DS_NONJOINT.
  * No existing feature aggregates over the broad DS_NONJOINT
    (DS bot ∧ ¬(top=max ∧ mid_ms)). The comparator's right-hand
    operand is genuinely new.
  * Even if both operands were available, the SIGNED COMPARATOR
    compresses information that the saturating DT (depth=36 ml=1)
    cannot easily reconstruct via axis-aligned splits in 2 nodes.
    S71's stated risk: "could fall into the 'derivable in 2 splits'
    trap" — the S74 experiment falsifies or confirms this directly.

The S74 4-phase playbook (CURRENT_PHASE.md):
  Phase 1: persist + smoke (this file + persist_high_only_aug_v7_gated.py).
  Phase 2: train v47_dt at depth=36 ml=1 (regime LOCKED to v44).
  Phase 3: prefix grader — byte-identity check on non-high_only.
  Phase 4: full grader — decision at +$10/1000h ship bar.
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
    """True iff the 4-card suit multiset is exactly 2+2 (double-suited)."""
    c = Counter(suits)
    sv = sorted(c.values(), reverse=True)
    return sv == [2, 2]


def compute_high_only_v7_features_for_hand(hand: np.ndarray) -> tuple[int]:
    """Return (comparator,) for the JOINT-vs-DS_NONJOINT route trade-off.
    (0,) for any non-high_only hand or when no DS bot is achievable.

    Returns a 1-tuple for parity with other ho_v* compute_* APIs.
    """
    if hand.shape[0] != 7:
        return (0,)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 0 or n_trips != 0 or n_quads != 0:
        return (0,)

    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    max_rank = max(int_ranks)

    best_joint_mid_high = 0
    best_ds_nonjoint_top = 0

    positions = list(range(7))
    for bot_idx in combinations(positions, 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        if not _is_ds(bot_suits):
            continue
        rest = [i for i in positions if i not in bot_idx]  # 3 cards
        for top_pos in rest:
            mid_pos = [i for i in rest if i != top_pos]  # 2 cards
            top_rank = int_ranks[top_pos]
            mid_suited = int_suits[mid_pos[0]] == int_suits[mid_pos[1]]
            is_joint = (top_rank == max_rank) and mid_suited
            if is_joint:
                mid_high = max(int_ranks[mid_pos[0]], int_ranks[mid_pos[1]])
                if mid_high > best_joint_mid_high:
                    best_joint_mid_high = mid_high
            else:
                if top_rank > best_ds_nonjoint_top:
                    best_ds_nonjoint_top = top_rank

    comparator = int(best_joint_mid_high) - int(best_ds_nonjoint_top)
    return (comparator,)


def compute_high_only_v7_features_batch(hands: np.ndarray,
                                          log_every: int = 500_000
                                          ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        (v,) = compute_high_only_v7_features_for_hand(h)
        out[i] = v
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  ho_v7 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_v7_route_tradeoff_joint_minus_nonjoint_g": out,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Test 1 — non-high_only (pair AA): gated, expect 0.
    # Hand: Ac Ad Kh Qs Js Th 9d
    case1_h = hh("Ac", "Ad", "Kh", "Qs", "Js", "Th", "9d")
    case1_exp = 0
    case1_desc = "pair AA → gated"

    # Test 2 — high_only, no DS bot achievable (suit dist 4+1+1+1).
    # Hand: As Kh Qd Jc 2s 3s 4s. ranks A,K,Q,J,2,3,4 distinct.
    # Suits: s=4(As,2s,3s,4s), h=1, d=1, c=1. No DS bot: need 2+2 but
    # only the 4-suit has ≥2 cards. Comparator = 0 - 0 = 0.
    case2_h = hh("As", "Kh", "Qd", "Jc", "2s", "3s", "4s")
    case2_exp = 0
    case2_desc = "no DS bot (suits 4+1+1+1)"

    # Test 3 — JOINT not achievable, DS_NONJOINT top=A.
    # Hand: As Ks Qh Jh Td 9d 8c. ranks A,K,Q,J,T,9,8 distinct.
    # Suits: s=2(As,Ks), h=2(Qh,Jh), d=2(Td,9d), c=1(8c).
    # Non-A 6 suits (after top=A): s=1,h=2,d=2,c=1 = (2,2,1,1). Only 1
    # DS bot: 2h+2d = {Qh,Jh,Td,9d}, mid {Ks,8c} = s/c unsuited.
    # JOINT requires top=A AND mid suited — mid unsuited → JOINT=0.
    # That bot with top=A and unsuited mid IS a DS_NONJOINT config
    # (top=A=14). best_DS_NONJOINT_top = 14.
    # comparator = 0 - 14 = -14.
    case3_h = hh("As", "Ks", "Qh", "Jh", "Td", "9d", "8c")
    case3_exp = -14
    case3_desc = "JOINT=0, DS_NONJOINT top=A → -14"

    # Test 4 — JOINT mid_high=K, no top=A unsuited bot (all DS bots
    # at top=A have ms mid), DS_NONJOINT top=K via top=Kh non-A config.
    # Hand: As Kh 5h 6d 7d 8c 9c. ranks A,K,5,6,7,8,9 distinct.
    # Suits: s=1(As), h=2(Kh,5h), d=2(6d,7d), c=2(8c,9c).
    # Non-A 6 suits: h=2,d=2,c=2 = (2,2,2,0).
    # JOINT bots (top=As):
    #   2h+2d: {Kh,5h,6d,7d}, mid {8c,9c} ms (c). mid_high=9.
    #   2h+2c: {Kh,5h,8c,9c}, mid {6d,7d} ms (d). mid_high=7.
    #   2d+2c: {6d,7d,8c,9c}, mid {Kh,5h} ms (h). mid_high=K=13.
    # best_JOINT_mid_high = 13.
    # All top=A bots have ms mid → no top=A DS_NONJOINT.
    # top=Kh: rest = {As,5h,6d,7d,8c,9c}. Suits s=1,h=1,d=2,c=2. DS
    # bot 2d+2c achievable; mid {As,5h} unsuited. top=K=13 DS_NONJOINT.
    # best_DS_NONJOINT_top = 13.
    # comparator = 13 - 13 = 0.
    case4_h = hh("As", "Kh", "5h", "6d", "7d", "8c", "9c")
    case4_exp = 0
    case4_desc = "JOINT mid_high=K, DS_NONJOINT top=K → 0"

    # Test 5 — max_rank=K (not A). JOINT not achievable, DS_NONJOINT
    # top=K → comparator = -13.
    # Hand: Kc Jc Tc 5c Qh 7h 4d. ranks K,J,T,5,Q,7,4 distinct. Max=K.
    # Suits: c=4(Kc,Jc,Tc,5c), h=2(Qh,7h), d=1(4d).
    # Non-K-pos 6 (Kc removed): {Jc,Tc,5c,Qh,7h,4d}. c=3,h=2,d=1.
    # JOINT bots (top=Kc): 2c+2h ⇒ pick 2 of 3 c × 1 = 3 bots.
    #   Bot {Jc,Tc,Qh,7h}, mid {5c,4d}: c/d unsuited.
    #   Bot {Jc,5c,Qh,7h}, mid {Tc,4d}: c/d unsuited.
    #   Bot {Tc,5c,Qh,7h}, mid {Jc,4d}: c/d unsuited.
    # 2c+2d: only 1 d. 2h+2d: only 1 d. All bots unsuited mid.
    # JOINT=0. Those 3 bots are top=K=13 DS_NONJOINT (mid unsuited).
    # best_DS_NONJOINT_top = K=13.
    # comparator = 0 - 13 = -13.
    case5_h = hh("Kc", "Jc", "Tc", "5c", "Qh", "7h", "4d")
    case5_exp = -13
    case5_desc = "max=K, JOINT=0, DS_NONJOINT top=K → -13"

    cases = [
        (case1_h, case1_desc, case1_exp),
        (case2_h, case2_desc, case2_exp),
        (case3_h, case3_desc, case3_exp),
        (case4_h, case4_desc, case4_exp),
        (case5_h, case5_desc, case5_exp),
    ]

    print("ho_v7 smoke tests:")
    all_pass = True
    for hand, desc, exp in cases:
        (v,) = compute_high_only_v7_features_for_hand(hand)
        actual = v
        ok = "✓" if actual == exp else "✗ FAIL"
        if actual != exp:
            all_pass = False
        print(f"  [{ok}] {desc:<45} actual={actual:>4}  exp={exp}")
    print()
    if all_pass:
        print("All smoke tests passed.")
    else:
        print("SMOKE TEST FAILED — fix before persisting to parquet.")
        sys.exit(1)
