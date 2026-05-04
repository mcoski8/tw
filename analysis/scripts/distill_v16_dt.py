"""
Session 28 — distill_v16_dt: rank the highest-impact splits in v16's
28,790-leaf DecisionTreeRegressor and translate them to plain-English
candidate rules for STRATEGY_GUIDE.md.

Approach:
  1. Build the 37-feature matrix X for all 6M canonical hands by joining
     the cached parquet feature tables + computing 7 derived flags +
     remapping category_id to v5/v16's alphabetical map.
  2. Load Y from data/oracle_grid_full_realistic_n200.bin (memmap).
  3. Walk every hand through the saved tree to record its leaf id.
  4. Aggregate per-leaf (count, sum_Y, sum_Y_sq) via np.bincount per
     output column.
  5. Propagate (count, sum, sumsq) from leaves up to the root using a
     parent pointer array.
  6. For each internal node, compute MSE-reduction (the impurity
     decrease attributable to that split, summed over all 105 outputs).
       impurity(node) = mean over k of [E[Y_k^2] - E[Y_k]^2]
       reduction = n*impurity(node) - n_L*impurity(L) - n_R*impurity(R)
  7. Print the top-N splits ordered by reduction, with feature name,
     threshold, sample counts, and the leaf-vs-leaf argmax-EV delta on
     each side.

Input data sources (no retrain needed):
  - data/v16_dt_model.npz        (saved tree)
  - data/feature_table.parquet   (28 baseline features, 6M rows)
  - data/feature_table_aug.parquet
  - data/feature_table_high_only_aug.parquet
  - data/feature_table_two_pair_aug.parquet
  - data/oracle_grid_full_realistic_n200.bin  (Y vectors)

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/distill_v16_dt.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

MODEL_PATH = ROOT / "data" / "v16_dt_model.npz"
GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
PA_PATH = ROOT / "data" / "feature_table_aug.parquet"
HA_PATH = ROOT / "data" / "feature_table_high_only_aug.parquet"
TP_PATH = ROOT / "data" / "feature_table_two_pair_aug.parquet"

CATS = ["high_only", "pair", "quads", "three_pair", "trips", "trips_pair", "two_pair"]
ALPHA_MAP = {c: i for i, c in enumerate(CATS)}


def categorize_row(n_pairs: int, n_trips: int, n_quads: int) -> str:
    if n_quads >= 1:
        return "quads"
    if n_trips >= 1 and n_pairs >= 1:
        return "trips_pair"
    if n_trips >= 1:
        return "trips"
    if n_pairs == 3:
        return "three_pair"
    if n_pairs == 2:
        return "two_pair"
    if n_pairs == 1:
        return "pair"
    return "high_only"


def build_feature_matrix(model_columns: list[str]) -> np.ndarray:
    print(f"loading parquet feature tables ...", flush=True)
    t0 = time.time()
    ft = pd.read_parquet(FT_PATH)
    pa = pd.read_parquet(PA_PATH)
    ha = pd.read_parquet(HA_PATH)
    tp = pd.read_parquet(TP_PATH)
    print(f"  ft={ft.shape}  pa={pa.shape}  ha={ha.shape}  tp={tp.shape}  ({time.time()-t0:.1f}s)", flush=True)

    # All four are sorted by canonical_id and have the same row count, so we
    # can join by row position. Verify.
    assert (ft["canonical_id"].values == np.arange(len(ft))).all()
    assert (pa["canonical_id"].values == np.arange(len(pa))).all()
    assert (ha["canonical_id"].values == np.arange(len(ha))).all()
    assert (tp["canonical_id"].values == np.arange(len(tp))).all()

    n = len(ft)
    print(f"\nbuilding 37-col X matrix for {n:,} hands ...", flush=True)
    t0 = time.time()

    # Category id under the alphabetical map (the one v5_dt was trained with).
    cat_id = np.empty(n, dtype=np.int16)
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    for i in range(n):
        cat_id[i] = ALPHA_MAP[categorize_row(int(n_pairs[i]), int(n_trips[i]), int(n_quads[i]))]
    print(f"  category_id remap: {time.time()-t0:.1f}s", flush=True)

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

    column_data = {
        "n_pairs": n_pairs,
        "pair_high_rank": pair_high_rank,
        "pair_low_rank": pair_low_rank,
        "pair_third_rank": ft["pair_third_rank"].to_numpy(),
        "n_trips": n_trips,
        "trips_rank": trips_rank,
        "n_quads": n_quads,
        "quads_rank": quads_rank,
        "top_rank": top_rank,
        "second_rank": ft["second_rank"].to_numpy(),
        "third_rank": ft["third_rank"].to_numpy(),
        "suit_max": ft["suit_max"].to_numpy(),
        "suit_2nd": suit_2nd,
        "suit_3rd": ft["suit_3rd"].to_numpy(),
        "suit_4th": ft["suit_4th"].to_numpy(),
        "n_suits_present": ft["n_suits_present"].to_numpy(),
        "is_monosuit": ft["is_monosuit"].to_numpy().astype(np.int16),
        "connectivity": connectivity,
        "n_broadway": ft["n_broadway"].to_numpy(),
        "n_low": ft["n_low"].to_numpy(),
        "category_id": cat_id,
        "can_make_ds_bot": can_make_ds_bot,
        "can_make_4run": can_make_4run,
        "has_high_pair": has_high_pair,
        "has_low_pair": has_low_pair,
        "has_premium_pair": has_premium_pair,
        "has_ace_singleton": has_ace_singleton,
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
    }

    X = np.empty((n, len(model_columns)), dtype=np.int16)
    for j, c in enumerate(model_columns):
        X[:, j] = column_data[c].astype(np.int16, copy=False)
    print(f"  X built: {X.shape} {X.nbytes/1e6:.1f} MB  ({time.time()-t0:.1f}s)", flush=True)
    return X


def walk_each_hand_to_leaf(X: np.ndarray, model: dict) -> np.ndarray:
    """Vectorised tree walk; returns leaf node id per row."""
    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]
    n = X.shape[0]
    node = np.zeros(n, dtype=np.int32)
    active = np.ones(n, dtype=bool)
    depth = int(model["depth"])
    for _ in range(depth + 5):
        if not active.any():
            break
        cur_nodes = node[active]
        cur_left = cl[cur_nodes]
        leaf_mask = cur_left == -1
        cur_features = feat[cur_nodes]
        cur_thresholds = thr[cur_nodes]
        cur_right = cr[cur_nodes]
        row_idx = np.where(active)[0]
        vals = X[row_idx, cur_features]
        go_left = vals <= cur_thresholds
        new_node = np.where(go_left, cur_left, cur_right)
        new_node = np.where(leaf_mask, cur_nodes, new_node)
        node[row_idx] = new_node
        active[row_idx] = ~leaf_mask
    return node


def aggregate_per_leaf(leaf_ids: np.ndarray, Y: np.ndarray, n_nodes: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (count[n_nodes], sumY[n_nodes,105], sumY2[n_nodes,105]) — only
    leaf entries are non-zero; internal nodes get filled by propagation later.

    Memory-conscious: never materialize Y64 (5GB) or Y*Y (5GB). Pull one
    column at a time as float64 (48MB) and call bincount twice."""
    n, K = Y.shape
    print(f"\naggregating per-leaf (count, sumY, sumY^2) for {n:,} hands × {K} outputs ...", flush=True)
    t0 = time.time()
    count = np.bincount(leaf_ids, minlength=n_nodes).astype(np.float64)
    sumY = np.zeros((n_nodes, K), dtype=np.float64)
    sumY2 = np.zeros((n_nodes, K), dtype=np.float64)
    for k in range(K):
        col64 = np.asarray(Y[:, k], dtype=np.float64)  # 48 MB
        sumY[:, k] = np.bincount(leaf_ids, weights=col64, minlength=n_nodes)
        sumY2[:, k] = np.bincount(leaf_ids, weights=col64 * col64, minlength=n_nodes)
        del col64
        if (k + 1) % 15 == 0 or k == K - 1:
            print(f"  output {k+1}/{K}  ({time.time()-t0:.1f}s)", flush=True)
    print(f"  per-leaf agg: {time.time()-t0:.1f}s", flush=True)
    return count, sumY, sumY2


