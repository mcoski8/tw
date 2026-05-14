"""
Session 80 — train_v49_a1_dt: A1 experiment from S80 M2 plan (Decision 114).

ONE knob differs from train_v44_dt.py: training labels for the first 500K
canonical hands come from the N=1000 prefix oracle grid instead of the
N=200 full grid. Remaining ~4.34M training rows continue to use N=200
labels (unchanged from v44).

Hyperparameters identical to v44_dt:
  - DecisionTreeRegressor, multi-output (105-dim EV vector per leaf)
  - max_depth=36, min_samples_leaf=1, criterion=squared_error
  - random_state=42

Feature pipeline identical to v44_dt: build_X imported from train_v44_dt
(107 features = v43 base 103 + 4 high_only_aug_v4 gated).

The S79 label-noise diagnostic measured oracle self-disagreement of 32%
(N=200 argmax vs N=1000 argmax on the shared 500K prefix). A1 is the
direct test of the label-noise lever: if v44's architecture trained on
cleaner labels (where they exist) lifts N=1000 match rate above v44's
67.05%, label noise dominates the gap.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/train_v49_a1_dt.py \\
      --max-depth 36 --min-samples-leaf 1 \\
      --output data/v49_a1_dt_model.npz
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
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data" / "v49_a1_dt_model.npz")
    args = ap.parse_args()

    print("=" * 100, flush=True)
    print("Session 80 — train_v49_a1_dt (A1 experiment, M2 plan)", flush=True)
    print("=" * 100, flush=True)
    print(f"  ONE knob vs v44: first 500K rows use N=1000 prefix labels.", flush=True)
    print(f"  Remaining rows use N=200 full-grid labels (unchanged).", flush=True)
    print(f"  Hyperparams: depth={args.max_depth}, ml={args.min_samples_leaf}.\n",
          flush=True)

    print("[1/4] building X (shared with v44 pipeline) ...", flush=True)
    t0 = time.time()
    X, n = build_X()
    print(f"  X={X.shape}  ({len(FEATURE_COLUMNS)} features)  built in {time.time()-t0:.1f}s",
          flush=True)

    print("\n[2/4] loading Y from N=200 full grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(gf.evs[:n], dtype=np.float32).copy()
    print(f"  Y_full={Y.shape}  {Y.nbytes/1e6:.1f} MB  (N=200 labels everywhere)",
          flush=True)

    print("\n[3/4] swapping first 500K rows to N=1000 prefix labels ...",
          flush=True)
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    n_prefix = len(gp)
    print(f"  prefix grid: n_records={n_prefix:,}, samples={gp.header.samples}, "
          f"opp={gp.header.opp_label}", flush=True)
    if n_prefix > n:
        print(f"ERROR: prefix grid has {n_prefix} records but X only has {n} rows.",
              flush=True)
        return 1
    # Verify alignment: prefix and full canonical_ids must match in first n_prefix rows.
    ids_prefix = np.asarray(gp.canonical_ids[:1000], dtype=np.uint32)
    ids_full = np.asarray(gf.canonical_ids[:1000], dtype=np.uint32)
    if not np.array_equal(ids_prefix, ids_full):
        print("ERROR: prefix and full canonical_ids disagree in first 1000 rows.",
              flush=True)
        return 1
    print("  ✓ canonical_ids align (first 1000 spot-checked).", flush=True)
    Y[:n_prefix] = np.asarray(gp.evs[:n_prefix], dtype=np.float32)
    print(f"  swapped first {n_prefix:,} rows.  remaining "
          f"{n - n_prefix:,} rows keep N=200 labels.", flush=True)

    # Sanity: how often does the swap actually move the argmax?
    n200_argmax = np.asarray(gf.evs[:n_prefix]).argmax(axis=1)
    n1000_argmax = np.asarray(gp.evs[:n_prefix]).argmax(axis=1)
    n_changed = int((n200_argmax != n1000_argmax).sum())
    print(f"  oracle self-disagreement on swapped rows: {n_changed:,}/{n_prefix:,} "
          f"= {100.0*n_changed/n_prefix:.2f}% (matches S79: 32%)", flush=True)

    print(f"\n[4/4] fitting DT depth={args.max_depth} ml={args.min_samples_leaf} ...",
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
        training_grid=np.array(["v49_a1_hybrid_500K_n1000_plus_n200"], dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
        n_prefix_swapped=np.int32(n_prefix),
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
