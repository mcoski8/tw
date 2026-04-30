"""
Session 20 — strategy_v5_dt: production-ready strategy callable that walks
the saved depth-15 DT (37 features, 18,399 leaves) trained in Session 19.

Provides:
    strategy_v5_dt(hand: np.ndarray) -> int

where ``hand`` is a sorted 7-byte uint8 array of card bytes (matching the
strategy_v3 contract in encode_rules.py). Returns a setting_index in 0..104.

Feature compute is done from-scratch on the hand bytes, using:
  - tw_analysis.features.hand_features_scalar  (28 baseline features, less category_id which we override)
  - pair_aug_features.compute_pair_aug_for_hand  (3 pair-aug features)
  - high_only_aug_features.compute_high_only_aug_for_hand  (3 high-aug features)
  - two_pair_aug_features.compute_two_pair_aug_for_hand  (3 two_pair-aug features)

Plus the 7 derived feature columns (can_make_ds_bot etc.) which are pure
numpy comparisons over the baseline columns.

CATEGORY_ID OVERRIDE: dt_phase1_aug3.py uses an alphabetical category→id
mapping ({'high_only':0, 'pair':1, 'quads':2, 'three_pair':3, 'trips':4,
'trips_pair':5, 'two_pair':6}) which differs from the natural CATEGORY_TO_ID
ordering in tw_analysis.features. We use the saved cat_map from
v5_dt_model.npz to remap the category string to the id used at training time.
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

from tw_analysis.features import (  # noqa: E402
    CATEGORY_HIGH_ONLY, CATEGORY_PAIR, CATEGORY_TWO_PAIR, CATEGORY_THREE_PAIR,
    CATEGORY_TRIPS, CATEGORY_TRIPS_PAIR, CATEGORY_QUADS,
    hand_features_scalar,
)
from pair_aug_features import compute_pair_aug_for_hand  # noqa: E402
from high_only_aug_features import compute_high_only_aug_for_hand  # noqa: E402
from two_pair_aug_features import compute_two_pair_aug_for_hand  # noqa: E402


_MODEL_CACHE: Optional[dict] = None


def _category_string_for_hand(features: dict) -> str:
    """Recover the category string from baseline features (matches the
    ``category`` column in feature_table.parquet)."""
    if features["n_quads"] >= 1:
        return CATEGORY_QUADS
    if features["n_trips"] >= 1 and features["n_pairs"] >= 1:
        return CATEGORY_TRIPS_PAIR
    if features["n_trips"] >= 1:
        return CATEGORY_TRIPS
    if features["n_pairs"] == 3:
        return CATEGORY_THREE_PAIR
    if features["n_pairs"] == 2:
        return CATEGORY_TWO_PAIR
    if features["n_pairs"] == 1:
        return CATEGORY_PAIR
    return CATEGORY_HIGH_ONLY


def load_model(path: Optional[Path] = None) -> dict:
    """Load v5_dt_model.npz once and cache."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if path is None:
        path = ROOT / "data" / "v5_dt_model.npz"
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
        "value_argmax": arr["value_argmax"],
        "classes": arr["classes"],
        "feature_columns": feature_columns,
        "cat_map": cat_map,
        "depth": int(arr["depth"]),
        "n_leaves": int(arr["n_leaves"]),
    }
    return _MODEL_CACHE


