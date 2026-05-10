"""
Session 54 — train_v39_dt: v36 (83) + 4 pair_aug_v5 rank-valued features = 87 total.

Phase 2 v1 (v38 = v36 + 2 booleans) shipped $0 because booleans were redundant.
Phase 2 v2: rank-valued conditional features encoding the QUALITY of the
pair-bot DS option (not just achievability).

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v39_dt.py \\
      --max-depth 36 --min-samples-leaf 1 --output data/v39_dt_model.npz
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
PAIR_V5_PATH = ROOT / "data" / "feature_table_pair_aug_v5_gated.parquet"

PAIR_V5_COLUMNS = [
    "pair_aug_v5_bot_DS_n_configs_g",
    "pair_aug_v5_bot_DS_max_top_rank_g",
    "pair_aug_v5_bot_DS_min_top_rank_g",
    "pair_aug_v5_bot_DS_max_mid_sum_g",
]
FEATURE_COLUMNS = list(V31B_COLUMNS) + PAIR_V5_COLUMNS  # 83 + 4 = 87


def build_X():
    X31b, n = build_X_v31b()
    print(f"  v31b base X: {X31b.shape}  loading pair_aug_v5 gated ...", flush=True)
    pv5 = pd.read_parquet(PAIR_V5_PATH)
    extras = np.empty((n, len(PAIR_V5_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(PAIR_V5_COLUMNS):
        extras[:, j] = pv5[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X31b, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v39_dt_model.npz")
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

    print(f"\nTRIPWIRE — new pair_aug_v5_*_g features placement:")
    for new_col in PAIR_V5_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<42} {100*fi[idx]:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
