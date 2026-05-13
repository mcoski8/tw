"""
Session 72 — train_v46_dt: v44 (107) + 2 high_only_aug_v6 features = 109 total.

Per CURRENT_PHASE.md S71 and SESSION_71_V45_FEATURE_HYPOTHESES.md:

H1 SS+ms route quality is the SS-axis counterpart to ho_v3's DS-axis pair
(which shipped +$79/1000h in S57). The S71 setting-rank drill isolated
$147.59 WG of STRUCTURE-bucket leak in v44's high_only residual; the
dominant mismatch family across K/Q/J/A × DS_NO_JOINT × STRUCTURE is
`SS_mu → SS_ms` (same top, same SS bot, only differing in whether the
mid pair shares a suit). v44 has zero SS+ms enumeration features — clean
non-derivability story.

ho_v6 adds 2 features (each gated to high_only):

  ho_v6_topMax_SS_ms_n_configs_g       0..15 — count of (top=max-rank,
    SS bot, ms mid) configurations.

  ho_v6_topMax_SS_ms_max_mid_high_g    0..14 — best higher-of-suited-mid
    rank across them; 0 if no config.

**Hyperparameter regime change:** v44 / v45 both used depth=36 ml=1.
v46 defaults to **depth=32 ml=3** (project default per CURRENT_PHASE.md
S70 memo) — a deliberate regime switch testing whether saturation was
the binding constraint at the v45 NULL. If v46 ships at depth=32 ml=3
and a hypothetical v46b at depth=36 ml=1 also ships, the regime change
is harmless. If only v46 ships, saturation was binding.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v46_dt.py \\
      --max-depth 32 --min-samples-leaf 3 --output data/v46_dt_model.npz
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
HO_V6_PATH = ROOT / "data" / "feature_table_high_only_aug_v6_gated.parquet"

HO_V6_COLUMNS = [
    "ho_v6_topMax_SS_ms_n_configs_g",
    "ho_v6_topMax_SS_ms_max_mid_high_g",
]
FEATURE_COLUMNS = list(V44_COLUMNS) + HO_V6_COLUMNS  # 107 + 2 = 109


def build_X():
    X44, n = build_X_v44()
    print(f"  v44 base X: {X44.shape}  loading high_only_aug_v6 gated ...", flush=True)
    pv6 = pd.read_parquet(HO_V6_PATH)
    extras = np.empty((n, len(HO_V6_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(HO_V6_COLUMNS):
        extras[:, j] = pv6[c].to_numpy().astype(np.int16, copy=False)
    X = np.concatenate([X44, extras], axis=1)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=32)
    ap.add_argument("--min-samples-leaf", type=int, default=3)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v46_dt_model.npz")
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

    print(f"\nTRIPWIRE — new ho_v6_*_g features placement:")
    for new_col in HO_V6_COLUMNS:
        idx = FEATURE_COLUMNS.index(new_col)
        rank = int(np.where(order == idx)[0][0]) + 1
        print(f"  #{rank:<3} {new_col:<46} {100*fi[idx]:.2f}%")

    # S59 tripwire: report leaf-growth signature vs v44's 2,248,173
    v44_leaves = 2_248_173
    delta = dt.get_n_leaves() - v44_leaves
    print(f"\nTRIPWIRE — leaf growth vs v44 ({v44_leaves:,}): {delta:+,}")
    if delta >= 10_000:
        print(f"  ≥10K leaf growth → ship signal")
    elif delta < 1_000:
        print(f"  <1K leaf growth → NULL signal (like v45's +9)")
    else:
        print(f"  ambiguous — between 1K and 10K")

    return 0


if __name__ == "__main__":
    sys.exit(main())
