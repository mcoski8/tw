"""
Session 42 — Always-X structural baseline probe for composite.

composite = the rare 7-card hand archetypes that don't fit the 7 named
categories (high_only / pair / two_pair / trips / trips_pair / three_pair
/ quads). With 7 cards from 52, the composite shapes are:

  - quads_pair  (4 + 2 + 1):  n_quads=1, n_pairs=1
  - quads_trip  (4 + 3):      n_quads=1, n_trips=1   (no singleton)
  - two_trips   (3 + 3 + 1):  n_trips=2
  - trips_two_pair (3+2+2):   n_trips=1, n_pairs=2   (no singleton)

Total in canonical 6,009,159 population: 14,742 hands (0.245%).

CURRENT_PHASE.md (Session 41 close): v34_dt residual on composite =
$2.9/1000h whole-grid; gated `comp_*_g` features fired in v34. The
question this probe answers: is there a clean per-subtype always-X rule
that captures >$1/1000h whole-grid (small absolute, but high per-hand
share since the population is tiny)?

The hand-shape heterogeneity means we stratify by subtype:

  quads_pair (4+2+1):
    Natural set: top=singleton, mid=pair, bot=quads (4 cards).
    Variants:    top=singleton, mid=pair-broken-onto-bot, etc.
                 Quads in mid is also a candidate (mid=2 of quad,
                 bot=other 2 quad cards + pair + ...).

  quads_trip (4+3):
    No singleton — top must be a pair member of trip OR a quad member.
    Natural: top=trip-member, mid=2 trip members? But 4+3=7, so split:
      C1: top=trip-member, mid=quad-2-members, bot=other 2 quad + 2
           remaining trip members  → bot has trips
      C2: top=quad-member, mid=2 trip-members, bot=other 3 quad + 1 trip
           → bot has trips (the trip's 4th card is on top? no, only
           3 trip members exist).
    Reality: 4 quad cards + 3 trip cards = 7. So:
      D1: top=trip-mem, mid=2 trip-mems, bot=4 quad cards (= quads in bot!)
         (this means the trip is fully on top+mid, splitting the trip
         across top + mid → mid is paired by trip leftovers)
      D2: top=quad-mem, mid=2 trip-mems, bot=3 quad-mems + 1 trip-mem
         (mid is the full trip pair; bot is "trip plus 1 of trip")
    D1 is canonical: keep quads intact in bot, split trip across top/mid.

  two_trips (3+3+1):
    7 cards = 3 high-trip + 3 low-trip + 1 singleton.
    Natural settings:
      E1: top=singleton, mid=2 of HIGH-trip, bot=remaining 1 high-trip + 3
          low-trip → bot is "trips-plus-one" (3 of low + 1 high → low trip
          on the bot, mid is a high pair)
      E2: top=singleton, mid=2 of LOW-trip, bot=1 low + 3 high → high trip
          on bot
      E3: top=trip-member-from-LOW (split low trip), mid=2 of HIGH-trip,
          bot=1 low + 1 low + 3 high → bot has trips of high + 2 of low
          (= full house bot)
      E4: top=trip-member-from-HIGH, mid=2 of LOW-trip, bot=1 high + 1
          high + 3 low → full house bot (3 low + 2 high)

  Sub-stratification candidates per CURRENT_PHASE.md hint.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/verify_rule_X_v33_composite.py
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"

EV_TO_DOLLARS = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

# Composite subtype codes
ST_QUADS_PAIR = 0     # 4+2+1
ST_QUADS_TRIP = 1     # 4+3
ST_TWO_TRIPS = 2      # 3+3+1
ST_TRIPS_2P = 3       # 3+2+2
ST_NAMES = ["quads_pair", "quads_trip", "two_trips", "trips_two_pair"]


def _classify_composite(rank_counts: np.ndarray) -> int:
    """Return subtype code (or -1 if not composite)."""
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    if n_quads == 1 and n_pairs == 1:
        return ST_QUADS_PAIR
    if n_quads == 1 and n_trips == 1:
        return ST_QUADS_TRIP
    if n_trips == 2:
        return ST_TWO_TRIPS
    if n_trips == 1 and n_pairs == 2:
        return ST_TRIPS_2P
    return -1


def main() -> int:
    print("=" * 80)
    print("Session 42: Always-X structural probe for composite")
    print("=" * 80)

    print("\n[1/4] identifying composite hands (categorize_hands code 7) ...",
          flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    n_total = ch.hands.shape[0]
    all_hands = np.asarray(ch.hands[:])
    cats = categorize_hands(all_hands)
    composite_idx = np.where(cats == 7)[0]
    n_comp = len(composite_idx)
    pop_share = n_comp / n_total
    print(f"  composite: {n_comp:,}  ({100*pop_share:.4f}% of canonical)")

    print("\n[2/4] loading oracle grid (memmap) ...", flush=True)
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    # Per-hand fields (sized to composite count). Pre-fill with NaN so
    # any unclassified hand (would be a subtype-classifier bug) shows up
    # as NaN rather than uninitialized memory.
    subtype = np.full(n_comp, -1, dtype=np.int8)
    v33_evs = np.full(n_comp, np.nan, dtype=np.float64)
    oracle_evs = np.full(n_comp, np.nan, dtype=np.float64)
    # We compute the "natural" rule per subtype + 2-3 alternatives.
    # Slot rN_ev[i] holds the EV under candidate N for hand i; NaN if N/A.
    rN_evs = {n: np.full(n_comp, np.nan, dtype=np.float64) for n in
              ["QP_natural", "QP_quad_in_mid", "QP_split_pair_top",
               "QT_quad_in_bot", "QT_quad_split",
               "TT_high_trip_to_bot", "TT_low_trip_to_bot",
               "TT_full_house_split",
               "T2P_trip_in_mid", "T2P_trip_in_bot",
               "T2P_split_trip_top"]}

    # v33 diagnostics by subtype
    v33_top_kind_count = defaultdict(lambda: defaultdict(int))
    v33_mid_kind_count = defaultdict(lambda: defaultdict(int))

    print(f"\n[3/4] walking entire {n_comp:,} composite population ...",
          flush=True)
    t0 = time.time()
    last_log = time.time()

    for i, cid in enumerate(composite_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        rank_counts = np.bincount(ranks, minlength=15)
        st = _classify_composite(rank_counts)
        if st < 0:
            continue
        subtype[i] = st

        evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
        oracle_evs[i] = evs_row.max()
        v33_pick = int(strategy_v33_rule6_trips(h))
        v33_evs[i] = evs_row[v33_pick]

        # ============================================================
        # Subtype-specific candidate evaluation
        # ============================================================
        if st == ST_QUADS_PAIR:
            quad_rank = next(r for r in range(2, 15) if rank_counts[r] >= 4)
            pair_rank = next(r for r in range(2, 15) if rank_counts[r] == 2)
            sing_rank = next(r for r in range(2, 15) if rank_counts[r] == 1)
            pos_quad = sorted(j for j in range(7) if int(ranks[j]) == quad_rank)
            pos_pair = sorted(j for j in range(7) if int(ranks[j]) == pair_rank)
            pos_sing = next(j for j in range(7) if int(ranks[j]) == sing_rank)

            # QP_natural: top=singleton, mid=PAIR, bot=4 quad cards.
            qp_nat = _setting_index_from_tmb(pos_sing,
                                             pos_pair[0], pos_pair[1])
            rN_evs["QP_natural"][i] = float(evs_row[qp_nat])

            # QP_quad_in_mid: top=singleton, mid=2 of QUAD,
            #   bot=other 2 quad + pair (= quads broken across mid+bot;
            #   bot has 2 pair pairs = quads-on-board-style-tradeoff).
            # Two pair-of-quad mid choices, take oracle within the
            # "mid is 2 of quad" subspace.
            qp_qm_best = -np.inf
            for a_idx in range(len(pos_quad)):
                for b_idx in range(a_idx + 1, len(pos_quad)):
                    s = _setting_index_from_tmb(pos_sing,
                                                pos_quad[a_idx],
                                                pos_quad[b_idx])
                    v = float(evs_row[s])
                    if v > qp_qm_best:
                        qp_qm_best = v
            rN_evs["QP_quad_in_mid"][i] = qp_qm_best

            # QP_split_pair_top: top=pair-member, mid=2 quad cards,
            #   bot=2 other quad + 1 other pair-mem + 1 sing.
            #   Oracle within constraint.
            qp_sp_best = -np.inf
            for top_pos in pos_pair:
                block = evs_row[top_pos * 15:top_pos * 15 + 15]
                v = float(block.max())
                if v > qp_sp_best:
                    qp_sp_best = v
            rN_evs["QP_split_pair_top"][i] = qp_sp_best

            # v33 diagnostics
            v33_top_idx = v33_pick // 15
            top_rank = int(ranks[v33_top_idx])
            if top_rank == sing_rank:
                v33_top_kind_count["QP"]["singleton"] += 1
            elif top_rank == pair_rank:
                v33_top_kind_count["QP"]["pair_member"] += 1
            elif top_rank == quad_rank:
                v33_top_kind_count["QP"]["quad_member"] += 1
            feats = setting_features_from_bytes(h)
            if bool(feats.mid_is_pair[v33_pick]):
                mid_pr = int(feats.mid_pair_rank[v33_pick])
                if mid_pr == pair_rank:
                    v33_mid_kind_count["QP"]["pair"] += 1
                elif mid_pr == quad_rank:
                    v33_mid_kind_count["QP"]["quad-pair"] += 1
                else:
                    v33_mid_kind_count["QP"]["other_pair"] += 1
            else:
                v33_mid_kind_count["QP"]["unpaired"] += 1

        elif st == ST_QUADS_TRIP:
            quad_rank = next(r for r in range(2, 15) if rank_counts[r] >= 4)
            trip_rank = next(r for r in range(2, 15) if rank_counts[r] == 3)
            pos_quad = sorted(j for j in range(7) if int(ranks[j]) == quad_rank)
            pos_trip = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)

            # QT_quad_in_bot: top=trip-member, mid=2 trip-members,
            #   bot=4 quad cards. (mid is a paired-by-trip-leftover pair;
            #   bot is quads.) Three (top, mid-pair) layouts in the trip.
            # If top = trip[k], mid = the other two trip members.
            qt_qb_best = -np.inf
            for k in range(len(pos_trip)):
                top_pos = pos_trip[k]
                mid_a = pos_trip[(k + 1) % 3]
                mid_b = pos_trip[(k + 2) % 3]
                if mid_a > mid_b:
                    mid_a, mid_b = mid_b, mid_a
                s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                v = float(evs_row[s])
                if v > qt_qb_best:
                    qt_qb_best = v
            rN_evs["QT_quad_in_bot"][i] = qt_qb_best

            # QT_quad_split: top=quad-member, oracle within constraint
            qt_qs_best = -np.inf
            for top_pos in pos_quad:
                block = evs_row[top_pos * 15:top_pos * 15 + 15]
                v = float(block.max())
                if v > qt_qs_best:
                    qt_qs_best = v
            rN_evs["QT_quad_split"][i] = qt_qs_best

            v33_top_idx = v33_pick // 15
            top_rank = int(ranks[v33_top_idx])
            if top_rank == trip_rank:
                v33_top_kind_count["QT"]["trip_member"] += 1
            elif top_rank == quad_rank:
                v33_top_kind_count["QT"]["quad_member"] += 1
            feats = setting_features_from_bytes(h)
            if bool(feats.mid_is_pair[v33_pick]):
                mid_pr = int(feats.mid_pair_rank[v33_pick])
                if mid_pr == trip_rank:
                    v33_mid_kind_count["QT"]["trip-leftover"] += 1
                elif mid_pr == quad_rank:
                    v33_mid_kind_count["QT"]["quad-leftover"] += 1
                else:
                    v33_mid_kind_count["QT"]["other"] += 1
            else:
                v33_mid_kind_count["QT"]["unpaired"] += 1

        elif st == ST_TWO_TRIPS:
            trip_ranks = sorted([r for r in range(2, 15)
                                  if rank_counts[r] == 3], reverse=True)
            high_trip = trip_ranks[0]
            low_trip = trip_ranks[1]
            sing_rank = next(r for r in range(2, 15) if rank_counts[r] == 1)
            pos_high = sorted(j for j in range(7)
                              if int(ranks[j]) == high_trip)
            pos_low = sorted(j for j in range(7)
                             if int(ranks[j]) == low_trip)
            pos_sing = next(j for j in range(7)
                            if int(ranks[j]) == sing_rank)

            # TT_high_trip_to_bot: top=singleton, mid = pair from LOW-trip,
            #   bot = 2 of low-trip + 3 of high-trip? No — bot is 4 cards.
            #   With 3+3+1, bot=4 means: pick 2 from each trip OR 3+1.
            #   "high trip to bot" → bot includes all 3 high-trip cards
            #   plus 1 low-trip card (= full house base on bot).
            #   Then mid = 2 of low-trip (paired mid), top = singleton.
            #   Need to pick which low-trip card goes to bot (3 ways).
            tt_hb_best = -np.inf
            for k in range(len(pos_low)):
                # bot includes: pos_high[0,1,2] + pos_low[k]
                # mid = pos_low minus k (= the other two low-trip cards)
                mid_a = pos_low[(k + 1) % 3]
                mid_b = pos_low[(k + 2) % 3]
                if mid_a > mid_b:
                    mid_a, mid_b = mid_b, mid_a
                s = _setting_index_from_tmb(pos_sing, mid_a, mid_b)
                v = float(evs_row[s])
                if v > tt_hb_best:
                    tt_hb_best = v
            rN_evs["TT_high_trip_to_bot"][i] = tt_hb_best

            # TT_low_trip_to_bot: top=singleton, mid = pair from HIGH-trip,
            #   bot = 2 of high-trip + 3 of low-trip... wait. Bot=4 so:
            #   bot = full low-trip (3) + 1 high-trip card. Mid = remaining
            #   2 high-trip cards. → Full house bottom (low trip + 2 high).
            tt_lb_best = -np.inf
            for k in range(len(pos_high)):
                mid_a = pos_high[(k + 1) % 3]
                mid_b = pos_high[(k + 2) % 3]
                if mid_a > mid_b:
                    mid_a, mid_b = mid_b, mid_a
                s = _setting_index_from_tmb(pos_sing, mid_a, mid_b)
                v = float(evs_row[s])
                if v > tt_lb_best:
                    tt_lb_best = v
            rN_evs["TT_low_trip_to_bot"][i] = tt_lb_best

            # TT_full_house_split: top = trip-member (split a trip),
            #   oracle within constraint.
            tt_fhs_best = -np.inf
            for top_pos in pos_high + pos_low:
                block = evs_row[top_pos * 15:top_pos * 15 + 15]
                v = float(block.max())
                if v > tt_fhs_best:
                    tt_fhs_best = v
            rN_evs["TT_full_house_split"][i] = tt_fhs_best

            v33_top_idx = v33_pick // 15
            top_rank = int(ranks[v33_top_idx])
            if top_rank == sing_rank:
                v33_top_kind_count["TT"]["singleton"] += 1
            elif top_rank == high_trip:
                v33_top_kind_count["TT"]["high_trip_member"] += 1
            elif top_rank == low_trip:
                v33_top_kind_count["TT"]["low_trip_member"] += 1
            feats = setting_features_from_bytes(h)
            if bool(feats.mid_is_pair[v33_pick]):
                mid_pr = int(feats.mid_pair_rank[v33_pick])
                if mid_pr == high_trip:
                    v33_mid_kind_count["TT"]["high-trip-pair"] += 1
                elif mid_pr == low_trip:
                    v33_mid_kind_count["TT"]["low-trip-pair"] += 1
                else:
                    v33_mid_kind_count["TT"]["other"] += 1
            else:
                v33_mid_kind_count["TT"]["unpaired"] += 1

        elif st == ST_TRIPS_2P:
            # Shape: 1 trip + 2 pairs, no singleton (3+2+2=7).
            trip_rank = next(r for r in range(2, 15) if rank_counts[r] == 3)
            pair_ranks_t2p = sorted([r for r in range(2, 15)
                                      if rank_counts[r] == 2], reverse=True)
            hi_pair, lo_pair = pair_ranks_t2p
            pos_trip = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
            pos_hi_p = sorted(j for j in range(7) if int(ranks[j]) == hi_pair)
            pos_lo_p = sorted(j for j in range(7) if int(ranks[j]) == lo_pair)

            # T2P_trip_in_mid: top = a trip-member (split trip), mid = 2
            #   trip-members (paired mid), bot = both pairs (4 cards = 2+2).
            #   3 ways to pick which trip-member goes top.
            t2p_tm_best = -np.inf
            for k in range(len(pos_trip)):
                top_pos = pos_trip[k]
                mid_a = pos_trip[(k + 1) % 3]
                mid_b = pos_trip[(k + 2) % 3]
                if mid_a > mid_b:
                    mid_a, mid_b = mid_b, mid_a
                s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                v = float(evs_row[s])
                if v > t2p_tm_best:
                    t2p_tm_best = v
            rN_evs["T2P_trip_in_mid"][i] = t2p_tm_best

            # T2P_trip_in_bot: top = a pair-member (split a pair),
            #   mid = the other pair, bot = trip + remaining pair-mem (4 cards
            #   = trip + 1 = "trips on bot"). Oracle within constraint over
            #   (top in pos_hi_p ∪ pos_lo_p) × (mid is the other pair).
            t2p_tb_best = -np.inf
            for top_pos in pos_hi_p:
                # mid must be the LO pair to keep "trip in bot"
                s = _setting_index_from_tmb(top_pos, pos_lo_p[0], pos_lo_p[1])
                v = float(evs_row[s])
                if v > t2p_tb_best:
                    t2p_tb_best = v
            for top_pos in pos_lo_p:
                s = _setting_index_from_tmb(top_pos, pos_hi_p[0], pos_hi_p[1])
                v = float(evs_row[s])
                if v > t2p_tb_best:
                    t2p_tb_best = v
            rN_evs["T2P_trip_in_bot"][i] = t2p_tb_best

            # T2P_split_trip_top: top = trip-member (split trip), oracle
            #   within constraint (mid free).
            t2p_st_best = -np.inf
            for top_pos in pos_trip:
                block = evs_row[top_pos * 15:top_pos * 15 + 15]
                v = float(block.max())
                if v > t2p_st_best:
                    t2p_st_best = v
            rN_evs["T2P_split_trip_top"][i] = t2p_st_best

            v33_top_idx = v33_pick // 15
            top_rank = int(ranks[v33_top_idx])
            if top_rank == trip_rank:
                v33_top_kind_count["T2P"]["trip_member"] += 1
            elif top_rank == hi_pair:
                v33_top_kind_count["T2P"]["hi_pair_member"] += 1
            elif top_rank == lo_pair:
                v33_top_kind_count["T2P"]["lo_pair_member"] += 1
            feats = setting_features_from_bytes(h)
            if bool(feats.mid_is_pair[v33_pick]):
                mid_pr = int(feats.mid_pair_rank[v33_pick])
                if mid_pr == trip_rank:
                    v33_mid_kind_count["T2P"]["trip-leftover"] += 1
                elif mid_pr == hi_pair:
                    v33_mid_kind_count["T2P"]["hi-pair"] += 1
                elif mid_pr == lo_pair:
                    v33_mid_kind_count["T2P"]["lo-pair"] += 1
                else:
                    v33_mid_kind_count["T2P"]["other"] += 1
            else:
                v33_mid_kind_count["T2P"]["unpaired"] += 1

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (n_comp - i - 1) / rate
            print(f"    progress {i+1:>6,}/{n_comp:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_comp/elapsed:.0f}/s)")

    # ============================================================
    # [4/4] Per-subtype summary
    # ============================================================
    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    print("\n" + "=" * 80)
    print("PER-SUBTYPE BREAKDOWN")
    print("=" * 80)

    n_classified = int((subtype >= 0).sum())
    print(f"\n  classified {n_classified:,}/{n_comp:,} composite hands "
          f"({100*n_classified/n_comp:.2f}%) into named subtypes")
    if n_classified < n_comp:
        n_unclass = n_comp - n_classified
        print(f"  ⚠ {n_unclass:,} composite hands unclassified — classifier bug")

    for st in (ST_QUADS_PAIR, ST_QUADS_TRIP, ST_TWO_TRIPS, ST_TRIPS_2P):
        mask = subtype == st
        idxs = np.where(mask)[0]
        n_st = len(idxs)
        if n_st == 0:
            continue
        st_share = n_st / n_total  # share of FULL canonical, not within-comp
        v33_r = oracle_evs[idxs] - v33_evs[idxs]
        print(f"\n  ── {ST_NAMES[st]}  (n={n_st:,}, "
              f"{100*st_share:.4f}% of canonical) ──")
        print(f"  v33 mean regret: ${fmt_in(v33_r.mean()):+,.1f}/1000h within-st  "
              f"(${fmt_in(v33_r.mean()) * st_share:+,.2f}/1000h whole-grid)")
        kind = {ST_QUADS_PAIR: "QP", ST_QUADS_TRIP: "QT",
                ST_TWO_TRIPS: "TT", ST_TRIPS_2P: "T2P"}[st]
        if v33_top_kind_count[kind]:
            tops = sorted(v33_top_kind_count[kind].items(),
                          key=lambda kv: -kv[1])
            mids = sorted(v33_mid_kind_count[kind].items(),
                          key=lambda kv: -kv[1])
            print(f"  v33 top: " + ", ".join(
                f"{k}={v}" for k, v in tops))
            print(f"  v33 mid: " + ", ".join(
                f"{k}={v}" for k, v in mids))

        # Candidate-by-candidate
        prefix_for_st = {ST_QUADS_PAIR: "QP_", ST_QUADS_TRIP: "QT_",
                         ST_TWO_TRIPS: "TT_", ST_TRIPS_2P: "T2P_"}[st]
        for cand in rN_evs:
            if not cand.startswith(prefix_for_st):
                continue
            cand_evs = rN_evs[cand][idxs]
            valid = ~np.isnan(cand_evs)
            if valid.sum() == 0:
                continue
            r = oracle_evs[idxs][valid] - cand_evs[valid]
            v33_r_v = oracle_evs[idxs][valid] - v33_evs[idxs][valid]
            delta = v33_r_v.mean() - r.mean()
            print(f"    {cand:<28}  regret=${fmt_in(r.mean()):+9,.1f}/1000h  "
                  f"Δ vs v33: ${fmt_in(delta):+8,.1f} within-st  "
                  f"(${fmt_in(delta) * st_share:+6.2f} whole-grid)")

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • Composite is 0.245% of canonical hands. Even a perfect rule")
    print("    captures at most v33's full residual ($2.9/1000h whole-grid)")
    print("    and likely much less. A heuristic Δ > +$1/1000h whole-grid")
    print("    on any subtype is publishable.")
    print("  • If the per-subtype natural rule is already what v33 picks")
    print("    >70% of the time AND v33's per-st regret is small (<$5/1000h")
    print("    within-st), declare composite as 'no rule extraction needed'.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
