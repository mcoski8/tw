"""
Session 59 — Drill HO13 follow-up: NON-MAX-TOP joint quality stratification.

Joins the per-hand v44 deep-dive parquet (HO11+HO12+HO13 sweep) with the
existing non-max-joint enumeration parquet (S58 HO10) to surface WHICH
(best_top_rank, best_mid_high) tuples in non-max joints oracle prefers
vs which v44 routes there.

The hypothesis is: v44 has `ho_v4_topNonMax_DS_ms_max_top_rank_g` (best
non-max top rank) but NOT the corresponding `best_mid_high` in those
non-max joints. So at K/Q × DS_NO_JOINT, v44 can detect "a non-max joint
with a high top is achievable" but cannot route based on the JOINT'S MID
QUALITY — which is what oracle is actually optimizing.

Cross-tab schema:
  per-(max_rank, best_top_rank_topNonMax, best_mid_high_topNonMax bucket)
  rows: n_hands, n_oracle_picks_nonmax_route, n_v44_picks_nonmax_route,
        mean_regret, total_wg_contrib

A "nonmax route pick" = pick where top != max_rank AND (bot=DS) AND mid_suited.

Reads:
  data/drill_ho_v44_per_hand_structural.parquet  (must exist)
  data/drill_ho_v43_nonmax_joint.parquet         (from S58)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v44_nonmax_quality.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

PARQ_V44 = ROOT / "data" / "drill_ho_v44_per_hand_structural.parquet"
PARQ_NONMAX = ROOT / "data" / "drill_ho_v43_nonmax_joint.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

# Maps for v44/oracle bot_suit codes — must match the codes
# tw_analysis.query.SUIT_PROFILE_* uses.
from tw_analysis.query import (  # noqa: E402
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)
SUIT_LABELS = {
    int(SUIT_PROFILE_DS): "DS",
    int(SUIT_PROFILE_SS): "SS",
    int(SUIT_PROFILE_RAINBOW): "RB",
    int(SUIT_PROFILE_THREE_ONE): "31",
    int(SUIT_PROFILE_FOUR_FLUSH): "4f",
}


def main() -> int:
    print("=" * 100)
    print("HO13 follow-up — non-max joint QUALITY stratification (v44 vs oracle)")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    if not PARQ_V44.exists():
        print(f"ERROR: missing {PARQ_V44} — run drill_high_only_v44_deepdive first.")
        return 1

    print("\nloading parquets ...", flush=True)
    p_v44 = pd.read_parquet(PARQ_V44)
    p_nm = pd.read_parquet(PARQ_NONMAX)
    print(f"  v44 deepdive rows: {len(p_v44):,}")
    print(f"  nonmax_joint rows: {len(p_nm):,}")
    df = p_v44.merge(p_nm, on=("canonical_id", "max_rank"), how="inner")
    print(f"  merged rows: {len(df):,}\n", flush=True)

    # Oracle and v44 "non-max-joint pick" = top != max_rank AND bot DS AND mid suited
    df["or_is_nonmax_joint"] = (
        (df["or_top"] != df["max_rank"])
        & (df["or_bot_suit"] == int(SUIT_PROFILE_DS))
        & (df["or_mid_suited"])
    )
    df["v44_is_nonmax_joint"] = (
        (df["v44_top"] != df["max_rank"])
        & (df["v44_bot_suit"] == int(SUIT_PROFILE_DS))
        & (df["v44_mid_suited"])
    )
    df["or_is_topMax_DS_ms"] = (
        (df["or_top"] == df["max_rank"])
        & (df["or_bot_suit"] == int(SUIT_PROFILE_DS))
        & (df["or_mid_suited"])
    )
    df["v44_is_topMax_DS_ms"] = (
        (df["v44_top"] == df["max_rank"])
        & (df["v44_bot_suit"] == int(SUIT_PROFILE_DS))
        & (df["v44_mid_suited"])
    )

    # Population: hands with n_joint_topNonMax > 0 (where non-max route is achievable)
    pop_nonmax_achievable = df[df["n_joint_topNonMax"] > 0]
    print(f"hands with non-max joint achievable: {len(pop_nonmax_achievable):,}  "
          f"({100*len(pop_nonmax_achievable)/len(df):.1f}% of high_only)\n")

    # ===========================================================
    # Stratification 1: per (max_rank, best_top_rank_topNonMax)
    # ===========================================================
    print("=" * 100)
    print("STRATIFICATION 1: oracle vs v44 non-max-route pick rate by best_top_rank")
    print("=" * 100)
    for max_r in sorted(pop_nonmax_achievable["max_rank"].unique(), reverse=True):
        sub = pop_nonmax_achievable[pop_nonmax_achievable["max_rank"] == max_r]
        if len(sub) == 0:
            continue
        print(f"\n── max_rank = {RANK_CHAR[max_r]}  (n_nonmax_avail = {len(sub):,}) ──")
        print(f"  {'best_top':>9} {'n':>9} {'oracle_nm%':>11} {'v44_nm%':>9} "
              f"{'mean_reg':>10} {'wg_contrib':>11}")
        for bt in sorted(sub["best_top_rank_topNonMax"].unique(), reverse=True):
            sub2 = sub[sub["best_top_rank_topNonMax"] == bt]
            n = len(sub2)
            if n == 0:
                continue
            or_nm = 100 * sub2["or_is_nonmax_joint"].mean()
            v44_nm = 100 * sub2["v44_is_nonmax_joint"].mean()
            mean_reg = sub2["regret"].mean() * EV_TO_DOL * 1000
            wg = sub2["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"  {RANK_CHAR.get(int(bt), str(bt)):>9} {n:>9,} "
                  f"{or_nm:>10.1f}% {v44_nm:>8.1f}% ${mean_reg:>+8.1f} "
                  f"${wg:>+9.2f}")

    # ===========================================================
    # Stratification 2: per (max_rank, best_top, best_mid_high)
    # ===========================================================
    print("\n" + "=" * 100)
    print("STRATIFICATION 2: oracle non-max-route pick rate by (best_top, best_mid)")
    print("=" * 100)
    for max_r in [13, 12, 11, 14]:  # K, Q, J, A
        sub = pop_nonmax_achievable[pop_nonmax_achievable["max_rank"] == max_r]
        if len(sub) == 0:
            continue
        # Focus on the K/Q × DS_NO_JOINT subgroup: best_top high, best_mid varied
        sub_ds_no_joint = sub[sub["n_joint_DS_ms_max_top"] == 0]
        if len(sub_ds_no_joint) == 0:
            continue
        print(f"\n── max_rank = {RANK_CHAR[max_r]}  DS_NO_JOINT subgroup  "
              f"(n = {len(sub_ds_no_joint):,}) ──")
        # Sub-stratify by (best_top, best_mid_high_nonmax) buckets.
        # Buckets for best_mid_high: low(<=7), mid(8-10), high(11+)
        def midbucket(v):
            if v >= 11:
                return "high(J+)"
            if v >= 8:
                return "mid(8-T)"
            return "low(2-7)"
        sub_ds_no_joint = sub_ds_no_joint.copy()
        sub_ds_no_joint["mid_b"] = sub_ds_no_joint["best_mid_high_topNonMax"].apply(midbucket)
        print(f"  {'best_top':>9} {'mid_b':>9} {'n':>9} {'oracle_nm%':>11} "
              f"{'v44_nm%':>9} {'mean_reg':>10} {'wg_contrib':>11}")
        for (bt, mb), sub2 in sub_ds_no_joint.groupby(["best_top_rank_topNonMax", "mid_b"]):
            n = len(sub2)
            if n < 100:
                continue
            or_nm = 100 * sub2["or_is_nonmax_joint"].mean()
            v44_nm = 100 * sub2["v44_is_nonmax_joint"].mean()
            mean_reg = sub2["regret"].mean() * EV_TO_DOL * 1000
            wg = sub2["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"  {RANK_CHAR.get(int(bt), str(bt)):>9} {mb:>9} {n:>9,} "
                  f"{or_nm:>10.1f}% {v44_nm:>8.1f}% ${mean_reg:>+8.1f} "
                  f"${wg:>+9.2f}")

    # ===========================================================
    # Diagnostic: how often does max-rank end up paired in the bot
    # within oracle's non-max joint picks?
    # The signal would be: best_bot_pair_high_topNonMax >= max_rank.
    # ===========================================================
    print("\n" + "=" * 100)
    print("DIAGNOSTIC 3: max-rank-in-bot-pair signature within non-max joint route")
    print("=" * 100)
    for max_r in [13, 12, 11, 14]:
        sub = pop_nonmax_achievable[pop_nonmax_achievable["max_rank"] == max_r]
        if len(sub) == 0:
            continue
        sub2 = sub[sub["best_bot_pair_high_topNonMax"] == max_r]
        n = len(sub2)
        if n == 0:
            print(f"  max={RANK_CHAR[max_r]}: no hands where non-max joint has max-in-bot-pair")
            continue
        or_nm = 100 * sub2["or_is_nonmax_joint"].mean()
        v44_nm = 100 * sub2["v44_is_nonmax_joint"].mean()
        mean_reg = sub2["regret"].mean() * EV_TO_DOL * 1000
        wg = sub2["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        # Compare to non-max joint achievable but WITHOUT max-in-bot-pair
        sub3 = sub[sub["best_bot_pair_high_topNonMax"] != max_r]
        or_nm3 = 100 * sub3["or_is_nonmax_joint"].mean() if len(sub3) else float("nan")
        v44_nm3 = 100 * sub3["v44_is_nonmax_joint"].mean() if len(sub3) else float("nan")
        print(f"  max={RANK_CHAR[max_r]}: max-in-bot-pair n={n:,}  "
              f"oracle_nm={or_nm:.1f}%  v44_nm={v44_nm:.1f}%  "
              f"mean=${mean_reg:+.1f}  wg=${wg:+.2f}")
        print(f"    (vs other     n={len(sub3):,}  oracle_nm={or_nm3:.1f}%  "
              f"v44_nm={v44_nm3:.1f}%)")

    # ===========================================================
    # Diagnostic 4: 4-flush+ms top=max route — does v44 capture it?
    # ===========================================================
    print("\n" + "=" * 100)
    print("DIAGNOSTIC 4: 4f+ms top=max route capture (S58 ho_v4 #2 axis)")
    print("=" * 100)
    sub4f = df[df["n_topMax_4f_ms"] > 0]
    print(f"  hands with topMax_4f_ms achievable: {len(sub4f):,}  "
          f"({100*len(sub4f)/len(df):.1f}% of high_only)")
    for max_r in sorted(sub4f["max_rank"].unique(), reverse=True):
        sub = sub4f[sub4f["max_rank"] == max_r]
        if len(sub) == 0:
            continue
        # Oracle pick = 4f bot AND top=max AND mid suited
        oracle_4f_pick = (
            (sub["or_bot_suit"] == int(SUIT_PROFILE_FOUR_FLUSH))
            & (sub["or_top"] == max_r)
            & (sub["or_mid_suited"])
        )
        v44_4f_pick = (
            (sub["v44_bot_suit"] == int(SUIT_PROFILE_FOUR_FLUSH))
            & (sub["v44_top"] == max_r)
            & (sub["v44_mid_suited"])
        )
        mean_reg = sub["regret"].mean() * EV_TO_DOL * 1000
        print(f"  max={RANK_CHAR[max_r]}: n={len(sub):,}  "
              f"oracle_4f_topmax={100*oracle_4f_pick.mean():.1f}%  "
              f"v44_4f_topmax={100*v44_4f_pick.mean():.1f}%  "
              f"mean_reg=${mean_reg:+.1f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
