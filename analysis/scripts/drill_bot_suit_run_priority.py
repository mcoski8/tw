"""
Session 44 — bot suit × connectivity priority hierarchy drill.

Question (from Session 43 closure conversation): the project's existing
methodology rule "DS > SS > rainbow > 3+1 > 4-flush" was extracted from
trips territory (Rule 6 Step 2 + Session 40 connectivity probe). It has
NEVER been head-to-head tested for J-low pair or J-low no-pair populations,
and connectivity (run-3, run-4, one-gap-4, etc.) has NOT been formally
placed in the hierarchy.

Drill: empirically test the FULL cross product of:

  Suit classes (5):
    DS       (2+2 distribution)
    SS       (2+1+1 distribution)
    Rainbow  (1+1+1+1)
    3+1      (3 of one suit + 1)
    4-flush  (4+0)

  Connectivity classes (7, mutually exclusive partition based on
  the 4 sorted bot ranks and their adjacency pattern):
    run-4               4 consecutive ranks (e.g., 5-6-7-8)
    one-gap-4           span 4 with 1 missing inside (e.g., 5-7-8-9; 4-5-6-8)
    run-3+stray         span 5+ with run-3 + 1 distant card (e.g., 5-6-7-T)
    two-runs-2          two separated run-2 chunks (e.g., 5-6-9-T)
    two-gap-4           span 5 with 2 missing inside (e.g., 4-6-7-9)
    run-2+strays        1 run-2 + 2 isolated strays (e.g., 5-6-9-J)
    scattered           no two adjacent (e.g., 5-8-J-2)

  Wheel-eligibility: NOT applicable since max ≤ J → no Ace possible.

Cross product = 5 × 7 = 35 base classes.

Per hand: enumerate all 105 settings (or restrict to mid=pair for the
pair population), classify each by (suit, conn), then for each class
that's achievable on the hand, find the best EV among settings producing
that class. Compare to overall oracle EV.

Aggregation per (population, suit_class, conn_class):
  - n_hands_achievable
  - mean best EV in class (across achievable hands)
  - mean regret vs overall oracle (mean_oracle - mean_best_in_class)
  - mean regret expressed as $/hand within-class
  - rank classes by mean regret

Populations:
  - J-low pair: max_rank ≤ J AND category == pair (343K hands).
                Filter to mid=pair settings only.
  - J-low no-pair: max_rank ≤ J AND category == high_only (86K hands).
                   All 105 settings.

Validation: full grid (N=200) AND prefix grid (N=1000). Note: high_only
has zero prefix coverage; pair has SOME prefix coverage (mostly pair=2).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_priority.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_priority.py --sample 1000
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_priority.py --pair-only
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_priority.py --no-pair-only
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
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
    SETTING_HAND_INDICES,
    SUIT_PROFILE_DS,
    SUIT_PROFILE_SS,
    SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE,
    SUIT_PROFILE_FOUR_FLUSH,
)

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0

# Connectivity class codes
CONN_RUN_4 = 0
CONN_ONE_GAP_4 = 1
CONN_RUN_3_STRAY = 2
CONN_TWO_RUNS_2 = 3
CONN_TWO_GAP_4 = 4
CONN_RUN_2_STRAYS = 5
CONN_SCATTERED = 6

CONN_LABELS = {
    CONN_RUN_4: "run-4",
    CONN_ONE_GAP_4: "one-gap-4",
    CONN_RUN_3_STRAY: "run-3+stray",
    CONN_TWO_RUNS_2: "two-runs-2",
    CONN_TWO_GAP_4: "two-gap-4",
    CONN_RUN_2_STRAYS: "run-2+strays",
    CONN_SCATTERED: "scattered",
}
N_CONN = 7

SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS",
    SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "rainbow",
    SUIT_PROFILE_THREE_ONE: "3+1",
    SUIT_PROFILE_FOUR_FLUSH: "4-flush",
}
SUIT_ORDER = [SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
              SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH]
N_SUIT = 5


def compute_connectivity_classes(hand_bytes: np.ndarray) -> np.ndarray:
    """Return per-setting connectivity-class array of shape (105,) for the
    given 7-card hand. Vectorized.

    Each setting's bot has 4 cards. We sort by rank, compute pairwise diffs,
    and classify by (n_adjacencies, span, diff pattern).
    """
    permuted = hand_bytes[SETTING_HAND_INDICES]  # (105, 7)
    bot_bytes = permuted[:, 3:]  # (105, 4)
    bot_ranks = (bot_bytes // 4 + 2).astype(np.int8)  # (105, 4)
    sorted_ranks = np.sort(bot_ranks, axis=1)  # (105, 4)
    diffs = np.diff(sorted_ranks, axis=1)  # (105, 3)
    span = (sorted_ranks[:, -1] - sorted_ranks[:, 0]).astype(np.int8)
    n_adj = (diffs == 1).sum(axis=1)

    classes = np.full(105, -1, dtype=np.int8)

    # 3 adjacencies → run-4 (must have span 3 since 4 distinct ranks)
    classes[n_adj == 3] = CONN_RUN_4

    # 2 adjacencies cases:
    # diff patterns under 2 adj:
    #   [1,1,k] / [k,1,1]: run-3 chunk + 1 stray. span = 3 + k.
    #     k=2 (span 4) → one-gap-4 (run-3 + close stray inside 5-rank window)
    #     k≥3 (span 5+) → run-3+stray
    #   [1,k,1] (k≥2): two run-2 chunks. span = 2 + k.
    #     k=2 (span 4) → also one-gap-4 (two run-2 within 5-rank window)
    #     k≥3 (span 5+) → two-runs-2
    mask_2adj = (n_adj == 2)
    pat_run3_left = (diffs[:, 0] == 1) & (diffs[:, 1] == 1)  # [1,1,?]
    pat_run3_right = (diffs[:, 1] == 1) & (diffs[:, 2] == 1)  # [?,1,1]
    pat_run3 = pat_run3_left | pat_run3_right
    pat_two_runs_2 = mask_2adj & ~pat_run3  # [1,k,1] with k≥2

    classes[mask_2adj & pat_run3 & (span == 4)] = CONN_ONE_GAP_4
    classes[mask_2adj & pat_run3 & (span >= 5)] = CONN_RUN_3_STRAY
    classes[pat_two_runs_2 & (span == 4)] = CONN_ONE_GAP_4  # tight two-run case
    classes[pat_two_runs_2 & (span >= 5)] = CONN_TWO_RUNS_2

    # 1 adjacency cases:
    #   [2,1,2]: span 5, classic two-gap-4
    #   [k,1,m] / [k,m,1] / [1,k,m] with k,m≥2: run-2 + 2 strays
    mask_1adj = (n_adj == 1)
    pat_2_1_2 = (diffs[:, 0] == 2) & (diffs[:, 1] == 1) & (diffs[:, 2] == 2)
    classes[mask_1adj & pat_2_1_2] = CONN_TWO_GAP_4
    classes[mask_1adj & ~pat_2_1_2] = CONN_RUN_2_STRAYS

    # 0 adjacencies → scattered
    classes[n_adj == 0] = CONN_SCATTERED

    # NOTE: settings where the bot has duplicate ranks (e.g., for pair
    # hands where the pair is split into bot, giving bot ranks like
    # [2,2,3,4]) end up with diff[i]==0 somewhere, which doesn't match
    # any of the partitions above and stays at -1. These settings will
    # be filtered out by the population's valid_mask (mid=pair) since
    # bot-contains-pair implies mid is unpaired.
    return classes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, randomly subsample N hands per population")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pair-only", action="store_true")
    ap.add_argument("--no-pair-only", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 44: bot SUIT × CONNECTIVITY priority drill (J-low pair + no-pair)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    print(f"  total hands: {n_total:,}")

    print("\n[2/4] filtering to scope (J-low + cat in {0, 1}) ...", flush=True)
    t0 = time.time()
    scope_hands = []
    scope_pop = []  # 0 = no-pair, 1 = pair
    scope_pair_rank = []  # 0 if no-pair
    scope_max_rank = []
    for cid in range(n_total):
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        max_r = int(ranks.max())
        if max_r > 11:
            continue
        c = int(cats[cid])
        if c == 0 and not args.pair_only:
            scope_hands.append(int(cid))
            scope_pop.append(0)
            scope_pair_rank.append(0)
            scope_max_rank.append(max_r)
        elif c == 1 and not args.no_pair_only:
            rc = np.bincount(ranks, minlength=15)
            P = next(r for r in range(2, 15) if rc[r] == 2)
            scope_hands.append(int(cid))
            scope_pop.append(1)
            scope_pair_rank.append(P)
            scope_max_rank.append(max_r)
    scope_hands = np.asarray(scope_hands, dtype=np.int64)
    scope_pop = np.asarray(scope_pop, dtype=np.int8)
    scope_pair_rank = np.asarray(scope_pair_rank, dtype=np.int8)
    scope_max_rank = np.asarray(scope_max_rank, dtype=np.int8)
    print(f"  scope hands: {len(scope_hands):,}")
    print(f"    no-pair (cat 0, max ≤ J): {(scope_pop == 0).sum():,}")
    print(f"    pair    (cat 1, max ≤ J): {(scope_pop == 1).sum():,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        # Sample per-population
        sampled_indices = []
        for pop in (0, 1):
            mask = (scope_pop == pop)
            pop_idx = np.where(mask)[0]
            if len(pop_idx) > args.sample:
                pop_idx = rng.choice(pop_idx, size=args.sample, replace=False)
            sampled_indices.extend(pop_idx.tolist())
        sampled_indices = np.asarray(sorted(sampled_indices))
        scope_hands = scope_hands[sampled_indices]
        scope_pop = scope_pop[sampled_indices]
        scope_pair_rank = scope_pair_rank[sampled_indices]
        scope_max_rank = scope_max_rank[sampled_indices]
        print(f"  [sample mode: capped each population at {args.sample}; "
              f"total={len(scope_hands):,}]")

    full_pop_sizes = {
        0: int((scope_pop == 0).sum()),
        1: int((scope_pop == 1).sum()),
    }

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Per-population, per-(suit, conn) cell:
    #   n_achievable: count of hands where some setting (mid-restricted)
    #     produces this class
    #   sum_best: sum of best EV in class across achievable hands
    #   sum_oracle: sum of overall oracle EV across achievable hands
    #   sum_v40b: sum of v40b baseline EV across achievable hands (for ref)
    #   worst_regret: max regret-vs-oracle observed in class
    # Same fields for prefix.

    def make_cells():
        return {
            (s, c): {
                "n_full": 0, "sum_best_full": 0.0, "sum_oracle_full": 0.0, "worst_full": 0.0,
                "n_pref": 0, "sum_best_pref": 0.0, "sum_oracle_pref": 0.0, "worst_pref": 0.0,
            }
            for s in SUIT_ORDER for c in range(N_CONN)
        }
    cells = {0: make_cells(), 1: make_cells()}
    n_full_total = {0: 0, 1: 0}
    n_pref_total = {0: 0, 1: 0}
    sum_oracle_full = {0: 0.0, 1: 0.0}
    sum_oracle_pref = {0: 0.0, 1: 0.0}

    print("\n[4/4] per-hand cross-product enumeration ...", flush=True)
    t0 = time.time()
    n_hands = len(scope_hands)
    for i in range(n_hands):
        cid = int(scope_hands[i])
        pop = int(scope_pop[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)

        feats = setting_features_from_bytes(h)
        suit_classes = feats.bot_suit_profile  # shape (105,)
        conn_classes = compute_connectivity_classes(h)  # shape (105,)

        # Build the setting-mask: which settings count in this population's
        # mid restriction.
        if pop == 1:
            P = int(scope_pair_rank[i])
            mid_is_pair = feats.mid_is_pair & (feats.mid_pair_rank == P)
            valid_mask = mid_is_pair
        else:
            valid_mask = np.ones(105, dtype=bool)

        if not valid_mask.any():
            continue

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        ev_oracle_full = float(rowf[valid_mask].max())  # oracle within population
        n_full_total[pop] += 1
        sum_oracle_full[pop] += ev_oracle_full

        in_prefix = cid < 500_000
        if in_prefix:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            ev_oracle_pref = float(rowp[valid_mask].max())
            n_pref_total[pop] += 1
            sum_oracle_pref[pop] += ev_oracle_pref

        # Optimized: build a single per-setting combined-class array
        # (suit*N_CONN + conn) with -1 for invalid (or unclassified-bot) settings,
        # then iterate ONLY over present combos and use np.maximum.reduceat
        # via argsort-grouping. For best EV per combo we just iterate present
        # combos, which is typically 5-15 out of 35.
        combined = (suit_classes.astype(np.int16) * N_CONN
                     + conn_classes.astype(np.int16))
        combined[~valid_mask] = -1
        combined[conn_classes < 0] = -1  # exclude bot-has-pair settings
        # Find present combos and best EV per combo without iterating 35x
        present_combos = np.unique(combined[combined >= 0])
        for combo in present_combos:
            s_class = int(combo // N_CONN)
            c_class = int(combo % N_CONN)
            mask = combined == combo
            best_full = float(rowf[mask].max())
            cell = cells[pop][(s_class, c_class)]
            cell["n_full"] += 1
            cell["sum_best_full"] += best_full
            cell["sum_oracle_full"] += ev_oracle_full
            regret = ev_oracle_full - best_full
            if regret > cell["worst_full"]:
                cell["worst_full"] = regret
            if in_prefix:
                best_pref = float(rowp[mask].max())
                cell["n_pref"] += 1
                cell["sum_best_pref"] += best_pref
                cell["sum_oracle_pref"] += ev_oracle_pref
                regret_p = ev_oracle_pref - best_pref
                if regret_p > cell["worst_pref"]:
                    cell["worst_pref"] = regret_p

        if (i + 1) % 5000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_hands:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # ── Reporting ──
    pop_labels = {0: "J-low NO-PAIR (high_only)", 1: "J-low PAIR (mid=pair)"}
    for pop in (0, 1):
        if pop == 0 and args.pair_only:
            continue
        if pop == 1 and args.no_pair_only:
            continue
        n_pop_full = n_full_total[pop]
        n_pop_pref = n_pop_total = n_pref_total[pop]
        if n_pop_full == 0:
            continue
        full_pop_size = full_pop_sizes.get(pop, n_pop_full)
        share = full_pop_size / n_total
        print("=" * 100)
        print(f"POPULATION: {pop_labels[pop]}  "
              f"(n_full={n_pop_full:,}, n_pref={n_pop_pref:,}, "
              f"share={share*100:.3f}% of grid)")
        print("=" * 100)

        # Build a flat list of (suit, conn, n_full, mean_regret_full, n_pref,
        # mean_regret_pref) for ranking.
        rows = []
        for s_class in SUIT_ORDER:
            for c_class in range(N_CONN):
                cell = cells[pop][(s_class, c_class)]
                if cell["n_full"] == 0:
                    continue
                mean_oracle_full = cell["sum_oracle_full"] / cell["n_full"]
                mean_best_full = cell["sum_best_full"] / cell["n_full"]
                regret_full = mean_oracle_full - mean_best_full
                if cell["n_pref"] > 0:
                    mean_oracle_pref = cell["sum_oracle_pref"] / cell["n_pref"]
                    mean_best_pref = cell["sum_best_pref"] / cell["n_pref"]
                    regret_pref = mean_oracle_pref - mean_best_pref
                else:
                    regret_pref = float('nan')
                rows.append({
                    "s": s_class,
                    "c": c_class,
                    "n_full": cell["n_full"],
                    "achievable_pct": 100 * cell["n_full"] / n_pop_full,
                    "mean_regret_full": regret_full,
                    "worst_full": cell["worst_full"],
                    "n_pref": cell["n_pref"],
                    "mean_regret_pref": regret_pref,
                    "worst_pref": cell["worst_pref"],
                })

        rows_sorted = sorted(rows, key=lambda r: r["mean_regret_full"])

        print(f"\n{'rank':>4}  {'suit':<8} {'conn':<14} {'n_full':>8} "
              f"{'reach%':>6}  {'reg_full($)':>12}  {'worst_f':>9}  "
              f"{'reg_pref($)':>12}  {'worst_p':>9}")
        print("-" * 100)
        for rank, r in enumerate(rows_sorted, 1):
            print(f"{rank:>4}. {SUIT_LABELS[r['s']]:<8} {CONN_LABELS[r['c']]:<14} "
                  f"{r['n_full']:>8,}  {r['achievable_pct']:>5.1f}%  "
                  f"${r['mean_regret_full']*EV_TO_DOL*1000:>+10.1f}  "
                  f"${r['worst_full']*EV_TO_DOL:>+7.2f}  "
                  f"${r['mean_regret_pref']*EV_TO_DOL*1000:>+10.1f}  "
                  f"${r['worst_pref']*EV_TO_DOL:>+7.2f}")

        # 5×7 matrix view (mean regret per cell, by suit row × conn col)
        print(f"\n5×7 MEAN REGRET MATRIX ($/1000h within-class regret-vs-oracle, "
              f"lower is better):")
        print(f"  {'':<8}", end="")
        for c_class in range(N_CONN):
            print(f"  {CONN_LABELS[c_class]:>13}", end="")
        print()
        for s_class in SUIT_ORDER:
            print(f"  {SUIT_LABELS[s_class]:<8}", end="")
            for c_class in range(N_CONN):
                cell = cells[pop][(s_class, c_class)]
                if cell["n_full"] == 0:
                    print(f"  {'(n=0)':>13}", end="")
                else:
                    mean_oracle = cell["sum_oracle_full"] / cell["n_full"]
                    mean_best = cell["sum_best_full"] / cell["n_full"]
                    regret = (mean_oracle - mean_best) * EV_TO_DOL * 1000
                    print(f"  {regret:>+12.1f}", end="")
            print()

        # Achievability matrix
        print(f"\n5×7 ACHIEVABILITY % (fraction of hands in this pop where the "
              f"(suit,conn) class is producible):")
        print(f"  {'':<8}", end="")
        for c_class in range(N_CONN):
            print(f"  {CONN_LABELS[c_class]:>13}", end="")
        print()
        for s_class in SUIT_ORDER:
            print(f"  {SUIT_LABELS[s_class]:<8}", end="")
            for c_class in range(N_CONN):
                cell = cells[pop][(s_class, c_class)]
                pct = 100 * cell["n_full"] / n_pop_full
                print(f"  {pct:>12.1f}%", end="")
            print()
        print()

    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
