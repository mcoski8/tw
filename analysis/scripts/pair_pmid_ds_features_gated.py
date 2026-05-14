"""
Session 78 — H6: pair_pmid_ds_n_configs_g (single-pair gated, int8 0..5).

Counts, for single-pair hands, the number of distinct top-singleton choices
(out of the 5 non-pair singletons) such that the bot (= pair-in-mid + 4
non-top singletons) is double-suited (2+2 suit pattern). Returns 0..5.
Zero on all non-single-pair hands.

H6 lets v48_dt distinguish how many alternative PMID_DS routings exist —
information v44 lacks. v44 has `pair_r4_bot_suit_profile_g` (the suit
profile of the DEFAULT-routing bot = top=max, bot=4 lowest); it does NOT
enumerate alternative top-choices. v44's `pair_aug_v5_bot_DS_n_configs_g`
counts PBOT_DS (pair in bot) configs, not PMID_DS.

Drill target: LOW × {PMID_DS_MAXTOP, PMID_DS_NOMAXTOP} STRUCTURE cells
(18,644 hands, $52.68/1000h pair STR leak). Expected within-pair lift
$15-26/1000h, full-grid $7-12/1000h. See PAIR_S77_FEATURE_HYPOTHESES.md.
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


def compute_pair_pmid_ds_n_configs_for_hand(hand: np.ndarray) -> int:
    """Return the count of top-choices yielding 2+2 (DS) bot when pair is in mid.

    Gated to single-pair hands (n_pairs==1, n_trips==0, n_quads==0).
    Returns 0..5. Zero outside the gate.
    """
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
    sing_pos = [i for i in range(7) if int_ranks[i] != pair_rank]
    sing_suits = [int_suits[i] for i in sing_pos]
    # assert len(sing_suits) == 5

    n = 0
    for top_local in range(5):
        bot_suits = [sing_suits[k] for k in range(5) if k != top_local]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt == [2, 2]:
            n += 1
    return n


def compute_pair_pmid_ds_n_configs_for_hand_tuple(hand: np.ndarray) -> tuple[int]:
    """Tuple-returning wrapper for batch-loader symmetry with v5/v2 patterns."""
    return (compute_pair_pmid_ds_n_configs_for_hand(hand),)


def compute_pair_pmid_ds_batch(hands: np.ndarray,
                                log_every: int = 500_000) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_n = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        out_n[i] = compute_pair_pmid_ds_n_configs_for_hand(h)
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  pair_pmid_ds {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {"pair_pmid_ds_n_configs_g": out_n}


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    # Sanity tests grounded in the PMID_DS enumeration.
    cases = [
        # AA pair, suits hd. Sings: 2s, 3h, 4d, 9s, Kd.
        # PMID_DS top-choices:
        #   top=2s   bot=3h,4d,9s,Kd suits={h,d,s,d} 2+1+1 SS  ✗
        #   top=3h   bot=2s,4d,9s,Kd suits={s,d,s,d} 2+2 DS    ✓
        #   top=4d   bot=2s,3h,9s,Kd suits={s,h,s,d} 2+1+1 SS  ✗
        #   top=9s   bot=2s,3h,4d,Kd suits={s,h,d,d} 2+1+1 SS  ✗
        #   top=Kd   bot=2s,3h,4d,9s suits={s,h,d,s} 2+1+1 SS  ✗
        # → n=1
        ("2s 3h 4d 9s Kd Ah Ad", 1, "AA pair: 1 PMID_DS config (top=3h)"),
        # 33 pair, suits sh. Sings: 2s, 4d, 5h, 6d, 8c.
        #   top=2s   bot=4d,5h,6d,8c suits={d,h,d,c} 2+1+1 SS  ✗
        #   top=4d   bot=2s,5h,6d,8c suits={s,h,d,c} 1+1+1+1 RB ✗
        #   top=5h   bot=2s,4d,6d,8c suits={s,d,d,c} 2+1+1 SS  ✗
        #   top=6d   bot=2s,4d,5h,8c suits={s,d,h,c} 1+1+1+1 RB ✗
        #   top=8c   bot=2s,4d,5h,6d suits={s,d,h,d} 2+1+1 SS  ✗
        # → n=0
        ("2s 3s 3h 4d 5h 6d 8c", 0, "33 pair: 0 PMID_DS configs"),
        # 44 pair (LOW), suits cs. Sings: 2h, 3h, 5c, 6d, Ad.
        #   top=2h   bot=3h,5c,6d,Ad suits={h,c,d,d} 2+1+1 SS  ✗
        #   top=3h   bot=2h,5c,6d,Ad suits={h,c,d,d} 2+1+1 SS  ✗
        #   top=5c   bot=2h,3h,6d,Ad suits={h,h,d,d} 2+2 DS    ✓ (not maxtop)
        #   top=6d   bot=2h,3h,5c,Ad suits={h,h,c,d} 2+1+1 SS  ✗
        #   top=Ad   bot=2h,3h,5c,6d suits={h,h,c,d} 2+1+1 SS  ✗
        # → n=1, PMID_DS_NOMAXTOP cell
        ("2h 3h 4c 4s 5c 6d Ad", 1, "44 LOW pair: 1 PMID_DS, NOMAXTOP"),
        # 44 pair (LOW), suits cs. Sings: 2h, 3h, 5d, 6d, As.
        #   top=As (max)  bot=2h,3h,5d,6d suits={h,h,d,d} 2+2 DS  ✓ maxtop
        #   top=2h   bot=3h,5d,6d,As suits={h,d,d,s} 2+1+1 SS    ✗
        #   top=3h   bot=2h,5d,6d,As suits={h,d,d,s} 2+1+1 SS    ✗
        #   top=5d   bot=2h,3h,6d,As suits={h,h,d,s} 2+1+1 SS    ✗
        #   top=6d   bot=2h,3h,5d,As suits={h,h,d,s} 2+1+1 SS    ✗
        # → n=1, PMID_DS_MAXTOP cell
        ("2h 3h 4c 4s 5d 6d As", 1, "44 LOW pair: 1 PMID_DS, MAXTOP"),
        # No pair: must return 0
        ("2c 3c 4d 5h 6s 7c 8d", 0, "no pair: 0"),
        # Trips (333): must return 0
        ("3c 3d 3h 5s 7c 9d Kh", 0, "trips: 0 (gated out)"),
        # Two pair: must return 0
        ("2c 2d 5h 5s 7c 9d Kh", 0, "two pair: 0 (gated out)"),
        # Quads: must return 0
        ("4c 4d 4h 4s 7c 9d Kh", 0, "quads: 0 (gated out)"),
    ]
    print("H6 sanity tests (pair_pmid_ds_n_configs_g):")
    n_fail = 0
    for cards, expect, desc in cases:
        h = hh(*cards.split())
        got = compute_pair_pmid_ds_n_configs_for_hand(h)
        ok = "OK " if got == expect else "FAIL"
        if got != expect:
            n_fail += 1
        print(f"  [{ok}] {cards:<25} expect={expect}  got={got}  {desc}")
    if n_fail:
        print(f"\n{n_fail} failures")
        sys.exit(1)
    print("\nAll H6 sanity tests pass.")
