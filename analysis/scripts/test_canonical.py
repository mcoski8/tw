"""
Self-tests for ``tw_analysis.canonical`` — mirrors the Rust tests in
``engine/src/bucketing.rs``.

Run:
    python3 analysis/scripts/test_canonical.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

from tw_analysis.canonical import (  # noqa: E402
    SUIT_PERMUTATIONS,
    apply_perm,
    canonicalize,
    is_canonical,
)
from tw_analysis.settings import Card, parse_hand  # noqa: E402


def expect(cond: bool, msg: str) -> None:
    if not cond:
        print(f"  FAIL: {msg}")
        raise SystemExit(1)


def _hand_bytes(s: str) -> np.ndarray:
    cards = parse_hand(s)
    arr = np.array([c.idx for c in cards], dtype=np.uint8)
    arr.sort()
    return arr


def test_suit_permutations_are_24_distinct_bijections() -> None:
    expect(SUIT_PERMUTATIONS.shape == (24, 4), f"shape {SUIT_PERMUTATIONS.shape}")
    seen = set()
    for sigma in SUIT_PERMUTATIONS:
        t = tuple(int(x) for x in sigma)
        expect(set(t) == {0, 1, 2, 3}, f"not a bijection: {t}")
        expect(t not in seen, f"duplicate permutation: {t}")
        seen.add(t)
    expect(len(seen) == 24, f"only {len(seen)} distinct perms")
    # Row 0 is identity
    expect(list(SUIT_PERMUTATIONS[0]) == [0, 1, 2, 3], "row 0 must be identity")


def test_canonicalize_is_idempotent() -> None:
    h = _hand_bytes("As Kh Qd Jc Ts 9h 2d")
    c1 = canonicalize(h)
    c2 = canonicalize(c1)
    expect(np.array_equal(c1, c2), f"not idempotent: {c1} vs {c2}")


def test_canonicalize_agrees_across_suit_permutations() -> None:
    """All 24 relabelings of the same hand must share one canonical form."""
    original = _hand_bytes("As Kh Qd Jc Ts 9h 2d")
    canon = canonicalize(original)
    for sigma in SUIT_PERMUTATIONS:
        relabeled = apply_perm(original, sigma)
        got = canonicalize(relabeled)
        expect(
            np.array_equal(got, canon),
            f"relabeling via {list(sigma)} changed canonical: {got} vs {canon}"
        )


def test_is_canonical_matches_canonicalize_fixpoint() -> None:
    for s in [
        "2c 3d 4h 5s 6c 7d 8h",
        "As Ad Ah Ac Kh Qd Jc",
        "2c 2d 2h 2s 3c 3d 3h",
        "As Kh Qd Jc Ts 9h 2d",
        "As 2c 3c 4c 5c 6c 7c",
    ]:
        h = _hand_bytes(s)
        c = canonicalize(h)
        expected = bool(np.array_equal(h, c))
        got = is_canonical(h)
        expect(got == expected, f"is_canonical mismatch on {s}: got {got}, expected {expected}")


def test_canonical_uses_suit_0() -> None:
    """Any canonical hand must contain suit 0 (clubs) at least once — otherwise
    a relabeling that sends the smallest used suit to 0 would be lex-smaller."""
    h = _hand_bytes("As Kh Qd Jc Ts 9h 2d")
    c = canonicalize(h)
    has_suit0 = any((int(b) & 0b11) == 0 for b in c)
    expect(has_suit0, f"canonical should use suit 0: {c}")


def test_apply_perm_preserves_ranks() -> None:
    h = _hand_bytes("As Kh Qd Jc Ts 9h 2d")
    # Swap hearts (2) with spades (3)
    sigma = np.array([0, 1, 3, 2], dtype=np.uint8)
    p = apply_perm(h, sigma)
    # Same multiset of ranks
    ranks_orig = sorted((int(x) >> 2) for x in h)
    ranks_new = sorted((int(x) >> 2) for x in p)
    expect(ranks_orig == ranks_new, "rank multiset changed")


def test_rank_only_orbit() -> None:
    """7 cards in one suit: only 1 distinct canonical form across orbits."""
    # 7 clubs: "2c 3c 4c 5c 6c 7c 8c"
    h = _hand_bytes("2c 3c 4c 5c 6c 7c 8c")
    c = canonicalize(h)
    # Canonical form places the single-suit hand in suit 0 (clubs).
    expect(all((int(b) & 0b11) == 0 for b in c), f"monotone-suit not in suit 0: {c}")


def test_lex_smallest_under_trivial_case() -> None:
    """For a hand already in canonical-looking form, canonicalize returns it unchanged."""
    # 7 cards entirely in clubs, sorted asc: already minimal.
    h = _hand_bytes("2c 3c 4c 5c 6c 7c 8c")
    c = canonicalize(h)
    expect(np.array_equal(c, h), f"simple case should be self: {c} vs {h}")


def test_canonicalize_rejects_bad_shape() -> None:
    bad = False
    try:
        canonicalize([1, 2, 3])
    except ValueError:
        bad = True
    expect(bad, "canonicalize should reject 3-card input")


TESTS = [
    ("suit_permutations_are_24_distinct_bijections", test_suit_permutations_are_24_distinct_bijections),
    ("canonicalize_is_idempotent", test_canonicalize_is_idempotent),
    ("canonicalize_agrees_across_suit_permutations", test_canonicalize_agrees_across_suit_permutations),
    ("is_canonical_matches_canonicalize_fixpoint", test_is_canonical_matches_canonicalize_fixpoint),
    ("canonical_uses_suit_0", test_canonical_uses_suit_0),
    ("apply_perm_preserves_ranks", test_apply_perm_preserves_ranks),
    ("rank_only_orbit", test_rank_only_orbit),
    ("lex_smallest_under_trivial_case", test_lex_smallest_under_trivial_case),
    ("canonicalize_rejects_bad_shape", test_canonicalize_rejects_bad_shape),
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
