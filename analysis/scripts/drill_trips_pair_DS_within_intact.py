"""
Session 49 — Drill I: trips_pair within-class DS-bot.

Trips_pair (cat=4, 171,600 hands, 2.86% of grid) = 1 trip (HHH) + 1 pair
(PP) + 2 singletons. Total 7 cards.

For "pair anchor preserved" structures, classify each setting by
pair_state × bot_suit:

  pair_state:
    - pair_in_mid (mid_is_pair == True with mid_pair_rank == P)
    - pair_in_bot (bot_pair_rank == P)
    - pair_split (otherwise)

  bot_suit_profile: DS (2+2) vs non-DS

For each hand, compute best EV per class. Within-hand pairwise lift
identifies the production-target class.

Note on trip-suit interaction: trip has 3 cards across 3 distinct suits
(in canonical hands). The 4th suit is "missing" from trip. This
constrains DS-bot achievability:
- Trip-in-bot (3 trip cards in bot) → bot has 3 distinct suits → DS impossible.
- Trip split (e.g., 2 trip + 2 other in bot) can be DS if the other 2
  cards' suits match the 2 chosen trip suits.

Compare against v44 production pick (which falls through to Rule 3
"split trips, keep pair" type logic via v14_combined).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_pair_DS_within_intact.py
"""
from __future__ import annotations

import argparse
import sys
import time
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
from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}

N_CLASSES = 6
CLASS_LABELS = {
    0: "V1 pair-mid + DS",
    1: "V2 pair-mid + non-DS",
    2: "V3 pair-bot + DS",
    3: "V4 pair-bot + non-DS",
    4: "V5 pair-split + DS",
    5: "V6 pair-split + non-DS",
}


