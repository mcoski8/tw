"""
Session 33 — train_v26_dt: extends train_v25 with 6 two_pair-gated aug
features (zeros for non-two_pair hands). Total feature count:
37 base + 6 suited-gated + 6 trips_pair-gated + 4 composite-gated +
6 pair-gated + 6 two_pair-gated = 65.

The two_pair category is the largest fully-untouched residual on v25:
  22.3% population × $1,458/1000h regret = $325/1000h share.

Three two_pair-specific aug features have been in the model since
Session 19 (default_bot_is_ds_tp, n_routings_yielding_ds_bot_tp,
swap_high_pair_to_bot_ds_compatible). Session 33 audit verified they
are strictly category-gated. The 6 new features split Layout B
(high pair → mid) from Layout C (low pair → mid), which the existing
`n_routings_yielding_ds_bot_tp` lumps together — Session 19 mining
called out exactly this distinction as the dominant miss pattern.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v26_dt.py \\
      --max-depth 30 --min-samples-leaf 5 --output data/v26_dt_model.npz
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
from train_v25_dt import build_X as build_X_v25, FEATURE_COLUMNS as V25_COLUMNS, ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
TWO_PAIR_GATED_PATH = ROOT / "data" / "feature_table_two_pair_aug_gated.parquet"

TWO_PAIR_GATED_COLUMNS = [
    "t2p_layout_a_bot_is_ds_g",
    "t2p_n_layout_b_routings_ds_g",
    "t2p_top_singleton_rank_g",
    "t2p_low_singleton_rank_g",
    "t2p_singletons_max_suit_count_g",
    "t2p_high_pair_rank_g",
]
FEATURE_COLUMNS = list(V25_COLUMNS) + TWO_PAIR_GATED_COLUMNS


def build_X():
    X25, n = build_X_v25()
    print(f"  v25 base X: {X25.shape}  loading two_pair gated ...", flush=True)
    tpg = pd.read_parquet(TWO_PAIR_GATED_PATH)
    extras = np.empty((n, len(TWO_PAIR_GATED_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(TWO_PAIR_GATED_COLUMNS):
        extras[:, j] = tpg[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X25, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=30)
    ap.add_argument("--min-samples-leaf", type=int, default=5)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v26_dt_model.npz")
    args = ap.parse_args()

    X, n = build_X()
    print(f"X={X.shape}  ({len(FEATURE_COLUMNS)} features)", flush=True)

    print("loading Y from grid ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(grid.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB", flush=True)

    print(f"\nfitting DecisionTreeRegressor depth={args.max_depth} min_samples_leaf={args.min_samples_leaf} ...", flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=42,
        criterion="squared_error",
    )
    dt.fit(X, Y)
    fit_t = time.time() - t0
    print(f"  fit {fit_t:.1f}s  leaves={dt.get_n_leaves():,}  depth={dt.get_depth()}", flush=True)

    tree = dt.tree_
    val = tree.value
    if val.ndim == 3:
        val = val[:, :, 0]
    children_left = tree.children_left.astype(np.int32)
    children_right = tree.children_right.astype(np.int32)
    feature = tree.feature.astype(np.int32)
    threshold = tree.threshold.astype(np.float64)
    leaf_values = val.astype(np.float32)

    sk_pred = dt.predict(X)
    picked_idx = sk_pred.argmax(axis=1)
    picked_ev = Y[np.arange(n), picked_idx].mean()
    oracle_ev = Y.max(axis=1).mean()
    shape_agree = float((picked_idx == Y.argmax(axis=1)).mean()) * 100
    print(f"  oracle argmax mean EV: {oracle_ev:+.4f}", flush=True)
    print(f"  v26 picked mean EV:    {picked_ev:+.4f}", flush=True)
    print(f"  retention: {(picked_ev / oracle_ev) * 100:.2f}%", flush=True)
    print(f"  shape-agreement vs oracle argmax: {shape_agree:.2f}%", flush=True)

    np.savez_compressed(
        args.output,
        children_left=children_left,
        children_right=children_right,
        feature=feature,
        threshold=threshold,
        leaf_values=leaf_values,
        feature_columns=np.array(FEATURE_COLUMNS, dtype=object),
        cat_map_keys=np.array(list(ALPHA_MAP.keys()), dtype=object),
        cat_map_values=np.array(list(ALPHA_MAP.values()), dtype=np.int32),
        depth=np.int32(dt.get_depth()),
        n_leaves=np.int32(dt.get_n_leaves()),
        training_grid=np.array(["full"], dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
    )
    sz = args.output.stat().st_size
    print(f"\nsaved {args.output} ({sz/1e6:.2f} MB)", flush=True)

    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-25 feature importances:")
    for r, idx in enumerate(order[:25], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<40} {100*fi[idx]:6.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
