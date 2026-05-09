"""
Session 47 — Drill F: two_pair within-class suit-aware bot variant sweep.

Drill B (Session 45) showed B1 − B2 = +$1,864/1000h within-hand on J-low
two_pair (n=262,080), where:
  B1 = both-pairs-intact + DS-bot
  B2 = both-pairs-intact + non-DS-bot
B1 was achievable on 59.6% of J-low two_pair hands.

Drill F sweeps the heuristic variants for "both-intact + DS bot" and
finds the best one. Variants:

  Two_pair has 7 cards = HH (high pair) + LL (low pair) + 3 singletons.
  Both-intact = (mid=one pair, bot=other pair + 2 singletons, top=1 singleton).

  The choice space:
    1. Which pair goes to bot? (HH vs LL)
    2. Which 2 singletons complete DS-bot (often only one valid pair)
    3. Which singleton goes to top? (1 leftover after step 2 — no choice
       since 3 sings - 2 for bot = 1 for top)

  So there are at most 2 choices: HH-bot vs LL-bot.

Variants:
  V_LL_BOT  : LL pair to bot (preserves HH in mid; LL+kickers Omaha)
  V_HH_BOT  : HH pair to bot (preserves LL in mid; HH+kickers Omaha)

Population: cat=two_pair AND max≤J AND DS-bot achievable with both intact.

For each fire, compute:
  - v42 production pick EV (no Rule 12 yet — v42 falls through to v41 = v40b for two_pair)
  - V_LL_BOT EV (if achievable)
  - V_HH_BOT EV (if achievable)
  - B1 oracle EV (best EV among all both-intact + DS settings)

Aggregate within-fires lift vs v42 and gap to B1 oracle.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_DS_within_intact.py
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
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v42_rule11_jpair_pbot_ds import strategy_v42_rule11_jpair_pbot_ds  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0


def _enumerate_both_intact_DS_settings(hand: np.ndarray, P_hi: int, P_lo: int):
    """For a two_pair hand, enumerate every (mid_pair_choice, bot_sings) such
    that mid is one pair, bot is the other pair + 2 singletons, top is the
    leftover singleton, and bot is DS.

    Returns list of dicts: {pair_in_bot_rank, setting_idx, ev_ranks}
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_HH = sorted(j for j in range(7) if int(ranks[j]) == P_hi)
    pos_LL = sorted(j for j in range(7) if int(ranks[j]) == P_lo)
    sing_pos = [j for j in range(7) if int(ranks[j]) not in (P_hi, P_lo)]

    out = []
    for pair_to_bot_rank, pair_in_bot_pos, pair_in_mid_pos in [
        (P_lo, pos_LL, pos_HH),  # LL-bot
        (P_hi, pos_HH, pos_LL),  # HH-bot
    ]:
        bot_pair_suits = [int(suits[p]) for p in pair_in_bot_pos]
        # Try every pair of 2 singletons for bot
        for sa, sb in combinations(sing_pos, 2):
            bot_suits = bot_pair_suits + [int(suits[sa]), int(suits[sb])]
            cnt = sorted(Counter(bot_suits).values(), reverse=True)
            if cnt[:2] != [2, 2]:
                continue  # not DS
            # Top = the leftover singleton
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
    print("Session 47 Drill F: two_pair within-class DS variants (J-low scope)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    tp_idx = np.where(cats == 2)[0]
    print(f"  cat=two_pair: {len(tp_idx):,}")

    print("\n[2/4] filtering to J-low two_pair (max_r ≤ 11) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    p_hi = []
    p_lo = []
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) > 11:
            continue
        rc = np.bincount(ranks, minlength=15)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        if len(pairs) != 2:
            continue
        scope_cids.append(int(cid))
        p_hi.append(pairs[0])
        p_lo.append(pairs[1])
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    p_hi = np.asarray(p_hi, dtype=np.int8)
    p_lo = np.asarray(p_lo, dtype=np.int8)
    print(f"  J-low two_pair scope: {len(scope_cids):,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        sel = np.sort(idx)
        scope_cids = scope_cids[sel]
        p_hi = p_hi[sel]
        p_lo = p_lo[sel]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Per-variant accumulators (full grid)
    sum_ev_ll = 0.0
    n_ll = 0
    sum_ev_hh = 0.0
    n_hh = 0
    sum_ev_v42 = 0.0
    sum_ev_b1 = 0.0
    n_v42 = 0
    n_b1 = 0
    n_perfect_ll = 0
    n_perfect_hh = 0
    n_fired_overall = 0

    # Prefix
    sum_ev_ll_p = 0.0
    n_ll_p = 0
    sum_ev_hh_p = 0.0
    n_hh_p = 0
    sum_ev_v42_p = 0.0
    sum_ev_b1_p = 0.0
    n_v42_p = 0

    print("\n[4/4] per-hand variant evaluation ...", flush=True)
    t0 = time.time()
    n_total_scope = len(scope_cids)

    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        PH = int(p_hi[i])
        PL = int(p_lo[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        settings = _enumerate_both_intact_DS_settings(h, PH, PL)
        if not settings:
            continue
        n_fired_overall += 1

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v42_pick = strategy_v42_rule11_jpair_pbot_ds(h)
        v42_ev = float(rowf[v42_pick])
        b1_oracle_ev = max(float(rowf[s["idx"]]) for s in settings)

        sum_ev_v42 += v42_ev
        sum_ev_b1 += b1_oracle_ev
        n_v42 += 1

        # V_LL_BOT: pick LL-to-bot setting (if any). Among those, pick the
        # one with the LOWEST sum-of-bot-singleton-ranks (preserve top/mid
        # strength).
        ll_options = [s for s in settings if s["pair_to_bot_rank"] == PL]
        hh_options = [s for s in settings if s["pair_to_bot_rank"] == PH]

        def best_simple(options):
            # Tie-break: lowest pair-of-bot-singleton-ranks (sum)
            return min(options,
                       key=lambda s: (s["bot_sing_ranks"][0]
                                       + s["bot_sing_ranks"][1]))

        if ll_options:
            chosen = best_simple(ll_options)
            ev = float(rowf[chosen["idx"]])
            sum_ev_ll += ev
            n_ll += 1
            if abs(ev - b1_oracle_ev) < 1e-9:
                n_perfect_ll += 1
        if hh_options:
            chosen = best_simple(hh_options)
            ev = float(rowf[chosen["idx"]])
            sum_ev_hh += ev
            n_hh += 1
            if abs(ev - b1_oracle_ev) < 1e-9:
                n_perfect_hh += 1

        if cid < 500_000:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            v42_ev_p = float(rowp[v42_pick])
            b1_oracle_ev_p = max(float(rowp[s["idx"]]) for s in settings)
            sum_ev_v42_p += v42_ev_p
            sum_ev_b1_p += b1_oracle_ev_p
            n_v42_p += 1
            if ll_options:
                chosen = best_simple(ll_options)
                ev_p = float(rowp[chosen["idx"]])
                sum_ev_ll_p += ev_p
                n_ll_p += 1
            if hh_options:
                chosen = best_simple(hh_options)
                ev_p = float(rowp[chosen["idx"]])
                sum_ev_hh_p += ev_p
                n_hh_p += 1

        if (i + 1) % 10000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.")
    print(f"  fires (DS achievable in both-intact): {n_fired_overall:,} "
          f"({100*n_fired_overall/n_total_scope:.1f}%)\n")

    # ── Reporting ──
    n_total_grid = 6_009_159
    grid_share = n_fired_overall / n_total_grid

    print("=" * 100)
    print("DRILL F — within-fires variant sweep (full grid)")
    print("=" * 100)

    if n_v42 == 0:
        print("(no fires)")
        return 0

    mean_v42 = sum_ev_v42 / n_v42
    mean_b1 = sum_ev_b1 / n_b1 if n_b1 > 0 else (sum_ev_b1 / n_v42)
    mean_b1 = sum_ev_b1 / n_v42  # same n
    b1_lift = (mean_b1 - mean_v42) * EV_TO_DOL * 1000

    print(f"\n  v42 mean EV per fire:          ${mean_v42 * EV_TO_DOL:>+10.2f}")
    print(f"  B1 oracle mean EV per fire:    ${mean_b1 * EV_TO_DOL:>+10.2f}")
    print(f"  B1 oracle lift vs v42:         ${b1_lift:>+10.1f}/1000h within fires")
    print(f"  → B1 oracle whole-grid full:   ${b1_lift * grid_share:>+8.2f}/1000h "
          f"(across {n_fired_overall:,} hands)")

    print(f"\n  {'variant':<10} {'fires':>7} {'perfect%':>9} "
          f"{'mean_EV':>11} {'lift_vs_v42':>14} {'whole_grid':>12} {'gap_to_B1':>12}")
    print("-" * 80)
    for v_name, n_v, sum_v, n_perf in [
        ("V_LL_BOT", n_ll, sum_ev_ll, n_perfect_ll),
        ("V_HH_BOT", n_hh, sum_ev_hh, n_perfect_hh),
    ]:
        if n_v == 0:
            continue
        mean_ev = sum_v / n_v
        # compare against v42 ev computed only on hands where this variant is achievable
        # (approximation: use same mean_v42 since the population is similar)
        lift = (mean_ev - mean_v42) * EV_TO_DOL * 1000
        wg_lift = lift * (n_v / n_v42) * grid_share
        gap = (mean_b1 - mean_ev) * EV_TO_DOL * 1000
        perfect_pct = 100 * n_perf / n_v
        print(f"  {v_name:<10} {n_v:>7,} {perfect_pct:>8.1f}% "
              f"${mean_ev * EV_TO_DOL:>+9.2f} ${lift:>+11.1f} "
              f"${wg_lift:>+10.2f} ${gap:>+10.1f}")

    # Prefix
    print(f"\n  PREFIX GRID (n_v42={n_v42_p:,}):")
    if n_v42_p > 0:
        mean_v42_p = sum_ev_v42_p / n_v42_p
        mean_b1_p = sum_ev_b1_p / n_v42_p
        b1_lift_p = (mean_b1_p - mean_v42_p) * EV_TO_DOL * 1000
        print(f"    v42 mean EV per fire (prefix):   ${mean_v42_p * EV_TO_DOL:>+10.2f}")
        print(f"    B1 oracle mean (prefix):         ${mean_b1_p * EV_TO_DOL:>+10.2f}")
        print(f"    B1 oracle lift vs v42 (prefix):  ${b1_lift_p:>+10.1f}/1000h within fires")
        for v_name, n_v_p, sum_v_p in [
            ("V_LL_BOT", n_ll_p, sum_ev_ll_p),
            ("V_HH_BOT", n_hh_p, sum_ev_hh_p),
        ]:
            if n_v_p == 0:
                continue
            mean_ev_p = sum_v_p / n_v_p
            lift_p = (mean_ev_p - mean_v42_p) * EV_TO_DOL * 1000
            print(f"    {v_name:<10} n={n_v_p:>6,}  mean ${mean_ev_p * EV_TO_DOL:>+9.2f}  "
                  f"lift_vs_v42 ${lift_p:>+9.1f}/1000h within fires")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
