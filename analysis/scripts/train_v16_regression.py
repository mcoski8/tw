"""
Session 27 — train v16: a DecisionTreeRegressor on the Oracle Grid built
against the realistic 70/25/5 human mixture. Mirrors the v7 regression
methodology (Decision 042) but uses today's grid as ground truth instead
of the OLD 4-profile mixture.

Inputs:
    --training-grid {full,prefix}
        full   = data/oracle_grid_full_realistic_n200.bin (6,009,159 hands × N=200)
        prefix = data/oracle_grid_prefix500k_n1000.bin    (500,000 hands × N=1000)

Features (37 total, byte-identical to v5/v7 via strategy_v5_dt.compute_feature_vector):
    baseline (28) + pair_aug (3) + high_only_aug (3) + two_pair_aug (3) +
    7 derived flags (can_make_ds_bot etc.).

Target: per-hand 105-EV vector (regression, multi-output).
Inference time (strategy_v16_dt.py): walk tree → leaf 105-vec → argmax.

Output: data/v16_dt_model.npz (same array layout as v7_regression_model.npz).
"""
from __future__ import annotations

import argparse
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

from strategy_v5_dt import compute_feature_vector, load_model as load_v5_model  # noqa: E402
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"


def load_v5_feature_meta() -> dict:
    """Return the {feature_columns, cat_map} dict v5_dt uses, for parity at training time."""
    return {
        "feature_columns": load_v5_model()["feature_columns"],
        "cat_map": load_v5_model()["cat_map"],
    }


def compute_feature_matrix(hands_bytes: np.ndarray, log_every: int = 200_000) -> tuple[np.ndarray, list[str]]:
    feat_meta = load_v5_feature_meta()
    n = hands_bytes.shape[0]
    n_features = len(feat_meta["feature_columns"])
    X = np.empty((n, n_features), dtype=np.int16)
    t0 = time.time()
    for i in range(n):
        X[i] = compute_feature_vector(np.asarray(hands_bytes[i], dtype=np.uint8), feat_meta)
        if (i + 1) % log_every == 0 or i + 1 == n:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (n - i - 1) / rate
            print(f"  features {i+1:>10,}/{n:,}  rate {rate:>5.0f}/s  elapsed {elapsed:>6.0f}s  ETA {eta:>6.0f}s", flush=True)
    return X, feat_meta["feature_columns"]


