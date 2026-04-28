"""
Session 18 — depth-vs-agreement curve on the FULL 6M with all 33 features
(27 baseline + 3 pair-aug + 3 high_only-aug).

Identical methodology to dt_phase1.py / dt_phase1_aug.py (3-fold CV on a
1M subsample, full-6M fit at each chosen depth, shape-agreement scoring).

References:
  Session 16 baseline (27 features):
    depth=None:        61.74% / 57.24% (full / cv)
    cv peak depth=15:   cv_shape 59.57%
  Session 17 augmented (30 features = +pair-aug):
    depth=None:        63.76% / 58.0%
    depth=15:          62.0% / 60.7% (knee — best generalization)
  Session 18 ALL AUGMENTED (33) ceiling on full 6M (depth=None):
    65.20% (dt_high_only_aug_ceiling.py)

Hypothesis: the +1.44pp depth=None lift over Session 17 should propagate
to bounded depths. If the lift survives at depth 15, that depth remains
the chain-extraction target with a higher ceiling.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
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

# Load augmented-feature parquets.
print("loading pair_aug parquet ...")
t0 = time.time()
pair_aug = pq.read_table(ROOT / "data" / "feature_table_aug.parquet").to_pandas()
print(f"  done ({time.time()-t0:.1f}s)")
print("loading high_only_aug parquet ...")
t0 = time.time()
high_aug = pq.read_table(ROOT / "data" / "feature_table_high_only_aug.parquet").to_pandas()
print(f"  done ({time.time()-t0:.1f}s)")

for col in ("default_bot_is_ds", "n_top_choices_yielding_ds_bot", "pair_to_bot_alt_is_ds"):
    df[col] = pair_aug[col].values
for col in ("default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot", "best_ds_bot_mid_max_rank"):
    df[col] = high_aug[col].values

# Baseline-feature engineering (identical to dt_phase1.py / dt_phase1_aug.py).
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
    # Session 17 pair-aug:
    "default_bot_is_ds","n_top_choices_yielding_ds_bot","pair_to_bot_alt_is_ds",
    # Session 18 high_only-aug:
    "default_bot_is_ds_high","n_mid_choices_yielding_ds_bot","best_ds_bot_mid_max_rank",
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


# Depth sweep.
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
print("Reference (Session 16/17):")
print("  Session 16 baseline (27)   depth=None:  61.74% / 57.24% (full / cv)")
print("  Session 16 baseline (27)   depth=15:    61.96% / 59.57%")
print("  Session 17 aug-30          depth=None:  63.76% / 58.0%")
print("  Session 17 aug-30          depth=15:    62.0% / 60.7%   ← Session 17 knee")
print("  Session 18 aug-33 ceiling  depth=None:  65.20% (dt_high_only_aug_ceiling.py)")
print()
print("v3 production rule chain shape-agreement on full 6M: 56.16%")
