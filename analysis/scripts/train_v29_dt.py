"""
Session 35 — train_v29_dt: extends train_v27 with 4 pair-gated v2 aug
features (zeros for non-single-pair hands). Total feature count:
69 (v27) + 4 (pair_r4_*_g) = 73.

Diagnostic-driven design (`distill_v27_pair.py`, Session 35):
v27 is $20/1000h whole-grid WORSE than Rule 4 alone on the KK/AA
subset. The missing signal is the suit profile of Rule 4's resulting
bot — when rainbow, DS-bot is the right swap (43.6% strict-wins);
when already single-suited or DS, Rule 4 is correct most of the time.

The 4 new features are the 7th gating template instance (after
suited/v20, trips_pair/v23, composite/v24, pair/v25, two_pair/v26,
high_only-direct/v27, pair-v2/v29). Note: v28 is reserved for the
Rule 5 strategy (human-memorizable rainbow override, Session 34
Decision 063); v29 is the next ML champion candidate.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v29_dt.py \\
      --max-depth 30 --min-samples-leaf 5 --output data/v29_dt_model.npz
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
from train_v27_dt import build_X as build_X_v27, FEATURE_COLUMNS as V27_COLUMNS, ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PAIR_R4_GATED_PATH = ROOT / "data" / "feature_table_pair_aug_v2_gated.parquet"

PAIR_R4_GATED_COLUMNS = [
    "pair_r4_bot_suit_profile_g",
    "pair_r4_bot_max_rank_g",
    "pair_r4_n_broadway_kickers_g",
    "pair_r4_n_low_kickers_g",
]
FEATURE_COLUMNS = list(V27_COLUMNS) + PAIR_R4_GATED_COLUMNS


def build_X():
    X27, n = build_X_v27()
    print(f"  v27 base X: {X27.shape}  loading pair_r4 gated ...", flush=True)
    pr4 = pd.read_parquet(PAIR_R4_GATED_PATH)
    extras = np.empty((n, len(PAIR_R4_GATED_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(PAIR_R4_GATED_COLUMNS):
        extras[:, j] = pr4[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X27, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=30)
    ap.add_argument("--min-samples-leaf", type=int, default=5)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v29_dt_model.npz")
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
    print(f"  v29 picked mean EV:    {picked_ev:+.4f}", flush=True)
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
    print(f"\nTop-30 feature importances:")
    for r, idx in enumerate(order[:30], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<40} {100*fi[idx]:6.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
