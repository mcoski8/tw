"""
Session 78 — train_v48_dt: v44 (107) + H6/H7/H8 pair features = 110 total.

The 3 new pair-gated features address pair STRUCTURE-bucket leak (S77 drill):
  H6: pair_pmid_ds_n_configs_g       (single-pair, int8 0..5)
  H7: pair_kicker_max_in_pair_suit_g (single-pair, bool 0/1)
  H8: pair_low_pmid_safety_g         (LOW pair only, int8 0..5)

S73 regime LOCKED: depth=36, min_samples_leaf=1, criterion=squared_error.

Smoke mode: --max-rows 100000 trains on a small prefix to verify feature
importance places H6/H7/H8 in top-30 before the full retrain.

Run:
  # smoke
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v48_dt.py \\
      --max-rows 100000 --output data/v48_dt_smoke.npz

  # full
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v48_dt.py \\
      --output data/v48_dt_model.npz
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
H6_PATH = ROOT / "data" / "feature_table_pair_pmid_ds_gated.parquet"
H7_PATH = ROOT / "data" / "feature_table_pair_kicker_align_gated.parquet"
H8_PATH = ROOT / "data" / "feature_table_pair_low_pmid_safety_gated.parquet"

NEW_COLUMNS = [
    "pair_pmid_ds_n_configs_g",          # H6
    "pair_kicker_max_in_pair_suit_g",    # H7
    "pair_low_pmid_safety_g",            # H8
]
FEATURE_COLUMNS = list(V44_COLUMNS) + NEW_COLUMNS  # 107 + 3 = 110


def build_X():
    X44, n = build_X_v44()
    print(f"  v44 base X: {X44.shape}  loading H6/H7/H8 gated ...", flush=True)
    h6 = pd.read_parquet(H6_PATH)["pair_pmid_ds_n_configs_g"].to_numpy()
    h7 = pd.read_parquet(H7_PATH)["pair_kicker_max_in_pair_suit_g"].to_numpy()
    h8 = pd.read_parquet(H8_PATH)["pair_low_pmid_safety_g"].to_numpy()
    extras = np.empty((n, 3), dtype=np.int16)
    extras[:, 0] = h6[:n].astype(np.int16, copy=False)
    extras[:, 1] = h7[:n].astype(np.int16, copy=False)
    extras[:, 2] = h8[:n].astype(np.int16, copy=False)
    X = np.concatenate([X44, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v48_dt_model.npz")
    ap.add_argument("--max-rows", type=int, default=0,
                     help="Limit training to first N rows (for smoke runs).")
    args = ap.parse_args()

    X, n = build_X()
    if args.max_rows and args.max_rows < n:
        X = X[: args.max_rows]
        n = args.max_rows
        print(f"  SMOKE: truncated to first {n:,} rows", flush=True)
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
        n_train_rows=np.int32(n),
    )
    print(f"\nsaved {args.output} ({args.output.stat().st_size/1e6:.2f} MB)",
          flush=True)

    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-30 feature importances:")
    for r, idx in enumerate(order[:30], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<42} {100*fi[idx]:6.2f}%")

    print(f"\nTRIPWIRE — new H6/H7/H8 features placement:")
    for new_col in NEW_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<42} {100*fi[idx]:.4f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
