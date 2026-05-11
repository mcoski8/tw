"""
Session 58 — Drill HO9: DS-vs-SS trade-off threshold per max_rank.

QUESTION (from user S57 review):
  When DS+ms is achievable but the suited mid would be a low pair, does
  oracle pick:
    a) JOINT (top=max, DS bot, ms mid) with low mid_high
    b) SS+ms with HIGHER mid_high (outside JOINT)
    c) DS_mu with highest available mid (no mid suiting)
    d) 4f / 31 / RB
  And per max_rank, what's the break-even mid_high threshold where
  oracle switches between (a) and (b)?

METHOD:
  Reads the per-hand parquet from drill HO5+HO6+HO7. For hands with
  n_joint_DS_ms_max_top > 0 (joint achievable), stratify by:
    - max_rank
    - best_ms_mid_high (joint mid_high quality)
    - best_ms_mid_high_anytop − best_ms_mid_high
       (gap = how much HIGHER an SS-route mid would be vs joint mid)
  Then for each cell, compute the fraction where oracle picked:
    JOINT_PICK      : top=max AND bot=DS AND mid suited
    DS_NONJOINT     : bot=DS but NOT (top=max AND mid suited)
    SS_MS_NONMAX    : bot=SS, mid suited, top ≠ max
    SS_MS_MAX       : bot=SS, mid suited, top = max
    SS_MU           : bot=SS, mid unsuited
    OTHER           : 4f / 31 / RB
  The threshold: at what (max_rank, best_ms_mid_high) does JOINT_PICK
  fraction cross 50%?

OUTPUTS:
  Per (max_rank, best_ms_mid_high) cell: oracle pick distribution.
  Per max_rank: break-even mid_high.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v43_threshold.py
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

from tw_analysis.query import (  # noqa: E402
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)

PARQUET = ROOT / "data" / "drill_ho_v43_per_hand_structural.parquet"
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def classify_oracle_pick(row):
    is_top_max = row["or_top"] == row["max_rank"]
    is_DS = row["or_bot_suit"] == SUIT_PROFILE_DS
    is_SS = row["or_bot_suit"] == SUIT_PROFILE_SS
    is_ms = row["or_mid_suited"]
    if is_top_max and is_DS and is_ms:
        return "JOINT_PICK"
    if is_DS and not (is_top_max and is_ms):
        return "DS_NONJOINT"
    if is_SS and is_ms:
        return "SS_MS_MAX" if is_top_max else "SS_MS_NONMAX"
    if is_SS and not is_ms:
        return "SS_MU"
    return "OTHER"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", type=Path, default=PARQUET)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 58 — Drill HO9: DS-vs-SS trade-off threshold per max_rank")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print(f"\n[1/3] reading parquet {args.parquet} ...", flush=True)
    df = pd.read_parquet(args.parquet)
    print(f"  rows: {len(df):,}")

    # Vectorized oracle-pick classification
    is_top_max = df["or_top"] == df["max_rank"]
    is_DS = df["or_bot_suit"] == SUIT_PROFILE_DS
    is_SS = df["or_bot_suit"] == SUIT_PROFILE_SS
    is_ms = df["or_mid_suited"].astype(bool)

    df["or_class"] = "OTHER"
    df.loc[is_top_max & is_DS & is_ms, "or_class"] = "JOINT_PICK"
    df.loc[is_DS & ~(is_top_max & is_ms), "or_class"] = "DS_NONJOINT"
    df.loc[is_SS & is_ms & is_top_max, "or_class"] = "SS_MS_MAX"
    df.loc[is_SS & is_ms & ~is_top_max, "or_class"] = "SS_MS_NONMAX"
    df.loc[is_SS & ~is_ms, "or_class"] = "SS_MU"

    # === Per-max-rank pick distribution overall ===
    print("\n" + "=" * 100)
    print("Overall oracle-pick distribution per max_rank")
    print("=" * 100)
    classes = ["JOINT_PICK", "DS_NONJOINT", "SS_MS_MAX", "SS_MS_NONMAX",
                "SS_MU", "OTHER"]
    for mr in sorted(df["max_rank"].unique(), reverse=True):
        sub = df[df["max_rank"] == mr]
        n = len(sub)
        if n == 0:
            continue
        counts = sub["or_class"].value_counts()
        line = f"  max={RANK_CHAR[mr]:>2}  n={n:>8,}: "
        line += "  ".join(f"{c}:{100*counts.get(c,0)/n:>5.1f}%" for c in classes)
        print(line)

    # === Cell: max_rank × n_joint > 0 (joint achievable) × best_ms_mid_high ===
    print("\n" + "=" * 100)
    print("HO9: WHEN JOINT ACHIEVABLE — oracle pick fraction by max_rank x best_ms_mid_high")
    print("=" * 100)
    joint = df[df["n_joint_DS_ms_max_top"] > 0].copy()
    print(f"  hands with joint achievable: {len(joint):,} ({100*len(joint)/len(df):.1f}% of high_only)")

    print(f"\n  {'max':>3} {'mid_high':>9} {'n':>8} "
          + "  ".join(f"{c:>13}" for c in classes))
    for mr in sorted(joint["max_rank"].unique(), reverse=True):
        sub_max = joint[joint["max_rank"] == mr]
        for mid_h in sorted(sub_max["best_ms_mid_high"].unique(), reverse=True):
            sub = sub_max[sub_max["best_ms_mid_high"] == mid_h]
            n = len(sub)
            if n == 0:
                continue
            counts = sub["or_class"].value_counts()
            row = f"  {RANK_CHAR[mr]:>3} {RANK_CHAR.get(mid_h, mid_h):>9} {n:>8,} "
            row += "  ".join(f"{100*counts.get(c,0)/n:>12.1f}%" for c in classes)
            print(row)
        print()

    # === Threshold finder: at what best_ms_mid_high does JOINT_PICK fraction cross 50% per max_rank? ===
    print("\n" + "=" * 100)
    print("HO9: Joint-pick threshold per max_rank (at what mid_high does JOINT fraction cross 50%?)")
    print("=" * 100)
    print(f"  {'max':>3} {'best_mid_h':>10} {'n':>8} {'%joint':>8}")
    for mr in sorted(joint["max_rank"].unique(), reverse=True):
        sub_max = joint[joint["max_rank"] == mr]
        for mid_h in sorted(sub_max["best_ms_mid_high"].unique()):
            sub = sub_max[sub_max["best_ms_mid_high"] == mid_h]
            n = len(sub)
            if n < 10:
                continue
            pct_joint = 100 * (sub["or_class"] == "JOINT_PICK").sum() / n
            print(f"  {RANK_CHAR[mr]:>3} {RANK_CHAR.get(mid_h, mid_h):>10} {n:>8,} "
                  f"{pct_joint:>7.1f}%")
        print()

    # === Cross: gap between (mid_high in joint) and (mid_high any-top) ===
    # If best_ms_mid_high_anytop > best_ms_mid_high, there's a stronger SS+ms route
    # outside the joint. Does oracle take the SS+ms route as the gap grows?
    print("\n" + "=" * 100)
    print("HO9: When SS+ms NON-MAX mid_high is HIGHER than joint mid_high — does oracle swap?")
    print("=" * 100)
    joint["mid_high_gap"] = joint["best_ms_mid_high_anytop"] - joint["best_ms_mid_high"]
    print(f"  {'max':>3} {'gap':>4} {'n':>8} {'%JOINT':>8} {'%SS_MS_NONMAX':>14}")
    for mr in sorted(joint["max_rank"].unique(), reverse=True):
        sub_max = joint[joint["max_rank"] == mr]
        for gap in sorted(sub_max["mid_high_gap"].unique()):
            sub = sub_max[sub_max["mid_high_gap"] == gap]
            n = len(sub)
            if n < 50:
                continue
            pct_joint = 100 * (sub["or_class"] == "JOINT_PICK").sum() / n
            pct_ssms_nonmax = 100 * (sub["or_class"] == "SS_MS_NONMAX").sum() / n
            print(f"  {RANK_CHAR[mr]:>3} {int(gap):>4} {n:>8,} {pct_joint:>7.1f}% "
                  f"{pct_ssms_nonmax:>13.1f}%")
        print()

    # === Inverse: when DS_pair_high is high vs low — does oracle prefer JOINT? ===
    print("\n" + "=" * 100)
    print("HO9: best_DS_bot_pair_high stratification (within joint-avail hands)")
    print("=" * 100)
    print(f"  {'max':>3} {'DS_pair_h':>9} {'n':>8} {'%JOINT':>8} {'%DS_NONJOINT':>14}")
    for mr in sorted(joint["max_rank"].unique(), reverse=True):
        sub_max = joint[joint["max_rank"] == mr]
        for ph in sorted(sub_max["best_DS_bot_pair_high"].unique()):
            sub = sub_max[sub_max["best_DS_bot_pair_high"] == ph]
            n = len(sub)
            if n < 50:
                continue
            pct_joint = 100 * (sub["or_class"] == "JOINT_PICK").sum() / n
            pct_ds_nonjoint = 100 * (sub["or_class"] == "DS_NONJOINT").sum() / n
            print(f"  {RANK_CHAR[mr]:>3} {RANK_CHAR.get(ph, ph):>9} {n:>8,} "
                  f"{pct_joint:>7.1f}% {pct_ds_nonjoint:>13.1f}%")
        print()

    # === v43 vs oracle JOINT take-rate (where joint is avail) ===
    print("\n" + "=" * 100)
    print("v43 vs oracle JOINT take-rate (where joint is achievable)")
    print("=" * 100)
    is_top_max_v = joint["v43_top"] == joint["max_rank"]
    is_DS_v = joint["v43_bot_suit"] == SUIT_PROFILE_DS
    is_ms_v = joint["v43_mid_suited"].astype(bool)
    joint["v43_class"] = "OTHER"
    joint.loc[is_top_max_v & is_DS_v & is_ms_v, "v43_class"] = "JOINT_PICK"

    print(f"  {'max':>3} {'mid_high':>9} {'n':>8} {'%v43_JOINT':>11} {'%or_JOINT':>11} {'gap':>6}")
    for mr in sorted(joint["max_rank"].unique(), reverse=True):
        sub_max = joint[joint["max_rank"] == mr]
        for mid_h in sorted(sub_max["best_ms_mid_high"].unique(), reverse=True):
            sub = sub_max[sub_max["best_ms_mid_high"] == mid_h]
            n = len(sub)
            if n < 50:
                continue
            v43_pct = 100 * (sub["v43_class"] == "JOINT_PICK").sum() / n
            or_pct = 100 * (sub["or_class"] == "JOINT_PICK").sum() / n
            gap = or_pct - v43_pct
            print(f"  {RANK_CHAR[mr]:>3} {RANK_CHAR.get(mid_h, mid_h):>9} {n:>8,} "
                  f"{v43_pct:>10.1f}% {or_pct:>10.1f}% {gap:>+5.1f}")
        print()

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
