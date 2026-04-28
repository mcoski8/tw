"""
Session 18 — high_only miss-driven feature mining (Steps 1-3).

Modelled on mine_pair_leaves.py. Filters feature_table.parquet to
(mode_count == 3 AND category == 'high_only'), trains a depth=None
DecisionTreeClassifier on the current 27-feature set, reports shape-agreement
ceiling on the slice, then ranks terminal leaves by absolute shape-miss count
and dumps the cards clustering in the top-N most impactful leaves.

The Session 17 pair-aug features are vacuous on non-pair hands, so they
contribute nothing to this slice. The discovery target is high_only-specific
structural blind spots (likely: bot-DS-per-top-choice, mid-suit-coupling,
gap-sensitivity of top-demotion).

Output: prints a per-depth report, then for the top-50 leaves by miss count:
  - leaf id, n_samples, n_misses, miss-share, predicted-shape
  - distribution of TRUE shapes in that leaf (top 3)
  - 8 sample hands tagged correct/miss with one-line feature summary
"""
from __future__ import annotations

import sys
import time
from collections import Counter
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

RANK_CHARS = "23456789TJQKA"
SUIT_CHARS = "cdhs"

def card_str(byte: int) -> str:
    rank = (byte // 4) + 2
    suit = byte % 4
    return f"{RANK_CHARS[rank-2]}{SUIT_CHARS[suit]}"

def hand_str(hand: np.ndarray) -> str:
    return " ".join(card_str(int(b)) for b in hand)

def shape_str(shape: tuple) -> str:
    top, mid, bot = shape
    rank_to = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
               10:"T",11:"J",12:"Q",13:"K",14:"A"}
    t = rank_to[top]
    m = "-".join(rank_to[r] for r in sorted(mid, reverse=True))
    b = "-".join(rank_to[r] for r in sorted(bot, reverse=True))
    return f"top {t} | mid {m} | bot {b}"


# ---------- Load + filter ----------
t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df):,} hands ({time.time()-t0:.1f}s)")

mask = (df["mode_count"].values == 3) & (df["category"].values == "high_only")
df = df[mask].reset_index(drop=True)
hands = hands_all[mask]
N = len(df)
print(f"slice: mode_count==3 AND category=='high_only' → {N:,} hands "
      f"({100*N/len(mask):.2f}% of full 6M)")

y = df["multiway_robust"].values.astype(np.int16)
print(f"unique setting_indexes in slice: {len(np.unique(y))}")

# ---------- Pre-compute target shape tuples ----------
t0 = time.time()
target_shape = np.empty((N, 7), dtype=np.int8)
for i in range(N):
    sh = setting_shape(hands[i], int(y[i]))
    target_shape[i, 0] = sh[0]
    target_shape[i, 1:3] = sh[1]
    target_shape[i, 3:7] = sh[2]
print(f"pre-computed target shape tuples ({time.time()-t0:.1f}s)")

def shape_of(i: int, setting_idx: int) -> tuple:
    sh = setting_shape(hands[i], int(setting_idx))
    return (sh[0], tuple(sh[1]), tuple(sh[2]))

def target_shape_of(i: int) -> tuple:
    return (
        int(target_shape[i, 0]),
        (int(target_shape[i, 1]), int(target_shape[i, 2])),
        (int(target_shape[i, 3]), int(target_shape[i, 4]),
         int(target_shape[i, 5]), int(target_shape[i, 6])),
    )

# ---------- Feature engineering (identical to dt_phase1.py) ----------
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
]
X = df[features].values.astype(np.int16)
print(f"X = {X.shape}")

# ---------- Train depth=None DT on slice ----------
t0 = time.time()
dt = DecisionTreeClassifier(max_depth=None, random_state=42, criterion="gini")
dt.fit(X, y)
fit_t = time.time() - t0
preds = dt.predict(X)
literal_acc = float((preds == y).mean())

# Shape ceiling on slice
t0 = time.time()
shape_correct = np.zeros(N, dtype=bool)
for i in range(N):
    pred_shape = shape_of(i, int(preds[i]))
    target = target_shape_of(i)
    shape_correct[i] = (pred_shape == target)
shape_acc = float(shape_correct.mean())
shape_t = time.time() - t0

leaf_ids = dt.apply(X)
n_leaves = dt.get_n_leaves()
print(f"\n=== depth=None DT on high_only 3-of-4 slice ===")
print(f"fit time:           {fit_t:.1f}s")
print(f"shape eval time:    {shape_t:.1f}s")
print(f"n_leaves:           {n_leaves:,}")
print(f"literal agreement:  {100*literal_acc:.2f}%")
print(f"shape agreement:    {100*shape_acc:.2f}%   ← slice ceiling")

