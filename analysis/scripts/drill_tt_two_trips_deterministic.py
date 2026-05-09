"""
Session 42 deep-dive — TT (two_trips, 3+3+1) heuristic-refinement drill.

verify_rule_X_v33_composite.py headlines (full grid):
  v33 within-st mean regret: $11,400/1000h
  Best heuristic-realizable ceiling (oracle within "split-trip-to-top"): +$7.22 whole-grid
  v33 top: high_trip=2,146 (50%), singleton=1,166 (27%), low_trip=978 (23%)

Goal: find a deterministic 1- or 2-condition rule that captures most of
the +$7.22 oracle ceiling. Mirror QP (which captured 100% via suit-aware
deterministic pick).

Structural classes for TT (3+3+1, where H=high trip rank, L=low trip rank,
S=singleton rank):

  E1 (high→bot):  top=S, mid = pair-of-L (2 of L-trip), bot = 3 H-trip + 1 L-trip
  E2 (low→bot):   top=S, mid = pair-of-H (2 of H-trip), bot = 3 L-trip + 1 H-trip
  E3a (split-H):  top = H-member, mid = pair-of-L, bot = 2 H + 1 L + S
  E3b (split-L):  top = L-member, mid = pair-of-H, bot = 1 H + 2 L + S

In E1/E2: paired mid + trips-on-board bot (board pair → trips). Bot's
"trip-rank" anchor is the trip we put 3 of in the bot.
In E3a/E3b: split-trip-to-top + paired mid (full trip on mid) + paired bot
(2 of split-trip on bot).

Within E1/E2: which singleton-position to pick on top? Only 1 singleton
exists (S). Suit choice: which trip-leftover to put in bot?
  E1: bot = 3 H-trip + 1 L-trip. Which L-trip card joins bot? 3 choices.
  E2: bot = 3 L-trip + 1 H-trip. Which H-trip card joins bot? 3 choices.

Within E3a: which of 3 H-trip cards goes on top, which 2 H-trip cards
go on bot, which L-trip card joins bot.

For each, evaluate oracle-within-class. Then test deterministic heuristics:
  H1 = always E1 (high to bot)
  H2 = always E2 (low to bot)
  H3 = E1 if (H >= some threshold) else E2
  H4 = E2 if (H is broadway) else E1   (mirror three_pair Rule 7)
  H5 = E3a if (S is broadway) else E1
  H6 = boundary on (H, L) gap

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/drill_tt_two_trips_deterministic.py
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
    print("Session 42 deep-dive: TT (two_trips) heuristic-refinement drill")
    print("=" * 80)

    print("\n[1/5] identifying TT (3+3+1) hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tt_idx = []
    for cid in np.where(cats == 7)[0]:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        n_q = int(sum(rc[r] >= 4 for r in range(2, 15)))
        n_t = int(sum(rc[r] == 3 for r in range(2, 15)))
        n_p = int(sum(rc[r] == 2 for r in range(2, 15)))
        if n_t == 2 and n_q == 0 and n_p == 0:
            tt_idx.append(int(cid))
    n_tt = len(tt_idx)
    pop_share_full = n_tt / len(ch.hands)
    print(f"  TT (two_trips): {n_tt:,} hands  ({100*pop_share_full:.4f}% of canonical)")

    print("\n[2/5] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    print("\n[3/5] enumerating per-hand structural EVs (full + prefix) ...",
          flush=True)
    # Per-hand fields
    full_v37_evs = np.full(n_tt, np.nan)
    full_oracle_evs = np.full(n_tt, np.nan)
    full_e1_evs = np.full(n_tt, np.nan)  # heuristic E1 (deterministic)
    full_e2_evs = np.full(n_tt, np.nan)
    full_e1_oracle = np.full(n_tt, np.nan)  # oracle within E1 class
    full_e2_oracle = np.full(n_tt, np.nan)
    full_e3a_oracle = np.full(n_tt, np.nan)
    full_e3b_oracle = np.full(n_tt, np.nan)

    pref_v37_evs = np.full(n_tt, np.nan)
    pref_oracle_evs = np.full(n_tt, np.nan)
    pref_e1_evs = np.full(n_tt, np.nan)
    pref_e2_evs = np.full(n_tt, np.nan)

    high_ranks = np.zeros(n_tt, dtype=np.int8)
    low_ranks = np.zeros(n_tt, dtype=np.int8)
    sing_ranks = np.zeros(n_tt, dtype=np.int8)
    in_prefix = np.zeros(n_tt, dtype=bool)

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(tt_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        trips = sorted([r for r in range(2, 15) if rc[r] == 3], reverse=True)
        H, L = trips[0], trips[1]
        S = next(r for r in range(2, 15) if rc[r] == 1)
        high_ranks[i] = H
        low_ranks[i] = L
        sing_ranks[i] = S
        pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
        pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
        pos_S = next(j for j in range(7) if int(ranks[j]) == S)
        in_prefix[i] = (cid < 500_000)

        # E1 deterministic: top=S, mid=pair-of-L, bot=3H+1L.
        # Mid uses 2 of 3 L cards. Choose the 2 "least useful for bot DS":
        #   bot has 3 H + 1 L. To maximize bot DS-ness, pick the L card whose
        #   suit matches an H-suit appearing in the bot. Heuristic deterministic:
        #   put the L-card whose suit is "most common among H suits" into the bot.
        H_suits = sorted([int(suits[j]) for j in pos_H])
        L_suits = sorted([int(suits[j]) for j in pos_L])
        # Score each L card by how well its suit aligns with H suits (sum match).
        def _score_L_for_bot(j):
            return H_suits.count(int(suits[j]))
        L_for_bot = max(pos_L, key=_score_L_for_bot)
        L_for_mid_a, L_for_mid_b = sorted(j for j in pos_L if j != L_for_bot)
        e1_setting = _setting_index_from_tmb(pos_S, L_for_mid_a, L_for_mid_b)

        # E2 deterministic: top=S, mid=pair-of-H, bot=3L+1H.
        def _score_H_for_bot(j):
            return L_suits.count(int(suits[j]))
        H_for_bot = max(pos_H, key=_score_H_for_bot)
        H_for_mid_a, H_for_mid_b = sorted(j for j in pos_H if j != H_for_bot)
        e2_setting = _setting_index_from_tmb(pos_S, H_for_mid_a, H_for_mid_b)

        # FULL grid evaluation
        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37_evs[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle_evs[i] = rowf.max()
        full_e1_evs[i] = rowf[e1_setting]
        full_e2_evs[i] = rowf[e2_setting]

        # E1 oracle within class: best of 3 L-card-to-bot picks (× 1 top + 1 mid)
        e1_best = -np.inf
        for k_idx in range(3):
            L_bot = pos_L[k_idx]
            mid_a, mid_b = sorted(j for j in pos_L if j != L_bot)
            s = _setting_index_from_tmb(pos_S, mid_a, mid_b)
            e1_best = max(e1_best, float(rowf[s]))
        full_e1_oracle[i] = e1_best

        # E2 oracle within class
        e2_best = -np.inf
        for k_idx in range(3):
            H_bot = pos_H[k_idx]
            mid_a, mid_b = sorted(j for j in pos_H if j != H_bot)
            s = _setting_index_from_tmb(pos_S, mid_a, mid_b)
            e2_best = max(e2_best, float(rowf[s]))
        full_e2_oracle[i] = e2_best

        # E3a oracle within class: top = an H-trip-member, mid = pair-of-L (full
        # L pair: 2 of 3 L cards). 3 (top H choices) × 3 (which L-bot) = 9 combos
        # but mid only uses 2 L cards. Actually mid = pair-of-L means 2 of 3
        # L cards; the 3rd L joins bot.
        e3a_best = -np.inf
        for top_pos in pos_H:
            for L_bot_idx in range(3):
                mid_a, mid_b = sorted(j for j in pos_L if j != pos_L[L_bot_idx])
                s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                e3a_best = max(e3a_best, float(rowf[s]))
        full_e3a_oracle[i] = e3a_best

        # E3b oracle: top=L-member, mid=pair-of-H, 1 H joins bot, plus 2L + S.
        e3b_best = -np.inf
        for top_pos in pos_L:
            for H_bot_idx in range(3):
                mid_a, mid_b = sorted(j for j in pos_H if j != pos_H[H_bot_idx])
                s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                e3b_best = max(e3b_best, float(rowf[s]))
        full_e3b_oracle[i] = e3b_best

        # PREFIX grid (only if in prefix)
        if in_prefix[i]:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37_evs[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle_evs[i] = rowp.max()
            pref_e1_evs[i] = rowp[e1_setting]
            pref_e2_evs[i] = rowp[e2_setting]

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta = (n_tt - i - 1) / rate
            print(f"    progress {i+1:>5,}/{n_tt:,}  rate={rate:.0f}/s  eta {eta:.0f}s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.1f}s")

    n_in_pref = int(in_prefix.sum())
    pop_share_pref = n_in_pref / 500_000
    print(f"  TT in prefix: {n_in_pref:,} ({100*pop_share_pref:.4f}%)")

    def fmt_dollars(ev):
        return ev * EV_TO_DOL * 1000

    full_v37_reg = full_oracle_evs - full_v37_evs
    full_e1_reg = full_oracle_evs - full_e1_evs
    full_e2_reg = full_oracle_evs - full_e2_evs
    full_e1_oracle_reg = full_oracle_evs - full_e1_oracle
    full_e2_oracle_reg = full_oracle_evs - full_e2_oracle
    full_e3a_oracle_reg = full_oracle_evs - full_e3a_oracle
    full_e3b_oracle_reg = full_oracle_evs - full_e3b_oracle

    pref_mask = in_prefix
    pref_v37_reg = pref_oracle_evs[pref_mask] - pref_v37_evs[pref_mask]
    pref_e1_reg = pref_oracle_evs[pref_mask] - pref_e1_evs[pref_mask]
    pref_e2_reg = pref_oracle_evs[pref_mask] - pref_e2_evs[pref_mask]

    print("\n" + "=" * 80)
    print("HEADLINES (full + prefix)")
    print("=" * 80)
    print(f"  {'rule':<55}  {'full_Δ_grid':>14}  {'pref_Δ_grid':>14}")

    def _row(name, full_reg, pref_reg=None, kind="det"):
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        s = f"  {name:<55}  ${full_delta:>+12.2f}"
        if pref_reg is not None:
            pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
            s += f"  ${pref_delta:>+12.2f}"
        else:
            s += "  " + " "*14
        s += f"   [{kind}]"
        print(s)

    _row("v37 baseline (no Rule 9 yet)", full_v37_reg, pref_v37_reg, "actual")
    print(f"  {'─'*100}")
    _row("E1 deterministic (top=S, mid=L-pair, bot=3H+1L, suit-aware)",
         full_e1_reg, pref_e1_reg)
    _row("E2 deterministic (top=S, mid=H-pair, bot=3L+1H, suit-aware)",
         full_e2_reg, pref_e2_reg)
    _row("E1 oracle-within-class (best L-bot choice)",
         full_e1_oracle_reg, kind="oracle")
    _row("E2 oracle-within-class (best H-bot choice)",
         full_e2_oracle_reg, kind="oracle")
    _row("E3a oracle (split-H + L-pair-mid)",
         full_e3a_oracle_reg, kind="oracle")
    _row("E3b oracle (split-L + H-pair-mid)",
         full_e3b_oracle_reg, kind="oracle")

    # ============================================================
    # [4/5] Per-cell breakdown (H, L)
    # ============================================================
    print("\n" + "=" * 80)
    print("PER-CELL (high_trip, low_trip) — best deterministic E1 vs E2")
    print("=" * 80)
    cells = defaultdict(list)
    for i in range(n_tt):
        cells[(int(high_ranks[i]), int(low_ranks[i]))].append(i)

    print(f"  {'pair':<6}  {'n':>4}  {'v37$':>8}  {'E1$':>8}  {'E2$':>8}  {'E1_oc$':>8}  {'E2_oc$':>8}  best_det")
    rows_e1_wins = 0
    rows_e2_wins = 0
    for (H, L), idxs in sorted(cells.items()):
        if len(idxs) < 30:
            continue
        idxs_np = np.array(idxs, dtype=np.int64)
        v37m = full_v37_reg[idxs_np].mean()
        e1m = full_e1_reg[idxs_np].mean()
        e2m = full_e2_reg[idxs_np].mean()
        e1ocm = full_e1_oracle_reg[idxs_np].mean()
        e2ocm = full_e2_oracle_reg[idxs_np].mean()
        best = "E1" if e1m < e2m else "E2"
        if best == "E1":
            rows_e1_wins += 1
        else:
            rows_e2_wins += 1
        label = f"{RANK_CHARS[H]}{RANK_CHARS[L]}"
        print(f"  {label:<6}  {len(idxs):>4,}  ${fmt_dollars(v37m):>+7.1f}  "
              f"${fmt_dollars(e1m):>+7.1f}  ${fmt_dollars(e2m):>+7.1f}  "
              f"${fmt_dollars(e1ocm):>+7.1f}  ${fmt_dollars(e2ocm):>+7.1f}  {best}")
    print(f"\n  E1 wins: {rows_e1_wins} cells; E2 wins: {rows_e2_wins} cells")

    # ============================================================
    # [5/5] Boundary search
    # ============================================================
    print("\n" + "=" * 80)
    print("BOUNDARY RULE SEARCH (full grid + prefix)")
    print("=" * 80)

    def evaluate(rule_fn, label):
        pick = np.empty(n_tt, dtype=int)  # 0=E1, 1=E2
        for i in range(n_tt):
            pick[i] = rule_fn(int(high_ranks[i]), int(low_ranks[i]),
                              int(sing_ranks[i]))
        full_picked = np.where(pick == 0, full_e1_evs, full_e2_evs)
        full_reg = full_oracle_evs - full_picked
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full

        pref_picked_p = np.where(pick[pref_mask] == 0, pref_e1_evs[pref_mask], pref_e2_evs[pref_mask])
        pref_reg = pref_oracle_evs[pref_mask] - pref_picked_p
        pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
        marker = "★" if (full_delta > 0 and pref_delta > 0) else ""
        print(f"  {label:<60}  full ${full_delta:>+8.2f}  pref ${pref_delta:>+8.2f}  {marker}")

    print(f"  {'rule':<60}  {'full_Δ_grid':>14}  {'pref_Δ_grid':>14}  ")
    evaluate(lambda H, L, S: 0, "always E1 (high-to-bot)")
    evaluate(lambda H, L, S: 1, "always E2 (low-to-bot)")
    evaluate(lambda H, L, S: 1 if H >= 11 else 0, "E2 if H>=J else E1")
    evaluate(lambda H, L, S: 1 if H >= 12 else 0, "E2 if H>=Q else E1")
    evaluate(lambda H, L, S: 1 if H >= 10 else 0, "E2 if H>=T else E1")
    evaluate(lambda H, L, S: 1 if H == 14 else 0, "E2 if H=A else E1")
    evaluate(lambda H, L, S: 1 if H >= 10 and H < 14 else 0,
             "E2 if T<=H<=K else E1 (broadway non-A)")
    evaluate(lambda H, L, S: 1 if (H - L) >= 5 else 0, "E2 if gap>=5 else E1")
    evaluate(lambda H, L, S: 1 if (H - L) >= 7 else 0, "E2 if gap>=7 else E1")

    return 0


if __name__ == "__main__":
    sys.exit(main())
