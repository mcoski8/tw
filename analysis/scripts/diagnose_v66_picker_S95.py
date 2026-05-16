"""S95 diagnostic — why does v66 swap-right rate (36-48%) lag the sub-bucket
predictivity (P(oracle=DS) = 57-90%) so dramatically?

Hypothesis: the rule's deterministic "best DS bot" picker selects a DIFFERENT
DS config than oracle's. Predictivity measured DIRECTION (oracle picks SOME DS),
but the rule has to pick a SPECIFIC DS. If oracle's DS pick differs from
ours, we're effectively a random DS picker among DS-achievable configs.

Diagnostic: among hands where oracle picks DS AND rule fires, what fraction
match oracle's exact setting? What's the average EV gap (oracle - rule's DS)
vs (oracle - v65's non-DS)?
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

from strategy_v66_trips_layout_a_force_ds_bot import (  # noqa: E402
    _detect_trips_layout_a_force_ds_bot,
    GATE_TRIGGERS,
)
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

DATA = ROOT / "data"


def main():
    df = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    c1 = df[df["cell_idx"] == 1]
    target = c1[(c1["v44_layout"] == 0) & (c1["v44_bot_suit"] != 0)].copy()
    print(f"target n={len(target):,}")

    ch = read_canonical_hands(DATA / "canonical_hands.bin", mode="memmap")
    hands_arr = ch.hands
    grid = read_oracle_grid(DATA / "oracle_grid_full_realistic_n200.bin", mode="memmap")
    evs = grid.evs

    canonical_ids = target["canonical_id"].astype(np.int64).to_numpy()
    v44_idx = target["v44_idx"].astype(np.int16).to_numpy()
    oracle_idx = target["oracle_idx"].astype(np.int16).to_numpy()
    or_bot_suit = target["or_bot_suit"].astype(np.int8).to_numpy()
    or_layout = target["or_layout"].astype(np.int8).to_numpy()
    ksc = target["kickers_max_suit_count"].astype(np.int8).to_numpy()
    nkts = target["n_kickers_in_trip_suits"].astype(np.int8).to_numpy()
    nbds = target["n_b_ds_routings"].astype(np.int8).to_numpy()

    n_target = len(target)

    # Compute v66 forced picks (WIDE)
    print("computing v66 picks at WIDE...")
    triggers = GATE_TRIGGERS["WIDE"]
    v66_pick = np.empty(n_target, dtype=np.int16)
    fired = np.zeros(n_target, dtype=bool)
    t0 = time.time()
    for i in range(n_target):
        cid = int(canonical_ids[i])
        h = np.asarray(hands_arr[cid], dtype=np.uint8)
        forced = _detect_trips_layout_a_force_ds_bot(h, triggers)
        if forced is None:
            v66_pick[i] = v44_idx[i]
        else:
            v66_pick[i] = int(forced)
            fired[i] = True
    print(f"  done in {time.time()-t0:.1f}s, fired={int(fired.sum()):,}")

    # Diagnostic per gate
    print("\nDiagnostic — among FIRED + ORACLE PICKS DS hands:")
    print("  match_rate = P(v66_pick == oracle_pick)")
    print("  Among hands where rule fires AND oracle agrees on direction (DS),")
    print("  what's the rule's specific-setting-match rate?")
    print("")
    for gate_name in ["NARROW", "MEDIUM", "WIDE"]:
        triggers = GATE_TRIGGERS[gate_name]
        mask = np.zeros(n_target, dtype=bool)
        for tk in triggers:
            mask |= ((ksc == tk[0]) & (nkts == tk[1]) & (nbds == tk[2]))
        # Among fired in this gate
        sub = mask & fired
        # Among fired AND oracle picks DS (or_bot_suit==0)
        sub_ds = sub & (or_bot_suit == 0)
        n_sub = int(sub.sum())
        n_sub_ds = int(sub_ds.sum())
        n_match = int(((v66_pick == oracle_idx) & sub_ds).sum())
        # Among fired AND oracle picks DS — EV gap
        if n_sub_ds > 0:
            sample_idx = np.where(sub_ds)[0]
            ev_oracle = np.array([evs[int(canonical_ids[i])][int(oracle_idx[i])] for i in sample_idx])
            ev_v65 = np.array([evs[int(canonical_ids[i])][int(v44_idx[i])] for i in sample_idx])
            ev_v66 = np.array([evs[int(canonical_ids[i])][int(v66_pick[i])] for i in sample_idx])
            d_v66_minus_v65 = (ev_v66 - ev_v65).mean()
            d_oracle_minus_v65 = (ev_oracle - ev_v65).mean()
            d_v66_minus_oracle = (ev_v66 - ev_oracle).mean()
            recapture = (d_v66_minus_v65 / d_oracle_minus_v65) if d_oracle_minus_v65 != 0 else 0.0
        else:
            d_v66_minus_v65 = d_oracle_minus_v65 = d_v66_minus_oracle = recapture = 0.0
        # Also check: among ALL fired hands (including where oracle picks non-DS)
        if n_sub > 0:
            si = np.where(sub)[0]
            ev_o = np.array([evs[int(canonical_ids[i])][int(oracle_idx[i])] for i in si])
            ev_v = np.array([evs[int(canonical_ids[i])][int(v44_idx[i])] for i in si])
            ev_r = np.array([evs[int(canonical_ids[i])][int(v66_pick[i])] for i in si])
            d_all_v66_v65 = (ev_r - ev_v).mean()
        else:
            d_all_v66_v65 = 0.0

        print(f"  Gate {gate_name}:")
        print(f"    fired:                                  {n_sub:>6,}")
        print(f"    fired AND oracle picks DS:              {n_sub_ds:>6,}  ({n_sub_ds/max(n_sub,1)*100:.1f}% of fired)")
        print(f"    Rule pick matches oracle exactly:       {n_match:>6,}  ({n_match/max(n_sub_ds,1)*100:.1f}% of fired+oracle-DS)")
        print(f"    Mean EV(v66 - v65) on fired+oracle-DS:  {d_v66_minus_v65*1000:+.4f} ev_units")
        print(f"    Mean EV(oracle - v65) on fired+oracle-DS: {d_oracle_minus_v65*1000:+.4f} ev_units")
        print(f"    Mean EV(v66 - oracle) on fired+oracle-DS: {d_v66_minus_oracle*1000:+.4f} ev_units")
        print(f"    Recapture rate (v66 vs oracle):         {recapture*100:.1f}%")
        print(f"    Mean EV(v66 - v65) on ALL fired hands:  {d_all_v66_v65*1000:+.4f} ev_units")
        print()

    # Per-sub-bucket breakdown for WIDE
    print("\nPer-sub-bucket diagnostic (WIDE):")
    print(f"  {'ksc':>3} {'nkts':>4} {'nbds':>4} | {'n_fired':>7} | {'P_or_DS':>7} | {'match_idx':>9} | {'EV(v66-v65)':>11} | {'EV(or-v65)':>10}")
    rows_diag = []
    for tk in sorted(GATE_TRIGGERS["WIDE"]):
        sub_mask = (
            (ksc == tk[0]) & (nkts == tk[1]) & (nbds == tk[2])
        ) & fired
        si = np.where(sub_mask)[0]
        n = len(si)
        if n == 0:
            continue
        n_ords = int((or_bot_suit[si] == 0).sum())
        si_ords = si[(or_bot_suit[si] == 0)]
        n_match = int((v66_pick[si_ords] == oracle_idx[si_ords]).sum())
        ev_r = np.array([evs[int(canonical_ids[i])][int(v66_pick[i])] for i in si])
        ev_v = np.array([evs[int(canonical_ids[i])][int(v44_idx[i])] for i in si])
        ev_o = np.array([evs[int(canonical_ids[i])][int(oracle_idx[i])] for i in si])
        d_r = (ev_r - ev_v).mean()
        d_o = (ev_o - ev_v).mean()
        print(f"  {tk[0]:>3} {tk[1]:>4} {tk[2]:>4} | {n:>7,} | {n_ords/n*100:>6.1f}% | {n_match/max(n_ords,1)*100:>8.1f}% | {d_r*1000:>+10.4f} | {d_o*1000:>+9.4f}")
        rows_diag.append({"ksc": tk[0], "nkts": tk[1], "nbds": tk[2], "n_fired": n,
                          "p_or_ds": n_ords/n, "exact_match_rate": n_match/max(n_ords,1),
                          "ev_v66_minus_v65_mean": d_r, "ev_oracle_minus_v65_mean": d_o})

    return 0


if __name__ == "__main__":
    sys.exit(main())