def propagate_up_to_internal(model: dict, count: np.ndarray, sumY: np.ndarray, sumY2: np.ndarray) -> None:
    """In place: fill internal-node count/sum entries from children. Assumes
    sklearn DT node ordering: children indices are larger than the parent
    in array index? Actually NOT guaranteed — DTs are built recursively and
    children can be at any index. So we compute parent[] explicitly and
    then process nodes in reverse-BFS / topological order."""
    cl = model["children_left"]
    cr = model["children_right"]
    n_nodes = len(cl)

    # Compute parent + depth in a single BFS from root (O(n_nodes)).
    parent = np.full(n_nodes, -1, dtype=np.int32)
    depth_arr = np.zeros(n_nodes, dtype=np.int32)
    stack = [(0, 0)]
    while stack:
        node, d = stack.pop()
        depth_arr[node] = d
        if cl[node] != -1:
            parent[cl[node]] = node
            parent[cr[node]] = node
            stack.append((cl[node], d + 1))
            stack.append((cr[node], d + 1))
    # Process internal nodes deepest first (children before parent).
    is_internal = cl != -1
    internal_idx = np.where(is_internal)[0]
    order = internal_idx[np.argsort(-depth_arr[internal_idx])]

    print(f"  propagating sums up through {len(order):,} internal nodes ...", flush=True)
    t0 = time.time()
    for node in order:
        L = cl[node]
        R = cr[node]
        count[node] = count[L] + count[R]
        sumY[node] += sumY[L] + sumY[R]
        sumY2[node] += sumY2[L] + sumY2[R]
    print(f"  propagate: {time.time()-t0:.1f}s", flush=True)


