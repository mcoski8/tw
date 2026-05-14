"""
Session 78 — H8: pair_low_pmid_safety_g (LOW-pair-only gated, int8 0..5).

Categorical encoding of the S66 6-cell structural taxonomy, gated to single-
pair hands with pair_rank ∈ {2,3,4,5,6,7} (the "LOW" tier). Zero elsewhere.

Encoding:
  0 — not LOW pair (not single-pair OR pair_rank >= 8)
  1 — LOW pair AND cell == PMID_DS_MAXTOP
  2 — LOW pair AND cell == PMID_DS_NOMAXTOP
  3 — LOW pair AND cell == PMID_SS_MAXTOP
  4 — LOW pair AND cell == PMID_OTHER
  5 — LOW pair AND cell ∈ {PBOT_DS_JOINT, PBOT_DS_PARTIAL}

Levels 1-4 are the v44-over-routes-to-SPLIT/PBOT cells (oracle keeps PMID).
Level 5 is the reverse-direction exception (v44 may stay PMID, oracle
routes to PBOT_DS). Levels are NOT linearly EV-ordered — they are a clean
categorical the DT can split on directly.

NEVER ship H8 standalone: cell 5 (PBOT_DS_PARTIAL) requires H6+H7 to give
the DT the kicker_max-alignment discriminator. See
PAIR_S77_FEATURE_HYPOTHESES.md and the S77 drill data.

Expected within-pair lift $22-35/1000h, full-grid $10-17/1000h.
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)


LEVEL_NOT_LOW_PAIR    = 0
LEVEL_PMID_DS_MAXTOP  = 1
LEVEL_PMID_DS_NOMAXTOP = 2
LEVEL_PMID_SS_MAXTOP  = 3
LEVEL_PMID_OTHER      = 4
LEVEL_PBOT_DS         = 5


def _pair_cell_for_low(int_ranks: list[int], int_suits: list[int],
                        pair_rank: int) -> str:
    """Compute the S66 cell label inline (no imports from drill files).

    Mirrors compute_pair_structural+cell_for_pair_hand from S66 with priority:
      PBOT_DS_JOINT  : n_PBOT_DS_w_msmid_maxtop > 0
      PBOT_DS_PARTIAL: n_PBOT_DS > 0 (but no msmid+maxtop)
      PMID_DS_MAXTOP : n_PMID_DS_w_maxtop > 0
      PMID_DS_NOMAXTOP: n_PMID_DS > 0
      PMID_SS_MAXTOP : n_PMID_SS_w_maxtop > 0
      PMID_OTHER     : otherwise
    """
    pair_pos = [i for i in range(7) if int_ranks[i] == pair_rank]
    pair_suits = (int_suits[pair_pos[0]], int_suits[pair_pos[1]])
    sa, sb = pair_suits  # distinct by deck construction

    sing_pos = [i for i in range(7) if i not in pair_pos]
    sing_ranks = [int_ranks[i] for i in sing_pos]
    sing_suits = [int_suits[i] for i in sing_pos]
    max_sing_rank = max(sing_ranks)
    max_sing_local = sing_ranks.index(max_sing_rank)

    # PBOT_DS: bot = (pair, sing_a, sing_b) with one each of pair_suits.
    sing_by_a = [k for k, s in enumerate(sing_suits) if s == sa]
    sing_by_b = [k for k, s in enumerate(sing_suits) if s == sb]
    n_PBOT_DS = 0
    n_PBOT_DS_w_msmid_maxtop = 0
    for ka in sing_by_a:
        for kb in sing_by_b:
            if ka == kb:
                continue
            n_PBOT_DS += 1
            # remaining 3 singletons; top must be max_sing AND the other 2
            # singletons must share a suit (ms_mid).
            remaining = [k for k in range(5) if k != ka and k != kb]
            if max_sing_local not in remaining:
                continue
            mid_locals = [k for k in remaining if k != max_sing_local]
            if sing_suits[mid_locals[0]] == sing_suits[mid_locals[1]]:
                n_PBOT_DS_w_msmid_maxtop += 1

    if n_PBOT_DS_w_msmid_maxtop > 0:
        return "PBOT_DS_JOINT"
    if n_PBOT_DS > 0:
        return "PBOT_DS_PARTIAL"

    # PMID: enumerate top_local; bot = 4 of 5 singletons.
    n_PMID_DS = 0
    n_PMID_DS_w_maxtop = 0
    n_PMID_SS_w_maxtop = 0
    for top_local in range(5):
        bot_suits = [sing_suits[k] for k in range(5) if k != top_local]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        is_DS = (cnt == [2, 2])
        is_SS = (cnt == [2, 1, 1])
        if is_DS:
            n_PMID_DS += 1
            if top_local == max_sing_local:
                n_PMID_DS_w_maxtop += 1
        if is_SS and top_local == max_sing_local:
            n_PMID_SS_w_maxtop += 1

    if n_PMID_DS_w_maxtop > 0:
        return "PMID_DS_MAXTOP"
    if n_PMID_DS > 0:
        return "PMID_DS_NOMAXTOP"
    if n_PMID_SS_w_maxtop > 0:
        return "PMID_SS_MAXTOP"
    return "PMID_OTHER"


_CELL_TO_LEVEL = {
    "PMID_DS_MAXTOP":   LEVEL_PMID_DS_MAXTOP,
    "PMID_DS_NOMAXTOP": LEVEL_PMID_DS_NOMAXTOP,
    "PMID_SS_MAXTOP":   LEVEL_PMID_SS_MAXTOP,
    "PMID_OTHER":       LEVEL_PMID_OTHER,
    "PBOT_DS_JOINT":    LEVEL_PBOT_DS,
    "PBOT_DS_PARTIAL":  LEVEL_PBOT_DS,
}


def compute_pair_low_pmid_safety_for_hand(hand: np.ndarray) -> int:
    """Return int8 0..5 per H8 definition. Gated to LOW single-pair hands."""
    if hand.shape[0] != 7:
        return 0
    ranks = (hand // 4) + 2
    suits = hand % 4
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    rc = Counter(int_ranks)
    counts = list(rc.values())
    n_pairs = sum(1 for c in counts if c == 2)
    n_trips = sum(1 for c in counts if c == 3)
    n_quads = sum(1 for c in counts if c == 4)
    if n_pairs != 1 or n_trips != 0 or n_quads != 0:
        return 0

    pair_rank = next(r for r, c in rc.items() if c == 2)
    if pair_rank >= 8:
        return 0  # not LOW

    cell = _pair_cell_for_low(int_ranks, int_suits, pair_rank)
    return _CELL_TO_LEVEL[cell]


def compute_pair_low_pmid_safety_batch(hands: np.ndarray,
                                          log_every: int = 500_000
                                          ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        out[i] = compute_pair_low_pmid_safety_for_hand(h)
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_low_safety {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {"pair_low_pmid_safety_g": out}


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Sanity tests (worked out by hand from PAIR_S77_FEATURE_HYPOTHESES.md
    # and the S66 cell taxonomy).
    cases = [
        # 33 LOW, suits {s,h}. Sings 2s,4d,5h,6d,8c. max_sing=8c.
        #   PBOT_DS: ka in s-sings={2s}, kb in h-sings={5h}. → n_PBOT_DS=1
        #     remaining={4d,6d,8c}, max_local=8c is in it; mid_locals={4d,6d} both d
        #     → n_PBOT_DS_w_msmid_maxtop=1 → cell = PBOT_DS_JOINT
        # → level 5
        ("2s 3s 3h 4d 5h 6d 8c", 5, "33 LOW → PBOT_DS_JOINT (level 5)"),
        # 44 LOW, suits {c,s}. Sings 2h,3h,5c,6d,Ad. PBOT_DS: ka∈c={5c},kb∈s={}
        # → n_PBOT_DS=0. PMID_DS: only top=5c gives DS bot. Not maxtop.
        # → cell = PMID_DS_NOMAXTOP → level 2
        ("2h 3h 4c 4s 5c 6d Ad", 2, "44 LOW → PMID_DS_NOMAXTOP (level 2)"),
        # 44 LOW, suits {c,s}. Sings 2h,3h,5d,6d,As. PBOT_DS: ka∈c={},kb∈s={As}
        # → n_PBOT_DS=0. PMID_DS: top=As(max) yields 2+2 DS → maxtop.
        # → cell = PMID_DS_MAXTOP → level 1
        ("2h 3h 4c 4s 5d 6d As", 1, "44 LOW → PMID_DS_MAXTOP (level 1)"),
        # 44 LOW, suits {c,s}. Sings 2h,3h,5c,6d,Ah. PBOT_DS: ka∈c={5c},kb∈s={}
        # → n_PBOT_DS=0.
        # PMID_DS top-choices:
        #   top=2h bot=3h,5c,6d,Ah suits=h,c,d,h → 2+1+1 SS
        #   top=3h bot=2h,5c,6d,Ah suits=h,c,d,h → 2+1+1 SS
        #   top=5c bot=2h,3h,6d,Ah suits=h,h,d,h → 3+1
        #   top=6d bot=2h,3h,5c,Ah suits=h,h,c,h → 3+1
        #   top=Ah(max) bot=2h,3h,5c,6d suits=h,h,c,d → 2+1+1 SS
        # → n_PMID_DS=0, n_PMID_SS_w_maxtop=1 (top=Ah is SS bot)
        # → cell = PMID_SS_MAXTOP → level 3
        ("2h 3h 4c 4s 5c 6d Ah", 3, "44 LOW → PMID_SS_MAXTOP (level 3)"),
        # 55 LOW, suits {c,d}. Sings 2h,3h,4h,Ks,Ac. PBOT_DS: ka∈c={Ac},kb∈d={}
        # → n_PBOT_DS=0.
        # PMID_DS top-choices:
        #   top=2h bot=3h,4h,Ks,Ac s={h,h,s,c} 2+1+1 SS
        #   top=3h bot=2h,4h,Ks,Ac s={h,h,s,c} 2+1+1 SS
        #   top=4h bot=2h,3h,Ks,Ac s={h,h,s,c} 2+1+1 SS
        #   top=Ks bot=2h,3h,4h,Ac s={h,h,h,c} 3+1
        #   top=Ac(max) bot=2h,3h,4h,Ks s={h,h,h,s} 3+1
        # → n_PMID_DS=0, n_PMID_SS_w_maxtop=0 (top=Ac is 3+1, not SS)
        # → cell = PMID_OTHER → level 4
        ("2h 3h 4h 5c 5d Ks Ac", 4, "55 LOW → PMID_OTHER (level 4)"),
        # AA pair (HIGH) — H8 gated to LOW → 0
        ("2s 3h 4d 9s Kd Ah Ad", 0, "AA HIGH pair: 0 (not LOW)"),
        # 88 MID pair → 0
        ("2s 3s 4d 5c 7d 8c 8d", 0, "88 MID pair: 0 (not LOW)"),
        # TT MID pair → 0
        ("2c 3d 4h 5s 7c Tc Td", 0, "TT MID pair: 0 (not LOW)"),
        # No pair → 0
        ("2c 3c 4d 5h 6s 7c 8d", 0, "no pair: 0"),
        # Trips → 0
        ("3c 3d 3h 5s 7c 9d Kh", 0, "trips: 0 (gated)"),
        # Two pair → 0
        ("2c 2d 5h 5s 7c 9d Kh", 0, "two pair: 0 (gated)"),
        # Quads → 0
        ("4c 4d 4h 4s 7c 9d Kh", 0, "quads: 0 (gated)"),
    ]
    print("H8 sanity tests (pair_low_pmid_safety_g):")
    n_fail = 0
    for cards, expect, desc in cases:
        h = hh(*cards.split())
        got = compute_pair_low_pmid_safety_for_hand(h)
        ok = "OK " if got == expect else "FAIL"
        if got != expect:
            n_fail += 1
        print(f"  [{ok}] {cards:<25} expect={expect}  got={got}  {desc}")
    if n_fail:
        print(f"\n{n_fail} failures")
        sys.exit(1)
    print("\nAll H8 sanity tests pass.")
