"""
Sprint-7 deep pattern mining over the 6M-hand feature table.

Each section answers a specific question the user posed in Session 12:

  1. Trips placement      — where do 3-of-a-kind go in the robust setting?
  2. Trips + pair         — full-house-shape hands: split by trip vs pair rank
  3. Quads                — what's the play with 4-of-a-kind?
  4. Three pair           — which two pairs go to bottom vs which to mid?
  5. Big pair location    — when does a 9+ pair go to bottom instead of mid?
  6. Top card cutoff      — for unpaired top, what's the distribution by rank?
  7. Suits vs connectivity — once mid is locked, does bot prefer DS or runs?
  8. Garbage hands        — low+broadway-poor: what's the structure of the play?
  9. Buyout +EV analysis  — at what EV threshold is "pay 4 to fold" cheaper than playing?
                             Per-profile breakdown + feature signature of buyout candidates.

Each section is opinionated about what counts as a "rule" worth keeping for
the eventual decision tree. A rule survives only if it has high agreement on
high-applicability sub-populations. Anything weaker is flagged as "needs
opponent read" rather than rule.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

# Buyout cost per opponent who accepts. The user's home rule.
BUYOUT_COST = 4.0


def header(s: str) -> None:
    print()
    print("=" * 78)
    print(f" {s}")
    print("=" * 78)


def subhead(s: str) -> None:
    print()
    print(f"--- {s} ---")


def pct(x: float) -> str:
    return f"{100*x:5.2f}%"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", type=Path,
                    default=ROOT / "data" / "feature_table.parquet")
    args = ap.parse_args()

    print(f"Loading {args.table}…")
    df = pq.read_table(args.table).to_pandas()
    n = len(df)
    print(f"  {n:,} canonical hands × {len(df.columns)} columns\n")

    # ==================================================================
    # 1. TRIPS PLACEMENT
    # ==================================================================
    header("1. Trips placement (where do 3-of-a-kind go?)")

    # Hands with exactly trips, no pair (pure trips).
    # When you have trips of rank R, three slots can hold the 3 cards:
    #   (a) Trips in mid (mid pair of R) + 1 R card in top or bot
    #   (b) Trips in bot (3 of R in bot, 0 elsewhere)
    #   (c) Mid 1 + bot 2: mid is NOT pair of R, but 2 of R sit in bot + 1 elsewhere
    # We detect this via robust_mid_high_rank == trips_rank AND robust_mid_is_pair.
    pure_trips = df[df["category"] == "trips"]
    print(f"Pure-trips hands (no accompanying pair): {len(pure_trips):,} "
          f"({100*len(pure_trips)/n:.2f}%)")

    if len(pure_trips):
        trips_pair_in_mid = (
            pure_trips["robust_mid_is_pair"]
            & (pure_trips["robust_mid_high_rank"] == pure_trips["trips_rank"])
        )
        # If trips not in mid, count remaining R cards in bot.
        # bot_pair_high reaches rank R only if 2+ of R sit in bot.
        trips_pair_in_bot = (
            (~trips_pair_in_mid)
            & (pure_trips["robust_bot_pair_high"] == pure_trips["trips_rank"])
        )
        trips_split = ~(trips_pair_in_mid | trips_pair_in_bot)

        print(f"  trips → mid (pair) + 1 elsewhere : {pct(trips_pair_in_mid.mean())}")
        print(f"  trips → bot (pair) + 1 elsewhere : {pct(trips_pair_in_bot.mean())}")
        print(f"  trips split across all 3 tiers   : {pct(trips_split.mean())}")

        subhead("By trips_rank:")
        rows = []
        for r in range(2, 15):
            sub = pure_trips[pure_trips["trips_rank"] == r]
            if len(sub) < 200:
                continue
            t_mid = (
                sub["robust_mid_is_pair"]
                & (sub["robust_mid_high_rank"] == r)
            ).mean()
            t_bot = (
                (~(sub["robust_mid_is_pair"] & (sub["robust_mid_high_rank"] == r)))
                & (sub["robust_bot_pair_high"] == r)
            ).mean()
            rows.append((r, len(sub), t_mid, t_bot))
        print(f"  {'rank':>5} {'n':>9} {'trips→mid':>11} {'trips→bot':>11}")
        for r, k, m, b in rows:
            print(f"  {r:>5} {k:>9,} {pct(m):>11} {pct(b):>11}")

    # ==================================================================
    # 2. TRIPS + PAIR (FULL-HOUSE SHAPE)
    # ==================================================================
    header("2. Trips + pair (full-house shape) — split by trip & pair rank")

    fh = df[df["category"] == "trips_pair"].copy()
    print(f"Full-house-shape hands: {len(fh):,} ({100*len(fh)/n:.2f}%)")
    if len(fh):
        # Where do trips go? Where does pair go?
        fh["trips_in_mid"] = (
            fh["robust_mid_is_pair"]
            & (fh["robust_mid_high_rank"] == fh["trips_rank"])
        )
        fh["pair_in_mid"] = (
            fh["robust_mid_is_pair"]
            & (fh["robust_mid_high_rank"] == fh["pair_high_rank"])
        )
        fh["pair_in_bot"] = fh["robust_bot_pair_high"] == fh["pair_high_rank"]
        # Trips kept in bot: 2 of trip-rank in bot, 1 elsewhere.
        fh["trips_in_bot"] = (~fh["trips_in_mid"]) & (
            fh["robust_bot_pair_high"] == fh["trips_rank"]
        )

        # Quadrant: low/high trip × low/high pair (cutoff = 9).
        fh["high_trips"] = fh["trips_rank"] >= 9
        fh["high_pair"] = fh["pair_high_rank"] >= 9
        for ht in (False, True):
            for hp in (False, True):
                sub = fh[(fh["high_trips"] == ht) & (fh["high_pair"] == hp)]
                if len(sub) < 200:
                    continue
                label = (
                    f"trips_{'high' if ht else 'low'}_pair_{'high' if hp else 'low'}"
                )
                print(f"\n  {label}  n={len(sub):,}")
                print(f"    trips → mid: {pct(sub['trips_in_mid'].mean())}")
                print(f"    pair  → mid: {pct(sub['pair_in_mid'].mean())}")
                print(f"    trips → bot (pair-of-3rd-rank): {pct(sub['trips_in_bot'].mean())}")
                print(f"    mean ev (vs MFSA): {sub['ev_mfsuitaware'].mean():+.3f}")

    # ==================================================================
    # 3. QUADS
    # ==================================================================
    header("3. Quads (4-of-a-kind)")

    q = df[df["category"] == "quads"].copy()
    print(f"Quads hands: {len(q):,} ({100*len(q)/n:.2f}%)")
    if len(q):
        # Quads rank distribution
        rows = []
        for r in range(2, 15):
            sub = q[q["quads_rank"] == r]
            if not len(sub):
                continue
            # Pair-in-bot rate (when the 4 cards split: 2 mid + 2 bot)
            quads_split_2_2 = (
                sub["robust_mid_is_pair"]
                & (sub["robust_mid_high_rank"] == r)
                & (sub["robust_bot_pair_high"] == r)
            ).mean()
            quads_all_in_bot = (
                (~(sub["robust_mid_is_pair"] & (sub["robust_mid_high_rank"] == r)))
                & (sub["robust_bot_pair_high"] == r)
                & (sub["robust_bot_n_pairs"] >= 1)
            ).mean()
            mean_ev = sub["ev_mean"].mean()
            rows.append((r, len(sub), quads_split_2_2, quads_all_in_bot, mean_ev))
        print(f"  {'rank':>5} {'n':>7} {'split 2mid+2bot':>16} {'≥3 in bot':>11} {'mean_ev':>9}")
        for r, k, sp, allbot, ev in rows:
            print(f"  {r:>5} {k:>7,} {pct(sp):>16} {pct(allbot):>11} {ev:>+9.3f}")

    # ==================================================================
    # 4. THREE PAIR
    # ==================================================================
    header("4. Three-pair hands — which pair lands in middle?")

    tp = df[df["n_pairs"] == 3].copy()
    print(f"Three-pair hands: {len(tp):,} ({100*len(tp)/n:.2f}%)")
    if len(tp):
        tp["mid_pair_is_high"] = (
            tp["robust_mid_is_pair"]
            & (tp["robust_mid_high_rank"] == tp["pair_high_rank"])
        )
        tp["mid_pair_is_mid"] = (
            tp["robust_mid_is_pair"]
            & (tp["robust_mid_high_rank"] == tp["pair_low_rank"])
        )
        tp["mid_pair_is_low"] = (
            tp["robust_mid_is_pair"]
            & (tp["robust_mid_high_rank"] == tp["pair_third_rank"])
        )
        tp["mid_no_pair"] = ~tp["robust_mid_is_pair"]
        print(f"  mid = highest pair : {pct(tp['mid_pair_is_high'].mean())}")
        print(f"  mid = middle pair  : {pct(tp['mid_pair_is_mid'].mean())}")
        print(f"  mid = lowest pair  : {pct(tp['mid_pair_is_low'].mean())}")
        print(f"  mid is not a pair  : {pct(tp['mid_no_pair'].mean())}")

    # ==================================================================
    # 5. BIG PAIR ON BOTTOM INSTEAD OF MIDDLE
    # ==================================================================
    header("5. When does a high pair (9+) go to BOTTOM instead of MIDDLE?")

    # Hand has a high pair. Robust setting puts a pair of that rank in bot
    # instead of mid.
    has_hp = (df["n_pairs"] >= 1) & (df["pair_high_rank"] >= 9)
    print(f"Hands with a 9+ pair: {int(has_hp.sum()):,} ({pct(has_hp.mean())})")
    sub = df[has_hp].copy()
    if len(sub):
        sub["highpair_in_mid"] = (
            sub["robust_mid_is_pair"] & (sub["robust_mid_high_rank"] >= 9)
        )
        sub["highpair_in_bot"] = (
            (~sub["highpair_in_mid"])
            & (sub["robust_bot_pair_high"] >= 9)
        )
        sub["highpair_split"] = ~(sub["highpair_in_mid"] | sub["highpair_in_bot"])
        print(f"  high pair → mid : {pct(sub['highpair_in_mid'].mean())}")
        print(f"  high pair → bot : {pct(sub['highpair_in_bot'].mean())}")
        print(f"  high pair split : {pct(sub['highpair_split'].mean())}")

        # Per pair-rank breakdown — at what rank does "→ bot" become a thing?
        subhead("by highest-pair rank:")
        print(f"  {'rank':>5} {'n':>9} {'→mid':>9} {'→bot':>9} {'split':>9}")
        for r in range(9, 15):
            s = sub[sub["pair_high_rank"] == r]
            if len(s) < 200:
                continue
            print(f"  {r:>5} {len(s):>9,} {pct(s['highpair_in_mid'].mean()):>9} "
                  f"{pct(s['highpair_in_bot'].mean()):>9} "
                  f"{pct(s['highpair_split'].mean()):>9}")

        # When high pair goes to bottom, what's the OTHER feature? Trip co-occur?
        bot_cases = sub[sub["highpair_in_bot"]]
        if len(bot_cases):
            print(f"\n  When high pair lands in BOT ({len(bot_cases):,} hands), "
                  f"what's also true?")
            print(f"    has_trips         : {pct((bot_cases['n_trips'] >= 1).mean())}")
            print(f"    has_higher_pair   : "
                  f"{pct(((bot_cases['n_pairs'] >= 2) & (bot_cases['pair_high_rank'] > bot_cases['pair_low_rank'].clip(lower=9))).mean())}")
            print(f"    is_double_suited_hand_friendly (suit_max==4): "
                  f"{pct((bot_cases['suit_max'] == 4).mean())}")
            print(f"    bot_is_double_suited (in robust): "
                  f"{pct(bot_cases['robust_bot_is_double_suited'].mean())}")

    # ==================================================================
    # 6. TOP CARD CUTOFF (UNPAIRED-TOP CASE)
    # ==================================================================
    header("6. Top-card cutoff for hands where the top is a singleton")

    # The robust top is a singleton (rank appears only once in the 7 cards).
    # We approximate: robust_top_rank not equal to any pair/trip/quad rank.
    df["top_is_singleton"] = (
        (df["robust_top_rank"] != df["pair_high_rank"])
        & (df["robust_top_rank"] != df["pair_low_rank"])
        & (df["robust_top_rank"] != df["pair_third_rank"])
        & (df["robust_top_rank"] != df["trips_rank"])
        & (df["robust_top_rank"] != df["quads_rank"])
    )
    sing = df[df["top_is_singleton"]]
    print(f"Hands where robust top is a singleton: "
          f"{len(sing):,} ({pct(len(sing)/n)})")
    print()
    print(f"  {'top_rank':>9} {'n':>9} {'share':>7}")
    for r in range(2, 15):
        c = int((sing["robust_top_rank"] == r).sum())
        print(f"  {r:>9} {c:>9,} {pct(c/len(sing)):>7}")
    # Cumulative tail: P(robust top ≤ X) given singleton.
    print()
    cum = 0
    for r in range(2, 15):
        c = int((sing["robust_top_rank"] == r).sum())
        cum += c
        print(f"  P(robust top ≤ {r:>2}) = {pct(cum/len(sing))}")

    # ==================================================================
    # 7. SUITS vs CONNECTIVITY TIEBREAKER (mid locked = high pair)
    # ==================================================================
    header("7. With mid locked as a high pair, does bot lean DS or connectivity?")

    locked = df[
        df["robust_mid_is_pair"]
        & (df["robust_mid_high_rank"] >= 10)
        & ~(df["n_trips"] >= 1)  # exclude trips-driven cases
        & ~(df["n_quads"] >= 1)
    ]
    print(f"Hands with mid = pair of T+ (and no trips/quads): {len(locked):,}")
    if len(locked):
        ds_only = locked["robust_bot_is_double_suited"] & (locked["robust_bot_connectivity"] < 4)
        conn_only = (locked["robust_bot_connectivity"] >= 4) & ~locked["robust_bot_is_double_suited"]
        both = locked["robust_bot_is_double_suited"] & (locked["robust_bot_connectivity"] >= 4)
        neither = ~(locked["robust_bot_is_double_suited"] | (locked["robust_bot_connectivity"] >= 4))
        print(f"  bot DS-only (no straight)        : {pct(ds_only.mean())}")
        print(f"  bot connected-only (≥4 in run)   : {pct(conn_only.mean())}")
        print(f"  bot both DS AND connected        : {pct(both.mean())}")
        print(f"  bot neither (random fill)        : {pct(neither.mean())}")
        # Conditional: when the HAND supports both options (suit_max ≤ 3 AND connectivity ≥ 4),
        # what does robust pick?
        feasible = (
            (locked["suit_max"] <= 3)
            & (locked["connectivity"] >= 4)
        )
        f = locked[feasible]
        if len(f):
            print(f"\n  When the hand can support EITHER DS or connectivity ({len(f):,} hands):")
            print(f"    robust picked DS:        {pct(f['robust_bot_is_double_suited'].mean())}")
            print(f"    robust picked connected: {pct((f['robust_bot_connectivity'] >= 4).mean())}")

    # ==================================================================
    # 8. GARBAGE HANDS — low + broadway-poor
    # ==================================================================
    header("8. Garbage hands (low cards dominate, no pairs)")

    garbage = df[
        (df["n_pairs"] == 0)
        & (df["n_low"] >= 3)         # 3+ cards ≤ rank 5
        & (df["n_broadway"] <= 2)
    ]
    print(f"Garbage hands (no pair, ≥3 low, ≤2 broadway): "
          f"{len(garbage):,} ({pct(len(garbage)/n)})")
    if len(garbage):
        print(f"  mean ev_mean    : {garbage['ev_mean'].mean():+.3f}")
        print(f"  mean ev_min     : {garbage['ev_min'].mean():+.3f}")
        print(f"  mean ev_max     : {garbage['ev_max'].mean():+.3f}")
        print(f"  share with ev_mean < -4 (buyout +EV vs avg): "
              f"{pct((garbage['ev_mean'] < -BUYOUT_COST).mean())}")
        print(f"  share with ev_mean < 0  : "
              f"{pct((garbage['ev_mean'] < 0).mean())}")

    # ==================================================================
    # 9. BUYOUT +EV ANALYSIS
    # ==================================================================
    header("9. BUYOUT analysis — when is paying 4 to fold cheaper than playing?")

    print(f"Buyout cost per accepting opponent: {BUYOUT_COST} points")
    print(f"Heads-up buyout is +EV iff ev < -{BUYOUT_COST} vs that opponent.")
    print()

    subhead("Per-profile buyout-rate (% of hands where heads-up buyout is +EV):")
    for col, label in [
        ("ev_mfsuitaware", "MF-SA (typical)"),
        ("ev_omaha",       "OmahaFirst (weakest opp)"),
        ("ev_topdef",      "TopDefensive (toughest opp)"),
        ("ev_weighted",    "RandomWeighted (loose-ish)"),
    ]:
        share = float((df[col] < -BUYOUT_COST).mean())
        worst = float(df[col].min())
        median = float(df[col].median())
        p1 = float(df[col].quantile(0.01))
        p5 = float(df[col].quantile(0.05))
        print(f"  {label:<28} buyout +EV: {pct(share)}  "
              f"min={worst:+.2f}  p1={p1:+.2f}  p5={p5:+.2f}  median={median:+.2f}")

    subhead("Mean-EV (4-profile average) buyout rate — robust to opp identity:")
    share_mean_below_buyout = float((df["ev_mean"] < -BUYOUT_COST).mean())
    print(f"  P(ev_mean < -{BUYOUT_COST})     = {pct(share_mean_below_buyout)}")
    for thresh in (-2, -3, -4, -5, -6, -8, -10):
        s = float((df["ev_mean"] < thresh).mean())
        print(f"  P(ev_mean < {thresh:>3})       = {pct(s)}")

    subhead("FEATURE signature of buyout-candidate hands (ev_mean < -4):")
    bo = df[df["ev_mean"] < -BUYOUT_COST]
    print(f"  buyout-candidate hands: {len(bo):,} ({pct(len(bo)/n)})")
    if len(bo):
        for col in ("category", "n_pairs", "top_rank", "n_broadway", "n_low",
                     "suit_max", "connectivity"):
            if col == "category":
                vc = bo[col].value_counts(normalize=True).sort_index()
                base = df[col].value_counts(normalize=True)
                print()
                print(f"  By {col} (buyout share vs base):")
                for k, v in vc.items():
                    b = float(base.get(k, 0))
                    lift = (v/b) if b else float("nan")
                    print(f"    {k:<12} buyout={pct(v)} base={pct(b)} lift={lift:>5.2f}x")
            else:
                print(f"  {col:<14} buyout-candidate mean: {bo[col].mean():.2f}  "
                      f"all-hands mean: {df[col].mean():.2f}")

    subhead("Multiway buyout intuition (per-profile-INDEPENDENT decision):")
    # For each hand and each opp profile, you decide to buy out from that opp
    # iff EV vs that opp < -4. That's an independent per-opp decision.
    # Total expected loss with optimal-buyout = sum_p min(EV_p, -4) for the p
    # opps actually at the table.
    # Compute: how many of the 4 profile slots would the player buy out from?
    n_buy_per_hand = (
        (df["ev_mfsuitaware"] < -BUYOUT_COST).astype(int)
        + (df["ev_omaha"]       < -BUYOUT_COST).astype(int)
        + (df["ev_topdef"]      < -BUYOUT_COST).astype(int)
        + (df["ev_weighted"]    < -BUYOUT_COST).astype(int)
    )
    print(f"  In a 4-handed game with one opp from each profile,")
    print(f"  distribution of #opps you should buy out from:")
    for k in range(5):
        s = float((n_buy_per_hand == k).mean())
        print(f"    {k} buyouts : {pct(s)}")
    print(f"  At least 1 buyout : {pct((n_buy_per_hand >= 1).mean())}")
    print(f"  All 4 buyouts     : {pct((n_buy_per_hand == 4).mean())}")
    # Average savings per hand if you adopt the buyout policy.
    saved_per_profile = []
    for col in ("ev_mfsuitaware", "ev_omaha", "ev_topdef", "ev_weighted"):
        saved = np.maximum(-BUYOUT_COST - df[col], 0).sum()
        saved_per_profile.append(saved / n)
    avg_saved = sum(saved_per_profile)
    print(f"  Total avg points saved/hand by selective buyout in 4-handed: "
          f"{avg_saved:+.4f}")
    print(f"  Per-100-hands savings: {avg_saved*100:+.2f} points")

    return 0


if __name__ == "__main__":
    sys.exit(main())
