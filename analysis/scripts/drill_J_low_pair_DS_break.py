"""
Session 45 — Drill A: J-low single-pair DS-bot vs pair-anchor (within-hand).

Question (from S44 closure): v40b's Rule 10 gates the pair into mid and the
4 highest non-pair singletons into bot, with NO suit-aware bot construction.
S44 proved suit dominates connectivity in the J-low no-pair zone. Does the
same suit-dominance pattern hold for J-low pair when the cost of getting a
DS bot is breaking the pair anchor?

Within-hand pairwise classes (pair_state × bot_suit, 6 classes):

  A1  pair-in-mid + DS-bot       (Rule 10 baseline + DS-singletons; rare)
  A2  pair-in-mid + non-DS-bot   (Rule 10 typical case)
  A3  pair-split + DS-bot        (DS achieved by breaking the pair)
  A4  pair-split + non-DS-bot
  A5  pair-in-bot + DS-bot       (DS by moving pair to bot for 2-pair anchor)
  A6  pair-in-bot + non-DS-bot

For each hand, find the best EV achievable in each class (NaN if not
achievable on this hand). Within-hand pairwise lift = EV(best_A) - EV(best_B)
averaged across hands where both are achievable. Eliminates the cross-class
hand-population confounder (S44 methodology rule).

Headline pairwise comparisons:
  A3 - A2  : DS via pair-break vs non-DS pair anchor      (THE question)
  A5 - A2  : DS via pair-to-bot vs non-DS pair anchor
  A3 - A1  : pair-broken DS vs pair-anchored DS (both DS, pair stays vs broken)
  A5 - A1  : pair-to-bot DS vs pair-anchored DS
  A1 - A2  : DS premium WITHIN pair-in-mid (Rule 10 internal lift)

Per-pair-rank stratification: J-low pair is pair_rank ∈ {2..J}. We also break
results down by pair_rank cell so we can detect a cell-specific tipping point
(does the answer differ for pair=2 vs pair=J?).

Validation: full grid (N=200) AND prefix grid (N=1000). J-low pair has decent
prefix coverage (per Session 43 docs, ~10% of prefix is J-high pair, but most
prefix pair=2).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_J_low_pair_DS_break.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_J_low_pair_DS_break.py --sample 5000
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

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}

N_CLASSES = 6
CLASS_LABELS = {
    0: "A1 pair-mid + DS",
    1: "A2 pair-mid + non-DS",
    2: "A3 pair-split + DS",
    3: "A4 pair-split + non-DS",
    4: "A5 pair-bot + DS",
    5: "A6 pair-bot + non-DS",
}


def classify_settings(feats, P: int) -> np.ndarray:
    """Return per-setting class index (105,), int8, -1 if invalid.

    Class encoding:
      0 = A1 pair-mid + DS
      1 = A2 pair-mid + non-DS
      2 = A3 pair-split + DS
      3 = A4 pair-split + non-DS
      4 = A5 pair-bot + DS
      5 = A6 pair-bot + non-DS
    """
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


def fmt_dollar(x):
    if np.isnan(x):
        return "       n/a"
    return f"${x:>+9.1f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, randomly subsample N hands per pair_rank cell.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 45 Drill A: J-low single-pair DS-break vs pair-anchor (within-hand)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    pair_idx = np.where(cats == 1)[0]
    print(f"  total hands: {n_total:,}")
    print(f"  cat=pair    : {len(pair_idx):,}")

    print("\n[2/4] filtering to J-low pair (max_r ≤ 11) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    pair_rank = []
    for cid in pair_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) > 11:
            continue
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        scope_cids.append(int(cid))
        pair_rank.append(P)
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    pair_rank = np.asarray(pair_rank, dtype=np.int8)
    print(f"  J-low pair scope: {len(scope_cids):,}")
    print(f"  pair_rank distribution:")
    for P in range(2, 12):
        n = (pair_rank == P).sum()
        print(f"    P={RANK_CHAR[P]}: {n:>7,}  ({100*n/len(scope_cids):>5.2f}%)")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        keep = []
        for P in range(2, 12):
            mask = (pair_rank == P)
            idx = np.where(mask)[0]
            if len(idx) > args.sample:
                idx = rng.choice(idx, size=args.sample, replace=False)
            keep.extend(idx.tolist())
        keep = np.asarray(sorted(keep))
        scope_cids = scope_cids[keep]
        pair_rank = pair_rank[keep]
        print(f"  [sample mode: capped each P-cell at {args.sample}; "
              f"total={len(scope_cids):,}]")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Per-cell accumulators (cell = pair_rank), and overall.
    # For each cell, hold:
    #   sum_lift_full[A, B]  : sum over hands of EV(A) - EV(B) where both ach.
    #   n_pairs_full[A, B]   : count of co-achievability
    #   n_classes_ach_full[A]: count of hands where class A is achievable
    #   n_hands_full         : total hands processed in cell
    # Same for prefix.
    P_RANGE = list(range(2, 12))  # 2..J
    cells_full = {P: {
        "sum_lift": np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64),
        "n_pairs":  np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64),
        "n_ach":    np.zeros(N_CLASSES, dtype=np.int64),
        "n_hands":  0,
    } for P in P_RANGE}
    cells_pref = {P: {
        "sum_lift": np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64),
        "n_pairs":  np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64),
        "n_ach":    np.zeros(N_CLASSES, dtype=np.int64),
        "n_hands":  0,
    } for P in P_RANGE}

    print("\n[4/4] per-hand within-hand pairwise enumeration ...", flush=True)
    t0 = time.time()
    n_total_scope = len(scope_cids)
    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        P = int(pair_rank[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        classes = classify_settings(feats, P)

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        # Best EV per class (NaN if class not achievable on this hand)
        best_full = np.full(N_CLASSES, np.nan, dtype=np.float64)
        for k in range(N_CLASSES):
            mask = classes == k
            if mask.any():
                best_full[k] = float(rowf[mask].max())

        avail = ~np.isnan(best_full)
        if avail.sum() >= 2:
            diff = best_full[:, None] - best_full[None, :]
            both = avail[:, None] & avail[None, :]
            cells_full[P]["sum_lift"] += np.where(both, diff, 0.0)
            cells_full[P]["n_pairs"] += both.astype(np.int64)
        cells_full[P]["n_ach"] += avail.astype(np.int64)
        cells_full[P]["n_hands"] += 1

        if cid < 500_000:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            best_pref = np.full(N_CLASSES, np.nan, dtype=np.float64)
            for k in range(N_CLASSES):
                mask = classes == k
                if mask.any():
                    best_pref[k] = float(rowp[mask].max())
            avail_p = ~np.isnan(best_pref)
            if avail_p.sum() >= 2:
                diff_p = best_pref[:, None] - best_pref[None, :]
                both_p = avail_p[:, None] & avail_p[None, :]
                cells_pref[P]["sum_lift"] += np.where(both_p, diff_p, 0.0)
                cells_pref[P]["n_pairs"] += both_p.astype(np.int64)
            cells_pref[P]["n_ach"] += avail_p.astype(np.int64)
            cells_pref[P]["n_hands"] += 1

        if (i + 1) % 5000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # ── Reporting ──
    # Aggregate across all P-cells for the headline
    agg_full = {
        "sum_lift": sum(cells_full[P]["sum_lift"] for P in P_RANGE),
        "n_pairs":  sum(cells_full[P]["n_pairs"]  for P in P_RANGE),
        "n_ach":    sum(cells_full[P]["n_ach"]    for P in P_RANGE),
        "n_hands":  sum(cells_full[P]["n_hands"]  for P in P_RANGE),
    }
    agg_pref = {
        "sum_lift": sum(cells_pref[P]["sum_lift"] for P in P_RANGE),
        "n_pairs":  sum(cells_pref[P]["n_pairs"]  for P in P_RANGE),
        "n_ach":    sum(cells_pref[P]["n_ach"]    for P in P_RANGE),
        "n_hands":  sum(cells_pref[P]["n_hands"]  for P in P_RANGE),
    }

    def report(label, agg):
        print("=" * 100)
        print(f"AGGREGATE: {label}  (n_hands={agg['n_hands']:,})")
        print("=" * 100)
        n_h = agg["n_hands"]
        if n_h == 0:
            print("  (no hands)\n")
            return

        # Achievability per class
        print(f"\n── ACHIEVABILITY (% of hands where class achievable) ──")
        for k in range(N_CLASSES):
            pct = 100 * agg["n_ach"][k] / n_h
            print(f"  {CLASS_LABELS[k]:<26}  {agg['n_ach'][k]:>7,}  ({pct:>5.1f}%)")

        # Pairwise lift matrix
        print(f"\n── PAIRWISE LIFT MATRIX  EV(row) − EV(col) in $/1000h ──")
        with np.errstate(invalid="ignore", divide="ignore"):
            lift = agg["sum_lift"] / np.where(agg["n_pairs"] > 0,
                                               agg["n_pairs"], 1)
        lift_dol = lift * EV_TO_DOL * 1000

        print(f"  {'row\\col':<26}  " + "  ".join(
            f"{f'A{j+1}':>10}" for j in range(N_CLASSES)))
        for i in range(N_CLASSES):
            row_str = f"  {CLASS_LABELS[i]:<26}  "
            for j in range(N_CLASSES):
                if i == j or agg["n_pairs"][i, j] == 0:
                    row_str += f"  {'─':>10}"
                else:
                    row_str += f"  {lift_dol[i, j]:>+10.1f}"
            print(row_str)

        # Headline comparisons
        print(f"\n── HEADLINE COMPARISONS (within-hand, $/1000h lift = row−col) ──")
        headline = [
            (2, 1, "A3 − A2: DS via pair-break vs non-DS pair-anchor (THE question)"),
            (4, 1, "A5 − A2: DS via pair-to-bot vs non-DS pair-anchor"),
            (2, 0, "A3 − A1: pair-broken DS vs pair-anchored DS"),
            (4, 0, "A5 − A1: pair-to-bot DS vs pair-anchored DS"),
            (0, 1, "A1 − A2: DS premium WITHIN pair-in-mid (Rule 10 internal lift)"),
            (2, 3, "A3 − A4: DS premium WITHIN pair-split"),
            (4, 5, "A5 − A6: DS premium WITHIN pair-in-bot"),
            (3, 1, "A4 − A2: pair-split (non-DS) vs pair-mid (non-DS)"),
            (5, 1, "A6 − A2: pair-bot (non-DS) vs pair-mid (non-DS)"),
        ]
        for i, j, label in headline:
            n = agg["n_pairs"][i, j]
            if n == 0:
                print(f"  {label}: n=0 (no co-achievable hands)")
                continue
            lf = agg["sum_lift"][i, j] / n * EV_TO_DOL * 1000
            verdict = "row wins" if lf > 0 else "col wins"
            print(f"  {label}")
            print(f"    n_co-achievable = {n:>7,}  |  lift = ${lf:>+9.1f}/1000h  ({verdict})")

    report("FULL GRID  (N=200)", agg_full)
    print()
    report("PREFIX GRID (N=1000)", agg_pref)
    print()

    # Per-pair-rank breakdown
    print("=" * 100)
    print("PER-PAIR-RANK BREAKDOWN (full grid only — per cell may be sparse)")
    print("=" * 100)
    print(f"  Headline lift A3 − A2 (DS-break vs pair-anchor non-DS), per pair_rank:")
    print(f"  {'P':<3} {'n_hands':>9} {'n_co_A3A2':>11}  {'A3-A2($/1000h)':>16}  "
          f"{'n_co_A5A2':>11}  {'A5-A2($/1000h)':>16}")
    for P in P_RANGE:
        cell = cells_full[P]
        if cell["n_hands"] == 0:
            continue
        n_a3a2 = cell["n_pairs"][2, 1]
        n_a5a2 = cell["n_pairs"][4, 1]
        lift_a3a2 = (cell["sum_lift"][2, 1] / n_a3a2 * EV_TO_DOL * 1000
                     if n_a3a2 > 0 else float('nan'))
        lift_a5a2 = (cell["sum_lift"][4, 1] / n_a5a2 * EV_TO_DOL * 1000
                     if n_a5a2 > 0 else float('nan'))
        print(f"  {RANK_CHAR[P]:<3} {cell['n_hands']:>9,} {n_a3a2:>11,}  "
              f"{fmt_dollar(lift_a3a2):>16}  {n_a5a2:>11,}  "
              f"{fmt_dollar(lift_a5a2):>16}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
