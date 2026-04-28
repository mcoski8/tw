"""
Session 19 — augmented features for two_pair miss patterns.

Mining findings (mine_two_pair_leaves.py, 2026-04-28):
  - Slice ceiling on (mode_count==3, category=='two_pair') at depth=None:
    79.47% / 39,677 leaves on 675K hands. Slice misses: 138,693 (20.53%).
  - Miss concentration is DIFFUSE (top-10 leaves = 0.5%; top-100 = 3.4%) —
    much flatter than single-pair/high_only. The structural pattern across
    the dominant top miss-leaves is "high-pair-on-mid (DT default,
    settings 14/44) vs high-pair-on-bot (BR swap)" — picking which of the
    two pairs goes to mid vs bot, plus the singleton-on-top choice.
  - The discriminator within each leaf is suit-coupling that the 27 baseline
    features cannot expose: per-routing bot suit profile.

Three candidate features encode bot-suit-profile per intact-pair routing.
The "intact-pair routings" abstraction is: mid holds one full pair (high
or low), top holds one of the 3 singletons, bot holds the other pair +
the remaining 2 singletons. There are (2 mid-pair choices) × (3 top
singleton choices) = 6 such routings.

  1. default_bot_is_ds_tp                      (bool) — under (mid=high-pair,
                                                           top=highest-singleton,
                                                           bot=low-pair+2-lowest-
                                                           singletons), is bot
                                                           DS (2,2)?
  2. n_routings_yielding_ds_bot_tp             (0-6) — over the 6 intact-pair
                                                       routings, count those
                                                       yielding DS bot.
  3. swap_high_pair_to_bot_ds_compatible       (bool) — among the DS-bot
                                                       routings, does ANY
                                                       have HIGH pair on bot
                                                       (i.e., mid=low-pair)?

Vacuous on non-two_pair hands (early-return on n_pairs != 2).
"""
from __future__ import annotations

import sys
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


