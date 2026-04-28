"""
Session 19 — odds-ratio signal check for the 3 candidate two_pair-aug features.

Doctrine (Decision 033, step 2): measure signal BEFORE training compute.
For each candidate feature, compute:
  - distribution over the slice
  - P(BR = DT-default-routing | feature value) cross-tab
  - odds ratio for the binary features

The "DT-default-routing" proxy: BR's setting_index in the top-N most-common
DT-predicted settings on the slice (settings 14 + 44 dominate per the
leaf-dump sample). If the candidate features sharply discriminate between
"BR sticks with default" and "BR swaps", they have signal.

Halt-gate: if the strongest feature OR is < 2x AND the cross-tab spread
is <10pp, signal is weak — document the negative result and recommend
pivot to path (b) (chain extraction from current 33-feature tree) rather
than continuing the augmentation pipeline.
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
from two_pair_aug_features import compute_two_pair_aug_batch  # noqa: E402

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df):,} hands ({time.time()-t0:.1f}s)")

mask = (df["mode_count"].values == 3) & (df["category"].values == "two_pair")
df_slice = df[mask].reset_index(drop=True)
hands = hands_all[mask]
N = len(df_slice)
print(f"slice: mode_count==3 AND category=='two_pair' → {N:,} hands")

# Compute features on slice.
t0 = time.time()
feats = compute_two_pair_aug_batch(hands_all, mask)
print(f"feature compute on slice: {time.time()-t0:.1f}s")

f1 = feats["default_bot_is_ds_tp"][mask]
f2 = feats["n_routings_yielding_ds_bot_tp"][mask]
f3 = feats["swap_high_pair_to_bot_ds_compatible"][mask]

print(f"\nDistribution of features on slice:")
for name, arr in (("f1=default_bot_is_ds_tp", f1),
                  ("f2=n_routings_yielding_ds_bot_tp", f2),
                  ("f3=swap_high_pair_to_bot_ds_compatible", f3)):
    vals, cnts = np.unique(arr, return_counts=True)
    print(f"  {name}:")
    for v, c in zip(vals, cnts):
        print(f"    {int(v)}: {int(c):>8,} ({100*c/N:5.2f}%)")

# Identify dominant DT-default settings on slice via baseline DT.
print("\nFitting baseline depth=None DT on slice (27 features) for default-setting reference ...")
from sklearn.tree import DecisionTreeClassifier

df_slice["can_make_ds_bot"]   = (df_slice["suit_2nd"] >= 2).astype(np.int8)
df_slice["can_make_4run"]     = (df_slice["connectivity"] >= 4).astype(np.int8)
df_slice["has_high_pair"]     = (df_slice["pair_high_rank"] >= 12).astype(np.int8)
df_slice["has_low_pair"]      = ((df_slice["n_pairs"] >= 1) & (df_slice["pair_high_rank"] <= 5)).astype(np.int8)
df_slice["has_premium_pair"]  = ((df_slice["pair_high_rank"] == 14) | (df_slice["pair_high_rank"] == 13)).astype(np.int8)
df_slice["has_ace_singleton"] = (
    (df_slice["top_rank"] == 14)
    & (df_slice["pair_high_rank"] != 14)
    & (df_slice["trips_rank"] != 14)
    & (df_slice["quads_rank"] != 14)
).astype(np.int8)
df_slice["has_king_singleton"] = (
    (df_slice["top_rank"] >= 13)
    & (df_slice["pair_high_rank"] < 13)
    & (df_slice["pair_low_rank"] < 13)
    & (df_slice["trips_rank"] < 13)
    & (df_slice["quads_rank"] < 13)
).astype(np.int8)
cat_map = {c: i for i, c in enumerate(sorted(df["category"].unique()))}
df_slice["category_id"] = df_slice["category"].map(cat_map).astype(np.int8)

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
X = df_slice[baseline_features].values.astype(np.int16)
y = df_slice["multiway_robust"].values.astype(np.int16)
dt = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
dt.fit(X, y)
preds = dt.predict(X)
literal_acc = (preds == y).mean()
print(f"  baseline DT slice literal-agreement: {100*literal_acc:.2f}%")

# "Match-default" proxy: prediction == BR. When match-default = 1, the DT
# (which has only baseline features) gets the right answer; when 0, BR
# diverges from what the baseline-feature DT would call default.
match_default = (preds == y).astype(np.int8)
print(f"\nP(BR = baseline-DT prediction): {100*match_default.mean():.2f}% (= literal-agreement on slice)")

print("\n--- Cross-tabs (rows = feature value; col = % match-default) ---")

def crosstab(name, arr):
    print(f"\n  {name}:")
    vals = np.unique(arr)
    for v in vals:
        sel = arr == v
        n = int(sel.sum())
        if n == 0:
            continue
        match_rate = 100 * match_default[sel].mean()
        print(f"    f={int(v):>2}  n={n:>8,}  P(BR=baseline)={match_rate:5.2f}%")

crosstab("f1=default_bot_is_ds_tp", f1)
crosstab("f2=n_routings_yielding_ds_bot_tp", f2)
crosstab("f3=swap_high_pair_to_bot_ds_compatible", f3)

print("\n--- Odds ratios for binary features (f1, f3) ---")
def odds_ratio(name, arr):
    sel1 = arr == 1
    sel0 = arr == 0
    p1 = match_default[sel1].mean() if sel1.sum() else 0.0
    p0 = match_default[sel0].mean() if sel0.sum() else 0.0
    if p0 in (0.0, 1.0) or p1 in (0.0, 1.0):
        print(f"  {name}: degenerate (p0={p0}, p1={p1})")
        return
    or_ = (p1 / (1 - p1)) / (p0 / (1 - p0))
    print(f"  {name}: P|f=1={100*p1:.2f}%  P|f=0={100*p0:.2f}%  OR={or_:.2f}x")

odds_ratio("f1=default_bot_is_ds_tp", f1)
odds_ratio("f3=swap_high_pair_to_bot_ds_compatible", f3)

print("\n--- Sanity: does adding the 3 features lift the slice ceiling? ---")
for label, extra in (
    ("BASELINE (27)", []),
    ("BASELINE + 2P-AUG (30)", [f1, f2, f3]),
):
    if not extra:
        Xrun = X
    else:
        Xrun = np.column_stack([X] + [a.reshape(-1, 1) for a in extra])
    dt2 = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
    dt2.fit(Xrun, y)
    p = dt2.predict(Xrun)
    print(f"  {label:<24}  literal={100*(p==y).mean():5.2f}%  leaves={dt2.get_n_leaves():>7,}")
