"""
Session 38 — train_v32_capacity_sweep: retrain v32's 83 features at higher
capacity (depth=34, min_samples_leaf=2 / 3) per the methodology rule that
when feature count grows the capacity sweep should be re-run.

Naming:
  - v32_d34ml2 = same 83 features, depth=34 ml=2  (high-capacity candidate)
  - v32_d34ml3 = same 83 features, depth=34 ml=3  (control)

Per Session 37 wrap, v32 (depth=32 ml=3) has 731,606 leaves and ships
$+1,715/1000h regret on full grid. Adding +5% leaf budget at depth=32 ml=3
already exhausted; the question is whether depth=34 unlocks more leaves
(and if ml=2 does so vs ml=3).

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v32_capacity_sweep.py
"""
from __future__ import annotations

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
from train_v31b_dt import build_X, FEATURE_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
OUT_DIR = ROOT / "data"


def fit_one(X, Y, n, max_depth: int, min_samples_leaf: int, label: str,
            output_path: Path):
    print(f"\n{'='*70}", flush=True)
    print(f"Training {label}: depth={max_depth}, ml={min_samples_leaf}", flush=True)
    print(f"{'='*70}", flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=max_depth, min_samples_leaf=min_samples_leaf,
        random_state=42, criterion="squared_error",
    )
    dt.fit(X, Y)
    fit_t = time.time() - t0
    leaves = dt.get_n_leaves()
    achieved_depth = dt.get_depth()
    print(f"  fit {fit_t:.1f}s  leaves={leaves:,}  depth={achieved_depth}", flush=True)

    sk_pred = dt.predict(X)
    picked_idx = sk_pred.argmax(axis=1)
    picked_ev = Y[np.arange(n), picked_idx].mean()
    oracle_ev = Y.max(axis=1).mean()
    shape_agree = float((picked_idx == Y.argmax(axis=1)).mean()) * 100
    print(f"  oracle argmax mean EV: {oracle_ev:+.4f}", flush=True)
    print(f"  picked mean EV:        {picked_ev:+.4f}", flush=True)
    print(f"  retention:             {(picked_ev / oracle_ev) * 100:.2f}%", flush=True)
    print(f"  shape-agreement:       {shape_agree:.2f}%", flush=True)

    tree = dt.tree_
    val = tree.value
    if val.ndim == 3:
        val = val[:, :, 0]
    np.savez_compressed(
        output_path,
        children_left=tree.children_left.astype(np.int32),
        children_right=tree.children_right.astype(np.int32),
        feature=tree.feature.astype(np.int32),
        threshold=tree.threshold.astype(np.float64),
        leaf_values=val.astype(np.float32),
        feature_columns=np.array(FEATURE_COLUMNS, dtype=object),
        cat_map_keys=np.array(list(ALPHA_MAP.keys()), dtype=object),
        cat_map_values=np.array(list(ALPHA_MAP.values()), dtype=np.int32),
        depth=np.int32(achieved_depth),
        n_leaves=np.int32(leaves),
        training_grid=np.array(["full"], dtype=object),
        max_depth=np.int32(max_depth),
        min_samples_leaf=np.int32(min_samples_leaf),
    )
    sz = output_path.stat().st_size
    print(f"  saved {output_path.name} ({sz/1e6:.1f} MB)", flush=True)
    return {"fit_t": fit_t, "leaves": leaves, "achieved_depth": achieved_depth,
            "picked_ev": float(picked_ev), "shape_agree": shape_agree}


def main() -> int:
    print("Building features ...", flush=True)
    X, n = build_X()
    print(f"  X={X.shape}  ({len(FEATURE_COLUMNS)} features)", flush=True)

    print("\nLoading oracle grid Y ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(grid.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB", flush=True)

    results = {}
    # depth=34 ml=3 control first (faster than ml=2 typically)
    results["d34ml3"] = fit_one(
        X, Y, n, max_depth=34, min_samples_leaf=3,
        label="v32_d34ml3 (control)",
        output_path=OUT_DIR / "v32_d34ml3_dt_model.npz",
    )
    # depth=34 ml=2 candidate
    results["d34ml2"] = fit_one(
        X, Y, n, max_depth=34, min_samples_leaf=2,
        label="v32_d34ml2 (high capacity)",
        output_path=OUT_DIR / "v32_d34ml2_dt_model.npz",
    )

    print("\n" + "=" * 70)
    print("CAPACITY SWEEP SUMMARY")
    print("=" * 70)
    print(f"  {'config':<20}  {'leaves':>10}  {'pickedEV':>9}  {'shape%':>6}  {'fit_s':>6}")
    print(f"  {'v32 (d32 ml=3)':<20}  {731606:>10,}  {'(prev)':>9}  {'(prev)':>6}  {'(prev)':>6}")
    for k, r in results.items():
        print(f"  v32_{k:<16}  {r['leaves']:>10,}  {r['picked_ev']:>+8.4f}  "
              f"{r['shape_agree']:>5.2f}  {r['fit_t']:>5.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
