"""
Session 37 — train_v32_dt: v31b's feature set (79 v30 + 4 trips_v2 round-2 = 83)
trained at v31's high-capacity config (depth=32, min_samples_leaf=3).

This combines the two pieces of Session 36's overnight cascade that each
shipped independently:
  - v31b (round-2 trips, +$15/1000h full at depth=30 ml=5)
  - v31  (capacity expansion, +$58/1000h full vs v30 with no new features)

Hypothesis: at the bigger leaf budget the trips_v2 features should still
add their ~$15 of trips routing on top of the $58 v31 already captured,
giving v32 vs v30 ≈ $73/1000h — would tie v26 as the largest single ship
in project history.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v32_dt.py \\
      --max-depth 32 --min-samples-leaf 3 --output data/v32_dt_model.npz
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
from train_v31b_dt import build_X, FEATURE_COLUMNS, TRIPS_V2_GATED_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=32)
    ap.add_argument("--min-samples-leaf", type=int, default=3)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v32_dt_model.npz")
    args = ap.parse_args()

    X, n = build_X()
    print(f"X={X.shape}  ({len(FEATURE_COLUMNS)} features)", flush=True)

    print("loading Y from grid ...", flush=True)
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
    print(f"  v32 picked mean EV:    {picked_ev:+.4f}", flush=True)
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

    print(f"\nTRIPWIRE — new trips_v2_*_g features in top-30 (vs v31's 79 features):")
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
    print(f"\n  Note: tripwire predicts CONVERSION rate; v31b at depth=30 placed 0/4")
    print(f"  in top-30 yet still shipped +$15. Expect a bearish tripwire here too;")
    print(f"  the round-2 trips signal is real even if it's diluted in importance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
