"""
Session 48 — Drill H: three_pair within-class DS-bot.

Three_pair has 3 pairs (HH, MM, LL) + 1 singleton = 7 cards.

For all-3-pairs-intact configurations:
  bot (4 cards) = 2 of the 3 pairs (no singletons; bot is 2 paired ranks)
  mid (2 cards) = 1 pair (the remaining pair)
  top (1 card) = the singleton (deterministic)

There are 3 choices for which pair stays in mid: HH-mid (bot=MM+LL),
MM-mid (bot=HH+LL), LL-mid (bot=HH+MM).

For DS bot: the 4 cards (2 pairs) must form a 2+2 suit pattern. Each
pair has 2 cards with 2 different suits (canonical). For bot=pair_a +
pair_b: suits = {a1, a2, b1, b2}. DS iff {a1,a2} == {b1,b2}, i.e., the
two pairs share IDENTICAL suit sets.

Probability of identical suit sets: in a random canonical hand, each
pair's suit set is one of C(4,2)=6 options. Two pairs identical = 1/6.
So ~1/6 = 16.7% of three_pair hands should have ≥1 DS-achievable
both-intact configuration. Additionally a hand might have HH=MM (HH and
MM share suits but not LL) or other combinations.

For each three_pair hand, enumerate the 3 candidate "which pair to mid"
configs. For each, check DS achievability. Compute B1 oracle = best EV
among DS-achievable settings.

Variants tested:
  V_LL_MID  : LL pair to mid, bot = HH+MM  (highest pairs in bot)
  V_MM_MID  : MM pair to mid, bot = HH+LL
  V_HH_MID  : HH pair to mid, bot = MM+LL  (lowest pairs in bot — anchors weak)

Expected: V_LL_MID wins by analogy with Drill F (HH-to-bot beats LL-to-bot).
HH+MM in bot creates the strongest 2-pair-with-kicker Omaha hand.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_three_pair_DS_within_intact.py
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
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


def _enumerate_all_intact_DS_settings(hand: np.ndarray, P_hi: int,
                                        P_mid: int, P_lo: int):
    """For a three_pair hand (HH, MM, LL + 1 singleton), enumerate all
    (mid_pair_choice) configs where bot=2 pairs, top=singleton, and bot is DS.
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_HH = sorted(j for j in range(7) if int(ranks[j]) == P_hi)
    pos_MM = sorted(j for j in range(7) if int(ranks[j]) == P_mid)
    pos_LL = sorted(j for j in range(7) if int(ranks[j]) == P_lo)
    sing_pos = next(j for j in range(7) if int(ranks[j]) not in (P_hi, P_mid, P_lo))

    out = []
    for mid_label, mid_pos, bot_pair_a_pos, bot_pair_b_pos in [
        ("LL_mid", pos_LL, pos_HH, pos_MM),
        ("MM_mid", pos_MM, pos_HH, pos_LL),
        ("HH_mid", pos_HH, pos_MM, pos_LL),
    ]:
        a_suits = sorted([int(suits[p]) for p in bot_pair_a_pos])
        b_suits = sorted([int(suits[p]) for p in bot_pair_b_pos])
        if a_suits != b_suits:
            continue  # not DS (suit sets differ)
        # DS bot achieved
        mid_a, mid_b = sorted(mid_pos)
        setting_idx = _setting_index_from_tmb(sing_pos, mid_a, mid_b)
        out.append({
            "mid_label": mid_label,
            "mid_rank": int(ranks[mid_pos[0]]),
            "idx": setting_idx,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 48 Drill H: three_pair all-intact + DS-bot variant sweep")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    tp_idx = np.where(cats == 5)[0]
    print(f"  cat=three_pair: {len(tp_idx):,}")

    print("\n[2/4] extracting pair ranks ...", flush=True)
    t0 = time.time()
    scope_cids = []
    p_info = []
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        if len(pairs) != 3:
            continue
        scope_cids.append(int(cid))
        p_info.append(tuple(pairs))
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    print(f"  three_pair scope: {len(scope_cids):,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        idx_sorted = np.sort(idx)
        scope_cids = scope_cids[idx_sorted]
        p_info = [p_info[i] for i in idx_sorted]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    sum_ev_v43 = 0.0
    sum_ev_b1 = 0.0
    sum_ev_ll = 0.0
    sum_ev_mm = 0.0
    sum_ev_hh = 0.0
    n_v43 = 0
    n_ll = n_mm = n_hh = 0
    sum_ev_v43_p = 0.0
    sum_ev_b1_p = 0.0
    sum_ev_ll_p = 0.0
    sum_ev_mm_p = 0.0
    sum_ev_hh_p = 0.0
    n_v43_p = 0
    n_ll_p = n_mm_p = n_hh_p = 0
    n_fires_full = 0
    achievability_count = Counter()

    print("\n[4/4] per-hand variant evaluation ...", flush=True)
    t0 = time.time()
    for i, cid in enumerate(scope_cids):
        PH, PM, PL = p_info[i]
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        settings = _enumerate_all_intact_DS_settings(h, PH, PM, PL)
        if not settings:
            continue
        n_fires_full += 1
        labels_in_hand = tuple(sorted(s["mid_label"] for s in settings))
        achievability_count[labels_in_hand] += 1

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        v43_pick = strategy_v43_rule12_two_pair_DS_intact(h)
        v43_ev = float(rowf[v43_pick])
        b1_oracle_ev = max(float(rowf[s["idx"]]) for s in settings)

        sum_ev_v43 += v43_ev
        sum_ev_b1 += b1_oracle_ev
        n_v43 += 1

        # Pick each variant's EV (if achievable)
        ll_set = next((s for s in settings if s["mid_label"] == "LL_mid"), None)
        mm_set = next((s for s in settings if s["mid_label"] == "MM_mid"), None)
        hh_set = next((s for s in settings if s["mid_label"] == "HH_mid"), None)
        if ll_set:
            sum_ev_ll += float(rowf[ll_set["idx"]])
            n_ll += 1
        if mm_set:
            sum_ev_mm += float(rowf[mm_set["idx"]])
            n_mm += 1
        if hh_set:
            sum_ev_hh += float(rowf[hh_set["idx"]])
            n_hh += 1

        if int(cid) < 500_000:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            sum_ev_v43_p += float(rowp[v43_pick])
            sum_ev_b1_p += max(float(rowp[s["idx"]]) for s in settings)
            n_v43_p += 1
            if ll_set:
                sum_ev_ll_p += float(rowp[ll_set["idx"]])
                n_ll_p += 1
            if mm_set:
                sum_ev_mm_p += float(rowp[mm_set["idx"]])
                n_mm_p += 1
            if hh_set:
                sum_ev_hh_p += float(rowp[hh_set["idx"]])
                n_hh_p += 1

        if (i + 1) % 10000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{len(scope_cids):,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  fires (≥1 DS-intact achievable): {n_fires_full:,} "
          f"({100*n_fires_full/len(scope_cids):.1f}% of three_pair)")

    print(f"\n  Achievability label distributions:")
    for labels, cnt in sorted(achievability_count.items(),
                                key=lambda x: -x[1]):
        print(f"    {labels}: {cnt:,}  ({100*cnt/n_fires_full:.1f}% of fires)")

    if n_v43 == 0:
        print("(no fires)")
        return 0

    n_total_grid = 6_009_159
    grid_share = n_fires_full / n_total_grid

    mean_v43 = sum_ev_v43 / n_v43
    mean_b1 = sum_ev_b1 / n_v43
    b1_lift = (mean_b1 - mean_v43) * EV_TO_DOL * 1000

    print(f"\n=== FULL GRID ===")
    print(f"  v43 mean EV per fire:   ${mean_v43 * EV_TO_DOL:>+10.2f}")
    print(f"  B1 oracle mean:          ${mean_b1 * EV_TO_DOL:>+10.2f}")
    print(f"  B1 lift vs v43:          ${b1_lift:>+10.1f}/1000h within fires")
    print(f"  → Whole-grid full ceil:  ${b1_lift * grid_share:>+8.2f}/1000h")

    print(f"\n  {'variant':<10} {'fires':>7} {'mean_EV':>11} "
          f"{'lift_vs_v43':>14} {'whole_grid':>12} {'gap_to_B1':>12}")
    print("-" * 80)
    for v_name, n_v, sum_v in [
        ("V_LL_MID", n_ll, sum_ev_ll),
        ("V_MM_MID", n_mm, sum_ev_mm),
        ("V_HH_MID", n_hh, sum_ev_hh),
    ]:
        if n_v == 0:
            continue
        mean_ev = sum_v / n_v
        lift = (mean_ev - mean_v43) * EV_TO_DOL * 1000
        wg_lift = lift * (n_v / n_v43) * grid_share
        gap = (mean_b1 - mean_ev) * EV_TO_DOL * 1000
        print(f"  {v_name:<10} {n_v:>7,} ${mean_ev * EV_TO_DOL:>+9.2f} "
              f"${lift:>+11.1f} ${wg_lift:>+10.2f} ${gap:>+10.1f}")

    if n_v43_p > 0:
        mean_v43_p = sum_ev_v43_p / n_v43_p
        mean_b1_p = sum_ev_b1_p / n_v43_p
        b1_lift_p = (mean_b1_p - mean_v43_p) * EV_TO_DOL * 1000
        print(f"\n=== PREFIX GRID (n_v43_p={n_v43_p:,}) ===")
        print(f"  v43 mean EV (prefix):    ${mean_v43_p * EV_TO_DOL:>+10.2f}")
        print(f"  B1 lift vs v43 (prefix): ${b1_lift_p:>+10.1f}/1000h within fires")
        for v_name, n_v_p, sum_v_p in [
            ("V_LL_MID", n_ll_p, sum_ev_ll_p),
            ("V_MM_MID", n_mm_p, sum_ev_mm_p),
            ("V_HH_MID", n_hh_p, sum_ev_hh_p),
        ]:
            if n_v_p == 0:
                continue
            mean_p = sum_v_p / n_v_p
            lift_p = (mean_p - mean_v43_p) * EV_TO_DOL * 1000
            print(f"    {v_name:<10} n={n_v_p:>6,}  mean ${mean_p * EV_TO_DOL:>+9.2f}  "
                  f"lift ${lift_p:>+9.1f}/1000h within fires")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