def _decompose_two_pair(hand: np.ndarray):
    """Return (high_pair_positions, low_pair_positions, singleton_positions_desc)
    or None if hand is not two_pair shape (n_pairs == 2, no trips/quads,
    3 distinct singletons → 7 cards total).
    """
    if hand.shape[0] != 7:
        return None
    ranks = (hand // 4) + 2
    rank_to_positions: dict[int, list[int]] = {}
    for i in range(7):
        rank_to_positions.setdefault(int(ranks[i]), []).append(i)

    pairs: list[tuple[int, list[int]]] = []
    singles: list[tuple[int, int]] = []
    for r, positions in rank_to_positions.items():
        if len(positions) == 2:
            pairs.append((r, positions))
        elif len(positions) == 1:
            singles.append((r, positions[0]))
        else:
            return None  # trips or quads — not two_pair
    if len(pairs) != 2 or len(singles) != 3:
        return None
    pairs.sort(reverse=True)  # highest-rank pair first
    high_pair_positions = pairs[0][1]
    low_pair_positions = pairs[1][1]
    singles.sort(reverse=True)  # highest singleton first
    singleton_positions_desc = [p for (_, p) in singles]
    return high_pair_positions, low_pair_positions, singleton_positions_desc


def compute_two_pair_aug_for_hand(hand: np.ndarray) -> tuple[int, int, int]:
    """Compute (default_bot_is_ds_tp, n_routings_yielding_ds_bot_tp,
    swap_high_pair_to_bot_ds_compatible) for ONE 7-card two_pair hand.
    Returns (0,0,0) if hand is not two_pair shape.
    """
    decomp = _decompose_two_pair(hand)
    if decomp is None:
        return (0, 0, 0)
    high_pair, low_pair, sing_desc = decomp
    suits = hand % 4

    # Iterate all 6 intact-pair routings: (mid_pair ∈ {high, low}) × (top ∈ 3 singletons).
    # Bot = the other pair (4 cards = pair_other_pos + 2 singletons not on top).
    n_ds = 0
    swap_ds = 0  # 1 if any DS routing has HIGH pair on bot (mid=low_pair)
    default_is_ds = 0
    for mid_choice, mid_positions, bot_pair_positions in (
        ("high", high_pair, low_pair),
        ("low", low_pair, high_pair),
    ):
        for top_idx in range(3):  # 0=highest sing, 1=mid sing, 2=lowest sing
            bot_singletons = [sing_desc[j] for j in range(3) if j != top_idx]
            bot_positions = bot_pair_positions + bot_singletons
            if _is_ds(suits[bot_positions]):
                n_ds += 1
                if mid_choice == "low":
                    swap_ds = 1
            # The "default" routing: mid=high-pair, top=highest-singleton, bot=low-pair+2-lowest.
            if mid_choice == "high" and top_idx == 0:
                default_is_ds = int(_is_ds(suits[bot_positions]))

    return (default_is_ds, n_ds, swap_ds)


def compute_two_pair_aug_batch(hands: np.ndarray, slice_mask: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 3 augmented features over the WHOLE hands array; rows not
    in the slice mask (i.e., not two_pair) return 0.

    Args:
        hands: (N, 7) uint8 canonical hands.
        slice_mask: (N,) bool — True where hand is two_pair.

    Returns: dict of three int8 arrays, length N.
    """
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)  # default_bot_is_ds_tp 0/1
    b = np.zeros(N, dtype=np.int8)  # n_routings_yielding_ds_bot_tp 0-6
    c = np.zeros(N, dtype=np.int8)  # swap_high_pair_to_bot_ds_compatible 0/1
    idxs = np.where(slice_mask)[0]
    for k, i in enumerate(idxs):
        f1, f2, f3 = compute_two_pair_aug_for_hand(hands[i])
        a[i] = f1
        b[i] = f2
        c[i] = f3
        if (k + 1) % 200_000 == 0:
            print(f"  augment progress: {k+1:,}/{len(idxs):,}")
    return {
        "default_bot_is_ds_tp": a,
        "n_routings_yielding_ds_bot_tp": b,
        "swap_high_pair_to_bot_ds_compatible": c,
    }


if __name__ == "__main__":
    # Spot-check 5+ hand-picked cases from the leaf dump (Session 17/18 lesson).
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    # Hand-picked cases from /tmp/two_pair_leaves.log + manually constructed defaults.
    cases = [
        # Leaf-1 miss: AA(c,d) + KK(h,s) + Jd 6c 2c. Default mid=AA top=J bot=KK62
        # → suits hscc → NOT DS. Two DS routings exist (mid=KK, top=6 or top=2)
        # — both with HIGH pair (AA) on bot. Expect (0, 2, 1).
        ("Leaf-1 miss",
            ("2c","6c","Jd","Kh","Ks","Ac","Ad"),
            (0, 2, 1)),
        # Leaf-2 miss: AA(h,s) + KK(c,h) + Td 6c 2c. None of the 6 routings yield
        # DS bot. Expect (0, 0, 0).
        ("Leaf-2 miss",
            ("2c","6c","Td","Kc","Kh","Ah","As"),
            (0, 0, 0)),
        # Leaf-3 miss: KK(c,s) + 99(d,h) + 8d 3c 2c. None DS. Expect (0, 0, 0).
        ("Leaf-3 miss",
            ("2c","3c","8d","9d","9h","Kc","Ks"),
            (0, 0, 0)),
        # Default-IS-DS construction: AA(c,d) + KK(c,d) + 8h 5d 2c.
        # mid=AA, top=8h, bot=KK+5d+2c = Kc,Kd,5d,2c → cdhc... wait Kc,Kd,5d,2c
        # = c,d,d,c → 2c+2d → DS. ✓
        # mid=KK, top=8h, bot=AA+5d+2c = Ac,Ad,5d,2c → c,d,d,c → DS. ✓
        # Other 4 routings: not DS (the 8h breaks the suit balance).
        # Expect (1, 2, 1).
        ("Default-IS-DS",
            ("2c","5d","8h","Kc","Kd","Ac","Ad"),
            (1, 2, 1)),
        # Monosuit sanity: AA(c,d) + KK(c,h) + 2c 3c 5c (3 of clubs).
        # All routings: bot has 3+ clubs → never DS. Expect (0, 0, 0).
        ("Monosuit",
            ("2c","3c","5c","Kc","Kh","Ac","Ad"),
            (0, 0, 0)),
        # AA(c,d) + KK(h,s) + 2c 3d 5h. Default routing (mid=AA, top=5h):
        # bot=KK+3d+2c = h,s,d,c → rainbow → NOT DS. Swap routing
        # (mid=KK, top=5h): bot=AA+3d+2c = c,d,d,c → 2c+2d → DS. ✓
        # Only one DS-bot routing, with HIGH pair on bot. Expect (0, 1, 1).
        ("Swap-only-DS",
            ("2c","3d","5h","Kh","Ks","Ac","Ad"),
            (0, 1, 1)),
    ]
    print(f"\n{'case':<22}{'hand':<32}{'f':>10}{'  exp':>8}  {'note'}")
    pass_count = 0
    for name, cs, exp in cases:
        h = hh(*cs)
        f = compute_two_pair_aug_for_hand(h)
        ok = "✓" if f == exp else "✗"
        if f == exp:
            pass_count += 1
        print(f"{name:<22}{' '.join(cs):<32}{str(f):>10}  {str(exp):>10}  {ok}")
    print(f"\n{pass_count}/{len(cases)} spot-checks pass.")
