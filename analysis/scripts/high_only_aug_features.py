"""
Session 18 — augmented features for high_only miss patterns.

Mining findings (mine_high_only_leaves.py, 2026-04-28):
  - Slice ceiling on (mode_count==3, category=='high_only') at depth=None:
    39.64% — much lower than single-pair's 74.23%. Misses are diffuse
    (top 100 of 4,176 miss-leaves cover only 24.7% of misses) consistent
    with Session 13's "opponent-dependent" finding.
  - Within the dominant top-15 miss-leaves, the recurring pattern is bot
    suit-profile under DEFAULT routing (NAIVE_104):
      top=byte[6] (highest), mid=bytes[4,5] (next 2), bot=bytes[0..3] (4 lowest).
    When bot[0..3] is 3-suited (very common when 3 of the 4 lowest cards
    share a suit), BR demotes a same-suit broadway pair from mid → bot to
    repair the bot to DS.
    Example: hand 2c 3c 6c 7d Jh Qh Ks → NAIVE bot 2c-3c-6c-7d = 3 clubs
    (NOT DS). BR routes Q-J → bot, mid = 7-6, bot = Qh-Jh-3c-2c = DS (2h+2c).

Three candidate features encode bot-suit-profile per strategic routing:

  1. default_bot_is_ds_high           (bool) — under NAIVE_104 routing
                                                 (top=byte[6], mid=(4,5),
                                                 bot=(0..3)), is bot DS (2,2)?
                                                 The single most actionable
                                                 signal: when 1, BR almost
                                                 always uses NAIVE; when 0,
                                                 BR often demotes broadway.
  2. n_mid_choices_yielding_ds_bot     (0-15)  — fix top = highest (byte[6]).
                                                 For each of the C(6,2)=15
                                                 mid-pair choices from the
                                                 remaining 6, count how many
                                                 yield a DS bot. Captures
                                                 "DS-bot is achievable by
                                                 choosing mid wisely."
  3. best_ds_bot_mid_max_rank          (0-14)  — fix top = highest. Among the
                                                 mid choices that yield DS
                                                 bot, what's the maximum
                                                 RANK of any card that can
                                                 appear in mid? 0 means no
                                                 DS-bot is achievable with
                                                 top=highest. Encodes the
                                                 "cost of DS bot in rank
                                                 sacrifice" — if max ≥ 11,
                                                 broadway can stay in mid.

The features are vacuous on non-high_only hands; we leave those rows zero.

Note on canonical hands: hands are sorted ascending by byte (rank-major,
suit-minor within rank). High_only hands have 7 distinct ranks, so byte[6]
is unambiguously the highest-rank card.
"""
from __future__ import annotations

import sys
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


def _is_ds(suits_4: np.ndarray) -> bool:
    counts = np.zeros(4, dtype=np.int8)
    for s in suits_4:
        counts[int(s)] += 1
    counts.sort()
    return counts[3] == 2 and counts[2] == 2


# Pre-compute the 15 mid-pair index combinations from the remaining-6 cards
# (after fixing top=byte[6]). Each entry is (mid_idx_a, mid_idx_b) into
# positions 0..5 (NOT positions 0..6 — the top is position 6 by convention).
_MID_PAIRS_OF_6 = list(combinations(range(6), 2))  # 15 tuples


