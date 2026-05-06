"""
Session 36 — distill v29's tree on the pure trips category.

Pure trips = (n_trips=1, n_pairs=0, n_quads=0). 5.46% of grid (328,185
hands), uniform distribution across 13 ranks (25,245 each). v29's trips
regret is $1,997/1000h within-trips → $109/1000h whole-grid contribution.
This is the largest fully-untouched residual at v29.

Mirrors the pair-audit structure (`distill_v29_pair.py`). Goals:

A) Stratify by trips_rank to find which rank-groups leak most.
B) Compare v29 vs structural baselines (analogous to Rule 4 for pair):
   - A_paired_mid : mid is a pair of the trip rank (2 of 3 trips → mid)
   - B_paired_bot_any : bot has 2 trip-rank cards (any suit profile)
   - B_paired_bot_DS : same but bot is DS-shaped
   - C_top_trip : top is the trip rank (1 trip on top, 2 trips → mid)
   - Oracle = max over {A, B_any, C_top}
C) For each baseline, compute the gap from v29 to that baseline, and
   from v29 to oracle. The "competing baseline" finding (à la Session 35
   v27 < Rule 4) is the prescriptive signal for designing trips_aug
   gated features.
D) Top miss leaves on trips; feature importance restricted to trips.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/distill_v29_trips.py
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
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.query import setting_features_from_bytes, SUIT_PROFILE_DS  # noqa: E402
from train_v29_dt import build_X, FEATURE_COLUMNS  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
MODEL_PATH = ROOT / "data" / "v29_dt_model.npz"
FT_PATH = ROOT / "data" / "feature_table.parquet"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"

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


def compute_per_node_stats(leaf_ids, mask_target, Y, n_nodes, K, model):
    cl = model["children_left"]
    cr = model["children_right"]

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

    print("  aggregating per-leaf for target subset ...", flush=True)
    t0 = time.time()
    leaf_t = leaf_ids[mask_target]
    count_t = np.bincount(leaf_t, minlength=n_nodes).astype(np.float64)
    sumY_t = np.zeros((n_nodes, K), dtype=np.float64)
    sumY2_t = np.zeros((n_nodes, K), dtype=np.float64)
    for k in range(K):
        col = np.asarray(Y[mask_target, k], dtype=np.float64)
        sumY_t[:, k] = np.bincount(leaf_t, weights=col, minlength=n_nodes)
        sumY2_t[:, k] = np.bincount(leaf_t, weights=col * col, minlength=n_nodes)
        if (k + 1) % 25 == 0 or k == K - 1:
            print(f"    output {k+1}/{K}  ({time.time()-t0:.1f}s)", flush=True)

    print("  propagating sums up tree ...", flush=True)
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
        count_t[node] = count_t[L] + count_t[R]
        sumY_t[node] += sumY_t[L] + sumY_t[R]
        sumY2_t[node] += sumY2_t[L] + sumY2_t[R]
    print(f"  propagate: {time.time()-t0:.1f}s", flush=True)

    return count_all, sumY_all, sumY2_all, count_t, sumY_t, sumY2_t, depth_arr


def compute_node_impurity(count, sumY, sumY2):
    n_nodes, K = sumY.shape
    impurity = np.zeros(n_nodes, dtype=np.float64)
    safe = count > 0
    n = count[safe].reshape(-1, 1)
    mean = sumY[safe] / n
    mean_sq = sumY2[safe] / n
    var = np.maximum(mean_sq - mean * mean, 0.0)
    impurity[safe] = var.mean(axis=1)
    return impurity


def compute_routing_baselines_for_trips(Y_t, hands_bytes, trips_ranks, n_total):
    """For each trips hand compute EVs of A_paired_mid, B_paired_bot_DS,
    B_paired_bot_any, C_top_trip. Returns arrays of shape (n_trips,).
    NaN where the routing is unavailable.
    """
    n = Y_t.shape[0]
    ev_a = np.full(n, np.nan, dtype=np.float64)
    ev_b_ds = np.full(n, np.nan, dtype=np.float64)
    ev_b_any = np.full(n, np.nan, dtype=np.float64)
    ev_c = np.full(n, np.nan, dtype=np.float64)
    t0 = time.time()
    last_log = time.time()
    for i in range(n):
        h = np.asarray(hands_bytes[i], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        evs64 = np.asarray(Y_t[i], dtype=np.float64)
        tr = int(trips_ranks[i])

        mask_a = feats.mid_is_pair & (feats.mid_pair_rank == tr)
        mask_b_ds = (feats.bot_top_pair_rank == tr) & (feats.bot_suit_profile == SUIT_PROFILE_DS)
        mask_b_any = (feats.bot_top_pair_rank == tr)
        mask_c = (feats.top_rank == tr) & feats.mid_is_pair & (feats.mid_pair_rank == tr)

        if mask_a.any(): ev_a[i] = float(evs64[mask_a].max())
        if mask_b_ds.any(): ev_b_ds[i] = float(evs64[mask_b_ds].max())
        if mask_b_any.any(): ev_b_any[i] = float(evs64[mask_b_any].max())
        if mask_c.any(): ev_c[i] = float(evs64[mask_c].max())

        if time.time() - last_log > 5:
            print(f"    routing scan {i+1:>7,}/{n:,}  rate={(i+1)/(time.time()-t0):.0f}/s",
                  flush=True)
            last_log = time.time()
    return ev_a, ev_b_ds, ev_b_any, ev_c


def main():
    print("=" * 80)
    print("Session 36: v29 distillation focused on pure trips category")
    print("=" * 80)

    print(f"\n[1/8] Loading model {MODEL_PATH} ...", flush=True)
    arr = np.load(MODEL_PATH, allow_pickle=True)
    feature_columns = [str(c) for c in arr["feature_columns"]]
    print(f"  feature_columns: {len(feature_columns)} columns")
    assert feature_columns == FEATURE_COLUMNS, "feature column mismatch"
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

    print(f"\n[2/8] Building 73-col feature matrix X for all 6M hands ...", flush=True)
    t0 = time.time()
    X, n_hands = build_X()
    print(f"  X={X.shape}  ({X.nbytes/1e6:.0f} MB)  ({time.time()-t0:.1f}s)")

    print("\n[3/8] Identifying trips mask via base feature_table ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=[
        "canonical_id", "n_pairs", "n_trips", "n_quads", "trips_rank",
        "n_broadway", "n_low", "connectivity",
        "suit_max", "suit_2nd", "suit_3rd",
    ])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank = ft["trips_rank"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    print(f"  trips hands: {int(mask_trips.sum()):>10,}  ({100*mask_trips.mean():.2f}%)")

    print(f"\n[4/8] Loading oracle grid (memmap) ...", flush=True)
    t0 = time.time()
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_hands])
    print(f"  Y={Y.shape}  ({time.time()-t0:.1f}s)")

    print(f"\n[5/8] Walking all {n_hands:,} hands to leaf ...", flush=True)
    t0 = time.time()
    leaf_ids = walk_each_hand_to_leaf(X, model)
    print(f"  walk: {time.time()-t0:.1f}s  unique leaves hit: {len(np.unique(leaf_ids)):,}")

    K = Y.shape[1]
    count_all, sumY_all, sumY2_all, count_t, sumY_t, sumY2_t, depth_arr = compute_per_node_stats(
        leaf_ids, mask_trips, Y, n_nodes, K, model)

    print("\nROOT SANITY:")
    print(f"  root count_all = {count_all[0]:,.0f}  (expect {n_hands:,})")
    print(f"  root count_t   = {count_t[0]:,.0f}   (expect {int(mask_trips.sum()):,})")

    impurity_all = compute_node_impurity(count_all, sumY_all, sumY2_all)
    impurity_t = compute_node_impurity(count_t, sumY_t, sumY2_t)
    print(f"  root impurity_all = {impurity_all[0]:.4f}")
    print(f"  root impurity_t   = {impurity_t[0]:.4f}")

    cl = model["children_left"]
    feat = model["feature"]
    is_internal = cl != -1

    # ---------- Per-leaf miss stats on trips ----------
    print(f"\n[6/8] Per-leaf v29 vs BR on trips (top miss leaves)", flush=True)
    leaf_mask = cl == -1

    leaf_ids_t = leaf_ids[mask_trips]
    Y_t = np.asarray(Y[mask_trips], dtype=np.float32)
    best_ev_t = Y_t.max(axis=1).astype(np.float64)
    lv = model["leaf_values"]
    v29_pick_per_leaf = lv.argmax(axis=1)
    v29_ev_t = Y_t[np.arange(Y_t.shape[0]), v29_pick_per_leaf[leaf_ids_t]].astype(np.float64)
    regret_t = best_ev_t - v29_ev_t

    print(f"  trips mean v29 EV: {v29_ev_t.mean():+.4f}  BR EV: {best_ev_t.mean():+.4f}  "
          f"regret: {regret_t.mean():+.4f}  (${regret_t.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h)")

    leaf_count_t = np.bincount(leaf_ids_t, minlength=n_nodes)
    leaf_total_regret_t = np.bincount(leaf_ids_t, weights=regret_t, minlength=n_nodes)
    leaf_sum_brev = np.bincount(leaf_ids_t, weights=best_ev_t, minlength=n_nodes)
    leaf_sum_brev_sq = np.bincount(leaf_ids_t, weights=best_ev_t * best_ev_t, minlength=n_nodes)

    eligible = leaf_count_t >= 30
    print(f"  leaves with >=30 trips hands: {int(eligible.sum()):,}/{int(leaf_mask.sum()):,}")
    leaf_order = np.argsort(-(leaf_total_regret_t * eligible))[:30]

    print(f"\n  TOP 30 TRIPS MISS LEAVES (by total within-leaf regret):")
    print(f"  {'rank':>4}  {'leaf':>8}  {'n_t':>6}  {'mean_reg':>10}  {'tot_reg':>10}  "
          f"{'mean_brev':>10}  {'std_brev':>10}  {'v29_pick':>9}")
    for rank, leaf in enumerate(leaf_order, 1):
        n_l = int(leaf_count_t[leaf])
        if n_l < 30: continue
        mean_reg = leaf_total_regret_t[leaf] / n_l
        tot_reg = leaf_total_regret_t[leaf]
        mean_brev = leaf_sum_brev[leaf] / n_l
        var_br = leaf_sum_brev_sq[leaf] / n_l - mean_brev ** 2
        std_br = float(np.sqrt(max(var_br, 0)))
        print(f"  {rank:>4}  {leaf:>8}  {n_l:>6d}  {mean_reg:>+10.4f}  {tot_reg:>+10.2f}  "
              f"{mean_brev:>+10.4f}  {std_br:>10.4f}  {v29_pick_per_leaf[leaf]:>9d}")

    # ---------- Feature importance restricted to trips ----------
    print(f"\n  FEATURE IMPORTANCE on trips-restricted MSE reduction (top 25):")
    reductions_t = np.zeros(n_nodes, dtype=np.float64)
    cr_arr = model["children_right"]
    for node in np.where(is_internal)[0]:
        L = cl[node]; R = cr_arr[node]
        nN = count_t[node]; nL = count_t[L]; nR = count_t[R]
        if nN < 30:
            continue
        reductions_t[node] = nN * impurity_t[node] - nL * impurity_t[L] - nR * impurity_t[R]
    feat_imp = np.zeros(len(feature_columns), dtype=np.float64)
    for node in np.where(is_internal)[0]:
        feat_imp[feat[node]] += reductions_t[node]
    feat_total = feat_imp.sum()
    fi_order = np.argsort(-feat_imp)
    print(f"  {'rank':>4}  {'feature':<40}  {'pct':>7}  {'reduction':>14}")
    for rank, idx in enumerate(fi_order[:25], 1):
        if feat_imp[idx] <= 0: continue
        pct = 100.0 * feat_imp[idx] / feat_total if feat_total > 0 else 0
        print(f"  {rank:>4}  {feature_columns[idx]:<40}  {pct:>6.2f}%  {feat_imp[idx]:>14.0f}")

    # ---------- Per trips_rank stratification ----------
    print(f"\n[7/8] Per trips_rank stratification (within-trips regret)", flush=True)
    trips_rank_t = trips_rank[mask_trips]
    print(f"\n  trips_rank summary  (within-rank mean regret + share of trips total):")
    print(f"    {'rank':>4}  {'n':>7}  {'v29_reg':>10}  {'br_ev':>10}  {'v29_ev':>10}  {'$/1000h_grid':>14}")
    n_total = n_hands
    for r in range(2, 15):
        m = trips_rank_t == r
        n_m = int(m.sum())
        if n_m == 0: continue
        v29_r = regret_t[m].mean()
        br_r = best_ev_t[m].mean()
        v29_ev_r = v29_ev_t[m].mean()
        share = n_m / n_total
        dol = v29_r * EV_TO_DOLLARS * 1000 * share
        print(f"    {r:>4}  {n_m:>7,}  {v29_r:>+10.4f}  {br_r:>+10.4f}  {v29_ev_r:>+10.4f}  "
              f"${dol:>+13.1f}")

    # ---------- Routing-baseline comparison (the "competing baseline" check) ----------
    print(f"\n[8/8] Routing baseline analysis on trips", flush=True)
    print(f"  Loading canonical hands (for setting feature lookup) ...")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    trips_canonical_ids = np.where(mask_trips)[0]
    print(f"\n  Computing per-routing EVs for {len(trips_canonical_ids):,} trips hands ...")
    print(f"    A_paired_mid    : mid is pair of trip-rank")
    print(f"    B_paired_bot_DS : bot has 2 trip-rank cards AND bot is DS")
    print(f"    B_paired_bot_any: bot has 2 trip-rank cards (any suit profile)")
    print(f"    C_top_trip      : top is trip-rank (1 trip top + 2 mid)")
    print(f"    Oracle          : max over {{A, B_any, C_top}}")
    t0 = time.time()
    hands_bytes = ch.hands[trips_canonical_ids]  # shape (n_trips, 7)
    Y_trips = Y[trips_canonical_ids]  # shape (n_trips, 105)
    trips_ranks_arr = trips_rank[trips_canonical_ids]
    ev_a, ev_b_ds, ev_b_any, ev_c = compute_routing_baselines_for_trips(
        Y_trips, hands_bytes, trips_ranks_arr, n_total)
    print(f"  routing scan: {time.time()-t0:.1f}s")

    # Stack baseline EVs into a max-of-routings oracle (NaN-safe)
    avail_a = ~np.isnan(ev_a)
    avail_b_any = ~np.isnan(ev_b_any)
    avail_b_ds = ~np.isnan(ev_b_ds)
    avail_c = ~np.isnan(ev_c)
    print(f"\n  Routing availability (within trips):")
    print(f"    A_paired_mid : {int(avail_a.sum()):>6,} ({100*avail_a.mean():5.1f}%)")
    print(f"    B_paired_bot_any : {int(avail_b_any.sum()):>6,} ({100*avail_b_any.mean():5.1f}%)")
    print(f"    B_paired_bot_DS : {int(avail_b_ds.sum()):>6,} ({100*avail_b_ds.mean():5.1f}%)")
    print(f"    C_top_trip : {int(avail_c.sum()):>6,} ({100*avail_c.mean():5.1f}%)")

    # Build oracle = max over {A, B_any, C_top}, ignoring NaN
    stk = np.stack([ev_a, ev_b_any, ev_c], axis=1)
    oracle_ev = np.nanmax(stk, axis=1)
    # If everything is NaN (shouldn't happen for trips), set to BR
    oracle_ev = np.where(np.isnan(oracle_ev), best_ev_t, oracle_ev)

    # baseline regrets vs BR
    a_regret = best_ev_t - ev_a
    b_any_regret = best_ev_t - ev_b_any
    c_regret = best_ev_t - ev_c
    oracle_regret = best_ev_t - oracle_ev
    v29_regret = regret_t  # already computed

    pop_share_trips = mask_trips.mean()
    def grid_dollars(r):
        return r * EV_TO_DOLLARS * 1000 * pop_share_trips

    def fmt_baseline(name, regret_arr):
        avail = ~np.isnan(regret_arr)
        if avail.sum() == 0:
            return f"  {name:<25}: (always unavailable)"
        # For unavailable hands, treat regret as same as v29 (so we compare apples)
        # The baseline "always pick X if available, else fall back to v29"
        eff = np.where(avail, regret_arr, v29_regret)
        return (f"  {name:<25}: avail {100*avail.mean():>5.1f}%  "
                f"if-pick-when-avail-else-v29 mean regret: {eff.mean():+.4f}  "
                f"(${grid_dollars(eff.mean()):+,.1f}/1000h whole-grid)")

    print(f"\n  Mean regret on TRIPS subset (vs BR):")
    print(f"  {'v29 actual':<25}: mean regret: {v29_regret.mean():+.4f}  "
          f"(${grid_dollars(v29_regret.mean()):+,.1f}/1000h whole-grid)")
    print(fmt_baseline("Always A_paired_mid", a_regret))
    print(fmt_baseline("Always B_bot_any", b_any_regret))
    print(fmt_baseline("Always C_top_trip", c_regret))
    print(f"  {'Oracle (A∪B_any∪C)':<25}: mean regret: {oracle_regret.mean():+.4f}  "
          f"(${grid_dollars(oracle_regret.mean()):+,.1f}/1000h whole-grid)")

    # The CRITICAL question: is v29 worse than any single baseline?
    print(f"\n  v29 vs baselines (positive ⇒ v29 worse):")
    for name, br in [("A_paired_mid", a_regret),
                     ("B_bot_any", b_any_regret),
                     ("C_top_trip", c_regret),
                     ("Oracle (A∪B_any∪C)", oracle_regret)]:
        avail = ~np.isnan(br)
        eff = np.where(avail, br, v29_regret)
        gap = v29_regret.mean() - eff.mean()
        print(f"    v29 - ({name:<22}): {gap:+.4f}  (${gap*EV_TO_DOLLARS*1000*pop_share_trips:+,.1f}/1000h whole-grid)")

    # Per trips_rank: v29 vs A vs Oracle
    print(f"\n  Per trips_rank: v29 regret vs always-A vs oracle (whole-grid $/1000h):")
    print(f"  {'rank':>4}  {'n':>7}  {'v29_$':>8}  {'A_$':>8}  {'oracle_$':>10}  {'v29-A':>8}  {'v29-orcl':>10}")
    for r in range(2, 15):
        m = trips_ranks_arr == r
        n_m = int(m.sum())
        if n_m == 0: continue
        v29_r = v29_regret[m].mean()
        a_avail = ~np.isnan(a_regret[m])
        a_r_eff = np.where(a_avail, a_regret[m], v29_regret[m]).mean()
        oracle_r = oracle_regret[m].mean()
        share_r = n_m / n_total
        v29_dol = v29_r * EV_TO_DOLLARS * 1000 * share_r
        a_dol = a_r_eff * EV_TO_DOLLARS * 1000 * share_r
        orcl_dol = oracle_r * EV_TO_DOLLARS * 1000 * share_r
        v29_a = (v29_r - a_r_eff) * EV_TO_DOLLARS * 1000 * share_r
        v29_orcl = (v29_r - oracle_r) * EV_TO_DOLLARS * 1000 * share_r
        print(f"  {r:>4}  {n_m:>7,}  ${v29_dol:>+6.1f}  ${a_dol:>+6.1f}  ${orcl_dol:>+8.1f}  "
              f"${v29_a:>+6.1f}  ${v29_orcl:>+8.1f}")

    print(f"\n  v29 pick distribution on trips (sample of 20K):")
    sample_size = min(20000, len(trips_canonical_ids))
    sample_indices = np.random.RandomState(42).choice(len(trips_canonical_ids), sample_size, replace=False)
    n_pick_a = 0; n_pick_b = 0; n_pick_c = 0; n_pick_other = 0
    leaf_ids_t_arr = leaf_ids[mask_trips]
    v29_pick_t = v29_pick_per_leaf[leaf_ids_t_arr]
    for j in sample_indices:
        cid = int(trips_canonical_ids[j])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        pick = int(v29_pick_t[j])
        tr = int(trips_ranks_arr[j])
        is_a = bool(feats.mid_is_pair[pick]) and int(feats.mid_pair_rank[pick]) == tr and int(feats.top_rank[pick]) != tr
        is_b = int(feats.bot_top_pair_rank[pick]) == tr and not (bool(feats.mid_is_pair[pick]) and int(feats.mid_pair_rank[pick]) == tr)
        is_c = int(feats.top_rank[pick]) == tr and bool(feats.mid_is_pair[pick]) and int(feats.mid_pair_rank[pick]) == tr
        if is_a: n_pick_a += 1
        elif is_b: n_pick_b += 1
        elif is_c: n_pick_c += 1
        else: n_pick_other += 1
    print(f"    v29 picks A_paired_mid (top != trip)   : {100*n_pick_a/sample_size:5.1f}%")
    print(f"    v29 picks B_paired_bot                  : {100*n_pick_b/sample_size:5.1f}%")
    print(f"    v29 picks C_top_trip (top == trip, mid==pair) : {100*n_pick_c/sample_size:5.1f}%")
    print(f"    v29 picks something else                : {100*n_pick_other/sample_size:5.1f}%")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"v29 mean regret on TRIPS category: ${regret_t.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips "
          f"(${regret_t.mean()*EV_TO_DOLLARS*1000*mask_trips.mean():+.1f}/1000h whole-grid contribution)")
    print(f"Oracle (A∪B_any∪C) regret on trips: ${oracle_regret.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips "
          f"(${oracle_regret.mean()*EV_TO_DOLLARS*1000*mask_trips.mean():+.1f}/1000h whole-grid contribution)")
    print(f"  → Available headroom from routing-aware ML: "
          f"${(regret_t.mean()-oracle_regret.mean())*EV_TO_DOLLARS*1000*mask_trips.mean():+.1f}/1000h whole-grid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
