"""
Session 74 — train_v47_dt: v44 (107) + 1 high_only_aug_v7 feature = 108 total.

Per SESSION_71_V45_FEATURE_HYPOTHESES.md §6 (originally H3, renumbered to
H2 in S73 CURRENT_PHASE.md) and S73 methodology lessons:

H2 — JOINT-vs-DS_NONJOINT route trade-off comparator. Single signed
scalar:
  best_JOINT_mid_high - best_DS_NONJOINT_top  (int8, range −14..+14)

S71 quoted -13..+13; empirical distribution (persist_v7 output) confirms
values lie in {-14..-1, 0}; positive values structurally rare with
max_rank=A. 15.7% of hands have non-zero signal; 84.3% are 0 (gated
or no DS bot achievable).

**Hyperparameter regime LOCKED to depth=36 ml=1** per S73 methodology
lesson #1: "NEVER change features AND hyperparams in the same
experiment." v44 baseline = depth=36 ml=1 saturating regime.

H1 (ho_v6 SS+ms route quality, v46b_dt) at the same regime landed at
+$5/1000h full grid — within-cat +$24 on high_only, surgical gating
byte-identical on 7 of 8 other cats. Below +$10 ship bar (Decision 108).
H2 tests an alternate-axis feature targeting the remaining $123 of the
S71 diagnostic $147.59 STRUCTURE-bucket leak.

Base set is v44 (NOT v46b) for clean H2 isolation. If v47 ships, the
ho_v7 feature alone clears the +$10 bar. If v47 partial-positives,
consider v48 = v44 + ho_v6 + ho_v7 (110 features) for compound effect.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v47_dt.py \\
      --max-depth 36 --min-samples-leaf 1 --output data/v47_dt_model.npz
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from train_v44_dt import build_X as build_X_v44, FEATURE_COLUMNS as V44_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
HO_V7_PATH = ROOT / "data" / "feature_table_high_only_aug_v7_gated.parquet"

HO_V7_COLUMNS = [
    "ho_v7_route_tradeoff_joint_minus_nonjoint_g",
]
FEATURE_COLUMNS = list(V44_COLUMNS) + HO_V7_COLUMNS  # 107 + 1 = 108


def build_X():
    X44, n = build_X_v44()
    print(f"  v44 base X: {X44.shape}  loading high_only_aug_v7 gated ...", flush=True)
    pv7 = pd.read_parquet(HO_V7_PATH)
    extras = np.empty((n, len(HO_V7_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(HO_V7_COLUMNS):
        extras[:, j] = pv7[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X44, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v47_dt_model.npz")
    args = ap.parse_args()

    X, n = build_X()
    print(f"X={X.shape}  ({len(FEATURE_COLUMNS)} features)", flush=True)

    print("loading Y from grid ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(grid.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB", flush=True)

    print(f"\nfitting DT depth={args.max_depth} ml={args.min_samples_leaf} ...",
          flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=args.max_depth, min_samples_leaf=args.min_samples_leaf,
        random_state=42, criterion="squared_error",
    )
    dt.fit(X, Y)
    print(f"  fit {time.time()-t0:.1f}s  leaves={dt.get_n_leaves():,}  "
          f"depth={dt.get_depth()}", flush=True)

    tree = dt.tree_
    val = tree.value
    if val.ndim == 3:
        val = val[:, :, 0]
    np.savez_compressed(
        args.output,
        children_left=tree.children_left.astype(np.int32),
        children_right=tree.children_right.astype(np.int32),
        feature=tree.feature.astype(np.int32),
        threshold=tree.threshold.astype(np.float64),
        leaf_values=val.astype(np.float32),
        feature_columns=np.array(FEATURE_COLUMNS, dtype=object),
        cat_map_keys=np.array(list(ALPHA_MAP.keys()), dtype=object),
        cat_map_values=np.array(list(ALPHA_MAP.values()), dtype=np.int32),
        depth=np.int32(dt.get_depth()),
        n_leaves=np.int32(dt.get_n_leaves()),
        training_grid=np.array(["full"], dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
    )
    print(f"\nsaved {args.output} ({args.output.stat().st_size/1e6:.2f} MB)",
          flush=True)

    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-30 feature importances:")
    for r, idx in enumerate(order[:30], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<46} {100*fi[idx]:6.2f}%")

    print(f"\nTRIPWIRE — new ho_v7_*_g feature placement:")
    for new_col in HO_V7_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<48} {100*fi[idx]:.2f}%")

    # S73 tripwire calibration: feature importance > leaf growth at saturating
    # regime. Top-50 = ship; 50-100 = ambiguous; 100+ = NULL signal.
    print(f"\nTRIPWIRE INTERPRETATION (S73 calibration):")
    for new_col in HO_V7_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        if rank <= 50:
            sig = "SHIP signal"
        elif rank <= 100:
            sig = "AMBIGUOUS"
        else:
            sig = "NULL signal"
        print(f"  {new_col}: rank #{rank} → {sig}")

    # Leaf-growth tripwire vs v44's 2,248,173.
    v44_leaves = 2_248_173
    delta = dt.get_n_leaves() - v44_leaves
    print(f"\nTRIPWIRE — leaf growth vs v44 ({v44_leaves:,}): {delta:+,}")
    if delta >= 10_000:
        print(f"  ≥10K leaf growth → ship signal (confirmatory at saturating regime)")
    elif delta < 1_000:
        print(f"  <1K leaf growth → NULL signal")
    else:
        print(f"  ambiguous — between 1K and 10K")

    return 0


if __name__ == "__main__":
    sys.exit(main())