def fit_and_extract(X: np.ndarray, Y: np.ndarray, max_depth: int, min_samples_leaf: int):
    print(f"\nfitting DecisionTreeRegressor depth={max_depth} min_samples_leaf={min_samples_leaf} ...", flush=True)
    print(f"  X={X.shape}  Y={Y.shape}", flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=42,
        criterion="squared_error",
    )
    dt.fit(X, Y)
    fit_t = time.time() - t0
    print(f"  fit {fit_t:.1f}s  leaves={dt.get_n_leaves():,}  depth={dt.get_depth()}", flush=True)

    tree = dt.tree_
    val = tree.value
    if val.ndim == 3:
        val = val[:, :, 0]
    children_left = tree.children_left.astype(np.int32)
    children_right = tree.children_right.astype(np.int32)
    feature = tree.feature.astype(np.int32)
    threshold = tree.threshold.astype(np.float64)
    leaf_values = val.astype(np.float32)

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
    cl = t["children_left"]
    cr = t["children_right"]
    feat = t["feature"]
    thr = t["threshold"]
    leaf_values = t["leaf_values"]
    n = X.shape[0]
    out_argmax = np.empty(n, dtype=np.int32)
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
            cur_left = cl[cur_nodes]
            leaf_mask = (cur_left == -1)
            cur_features = feat[cur_nodes]
            cur_thresholds = thr[cur_nodes]
            cur_right = cr[cur_nodes]
            row_idx = np.where(active)[0]
            vals = Xc[row_idx, cur_features]
            go_left = vals <= cur_thresholds
            new_node = np.where(go_left, cur_left, cur_right)
            new_node = np.where(leaf_mask, cur_nodes, new_node)
            node[row_idx] = new_node
            active[row_idx] = ~leaf_mask
        chunk_leaves = leaf_values[node]
        out_argmax[start:end] = chunk_leaves.argmax(axis=1)
    return out_argmax


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--training-grid", choices=["full", "prefix"], default="prefix",
                    help="full=6M N=200; prefix=500K N=1000 (tighter labels)")
    ap.add_argument("--max-depth", type=int, default=15)
    ap.add_argument("--min-samples-leaf", type=int, default=200)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v16_dt_model.npz")
    args = ap.parse_args()

    if args.training_grid == "full":
        grid_path = GRID_FULL
    else:
        grid_path = GRID_PREFIX

    print(f"loading {grid_path} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    n = len(grid)
    print(f"  grid records={n:,}  canonical hands available={len(ch):,}", flush=True)

    # Validate canonical_id ordering aligns with row position.
    ids = np.asarray(grid.canonical_ids[:1000])
    if not np.array_equal(ids, np.arange(1000, dtype=ids.dtype)):
        # OK if the grid is the prefix in canonical-ascending order; otherwise we must use canonical_ids to fetch hand bytes.
        print("  WARN: grid canonical_ids != row-ordering on the head; will fetch hand bytes via canonical_ids per row.", flush=True)

    # Materialize hand bytes for every grid row.
    print(f"\ncollecting hand bytes for {n:,} rows ...", flush=True)
    hands_bytes = np.empty((n, 7), dtype=np.uint8)
    cids_full = np.asarray(grid.canonical_ids[:n])
    t0 = time.time()
    for i in range(n):
        hands_bytes[i] = ch.hands[int(cids_full[i])]
    print(f"  done {time.time()-t0:.1f}s", flush=True)

    # Y = per-hand 105-EV vec.
    print(f"\nmaterializing Y (N, 105) from memmap evs ...", flush=True)
    t0 = time.time()
    Y = np.asarray(grid.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB  load {time.time()-t0:.1f}s", flush=True)
    print(f"  oracle argmax mean EV = {Y.max(axis=1).mean():+.4f}", flush=True)

    # Compute features.
    print(f"\ncomputing 37-feature matrix ...", flush=True)
    X, feature_columns = compute_feature_matrix(hands_bytes)

    dt, model = fit_and_extract(X, Y, args.max_depth, args.min_samples_leaf)

    # Parity check.
    print(f"\nparity check (sklearn predict vs manual walk) on a 50K sample ...", flush=True)
    sample_n = min(50_000, n)
    sk_pred = dt.predict(X[:sample_n])
    sk_argmax = sk_pred.argmax(axis=1)
    walk_argmax = walk_tree_argmax(X[:sample_n], model)
    n_diff = int((sk_argmax != walk_argmax).sum())
    print(f"  argmax diffs: {n_diff:,} on {sample_n:,} (must be 0)", flush=True)
    if n_diff != 0:
        return 2

    # Training-set recovery.
    walk_full = walk_tree_argmax(X, model)
    train_picked_ev = Y[np.arange(n), walk_full].mean()
    train_oracle_ev = Y.max(axis=1).mean()
    shape_agree = float((walk_full == Y.argmax(axis=1)).mean()) * 100
    print(f"\nTraining-set recovery:", flush=True)
    print(f"  oracle argmax mean EV: {train_oracle_ev:+.4f}", flush=True)
    print(f"  v16 picked  mean EV:   {train_picked_ev:+.4f}", flush=True)
    print(f"  retention (closer to 100% better): {(train_picked_ev / train_oracle_ev) * 100:.2f}%", flush=True)
    print(f"  shape-agreement vs oracle argmax: {shape_agree:.2f}%", flush=True)

    cat_map = load_v5_feature_meta()["cat_map"]
    np.savez_compressed(
        args.output,
        children_left=model["children_left"],
        children_right=model["children_right"],
        feature=model["feature"],
        threshold=model["threshold"],
        leaf_values=model["leaf_values"],
        feature_columns=np.array(feature_columns, dtype=object),
        cat_map_keys=np.array(list(cat_map.keys()), dtype=object),
        cat_map_values=np.array(list(cat_map.values()), dtype=np.int32),
        depth=np.int32(model["depth"]),
        n_leaves=np.int32(model["n_leaves"]),
        training_grid=np.array([args.training_grid], dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
    )
    sz = args.output.stat().st_size
    print(f"\nsaved {args.output} ({sz/1e6:.2f} MB)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
