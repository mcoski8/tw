"""
Strategy-Grading harness — score any deterministic ``strategy(hand_bytes) -> int``
function against the Full Oracle Grid in seconds.

This is the drop-in replacement for ``tournament_50k.py`` at full 6M-hand
scale. Per Session 24's Decision 044, the grid is the new ground truth;
strategies are graded by how much money they leave on the table relative
to the per-hand argmax EV.

Per hand:
    chosen_idx  = strategy(hand_bytes)         # 0..104
    chosen_ev   = grid.evs[hand, chosen_idx]
    oracle_ev   = grid.evs[hand, :].max()
    regret      = oracle_ev - chosen_ev        # always >= 0

Aggregates:
    mean_regret_overall                          # $ / 1000h vs ceiling
    pct_optimal                                  # frac of hands where chosen == oracle
    by hand_category {high_only, pair, two_pair, trips, trips_pair, three_pair, quads}

Hand categorization mirrors `analysis/scripts/encode_rules.hand_decompose`
but is recomputed from raw bytes here so the harness has no Pandas/Parquet
dependency.

Usage:
    from tw_analysis.grade_strategy import grade_strategy
    from tw_analysis.canonical import read_canonical_hands
    from tw_analysis.oracle_grid import read_oracle_grid

    grid = read_oracle_grid("data/oracle_grid_full_realistic_n200.bin", mode="memmap")
    ch   = read_canonical_hands("data/canonical_hands.bin", mode="memmap")
    res  = grade_strategy(my_strategy_fn, grid, ch, label="my_strategy")
    print(res.summary())
"""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from tw_analysis.canonical import CanonicalHands
from tw_analysis.oracle_grid import OracleGrid

StrategyFn = Callable[[np.ndarray], int]

# ----- Hand categorization (vectorized over canonical_hands.hands) -----


