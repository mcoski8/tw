"""
Session 70 Phase 3a — Trips catalog candidate sweep.

Tests 3 blanket structural rules against (v55 baseline) and (v44 ceiling)
per S69 methodology lesson: a T2 verdict vs the baseline is not enough
to ship a rule when the hybrid option exists; always test "lift vs v44".

Candidates (all blanket rules; fire on ALL trips hands matching cell):
  C_TR_1 — Force A_DS_tkmax in B_DS_AVAIL_LKR + B_DS_AVAIL_HKR cells:
           if B-DS is achievable (trips_b_ds_avail), pick the Layout-A
           setting with DS-bot pattern and top=max_kicker (highest
           singleton kicker rank).
  C_TR_2 — Force A_DS_tkmax in NO_BDS_AKDOM cells: when no B-DS available
           AND max_kicker >= trip_rank, pick best Layout-A setting with
           DS-bot if achievable, else best A-bot.
  C_TR_3 — Force C_top_trip in NO_BDS_CTOP: when trip_rank > max_kicker,
           pick Layout-C with top=trip card (C-top advantage).

Output:
  data/session70/trips_catalog_candidates.log
  data/session70/trips_catalog_candidates.json
  Console: per-candidate verdict (T1/T2/T3 vs baseline AND vs v44)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/test_trips_catalog_candidates_S70.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.query import SETTING_HAND_INDICES  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
TR_PARQUET = ROOT / "data" / "drill_trips_v44_per_hand_structural.parquet"
V55_PARQUET = ROOT / "data" / "drill_trips_v55_per_hand.parquet"
OUT_JSON = ROOT / "data" / "session70" / "trips_catalog_candidates.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

CELLS_ORDER = [
    "B_DS_AVAIL_HKR",
    "B_DS_AVAIL_LKR",
    "NO_BDS_CTOP",
    "NO_BDS_AKDOM",
]
CELL_TO_IDX = {c: i for i, c in enumerate(CELLS_ORDER)}


def _bot_suit_kind(suits):
    counts = sorted(Counter(int(s) for s in suits).values(), reverse=True)
    if counts == [4]:
        return "4f"
    if counts == [2, 2]:
        return "DS"
    if counts == [2, 1, 1]:
        return "SS"
    if counts == [3, 1]:
        return "31"
    return "RB"


def find_best_a_ds_tkmax(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc):
    """Find the Layout-A setting index with DS bot and top = max_kicker.

    A_paired_mid: top=kicker, mid=2 trips, bot=1 trip + 3 kickers.
    DS bot = 4 cards in 2+2 suit pattern.
    top must be the max-rank kicker.

    Returns setting_idx or None if no such setting exists.
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    max_kicker_rank = kicker_ranks_sorted_desc[0]

    best_idx = None
    for idx in range(105):
        pos = SETTING_HAND_INDICES[idx]
        top_pos = int(pos[0])
        mid_pos = (int(pos[1]), int(pos[2]))
        bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

        n_trip_top = 1 if top_pos in trip_pos_set else 0
        n_trip_mid = sum(1 for p in mid_pos if p in trip_pos_set)
        n_trip_bot = sum(1 for p in bot_pos if p in trip_pos_set)

        if n_trip_top != 0 or n_trip_mid != 2 or n_trip_bot != 1:
            continue
        if int(ranks[top_pos]) != max_kicker_rank:
            continue
        bot_suits_arr = [int(suits[p]) for p in bot_pos]
        if _bot_suit_kind(bot_suits_arr) != "DS":
            continue
        return idx
    return best_idx


