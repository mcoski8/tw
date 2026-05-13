#!/usr/bin/env python3
"""Grade v47_xgb (gradient boosting) vs v44_dt — batch-mode for XGBoost.

The XGBoost model is per-hand-slow at grader scale, so this script bypasses
grade_strategy's per-hand fn and computes chosen-indices via batch
prediction over the canonical X matrix.  Output structure mirrors
GradeResult so compare_grades works.

Usage:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v47_xgb.py \\
      --grid full --baseline v44
"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.grade_strategy import (  # noqa: E402
    CATEGORY_NAMES,
    CategoryStats,
    GradeResult,
    categorize_hands,
    compare_grades,
    grade_strategy,
)
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def grade_from_chosen(chosen: np.ndarray, grid, ch, label: str,
                       max_hands: int = None) -> GradeResult:
    """Mirror grade_strategy's aggregation given a precomputed chosen-indices
    array.

    chosen: (N,) int — per-canonical-id setting choice in [0, 105).
            Length must be >= n_records of grid.
    """
    n_records = len(grid)
    if max_hands is not None:
        n_records = min(n_records, max_hands)
    if n_records > len(ch):
        raise ValueError("grid has more records than canonical-hands file")

    evs = grid.evs
    ids = grid.canonical_ids
    hands_arr = ch.hands
    cats = categorize_hands(np.asarray(hands_arr[:n_records], dtype=np.uint8))

    # Vectorized regret computation. We need:
    #   chosen_ev[row] = evs[row, chosen[ids[row]]]
    #   oracle_ev[row] = evs[row].max()
    print(f"  [grade_from_chosen] aggregating {n_records:,} rows ...",
          flush=True)
    t0 = time.time()

    # Build per-row chosen-index by indirecting through canonical_id ordering
    ids_arr = np.asarray(ids[:n_records], dtype=np.int64)
    # Per-row chosen
    per_row_chosen = chosen[ids_arr].astype(np.int64)

    # Validate canonical_id == row_pos invariant (cheap sanity check)
    if not np.array_equal(ids_arr, np.arange(n_records)):
        raise ValueError("canonical_id != row_pos invariant broken")

    # Compute regret per row. Chunked to avoid loading the whole evs
    # memmap into RAM at once.
    regrets = np.empty(n_records, dtype=np.float32)
    chunk = 500_000
    for start in range(0, n_records, chunk):
        end = min(start + chunk, n_records)
        ev_chunk = np.asarray(evs[start:end], dtype=np.float32)
        # chosen-EV per row in chunk
        rows = np.arange(end - start)
        chosen_ev = ev_chunk[rows, per_row_chosen[start:end]]
        oracle_ev = ev_chunk.max(axis=1)
        regrets[start:end] = oracle_ev - chosen_ev
    elapsed = time.time() - t0

    n_optimal = int((regrets == 0).sum())
    total_regret_sum = float(regrets.sum())
    by_cat: list[CategoryStats] = []
    for code, name in enumerate(CATEGORY_NAMES):
        mask = cats == code
        n_in_cat = int(mask.sum())
        if n_in_cat == 0:
            continue
        cat_regrets = regrets[mask]
        cat_n_optimal = int((cat_regrets == 0).sum())
        share = (100.0 * float(cat_regrets.sum()) / total_regret_sum
                 if total_regret_sum > 0 else 0.0)
        by_cat.append(CategoryStats(
            name=name, n_hands=n_in_cat,
            mean_regret=float(cat_regrets.mean()),
            median_regret=float(np.median(cat_regrets)),
            p90_regret=float(np.percentile(cat_regrets, 90)),
            p99_regret=float(np.percentile(cat_regrets, 99)),
            pct_optimal=100.0 * cat_n_optimal / n_in_cat,
            weighted_share_of_total_regret_pct=share,
        ))

    return GradeResult(
        label=label, n_hands=n_records, n_optimal=n_optimal,
        pct_optimal=100.0 * n_optimal / n_records,
        mean_regret=float(regrets.mean()),
        median_regret=float(np.median(regrets)),
        p90_regret=float(np.percentile(regrets, 90)),
        p99_regret=float(np.percentile(regrets, 99)),
        max_regret=float(regrets.max()),
        by_category=by_cat, elapsed_sec=elapsed,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", choices=["full", "prefix"], default="full")
    ap.add_argument("--baseline", choices=["v44"], default="v44")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    n_records = len(grid)
    progress_every = 2_000_000 if args.grid == "full" else 200_000

    print(f"\n=== v47_xgb (batch) vs {args.baseline}_dt ({args.grid} grid) ===",
          flush=True)
    print(f"  grid records: {n_records:,}  canonical hands: {len(ch):,}",
          flush=True)

    # Step 1 — batch-predict v47_xgb chosen indices for ALL 6M canonical
    # hands (covers both full and prefix grids since the latter is a prefix).
    print(f"\n[1/3] Batch predict v47_xgb chosen indices ...", flush=True)
    from strategy_v47_xgb import predict_all_chosen
    t0 = time.time()
    chosen_v47 = predict_all_chosen()
    print(f"  predicted {len(chosen_v47):,} hands in {time.time()-t0:.1f}s",
          flush=True)

    # Step 2 — grade v47_xgb on selected grid
    print(f"\n[2/3] Grade v47_xgb on {args.grid} grid ...", flush=True)
    res_v47 = grade_from_chosen(chosen_v47, grid, ch,
                                 label="v47_xgb (107-feat boosting)")
    print(res_v47.summary(), flush=True)

    # Step 3 — grade baseline (v44_dt) via per-hand path
    print(f"\n[3/3] Grade {args.baseline}_dt baseline on {args.grid} grid ...",
          flush=True)
    if args.baseline == "v44":
        from strategy_v44_dt import strategy_v44_dt as baseline_fn
        baseline_label = "v44_dt"
    else:
        raise ValueError(f"unsupported baseline: {args.baseline}")
    res_base = grade_strategy(baseline_fn, grid, ch,
                                label=f"{baseline_label} (baseline)",
                                progress_every=progress_every)
    print(res_base.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v47_xgb vs {baseline_label} ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_base, res_v47))
    delta = res_base.mean_regret - res_v47.mean_regret
    print(f"\nv47_xgb vs {baseline_label}: {delta:+.4f}  "
          f"≈ ${delta * 10 * 1000:+,.0f}/1000h", flush=True)

    # Per-category delta
    print(f"\nPer-category $/1000h delta (v47_xgb − v44_dt; "
          f"positive = v47 better):")
    by_cat_base = {c.name: c for c in res_base.by_category}
    by_cat_v47 = {c.name: c for c in res_v47.by_category}
    for name in CATEGORY_NAMES:
        if name not in by_cat_base or name not in by_cat_v47:
            continue
        b = by_cat_base[name]
        v = by_cat_v47[name]
        d_dollars = (b.mean_regret - v.mean_regret) * 10 * 1000
        print(f"  {name:<14} n={b.n_hands:>10,}  "
              f"v44=${b.mean_regret*10000:>5,.0f}  "
              f"v47=${v.mean_regret*10000:>5,.0f}  "
              f"Δ=${d_dollars:>+6,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
