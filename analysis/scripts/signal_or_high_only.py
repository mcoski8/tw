"""
Session 18 — odds-ratio signal test for the 3 high_only candidate features
BEFORE training a tree (per the 4-step doctrine).

For the slice (mode_count==3 AND category=='high_only'), we compute:
  - P(BR uses NAIVE_104 routing) overall
  - P(BR=NAIVE | default_bot_is_ds_high=1)  vs  P(BR=NAIVE | =0)
  - same conditioned on n_mid_choices_yielding_ds_bot bins
  - same conditioned on best_ds_bot_mid_max_rank bins

The "BR uses NAIVE_104" detector here is shape-based: top_rank == byte[6] AND
mid_ranks == sorted(byte[4..5]). We don't care about exact bot-rank-set since
under default routing bot is forced.

Strong signal direction expected:
  - default_bot_is_ds_high=1 → BR almost always NAIVE (high P).
  - default_bot_is_ds_high=0 → BR often deviates (lower P).

If the OR is < 1.5x or unstable, the feature is weak signal — skip training.
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
from high_only_aug_features import compute_high_only_aug_batch  # noqa: E402


def pct(x: float) -> str:
    return f"{100*x:5.2f}%"


t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands_all = canonical.hands
df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
print(f"loaded {len(df):,} hands ({time.time()-t0:.1f}s)")

mask = (df["mode_count"].values == 3) & (df["category"].values == "high_only")
df = df[mask].reset_index(drop=True)
hands = hands_all[mask]
N = len(df)
print(f"slice: high_only 3-of-4 → {N:,} hands ({100*N/len(mask):.2f}% of full 6M)")

# ----- Compute "BR shape == NAIVE_104 shape" -----
# NAIVE shape: top=ranks[6], mid_set={ranks[4],ranks[5]}, bot_set={ranks[0..3]}.
print("Computing NAIVE_104 vs BR shape-equality ...")
t0 = time.time()
y = df["multiway_robust"].values.astype(np.int16)
br_is_naive = np.zeros(N, dtype=bool)
ranks_all = (hands // 4) + 2
for i in range(N):
    sh = setting_shape(hands[i], int(y[i]))
    naive_top = int(ranks_all[i, 6])
    naive_mid = tuple(sorted([int(ranks_all[i, 4]), int(ranks_all[i, 5])]))
    naive_bot = tuple(sorted([int(ranks_all[i, j]) for j in range(4)]))
    br_top = int(sh[0])
    br_mid = tuple(sorted([int(x) for x in sh[1]]))
    br_bot = tuple(sorted([int(x) for x in sh[2]]))
    br_is_naive[i] = (br_top == naive_top and br_mid == naive_mid and br_bot == naive_bot)
print(f"  done ({time.time()-t0:.1f}s). BR=NAIVE rate: {pct(br_is_naive.mean())}")

# ----- Compute the 3 augmented features over the slice. -----
print("\nComputing high_only augmented features ...")
t0 = time.time()
slice_mask = np.ones(N, dtype=bool)  # already filtered
aug = compute_high_only_aug_batch(hands, slice_mask)
print(f"  done ({time.time()-t0:.1f}s)")
f1 = aug["default_bot_is_ds_high"]
f2 = aug["n_mid_choices_yielding_ds_bot"]
f3 = aug["best_ds_bot_mid_max_rank"]


def odds_ratio_2x2(cond: np.ndarray, target: np.ndarray, label: str):
    """OR for binary cond vs binary target."""
    a = int(((cond == 1) & (target == 1)).sum())
    b = int(((cond == 1) & (target == 0)).sum())
    c = int(((cond == 0) & (target == 1)).sum())
    d = int(((cond == 0) & (target == 0)).sum())
    p1 = a / max(a + b, 1)
    p0 = c / max(c + d, 1)
    or_val = (a * d) / max(b * c, 1)
    print(f"  {label}: P(BR=NAIVE|cond=1)={pct(p1)} (n={a+b:,})   "
          f"P(BR=NAIVE|cond=0)={pct(p0)} (n={c+d:,})   OR={or_val:.2f}x")


print("\n=== Feature 1: default_bot_is_ds_high (bool) ===")
odds_ratio_2x2(f1, br_is_naive.astype(np.int8), "default_bot_is_ds_high")

print("\n=== Feature 2: n_mid_choices_yielding_ds_bot (binned) ===")
print(f"  {'bin':>10} {'n':>10} {'BR=NAIVE rate':>16}")
for lo, hi in [(0, 0), (1, 2), (3, 5), (6, 9), (10, 15)]:
    sel = (f2 >= lo) & (f2 <= hi)
    n = int(sel.sum())
    if n == 0:
        continue
    rate = float(br_is_naive[sel].mean())
    print(f"  [{lo:>2},{hi:>2}] {n:>10,}  {pct(rate):>16}")

print("\n=== Feature 3: best_ds_bot_mid_max_rank (binned) ===")
print(f"  {'bin':>10} {'n':>10} {'BR=NAIVE rate':>16}")
for lo, hi, label in [(0, 0, "0 (no DS-bot)"), (4, 8, "4-8"),
                      (9, 10, "9-10"), (11, 12, "11-12 (≥J broadway)"),
                      (13, 14, "13-14 (K/A)")]:
    sel = (f3 >= lo) & (f3 <= hi)
    n = int(sel.sum())
    if n == 0:
        continue
    rate = float(br_is_naive[sel].mean())
    print(f"  {label:<22} {n:>10,}  {pct(rate):>16}")

# ----- Cross-tab: F1=0 vs F1=1, conditional on F2 bins (interaction signal). -----
print("\n=== Cross-tab: F1 × F2 (bin) — interaction ===")
print(f"  {'F1 / F2 bin':>12}  {'(0)':>10} {'(1-2)':>10} {'(3-5)':>10} {'(6+)':>10}")
for f1_val in [0, 1]:
    cells = []
    for lo, hi in [(0, 0), (1, 2), (3, 5), (6, 15)]:
        sel = (f1 == f1_val) & (f2 >= lo) & (f2 <= hi)
        n = int(sel.sum())
        if n == 0:
            cells.append("       —")
        else:
            r = float(br_is_naive[sel].mean())
            cells.append(f"{pct(r)} (n={n//1000}k)")
    print(f"  F1={f1_val:>10}  " + " ".join(f"{c:>10}" for c in cells))

print("\nIf OR(F1) > 1.5x AND F1 × F2 cells separate, the features have")
print("usable signal; proceed to drop-out ablation in dt training.")
