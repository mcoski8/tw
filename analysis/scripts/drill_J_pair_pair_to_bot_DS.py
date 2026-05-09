"""
Session 46 — Drill D: J-pair pair-to-bot + DS focused drill.

Drill A (Session 45) per-pair-rank breakdown found that A5 − A2 = +$2,975/1000h
at P=J specifically (vs negative or near-zero for P=2..T). A5 = "pair-in-bot
+ DS-bot"; A2 = "pair-in-mid + non-DS-bot". This focused drill answers two
critical follow-ups:

  1. Does pair-to-bot + DS beat v41's actual pick (which is pair-in-mid +
     DS-bot when achievable)? Drill A's headline A5-A2 compared to non-DS
     pair-mid; the right apples-to-apples is A5 vs A1 (pair-mid + DS).

  2. Does the v41 production pick already capture the J-pair signal, or is
     there residual lift available from a Rule 11 that overrides v41 for
     J-pair specifically?

Population: cat=pair AND P=11 AND max_rank=11 (J-pair-J cell).
Population size: 34,272 hands (10% of J-low pair zone, 0.57% of grid).

Method: for each hand, compute best EV in each of A1..A6 classes (S45 Drill A
schema). Also compute v41's production pick EV. Within-hand pairwise lift:

  A5 vs A1  : pair-to-bot DS vs pair-mid DS (the apples-to-apples question)
  A5 vs v41 : pair-to-bot DS vs production pick (the "should we override v41?" question)
  A1 vs v41 : pair-mid DS vs production pick (sanity check — should be ≥0 since
              v41 picks among DS-mid settings; positive means there's a better
              DS-mid pick than v41's tie-break)

Validation: full grid (N=200) and prefix grid (N=1000). J-pair-J has
prefix coverage but pair=11 hands skew higher in the canonical ID space
than pair=2, so prefix coverage is partial.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_J_pair_pair_to_bot_DS.py
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
from strategy_v41_rule10_v3_ds import strategy_v41_rule10_v3_ds  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0

N_CLASSES = 6  # A1..A6 same as Drill A
CLASS_LABELS = {
    0: "A1 pair-mid + DS",
    1: "A2 pair-mid + non-DS",
    2: "A3 pair-split + DS",
    3: "A4 pair-split + non-DS",
    4: "A5 pair-bot + DS",
    5: "A6 pair-bot + non-DS",
}


def classify_settings(feats, P: int) -> np.ndarray:
    """Return per-setting class index (105,), int8, -1 if invalid."""
    pair_in_mid = feats.mid_is_pair & (feats.mid_pair_rank == P)
    pair_in_bot = (feats.bot_pair_rank == P) & ~pair_in_mid
    pair_split = ~pair_in_mid & ~pair_in_bot
    is_ds = feats.bot_suit_profile == SUIT_PROFILE_DS

    classes = np.full(105, -1, dtype=np.int8)
    classes[pair_in_mid & is_ds] = 0
    classes[pair_in_mid & ~is_ds] = 1
    classes[pair_split & is_ds] = 2
    classes[pair_split & ~is_ds] = 3
    classes[pair_in_bot & is_ds] = 4
    classes[pair_in_bot & ~is_ds] = 5
    return classes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 46 Drill D: J-pair (P=11 AND max=11) pair-to-bot + DS focus")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    pair_idx = np.where(cats == 1)[0]

    print("\n[2/4] filtering to J-pair (P=11 AND max=11) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    for cid in pair_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) != 11:
            continue
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        if P != 11:
            continue
        scope_cids.append(int(cid))
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    P = 11
    print(f"  J-pair-J scope: {len(scope_cids):,}  "
          f"({100*len(scope_cids)/n_total:.4f}% of grid)")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        scope_cids = scope_cids[np.sort(idx)]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Per-class accumulators
    sum_lift_full = np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)
    n_pairs_full = np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)
    n_ach_full = np.zeros(N_CLASSES, dtype=np.int64)
    n_hands_full = 0
    sum_lift_pref = np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)
    n_pairs_pref = np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)
    n_ach_pref = np.zeros(N_CLASSES, dtype=np.int64)
    n_hands_pref = 0

    # v41 pick comparisons: per class A_i, sum_lift_v41[i] = sum over hands
    # where class i is achievable AND v41's pick is also evaluated, of
    # (best_in_class_i - v41_pick_ev). n_v41[i] = count.
    sum_lift_v41_full = np.zeros(N_CLASSES, dtype=np.float64)
    n_v41_full = np.zeros(N_CLASSES, dtype=np.int64)
    sum_lift_v41_pref = np.zeros(N_CLASSES, dtype=np.float64)
    n_v41_pref = np.zeros(N_CLASSES, dtype=np.int64)

    # Track v41's class distribution (which class does v41's pick fall into?)
    v41_class_distribution_full = np.zeros(N_CLASSES + 1, dtype=np.int64)  # last bin = 'invalid/-1'
    v41_class_distribution_pref = np.zeros(N_CLASSES + 1, dtype=np.int64)

    print("\n[4/4] per-hand within-hand pairwise enumeration ...", flush=True)
    t0 = time.time()
    n = len(scope_cids)
    for i in range(n):
        cid = int(scope_cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        classes = classify_settings(feats, P)

        v41_pick = int(strategy_v41_rule10_v3_ds(h))
        v41_class = int(classes[v41_pick])

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v41_ev_full = float(rowf[v41_pick])
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
                sum_lift_v41_full[k] += best_full[k] - v41_ev_full
                n_v41_full[k] += 1
        if v41_class < 0:
            v41_class_distribution_full[N_CLASSES] += 1
        else:
            v41_class_distribution_full[v41_class] += 1

        if cid < 500_000:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            v41_ev_pref = float(rowp[v41_pick])
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
                    sum_lift_v41_pref[k] += best_pref[k] - v41_ev_pref
                    n_v41_pref[k] += 1
            if v41_class < 0:
                v41_class_distribution_pref[N_CLASSES] += 1
            else:
                v41_class_distribution_pref[v41_class] += 1

        if (i + 1) % 5000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    def fmt_dollar(x):
        if np.isnan(x):
            return "      n/a"
        return f"${x:>+9.1f}"

    def report(label, n_h, sum_lift, n_pairs, n_ach,
               sum_lift_v41, n_v41, v41_dist):
        print("=" * 100)
        print(f"AGGREGATE: {label}  (n_hands={n_h:,})")
        print("=" * 100)
        if n_h == 0:
            print("  (no hands)\n")
            return

        print(f"\n── ACHIEVABILITY (% of hands where class achievable) ──")
        for k in range(N_CLASSES):
            pct = 100 * n_ach[k] / n_h
            print(f"  {CLASS_LABELS[k]:<26}  {n_ach[k]:>7,}  ({pct:>5.1f}%)")

        print(f"\n── v41 PRODUCTION PICK CLASS DISTRIBUTION ──")
        for k in range(N_CLASSES):
            pct = 100 * v41_dist[k] / n_h
            print(f"  {CLASS_LABELS[k]:<26}  {v41_dist[k]:>7,}  ({pct:>5.1f}%)")
        if v41_dist[N_CLASSES] > 0:
            pct = 100 * v41_dist[N_CLASSES] / n_h
            print(f"  {'(invalid/unclassified)':<26}  {v41_dist[N_CLASSES]:>7,}  ({pct:>5.1f}%)")

        print(f"\n── v41 vs BEST-IN-CLASS (within-hand, $/1000h) ──")
        print(f"  Positive = best-in-class beats v41 on those hands")
        print(f"  {'class':<26}  {'n':>7}  {'lift_vs_v41':>14}")
        for k in range(N_CLASSES):
            if n_v41[k] == 0:
                continue
            lift = sum_lift_v41[k] / n_v41[k] * EV_TO_DOL * 1000
            print(f"  {CLASS_LABELS[k]:<26}  {n_v41[k]:>7,}  {fmt_dollar(lift):>14}")

        print(f"\n── PAIRWISE LIFT (EV(row) − EV(col), $/1000h, within-hand) ──")
        with np.errstate(invalid="ignore", divide="ignore"):
            lift = sum_lift / np.where(n_pairs > 0, n_pairs, 1)
        lift_dol = lift * EV_TO_DOL * 1000
        print(f"  {'row\\col':<26}  " + "  ".join(
            f"{f'A{j+1}':>10}" for j in range(N_CLASSES)))
        for i in range(N_CLASSES):
            row_str = f"  {CLASS_LABELS[i]:<26}  "
            for j in range(N_CLASSES):
                if i == j or n_pairs[i, j] == 0:
                    row_str += f"  {'─':>10}"
                else:
                    row_str += f"  {lift_dol[i, j]:>+10.1f}"
            print(row_str)

        print(f"\n── HEADLINE COMPARISONS (within-hand) ──")
        headline = [
            (4, 0, "A5 − A1: pair-to-bot DS vs pair-mid DS (apples-to-apples Rule 11 question)"),
            (4, 1, "A5 − A2: pair-to-bot DS vs pair-mid non-DS (Drill A's reported headline)"),
            (0, 1, "A1 − A2: DS premium WITHIN pair-mid (Rule 10 v3 internal lift)"),
            (4, 5, "A5 − A6: DS premium WITHIN pair-bot"),
        ]
        for i, j, label in headline:
            np_pairs = n_pairs[i, j]
            if np_pairs == 0:
                print(f"  {label}: n=0")
                continue
            lf = sum_lift[i, j] / np_pairs * EV_TO_DOL * 1000
            verdict = "row wins" if lf > 0 else "col wins"
            print(f"  {label}")
            print(f"    n_co-achievable = {np_pairs:>7,}  |  lift = ${lf:>+9.1f}/1000h  ({verdict})")

    report("FULL GRID  (N=200)", n_hands_full, sum_lift_full, n_pairs_full,
           n_ach_full, sum_lift_v41_full, n_v41_full,
           v41_class_distribution_full)
    print()
    report("PREFIX GRID (N=1000)", n_hands_pref, sum_lift_pref, n_pairs_pref,
           n_ach_pref, sum_lift_v41_pref, n_v41_pref,
           v41_class_distribution_pref)

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
