"""
Session 20 — full-pipeline parity check for strategy_v5_dt.

Goal: prove that strategy_v5_dt(hand_bytes) (which derives all 37 features
from raw hand bytes, then walks the saved DT) produces byte-identical
predictions to the sklearn DT acting on the parquet-precomputed feature
matrix used at training time.

Methodology:
  1. Load canonical_hands.bin (the 6M canonical hands).
  2. Sample N rows uniformly (default 50K — enough to cover all 7 categories
     and exercise every feature).
  3. For each sampled row, compute the 37-feature vector from raw hand bytes
     using strategy_v5_dt.compute_feature_vector(...).
  4. Compare to the corresponding row of the parquet-precomputed X used at
     training time (extract_v5_dt.py logic).
  5. Walk the saved DT on both — assert identical setting_index predictions.
  6. Also report the v5_dt shape-agreement on the sampled subset (should be
     ~63.74% per Session 19 depth-15 metric).

If any feature mismatches between the from-hand path and the parquet path,
abort with a diagnostic listing the offending columns.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis import read_canonical_hands  # noqa: E402
from encode_rules import setting_shape  # noqa: E402
from strategy_v5_dt import (  # noqa: E402
    load_model, compute_feature_vector, _walk_tree,
)


def build_parquet_X(df_indices: np.ndarray, feature_columns: list[str]) -> np.ndarray:
    """Reproduce extract_v5_dt.py's feature matrix construction for given rows."""
    df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
    pair_aug = pq.read_table(ROOT / "data" / "feature_table_aug.parquet").to_pandas()
    high_aug = pq.read_table(ROOT / "data" / "feature_table_high_only_aug.parquet").to_pandas()
    tp_aug = pq.read_table(ROOT / "data" / "feature_table_two_pair_aug.parquet").to_pandas()

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

    sub = df.iloc[df_indices]
    X = sub[feature_columns].values.astype(np.int16)
    y = sub["multiway_robust"].values.astype(np.int16)
    return X, y


def main() -> int:
    N_SAMPLE = 50_000
    rng = np.random.default_rng(2026)

    print("loading canonical hands ...")
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    hands = canonical.hands
    N = hands.shape[0]
    print(f"  {N:,} hands")

    sample_idx = rng.choice(N, size=N_SAMPLE, replace=False)
    sample_idx.sort()
    print(f"sampled {N_SAMPLE:,} rows for parity check")

    print("\nloading saved v5_dt model ...")
    model = load_model()
    feature_columns = model["feature_columns"]
    print(f"  feature_columns: {len(feature_columns)} cols")

    print("\nbuilding parquet-derived feature matrix for sampled rows ...")
    t0 = time.time()
    X_parq, y_target = build_parquet_X(sample_idx, feature_columns)
    print(f"  done ({time.time()-t0:.1f}s)  X_parq={X_parq.shape}")

    print("\ncomputing from-hand feature matrix ...")
    t0 = time.time()
    X_hand = np.empty_like(X_parq)
    for i, row_idx in enumerate(sample_idx):
        X_hand[i] = compute_feature_vector(hands[row_idx], model)
        if (i + 1) % 10_000 == 0:
            print(f"  {i+1:,}/{N_SAMPLE:,}  ({time.time()-t0:.1f}s)")
    print(f"  done ({time.time()-t0:.1f}s)")

    print("\ncomparing feature matrices column-by-column ...")
    diffs = (X_hand != X_parq)
    n_total_diff = int(diffs.sum())
    if n_total_diff > 0:
        print(f"  TOTAL DIFFS: {n_total_diff:,} cells")
        per_col_diff = diffs.sum(axis=0)
        for j, c in enumerate(feature_columns):
            if per_col_diff[j] > 0:
                # Find one example.
                bad_rows = np.where(diffs[:, j])[0][:3]
                print(f"  col '{c}' (idx {j}): {per_col_diff[j]:,} diffs")
                for r in bad_rows:
                    print(f"    row {r} (canon idx {sample_idx[r]}): "
                          f"hand={X_hand[r,j]} parq={X_parq[r,j]}")
        print("\nABORT — feature compute mismatch.")
        return 2
    print("  byte-identical: 0 cell-level diffs across all 37 features")

    print("\nwalking tree on both matrices ...")
    preds_parq = np.array([_walk_tree(X_parq[i], model) for i in range(N_SAMPLE)], dtype=np.int32)
    preds_hand = np.array([_walk_tree(X_hand[i], model) for i in range(N_SAMPLE)], dtype=np.int32)
    n_pred_diff = int((preds_parq != preds_hand).sum())
    print(f"  prediction diffs: {n_pred_diff}")
    if n_pred_diff != 0:
        print("ABORT — tree-walk mismatch despite identical features.")
        return 2

    # Shape-agreement on the sample.
    print("\ncomputing shape-agreement on sample ...")
    correct = 0
    for i, row_idx in enumerate(sample_idx):
        h = hands[row_idx]
        pred_sh = setting_shape(h, int(preds_hand[i]))
        true_sh = setting_shape(h, int(y_target[i]))
        if (pred_sh[0] == true_sh[0]
            and tuple(pred_sh[1]) == tuple(true_sh[1])
            and tuple(pred_sh[2]) == tuple(true_sh[2])):
            correct += 1
    shape_acc = 100 * correct / N_SAMPLE
    literal_acc = 100 * float((preds_hand == y_target).mean())
    print(f"  literal-agreement: {literal_acc:.4f}%")
    print(f"  shape-agreement:   {shape_acc:.4f}%   (Session 19 depth-15 reference: 63.74%)")

    print("\nALL PARITY CHECKS PASSED — strategy_v5_dt is byte-identical to the trained DT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
