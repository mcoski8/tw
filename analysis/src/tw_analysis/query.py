"""
Query Harness for the Full Oracle Grid (Decision 043, Session 24).

The grid stores all 105 setting EVs for every canonical 7-card hand against
the realistic-human mixture profile. This module lets the user pose
poker-domain questions directly to that data — e.g. "is double-suited
unconnected bot better than rainbow connected bot?" — without writing
new MC compute.

Design
------
- `setting_features_for_hand(canonical_id_or_hand_bytes)` returns a dict of
  per-setting feature arrays (each shape (105,)) computed by enumerating
  all 105 settings via `decode_setting`.
- `compare_setting_classes(...)` is the headline API: for each hand, pick
  the max-EV setting in each of two filter classes; report aggregate Δ.
- Bring-your-own-filter: a "filter" is a function that takes the
  per-setting features dict and returns a boolean numpy array of shape
  (105,). Combinators `all_of`, `any_of`, `not_` compose them.

Performance
-----------
Per-hand work is O(105) feature evaluations + a max over 105 EVs for each
filter. At 6M hands × 2 filters, this is ~1.3B arithmetic ops — about a
minute in numpy. For repeat queries, cache the features array per hand
or vectorize the loop.

User-locked initial questions (from CURRENT_PHASE.md):
  - DS unconnected vs connected unsuited bot — which makes more money?
  - DS unconnected vs single-suited connected bot
  - Generally favoring DS over connectivity?
  - When does pair-to-mid become a blunder for bot DS preservation?
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np

from tw_analysis.canonical import CanonicalHands
from tw_analysis.oracle_grid import OracleGrid
from tw_analysis.settings import (
    Card,
    HandSetting,
    NUM_SETTINGS,
    all_settings as enumerate_settings,
)

# --- Setting-enumeration index table (vectorized features) ----------------

def _build_setting_hand_indices() -> np.ndarray:
    """Precompute, for every setting_index 0..104, the 7 hand-index positions
    that make up that setting in [top, mid_a, mid_b, bot_a, bot_b, bot_c, bot_d]
    order (no within-tier sort applied — features below are sort-independent).

    Mirrors the enumeration in ``settings.decode_setting``.
    """
    table = np.empty((NUM_SETTINGS, 7), dtype=np.uint8)
    mid_pairs = [(a, b) for a in range(6) for b in range(a + 1, 6)]
    for idx in range(NUM_SETTINGS):
        top_i, mid_combo_i = divmod(idx, 15)
        a, b = mid_pairs[mid_combo_i]
        remaining = [j for j in range(7) if j != top_i]
        mid_a = remaining[a]
        mid_b = remaining[b]
        bot = [remaining[j] for j in range(6) if j != a and j != b]
        table[idx] = [top_i, mid_a, mid_b, *bot]
    return table


SETTING_HAND_INDICES: np.ndarray = _build_setting_hand_indices()
assert SETTING_HAND_INDICES.shape == (NUM_SETTINGS, 7)


def setting_features_from_bytes(hand_bytes: np.ndarray) -> "SettingFeatures":
    """Vectorized feature extraction for a single 7-card hand.

    ``hand_bytes`` is a (7,) uint8 array of packed card indices in the
    canonical-hand order. Returns the same SettingFeatures dataclass as
    ``setting_features_for_hand`` but computed entirely with numpy ops —
    ~100x faster than the Python-object path.
    """
    if hand_bytes.shape != (7,):
        raise ValueError(f"hand_bytes must be (7,), got {hand_bytes.shape}")
    permuted = hand_bytes[SETTING_HAND_INDICES]  # (105, 7) uint8

    top_byte = permuted[:, 0]
    mid_bytes = permuted[:, 1:3]
    bot_bytes = permuted[:, 3:]

    top_rank = (top_byte // 4 + 2).astype(np.int8)
    mid_ranks = (mid_bytes // 4 + 2).astype(np.int8)
    bot_ranks = (bot_bytes // 4 + 2).astype(np.int8)
    bot_suits = bot_bytes & 0b11

    mid_is_pair_arr = mid_ranks[:, 0] == mid_ranks[:, 1]
    mid_pair_rank = np.where(mid_is_pair_arr, mid_ranks[:, 0], 0).astype(np.int8)
    top_is_ace = (top_rank == 14)
    bot_has_ace = (bot_ranks == 14).any(axis=1)

    # Bot suit profile: count suits, sort descending, classify the (max, 2nd) pair.
    suit0 = (bot_suits == 0).sum(axis=1)
    suit1 = (bot_suits == 1).sum(axis=1)
    suit2 = (bot_suits == 2).sum(axis=1)
    suit3 = (bot_suits == 3).sum(axis=1)
    counts_stacked = np.stack([suit0, suit1, suit2, suit3], axis=1)
    sorted_desc = -np.sort(-counts_stacked, axis=1)
    top1 = sorted_desc[:, 0]
    top2 = sorted_desc[:, 1]
    profile = np.full(NUM_SETTINGS, -1, dtype=np.int8)
    profile[(top1 == 2) & (top2 == 2)] = SUIT_PROFILE_DS
    profile[(top1 == 2) & (top2 == 1)] = SUIT_PROFILE_SS
    profile[(top1 == 1) & (top2 == 1)] = SUIT_PROFILE_RAINBOW
    profile[(top1 == 3) & (top2 == 1)] = SUIT_PROFILE_THREE_ONE
    profile[(top1 == 4) & (top2 == 0)] = SUIT_PROFILE_FOUR_FLUSH
    if (profile == -1).any():
        # Defensive: should never hit a non-classifiable distribution.
        idx = int((profile == -1).argmax())
        raise ValueError(
            f"unclassifiable bot suit distribution at setting {idx}: "
            f"{counts_stacked[idx]}"
        )

    # Bot longest run of consecutive distinct ranks. Vectorized via a
    # presence vector across rank slots 2..14 (13 ranks).
    presence = np.zeros((NUM_SETTINGS, 13), dtype=np.uint8)
    for k in range(4):
        np.add.at(presence, (np.arange(NUM_SETTINGS), bot_ranks[:, k] - 2), 1)
    binary_presence = (presence > 0).astype(np.int8)
    # Walk the 13 columns, accumulating run lengths; reset on zero.
    longest = np.zeros(NUM_SETTINGS, dtype=np.int8)
    cur = np.zeros(NUM_SETTINGS, dtype=np.int8)
    for r in range(13):
        col = binary_presence[:, r]
        cur = np.where(col == 1, cur + 1, 0)
        longest = np.maximum(longest, cur)
    bot_longest_run = longest

    # Bot high-card count (rank >= 10).
    bot_high_count = (bot_ranks >= 10).sum(axis=1).astype(np.int8)

    # Bot pair rank: highest rank with count >= 2 in bot.
    pair_mask = presence >= 2  # (105, 13)
    # Multiply by rank value (rank = col + 2), then take max along axis=1.
    rank_lookup = np.arange(2, 15, dtype=np.int8)  # ranks 2..14
    pair_rank_per_col = np.where(pair_mask, rank_lookup, 0)
    bot_pair_rank = pair_rank_per_col.max(axis=1).astype(np.int8)

    return SettingFeatures(
        top_rank=top_rank,
        mid_pair_rank=mid_pair_rank,
        mid_is_pair=mid_is_pair_arr,
        bot_suit_profile=profile,
        bot_longest_run=bot_longest_run,
        bot_high_count=bot_high_count,
        bot_pair_rank=bot_pair_rank,
        bot_top_pair_rank=bot_pair_rank,
        bot_has_ace=bot_has_ace,
        top_is_ace=top_is_ace,
    )


# --- Per-setting feature codes ---------------------------------------------

# Bot suit-profile codes. Higher number = "tighter" Omaha 2+3 fit.
SUIT_PROFILE_RAINBOW = 0    # 1+1+1+1
SUIT_PROFILE_SS = 1         # 2+1+1
SUIT_PROFILE_DS = 2         # 2+2 (best for Omaha)
SUIT_PROFILE_THREE_ONE = 3  # 3+1 (wastes 1 card under 2+3)
SUIT_PROFILE_FOUR_FLUSH = 4 # 4+0 (wastes 2)

SUIT_PROFILE_LABELS = {
    SUIT_PROFILE_RAINBOW: "rainbow",
    SUIT_PROFILE_SS: "single-suited (2+1+1)",
    SUIT_PROFILE_DS: "double-suited (2+2)",
    SUIT_PROFILE_THREE_ONE: "three-one (3+1)",
    SUIT_PROFILE_FOUR_FLUSH: "four-flush (4+0)",
}


# --- Feature extraction ----------------------------------------------------


def _bot_suit_profile_one(bot: Sequence[Card]) -> int:
    counts = [0, 0, 0, 0]
    for c in bot:
        counts[c.suit] += 1
    s = sorted(counts, reverse=True)
    if s == [2, 2, 0, 0]:
        return SUIT_PROFILE_DS
    if s == [2, 1, 1, 0]:
        return SUIT_PROFILE_SS
    if s == [1, 1, 1, 1]:
        return SUIT_PROFILE_RAINBOW
    if s == [3, 1, 0, 0]:
        return SUIT_PROFILE_THREE_ONE
    if s == [4, 0, 0, 0]:
        return SUIT_PROFILE_FOUR_FLUSH
    raise ValueError(f"unexpected suit count {s}")


def _bot_longest_run_one(bot: Sequence[Card]) -> int:
    """Longest run of consecutive distinct ranks in the 4-card bot."""
    ranks = sorted({c.rank for c in bot})
    if not ranks:
        return 0
    longest = 1
    cur = 1
    for i in range(1, len(ranks)):
        if ranks[i] == ranks[i - 1] + 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1
    return longest


def _bot_high_count_one(bot: Sequence[Card], threshold: int = 10) -> int:
    return sum(1 for c in bot if c.rank >= threshold)


def _pair_rank_one(cards: Sequence[Card]) -> int:
    """Highest rank that appears at least twice in `cards`. 0 if no pair."""
    counts: dict[int, int] = {}
    for c in cards:
        counts[c.rank] = counts.get(c.rank, 0) + 1
    paired = [r for r, n in counts.items() if n >= 2]
    return max(paired) if paired else 0


@dataclass(frozen=True)
class SettingFeatures:
    """Per-setting feature arrays for one canonical hand. Each array has
    shape (105,), aligned to setting-index order."""

    top_rank: np.ndarray              # int8, the rank of the top card
    mid_pair_rank: np.ndarray         # int8, 0 if mid is not a pair
    mid_is_pair: np.ndarray           # bool
    bot_suit_profile: np.ndarray      # int8, see SUIT_PROFILE_*
    bot_longest_run: np.ndarray       # int8, 1..4
    bot_high_count: np.ndarray        # int8, count of bot cards with rank>=10
    bot_pair_rank: np.ndarray         # int8, 0 if no pair in bot
    bot_top_pair_rank: np.ndarray     # int8, top pair (highest pair) in bot, 0 if none
    bot_has_ace: np.ndarray           # bool
    top_is_ace: np.ndarray            # bool


def setting_features_for_hand(hand: Sequence[Card]) -> SettingFeatures:
    """Compute the per-setting feature arrays for a single 7-card hand.

    `hand` must be in the same order the engine used (canonical order).
    Returns arrays of shape (105,) aligned to setting-index.
    """
    if len(hand) != 7:
        raise ValueError(f"hand must be 7 cards, got {len(hand)}")
    settings = enumerate_settings(hand)
    n = len(settings)
    assert n == NUM_SETTINGS

    top_rank = np.empty(n, dtype=np.int8)
    mid_pair_rank = np.zeros(n, dtype=np.int8)
    mid_is_pair = np.zeros(n, dtype=bool)
    bot_suit_profile = np.empty(n, dtype=np.int8)
    bot_longest_run = np.empty(n, dtype=np.int8)
    bot_high_count = np.empty(n, dtype=np.int8)
    bot_pair_rank = np.zeros(n, dtype=np.int8)
    bot_top_pair_rank = np.zeros(n, dtype=np.int8)
    bot_has_ace = np.zeros(n, dtype=bool)
    top_is_ace = np.zeros(n, dtype=bool)

    for i, s in enumerate(settings):
        top_rank[i] = s.top.rank
        top_is_ace[i] = s.top.rank == 14
        if s.mid[0].rank == s.mid[1].rank:
            mid_is_pair[i] = True
            mid_pair_rank[i] = s.mid[0].rank
        bot_suit_profile[i] = _bot_suit_profile_one(s.bot)
        bot_longest_run[i] = _bot_longest_run_one(s.bot)
        bot_high_count[i] = _bot_high_count_one(s.bot)
        bot_pair_rank[i] = _pair_rank_one(s.bot)
        bot_top_pair_rank[i] = bot_pair_rank[i]  # alias for clarity
        bot_has_ace[i] = any(c.rank == 14 for c in s.bot)

    return SettingFeatures(
        top_rank=top_rank,
        mid_pair_rank=mid_pair_rank,
        mid_is_pair=mid_is_pair,
        bot_suit_profile=bot_suit_profile,
        bot_longest_run=bot_longest_run,
        bot_high_count=bot_high_count,
        bot_pair_rank=bot_pair_rank,
        bot_top_pair_rank=bot_top_pair_rank,
        bot_has_ace=bot_has_ace,
        top_is_ace=top_is_ace,
    )


# --- Filter primitives -----------------------------------------------------

# A "filter" takes a SettingFeatures and returns a (105,) bool array.
SettingFilter = Callable[[SettingFeatures], np.ndarray]


def bot_suit_profile_eq(code: int) -> SettingFilter:
    return lambda f: f.bot_suit_profile == code


def bot_longest_run_at_least(n: int) -> SettingFilter:
    return lambda f: f.bot_longest_run >= n


def bot_longest_run_at_most(n: int) -> SettingFilter:
    return lambda f: f.bot_longest_run <= n


def mid_is_pair() -> SettingFilter:
    return lambda f: f.mid_is_pair


def mid_pair_rank_eq(rank: int) -> SettingFilter:
    return lambda f: (f.mid_is_pair) & (f.mid_pair_rank == rank)


def top_rank_eq(rank: int) -> SettingFilter:
    return lambda f: f.top_rank == rank


def top_is_ace() -> SettingFilter:
    return lambda f: f.top_is_ace


def all_of(*filters: SettingFilter) -> SettingFilter:
    def combined(f: SettingFeatures) -> np.ndarray:
        out = np.ones(NUM_SETTINGS, dtype=bool)
        for filt in filters:
            out &= filt(f)
        return out
    return combined


def any_of(*filters: SettingFilter) -> SettingFilter:
    def combined(f: SettingFeatures) -> np.ndarray:
        out = np.zeros(NUM_SETTINGS, dtype=bool)
        for filt in filters:
            out |= filt(f)
        return out
    return combined


def not_(filt: SettingFilter) -> SettingFilter:
    return lambda f: ~filt(f)


# --- Comparison API --------------------------------------------------------


@dataclass(frozen=True)
class CompareResult:
    label_a: str
    label_b: str
    n_hands_total: int
    n_hands_both_available: int
    n_hands_only_a: int
    n_hands_only_b: int
    n_hands_neither: int
    mean_delta: float
    median_delta: float
    p10_delta: float
    p90_delta: float
    pct_a_wins: float
    pct_b_wins: float
    pct_chop: float
    sample_canonical_ids_top10_a_wins: list[int]
    sample_canonical_ids_top10_b_wins: list[int]

    def summary(self) -> str:
        ev_to_dollars = 10.0  # $/EV-pt, project convention
        n = self.n_hands_both_available
        return (
            f"\n{'A':>5}: {self.label_a}\n"
            f"{'B':>5}: {self.label_b}\n"
            f"{'-' * 60}\n"
            f"hands available for comparison: {n} / {self.n_hands_total} "
            f"({100.0 * n / max(self.n_hands_total, 1):.1f}%)\n"
            f"  only A available:    {self.n_hands_only_a:>10}\n"
            f"  only B available:    {self.n_hands_only_b:>10}\n"
            f"  neither available:   {self.n_hands_neither:>10}\n"
            f"\n  mean ΔEV (A − B):    {self.mean_delta:+.4f}  "
            f"  ≈ ${self.mean_delta * ev_to_dollars * 1000:+,.0f} per 1,000 hands\n"
            f"  median ΔEV:          {self.median_delta:+.4f}\n"
            f"  p10..p90:            {self.p10_delta:+.4f} .. {self.p90_delta:+.4f}\n"
            f"  A wins / chop / B:   {self.pct_a_wins:.1f}% / {self.pct_chop:.1f}% / {self.pct_b_wins:.1f}%\n"
            f"\nA-wins-by-most canonical_ids: {self.sample_canonical_ids_top10_a_wins}\n"
            f"B-wins-by-most canonical_ids: {self.sample_canonical_ids_top10_b_wins}\n"
        )


def compare_setting_classes(
    grid: OracleGrid,
    canonical_hands: CanonicalHands,
    filter_a: SettingFilter,
    filter_b: SettingFilter,
    label_a: str,
    label_b: str,
    hand_filter: Optional[Callable[[Sequence[Card]], bool]] = None,
    max_hands: Optional[int] = None,
    progress_every: int = 50_000,
) -> CompareResult:
    """For each hand, find the max-EV setting in each class and compare.

    A hand contributes to the comparison only if it has at least one
    setting matching filter_a AND at least one matching filter_b.
    """
    n_records = len(grid)
    if max_hands is not None:
        n_records = min(n_records, max_hands)
    if n_records > len(canonical_hands):
        raise ValueError("grid has more records than canonical-hands file")

    deltas: list[float] = []
    contributing_ids: list[int] = []
    n_only_a = 0
    n_only_b = 0
    n_neither = 0
    n_seen = 0

    evs_arr = grid.evs
    ids_arr = grid.canonical_ids
    hands_arr = canonical_hands.hands

    for row_pos in range(n_records):
        canonical_id = int(ids_arr[row_pos])
        if canonical_id != row_pos:
            raise ValueError(
                f"row {row_pos} has canonical_id {canonical_id} (file order broken)"
            )
        hand_bytes = np.asarray(hands_arr[canonical_id], dtype=np.uint8)
        if hand_filter is not None:
            hand = [Card(int(b)) for b in hand_bytes]
            if not hand_filter(hand):
                continue
        n_seen += 1
        feats = setting_features_from_bytes(hand_bytes)
        mask_a = filter_a(feats)
        mask_b = filter_b(feats)
        evs = evs_arr[row_pos]
        a_avail = bool(mask_a.any())
        b_avail = bool(mask_b.any())
        if a_avail and b_avail:
            ev_a = float(evs[mask_a].max())
            ev_b = float(evs[mask_b].max())
            deltas.append(ev_a - ev_b)
            contributing_ids.append(canonical_id)
        elif a_avail and not b_avail:
            n_only_a += 1
        elif b_avail and not a_avail:
            n_only_b += 1
        else:
            n_neither += 1

        if progress_every and (row_pos + 1) % progress_every == 0:
            print(f"  scanned {row_pos + 1:>10}/{n_records}  contributing={len(deltas):>10}")

    deltas_arr = np.asarray(deltas, dtype=np.float64)
    if len(deltas_arr) == 0:
        return CompareResult(
            label_a=label_a,
            label_b=label_b,
            n_hands_total=n_seen,
            n_hands_both_available=0,
            n_hands_only_a=n_only_a,
            n_hands_only_b=n_only_b,
            n_hands_neither=n_neither,
            mean_delta=0.0,
            median_delta=0.0,
            p10_delta=0.0,
            p90_delta=0.0,
            pct_a_wins=0.0,
            pct_b_wins=0.0,
            pct_chop=0.0,
            sample_canonical_ids_top10_a_wins=[],
            sample_canonical_ids_top10_b_wins=[],
        )

    pct_a_wins = 100.0 * float((deltas_arr > 0).sum()) / len(deltas_arr)
    pct_b_wins = 100.0 * float((deltas_arr < 0).sum()) / len(deltas_arr)
    pct_chop = 100.0 * float((deltas_arr == 0).sum()) / len(deltas_arr)

    order_a_top = np.argsort(-deltas_arr)[:10]
    order_b_top = np.argsort(deltas_arr)[:10]
    a_top_ids = [contributing_ids[int(i)] for i in order_a_top]
    b_top_ids = [contributing_ids[int(i)] for i in order_b_top]

    return CompareResult(
        label_a=label_a,
        label_b=label_b,
        n_hands_total=n_seen,
        n_hands_both_available=len(deltas_arr),
        n_hands_only_a=n_only_a,
        n_hands_only_b=n_only_b,
        n_hands_neither=n_neither,
        mean_delta=float(deltas_arr.mean()),
        median_delta=float(np.median(deltas_arr)),
        p10_delta=float(np.percentile(deltas_arr, 10)),
        p90_delta=float(np.percentile(deltas_arr, 90)),
        pct_a_wins=pct_a_wins,
        pct_b_wins=pct_b_wins,
        pct_chop=pct_chop,
        sample_canonical_ids_top10_a_wins=a_top_ids,
        sample_canonical_ids_top10_b_wins=b_top_ids,
    )
