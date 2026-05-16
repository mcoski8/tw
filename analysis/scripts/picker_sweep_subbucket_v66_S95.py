"""S95 — break out TOP_HIGH picker results per sub-bucket to find any slice
clearing the $5 SHIP bar.

Also test additional tighter criteria (TOP_HIGH with tertiary tiebreakers).
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
for p in (str(HERE), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from picker_sweep_v66_S95 import enumerate_layout_a_ds_bot_settings  # noqa: E402
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

DATA = ROOT / "data"
EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159


CRITERIA = {
    "TOP_HIGH_then_pair_tops": lambda c: (c["top_rank"], c["pair_top_1"], c["pair_top_2"]),
    "TOP_HIGH_then_pair_tops_then_botmin_lo": lambda c: (
        c["top_rank"], c["pair_top_1"], c["pair_top_2"], -c["bot_min"]
    ),
    "TOP_HIGH_then_pair_tops_then_botmin_hi": lambda c: (
        c["top_rank"], c["pair_top_1"], c["pair_top_2"], c["bot_min"]
    ),
    "TOP_HIGH_then_pair_top_2_lo": lambda c: (
        c["top_rank"], c["pair_top_1"], -c["pair_top_2"]
    ),
    "TOP_HIGH_then_pair_top_2_hi": lambda c: (
        c["top_rank"], c["pair_top_2"], c["pair_top_1"]
    ),
}


def main():
    df = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    c1 = df[df["cell_idx"] == 1]
    target = c1[(c1["v44_layout"] == 0) & (c1["v44_bot_suit"] != 0)].copy()
    canonical_ids = target["canonical_id"].astype(np.int64).to_numpy()
    v44_idx = target["v44_idx"].astype(np.int16).to_numpy()
    oracle_idx = target["oracle_idx"].astype(np.int16).to_numpy()
    or_bot_suit = target["or_bot_suit"].astype(np.int8).to_numpy()
    ksc = target["kickers_max_suit_count"].astype(np.int8).to_numpy()
    nkts = target["n_kickers_in_trip_suits"].astype(np.int8).to_numpy()
    nbds = target["n_b_ds_routings"].astype(np.int8).to_numpy()
    n_target = len(target)
    print(f"target n={n_target:,}")

    ch = read_canonical_hands(DATA / "canonical_hands.bin", mode="memmap")
    hands_arr = ch.hands
    grid = read_oracle_grid(DATA / "oracle_grid_full_realistic_n200.bin", mode="memmap")
    evs = grid.evs

    # Enumerate Layout-A DS-bot configs once
    print("enumerating Layout-A DS configs ...")
    t0 = time.time()
    all_configs = []
    for i in range(n_target):
        cid = int(canonical_ids[i])
        h = np.asarray(hands_arr[cid], dtype=np.uint8)
        cfgs = list(enumerate_layout_a_ds_bot_settings(h))
        all_configs.append(cfgs if cfgs else None)
    print(f"  done in {time.time()-t0:.1f}s")

    # Sub-buckets of interest (from S94 / Phase A)
    SUB_BUCKETS = [
        (2, 4, 1),  # P=100%
        (3, 4, 1),  # P=88%
        (2, 4, 3),  # P=63%
        (2, 3, 1),  # P=46%
        (2, 2, 1),  # P=10%
        (1, 3, 3),  # P=0%
    ]

    print("\n" + "=" * 100)
    print("Per-sub-bucket lift under each TOP_HIGH variant:")
    print("=" * 100)
    print(f"  {'criterion':<42} | {'(ksc,nkts,nbds)':<16} | {'n':>7} | {'chg':>7} | {'sr%':>6} | {'lift':>9}")
    print(f"  {'-'*42}-+-{'-'*16}-+-{'-'*7}-+-{'-'*7}-+-{'-'*6}-+-{'-'*9}")

    results = []
    for crit_name, crit_fn in CRITERIA.items():
        # pre-compute picker
        rule_pick = np.empty(n_target, dtype=np.int16)
        for i in range(n_target):
            cfgs = all_configs[i]
            if cfgs is None:
                rule_pick[i] = v44_idx[i]
            else:
                rule_pick[i] = int(max(cfgs, key=crit_fn)["setting_idx"])

        for tk in SUB_BUCKETS:
            mask = (ksc == tk[0]) & (nkts == tk[1]) & (nbds == tk[2])
            applicable = mask & np.array([c is not None for c in all_configs])
            n_app = int(applicable.sum())
            if n_app == 0:
                continue
            v66 = np.where(applicable, rule_pick, v44_idx)
            n_chg = int((v66 != v44_idx).sum())
            sum_delta = 0.0
            n_better = 0
            for i in np.where(applicable)[0]:
                cid = int(canonical_ids[i])
                er = evs[cid]
                d = float(er[int(v66[i])]) - float(er[int(v44_idx[i])])
                sum_delta += d
                if d > 0: n_better += 1
            lift = sum_delta / N_TOTAL_GRID * EV_TO_DOL * 1000
            sr = (n_better / n_chg) if n_chg > 0 else 0.0
            results.append({
                "criterion": crit_name, "sub_bucket": tk,
                "n_applicable": n_app, "n_changed": n_chg,
                "swap_right": sr, "lift_dol_per_1000h_n200": lift,
            })
            print(f"  {crit_name:<42} | ({tk[0]},{tk[1]},{tk[2]}){'':<10} | "
                  f"{n_app:>7,} | {n_chg:>7,} | {sr*100:>5.1f}% | ${lift:>+7.2f}")

    # Also: cumulative combinations using top criterion
    print("\n" + "=" * 100)
    print("Cumulative gate slices under TOP_HIGH_then_pair_tops:")
    print("=" * 100)
    crit_fn = CRITERIA["TOP_HIGH_then_pair_tops"]
    rule_pick = np.empty(n_target, dtype=np.int16)
    for i in range(n_target):
        cfgs = all_configs[i]
        if cfgs is None:
            rule_pick[i] = v44_idx[i]
        else:
            rule_pick[i] = int(max(cfgs, key=crit_fn)["setting_idx"])

    SLICES = {
        "(3,4,1) only":             [(3, 4, 1)],
        "(2,4,1) only":             [(2, 4, 1)],
        "(2,4,1)+(3,4,1) [NARROW]": [(2, 4, 1), (3, 4, 1)],
        "(2,4,3) only":             [(2, 4, 3)],
        "NARROW + (2,4,3) [MEDIUM]": [(2, 4, 1), (3, 4, 1), (2, 4, 3)],
        "(2,3,1) only":             [(2, 3, 1)],
        "(2,2,1) only":             [(2, 2, 1)],
        "all nkts=4 sub-buckets":   [(2, 4, 1), (3, 4, 1), (2, 4, 3)],
    }
    print(f"  {'slice':<32} | {'n_changed':>9} | {'sr%':>6} | {'lift':>9}")
    for slice_name, triggers in SLICES.items():
        mask = np.zeros(n_target, dtype=bool)
        for tk in triggers:
            mask |= ((ksc == tk[0]) & (nkts == tk[1]) & (nbds == tk[2]))
        applicable = mask & np.array([c is not None for c in all_configs])
        n_app = int(applicable.sum())
        v66 = np.where(applicable, rule_pick, v44_idx)
        n_chg = int((v66 != v44_idx).sum())
        sum_delta = 0.0
        n_better = 0
        for i in np.where(applicable)[0]:
            cid = int(canonical_ids[i])
            er = evs[cid]
            d = float(er[int(v66[i])]) - float(er[int(v44_idx[i])])
            sum_delta += d
            if d > 0: n_better += 1
        lift = sum_delta / N_TOTAL_GRID * EV_TO_DOL * 1000
        sr = (n_better / n_chg) if n_chg > 0 else 0.0
        flag = "  SHIP" if lift >= 5.0 else ("  null" if lift <= 1.0 else "  mid")
        print(f"  {slice_name:<32} | {n_chg:>9,} | {sr*100:>5.1f}% | ${lift:>+7.2f} {flag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
