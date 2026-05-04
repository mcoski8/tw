#!/usr/bin/env python3
"""Grade v20 (v18e capacity + gated suited features) vs v18e on full + prefix."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", choices=["full", "prefix"], default="full")
    args = ap.parse_args()
    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}", flush=True)

    from strategy_v18_dt import _walk_tree_to_leaf
    from strategy_v5_dt import compute_feature_vector
    from strategy_v19_gated_dt import strategy_v19_gated_dt, load_model as load_gated

    arr = np.load(REPO / "data" / "v18e_dt_model.npz", allow_pickle=True)
    keys = list(arr["cat_map_keys"]); vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    v18e_model = {
        "children_left": arr["children_left"], "children_right": arr["children_right"],
        "feature": arr["feature"], "threshold": arr["threshold"],
        "leaf_values": arr["leaf_values"], "feature_columns": feature_columns,
        "cat_map": cat_map, "depth": int(arr["depth"]), "n_leaves": int(arr["n_leaves"]),
    }
    feat_meta = {"cat_map": cat_map, "feature_columns": feature_columns}
    def strategy_v18e(hand):
        x = compute_feature_vector(hand, feat_meta)
        return int(v18e_model["leaf_values"][_walk_tree_to_leaf(x, v18e_model)].argmax())

    # Override the v19_gated MODEL_PATH global so it loads the v20 model.
    import strategy_v19_gated_dt as v19g_mod
    v19g_mod.MODEL_PATH = REPO / "data" / "v20_dt_model.npz"
    v19g_mod._MODEL_CACHE = None  # force reload

    strategies = [
        ("v18e   (d=30, ml=5, 274K leaves, 37 feat)", strategy_v18e),
        ("v20    (d=30, ml=5, 308K leaves, 43 feat gated)", strategy_v19_gated_dt),
    ]
    results = []
    for label, fn in strategies:
        print(f"\nGrading {label} ...", flush=True)
        res = grade_strategy(fn, grid, ch, label=label,
                             progress_every=2_000_000 if args.grid == "full" else 200_000)
        print(res.summary(), flush=True)
        results.append(res)

    print("\n" + "=" * 70)
    print(f"SUMMARY ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(*results))
    print(f"\nv20 vs v18e: {results[0].mean_regret - results[1].mean_regret:+.4f}  ≈ ${(results[0].mean_regret - results[1].mean_regret) * 10 * 1000:+,.0f}/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
