"""
Session 17 — augmented features for single-pair miss patterns.

Mining findings (mine_pair_leaves.py, 2026-04-27):
  - Slice ceiling on (mode_count==3, category=='pair') at depth=None: 74.23%.
  - Misses concentrate around bot-suit-profile decisions the current 27
    features cannot see. The features expose 7-card suit profile (suit_max,
    suit_2nd, ...) but NOT the suit profile of the SPECIFIC 4 cards that
    end up in the bot under each routing.
  - Two recurring patterns across the top miss-leaves:
      A. v3-default bot has a 3-of-a-suit problem → BR moves a non-default
         singleton to top to repair the bot (top=lowest or middle singleton).
      B. Low pair + 2 high singletons + DS-feasible-on-pair-route → BR
         routes pair→bot, mid=top-2 singletons.

Three candidate features encode bot-suit-profile per strategic routing:
  1. default_bot_is_ds              (bool) — under v3-default routing
                                              (mid=pair, top=highest singleton,
                                              bot=4 lowest non-pair cards),
                                              is the bot double-suited (2,2)?
                                              The single most actionable signal.
  2. n_top_choices_yielding_ds_bot   (0-5) — out of the 5 non-pair singleton
                                              positions, how many yield a
                                              DS bot if used as top while
                                              the pair stays in mid. Captures
                                              "bot can be repaired by moving
                                              a non-default singleton to top".
  3. pair_to_bot_alt_is_ds          (bool) — under alternative routing
                                              (pair→bot, mid=top-2 singletons,
                                              top=3rd-highest singleton,
                                              bot=pair+2 lowest singletons),
                                              is the bot DS?

The features are vacuous on non-pair hands; we leave those rows zero.
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


def _hand_decompose_simple(hand: np.ndarray):
    """Light decomposition: ranks, suits, list of non-pair singleton positions
    (sorted by rank descending), pair positions. Faster than encode_rules.hand_decompose
    because we don't need quads/trips for the single-pair slice (caller has already
    filtered to category=='pair' which means n_pairs==1 AND n_trips==0 AND n_quads==0).
    """
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_to_positions: dict[int, list[int]] = {}
    for i in range(7):
        rank_to_positions.setdefault(int(ranks[i]), []).append(i)
    pair_positions: list[int] = []
    singletons_desc: list[tuple[int, int]] = []
    for r, positions in rank_to_positions.items():
        if len(positions) == 2:
            pair_positions = positions
        else:
            singletons_desc.append((r, positions[0]))
    singletons_desc.sort(reverse=True)
    return ranks, suits, pair_positions, singletons_desc


def _suit_max_2nd(suits_4: np.ndarray) -> tuple[int, int]:
    """Return (suit_max, suit_2nd) for a length-4 suits array."""
    counts = np.zeros(4, dtype=np.int8)
    for s in suits_4:
        counts[int(s)] += 1
    counts.sort()
    return int(counts[3]), int(counts[2])


def _is_ds(suits_4: np.ndarray) -> bool:
    smax, s2nd = _suit_max_2nd(suits_4)
    return smax == 2 and s2nd == 2


def compute_pair_aug_for_hand(hand: np.ndarray) -> tuple[int, int, int]:
    """Compute (default_bot_is_ds, n_top_choices_yielding_ds_bot,
    pair_to_bot_alt_is_ds) for ONE 7-card hand assumed to be a single-pair
    hand (n_pairs==1, no trips, no quads). Returns (0,0,0) defensive on shape mismatch.
    """
    ranks, suits, pair_pos, sing_desc = _hand_decompose_simple(hand)
    if len(pair_pos) != 2 or len(sing_desc) != 5:
        return (0, 0, 0)

    sing_positions = [p for (_, p) in sing_desc]  # length 5, sing_positions[0] is highest-rank

    # ----- Feature 1: is the v3-default bot double-suited? -----
    # Default routing: mid=pair, top=highest singleton, bot=4 lowest non-pair cards.
    bot_default_positions = sing_positions[1:]
    default_bot_is_ds = int(_is_ds(suits[bot_default_positions]))

    # ----- Feature 2: count of top-choices (under pair-on-mid) yielding DS bot. -----
    n_ds = 0
    for k in range(5):
        bot_positions = [sing_positions[j] for j in range(5) if j != k]
        if _is_ds(suits[bot_positions]):
            n_ds += 1

    # ----- Feature 3: alternative routing (pair → bot) — is the bot DS? -----
    # mid = top-2 singletons; top = 3rd-highest singleton; bot = pair + 2 lowest singletons.
    used_alt = {sing_positions[0], sing_positions[1], sing_positions[2]}
    bot_alt_positions = [p for p in range(7) if p not in used_alt]
    pair_to_bot_alt_is_ds = int(_is_ds(suits[bot_alt_positions]))

    return (default_bot_is_ds, n_ds, pair_to_bot_alt_is_ds)


def compute_pair_aug_batch(hands: np.ndarray, slice_mask: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 3 augmented features over the WHOLE hands array; for rows
    not in the slice mask (i.e., not single-pair), return 0.

    Args:
        hands: (N, 7) uint8 canonical hands.
        slice_mask: (N,) bool — True where hand is single-pair.

    Returns: dict of three int8 arrays, length N.
    """
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)  # default_bot_is_ds 0/1
    b = np.zeros(N, dtype=np.int8)  # n_top_choices_yielding_ds_bot 0-5
    c = np.zeros(N, dtype=np.int8)  # pair_to_bot_alt_is_ds 0/1
    idxs = np.where(slice_mask)[0]
    for k, i in enumerate(idxs):
        f1, f2, f3 = compute_pair_aug_for_hand(hands[i])
        a[i] = f1
        b[i] = f2
        c[i] = f3
        if (k + 1) % 200_000 == 0:
            print(f"  augment progress: {k+1:,}/{len(idxs):,}")
    return {
        "default_bot_is_ds": a,
        "n_top_choices_yielding_ds_bot": b,
        "pair_to_bot_alt_is_ds": c,
    }


