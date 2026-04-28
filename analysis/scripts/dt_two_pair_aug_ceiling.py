"""
Session 19 — augmented-feature ceiling on two_pair slices + drop-out ablation.

Mirrors dt_high_only_aug_ceiling.py (Session 18). Trains depth=None DTs on
multiple subsets:
  - two_pair 3-of-4 (slice — primary target)
  - two_pair full
  - 3-of-4 majority (with all 3 augment families: pair + high + 2p)
  - full 6M

For each, compares baseline 27 features vs +pair-aug, +high-aug, +2p-aug,
+ALL combinations. Per-feature drop-out ablation on the slice confirms
each new 2p-aug feature's contribution.

References for context:
  - Session 18 augmented (33 features = 27 + 3 pair + 3 high):
      pair 3-of-4:        80.08%
      high_only 3-of-4:   48.92%
      3-of-4:             74.38%
      full 6M:            65.20%
  - Session 19 mining: two_pair 3-of-4 baseline 79.47% / 39,677 leaves
                       (signal_or_two_pair literal lift: +5.95pp).
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
from two_pair_aug_features import compute_two_pair_aug_batch  # noqa: E402

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df_all = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df_all):,} hands ({time.time()-t0:.1f}s)")

print("loading pair_aug + high_only_aug parquets ...")
t0 = time.time()
pair_aug = pq.read_table(ROOT / "data" / "feature_table_aug.parquet").to_pandas()
high_aug = pq.read_table(ROOT / "data" / "feature_table_high_only_aug.parquet").to_pandas()
print(f"  done ({time.time()-t0:.1f}s)")

for col in ("default_bot_is_ds", "n_top_choices_yielding_ds_bot", "pair_to_bot_alt_is_ds"):
    df_all[col] = pair_aug[col].values
for col in ("default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot", "best_ds_bot_mid_max_rank"):
    df_all[col] = high_aug[col].values

print("computing two_pair_aug features (only on two_pair rows) ...")
mask_two_pair_full = (df_all["category"].values == "two_pair")
t0 = time.time()
tp_aug = compute_two_pair_aug_batch(hands_all, mask_two_pair_full)
print(f"  done ({time.time()-t0:.1f}s)  — {int(mask_two_pair_full.sum()):,} two_pair rows augmented")
for col in ("default_bot_is_ds_tp", "n_routings_yielding_ds_bot_tp", "swap_high_pair_to_bot_ds_compatible"):
    df_all[col] = tp_aug[col]

# Baseline-feature engineering (identical to dt_high_only_aug_ceiling.py).
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
tp_aug_features = ["default_bot_is_ds_tp", "n_routings_yielding_ds_bot_tp", "swap_high_pair_to_bot_ds_compatible"]
all_features = baseline_features + pair_aug_features + high_aug_features + tp_aug_features


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
        ("BASELINE (27)",          baseline_features),
        ("+ PAIR (30)",            baseline_features + pair_aug_features),
        ("+ HIGH (30)",            baseline_features + high_aug_features),
        ("+ 2P (30)",              baseline_features + tp_aug_features),
        ("+ PAIR+HIGH (33)",       baseline_features + pair_aug_features + high_aug_features),
        ("+ ALL AUGMENTED (36)",   all_features),
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
        print(f"\n  ----- per-feature drop-out ablation on {name} (vs ALL AUGMENTED 36) -----")
        full_shape = rows[-1][3]
        all_aug = pair_aug_features + high_aug_features + tp_aug_features
        for drop in all_aug:
            cols = [c for c in all_features if c != drop]
            Xf = df[cols].values.astype(np.int16)
            t0 = time.time()
            dt = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
            dt.fit(Xf, y)
            preds = dt.predict(Xf)
            shape_acc = shape_agreement(preds, np.arange(N), hands, target_shape)
            delta = (full_shape - shape_acc) * 100
            print(f"    drop {drop:<40} shape={100*shape_acc:5.2f}%  "
                  f"Δ={delta:+5.2f}pp ({time.time()-t0:.1f}s)")

    return rows


mask_3of4         = (df_all["mode_count"].values == 3)
mask_full         = np.ones(len(df_all), dtype=bool)
mask_two_pair     = (df_all["category"].values == "two_pair")
mask_two_pair_3of4 = mask_3of4 & mask_two_pair

evaluate_subset("TWO_PAIR 3-of-4 (slice)",        mask_two_pair_3of4, with_ablation=True)
evaluate_subset("TWO_PAIR full",                  mask_two_pair)
evaluate_subset("3-of-4 MAJORITY",                mask_3of4)
evaluate_subset("FULL 6M",                        mask_full)

print("\n=== Reference: Session 17/18 results (depth=None) ===")
print("  full 6M baseline (27):       61.74%")
print("  full 6M + pair (30):         63.76%  (+2.02pp)")
print("  full 6M + pair+high (33):    65.20%  (+3.46pp)")
print("  3-of-4 + pair+high (33):     74.38%")
print("  high_only 3-of-4 + 33:       48.92%  (lift +9.28pp from 39.64% baseline)")
print("  pair 3-of-4 + 30:            80.08%  (lift +5.85pp from 74.23% baseline)")
print("  two_pair 3-of-4 baseline:    79.47% (Session 19 mining)")
