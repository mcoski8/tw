"""
Session 55 — strategy_v40_dt: v39 + 4 trips_pair_aug_v2 rank-valued features (91 total).
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
from trips_aug_v2_features_gated import compute_trips_v2_features_for_hand  # noqa: E402
from pair_aug_v5_features_gated import compute_pair_v5_features_for_hand  # noqa: E402
from trips_pair_aug_v2_features_gated import compute_trips_pair_v2_features_for_hand  # noqa: E402

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v40_dt_model.npz"

_SUITED_NAMES = ["n_suited_pairs_total_g","max_suited_pair_high_rank_g","max_suited_pair_low_rank_g","has_suited_broadway_pair_g","has_suited_premium_pair_g","n_broadway_in_largest_suit_g"]
_TP_NAMES = ["tp_trip_rank_g","tp_pair_rank_g","tp_high_singleton_rank_g","tp_low_singleton_rank_g","tp_singletons_suited_g","tp_pair_routing_is_ds_g"]
_COMP_NAMES = ["comp_archetype_g","comp_lower_trip_rank_g","comp_singleton_rank_g","comp_higher_pair_rank_g"]
_PAIR_NAMES = ["pair_kickers_in_pair_suit_max_g","pair_kickers_in_pair_suit_min_g","pair_default_top_rank_g","pair_alt_top_rank_g","pair_alt_mid_suited_g","pair_alt_mid_n_broadway_g"]
_TWOP_NAMES = ["t2p_layout_a_bot_is_ds_g","t2p_n_layout_b_routings_ds_g","t2p_top_singleton_rank_g","t2p_low_singleton_rank_g","t2p_singletons_max_suit_count_g","t2p_high_pair_rank_g"]
_HO_NAMES = ["ho_n_broadway_in_2nd_suit_g","ho_n_broadway_in_3rd_suit_g","ho_connectivity_high_g","ho_n_broadway_pairs_adj_g"]
_PAIR_R4_NAMES = ["pair_r4_bot_suit_profile_g","pair_r4_bot_max_rank_g","pair_r4_n_broadway_kickers_g","pair_r4_n_low_kickers_g"]
_TRIPS_NAMES = ["trips_b_ds_avail_g","trips_b_ds_n_routings_g","trips_kickers_max_suit_count_g","trips_kickers_max_rank_g","trips_n_broadway_kickers_g","trips_n_low_kickers_g"]
_TRIPS_V2_NAMES = ["trips_v2_c_top_advantage_g","trips_v2_b_ds_kicker_max_rank_g","trips_v2_b_ds_kicker_2nd_rank_g","trips_v2_n_kickers_in_trip_suits_g"]
_PAIR_V5_NAMES = ["pair_aug_v5_bot_DS_n_configs_g", "pair_aug_v5_bot_DS_max_top_rank_g",
                   "pair_aug_v5_bot_DS_min_top_rank_g", "pair_aug_v5_bot_DS_max_mid_sum_g"]
_TP_V2_NAMES = ["tp_v2_bot_DS_n_configs_g", "tp_v2_bot_DS_max_top_rank_g",
                 "tp_v2_bot_DS_min_top_rank_g", "tp_v2_bot_DS_max_mid_sum_g"]


def load_model(path: Optional[Path] = None) -> dict:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if path is None:
        path = MODEL_PATH
    arr = np.load(path, allow_pickle=True)
    keys = list(arr["cat_map_keys"]); vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    all_gated = [
        set(_SUITED_NAMES), set(_TP_NAMES), set(_COMP_NAMES), set(_PAIR_NAMES),
        set(_TWOP_NAMES), set(_HO_NAMES), set(_PAIR_R4_NAMES), set(_TRIPS_NAMES),
        set(_TRIPS_V2_NAMES), set(_PAIR_V5_NAMES), set(_TP_V2_NAMES),
    ]
    base_columns = [c for c in feature_columns if not any(c in gs for gs in all_gated)]
    _MODEL_CACHE = {
        "children_left": arr["children_left"], "children_right": arr["children_right"],
        "feature": arr["feature"], "threshold": arr["threshold"],
        "leaf_values": arr["leaf_values"], "feature_columns": feature_columns,
        "base_columns": base_columns,
        "base_index_in_full":     [feature_columns.index(c) for c in base_columns],
        "suited_index_in_full":   [feature_columns.index(c) for c in _SUITED_NAMES],
        "tp_index_in_full":       [feature_columns.index(c) for c in _TP_NAMES],
        "comp_index_in_full":     [feature_columns.index(c) for c in _COMP_NAMES],
        "pair_index_in_full":     [feature_columns.index(c) for c in _PAIR_NAMES],
        "twopair_index_in_full":  [feature_columns.index(c) for c in _TWOP_NAMES],
        "ho_index_in_full":       [feature_columns.index(c) for c in _HO_NAMES],
        "pair_r4_index_in_full":  [feature_columns.index(c) for c in _PAIR_R4_NAMES],
        "trips_index_in_full":    [feature_columns.index(c) for c in _TRIPS_NAMES],
        "trips_v2_index_in_full": [feature_columns.index(c) for c in _TRIPS_V2_NAMES],
        "pair_v5_index_in_full":  [feature_columns.index(c) for c in _PAIR_V5_NAMES],
        "tp_v2_index_in_full":    [feature_columns.index(c) for c in _TP_V2_NAMES],
        "cat_map": cat_map, "depth": int(arr["depth"]), "n_leaves": int(arr["n_leaves"]),
    }
    return _MODEL_CACHE


def _walk(x, model):
    cl = model["children_left"]; cr = model["children_right"]
    feat = model["feature"]; thr = model["threshold"]
    node = 0
    while cl[node] != -1:
        node = cl[node] if x[feat[node]] <= thr[node] else cr[node]
    return node


def strategy_v40_dt(hand: np.ndarray) -> int:
    model = load_model()
    base_meta = {"cat_map": model["cat_map"], "feature_columns": model["base_columns"]}
    base_x = compute_feature_vector(hand, base_meta)
    h = np.asarray(hand, dtype=np.uint8)
    suited = compute_suited_aug_gated_for_hand(h)
    tp = compute_trips_pair_aug_gated_for_hand(h)
    comp = compute_composite_aug_gated_for_hand(h)
    pair = compute_pair_aug_gated_for_hand(h)
    twopair = compute_two_pair_aug_gated_for_hand(h)
    ho = compute_high_only_aug_gated_for_hand(h)
    pair_r4 = compute_pair_r4_features_for_hand(h)
    trips = compute_trips_features_for_hand(h)
    trips_v2 = compute_trips_v2_features_for_hand(h)
    pair_v5 = compute_pair_v5_features_for_hand(h)
    tp_v2 = compute_trips_pair_v2_features_for_hand(h)

    full = np.empty(len(model["feature_columns"]), dtype=np.int16)
    for k, ci in enumerate(model["base_index_in_full"]):     full[ci] = base_x[k]
    for k, ci in enumerate(model["suited_index_in_full"]):   full[ci] = suited[k]
    for k, ci in enumerate(model["tp_index_in_full"]):       full[ci] = tp[k]
    for k, ci in enumerate(model["comp_index_in_full"]):     full[ci] = comp[k]
    for k, ci in enumerate(model["pair_index_in_full"]):     full[ci] = pair[k]
    for k, ci in enumerate(model["twopair_index_in_full"]):  full[ci] = twopair[k]
    for k, ci in enumerate(model["ho_index_in_full"]):       full[ci] = ho[k]
    for k, ci in enumerate(model["pair_r4_index_in_full"]):  full[ci] = pair_r4[k]
    for k, ci in enumerate(model["trips_index_in_full"]):    full[ci] = trips[k]
    for k, ci in enumerate(model["trips_v2_index_in_full"]): full[ci] = trips_v2[k]
    for k, ci in enumerate(model["pair_v5_index_in_full"]):  full[ci] = pair_v5[k]
    for k, ci in enumerate(model["tp_v2_index_in_full"]):    full[ci] = tp_v2[k]
    return int(model["leaf_values"][_walk(full, model)].argmax())