def categorize_hands(hands: np.ndarray) -> np.ndarray:
    """Return an int8 category code for each hand. Vectorized.

    Codes:
       0 = high_only         (no pair, no trip, no quad)
       1 = pair              (exactly one pair)
       2 = two_pair          (exactly two pairs)
       3 = trips             (one trip, no pair)
       4 = trips_pair        (one trip + one pair)
       5 = three_pair        (three pairs)
       6 = quads             (one quad)
       7 = quads_pair / quads_trip / two_trips / etc. (rare composites)
    """
    if hands.ndim != 2 or hands.shape[1] != 7:
        raise ValueError(f"hands must be (N, 7), got {hands.shape}")
    n = hands.shape[0]
    ranks = (hands // 4 + 2).astype(np.int8)  # (N, 7), 2..14
    # Per-hand rank histogram via one-hot + sum
    one_hot = np.zeros((n, 15), dtype=np.int8)
    for k in range(7):
        np.add.at(one_hot, (np.arange(n), ranks[:, k]), 1)
    counts = one_hot[:, 2:15]  # (N, 13)
    n_quads = (counts == 4).sum(axis=1)
    n_trips = (counts == 3).sum(axis=1)
    n_pairs = (counts == 2).sum(axis=1)

    cat = np.full(n, 7, dtype=np.int8)  # default = composite/rare
    is_high_only = (n_quads == 0) & (n_trips == 0) & (n_pairs == 0)
    is_pair = (n_quads == 0) & (n_trips == 0) & (n_pairs == 1)
    is_two_pair = (n_quads == 0) & (n_trips == 0) & (n_pairs == 2)
    is_three_pair = (n_quads == 0) & (n_trips == 0) & (n_pairs == 3)
    is_trips = (n_quads == 0) & (n_trips == 1) & (n_pairs == 0)
    is_trips_pair = (n_quads == 0) & (n_trips == 1) & (n_pairs == 1)
    is_quads = (n_quads == 1) & (n_trips == 0) & (n_pairs == 0)

    cat[is_high_only] = 0
    cat[is_pair] = 1
    cat[is_two_pair] = 2
    cat[is_trips] = 3
    cat[is_trips_pair] = 4
    cat[is_three_pair] = 5
    cat[is_quads] = 6
    return cat


CATEGORY_NAMES = [
    "high_only",
    "pair",
    "two_pair",
    "trips",
    "trips_pair",
    "three_pair",
    "quads",
    "composite",
]


@dataclass(frozen=True)
class CategoryStats:
    name: str
    n_hands: int
    mean_regret: float
    median_regret: float
    p90_regret: float
    p99_regret: float
    pct_optimal: float
    weighted_share_of_total_regret_pct: float


@dataclass(frozen=True)
class GradeResult:
    label: str
    n_hands: int
    n_optimal: int
    pct_optimal: float
    mean_regret: float
    median_regret: float
    p90_regret: float
    p99_regret: float
    max_regret: float
    by_category: list[CategoryStats]
    elapsed_sec: float
    chosen_indices: Optional[np.ndarray] = field(default=None, repr=False)
    regret_per_hand: Optional[np.ndarray] = field(default=None, repr=False)

    def summary(self) -> str:
        ev_to_dollars = 10.0
        lines = [
            f"\nStrategy: {self.label}",
            f"  hands evaluated:   {self.n_hands:,}",
            f"  pct optimal:       {self.pct_optimal:.2f}%  ({self.n_optimal:,} hands matched the grid argmax)",
            f"  mean regret:       {self.mean_regret:+.4f}  "
            f"≈ ${self.mean_regret * ev_to_dollars * 1000:,.0f}/1000h vs ceiling",
            f"  median regret:     {self.median_regret:.4f}",
            f"  p90 regret:        {self.p90_regret:.4f}",
            f"  p99 regret:        {self.p99_regret:.4f}",
            f"  max regret:        {self.max_regret:.4f}",
            f"  wall time:         {self.elapsed_sec:.1f}s",
            "",
            f"  By hand category ($/1000h is mean regret × $10 × 1000):",
            f"  {'category':<14}{'n_hands':>10}{'pct_optimal':>12}{'mean_regret':>14}{'$/1000h':>12}{'share %':>10}",
        ]
        for cs in self.by_category:
            lines.append(
                f"  {cs.name:<14}"
                f"{cs.n_hands:>10,}"
                f"{cs.pct_optimal:>11.1f}%"
                f"{cs.mean_regret:>14.4f}"
                f"{cs.mean_regret * ev_to_dollars * 1000:>11,.0f}"
                f"{cs.weighted_share_of_total_regret_pct:>9.1f}%"
            )
        return "\n".join(lines)


def grade_strategy(
    strategy_fn: StrategyFn,
    grid: OracleGrid,
    canonical_hands: CanonicalHands,
    label: str = "strategy",
    max_hands: Optional[int] = None,
    progress_every: int = 1_000_000,
    keep_per_hand: bool = False,
) -> GradeResult:
    """Score ``strategy_fn`` against the oracle grid.

    `strategy_fn(hand_bytes: np.ndarray) -> int` must return a setting index in
    [0, 105). `hand_bytes` is a (7,) uint8 array in canonical (sorted-ascending)
    order.

    `keep_per_hand=True` retains the chosen-index and regret-per-hand arrays
    on the result so callers can do their own breakdowns (e.g. find the hands
    where this strategy bleeds the most).
    """
    n_records = len(grid)
    if max_hands is not None:
        n_records = min(n_records, max_hands)
    if n_records > len(canonical_hands):
        raise ValueError("grid has more records than canonical-hands file")

    evs = grid.evs  # (N, 105) memmap
    ids = grid.canonical_ids
    hands_arr = canonical_hands.hands
    cats = categorize_hands(np.asarray(hands_arr[:n_records], dtype=np.uint8))

    chosen_idx = np.empty(n_records, dtype=np.int16)
    regrets = np.empty(n_records, dtype=np.float32)
    oracle_ev_per_hand = np.empty(n_records, dtype=np.float32)
    chosen_ev_per_hand = np.empty(n_records, dtype=np.float32)

    t0 = time.time()
    for row_pos in range(n_records):
        canonical_id = int(ids[row_pos])
        if canonical_id != row_pos:
            raise ValueError(
                f"row {row_pos} has canonical_id {canonical_id} (file order broken)"
            )
        hand_bytes = np.asarray(hands_arr[canonical_id], dtype=np.uint8)
        idx = int(strategy_fn(hand_bytes))
        if not 0 <= idx < 105:
            raise ValueError(
                f"strategy returned out-of-range setting_index {idx} on canonical_id {canonical_id}"
            )
        chosen_idx[row_pos] = idx
        ev_row = evs[row_pos]
        chosen_ev_per_hand[row_pos] = ev_row[idx]
        oracle_ev = float(ev_row.max())
        oracle_ev_per_hand[row_pos] = oracle_ev
        regrets[row_pos] = oracle_ev - ev_row[idx]
        if progress_every and (row_pos + 1) % progress_every == 0:
            elapsed = time.time() - t0
            rate = (row_pos + 1) / elapsed
            eta = (n_records - row_pos - 1) / rate
            print(
                f"  scanned {row_pos + 1:>10}/{n_records}  "
                f"rate={rate:>6.0f} hands/s  ETA={eta:>5.1f}s"
            )

    elapsed = time.time() - t0
    n_optimal = int((regrets == 0).sum())

    # Per-category aggregation.
    total_regret_sum = float(regrets.sum())
    by_cat: list[CategoryStats] = []
    for code, name in enumerate(CATEGORY_NAMES):
        mask = cats == code
        n_in_cat = int(mask.sum())
        if n_in_cat == 0:
            continue
        cat_regrets = regrets[mask]
        cat_n_optimal = int((cat_regrets == 0).sum())
        share = (
            100.0 * float(cat_regrets.sum()) / total_regret_sum
            if total_regret_sum > 0
            else 0.0
        )
        by_cat.append(
            CategoryStats(
                name=name,
                n_hands=n_in_cat,
                mean_regret=float(cat_regrets.mean()),
                median_regret=float(np.median(cat_regrets)),
                p90_regret=float(np.percentile(cat_regrets, 90)),
                p99_regret=float(np.percentile(cat_regrets, 99)),
                pct_optimal=100.0 * cat_n_optimal / n_in_cat,
                weighted_share_of_total_regret_pct=share,
            )
        )

    return GradeResult(
        label=label,
        n_hands=n_records,
        n_optimal=n_optimal,
        pct_optimal=100.0 * n_optimal / n_records,
        mean_regret=float(regrets.mean()),
        median_regret=float(np.median(regrets)),
        p90_regret=float(np.percentile(regrets, 90)),
        p99_regret=float(np.percentile(regrets, 99)),
        max_regret=float(regrets.max()),
        by_category=by_cat,
        elapsed_sec=elapsed,
        chosen_indices=chosen_idx if keep_per_hand else None,
        regret_per_hand=regrets if keep_per_hand else None,
    )


def compare_grades(*results: GradeResult) -> str:
    """Side-by-side comparison table for multiple GradeResults."""
    if not results:
        return ""
    lines = [
        f"{'strategy':<40}{'pct_opt':>10}{'mean_regret':>14}{'$/1000h':>12}{'p90':>8}{'wall':>8}",
    ]
    for r in results:
        lines.append(
            f"{r.label:<40}"
            f"{r.pct_optimal:>9.2f}%"
            f"{r.mean_regret:>14.4f}"
            f"{r.mean_regret * 10000:>11,.0f}"
            f"{r.p90_regret:>8.3f}"
            f"{r.elapsed_sec:>7.0f}s"
        )
    return "\n".join(lines)
