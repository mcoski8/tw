"""
Session 21 — strategy_v6_ensemble: vote-of-4-per-profile-DTs.

Trained by extract_v6_per_profile_dts.py on the same 37 features as v5_dt
but with per-profile br_<profile> targets instead of multiway_robust.

Voting rule:
  - Compute the 4 settings predicted by the 4 per-profile DTs.
  - Pick the modal vote.
  - On a tie (2-2 split or 4 distinct), default to the mfsuitaware DT's
    vote (the "production representative" profile per Decision 005, and
    the highest single-profile overlap with oracle_argmax_mean per the
    Session 21 cheap-test: 77.5% overlap on 200 hands).

This is path A.2 from Decision 033's Session 21 fork. It uses ONLY existing
6M-row training data — no new MC required. The cheap-test showed an upper-
bound argmax_mean ceiling of +$12,949/1000h vs v5_dt at $10/EV-pt; this
ensemble is the lowest-friction way to capture a portion of that.

Provides:
    strategy_v6_ensemble(hand: np.ndarray) -> int

Drop-in replacement for strategy_v5_dt in v3_evloss_baseline.py.
"""
from __future__ import annotations

import sys
from collections import Counter
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

# Re-use feature compute from strategy_v5_dt (shares the same 37-feature pipeline).
from strategy_v5_dt import compute_feature_vector  # noqa: E402


_MODEL_CACHE: Optional[dict] = None
_FEATURE_MODEL_CACHE: Optional[dict] = None


def _load_feature_model() -> dict:
    """Lazy-load v5_dt's feature_columns + cat_map (same set used by v6 trees)."""
    global _FEATURE_MODEL_CACHE
    if _FEATURE_MODEL_CACHE is not None:
        return _FEATURE_MODEL_CACHE
    arr = np.load(ROOT / "data" / "v5_dt_model.npz", allow_pickle=True)
    keys = list(arr["cat_map_keys"])
    vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    _FEATURE_MODEL_CACHE = {"cat_map": cat_map, "feature_columns": feature_columns}
    return _FEATURE_MODEL_CACHE


def load_model(path: Optional[Path] = None) -> dict:
    """Load all 4 per-profile trees + metadata into a single cache dict."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if path is None:
        path = ROOT / "data" / "v6_per_profile_dts.npz"
    arr = np.load(path, allow_pickle=True)
    profile_ids = [str(p) for p in arr["profile_ids"]]
    keys = list(arr["cat_map_keys"])
    vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    trees = {}
    for pid in profile_ids:
        trees[pid] = {
            "children_left": arr[f"children_left_{pid}"],
            "children_right": arr[f"children_right_{pid}"],
            "feature": arr[f"feature_{pid}"],
            "threshold": arr[f"threshold_{pid}"],
            "value_argmax": arr[f"value_argmax_{pid}"],
            "classes": arr[f"classes_{pid}"],
            "depth": int(arr[f"depth_{pid}"]),
            "n_leaves": int(arr[f"n_leaves_{pid}"]),
        }
    _MODEL_CACHE = {
        "profile_ids": profile_ids,
        "trees": trees,
        "feature_columns": feature_columns,
        "cat_map": cat_map,
    }
    return _MODEL_CACHE


def _walk_tree_scalar(x: np.ndarray, t: dict) -> int:
    cl = t["children_left"]
    cr = t["children_right"]
    feat = t["feature"]
    thr = t["threshold"]
    node = 0
    while cl[node] != -1:
        if x[feat[node]] <= thr[node]:
            node = cl[node]
        else:
            node = cr[node]
    return int(t["classes"][int(t["value_argmax"][node])])


def strategy_v6_ensemble(hand: np.ndarray) -> int:
    """Predict setting_index by voting 4 per-profile DTs."""
    model = load_model()
    feat_meta = {
        "cat_map": model["cat_map"],
        "feature_columns": model["feature_columns"],
    }
    x = compute_feature_vector(hand, feat_meta)

    profile_ids = model["profile_ids"]
    votes = [_walk_tree_scalar(x, model["trees"][pid]) for pid in profile_ids]

    counts = Counter(votes)
    # most_common gives [(setting, count), ...] sorted by count desc, ties arbitrary.
    sorted_votes = counts.most_common()
    top_setting, top_count = sorted_votes[0]
    if len(sorted_votes) > 1 and sorted_votes[1][1] == top_count:
        # 2-2 tie or 4-distinct → default to mfsuitaware (index 0).
        mfsuit_idx = profile_ids.index("mfsuitaware")
        return votes[mfsuit_idx]
    return top_setting


# Vectorised batch predict over the full 6M, used for parity diagnostics.
def predict_many(X: np.ndarray) -> np.ndarray:
    """X: (N, 37) int16. Walk all 4 trees, then vote per row."""
    model = load_model()
    profile_ids = model["profile_ids"]
    n = X.shape[0]

    all_preds = np.empty((n, len(profile_ids)), dtype=np.int32)
    for j, pid in enumerate(profile_ids):
        t = model["trees"][pid]
        cl = t["children_left"]
        cr = t["children_right"]
        feat = t["feature"]
        thr = t["threshold"]
        classes = t["classes"]
        value_argmax = t["value_argmax"]
        # Vectorised walk identical to extract_v5_dt's manual walk.
        node = np.zeros(n, dtype=np.int32)
        active = np.ones(n, dtype=bool)
        for _ in range(t["depth"] + 5):
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
        all_preds[:, j] = classes[value_argmax[node]]

    # Vote per row. Using a per-row Python Counter is ~slow but only needed
    # for the diagnostic. ~5-10s for 6M rows.
    out = np.empty(n, dtype=np.int32)
    mfsuit_j = profile_ids.index("mfsuitaware")
    for i in range(n):
        row = all_preds[i]
        counts = Counter(int(v) for v in row)
        sorted_votes = counts.most_common()
        top_setting, top_count = sorted_votes[0]
        if len(sorted_votes) > 1 and sorted_votes[1][1] == top_count:
            out[i] = int(row[mfsuit_j])
        else:
            out[i] = top_setting
    return out


if __name__ == "__main__":
    # Spot-check.
    _RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
             "T":10,"J":11,"Q":12,"K":13,"A":14}
    _SUIT = {"c":0,"d":1,"h":2,"s":3}
    def hh(*cards):
        bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    sample_hands = [
        ("2c 3d 5h 7s 9d Jh Kc",),
        ("2c 6c Jd Kh Ks Ac Ad",),
        ("2c 8c 8d 8h 9s Qc Qs",),
        ("Ac Ad Ah Kc Kd Qc Qd",),
        ("2c 3c 4c 5c 6c 7c 8c",),
    ]
    for (s,) in sample_hands:
        cards = s.split()
        h = hh(*cards)
        idx = strategy_v6_ensemble(h)
        print(f"  {s:<32}  v6_ensemble setting = {idx}")
