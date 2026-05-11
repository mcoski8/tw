"""
Session 58 — train_v44_dt: v43 (103) + 4 high_only_aug_v4 features = 107 total.

Drills HO5–HO10 surfaced THREE structural axes invisible to v43:

  AXIS A — DS bot pair_high quality with top=max (DS_NO_JOINT cell,
           62.9% of high_only). v43 has DS-achievability count but no
           DS bot strength signal — over-routes SS_mu by 11% at A/K.
  AXIS B — 4-flush bot + suited mid with top=max. 54% of A-alts.
  AXIS C — non-max-top joint achievability. 47.7% of high_only hands;
           dominant at lower max-ranks where DS_NONJOINT take-rate is
           48-65% (Q/J/T/9/8).

The 4 new ho_v4 features encode each axis as a rank-valued conditional
signal, mirroring the v2/v3/v5 surgical-gating shape.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v44_dt.py \\
      --max-depth 36 --min-samples-leaf 1 --output data/v44_dt_model.npz
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
from train_v43_dt import build_X as build_X_v43, FEATURE_COLUMNS as V43_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
HO_V4_PATH = ROOT / "data" / "feature_table_high_only_aug_v4_gated.parquet"

HO_V4_COLUMNS = [
    "ho_v4_topMax_DS_max_bot_pair_high_g",
    "ho_v4_topMax_4f_ms_max_mid_high_g",
    "ho_v4_topNonMax_DS_ms_n_configs_g",
    "ho_v4_topNonMax_DS_ms_max_top_rank_g",
]
FEATURE_COLUMNS = list(V43_COLUMNS) + HO_V4_COLUMNS  # 103 + 4 = 107


def build_X():
    X43, n = build_X_v43()
    print(f"  v43 base X: {X43.shape}  loading high_only_aug_v4 gated ...", flush=True)
    pv4 = pd.read_parquet(HO_V4_PATH)
    extras = np.empty((n, len(HO_V4_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(HO_V4_COLUMNS):
        extras[:, j] = pv4[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X43, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v44_dt_model.npz")
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

    print(f"\nTRIPWIRE — new ho_v4_*_g features placement:")
    for new_col in HO_V4_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<42} {100*fi[idx]:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
