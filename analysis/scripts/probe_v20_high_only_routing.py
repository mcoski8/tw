"""
Session 31 — probe what v20's gated suited features actually DO for
high_only hands. The Session 30 v20 win came entirely from the high_only
category (-$413/1000h vs v18e). Distill ranked
``max_suited_pair_high_rank_g`` as the dominant gated feature.

This probe quantifies the routing change so we can write a Rule 5
candidate for STRATEGY_GUIDE.md:

  1. Walk v18e and v20 against their respective feature matrices over
     all 6M canonical hands; record the chosen setting per hand.
  2. Compute oracle argmax + EVs from the full grid (memmap).
  3. Filter to high_only (n_pairs/n_trips/n_quads all 0).
  4. Stratify by `max_suited_pair_high_rank_g` (0, 2-8 = "low", 9-14 by
     rank), and within each stratum report:
       - count of hands
       - v18e / v20 / oracle mid-suited rate (mid card 0 same suit as
         mid card 1)
       - mean EV (oracle / v20 / v18e), $/1000h equivalents
       - mean regret of v18e and v20 vs oracle, and the v20−v18e EV
         delta — i.e. where the gating actually paid us back.
  5. Report stratified setting-distribution shifts: top-5 settings v20
     picks vs v18e picks within the "high suited pair" subset
     (max_suited_pair_high_rank_g >= 9).
  6. Among hands where v20 routes to a SUITED mid but v18e does not,
     spot-check the suit pattern of mid (is the v20 mid using the SAME
     two suited high cards the gated features tag?).

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_v20_high_only_routing.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter
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

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from high_only_v16_residual import decode_setting  # noqa: E402

V18E_PATH = ROOT / "data" / "v18e_dt_model.npz"
V20_PATH = ROOT / "data" / "v20_dt_model.npz"
GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
PA_PATH = ROOT / "data" / "feature_table_aug.parquet"
HA_PATH = ROOT / "data" / "feature_table_high_only_aug.parquet"
TP_PATH = ROOT / "data" / "feature_table_two_pair_aug.parquet"
SG_PATH = ROOT / "data" / "feature_table_suited_aug_gated.parquet"
CANON = ROOT / "data" / "canonical_hands.bin"

CATS = ["high_only", "pair", "quads", "three_pair", "trips", "trips_pair", "two_pair"]
ALPHA_MAP = {c: i for i, c in enumerate(CATS)}


def build_column_data():
    print("loading parquets ...", flush=True)
    t0 = time.time()
    ft = pd.read_parquet(FT_PATH)
    pa = pd.read_parquet(PA_PATH)
    ha = pd.read_parquet(HA_PATH)
    tp = pd.read_parquet(TP_PATH)
    sg = pd.read_parquet(SG_PATH)
    print(f"  loaded in {time.time()-t0:.1f}s", flush=True)
    n = len(ft)
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    cat_id = np.empty(n, dtype=np.int16)
    for i in range(n):
        if n_quads[i] >= 1:
            cat_id[i] = ALPHA_MAP["quads"]
        elif n_trips[i] >= 1 and n_pairs[i] >= 1:
            cat_id[i] = ALPHA_MAP["trips_pair"]
        elif n_trips[i] >= 1:
            cat_id[i] = ALPHA_MAP["trips"]
        elif n_pairs[i] == 3:
            cat_id[i] = ALPHA_MAP["three_pair"]
        elif n_pairs[i] == 2:
            cat_id[i] = ALPHA_MAP["two_pair"]
        elif n_pairs[i] == 1:
            cat_id[i] = ALPHA_MAP["pair"]
        else:
            cat_id[i] = ALPHA_MAP["high_only"]

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
        "n_suited_pairs_total_g": sg["n_suited_pairs_total_g"].to_numpy(),
        "max_suited_pair_high_rank_g": sg["max_suited_pair_high_rank_g"].to_numpy(),
        "max_suited_pair_low_rank_g": sg["max_suited_pair_low_rank_g"].to_numpy(),
        "has_suited_broadway_pair_g": sg["has_suited_broadway_pair_g"].to_numpy(),
        "has_suited_premium_pair_g": sg["has_suited_premium_pair_g"].to_numpy(),
        "n_broadway_in_largest_suit_g": sg["n_broadway_in_largest_suit_g"].to_numpy(),
    }
    return cd, n


def build_X_for_columns(cd, columns):
    n = len(cd[columns[0]])
    X = np.empty((n, len(columns)), dtype=np.int16)
    for j, c in enumerate(columns):
        X[:, j] = cd[c].astype(np.int16, copy=False)
    return X


def load_model(path):
    arr = np.load(path, allow_pickle=True)
    return {
        "children_left": np.asarray(arr["children_left"], dtype=np.int32),
        "children_right": np.asarray(arr["children_right"], dtype=np.int32),
        "feature": np.asarray(arr["feature"], dtype=np.int32),
        "threshold": np.asarray(arr["threshold"], dtype=np.float64),
        "leaf_values": np.asarray(arr["leaf_values"], dtype=np.float32),
        "depth": int(arr["depth"]),
        "n_leaves": int(arr["n_leaves"]),
        "feature_columns": [str(c) for c in arr["feature_columns"]],
    }


def walk_to_leaf(X, model):
    cl = model["children_left"]; cr = model["children_right"]
    feat = model["feature"]; thr = model["threshold"]
    n = X.shape[0]
    node = np.zeros(n, dtype=np.int32)
    active = np.ones(n, dtype=bool)
    for _ in range(int(model["depth"]) + 5):
        if not active.any(): break
        cur = node[active]
        cur_left = cl[cur]
        leaf_mask = cur_left == -1
        cf = feat[cur]; ct = thr[cur]; cright = cr[cur]
        ridx = np.where(active)[0]
        vals = X[ridx, cf]
        gl = vals <= ct
        nn = np.where(gl, cur_left, cright)
        nn = np.where(leaf_mask, cur, nn)
        node[ridx] = nn
        active[ridx] = ~leaf_mask
    return node


def mid_indices_per_setting() -> np.ndarray:
    """Return a (105, 2) int8 array of (mid_a, mid_b) hand-positions per setting_idx."""
    out = np.zeros((105, 2), dtype=np.int8)
    for s in range(105):
        _, (a, b) = decode_setting(s)
        out[s, 0] = a
        out[s, 1] = b
    return out


def settings_use_suited_mid(hands, chosen_idx, mid_pos):
    """For each hand i, return True if hand[mid_pos[chosen_idx[i],0]] and
    hand[mid_pos[chosen_idx[i],1]] share a suit. Vectorised over n hands."""
    a_idx = mid_pos[chosen_idx, 0]
    b_idx = mid_pos[chosen_idx, 1]
    n = hands.shape[0]
    rows = np.arange(n)
    a_card = hands[rows, a_idx]
    b_card = hands[rows, b_idx]
    return (a_card % 4) == (b_card % 4)


def settings_use_suited_mid_with_min_rank(hands, chosen_idx, mid_pos):
    """Like above but also returns the min rank in mid for each hand."""
    a_idx = mid_pos[chosen_idx, 0]
    b_idx = mid_pos[chosen_idx, 1]
    n = hands.shape[0]
    rows = np.arange(n)
    a_card = hands[rows, a_idx]
    b_card = hands[rows, b_idx]
    suited = (a_card % 4) == (b_card % 4)
    a_rank = (a_card // 4) + 2
    b_rank = (b_card // 4) + 2
    min_rank = np.minimum(a_rank, b_rank).astype(np.int8)
    max_rank = np.maximum(a_rank, b_rank).astype(np.int8)
    return suited, min_rank, max_rank


def main() -> int:
    cd, n = build_column_data()
    print(f"  cd built, n={n:,}", flush=True)

    print(f"\nloading models ...", flush=True)
    v18e = load_model(V18E_PATH)
    v20 = load_model(V20_PATH)
    print(f"  v18e leaves={v18e['n_leaves']:,} cols={len(v18e['feature_columns'])}", flush=True)
    print(f"  v20  leaves={v20['n_leaves']:,} cols={len(v20['feature_columns'])}", flush=True)

    print("\nbuilding feature matrices ...", flush=True)
    t0 = time.time()
    X18 = build_X_for_columns(cd, v18e["feature_columns"])
    X20 = build_X_for_columns(cd, v20["feature_columns"])
    print(f"  X18 {X18.shape}  X20 {X20.shape}  ({time.time()-t0:.1f}s)", flush=True)

    print("\nwalking trees ...", flush=True)
    t0 = time.time()
    leaf18 = walk_to_leaf(X18, v18e)
    leaf20 = walk_to_leaf(X20, v20)
    print(f"  walks: {time.time()-t0:.1f}s", flush=True)
    chosen18 = v18e["leaf_values"][leaf18].argmax(axis=1).astype(np.int16)
    chosen20 = v20["leaf_values"][leaf20].argmax(axis=1).astype(np.int16)

    print(f"\nloading oracle grid + canonical hands ...", flush=True)
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    Y = np.asarray(grid.evs[:n])
    hands = np.asarray(ch.hands[:n])
    rows = np.arange(n)
    oracle_idx = Y.argmax(axis=1).astype(np.int16)
    ev_oracle = Y[rows, oracle_idx]
    ev18 = Y[rows, chosen18]
    ev20 = Y[rows, chosen20]

    print(f"\nfull-grid summary (all 6M hands):", flush=True)
    print(f"  oracle mean EV: {ev_oracle.mean():+.4f}", flush=True)
    print(f"  v18e   mean EV: {ev18.mean():+.4f}  regret/1000h = ${(ev_oracle.mean()-ev18.mean())*1000:.2f}", flush=True)
    print(f"  v20    mean EV: {ev20.mean():+.4f}  regret/1000h = ${(ev_oracle.mean()-ev20.mean())*1000:.2f}", flush=True)
    print(f"  v20 over v18e:                              ${(ev20.mean()-ev18.mean())*1000:+.2f}", flush=True)

    # Filter to high_only.
    cat_id = cd["category_id"]
    ho = (cat_id == ALPHA_MAP["high_only"])
    ho_idx = np.where(ho)[0]
    print(f"\nhigh_only subset: {ho.sum():,} hands ({ho.mean()*100:.1f}%)", flush=True)
    print(f"  oracle mean EV: {ev_oracle[ho].mean():+.4f}", flush=True)
    print(f"  v18e   mean EV: {ev18[ho].mean():+.4f}  regret/1000h = ${(ev_oracle[ho].mean()-ev18[ho].mean())*1000:.2f}", flush=True)
    print(f"  v20    mean EV: {ev20[ho].mean():+.4f}  regret/1000h = ${(ev_oracle[ho].mean()-ev20[ho].mean())*1000:.2f}", flush=True)
    print(f"  v20 over v18e:                              ${(ev20[ho].mean()-ev18[ho].mean())*1000:+.2f}", flush=True)

    # Mid-suited rates.
    mid_pos = mid_indices_per_setting()
    suited18, min18, max18 = settings_use_suited_mid_with_min_rank(hands, chosen18, mid_pos)
    suited20, min20, max20 = settings_use_suited_mid_with_min_rank(hands, chosen20, mid_pos)
    suitedO,  minO,  maxO = settings_use_suited_mid_with_min_rank(hands, oracle_idx, mid_pos)

    print(f"\n=== mid-suited rates by category ===", flush=True)
    for cat, ci in ALPHA_MAP.items():
        m = (cat_id == ci)
        if m.sum() == 0:
            continue
        print(f"  {cat:<11} n={m.sum():>8,d}  v18e={suited18[m].mean()*100:5.1f}%  v20={suited20[m].mean()*100:5.1f}%  oracle={suitedO[m].mean()*100:5.1f}%", flush=True)

    print(f"\n=== high_only mid-suited stratified by max_suited_pair_high_rank_g ===", flush=True)
    msphr = cd["max_suited_pair_high_rank_g"]
    print(f"{'max_high':>9}  {'count':>9}  {'v18e_mid_su%':>12}  {'v20_mid_su%':>11}  {'oracle_mid_su%':>14}  "
          f"{'v18e_$/1000':>11}  {'v20_$/1000':>10}  {'gain_$/1000':>11}  {'pop_share%':>10}", flush=True)
    print("-" * 130, flush=True)
    rows_ho = []
    for r in [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
        m = ho & (msphr == r)
        cnt = int(m.sum())
        if cnt == 0:
            continue
        v18e_mid = suited18[m].mean() * 100
        v20_mid = suited20[m].mean() * 100
        oracle_mid = suitedO[m].mean() * 100
        v18e_regret = (ev_oracle[m].mean() - ev18[m].mean()) * 1000
        v20_regret = (ev_oracle[m].mean() - ev20[m].mean()) * 1000
        gain = (ev20[m].mean() - ev18[m].mean()) * 1000
        share = cnt / ho.sum() * 100
        print(f"{r:>9d}  {cnt:>9,}  {v18e_mid:>11.1f}%  {v20_mid:>10.1f}%  {oracle_mid:>13.1f}%  "
              f"{v18e_regret:>11.2f}  {v20_regret:>10.2f}  {gain:>+11.2f}  {share:>10.1f}", flush=True)
        rows_ho.append({
            "msphr": r, "count": cnt, "share": share,
            "v18e_mid_su": v18e_mid, "v20_mid_su": v20_mid, "ora_mid_su": oracle_mid,
            "v18e_regret_per1000": v18e_regret, "v20_regret_per1000": v20_regret,
            "gain_per1000": gain,
        })

    # Among high_only hands where v20 picks suited mid AND v18e doesn't.
    ho_flip = ho & suited20 & ~suited18
    n_flip = int(ho_flip.sum())
    print(f"\n=== Hands where v20 picks SUITED mid and v18e does NOT (among high_only) ===", flush=True)
    print(f"count = {n_flip:,} ({n_flip / ho.sum() * 100:.2f}% of high_only)", flush=True)
    if n_flip:
        v18e_regret_flip = (ev_oracle[ho_flip].mean() - ev18[ho_flip].mean()) * 1000
        v20_regret_flip = (ev_oracle[ho_flip].mean() - ev20[ho_flip].mean()) * 1000
        gain_flip = (ev20[ho_flip].mean() - ev18[ho_flip].mean()) * 1000
        print(f"  v18e regret: ${v18e_regret_flip:.2f}/1000h", flush=True)
        print(f"  v20 regret:  ${v20_regret_flip:.2f}/1000h", flush=True)
        print(f"  v20 - v18e gain: ${gain_flip:+.2f}/1000h on this slice", flush=True)
        print(f"  total contribution to high_only EV gain: ${(ev20[ho_flip].sum()-ev18[ho_flip].sum())*1000/ho.sum():+.2f}/1000h", flush=True)
        # Distribution of mid min-rank in flip slice
        print(f"  v20 mid min-rank: mean={min20[ho_flip].mean():.2f}, median={int(np.median(min20[ho_flip]))}", flush=True)
        print(f"  v20 mid max-rank: mean={max20[ho_flip].mean():.2f}, median={int(np.median(max20[ho_flip]))}", flush=True)

    # Distribution of v20 chosen settings on high_only & high suited pair (msphr >= 9)
    print(f"\n=== top-10 v20 settings on high_only with max_suited_pair_high_rank_g >= 9 ===", flush=True)
    m = ho & (msphr >= 9)
    cnt_m = int(m.sum())
    if cnt_m:
        v20_settings = chosen20[m]
        v18_settings = chosen18[m]
        ora_settings = oracle_idx[m]
        print(f"{cnt_m:,} hands. v20 setting mode-share / v18e setting mode-share / oracle setting mode-share:", flush=True)
        c20 = Counter(v20_settings.tolist()).most_common(10)
        c18 = Counter(v18_settings.tolist()).most_common(10)
        cor = Counter(ora_settings.tolist()).most_common(10)
        print(f"  v20: {c20}", flush=True)
        print(f"  v18e: {c18}", flush=True)
        print(f"  oracle: {cor}", flush=True)

    # Now break the slice further: msphr >= 9 AND max_suited_pair_low_rank_g >= 9
    # (BOTH cards >= 9). This is the "high suited pair" Rule 5 candidate.
    msplr = cd["max_suited_pair_low_rank_g"]
    print(f"\n=== high_only with BOTH suited cards >= 9 (msphr>=9 AND msplr>=9) ===", flush=True)
    rule_m = ho & (msphr >= 9) & (msplr >= 9)
    cnt_r = int(rule_m.sum())
    if cnt_r:
        share_r = cnt_r / n * 100
        v18e_mid_r = suited18[rule_m].mean() * 100
        v20_mid_r = suited20[rule_m].mean() * 100
        ora_mid_r = suitedO[rule_m].mean() * 100
        v18e_regret_r = (ev_oracle[rule_m].mean() - ev18[rule_m].mean()) * 1000
        v20_regret_r = (ev_oracle[rule_m].mean() - ev20[rule_m].mean()) * 1000
        gain_r = (ev20[rule_m].mean() - ev18[rule_m].mean()) * 1000
        print(f"  count = {cnt_r:,} ({share_r:.2f}% of all hands, {cnt_r / ho.sum() * 100:.2f}% of high_only)", flush=True)
        print(f"  v18e mid-suited: {v18e_mid_r:.1f}%  v20 mid-suited: {v20_mid_r:.1f}%  oracle mid-suited: {ora_mid_r:.1f}%", flush=True)
        print(f"  v18e regret: ${v18e_regret_r:.2f}/1000h", flush=True)
        print(f"  v20 regret:  ${v20_regret_r:.2f}/1000h", flush=True)
        print(f"  gain on slice: ${gain_r:+.2f}/1000h × ({share_r:.2f}% pop) = ${gain_r * share_r / 100:+.2f}/1000h global", flush=True)

    # Also: msphr in [10..14] alone.
    print(f"\n=== high_only stratified by max_suited_pair_high_rank_g (msphr) thresholds ===", flush=True)
    for thr in [9, 10, 11, 12, 13, 14]:
        m = ho & (msphr >= thr)
        if m.sum() == 0:
            continue
        share = m.sum() / n * 100
        v18e_mid = suited18[m].mean() * 100
        v20_mid = suited20[m].mean() * 100
        ora_mid = suitedO[m].mean() * 100
        v18e_regret = (ev_oracle[m].mean() - ev18[m].mean()) * 1000
        v20_regret = (ev_oracle[m].mean() - ev20[m].mean()) * 1000
        gain = (ev20[m].mean() - ev18[m].mean()) * 1000
        print(f"  msphr>={thr:2d}: n={m.sum():>8,}  pop={share:5.2f}%  "
              f"v18e_mid={v18e_mid:5.1f}% v20_mid={v20_mid:5.1f}% ora_mid={ora_mid:5.1f}%  "
              f"v18e_regret=${v18e_regret:>7.2f} v20_regret=${v20_regret:>7.2f} gain=${gain:>+6.2f}/1000h  "
              f"global_gain=${gain*share/100:>+5.2f}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
