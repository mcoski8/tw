"""
Pre-test: where does v3 actually bleed money, and what archetypes dominate?

Following the Session 23 plan agreed with Gemini:
  1. For every hand in the 50K oracle grid, compute Δ_global = EV(oracle) - EV(v3),
     averaged across the 4 opponent profiles.
  2. Take the top-bleed hands (top 5% / 10% by Δ_global) — this is where rule
     work pays.
  3. For each top-bleed hand, compute Δ_local = a simple local-mid-strength
     comparison (does v3's mid LOOK stronger to a human than oracle's mid?).
       - Trap zone:  |Δ_local| small.  v3's choice locally looked fine, but
                     oracle wins globally via cascade into bot.
       - Confident blunder: Δ_local > 0.  v3's mid looked locally stronger,
                     but oracle's globally-weaker-mid wins via cascade.
  4. Cluster top-bleed hands by (category, routing change v3→oracle,
     bot-suit-profile change). Report population × mean-bleed × dominant
     routing pattern.

Outputs:
  - Console: bleed-by-archetype tables.
  - data/v3_bleed_zones.parquet: per-hand record for further analysis.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from encode_rules import strategy_v3  # noqa: E402
from tw_analysis.features import (  # noqa: E402
    decode_tier_positions,
    hand_features_scalar,
)

GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"
OUT_PATH = ROOT / "data" / "v3_bleed_zones.parquet"

CATEGORY_NAMES = {
    0: "high_only",
    1: "pair",
    2: "two_pair",
    3: "three_pair",
    4: "trips",
    5: "trips_pair",
    6: "quads",
}


def mid_strength(rank_a: int, rank_b: int, suited: bool) -> int:
    """
    Simple local-mid-strength metric for a 2-card hole.
    Larger = looks stronger to a human at first glance.

    Pair >> any unpaired hand. Within unpaired: higher cards > lower,
    suited > unsuited.

    NOTE: this is intentionally crude — it's the "vibes-level" eval a
    human does in <5 seconds. The whole point of the trap-zone analysis
    is that this simple metric MISSES bot-cascade effects.
    """
    high, low = max(rank_a, rank_b), min(rank_a, rank_b)
    if rank_a == rank_b:
        return 1000 + 10 * high  # any pair beats any non-pair
    return 100 * high + low + (5 if suited else 0)


def bot_suit_profile(suits: tuple[int, int, int, int]) -> str:
    """Classify a 4-card suit profile."""
    counts = sorted(Counter(suits).values(), reverse=True)
    while len(counts) < 4:
        counts.append(0)
    if counts[0] == 4:
        return "monosuit"  # 4 of a suit — bad in Omaha 2+3
    if counts[0] == 3:
        return "3-suited"  # 3 of a suit — bad
    if counts[0] == 2 and counts[1] == 2:
        return "double_suited"  # best
    if counts[0] == 2 and counts[1] == 1:
        return "single_suited"
    return "rainbow"


def bot_max_run(ranks: tuple[int, int, int, int]) -> int:
    """Longest consecutive run within the 4 bot ranks."""
    rs = sorted(set(ranks))
    if not rs:
        return 0
    best = cur = 1
    for i in range(1, len(rs)):
        if rs[i] == rs[i - 1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def routing_label(hand: np.ndarray, setting_index: int) -> str:
    """
    Classify the qualitative routing of a setting given the hand structure.
    Returns a short label like 'pair_to_mid', 'pair_to_bot', 'trips_to_mid',
    'high_only_top_lo_mid_hi_bot', etc.
    """
    feats = hand_features_scalar([int(b) for b in hand])
    cat = CATEGORY_NAMES[feats["category_id"]]
    top_pos, mid_pos, bot_pos = decode_tier_positions(setting_index)
    ranks = (hand // 4) + 2
    mid_ranks = sorted((int(ranks[mid_pos[0]]), int(ranks[mid_pos[1]])), reverse=True)
    bot_ranks = sorted((int(ranks[i]) for i in bot_pos), reverse=True)
    top_rank = int(ranks[top_pos])

    if cat == "pair":
        pair_rank = feats["pair_high_rank"]
        if mid_ranks[0] == pair_rank and mid_ranks[1] == pair_rank:
            return f"pair{pair_rank}_to_mid"
        if bot_ranks.count(pair_rank) == 2:
            return f"pair{pair_rank}_to_bot"
        if top_rank == pair_rank:  # rare
            return f"pair{pair_rank}_split"
        return f"pair{pair_rank}_split"

    if cat == "two_pair":
        ph = feats["pair_high_rank"]
        pl = feats["pair_low_rank"]
        # Where is each pair?
        def loc(rank: int) -> str:
            n_in_mid = mid_ranks.count(rank)
            n_in_bot = bot_ranks.count(rank)
            if n_in_mid == 2:
                return "mid"
            if n_in_bot == 2:
                return "bot"
            return "split"
        return f"hp{ph}_{loc(ph)}_lp{pl}_{loc(pl)}"

    if cat == "trips":
        tr = feats["trips_rank"]
        if mid_ranks.count(tr) == 2 and bot_ranks.count(tr) == 1:
            return f"trips{tr}_2mid_1bot"
        if bot_ranks.count(tr) == 3:
            return f"trips{tr}_to_bot"
        if mid_ranks.count(tr) == 2 and top_rank == tr:
            return f"trips{tr}_2mid_1top"
        if bot_ranks.count(tr) == 2 and top_rank == tr:
            return f"trips{tr}_2bot_1top"
        return f"trips{tr}_other"

    if cat == "trips_pair":
        tr = feats["trips_rank"]
        pr = feats["pair_high_rank"]
        # trips routing
        if bot_ranks.count(tr) == 3:
            t_loc = "all_bot"
        elif mid_ranks.count(tr) == 2:
            t_loc = "2mid"
        else:
            t_loc = "split"
        # pair routing
        if mid_ranks.count(pr) == 2:
            p_loc = "mid"
        elif bot_ranks.count(pr) == 2:
            p_loc = "bot"
        else:
            p_loc = "split"
        return f"trips{tr}_{t_loc}_pair{pr}_{p_loc}"

    if cat == "three_pair":
        return "three_pair_other"  # can refine later

    if cat == "high_only":
        return f"hi{top_rank}_mid{mid_ranks[0]}{mid_ranks[1]}"

    if cat == "quads":
        return "quads"

    return "other"


def main() -> int:
    print(f"Loading {GRID_PATH} ...")
    arr = np.load(GRID_PATH, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]
    ev_grid = arr["ev_grid"]                 # (N, 4, 105)
    profile_ids = list(arr["profile_ids"])
    n = hands_bytes.shape[0]
    n_profiles = len(profile_ids)
    print(f"  {n:,} hands × {n_profiles} profiles × 105 settings")
    print(f"  profiles: {profile_ids}\n")

    # 1. Compute v3 picks and oracle (argmax-mean) picks.
    print("Computing v3 + oracle picks ...")
    v3_picks = np.empty(n, dtype=np.int32)
    for i in range(n):
        v3_picks[i] = int(strategy_v3(hands_bytes[i]))
    ev_mean_per_setting = ev_grid.mean(axis=1)            # (N, 105)
    oracle_picks = ev_mean_per_setting.argmax(axis=1).astype(np.int32)

    # 2. Δ_global per hand (averaged over 4 profiles, in EV units).
    ev_v3 = ev_mean_per_setting[np.arange(n), v3_picks]
    ev_oracle = ev_mean_per_setting[np.arange(n), oracle_picks]
    delta_global = ev_oracle - ev_v3                       # (N,)
    delta_global_dollars = delta_global * 10000            # $/1000h equivalent

    # 3. Per-hand features and routing labels.
    print("Extracting per-hand features + routing labels ...")
    cats = np.empty(n, dtype=object)
    pair_high = np.empty(n, dtype=np.int8)
    n_broadway = np.empty(n, dtype=np.int8)
    connectivity_arr = np.empty(n, dtype=np.int8)
    suit_max = np.empty(n, dtype=np.int8)

    v3_routing = np.empty(n, dtype=object)
    oracle_routing = np.empty(n, dtype=object)
    v3_bot_suitprof = np.empty(n, dtype=object)
    oracle_bot_suitprof = np.empty(n, dtype=object)
    v3_bot_run = np.empty(n, dtype=np.int8)
    oracle_bot_run = np.empty(n, dtype=np.int8)
    delta_local_arr = np.empty(n, dtype=np.float32)

    for i in range(n):
        hand = hands_bytes[i]
        feats = hand_features_scalar([int(b) for b in hand])
        cats[i] = CATEGORY_NAMES[feats["category_id"]]
        pair_high[i] = feats["pair_high_rank"]
        n_broadway[i] = feats["n_broadway"]
        connectivity_arr[i] = feats["connectivity"]
        suit_max[i] = feats["suit_max"]

        ranks = (hand // 4) + 2
        suits = hand % 4

        for picks, routing_arr, bot_suit_arr, bot_run_arr in (
            (v3_picks, v3_routing, v3_bot_suitprof, v3_bot_run),
            (oracle_picks, oracle_routing, oracle_bot_suitprof, oracle_bot_run),
        ):
            s = int(picks[i])
            top_pos, mid_pos, bot_pos = decode_tier_positions(s)
            routing_arr[i] = routing_label(hand, s)
            bot_suits = tuple(int(suits[p]) for p in bot_pos)
            bot_ranks = tuple(int(ranks[p]) for p in bot_pos)
            bot_suit_arr[i] = bot_suit_profile(bot_suits)
            bot_run_arr[i] = bot_max_run(bot_ranks)

        # Δ_local: compare the v3-mid local strength vs oracle-mid local strength.
        v3_top, v3_mid, _ = decode_tier_positions(int(v3_picks[i]))
        o_top, o_mid, _ = decode_tier_positions(int(oracle_picks[i]))
        v3_mid_str = mid_strength(
            int(ranks[v3_mid[0]]),
            int(ranks[v3_mid[1]]),
            int(suits[v3_mid[0]]) == int(suits[v3_mid[1]]),
        )
        o_mid_str = mid_strength(
            int(ranks[o_mid[0]]),
            int(ranks[o_mid[1]]),
            int(suits[o_mid[0]]) == int(suits[o_mid[1]]),
        )
        delta_local_arr[i] = float(v3_mid_str - o_mid_str)

        if (i + 1) % 10000 == 0:
            print(f"  ...{i+1:,}/{n:,}")

    # 4. Build the per-hand DataFrame.
    df = pd.DataFrame({
        "hand_idx": np.arange(n),
        "category": cats,
        "pair_rank": pair_high,
        "n_broadway": n_broadway,
        "connectivity": connectivity_arr,
        "suit_max": suit_max,
        "v3_pick": v3_picks,
        "oracle_pick": oracle_picks,
        "ev_v3": ev_v3,
        "ev_oracle": ev_oracle,
        "delta_global": delta_global,
        "delta_global_dollars": delta_global_dollars,
        "delta_local": delta_local_arr,
        "v3_routing": v3_routing,
        "oracle_routing": oracle_routing,
        "v3_bot_suitprof": v3_bot_suitprof,
        "oracle_bot_suitprof": oracle_bot_suitprof,
        "v3_bot_run": v3_bot_run,
        "oracle_bot_run": oracle_bot_run,
    })
    df["disagrees"] = df["v3_pick"] != df["oracle_pick"]

    # 5. Headline numbers.
    print("\n" + "=" * 100)
    print(f"BLEED LANDSCAPE — {n:,} hands, oracle = argmax_mean across 4 profiles")
    print("=" * 100)
    total_bleed = float(df["delta_global"].sum())
    mean_bleed = float(df["delta_global"].mean())
    n_disagree = int(df["disagrees"].sum())
    print(f"Total bleed (sum Δ_global):              {total_bleed:>+10.2f} EV units")
    print(f"Mean bleed per hand:                     {mean_bleed:>+10.4f} EV units")
    print(f"Mean bleed in $/1000h:                   {mean_bleed * 10000:>+10.1f}")
    print(f"v3 == oracle on:                         {n - n_disagree:,} / {n:,} hands "
          f"({100 * (n - n_disagree) / n:.1f}%)")
    print(f"Top-1% bleed share:                      "
          f"{df.nlargest(int(0.01*n), 'delta_global')['delta_global'].sum() / total_bleed * 100:.1f}%")
    print(f"Top-5% bleed share:                      "
          f"{df.nlargest(int(0.05*n), 'delta_global')['delta_global'].sum() / total_bleed * 100:.1f}%")
    print(f"Top-10% bleed share:                     "
          f"{df.nlargest(int(0.10*n), 'delta_global')['delta_global'].sum() / total_bleed * 100:.1f}%")

    # 6. Bleed by category.
    print("\n" + "-" * 100)
    print("BLEED BY HAND CATEGORY (all hands)")
    print("-" * 100)
    by_cat = (
        df.groupby("category")
        .agg(
            n=("delta_global", "size"),
            share_pct=("delta_global", lambda s: 100 * len(s) / n),
            mean_bleed_dollars=("delta_global_dollars", "mean"),
            total_bleed=("delta_global", "sum"),
            disagree_pct=("disagrees", lambda s: 100 * s.mean()),
        )
        .sort_values("total_bleed", ascending=False)
    )
    by_cat["share_of_total_bleed_pct"] = 100 * by_cat["total_bleed"] / total_bleed
    print(by_cat.to_string(float_format=lambda x: f"{x:>10.2f}"))

    # 7. Top-5% bleed slice — categorical archetypes.
    top_n = max(1, int(0.05 * n))
    top_df = df.nlargest(top_n, "delta_global").copy()
    print("\n" + "-" * 100)
    print(f"TOP-5% BLEED SLICE — {top_n:,} hands  (these are where rules pay)")
    print("-" * 100)

    print("\n  By category × pair_rank (where applicable):")
    grouped = top_df.groupby(["category", "pair_rank"]).agg(
        n=("delta_global", "size"),
        mean_bleed_dollars=("delta_global_dollars", "mean"),
        total_bleed=("delta_global", "sum"),
    ).sort_values("total_bleed", ascending=False)
    grouped["share_pct"] = 100 * grouped["total_bleed"] / top_df["delta_global"].sum()
    print(grouped.head(20).to_string(float_format=lambda x: f"{x:>10.2f}"))

    # 8. Trap zone vs confident blunder split.
    # Trap: |Δ_local| small  (v3's mid looked locally as good or better,
    #        but oracle wins via cascade).
    # Confident blunder: Δ_local > 0  (v3 picked stronger-looking mid)
    #        AND large Δ_global.
    print("\n" + "-" * 100)
    print("TOP-5% — TRAP-ZONE vs CONFIDENT-BLUNDER classification")
    print("-" * 100)
    # Define "small" Δ_local as |Δ_local| ≤ 50 (less than a full-rank gap).
    top_df["zone"] = np.where(
        top_df["delta_local"].abs() <= 50,
        "trap_zone (local wash, global cascade)",
        np.where(
            top_df["delta_local"] > 50,
            "confident_blunder (v3 mid looked stronger)",
            "v3_local_weaker (rare)",
        ),
    )
    zone_summary = top_df.groupby("zone").agg(
        n=("delta_global", "size"),
        mean_bleed_dollars=("delta_global_dollars", "mean"),
        total_bleed=("delta_global", "sum"),
    ).sort_values("total_bleed", ascending=False)
    zone_summary["share_pct"] = 100 * zone_summary["total_bleed"] / top_df["delta_global"].sum()
    print(zone_summary.to_string(float_format=lambda x: f"{x:>10.2f}"))

    # 9. Routing change: v3_routing → oracle_routing.
    print("\n  Top routing changes (v3 → oracle) by total bleed in top-5% slice:")
    top_df["routing_change"] = top_df["v3_routing"] + " >>> " + top_df["oracle_routing"]
    rc = top_df.groupby("routing_change").agg(
        n=("delta_global", "size"),
        mean_bleed_dollars=("delta_global_dollars", "mean"),
        total_bleed=("delta_global", "sum"),
    ).sort_values("total_bleed", ascending=False)
    rc["share_pct"] = 100 * rc["total_bleed"] / top_df["delta_global"].sum()
    print(rc.head(15).to_string(float_format=lambda x: f"{x:>10.2f}"))

    # 10. Bot-suit-profile change.
    print("\n  Bot suit-profile change (v3 → oracle) in top-5% slice:")
    top_df["bot_suit_change"] = top_df["v3_bot_suitprof"] + " >>> " + top_df["oracle_bot_suitprof"]
    bs = top_df.groupby("bot_suit_change").agg(
        n=("delta_global", "size"),
        mean_bleed_dollars=("delta_global_dollars", "mean"),
        total_bleed=("delta_global", "sum"),
    ).sort_values("total_bleed", ascending=False)
    bs["share_pct"] = 100 * bs["total_bleed"] / top_df["delta_global"].sum()
    print(bs.head(10).to_string(float_format=lambda x: f"{x:>10.2f}"))

    # 11. Bot-connectivity change.
    print("\n  Bot connectivity (max-run) change (v3 → oracle) in top-5% slice:")
    top_df["bot_run_change"] = (
        top_df["v3_bot_run"].astype(str) + " >>> " + top_df["oracle_bot_run"].astype(str)
    )
    br = top_df.groupby("bot_run_change").agg(
        n=("delta_global", "size"),
        mean_bleed_dollars=("delta_global_dollars", "mean"),
        total_bleed=("delta_global", "sum"),
    ).sort_values("total_bleed", ascending=False)
    br["share_pct"] = 100 * br["total_bleed"] / top_df["delta_global"].sum()
    print(br.head(10).to_string(float_format=lambda x: f"{x:>10.2f}"))

    # 12. Persist for further analysis.
    df.to_parquet(OUT_PATH, index=False)
    print(f"\nFull per-hand records written to {OUT_PATH}")
    print(f"  Use this for follow-up clustering / rule mining.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
