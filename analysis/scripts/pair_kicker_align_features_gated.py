"""
Session 78 — H7: pair_kicker_max_in_pair_suit_g (single-pair gated, bool 0/1).

For single-pair hands: 1 iff the suit of the highest-rank non-pair card
(the "kicker_max") is one of the two pair-suits. Zero on all non-single-pair
hands.

H7 isolates a 1-bit signal v44 cannot derive cleanly: v44 has
`pair_kickers_in_pair_suit_max_g` / `_min_g` which COUNT how many kickers
sit in each pair-suit, but not WHICH RANK kicker does. The drill (S77,
P_S77_OUT_4) showed kicker_max-in-pair-suits running cleanly in opposite
directions across PMID-target vs PBOT-target cells:

  * LOW × PMID_DS_NOMAXTOP STR: 32% TRUE / 68% FALSE
  * LOW × PMID_DS_MAXTOP   STR: 34% TRUE / 66% FALSE
  * LOW × PBOT_DS_PARTIAL  STR: 70% TRUE / 30% FALSE  (reverse direction)

Expected within-pair lift $14-21/1000h, full-grid $5-10/1000h. See
PAIR_S77_FEATURE_HYPOTHESES.md.
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


def compute_pair_kicker_max_in_pair_suit_for_hand(hand: np.ndarray) -> int:
    """Return 1 if kicker_max's suit is in pair_suits, else 0. Gated."""
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
    pair_pos = [i for i in range(7) if int_ranks[i] == pair_rank]
    pair_suits = {int_suits[pair_pos[0]], int_suits[pair_pos[1]]}
    sing_pos = [i for i in range(7) if i not in pair_pos]
    # max-rank singleton
    max_sing_local = 0
    max_sing_rank = int_ranks[sing_pos[0]]
    for k in range(1, len(sing_pos)):
        r = int_ranks[sing_pos[k]]
        if r > max_sing_rank:
            max_sing_rank = r
            max_sing_local = k
    max_sing_suit = int_suits[sing_pos[max_sing_local]]
    return 1 if max_sing_suit in pair_suits else 0


def compute_pair_kicker_align_batch(hands: np.ndarray,
                                      log_every: int = 500_000
                                      ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        out[i] = compute_pair_kicker_max_in_pair_suit_for_hand(h)
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_kicker_align {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {"pair_kicker_max_in_pair_suit_g": out}


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    cases = [
        # AA pair, pair_suits={h,d}. Sings={2s,3h,4d,9s,Kd}. kicker_max=Kd (suit d).
        # d in {h,d} → 1
        ("2s 3h 4d 9s Kd Ah Ad", 1, "AA pair: Kd kicker_max, suit d in pair_suits {h,d}"),
        # 33 pair, pair_suits={s,h}. Sings={2s,4d,5h,6d,8c}. kicker_max=8c (suit c).
        # c not in {s,h} → 0
        ("2s 3s 3h 4d 5h 6d 8c", 0, "33 pair: 8c kicker_max, suit c not in pair_suits {s,h}"),
        # 44 pair, pair_suits={c,s}. Sings={2h,3h,5c,6d,Ad}. kicker_max=Ad (suit d).
        # d not in {c,s} → 0
        ("2h 3h 4c 4s 5c 6d Ad", 0, "44 pair: Ad kicker_max, suit d not in pair_suits {c,s}"),
        # 44 pair, pair_suits={c,s}. Sings={2h,3h,5d,6d,As}. kicker_max=As (suit s).
        # s in {c,s} → 1
        ("2h 3h 4c 4s 5d 6d As", 1, "44 pair: As kicker_max, suit s in pair_suits {c,s}"),
        # 77 pair, pair_suits={c,h}. Sings={2s,4s,9h,Td,Kh}. kicker_max=Kh (suit h).
        # h in {c,h} → 1
        ("2s 4s 7c 7h 9h Td Kh", 1, "77 pair: Kh kicker_max, suit h in pair_suits {c,h}"),
        # No pair: 0
        ("2c 3c 4d 5h 6s 7c 8d", 0, "no pair: 0"),
        # Trips
        ("3c 3d 3h 5s 7c 9d Kh", 0, "trips: 0 (gated)"),
        # Two pair
        ("2c 2d 5h 5s 7c 9d Kh", 0, "two pair: 0 (gated)"),
        # Quads
        ("4c 4d 4h 4s 7c 9d Kh", 0, "quads: 0 (gated)"),
    ]
    print("H7 sanity tests (pair_kicker_max_in_pair_suit_g):")
    n_fail = 0
    for cards, expect, desc in cases:
        h = hh(*cards.split())
        got = compute_pair_kicker_max_in_pair_suit_for_hand(h)
        ok = "OK " if got == expect else "FAIL"
        if got != expect:
            n_fail += 1
        print(f"  [{ok}] {cards:<25} expect={expect}  got={got}  {desc}")
    if n_fail:
        print(f"\n{n_fail} failures")
        sys.exit(1)
    print("\nAll H7 sanity tests pass.")
