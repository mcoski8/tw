"""
Session 32 — train_v25_dt: extends train_v24 with 6 pair-gated aug
features (zeros for non-pair hands). Total feature count:
37 base + 6 suited-gated + 6 trips_pair-gated + 4 composite-gated +
6 pair-gated = 59.

The pair category is the largest residual on v24:
  46.6% population × $1,873/1000h regret = $873/1000h share.

Three pair-specific aug features have been in the model since Session
17 (default_bot_is_ds, n_top_choices_yielding_ds_bot,
pair_to_bot_alt_is_ds), but they are coarse booleans / 0-3 buckets that
ask only "is the bot DS under this routing?" — they tell the DT
WHETHER, not WHY/HOW.

The 6 new features add rank- and mid-quality signal so the DT can split
on combinations such as:
  - "default_bot_is_ds==1 AND default_top_rank_g>=13"
  - "pair_to_bot_alt_is_ds==1 AND alt_mid_suited_g==1
     AND alt_mid_n_broadway_g==2"
  - "kickers_in_pair_suit_max_g==2 AND _min_g==2" (Rule 1 (2,2) split)

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v25_dt.py \\
      --max-depth 30 --min-samples-leaf 5 --output data/v25_dt_model.npz
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
from train_v24_dt import build_X as build_X_v24, FEATURE_COLUMNS as V24_COLUMNS, ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PAIR_GATED_PATH = ROOT / "data" / "feature_table_pair_aug_gated.parquet"

PAIR_GATED_COLUMNS = [
    "pair_kickers_in_pair_suit_max_g",
    "pair_kickers_in_pair_suit_min_g",
    "pair_default_top_rank_g",
    "pair_alt_top_rank_g",
    "pair_alt_mid_suited_g",
    "pair_alt_mid_n_broadway_g",
]
FEATURE_COLUMNS = list(V24_COLUMNS) + PAIR_GATED_COLUMNS


def build_X():
    X24, n = build_X_v24()
    print(f"  v24 base X: {X24.shape}  loading pair gated ...", flush=True)
    pg = pd.read_parquet(PAIR_GATED_PATH)
    extras = np.empty((n, len(PAIR_GATED_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(PAIR_GATED_COLUMNS):
        extras[:, j] = pg[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X24, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=30)
    ap.add_argument("--min-samples-leaf", type=int, default=5)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v25_dt_model.npz")
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
    print(f"  v25 picked mean EV:    {picked_ev:+.4f}", flush=True)
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
