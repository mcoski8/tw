"""
Session 48 — Drill G: two_pair Rule 12 extension to max≥Q.

Rule 12 (Session 47) is scoped to max_rank ≤ J. Drill G tests whether the
same HH-to-bot + LL-fallback heuristic ships clean lift at higher max_rank
cells (Q-high, K-high, A-high two_pair).

Population: cat=two_pair AND max_rank ∈ {12, 13, 14}, n_total per cell:
- max=Q: 393,120 hands (4.36% of two_pair)
- max=K: 524,160 hands
- max=A: 655,200 hands

For each max_rank cell, run the Drill F variant sweep (V_HH_BOT, V_LL_BOT,
B1 oracle ceiling) within-fires. Compare lift vs v43 production pick (NOT
v42 — v43 already fires on max≤J, so we want to see what v43 picks at
max≥Q and the residual lift available).

Key question: at max≥Q, the highest singleton may be Q/K/A which has
significant top-tier equity. Does putting an A on top change the calculus?
The answer depends on whether v43 (which falls through to v42 at max≥Q)
picks a setting that already realizes the top-tier value.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_DS_extension.py
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from itertools import combinations
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
from strategy_v43_rule12_two_pair_DS_intact import strategy_v43_rule12_two_pair_DS_intact  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def _enumerate_both_intact_DS_settings(hand: np.ndarray, P_hi: int, P_lo: int):
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_HH = sorted(j for j in range(7) if int(ranks[j]) == P_hi)
    pos_LL = sorted(j for j in range(7) if int(ranks[j]) == P_lo)
    sing_pos = [j for j in range(7) if int(ranks[j]) not in (P_hi, P_lo)]

    out = []
    for pair_to_bot_rank, pair_in_bot_pos, pair_in_mid_pos in [
        (P_lo, pos_LL, pos_HH),
        (P_hi, pos_HH, pos_LL),
    ]:
        bot_pair_suits = [int(suits[p]) for p in pair_in_bot_pos]
        for sa, sb in combinations(sing_pos, 2):
            bot_suits = bot_pair_suits + [int(suits[sa]), int(suits[sb])]
            cnt = sorted(Counter(bot_suits).values(), reverse=True)
            if cnt[:2] != [2, 2]:
                continue
            top_pos = next(j for j in sing_pos if j != sa and j != sb)
            mid_a, mid_b = sorted(pair_in_mid_pos)
            setting_idx = _setting_index_from_tmb(top_pos, mid_a, mid_b)
            out.append({
                "pair_to_bot_rank": pair_to_bot_rank,
                "idx": setting_idx,
                "top_rank": int(ranks[top_pos]),
                "bot_sing_ranks": (int(ranks[sa]), int(ranks[sb])),
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 48 Drill G: two_pair Rule 12 extension to max≥Q")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    tp_idx = np.where(cats == 2)[0]

    print("\n[2/4] filtering to max≥Q two_pair ...", flush=True)
    t0 = time.time()
    cells = {12: [], 13: [], 14: []}
    cell_pair_info = {12: [], 13: [], 14: []}
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        max_r = int(ranks.max())
        if max_r < 12:
            continue
        rc = np.bincount(ranks, minlength=15)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        if len(pairs) != 2:
            continue
        cells[max_r].append(int(cid))
        cell_pair_info[max_r].append((pairs[0], pairs[1]))
    for mr in (12, 13, 14):
        print(f"  max={RANK_CHAR[mr]}: {len(cells[mr]):>7,}  "
              f"({100*len(cells[mr])/n_total:.4f}% of grid)")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        for mr in (12, 13, 14):
            if len(cells[mr]) > args.sample:
                idx = rng.choice(len(cells[mr]), size=args.sample, replace=False)
                idx_sorted = sorted(idx)
                cells[mr] = [cells[mr][i] for i in idx_sorted]
                cell_pair_info[mr] = [cell_pair_info[mr][i] for i in idx_sorted]
        print(f"  [sample mode: {args.sample:,} per cell]")

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    def best_simple(options):
        return min(options, key=lambda s: s["bot_sing_ranks"][0]
                                            + s["bot_sing_ranks"][1])

    def fmt_dollar(x):
        if np.isnan(x):
            return "       n/a"
        return f"${x:>+9.1f}"

    print("\n[4/4] per-cell variant evaluation ...", flush=True)
    t0 = time.time()

    for mr in (12, 13, 14):
        n_pop = len(cells[mr])
        if n_pop == 0:
            continue
        sum_v43 = 0.0
        sum_b1 = 0.0
        sum_ll = 0.0
        sum_hh = 0.0
        n_v43 = 0
        n_ll = 0
        n_hh = 0
        sum_v43_p = 0.0
        sum_b1_p = 0.0
        sum_ll_p = 0.0
        sum_hh_p = 0.0
        n_v43_p = 0
        n_ll_p = 0
        n_hh_p = 0
        n_fires_full = 0

        for i, cid in enumerate(cells[mr]):
            PH, PL = cell_pair_info[mr][i]
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            settings = _enumerate_both_intact_DS_settings(h, PH, PL)
            if not settings:
                continue
            n_fires_full += 1

            rowf = np.asarray(gf.evs[cid], dtype=np.float64)
            v43_pick = strategy_v43_rule12_two_pair_DS_intact(h)
            v43_ev = float(rowf[v43_pick])
            b1_oracle_ev = max(float(rowf[s["idx"]]) for s in settings)

            sum_v43 += v43_ev
            sum_b1 += b1_oracle_ev
            n_v43 += 1

            ll_options = [s for s in settings if s["pair_to_bot_rank"] == PL]
            hh_options = [s for s in settings if s["pair_to_bot_rank"] == PH]
            if ll_options:
                ev = float(rowf[best_simple(ll_options)["idx"]])
                sum_ll += ev
                n_ll += 1
            if hh_options:
                ev = float(rowf[best_simple(hh_options)["idx"]])
                sum_hh += ev
                n_hh += 1

            if cid < 500_000:
                rowp = np.asarray(gp.evs[cid], dtype=np.float64)
                v43_ev_p = float(rowp[v43_pick])
                b1_p = max(float(rowp[s["idx"]]) for s in settings)
                sum_v43_p += v43_ev_p
                sum_b1_p += b1_p
                n_v43_p += 1
                if ll_options:
                    sum_ll_p += float(rowp[best_simple(ll_options)["idx"]])
                    n_ll_p += 1
                if hh_options:
                    sum_hh_p += float(rowp[best_simple(hh_options)["idx"]])
                    n_hh_p += 1

        print()
        print("=" * 100)
        print(f"max={RANK_CHAR[mr]}-high two_pair  (pop={n_pop:,}, "
              f"fires={n_fires_full:,} ({100*n_fires_full/n_pop:.1f}%))")
        print("=" * 100)

        if n_v43 == 0:
            print("(no fires)")
            continue

        mean_v43 = sum_v43 / n_v43
        mean_b1 = sum_b1 / n_v43
        b1_lift = (mean_b1 - mean_v43) * EV_TO_DOL * 1000
        grid_share = n_fires_full / n_total
        prefix_share = n_v43_p / 500_000 if n_v43_p > 0 else 0

        print(f"\n  v43 mean EV per fire (full):     ${mean_v43 * EV_TO_DOL:>+10.2f}")
        print(f"  B1 oracle mean (full):           ${mean_b1 * EV_TO_DOL:>+10.2f}")
        print(f"  B1 lift vs v43 (within fires):   ${b1_lift:>+10.1f}/1000h")
        print(f"  → Whole-grid full ceiling:       ${b1_lift * grid_share:>+8.2f}/1000h")

        print(f"\n  {'variant':<10} {'fires':>7} {'mean_EV':>11} "
              f"{'lift_vs_v43':>14} {'whole_grid':>12} {'gap_to_B1':>12}")
        print("-" * 80)
        for v_name, n_v, sum_v in [("V_LL_BOT", n_ll, sum_ll),
                                     ("V_HH_BOT", n_hh, sum_hh)]:
            if n_v == 0:
                continue
            mean_ev = sum_v / n_v
            lift = (mean_ev - mean_v43) * EV_TO_DOL * 1000
            wg_lift = lift * (n_v / n_v43) * grid_share
            gap = (mean_b1 - mean_ev) * EV_TO_DOL * 1000
            print(f"  {v_name:<10} {n_v:>7,} ${mean_ev * EV_TO_DOL:>+9.2f} "
                  f"${lift:>+11.1f} ${wg_lift:>+10.2f} ${gap:>+10.1f}")

        if n_v43_p > 0:
            mean_v43_p = sum_v43_p / n_v43_p
            mean_b1_p = sum_b1_p / n_v43_p
            b1_lift_p = (mean_b1_p - mean_v43_p) * EV_TO_DOL * 1000
            print(f"\n  PREFIX (n_v43_p={n_v43_p:,}):")
            print(f"    v43 mean EV (prefix):         ${mean_v43_p * EV_TO_DOL:>+10.2f}")
            print(f"    B1 lift vs v43 (prefix):      ${b1_lift_p:>+10.1f}/1000h within fires")
            for v_name, n_v_p, sum_v_p in [("V_LL_BOT", n_ll_p, sum_ll_p),
                                            ("V_HH_BOT", n_hh_p, sum_hh_p)]:
                if n_v_p == 0:
                    continue
                mean_p = sum_v_p / n_v_p
                lift_p = (mean_p - mean_v43_p) * EV_TO_DOL * 1000
                print(f"    {v_name:<10} n={n_v_p:>6,}  mean ${mean_p * EV_TO_DOL:>+9.2f}  "
                      f"lift ${lift_p:>+9.1f}/1000h")

    print(f"\n  done in {time.time()-t0:.1f}s")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
