"""
Session 28 — high_only deep-dive: find the archetypes where v16 still
bleeds. high_only is 31% of v16's total residual ($3,785/1000h × 20.4%
share). If we can tag a sub-cluster with a clean signal, it becomes a v18
candidate rule.

Pipeline:
  1. Build the same 37-feature X for all hands (reuse distill helpers if
     present; do inline for self-containedness).
  2. Walk v16's tree to get chosen_idx per hand (argmax of leaf_value_vec).
  3. Filter to high_only (cat == 0). Compute regret = oracle_ev - chosen_ev.
  4. Cluster by (suit_dist_tuple, n_broadway, connectivity, has_ace_singleton,
     has_king_singleton). Aggregate count + sum_regret + mean_regret.
  5. Print the top-30 clusters by total_regret (count × mean) — those are
     where v16's leaf prediction is farthest from oracle argmax in
     high-volume populations.
  6. For the top-3 clusters, dump the typical v16 chosen setting vs oracle
     argmax setting (mode of each), so the human reader can see what
     v16 is picking and what it should be picking.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/high_only_v16_residual.py
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

MODEL_PATH = ROOT / "data" / "v16_dt_model.npz"
GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
PA_PATH = ROOT / "data" / "feature_table_aug.parquet"
HA_PATH = ROOT / "data" / "feature_table_high_only_aug.parquet"
TP_PATH = ROOT / "data" / "feature_table_two_pair_aug.parquet"
CANON = ROOT / "data" / "canonical_hands.bin"

CATS = ["high_only", "pair", "quads", "three_pair", "trips", "trips_pair", "two_pair"]
ALPHA_MAP = {c: i for i, c in enumerate(CATS)}


def categorize_row(np_arr: np.ndarray, n_pairs_arr, n_trips_arr, n_quads_arr) -> np.ndarray:
    out = np.empty(len(np_arr), dtype=np.int16)
    for i in range(len(np_arr)):
        if n_quads_arr[i] >= 1:
            out[i] = ALPHA_MAP["quads"]
        elif n_trips_arr[i] >= 1 and n_pairs_arr[i] >= 1:
            out[i] = ALPHA_MAP["trips_pair"]
        elif n_trips_arr[i] >= 1:
            out[i] = ALPHA_MAP["trips"]
        elif n_pairs_arr[i] == 3:
            out[i] = ALPHA_MAP["three_pair"]
        elif n_pairs_arr[i] == 2:
            out[i] = ALPHA_MAP["two_pair"]
        elif n_pairs_arr[i] == 1:
            out[i] = ALPHA_MAP["pair"]
        else:
            out[i] = ALPHA_MAP["high_only"]
    return out


def build_X(model_columns: list[str]):
    print("loading parquets ...", flush=True)
    ft = pd.read_parquet(FT_PATH)
    pa = pd.read_parquet(PA_PATH)
    ha = pd.read_parquet(HA_PATH)
    tp = pd.read_parquet(TP_PATH)
    n = len(ft)
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    cat_id = categorize_row(np.empty(n), n_pairs, n_trips, n_quads)
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
    }
    X = np.empty((n, len(model_columns)), dtype=np.int16)
    for j, c in enumerate(model_columns):
        X[:, j] = cd[c].astype(np.int16, copy=False)
    return X, cd


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


# Decode setting_index 0..104 to (top_idx 0..6, mid_combo_idx 0..14)
# enumeration order: for top_idx in 0..6: for mid in C(remaining 6, 2)
def decode_setting(setting_idx: int) -> tuple[int, tuple[int, int]]:
    """Return (top_idx, (mid_a_idx, mid_b_idx)) where indices are 0..6
    refer to position in the sorted 7-card hand."""
    top_idx = setting_idx // 15
    mid_combo = setting_idx % 15
    rest = [i for i in range(7) if i != top_idx]
    # 15 = C(6,2). enumerate combos in lex order.
    pairs = []
    for a in range(6):
        for b in range(a + 1, 6):
            pairs.append((rest[a], rest[b]))
    return top_idx, pairs[mid_combo]


def hand_str(hand_bytes: np.ndarray) -> str:
    RANKS = "23456789TJQKA"
    SUITS = "cdhs"
    return " ".join(f"{RANKS[(b // 4)]}{SUITS[b % 4]}" for b in hand_bytes)


def setting_str(hand_bytes: np.ndarray, setting_idx: int) -> str:
    top_idx, (mid_a, mid_b) = decode_setting(setting_idx)
    bot_idx = sorted([i for i in range(7) if i not in {top_idx, mid_a, mid_b}])
    RANKS = "23456789TJQKA"
    SUITS = "cdhs"
    def card(i):
        b = hand_bytes[i]
        return f"{RANKS[(b // 4)]}{SUITS[b % 4]}"
    top = card(top_idx)
    mid = " ".join(card(i) for i in (mid_a, mid_b))
    bot = " ".join(card(i) for i in bot_idx)
    return f"top={top} mid=[{mid}] bot=[{bot}]"


def main() -> int:
    print(f"loading model ...", flush=True)
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
    }
    print(f"  leaves={model['n_leaves']:,}", flush=True)

    X, cd = build_X(feature_columns)
    n = X.shape[0]
    print(f"  X={X.shape}", flush=True)

    print(f"loading grid ...", flush=True)
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    Y = np.asarray(grid.evs[:n])
    hands_arr = np.asarray(ch.hands[:n])

    print(f"walking tree ...", flush=True)
    leaf_ids = walk_to_leaf(X, model)
    print(f"computing chosen_idx + regret ...", flush=True)
    leaf_values = model["leaf_values"]
    chosen_idx = leaf_values[leaf_ids].argmax(axis=1).astype(np.int16)
    oracle_idx = Y.argmax(axis=1).astype(np.int16)
    chosen_ev = Y[np.arange(n), chosen_idx]
    oracle_ev = Y[np.arange(n), oracle_idx]
    regret = (oracle_ev - chosen_ev).astype(np.float32)

    cat_id = cd["category_id"]
    high_only_mask = cat_id == ALPHA_MAP["high_only"]
    n_ho = int(high_only_mask.sum())
    print(f"\nhigh_only hands: {n_ho:,}  ({100.0 * n_ho / n:.2f}%)", flush=True)
    ho_regret = regret[high_only_mask]
    print(f"  v16 high_only mean regret: {ho_regret.mean():+.4f}  ≈ ${ho_regret.mean()*10000:+,.0f}/1000h within high_only", flush=True)

    # Sub-cluster signature on the high_only subset.
    # signature key: (suit_max, suit_2nd, suit_3rd, suit_4th, n_broadway, connectivity, has_ace_singleton, has_king_singleton)
    suit_max = cd["suit_max"]
    suit_2nd = cd["suit_2nd"]
    suit_3rd = cd["suit_3rd"]
    suit_4th = cd["suit_4th"]
    n_broadway = cd["n_broadway"]
    connectivity = cd["connectivity"]
    has_ace = cd["has_ace_singleton"]
    has_king = cd["has_king_singleton"]
    can_ds = cd["can_make_ds_bot"]
    n_low = cd["n_low"]

    print(f"\nbuilding cluster keys ...", flush=True)
    rows = np.where(high_only_mask)[0]
    df = pd.DataFrame({
        "suit_dist": [
            f"{suit_max[i]}+{suit_2nd[i]}+{suit_3rd[i]}+{suit_4th[i]}"
            for i in rows
        ],
        "n_broadway": n_broadway[rows],
        "connectivity": connectivity[rows],
        "has_ace_singleton": has_ace[rows],
        "has_king_singleton": has_king[rows],
        "can_ds_bot": can_ds[rows],
        "n_low": n_low[rows],
        "regret": regret[rows],
        "chosen_idx": chosen_idx[rows],
        "oracle_idx": oracle_idx[rows],
        "row_idx": rows,
    })

    # Cluster by 4 keys: suit_dist + n_broadway + can_ds_bot + has_ace_singleton.
    # That keeps clusters big enough to be statistically meaningful.
    grp = df.groupby(["suit_dist", "n_broadway", "can_ds_bot", "has_ace_singleton"], sort=False).agg(
        count=("regret", "size"),
        mean_regret=("regret", "mean"),
        sum_regret=("regret", "sum"),
    ).reset_index()
    grp["pct_of_high_only"] = 100.0 * grp["count"] / n_ho
    grp["pct_of_total_high_only_regret"] = 100.0 * grp["sum_regret"] / float(ho_regret.sum())
    grp = grp.sort_values("sum_regret", ascending=False)

    print(f"\n=== TOP 30 high_only CLUSTERS BY TOTAL REGRET (within high_only) ===\n", flush=True)
    pd.set_option("display.max_rows", 40)
    pd.set_option("display.width", 200)
    print(grp.head(30).to_string(index=False), flush=True)

    # For the top-3 worst clusters, dump 5 example hands with v16's pick vs oracle pick.
    print(f"\n\n=== EXAMPLES FROM TOP-3 CLUSTERS ===", flush=True)
    for cluster_rank in range(min(3, len(grp))):
        row = grp.iloc[cluster_rank]
        print(f"\n--- Cluster #{cluster_rank+1}: suit_dist={row['suit_dist']}  n_broadway={row['n_broadway']}  can_ds_bot={row['can_ds_bot']}  has_ace_singleton={row['has_ace_singleton']}", flush=True)
        print(f"    count={row['count']:,}  mean_regret={row['mean_regret']:.4f}  sum_regret={row['sum_regret']:.1f}  share_of_high_only_regret={row['pct_of_total_high_only_regret']:.1f}%", flush=True)
        # Filter df to this cluster, sort by regret desc, take 5 examples.
        sub = df[
            (df["suit_dist"] == row["suit_dist"])
            & (df["n_broadway"] == row["n_broadway"])
            & (df["can_ds_bot"] == row["can_ds_bot"])
            & (df["has_ace_singleton"] == row["has_ace_singleton"])
        ].nlargest(5, "regret")
        # Mode of v16 chosen_idx and oracle_idx in this cluster
        chosen_mode = Counter(df[
            (df["suit_dist"] == row["suit_dist"])
            & (df["n_broadway"] == row["n_broadway"])
            & (df["can_ds_bot"] == row["can_ds_bot"])
            & (df["has_ace_singleton"] == row["has_ace_singleton"])
        ]["chosen_idx"]).most_common(3)
        oracle_mode = Counter(df[
            (df["suit_dist"] == row["suit_dist"])
            & (df["n_broadway"] == row["n_broadway"])
            & (df["can_ds_bot"] == row["can_ds_bot"])
            & (df["has_ace_singleton"] == row["has_ace_singleton"])
        ]["oracle_idx"]).most_common(3)
        print(f"    v16 chosen_idx mode (top 3): {chosen_mode}", flush=True)
        print(f"    oracle    idx mode (top 3): {oracle_mode}", flush=True)
        print(f"    Worst-regret example hands in this cluster:", flush=True)
        for _, ex in sub.iterrows():
            ri = int(ex["row_idx"])
            hb = hands_arr[ri].astype(np.uint8)
            v16_str = setting_str(hb, int(ex["chosen_idx"]))
            ora_str = setting_str(hb, int(ex["oracle_idx"]))
            print(f"      hand {hand_str(hb)} | regret={ex['regret']:.3f}", flush=True)
            print(f"        v16   : {v16_str}", flush=True)
            print(f"        oracle: {ora_str}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