def classify_settings(feats, P: int) -> np.ndarray:
    pair_in_mid = feats.mid_is_pair & (feats.mid_pair_rank == P)
    pair_in_bot = (feats.bot_pair_rank == P) & ~pair_in_mid
    pair_split = ~pair_in_mid & ~pair_in_bot
    is_ds = feats.bot_suit_profile == SUIT_PROFILE_DS

    classes = np.full(105, -1, dtype=np.int8)
    classes[pair_in_mid & is_ds] = 0
    classes[pair_in_mid & ~is_ds] = 1
    classes[pair_split & is_ds] = 2  # placeholder, fix below
    classes[pair_split & ~is_ds] = 3
    classes[pair_in_bot & is_ds] = 4
    classes[pair_in_bot & ~is_ds] = 5
    # Re-assign (since I want pair_in_bot first, pair_split last)
    classes2 = np.full(105, -1, dtype=np.int8)
    classes2[pair_in_mid & is_ds] = 0
    classes2[pair_in_mid & ~is_ds] = 1
    classes2[pair_in_bot & is_ds] = 2
    classes2[pair_in_bot & ~is_ds] = 3
    classes2[pair_split & is_ds] = 4
    classes2[pair_split & ~is_ds] = 5
    return classes2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 49 Drill I: trips_pair within-class DS-bot variant sweep")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    tp_idx = np.where(cats == 4)[0]
    print(f"  cat=trips_pair: {len(tp_idx):,}")

    print("\n[2/4] extracting (trip_rank, pair_rank, max_r) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    p_info = []  # list of (trip_rank, pair_rank, max_rank)
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
        pair_rank = next(r for r in range(2, 15) if rc[r] == 2)
        max_r = int(ranks.max())
        scope_cids.append(int(cid))
        p_info.append((trip_rank, pair_rank, max_r))
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

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    sum_lift_full = np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)
    n_pairs_full = np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)
    n_ach_full = np.zeros(N_CLASSES, dtype=np.int64)
    n_hands_full = 0
    sum_lift_pref = np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)
    n_pairs_pref = np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)
    n_ach_pref = np.zeros(N_CLASSES, dtype=np.int64)
    n_hands_pref = 0

    # v44 vs best-in-class (the single-cell rule discovery lens)
    sum_lift_v44_full = np.zeros(N_CLASSES, dtype=np.float64)
    n_v44_full = np.zeros(N_CLASSES, dtype=np.int64)
    sum_lift_v44_pref = np.zeros(N_CLASSES, dtype=np.float64)
    n_v44_pref = np.zeros(N_CLASSES, dtype=np.int64)

    v44_class_dist_full = np.zeros(N_CLASSES + 1, dtype=np.int64)
    v44_class_dist_pref = np.zeros(N_CLASSES + 1, dtype=np.int64)

    print("\n[4/4] per-hand within-hand pairwise enumeration ...", flush=True)
    t0 = time.time()
    n_total_scope = len(scope_cids)
    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        trip_rank, pair_rank, max_r = p_info[i]
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        classes = classify_settings(feats, pair_rank)

        v44_pick = strategy_v44_rule13_three_pair_DS(h)
        v44_class = int(classes[v44_pick])

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v44_ev = float(rowf[v44_pick])
        best_full = np.full(N_CLASSES, np.nan, dtype=np.float64)
        for k in range(N_CLASSES):
            mask = classes == k
            if mask.any():
                best_full[k] = float(rowf[mask].max())
        avail = ~np.isnan(best_full)
        if avail.sum() >= 2:
            diff = best_full[:, None] - best_full[None, :]
            both = avail[:, None] & avail[None, :]
            sum_lift_full += np.where(both, diff, 0.0)
            n_pairs_full += both.astype(np.int64)
        n_ach_full += avail.astype(np.int64)
        n_hands_full += 1
        for k in range(N_CLASSES):
            if not np.isnan(best_full[k]):
                sum_lift_v44_full[k] += best_full[k] - v44_ev
                n_v44_full[k] += 1
        if v44_class < 0:
            v44_class_dist_full[N_CLASSES] += 1
        else:
            v44_class_dist_full[v44_class] += 1

        if cid < 500_000:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            v44_ev_p = float(rowp[v44_pick])
            best_pref = np.full(N_CLASSES, np.nan, dtype=np.float64)
            for k in range(N_CLASSES):
                mask = classes == k
                if mask.any():
                    best_pref[k] = float(rowp[mask].max())
            avail_p = ~np.isnan(best_pref)
            if avail_p.sum() >= 2:
                diff_p = best_pref[:, None] - best_pref[None, :]
                both_p = avail_p[:, None] & avail_p[None, :]
                sum_lift_pref += np.where(both_p, diff_p, 0.0)
                n_pairs_pref += both_p.astype(np.int64)
            n_ach_pref += avail_p.astype(np.int64)
            n_hands_pref += 1
            for k in range(N_CLASSES):
                if not np.isnan(best_pref[k]):
                    sum_lift_v44_pref[k] += best_pref[k] - v44_ev_p
                    n_v44_pref[k] += 1
            if v44_class < 0:
                v44_class_dist_pref[N_CLASSES] += 1
            else:
                v44_class_dist_pref[v44_class] += 1

        if (i + 1) % 10000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    def report(label, n_h, sum_lift, n_pairs, n_ach,
               sum_v44, n_v44, v44_dist):
        print("=" * 100)
        print(f"AGGREGATE: {label}  (n_hands={n_h:,})")
        print("=" * 100)
        if n_h == 0:
            return
        print(f"\n── ACHIEVABILITY (% where class achievable) ──")
        for k in range(N_CLASSES):
            pct = 100 * n_ach[k] / n_h
            print(f"  {CLASS_LABELS[k]:<26}  {n_ach[k]:>7,}  ({pct:>5.1f}%)")

        print(f"\n── v44 PRODUCTION PICK CLASS DISTRIBUTION ──")
        for k in range(N_CLASSES):
            pct = 100 * v44_dist[k] / n_h
            print(f"  {CLASS_LABELS[k]:<26}  {v44_dist[k]:>7,}  ({pct:>5.1f}%)")
        if v44_dist[N_CLASSES] > 0:
            pct = 100 * v44_dist[N_CLASSES] / n_h
            print(f"  {'(invalid/-1)':<26}  {v44_dist[N_CLASSES]:>7,}  ({pct:>5.1f}%)")

        print(f"\n── v44 vs BEST-IN-CLASS (within-hand, $/1000h) ──")
        print(f"  {'class':<26}  {'n':>7}  {'lift_vs_v44':>14}")
        for k in range(N_CLASSES):
            if n_v44[k] == 0:
                continue
            lift = sum_v44[k] / n_v44[k] * EV_TO_DOL * 1000
            print(f"  {CLASS_LABELS[k]:<26}  {n_v44[k]:>7,}  ${lift:>+12.1f}")

        print(f"\n── HEADLINE COMPARISONS ──")
        headline = [
            (0, 1, "V1 − V2: DS premium WITHIN pair-mid"),
            (2, 3, "V3 − V4: DS premium WITHIN pair-bot"),
            (4, 5, "V5 − V6: DS premium WITHIN pair-split"),
            (0, 2, "V1 − V3: pair-mid vs pair-bot (both DS)"),
            (0, 4, "V1 − V5: pair-mid vs pair-split (both DS)"),
            (2, 4, "V3 − V5: pair-bot vs pair-split (both DS)"),
        ]
        for i, j, lab in headline:
            n = n_pairs[i, j]
            if n == 0:
                print(f"  {lab}: n=0")
                continue
            lf = sum_lift[i, j] / n * EV_TO_DOL * 1000
            verdict = "row wins" if lf > 0 else "col wins"
            print(f"  {lab}")
            print(f"    n_co-achievable = {n:>7,}  |  ${lf:>+9.1f}/1000h  ({verdict})")

    report("FULL GRID  (N=200)", n_hands_full, sum_lift_full, n_pairs_full,
           n_ach_full, sum_lift_v44_full, n_v44_full, v44_class_dist_full)
    print()
    report("PREFIX GRID (N=1000)", n_hands_pref, sum_lift_pref, n_pairs_pref,
           n_ach_pref, sum_lift_v44_pref, n_v44_pref, v44_class_dist_pref)

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
