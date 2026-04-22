"""
Reader for ``canonical_hands.bin`` — the ordered list of canonical 7-card
hands produced by ``tw-engine enumerate-canonical``.

File format (all little-endian):

    Header (32 bytes):
      [0..4]   magic              4 bytes, must equal b"TWCH"
      [4..8]   version            u32
      [8..16]  num_hands          u64
      [16..32] reserved           16 bytes (currently zero)

    Body: num_hands × 7 bytes, each row a sorted-ascending packed 7-card
    hand where card index = (rank - 2) * 4 + suit.

Canonicalization (mirrors ``engine/src/bucketing.rs``):
    Two hands that differ only by a permutation of suit labels are
    strategically identical, so every orbit under the 24-element suit group
    S_4 is represented once by its lex-smallest sorted form.

The canonical-hands file is ordered by that same lex comparison, so
``canonical_id`` indexes directly: hands[canonical_id] -> sorted 7 cards.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence, Union

import numpy as np

from tw_analysis.settings import HAND_SIZE, Card

CANON_MAGIC = b"TWCH"
CANON_HEADER_SIZE = 32
CANON_VERSION = 1
CANON_HAND_BYTES = HAND_SIZE  # 7

# All 24 suit permutations in the same order as engine/src/bucketing.rs.
# Row i maps old_suit -> new_suit. Row 0 is identity.
SUIT_PERMUTATIONS: np.ndarray = np.array(
    [
        [0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 3, 2, 1],
        [1, 0, 2, 3], [1, 0, 3, 2], [1, 2, 0, 3], [1, 2, 3, 0], [1, 3, 0, 2], [1, 3, 2, 0],
        [2, 0, 1, 3], [2, 0, 3, 1], [2, 1, 0, 3], [2, 1, 3, 0], [2, 3, 0, 1], [2, 3, 1, 0],
        [3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2], [3, 1, 2, 0], [3, 2, 0, 1], [3, 2, 1, 0],
    ],
    dtype=np.uint8,
)
assert SUIT_PERMUTATIONS.shape == (24, 4)


def apply_perm(sorted_hand: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """
    Apply a suit permutation to a sorted 7-card hand, return the new sorted form.

    ``sorted_hand`` must be a (7,) uint8 array of packed card indices, sorted
    ascending. ``sigma`` must be a (4,) uint8 array sending old_suit -> new_suit.
    """
    ranks = sorted_hand & 0xFC
    suits_in = sorted_hand & 0b11
    suits_out = sigma[suits_in]
    permuted = (ranks | suits_out).astype(np.uint8, copy=False)
    out = np.sort(permuted)
    return out


def canonicalize(hand: Union[Sequence[int], np.ndarray]) -> np.ndarray:
    """
    Return the lex-smallest sorted form of ``hand`` under the 24-element
    suit-permutation group. Mirrors ``engine/src/bucketing.rs::canonicalize``.

    Input: any iterable of 7 packed card indices (0..52), not necessarily sorted.
    Output: a (7,) uint8 array.
    """
    arr = np.asarray(hand, dtype=np.uint8).copy()
    if arr.shape != (HAND_SIZE,):
        raise ValueError(f"hand must be {HAND_SIZE} cards, got shape {arr.shape}")
    arr.sort()
    best = arr
    for i in range(1, 24):  # skip identity
        cand = apply_perm(arr, SUIT_PERMUTATIONS[i])
        if _lex_lt(cand, best):
            best = cand
    return best


def is_canonical(sorted_hand: Union[Sequence[int], np.ndarray]) -> bool:
    """
    Fast check: does this sorted 7-card hand equal its own canonical form?

    Input MUST already be sorted ascending. Mirrors engine's
    ``bucketing.rs::is_canonical`` — returns false as soon as any non-identity
    suit permutation yields a lex-smaller sorted form.
    """
    arr = np.asarray(sorted_hand, dtype=np.uint8)
    if arr.shape != (HAND_SIZE,):
        raise ValueError(f"hand must be {HAND_SIZE} cards, got shape {arr.shape}")
    for i in range(1, 24):
        cand = apply_perm(arr, SUIT_PERMUTATIONS[i])
        if _lex_lt(cand, arr):
            return False
    return True


def _lex_lt(a: np.ndarray, b: np.ndarray) -> bool:
    """Strict lex-less for two (7,) uint8 arrays."""
    for x, y in zip(a.tolist(), b.tolist()):
        if x < y:
            return True
        if x > y:
            return False
    return False


@dataclass(frozen=True)
class CanonicalHeader:
    version: int
    num_hands: int


@dataclass(frozen=True)
class CanonicalHands:
    """Loaded (or memmapped) view of canonical_hands.bin."""

    path: Path
    header: CanonicalHeader
    hands: np.ndarray  # shape (num_hands, 7), uint8

    def __len__(self) -> int:
        return self.header.num_hands

    def hand_bytes(self, canonical_id: int) -> np.ndarray:
        """Return the sorted 7-byte hand at ``canonical_id``."""
        if not 0 <= canonical_id < len(self):
            raise IndexError(f"canonical_id {canonical_id} out of range [0, {len(self)})")
        return self.hands[canonical_id]

    def hand_cards(self, canonical_id: int) -> list[Card]:
        """Return the 7-card hand at ``canonical_id`` as ``Card`` objects in the
        sorted-ascending order the Rust solver processed."""
        return [Card(int(b)) for b in self.hand_bytes(canonical_id)]

    def find(self, hand: Union[Sequence[int], np.ndarray]) -> int:
        """
        Return the canonical_id for the canonical form of ``hand``, or -1 if
        not found. ``hand`` is automatically canonicalized first so any suit
        relabeling of the same hand maps to the same id.

        Uses a binary search over ``hands.tobytes()`` rows; because packed
        card indices are uint8, lexicographic byte-order on 7-byte rows
        matches the engine's lex order on sorted ``[u8; 7]``.
        """
        target_bytes = canonicalize(hand).tobytes()
        lo, hi = 0, len(self.hands)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.hands[mid].tobytes() < target_bytes:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(self.hands) and self.hands[lo].tobytes() == target_bytes:
            return lo
        return -1


def read_canonical_hands(
    path: Union[str, Path],
    mode: Literal["load", "memmap"] = "load",
) -> CanonicalHands:
    """
    Read a canonical-hands file.

    mode="load"   — read body fully into RAM (~42 MB). Default.
    mode="memmap" — zero-copy mapping.
    """
    path = Path(path)
    size = path.stat().st_size
    if size < CANON_HEADER_SIZE:
        raise ValueError(
            f"{path}: file is {size} bytes, smaller than {CANON_HEADER_SIZE}-byte header"
        )

    with open(path, "rb") as f:
        header = f.read(CANON_HEADER_SIZE)

    if header[0:4] != CANON_MAGIC:
        raise ValueError(
            f"{path}: bad magic {header[0:4]!r} (expected {CANON_MAGIC!r})"
        )

    version = int.from_bytes(header[4:8], "little")
    if version != CANON_VERSION:
        raise ValueError(
            f"{path}: version {version} unsupported (reader knows v{CANON_VERSION})"
        )

    num_hands = int.from_bytes(header[8:16], "little")
    expected_size = CANON_HEADER_SIZE + num_hands * CANON_HAND_BYTES
    if size != expected_size:
        raise ValueError(
            f"{path}: size {size} != expected {expected_size} "
            f"(header + num_hands={num_hands} * {CANON_HAND_BYTES})"
        )

    if mode == "memmap":
        hands = np.memmap(
            path,
            dtype=np.uint8,
            mode="r",
            offset=CANON_HEADER_SIZE,
            shape=(num_hands, CANON_HAND_BYTES),
        )
    elif mode == "load":
        with open(path, "rb") as f:
            f.seek(CANON_HEADER_SIZE)
            body = f.read(num_hands * CANON_HAND_BYTES)
        hands = np.frombuffer(body, dtype=np.uint8).reshape(num_hands, CANON_HAND_BYTES)
    else:
        raise ValueError(f"mode must be 'load' or 'memmap', got {mode!r}")

    return CanonicalHands(
        path=path,
        header=CanonicalHeader(version=version, num_hands=num_hands),
        hands=hands,
    )


def validate_canonical_hands(
    ch: CanonicalHands,
    sample_size: int = 1000,
    seed: int = 42,
) -> list[str]:
    """
    Integrity checks against a CanonicalHands view. Full-file checks (monotonic
    lex order, all rows ascending, byte ranges) plus spot-checks on a random
    sample (``is_canonical`` per hand — O(24) per hand, too slow to run on
    all 6M).
    """
    issues: list[str] = []
    hands = ch.hands
    n = len(ch)

    # 1. Byte range
    if n > 0 and int(hands.max()) >= 52:
        issues.append(f"max byte {int(hands.max())} >= 52 (invalid card index)")

    # 2. Each row strictly ascending (no duplicate cards within a hand)
    if n > 0:
        row_diff = np.diff(hands.astype(np.int16), axis=1)
        if int(row_diff.min()) <= 0:
            bad_rows = int((row_diff <= 0).any(axis=1).sum())
            issues.append(f"{bad_rows} rows are not strictly ascending")

    # 3. File is globally lex-ascending (vectorized over 7 byte columns)
    if n >= 2:
        diff = hands[1:].astype(np.int16) - hands[:-1].astype(np.int16)
        # For each adjacent pair, the first column where bytes differ is
        # the leftmost non-zero entry of diff; argmax returns 0 for all-zero
        # rows (duplicates), and we want to flag those too.
        first_nonzero_col = (diff != 0).argmax(axis=1)
        first_diff = diff[np.arange(len(diff)), first_nonzero_col]
        all_zero = (diff == 0).all(axis=1)
        # Sorted ascending means first_diff must be strictly > 0 on every row.
        out_of_order = (first_diff <= 0) | all_zero
        bad_pairs = int(out_of_order.sum())
        if bad_pairs:
            issues.append(f"{bad_pairs} adjacent pairs out of lex order")

    # 4. Spot-check a random sample with is_canonical
    if n > 0:
        rng = np.random.default_rng(seed)
        sample = rng.choice(n, size=min(sample_size, n), replace=False)
        bad: list[int] = []
        for idx in sample:
            if not is_canonical(hands[idx]):
                bad.append(int(idx))
                if len(bad) > 5:
                    break
        if bad:
            issues.append(
                f"{len(bad)}+ sampled rows failed is_canonical (examples: {bad[:5]})"
            )

    return issues