def find_best_a_any_tkmax(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc):
    """Find any Layout-A setting with top=max_kicker. Prefer DS bot then SS.

    Used as fallback when DS-bot is infeasible.
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    max_kicker_rank = kicker_ranks_sorted_desc[0]

    pri_ds, pri_ss, pri_other = None, None, None
    for idx in range(105):
        pos = SETTING_HAND_INDICES[idx]
        top_pos = int(pos[0])
        mid_pos = (int(pos[1]), int(pos[2]))
        bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

        n_trip_top = 1 if top_pos in trip_pos_set else 0
        n_trip_mid = sum(1 for p in mid_pos if p in trip_pos_set)
        n_trip_bot = sum(1 for p in bot_pos if p in trip_pos_set)

        if n_trip_top != 0 or n_trip_mid != 2 or n_trip_bot != 1:
            continue
        if int(ranks[top_pos]) != max_kicker_rank:
            continue
        bot_suits_arr = [int(suits[p]) for p in bot_pos]
        kind = _bot_suit_kind(bot_suits_arr)
        if kind == "DS" and pri_ds is None:
            pri_ds = idx
        elif kind == "SS" and pri_ss is None:
            pri_ss = idx
        elif pri_other is None:
            pri_other = idx
    return pri_ds or pri_ss or pri_other


def find_best_c_top_trip(hand_bytes, trip_pos_set):
    """Find Layout-C setting (top=trip, mid=2 trips, bot=4 kickers).

    Prefer DS bot, then SS, then any.
    """
    suits = hand_bytes & 3
    pri_ds, pri_ss, pri_other = None, None, None
    for idx in range(105):
        pos = SETTING_HAND_INDICES[idx]
        top_pos = int(pos[0])
        mid_pos = (int(pos[1]), int(pos[2]))
        bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

        n_trip_top = 1 if top_pos in trip_pos_set else 0
        n_trip_mid = sum(1 for p in mid_pos if p in trip_pos_set)
        n_trip_bot = sum(1 for p in bot_pos if p in trip_pos_set)

        if n_trip_top != 1 or n_trip_mid != 2 or n_trip_bot != 0:
            continue
        bot_suits_arr = [int(suits[p]) for p in bot_pos]
        kind = _bot_suit_kind(bot_suits_arr)
        if kind == "DS" and pri_ds is None:
            pri_ds = idx
        elif kind == "SS" and pri_ss is None:
            pri_ss = idx
        elif pri_other is None:
            pri_other = idx
    return pri_ds or pri_ss or pri_other


def candidate_C_TR_1(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc,
                      cell, struct):
    """C_TR_1 — Force A_DS_tkmax in B_DS_AVAIL_* cells."""
    if cell not in ("B_DS_AVAIL_HKR", "B_DS_AVAIL_LKR"):
        return None
    return find_best_a_ds_tkmax(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc)


def candidate_C_TR_2(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc,
                      cell, struct):
    """C_TR_2 — Force A_DS_tkmax in NO_BDS_AKDOM (fallback to A_any)."""
    if cell != "NO_BDS_AKDOM":
        return None
    pick = find_best_a_ds_tkmax(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc)
    if pick is None:
        pick = find_best_a_any_tkmax(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc)
    return pick


def candidate_C_TR_3(hand_bytes, trip_pos_set, kicker_ranks_sorted_desc,
                      cell, struct):
    """C_TR_3 — Force C_top_trip in NO_BDS_CTOP."""
    if cell != "NO_BDS_CTOP":
        return None
    return find_best_c_top_trip(hand_bytes, trip_pos_set)


CANDIDATES = [
    ("C_TR_1", candidate_C_TR_1,
     "Force A_DS_tkmax in B_DS_AVAIL_* cells",
     ["B_DS_AVAIL_HKR", "B_DS_AVAIL_LKR"]),
    ("C_TR_2", candidate_C_TR_2,
     "Force A_DS_tkmax in NO_BDS_AKDOM cell",
     ["NO_BDS_AKDOM"]),
    ("C_TR_3", candidate_C_TR_3,
     "Force C_top_trip in NO_BDS_CTOP cell",
     ["NO_BDS_CTOP"]),
]


def compute_per_hand_struct(h):
    """Return (trip_pos_set, kicker_ranks_sorted_desc) for a trips hand."""
    ranks = (h // 4) + 2
    rc = Counter(int(r) for r in ranks)
    trip_rank = next(r for r, c in rc.items() if c == 3)
    trip_pos = [i for i in range(7) if int(ranks[i]) == trip_rank]
    trip_pos_set = set(trip_pos)
    kicker_pos = [i for i in range(7) if i not in trip_pos_set]
    kicker_ranks_sorted = tuple(sorted(
        (int(ranks[i]) for i in kicker_pos), reverse=True
    ))
    return trip_pos_set, kicker_ranks_sorted


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 70 Phase 3a — Trips catalog candidate sweep")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading trips Phase 1 parquet (v44 + cell tags + oracle)...",
          flush=True)
    df44 = pq.read_table(TR_PARQUET).to_pandas()
    print(f"  rows: {len(df44):,}")

    print("\n[2/4] loading trips Phase 2 parquet (v55 picks) ...", flush=True)
    df55 = pq.read_table(V55_PARQUET).to_pandas()
    df55_lookup = dict(zip(df55["canonical_id"].to_numpy(),
                            df55["v55_idx"].to_numpy()))
    v55_idx_arr = np.array([df55_lookup[int(cid)]
                             for cid in df44["canonical_id"].to_numpy()],
                            dtype=np.int16)
    df44["v55_idx"] = v55_idx_arr

    if args.sample > 0 and len(df44) > args.sample:
        rng = np.random.default_rng(args.seed)
        sel = np.sort(rng.choice(len(df44), size=args.sample, replace=False))
        df44 = df44.iloc[sel].reset_index(drop=True)
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading canonical hands + oracle grid ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n_total = len(df44)
    cids = df44["canonical_id"].to_numpy()
    cell_idxs = df44["cell_idx"].to_numpy()
    oracle_idxs = df44["oracle_idx"].to_numpy()
    v44_idxs = df44["v44_idx"].to_numpy()
    v55_idxs = df44["v55_idx"].to_numpy()
    trip_ranks = df44["trip_rank"].to_numpy()

    # Pre-load all hands as a single (n, 7) array for speed
    print("\n[3.5/4] pre-loading hand bytes ...", flush=True)
    hands_arr = np.zeros((n_total, 7), dtype=np.uint8)
    for i in range(n_total):
        hands_arr[i] = np.asarray(ch.hands[int(cids[i])], dtype=np.uint8)
    print(f"  loaded {n_total:,} hands.")

    print("\n[4/4] running candidates ...", flush=True)
    results = {}
    for cand_name, cand_fn, cand_desc, applicable_cells in CANDIDATES:
        print(f"\n  ── {cand_name}: {cand_desc} ──", flush=True)
        t0 = time.time()
        per_cell_stats = defaultdict(lambda: {
            "n": 0,
            "n_fires": 0,
            "rule_sum_ev": 0.0,
            "baseline_sum_ev": 0.0,
            "v44_sum_ev": 0.0,
            "oracle_sum_ev": 0.0,
            "n_rule_match_oracle": 0,
            "n_v55_match_oracle": 0,
            "n_v44_match_oracle": 0,
        })
        n_fires_total = 0
        for i in range(n_total):
            cid = int(cids[i])
            cell = CELLS_ORDER[int(cell_idxs[i])]
            if cell not in applicable_cells:
                # Rule doesn't fire on this cell — use baseline (v55)
                rule_idx = int(v55_idxs[i])
                fired = False
            else:
                h = hands_arr[i]
                trip_pos_set, kicker_ranks = compute_per_hand_struct(h)
                cand_idx = cand_fn(h, trip_pos_set, kicker_ranks, cell, None)
                if cand_idx is None:
                    rule_idx = int(v55_idxs[i])
                    fired = False
                else:
                    rule_idx = int(cand_idx)
                    fired = True
                    n_fires_total += 1

            rowf = gf.evs[cid]
            rule_ev = float(rowf[rule_idx])
            baseline_ev = float(rowf[int(v55_idxs[i])])
            v44_ev = float(rowf[int(v44_idxs[i])])
            oracle_ev = float(rowf[int(oracle_idxs[i])])

            tr = int(trip_ranks[i])
            key = (tr, cell)
            st = per_cell_stats[key]
            st["n"] += 1
            if fired:
                st["n_fires"] += 1
            st["rule_sum_ev"] += rule_ev
            st["baseline_sum_ev"] += baseline_ev
            st["v44_sum_ev"] += v44_ev
            st["oracle_sum_ev"] += oracle_ev
            if rule_idx == int(oracle_idxs[i]):
                st["n_rule_match_oracle"] += 1
            if int(v55_idxs[i]) == int(oracle_idxs[i]):
                st["n_v55_match_oracle"] += 1
            if int(v44_idxs[i]) == int(oracle_idxs[i]):
                st["n_v44_match_oracle"] += 1

            if (i + 1) % 50_000 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                eta = (n_total - i - 1) / rate
                print(f"    {cand_name} {i+1:>7,}/{n_total:,}  "
                      f"rate={rate:>5.0f}/s  ETA {eta:>4.0f}s",
                      flush=True)

        elapsed = time.time() - t0
        print(f"  done in {elapsed:.1f}s  (fires={n_fires_total:,})")

        # Aggregate per applicable-cell across ranks
        cell_summary = {}
        for cell in applicable_cells:
            agg_n = 0
            agg_fires = 0
            agg_rule_ev = 0.0
            agg_base_ev = 0.0
            agg_v44_ev = 0.0
            agg_oracle_ev = 0.0
            agg_rule_match = 0
            agg_v55_match = 0
            agg_v44_match = 0
            for (tr, c), st in per_cell_stats.items():
                if c != cell:
                    continue
                agg_n += st["n"]
                agg_fires += st["n_fires"]
                agg_rule_ev += st["rule_sum_ev"]
                agg_base_ev += st["baseline_sum_ev"]
                agg_v44_ev += st["v44_sum_ev"]
                agg_oracle_ev += st["oracle_sum_ev"]
                agg_rule_match += st["n_rule_match_oracle"]
                agg_v55_match += st["n_v55_match_oracle"]
                agg_v44_match += st["n_v44_match_oracle"]
            if agg_n == 0:
                continue
            rule_mean = agg_rule_ev / agg_n
            base_mean = agg_base_ev / agg_n
            v44_mean = agg_v44_ev / agg_n
            oracle_mean = agg_oracle_ev / agg_n
            lift_b_wg = (agg_rule_ev - agg_base_ev) * EV_TO_DOL * 1000 / N_TOTAL_GRID
            lift_v_wg = (agg_rule_ev - agg_v44_ev) * EV_TO_DOL * 1000 / N_TOTAL_GRID
            gap_b = oracle_mean - base_mean
            gap_v = oracle_mean - v44_mean
            cap_b = 100.0 * (rule_mean - base_mean) / gap_b if gap_b > 1e-12 else 0.0
            cap_v = 100.0 * (rule_mean - v44_mean) / gap_v if gap_v > 1e-12 else 0.0
            rule_pct = 100 * agg_rule_match / agg_n
            v55_pct = 100 * agg_v55_match / agg_n
            v44_pct = 100 * agg_v44_match / agg_n

            # Verdict (S69-style):
            # T1: capture >= 40% within cell AND lift_wg >= +$3 within-cell-WG
            # T2: lift_b_wg >= +$5 whole-grid AND lift_v_wg >= 0 (not negative vs v44)
            # T3: otherwise
            within_cell_lift = (agg_rule_ev - agg_base_ev) * EV_TO_DOL * 1000 / agg_n
            if cap_b >= 40 and within_cell_lift >= 3.0:
                if lift_b_wg >= 5.0 and lift_v_wg >= 0:
                    verdict = "T2"
                else:
                    verdict = "T1"
            else:
                verdict = "T3"

            cell_summary[cell] = {
                "n_hands": int(agg_n),
                "n_fires": int(agg_fires),
                "fire_rate_pct": float(100 * agg_fires / max(agg_n, 1)),
                "rule_pct_opt": float(rule_pct),
                "v55_pct_opt": float(v55_pct),
                "v44_pct_opt": float(v44_pct),
                "rule_mean_ev": float(rule_mean),
                "v55_mean_ev": float(base_mean),
                "v44_mean_ev": float(v44_mean),
                "oracle_mean_ev": float(oracle_mean),
                "capture_vs_baseline_pct": float(cap_b),
                "capture_vs_v44_pct": float(cap_v),
                "lift_vs_baseline_wg": float(lift_b_wg),
                "lift_vs_v44_wg": float(lift_v_wg),
                "within_cell_lift_per_hand_dollars": float(within_cell_lift),
                "verdict": verdict,
                "dominated_by_v44": bool(lift_v_wg < 0),
            }
            print(f"    cell={cell}  n={agg_n:,}  fires={agg_fires:,} "
                  f"({100*agg_fires/agg_n:.1f}%)")
            print(f"      pct_opt:   rule={rule_pct:.2f}%  "
                  f"v55={v55_pct:.2f}%  v44={v44_pct:.2f}%")
            print(f"      capture:   vs_v55={cap_b:+.2f}%  vs_v44={cap_v:+.2f}%")
            print(f"      lift_wg:   vs_v55=${lift_b_wg:+.2f}  "
                  f"vs_v44=${lift_v_wg:+.2f}")
            dom_str = "DOMINATED_BY_V44" if lift_v_wg < 0 else "competitive"
            print(f"      VERDICT:   {verdict}  ({dom_str})")

        results[cand_name] = {
            "description": cand_desc,
            "applicable_cells": applicable_cells,
            "elapsed_sec": elapsed,
            "n_fires_total": int(n_fires_total),
            "per_cell": cell_summary,
        }

    # =====================
    # Final verdict summary
    # =====================
    print("\n" + "=" * 88)
    print("CANDIDATE VERDICT SUMMARY")
    print("=" * 88)
    print(f"  {'candidate':<10} {'cell':<18} {'lift_v55':>10} {'lift_v44':>10} "
          f"{'verdict':>8} {'dominated':>12}")
    n_clear_t2 = 0
    n_dominated = 0
    for cand_name, cand_meta in results.items():
        for cell, cs in cand_meta["per_cell"].items():
            dom = "YES" if cs["dominated_by_v44"] else "no"
            print(f"  {cand_name:<10} {cell:<18} ${cs['lift_vs_baseline_wg']:>+8.2f} "
                  f"${cs['lift_vs_v44_wg']:>+8.2f} "
                  f"{cs['verdict']:>8} {dom:>12}")
            if cs["verdict"] in ("T1", "T2"):
                n_clear_t2 += 1
            if cs["dominated_by_v44"]:
                n_dominated += 1

    print(f"\n  Candidates clearing T1/T2 vs v55: {n_clear_t2}")
    print(f"  Candidates DOMINATED by v44 (lift vs v44 < 0): {n_dominated}")
    print(f"\n  Per S69 lesson: catalog candidates dominated by v44 should NOT")
    print(f"  ship; the hybrid extension (v56 = blanket trips → v44) captures")
    print(f"  strictly more.")

    # Persist
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote summary to {OUT_JSON}")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
