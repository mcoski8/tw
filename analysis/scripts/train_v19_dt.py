"""
Session 29 — train_v19_dt: extends train_v18_dt with the 6 new
suited-broadway aug features. Total feature count: 37 + 6 = 43.

Saves data/v19_dt_model.npz with the same npz layout as v16/v18.
Inference path is strategy_v19_dt.py.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v19_dt.py \
      --max-depth 22 --min-samples-leaf 50 --output data/v19_dt_model.npz
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

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
PA_PATH = ROOT / "data" / "feature_table_aug.parquet"
HA_PATH = ROOT / "data" / "feature_table_high_only_aug.parquet"
TP_PATH = ROOT / "data" / "feature_table_two_pair_aug.parquet"
SUITED_PATH = ROOT / "data" / "feature_table_suited_aug.parquet"

CATS = ["high_only", "pair", "quads", "three_pair", "trips", "trips_pair", "two_pair"]
ALPHA_MAP = {c: i for i, c in enumerate(CATS)}

# 37 v16/v18 base features + 6 suited-broadway = 43.
FEATURE_COLUMNS = [
    "n_pairs", "pair_high_rank", "pair_low_rank", "pair_third_rank",
    "n_trips", "trips_rank", "n_quads", "quads_rank",
    "top_rank", "second_rank", "third_rank",
    "suit_max", "suit_2nd", "suit_3rd", "suit_4th",
    "n_suits_present", "is_monosuit", "connectivity", "n_broadway", "n_low",
    "category_id",
    "can_make_ds_bot", "can_make_4run", "has_high_pair", "has_low_pair",
    "has_premium_pair", "has_ace_singleton", "has_king_singleton",
    "default_bot_is_ds", "n_top_choices_yielding_ds_bot", "pair_to_bot_alt_is_ds",
    "default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot", "best_ds_bot_mid_max_rank",
    "default_bot_is_ds_tp", "n_routings_yielding_ds_bot_tp", "swap_high_pair_to_bot_ds_compatible",
    # Session 29 additions:
    "n_suited_pairs_total",
    "max_suited_pair_high_rank",
    "max_suited_pair_low_rank",
    "has_suited_broadway_pair",
    "has_suited_premium_pair",
    "n_broadway_in_largest_suit",
]


def categorize(n_pairs, n_trips, n_quads):
    out = np.empty(len(n_pairs), dtype=np.int16)
    for i in range(len(n_pairs)):
        if n_quads[i] >= 1:
            out[i] = ALPHA_MAP["quads"]
        elif n_trips[i] >= 1 and n_pairs[i] >= 1:
            out[i] = ALPHA_MAP["trips_pair"]
        elif n_trips[i] >= 1:
            out[i] = ALPHA_MAP["trips"]
        elif n_pairs[i] == 3:
            out[i] = ALPHA_MAP["three_pair"]
        elif n_pairs[i] == 2:
            out[i] = ALPHA_MAP["two_pair"]
        elif n_pairs[i] == 1:
            out[i] = ALPHA_MAP["pair"]
        else:
            out[i] = ALPHA_MAP["high_only"]
    return out


def build_X():
    print("loading parquets ...", flush=True)
    t0 = time.time()
    ft = pd.read_parquet(FT_PATH)
    pa = pd.read_parquet(PA_PATH)
    ha = pd.read_parquet(HA_PATH)
    tp = pd.read_parquet(TP_PATH)
    su = pd.read_parquet(SUITED_PATH)
    print(f"  loaded {time.time()-t0:.1f}s", flush=True)
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    cat_id = categorize(n_pairs, n_trips, n_quads)
    pair_high_rank = ft["pair_high_rank"].to_numpy()
    pair_low_rank = ft["pair_low_rank"].to_numpy()
    trips_rank = ft["trips_rank"].to_numpy()
    quads_rank = ft["quads_rank"].to_numpy()
    top_rank = ft["top_rank"].to_numpy()
    suit_2nd = ft["suit_2nd"].to_numpy()
    connectivity = ft["connectivity"].to_numpy()

    can_make_ds_bot = (suit_2nd >= 2).astype(np.int16)
    can_make_4run = (connectivity >= 4).astype(np.int16)
    has_high_pair = (pair_high_rank >= 12).astype(np.int16)
    has_low_pair = ((n_pairs >= 1) & (pair_high_rank <= 5)).astype(np.int16)
    has_premium_pair = ((pair_high_rank == 14) | (pair_high_rank == 13)).astype(np.int16)
    has_ace_singleton = (
        (top_rank == 14)
        & (pair_high_rank != 14)
        & (trips_rank != 14)
        & (quads_rank != 14)
    ).astype(np.int16)
    has_king_singleton = (
        (top_rank >= 13)
        & (pair_high_rank < 13)
        & (pair_low_rank < 13)
        & (trips_rank < 13)
        & (quads_rank < 13)
    ).astype(np.int16)

    cd = {
        "n_pairs": n_pairs, "pair_high_rank": pair_high_rank, "pair_low_rank": pair_low_rank,
        "pair_third_rank": ft["pair_third_rank"].to_numpy(),
        "n_trips": n_trips, "trips_rank": trips_rank,
        "n_quads": n_quads, "quads_rank": quads_rank,
        "top_rank": top_rank, "second_rank": ft["second_rank"].to_numpy(),
        "third_rank": ft["third_rank"].to_numpy(),
        "suit_max": ft["suit_max"].to_numpy(), "suit_2nd": suit_2nd,
        "suit_3rd": ft["suit_3rd"].to_numpy(), "suit_4th": ft["suit_4th"].to_numpy(),
        "n_suits_present": ft["n_suits_present"].to_numpy(),
        "is_monosuit": ft["is_monosuit"].to_numpy().astype(np.int16),
        "connectivity": connectivity,
        "n_broadway": ft["n_broadway"].to_numpy(),
        "n_low": ft["n_low"].to_numpy(),
        "category_id": cat_id,
        "can_make_ds_bot": can_make_ds_bot, "can_make_4run": can_make_4run,
        "has_high_pair": has_high_pair, "has_low_pair": has_low_pair,
        "has_premium_pair": has_premium_pair, "has_ace_singleton": has_ace_singleton,
        "has_king_singleton": has_king_singleton,
        "default_bot_is_ds": pa["default_bot_is_ds"].to_numpy(),
        "n_top_choices_yielding_ds_bot": pa["n_top_choices_yielding_ds_bot"].to_numpy(),
        "pair_to_bot_alt_is_ds": pa["pair_to_bot_alt_is_ds"].to_numpy(),
        "default_bot_is_ds_high": ha["default_bot_is_ds_high"].to_numpy(),
        "n_mid_choices_yielding_ds_bot": ha["n_mid_choices_yielding_ds_bot"].to_numpy(),
        "best_ds_bot_mid_max_rank": ha["best_ds_bot_mid_max_rank"].to_numpy(),
        "default_bot_is_ds_tp": tp["default_bot_is_ds_tp"].to_numpy(),
        "n_routings_yielding_ds_bot_tp": tp["n_routings_yielding_ds_bot_tp"].to_numpy(),
        "swap_high_pair_to_bot_ds_compatible": tp["swap_high_pair_to_bot_ds_compatible"].to_numpy(),
        "n_suited_pairs_total": su["n_suited_pairs_total"].to_numpy(),
        "max_suited_pair_high_rank": su["max_suited_pair_high_rank"].to_numpy(),
        "max_suited_pair_low_rank": su["max_suited_pair_low_rank"].to_numpy(),
        "has_suited_broadway_pair": su["has_suited_broadway_pair"].to_numpy(),
        "has_suited_premium_pair": su["has_suited_premium_pair"].to_numpy(),
        "n_broadway_in_largest_suit": su["n_broadway_in_largest_suit"].to_numpy(),
    }
    n = len(ft)
    X = np.empty((n, len(FEATURE_COLUMNS)), dtype=np.int16)
    for j, c in enumerate(FEATURE_COLUMNS):
        X[:, j] = cd[c].astype(np.int16, copy=False)
    return X, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=22)
    ap.add_argument("--min-samples-leaf", type=int, default=50)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "v19_dt_model.npz")
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

    print("computing training-set recovery ...", flush=True)
    sk_pred = dt.predict(X)
    picked_idx = sk_pred.argmax(axis=1)
    picked_ev = Y[np.arange(n), picked_idx].mean()
    oracle_ev = Y.max(axis=1).mean()
    shape_agree = float((picked_idx == Y.argmax(axis=1)).mean()) * 100
    print(f"  oracle argmax mean EV: {oracle_ev:+.4f}", flush=True)
    print(f"  v19 picked  mean EV:   {picked_ev:+.4f}", flush=True)
    print(f"  retention: {(picked_ev / oracle_ev) * 100:.2f}%", flush=True)
    print(f"  shape-agreement vs oracle argmax: {shape_agree:.2f}%", flush=True)

    cat_map = ALPHA_MAP
    np.savez_compressed(
        args.output,
        children_left=children_left,
        children_right=children_right,
        feature=feature,
        threshold=threshold,
        leaf_values=leaf_values,
        feature_columns=np.array(FEATURE_COLUMNS, dtype=object),
        cat_map_keys=np.array(list(cat_map.keys()), dtype=object),
        cat_map_values=np.array(list(cat_map.values()), dtype=np.int32),
        depth=np.int32(dt.get_depth()),
        n_leaves=np.int32(dt.get_n_leaves()),
        training_grid=np.array(["full"], dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
    )
    sz = args.output.stat().st_size
    print(f"\nsaved {args.output} ({sz/1e6:.2f} MB)", flush=True)

    # Feature importance from sklearn directly.
    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-15 feature importances (sklearn impurity-decrease normalized):")
    for r, idx in enumerate(order[:15], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<40} {100*fi[idx]:6.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
