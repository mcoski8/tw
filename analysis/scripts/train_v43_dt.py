"""
Session 57 — train_v43_dt: v42 (99) + 4 high_only_aug_v3 features = 103 total.

S57 Phase 1 (drill HO3) showed v42_dt's high_only zone STILL has SS->DS
as the dominant residual: v42 picks SS bot 46.07% vs oracle 32.04%
(-14.0% absolute under-routing of DS). Top-mismatch class:
v42=tA_SS_mu, oracle=tA_DS_ms (28,027 hands @ $7,534 mean regret =
$35.14/1000h whole-grid).

S57 Phase 1b (drill HO4) confirmed:
  - 100% of mismatch hands have a (DS bot + suited mid) joint config
    achievable WITH the Ace on top.
  - 18% have 3 joint configs, 82% have 9 joint configs.
  - DS_AND_ms_max_mid_high distribution spans 7..K.
  - v42's ho_v2 features expose DS-bot achievability but NOT the joint.

The 4 new ho_v3 features describe (top=max-rank, DS bot, ms mid) JOINT
achievability + quality, mirroring the v2/v5 rank-valued conditional
shape but conditioning on the joint (DS bot + ms mid) structure.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v43_dt.py \\
      --max-depth 36 --min-samples-leaf 1 --output data/v43_dt_model.npz
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
from train_v42_dt import build_X as build_X_v42, FEATURE_COLUMNS as V42_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
HO_V3_PATH = ROOT / "data" / "feature_table_high_only_aug_v3_gated.parquet"

HO_V3_COLUMNS = [
    "ho_v3_topMax_DS_ms_n_configs_g",
    "ho_v3_topMax_DS_ms_max_mid_high_g",
    "ho_v3_topMax_DS_ms_min_mid_high_g",
    "ho_v3_topMax_DS_ms_max_mid_sum_g",
]
FEATURE_COLUMNS = list(V42_COLUMNS) + HO_V3_COLUMNS  # 99 + 4 = 103


def build_X():
    X42, n = build_X_v42()
    print(f"  v42 base X: {X42.shape}  loading high_only_aug_v3 gated ...", flush=True)
    pv3 = pd.read_parquet(HO_V3_PATH)
    extras = np.empty((n, len(HO_V3_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(HO_V3_COLUMNS):
        extras[:, j] = pv3[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X42, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v43_dt_model.npz")
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

    print(f"\nTRIPWIRE — new ho_v3_*_g features placement:")
    for new_col in HO_V3_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<42} {100*fi[idx]:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
