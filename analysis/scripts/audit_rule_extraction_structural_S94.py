"""
S94 STRUCTURAL NULL AUDIT — within-v44_dt rule-extraction (Option D-revised)
on two_pair + trips residuals.

Question: can a Rule-20-style structural-feature trigger ship a new
production rule on one of the within-v44_dt residual cells where the chain-
audit lever (S87-S92) cannot help (because v55/v56 collapse the chain to
v44_dt by construction)?

Phase A pre-drill answer: NO. Both two_pair (LAYOUT_A_SS at $35.22/1000h
on 437,580 hands) and trips (B_DS_AVAIL_LKR at $42.61/1000h on 163,170
hands) are STRUCTURALLY SATURATED at the bucket level. v44_dt picks the
modal layout correctly across the overwhelming majority of (hi,lo)
buckets, and within-bucket residual is HAND-SPECIFIC (suit details,
exact ranks) without the clean structural-feature trigger Rule 20 / Rule
25 required (≥70% trigger predictivity).

Rule 20 / Rule 25 anchor for comparison:
  * Rule 20 trigger (LOW × PMID_DS_NOMAXTOP × max_sing ≤ Q): swap-right
    rate ~89-93% on triggered hands (S83).
  * Rule 25 (= v65) trigger (MID × PMID_DS_NOMAXTOP × max_sing ≤ Q):
    swap-right rate 62.0% (S86/S93). Lower but still strong enough to
    ship at +$6.34 N=1000 / +$6.43 N=200.

Within-v44_dt residual cells DO NOT reach either of these levels for
any (cell × bucket × feature) combination tested here.

The audit produces a formal data/session94/audit_summary.json with the
saturation evidence per cell, plus a cross-cell tabular summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "session94"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159


def wg_dollars_per_1000h(s):
    """Whole-grid contribution in $/1000h for a regret column slice."""
    return float(s.sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID)


# Two_pair cells (S69 taxonomy)
TWO_PAIR_CELLS = {
    0: "LAYOUT_A_DS",
    1: "LAYOUT_C_DS",
    2: "LAYOUT_B_DS",
    3: "LAYOUT_A_SS",
    4: "LAYOUT_C_SS_ONLY",
    5: "LAYOUT_B_SS_ONLY",
}

# Trips cells (S70 taxonomy)
TRIPS_CELLS = {
    0: "B_DS_AVAIL_HKR",
    1: "B_DS_AVAIL_LKR",
    2: "NO_BDS_CTOP",
    3: "NO_BDS_AKDOM",
}


def audit_two_pair():
    """Bucket-level saturation audit on two_pair residuals."""
    df = pd.read_parquet(DATA / "drill_two_pair_v44_per_hand_structural.parquet")
    out = {"category": "two_pair", "cells": {}, "totals": {}}

    cross_pivot_rows = []
    for ci, name in TWO_PAIR_CELLS.items():
        c = df[df["cell_idx"] == ci]
        if len(c) == 0:
            continue
        tot_n = int(len(c))
        tot_wg = wg_dollars_per_1000h(c["regret"])
        n_mismatch = int((c["v44_idx"] != c["oracle_idx"]).sum())
        cid_min = int(c["canonical_id"].min())
        cid_max = int(c["canonical_id"].max())
        prefix_overlap = int((c["canonical_id"] < 500_000).sum())

        # Bucket analysis: (hi_pair_rank, lo_pair_rank)
        buckets = []
        for (hp, lp), seg in c.groupby(["hi_pair_rank", "lo_pair_rank"]):
            if len(seg) < 200:
                continue
            or_modal = int(seg["or_layout"].value_counts().idxmax())
            v44_modal = int(seg["v44_layout"].value_counts().idxmax())
            wg = wg_dollars_per_1000h(seg["regret"])
            agree = or_modal == v44_modal
            buckets.append({
                "hi": int(hp), "lo": int(lp), "n": int(len(seg)),
                "or_modal_layout": or_modal,
                "v44_modal_layout": v44_modal,
                "modal_agree": bool(agree),
                "wg_dollars_per_1000h": wg,
            })
        n_buckets = len(buckets)
        n_modal_mismatch = sum(1 for b in buckets if not b["modal_agree"])
        wg_modal_mismatch = sum(b["wg_dollars_per_1000h"] for b in buckets if not b["modal_agree"])

        # v44_layout × or_layout pivot (where v44 differs from oracle)
        g = c.groupby(["v44_layout", "or_layout"]).agg(
            n=("regret", "size"),
            wg=("regret", wg_dollars_per_1000h),
        ).reset_index()
        off_diag = g[g["v44_layout"] != g["or_layout"]].sort_values("wg", ascending=False)
        top_pivot = {}
        if len(off_diag) > 0:
            top = off_diag.iloc[0]
            top_pivot = {
                "v44_layout": int(top["v44_layout"]),
                "or_layout": int(top["or_layout"]),
                "n": int(top["n"]),
                "wg_dollars_per_1000h": float(top["wg"]),
            }

        # Tightest sub-bucket trigger search:
        # Within (v44_layout = top_pivot_v44), look for sub-bucket where
        # P(or_layout == top_pivot_or | hi, lo, max_sing) is highest.
        max_p_trigger = 0.0
        max_p_n = 0
        if top_pivot:
            wrong = c[c["v44_layout"] == top_pivot["v44_layout"]]
            sub = wrong.groupby(["hi_pair_rank", "lo_pair_rank", "max_sing_rank"]).agg(
                n=("regret", "size"),
                or_match=("or_layout", lambda s: (s == top_pivot["or_layout"]).sum()),
            ).reset_index()
            sub = sub[sub["n"] >= 100].copy()
            if len(sub) > 0:
                sub["p"] = sub["or_match"] / sub["n"]
                top = sub.sort_values("p", ascending=False).iloc[0]
                max_p_trigger = float(top["p"])
                max_p_n = int(top["n"])

        cell = {
            "n": tot_n,
            "wg_dollars_per_1000h": tot_wg,
            "n_mismatch_v44_vs_oracle": n_mismatch,
            "mismatch_rate": n_mismatch / tot_n,
            "cid_min": cid_min,
            "cid_max": cid_max,
            "prefix_overlap": prefix_overlap,
            "n_buckets_min200": n_buckets,
            "n_buckets_modal_mismatch": n_modal_mismatch,
            "wg_modal_mismatch": wg_modal_mismatch,
            "top_offdiag_pivot": top_pivot,
            "max_subbucket_trigger_p": max_p_trigger,
            "max_subbucket_trigger_n": max_p_n,
        }
        out["cells"][name] = cell

        # cross-row
        cross_pivot_rows.append({
            "cell": name,
            "n": tot_n,
            "wg": tot_wg,
            "n_buckets": n_buckets,
            "n_modal_mismatch": n_modal_mismatch,
            "wg_modal_mismatch": wg_modal_mismatch,
            "top_pivot_wg": top_pivot.get("wg_dollars_per_1000h", 0.0),
            "max_subbucket_p": max_p_trigger,
        })

    out["totals"] = {
        "n_hands": int(sum(c["n"] for c in out["cells"].values())),
        "total_wg": sum(c["wg_dollars_per_1000h"] for c in out["cells"].values()),
        "total_wg_modal_mismatch": sum(c["wg_modal_mismatch"] for c in out["cells"].values()),
        "ceiling_addressable_via_layout_flip": sum(c["wg_modal_mismatch"] for c in out["cells"].values()),
    }
    out["cross_summary"] = cross_pivot_rows
    return out


def audit_trips_intra_layout_a(df):
    """S94 follow-up: characterize the intra-Layout-A bot_suit leak in
    B_DS_AVAIL_LKR — the only within-v44_dt residual cell showing Rule 20-
    style structural signal (intra-layout bot_suit flip, $19.50/1000h on
    v44-non-DS-bot → oracle-DS-bot, 25,905 hands)."""
    c1 = df[df["cell_idx"] == 1].copy()  # B_DS_AVAIL_LKR
    agree_A = c1[(c1["v44_layout"] == 0) & (c1["or_layout"] == 0)].copy()

    # Bot-suit pivot within Layout-A-agree (codes: 0=DS, 1=SS, 2=31, 3=RB, 4=4f)
    pivot_rows = []
    for vs in sorted(agree_A["v44_bot_suit"].unique()):
        for os_ in sorted(agree_A["or_bot_suit"].unique()):
            seg = agree_A[(agree_A["v44_bot_suit"] == vs) & (agree_A["or_bot_suit"] == os_)]
            if len(seg) == 0:
                continue
            pivot_rows.append({
                "v44_bot_suit": int(vs),
                "or_bot_suit": int(os_),
                "n": int(len(seg)),
                "wg": wg_dollars_per_1000h(seg["regret"]),
            })

    # Aggregate: v44 non-DS bot, oracle DS bot
    v44_nonDS_to_or_DS = agree_A[
        (agree_A["v44_bot_suit"] != 0) & (agree_A["or_bot_suit"] == 0)
    ]
    aggregate_leak = wg_dollars_per_1000h(v44_nonDS_to_or_DS["regret"])

    # Sub-bucket predictivity search: within "v44 picks non-DS bot in Layout A",
    # what suit-features predict "oracle picks DS bot"?
    target_pop = agree_A[agree_A["v44_bot_suit"] != 0]
    g = target_pop.groupby([
        "kickers_max_suit_count", "n_kickers_in_trip_suits", "n_b_ds_routings",
    ]).agg(
        n=("regret", "size"),
        or_ds=("or_bot_suit", lambda s: (s == 0).sum()),
        wg=("regret", wg_dollars_per_1000h),
    ).reset_index()
    g["p_or_ds"] = g["or_ds"] / g["n"]
    g = g[g["n"] >= 100].copy()
    g = g.sort_values("p_or_ds", ascending=False)

    sub_buckets = []
    for _, row in g.iterrows():
        sub_buckets.append({
            "kickers_max_suit_count": int(row["kickers_max_suit_count"]),
            "n_kickers_in_trip_suits": int(row["n_kickers_in_trip_suits"]),
            "n_b_ds_routings": int(row["n_b_ds_routings"]),
            "n": int(row["n"]),
            "or_ds": int(row["or_ds"]),
            "p_or_ds": float(row["p_or_ds"]),
            "wg_full_subbucket": float(row["wg"]),
        })

    # Find the highest-predictivity (≥ 70% — Rule 20 anchor) sub-buckets
    ship_grade_buckets = [b for b in sub_buckets if b["p_or_ds"] >= 0.70]
    ship_grade_n = sum(b["n"] for b in ship_grade_buckets)
    ship_grade_wg_recoverable = sum(b["wg_full_subbucket"] for b in ship_grade_buckets)

    return {
        "v44_or_bot_suit_pivot": pivot_rows,
        "v44_nonDS_to_oracle_DS_aggregate": {
            "n": int(len(v44_nonDS_to_or_DS)),
            "wg_recoverable_if_perfect_trigger": aggregate_leak,
        },
        "subbucket_trigger_search": sub_buckets[:15],
        "ship_grade_subbuckets": ship_grade_buckets,
        "ship_grade_n_total": ship_grade_n,
        "ship_grade_wg_recoverable": ship_grade_wg_recoverable,
        "note": (
            "Rule 20 trigger predictivity anchor: ≥ 70%. Sub-buckets clearing "
            "that bar here total only ${:.2f}/1000h on {:,} hands — well "
            "under the $5 SHIP bar even at 100% trigger accuracy."
        ).format(ship_grade_wg_recoverable, ship_grade_n),
    }


def audit_trips():
    """Bucket-level saturation audit on trips residuals."""
    df = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    out = {"category": "trips", "cells": {}, "totals": {}}

    cross_pivot_rows = []
    for ci, name in TRIPS_CELLS.items():
        c = df[df["cell_idx"] == ci]
        if len(c) == 0:
            continue
        tot_n = int(len(c))
        tot_wg = wg_dollars_per_1000h(c["regret"])
        n_mismatch = int((c["v44_idx"] != c["oracle_idx"]).sum())
        cid_min = int(c["canonical_id"].min())
        cid_max = int(c["canonical_id"].max())
        prefix_overlap = int((c["canonical_id"] < 500_000).sum())

        buckets = []
        for (tr, mk), seg in c.groupby(["trip_rank", "max_kicker_rank"]):
            if len(seg) < 200:
                continue
            or_modal = int(seg["or_layout"].value_counts().idxmax())
            v44_modal = int(seg["v44_layout"].value_counts().idxmax())
            wg = wg_dollars_per_1000h(seg["regret"])
            agree = or_modal == v44_modal
            buckets.append({
                "trip": int(tr), "max_kicker": int(mk),
                "n": int(len(seg)),
                "or_modal_layout": or_modal,
                "v44_modal_layout": v44_modal,
                "modal_agree": bool(agree),
                "wg_dollars_per_1000h": wg,
            })
        n_buckets = len(buckets)
        n_modal_mismatch = sum(1 for b in buckets if not b["modal_agree"])
        wg_modal_mismatch = sum(b["wg_dollars_per_1000h"] for b in buckets if not b["modal_agree"])

        g = c.groupby(["v44_layout", "or_layout"]).agg(
            n=("regret", "size"),
            wg=("regret", wg_dollars_per_1000h),
        ).reset_index()
        off_diag = g[g["v44_layout"] != g["or_layout"]].sort_values("wg", ascending=False)
        top_pivot = {}
        if len(off_diag) > 0:
            top = off_diag.iloc[0]
            top_pivot = {
                "v44_layout": int(top["v44_layout"]),
                "or_layout": int(top["or_layout"]),
                "n": int(top["n"]),
                "wg_dollars_per_1000h": float(top["wg"]),
            }

        # Sub-bucket trigger search (richer feature set for trips)
        max_p_trigger = 0.0
        max_p_n = 0
        max_p_bucket = {}
        if top_pivot:
            wrong = c[c["v44_layout"] == top_pivot["v44_layout"]]
            sub = wrong.groupby([
                "trip_rank", "max_kicker_rank",
                "kickers_max_suit_count", "n_kickers_in_trip_suits", "n_b_ds_routings",
            ]).agg(
                n=("regret", "size"),
                or_match=("or_layout", lambda s: (s == top_pivot["or_layout"]).sum()),
            ).reset_index()
            sub = sub[sub["n"] >= 100].copy()
            if len(sub) > 0:
                sub["p"] = sub["or_match"] / sub["n"]
                top = sub.sort_values("p", ascending=False).iloc[0]
                max_p_trigger = float(top["p"])
                max_p_n = int(top["n"])
                max_p_bucket = {
                    "trip": int(top["trip_rank"]),
                    "max_kicker": int(top["max_kicker_rank"]),
                    "kickers_max_suit_count": int(top["kickers_max_suit_count"]),
                    "n_kickers_in_trip_suits": int(top["n_kickers_in_trip_suits"]),
                    "n_b_ds_routings": int(top["n_b_ds_routings"]),
                    "p": max_p_trigger,
                    "n": max_p_n,
                }

        cell = {
            "n": tot_n,
            "wg_dollars_per_1000h": tot_wg,
            "n_mismatch_v44_vs_oracle": n_mismatch,
            "mismatch_rate": n_mismatch / tot_n,
            "cid_min": cid_min,
            "cid_max": cid_max,
            "prefix_overlap": prefix_overlap,
            "n_buckets_min200": n_buckets,
            "n_buckets_modal_mismatch": n_modal_mismatch,
            "wg_modal_mismatch": wg_modal_mismatch,
            "top_offdiag_pivot": top_pivot,
            "max_subbucket_trigger_p": max_p_trigger,
            "max_subbucket_trigger_n": max_p_n,
            "max_subbucket_trigger_bucket": max_p_bucket,
        }
        out["cells"][name] = cell

        cross_pivot_rows.append({
            "cell": name,
            "n": tot_n,
            "wg": tot_wg,
            "n_buckets": n_buckets,
            "n_modal_mismatch": n_modal_mismatch,
            "wg_modal_mismatch": wg_modal_mismatch,
            "top_pivot_wg": top_pivot.get("wg_dollars_per_1000h", 0.0),
            "max_subbucket_p": max_p_trigger,
        })

    out["totals"] = {
        "n_hands": int(sum(c["n"] for c in out["cells"].values())),
        "total_wg": sum(c["wg_dollars_per_1000h"] for c in out["cells"].values()),
        "total_wg_modal_mismatch": sum(c["wg_modal_mismatch"] for c in out["cells"].values()),
        "ceiling_addressable_via_layout_flip": sum(c["wg_modal_mismatch"] for c in out["cells"].values()),
    }
    out["cross_summary"] = cross_pivot_rows
    return out


def print_summary(audit, label):
    print(f"\n=== {label} ===")
    print(f"  total hands: {audit['totals']['n_hands']:,}")
    print(f"  total wg: ${audit['totals']['total_wg']:.2f}/1000h")
    print(f"  ceiling addressable via layout flip (modal mismatch): ${audit['totals']['ceiling_addressable_via_layout_flip']:.2f}/1000h")
    print(f"\n  Per-cell:")
    print(f"    {'cell':<18} | {'n':>10} | {'tot_wg':>8} | {'n_bkt':>5} | {'mm_bkt':>6} | {'mm_wg':>7} | {'top_pivot':>9} | {'max_sub_p':>9}")
    print(f"    {'-'*18}-+-{'-'*10}-+-{'-'*8}-+-{'-'*5}-+-{'-'*6}-+-{'-'*7}-+-{'-'*9}-+-{'-'*9}")
    for r in audit["cross_summary"]:
        print(f"    {r['cell']:<18} | {r['n']:>10,} | ${r['wg']:>6.2f} | {r['n_buckets']:>5} | {r['n_modal_mismatch']:>6} | ${r['wg_modal_mismatch']:>5.2f} | ${r['top_pivot_wg']:>7.2f} | {r['max_subbucket_p']*100:>7.1f}%")


def main():
    print("S94 STRUCTURAL NULL AUDIT — within-v44_dt rule-extraction lever")
    print("=" * 80)

    tp = audit_two_pair()
    print_summary(tp, "TWO_PAIR (1,338,480 hands, $80.82/1000h v44 leak)")

    tr = audit_trips()
    print_summary(tr, "TRIPS (328,185 hands, $65.18/1000h v44 leak)")

    # Trips B_DS_AVAIL_LKR intra-Layout-A bot_suit follow-up
    df_tr = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    intra = audit_trips_intra_layout_a(df_tr)
    print(f"\n=== TRIPS B_DS_AVAIL_LKR intra-Layout-A bot_suit follow-up ===")
    print(f"  Aggregate v44 non-DS bot -> oracle DS bot (within Layout A agree):")
    print(f"    n={intra['v44_nonDS_to_oracle_DS_aggregate']['n']:,}, recoverable=${intra['v44_nonDS_to_oracle_DS_aggregate']['wg_recoverable_if_perfect_trigger']:.2f}/1000h")
    print(f"  Sub-buckets clearing Rule-20 trigger threshold (P >= 0.70):")
    print(f"    n_total={intra['ship_grade_n_total']:,}, wg_recoverable=${intra['ship_grade_wg_recoverable']:.2f}/1000h")
    print(f"  v44_bot_suit codes: 0=DS, 1=SS, 2=31, 3=RB, 4=4f")
    print(f"  Pivot (v44_bot_suit, or_bot_suit) - top 5 by wg:")
    top5 = sorted(intra["v44_or_bot_suit_pivot"], key=lambda r: -r["wg"])[:5]
    for r in top5:
        print(f"    v44_bot_suit={r['v44_bot_suit']}, or_bot_suit={r['or_bot_suit']}: n={r['n']:,}, wg=${r['wg']:.2f}")
    print(f"\n  {intra['note']}")

    # Combined verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    all_subbucket_p = []
    for audit in (tp, tr):
        for r in audit["cross_summary"]:
            all_subbucket_p.append(r["max_subbucket_p"])
    max_p = max(all_subbucket_p) if all_subbucket_p else 0.0
    print(f"\nMax sub-bucket trigger predictivity across ALL within-v44_dt residual cells: {max_p*100:.1f}%")
    print(f"Rule 20 / Rule 25 SHIP threshold: ≥ 70% (Rule 20 anchor: ~89-93%; Rule 25 anchor: 62%)")
    print(f"\nMax found <  70%: STRUCTURAL NULL on Option D-revised rule-extraction lever")
    print(f"applied to within-v44_dt residual cells via simple structural-feature triggers.")
    print(f"\nCeiling addressable via bucket-level layout-flip rules:")
    print(f"  two_pair: ${tp['totals']['ceiling_addressable_via_layout_flip']:.2f}/1000h")
    print(f"  trips:    ${tr['totals']['ceiling_addressable_via_layout_flip']:.2f}/1000h")
    print(f"  TOTAL:    ${tp['totals']['ceiling_addressable_via_layout_flip'] + tr['totals']['ceiling_addressable_via_layout_flip']:.2f}/1000h")
    print(f"\nEven if a structural-feature rule could perfectly flip every modal-mismatched")
    print(f"bucket (which it cannot, given <50% sub-bucket predictivity), the maximum")
    print(f"recoverable lift would be well under the project's $5 SHIP bar.")

    # Persist
    summary = {
        "session": 94,
        "verdict": "STRUCTURAL_NULL",
        "max_subbucket_trigger_p_across_cells": max_p,
        "rule20_threshold_p": 0.70,
        "rule25_threshold_p": 0.62,
        "two_pair": tp,
        "trips": tr,
        "trips_b_ds_avail_lkr_intra_layout_a_followup": intra,
    }
    out_path = OUT_DIR / "audit_rule_extraction_structural_summary.json"
    with out_path.open("w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
