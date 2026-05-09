"""
Session 42 deep-dive — T2P (trips_two_pair, 3+2+2) heuristic-refinement drill.

verify_rule_X_v33_composite.py headlines (full grid):
  v33 within-st mean regret: $7,210/1000h
  Best heuristic-realizable ceiling: TBD (probe used oracle-within-constraint)
  T2P_split_trip_top oracle: +$7.64 whole-grid (the highest ceiling)
  v33 top: trip_member=4,562 (66%), lo_pair=1,898 (28%), hi_pair=404 (6%)
  v33 mid: trip-leftover=3,495 (51%), hi-pair=2,521 (37%), lo-pair=552, unpaired=296

Goal: find a deterministic rule that captures most of the +$7.64 ceiling.

Structural classes for T2P (3+2+2, where T=trip rank, H=hi-pair rank, L=lo-pair rank):

  F1 (trip-split + 2-pair-bot):
       top = T-member, mid = pair-of-T-leftovers, bot = HH + LL (4 cards = 2-pair Omaha)
  F2 (trip + hi-pair-mid):
       top = T-member, mid = HH (high pair), bot = 2T + LL
  F3 (trip + lo-pair-mid):
       top = T-member, mid = LL (low pair), bot = 2T + HH
  F4 (split-hi-pair):
       top = H-member, mid = T-leftover-pair (any 2 of 3 trip), bot = H + 1T + LL
  F5 (split-lo-pair):
       top = L-member, mid = T-leftover-pair, bot = L + 1T + HH

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/drill_t2p_trips_two_pair_deterministic.py
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

EV_TO_DOL = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 42 deep-dive: T2P (trips_two_pair) heuristic drill")
    print("=" * 80)

    print("\n[1/4] identifying T2P (3+2+2) hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    t2p_idx = []
    for cid in np.where(cats == 7)[0]:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        n_q = int(sum(rc[r] >= 4 for r in range(2, 15)))
        n_t = int(sum(rc[r] == 3 for r in range(2, 15)))
        n_p = int(sum(rc[r] == 2 for r in range(2, 15)))
        if n_t == 1 and n_p == 2 and n_q == 0:
            t2p_idx.append(int(cid))
    n_t2p = len(t2p_idx)
    pop_share_full = n_t2p / len(ch.hands)
    print(f"  T2P (trips_two_pair): {n_t2p:,} hands  ({100*pop_share_full:.4f}%)")

    print("\n[2/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    print(f"\n[3/4] enumerating per-hand structural EVs ...", flush=True)
    full_v37 = np.full(n_t2p, np.nan)
    full_oracle = np.full(n_t2p, np.nan)
    full_F1 = np.full(n_t2p, np.nan)  # deterministic
    full_F2 = np.full(n_t2p, np.nan)
    full_F3 = np.full(n_t2p, np.nan)
    full_F1_oc = np.full(n_t2p, np.nan)  # oracle within class
    full_F2_oc = np.full(n_t2p, np.nan)
    full_F3_oc = np.full(n_t2p, np.nan)
    full_F4_oc = np.full(n_t2p, np.nan)
    full_F5_oc = np.full(n_t2p, np.nan)
    pref_v37 = np.full(n_t2p, np.nan)
    pref_oracle = np.full(n_t2p, np.nan)
    pref_F1 = np.full(n_t2p, np.nan)
    pref_F2 = np.full(n_t2p, np.nan)
    pref_F3 = np.full(n_t2p, np.nan)

    T_arr = np.zeros(n_t2p, dtype=np.int8)
    H_arr = np.zeros(n_t2p, dtype=np.int8)
    L_arr = np.zeros(n_t2p, dtype=np.int8)
    in_pref = np.zeros(n_t2p, dtype=bool)

    t0 = time.time()
    last_log = time.time()

    for i, cid in enumerate(t2p_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        T = next(r for r in range(2, 15) if rc[r] == 3)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        H, L = pairs
        T_arr[i] = T
        H_arr[i] = H
        L_arr[i] = L
        pos_T = sorted(j for j in range(7) if int(ranks[j]) == T)
        pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
        pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
        pair_H_suits = sorted(int(suits[j]) for j in pos_H)
        pair_L_suits = sorted(int(suits[j]) for j in pos_L)
        in_pref[i] = (cid < 500_000)

        # F1 deterministic: top = T-member, mid = pair-of-T-leftovers,
        #   bot = HH + LL.
        # Which T-member splits to top? With 3 T cards at 3 distinct suits,
        # the choice is suit-driven. Mirror QP: pick top = T-member at the suit
        # that's NOT in {pair_H_suits ∪ pair_L_suits}.
        all_pair_suits = set(pair_H_suits) | set(pair_L_suits)
        # T has 3 cards at 3 distinct suits; 1 suit is missing.
        T_suits = sorted(int(suits[j]) for j in pos_T)
        # Heuristic: pick top = T at suit ∉ all_pair_suits if possible, else
        # any tiebreaker (e.g., lowest position).
        outside = [j for j in pos_T if int(suits[j]) not in all_pair_suits]
        if outside:
            top_T = outside[0]
        else:
            top_T = pos_T[0]
        mid_a, mid_b = sorted(j for j in pos_T if j != top_T)
        f1_setting = _setting_index_from_tmb(top_T, mid_a, mid_b)

        # F2: top = T-member, mid = HH, bot = 2T + LL. 3 (top T choices) × 1.
        f2_best = -np.inf
        for top_pos in pos_T:
            s = _setting_index_from_tmb(top_pos, pos_H[0], pos_H[1])
            f2_best = max(f2_best, float(np.asarray(gf.evs[int(cid)])[s]))
        # Use F2 deterministic = the same suit-aware top T as F1
        f2_setting = _setting_index_from_tmb(top_T, pos_H[0], pos_H[1])

        # F3: top = T-member, mid = LL, bot = 2T + HH.
        f3_setting = _setting_index_from_tmb(top_T, pos_L[0], pos_L[1])

        # FULL grid evaluation
        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()
        full_F1[i] = rowf[f1_setting]
        full_F2[i] = rowf[f2_setting]
        full_F3[i] = rowf[f3_setting]

        # F1 oracle within class: top can be any of 3 T cards
        f1_best = -np.inf
        for top_pos in pos_T:
            mid_a_, mid_b_ = sorted(j for j in pos_T if j != top_pos)
            s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
            f1_best = max(f1_best, float(rowf[s]))
        full_F1_oc[i] = f1_best

        # F2 oracle: 3 T-tops × 1 mid
        f2_best = -np.inf
        for top_pos in pos_T:
            s = _setting_index_from_tmb(top_pos, pos_H[0], pos_H[1])
            f2_best = max(f2_best, float(rowf[s]))
        full_F2_oc[i] = f2_best

        # F3 oracle: 3 T-tops × 1 mid
        f3_best = -np.inf
        for top_pos in pos_T:
            s = _setting_index_from_tmb(top_pos, pos_L[0], pos_L[1])
            f3_best = max(f3_best, float(rowf[s]))
        full_F3_oc[i] = f3_best

        # F4 oracle: top = H-member (split H pair), mid = some 2 of T,
        # 3 (top H) × 3 (which T-bot) = 9 combos (mid is T-pair = 2 of 3 T).
        f4_best = -np.inf
        for top_pos in pos_H:
            for T_bot_idx in range(3):
                T_bot = pos_T[T_bot_idx]
                mid_a_, mid_b_ = sorted(j for j in pos_T if j != T_bot)
                s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
                f4_best = max(f4_best, float(rowf[s]))
        full_F4_oc[i] = f4_best

        # F5 oracle: top = L-member (split L pair)
        f5_best = -np.inf
        for top_pos in pos_L:
            for T_bot_idx in range(3):
                T_bot = pos_T[T_bot_idx]
                mid_a_, mid_b_ = sorted(j for j in pos_T if j != T_bot)
                s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
                f5_best = max(f5_best, float(rowf[s]))
        full_F5_oc[i] = f5_best

        # PREFIX grid
        if in_pref[i]:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            pref_F1[i] = rowp[f1_setting]
            pref_F2[i] = rowp[f2_setting]
            pref_F3[i] = rowp[f3_setting]

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta = (n_t2p - i - 1) / rate
            print(f"    progress {i+1:>5,}/{n_t2p:,}  rate={rate:.0f}/s  eta {eta:.0f}s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.1f}s")

    n_in_pref = int(in_pref.sum())
    pop_share_pref = n_in_pref / 500_000

    full_v37_reg = full_oracle - full_v37
    full_F1_reg = full_oracle - full_F1
    full_F2_reg = full_oracle - full_F2
    full_F3_reg = full_oracle - full_F3
    full_F1_oc_reg = full_oracle - full_F1_oc
    full_F2_oc_reg = full_oracle - full_F2_oc
    full_F3_oc_reg = full_oracle - full_F3_oc
    full_F4_oc_reg = full_oracle - full_F4_oc
    full_F5_oc_reg = full_oracle - full_F5_oc

    pref_v37_reg = pref_oracle[in_pref] - pref_v37[in_pref]
    pref_F1_reg = pref_oracle[in_pref] - pref_F1[in_pref]
    pref_F2_reg = pref_oracle[in_pref] - pref_F2[in_pref]
    pref_F3_reg = pref_oracle[in_pref] - pref_F3[in_pref]

    print(f"\n[4/4] HEADLINES (full + prefix)")
    print("=" * 80)

    def _row(name, full_reg, pref_reg=None, kind="det"):
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        s = f"  {name:<60}  full ${full_delta:>+8.2f}/1000h"
        if pref_reg is not None:
            pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
            s += f"  pref ${pref_delta:>+8.2f}/1000h"
        s += f"  [{kind}]"
        print(s)

    _row("v37 baseline (no Rule 9 yet)", full_v37_reg, pref_v37_reg, "actual")
    print(f"  {'─'*100}")
    _row("F1 deterministic (top=T-member-non-pair-suit, mid=T-pair, bot=HH+LL)",
         full_F1_reg, pref_F1_reg)
    _row("F2 deterministic (top=T, mid=HH, bot=2T+LL)",
         full_F2_reg, pref_F2_reg)
    _row("F3 deterministic (top=T, mid=LL, bot=2T+HH)",
         full_F3_reg, pref_F3_reg)
    _row("F1 oracle (best top-T choice)", full_F1_oc_reg, kind="oracle")
    _row("F2 oracle (best top-T choice + mid=HH)", full_F2_oc_reg, kind="oracle")
    _row("F3 oracle (best top-T choice + mid=LL)", full_F3_oc_reg, kind="oracle")
    _row("F4 oracle (split H-pair)", full_F4_oc_reg, kind="oracle")
    _row("F5 oracle (split L-pair)", full_F5_oc_reg, kind="oracle")

    # Per-cell breakdown (T, H, L)
    print(f"\n  Per-cell summary (T, H, L), top 30 cells by sample size:")
    print(f"  {'T_H_L':<10}  {'n':>4}  {'v37$':>8}  {'F1$':>8}  {'F2$':>8}  {'F3$':>8}  best_det")
    cells = defaultdict(list)
    for i in range(n_t2p):
        cells[(int(T_arr[i]), int(H_arr[i]), int(L_arr[i]))].append(i)
    cells_sorted = sorted(cells.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    f1_wins = 0
    f2_wins = 0
    f3_wins = 0
    for (T, H, L), idxs in cells_sorted[:30]:
        idxs_np = np.array(idxs, dtype=np.int64)
        v37m = full_v37_reg[idxs_np].mean()
        f1m = full_F1_reg[idxs_np].mean()
        f2m = full_F2_reg[idxs_np].mean()
        f3m = full_F3_reg[idxs_np].mean()
        means = {"F1": f1m, "F2": f2m, "F3": f3m}
        best = min(means, key=means.get)
        if best == "F1": f1_wins += 1
        elif best == "F2": f2_wins += 1
        else: f3_wins += 1
        label = f"{RANK_CHARS[T]}_{RANK_CHARS[H]}{RANK_CHARS[L]}"
        print(f"  {label:<10}  {len(idxs):>4,}  ${v37m*EV_TO_DOL*1000:>+7.1f}  "
              f"${f1m*EV_TO_DOL*1000:>+7.1f}  ${f2m*EV_TO_DOL*1000:>+7.1f}  "
              f"${f3m*EV_TO_DOL*1000:>+7.1f}  {best}")
    print(f"  Among top 30 cells: F1 wins {f1_wins}, F2 wins {f2_wins}, F3 wins {f3_wins}")

    # Boundary search
    print(f"\n  BOUNDARY SEARCH:")
    print(f"  {'rule':<60}  {'full_Δ_grid':>14}  {'pref_Δ_grid':>14}")

    def evaluate(rule_fn, label):
        pick = np.empty(n_t2p, dtype=int)
        for i in range(n_t2p):
            pick[i] = rule_fn(int(T_arr[i]), int(H_arr[i]), int(L_arr[i]))
        full_picked = np.choose(pick, [full_F1, full_F2, full_F3])
        full_reg = full_oracle - full_picked
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        pref_picked = np.choose(pick[in_pref], [pref_F1[in_pref], pref_F2[in_pref], pref_F3[in_pref]])
        pref_reg = pref_oracle[in_pref] - pref_picked
        pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
        marker = "★" if (full_delta > 0 and pref_delta > 0) else ""
        print(f"  {label:<60}  ${full_delta:>+12.2f}  ${pref_delta:>+12.2f}  {marker}")

    evaluate(lambda T, H, L: 0, "always F1 (split-trip + 2-pair-bot, suit-aware)")
    evaluate(lambda T, H, L: 1, "always F2 (mid=HH)")
    evaluate(lambda T, H, L: 2, "always F3 (mid=LL)")
    evaluate(lambda T, H, L: 0 if T >= H else 1,
             "F1 if T>=H else F2 (T is dominant pair)")
    evaluate(lambda T, H, L: 0 if T >= H else 2,
             "F1 if T>=H else F3")
    evaluate(lambda T, H, L: 1 if H >= 12 else 0, "F2 if H>=Q else F1")
    evaluate(lambda T, H, L: 1 if H >= 13 else 0, "F2 if H>=K else F1")

    return 0


if __name__ == "__main__":
    sys.exit(main())
