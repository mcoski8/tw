"""
Session 31 — strategy_v24_dt: extends v23 with the 4 composite-gated
aug features. At runtime computes all 3 gated families plus base
vector, walks the saved tree.
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
from suited_aug_features_gated import compute_suited_aug_gated_for_hand  # noqa: E402
from trips_pair_aug_features_gated import compute_trips_pair_aug_gated_for_hand  # noqa: E402
from composite_aug_features_gated import compute_composite_aug_gated_for_hand  # noqa: E402

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v24_dt_model.npz"

_SUITED_GATED_NAMES = [
    "n_suited_pairs_total_g",
    "max_suited_pair_high_rank_g",
    "max_suited_pair_low_rank_g",
    "has_suited_broadway_pair_g",
    "has_suited_premium_pair_g",
    "n_broadway_in_largest_suit_g",
]
_TRIPS_PAIR_GATED_NAMES = [
    "tp_trip_rank_g",
    "tp_pair_rank_g",
    "tp_high_singleton_rank_g",
    "tp_low_singleton_rank_g",
    "tp_singletons_suited_g",
    "tp_pair_routing_is_ds_g",
]
_COMPOSITE_GATED_NAMES = [
    "comp_archetype_g",
    "comp_lower_trip_rank_g",
    "comp_singleton_rank_g",
    "comp_higher_pair_rank_g",
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
    suited_set = set(_SUITED_GATED_NAMES)
    tp_set = set(_TRIPS_PAIR_GATED_NAMES)
    comp_set = set(_COMPOSITE_GATED_NAMES)
    base_columns = [c for c in feature_columns if c not in suited_set and c not in tp_set and c not in comp_set]
    base_index_in_full = [feature_columns.index(c) for c in base_columns]
    suited_index_in_full = [feature_columns.index(c) for c in _SUITED_GATED_NAMES]
    tp_index_in_full = [feature_columns.index(c) for c in _TRIPS_PAIR_GATED_NAMES]
    comp_index_in_full = [feature_columns.index(c) for c in _COMPOSITE_GATED_NAMES]
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
        "tp_index_in_full": tp_index_in_full,
        "comp_index_in_full": comp_index_in_full,
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


def strategy_v24_dt(hand: np.ndarray) -> int:
    model = load_model()
    base_meta = {"cat_map": model["cat_map"], "feature_columns": model["base_columns"]}
    base_x = compute_feature_vector(hand, base_meta)
    h_uint8 = np.asarray(hand, dtype=np.uint8)
    suited_vals = compute_suited_aug_gated_for_hand(h_uint8)
    tp_vals = compute_trips_pair_aug_gated_for_hand(h_uint8)
    comp_vals = compute_composite_aug_gated_for_hand(h_uint8)
    full = np.empty(len(model["feature_columns"]), dtype=np.int16)
    for k, ci in enumerate(model["base_index_in_full"]):
        full[ci] = base_x[k]
    for k, ci in enumerate(model["suited_index_in_full"]):
        full[ci] = suited_vals[k]
    for k, ci in enumerate(model["tp_index_in_full"]):
        full[ci] = tp_vals[k]
    for k, ci in enumerate(model["comp_index_in_full"]):
        full[ci] = comp_vals[k]
    return int(model["leaf_values"][_walk_tree_to_leaf(full, model)].argmax())
