"""
Session 42 overnight — TT E3a (split-trip-to-top) heuristic hunt.

The TT drill found that E3a (top = H-trip-member, mid = pair-of-L, bot has
2 H + 1 L + 1 singleton) has an oracle-within-class ceiling of +$5.98/1000h
whole-grid — the largest TT opportunity. This drill tests deterministic
heuristics for the in-class choice (which H-trip card to top, which L-trip
card joins bot).

Within E3a:
  - Top: 3 choices (which H-trip-member)
  - Mid: 2 of 3 L-trip cards (= which 1 L-trip joins bot)
  - 3 × 3 = 9 EV-distinct settings within E3a class

The heuristic question:
  - Pick top H-trip-member by suit (which suit "leaves" bot)
  - Pick L-trip-bot member by suit (which suit "joins" bot's pair pattern)

Goal: bot composition is 2 H-trip + 1 L-trip + 1 singleton = 4 cards.
For DS bot (best Omaha): want bot to have "2 of suit X + 2 of suit Y".
The 2 H-trip cards have 2 of 3 H-suits (since 1 H goes to top). The 1 L-trip
in bot has 1 suit. The singleton has 1 fixed suit.

Heuristic candidates:
  (a) Top = H-trip card at suit ∉ {singleton_suit}, so singleton's suit
      stays in bot's H-portion.
  (b) Top = H-trip card whose suit matches the singleton's, so bot's H-suits
      are the OTHER 2 (DS-friendly with L-bot suit).
  (c) Top = H-trip at suit ∉ {L_trip_suits}.
  (d) Top = first H-trip (canonical-position tiebreaker, no suit awareness).
  (e) Top = H-trip at suit shared with most L-trip cards.
For each top choice, the L-bot card is also picked by suit (analogous suit-aware).

We test all combinations (top suit-pick × L-bot suit-pick) on full + prefix.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_tt_e3a_heuristic_hunt.py
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


def main() -> int:
    print("=" * 80)
    print("Session 42 overnight: TT E3a heuristic hunt")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] identifying TT (3+3+1) hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tt_idx = []
    for cid in np.where(cats == 7)[0]:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        n_t = int(sum(rc[r] == 3 for r in range(2, 15)))
        n_q = int(sum(rc[r] >= 4 for r in range(2, 15)))
        n_p = int(sum(rc[r] == 2 for r in range(2, 15)))
        if n_t == 2 and n_q == 0 and n_p == 0:
            tt_idx.append(int(cid))
    n_tt = len(tt_idx)
    pop_share_full = n_tt / len(ch.hands)
    print(f"  TT: {n_tt:,} hands  ({100*pop_share_full:.4f}%)")

    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    in_pref = np.array([cid < 500_000 for cid in tt_idx], dtype=bool)
    pop_share_pref = int(in_pref.sum()) / 500_000

    # Pre-extract per-hand fields and full E3a EV matrix per hand.
    # For each hand, store the 9 EVs of the E3a 3x3 grid + suit info.
    print(f"\n[2/3] enumerating E3a 9-setting grid for {n_tt:,} hands ...",
          flush=True)
    full_v37 = np.zeros(n_tt)
    full_oracle = np.zeros(n_tt)
    pref_v37 = np.full(n_tt, np.nan)
    pref_oracle = np.full(n_tt, np.nan)
    full_e3a_grid = np.zeros((n_tt, 3, 3))  # [hand, top_h_idx, l_bot_idx]
    pref_e3a_grid = np.full((n_tt, 3, 3), np.nan)
    h_suits_arr = np.zeros((n_tt, 3), dtype=np.int8)
    l_suits_arr = np.zeros((n_tt, 3), dtype=np.int8)
    s_suit_arr = np.zeros(n_tt, dtype=np.int8)
    h_rank_arr = np.zeros(n_tt, dtype=np.int8)
    l_rank_arr = np.zeros(n_tt, dtype=np.int8)
    s_rank_arr = np.zeros(n_tt, dtype=np.int8)

    t0 = time.time()
    for i, cid in enumerate(tt_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        trips = sorted([r for r in range(2, 15) if rc[r] == 3], reverse=True)
        H, L = trips[0], trips[1]
        S = next(r for r in range(2, 15) if rc[r] == 1)
        pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
        pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
        pos_S = next(j for j in range(7) if int(ranks[j]) == S)
        h_rank_arr[i] = H
        l_rank_arr[i] = L
        s_rank_arr[i] = S
        h_suits_arr[i] = sorted(int(suits[j]) for j in pos_H)
        l_suits_arr[i] = sorted(int(suits[j]) for j in pos_L)
        s_suit_arr[i] = int(suits[pos_S])

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()

        for top_h_idx in range(3):
            top_h_pos = pos_H[top_h_idx]
            for l_bot_idx in range(3):
                # mid = the 2 L-trip cards NOT chosen as bot
                mid_a, mid_b = sorted(j for j in pos_L if j != pos_L[l_bot_idx])
                s = _setting_index_from_tmb(top_h_pos, mid_a, mid_b)
                full_e3a_grid[i, top_h_idx, l_bot_idx] = float(rowf[s])

        if cid < 500_000:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            for top_h_idx in range(3):
                top_h_pos = pos_H[top_h_idx]
                for l_bot_idx in range(3):
                    mid_a, mid_b = sorted(j for j in pos_L if j != pos_L[l_bot_idx])
                    s = _setting_index_from_tmb(top_h_pos, mid_a, mid_b)
                    pref_e3a_grid[i, top_h_idx, l_bot_idx] = float(rowp[s])

        if i % 500 == 0 and i > 0:
            rate = i / (time.time() - t0)
            print(f"    progress {i:>5,}/{n_tt:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.0f}s")

    full_v37_reg = full_oracle - full_v37
    pref_v37_reg = pref_oracle[in_pref] - pref_v37[in_pref]

    def fmt_dollar(v): return v * EV_TO_DOL * 1000

    print(f"\n[3/3] HEURISTIC HUNT")
    print(f"  v37 baseline: full ${full_v37_reg.mean()*EV_TO_DOL*1000:+.1f}/1000h within-st")
    print(f"\n  {'heuristic':<55}  {'full_Δ_grid':>14}  {'pref_Δ_grid':>14}")

    def eval_heur(top_pick_fn, lbot_pick_fn, label):
        # For each hand, pick top_h_idx and l_bot_idx, look up EV from grid
        full_picked_evs = np.zeros(n_tt)
        pref_picked_evs = np.full(n_tt, np.nan)
        for i in range(n_tt):
            t_idx = top_pick_fn(h_suits_arr[i], l_suits_arr[i], int(s_suit_arr[i]))
            l_idx = lbot_pick_fn(h_suits_arr[i], l_suits_arr[i],
                                  int(s_suit_arr[i]), t_idx)
            full_picked_evs[i] = full_e3a_grid[i, t_idx, l_idx]
            if in_pref[i]:
                pref_picked_evs[i] = pref_e3a_grid[i, t_idx, l_idx]
        full_reg = full_oracle - full_picked_evs
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        pref_reg = pref_oracle[in_pref] - pref_picked_evs[in_pref]
        pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
        marker = "★" if (full_delta > 0 and pref_delta > 0) else ""
        print(f"  {label:<55}  ${full_delta:>+12.2f}  ${pref_delta:>+12.2f}  {marker}")
        return full_delta, pref_delta

    # Heuristic top picks: function(h_suits, l_suits, s_suit) -> 0|1|2 (idx in pos_H)
    # Note: h_suits is sorted 3-tuple; the index returned maps to position in pos_H
    # (which is sorted by hand position, not by suit). We need to map "suit-A H card"
    # to its position-index in pos_H. Since pos_H was sorted by position and suits
    # were stored in same order, h_suits_arr[i][k] is the suit of pos_H[k].

    def top_canonical(hs, ls, ss): return 0  # always first H-trip card
    def top_match_singleton(hs, ls, ss):
        # top = H card sharing suit with singleton, else canonical
        for k in range(3):
            if hs[k] == ss:
                return k
        return 0
    def top_avoid_singleton(hs, ls, ss):
        # top = H card NOT sharing suit with singleton (so bot keeps the matching one)
        for k in range(3):
            if hs[k] != ss:
                return k
        return 0
    def top_at_missing_pair_suit(hs, ls, ss):
        # top = H card at suit ∉ L_suits
        l_set = set(ls)
        for k in range(3):
            if hs[k] not in l_set:
                return k
        return 0
    def top_at_pair_suit(hs, ls, ss):
        # top = H card at suit ∈ L_suits
        l_set = set(ls)
        for k in range(3):
            if hs[k] in l_set:
                return k
        return 0
    def top_at_singleton_or_l(hs, ls, ss):
        # top = H card at suit matching singleton OR an L
        candidates = set(ls) | {ss}
        for k in range(3):
            if hs[k] in candidates:
                return k
        return 0

    # Heuristic L-bot picks: function(h_suits, l_suits, s_suit, top_idx) -> 0|1|2
    def lbot_canonical(hs, ls, ss, ti): return 0
    def lbot_match_singleton(hs, ls, ss, ti):
        for k in range(3):
            if ls[k] == ss:
                return k
        return 0
    def lbot_match_remaining_h(hs, ls, ss, ti):
        # bot has 2 H (suits = hs minus hs[ti]) + 1 L + 1 S. For DS bot, want
        # L's suit ∈ {remaining_h_suits ∪ {ss}}. Pick L whose suit appears in
        # this set most often.
        rem_h = list(hs)
        rem_h.pop(ti)
        targets = set(rem_h)
        # Try to find an L whose suit matches BOTH remaining h-suits + singleton
        # Score each L:
        scores = []
        for k in range(3):
            score = (1 if ls[k] in targets else 0) + (1 if ls[k] == ss else 0)
            scores.append((score, k))
        scores.sort(key=lambda x: (-x[0], x[1]))
        return scores[0][1]

    # Test combinations. Top picks first (with canonical L-bot for baseline).
    print("  -- Top-pick heuristics (with canonical L-bot tiebreaker):")
    eval_heur(top_canonical, lbot_canonical, "top=canonical, L-bot=canonical")
    eval_heur(top_match_singleton, lbot_canonical, "top matches singleton suit")
    eval_heur(top_avoid_singleton, lbot_canonical, "top avoids singleton suit")
    eval_heur(top_at_missing_pair_suit, lbot_canonical, "top at suit ∉ L-suits")
    eval_heur(top_at_pair_suit, lbot_canonical, "top at suit ∈ L-suits")
    eval_heur(top_at_singleton_or_l, lbot_canonical, "top at singleton-suit OR L-suit")
    print("  -- L-bot heuristics (with canonical top):")
    eval_heur(top_canonical, lbot_match_singleton, "L-bot matches singleton")
    eval_heur(top_canonical, lbot_match_remaining_h, "L-bot maximizes DS-bot score")
    print("  -- Combined:")
    eval_heur(top_avoid_singleton, lbot_match_singleton, "top∉s, L-bot=s")
    eval_heur(top_at_missing_pair_suit, lbot_match_remaining_h,
              "top∉L-suits, L-bot=DS-aware")
    eval_heur(top_at_pair_suit, lbot_match_remaining_h, "top∈L-suits, L-bot=DS-aware")
    eval_heur(top_match_singleton, lbot_match_remaining_h,
              "top=singleton-suit, L-bot=DS-aware")

    # Oracle within E3a (best 1 of 9 per hand)
    full_oracle_e3a = full_e3a_grid.reshape(n_tt, 9).max(axis=1)
    pref_oracle_e3a = pref_e3a_grid.reshape(n_tt, 9).max(axis=1)
    full_oc_reg = full_oracle - full_oracle_e3a
    pref_oc_reg = pref_oracle[in_pref] - pref_oracle_e3a[in_pref]
    full_oc_delta = (full_v37_reg.mean() - full_oc_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
    pref_oc_delta = (pref_v37_reg.mean() - pref_oc_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
    print(f"\n  Oracle within E3a (ceiling)                            "
          f"${full_oc_delta:>+12.2f}  ${pref_oc_delta:>+12.2f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
