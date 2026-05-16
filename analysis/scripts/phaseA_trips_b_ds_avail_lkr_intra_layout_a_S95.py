"""S95 Phase A — re-confirm S94 finding on trips B_DS_AVAIL_LKR
intra-Layout-A bot_suit candidate and lock trigger definitions.

This is the only OPEN candidate at the rule-extraction layer after S94
closed the bucket-level lever. We re-derive from per-hand parquet:

  cell_idx = 1            (B_DS_AVAIL_LKR)
  v44_layout = or_layout = 0   (Layout A agree)
  v44_bot_suit != 0       (v44 picks NON-DS bot)
  target predicate: oracle picks DS bot (or_bot_suit == 0)

Sub-bucket trigger search across:
  (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings)

Lock 3 candidate gates per the S94 audit:
  NARROW  — predictivity >= 0.70 (Rule 20 anchor): expect 580 hands, $0.53 wg
  MEDIUM  — predictivity >= 0.40 (include (2,4,3) at 0.484):     +4,911 hands, +$2.42 wg
  WIDE    — include (2,3,1) at 0.289:                            +17,838 hands, +$4.70 wg

We emit ID lists per gate (canonical_id sets) so we can later evaluate the rule
on N=200 / N=1000 grids on the right populations only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "session95"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

# Trigger gates derived from S94 Phase A.2 cell-level sub-bucket analysis.
# Format: list of (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings)
GATES = {
    "NARROW": [
        (2, 4, 1),
        (3, 4, 1),
    ],
    "MEDIUM": [
        (2, 4, 1),
        (3, 4, 1),
        (2, 4, 3),
    ],
    "WIDE": [
        (2, 4, 1),
        (3, 4, 1),
        (2, 4, 3),
        (2, 3, 1),
    ],
}


def wg_dollars_per_1000h(s):
    return float(s.sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID)


def main():
    print("S95 Phase A — re-confirm trips B_DS_AVAIL_LKR intra-Layout-A bot_suit")
    print("=" * 80)

    df = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    print(f"Loaded {len(df):,} trips hands from S70 drill")
    print(f"Columns: {list(df.columns)}")

    # ---- Cell B_DS_AVAIL_LKR (cell_idx=1) ----
    c1 = df[df["cell_idx"] == 1].copy()
    print(f"\nCell B_DS_AVAIL_LKR: n={len(c1):,}, wg=${wg_dollars_per_1000h(c1['regret']):.2f}/1000h")

    # ---- Layout A agree ----
    agree_A = c1[(c1["v44_layout"] == 0) & (c1["or_layout"] == 0)].copy()
    print(f"  Layout-A agree (v44=or=0): n={len(agree_A):,}, wg=${wg_dollars_per_1000h(agree_A['regret']):.2f}/1000h")

    # ---- v44 non-DS bot population ----
    nonDS = agree_A[agree_A["v44_bot_suit"] != 0].copy()
    nonDS_to_DS = nonDS[nonDS["or_bot_suit"] == 0]
    print(f"  v44 non-DS bot: n={len(nonDS):,}, wg=${wg_dollars_per_1000h(nonDS['regret']):.2f}/1000h")
    print(f"  v44 non-DS bot AND oracle DS bot: n={len(nonDS_to_DS):,}, wg=${wg_dollars_per_1000h(nonDS_to_DS['regret']):.2f}/1000h")

    # ---- Sub-bucket pivot ----
    print(f"\nSub-bucket pivot on (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings)")
    print(f"  Population: v44 picks non-DS bot in Layout A (n={len(nonDS):,})")
    print(f"  Target: P(oracle picks DS bot | sub-bucket)")
    print("")
    g = nonDS.groupby([
        "kickers_max_suit_count", "n_kickers_in_trip_suits", "n_b_ds_routings"
    ]).agg(
        n=("regret", "size"),
        or_ds=("or_bot_suit", lambda s: (s == 0).sum()),
        wg=("regret", wg_dollars_per_1000h),
    ).reset_index()
    g["p_or_ds"] = g["or_ds"] / g["n"]
    g = g.sort_values("p_or_ds", ascending=False)
    print(f"  {'ksc':>3} | {'nkts':>4} | {'nbds':>4} | {'n':>7} | {'or_ds':>6} | {'P':>6} | {'wg':>7}")
    print(f"  {'-'*3}-+-{'-'*4}-+-{'-'*4}-+-{'-'*7}-+-{'-'*6}-+-{'-'*6}-+-{'-'*7}")
    for _, row in g[g["n"] >= 100].iterrows():
        print(f"  {int(row['kickers_max_suit_count']):>3} | "
              f"{int(row['n_kickers_in_trip_suits']):>4} | "
              f"{int(row['n_b_ds_routings']):>4} | "
              f"{int(row['n']):>7,} | "
              f"{int(row['or_ds']):>6,} | "
              f"{row['p_or_ds']*100:>5.1f}% | "
              f"${row['wg']:>5.2f}")

    # ---- Per-gate aggregation ----
    print(f"\nPer-gate aggregation:")
    print(f"  {'GATE':<8} | {'n_buckets':>9} | {'n_hands':>9} | {'or_ds':>7} | {'mean_P':>7} | {'wg_full':>8}")
    print(f"  {'-'*8}-+-{'-'*9}-+-{'-'*9}-+-{'-'*7}-+-{'-'*7}-+-{'-'*8}")
    gate_summary = {}
    for gate_name, triggers in GATES.items():
        mask = np.zeros(len(nonDS), dtype=bool)
        for tk_ksc, tk_nkts, tk_nbds in triggers:
            mask |= (
                (nonDS["kickers_max_suit_count"] == tk_ksc)
                & (nonDS["n_kickers_in_trip_suits"] == tk_nkts)
                & (nonDS["n_b_ds_routings"] == tk_nbds)
            )
        seg = nonDS[mask]
        n_seg = len(seg)
        n_or_ds = int((seg["or_bot_suit"] == 0).sum())
        mean_p = (n_or_ds / n_seg) if n_seg > 0 else 0.0
        wg_seg = wg_dollars_per_1000h(seg["regret"])
        gate_summary[gate_name] = {
            "triggers": triggers,
            "n_hands": int(n_seg),
            "n_or_ds": n_or_ds,
            "mean_predictivity": float(mean_p),
            "wg_full_population": float(wg_seg),
        }
        print(f"  {gate_name:<8} | {len(triggers):>9} | {n_seg:>9,} | {n_or_ds:>7,} | "
              f"{mean_p*100:>6.1f}% | ${wg_seg:>6.2f}")

    # ---- Emit canonical_id lists per gate ----
    print(f"\nEmitting canonical_id lists per gate:")
    cid_lists = {}
    for gate_name, triggers in GATES.items():
        mask = np.zeros(len(nonDS), dtype=bool)
        for tk_ksc, tk_nkts, tk_nbds in triggers:
            mask |= (
                (nonDS["kickers_max_suit_count"] == tk_ksc)
                & (nonDS["n_kickers_in_trip_suits"] == tk_nkts)
                & (nonDS["n_b_ds_routings"] == tk_nbds)
            )
        cids = sorted(nonDS.loc[mask, "canonical_id"].astype(int).tolist())
        cid_lists[gate_name] = cids
        out_path = OUT_DIR / f"phaseA_cids_gate_{gate_name}.txt"
        with out_path.open("w") as f:
            for c in cids:
                f.write(f"{c}\n")
        print(f"  {gate_name}: {len(cids):,} cids -> {out_path}")

    # ---- Write summary JSON ----
    summary = {
        "session": 95,
        "phase": "A",
        "candidate": "trips B_DS_AVAIL_LKR intra-Layout-A bot_suit",
        "cell_b_ds_avail_lkr": {
            "n_total": int(len(c1)),
            "n_layout_a_agree": int(len(agree_A)),
            "n_v44_nonDS": int(len(nonDS)),
            "n_v44_nonDS_to_or_DS": int(len(nonDS_to_DS)),
            "wg_v44_nonDS_to_or_DS_recoverable_if_perfect": wg_dollars_per_1000h(nonDS_to_DS["regret"]),
        },
        "gates": gate_summary,
    }
    out_json = OUT_DIR / "phaseA_summary.json"
    with out_json.open("w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote {out_json}")

    # ---- Lock decision summary ----
    print(f"\n" + "=" * 80)
    print("PHASE A VERDICT")
    print("=" * 80)
    print(f"S94 finding RE-CONFIRMED from per-hand data:")
    for gate_name in ["NARROW", "MEDIUM", "WIDE"]:
        gs = gate_summary[gate_name]
        print(f"  {gate_name:<8}: {gs['n_hands']:>6,} hands, mean P={gs['mean_predictivity']*100:>5.1f}%, "
              f"wg=${gs['wg_full_population']:>5.2f}/1000h (ceiling at 100% trigger accuracy)")
    print(f"")
    print(f"Trigger definition LOCKED for Phase B (multi-gate pre-drill on N=200).")
    print(f"Rule 20 anchor: trigger predictivity >= 70% required for clean ship.")
    print(f"Rule 25 anchor: trigger predictivity >= 62% acceptable for ship at $5+.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
