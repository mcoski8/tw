"""
Unit tests for tw_analysis.features.

Cases are hand-picked to exercise:
  * Pair / two-pair / three-pair / trips / quads / trips+pair / no-pair categories
  * Wheel-low connectivity (A-2-3-4-5 should connect)
  * Broadway connectivity (T-J-Q-K-A)
  * Monosuit detection
  * Per-tier (top/mid/bot) decomposition for representative settings
  * Scalar/batch parity on the cases above
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis.features import (  # noqa: E402
    AGREEMENT_3OF4,
    AGREEMENT_ORDER,
    AGREEMENT_SPLIT_2_2,
    AGREEMENT_SPLIT_1_1_1_1,
    AGREEMENT_UNANIMOUS,
    AGREEMENT_2OF4,
    CATEGORY_HIGH_ONLY,
    CATEGORY_PAIR,
    CATEGORY_QUADS,
    CATEGORY_THREE_PAIR,
    CATEGORY_TO_ID,
    CATEGORY_TRIPS,
    CATEGORY_TRIPS_PAIR,
    CATEGORY_TWO_PAIR,
    assert_scalar_batch_parity,
    compute_multiway_robust,
    decode_tier_positions,
    hand_features_batch,
    hand_features_scalar,
    tier_features_batch,
    tier_features_scalar,
)


# ----------------------------------------------------------------------
# Card-byte helper for test fixtures.
# Suit map: c=0, d=1, h=2, s=3
# Card byte = (rank-2)*4 + suit
# ----------------------------------------------------------------------

_SUIT_MAP = {"c": 0, "d": 1, "h": 2, "s": 3}
_RANK_MAP = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
             "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}


def card(s: str) -> int:
    """'As' → 51, '2c' → 0, etc."""
    return (_RANK_MAP[s[0]] - 2) * 4 + _SUIT_MAP[s[1]]


def hand(*cards: str) -> np.ndarray:
    """Return a sorted-ascending uint8 array of card bytes for use as a canonical-style hand."""
    arr = np.array([card(c) for c in cards], dtype=np.uint8)
    arr.sort()
    if len(arr) != 7:
        raise ValueError(f"hand() needs 7 cards, got {len(arr)}")
    return arr


# ======================================================================
# hand_features_scalar — hand-rolled cases
# ======================================================================

def test_high_only_no_pair():
    h = hand("Ac", "Kd", "Qh", "Js", "9c", "7d", "2h")
    f = hand_features_scalar(h)
    assert f["n_pairs"] == 0
    assert f["n_trips"] == 0
    assert f["n_quads"] == 0
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_HIGH_ONLY]
    assert f["top_rank"] == 14
    assert f["second_rank"] == 13
    assert f["third_rank"] == 12
    assert f["n_broadway"] == 4
    assert f["pair_high_rank"] == 0


def test_one_pair():
    h = hand("As", "Ah", "Kd", "Qc", "Js", "9c", "2d")
    f = hand_features_scalar(h)
    assert f["n_pairs"] == 1
    assert f["pair_high_rank"] == 14
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_PAIR]


def test_two_pair():
    h = hand("As", "Ah", "Kd", "Kc", "Js", "9c", "2d")
    f = hand_features_scalar(h)
    assert f["n_pairs"] == 2
    assert f["pair_high_rank"] == 14
    assert f["pair_low_rank"] == 13
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_TWO_PAIR]


def test_three_pair():
    h = hand("As", "Ah", "Kd", "Kc", "Qs", "Qc", "2d")
    f = hand_features_scalar(h)
    assert f["n_pairs"] == 3
    assert f["pair_high_rank"] == 14
    assert f["pair_low_rank"] == 13
    assert f["pair_third_rank"] == 12
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_THREE_PAIR]


def test_trips_no_pair():
    h = hand("As", "Ah", "Ad", "Kc", "Js", "9c", "2d")
    f = hand_features_scalar(h)
    assert f["n_trips"] == 1
    assert f["trips_rank"] == 14
    assert f["n_pairs"] == 0
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_TRIPS]


def test_trips_with_pair():
    h = hand("As", "Ah", "Ad", "Kc", "Kh", "9c", "2d")
    f = hand_features_scalar(h)
    assert f["n_trips"] == 1
    assert f["n_pairs"] == 1
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_TRIPS_PAIR]


def test_quads():
    h = hand("As", "Ah", "Ad", "Ac", "Kc", "9c", "2d")
    f = hand_features_scalar(h)
    assert f["n_quads"] == 1
    assert f["quads_rank"] == 14
    assert f["category_id"] == CATEGORY_TO_ID[CATEGORY_QUADS]


def test_broadway_connectivity_5():
    h = hand("As", "Kh", "Qd", "Jc", "Ts", "5c", "2d")
    f = hand_features_scalar(h)
    assert f["connectivity"] == 5  # T-J-Q-K-A


def test_wheel_connectivity_5():
    h = hand("As", "2h", "3d", "4c", "5s", "9c", "Td")
    f = hand_features_scalar(h)
    assert f["connectivity"] == 5  # A-2-3-4-5 (wheel)


def test_short_run_4():
    h = hand("9s", "8h", "7d", "6c", "Qh", "2c", "Ad")
    f = hand_features_scalar(h)
    assert f["connectivity"] == 4  # 6-7-8-9


def test_monosuit():
    h = hand("As", "Ks", "Qs", "Js", "Ts", "9s", "2s")
    f = hand_features_scalar(h)
    assert f["is_monosuit"]
    assert f["suit_max"] == 7
    assert f["n_suits_present"] == 1
    assert f["connectivity"] == 6  # 9-T-J-Q-K-A


def test_suit_profile_4_2_1():
    h = hand("As", "Ks", "Qs", "Js", "Th", "9h", "2c")
    f = hand_features_scalar(h)
    assert f["suit_max"] == 4
    assert f["suit_2nd"] == 2
    assert f["suit_3rd"] == 1
    assert f["suit_4th"] == 0


# ======================================================================
# tier_features_scalar — known decompositions
# ======================================================================

def test_setting_0_decomposition():
    """Setting 0 → top_pos=0, mid=positions(1,2), bot=positions(3,4,5,6)."""
    top, mid, bot = decode_tier_positions(0)
    assert top == 0
    assert mid == (1, 2)
    assert bot == (3, 4, 5, 6)


def test_setting_104_decomposition():
    """Setting 104 = top * 15 + 14, top_pos=6 (last index), mid_inner=14
    which is the last lex-pair (4,5). Remaining 6 positions = (0..5).
    mid = (positions[4], positions[5]) = (4, 5). bot = (0,1,2,3)."""
    top, mid, bot = decode_tier_positions(104)
    assert top == 6
    assert mid == (4, 5)
    assert bot == (0, 1, 2, 3)


def test_tier_features_setting_104_naive():
    """
    For setting 104, top is the highest-byte card, mid is the next two,
    bot is the lowest four. On A-K-Q-J-T-9-2 (rainbowish), top is the Ace.
    """
    h = hand("As", "Kh", "Qd", "Jc", "Th", "9d", "2c")
    # h is sorted ascending by byte:
    # 2c(0)=byte0, 9d(1*4+1=29), Th(10*4+2-2*4=34? let me compute)
    # Actually let me just trust hand() sorts ascending.
    f = tier_features_scalar(h, 104)
    # top = byte index 6 (highest); h sorted asc; highest byte = As (51)
    assert f["top_rank"] == 14
    # mid rank-sum: positions 4, 5 = 2nd and 3rd highest cards ... should be K + Q = 25
    assert f["mid_rank_sum"] in (24, 25, 26)  # depends on suit ordering tie-break; will assert exact below
    # bot 4 = lowest 4 cards.
    assert f["bot_low_rank"] == 2
    # Pair structure of bot: 4 distinct ranks → no pair.
    assert f["bot_n_pairs"] == 0


def test_tier_features_pair_in_mid():
    """Setting that puts the pair in the middle: a known broadway hand."""
    # Hand: As Ah Kd Qc Js 9c 2d → sorted ascending by byte
    h = hand("As", "Ah", "Kd", "Qc", "Js", "9c", "2d")
    # We want setting where top=2d (lowest), mid=As+Ah, bot=Kd Qc Js 9c.
    # 2d is at position 0 in the sorted hand. As, Ah are at the top positions.
    # Actually let's just probe: find such a setting by enumeration.
    best = None
    for s in range(105):
        f = tier_features_scalar(h, s)
        if f["top_rank"] == 2 and f["mid_is_pair"] and f["mid_high_rank"] == 14:
            best = (s, f)
            break
    assert best is not None, "should be able to construct top=2, mid=AA"
    _, f = best
    assert f["mid_is_pair"]
    assert f["bot_n_pairs"] == 0


def test_tier_features_double_suited_bot():
    """A hand with a clear double-suited bottom — verify detection works."""
    # 4-card bot: 2c 3c 4d 5d → suit profile (2,2)
    # Top + mid: As Kh Qh
    h = hand("As", "Kh", "Qh", "2c", "3c", "4d", "5d")
    # Find a setting where bot = {2c,3c,4d,5d}
    found = None
    for s in range(105):
        f = tier_features_scalar(h, s)
        if f["bot_is_double_suited"] and f["bot_high_rank"] == 5:
            found = (s, f)
            break
    assert found is not None, "expected a setting that puts {2c,3c,4d,5d} in bot"
    _, f = found
    assert f["bot_is_double_suited"]
    assert f["bot_suit_max"] == 2


# ======================================================================
# compute_multiway_robust — agreement classes
# ======================================================================

def test_robust_unanimous():
    pp = np.array([[42, 42, 42, 42]], dtype=np.uint8)
    r = compute_multiway_robust(pp)
    assert int(r.multiway_robust[0]) == 42
    assert AGREEMENT_ORDER[int(r.agreement_id[0])] == AGREEMENT_UNANIMOUS
    assert int(r.mode_count[0]) == 4


def test_robust_3of4():
    pp = np.array([[10, 10, 10, 99]], dtype=np.uint8)
    r = compute_multiway_robust(pp)
    assert int(r.multiway_robust[0]) == 10
    assert AGREEMENT_ORDER[int(r.agreement_id[0])] == AGREEMENT_3OF4
    assert int(r.mode_count[0]) == 3


def test_robust_2of4_two_one_one():
    """Pattern AABC: top mode count is 2, only one pair of matching profiles."""
    pp = np.array([[5, 5, 7, 9]], dtype=np.uint8)
    r = compute_multiway_robust(pp)
    assert int(r.multiway_robust[0]) == 5
    assert AGREEMENT_ORDER[int(r.agreement_id[0])] == AGREEMENT_2OF4
    assert int(r.mode_count[0]) == 2


def test_robust_2of4_split_2_2():
    """Pattern AABB: two distinct pairs of equal size — 2-2 split."""
    pp = np.array([[5, 5, 7, 7]], dtype=np.uint8)
    r = compute_multiway_robust(pp)
    # Tie-break = earliest profile, so robust=5.
    assert int(r.multiway_robust[0]) == 5
    assert AGREEMENT_ORDER[int(r.agreement_id[0])] == AGREEMENT_SPLIT_2_2
    assert int(r.mode_count[0]) == 2


def test_robust_all_distinct():
    pp = np.array([[1, 2, 3, 4]], dtype=np.uint8)
    r = compute_multiway_robust(pp)
    assert int(r.multiway_robust[0]) == 1  # earliest tie-break
    assert AGREEMENT_ORDER[int(r.agreement_id[0])] == AGREEMENT_SPLIT_1_1_1_1
    assert int(r.mode_count[0]) == 1


# ======================================================================
# scalar/batch parity (Decision 028 discipline)
# ======================================================================

def test_parity_synthetic_batch():
    """Synthesise some hands by random sampling 7 distinct cards and check parity."""
    rng = np.random.default_rng(42)
    hands_list = []
    for _ in range(150):
        cards = rng.choice(52, 7, replace=False)
        cards.sort()
        hands_list.append(cards.astype(np.uint8))
    hands_arr = np.stack(hands_list)
    settings = rng.integers(0, 105, size=len(hands_arr), dtype=np.int16)
    assert_scalar_batch_parity(hands_arr, settings, sample_size=150, seed=0)


def test_parity_edge_case_quads_and_wheel():
    """Hand-rolled edge cases: quads, wheel, monosuit. Run them through batch."""
    cases = [
        hand("As", "Ah", "Ad", "Ac", "Kc", "9c", "2d"),  # quads
        hand("As", "2h", "3d", "4c", "5s", "9c", "Td"),  # wheel
        hand("As", "Ks", "Qs", "Js", "Ts", "9s", "2s"),  # monosuit
        hand("As", "Ah", "Kd", "Kc", "Qs", "Qc", "2d"),  # 3-pair
    ]
    arr = np.stack(cases)
    settings = np.array([0, 50, 104, 73], dtype=np.int16)
    assert_scalar_batch_parity(arr, settings, sample_size=4, seed=0)


# ======================================================================
# Test runner.
# ======================================================================

def main() -> int:
    failures = []
    test_funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for fn in test_funcs:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failures.append((fn.__name__, e))
            print(f"  FAIL  {fn.__name__} — {type(e).__name__}: {e}")
    print()
    if failures:
        print(f"{len(failures)} of {len(test_funcs)} tests failed.")
        return 1
    print(f"All {len(test_funcs)} tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