def compute_feature_vector(hand: np.ndarray, model: dict) -> np.ndarray:
    """Compute the 37-feature vector for ``hand`` in the trained column order."""
    feats = hand_features_scalar(hand)

    # Override category_id to match alphabetical map used in training.
    cat_str = _category_string_for_hand(feats)
    cat_id = model["cat_map"][cat_str]

    # The aug parquets were built with `category == 'X'` slice masks, so each
    # aug family must return (0,0,0) for out-of-category hands. Some compute
    # functions short-circuit internally; others assume the caller filters.
    # Gate explicitly here to be byte-identical with persist_*.py.
    h_arr = np.asarray(hand, dtype=np.uint8)
    pa1, pa2, pa3 = (compute_pair_aug_for_hand(h_arr)
                     if cat_str == CATEGORY_PAIR else (0, 0, 0))
    ha1, ha2, ha3 = (compute_high_only_aug_for_hand(h_arr)
                     if cat_str == CATEGORY_HIGH_ONLY else (0, 0, 0))
    tp1, tp2, tp3 = (compute_two_pair_aug_for_hand(h_arr)
                     if cat_str == CATEGORY_TWO_PAIR else (0, 0, 0))

    can_make_ds_bot = int(feats["suit_2nd"] >= 2)
    can_make_4run = int(feats["connectivity"] >= 4)
    has_high_pair = int(feats["pair_high_rank"] >= 12)
    has_low_pair = int(feats["n_pairs"] >= 1 and feats["pair_high_rank"] <= 5)
    has_premium_pair = int(feats["pair_high_rank"] == 14 or feats["pair_high_rank"] == 13)
    has_ace_singleton = int(
        feats["top_rank"] == 14
        and feats["pair_high_rank"] != 14
        and feats["trips_rank"] != 14
        and feats["quads_rank"] != 14
    )
    has_king_singleton = int(
        feats["top_rank"] >= 13
        and feats["pair_high_rank"] < 13
        and feats["pair_low_rank"] < 13
        and feats["trips_rank"] < 13
        and feats["quads_rank"] < 13
    )

    full = {
        "n_pairs": feats["n_pairs"],
        "pair_high_rank": feats["pair_high_rank"],
        "pair_low_rank": feats["pair_low_rank"],
        "pair_third_rank": feats["pair_third_rank"],
        "n_trips": feats["n_trips"],
        "trips_rank": feats["trips_rank"],
        "n_quads": feats["n_quads"],
        "quads_rank": feats["quads_rank"],
        "top_rank": feats["top_rank"],
        "second_rank": feats["second_rank"],
        "third_rank": feats["third_rank"],
        "suit_max": feats["suit_max"],
        "suit_2nd": feats["suit_2nd"],
        "suit_3rd": feats["suit_3rd"],
        "suit_4th": feats["suit_4th"],
        "n_suits_present": feats["n_suits_present"],
        "is_monosuit": int(feats["is_monosuit"]),
        "connectivity": feats["connectivity"],
        "n_broadway": feats["n_broadway"],
        "n_low": feats["n_low"],
        "category_id": cat_id,
        "can_make_ds_bot": can_make_ds_bot,
        "can_make_4run": can_make_4run,
        "has_high_pair": has_high_pair,
        "has_low_pair": has_low_pair,
        "has_premium_pair": has_premium_pair,
        "has_ace_singleton": has_ace_singleton,
        "has_king_singleton": has_king_singleton,
        "default_bot_is_ds": pa1,
        "n_top_choices_yielding_ds_bot": pa2,
        "pair_to_bot_alt_is_ds": pa3,
        "default_bot_is_ds_high": ha1,
        "n_mid_choices_yielding_ds_bot": ha2,
        "best_ds_bot_mid_max_rank": ha3,
        "default_bot_is_ds_tp": tp1,
        "n_routings_yielding_ds_bot_tp": tp2,
        "swap_high_pair_to_bot_ds_compatible": tp3,
    }
    return np.array([full[c] for c in model["feature_columns"]], dtype=np.int16)


def _walk_tree(x: np.ndarray, model: dict) -> int:
    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]
    node = 0
    while cl[node] != -1:
        if x[feat[node]] <= thr[node]:
            node = cl[node]
        else:
            node = cr[node]
    class_idx = int(model["value_argmax"][node])
    return int(model["classes"][class_idx])


def strategy_v5_dt(hand: np.ndarray) -> int:
    """Predict setting_index for a 7-card hand by walking the saved DT."""
    model = load_model()
    x = compute_feature_vector(hand, model)
    return _walk_tree(x, model)


# Vectorised batch predict for the full-6M parity check. Computes features
# row-by-row (slow Python) but walks the tree on the assembled matrix.
def predict_many_from_hands(hands: np.ndarray, log_every: int = 500_000) -> np.ndarray:
    """Predict setting_index for each row of ``hands`` (N, 7) uint8."""
    model = load_model()
    n = hands.shape[0]
    n_features = len(model["feature_columns"])
    X = np.empty((n, n_features), dtype=np.int16)
    import time as _t
    t0 = _t.time()
    for i in range(n):
        X[i] = compute_feature_vector(hands[i], model)
        if (i + 1) % log_every == 0:
            print(f"  features computed: {i+1:,}/{n:,}  ({_t.time()-t0:.1f}s)")
    print(f"feature compute total: {_t.time()-t0:.1f}s")
    # Vectorised tree walk over the matrix.
    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]
    classes = model["classes"]
    value_argmax = model["value_argmax"]
    node = np.zeros(n, dtype=np.int32)
    active = np.ones(n, dtype=bool)
    for _ in range(model["depth"] + 5):
        if not active.any():
            break
        cur_nodes = node[active]
        cur_features = feat[cur_nodes]
        cur_thresholds = thr[cur_nodes]
        cur_left = cl[cur_nodes]
        cur_right = cr[cur_nodes]
        leaf_mask = (cur_left == -1)
        row_idx = np.where(active)[0]
        vals = X[row_idx, cur_features]
        go_left = vals <= cur_thresholds
        new_node = np.where(go_left, cur_left, cur_right)
        new_node = np.where(leaf_mask, cur_nodes, new_node)
        node[row_idx] = new_node
        active[row_idx] = ~leaf_mask
    return classes[value_argmax[node]]


if __name__ == "__main__":
    # Spot-check: print the predicted setting for a few hand-picked hands.
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    sample_hands = [
        ("2c 3d 5h 7s 9d Jh Kc",), # high_only
        ("2c 6c Jd Kh Ks Ac Ad",), # two_pair
        ("2c 8c 8d 8h 9s Qc Qs",), # trips_pair (from leaf rank 1)
        ("Ac Ad Ah Kc Kd Qc Qd",), # trips+pair high
        ("2c 3c 4c 5c 6c 7c 8c",), # monosuit straight flush oddity
    ]
    for (s,) in sample_hands:
        cards = s.split()
        h = hh(*cards)
        idx = strategy_v5_dt(h)
        print(f"  {s:<32}  v5_dt setting = {idx}")
