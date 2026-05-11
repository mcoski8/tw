"""
Session 59 — train_v45_dt: v44 (107) + 4 high_only_aug_v5 features = 111 total.

S58 decision matrix found that v44's `ho_v4_topNonMax_DS_ms_max_top_rank_g`
gives the DT a "best non-max top rank" signal but NOT the corresponding
mid_high quality or the count of (non-max joint with max-rank-as-bot-pair).
S58's HO9 stratification found best_DS_bot_pair_high == max_rank correlates
strongly with oracle picking DS_NONJOINT over JOINT — a signature v44 can't
see directly.

ho_v5 adds 4 features (each gated to high_only):

  ho_v5_topNonMax_DS_ms_max_mid_high_g       0..13 — best mid_high in
    non-max joints (the missing quality counterpart to v44's max_top_rank).

  ho_v5_topNonMax_DS_ms_best_combined_q_g    0..26 — max(top_rank +
    mid_high) across non-max joints; the "joint quality" scalar.

  ho_v5_topNonMax_DS_max_in_bot_pair_n_g     0..15 — count of (top!=max,
    DS bot) configs where max-rank is paired in the bot's suited pair.

  ho_v5_topMax_4f_ms_n_configs_g             0..15 — count of (top=max,
    bot 4-flush, mid suited) configs.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v45_dt.py \\
      --max-depth 36 --min-samples-leaf 1 --output data/v45_dt_model.npz
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
HO_V5_PATH = ROOT / "data" / "feature_table_high_only_aug_v5_gated.parquet"

HO_V5_COLUMNS = [
    "ho_v5_topNonMax_DS_ms_max_mid_high_g",
    "ho_v5_topNonMax_DS_ms_best_combined_q_g",
    "ho_v5_topNonMax_DS_max_in_bot_pair_n_g",
    "ho_v5_topMax_4f_ms_n_configs_g",
]
FEATURE_COLUMNS = list(V44_COLUMNS) + HO_V5_COLUMNS  # 107 + 4 = 111


def build_X():
    X44, n = build_X_v44()
    print(f"  v44 base X: {X44.shape}  loading high_only_aug_v5 gated ...", flush=True)
    pv5 = pd.read_parquet(HO_V5_PATH)
    extras = np.empty((n, len(HO_V5_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(HO_V5_COLUMNS):
        extras[:, j] = pv5[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X44, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v45_dt_model.npz")
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

    print(f"\nTRIPWIRE — new ho_v5_*_g features placement:")
    for new_col in HO_V5_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<46} {100*fi[idx]:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
