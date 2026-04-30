"""
Session 20 — extract the depth-15 DT chain (37 features) from feature_table.parquet
into a portable model artifact + run a byte-identical parity check on the full 6M.

Inputs:
  data/feature_table.parquet                   (28 baseline)
  data/feature_table_aug.parquet               (3 pair-aug)
  data/feature_table_high_only_aug.parquet     (3 high-aug)
  data/feature_table_two_pair_aug.parquet      (3 two_pair-aug)

Output:
  data/v5_dt_model.npz                         (tree arrays + metadata)

Tree arrays (sklearn convention):
  children_left[i]   — int, left child index, or -1 if leaf
  children_right[i]  — int, right child index, or -1 if leaf
  feature[i]         — int, feature column index used at internal node i
  threshold[i]       — float, split threshold
  value_argmax[i]    — int, argmax of class counts per node (predicted class
                       at this node IF it's a leaf — for safety we store argmax
                       at every node)
  classes            — int array, sklearn .classes_ (sorted unique y values)

Plus:
  feature_columns    — list of column names in training order
  cat_map            — dict[str,int] alphabetical category → id (matches
                       dt_phase1_aug3.py / dt_two_pair_aug_ceiling.py)

Parity check at end: refit depth=15 DT on full 6M, predict, and assert that
walking the saved tree from-scratch on the SAME pre-computed feature matrix
produces byte-identical predictions.

This script does NOT validate from-hand-bytes feature compute — that's
strategy_v5_dt.py's job. Here we lock in the tree itself.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from sklearn.tree import DecisionTreeClassifier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)


def load_features():
    print("loading feature_table.parquet ...")
    t0 = time.time()
    df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
    print(f"  {len(df):,} rows ({time.time()-t0:.1f}s)")

    print("loading 3 augmented parquets ...")
    t0 = time.time()
    pair_aug = pq.read_table(ROOT / "data" / "feature_table_aug.parquet").to_pandas()
    high_aug = pq.read_table(ROOT / "data" / "feature_table_high_only_aug.parquet").to_pandas()
    tp_aug = pq.read_table(ROOT / "data" / "feature_table_two_pair_aug.parquet").to_pandas()
    print(f"  done ({time.time()-t0:.1f}s)")

    for col in ("default_bot_is_ds", "n_top_choices_yielding_ds_bot", "pair_to_bot_alt_is_ds"):
        df[col] = pair_aug[col].values
    for col in ("default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot", "best_ds_bot_mid_max_rank"):
        df[col] = high_aug[col].values
    for col in ("default_bot_is_ds_tp", "n_routings_yielding_ds_bot_tp", "swap_high_pair_to_bot_ds_compatible"):
        df[col] = tp_aug[col].values

    df["can_make_ds_bot"]   = (df["suit_2nd"] >= 2).astype(np.int8)
    df["can_make_4run"]     = (df["connectivity"] >= 4).astype(np.int8)
    df["has_high_pair"]     = (df["pair_high_rank"] >= 12).astype(np.int8)
    df["has_low_pair"]      = ((df["n_pairs"] >= 1) & (df["pair_high_rank"] <= 5)).astype(np.int8)
    df["has_premium_pair"]  = ((df["pair_high_rank"] == 14) | (df["pair_high_rank"] == 13)).astype(np.int8)
    df["has_ace_singleton"] = (
        (df["top_rank"] == 14)
        & (df["pair_high_rank"] != 14)
        & (df["trips_rank"] != 14)
        & (df["quads_rank"] != 14)
    ).astype(np.int8)
    df["has_king_singleton"] = (
        (df["top_rank"] >= 13)
        & (df["pair_high_rank"] < 13)
        & (df["pair_low_rank"] < 13)
        & (df["trips_rank"] < 13)
        & (df["quads_rank"] < 13)
    ).astype(np.int8)

    cat_map = {c: i for i, c in enumerate(sorted(df["category"].unique()))}
    df["category_id"] = df["category"].map(cat_map).astype(np.int8)

    feature_columns = [
        "n_pairs","pair_high_rank","pair_low_rank","pair_third_rank",
        "n_trips","trips_rank","n_quads","quads_rank",
        "top_rank","second_rank","third_rank",
        "suit_max","suit_2nd","suit_3rd","suit_4th",
        "n_suits_present","is_monosuit",
        "connectivity","n_broadway","n_low",
        "category_id",
        "can_make_ds_bot","can_make_4run","has_high_pair",
        "has_low_pair","has_premium_pair",
        "has_ace_singleton","has_king_singleton",
        # pair-aug:
        "default_bot_is_ds","n_top_choices_yielding_ds_bot","pair_to_bot_alt_is_ds",
        # high_only-aug:
        "default_bot_is_ds_high","n_mid_choices_yielding_ds_bot","best_ds_bot_mid_max_rank",
        # two_pair-aug:
        "default_bot_is_ds_tp","n_routings_yielding_ds_bot_tp","swap_high_pair_to_bot_ds_compatible",
    ]
    X = df[feature_columns].values.astype(np.int16)
    y = df["multiway_robust"].values.astype(np.int16)
    return X, y, feature_columns, cat_map


def main() -> int:
    X, y, feature_columns, cat_map = load_features()
    print(f"X = {X.shape}, |classes| = {len(np.unique(y))}")
    print(f"cat_map = {cat_map}")

    print("\nfitting DT depth=15 on full 6M ...")
    t0 = time.time()
    dt = DecisionTreeClassifier(max_depth=15, random_state=42, criterion="gini")
    dt.fit(X, y)
    fit_t = time.time() - t0
    print(f"  fit time {fit_t:.1f}s, n_leaves={dt.get_n_leaves():,}, depth={dt.get_depth()}")

    # sklearn's tree_ holds the data we need.
    tree = dt.tree_
    n_nodes = tree.node_count
    children_left = tree.children_left.astype(np.int32)
    children_right = tree.children_right.astype(np.int32)
    feature = tree.feature.astype(np.int32)
    threshold = tree.threshold.astype(np.float64)
    # tree.value is (n_nodes, n_outputs, n_classes); for single-output it's (n_nodes, 1, n_classes).
    # Per-node argmax over classes_ → predicted class index.
    value = tree.value.squeeze(axis=1)  # (n_nodes, n_classes)
    value_argmax = value.argmax(axis=1).astype(np.int32)
    classes = dt.classes_.astype(np.int32)

    print(f"  n_nodes = {n_nodes:,} (internal+leaf)")

    # ---- Parity check: walk tree from-scratch, compare vs dt.predict(X). ----
    print("\nparity check: predicting via sklearn ...")
    t0 = time.time()
    sk_preds = dt.predict(X)
    print(f"  sklearn predict {time.time()-t0:.1f}s")

    print("walking the saved tree arrays in numpy ...")
    t0 = time.time()
    walk_preds = np.empty(X.shape[0], dtype=np.int32)
    # Vectorise the walk: at each step, branch left/right based on feature & threshold.
    # We do it in chunks to keep memory tame.
    CHUNK = 250_000
    for start in range(0, X.shape[0], CHUNK):
        end = min(start + CHUNK, X.shape[0])
        Xc = X[start:end]
        n = Xc.shape[0]
        node = np.zeros(n, dtype=np.int32)  # all start at root (node 0)
        active = np.ones(n, dtype=bool)
        # Up to depth+1 iterations is enough for a depth-15 tree.
        for _ in range(20):
            if not active.any():
                break
            # For active rows, get current node's feature/threshold/children.
            cur_nodes = node[active]
            cur_features = feature[cur_nodes]
            cur_thresholds = threshold[cur_nodes]
            cur_left = children_left[cur_nodes]
            cur_right = children_right[cur_nodes]
            # Active rows that are leaves stay put; mark them inactive.
            leaf_mask = (cur_left == -1)
            # Branch by feature value vs threshold (sklearn uses <= threshold goes left).
            row_idx = np.where(active)[0]
            vals = Xc[row_idx, cur_features]
            go_left = vals <= cur_thresholds
            new_node = np.where(go_left, cur_left, cur_right)
            # Where leaf, keep current node; else move to new_node.
            new_node = np.where(leaf_mask, cur_nodes, new_node)
            node[row_idx] = new_node
            # Update active: rows still active iff they did NOT just hit a leaf.
            active[row_idx] = ~leaf_mask
        # node[i] should now be the leaf for row i; predict via value_argmax → classes
        chunk_class_idx = value_argmax[node]
        walk_preds[start:end] = classes[chunk_class_idx]
    walk_t = time.time() - t0
    print(f"  manual walk {walk_t:.1f}s")

    n_diff = int((sk_preds != walk_preds).sum())
    print(f"\nbyte-identical parity: sklearn vs manual-walk diffs = {n_diff:,}")
    if n_diff != 0:
        # Show a few examples to debug.
        diff_idx = np.where(sk_preds != walk_preds)[0][:10]
        print("first 10 mismatches:")
        for i in diff_idx:
            print(f"  i={i}: sk={sk_preds[i]} walk={walk_preds[i]}")
        print("\nABORT — tree-walker does not match sklearn predictions.")
        return 2

    # Shape-agreement of this depth-15 DT (using the parquet-precomputed setting_shape).
    # We don't need to recompute shape here — we already know from Session 19's depth curve:
    #   depth=15, full-shape 63.74%. We confirm via literal-agreement.
    literal_acc = float((walk_preds == y).mean())
    print(f"\nliteral-agreement on full 6M: {100*literal_acc:.4f}%")

    # ---- Save model artifact. ----
    out_path = ROOT / "data" / "v5_dt_model.npz"
    np.savez_compressed(
        out_path,
        children_left=children_left,
        children_right=children_right,
        feature=feature,
        threshold=threshold,
        value_argmax=value_argmax,
        classes=classes,
        feature_columns=np.array(feature_columns, dtype=object),
        cat_map_keys=np.array(list(cat_map.keys()), dtype=object),
        cat_map_values=np.array(list(cat_map.values()), dtype=np.int32),
        depth=np.int32(dt.get_depth()),
        n_leaves=np.int32(dt.get_n_leaves()),
    )
    sz = out_path.stat().st_size
    print(f"\nsaved {out_path} ({sz/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
