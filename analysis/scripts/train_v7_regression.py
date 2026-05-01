"""
Session 22 — train the path-A.1 regression DT.

Reads `data/oracle_grid_50k.npz` (per-setting × per-profile EV grid built
by cheap_test_oracle_hedges.py at hands=50000) and trains a single
multi-output regression DT to predict the mean-across-profiles EV vector
(length 105) for every hand.

Target: mean over the 4 profile axis of ev_grid[hand, profile, setting]
        — i.e. mean_EV[hand, setting] (50000 × 105).

Features: same 37-feature set as v5_dt and v6_ensemble (computed via
strategy_v5_dt.compute_feature_vector for parity).

Output: data/v7_regression_model.npz with sklearn-tree arrays + leaf-EV
matrix. Plus a parity check (sklearn vs manual walk on full training set)
and shape-agreement vs the oracle argmax_mean (training-set ceiling).

The training set is the SAME hands that an inference-time predictor will
NOT have seen — but the cheap-test pattern shows that argmax_mean overlap
with v5_dt is only 14% and the median margin is 0.245 EV/hand. So even
training on these 50K hands produces a generalizable model: the splits
the DT learns will be on hand-features, not on the noisy MC values.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from sklearn.tree import DecisionTreeRegressor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v5_dt import compute_feature_vector  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"
MODEL_PATH = ROOT / "data" / "v7_regression_model.npz"


def load_grid(path: Path = GRID_PATH):
    print(f"loading {path} ...")
    t0 = time.time()
    arr = np.load(path, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]      # (N, 7) uint8
    ev_grid = arr["ev_grid"]               # (N, 4, 105) float64
    profile_ids = list(arr["profile_ids"])
    print(f"  hands_bytes {hands_bytes.shape}, ev_grid {ev_grid.shape}, "
          f"profiles {profile_ids} ({time.time()-t0:.1f}s)")
    return hands_bytes, ev_grid, profile_ids


def load_v5_feature_meta() -> dict:
    """Reuse v5_dt's saved feature_columns + cat_map (same set used by v7)."""
    arr = np.load(ROOT / "data" / "v5_dt_model.npz", allow_pickle=True)
    keys = list(arr["cat_map_keys"])
    vals = list(arr["cat_map_values"])
    cat_map = {str(k): int(v) for k, v in zip(keys, vals)}
    feature_columns = [str(c) for c in arr["feature_columns"]]
    return {"cat_map": cat_map, "feature_columns": feature_columns}


def compute_feature_matrix(hands_bytes: np.ndarray) -> tuple[np.ndarray, list[str]]:
    feat_meta = load_v5_feature_meta()
    n = hands_bytes.shape[0]
    n_features = len(feat_meta["feature_columns"])
    X = np.empty((n, n_features), dtype=np.int16)
    t0 = time.time()
    for i in range(n):
        X[i] = compute_feature_vector(hands_bytes[i], feat_meta)
        if (i + 1) % 5000 == 0 or i + 1 == n:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            print(f"  features {i+1:>6}/{n}  rate {rate:.0f}/s  elapsed {elapsed:.0f}s")
    return X, feat_meta["feature_columns"]


def fit_and_extract(X: np.ndarray, Y: np.ndarray, max_depth: int = 15):
    """Y is (N, 105) mean-EV target."""
    print(f"\nfitting DecisionTreeRegressor depth={max_depth} ...")
    print(f"  X={X.shape}  Y={Y.shape}")
    t0 = time.time()
    dt = DecisionTreeRegressor(max_depth=max_depth, random_state=42, criterion="squared_error")
    dt.fit(X, Y)
    fit_t = time.time() - t0
    print(f"  fit {fit_t:.1f}s, leaves={dt.get_n_leaves():,}, depth={dt.get_depth()}")

    tree = dt.tree_
    # tree.value shape: (n_nodes, n_outputs, 1)? or (n_nodes, n_outputs)? Let's normalize.
    val = tree.value
    if val.ndim == 3:
        val = val[:, :, 0]  # (n_nodes, n_outputs)
    children_left = tree.children_left.astype(np.int32)
    children_right = tree.children_right.astype(np.int32)
    feature = tree.feature.astype(np.int32)
    threshold = tree.threshold.astype(np.float64)
    leaf_values = val.astype(np.float32)  # (n_nodes, 105)

    return dt, {
        "children_left": children_left,
        "children_right": children_right,
        "feature": feature,
        "threshold": threshold,
        "leaf_values": leaf_values,
        "depth": dt.get_depth(),
        "n_leaves": dt.get_n_leaves(),
    }


