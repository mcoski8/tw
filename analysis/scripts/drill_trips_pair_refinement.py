"""
Session 42 deep-dive — trips_pair (Rule 3) refinement.

Rule 3 (trips_pair, 3+2+2): "split trips, keep pair, build DS bot".
Existing implementation is heuristic. Within-cat residual at v34_dt is
$1,225/1000h. Could a deterministic suit-aware refinement help?

Structures (T=trip rank, P=pair rank, K=kicker):
  G1: top = T-member, mid = 2 T-leftovers (paired-by-trip), bot = P+P+K+K
       (Layout A — paired mid via trip)
  G2: top = T-member, mid = P+K (mixed), bot = 2T+P-leftover+K
       (some Layout-B variant)
  G3: top = K, mid = 2-T-leftovers, bot = P+P+T+K
       (top is a kicker, paired-mid via trip, bot is 2-pair plus T)

Test deterministic candidates with suit-aware top-T pick.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_pair_refinement.py
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
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
    print("Session 42 deep-dive: trips_pair (Rule 3) refinement")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading trips_pair mask + grid ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    mask = ((ft["n_pairs"].to_numpy() == 1)
            & (ft["n_trips"].to_numpy() == 1)
            & (ft["n_quads"].to_numpy() == 0))
    n_tp = int(mask.sum())
    tp_idx = np.where(mask)[0]
    pop_share_full = n_tp / len(ft)
    print(f"  trips_pair: {n_tp:,} ({100*pop_share_full:.4f}%)")

    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    in_pref = tp_idx < 500_000
    pop_share_pref = int(in_pref.sum()) / 500_000

    # Sample 30K hands for quick analysis
    sample_size = min(30_000, n_tp)
    rng = np.random.default_rng(42)
    sample_pos = rng.choice(np.arange(n_tp), sample_size, replace=False)
    sample_idx = tp_idx[sample_pos]

    print(f"\n[2/3] enumerating {sample_size:,} hand sample ...", flush=True)
    full_v37 = np.zeros(sample_size)
    full_oracle = np.zeros(sample_size)
    full_G1 = np.zeros(sample_size)  # heuristic G1
    full_G1_oc = np.zeros(sample_size)  # G1 oracle within
    full_G2_oc = np.zeros(sample_size)
    full_G3_oc = np.zeros(sample_size)
    pref_v37 = np.full(sample_size, np.nan)
    pref_oracle = np.full(sample_size, np.nan)
    pref_G1 = np.full(sample_size, np.nan)
    is_in_pref = np.zeros(sample_size, dtype=bool)

    T_arr = np.zeros(sample_size, dtype=np.int8)
    P_arr = np.zeros(sample_size, dtype=np.int8)

    t0 = time.time()
    for i, cid in enumerate(sample_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        T = next(r for r in range(2, 15) if rc[r] == 3)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)
        T_arr[i] = T
        P_arr[i] = P
        pos_T = sorted(j for j in range(7) if int(ranks[j]) == T)
        pos_P = sorted(j for j in range(7) if int(ranks[j]) == P)
        pos_K1 = next(j for j in range(7) if int(ranks[j]) == sings[0])
        pos_K2 = next(j for j in range(7) if int(ranks[j]) == sings[1])
        # Heuristic top-T pick: T-member at suit ∉ {pair_suits ∪ kicker_suits}
        forbidden = set(int(suits[j]) for j in pos_P) | {int(suits[pos_K1]), int(suits[pos_K2])}
        outside = [j for j in pos_T if int(suits[j]) not in forbidden]
        top_T = outside[0] if outside else pos_T[0]
        mid_a, mid_b = sorted(j for j in pos_T if j != top_T)
        g1_setting = _setting_index_from_tmb(top_T, mid_a, mid_b)

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()
        full_G1[i] = rowf[g1_setting]

        # G1 oracle: 3 top-T choices
        g1_best = -np.inf
        for top_pos in pos_T:
            mid_a_, mid_b_ = sorted(j for j in pos_T if j != top_pos)
            s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
            g1_best = max(g1_best, float(rowf[s]))
        full_G1_oc[i] = g1_best

        # G2: top=T-member, mid=P+K (mixed unpaired), bot=remaining 4
        # 3 top-T × 2 mids of {P_a + K_1, P_a + K_2, P_b + K_1, P_b + K_2} = 12
        g2_best = -np.inf
        for top_pos in pos_T:
            for p_idx in range(2):
                for K_pos in [pos_K1, pos_K2]:
                    mid_a_ = pos_P[p_idx]
                    mid_b_ = K_pos
                    if mid_a_ == top_pos or mid_b_ == top_pos:
                        continue
                    if mid_a_ > mid_b_:
                        mid_a_, mid_b_ = mid_b_, mid_a_
                    s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
                    g2_best = max(g2_best, float(rowf[s]))
        full_G2_oc[i] = g2_best

        # G3: top=K, mid=2-T-leftovers (= 2 of 3 trip cards, paired)
        # 2 K choices × 3 (which T-not-in-mid) = 6
        g3_best = -np.inf
        for top_pos in [pos_K1, pos_K2]:
            for k_idx in range(3):
                T_bot = pos_T[k_idx]
                mid_a_, mid_b_ = sorted(j for j in pos_T if j != T_bot)
                s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
                g3_best = max(g3_best, float(rowf[s]))
        full_G3_oc[i] = g3_best

        if cid < 500_000:
            is_in_pref[i] = True
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            pref_G1[i] = rowp[g1_setting]

    print(f"  done in {time.time()-t0:.0f}s")
    n_in_pref = int(is_in_pref.sum())

    full_v37_reg = full_oracle - full_v37
    pref_v37_reg = pref_oracle[is_in_pref] - pref_v37[is_in_pref]

    # Compute Δ vs v37
    def compute(picked_full, picked_pref=None, label="", kind="det"):
        full_reg = full_oracle - picked_full
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        s = f"  {label:<55}  full ${full_delta:>+8.2f}/1000h"
        if picked_pref is not None:
            pref_reg = pref_oracle[is_in_pref] - picked_pref[is_in_pref]
            pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
            s += f"  pref ${pref_delta:>+8.2f}/1000h"
        s += f"  [{kind}]"
        print(s)

    print(f"\n[3/3] HEADLINES")
    print(f"  v37 baseline regret on trips_pair sample: full ${full_v37_reg.mean()*EV_TO_DOL*1000:+.1f}/1000h "
          f"(${full_v37_reg.mean()*EV_TO_DOL*1000*pop_share_full:+.2f} whole-grid)")

    compute(full_v37, pref_v37, "v37 baseline", "actual")
    print(f"  {'─'*100}")
    compute(full_G1, pref_G1, "G1 deterministic (suit-aware top-T, paired-mid)")
    compute(full_G1_oc, label="G1 oracle within (best top-T choice)", kind="oracle")
    compute(full_G2_oc, label="G2 oracle (mid=P+K, unpaired)", kind="oracle")
    compute(full_G3_oc, label="G3 oracle (top=K, mid=2T paired)", kind="oracle")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
