"""
Session 50 — Drill L (Phase 2): A-on-top + bot heuristic sweep.

Drill K showed best-in-DS vs v44 = +$1,937/1000h within fires. Drill L
sweeps deterministic heuristics for "A on top + DS-bot when achievable,
else SS-bot, else fall through" to find the best simple rule.

CRITICAL methodology (S49 lesson): proper within-hand pairwise — for each
hand where the heuristic produces a different setting than v44, compare
the heuristic's pick EV vs v44's pick EV on that SAME hand.

Heuristic variants (all with TOP=A):
  H1_DS_HIBOT  : DS-bot achievable → pick the DS-setting whose bot has
                 highest rank-sum (bot has 4 highest possible cards)
  H2_DS_HIMID  : DS-bot achievable → pick the DS-setting whose mid has
                 highest rank-sum (mid keeps the 2 highest non-A cards)
  H3_DS_HIRUN  : DS-bot achievable → pick the DS-setting with best
                 connectivity (run-4 > one-gap-4 > run-3+stray > ...)
  H4_DS_LOMID  : DS-bot achievable → pick DS-setting whose mid has
                 LOWEST rank-sum (extreme: mid as weak as possible to
                 maximize bot kicker strength)
  H_BEST_DS    : oracle within DS class (upper bound)

Same variants for SS as fallback when DS not achievable.

For each hand:
  - Try H_X (DS variant) first. If achievable, evaluate.
  - Else try H_X_SS (SS variant). If achievable, evaluate.
  - Else fall through to v44.
  - Compare heuristic's chosen EV vs v44's EV on the SAME hand.

Reports:
  - Per variant: sanity-check pick-difference rate vs v44
  - Per variant: within-hand lift vs v44 (averaged over hands where
    variant differs from v44 — within-hand pairwise)
  - Whole-grid full lift estimate

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_A_high_topA_bot_heuristic.py
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
    SUIT_PROFILE_DS, SUIT_PROFILE_SS,
)
from drill_bot_suit_run_priority import (  # noqa: E402
    compute_connectivity_classes, CONN_RUN_4, CONN_ONE_GAP_4,
    CONN_RUN_3_STRAY, CONN_TWO_RUNS_2, CONN_TWO_GAP_4,
    CONN_RUN_2_STRAYS, CONN_SCATTERED,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0

# Connectivity preference order (best to worst, per S44)
CONN_PREF = {CONN_RUN_4: 0, CONN_ONE_GAP_4: 0, CONN_RUN_3_STRAY: 2,
             CONN_TWO_RUNS_2: 3, CONN_TWO_GAP_4: 4,
             CONN_RUN_2_STRAYS: 5, CONN_SCATTERED: 6}


def _enumerate_A_top_settings(hand_pos_idx, ace_pos):
    """Yield (setting_idx, mid_pos_a, mid_pos_b, bot_pos) for each A-on-top setting."""
    others = [j for j in range(7) if j != ace_pos]  # 6 non-A positions
    for mid_a, mid_b in combinations(others, 2):
        bot_pos = sorted(j for j in others if j not in (mid_a, mid_b))
        setting_idx = _setting_index_from_tmb(ace_pos, mid_a, mid_b)
        yield (setting_idx, mid_a, mid_b, bot_pos)


def _bot_suit_class(bot_pos, suits):
    bot_suits = [int(suits[p]) for p in bot_pos]
    cnt = sorted(Counter(bot_suits).values(), reverse=True)
    if cnt == [2, 2]:
        return SUIT_PROFILE_DS
    elif cnt == [2, 1, 1]:
        return SUIT_PROFILE_SS
    elif cnt == [1, 1, 1, 1]:
        return -2  # rainbow
    elif cnt == [3, 1]:
        return -3  # 3+1
    elif cnt == [4]:
        return -4  # 4-flush
    return -5


def _connectivity(bot_pos, ranks):
    sorted_ranks = sorted(int(ranks[p]) for p in bot_pos)
    if len(set(sorted_ranks)) != 4:
        return -1
    diffs = [sorted_ranks[i+1] - sorted_ranks[i] for i in range(3)]
    span = sorted_ranks[-1] - sorted_ranks[0]
    n_adj = sum(1 for d in diffs if d == 1)
    if n_adj == 3:
        return CONN_RUN_4
    if n_adj == 2:
        if span == 4:
            return CONN_ONE_GAP_4
        else:
            return CONN_RUN_3_STRAY
    if n_adj == 1:
        if diffs[0] == 2 and diffs[1] == 1 and diffs[2] == 2:
            return CONN_TWO_GAP_4
        if span == 4:
            return CONN_ONE_GAP_4  # tight two-runs
        else:
            return CONN_RUN_2_STRAYS
    return CONN_SCATTERED


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 50 Drill L: A-on-top + bot heuristic sweep (Phase 2)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)

    print("\n[2/4] filtering to A-high no-pair ...", flush=True)
    t0 = time.time()
    scope_cids = []
    for cid in np.where(cats == 0)[0]:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) != 14:
            continue
        scope_cids.append(int(cid))
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    print(f"  scope: {len(scope_cids):,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        scope_cids = scope_cids[np.sort(idx)]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    # Variant accumulators (within-hand pairwise vs v44)
    variants = ["H1_DS_HIBOT", "H2_DS_HIMID", "H3_DS_HIRUN", "H4_DS_LOMID",
                "H1_SS_HIBOT", "H_BEST_DS", "H_BEST_SS"]
    sum_lift = {v: 0.0 for v in variants}
    n_pairs = {v: 0 for v in variants}    # count of hands where variant fires (rule applies)
    n_diff = {v: 0 for v in variants}     # count of hands where variant pick != v44 pick

    n_total_scope = len(scope_cids)
    n_processed = 0

    print("\n[4/4] per-hand variant evaluation ...", flush=True)
    t0 = time.time()
    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        suits = h & 3
        ace_pos = next(j for j in range(7) if int(ranks[j]) == 14)

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v44_pick = int(strategy_v44_rule13_three_pair_DS(h))
        v44_ev = float(rowf[v44_pick])

        # Enumerate all A-top settings
        a_top_settings = list(_enumerate_A_top_settings(7, ace_pos))

        # Classify each by suit and rank profile
        ds_options = []
        ss_options = []
        for setting_idx, mid_a, mid_b, bot_pos in a_top_settings:
            suit_class = _bot_suit_class(bot_pos, suits)
            bot_rank_sum = sum(int(ranks[p]) for p in bot_pos)
            mid_rank_sum = int(ranks[mid_a]) + int(ranks[mid_b])
            conn = _connectivity(bot_pos, ranks)
            entry = {
                "idx": setting_idx,
                "bot_rank_sum": bot_rank_sum,
                "mid_rank_sum": mid_rank_sum,
                "conn": conn,
            }
            if suit_class == SUIT_PROFILE_DS:
                ds_options.append(entry)
            elif suit_class == SUIT_PROFILE_SS:
                ss_options.append(entry)

        # Pick variant settings
        variant_picks = {}
        if ds_options:
            variant_picks["H1_DS_HIBOT"] = max(ds_options, key=lambda x: x["bot_rank_sum"])["idx"]
            variant_picks["H2_DS_HIMID"] = max(ds_options, key=lambda x: x["mid_rank_sum"])["idx"]
            variant_picks["H3_DS_HIRUN"] = min(ds_options, key=lambda x: CONN_PREF.get(x["conn"], 99))["idx"]
            variant_picks["H4_DS_LOMID"] = min(ds_options, key=lambda x: x["mid_rank_sum"])["idx"]
            variant_picks["H_BEST_DS"] = max(ds_options, key=lambda x: float(rowf[x["idx"]]))["idx"]
        if ss_options:
            variant_picks["H1_SS_HIBOT"] = max(ss_options, key=lambda x: x["bot_rank_sum"])["idx"]
            variant_picks["H_BEST_SS"] = max(ss_options, key=lambda x: float(rowf[x["idx"]]))["idx"]

        for v_name in variants:
            if v_name in variant_picks:
                pick_ev = float(rowf[variant_picks[v_name]])
                sum_lift[v_name] += pick_ev - v44_ev
                n_pairs[v_name] += 1
                if variant_picks[v_name] != v44_pick:
                    n_diff[v_name] += 1

        n_processed += 1
        if n_processed % 20000 == 0:
            rate = n_processed / (time.time() - t0)
            print(f"    progress {n_processed:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # ── Reporting ──
    print("=" * 100)
    print(f"VARIANT COMPARISON (n_processed={n_processed:,})")
    print("=" * 100)
    print(f"\n  {'variant':<14} {'fires':>9} {'%pop':>5} {'%diff_v44':>10} "
          f"{'lift_per_fire':>14} {'whole_grid':>12}")
    print("-" * 80)
    for v_name in variants:
        n_v = n_pairs[v_name]
        if n_v == 0:
            continue
        nd = n_diff[v_name]
        coverage = n_v / n_processed
        diff_pct = 100 * nd / n_v
        mean_lift = sum_lift[v_name] / n_v
        # Whole-grid lift: lift × coverage × scope_share
        scope_share = n_processed / n_total
        wg_lift = mean_lift * EV_TO_DOL * 1000 * coverage * scope_share
        print(f"  {v_name:<14} {n_v:>9,} {coverage*100:>4.0f}% {diff_pct:>9.1f}% "
              f"${mean_lift*EV_TO_DOL*1000:>+11.1f}  ${wg_lift:>+10.2f}")

    # Hybrid: H1_DS_HIBOT first, H1_SS_HIBOT fallback
    print(f"\n── HYBRID CANDIDATES (DS first, SS fallback) ──")
    # Reset for hybrid analysis
    n_total_scope = len(scope_cids)
    sum_h_hibot_hybrid = 0.0
    n_h_hibot_hybrid = 0
    sum_h_himid_hybrid = 0.0
    n_h_himid_hybrid = 0
    sum_h_oracle_hybrid = 0.0
    n_h_oracle_hybrid = 0

    print(f"\n  Re-enumerating for hybrid evaluation...")
    t0 = time.time()
    for i in range(min(50000, n_total_scope)):  # sample for speed
        cid = int(scope_cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        suits = h & 3
        ace_pos = next(j for j in range(7) if int(ranks[j]) == 14)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v44_pick = int(strategy_v44_rule13_three_pair_DS(h))
        v44_ev = float(rowf[v44_pick])

        ds_options = []
        ss_options = []
        for setting_idx, mid_a, mid_b, bot_pos in _enumerate_A_top_settings(7, ace_pos):
            suit_class = _bot_suit_class(bot_pos, suits)
            bot_rank_sum = sum(int(ranks[p]) for p in bot_pos)
            mid_rank_sum = int(ranks[mid_a]) + int(ranks[mid_b])
            entry = {"idx": setting_idx, "bot_rank_sum": bot_rank_sum,
                       "mid_rank_sum": mid_rank_sum}
            if suit_class == SUIT_PROFILE_DS:
                ds_options.append(entry)
            elif suit_class == SUIT_PROFILE_SS:
                ss_options.append(entry)

        # Hybrid HIBOT
        if ds_options:
            pick = max(ds_options, key=lambda x: x["bot_rank_sum"])["idx"]
        elif ss_options:
            pick = max(ss_options, key=lambda x: x["bot_rank_sum"])["idx"]
        else:
            pick = None
        if pick is not None:
            sum_h_hibot_hybrid += float(rowf[pick]) - v44_ev
            n_h_hibot_hybrid += 1

        # Hybrid HIMID
        if ds_options:
            pick = max(ds_options, key=lambda x: x["mid_rank_sum"])["idx"]
        elif ss_options:
            pick = max(ss_options, key=lambda x: x["mid_rank_sum"])["idx"]
        else:
            pick = None
        if pick is not None:
            sum_h_himid_hybrid += float(rowf[pick]) - v44_ev
            n_h_himid_hybrid += 1

        # Hybrid ORACLE (oracle within DS or SS class)
        if ds_options:
            pick = max(ds_options, key=lambda x: float(rowf[x["idx"]]))["idx"]
        elif ss_options:
            pick = max(ss_options, key=lambda x: float(rowf[x["idx"]]))["idx"]
        else:
            pick = None
        if pick is not None:
            sum_h_oracle_hybrid += float(rowf[pick]) - v44_ev
            n_h_oracle_hybrid += 1

    print(f"  Done in {time.time()-t0:.1f}s. (sample={min(50000, n_total_scope):,})")
    sample_size = min(50000, n_total_scope)
    scope_share = n_total_scope / n_total
    for label, sum_v, n_v in [("HYBRID HIBOT (DS-HIBOT, SS-HIBOT fallback)", sum_h_hibot_hybrid, n_h_hibot_hybrid),
                                ("HYBRID HIMID (DS-HIMID, SS-HIMID fallback)", sum_h_himid_hybrid, n_h_himid_hybrid),
                                ("HYBRID ORACLE (best in DS, fallback best in SS)", sum_h_oracle_hybrid, n_h_oracle_hybrid)]:
        if n_v == 0: continue
        mean_lift = sum_v / n_v
        coverage = n_v / sample_size
        wg_lift = mean_lift * EV_TO_DOL * 1000 * coverage * scope_share
        print(f"  {label}")
        print(f"    fires {n_v:>6,} (coverage {coverage*100:.1f}%) | "
              f"lift_vs_v44 ${mean_lift*EV_TO_DOL*1000:>+9.1f}/1000h | "
              f"whole_grid_full ${wg_lift:>+8.2f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