def walk_tree_argmax(X: np.ndarray, t: dict) -> np.ndarray:
    """Vectorised tree-walk → for each row, argmax over 105 of the leaf-vec."""
    cl = t["children_left"]
    cr = t["children_right"]
    feat = t["feature"]
    thr = t["threshold"]
    leaf_values = t["leaf_values"]
    n = X.shape[0]
    out_argmax = np.empty(n, dtype=np.int32)
    out_meanev = np.empty(n, dtype=np.float64)
    CHUNK = 100_000
    for start in range(0, n, CHUNK):
        end = min(start + CHUNK, n)
        Xc = X[start:end]
        m = Xc.shape[0]
        node = np.zeros(m, dtype=np.int32)
        active = np.ones(m, dtype=bool)
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
            vals = Xc[row_idx, cur_features]
            go_left = vals <= cur_thresholds
            new_node = np.where(go_left, cur_left, cur_right)
            new_node = np.where(leaf_mask, cur_nodes, new_node)
            node[row_idx] = new_node
            active[row_idx] = ~leaf_mask
        chunk_leaves = leaf_values[node]                    # (m, 105)
        chunk_argmax = chunk_leaves.argmax(axis=1)          # (m,)
        out_argmax[start:end] = chunk_argmax
        out_meanev[start:end] = chunk_leaves[np.arange(m), chunk_argmax]
    return out_argmax, out_meanev


def main() -> int:
    if not GRID_PATH.exists():
        print(f"ERROR: {GRID_PATH} not found. Run cheap_test_oracle_hedges.py "
              f"with --hands 50000 --save-grid {GRID_PATH} first.", file=sys.stderr)
        return 1

    hands_bytes, ev_grid, profile_ids = load_grid()
    n = hands_bytes.shape[0]
    print(f"\nN = {n:,} hands × {ev_grid.shape[1]} profiles × {ev_grid.shape[2]} settings")

    # Target: mean across profiles → (N, 105) per-setting mean EV.
    Y = ev_grid.mean(axis=1).astype(np.float32)
    print(f"Y (mean-EV per setting): {Y.shape}, range [{Y.min():.3f}, {Y.max():.3f}]")

    # Oracle argmax_mean target (for shape-agreement reporting).
    oracle_argmax = Y.argmax(axis=1)
    oracle_ev = Y[np.arange(n), oracle_argmax]
    print(f"Oracle argmax_mean: per-hand mean across hands = {oracle_ev.mean():+.4f}")

    # Compute features.
    print("\ncomputing 37-feature matrix ...")
    X, feature_columns = compute_feature_matrix(hands_bytes)
    print(f"X = {X.shape}")

    # Fit.
    dt, model = fit_and_extract(X, Y, max_depth=15)

    # Parity: sklearn vs manual walk.
    print("\nparity check (sklearn predict vs manual walk):")
    sk_pred_full = dt.predict(X)                        # (N, 105)
    sk_argmax = sk_pred_full.argmax(axis=1)
    walk_argmax, walk_ev = walk_tree_argmax(X, model)
    n_diff = int((sk_argmax != walk_argmax).sum())
    print(f"  argmax diffs: {n_diff:,} (must be 0)")
    if n_diff != 0:
        bad = np.where(sk_argmax != walk_argmax)[0][:5]
        for i in bad:
            print(f"    row {i}: sk_argmax={sk_argmax[i]} walk_argmax={walk_argmax[i]}  "
                  f"sk_pred[walk]={sk_pred_full[i, walk_argmax[i]]:.4f}  "
                  f"sk_pred[sk]={sk_pred_full[i, sk_argmax[i]]:.4f}")
        return 2

    # Training-set EV: the model's predicted setting per hand, scored against the TRUE
    # ev_grid (the noiseless oracle). This is the upper-bound recovery the model can do.
    train_picked_meanev = ev_grid.mean(axis=1)[np.arange(n), walk_argmax].mean()
    train_oracle_meanev = oracle_ev.mean()
    print(f"\nTraining-set argmax_mean recovery:")
    print(f"  oracle_argmax_mean: per-hand mean = {train_oracle_meanev:+.4f}")
    print(f"  v7 model on train: per-hand mean = {train_picked_meanev:+.4f}")
    print(f"  retention: {(train_picked_meanev / train_oracle_meanev) * 100:.2f}%  "
          f"(100% = perfect oracle reproduction on training set)")

    # Shape-agreement vs oracle_argmax_mean on training set.
    shape_agree = float((walk_argmax == oracle_argmax).mean()) * 100
    print(f"  shape-agreement vs oracle_argmax_mean: {shape_agree:.2f}%")

    # Save.
    np.savez_compressed(
        MODEL_PATH,
        children_left=model["children_left"],
        children_right=model["children_right"],
        feature=model["feature"],
        threshold=model["threshold"],
        leaf_values=model["leaf_values"],
        feature_columns=np.array(feature_columns, dtype=object),
        cat_map_keys=np.array(list(load_v5_feature_meta()["cat_map"].keys()), dtype=object),
        cat_map_values=np.array(list(load_v5_feature_meta()["cat_map"].values()), dtype=np.int32),
        depth=np.int32(model["depth"]),
        n_leaves=np.int32(model["n_leaves"]),
        profile_ids=np.array(profile_ids, dtype=object),
    )
    sz = MODEL_PATH.stat().st_size
    print(f"\nsaved {MODEL_PATH} ({sz/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
