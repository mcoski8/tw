"""
Session 36 — distill v29's tree on the pair category.

This is the round-2 pair audit. v29 added 4 pair-gated v2 features
(`pair_r4_*_g`) targeting the Rule-4-bot suit profile axis identified by
Session 35's distill_v27_pair.py. Headline: pair dropped $1,771 → $1,674
within-pair (−$97), pct_opt 53.9% → 55.0%. The whole-grid contribution
of pair was $825 (v27) → $780 (v29) — about $45 captured.

The key question for Session 36: how much of the v27→oracle KK/AA gap
that motivated v29 has actually been closed, vs how much remains?

Recap of v27's diagnostic:
  Rule 4 alone on KK/AA   : $949/1000h regret = $68/1000h whole-grid
  v27 actual on KK/AA     : $1,236/1000h regret = $89/1000h whole-grid
  Oracle (R4 OR DS-bot)   : $362/1000h regret = $26/1000h whole-grid

v27 was $20 WORSE than Rule 4 on KK/AA. The Rule-4 → oracle gap was
$42/1000h whole-grid; v27 captured *negative* of it.

Compute on v29:
  - v29 actual regret on KK/AA (vs BR)
  - Rule-4 alone (= ev_a_mid in probe)
  - Oracle (Rule 4 OR DS-bot, max)
  - The capture ratio of the Rule-4 → oracle gap
  - v29's pick distribution on KK/AA (Rule-4 / DS-bot / other)

If a notable chunk of the gap remains → design pair_r4 round-2 features
(e.g. alt-routing mid quality conditioned on Rule-4-bot suit profile,
KK/AA-specific gating refinements).

If gap is mostly closed → pivot to trips_aug_gated (8th gating template
instance, $110 share).

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/distill_v29_pair.py
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
    """For both ALL hands and the target subset, aggregate per-leaf stats and propagate."""
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


def main():
    print("=" * 80)
    print("Session 36: v29 distillation focused on pair category (round 2 audit)")
    print("=" * 80)

    print(f"\n[1/7] Loading model {MODEL_PATH} ...", flush=True)
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

    print(f"\n[2/7] Building 73-col feature matrix X for all 6M hands ...", flush=True)
    t0 = time.time()
    X, n_hands = build_X()
    print(f"  X={X.shape}  ({X.nbytes/1e6:.0f} MB)  ({time.time()-t0:.1f}s)")

    print("\n[3/7] Identifying pair mask via base feature_table ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=[
        "canonical_id", "n_pairs", "n_trips", "n_quads", "pair_high_rank",
        "n_broadway", "n_low", "connectivity",
        "suit_max", "suit_2nd", "suit_3rd",
    ])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    pair_high = ft["pair_high_rank"].to_numpy()
    mask_pair = (n_pairs == 1) & (n_trips == 0) & (n_quads == 0)
    mask_kkaa = mask_pair & ((pair_high == 13) | (pair_high == 14))
    print(f"  pair hands: {int(mask_pair.sum()):>10,}  ({100*mask_pair.mean():.2f}%)")
    print(f"    of which KK/AA: {int(mask_kkaa.sum()):>10,}  "
          f"({100*mask_kkaa.mean():.2f}% of grid, "
          f"{100*mask_kkaa.sum()/mask_pair.sum():.1f}% of pair)")

    print(f"\n[4/7] Loading oracle grid (memmap) ...", flush=True)
    t0 = time.time()
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_hands])
    print(f"  Y={Y.shape}  ({time.time()-t0:.1f}s)")

    print(f"\n[5/7] Walking all {n_hands:,} hands to leaf ...", flush=True)
    t0 = time.time()
    leaf_ids = walk_each_hand_to_leaf(X, model)
    print(f"  walk: {time.time()-t0:.1f}s  unique leaves hit: {len(np.unique(leaf_ids)):,}")

    K = Y.shape[1]
    count_all, sumY_all, sumY2_all, count_p, sumY_p, sumY2_p, depth_arr = compute_per_node_stats(
        leaf_ids, mask_pair, Y, n_nodes, K, model)

    print("\nROOT SANITY:")
    print(f"  root count_all = {count_all[0]:,.0f}  (expect {n_hands:,})")
    print(f"  root count_p   = {count_p[0]:,.0f}   (expect {int(mask_pair.sum()):,})")

    impurity_all = compute_node_impurity(count_all, sumY_all, sumY2_all)
    impurity_p = compute_node_impurity(count_p, sumY_p, sumY2_p)
    print(f"  root impurity_all = {impurity_all[0]:.4f}")
    print(f"  root impurity_p   = {impurity_p[0]:.4f}")

    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]
    is_internal = cl != -1

    # ---------- Per-leaf miss stats on pair ----------
    print(f"\n[6/7] Per-leaf v29 vs BR on pair (top miss leaves)", flush=True)
    leaf_mask = cl == -1
    leaf_indices = np.where(leaf_mask)[0]

    leaf_ids_p = leaf_ids[mask_pair]
    Y_p = np.asarray(Y[mask_pair], dtype=np.float32)
    best_ev_p = Y_p.max(axis=1).astype(np.float64)
    lv = model["leaf_values"]
    v29_pick_per_leaf = lv.argmax(axis=1)
    v29_ev_p = Y_p[np.arange(Y_p.shape[0]), v29_pick_per_leaf[leaf_ids_p]].astype(np.float64)
    regret_p = best_ev_p - v29_ev_p

    print(f"  pair mean v29 EV: {v29_ev_p.mean():+.4f}  BR EV: {best_ev_p.mean():+.4f}  "
          f"regret: {regret_p.mean():+.4f}  (${regret_p.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h)")

    leaf_count_p = np.bincount(leaf_ids_p, minlength=n_nodes)
    leaf_total_regret_p = np.bincount(leaf_ids_p, weights=regret_p, minlength=n_nodes)
    leaf_sum_brev = np.bincount(leaf_ids_p, weights=best_ev_p, minlength=n_nodes)
    leaf_sum_brev_sq = np.bincount(leaf_ids_p, weights=best_ev_p * best_ev_p, minlength=n_nodes)

    eligible = leaf_count_p >= 50
    print(f"  leaves with >=50 pair hands: {int(eligible.sum()):,}/{int(leaf_mask.sum()):,}")
    leaf_order = np.argsort(-(leaf_total_regret_p * eligible))[:30]

    print(f"\n  TOP 30 PAIR MISS LEAVES (by total within-leaf regret):")
    print(f"  {'rank':>4}  {'leaf':>8}  {'n_p':>8}  {'mean_reg':>10}  {'tot_reg':>10}  "
          f"{'mean_brev':>10}  {'std_brev':>10}  {'v29_pick':>9}")
    for rank, leaf in enumerate(leaf_order, 1):
        n_l = int(leaf_count_p[leaf])
        if n_l < 50: continue
        mean_reg = leaf_total_regret_p[leaf] / n_l
        tot_reg = leaf_total_regret_p[leaf]
        mean_brev = leaf_sum_brev[leaf] / n_l
        var_br = leaf_sum_brev_sq[leaf] / n_l - mean_brev ** 2
        std_br = float(np.sqrt(max(var_br, 0)))
        print(f"  {rank:>4}  {leaf:>8}  {n_l:>8d}  {mean_reg:>+10.4f}  {tot_reg:>+10.2f}  "
              f"{mean_brev:>+10.4f}  {std_br:>10.4f}  {v29_pick_per_leaf[leaf]:>9d}")

    # ---------- Feature importance restricted to pair ----------
    print(f"\n  FEATURE IMPORTANCE on pair-restricted MSE reduction (top 25):")
    reductions_p = np.zeros(n_nodes, dtype=np.float64)
    for node in np.where(is_internal)[0]:
        L = cl[node]; R = cr[node]
        nN = count_p[node]; nL = count_p[L]; nR = count_p[R]
        if nN < 50:
            continue
        reductions_p[node] = nN * impurity_p[node] - nL * impurity_p[L] - nR * impurity_p[R]
    feat_imp = np.zeros(len(feature_columns), dtype=np.float64)
    for node in np.where(is_internal)[0]:
        feat_imp[feat[node]] += reductions_p[node]
    feat_total = feat_imp.sum()
    fi_order = np.argsort(-feat_imp)
    print(f"  {'rank':>4}  {'feature':<40}  {'pct':>7}  {'reduction':>14}")
    for rank, idx in enumerate(fi_order[:25], 1):
        if feat_imp[idx] <= 0: continue
        pct = 100.0 * feat_imp[idx] / feat_total if feat_total > 0 else 0
        print(f"  {rank:>4}  {feature_columns[idx]:<40}  {pct:>6.2f}%  {feat_imp[idx]:>14.0f}")

    # ---------- KK/AA upper-bound capture analysis ----------
    print(f"\n[7/7] KK/AA $42 upper-bound capture analysis (round 2 — v29)", flush=True)
    print(f"\n  Loading canonical hands for KK/AA-specific routing analysis ...")
    ch = read_canonical_hands(CANON_PATH, mode="memmap")

    print(f"  Loading KK/AA Rule-4 boundary probe CSV ...")
    kk_aa_probe = pd.read_csv(ROOT / "data" / "kk_aa_rule4_probe.csv")
    kk_aa_probe = kk_aa_probe.set_index("canonical_id")
    kk_aa_probe_cids = kk_aa_probe.index.to_numpy()
    print(f"  KK/AA hands in probe: {len(kk_aa_probe_cids):,}")

    # Map: canonical_id → v29 picked EV
    kk_aa_mask_arr = np.zeros(n_hands, dtype=bool)
    kk_aa_mask_arr[kk_aa_probe_cids] = True
    # v29's pick on KK/AA
    kk_aa_v29_pick = v29_pick_per_leaf[leaf_ids[kk_aa_mask_arr]]
    Y_kkaa = np.asarray(Y[kk_aa_mask_arr], dtype=np.float32)
    v29_ev_kkaa = Y_kkaa[np.arange(Y_kkaa.shape[0]), kk_aa_v29_pick].astype(np.float64)
    br_ev_kkaa = Y_kkaa.max(axis=1).astype(np.float64)
    v29_regret_kkaa = br_ev_kkaa - v29_ev_kkaa

    # Reorder probe to match the canonical-id order in our scan (probe is already in order)
    assert (kk_aa_probe_cids == np.sort(kk_aa_probe_cids)).all()

    rule4_ev_kkaa = kk_aa_probe.loc[kk_aa_probe_cids, "ev_a_mid"].to_numpy()
    bds_ev_kkaa = kk_aa_probe.loc[kk_aa_probe_cids, "ev_b_bot_ds"].to_numpy()
    oracle_r4_or_bds = np.where(
        ~np.isnan(bds_ev_kkaa) & (bds_ev_kkaa > rule4_ev_kkaa),
        bds_ev_kkaa, rule4_ev_kkaa
    )

    rule4_regret_kkaa = br_ev_kkaa - rule4_ev_kkaa
    oracle_r4bds_regret_kkaa = br_ev_kkaa - oracle_r4_or_bds

    n_total = n_hands
    n_kkaa = len(kk_aa_probe_cids)
    print(f"\n  Mean per-hand regrets vs BR on the {n_kkaa:,} KK/AA hands:")
    print(f"    Rule 4 (always mid)              : {rule4_regret_kkaa.mean():+.4f} EV")
    print(f"    Oracle (Rule 4 OR DS-bot, max)   : {oracle_r4bds_regret_kkaa.mean():+.4f} EV")
    print(f"    v29 actual                       : {v29_regret_kkaa.mean():+.4f} EV")
    print(f"    BR (zero by definition)          : 0.0000")
    print()
    pop_share = n_kkaa / n_total
    def grid_dollars(r):
        return r * EV_TO_DOLLARS * 1000 * pop_share
    print(f"  Whole-grid contribution from KK/AA category at $/1000h:")
    print(f"    Rule 4 (always mid)              : ${grid_dollars(rule4_regret_kkaa.mean()):+,.1f}")
    print(f"    Oracle (Rule 4 OR DS-bot)        : ${grid_dollars(oracle_r4bds_regret_kkaa.mean()):+,.1f}")
    print(f"    v29 actual                       : ${grid_dollars(v29_regret_kkaa.mean()):+,.1f}")
    print()

    # The CRITICAL question: what fraction of the "Rule 4 → oracle-r4bds" gap does v29 close?
    rule4_to_oracle_gap = rule4_regret_kkaa.mean() - oracle_r4bds_regret_kkaa.mean()
    rule4_to_v29_gap = rule4_regret_kkaa.mean() - v29_regret_kkaa.mean()
    print(f"  RULE-4 -> ORACLE GAP (the '$42/1000h' upper bound at KK/AA level):")
    print(f"    EV/hand: {rule4_to_oracle_gap:+.4f}  (= ${grid_dollars(rule4_to_oracle_gap):+,.1f}/1000h whole-grid contribution)")
    print(f"  RULE-4 -> v29 GAP (= what v29 captures relative to Rule 4):")
    print(f"    EV/hand: {rule4_to_v29_gap:+.4f}  (= ${grid_dollars(rule4_to_v29_gap):+,.1f}/1000h whole-grid contribution)")
    if rule4_to_oracle_gap > 1e-9:
        capture_pct = 100.0 * rule4_to_v29_gap / rule4_to_oracle_gap
        print(f"  v29 CAPTURE RATIO of the Rule-4 → oracle gap : {capture_pct:.1f}%")
        remaining = oracle_r4bds_regret_kkaa.mean() - v29_regret_kkaa.mean()
        if remaining > 0:
            print(f"  Remaining gap for v29 to oracle               : ${grid_dollars(remaining):+,.1f}/1000h whole-grid")
        else:
            print(f"  v29 already BEATS the Rule-4-OR-DS-bot oracle! "
                  f"(by {-remaining:.4f} EV/hand = ${-grid_dollars(-remaining):+,.1f}/1000h whole-grid)")
            print(f"  This means v29 picks routings outside {{Rule 4, DS-bot}} on a meaningful subset of KK/AA.")
    print()

    # Pct of KK/AA hands where v29 picks Rule 4 vs DS-bot vs neither
    print(f"  v29's pick distribution on KK/AA:")
    n_pick_rule4 = 0
    n_pick_ds_bot = 0
    n_pick_other = 0
    sample_size = min(20000, n_kkaa)
    sample_indices = np.random.RandomState(42).choice(n_kkaa, sample_size, replace=False)
    for j in sample_indices:
        cid = int(kk_aa_probe_cids[j])
        hand = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(hand)
        pick = int(kk_aa_v29_pick[j])
        pr = int(kk_aa_probe.loc[cid, "pair_rank"])
        if bool(feats.mid_is_pair[pick]) and int(feats.mid_pair_rank[pick]) == pr:
            n_pick_rule4 += 1
        elif int(feats.bot_top_pair_rank[pick]) == pr and int(feats.bot_suit_profile[pick]) == SUIT_PROFILE_DS:
            n_pick_ds_bot += 1
        else:
            n_pick_other += 1
    print(f"    (sample of {sample_size:,} hands)")
    print(f"    v29 picks Rule-4 (mid=KK/AA)        : {100*n_pick_rule4/sample_size:5.1f}%")
    print(f"    v29 picks DS-bot routing             : {100*n_pick_ds_bot/sample_size:5.1f}%")
    print(f"    v29 picks something else             : {100*n_pick_other/sample_size:5.1f}%")
    print()

    # ---------- Stratify KK/AA regret by Rule-4-bot suit profile ----------
    print(f"  v29 regret on KK/AA stratified by Rule-4-bot suit profile:")
    # The pair_r4_bot_suit_profile_g feature column index
    suit_profile_col = FEATURE_COLUMNS.index("pair_r4_bot_suit_profile_g")
    profile_vals = X[kk_aa_mask_arr, suit_profile_col]
    profile_names = {1: "rainbow", 2: "single-suited", 3: "double-suited",
                     4: "three-of-suit", 5: "four-of-suit", 0: "invalid"}
    for prof_code in sorted(profile_names.keys()):
        m = profile_vals == prof_code
        n_m = int(m.sum())
        if n_m == 0:
            continue
        v29_r = v29_regret_kkaa[m].mean()
        rule4_r = rule4_regret_kkaa[m].mean()
        oracle_r = oracle_r4bds_regret_kkaa[m].mean()
        # contribution to whole-grid in $/1000h
        share = n_m / n_total
        v29_dol = v29_r * EV_TO_DOLLARS * 1000 * share
        rule4_dol = rule4_r * EV_TO_DOLLARS * 1000 * share
        oracle_dol = oracle_r * EV_TO_DOLLARS * 1000 * share
        gap_dol = (v29_r - oracle_r) * EV_TO_DOLLARS * 1000 * share
        print(f"    profile={prof_code} ({profile_names[prof_code]:<14}) n={n_m:>6,} ({100*n_m/n_kkaa:>5.1f}% of KK/AA)  "
              f"v29 ${v29_dol:>+6.1f}  rule4 ${rule4_dol:>+6.1f}  oracle ${oracle_dol:>+6.1f}  "
              f"v29-oracle ${gap_dol:>+5.1f}/1000h whole-grid")
    print()

    # ---------- Summary ----------
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"v29 mean regret on PAIR category: ${regret_p.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-pair "
          f"(${regret_p.mean()*EV_TO_DOLLARS*1000*mask_pair.mean():+.1f}/1000h whole-grid contribution)")
    print(f"v29 mean regret on KK/AA subset:  ${v29_regret_kkaa.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-KK/AA "
          f"(${grid_dollars(v29_regret_kkaa.mean()):+.1f}/1000h whole-grid contribution)")
    print(f"\nRecap of v27 (Session 35 baseline):")
    print(f"  v27 KK/AA whole-grid: $89/1000h  Rule-4: $68  Oracle: $26")
    print(f"  v27 was $20 WORSE than Rule 4 on KK/AA.")
    print(f"v29 KK/AA whole-grid (above): see [7/7] block.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