if __name__ == "__main__":
    # Self-test on a few hands chosen from the leaf dump (Session 17 mining).
    import pyarrow.parquet as pq
    from tw_analysis import read_canonical_hands

    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    hands_all = canonical.hands
    df = pq.read_table(ROOT / "data" / "feature_table.parquet",
                       columns=["category", "mode_count"]).to_pandas()
    mask = (df["category"].values == "pair") & (df["mode_count"].values == 3)
    print(f"single-pair 3-of-4 slice: {mask.sum():,}")

    # Hand-rolled test cases from the leaf dump (Session 17 mining).
    # Helper: canonicalize ascending byte array from card strings.
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    cases = [
        # Leaf 1, miss: top=2, mid=JJ, bot has 3 diamonds (3-suit problem).
        ("Leaf-1 miss",   ("2c","3c","6d","9d","Td","Jh","Js")),
        # Leaf 1, correct: top=2, mid=JJ, bot is DS.
        ("Leaf-1 OK",     ("2c","3c","6c","9d","Td","Jh","Js")),
        # Leaf 7, miss: pair=77, mid wants to flip to KQ for AKQ-broadway.
        ("Leaf-7 miss",   ("2c","6c","7c","7d","Qh","Kh","As")),
        # Leaf 4, miss: pair=22 with A,K,Q broadway singletons.
        ("Leaf-4 miss",   ("2c","2d","3c","6c","Qh","Ks","Ad")),
        # Sanity: monochrome (4 same-suit in singletons).
        ("monosuit",      ("2c","2d","3c","4c","5c","6c","Ad")),
    ]
    print(f"\n{'case':<14}{'hand':<28}{'def_ds':>8}{'n_ds':>6}{'alt_ds':>8}")
    for name, cs in cases:
        h = hh(*cs)
        f = compute_pair_aug_for_hand(h)
        print(f"{name:<14}{' '.join(cs):<28}{f[0]:>8}{f[1]:>6}{f[2]:>8}")
