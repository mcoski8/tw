"""
Session 75 — train_v47_xgb: v44's 107 features (NO ho_v7) trained with
XGBoost gradient boosting.

Per S74 CURRENT_PHASE.md & resume prompt: isolate "boosting vs DT" as
the ONLY variable. Feature set is v44's 107 (NOT v46b's 109, NOT v47_dt's
108). ho_v6 / ho_v7 deferred to v48_xgb iff v47_xgb ships.

Hyperparams (initial defaults, tunable via CLI):
  n_estimators=500, max_depth=10, learning_rate=0.05,
  tree_method='hist', multi_strategy='multi_output_tree',
  early_stopping_rounds=30, validation_split=0.20.

XGBoost ≥2.0 required for multi_strategy='multi_output_tree' (single
tree predicts all 105 outputs per node, sharing structure). Falls back
to one_output_per_tree if multi_output_tree fails — slower but works.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v47_xgb.py \\
      --n-estimators 500 --max-depth 10 --learning-rate 0.05 \\
      --output data/v47_xgb_model.ubj
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import xgboost as xgb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from train_v44_dt import build_X as build_X_v44, FEATURE_COLUMNS as V44_COLUMNS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
FEATURE_COLUMNS = list(V44_COLUMNS)  # 107 features, v44 exact set


def build_X():
    X44, n = build_X_v44()
    return X44, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-estimators", type=int, default=500)
    ap.add_argument("--max-depth", type=int, default=10)
    ap.add_argument("--learning-rate", type=float, default=0.05)
    ap.add_argument("--early-stopping", type=int, default=30,
                    help="Early stopping rounds on validation set")
    ap.add_argument("--val-frac", type=float, default=0.20,
                    help="Fraction of rows held out for validation")
    ap.add_argument("--tree-method", default="hist")
    ap.add_argument("--multi-strategy", default="multi_output_tree",
                    choices=["multi_output_tree", "one_output_per_tree"])
    ap.add_argument("--subsample", type=float, default=0.8)
    ap.add_argument("--colsample-bytree", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data" / "v47_xgb_model.ubj")
    ap.add_argument("--meta-output", type=Path,
                    default=ROOT / "data" / "v47_xgb_meta.json")
    args = ap.parse_args()

    print(f"XGBoost version: {xgb.__version__}", flush=True)

    print("Building X (v44's 107 features) ...", flush=True)
    X, n = build_X()
    print(f"X={X.shape}  ({len(FEATURE_COLUMNS)} features, "
          f"{X.nbytes/1e6:.1f} MB int16)", flush=True)

    print("Loading Y from grid ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    Y = np.asarray(grid.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB", flush=True)

    # Cast X to float32 for XGBoost (it accepts int16 but float32 is the
    # canonical hist-method input)
    X = X.astype(np.float32, copy=False)

    # Train/val split by row index (deterministic with seed)
    rng = np.random.default_rng(args.seed)
    n_val = int(round(n * args.val_frac))
    perm = rng.permutation(n)
    val_idx = perm[:n_val]
    tr_idx = perm[n_val:]
    val_idx.sort()
    tr_idx.sort()
    X_tr, Y_tr = X[tr_idx], Y[tr_idx]
    X_val, Y_val = X[val_idx], Y[val_idx]
    print(f"  train={X_tr.shape[0]:,}  val={X_val.shape[0]:,} "
          f"(val_frac={args.val_frac})", flush=True)

    print(f"\nTraining XGBRegressor:", flush=True)
    print(f"  n_estimators        = {args.n_estimators}", flush=True)
    print(f"  max_depth           = {args.max_depth}", flush=True)
    print(f"  learning_rate       = {args.learning_rate}", flush=True)
    print(f"  tree_method         = {args.tree_method}", flush=True)
    print(f"  multi_strategy      = {args.multi_strategy}", flush=True)
    print(f"  subsample           = {args.subsample}", flush=True)
    print(f"  colsample_bytree    = {args.colsample_bytree}", flush=True)
    print(f"  early_stopping      = {args.early_stopping}", flush=True)

    model = xgb.XGBRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        tree_method=args.tree_method,
        multi_strategy=args.multi_strategy,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        objective="reg:squarederror",
        random_state=args.seed,
        n_jobs=-1,
        early_stopping_rounds=args.early_stopping,
        verbosity=1,
    )

    t0 = time.time()
    try:
        model.fit(X_tr, Y_tr, eval_set=[(X_val, Y_val)], verbose=1)
    except xgb.core.XGBoostError as e:
        if "multi_output_tree" in str(e) or args.multi_strategy == "multi_output_tree":
            print(f"\n[fallback] multi_output_tree failed: {e}", flush=True)
            print(f"[fallback] retrying with one_output_per_tree ...", flush=True)
            model = xgb.XGBRegressor(
                n_estimators=args.n_estimators,
                max_depth=args.max_depth,
                learning_rate=args.learning_rate,
                tree_method=args.tree_method,
                multi_strategy="one_output_per_tree",
                subsample=args.subsample,
                colsample_bytree=args.colsample_bytree,
                objective="reg:squarederror",
                random_state=args.seed,
                n_jobs=-1,
                early_stopping_rounds=args.early_stopping,
                verbosity=1,
            )
            model.fit(X_tr, Y_tr, eval_set=[(X_val, Y_val)], verbose=1)
        else:
            raise
    fit_time = time.time() - t0
    print(f"\nfit {fit_time:.1f}s  best_iter={model.best_iteration}  "
          f"best_score={model.best_score:.6f}", flush=True)

    # Save booster in native UBJSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    booster = model.get_booster()
    booster.save_model(str(args.output))
    print(f"saved booster {args.output} "
          f"({args.output.stat().st_size/1e6:.2f} MB)", flush=True)

    # Feature importances (gain)
    fi = model.feature_importances_  # normalized
    order = np.argsort(-fi)
    top30 = []
    print(f"\nTop-30 feature importances (gain):")
    for r, idx in enumerate(order[:30], 1):
        line = f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<46} {100*fi[idx]:6.2f}%"
        print(line)
        top30.append({"rank": int(r), "feature": FEATURE_COLUMNS[idx],
                       "importance_pct": float(100*fi[idx])})

    # Validation curve
    eval_history = model.evals_result()
    val_curve = eval_history.get("validation_0", {}).get("rmse", [])

    meta = {
        "n_estimators": int(args.n_estimators),
        "max_depth": int(args.max_depth),
        "learning_rate": float(args.learning_rate),
        "tree_method": args.tree_method,
        "multi_strategy": model.get_xgb_params().get("multi_strategy"),
        "subsample": float(args.subsample),
        "colsample_bytree": float(args.colsample_bytree),
        "early_stopping_rounds": int(args.early_stopping),
        "val_frac": float(args.val_frac),
        "seed": int(args.seed),
        "best_iteration": int(model.best_iteration),
        "best_score_rmse": float(model.best_score),
        "fit_time_sec": float(fit_time),
        "n_rows_total": int(n),
        "n_rows_train": int(X_tr.shape[0]),
        "n_rows_val": int(X_val.shape[0]),
        "n_features": len(FEATURE_COLUMNS),
        "feature_columns": FEATURE_COLUMNS,
        "top30_importance": top30,
        "validation_rmse_per_iter": [float(v) for v in val_curve],
        "xgboost_version": xgb.__version__,
    }
    with open(args.meta_output, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nsaved meta {args.meta_output}", flush=True)

    # Validation-curve tripwire: did training plateau, or could it still
    # benefit from more iterations?
    if len(val_curve) >= 50:
        last_50 = val_curve[-50:]
        delta = val_curve[-50] - val_curve[-1]
        print(f"\nVAL CURVE TRIPWIRE:")
        print(f"  last 50 iter val RMSE delta: {delta:+.6f}")
        print(f"  best_iteration: {model.best_iteration} / {args.n_estimators}")
        if model.best_iteration >= args.n_estimators - args.early_stopping - 5:
            print(f"  → Model still improving at iter limit; could benefit "
                  f"from --n-estimators > {args.n_estimators}")
        else:
            print(f"  → Early stopping fired; model converged")

    # Feature-importance tripwire (top-50 SHIP, #50-100 AMBIGUOUS, #100+ NULL)
    # — does not apply for v47_xgb since we have no novel feature to track.
    # It applies in v48_xgb when ho_v6/ho_v7 are added.

    return 0


if __name__ == "__main__":
    sys.exit(main())
