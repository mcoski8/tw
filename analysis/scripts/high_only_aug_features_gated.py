"""
Session 34 — high_only_aug_gated: 4 new features for the high_only category
(7 distinct ranks, no pair / trips / quads). 6th gating template instance.

high_only is the biggest UNTOUCHED lever after Session 33 (v26):
20.4% population × $2,894/1000h regret = $590/1000h share. Untouched
since v20 (Session 30).

Diagnostic (`distill_v26_high_only.py` in Session 34) walked v26's
459K-leaf tree on the 1.23M high_only hands and found:

  - ALL top miss leaves share the path
      `n_broadway in [3,4]` AND `n_broadway_in_largest_suit_g >= 2`
    i.e. suited-broadway hands with multiple broadway ranks present.
  - Stratifying those leaves by the count of broadway in the SECOND-
    largest suit produced **0.34-0.41 EV within-leaf separation**:
        leaf 545045: cand=0 reg=+0.640, cand=1 reg=+0.486 (Δ +0.154)
        leaf 578474: cand=0 reg=+0.773, cand=1 reg=+0.359 (Δ +0.414)
        leaf 545147: cand=0 reg=+0.748, cand=1 reg=+0.408 (Δ +0.340)
    v26 cannot see this axis because no feature captures broadway in
    the 2nd suit.

Four features, all gated to high_only hands (zeros elsewhere). Prefix
`ho_*_g` is unclaimed by suited (`*_g` suffix), trips_pair (`tp_*_g`),
composite (`comp_*_g`), pair (`pair_*_g`), or two_pair (`t2p_*_g`)
families.

  ho_n_broadway_in_2nd_suit_g  count of T-A in the 2nd-largest suit
                               (0..3). PRIMARY candidate from diagnostic.
  ho_n_broadway_in_3rd_suit_g  count of T-A in the 3rd-largest suit
                               (0..3). Completes the per-suit broadway
                               distribution alongside the existing
                               n_broadway_in_largest_suit_g.
  ho_connectivity_high_g       longest run of consecutive ranks within
                               broadway (T-A, with A treated as 14 only;
                               wheel is captured by n_low+connectivity).
                               (0..5)
  ho_n_broadway_pairs_adj_g    count of adjacent broadway pairs present
                               in the hand from {AK, KQ, QJ, JT}.
                               Differs from connectivity_high — KQ + JT
                               gives 2 here but only longest=2.
                               (0..4)
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


def compute_high_only_aug_gated_for_hand(hand: np.ndarray) -> tuple[int, int, int, int]:
    """Return the 4 gated features for a single 7-card hand. Zeros for
    any non-high_only hand (any pair / trip / quad).
    """
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_count: Counter[int] = Counter(int(r) for r in ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 0 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    # Per-suit broadway counts.
    bw_by_suit = [0, 0, 0, 0]
    suit_total = [0, 0, 0, 0]
    for i in range(7):
        s = int(suits[i])
        suit_total[s] += 1
        if int(ranks[i]) >= 10:
            bw_by_suit[s] += 1
    # Order suits by total card count desc, breaking ties by broadway
    # count desc so the 2nd-largest-suit feature is well-defined when
    # two suits have the same overall count.
    suit_order = sorted(
        range(4),
        key=lambda s: (-suit_total[s], -bw_by_suit[s], s),
    )
    n_bw_2nd = bw_by_suit[suit_order[1]]
    n_bw_3rd = bw_by_suit[suit_order[2]]

    # Connectivity within broadway only (T..A, ranks 10..14).
    # Treat A only as high (rank 14); the wheel A-2-3-4-5 is already
    # encoded via base `connectivity` + `n_low`.
    presence = [0, 0, 0, 0, 0]  # ranks 10,11,12,13,14
    for i in range(7):
        r = int(ranks[i])
        if 10 <= r <= 14:
            presence[r - 10] = 1
    longest = 0
    cur = 0
    for v in presence:
        cur = cur + 1 if v == 1 else 0
        if cur > longest:
            longest = cur

    # Adjacent-broadway-pair count: AK, KQ, QJ, JT.
    # presence[r-10] == 1 means rank r present.
    pairs_adj = 0
    for j in range(4):  # j=0..3 → adjacent pairs (T,J),(J,Q),(Q,K),(K,A)
        if presence[j] == 1 and presence[j + 1] == 1:
            pairs_adj += 1

    return (
        int(n_bw_2nd),
        int(n_bw_3rd),
        int(longest),
        int(pairs_adj),
    )


def compute_high_only_aug_gated_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_2nd = np.zeros(N, dtype=np.int8)
    out_3rd = np.zeros(N, dtype=np.int8)
    out_conn = np.zeros(N, dtype=np.int8)
    out_pa = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_high_only_aug_gated_for_hand(h)
        out_2nd[i] = v1
        out_3rd[i] = v2
        out_conn[i] = v3
        out_pa[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  high_only_aug_gated {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_n_broadway_in_2nd_suit_g": out_2nd,
        "ho_n_broadway_in_3rd_suit_g": out_3rd,
        "ho_connectivity_high_g": out_conn,
        "ho_n_broadway_pairs_adj_g": out_pa,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        # (hand, expected (n_bw_2nd, n_bw_3rd, conn_high, pairs_adj), label)
        ("Ac Kc Qc Jc Tc 5d 2h",  None,  "Royal-flush draw cccccdh: bw concentrated in c"),
        ("Ac Kd Qc Jd Tc 5d 2h",  None,  "Broadway 2-2 split between c and d"),
        ("Ac Kd Qh Js Tc 5d 2h",  None,  "Broadway in all 4 suits"),
        ("Ac Kc 8d 7d 5h 4h 2s",  None,  "Only AK broadway, suited"),
        ("Ac Kd 8c 7d 5h 4h 2s",  None,  "AK off-suit, no broadway connectors"),
        ("Ac Qc Jc 9d 8d 5h 2s",  None,  "AQJ suited, no K → conn=2 (QJ), bw_2nd=0"),
        ("Ac Ad Kh Qs Js Th 9d",  (0,0,0,0), "high pair AA — should be all zeros"),
        ("Ac Ad As Kh Kd Qs Js",  (0,0,0,0), "trips_two_pair — should be all zeros"),
        ("2c 3d 4h 5s 6c 7h 9d",  (0,0,0,0), "all low — high_only but n_broadway=0"),
        ("Ac Kc Qd Jd 8h 5s 2c",  None,  "AK suited c, QJ suited d → 2nd suit has 2 bw"),
    ]
    print(f"{'hand':<32}{'label':<60}-> bw2  bw3  conn  pairs_adj")
    for s, expected, label in cases:
        feats = compute_high_only_aug_gated_for_hand(hh(*s.split()))
        ok = "" if expected is None else (" OK" if feats == expected else f" EXPECTED {expected}")
        print(f"{s:<32}{label:<60}-> {feats[0]:>3}  {feats[1]:>3}  {feats[2]:>3}  {feats[3]:>3}{ok}")
