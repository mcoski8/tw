"""
Session 36 — strategy_v31a_dt: extends v30 with 4 pair-r4v3 KK/AA-tight
features. 9th gating-template feature family at runtime.
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
from pair_aug_features_gated import compute_pair_aug_gated_for_hand  # noqa: E402
from two_pair_aug_features_gated import compute_two_pair_aug_gated_for_hand  # noqa: E402
from high_only_aug_features_gated import compute_high_only_aug_gated_for_hand  # noqa: E402
from pair_aug_v2_features_gated import compute_pair_r4_features_for_hand  # noqa: E402
from trips_aug_features_gated import compute_trips_features_for_hand  # noqa: E402
from pair_aug_v3_features_gated import compute_pair_r4v3_features_for_hand  # noqa: E402

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v31a_dt_model.npz"

_SUITED_GATED_NAMES = [
    "n_suited_pairs_total_g",
    "max_suited_pair_high_rank_g",
    "max_suited_pair_low_rank_g",
    "has_suited_broadway_pair_g",
    "has_suited_premium_pair_g",
    "n_broadway_in_largest_suit_g",
]
_TRIPS_PAIR_GATED_NAMES = [
    "tp_trip_rank_g", "tp_pair_rank_g", "tp_high_singleton_rank_g",
    "tp_low_singleton_rank_g", "tp_singletons_suited_g", "tp_pair_routing_is_ds_g",
]
_COMPOSITE_GATED_NAMES = [
    "comp_archetype_g", "comp_lower_trip_rank_g", "comp_singleton_rank_g", "comp_higher_pair_rank_g",
]
_PAIR_GATED_NAMES = [
    "pair_kickers_in_pair_suit_max_g", "pair_kickers_in_pair_suit_min_g",
    "pair_default_top_rank_g", "pair_alt_top_rank_g",
    "pair_alt_mid_suited_g", "pair_alt_mid_n_broadway_g",
]
_TWO_PAIR_GATED_NAMES = [
    "t2p_layout_a_bot_is_ds_g", "t2p_n_layout_b_routings_ds_g",
    "t2p_top_singleton_rank_g", "t2p_low_singleton_rank_g",
    "t2p_singletons_max_suit_count_g", "t2p_high_pair_rank_g",
]
_HIGH_ONLY_GATED_NAMES = [
    "ho_n_broadway_in_2nd_suit_g", "ho_n_broadway_in_3rd_suit_g",
    "ho_connectivity_high_g", "ho_n_broadway_pairs_adj_g",
]
_PAIR_R4_GATED_NAMES = [
    "pair_r4_bot_suit_profile_g", "pair_r4_bot_max_rank_g",
    "pair_r4_n_broadway_kickers_g", "pair_r4_n_low_kickers_g",
]
_TRIPS_GATED_NAMES = [
    "trips_b_ds_avail_g", "trips_b_ds_n_routings_g",
    "trips_kickers_max_suit_count_g", "trips_kickers_max_rank_g",
    "trips_n_broadway_kickers_g", "trips_n_low_kickers_g",
]
_PAIR_R4V3_GATED_NAMES = [
    "pair_r4v3_kkaa_dom_suit_count_g",
    "pair_r4v3_kkaa_dom_suit_max_rank_g",
    "pair_r4v3_kkaa_n_high_kickers_g",
    "pair_r4v3_kkaa_pair_suit_alignment_g",
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
    all_gated_sets = [
        set(_SUITED_GATED_NAMES), set(_TRIPS_PAIR_GATED_NAMES), set(_COMPOSITE_GATED_NAMES),
        set(_PAIR_GATED_NAMES), set(_TWO_PAIR_GATED_NAMES), set(_HIGH_ONLY_GATED_NAMES),
        set(_PAIR_R4_GATED_NAMES), set(_TRIPS_GATED_NAMES), set(_PAIR_R4V3_GATED_NAMES),
    ]
    base_columns = [
        c for c in feature_columns
        if not any(c in gs for gs in all_gated_sets)
    ]
    base_index_in_full = [feature_columns.index(c) for c in base_columns]
    suited_index_in_full = [feature_columns.index(c) for c in _SUITED_GATED_NAMES]
    tp_index_in_full = [feature_columns.index(c) for c in _TRIPS_PAIR_GATED_NAMES]
    comp_index_in_full = [feature_columns.index(c) for c in _COMPOSITE_GATED_NAMES]
    pair_index_in_full = [feature_columns.index(c) for c in _PAIR_GATED_NAMES]
    twopair_index_in_full = [feature_columns.index(c) for c in _TWO_PAIR_GATED_NAMES]
    ho_index_in_full = [feature_columns.index(c) for c in _HIGH_ONLY_GATED_NAMES]
    pair_r4_index_in_full = [feature_columns.index(c) for c in _PAIR_R4_GATED_NAMES]
    trips_index_in_full = [feature_columns.index(c) for c in _TRIPS_GATED_NAMES]
    pair_r4v3_index_in_full = [feature_columns.index(c) for c in _PAIR_R4V3_GATED_NAMES]
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
        "pair_index_in_full": pair_index_in_full,
        "twopair_index_in_full": twopair_index_in_full,
        "ho_index_in_full": ho_index_in_full,
        "pair_r4_index_in_full": pair_r4_index_in_full,
        "trips_index_in_full": trips_index_in_full,
        "pair_r4v3_index_in_full": pair_r4v3_index_in_full,
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


def strategy_v31a_dt(hand: np.ndarray) -> int:
    model = load_model()
    base_meta = {"cat_map": model["cat_map"], "feature_columns": model["base_columns"]}
    base_x = compute_feature_vector(hand, base_meta)
    h_uint8 = np.asarray(hand, dtype=np.uint8)
    suited_vals = compute_suited_aug_gated_for_hand(h_uint8)
    tp_vals = compute_trips_pair_aug_gated_for_hand(h_uint8)
    comp_vals = compute_composite_aug_gated_for_hand(h_uint8)
    pair_vals = compute_pair_aug_gated_for_hand(h_uint8)
    twopair_vals = compute_two_pair_aug_gated_for_hand(h_uint8)
    ho_vals = compute_high_only_aug_gated_for_hand(h_uint8)
    pair_r4_vals = compute_pair_r4_features_for_hand(h_uint8)
    trips_vals = compute_trips_features_for_hand(h_uint8)
    pair_r4v3_vals = compute_pair_r4v3_features_for_hand(h_uint8)
    full = np.empty(len(model["feature_columns"]), dtype=np.int16)
    for k, ci in enumerate(model["base_index_in_full"]):
        full[ci] = base_x[k]
    for k, ci in enumerate(model["suited_index_in_full"]):
        full[ci] = suited_vals[k]
    for k, ci in enumerate(model["tp_index_in_full"]):
        full[ci] = tp_vals[k]
    for k, ci in enumerate(model["comp_index_in_full"]):
        full[ci] = comp_vals[k]
    for k, ci in enumerate(model["pair_index_in_full"]):
        full[ci] = pair_vals[k]
    for k, ci in enumerate(model["twopair_index_in_full"]):
        full[ci] = twopair_vals[k]
    for k, ci in enumerate(model["ho_index_in_full"]):
        full[ci] = ho_vals[k]
    for k, ci in enumerate(model["pair_r4_index_in_full"]):
        full[ci] = pair_r4_vals[k]
    for k, ci in enumerate(model["trips_index_in_full"]):
        full[ci] = trips_vals[k]
    for k, ci in enumerate(model["pair_r4v3_index_in_full"]):
        full[ci] = pair_r4v3_vals[k]
    return int(model["leaf_values"][_walk_tree_to_leaf(full, model)].argmax())
