"""
Self-tests for ``tw_analysis.settings`` — mirrors the Rust tests in
``engine/src/setting.rs``.

Run:
    python3 analysis/scripts/test_settings.py
"""
from __future__ import annotations

import sys
from itertools import permutations
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis.settings import (  # noqa: E402
    HAND_SIZE,
    NUM_SETTINGS,
    Card,
    all_settings,
    decode_setting,
    parse_hand,
)


def expect(cond: bool, msg: str) -> None:
    if not cond:
        print(f"  FAIL: {msg}")
        raise SystemExit(1)


def test_card_pack_unpack() -> None:
    # 2c is packed 0, As is packed 51.
    two_c = Card.from_rank_suit(2, 0)
    ace_s = Card.from_rank_suit(14, 3)
    expect(two_c.idx == 0, f"2c should pack to 0, got {two_c.idx}")
    expect(ace_s.idx == 51, f"As should pack to 51, got {ace_s.idx}")

    # Round-trip every card.
    for i in range(52):
        c = Card(i)
        c2 = Card.from_rank_suit(c.rank, c.suit)
        expect(c2.idx == i, f"round-trip failed at index {i}")

    # String parsing.
    for s, idx in (("2c", 0), ("2d", 1), ("2h", 2), ("2s", 3),
                   ("3c", 4), ("As", 51), ("Kh", 46), ("Td", 33)):
        got = Card.parse(s)
        expect(got.idx == idx, f"parse({s!r}) -> {got.idx}, expected {idx}")
        expect(str(got) == s, f"str({s}) round-trip failed: {str(got)!r}")


def test_parse_hand() -> None:
    hand = parse_hand("As Kh Qd Jc Ts 9h 2d")
    expect(len(hand) == 7, f"expected 7 cards, got {len(hand)}")
    expect(str(hand[0]) == "As" and str(hand[6]) == "2d", f"hand: {hand}")


def test_setting_count() -> None:
    hand = parse_hand("As Kh Qd Jc Ts 9h 2d")
    settings = all_settings(hand)
    expect(len(settings) == NUM_SETTINGS, f"got {len(settings)} settings")


def test_every_setting_uses_all_7() -> None:
    hand = parse_hand("As Kh Qd Jc Ts 9h 2d")
    input_set = frozenset(c.idx for c in hand)
    expect(len(input_set) == 7, "input hand has duplicates")

    for i, s in enumerate(all_settings(hand)):
        got = {c.idx for c in s.all_cards()}
        expect(len(got) == 7, f"setting {i} has duplicate: {s}")
        expect(got == input_set, f"setting {i} uses different cards: {s}")


def test_all_settings_unique() -> None:
    hand = parse_hand("As Kh Qd Jc Ts 9h 2d")
    seen: set[tuple[int, ...]] = set()
    for i, s in enumerate(all_settings(hand)):
        key = (s.top.idx, *(c.idx for c in s.mid), *(c.idx for c in s.bot))
        expect(key not in seen, f"duplicate setting at index {i}: {s}")
        seen.add(key)
    expect(len(seen) == NUM_SETTINGS, f"seen {len(seen)} unique settings")


def test_decode_matches_all_settings() -> None:
    # Decode every index on multiple hands and verify it matches the list.
    hands = [
        parse_hand("As Kh Qd Jc Ts 9h 2d"),
        parse_hand("2c 2d 2h 3s 3c 4d 5h"),          # low + pairs
        parse_hand("As Ah Ad Ac Ks Kh Kd"),          # quads-and-trips
        parse_hand("9c 9d 9h 9s 8c 8d 8h"),          # quads + trips
        parse_hand("7c 8c 9c Tc Jc Qc Kc"),          # seven to one suit
    ]
    for hand in hands:
        full = all_settings(hand)
        for i in range(NUM_SETTINGS):
            one = decode_setting(hand, i)
            expect(
                one == full[i],
                f"decode_setting mismatch at i={i}, hand={' '.join(str(c) for c in hand)}"
            )


