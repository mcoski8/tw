"""
Session 34 — distill v26's tree on the high_only category.

high_only is the biggest UNTOUCHED lever since v20 (Session 30):
  20.4% population × $2,894/1000h regret = $590/1000h share.

This diagnostic walks the full 6M-hand corpus through v26's tree, then
restricts analysis to high_only hands (n_pairs=n_trips=n_quads=0). The
goal is to identify whether v26's tree has clear "miss leaves" where a
single underused feature axis would separate winners from losers — i.e.,
whether a `connectivity_high_g` / `n_broadway_in_2nd_suit_g` /
`top_3_broadway_n_g` family is justified, or whether high_only is
intrinsically diffuse.

Reports:
  - root + depth-3 tree shape (which features v26 uses near the top)
  - top 30 splits by MSE-reduction (population-wide, but with high_only
    sub-counts so we can tell which splits dominate the high_only
    sub-tree)
  - per-leaf high_only stats: count, mean regret, v26 vs BR pick %
  - top 30 high-regret leaves: where v26 bleeds the most $/1000h on
    high_only — these are the candidate-feature target leaves
  - "what would a perfect feature do?" — for each top miss leaf, compute
    the BR-EV variance within the leaf (high variance = there's room for
    a feature to separate winners; low variance = the leaf is already
    tight and misses are MC noise)

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/distill_v26_high_only.py
"""
from __future__ import annotations

import argparse
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
from train_v26_dt import build_X, FEATURE_COLUMNS  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
MODEL_PATH = ROOT / "data" / "v26_dt_model.npz"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0


def walk_each_hand_to_leaf(X: np.ndarray, model: dict) -> np.ndarray:
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


def compute_per_node_stats(leaf_ids, mask_ho, Y, n_nodes, K, model):
    """For BOTH the full population AND the high_only subset, compute
    (count, sumY, sumY2) per node + propagate up to internal nodes.
    Returns four dicts keyed 'all' and 'ho' each with count/sumY/sumY2.
    """
    cl = model["children_left"]
    cr = model["children_right"]
    n_hands = leaf_ids.shape[0]

    print("  aggregating per-leaf for ALL hands ...", flush=True)
    t0 = time.time()
    count_all = np.bincount(leaf_ids, minlength=n_nodes).astype(np.float64)
    sumY_all = np.zeros((n_nodes, K), dtype=np.float64)
    sumY2_all = np.zeros((n_nodes, K), dtype=np.float64)
    for k in range(K):
        col = np.asarray(Y[:, k], dtype=np.float64)
        sumY_all[:, k] = np.bincount(leaf_ids, weights=col, minlength=n_nodes)
        sumY2_all[:, k] = np.bincount(leaf_ids, weights=col * col, minlength=n_nodes)
        if (k + 1) % 25 == 0 or k == K - 1:
            print(f"    output {k+1}/{K}  ({time.time()-t0:.1f}s)", flush=True)

    print("  aggregating per-leaf for high_only subset ...", flush=True)
    t0 = time.time()
    leaf_ho = leaf_ids[mask_ho]
    count_ho = np.bincount(leaf_ho, minlength=n_nodes).astype(np.float64)
    sumY_ho = np.zeros((n_nodes, K), dtype=np.float64)
    sumY2_ho = np.zeros((n_nodes, K), dtype=np.float64)
    for k in range(K):
        col = np.asarray(Y[mask_ho, k], dtype=np.float64)
        sumY_ho[:, k] = np.bincount(leaf_ho, weights=col, minlength=n_nodes)
        sumY2_ho[:, k] = np.bincount(leaf_ho, weights=col * col, minlength=n_nodes)
        if (k + 1) % 25 == 0 or k == K - 1:
            print(f"    output {k+1}/{K}  ({time.time()-t0:.1f}s)", flush=True)

    print("  propagating sums up ...", flush=True)
    t0 = time.time()
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
    is_internal = cl != -1
    internal_idx = np.where(is_internal)[0]
    order = internal_idx[np.argsort(-depth_arr[internal_idx])]
    for node in order:
        L = cl[node]
        R = cr[node]
        count_all[node] = count_all[L] + count_all[R]
        sumY_all[node] += sumY_all[L] + sumY_all[R]
        sumY2_all[node] += sumY2_all[L] + sumY2_all[R]
        count_ho[node] = count_ho[L] + count_ho[R]
        sumY_ho[node] += sumY_ho[L] + sumY_ho[R]
        sumY2_ho[node] += sumY2_ho[L] + sumY2_ho[R]
    print(f"    propagate: {time.time()-t0:.1f}s", flush=True)

    return (count_all, sumY_all, sumY2_all,
            count_ho, sumY_ho, sumY2_ho,
            depth_arr)