def compute_node_impurity(count: np.ndarray, sumY: np.ndarray, sumY2: np.ndarray) -> np.ndarray:
    """Mean over outputs of variance per output: 1/K * sum_k (sumY2_k/n - (sumY_k/n)^2).
    Multiply by n to get the squared-error sum that sklearn's MSE criterion uses
    (sklearn's "impurity" is the mean variance; reduction is n * impurity diff)."""
    n_nodes, K = sumY.shape
    impurity = np.zeros(n_nodes, dtype=np.float64)
    safe = count > 0
    n = count[safe].reshape(-1, 1)
    mean = sumY[safe] / n
    mean_sq = sumY2[safe] / n
    var = mean_sq - mean * mean
    var = np.maximum(var, 0.0)  # numerical
    impurity[safe] = var.mean(axis=1)
    return impurity


FEATURE_DESCRIPTIONS = {
    "n_pairs": "number of pairs in hand",
    "pair_high_rank": "rank of highest pair (2-14, 0 if none)",
    "pair_low_rank": "rank of 2nd-highest pair (0 if none)",
    "pair_third_rank": "rank of 3rd-highest pair (0 if none)",
    "n_trips": "number of trips in hand",
    "trips_rank": "rank of highest trips (0 if none)",
    "n_quads": "number of quads",
    "quads_rank": "rank of quads (0 if none)",
    "top_rank": "highest singleton rank (or pair/trip rank)",
    "second_rank": "2nd-highest distinct rank",
    "third_rank": "3rd-highest distinct rank",
    "suit_max": "count of cards in most-common suit",
    "suit_2nd": "count of cards in 2nd-most-common suit",
    "suit_3rd": "count of cards in 3rd-most-common suit",
    "suit_4th": "count of cards in 4th-most-common suit",
    "n_suits_present": "distinct suits present (1-4)",
    "is_monosuit": "1 if all 7 cards same suit",
    "connectivity": "longest run of consecutive ranks",
    "n_broadway": "count of broadway cards (T-A)",
    "n_low": "count of low cards (2-5)",
    "category_id": "category code (alphabetical: high_only=0,pair=1,quads=2,three_pair=3,trips=4,trips_pair=5,two_pair=6)",
    "can_make_ds_bot": "1 if suit_2nd >= 2 (DS bot is achievable)",
    "can_make_4run": "1 if 4-card straight run available",
    "has_high_pair": "1 if highest pair >= Q",
    "has_low_pair": "1 if has pair AND highest pair <= 5",
    "has_premium_pair": "1 if highest pair is K or A",
    "has_ace_singleton": "1 if hand contains a singleton Ace (no pair/trip/quad of A)",
    "has_king_singleton": "1 if hand contains a singleton K AND no other K-or-higher pair/trip/quad",
    "default_bot_is_ds": "(pair-cat aug) v8 default-bot is DS",
    "n_top_choices_yielding_ds_bot": "(pair-cat aug) # of top-card choices that allow DS bot",
    "pair_to_bot_alt_is_ds": "(pair-cat aug) the alt pair-to-bot routing is DS",
    "default_bot_is_ds_high": "(high_only-cat aug) v8 default-bot is DS",
    "n_mid_choices_yielding_ds_bot": "(high_only-cat aug) # of mid choices yielding DS bot",
    "best_ds_bot_mid_max_rank": "(high_only-cat aug) best mid max-rank when DS bot is taken",
    "default_bot_is_ds_tp": "(two_pair-cat aug) v8 default-bot is DS",
    "n_routings_yielding_ds_bot_tp": "(two_pair-cat aug) # of two-pair routings yielding DS bot",
    "swap_high_pair_to_bot_ds_compatible": "(two_pair-cat aug) swapping high pair to bot is DS-compatible",
}


