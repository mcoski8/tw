"""
Session 36 — train_v31b_dt: extends train_v30 with 4 trips_v2 round-2
features. Total feature count: 79 (v30) + 4 = 83.

The 4 features encode the C_top_trip routing signal, B-DS kicker pair
quality (max + 2nd rank), and the count of kickers in trip-suits.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v31b_dt.py \\
      --max-depth 30 --min-samples-leaf 5 --output data/v31b_dt_model.npz
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
from train_v30_dt import build_X as build_X_v30, FEATURE_COLUMNS as V30_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
TRIPS_V2_GATED_PATH = ROOT / "data" / "feature_table_trips_aug_v2_gated.parquet"

TRIPS_V2_GATED_COLUMNS = [
    "trips_v2_c_top_advantage_g",
    "trips_v2_b_ds_kicker_max_rank_g",
    "trips_v2_b_ds_kicker_2nd_rank_g",
    "trips_v2_n_kickers_in_trip_suits_g",
]
FEATURE_COLUMNS = list(V30_COLUMNS) + TRIPS_V2_GATED_COLUMNS


def build_X():
    X30, n = build_X_v30()
    print(f"  v30 base X: {X30.shape}  loading trips_v2 gated ...", flush=True)
    tv = pd.read_parquet(TRIPS_V2_GATED_PATH)
    extras = np.empty((n, len(TRIPS_V2_GATED_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(TRIPS_V2_GATED_COLUMNS):
        extras[:, j] = tv[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X30, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=30)
    ap.add_argument("--min-samples-leaf", type=int, default=5)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v31b_dt_model.npz")
    args = ap.parse_args()

    X, n = build_X()
    print(f"X={X.shape}  ({len(FEATURE_COLUMNS)} features)", flush=True)

    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(grid.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB", flush=True)

    print(f"\nfitting DT depth={args.max_depth} ml={args.min_samples_leaf} ...", flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=args.max_depth, min_samples_leaf=args.min_samples_leaf,
        random_state=42, criterion="squared_error",
    )
    dt.fit(X, Y)
    print(f"  fit {time.time()-t0:.1f}s  leaves={dt.get_n_leaves():,}  depth={dt.get_depth()}", flush=True)

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
    print(f"\nsaved {args.output} ({args.output.stat().st_size/1e6:.2f} MB)", flush=True)

    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-30 feature importances:")
    for r, idx in enumerate(order[:30], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<40} {100*fi[idx]:6.2f}%")

    print(f"\nTRIPWIRE — new trips_v2_*_g features in top-30:")
    placed = []; not_placed = []
    for new_col in TRIPS_V2_GATED_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        (placed if rank <= 30 else not_placed).append((rank, new_col, fi[idx]))
    print(f"  PLACED in top-30 ({len(placed)} of {len(TRIPS_V2_GATED_COLUMNS)}):")
    for r, c, imp in sorted(placed):
        print(f"    #{r:<3} {c:<40} {100*imp:.2f}%")
    print(f"  NOT in top-30 ({len(not_placed)} of {len(TRIPS_V2_GATED_COLUMNS)}):")
    for r, c, imp in sorted(not_placed):
        print(f"    #{r:<3} {c:<40} {100*imp:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
