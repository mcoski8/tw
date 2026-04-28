"""
Session 17 — augmented-feature ceiling on the 3-of-4 majority subset
(2.43M hands).

Compares the baseline 27 features (dt_phase1_3of4.py: 70.01%) against the
27 + 3 single-pair augmented features (default_bot_is_ds,
n_top_choices_yielding_ds_bot, pair_to_bot_alt_is_ds). The augmented features
are ZERO on non-pair hands by construction; their contribution is bounded
by the single-pair fraction of the subset (~44%) and the per-pair-hand lift
of +5.85pp shown by dt_pair_aug_ceiling.py.

We also report the full 6M ceiling at the same depth as a cross-check on
production-rule-chain headroom.
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
from pair_aug_features import compute_pair_aug_batch  # noqa: E402

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df_all = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df_all):,} hands ({time.time()-t0:.1f}s)")

# ----- Pre-compute augmented features over the full 6M (vacuous on non-pair). -----
print("Computing augmented features over full 6M (single-pair only)...")
t0 = time.time()
pair_mask = (df_all["category"].values == "pair")
augmented = compute_pair_aug_batch(hands_all, pair_mask)
print(f"augmented features computed ({time.time()-t0:.1f}s)")
for col, vals in augmented.items():
    df_all[col] = vals

# ----- Baseline-feature engineering (identical to dt_phase1_3of4.py) -----
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
augmented_features = list(augmented.keys())
all_features = baseline_features + augmented_features


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


def evaluate_subset(name: str, subset_mask: np.ndarray):
    """Run baseline + augmented depth=None DTs over a subset and report shape ceiling."""
    df = df_all[subset_mask].reset_index(drop=True)
    hands = hands_all[subset_mask]
    N = len(df)
    print(f"\n=== {name} — {N:,} hands "
          f"({100*N/len(hands_all):.2f}% of full 6M) ===")

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

    for label, cols in [("BASELINE (27)", baseline_features),
                        ("AUGMENTED (30)", all_features)]:
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
        print(f"  {label}  fit={fit_t:.1f}s  shape_eval={shape_t:.1f}s  "
              f"leaves={leaves:>7,}  literal={100*literal:5.2f}%  shape={100*shape_acc:5.2f}%")


# ----- Evaluation -----
mask_3of4 = (df_all["mode_count"].values == 3)
mask_full = np.ones(len(df_all), dtype=bool)
mask_pair = (df_all["category"].values == "pair")
mask_pair_3of4 = mask_3of4 & mask_pair

evaluate_subset("FULL 6M",                          mask_full)
evaluate_subset("3-of-4 MAJORITY",                  mask_3of4)
evaluate_subset("SINGLE-PAIR ONLY (3-of-4)",        mask_pair_3of4)
evaluate_subset("SINGLE-PAIR ONLY (full)",          mask_pair)

print("\n=== Reference: dt_phase1.py / dt_phase1_3of4.py results ===")
print("  full 6M baseline  depth=None:  61.74% / 57.24% (full / cv)")
print("  3-of-4 baseline   depth=None:  70.01% / 65.86% (full / cv)")
print("  single-pair 3-of-4 baseline:    74.23% (mine_pair_leaves.py)")
