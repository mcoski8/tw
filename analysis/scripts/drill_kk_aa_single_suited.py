"""
Session 42 deep-dive — KK/AA single-suited Rule-4-bot residual drill.

Project memory notes: KK/AA single-suited is 52.9% of KK/AA (the sub-stratum
where pair has SAME suit), with $37/1000h whole-grid below oracle within-stratum.
Rule 5 (Rainbow override) handles the rainbow case; Rule 4 handles KK/AA stay-mid
default. The single-suited case stays in mid by Rule 4 but might lose value.

This drill walks the KK + AA single-suited subset and tests:
  - V37 baseline (Rule 4 + 5 active)
  - "Pair-split with Ace top" (when Ace exists)
  - "Pair-split with kicker top"
  - "Top = highest singleton, mid = 2 lower singletons, bot = pair + 2 mid kickers"
  - oracle within "pair-to-bot" subspace

Goal: find a deterministic rule that captures part of the $37/1000h.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_kk_aa_single_suited.py
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
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
EV_TO_DOL = 10.0


def main() -> int:
    print("=" * 80)
    print("Session 42 deep-dive: KK/AA single-suited Rule-4-bot residual")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading KK+AA mask + grids ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads",
                                            "pair_high_rank"])
    mask = ((ft["n_pairs"].to_numpy() == 1)
            & (ft["n_trips"].to_numpy() == 0)
            & (ft["n_quads"].to_numpy() == 0))
    phr = ft["pair_high_rank"].to_numpy()
    target_mask = mask & ((phr == 13) | (phr == 14))
    pair_idx = np.where(target_mask)[0]
    n_target = len(pair_idx)
    pop_share_full = n_target / len(ft)
    print(f"  KK + AA pair hands: {n_target:,} ({100*pop_share_full:.4f}%)")

    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    in_pref = pair_idx < 500_000
    n_in_pref = int(in_pref.sum())
    pop_share_pref = n_in_pref / 500_000 if n_in_pref else 0.0
    print(f"  KK+AA in prefix: {n_in_pref:,}")

    full_v37 = np.zeros(n_target)
    full_oracle = np.zeros(n_target)
    full_p2b_oc = np.zeros(n_target)
    pref_v37 = np.full(n_target, np.nan)
    pref_oracle = np.full(n_target, np.nan)
    pref_p2b_oc = np.full(n_target, np.nan)

    P_arr = np.zeros(n_target, dtype=np.int8)
    pair_same_suit = np.zeros(n_target, dtype=bool)

    print(f"\n[2/3] enumerating EVs for {n_target:,} hands ...", flush=True)
    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)
        P_arr[i] = P
        pos_P = sorted(j for j in range(7) if int(ranks[j]) == P)
        pair_same_suit[i] = (int(suits[pos_P[0]]) == int(suits[pos_P[1]]))
        pos_sings = [next(j for j in range(7) if int(ranks[j]) == r)
                     for r in sings]

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()

        # Pair-to-bot oracle within: top in singletons, mid is 2 of remaining 4
        # singletons (mid is 2-singletons, no pair in mid), bot has pair + other 2
        p2b_best = -np.inf
        for top_pos in pos_sings:
            for ka in pos_sings:
                for kb in pos_sings:
                    if ka >= kb or ka == top_pos or kb == top_pos:
                        continue
                    other_sings = [j for j in pos_sings
                                   if j not in (top_pos, ka, kb)]
                    if len(other_sings) != 2:
                        continue
                    mid_a, mid_b = sorted(other_sings)
                    s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                    p2b_best = max(p2b_best, float(rowf[s]))
        full_p2b_oc[i] = p2b_best

        if cid < 500_000:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            p2b_best_p = -np.inf
            for top_pos in pos_sings:
                for ka in pos_sings:
                    for kb in pos_sings:
                        if ka >= kb or ka == top_pos or kb == top_pos:
                            continue
                        other_sings = [j for j in pos_sings
                                       if j not in (top_pos, ka, kb)]
                        if len(other_sings) != 2:
                            continue
                        mid_a, mid_b = sorted(other_sings)
                        s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                        p2b_best_p = max(p2b_best_p, float(rowp[s]))
            pref_p2b_oc[i] = p2b_best_p

        if time.time() - last_log > 10:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>6,}/{n_target:,}  rate={rate:.0f}/s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.0f}s")

    full_v37_reg = full_oracle - full_v37
    pref_v37_reg = (pref_oracle[in_pref] - pref_v37[in_pref]
                    if n_in_pref > 0 else np.array([0.0]))

    # Single-suited subset
    ss_mask = pair_same_suit
    n_ss = int(ss_mask.sum())
    ds_mask = ~pair_same_suit
    n_ds = int(ds_mask.sum())

    print(f"\n[3/3] HEADLINES (split by pair-suit-distinct vs same-suit)")
    print(f"  KK+AA pair-suits-distinct (DS-able):  {n_ds:,} ({100*n_ds/n_target:.1f}%)")
    print(f"  KK+AA pair-same-suit (SS):            {n_ss:,} ({100*n_ss/n_target:.1f}%)")
    print()
    for label, sub_mask in [("pair-distinct (DS subset)", ds_mask),
                              ("pair-same-suit (SS subset)", ss_mask),
                              ("ALL KK+AA", np.ones(n_target, dtype=bool))]:
        idxs = np.where(sub_mask)[0]
        if len(idxs) == 0:
            continue
        v37_m = full_v37_reg[idxs].mean()
        p2b_m = (full_oracle[idxs] - full_p2b_oc[idxs]).mean()
        print(f"  {label:<35}  v37 ${v37_m*EV_TO_DOL*1000:+.0f}/h  "
              f"P2B-oracle ${p2b_m*EV_TO_DOL*1000:+.0f}/h  "
              f"Δ ${(v37_m-p2b_m)*EV_TO_DOL*1000:+.0f}/h within-cat  "
              f"(${(v37_m-p2b_m)*EV_TO_DOL*1000*len(idxs)/len(ft):+.2f} whole-grid)")

    # Per-pair-rank-and-suit-pattern breakdown
    print(f"\n  Sub-breakdown:")
    for P in [13, 14]:
        for ss_label, ss_sub_mask in [("DS-able", ds_mask), ("SS-pair", ss_mask)]:
            comb_mask = (P_arr == P) & ss_sub_mask
            n_comb = int(comb_mask.sum())
            if n_comb == 0:
                continue
            v37_m = full_v37_reg[comb_mask].mean()
            p2b_m = (full_oracle[comb_mask] - full_p2b_oc[comb_mask]).mean()
            print(f"    {('K' if P==13 else 'A')}{ss_label:<10}  n={n_comb:>5,}  "
                  f"v37 ${v37_m*EV_TO_DOL*1000:+.0f}/h  "
                  f"P2B-oc ${p2b_m*EV_TO_DOL*1000:+.0f}/h")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
