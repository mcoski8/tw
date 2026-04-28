"""
Session 17 — augmented-feature DT ceiling on the single-pair 3-of-4 slice.

Steps (per the 4-step methodology doctrine):
  Step 2 (signal): odds-ratio of each new feature against (BR uses v3-default
    routing) on the slice — confirms each feature carries usable signal.
  Step 4 (cheap test): re-train depth=None DT with the 27 baseline features
    PLUS the 3 new ones; compare shape-agreement ceiling vs 74.23% baseline.

Baseline reference: dt_phase1_3of4.py says the 27-feature ceiling on the
broader 3-of-4 majority subset is 70.01%. mine_pair_leaves.py confirmed
74.23% on (mode_count==3 AND category=='pair').
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
from tw_analysis.features import decode_tier_positions  # noqa: E402
from pair_aug_features import compute_pair_aug_batch  # noqa: E402

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df):,} hands ({time.time()-t0:.1f}s)")

# ----- Slice: pair AND mode_count==3 -----
mask = (df["mode_count"].values == 3) & (df["category"].values == "pair")
df = df[mask].reset_index(drop=True)
hands = hands_all[mask]
N = len(df)
print(f"slice: {N:,} hands")

y = df["multiway_robust"].values.astype(np.int16)

# ----- Pre-compute target shape tuples for fast scoring -----
t0 = time.time()
target_shape = np.empty((N, 7), dtype=np.int8)
for i in range(N):
    sh = setting_shape(hands[i], int(y[i]))
    target_shape[i, 0] = sh[0]
    target_shape[i, 1:3] = sh[1]
    target_shape[i, 3:7] = sh[2]
print(f"pre-computed shapes ({time.time()-t0:.1f}s)")

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

# ----- Baseline 27 features (identical to dt_phase1.py) -----
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

# ----- Compute augmented features (single-pair only) -----
print("\nComputing augmented features...")
t0 = time.time()
slice_mask_local = np.ones(N, dtype=bool)  # the dataframe IS the slice
augmented = compute_pair_aug_batch(hands, slice_mask_local)
print(f"augmented features computed ({time.time()-t0:.1f}s)")
for col, vals in augmented.items():
    df[col] = vals
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{c:,}" for u, c in zip(uniq, counts))
    print(f"  {col:<32}  distribution: {dist}")

augmented_features = list(augmented.keys())
all_features = baseline_features + augmented_features
print(f"\ntotal feature count: {len(baseline_features)} baseline + {len(augmented_features)} new = {len(all_features)}")

# ----- Step 2: signal check via odds ratio. -----
# We need a "BR uses v3-default routing" outcome variable. Compute it from
# the multiway_robust setting_index: does the BR's chosen TOP rank equal the
# highest singleton rank (the v3 default)?
print("\n=== Step 2: signal odds ratios ===")
t0 = time.time()

def is_default_routing(i: int) -> bool:
    """True iff multiway_robust[i] uses (mid=highest pair, top=highest singleton)."""
    setting_idx = int(y[i])
    t_pos, m_pos, _b_pos = decode_tier_positions(setting_idx)
    h = hands[i]
    ranks = (h // 4) + 2
    # highest singleton rank
    rank_to_positions: dict[int, list[int]] = {}
    for p in range(7):
        rank_to_positions.setdefault(int(ranks[p]), []).append(p)
    sing_desc: list[tuple[int,int]] = []
    pair_pos: list[int] = []
    for r, ps in rank_to_positions.items():
        if len(ps) == 2:
            pair_pos = ps
        else:
            sing_desc.append((r, ps[0]))
    sing_desc.sort(reverse=True)
    if len(pair_pos) != 2 or len(sing_desc) != 5:
        return False
    return (set(m_pos) == set(pair_pos)) and (t_pos == sing_desc[0][1])

is_default = np.zeros(N, dtype=bool)
for i in range(N):
    is_default[i] = is_default_routing(i)
print(f"BR uses v3-default routing in {is_default.sum():,} of {N:,} slice hands "
      f"({100*is_default.mean():.2f}%) ({time.time()-t0:.1f}s)")

def odds_ratio(feat_vals: np.ndarray, outcome: np.ndarray) -> tuple[float, int, int, int, int]:
    """OR for binary feature → binary outcome.

    Computes 2x2 table:
      a = feat=1, outcome=1
      b = feat=1, outcome=0
      c = feat=0, outcome=1
      d = feat=0, outcome=0
    OR = (a*d)/(b*c). Returns (or, a, b, c, d).
    """
    f = feat_vals.astype(bool)
    a = int((f & outcome).sum())
    b = int((f & ~outcome).sum())
    c = int((~f & outcome).sum())
    d = int((~f & ~outcome).sum())
    if b == 0 or c == 0:
        return (float("inf") if (a*d) > 0 else 0.0, a, b, c, d)
    return ((a * d) / (b * c), a, b, c, d)

print()
for col in augmented_features:
    vals = df[col].values
    if col == "n_top_choices_yielding_ds_bot":
        # treat as "≥1" for binary OR
        vals_bin = (vals >= 1).astype(np.int8)
        or_, a, b, c, d = odds_ratio(vals_bin, is_default)
        print(f"  {col:<32}  (≥1)  OR={or_:>5.2f}  a={a:>7,} b={b:>7,} c={c:>7,} d={d:>7,}")
        # also show ≥3
        vals_bin3 = (vals >= 3).astype(np.int8)
        or_, a, b, c, d = odds_ratio(vals_bin3, is_default)
        print(f"  {col:<32}  (≥3)  OR={or_:>5.2f}  a={a:>7,} b={b:>7,} c={c:>7,} d={d:>7,}")
    else:
        or_, a, b, c, d = odds_ratio(vals, is_default)
        print(f"  {col:<32}        OR={or_:>5.2f}  a={a:>7,} b={b:>7,} c={c:>7,} d={d:>7,}")

# ----- Step 4: cheap test — depth=None DT with augmented features. -----
print("\n=== Step 4: depth=None DT comparison ===")
def fit_and_score(feature_cols: list[str], label: str):
    Xf = df[feature_cols].values.astype(np.int16)
    t0 = time.time()
    dt = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
    dt.fit(Xf, y)
    fit_t = time.time() - t0
    preds = dt.predict(Xf)
    literal_acc = float((preds == y).mean())
    t0 = time.time()
    shape_acc = shape_agreement(preds, np.arange(N))
    shape_t = time.time() - t0
    leaves = dt.get_n_leaves()
    print(f"  {label}")
    print(f"    n_features = {len(feature_cols)}  fit={fit_t:.1f}s  shape_eval={shape_t:.1f}s")
    print(f"    n_leaves   = {leaves:,}")
    print(f"    literal    = {100*literal_acc:.2f}%")
    print(f"    shape      = {100*shape_acc:.2f}%")
    return shape_acc

print()
shape_baseline = fit_and_score(baseline_features, "BASELINE  (27 features)")
print()
shape_aug      = fit_and_score(all_features,      "AUGMENTED (27 + 3 = 30 features)")

print(f"\n=== Lift: {100*(shape_aug - shape_baseline):+.2f}pp "
      f"(baseline {100*shape_baseline:.2f}% → augmented {100*shape_aug:.2f}%) ===")

# Also show individual contribution.
print("\n=== Per-feature drop-out test (augmented minus one) ===")
for drop in augmented_features:
    cols = [c for c in all_features if c != drop]
    sa = fit_and_score(cols, f"AUG−{drop}")
    print(f"  shape without {drop}: {100*sa:.2f}% (Δ from full aug = {100*(sa - shape_aug):+.2f}pp)")
    print()
