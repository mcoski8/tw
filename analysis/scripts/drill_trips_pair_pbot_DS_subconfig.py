"""
Session 49 — Drill J: trips_pair pair-bot + DS sub-config sweep.

Drill I (Session 49) showed best-in-V3 (pair-bot + DS) lifts vs v44 by
+$1,992/1000h within fires. v44 already picks pair-bot 85% of the time
but picks the wrong sub-config of pair-bot 35% of the time.

Pair-bot configurations for trips_pair (pair + trip + 2 sings):
  bot = 4 cards, including the pair (2). Other 2 cards from {3 trip, 2 sings}.

Sub-configs of pair-bot:
  A) bot = pair + 2 trip   → top + mid = 1 trip + 2 sings
  B) bot = pair + 1 trip + 1 sing → top + mid = 2 trip + 1 sing
  C) bot = pair + 2 sings  → top + mid = 3 trip → mid = 2 trip, top = 1 trip

For each pair-bot config, top placement choice:
  A) top ∈ {1 trip, 2 sings} (3 choices)
  B) top ∈ {2 trip, 1 sing} (3 choices); mid = 2 of remaining
  C) top must be 1 trip (only 1 sing or 0 left after mid=2 trip)

DS achievability per config depends on suit alignment.

This drill enumerates ALL pair-bot + DS settings per hand, classifies
them by sub-config, and finds the lift of each sub-config heuristic vs
v44 production pick.

Variants:
  V_A_TOP_TRIP : pair-bot, sub-config A (bot=pair+2trip), top=1 trip
  V_A_TOP_SING_HI : pair-bot, A, top=hi sing
  V_A_TOP_SING_LO : pair-bot, A, top=lo sing
  V_B_TOP_TRIP : pair-bot, B (bot=pair+1trip+1sing), top=1 trip (highest rank trip)
  V_B_TOP_SING_HI : B, top=hi sing
  V_B_TOP_SING_LO : B, top=lo sing
  V_C_TOP_TRIP : C (bot=pair+2sings), mid=2trip, top=1 trip

Pick the highest-EV variant per hand IF a DS-achievable config exists.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_pair_pbot_DS_subconfig.py
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
from tw_analysis.query import setting_features_from_bytes, SUIT_PROFILE_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0


def _enumerate_pbot_DS_settings(hand: np.ndarray, trip_rank: int,
                                  pair_rank: int):
    """Enumerate all (top_pos, mid_a, mid_b) settings where pair is in bot
    AND bot is DS. Returns list of dicts.
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
    pos_trip = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) not in
                        (trip_rank, pair_rank)],
                        key=lambda j: -int(ranks[j]))  # desc by rank

    # Pair (2 cards) is in bot. Bot has 4 cards = pair + 2 of {3 trip + 2 sings}.
    bot_pair_suits = [int(suits[p]) for p in pos_pair]
    out = []
    others = pos_trip + sing_pos  # 3 trip + 2 sings = 5 candidates
    for sa, sb in combinations(others, 2):
        bot_suits = bot_pair_suits + [int(suits[sa]), int(suits[sb])]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt[:2] != [2, 2]:
            continue
        # remaining 3 cards: 7 - 2 (pair) - 2 (sa, sb) = 3
        remaining = [j for j in range(7) if j not in pos_pair
                     and j not in (sa, sb)]
        # top + mid from remaining
        for top_pos in remaining:
            mid_pair = sorted(j for j in remaining if j != top_pos)
            setting_idx = _setting_index_from_tmb(top_pos, mid_pair[0], mid_pair[1])
            # Sub-config classification
            n_trip_in_bot = sum(1 for p in (sa, sb) if int(ranks[p]) == trip_rank)
            sub_config = ['C', 'B', 'A'][n_trip_in_bot]  # 0 trip→C, 1→B, 2→A
            top_is_trip = int(ranks[top_pos]) == trip_rank
            top_is_high_sing = (top_pos == sing_pos[0]) if sing_pos else False
            top_is_low_sing = (top_pos == sing_pos[-1]) if sing_pos else False
            out.append({
                "idx": setting_idx,
                "sub_config": sub_config,
                "top_is_trip": top_is_trip,
                "top_is_high_sing": top_is_high_sing,
                "top_is_low_sing": top_is_low_sing,
                "top_rank": int(ranks[top_pos]),
                "bot_others_pos": (sa, sb),
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 49 Drill J: trips_pair pair-bot + DS sub-config sweep")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    tp_idx = np.where(cats == 4)[0]

    print("\n[2/4] extracting (trip, pair) ranks ...", flush=True)
    t0 = time.time()
    scope_cids = []
    p_info = []
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
        pair_rank = next(r for r in range(2, 15) if rc[r] == 2)
        scope_cids.append(int(cid))
        p_info.append((trip_rank, pair_rank))
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    print(f"  scope: {len(scope_cids):,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        idx_sorted = np.sort(idx)
        scope_cids = scope_cids[idx_sorted]
        p_info = [p_info[i] for i in idx_sorted]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Per-variant accumulators
    variants = ["V_A_TOP_TRIP", "V_A_TOP_SING_HI", "V_A_TOP_SING_LO",
                "V_B_TOP_TRIP", "V_B_TOP_SING_HI", "V_B_TOP_SING_LO",
                "V_C_TOP_TRIP",
                "V_BEST_DS",  # oracle within pair-bot DS class
                "V_HEUR_BEST",  # current best heuristic — will determine empirically
               ]
    sum_ev = {v: 0.0 for v in variants}
    n_v = {v: 0 for v in variants}
    sum_ev_p = {v: 0.0 for v in variants}
    n_v_p = {v: 0 for v in variants}
    sum_ev_v44 = 0.0
    sum_ev_v44_p = 0.0
    n_v44 = 0
    n_v44_p = 0
    n_fires = 0
    achievability = Counter()

    print("\n[4/4] per-hand variant evaluation ...", flush=True)
    t0 = time.time()
    n_total_scope = len(scope_cids)
    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        trip_rank, pair_rank = p_info[i]
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        settings = _enumerate_pbot_DS_settings(h, trip_rank, pair_rank)
        if not settings:
            continue
        n_fires += 1

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v44_pick = strategy_v44_rule13_three_pair_DS(h)
        sum_ev_v44 += float(rowf[v44_pick])
        n_v44 += 1

        # Best DS pair-bot setting (oracle within class)
        best_idx = max(settings, key=lambda s: float(rowf[s["idx"]]))["idx"]
        sum_ev["V_BEST_DS"] += float(rowf[best_idx])
        n_v["V_BEST_DS"] += 1

        # Per-variant picks (if achievable)
        for variant_name, predicate in [
            ("V_A_TOP_TRIP", lambda s: s["sub_config"] == "A" and s["top_is_trip"]),
            ("V_A_TOP_SING_HI", lambda s: s["sub_config"] == "A" and s["top_is_high_sing"]),
            ("V_A_TOP_SING_LO", lambda s: s["sub_config"] == "A" and s["top_is_low_sing"]),
            ("V_B_TOP_TRIP", lambda s: s["sub_config"] == "B" and s["top_is_trip"]),
            ("V_B_TOP_SING_HI", lambda s: s["sub_config"] == "B" and s["top_is_high_sing"]),
            ("V_B_TOP_SING_LO", lambda s: s["sub_config"] == "B" and s["top_is_low_sing"]),
            ("V_C_TOP_TRIP", lambda s: s["sub_config"] == "C" and s["top_is_trip"]),
        ]:
            options = [s for s in settings if predicate(s)]
            if options:
                # Tie-break: pick highest-EV among matching settings (in case of multiple)
                best_match = max(options, key=lambda s: float(rowf[s["idx"]]))
                sum_ev[variant_name] += float(rowf[best_match["idx"]])
                n_v[variant_name] += 1

        # Achievability tracking
        configs_in_hand = sorted(set(s["sub_config"] for s in settings))
        achievability[tuple(configs_in_hand)] += 1

        if cid < 500_000:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            sum_ev_v44_p += float(rowp[v44_pick])
            n_v44_p += 1
            best_idx_p = max(settings, key=lambda s: float(rowp[s["idx"]]))["idx"]
            sum_ev_p["V_BEST_DS"] += float(rowp[best_idx_p])
            n_v_p["V_BEST_DS"] += 1
            for variant_name, predicate in [
                ("V_A_TOP_TRIP", lambda s: s["sub_config"] == "A" and s["top_is_trip"]),
                ("V_A_TOP_SING_HI", lambda s: s["sub_config"] == "A" and s["top_is_high_sing"]),
                ("V_A_TOP_SING_LO", lambda s: s["sub_config"] == "A" and s["top_is_low_sing"]),
                ("V_B_TOP_TRIP", lambda s: s["sub_config"] == "B" and s["top_is_trip"]),
                ("V_B_TOP_SING_HI", lambda s: s["sub_config"] == "B" and s["top_is_high_sing"]),
                ("V_B_TOP_SING_LO", lambda s: s["sub_config"] == "B" and s["top_is_low_sing"]),
                ("V_C_TOP_TRIP", lambda s: s["sub_config"] == "C" and s["top_is_trip"]),
            ]:
                options = [s for s in settings if predicate(s)]
                if options:
                    best_match = max(options, key=lambda s: float(rowp[s["idx"]]))
                    sum_ev_p[variant_name] += float(rowp[best_match["idx"]])
                    n_v_p[variant_name] += 1

        if (i + 1) % 10000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  fires (V3 achievable): {n_fires:,} ({100*n_fires/n_total_scope:.1f}%)")

    print(f"\n  Achievability decomposition:")
    for configs, cnt in sorted(achievability.items(), key=lambda x: -x[1]):
        print(f"    sub-configs achievable: {configs}  → {cnt:,} hands "
              f"({100*cnt/n_fires:.1f}% of fires)")

    if n_v44 == 0:
        return 0

    n_total_grid = 6_009_159
    grid_share = n_fires / n_total_grid
    mean_v44 = sum_ev_v44 / n_v44

    print(f"\n=== FULL GRID ===")
    print(f"  v44 mean EV per fire:    ${mean_v44 * EV_TO_DOL:>+10.2f}")
    print(f"\n  {'variant':<20} {'fires':>7} {'%cov':>5} "
          f"{'mean_EV':>11} {'lift_vs_v44':>14} {'whole_grid':>12}")
    print("-" * 80)
    for v in variants:
        if n_v[v] == 0:
            continue
        mean_ev = sum_ev[v] / n_v[v]
        lift = (mean_ev - mean_v44) * EV_TO_DOL * 1000
        coverage = n_v[v] / n_fires
        wg_lift = lift * coverage * grid_share
        print(f"  {v:<20} {n_v[v]:>7,} {coverage*100:>4.0f}% "
              f"${mean_ev * EV_TO_DOL:>+9.2f} ${lift:>+11.1f} ${wg_lift:>+10.2f}")

    if n_v44_p > 0:
        mean_v44_p = sum_ev_v44_p / n_v44_p
        print(f"\n=== PREFIX GRID (n_v44_p={n_v44_p:,}) ===")
        print(f"  v44 mean EV per fire (prefix): ${mean_v44_p * EV_TO_DOL:>+10.2f}")
        print(f"  {'variant':<20} {'fires':>7} {'mean_EV':>11} {'lift_vs_v44':>14}")
        print("-" * 60)
        for v in variants:
            if n_v_p[v] == 0:
                continue
            mean_ev_p = sum_ev_p[v] / n_v_p[v]
            lift_p = (mean_ev_p - mean_v44_p) * EV_TO_DOL * 1000
            print(f"  {v:<20} {n_v_p[v]:>7,} ${mean_ev_p * EV_TO_DOL:>+9.2f} "
                  f"${lift_p:>+11.1f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
