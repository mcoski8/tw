"""
Hand-feature and setting-feature extraction over canonical 7-card hands.

The Sprint 7 rule miner's substrate. For each canonical hand we expose:

  * Hand-level features: just from the 7 cards. Pair structure, top-rank,
    suitedness profile, connectivity, hand category.
  * Setting-level features: for any chosen setting index (top/mid/bot
    decomposition), the per-tier composition. Used for the multiway-robust
    setting in batch, but generic enough to use against any per-profile BR.

Two implementations live side-by-side:

  * Scalar (pure Python on a single hand) — clear, self-documenting, tested
    exhaustively against hand-rolled cases. The reference.
  * Batch (numpy-vectorized over (N, 7) uint8 arrays) — what the 6M-hand
    pipeline actually uses. ~1000x faster than scalar.

`assert_scalar_batch_parity()` checks they agree on a random sample. Run it
at the top of any script that consumes batch output, à la Decision 028.

Card byte encoding (matches engine):
  card_byte = (rank - 2) * 4 + suit
  rank ∈ 2..14, suit ∈ 0..3 (0=c, 1=d, 2=h, 3=s)
  So 0 = 2c, 51 = As; high cards have higher byte values.

Canonical hands are stored as (N, 7) uint8 arrays sorted ASCENDING by byte.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import numpy as np


# ----------------------------------------------------------------------
# Categorical enums (kept stable for downstream Parquet readers).
# ----------------------------------------------------------------------

CATEGORY_HIGH_ONLY = "high_only"
CATEGORY_PAIR = "pair"
CATEGORY_TWO_PAIR = "two_pair"
CATEGORY_THREE_PAIR = "three_pair"
CATEGORY_TRIPS = "trips"
CATEGORY_TRIPS_PAIR = "trips_pair"  # full-house shape in 7 cards
CATEGORY_QUADS = "quads"

CATEGORY_ORDER = (
    CATEGORY_HIGH_ONLY,
    CATEGORY_PAIR,
    CATEGORY_TWO_PAIR,
    CATEGORY_THREE_PAIR,
    CATEGORY_TRIPS,
    CATEGORY_TRIPS_PAIR,
    CATEGORY_QUADS,
)
CATEGORY_TO_ID: dict[str, int] = {c: i for i, c in enumerate(CATEGORY_ORDER)}
ID_TO_CATEGORY: tuple[str, ...] = CATEGORY_ORDER


AGREEMENT_UNANIMOUS = "unanimous"
AGREEMENT_3OF4 = "3of4"
AGREEMENT_2OF4 = "2of4"
AGREEMENT_SPLIT_2_2 = "split2_2"
AGREEMENT_SPLIT_1_1_1_1 = "split1_1_1_1"
AGREEMENT_ORDER = (
    AGREEMENT_UNANIMOUS,
    AGREEMENT_3OF4,
    AGREEMENT_2OF4,
    AGREEMENT_SPLIT_2_2,
    AGREEMENT_SPLIT_1_1_1_1,
)


# ----------------------------------------------------------------------
# Setting-index → tier-position decoder.
#
# setting_index ∈ 0..104 = top_outer_idx * 15 + mid_inner_idx
#   top_outer_idx ∈ 0..6 selects which of the 7 hand cards is the top.
#   mid_inner_idx ∈ 0..14 selects which lex-order pair of the remaining 6
#                  forms the middle. The other 4 are bot.
# ----------------------------------------------------------------------

_MID_PAIRS_OF_6: tuple[tuple[int, int], ...] = tuple(
    (a, b) for a in range(6) for b in range(a + 1, 6)
)
assert len(_MID_PAIRS_OF_6) == 15


def decode_tier_positions(setting_index: int) -> tuple[int, tuple[int, int], tuple[int, int, int, int]]:
    """
    Return (top_pos, mid_positions, bot_positions) — all indices into the
    7-card hand array. ``top_pos`` is a single int; ``mid_positions`` is a
    2-tuple; ``bot_positions`` is a 4-tuple.
    """
    if not (0 <= setting_index < 105):
        raise ValueError(f"setting_index out of range: {setting_index}")
    top_pos = setting_index // 15
    mid_inner = setting_index % 15
    remaining = [i for i in range(7) if i != top_pos]
    a_in_6, b_in_6 = _MID_PAIRS_OF_6[mid_inner]
    mid_positions = (remaining[a_in_6], remaining[b_in_6])
    bot_positions = tuple(p for p in remaining if p not in mid_positions)
    return top_pos, mid_positions, bot_positions


# Pre-computed lookup: setting_index → (top_pos, mid_pos_arr, bot_pos_arr).
# Used by the batch tier-feature path so we can vectorize "pick top of every
# hand" via fancy indexing.
_SETTING_TOP_POS = np.empty(105, dtype=np.int8)
_SETTING_MID_POS = np.empty((105, 2), dtype=np.int8)
_SETTING_BOT_POS = np.empty((105, 4), dtype=np.int8)
for _s in range(105):
    _t, _m, _b = decode_tier_positions(_s)
    _SETTING_TOP_POS[_s] = _t
    _SETTING_MID_POS[_s] = _m
    _SETTING_BOT_POS[_s] = _b


# ----------------------------------------------------------------------
# Card byte helpers.
# ----------------------------------------------------------------------

def card_rank(byte: int) -> int:
    """Rank 2..14 from a card byte."""
    return (int(byte) // 4) + 2


def card_suit(byte: int) -> int:
    """Suit 0..3 from a card byte."""
    return int(byte) % 4


# ----------------------------------------------------------------------
# Scalar feature extractors (the reference implementations).
# ----------------------------------------------------------------------

HAND_FEATURE_KEYS: tuple[str, ...] = (
    "n_pairs",
    "pair_high_rank",
    "pair_low_rank",
    "pair_third_rank",
    "n_trips",
    "trips_rank",
    "n_quads",
    "quads_rank",
    "top_rank",
    "second_rank",
    "third_rank",
    "suit_max",
    "suit_2nd",
    "suit_3rd",
    "suit_4th",
    "n_suits_present",
    "is_monosuit",
    "connectivity",
    "n_broadway",
    "n_low",
    "category_id",
)


def _longest_consecutive_run(rank_set: Iterable[int]) -> int:
    """
    Longest run of consecutive ranks present in ``rank_set``. The Ace counts
    as both 1 (wheel) and 14 (broadway), so an A-2-3-4-5 spans 5 ranks the
    same way 10-J-Q-K-A does.
    """
    rs = set(rank_set)
    if 14 in rs:
        rs = rs | {1}  # wheel-low ace
    if not rs:
        return 0
    best = cur = 0
    last = -2
    for r in sorted(rs):
        cur = cur + 1 if r == last + 1 else 1
        best = max(best, cur)
        last = r
    return best


def hand_features_scalar(hand_bytes: Iterable[int]) -> dict:
    """
    Hand-level features for one 7-card hand. ``hand_bytes`` is any iterable
    of 7 card bytes (uint8). Returns a dict keyed by ``HAND_FEATURE_KEYS``.
    """
    cards = [int(c) for c in hand_bytes]
    if len(cards) != 7:
        raise ValueError(f"hand_features_scalar: need 7 cards, got {len(cards)}")
    ranks = sorted((c // 4) + 2 for c in cards)  # ascending
    suits = [c % 4 for c in cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)

    # Pair / trips / quads are derived from rank_counts.values().
    quads_ranks = sorted([r for r, n in rank_counts.items() if n == 4], reverse=True)
    trips_ranks = sorted([r for r, n in rank_counts.items() if n == 3], reverse=True)
    pair_ranks = sorted([r for r, n in rank_counts.items() if n == 2], reverse=True)

    pair_high = pair_ranks[0] if len(pair_ranks) >= 1 else 0
    pair_low = pair_ranks[1] if len(pair_ranks) >= 2 else 0
    pair_third = pair_ranks[2] if len(pair_ranks) >= 3 else 0

    sorted_suit_counts = sorted(suit_counts.values(), reverse=True)
    while len(sorted_suit_counts) < 4:
        sorted_suit_counts.append(0)
    suit_max, suit_2nd, suit_3rd, suit_4th = sorted_suit_counts[:4]

    # Distinct ranks descending — for top/second/third "if you only kept the
    # highest distinct ranks, what are they". Useful for reasoning about
    # broadway-heavy hands.
    distinct_desc = sorted(rank_counts.keys(), reverse=True)
    top_rank = distinct_desc[0] if distinct_desc else 0
    second_rank = distinct_desc[1] if len(distinct_desc) >= 2 else 0
    third_rank = distinct_desc[2] if len(distinct_desc) >= 3 else 0

    n_broadway = sum(1 for r in ranks if r >= 10)
    n_low = sum(1 for r in ranks if r <= 5)
    connectivity = _longest_consecutive_run(rank_counts.keys())

    if quads_ranks:
        category = CATEGORY_QUADS
    elif trips_ranks and pair_ranks:
        category = CATEGORY_TRIPS_PAIR
    elif trips_ranks:
        category = CATEGORY_TRIPS
    elif len(pair_ranks) == 3:
        category = CATEGORY_THREE_PAIR
    elif len(pair_ranks) == 2:
        category = CATEGORY_TWO_PAIR
    elif len(pair_ranks) == 1:
        category = CATEGORY_PAIR
    else:
        category = CATEGORY_HIGH_ONLY

    return {
        "n_pairs": len(pair_ranks),
        "pair_high_rank": pair_high,
        "pair_low_rank": pair_low,
        "pair_third_rank": pair_third,
        "n_trips": len(trips_ranks),
        "trips_rank": trips_ranks[0] if trips_ranks else 0,
        "n_quads": len(quads_ranks),
        "quads_rank": quads_ranks[0] if quads_ranks else 0,
        "top_rank": top_rank,
        "second_rank": second_rank,
        "third_rank": third_rank,
        "suit_max": suit_max,
        "suit_2nd": suit_2nd,
        "suit_3rd": suit_3rd,
        "suit_4th": suit_4th,
        "n_suits_present": sum(1 for n in sorted_suit_counts if n > 0),
        "is_monosuit": suit_max == 7,
        "connectivity": connectivity,
        "n_broadway": n_broadway,
        "n_low": n_low,
        "category_id": CATEGORY_TO_ID[category],
    }


TIER_FEATURE_KEYS: tuple[str, ...] = (
    "top_rank",
    "mid_is_pair",
    "mid_is_suited",
    "mid_high_rank",
    "mid_low_rank",
    "mid_rank_sum",
    "bot_suit_max",
    "bot_is_double_suited",
    "bot_n_pairs",
    "bot_pair_high",
    "bot_high_rank",
    "bot_low_rank",
    "bot_rank_sum",
    "bot_n_broadway",
    "bot_connectivity",
)


def tier_features_scalar(
    hand_bytes: Iterable[int],
    setting_index: int,
) -> dict:
    """
    Per-tier features for ``hand_bytes`` arranged into ``setting_index``.

    Returns a dict keyed by ``TIER_FEATURE_KEYS``. All ranks are 2..14;
    booleans are True/False.
    """
    cards = [int(c) for c in hand_bytes]
    if len(cards) != 7:
        raise ValueError(f"tier_features_scalar: need 7 cards, got {len(cards)}")
    top_pos, mid_pos, bot_pos = decode_tier_positions(setting_index)

    top_card = cards[top_pos]
    mid_cards = [cards[i] for i in mid_pos]
    bot_cards = [cards[i] for i in bot_pos]

    mid_ranks = sorted((c // 4) + 2 for c in mid_cards)
    mid_suits = [c % 4 for c in mid_cards]
    bot_ranks = sorted([(c // 4) + 2 for c in bot_cards], reverse=True)
    bot_suits = [c % 4 for c in bot_cards]
    bot_suit_counts = sorted(Counter(bot_suits).values(), reverse=True)
    while len(bot_suit_counts) < 2:
        bot_suit_counts.append(0)
    bot_rank_counts = Counter(bot_ranks)
    bot_pair_ranks = sorted([r for r, n in bot_rank_counts.items() if n >= 2], reverse=True)
    bot_n_pairs = sum(1 for n in bot_rank_counts.values() if n >= 2)

    return {
        "top_rank": (top_card // 4) + 2,
        "mid_is_pair": mid_ranks[0] == mid_ranks[1],
        "mid_is_suited": mid_suits[0] == mid_suits[1],
        "mid_high_rank": mid_ranks[1],
        "mid_low_rank": mid_ranks[0],
        "mid_rank_sum": sum(mid_ranks),
        "bot_suit_max": bot_suit_counts[0],
        "bot_is_double_suited": bot_suit_counts[0] == 2 and bot_suit_counts[1] == 2,
        "bot_n_pairs": bot_n_pairs,
        "bot_pair_high": bot_pair_ranks[0] if bot_pair_ranks else 0,
        "bot_high_rank": bot_ranks[0],
        "bot_low_rank": bot_ranks[-1],
        "bot_rank_sum": sum(bot_ranks),
        "bot_n_broadway": sum(1 for r in bot_ranks if r >= 10),
        "bot_connectivity": _longest_consecutive_run(bot_rank_counts.keys()),
    }


# ----------------------------------------------------------------------
# Vectorized batch implementations.
# ----------------------------------------------------------------------

def _rank_one_hot(ranks: np.ndarray) -> np.ndarray:
    """
    Build (N, 13) uint8 one-hot count matrix from (N, 7) rank array (values 2..14).
    Each column counts occurrences of one rank in that hand.
    """
    n = ranks.shape[0]
    out = np.zeros((n, 13), dtype=np.uint8)
    for r in range(2, 15):
        out[:, r - 2] = (ranks == r).sum(axis=1).astype(np.uint8)
    return out


def _suit_one_hot(suits: np.ndarray) -> np.ndarray:
    """(N, 4) uint8 one-hot count matrix from (N, 7) suit array."""
    n = suits.shape[0]
    out = np.zeros((n, 4), dtype=np.uint8)
    for s in range(4):
        out[:, s] = (suits == s).sum(axis=1).astype(np.uint8)
    return out


def _max_run_length(rank_oh: np.ndarray) -> np.ndarray:
    """
    For each row of (N, 13) rank presence (count, treated as bool), return the
    longest run of consecutive ranks. Wheel-low: rank 14 (Ace) also acts as
    a virtual rank-1 prepended to the 2..14 sequence.
    """
    # Bool view of "rank present in hand".
    present = rank_oh > 0
    # Extend left with the Ace column to model wheel.
    extended = np.concatenate([present[:, 12:13], present], axis=1)  # (N, 14)
    n = extended.shape[0]
    cur = np.zeros(n, dtype=np.int16)
    best = np.zeros(n, dtype=np.int16)
    for c in range(extended.shape[1]):
        col = extended[:, c]
        cur = np.where(col, cur + 1, 0)
        best = np.maximum(best, cur)
    return best.astype(np.uint8)


def hand_features_batch(hands: np.ndarray) -> dict[str, np.ndarray]:
    """
    Vectorized hand-level features over a (N, 7) uint8 array.

    Returns a dict of column arrays, all aligned to the input rows. Uses the
    smallest-fitting dtype per column. Output keys match ``HAND_FEATURE_KEYS``.
    """
    if hands.ndim != 2 or hands.shape[1] != 7:
        raise ValueError(f"hands must be (N, 7); got shape {hands.shape}")
    if hands.dtype != np.uint8:
        hands = hands.astype(np.uint8)
    n = hands.shape[0]

    ranks = (hands // 4).astype(np.int16) + 2  # (N, 7), values 2..14
    suits = (hands % 4).astype(np.uint8)        # (N, 7)
    rank_oh = _rank_one_hot(ranks)              # (N, 13) — col c = rank c+2
    suit_oh = _suit_one_hot(suits)              # (N, 4)

    # Pair-pattern columns. For each row, "ranks where count == k" is what we want.
    is_pair_rank = rank_oh == 2
    is_trip_rank = rank_oh == 3
    is_quad_rank = rank_oh == 4

    n_pairs = is_pair_rank.sum(axis=1).astype(np.uint8)
    n_trips = is_trip_rank.sum(axis=1).astype(np.uint8)
    n_quads = is_quad_rank.sum(axis=1).astype(np.uint8)

    # Highest pair rank per row: argmax of is_pair_rank from the right.
    # Quick way: multiply mask by (rank id), take max → 0 if no pair, else highest rank.
    rank_ids = (np.arange(13, dtype=np.int16) + 2)[None, :]  # (1, 13), values 2..14
    pair_mask_ranks = np.where(is_pair_rank, rank_ids, 0)
    trip_mask_ranks = np.where(is_trip_rank, rank_ids, 0)
    quad_mask_ranks = np.where(is_quad_rank, rank_ids, 0)

    pair_sorted_desc = np.sort(pair_mask_ranks, axis=1)[:, ::-1]  # (N, 13) descending
    pair_high = pair_sorted_desc[:, 0].astype(np.uint8)
    pair_low = pair_sorted_desc[:, 1].astype(np.uint8)
    pair_third = pair_sorted_desc[:, 2].astype(np.uint8)

    trips_rank = trip_mask_ranks.max(axis=1).astype(np.uint8)
    quads_rank = quad_mask_ranks.max(axis=1).astype(np.uint8)

    # Distinct ranks descending — to extract top/2nd/3rd.
    distinct_mask_ranks = np.where(rank_oh > 0, rank_ids, 0)  # (N, 13)
    distinct_sorted_desc = np.sort(distinct_mask_ranks, axis=1)[:, ::-1]
    top_rank = distinct_sorted_desc[:, 0].astype(np.uint8)
    second_rank = distinct_sorted_desc[:, 1].astype(np.uint8)
    third_rank = distinct_sorted_desc[:, 2].astype(np.uint8)

    suit_sorted_desc = np.sort(suit_oh, axis=1)[:, ::-1]  # (N, 4)
    suit_max = suit_sorted_desc[:, 0]
    suit_2nd = suit_sorted_desc[:, 1]
    suit_3rd = suit_sorted_desc[:, 2]
    suit_4th = suit_sorted_desc[:, 3]
    n_suits_present = (suit_oh > 0).sum(axis=1).astype(np.uint8)
    is_monosuit = suit_max == 7

    connectivity = _max_run_length(rank_oh)
    n_broadway = (ranks >= 10).sum(axis=1).astype(np.uint8)
    n_low = (ranks <= 5).sum(axis=1).astype(np.uint8)

    # Category ID via priority chain.
    cat = np.full(n, CATEGORY_TO_ID[CATEGORY_HIGH_ONLY], dtype=np.uint8)
    cat = np.where(n_pairs == 1, CATEGORY_TO_ID[CATEGORY_PAIR], cat)
    cat = np.where(n_pairs == 2, CATEGORY_TO_ID[CATEGORY_TWO_PAIR], cat)
    cat = np.where(n_pairs == 3, CATEGORY_TO_ID[CATEGORY_THREE_PAIR], cat)
    cat = np.where(n_trips >= 1, CATEGORY_TO_ID[CATEGORY_TRIPS], cat)
    cat = np.where((n_trips >= 1) & (n_pairs >= 1), CATEGORY_TO_ID[CATEGORY_TRIPS_PAIR], cat)
    cat = np.where(n_quads >= 1, CATEGORY_TO_ID[CATEGORY_QUADS], cat)

    return {
        "n_pairs": n_pairs,
        "pair_high_rank": pair_high,
        "pair_low_rank": pair_low,
        "pair_third_rank": pair_third,
        "n_trips": n_trips,
        "trips_rank": trips_rank,
        "n_quads": n_quads,
        "quads_rank": quads_rank,
        "top_rank": top_rank,
        "second_rank": second_rank,
        "third_rank": third_rank,
        "suit_max": suit_max.astype(np.uint8),
        "suit_2nd": suit_2nd.astype(np.uint8),
        "suit_3rd": suit_3rd.astype(np.uint8),
        "suit_4th": suit_4th.astype(np.uint8),
        "n_suits_present": n_suits_present,
        "is_monosuit": is_monosuit,
        "connectivity": connectivity,
        "n_broadway": n_broadway,
        "n_low": n_low,
        "category_id": cat,
    }


def tier_features_batch(
    hands: np.ndarray,
    setting_indices: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    Per-tier features for the (hand, setting) pair on each row.

    ``hands`` is (N, 7) uint8; ``setting_indices`` is (N,) of dtype 0..104.
    Returns a dict of column arrays keyed by ``TIER_FEATURE_KEYS``.
    """
    if hands.ndim != 2 or hands.shape[1] != 7:
        raise ValueError(f"hands must be (N, 7); got {hands.shape}")
    if setting_indices.shape != (hands.shape[0],):
        raise ValueError("setting_indices length must match hands")
    if hands.dtype != np.uint8:
        hands = hands.astype(np.uint8)
    si = setting_indices.astype(np.int16)
    n = hands.shape[0]
    rows = np.arange(n)

    top_pos = _SETTING_TOP_POS[si].astype(np.intp)
    mid_pos = _SETTING_MID_POS[si].astype(np.intp)  # (N, 2)
    bot_pos = _SETTING_BOT_POS[si].astype(np.intp)  # (N, 4)

    top_card = hands[rows, top_pos]
    mid_cards = hands[rows[:, None], mid_pos]   # (N, 2)
    bot_cards = hands[rows[:, None], bot_pos]   # (N, 4)

    mid_ranks = (mid_cards // 4).astype(np.int16) + 2  # (N, 2)
    mid_suits = (mid_cards % 4).astype(np.uint8)
    mid_high = np.maximum(mid_ranks[:, 0], mid_ranks[:, 1]).astype(np.uint8)
    mid_low = np.minimum(mid_ranks[:, 0], mid_ranks[:, 1]).astype(np.uint8)
    mid_is_pair = mid_ranks[:, 0] == mid_ranks[:, 1]
    mid_is_suited = mid_suits[:, 0] == mid_suits[:, 1]
    mid_rank_sum = mid_ranks.sum(axis=1).astype(np.uint8)

    bot_ranks = (bot_cards // 4).astype(np.int16) + 2  # (N, 4)
    bot_suits = (bot_cards % 4).astype(np.uint8)
    bot_rank_sum = bot_ranks.sum(axis=1).astype(np.uint8)
    bot_high_rank = bot_ranks.max(axis=1).astype(np.uint8)
    bot_low_rank = bot_ranks.min(axis=1).astype(np.uint8)
    bot_n_broadway = (bot_ranks >= 10).sum(axis=1).astype(np.uint8)

    # Suit profile of bottom 4. Build (N, 4) suit one-hot, sort descending.
    bot_suit_oh = np.zeros((n, 4), dtype=np.uint8)
    for s in range(4):
        bot_suit_oh[:, s] = (bot_suits == s).sum(axis=1).astype(np.uint8)
    bot_suit_sorted = np.sort(bot_suit_oh, axis=1)[:, ::-1]
    bot_suit_max = bot_suit_sorted[:, 0]
    bot_is_double_suited = (bot_suit_sorted[:, 0] == 2) & (bot_suit_sorted[:, 1] == 2)

    # Rank distribution of bottom 4 — find pairs.
    bot_rank_oh = np.zeros((n, 13), dtype=np.uint8)
    for r in range(2, 15):
        bot_rank_oh[:, r - 2] = (bot_ranks == r).sum(axis=1).astype(np.uint8)
    is_bot_pair_rank = bot_rank_oh >= 2
    bot_n_pairs = is_bot_pair_rank.sum(axis=1).astype(np.uint8)
    rank_ids = (np.arange(13, dtype=np.int16) + 2)[None, :]
    bot_pair_high = np.where(is_bot_pair_rank, rank_ids, 0).max(axis=1).astype(np.uint8)

    bot_connectivity = _max_run_length(bot_rank_oh)

    return {
        "top_rank": ((top_card // 4) + 2).astype(np.uint8),
        "mid_is_pair": mid_is_pair,
        "mid_is_suited": mid_is_suited,
        "mid_high_rank": mid_high,
        "mid_low_rank": mid_low,
        "mid_rank_sum": mid_rank_sum,
        "bot_suit_max": bot_suit_max,
        "bot_is_double_suited": bot_is_double_suited,
        "bot_n_pairs": bot_n_pairs,
        "bot_pair_high": bot_pair_high,
        "bot_high_rank": bot_high_rank,
        "bot_low_rank": bot_low_rank,
        "bot_rank_sum": bot_rank_sum,
        "bot_n_broadway": bot_n_broadway,
        "bot_connectivity": bot_connectivity,
    }


# ----------------------------------------------------------------------
# Cross-model robust setting (the mode of N per-profile BR settings).
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RobustResult:
    multiway_robust: np.ndarray   # (N,) uint8
    agreement_id: np.ndarray      # (N,) uint8 — index into AGREEMENT_ORDER
    mode_count: np.ndarray        # (N,) uint8


def compute_multiway_robust(per_profile: np.ndarray) -> RobustResult:
    """
    Given (N, 4) uint8 of per-profile best-response settings, return the
    mode setting per row plus the agreement class.

    Tie-breaking: earliest profile wins (matches multiway_analysis.py).
    """
    if per_profile.ndim != 2 or per_profile.shape[1] != 4:
        raise ValueError(f"per_profile must be (N, 4); got {per_profile.shape}")
    n = per_profile.shape[0]

    # Vectorized "match count for each column" — ((N,4)==(N,1,4)).sum gives (N,4,4).
    eq = per_profile[:, :, None] == per_profile[:, None, :]  # (N, 4, 4)
    match_counts_each = eq.sum(axis=2).astype(np.uint8)  # (N, 4) — for each column, # of cols matching it

    # Argmax on match_counts picks the earliest column with the most matches → tie-break by earliest profile.
    pick_col = np.argmax(match_counts_each, axis=1)
    rows = np.arange(n)
    multiway_robust = per_profile[rows, pick_col].astype(np.uint8)
    mode_count = match_counts_each[rows, pick_col].astype(np.uint8)

    # Agreement class: based on shape of distinct-counts.
    # We recompute via sorted match counts per row.
    sorted_mc = np.sort(match_counts_each, axis=1)[:, ::-1]  # (N, 4) descending
    # sorted_mc patterns:
    #   unanimous (AAAA): [4,4,4,4]
    #   3-of-4 (AAAB):    [3,3,3,1]
    #   2-2 split (AABB): [2,2,2,2]
    #   2-1-1 (AABC):     [2,2,1,1]
    #   all distinct (ABCD): [1,1,1,1]
    agreement_id = np.full(n, AGREEMENT_ORDER.index(AGREEMENT_SPLIT_1_1_1_1), dtype=np.uint8)
    agreement_id = np.where(
        sorted_mc[:, 0] == 2,
        AGREEMENT_ORDER.index(AGREEMENT_2OF4),
        agreement_id,
    )
    agreement_id = np.where(
        (sorted_mc[:, 0] == 2) & (sorted_mc[:, 3] == 2),
        AGREEMENT_ORDER.index(AGREEMENT_SPLIT_2_2),
        agreement_id,
    )
    agreement_id = np.where(
        sorted_mc[:, 0] == 3,
        AGREEMENT_ORDER.index(AGREEMENT_3OF4),
        agreement_id,
    )
    agreement_id = np.where(
        sorted_mc[:, 0] == 4,
        AGREEMENT_ORDER.index(AGREEMENT_UNANIMOUS),
        agreement_id,
    )

    return RobustResult(
        multiway_robust=multiway_robust,
        agreement_id=agreement_id,
        mode_count=mode_count,
    )


# ----------------------------------------------------------------------
# Scalar/batch parity check.
# ----------------------------------------------------------------------

def assert_scalar_batch_parity(
    hands: np.ndarray,
    setting_indices: np.ndarray | None = None,
    sample_size: int = 200,
    seed: int = 0,
) -> None:
    """
    Spot-check that the batch implementations agree with the scalar reference
    on a random subsample. Raises AssertionError on any mismatch.

    Following Decision 028 — this is the regression gate for any change to
    the vectorized path. Cheap to run before trusting batch output for a
    long-lived analysis artifact.
    """
    rng = np.random.default_rng(seed)
    n = hands.shape[0]
    k = min(sample_size, n)
    idxs = rng.choice(n, k, replace=False)

    sub_hands = hands[idxs]
    batch_hand = hand_features_batch(sub_hands)
    for i in range(k):
        scalar = hand_features_scalar(sub_hands[i])
        for key in HAND_FEATURE_KEYS:
            bv = batch_hand[key][i]
            sv = scalar[key]
            # Cast both sides to int to compare (dodges np.bool vs Python bool).
            if int(bv) != int(sv):
                raise AssertionError(
                    f"hand parity mismatch at idx={idxs[i]}, key={key!r}: "
                    f"batch={int(bv)} vs scalar={int(sv)}; hand={list(sub_hands[i])}"
                )

    if setting_indices is not None:
        sub_settings = setting_indices[idxs]
        batch_tier = tier_features_batch(sub_hands, sub_settings)
        for i in range(k):
            scalar = tier_features_scalar(sub_hands[i], int(sub_settings[i]))
            for key in TIER_FEATURE_KEYS:
                bv = batch_tier[key][i]
                sv = scalar[key]
                if int(bv) != int(sv):
                    raise AssertionError(
                        f"tier parity mismatch at idx={idxs[i]}, key={key!r}: "
                        f"batch={int(bv)} vs scalar={int(sv)}; "
                        f"hand={list(sub_hands[i])} setting={int(sub_settings[i])}"
                    )
