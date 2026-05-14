"""
Session 80 — train_v49_c2_dt: C2 experiment from S80 M2 plan (Decision 114).

ONE knob differs from train_v44_dt.py: the model is regularized to test
the memorization hypothesis from the C side.

  v44 hyperparams: max_depth=36, min_samples_leaf=1, no leaf cap
                   → fit produced ~2.25M leaves on 4.84M training rows.
  v49_c2 hyperparams: max_depth=36 (same cap), min_samples_leaf=5,
                      max_leaf_nodes=500_000 (4.5x reduction from v44).

Training labels = N=200 full-grid EVs (UNCHANGED from v44). The only
question this experiment answers is: does a less-memorizing v44-class
DT trained on the SAME noisy labels lift N=1000 match rate above v44's
67.05% baseline?

If yes → v44 was overfitting N=200 noise; capacity reduction is the
        right lever (queue C1 high-capacity well-regularized boosting
        for S81).
If no  → memorization is not the dominant problem; the gap lives
        elsewhere.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/train_v49_c2_dt.py \\
      --max-depth 36 --min-samples-leaf 5 --max-leaf-nodes 500000 \\
      --output data/v49_c2_dt_model.npz
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.tree import DecisionTreeRegressor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from train_v44_dt import build_X, FEATURE_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=5)
    ap.add_argument("--max-leaf-nodes", type=int, default=500_000)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data" / "v49_c2_dt_model.npz")
    args = ap.parse_args()

    print("=" * 100, flush=True)
    print("Session 80 — train_v49_c2_dt (C2 experiment, M2 plan)", flush=True)
    print("=" * 100, flush=True)
    print(f"  ONE knob vs v44: regularize.", flush=True)
    print(f"    max_leaf_nodes={args.max_leaf_nodes:,} (vs v44's effective ~2.25M)",
          flush=True)
    print(f"    min_samples_leaf={args.min_samples_leaf}      (vs v44's 1)",
          flush=True)
    print(f"  Hyperparam unchanged: max_depth={args.max_depth}.", flush=True)
    print(f"  Training labels = N=200 full-grid EVs (UNCHANGED from v44).\n",
          flush=True)

    print("[1/3] building X (shared with v44 pipeline) ...", flush=True)
    t0 = time.time()
    X, n = build_X()
    print(f"  X={X.shape}  ({len(FEATURE_COLUMNS)} features)  built in {time.time()-t0:.1f}s",
          flush=True)

    print("\n[2/3] loading Y from N=200 full grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(gf.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB", flush=True)

    print(f"\n[3/3] fitting DT depth={args.max_depth} ml={args.min_samples_leaf} "
          f"max_leaf_nodes={args.max_leaf_nodes:,} ...", flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        max_leaf_nodes=args.max_leaf_nodes,
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
        training_grid=np.array(["v49_c2_n200_regularized"], dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
        max_leaf_nodes=np.int32(args.max_leaf_nodes),
    )
    print(f"\nsaved {args.output} ({args.output.stat().st_size/1e6:.2f} MB)",
          flush=True)

    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-15 feature importances:", flush=True)
    for r, idx in enumerate(order[:15], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<42} {100*fi[idx]:6.2f}%",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