def compute_high_only_aug_for_hand(hand: np.ndarray) -> tuple[int, int, int]:
    """Compute (default_bot_is_ds_high, n_mid_choices_yielding_ds_bot,
    best_ds_bot_mid_max_rank) for ONE 7-card high_only canonical hand.
    Caller is responsible for filtering to high_only (7 distinct ranks).

    Returns (0, 0, 0) defensively if shape mismatch.
    """
    if hand.shape[0] != 7:
        return (0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4

    # ----- Feature 1: default_bot_is_ds — NAIVE_104 routing. -----
    default_bot_suits = suits[:4]  # bytes 0..3
    default_bot_is_ds = int(_is_ds(default_bot_suits))

    # ----- Feature 2 + 3: top=byte[6] fixed, scan 15 mid-pair choices. -----
    # remaining-6 = positions 0..5; mid is 2 of these 6, bot is the OTHER 4.
    n_ds_mid = 0
    best_mid_max_rank = 0
    for (a, b) in _MID_PAIRS_OF_6:
        # bot = the 4 positions in 0..5 that are NOT (a, b).
        bot_positions = [p for p in range(6) if p != a and p != b]
        bot_suits = suits[bot_positions]
        if _is_ds(bot_suits):
            n_ds_mid += 1
            mid_max = int(max(ranks[a], ranks[b]))
            if mid_max > best_mid_max_rank:
                best_mid_max_rank = mid_max

    return (default_bot_is_ds, n_ds_mid, best_mid_max_rank)


def compute_high_only_aug_batch(hands: np.ndarray, slice_mask: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 3 augmented features over the WHOLE hands array; for rows
    not in the slice mask (i.e., not high_only), return 0.

    Args:
        hands: (N, 7) uint8 canonical hands.
        slice_mask: (N,) bool — True where hand is high_only.

    Returns: dict of three int8 arrays, length N.
    """
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)  # default_bot_is_ds_high 0/1
    b = np.zeros(N, dtype=np.int8)  # n_mid_choices_yielding_ds_bot 0-15
    c = np.zeros(N, dtype=np.int8)  # best_ds_bot_mid_max_rank 0 or 4-14
    idxs = np.where(slice_mask)[0]
    for k, i in enumerate(idxs):
        f1, f2, f3 = compute_high_only_aug_for_hand(hands[i])
        a[i] = f1
        b[i] = f2
        c[i] = f3
        if (k + 1) % 200_000 == 0:
            print(f"  augment progress: {k+1:,}/{len(idxs):,}")
    return {
        "default_bot_is_ds_high": a,
        "n_mid_choices_yielding_ds_bot": b,
        "best_ds_bot_mid_max_rank": c,
    }


if __name__ == "__main__":
    # Self-test on hand-picked cases from the high_only leaf dump (Session 18).
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    # Spot-check >=4 hand-picked cases from the leaf dump (Session 17 lesson).
    cases = [
        # Leaf-1 miss: NAIVE bot 2c-3c-6c-7d = 3 clubs (NOT DS).
        # BR routes Q-J → bot for DS bot (2h+2c). Expected: f1=0, f2>=1,
        # f3 includes some mid_max where DS-bot achievable. The (6,7) mid
        # choice is the BR; max in mid is 7. There may be higher mid-max
        # achievable with DS bot (e.g., mid = (7d, Jh) → bot = 2c,3c,6c,Qh
        # = 3c+1h, NOT DS; mid = (7d, Qh) → bot = 2c,3c,6c,Jh = 3c+1h, NOT DS).
        # So best_ds_bot_mid_max_rank should be 7.
        ("Leaf-1 miss",      ("2c","3c","6c","7d","Jh","Qh","Ks"),     0, "exp f1=0"),
        # Variant where one of the lower clubs is a diamond → bot might be DS.
        ("Leaf-1 alt-DS-bot", ("2c","3d","6c","7c","Jh","Qh","Ks"),    None, "manual check"),
        # Leaf-5 miss: top A, mid K-Q, bot J-7-6-2 (BR shape — but the
        # default bot is 2c+6c+7c+Jd = 3 clubs+1d, NOT DS). f1 should be 0.
        ("Leaf-5 miss",      ("2c","6c","7c","Jd","Qh","Kd","As"),    0, "exp f1=0"),
        # Default-DS case: bot is 2c+3d+4h+5s (rainbow, NOT DS) but with a
        # different hand structure where bot IS DS by default.
        ("Default-DS sample",("2c","3c","4d","5d","Jh","Qs","As"),    1, "bot=2c+3c+4d+5d=2c+2d → DS"),
        # Sanity: monosuit (4-of-suit cluster).
        ("Monosuit",         ("2c","3c","4c","5c","8d","Jh","As"),    0, "bot 2c+3c+4c+5c=4 clubs"),
    ]
    print(f"\n{'case':<22}{'hand':<32}{'f1':>4}{'f2':>4}{'f3':>4}  notes")
    for name, cs, exp_f1, note in cases:
        h = hh(*cs)
        f = compute_high_only_aug_for_hand(h)
        ok = "" if exp_f1 is None else (" ✓" if f[0] == exp_f1 else " ✗")
        print(f"{name:<22}{' '.join(cs):<32}{f[0]:>4}{f[1]:>4}{f[2]:>4}  {note}{ok}")
