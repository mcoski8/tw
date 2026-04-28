"""
Session 18 — augmented-feature ceiling on high_only slices + drop-out ablation.

Trains depth=None DTs on multiple subsets:
  - high_only 3-of-4 (slice — primary target)
  - high_only full
  - 3-of-4 majority (with both pair-aug and high_only-aug features)
  - full 6M

For each, compares baseline 27 features vs augmented 30 features (+ pair-aug
+ high_only-aug = 33). Per-feature drop-out ablation on the slice confirms
each new feature's contribution (per Session 17 lesson: signal magnitude
≠ contribution magnitude).

References:
  - Session 17 baseline 27 features:
      single-pair 3-of-4: 74.23% / 26,238 leaves
      single-pair full:   68.49%
      3-of-4:             70.01%
      full 6M:            61.74%
  - Session 17 augmented (27 + 3 pair-aug = 30 features):
      single-pair 3-of-4: 80.08% / +5.85pp
      3-of-4:             72.61% / +2.60pp
      full 6M:            63.76% / +2.02pp
  - Session 18 mining showed high_only 3-of-4 baseline ceiling: 39.64%.

Hypothesis: high_only-aug features lift the high_only-3-of-4 slice ceiling
substantially (high OR signal); the lift propagates as +0.5-1.5pp to the
3-of-4 majority and full 6M, on top of the pair-aug lift.
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

from tw_analysis import read_canonical_hands  # noqa: E402
from encode_rules import setting_shape  # noqa: E402

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df_all = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df_all):,} hands ({time.time()-t0:.1f}s)")

# ----- Read pair-aug + high_only-aug from persisted parquets. -----
print("loading pair_aug parquet ...")
t0 = time.time()
pair_aug = pq.read_table(ROOT / "data" / "feature_table_aug.parquet").to_pandas()
print(f"  done ({time.time()-t0:.1f}s)")
print("loading high_only_aug parquet ...")
t0 = time.time()
high_aug = pq.read_table(ROOT / "data" / "feature_table_high_only_aug.parquet").to_pandas()
print(f"  done ({time.time()-t0:.1f}s)")

for col in ("default_bot_is_ds", "n_top_choices_yielding_ds_bot", "pair_to_bot_alt_is_ds"):
    df_all[col] = pair_aug[col].values
for col in ("default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot", "best_ds_bot_mid_max_rank"):
    df_all[col] = high_aug[col].values

# ----- Baseline-feature engineering (identical to dt_phase1_3of4.py). -----
df_all["can_make_ds_bot"]   = (df_all["suit_2nd"] >= 2).astype(np.int8)
df_all["can_make_4run"]     = (df_all["connectivity"] >= 4).astype(np.int8)
df_all["has_high_pair"]     = (df_all["pair_high_rank"] >= 12).astype(np.int8)
df_all["has_low_pair"]      = ((df_all["n_pairs"] >= 1) & (df_all["pair_high_rank"] <= 5)).astype(np.int8)
df_all["has_premium_pair"]  = ((df_all["pair_high_rank"] == 14) | (df_all["pair_high_rank"] == 13)).astype(np.int8)
df_all["has_ace_singleton"] = (
    (df_all["top_rank"] == 14)
    & (df_all["pair_high_rank"] != 14)
    & (df_all["trips_rank"] != 14)
    & (df_all["quads_rank"] != 14)
).astype(np.int8)
df_all["has_king_singleton"] = (
    (df_all["top_rank"] >= 13)
    & (df_all["pair_high_rank"] < 13)
    & (df_all["pair_low_rank"] < 13)
    & (df_all["trips_rank"] < 13)
    & (df_all["quads_rank"] < 13)
).astype(np.int8)

cat_map = {c: i for i, c in enumerate(sorted(df_all["category"].unique()))}
df_all["category_id"] = df_all["category"].map(cat_map).astype(np.int8)

baseline_features = [
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
]
pair_aug_features = ["default_bot_is_ds", "n_top_choices_yielding_ds_bot", "pair_to_bot_alt_is_ds"]
high_aug_features = ["default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot", "best_ds_bot_mid_max_rank"]
all_features = baseline_features + pair_aug_features + high_aug_features


def shape_agreement(predicted, indices, hands_local, target_shape_local):
    n = len(predicted)
    correct = 0
    for k in range(n):
        i = indices[k]
        sh = setting_shape(hands_local[i], int(predicted[k]))
        target = (
            int(target_shape_local[i,0]),
            (int(target_shape_local[i,1]), int(target_shape_local[i,2])),
            (int(target_shape_local[i,3]), int(target_shape_local[i,4]),
             int(target_shape_local[i,5]), int(target_shape_local[i,6])),
        )
        if sh == target:
            correct += 1
    return correct / n


def evaluate_subset(name: str, subset_mask: np.ndarray, with_ablation: bool = False):
    df = df_all[subset_mask].reset_index(drop=True)
    hands = hands_all[subset_mask]
    N = len(df)
    print(f"\n=== {name} — {N:,} hands ({100*N/len(hands_all):.2f}% of full 6M) ===")

    y = df["multiway_robust"].values.astype(np.int16)
    print(f"unique setting_indexes in target: {len(np.unique(y))}")

    t0 = time.time()
    target_shape = np.empty((N, 7), dtype=np.int8)
    for i in range(N):
        sh = setting_shape(hands[i], int(y[i]))
        target_shape[i, 0] = sh[0]
        target_shape[i, 1:3] = sh[1]
        target_shape[i, 3:7] = sh[2]
    print(f"shape pre-compute: {time.time()-t0:.1f}s")

    runs = [
        ("BASELINE (27)",         baseline_features),
        ("BASELINE + PAIR (30)",  baseline_features + pair_aug_features),
        ("BASELINE + HIGH (30)",  baseline_features + high_aug_features),
        ("ALL AUGMENTED (33)",    all_features),
    ]

    rows = []
    for label, cols in runs:
        Xf = df[cols].values.astype(np.int16)
        t0 = time.time()
        dt = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
        dt.fit(Xf, y)
        fit_t = time.time() - t0
        preds = dt.predict(Xf)
        literal = float((preds == y).mean())
        t0 = time.time()
        shape_acc = shape_agreement(preds, np.arange(N), hands, target_shape)
        shape_t = time.time() - t0
        leaves = dt.get_n_leaves()
        rows.append((label, leaves, literal, shape_acc, fit_t, shape_t))
        print(f"  {label:<24}  fit={fit_t:5.1f}s  shape_eval={shape_t:5.1f}s  "
              f"leaves={leaves:>7,}  literal={100*literal:5.2f}%  shape={100*shape_acc:5.2f}%")

    if with_ablation:
        print(f"\n  ----- per-feature drop-out ablation on {name} (vs ALL AUGMENTED) -----")
        full_shape = rows[-1][3]
        for drop in pair_aug_features + high_aug_features:
            cols = [c for c in all_features if c != drop]
            Xf = df[cols].values.astype(np.int16)
            t0 = time.time()
            dt = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
            dt.fit(Xf, y)
            preds = dt.predict(Xf)
            shape_acc = shape_agreement(preds, np.arange(N), hands, target_shape)
            delta = (full_shape - shape_acc) * 100
            tag = "← LARGEST DROP" if delta > 0 else ""
            print(f"    drop {drop:<32} shape={100*shape_acc:5.2f}%  "
                  f"Δ={delta:+5.2f}pp ({time.time()-t0:.1f}s) {tag}")

    return rows


# ----- Subset masks. -----
mask_3of4       = (df_all["mode_count"].values == 3)
mask_full       = np.ones(len(df_all), dtype=bool)
mask_high       = (df_all["category"].values == "high_only")
mask_high_3of4  = mask_3of4 & mask_high
mask_pair       = (df_all["category"].values == "pair")
mask_pair_3of4  = mask_3of4 & mask_pair

# ----- Evaluation order: slice first (fast); then propagation. -----
evaluate_subset("HIGH_ONLY 3-of-4 (slice)",      mask_high_3of4, with_ablation=True)
evaluate_subset("HIGH_ONLY full",                mask_high)
evaluate_subset("3-of-4 MAJORITY",               mask_3of4)
evaluate_subset("FULL 6M",                       mask_full)

print("\n=== Reference: Session 16/17 results ===")
print("  full 6M baseline  depth=None:  61.74% / 57.24% (full / cv)")
print("  full 6M aug-30    depth=None:  63.76% / 58.0%")
print("  3-of-4 baseline   depth=None:  70.01%")
print("  3-of-4 aug-30     depth=None:  72.61%")
print("  pair 3-of-4 baseline:           74.23%")
print("  pair 3-of-4 aug-30:             80.08%")
print("  high_only 3-of-4 baseline:      39.64% (Session 18 mining)")
