#!/usr/bin/env python3
"""Grade v16 full-grid-trained model only (skip v8/v14, we have those)."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

import numpy as np

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid
from strategy_v5_dt import compute_feature_vector

MODEL_PATH = REPO / "data" / "v16_dt_model_full.npz"
GRID = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = REPO / "data" / "canonical_hands.bin"


def make_v16_full_strategy():
    arr = np.load(MODEL_PATH, allow_pickle=True)
    keys = list(arr["cat_map_keys"])
    vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    children_left = arr["children_left"]
    children_right = arr["children_right"]
    feature = arr["feature"]
    threshold = arr["threshold"]
    leaf_values = arr["leaf_values"]
    feat_meta = {"cat_map": cat_map, "feature_columns": feature_columns}

    def fn(hand: np.ndarray) -> int:
        x = compute_feature_vector(hand, feat_meta)
        node = 0
        while children_left[node] != -1:
            if x[feature[node]] <= threshold[node]:
                node = children_left[node]
            else:
                node = children_right[node]
        return int(leaf_values[node].argmax())

    return fn


def main() -> int:
    print(f"loading model {MODEL_PATH.name} ...", flush=True)
    grid = read_oracle_grid(GRID, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}", flush=True)

    fn = make_v16_full_strategy()
    print(f"\nGrading v16_full (depth=18, min_leaf=100, full-6M trained) ...", flush=True)
    res = grade_strategy(fn, grid, ch, label="v16_full", progress_every=1_000_000)
    print(res.summary(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