# ---------- Rank leaves by absolute shape-miss count ----------
print(f"\n=== Top 50 leaves by absolute shape-miss count ===\n")
unique_leaves = np.unique(leaf_ids)
print(f"distinct leaves visited: {len(unique_leaves):,}")

miss_mask = ~shape_correct
leaf_to_indices: dict[int, np.ndarray] = {}
for lid in unique_leaves:
    leaf_to_indices[int(lid)] = np.where(leaf_ids == lid)[0]

leaf_stats = []
for lid, idxs in leaf_to_indices.items():
    n_s = len(idxs)
    n_miss = int(miss_mask[idxs].sum())
    if n_miss == 0:
        continue
    pred_setting = int(preds[idxs[0]])
    pred_shape = shape_of(int(idxs[0]), pred_setting)
    leaf_stats.append((lid, n_s, n_miss, pred_setting, pred_shape, idxs))

leaf_stats.sort(key=lambda r: r[2], reverse=True)
total_miss = int(miss_mask.sum())
print(f"total slice misses: {total_miss:,} hands ({100*total_miss/N:.2f}% of slice)")
print()

TOP_LEAVES = 50
SAMPLE_PER_LEAF = 8

cum_miss = 0
for rank, (lid, n_s, n_miss, pred_setting, pred_shape, idxs) in enumerate(leaf_stats[:TOP_LEAVES]):
    cum_miss += n_miss
    miss_share = n_miss / n_s
    print(f"--- Leaf rank {rank+1:>2} (id={lid}) — {n_s:,} hands, {n_miss:,} misses "
          f"({100*miss_share:.1f}% of leaf) ---")
    print(f"  predicted setting = {pred_setting}, shape = {shape_str(pred_shape)}")

    shape_counter: Counter = Counter()
    for j in idxs:
        shape_counter[target_shape_of(int(j))] += 1
    print(f"  true-shape distribution (top 3 of {len(shape_counter)}):")
    for sh, cnt in shape_counter.most_common(3):
        match = "✓ pred" if sh == pred_shape else "  miss"
        print(f"    {match} {cnt:>5}  {shape_str(sh)}")

    miss_idxs = idxs[miss_mask[idxs]]
    correct_idxs = idxs[~miss_mask[idxs]]
    sample_miss = miss_idxs[:SAMPLE_PER_LEAF]
    sample_correct = correct_idxs[:max(0, 2)]
    print(f"  sample misses (up to {SAMPLE_PER_LEAF}):")
    for j in sample_miss:
        h = hands[int(j)]
        true_sh = target_shape_of(int(j))
        ace_sng = int(df["has_ace_singleton"].iloc[int(j)])
        king_sng = int(df["has_king_singleton"].iloc[int(j)])
        ds = int(df["can_make_ds_bot"].iloc[int(j)])
        run = int(df["can_make_4run"].iloc[int(j)])
        suits = (f"sm={int(df['suit_max'].iloc[int(j)])}"
                 f" s2={int(df['suit_2nd'].iloc[int(j)])}"
                 f" s3={int(df['suit_3rd'].iloc[int(j)])}")
        conn = int(df["connectivity"].iloc[int(j)])
        nbw = int(df["n_broadway"].iloc[int(j)])
        tr = int(df["top_rank"].iloc[int(j)])
        sr = int(df["second_rank"].iloc[int(j)])
        tags = []
        if ace_sng: tags.append("Asng")
        if king_sng: tags.append("Ksng")
        if ds: tags.append("DS-feas")
        if run: tags.append("4run")
        tag_str = ",".join(tags) or "-"
        print(f"    {hand_str(h):<26}  top={tr} 2nd={sr}  {suits} conn={conn} bw={nbw}  [{tag_str}]")
        print(f"      true: {shape_str(true_sh)}")
    if rank < 5 and len(sample_correct) > 0:
        print(f"  sample correct ({len(sample_correct)}):")
        for j in sample_correct:
            h = hands[int(j)]
            print(f"    {hand_str(h):<26}")
    print()

print(f"=== Top {TOP_LEAVES} leaves cover {cum_miss:,} of {total_miss:,} slice-misses "
      f"({100*cum_miss/total_miss:.1f}%) ===")

miss_leaves = [r for r in leaf_stats]
print(f"\n{len(miss_leaves):,} leaves have at least one miss.")
top10_pct = sorted([r[2] for r in miss_leaves], reverse=True)
top_10 = sum(top10_pct[:10])
top_50 = sum(top10_pct[:50])
top_100 = sum(top10_pct[:100])
print(f"miss concentration: top 10 leaves = {100*top_10/total_miss:.1f}% of misses, "
      f"top 50 = {100*top_50/total_miss:.1f}%, top 100 = {100*top_100/total_miss:.1f}%")
