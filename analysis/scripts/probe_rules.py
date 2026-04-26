"""
First-pass rule probing on the Sprint-7 feature table.

Each "rule" below is a hypothesis about robust play. We measure two things:

  * Applicability  — what fraction of the 6M canonical hands does the rule
                     even speak to?
  * Agreement      — among hands where the rule applies, what fraction does
                     the multiway-robust setting actually follow it?

A useful rule has high applicability AND high agreement. A rule that fires
on 1% of hands and is 99% accurate is interesting only as an edge-case
escape hatch; a rule that fires on 80% of hands but only matches 55% of the
time is just noise.

Rules tested (from CURRENT_PHASE.md / resume prompt):

  R1  "If you have a pair of 9+, put it in middle"
  R2  "If a double-suited bottom is achievable in the robust setting, take it"
       (this measures: how often DOES the robust setting use a DS bot?)
  R3  "Top is the highest single card"
  R4  "When in doubt, sort and slice (setting 104)"

Plus a few stratified breakdowns (by category, by agreement_class) so we
can see whether a low-overall-agreement rule is actually solid in a useful
sub-region.
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", type=Path,
                    default=ROOT / "data" / "feature_table.parquet")
    args = ap.parse_args()

    print(f"Loading {args.table}…")
    df = pq.read_table(args.table).to_pandas()
    n = len(df)
    print(f"  {n:,} rows, {len(df.columns)} columns\n")

    print("=" * 76)
    print(f"{'Rule':<60} {'applies':>8} {'agree':>7}")
    print("=" * 76)

    def report(name: str, applies_mask: pd.Series, agreement_mask: pd.Series) -> None:
        applies = int(applies_mask.sum())
        if applies == 0:
            print(f"{name:<60} {applies:>8,}  n/a")
            return
        agree = int((applies_mask & agreement_mask).sum())
        share = applies / n
        accuracy = agree / applies
        print(f"{name:<60} {applies:>8,} ({100*share:5.1f}%)  {100*accuracy:5.1f}%")

    # ------------------------------------------------------------------
    # R1  "If you have a pair of 9+, put it in middle."
    # Applies = the hand has a 9+ pair.
    # Robust setting follows it = robust_mid_is_pair AND robust_mid_high_rank
    # equals (one of) the 9+ pair ranks.
    # ------------------------------------------------------------------
    has_high_pair = (df["n_pairs"] >= 1) & (df["pair_high_rank"] >= 9)
    # The robust setting must put a pair in mid AND the mid pair rank must be
    # ≥ 9 (we don't require it to be the SAME pair if there are two 9+ pairs).
    follows_r1 = df["robust_mid_is_pair"] & (df["robust_mid_high_rank"] >= 9)
    report("R1  9+ pair → middle (any 9+ pair)", has_high_pair, follows_r1)

    # Stricter R1: must be the highest pair specifically.
    follows_r1_strict = (
        df["robust_mid_is_pair"]
        & (df["robust_mid_high_rank"] == df["pair_high_rank"])
    )
    report("R1' 9+ pair → middle (must be HIGHEST pair)", has_high_pair, follows_r1_strict)

    # Refinement: split by category — does the rule survive when there are
    # competing pairs (two_pair / three_pair / trips_pair)?
    print()
    print("R1 refinement by hand category:")
    for cat in ("pair", "two_pair", "three_pair", "trips_pair"):
        sub_app = has_high_pair & (df["category"] == cat)
        sub_n = int(sub_app.sum())
        if sub_n == 0:
            continue
        sub_acc = (sub_app & follows_r1).sum() / sub_n
        print(f"  category={cat:<14} applies={sub_n:>9,}  agree={100*sub_acc:5.1f}%")

    # ------------------------------------------------------------------
    # R2  "Robust setting uses a double-suited bottom" — measure the rate.
    # No "applies" gate — we report the unconditional rate.
    # Then split by whether DS was achievable at all (bot_suit_max == 2 in
    # the robust setting is the result; we can also probe how often the
    # whole HAND has the structure to support a DS bot, but that's a more
    # involved combinatorial check — skip for now).
    # ------------------------------------------------------------------
    print()
    print("R2  bot is double-suited in robust setting (unconditional):")
    ds_rate = float(df["robust_bot_is_double_suited"].mean())
    print(f"  overall: {100*ds_rate:.2f}%")
    # Stratified: when is the suit profile of the WHOLE hand "balanced"?
    # If the hand has at most 3 of any suit, a DS bot is at least possible.
    ds_possible = df["suit_max"] <= 3
    ds_rate_possible = float(df.loc[ds_possible, "robust_bot_is_double_suited"].mean())
    print(f"  among hands with suit_max ≤ 3 ({100*ds_possible.mean():.1f}% of hands): "
          f"{100*ds_rate_possible:.2f}%")
    # Among hands where 4-of-a-suit blocks DS:
    print(f"  among hands with suit_max ≥ 5 (DS impossible — flush draw forced): "
          f"{100*float(df.loc[df['suit_max'] >= 5, 'robust_bot_is_double_suited'].mean()):.2f}%")

    # ------------------------------------------------------------------
    # R3  "Top is the highest single card."
    # Applies always; failure case is when robust_top_rank < top_rank.
    # ------------------------------------------------------------------
    print()
    follows_r3 = df["robust_top_rank"] == df["top_rank"]
    report("R3  Top is the highest rank in the hand", pd.Series(np.ones(n, dtype=bool)), follows_r3)

    # Stratify R3 by whether the highest rank is also paired (then putting
    # it on top breaks the pair — a known failure mode).
    print("R3 refinement: highest-rank card is paired vs not.")
    high_is_pair = df["pair_high_rank"] == df["top_rank"]
    print(f"  when highest IS paired ({int(high_is_pair.sum()):,} hands, "
          f"{100*float(high_is_pair.mean()):.1f}%): "
          f"{100*float(follows_r3[high_is_pair].mean()):.1f}% follow R3")
    print(f"  when highest is NOT paired ({int((~high_is_pair).sum()):,} hands): "
          f"{100*float(follows_r3[~high_is_pair].mean()):.1f}% follow R3")

    # ------------------------------------------------------------------
    # R4  "Setting 104 (sort-and-slice) is the robust answer."
    # ------------------------------------------------------------------
    print()
    follows_r4 = df["multiway_robust"] == 104
    report("R4  Robust setting == 104 (naive sort-and-slice)",
           pd.Series(np.ones(n, dtype=bool)), follows_r4)

    # Stratify R4 by category — when does naive win?
    print("R4 refinement by hand category:")
    for cat in ("high_only", "pair", "two_pair", "three_pair",
                "trips", "trips_pair", "quads"):
        sub = df["category"] == cat
        sub_n = int(sub.sum())
        if sub_n == 0:
            continue
        sub_acc = float(follows_r4[sub].mean())
        print(f"  category={cat:<14} share={100*float(sub.mean()):5.1f}%  "
              f"naive_wins={100*sub_acc:5.1f}%")

    # ------------------------------------------------------------------
    # Bonus: how big is the unanimous slice and what's the dominant rule
    # there? CURRENT_PHASE.md said "high card top, pair middle, double-suited
    # bottom" — let's verify on the 6M.
    # ------------------------------------------------------------------
    print()
    print("=" * 76)
    print("Unanimous-only slice (the 'easy' hands):")
    unan = df[df["agreement_class"] == "unanimous"]
    print(f"  rows: {len(unan):,} ({100*len(unan)/n:.2f}%)")
    if len(unan):
        print(f"  robust_mid_is_pair        : {100*float(unan['robust_mid_is_pair'].mean()):.2f}%")
        print(f"  robust_bot_is_double_suited: {100*float(unan['robust_bot_is_double_suited'].mean()):.2f}%")
        print(f"  robust_top_rank mean      : {float(unan['robust_top_rank'].mean()):.2f}")
        print(f"  multiway_robust == 104    : {100*float((unan['multiway_robust'] == 104).mean()):.2f}%")

    print()
    print("Contested-only slice (2-2 splits + all-distinct):")
    cont = df[df["agreement_class"].isin(["split2_2", "split1_1_1_1"])]
    print(f"  rows: {len(cont):,} ({100*len(cont)/n:.2f}%)")
    if len(cont):
        print(f"  robust_mid_is_pair        : {100*float(cont['robust_mid_is_pair'].mean()):.2f}%")
        print(f"  robust_bot_is_double_suited: {100*float(cont['robust_bot_is_double_suited'].mean()):.2f}%")
        print(f"  robust_top_rank mean      : {float(cont['robust_top_rank'].mean()):.2f}")
        print(f"  multiway_robust == 104    : {100*float((cont['multiway_robust'] == 104).mean()):.2f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
