"""
Session 29 — strategy_v18c_dt: same code path as strategy_v18_dt, loads
the depth=26 / min_samples_leaf=20 model file (data/v18c_dt_model.npz).

This is the new ML champion as of Session 29. Capacity sweep:
  v16   = depth=18, ml=100, 28,790 leaves  → $2,464 full / $1,607 prefix
  v18   = depth=22, ml= 50, 60,651 leaves  → $2,306 full / $1,478 prefix
  v18b  = depth=24, ml= 30, 96,409 leaves  → $2,217 full / $1,343 prefix
  v18c  = depth=26, ml= 20, 124,902 leaves → $2,172 full / $1,261 prefix  ← champion
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v5_dt import compute_feature_vector  # noqa: E402

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v18c_dt_model.npz"


def load_model(path: Optional[Path] = None) -> dict:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if path is None:
        path = MODEL_PATH
    arr = np.load(path, allow_pickle=True)
    keys = list(arr["cat_map_keys"])
    vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    _MODEL_CACHE = {
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
    return _MODEL_CACHE


def _walk_tree_to_leaf(x, model):
    cl = model["children_left"]; cr = model["children_right"]
    feat = model["feature"]; thr = model["threshold"]
    node = 0
    while cl[node] != -1:
        node = cl[node] if x[feat[node]] <= thr[node] else cr[node]
    return node


def strategy_v18c_dt(hand: np.ndarray) -> int:
    model = load_model()
    feat_meta = {
        "cat_map": model["cat_map"],
        "feature_columns": model["feature_columns"],
    }
    x = compute_feature_vector(hand, feat_meta)
    return int(model["leaf_values"][_walk_tree_to_leaf(x, model)].argmax())