def compute_node_impurity(count: np.ndarray, sumY: np.ndarray, sumY2: np.ndarray) -> np.ndarray:
    n_nodes, K = sumY.shape
    impurity = np.zeros(n_nodes, dtype=np.float64)
    safe = count > 0
    n = count[safe].reshape(-1, 1)
    mean = sumY[safe] / n
    mean_sq = sumY2[safe] / n
    var = mean_sq - mean * mean
    var = np.maximum(var, 0.0)
    impurity[safe] = var.mean(axis=1)
    return impurity


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-splits", type=int, default=30)
    ap.add_argument("--top-leaves", type=int, default=30)
    args = ap.parse_args()

    print("=" * 80)
    print("Session 34: v26 distillation focused on high_only category")
    print("=" * 80)

    print(f"\n[1/6] Loading model {MODEL_PATH} ...", flush=True)
    arr = np.load(MODEL_PATH, allow_pickle=True)
    feature_columns = [str(c) for c in arr["feature_columns"]]
    print(f"  feature_columns: {len(feature_columns)} columns")
    assert feature_columns == FEATURE_COLUMNS, \
        f"feature column mismatch:\n model={feature_columns[:5]}...\n train_v26_dt={FEATURE_COLUMNS[:5]}..."
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
    print(f"  n_nodes={n_nodes:,}  n_leaves={model['n_leaves']:,}  depth={model['depth']}")

    print(f"\n[2/6] Building 65-col feature matrix X for all 6M hands ...", flush=True)
    t0 = time.time()
    X, n_hands = build_X()
    print(f"  X={X.shape}  ({X.nbytes/1e6:.0f} MB)  ({time.time()-t0:.1f}s)")

    print("\n[3/6] Identifying high_only mask via base feature_table ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=[
        "canonical_id", "n_pairs", "n_trips", "n_quads",
        "n_broadway", "n_low", "connectivity",
        "suit_max", "suit_2nd", "suit_3rd",
        "top_rank", "second_rank", "third_rank",
    ])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    mask_ho = (n_pairs == 0) & (n_trips == 0) & (n_quads == 0)
    print(f"  high_only hands: {int(mask_ho.sum()):>10,}  ({100*mask_ho.mean():.2f}%)")

    print(f"\n[4/6] Loading oracle grid (memmap) ...", flush=True)
    t0 = time.time()
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_hands])
    print(f"  Y={Y.shape}  ({time.time()-t0:.1f}s)")

    print(f"\n[5/6] Walking all {n_hands:,} hands to leaf ...", flush=True)
    t0 = time.time()
    leaf_ids = walk_each_hand_to_leaf(X, model)
    print(f"  walk: {time.time()-t0:.1f}s  unique leaves hit: {len(np.unique(leaf_ids)):,}")

    print(f"\n[6/6] Aggregating per-node stats (full + high_only) ...", flush=True)
    K = Y.shape[1]
    (count_all, sumY_all, sumY2_all,
     count_ho, sumY_ho, sumY2_ho, depth_arr) = compute_per_node_stats(
        leaf_ids, mask_ho, Y, n_nodes, K, model
    )

    print("\nROOT SANITY:")
    print(f"  root count_all = {count_all[0]:,.0f}  (expect {n_hands:,})")
    print(f"  root count_ho  = {count_ho[0]:,.0f}   (expect {int(mask_ho.sum()):,})")

    impurity_all = compute_node_impurity(count_all, sumY_all, sumY2_all)
    impurity_ho = compute_node_impurity(count_ho, sumY_ho, sumY2_ho)
    print(f"  root impurity_all = {impurity_all[0]:.4f}  (mean per-output variance)")
    print(f"  root impurity_ho  = {impurity_ho[0]:.4f}")

    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]
    is_internal = cl != -1

    # MSE reduction restricted to high_only sub-population
    print(f"\n=== TOP {args.top_splits} SPLITS BY HIGH_ONLY MSE REDUCTION ===\n", flush=True)
    reductions_ho = np.zeros(n_nodes, dtype=np.float64)
    for node in np.where(is_internal)[0]:
        L = cl[node]
        R = cr[node]
        nN = count_ho[node]; nL = count_ho[L]; nR = count_ho[R]
        if nN < 50:  # ignore tiny ho subpopulations
            continue
        reductions_ho[node] = nN * impurity_ho[node] - nL * impurity_ho[L] - nR * impurity_ho[R]
    order = np.argsort(-reductions_ho)[:args.top_splits]
    print(f"{'rank':>4}  {'node':>7}  {'feature':<38}  {'thr':>8}  {'red_ho':>10}  "
          f"{'n_ho':>9}  {'n_L_ho':>9}  {'n_R_ho':>9}  {'n_all':>10}  {'depth':>5}")
    print("-" * 165)
    for rank, node in enumerate(order, 1):
        f_idx = feat[node]
        f_name = feature_columns[f_idx]
        L = cl[node]; R = cr[node]
        print(f"{rank:>4}  {node:>7}  {f_name:<38}  {thr[node]:>8.2f}  "
              f"{reductions_ho[node]:>10.0f}  "
              f"{count_ho[node]:>9.0f}  {count_ho[L]:>9.0f}  {count_ho[R]:>9.0f}  "
              f"{count_all[node]:>10.0f}  {depth_arr[node]:>5d}")

    # Feature importance restricted to high_only
    print(f"\n=== FEATURE IMPORTANCE (sum of high_only-restricted MSE reduction) ===\n", flush=True)
    feat_imp = np.zeros(len(feature_columns), dtype=np.float64)
    for node in np.where(is_internal)[0]:
        feat_imp[feat[node]] += reductions_ho[node]
    feat_total = feat_imp.sum()
    fi_order = np.argsort(-feat_imp)
    print(f"{'rank':>4}  {'feature':<38}  {'pct':>8}  {'reduce':>14}")
    print("-" * 90)
    for rank, idx in enumerate(fi_order, 1):
        if feat_imp[idx] <= 0:
            continue
        pct = 100.0 * feat_imp[idx] / feat_total if feat_total > 0 else 0
        if pct < 0.05 and rank > 25:
            break
        print(f"{rank:>4}  {feature_columns[idx]:<38}  {pct:>7.2f}%  {feat_imp[idx]:>14.0f}")

    # Per-leaf high_only stats: regret = max(BR_EV) - max(v26_EV)
    print(f"\n=== TOP {args.top_leaves} HIGH_ONLY MISS LEAVES ===\n", flush=True)
    print("Computing per-leaf v26 pick + BR pick + total regret on high_only ...", flush=True)
    t0 = time.time()

    leaf_mask = cl == -1
    leaf_indices = np.where(leaf_mask)[0]
    leaf_total_regret_ho = np.zeros(n_nodes, dtype=np.float64)
    leaf_v26_pick = np.zeros(n_nodes, dtype=np.int32)
    leaf_br_pick = np.zeros(n_nodes, dtype=np.int32)
    leaf_v26_meanev_ho = np.zeros(n_nodes, dtype=np.float64)
    leaf_br_meanev_ho = np.zeros(n_nodes, dtype=np.float64)
    leaf_br_var_ho = np.zeros(n_nodes, dtype=np.float64)  # variance of BR-EV within the leaf

    # For per-leaf BR analysis on high_only, we need per-hand best-EV and v26-EV.
    # v26 picks the argmax of leaf_values per leaf — same for every hand in the leaf.
    # BR is per-hand argmax over Y.
    # We also want per-leaf variance of best-EV across hands in the leaf (high_only filtered).
    print("  computing per-hand best-EV and v26-EV (high_only) ...", flush=True)
    leaf_ids_ho = leaf_ids[mask_ho]
    Y_ho = np.asarray(Y[mask_ho], dtype=np.float32)
    best_ev_ho = Y_ho.max(axis=1).astype(np.float64)
    # v26's pick per leaf is leaf_values.argmax over the K=105 outputs
    lv = model["leaf_values"]
    v26_pick_per_leaf = lv.argmax(axis=1)
    # Per-hand v26-EV
    v26_ev_ho = Y_ho[np.arange(Y_ho.shape[0]), v26_pick_per_leaf[leaf_ids_ho]].astype(np.float64)
    regret_ho = best_ev_ho - v26_ev_ho

    n_ho = int(mask_ho.sum())
    print(f"  high_only mean v26 EV: {v26_ev_ho.mean():+.4f}  "
          f"BR EV: {best_ev_ho.mean():+.4f}  "
          f"regret: {regret_ho.mean():+.4f}  "
          f"(${regret_ho.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h)")

    # Per-leaf totals.
    leaf_total_regret_ho = np.bincount(leaf_ids_ho, weights=regret_ho, minlength=n_nodes)
    leaf_count_ho = np.bincount(leaf_ids_ho, minlength=n_nodes)
    leaf_sum_v26ev = np.bincount(leaf_ids_ho, weights=v26_ev_ho, minlength=n_nodes)
    leaf_sum_brev = np.bincount(leaf_ids_ho, weights=best_ev_ho, minlength=n_nodes)
    leaf_sum_brev_sq = np.bincount(leaf_ids_ho, weights=best_ev_ho * best_ev_ho, minlength=n_nodes)

    leaf_v26_pick = v26_pick_per_leaf

    # Order leaves by total regret (descending) — these are the cost centers.
    # Restrict to leaves with at least N=20 high_only hands (avoid tiny noisy ones).
    eligible = leaf_count_ho >= 20
    print(f"  leaves with >=20 high_only hands: {int(eligible.sum()):,}/{int(leaf_mask.sum()):,}")
    leaf_order = np.argsort(-(leaf_total_regret_ho * eligible))[:args.top_leaves]

    print(f"\n{'rank':>4}  {'leaf':>8}  {'n_ho':>8}  {'mean_reg':>10}  {'tot_reg':>10}  "
          f"{'mean_brev':>10}  {'mean_v26ev':>11}  {'std_brev':>10}  {'v26_pick':>9}")
    print("-" * 110)
    for rank, leaf in enumerate(leaf_order, 1):
        n_l = leaf_count_ho[leaf]
        if n_l == 0: continue
        mean_reg = leaf_total_regret_ho[leaf] / n_l
        tot_reg = leaf_total_regret_ho[leaf]
        mean_brev = leaf_sum_brev[leaf] / n_l
        mean_v26ev = leaf_sum_v26ev[leaf] / n_l
        var_br = leaf_sum_brev_sq[leaf] / n_l - mean_brev ** 2
        std_br = float(np.sqrt(max(var_br, 0)))
        print(f"{rank:>4}  {leaf:>8}  {n_l:>8.0f}  {mean_reg:>+10.4f}  {tot_reg:>+10.2f}  "
              f"{mean_brev:>+10.4f}  {mean_v26ev:>+11.4f}  {std_br:>10.4f}  {leaf_v26_pick[leaf]:>9d}")

    # For the top-10 miss leaves, compute the path from root → leaf to show
    # what conditions define the leaf, and report the ho-population's
    # distribution of useful candidate features.
    print(f"\n=== TOP-10 MISS-LEAF PATHS + CANDIDATE-FEATURE DISTRIBUTIONS ===\n", flush=True)
    parent = np.full(n_nodes, -1, dtype=np.int32)
    side = np.zeros(n_nodes, dtype=np.int8)  # +1 = right child, -1 = left
    stack = [(0, -1, 0)]
    while stack:
        node, par, s = stack.pop()
        parent[node] = par
        side[node] = s
        if cl[node] != -1:
            stack.append((cl[node], node, -1))
            stack.append((cr[node], node, +1))

    # Candidate feature: longest run RESTRICTED to broadway ranks (T-A).
    # We don't have this in the parquet — compute on the fly from canonical
    # hands. Quick: read the canonical_hands once, derive per-hand
    # "connectivity_high" = longest run among broadway ranks present.
    print("  loading canonical hands (memmap) for candidate-feature derivations ...", flush=True)
    from tw_analysis.canonical import read_canonical_hands
    ch = read_canonical_hands(ROOT / "data" / "canonical_hands.bin", mode="memmap")
    hands_arr = np.asarray(ch.hands)  # (n_hands, 7) uint8

    # Derive: connectivity_high (longest run in broadway, T..A is 10..14)
    # n_broadway_in_2nd_suit (count of broadway in the 2nd-largest suit)
    # top_3_broadway_n (count of T-A among the top-3 ranks)
    # n_broadway_distinct_ranks (distinct broadway ranks present)
    # We compute only for the rows we actually need (each top-miss leaf's ho
    # subset) to keep this snappy.
    def compute_candidate_features(hand_rows: np.ndarray) -> dict:
        """For a small subset of hands, compute candidate gated features."""
        ranks = (hand_rows // 4) + 2  # (m, 7)
        suits = hand_rows & 0b11
        m = hand_rows.shape[0]
        out = {}

        # connectivity_high: longest run of consecutive ranks within 10..14
        bw_ranks = np.where(ranks >= 10, ranks, 0)
        # presence vector across ranks 10..14 (5 slots)
        presence_high = np.zeros((m, 5), dtype=np.int8)
        for k in range(7):
            r = ranks[:, k]
            mask = r >= 10
            if mask.any():
                idx = np.where(mask)[0]
                presence_high[idx, r[idx] - 10] = 1
        cur = np.zeros(m, dtype=np.int8)
        longest = np.zeros(m, dtype=np.int8)
        for j in range(5):
            col = presence_high[:, j]
            cur = np.where(col == 1, cur + 1, 0)
            longest = np.maximum(longest, cur)
        out["connectivity_high"] = longest

        # n_broadway_in_2nd_suit: count of T..A cards in the 2nd-most-common suit
        suit_counts = np.zeros((m, 4), dtype=np.int8)
        for k in range(7):
            for s in range(4):
                suit_counts[:, s] += (suits[:, k] == s).astype(np.int8)
        sorted_idx = np.argsort(-suit_counts, axis=1)
        second_suit = sorted_idx[:, 1]  # (m,) — index of 2nd-most suit
        n_bw_2nd = np.zeros(m, dtype=np.int8)
        for k in range(7):
            mask = (suits[:, k] == second_suit) & (ranks[:, k] >= 10)
            n_bw_2nd[mask] += 1
        out["n_broadway_in_2nd_suit"] = n_bw_2nd

        # top_3_broadway_n: count of T..A among the top-3 ranks
        ranks_sorted = -np.sort(-ranks, axis=1)  # descending
        top3 = ranks_sorted[:, :3]
        out["top_3_broadway_n"] = (top3 >= 10).sum(axis=1).astype(np.int8)

        # n_broadway_distinct_ranks
        out["n_broadway_distinct_ranks"] = (presence_high > 0).sum(axis=1).astype(np.int8)

        return out

    for rank, leaf in enumerate(leaf_order[:10], 1):
        # Rebuild path from root → leaf
        path = []
        cur = int(leaf)
        while parent[cur] != -1:
            par = int(parent[cur])
            sd = "<=" if side[cur] == -1 else ">"
            path.append((par, feature_columns[feat[par]], thr[par], sd))
            cur = par
        path.reverse()
        n_l = int(leaf_count_ho[leaf])
        mean_reg = leaf_total_regret_ho[leaf] / max(n_l, 1)
        print(f"\nMISS LEAF #{rank}  node={leaf}  n_ho={n_l}  "
              f"mean_regret={mean_reg:+.4f}  v26_pick={leaf_v26_pick[leaf]}")
        for par, fname, t_, sd in path:
            print(f"    {fname:<38} {sd:>2} {t_:>7.2f}")
        # Pull out the high_only hand IDs in this leaf and run candidate features.
        is_in_leaf = (leaf_ids == leaf) & mask_ho
        leaf_cids = np.where(is_in_leaf)[0]
        if len(leaf_cids) == 0:
            continue
        rows = hands_arr[leaf_cids]
        cand = compute_candidate_features(rows)
        # For each candidate feature, see how it correlates with regret in
        # the leaf — i.e. does splitting on this feature reduce within-leaf
        # variance of BR-EV?
        regret_in_leaf = regret_ho[mask_ho[leaf_cids[:0]]]  # placeholder
        # Build the per-leaf regret in the leaf-restricted index order
        ho_idx_in_full = np.where(mask_ho)[0]
        leaf_ho_pos = np.where(leaf_ids_ho == leaf)[0]
        regret_leaf = regret_ho[leaf_ho_pos]
        brev_leaf = best_ev_ho[leaf_ho_pos]
        # Pull cand features in same order
        # We computed cand for all ho hands in this leaf in the order leaf_cids,
        # but leaf_cids is full-population canonical order whereas leaf_ho_pos
        # is high_only-only position. Map them.
        # leaf_cids = canonical_ids of high_only-and-in-this-leaf hands
        # ho_idx_in_full[leaf_ho_pos] = canonical_ids of ho-pos hands in this leaf
        # These should match (just possibly in different order; sort both).
        canonical_a = leaf_cids
        canonical_b = ho_idx_in_full[leaf_ho_pos]
        # Re-sort cand features to match canonical_b order
        order_remap = np.argsort(canonical_a)
        canonical_a_sorted = canonical_a[order_remap]
        for cname in ["connectivity_high", "n_broadway_in_2nd_suit",
                      "top_3_broadway_n", "n_broadway_distinct_ranks"]:
            cv = cand[cname][order_remap]  # (n_l,) in canonical_a_sorted order
            order_remap_b = np.argsort(canonical_b)
            cv_b = np.empty_like(cv)
            cv_b[order_remap_b] = cv  # now aligned to leaf_ho_pos order
            # Stratify regret by feature value
            by_value = {}
            for v in sorted(np.unique(cv_b)):
                m = cv_b == v
                if m.sum() < 5: continue
                by_value[int(v)] = (int(m.sum()),
                                    float(regret_leaf[m].mean()),
                                    float(brev_leaf[m].mean()))
            if len(by_value) >= 2:
                vals_str = "  ".join(
                    f"{v}:n={n} reg={r:+.3f} brev={br:+.3f}"
                    for v, (n, r, br) in by_value.items()
                )
                print(f"    [cand] {cname:<28} {vals_str}")

    print(f"\n=== TREE TOP (depth 0..3) ===\n")
    def print_node(node, indent=0):
        pad = "  " * indent
        if cl[node] == -1:
            argmax = int(model["leaf_values"][node].argmax())
            print(f"{pad}LEAF node={node} n_all={count_all[node]:.0f} n_ho={count_ho[node]:.0f} arg={argmax}")
            return
        f_idx = feat[node]
        print(f"{pad}node={node} d={indent}  if {feature_columns[f_idx]} <= {thr[node]:.2f}  "
              f"(n_all={count_all[node]:.0f}, n_ho={count_ho[node]:.0f}, "
              f"red_ho={reductions_ho[node]:.0f})")
    def recurse(node, depth):
        if cl[node] == -1 or depth > 3:
            return
        L = cl[node]; R = cr[node]
        pad = "  " * (depth + 1)
        print(f"{pad}LEFT")
        print_node(L, depth + 1)
        recurse(L, depth + 1)
        print(f"{pad}RIGHT")
        print_node(R, depth + 1)
        recurse(R, depth + 1)
    print_node(0, 0)
    recurse(0, 0)

    return 0


if __name__ == "__main__":
    sys.exit(main())
