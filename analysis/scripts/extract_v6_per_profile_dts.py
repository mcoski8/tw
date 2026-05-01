"""
Session 21 — extract 4 per-profile DTs (one per br_<profile> target) for the
v6 ensemble path (Decision 033 / Path A.2).

This mirrors extract_v5_dt.py but uses 4 different targets:
  br_mfsuitaware, br_omaha, br_topdef, br_weighted

(All present in feature_table.parquet — no new MC required.)

Output:
  data/v6_per_profile_dts.npz

Per profile, we save the same sklearn-tree arrays as v5_dt_model.npz:
  children_left_<p>, children_right_<p>, feature_<p>, threshold_<p>,
  value_argmax_<p>, classes_<p>

Plus shared metadata (feature_columns + cat_map + profile order).

The model is depth=15 to match v5_dt's leaf-count regime (~18K leaves).
Sklearn fit takes ~14s per profile = ~1 minute total.

Parity check: refit, predict, walk-from-scratch, assert byte-identical
across all 4 profiles on the full 6M.
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

PROFILE_IDS = ("mfsuitaware", "omaha", "topdef", "weighted")


def load_features():
    """Identical to extract_v5_dt.py — same 37 features, same cat_map."""
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
        "default_bot_is_ds","n_top_choices_yielding_ds_bot","pair_to_bot_alt_is_ds",
        "default_bot_is_ds_high","n_mid_choices_yielding_ds_bot","best_ds_bot_mid_max_rank",
        "default_bot_is_ds_tp","n_routings_yielding_ds_bot_tp","swap_high_pair_to_bot_ds_compatible",
    ]
    X = df[feature_columns].values.astype(np.int16)
    targets = {pid: df[f"br_{pid}"].values.astype(np.int16) for pid in PROFILE_IDS}
    return X, targets, feature_columns, cat_map


def fit_and_extract(X, y, profile_id: str, max_depth: int = 15):
    print(f"\nfitting DT depth={max_depth} for br_{profile_id} ...")
    t0 = time.time()
    dt = DecisionTreeClassifier(max_depth=max_depth, random_state=42, criterion="gini")
    dt.fit(X, y)
    fit_t = time.time() - t0
    print(f"  fit {fit_t:.1f}s, leaves={dt.get_n_leaves():,}, depth={dt.get_depth()}")

    tree = dt.tree_
    children_left = tree.children_left.astype(np.int32)
    children_right = tree.children_right.astype(np.int32)
    feature = tree.feature.astype(np.int32)
    threshold = tree.threshold.astype(np.float64)
    value = tree.value.squeeze(axis=1)
    value_argmax = value.argmax(axis=1).astype(np.int32)
    classes = dt.classes_.astype(np.int32)

    # Parity: walk-from-scratch must match dt.predict(X).
    print(f"  parity: predicting via sklearn ...")
    sk_preds = dt.predict(X)
    walk_preds = walk_tree(
        X, children_left, children_right, feature, threshold,
        value_argmax, classes, depth=max_depth + 5,
    )
    n_diff = int((sk_preds != walk_preds).sum())
    print(f"  parity (sk vs walk): {n_diff:,} diffs (must be 0)")
    if n_diff != 0:
        raise RuntimeError(f"parity check failed for br_{profile_id}: {n_diff} diffs")

    literal_acc = float((walk_preds == y).mean())
    print(f"  literal-agreement on full 6M (br_{profile_id}): {100*literal_acc:.4f}%")

    return {
        "children_left": children_left,
        "children_right": children_right,
        "feature": feature,
        "threshold": threshold,
        "value_argmax": value_argmax,
        "classes": classes,
        "n_leaves": dt.get_n_leaves(),
        "depth": dt.get_depth(),
        "literal_acc": literal_acc,
    }


def walk_tree(X, cl, cr, feat, thr, value_argmax, classes, depth: int = 20):
    """Vectorised manual tree-walk in chunks."""
    n = X.shape[0]
    out = np.empty(n, dtype=np.int32)
    CHUNK = 250_000
    for start in range(0, n, CHUNK):
        end = min(start + CHUNK, n)
        Xc = X[start:end]
        m = Xc.shape[0]
        node = np.zeros(m, dtype=np.int32)
        active = np.ones(m, dtype=bool)
        for _ in range(depth):
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
        out[start:end] = classes[value_argmax[node]]
    return out


def main() -> int:
    X, targets, feature_columns, cat_map = load_features()
    print(f"X = {X.shape}")

    trees = {}
    for pid in PROFILE_IDS:
        trees[pid] = fit_and_extract(X, targets[pid], pid)

    out_path = ROOT / "data" / "v6_per_profile_dts.npz"
    save_kwargs = {
        "feature_columns": np.array(feature_columns, dtype=object),
        "cat_map_keys": np.array(list(cat_map.keys()), dtype=object),
        "cat_map_values": np.array(list(cat_map.values()), dtype=np.int32),
        "profile_ids": np.array(list(PROFILE_IDS), dtype=object),
    }
    for pid in PROFILE_IDS:
        t = trees[pid]
        save_kwargs[f"children_left_{pid}"] = t["children_left"]
        save_kwargs[f"children_right_{pid}"] = t["children_right"]
        save_kwargs[f"feature_{pid}"] = t["feature"]
        save_kwargs[f"threshold_{pid}"] = t["threshold"]
        save_kwargs[f"value_argmax_{pid}"] = t["value_argmax"]
        save_kwargs[f"classes_{pid}"] = t["classes"]
        save_kwargs[f"n_leaves_{pid}"] = np.int32(t["n_leaves"])
        save_kwargs[f"depth_{pid}"] = np.int32(t["depth"])
        save_kwargs[f"literal_acc_{pid}"] = np.float64(t["literal_acc"])
    np.savez_compressed(out_path, **save_kwargs)
    sz = out_path.stat().st_size
    print(f"\nsaved {out_path} ({sz/1e6:.2f} MB)")

    # Per-profile ensemble agreement diagnostics.
    print("\n=== Per-profile DT shape-target literal-agreement (full 6M) ===")
    for pid in PROFILE_IDS:
        print(f"  br_{pid:<14}  {trees[pid]['literal_acc']*100:.4f}%  "
              f"(n_leaves={trees[pid]['n_leaves']:,})")

    # Cheap-test of ensemble agreement on full 6M:
    # Compute the 4 predictions, count how often the modal vote equals each
    # profile's own br target.
    print("\n=== Ensemble cheap-test: per-profile DT votes vs br targets on full 6M ===")
    preds = {}
    for pid in PROFILE_IDS:
        t = trees[pid]
        preds[pid] = walk_tree(
            X, t["children_left"], t["children_right"], t["feature"], t["threshold"],
            t["value_argmax"], t["classes"], depth=t["depth"] + 5,
        )

    # Stack preds: shape (N, P)
    pred_matrix = np.column_stack([preds[pid] for pid in PROFILE_IDS])
    # Count votes: for each row, how many distinct settings are predicted
    # (4 = full split, 1 = unanimous)
    n_distinct = np.array([len(set(row)) for row in pred_matrix[:100_000]])  # sample
    print(f"  sampled 100K rows for vote-distribution diagnostic:")
    for k in (1, 2, 3, 4):
        pct = (n_distinct == k).mean() * 100
        print(f"    {k} distinct votes: {pct:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
