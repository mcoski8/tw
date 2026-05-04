"""
Session 29 — strategy_v19_dt: ML champion candidate. Extends strategy_v18_dt
with 6 suited-broadway aug features (43 features total).

At inference: compute the 37-feature vector via compute_feature_vector
(reused from v5_dt), append the 6 suited-aug features computed inline,
walk the saved tree.
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
from suited_aug_features import compute_suited_aug_for_hand  # noqa: E402

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v19_dt_model.npz"

_SUITED_FEATURE_NAMES = [
    "n_suited_pairs_total",
    "max_suited_pair_high_rank",
    "max_suited_pair_low_rank",
    "has_suited_broadway_pair",
    "has_suited_premium_pair",
    "n_broadway_in_largest_suit",
]


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
    # Pre-split: indices of the 37 base features and 6 suited features in
    # the trained order.
    suited_set = set(_SUITED_FEATURE_NAMES)
    base_columns = [c for c in feature_columns if c not in suited_set]
    base_index_in_full = [feature_columns.index(c) for c in base_columns]
    suited_index_in_full = [feature_columns.index(c) for c in _SUITED_FEATURE_NAMES]
    _MODEL_CACHE = {
        "children_left": arr["children_left"],
        "children_right": arr["children_right"],
        "feature": arr["feature"],
        "threshold": arr["threshold"],
        "leaf_values": arr["leaf_values"],
        "feature_columns": feature_columns,
        "base_columns": base_columns,
        "base_index_in_full": base_index_in_full,
        "suited_index_in_full": suited_index_in_full,
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


def strategy_v19_dt(hand: np.ndarray) -> int:
    model = load_model()
    # Build a base feat_meta dict that compute_feature_vector uses:
    # it expects {"cat_map", "feature_columns"} where feature_columns is
    # the list of BASE column names.
    base_meta = {
        "cat_map": model["cat_map"],
        "feature_columns": model["base_columns"],
    }
    base_x = compute_feature_vector(hand, base_meta)  # 37 ints in base order
    suited_vals = compute_suited_aug_for_hand(np.asarray(hand, dtype=np.uint8))

    # Assemble full 43-vector in the trained column order.
    full = np.empty(len(model["feature_columns"]), dtype=np.int16)
    for k, col_idx in enumerate(model["base_index_in_full"]):
        full[col_idx] = base_x[k]
    for k, col_idx in enumerate(model["suited_index_in_full"]):
        full[col_idx] = suited_vals[k]

    return int(model["leaf_values"][_walk_tree_to_leaf(full, model)].argmax())


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)
    cases = [
        "2c 5d 6h 7s Ts Kd Ad",
        "2c 6c Jd Kh Ks Ac Ad",
        "Ac Ad Ah Kc Kd Qc Qd",
    ]
    for s in cases:
        h = hh(*s.split())
        idx = strategy_v19_dt(h)
        print(f"  {s}  →  v19 setting {idx}")
