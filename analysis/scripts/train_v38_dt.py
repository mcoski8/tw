"""
Session 54 — train_v38_dt: extends v36's feature set (83) with 2 new
pair-aug-v4 features = 85 total.

The 2 new features address the dominant pair-zone blind spot identified
in Drill P (Session 53 OVERNIGHT):
  - v36 picks pair-mid SS bot when oracle wants pair-bot DS bot
  - $100/1000h whole-grid contribution from this single mismatch
  - 100% of mismatch hands have DS-achievable pair-bot config
  - But v36's 83 features include NO "pair-bot DS achievability" signal

New features:
  pair_aug_v4_bot_DS_achievable_g       0/1
  pair_aug_v4_n_sings_in_pair_suits_g   0..5

Hypothesis: at the same depth=36 ml=1 capacity, the 2 new features let
the tree carve out the pair-bot zone correctly. Expected lift: $50-150
whole-grid full (capturing some fraction of the $680 mismatch contribution).

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v38_dt.py \\
      --max-depth 36 --min-samples-leaf 1 --output data/v38_dt_model.npz
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
from train_v31b_dt import build_X as build_X_v31b, FEATURE_COLUMNS as V31B_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PAIR_V4_PATH = ROOT / "data" / "feature_table_pair_aug_v4_gated.parquet"

PAIR_V4_COLUMNS = [
    "pair_aug_v4_bot_DS_achievable_g",
    "pair_aug_v4_n_sings_in_pair_suits_g",
]
FEATURE_COLUMNS = list(V31B_COLUMNS) + PAIR_V4_COLUMNS  # 83 + 2 = 85


def build_X():
    X31b, n = build_X_v31b()
    print(f"  v31b base X: {X31b.shape}  loading pair_aug_v4 gated ...", flush=True)
    pv4 = pd.read_parquet(PAIR_V4_PATH)
    extras = np.empty((n, len(PAIR_V4_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(PAIR_V4_COLUMNS):
        extras[:, j] = pv4[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X31b, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v38_dt_model.npz")
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
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<42} {100*fi[idx]:6.2f}%")

    print(f"\nTRIPWIRE — new pair_aug_v4_*_g features placement:")
    for new_col in PAIR_V4_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<42} {100*fi[idx]:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