def main() -> int:
    print(f"loading model {MODEL_PATH} ...", flush=True)
    arr = np.load(MODEL_PATH, allow_pickle=True)
    feature_columns = [str(c) for c in arr["feature_columns"]]
    model = {
        "children_left": np.asarray(arr["children_left"], dtype=np.int32),
        "children_right": np.asarray(arr["children_right"], dtype=np.int32),
        "feature": np.asarray(arr["feature"], dtype=np.int32),
        "threshold": np.asarray(arr["threshold"], dtype=np.float64),
        "leaf_values": np.asarray(arr["leaf_values"], dtype=np.float32),
        "depth": int(arr["depth"]),
        "n_leaves": int(arr["n_leaves"]),
        "feature_columns": feature_columns,
    }
    n_nodes = len(model["children_left"])
    print(f"  n_nodes={n_nodes}  n_leaves={model['n_leaves']}  depth={model['depth']}", flush=True)

    X = build_feature_matrix(feature_columns)
    n_hands = X.shape[0]

    print(f"\nloading oracle grid ...", flush=True)
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    assert len(grid) == n_hands, f"grid {len(grid)} vs feature table {n_hands}"
    Y = np.asarray(grid.evs[:n_hands])  # memmap view; bincount loops will materialize
    print(f"  Y={Y.shape} dtype={Y.dtype}", flush=True)

    print(f"\nwalking all {n_hands:,} hands to leaf ...", flush=True)
    t0 = time.time()
    leaf_ids = walk_each_hand_to_leaf(X, model)
    print(f"  walk: {time.time()-t0:.1f}s  unique leaves hit: {len(np.unique(leaf_ids)):,}", flush=True)

    count, sumY, sumY2 = aggregate_per_leaf(leaf_ids, Y, n_nodes)
    propagate_up_to_internal(model, count, sumY, sumY2)
    impurity = compute_node_impurity(count, sumY, sumY2)

    # Sanity: root count == n_hands.
    print(f"\nroot count = {count[0]:.0f} (expect {n_hands:,})", flush=True)
    print(f"root impurity = {impurity[0]:.6f}", flush=True)

    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]

    # Compute MSE-reduction per internal node.
    is_internal = cl != -1
    n_internal = int(is_internal.sum())
    print(f"\nranking {n_internal:,} internal splits by population-weighted MSE reduction ...", flush=True)

    reductions = np.zeros(n_nodes, dtype=np.float64)
    for node in np.where(is_internal)[0]:
        L = cl[node]
        R = cr[node]
        nN = count[node]
        nL = count[L]
        nR = count[R]
        if nN == 0:
            continue
        reductions[node] = nN * impurity[node] - nL * impurity[L] - nR * impurity[R]

    # Top-K splits by reduction.
    TOP = 30
    order = np.argsort(-reductions)[:TOP]
    print(f"\n=== TOP {TOP} SPLITS BY MSE REDUCTION ===\n", flush=True)
    print(f"{'rank':>4}  {'node':>6}  {'feature':<35}  {'thr':>8}  {'reduce':>12}  "
          f"{'n_node':>10}  {'n_left':>10}  {'n_right':>10}  {'leaf_arg_L':>10}  {'leaf_arg_R':>10}",
          flush=True)
    print("-" * 165, flush=True)
    for rank, node in enumerate(order, 1):
        f_idx = feat[node]
        f_name = feature_columns[f_idx]
        L = cl[node]
        R = cr[node]
        # leaf-vec argmax for the SUBTREE means at left/right (this is the
        # mean Y of the subtree, the "winning" setting if forced to a single
        # answer for that subpopulation).
        meanL = (sumY[L] / count[L]) if count[L] > 0 else np.zeros(105)
        meanR = (sumY[R] / count[R]) if count[R] > 0 else np.zeros(105)
        argL = int(meanL.argmax())
        argR = int(meanR.argmax())
        print(f"{rank:>4}  {node:>6}  {f_name:<35}  {thr[node]:>8.2f}  {reductions[node]:>12.0f}  "
              f"{count[node]:>10.0f}  {count[L]:>10.0f}  {count[R]:>10.0f}  {argL:>10d}  {argR:>10d}",
              flush=True)

    # Aggregate by feature: sum reduction across all splits using each feature.
    # That's the sklearn `feature_importances_` style ranking.
    print(f"\n=== FEATURE IMPORTANCE (sum of MSE reduction across all uses) ===\n", flush=True)
    feat_imp = np.zeros(len(feature_columns), dtype=np.float64)
    for node in np.where(is_internal)[0]:
        feat_imp[feat[node]] += reductions[node]
    feat_total = feat_imp.sum()
    fi_order = np.argsort(-feat_imp)
    print(f"{'rank':>4}  {'feature':<40}  {'pct':>8}  {'reduce':>14}  {'desc'}", flush=True)
    print("-" * 140, flush=True)
    for rank, idx in enumerate(fi_order, 1):
        if feat_imp[idx] <= 0:
            continue
        pct = 100.0 * feat_imp[idx] / feat_total if feat_total > 0 else 0
        desc = FEATURE_DESCRIPTIONS.get(feature_columns[idx], "")
        print(f"{rank:>4}  {feature_columns[idx]:<40}  {pct:>7.2f}%  {feat_imp[idx]:>14.0f}  {desc}", flush=True)

    # Print depth-1, depth-2 splits — these are the most consequential
    # high-level branching decisions.
    print(f"\n=== TREE TOP (root + depth-1 children) ===\n", flush=True)
    def print_node(node, indent=0):
        pad = "  " * indent
        if cl[node] == -1:
            argmax = int(model["leaf_values"][node].argmax())
            print(f"{pad}LEAF node={node} n={count[node]:.0f} arg={argmax}", flush=True)
            return
        f_idx = feat[node]
        print(f"{pad}node={node} d={indent}  if {feature_columns[f_idx]} <= {thr[node]:.2f}  (n={count[node]:.0f}, reduce={reductions[node]:.0f})", flush=True)
    # Depth 0
    print_node(0, 0)
    # Recurse to depth 4
    def recurse(node, depth):
        if cl[node] == -1 or depth > 4:
            return
        L = cl[node]
        R = cr[node]
        pad = "  " * (depth + 1)
        print(f"{pad}LEFT  node={L} (n={count[L]:.0f})", flush=True)
        print_node(L, depth + 1)
        recurse(L, depth + 1)
        print(f"{pad}RIGHT node={R} (n={count[R]:.0f})", flush=True)
        print_node(R, depth + 1)
        recurse(R, depth + 1)
    recurse(0, 0)

    return 0


if __name__ == "__main__":
    sys.exit(main())
