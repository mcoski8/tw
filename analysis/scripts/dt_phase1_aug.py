"""
Session 17 — depth-vs-agreement ceiling curve on the FULL 6M canonical set
with the 27 baseline features + 3 single-pair augmented features.

Identical methodology to dt_phase1.py (same CV folds, same depth list, same
shape-agreement scoring) so the only changed variable is the feature set.

Reference (dt_phase1.py, Session 16, baseline 27 features):
  depth=None  ceiling  61.74% / 57.24% (full / cv)
  cv peak     depth 15  cv_shape 59.57%

Hypothesis: the +2.02pp full-6M lift seen in dt_phase1_3of4_aug.py at
depth=None should propagate to bounded depths. If lift survives at depth
10-15, that depth is a viable target for chain extraction (Step 6 of the
Session 17 plan).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import KFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis import read_canonical_hands  # noqa: E402
from encode_rules import setting_shape  # noqa: E402
from pair_aug_features import compute_pair_aug_batch  # noqa: E402

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
N = len(df)
print(f"loaded {N:,} hands ({time.time()-t0:.1f}s)")

y = df["multiway_robust"].values.astype(np.int16)
print(f"unique setting_indexes in target: {len(np.unique(y))}")

# Pre-compute target shape tuples for fast scoring.
t0 = time.time()
print("pre-computing target shape tuples ...")
target_shape = np.empty((N, 7), dtype=np.int8)
for i in range(N):
    sh = setting_shape(hands[i], int(y[i]))
    target_shape[i, 0] = sh[0]
    target_shape[i, 1:3] = sh[1]
    target_shape[i, 3:7] = sh[2]
print(f"  done ({time.time()-t0:.1f}s)")

# Compute augmented features for the single-pair sub-population.
print("Computing augmented features (single-pair only)...")
t0 = time.time()
pair_mask = (df["category"].values == "pair")
augmented = compute_pair_aug_batch(hands, pair_mask)
print(f"  done ({time.time()-t0:.1f}s)")
for col, vals in augmented.items():
    df[col] = vals

# ---------- Feature engineering (identical to dt_phase1.py) + 3 new aug ----------
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

features = [
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
    # Session 17 augmented:
    "default_bot_is_ds","n_top_choices_yielding_ds_bot","pair_to_bot_alt_is_ds",
]
X = df[features].values.astype(np.int16)
print(f"X = {X.shape}\n")


def shape_agreement(predicted, indices):
    n = len(predicted)
    correct = 0
    for k in range(n):
        i = indices[k]
        sh = setting_shape(hands[i], int(predicted[k]))
        target = (
            int(target_shape[i,0]),
            (int(target_shape[i,1]), int(target_shape[i,2])),
            (int(target_shape[i,3]), int(target_shape[i,4]),
             int(target_shape[i,5]), int(target_shape[i,6])),
        )
        if sh == target:
            correct += 1
    return correct / n


# ---------- Depth sweep ----------
print(f"{'depth':<8}{'leaves':>10}{'cv_acc':>10}{'cv_shape':>10}{'full_acc':>11}{'full_shape':>12}{'fit_s':>8}")

rng = np.random.default_rng(0)
sub_idx = rng.choice(N, size=1_000_000, replace=False)
Xs = X[sub_idx]; ys = y[sub_idx]
all_idx = np.arange(N)

results = []
for depth in [3, 5, 7, 10, 15, 20, None]:
    label = str(depth) if depth is not None else "None"
    kf = KFold(n_splits=3, shuffle=True, random_state=0)
    cv_accs, cv_shapes = [], []
    for tr, te in kf.split(Xs):
        dt = DecisionTreeClassifier(max_depth=depth, random_state=42, criterion="gini")
        dt.fit(Xs[tr], ys[tr])
        cv_accs.append(dt.score(Xs[te], ys[te]))
        eval_idx = sub_idx[te[:50_000]]
        preds = dt.predict(X[eval_idx])
        cv_shapes.append(shape_agreement(preds, eval_idx))
    cv_acc_m = float(np.mean(cv_accs))
    cv_shape_m = float(np.mean(cv_shapes))

    fit_t0 = time.time()
    dt_full = DecisionTreeClassifier(max_depth=depth, random_state=42, criterion="gini")
    dt_full.fit(X, y)
    fit_t = time.time() - fit_t0
    full_pred = dt_full.predict(X)
    full_acc = float((full_pred == y).mean())
    full_shape = shape_agreement(full_pred, all_idx)
    leaves = dt_full.get_n_leaves()
    print(f"{label:<8}{leaves:>10,}{cv_acc_m*100:>9.2f}%{cv_shape_m*100:>9.2f}%"
          f"{full_acc*100:>10.2f}%{full_shape*100:>11.2f}%{fit_t:>7.1f}s")
    results.append((depth, leaves, cv_acc_m, cv_shape_m, full_acc, full_shape, fit_t))

print()
print("Reference (baseline 27 features, dt_phase1.py — Session 16):")
print(f"  depth=None ceiling: 61.74% / 57.24% (full / cv)")
print(f"  cv peak depth=15:    cv_shape 59.57%")
print()
print("v3 baseline (current rule chain) shape-agreement on full 6M: 56.16%")