def test_tier_sort_order() -> None:
    """Mid and bot must be sorted descending by card index."""
    hand = parse_hand("2c 3d 4h 5s 6c 7d 8h")  # all distinct, ascending
    for s in all_settings(hand):
        expect(s.mid[0].idx >= s.mid[1].idx, f"mid not desc: {s}")
        for i in range(3):
            expect(s.bot[i].idx >= s.bot[i + 1].idx, f"bot not desc: {s}")


def test_top_card_by_outer_index() -> None:
    """The first 15 settings pick hand[0] as top, next 15 pick hand[1], ..."""
    hand = parse_hand("As Kh Qd Jc Ts 9h 2d")
    for i, s in enumerate(all_settings(hand)):
        top_i = i // 15
        expect(
            s.top == hand[top_i],
            f"setting {i}: top should be hand[{top_i}]={hand[top_i]}, got {s.top}"
        )


def test_mid_combo_order() -> None:
    """
    Within each block of 15, (a, b) iterates in the order:
    (0,1), (0,2), ..., (0,5), (1,2), ..., (4,5).

    Because the cards for a<b come from the remaining6 list, and mid is
    sorted desc, we can verify by using a strictly-descending hand so the
    'remaining' order is predictable and the desc-sort is a no-op.
    """
    hand = parse_hand("As Ks Qs Js Ts 9s 8s")  # indices descending
    settings = all_settings(hand)
    expected_pairs = [(a, b) for a in range(6) for b in range(a + 1, 6)]

    for top_i in range(7):
        remaining = [hand[j] for j in range(7) if j != top_i]
        block = settings[top_i * 15:(top_i + 1) * 15]
        for k, (a, b) in enumerate(expected_pairs):
            s = block[k]
            # With a descending input, remaining stays descending; the mid
            # pick is (remaining[a], remaining[b]), already desc.
            expect(
                s.mid[0] == remaining[a] and s.mid[1] == remaining[b],
                f"top_i={top_i}, k={k}, expected mid=({remaining[a]}, {remaining[b]}), got {s.mid}"
            )


def test_decode_rejects_bad_input() -> None:
    hand = parse_hand("As Kh Qd Jc Ts 9h 2d")
    bad = False
    try:
        decode_setting(hand, 105)
    except ValueError:
        bad = True
    expect(bad, "decode_setting should reject index 105")

    bad = False
    try:
        decode_setting(hand[:6], 0)
    except ValueError:
        bad = True
    expect(bad, "decode_setting should reject 6-card hand")


def test_decode_invariance_across_permutations() -> None:
    """
    Sanity: whatever order we supply the hand in, decode_setting(hand, 0)
    always uses hand[0] as top. Not a correctness claim about the Rust engine,
    but a check that our Python mirrors the positional nature of the
    enumeration.
    """
    base = parse_hand("As Kh Qd Jc Ts 9h 2d")
    for perm in list(permutations(range(7)))[:20]:  # sample, not all 5040
        permuted = [base[i] for i in perm]
        s0 = decode_setting(permuted, 0)
        expect(s0.top == permuted[0], f"top mismatch under permutation {perm}")


TESTS = [
    ("card_pack_unpack", test_card_pack_unpack),
    ("parse_hand", test_parse_hand),
    ("setting_count", test_setting_count),
    ("every_setting_uses_all_7", test_every_setting_uses_all_7),
    ("all_settings_unique", test_all_settings_unique),
    ("decode_matches_all_settings", test_decode_matches_all_settings),
    ("tier_sort_order", test_tier_sort_order),
    ("top_card_by_outer_index", test_top_card_by_outer_index),
    ("mid_combo_order", test_mid_combo_order),
    ("decode_rejects_bad_input", test_decode_rejects_bad_input),
    ("decode_invariance_across_permutations", test_decode_invariance_across_permutations),
]


def main() -> int:
    failures = 0
    for name, fn in TESTS:
        print(f"  {name} ... ", end="", flush=True)
        try:
            fn()
            print("ok")
        except SystemExit:
            failures += 1
            print("(see failure above)")
        except Exception as e:
            failures += 1
            print(f"ERROR: {type(e).__name__}: {e}")
    print()
    if failures == 0:
        print(f"PASS: {len(TESTS)} tests")
        return 0
    print(f"FAIL: {failures} of {len(TESTS)} tests")
    return 1


if __name__ == "__main__":
    sys.exit(main())
