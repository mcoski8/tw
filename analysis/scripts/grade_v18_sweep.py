#!/usr/bin/env python3
"""Grade v18 hyperparameter sweep: v16 baseline vs v18 (d=22, ml=50) vs
v18b (d=24, ml=30)."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Optional

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def make_strategy_for_model(model_path: Path):
    """Returns a strategy function that walks the saved DT at model_path.
    Reuses strategy_v18_dt's compute path but with the supplied model."""
    from strategy_v18_dt import _walk_tree_to_leaf
    from strategy_v5_dt import compute_feature_vector
    arr = np.load(model_path, allow_pickle=True)
    keys = list(arr["cat_map_keys"])
    vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    model = {
        "children_left": arr["children_left"],
        "children_right": arr["children_right"],
        "feature": arr["feature"],
        "threshold": arr["threshold"],
        "leaf_values": arr["leaf_values"],
        "feature_columns": feature_columns,
        "cat_map": cat_map,
        "depth": int(arr["depth"]),
        "n_leaves": int(arr["n_leaves"]),
    }
    feat_meta = {"cat_map": model["cat_map"], "feature_columns": model["feature_columns"]}

    def strategy(hand: np.ndarray) -> int:
        x = compute_feature_vector(hand, feat_meta)
        return int(model["leaf_values"][_walk_tree_to_leaf(x, model)].argmax())
    return strategy


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", choices=["full", "prefix"], default="full")
    args = ap.parse_args()

    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}  Canonical: {len(ch):,}", flush=True)

    strategies = []
    for label, mp in [
        ("v16_dt (d=18, ml=100, 28K leaves)", REPO / "data" / "v16_dt_model.npz"),
        ("v18_dt (d=22, ml=50, 60K leaves)", REPO / "data" / "v18_dt_model.npz"),
        ("v18b   (d=24, ml=30, 96K leaves)", REPO / "data" / "v18b_dt_model.npz"),
        ("v18c   (d=26, ml=20, 125K leaves)", REPO / "data" / "v18c_dt_model.npz"),
        ("v18d   (d=28, ml=10, 193K leaves)", REPO / "data" / "v18d_dt_model.npz"),
    ]:
        if not mp.exists():
            print(f"  SKIP {label}: model not found at {mp}", flush=True)
            continue
        strategies.append((label, make_strategy_for_model(mp)))

    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label, progress_every=2_000_000 if args.grid == "full" else 200_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(*results))
    if len(results) >= 2:
        print(f"\nv18 vs v16:  {results[0].mean_regret - results[1].mean_regret:+.4f}  ≈ ${(results[0].mean_regret - results[1].mean_regret) * 10 * 1000:+,.0f}/1000h")
    if len(results) >= 3:
        print(f"v18b vs v18: {results[1].mean_regret - results[2].mean_regret:+.4f}  ≈ ${(results[1].mean_regret - results[2].mean_regret) * 10 * 1000:+,.0f}/1000h")
        print(f"v18b vs v16: {results[0].mean_regret - results[2].mean_regret:+.4f}  ≈ ${(results[0].mean_regret - results[2].mean_regret) * 10 * 1000:+,.0f}/1000h")
    if len(results) >= 4:
        print(f"v18c vs v18b: {results[2].mean_regret - results[3].mean_regret:+.4f}  ≈ ${(results[2].mean_regret - results[3].mean_regret) * 10 * 1000:+,.0f}/1000h")
        print(f"v18c vs v16:  {results[0].mean_regret - results[3].mean_regret:+.4f}  ≈ ${(results[0].mean_regret - results[3].mean_regret) * 10 * 1000:+,.0f}/1000h")
    if len(results) >= 5:
        print(f"v18d vs v18c: {results[3].mean_regret - results[4].mean_regret:+.4f}  ≈ ${(results[3].mean_regret - results[4].mean_regret) * 10 * 1000:+,.0f}/1000h")
        print(f"v18d vs v16:  {results[0].mean_regret - results[4].mean_regret:+.4f}  ≈ ${(results[0].mean_regret - results[4].mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
