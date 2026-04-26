"""
Sprint-7 Phase B: drill into high_only (no-pair) hands.

The current rule chain falls back to NAIVE_104 for no-pair hands:
  top = highest singleton
  mid = next two highest
  bot = the remaining four
That's wrong on ~80% of high_only hands (52.4% of all rule misses).

We don't yet know what TO do instead. This miner asks the data what the
robust setting actually does, breaking out variation by:

  1. Top-rank distribution and "highest goes top" rate.
  2. Top vs second-rank gap (does a small gap demote highest into mid?).
  3. Mid composition — is mid two highest singletons, suited connectors, or
     something else? Rate of mid_is_suited / mid_rank_sum percentiles.
  4. Bot suit structure — does robust pick a DS bot when feasible
     (suit_2nd ≥ 2)?
  5. Bot connectivity preference vs DS when both are feasible.
  6. NAIVE_104 hit rate broken down by hand suit/connectivity profile.
  7. Cross-tab: when do we differ from NAIVE_104? What conditions characterise
     the misses?

The output is a recipe of candidate rules sized by expected agreement gain.
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
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis import read_canonical_hands  # noqa: E402
from tw_analysis.features import decode_tier_positions  # noqa: E402


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


def naive_104_setting_shape(hand_bytes: np.ndarray) -> tuple:
    """
    Shape (top_rank, sorted_mid_ranks, sorted_bot_ranks) of NAIVE_104 on
    a canonical hand. Canonical hands are sorted ascending → highest byte
    last → setting 104 (top=pos6, mid=(4,5), bot=(0,1,2,3)).
    """
    ranks = (hand_bytes // 4) + 2
    return (
        int(ranks[6]),
        tuple(sorted([int(ranks[4]), int(ranks[5])])),
        tuple(sorted([int(ranks[0]), int(ranks[1]), int(ranks[2]), int(ranks[3])])),
    )


def robust_setting_shape(hand_bytes: np.ndarray, setting: int) -> tuple:
    t, m, b = decode_tier_positions(int(setting))
    ranks = (hand_bytes // 4) + 2
    return (
        int(ranks[t]),
        tuple(sorted([int(ranks[i]) for i in m])),
        tuple(sorted([int(ranks[i]) for i in b])),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canonical", type=Path,
                    default=ROOT / "data" / "canonical_hands.bin")
    ap.add_argument("--table", type=Path,
                    default=ROOT / "data" / "feature_table.parquet")
    args = ap.parse_args()

    print(f"Loading {args.canonical}…")
    canonical = read_canonical_hands(args.canonical)
    cards = canonical.hands
    print(f"  {canonical.header.num_hands:,} canonical hands")

    print(f"Loading {args.table}…")
    df = pq.read_table(args.table).to_pandas()
    n_total = len(df)
    print(f"  {n_total:,} rows × {len(df.columns)} columns")

    mask = (df["category"] == "high_only").values
    sub = df[mask].reset_index(drop=True)
    sub_hands = cards[mask]
    n = len(sub)
    print(f"\nhigh_only subset: {n:,} hands ({pct(n/n_total)} of total)")

    # ==================================================================
    # 1. Robust top-rank distribution
    # ==================================================================
    header("1. Robust top-rank distribution on high_only")

    print(f"  {'top_rank':>9} {'n':>9} {'share':>8}")
    for r in range(2, 15):
        c = int((sub["robust_top_rank"] == r).sum())
        if c == 0:
            continue
        print(f"  {r:>9} {c:>9,} {pct(c/n):>8}")

    # Hand top_rank vs robust top_rank
    follows = (sub["robust_top_rank"] == sub["top_rank"]).mean()
    print(f"\n  Robust top == hand top_rank (highest distinct rank): {pct(follows)}")

    # Demoted: highest hand-rank does NOT go to top.
    demoted = sub["robust_top_rank"] != sub["top_rank"]
    print(f"  highest hand-rank demoted from top: {pct(demoted.mean())}  "
          f"({int(demoted.sum()):,} hands)")

    # ==================================================================
    # 2. Top vs second-rank gap as a predictor of demotion
    # ==================================================================
    header("2. Demotion rate as a function of top vs second hand-rank gap")

    sub["rank_gap_top_2nd"] = (sub["top_rank"] - sub["second_rank"]).astype(int)
    sub["rank_gap_2nd_3rd"] = (sub["second_rank"] - sub["third_rank"]).astype(int)
    print(f"  {'gap':>4} {'n':>9} {'demoted':>9} {'mean ev':>9}")
    for g in range(0, 13):
        s = sub[sub["rank_gap_top_2nd"] == g]
        if len(s) < 200:
            continue
        d = (s["robust_top_rank"] != s["top_rank"]).mean()
        ev = s["ev_mean"].mean()
        print(f"  {g:>4} {len(s):>9,} {pct(d):>9} {ev:>+9.3f}")

    # ==================================================================
    # 3. Mid composition: suited / pair / connected / random
    # ==================================================================
    header("3. Robust mid composition on high_only")

    mid_is_pair = sub["robust_mid_is_pair"]
    mid_is_suited = sub["robust_mid_is_suited"]
    print(f"  mid is a pair          : {pct(mid_is_pair.mean())}  "
          f"({int(mid_is_pair.sum()):,})")
    print(f"  mid is suited          : {pct(mid_is_suited.mean())}")
    print(f"  mid is connected       : "
          f"{pct(((sub['robust_mid_high_rank'] - sub['robust_mid_low_rank']) <= 4).mean())}")

    # Whether robust mid is the two highest singletons (the NAIVE_104 mid).
    # Hand top_rank = highest distinct rank; second_rank = next; third_rank = third.
    # Naive mid = (third_rank, second_rank). If hand has 7 distinct ranks, those are positions [4,5].
    # Use a more robust check: robust_mid_high_rank == second_rank AND robust_mid_low_rank == third_rank.
    naive_mid = (
        (sub["robust_mid_high_rank"] == sub["second_rank"])
        & (sub["robust_mid_low_rank"]  == sub["third_rank"])
    )
    print(f"  mid = (second, third) [NAIVE_104 mid] : {pct(naive_mid.mean())}")

    # When mid is NOT (second, third), what is it? Bucket by mid_high_rank category.
    not_naive = sub[~naive_mid]
    if len(not_naive):
        print(f"\n  When mid != (second, third)  ({len(not_naive):,} hands):")
        # Highest mid card vs second_rank
        eq_sec = (not_naive["robust_mid_high_rank"] == not_naive["second_rank"]).mean()
        print(f"    mid_high_rank == second_rank : {pct(eq_sec)}")
        gt_third = (
            (not_naive["robust_mid_high_rank"] == not_naive["second_rank"])
            & (not_naive["robust_mid_low_rank"] != not_naive["third_rank"])
        ).mean()
        print(f"    mid = (second, NOT third)    : {pct(gt_third)}  "
              f"(mid keeps the 2nd-highest card and pairs it with a non-3rd-rank card)")
        contains_top = (
            (not_naive["robust_mid_high_rank"] == not_naive["top_rank"])
            | (not_naive["robust_mid_low_rank"] == not_naive["top_rank"])
        ).mean()
        print(f"    mid contains the highest hand-rank: {pct(contains_top)}  "
              f"(highest got demoted to mid)")

    # ==================================================================
    # 4. Bot DS preference (when feasible)
    # ==================================================================
    header("4. Bot suit structure: when can_make_ds_bot, does robust pick DS?")

    # `can_make_ds_bot` ≡ at least two suits each have ≥ 2 cards somewhere in the hand.
    # That's a sufficient feasibility check derivable from suit_max + suit_2nd: if
    # suit_2nd ≥ 2, you have at least one second-suit pair available. To make a DS bot
    # you need 2 cards of one suit AND 2 of another in the BOTTOM 4 (not constrained
    # to bot here — but if hand has suit_2nd ≥ 2, often achievable when bot has 4 of
    # the right cards).
    can_ds = sub["suit_2nd"] >= 2
    print(f"  Hands where suit_2nd >= 2 (DS feasible somewhere): "
          f"{int(can_ds.sum()):,} ({pct(can_ds.mean())})")
    if int(can_ds.sum()):
        ds_picked = sub.loc[can_ds, "robust_bot_is_double_suited"].mean()
        print(f"    robust picked DS bot           : {pct(ds_picked)}")

    # Stricter feasibility: if suit_max ≤ 4 (no monosuit) and suit_2nd ≥ 2 and
    # hand has at least 2 cards of a 3rd suit OR not.
    # Hand-level "structurally DS-able" = at least two suits with 2 cards each.
    # Derived: suit_max ≥ 2 AND suit_2nd ≥ 2.
    structural_ds = (sub["suit_max"] >= 2) & (sub["suit_2nd"] >= 2)
    print(f"\n  Hands with structural DS shape (suit_max ≥ 2 AND suit_2nd ≥ 2): "
          f"{int(structural_ds.sum()):,} ({pct(structural_ds.mean())})")
    if int(structural_ds.sum()):
        s = sub[structural_ds]
        print(f"    robust picked DS bot           : {pct(s['robust_bot_is_double_suited'].mean())}")

    # When suit_2nd < 2, DS is impossible. Confirm robust never picks DS.
    no_ds = ~can_ds
    if int(no_ds.sum()):
        s = sub[no_ds]
        print(f"\n  Hands with suit_2nd < 2 (DS infeasible): "
              f"{int(no_ds.sum()):,}, robust picked DS: {pct(s['robust_bot_is_double_suited'].mean())} "
              f"(should be 0%)")

    # ==================================================================
    # 5. Bot connectivity preference vs DS
    # ==================================================================
    header("5. Bot connectivity vs DS — when both feasible at hand level")

    # Hand-level "structurally connected" = connectivity ≥ 5 (so bot can have 4-run).
    structural_run = sub["connectivity"] >= 5
    both = structural_ds & structural_run
    print(f"  Hands where DS AND 5+ connected run feasible: "
          f"{int(both.sum()):,} ({pct(both.mean())})")
    if int(both.sum()):
        s = sub[both]
        ds = s["robust_bot_is_double_suited"].mean()
        run = (s["robust_bot_connectivity"] >= 4).mean()
        b_both = (s["robust_bot_is_double_suited"] & (s["robust_bot_connectivity"] >= 4)).mean()
        b_neither = (~s["robust_bot_is_double_suited"] & (s["robust_bot_connectivity"] < 4)).mean()
        print(f"    bot DS (any conn): {pct(ds)}")
        print(f"    bot 4+ run (any suit): {pct(run)}")
        print(f"    bot DS AND 4+ run: {pct(b_both)}")
        print(f"    bot neither: {pct(b_neither)}")

    # ==================================================================
    # 6. NAIVE_104 shape-agreement on high_only — full picture
    # ==================================================================
    header("6. NAIVE_104 shape-agreement decomposition")

    print("Computing NAIVE_104 shapes vs robust shapes on high_only…")
    naive_shapes = [naive_104_setting_shape(sub_hands[i]) for i in range(n)]
    robust_shapes = [robust_setting_shape(sub_hands[i], int(sub.iloc[i]["multiway_robust"]))
                     for i in range(n)]
    naive_match = np.array([naive_shapes[i] == robust_shapes[i] for i in range(n)])
    print(f"  NAIVE_104 shape-agreement on high_only: {pct(naive_match.mean())}")

    # Decompose: which of (top, mid, bot) does NAIVE get wrong in mismatches?
    # We do this on the SHAPE basis.
    top_match = np.array([naive_shapes[i][0] == robust_shapes[i][0] for i in range(n)])
    mid_match = np.array([naive_shapes[i][1] == robust_shapes[i][1] for i in range(n)])
    bot_match = np.array([naive_shapes[i][2] == robust_shapes[i][2] for i in range(n)])
    print(f"  top match: {pct(top_match.mean())}")
    print(f"  mid match: {pct(mid_match.mean())}")
    print(f"  bot match: {pct(bot_match.mean())}  "
          f"(once top+mid are right, bot is forced — so bot match ≈ top∧mid match)")
    print(f"  top AND mid match: {pct((top_match & mid_match).mean())}")

    # Where naive is wrong: which tier is the first to mismatch?
    naive_wrong = ~naive_match
    if int(naive_wrong.sum()):
        wrong = naive_wrong & ~top_match
        print(f"\n  Of {int(naive_wrong.sum()):,} naive misses:")
        print(f"    top is wrong (highest-singleton WAS NOT robust top): "
              f"{pct(wrong.sum()/naive_wrong.sum())} ({int(wrong.sum()):,})")
        wrong_mid_only = naive_wrong & top_match & ~mid_match
        print(f"    top right, mid wrong (mid is not (2nd, 3rd) ranks): "
              f"{pct(wrong_mid_only.sum()/naive_wrong.sum())} ({int(wrong_mid_only.sum()):,})")

    # ==================================================================
    # 7. Cross-tabs: characterise the naive misses
    # ==================================================================
    header("7. Naive misses — what's different about them?")

    miss = naive_wrong
    sub["naive_miss"] = miss

    subhead("Miss rate by suit_max:")
    for sm in range(1, 8):
        s = sub[sub["suit_max"] == sm]
        if len(s) < 1000:
            continue
        m = s["naive_miss"].mean()
        print(f"  suit_max={sm}  n={len(s):>9,}  miss_rate={pct(m)}  "
              f"share_of_misses={pct(int((s['naive_miss']).sum())/max(int(miss.sum()),1))}")

    subhead("Miss rate by structural DS feasibility (suit_max≥2 & suit_2nd≥2):")
    for label, m in [
        ("DS feasible", structural_ds),
        ("DS infeasible", ~structural_ds),
    ]:
        s = sub[m]
        if len(s):
            mr = s["naive_miss"].mean()
            print(f"  {label:<18} n={len(s):>9,}  miss_rate={pct(mr)}")

    subhead("Miss rate by connectivity:")
    for c in range(2, 8):
        s = sub[sub["connectivity"] == c]
        if len(s) < 1000:
            continue
        mr = s["naive_miss"].mean()
        print(f"  connectivity={c}  n={len(s):>9,}  miss_rate={pct(mr)}")

    subhead("Miss rate by top_rank (highest hand-rank):")
    for r in range(2, 15):
        s = sub[sub["top_rank"] == r]
        if len(s) < 200:
            continue
        mr = s["naive_miss"].mean()
        print(f"  top_rank={r:>2}  n={len(s):>9,}  miss_rate={pct(mr)}")

    subhead("Miss rate by n_broadway:")
    for nb in range(0, 8):
        s = sub[sub["n_broadway"] == nb]
        if len(s) < 1000:
            continue
        mr = s["naive_miss"].mean()
        print(f"  n_broadway={nb}  n={len(s):>9,}  miss_rate={pct(mr)}")

    # ==================================================================
    # 8. Candidate rule: "highest goes top, mid is best DS pair from rem6"
    # ==================================================================
    header("8. Heuristic check: 'top = highest, bot = best DS, mid = leftover' on high_only")

    # Compute the rate at which:
    #   robust top == hand top_rank (highest)
    #   robust bot is double-suited (when feasible) OR random (when infeasible)
    cond_top = sub["robust_top_rank"] == sub["top_rank"]
    cond_ds_when_feasible = (
        (~structural_ds) | sub["robust_bot_is_double_suited"]
    )
    print(f"  top = highest: {pct(cond_top.mean())}")
    print(f"  DS bot when feasible: {pct(cond_ds_when_feasible.mean())}")
    print(f"  BOTH conditions: {pct((cond_top & cond_ds_when_feasible).mean())}")

    # What's the most common ROBUST mid composition for high_only?
    # Express mid as (mid_high_rank, mid_low_rank) and report top-K patterns.
    subhead("Top mid (high, low) rank patterns in robust:")
    pairs = list(zip(sub["robust_mid_high_rank"].tolist(),
                       sub["robust_mid_low_rank"].tolist()))
    series = pd.Series(pairs).value_counts(normalize=True).head(15)
    for k, v in series.items():
        print(f"    mid=({k[0]:>2},{k[1]:>2})  share={pct(v)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
