"""
Session 44 — within-hand PAIRWISE bot suit×conn comparison.

Fixes the confounding artifact in drill_bot_suit_run_priority.py: that drill
averaged "best EV in class" across DIFFERENT hand populations per class
(hands achieving 4-flush-run-4 are not the same hands achieving SS-run-4),
making cross-class comparisons biased by hand-overall-EV rather than
bot-class quality.

This drill: for each hand, compute the best EV achievable in each of the
35 (suit × conn) classes, then for EACH ordered pair (A, B) where BOTH
are achievable, compute EV(best_A) - EV(best_B) on that same hand.
Average across hands where both achievable.

This eliminates the confounder. Within-hand comparison is fair because
the same hand has the same oracle ceiling, same top/mid options, etc.
The only thing varying is the bot's (suit, conn) class.

Output:
  1. Full 35×35 pairwise lift matrix (ordered: row beats col by $X/hand)
  2. Headline cells the user specifically asked about:
     - 4-flush-run-4 vs SS-run-4 (Omaha first-principles check)
     - DS-scattered vs SS-run-4 (the "DS no-conn vs SS perfect-conn" question)
     - DS-scattered vs Rainbow-run-4 (the "tipping point" example)
     - SS-run-4 vs Rainbow-run-4 (suit dominance with same connectivity)
  3. "Tipping point" analysis: rank classes by their average pairwise lift
     against all others (a more robust priority than the marginal mean
     regret reported in the original drill)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_pairwise.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_pairwise.py --sample 5000
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_pairwise.py --pair-only
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_bot_suit_run_pairwise.py --no-pair-only
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
    SUIT_PROFILE_SS,
    SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE,
    SUIT_PROFILE_FOUR_FLUSH,
)
from drill_bot_suit_run_priority import (  # noqa: E402
    compute_connectivity_classes,
    CONN_LABELS,
    SUIT_LABELS,
    SUIT_ORDER,
    N_CONN,
    N_SUIT,
)

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0

N_CLASSES = N_SUIT * N_CONN  # 35


def class_label(combo: int) -> str:
    s = combo // N_CONN
    c = combo % N_CONN
    # combo encoding uses the raw suit profile value (0..4), map to label
    return f"{SUIT_LABELS[s]} {CONN_LABELS[c]}"


def class_combo(suit_profile: int, conn_class: int) -> int:
    return suit_profile * N_CONN + conn_class


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pair-only", action="store_true")
    ap.add_argument("--no-pair-only", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("Session 44: bot suit×conn PAIRWISE drill (within-hand A vs B)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total_hands = len(ch.hands)

    print("\n[2/4] filtering to scope (J-low + cat in {0, 1}) ...", flush=True)
    t0 = time.time()
    scope_cids, scope_pop, scope_pair_rank = [], [], []
    for cid in range(n_total_hands):
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        max_r = int(ranks.max())
        if max_r > 11:
            continue
        c = int(cats[cid])
        if c == 0 and not args.pair_only:
            scope_cids.append(int(cid)); scope_pop.append(0); scope_pair_rank.append(0)
        elif c == 1 and not args.no_pair_only:
            rc = np.bincount(ranks, minlength=15)
            P = next(r for r in range(2, 15) if rc[r] == 2)
            scope_cids.append(int(cid)); scope_pop.append(1); scope_pair_rank.append(P)
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    scope_pop = np.asarray(scope_pop, dtype=np.int8)
    scope_pair_rank = np.asarray(scope_pair_rank, dtype=np.int8)
    print(f"  scope hands: {len(scope_cids):,}")
    print(f"    no-pair: {(scope_pop == 0).sum():,}")
    print(f"    pair:    {(scope_pop == 1).sum():,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        sampled = []
        for pop in (0, 1):
            mask = (scope_pop == pop)
            pop_idx = np.where(mask)[0]
            if len(pop_idx) > args.sample:
                pop_idx = rng.choice(pop_idx, size=args.sample, replace=False)
            sampled.extend(pop_idx.tolist())
        sampled = np.asarray(sorted(sampled))
        scope_cids = scope_cids[sampled]
        scope_pop = scope_pop[sampled]
        scope_pair_rank = scope_pair_rank[sampled]
        print(f"  [sample mode: capped at {args.sample}/pop; total={len(scope_cids):,}]")

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    # Per-population pairwise accumulators:
    #   sum_lift[pop, A, B] = sum over hands of (best_EV_A - best_EV_B) where both achievable
    #   n_pairs[pop, A, B] = count of hands where both achievable
    sum_lift = {0: np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64),
                 1: np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)}
    n_pairs = {0: np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64),
                1: np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)}
    n_hands_per_pop = {0: 0, 1: 0}
    n_classes_achieved_per_pop = {0: np.zeros(N_CLASSES, dtype=np.int64),
                                    1: np.zeros(N_CLASSES, dtype=np.int64)}

    print("\n[4/4] per-hand within-hand pairwise enumeration ...", flush=True)
    t0 = time.time()
    n_hands = len(scope_cids)
    for i in range(n_hands):
        cid = int(scope_cids[i])
        pop = int(scope_pop[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)

        feats = setting_features_from_bytes(h)
        suit_classes = feats.bot_suit_profile  # (105,) int8
        conn_classes = compute_connectivity_classes(h)  # (105,) int8

        if pop == 1:
            P = int(scope_pair_rank[i])
            valid_mask = feats.mid_is_pair & (feats.mid_pair_rank == P)
        else:
            valid_mask = np.ones(105, dtype=bool)

        if not valid_mask.any():
            continue

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)

        # Per-hand best EV per (suit, conn) class
        combined = (suit_classes.astype(np.int16) * N_CONN
                     + conn_classes.astype(np.int16))
        combined[~valid_mask] = -1
        combined[conn_classes < 0] = -1

        best_ev = np.full(N_CLASSES, np.nan, dtype=np.float64)
        present_combos = np.unique(combined[combined >= 0])
        for combo in present_combos:
            mask = combined == combo
            best_ev[int(combo)] = float(rowf[mask].max())

        # Pairwise: for each ordered pair (A, B) where both available,
        # accumulate EV(A) - EV(B).
        avail = ~np.isnan(best_ev)
        if avail.sum() < 2:
            continue
        # Outer-product diff matrix (NaN where either is NaN)
        diff = best_ev[:, None] - best_ev[None, :]  # (35, 35)
        both_avail = avail[:, None] & avail[None, :]
        diff_safe = np.where(both_avail, diff, 0.0)
        sum_lift[pop] += diff_safe
        n_pairs[pop] += both_avail.astype(np.int64)
        n_classes_achieved_per_pop[pop] += avail.astype(np.int64)
        n_hands_per_pop[pop] += 1

        if (i + 1) % 5000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_hands:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # ── Reporting ──
    pop_labels = {0: "J-low NO-PAIR (high_only)", 1: "J-low PAIR (mid=pair)"}
    for pop in (0, 1):
        if pop == 0 and args.pair_only: continue
        if pop == 1 and args.no_pair_only: continue
        if n_hands_per_pop[pop] == 0:
            continue
        n_pop = n_hands_per_pop[pop]
        print("=" * 100)
        print(f"POPULATION: {pop_labels[pop]}  (n_hands={n_pop:,})")
        print("=" * 100)

        # Mean pairwise lift = sum_lift / n_pairs (entry-wise)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean_lift = sum_lift[pop] / np.where(n_pairs[pop] > 0, n_pairs[pop], 1)
        mean_lift_dollars = mean_lift * EV_TO_DOL * 1000  # convert to $/1000h

        # ── Build a summary score per class: mean of mean_lift[A][:] over all
        # B classes weighted by n_pairs[A][B] (i.e. average lift of A over a
        # representative comparison). High score = A wins more / by more on
        # average against other classes.
        # We compute weighted-average-lift-per-class.
        with np.errstate(invalid="ignore", divide="ignore"):
            row_n = n_pairs[pop].sum(axis=1)
            # Total lift A vs all B's combined: sum_lift[pop, A, :]
            row_lift = sum_lift[pop].sum(axis=1)
            avg_lift_per_class = np.where(row_n > 0,
                                            row_lift / np.where(row_n > 0, row_n, 1),
                                            np.nan)
        # Achievability
        avail_pct = 100 * n_classes_achieved_per_pop[pop] / n_pop

        # Rank classes by avg_lift_per_class (high = beats other classes more)
        ranking = np.argsort(-avg_lift_per_class)  # descending
        print(f"\n── PRIORITY RANKING (within-hand pairwise lift, "
              f"averaged across all comparison classes) ──")
        print(f"{'rank':>4}  {'class':<22} {'reach%':>7}  {'avg_lift_$':>11}")
        print("-" * 55)
        for rank, combo in enumerate(ranking, 1):
            if np.isnan(avg_lift_per_class[combo]) or row_n[combo] == 0:
                continue
            print(f"{rank:>4}. {class_label(int(combo)):<22} "
                  f"{avail_pct[combo]:>6.1f}%  "
                  f"${avg_lift_per_class[combo]*EV_TO_DOL*1000:>+9.1f}")

        # ── Headline pairwise comparisons the user specifically asked about ──
        print(f"\n── HEADLINE CELL COMPARISONS (within-hand) ──")
        cells_of_interest = [
            (SUIT_PROFILE_FOUR_FLUSH, 0, SUIT_PROFILE_SS, 0,
             "4-flush run-4 vs SS run-4 (Omaha first-principles check)"),
            (SUIT_PROFILE_DS, 6, SUIT_PROFILE_SS, 0,
             "DS scattered vs SS run-4 (the user's tipping-point question)"),
            (SUIT_PROFILE_DS, 6, SUIT_PROFILE_RAINBOW, 0,
             "DS scattered vs Rainbow run-4 (Kd9h5d2h vs JcTd9h8s spirit)"),
            (SUIT_PROFILE_SS, 0, SUIT_PROFILE_RAINBOW, 0,
             "SS run-4 vs Rainbow run-4 (suit dominance, same connectivity)"),
            (SUIT_PROFILE_DS, 0, SUIT_PROFILE_DS, 6,
             "DS run-4 vs DS scattered (within-DS connectivity test)"),
            (SUIT_PROFILE_DS, 6, SUIT_PROFILE_SS, 5,
             "DS scattered vs SS run-2+strays (commonest cells)"),
            (SUIT_PROFILE_DS, 6, SUIT_PROFILE_FOUR_FLUSH, 0,
             "DS scattered vs 4-flush run-4 (does 4-flush ever beat DS?)"),
            (SUIT_PROFILE_DS, 0, SUIT_PROFILE_SS, 0,
             "DS run-4 vs SS run-4 (suit dominance, perfect connectivity)"),
            (SUIT_PROFILE_DS, 1, SUIT_PROFILE_SS, 0,
             "DS one-gap-4 vs SS run-4"),
            (SUIT_PROFILE_RAINBOW, 0, SUIT_PROFILE_FOUR_FLUSH, 0,
             "Rainbow run-4 vs 4-flush run-4 (best non-suit vs all-suit)"),
        ]
        for sa, ca, sb, cb, label in cells_of_interest:
            ia = class_combo(sa, ca); ib = class_combo(sb, cb)
            n = n_pairs[pop][ia, ib]
            if n == 0:
                print(f"  {label}: n=0 (no co-achievable hands)")
                continue
            lift = sum_lift[pop][ia, ib] / n
            print(f"  {label}:")
            print(f"    n_co-achievable = {n:,}  |  "
                  f"mean lift (A−B) = ${lift*EV_TO_DOL*1000:>+8.1f}/1000h")

        # ── Suit-dominance ladder at run-4 connectivity ──
        print(f"\n── SUIT-DOMINANCE AT RUN-4 (best connectivity, fixed) ──")
        run4_classes = [
            (SUIT_PROFILE_DS, "DS"),
            (SUIT_PROFILE_FOUR_FLUSH, "4-flush"),
            (SUIT_PROFILE_SS, "SS"),
            (SUIT_PROFILE_THREE_ONE, "3+1"),
            (SUIT_PROFILE_RAINBOW, "Rainbow"),
        ]
        print(f"  Pairwise (within-hand, run-4 vs run-4):")
        for sa, la in run4_classes:
            for sb, lb in run4_classes:
                if sa == sb: continue
                ia = class_combo(sa, 0); ib = class_combo(sb, 0)
                n = n_pairs[pop][ia, ib]
                if n == 0: continue
                lift = sum_lift[pop][ia, ib] / n
                print(f"    {la:<8} − {lb:<8}  n={n:>6,}  "
                      f"${lift*EV_TO_DOL*1000:>+8.1f}/1000h")

        # ── Connectivity ladder at DS suit (best suit, fixed) ──
        print(f"\n── CONNECTIVITY-DOMINANCE WITHIN DS ──")
        for ca in range(N_CONN):
            for cb in range(N_CONN):
                if ca == cb: continue
                ia = class_combo(SUIT_PROFILE_DS, ca); ib = class_combo(SUIT_PROFILE_DS, cb)
                n = n_pairs[pop][ia, ib]
                if n == 0: continue
                lift = sum_lift[pop][ia, ib] / n
                # Only show top candidates
                if abs(lift * EV_TO_DOL * 1000) > 100:
                    print(f"    {CONN_LABELS[ca]:<14} − {CONN_LABELS[cb]:<14}  "
                          f"n={n:>7,}  ${lift*EV_TO_DOL*1000:>+8.1f}/1000h")

        # ── Connectivity ladder at SS suit ──
        print(f"\n── CONNECTIVITY-DOMINANCE WITHIN SS ──")
        for ca in range(N_CONN):
            for cb in range(N_CONN):
                if ca == cb: continue
                ia = class_combo(SUIT_PROFILE_SS, ca); ib = class_combo(SUIT_PROFILE_SS, cb)
                n = n_pairs[pop][ia, ib]
                if n == 0: continue
                lift = sum_lift[pop][ia, ib] / n
                if abs(lift * EV_TO_DOL * 1000) > 100:
                    print(f"    {CONN_LABELS[ca]:<14} − {CONN_LABELS[cb]:<14}  "
                          f"n={n:>7,}  ${lift*EV_TO_DOL*1000:>+8.1f}/1000h")

        # ── Tipping-point analysis: DS-scattered (worst-DS) vs all SS variants ──
        print(f"\n── TIPPING POINT: DS-scattered vs all SS variants ──")
        ds_scat = class_combo(SUIT_PROFILE_DS, 6)
        for ca in range(N_CONN):
            ib = class_combo(SUIT_PROFILE_SS, ca)
            n = n_pairs[pop][ds_scat, ib]
            if n == 0: continue
            lift = sum_lift[pop][ds_scat, ib] / n
            print(f"    DS scattered − SS {CONN_LABELS[ca]:<14}  n={n:>7,}  "
                  f"${lift*EV_TO_DOL*1000:>+8.1f}/1000h  "
                  f"({'DS wins' if lift > 0 else 'SS wins'})")

        # ── Tipping-point analysis: DS-scattered vs all 4-flush + 3+1 variants ──
        print(f"\n── DS-scattered vs all other suit-class variants ──")
        for s_other, s_label in [(SUIT_PROFILE_FOUR_FLUSH, "4-flush"),
                                    (SUIT_PROFILE_THREE_ONE, "3+1"),
                                    (SUIT_PROFILE_RAINBOW, "rainbow")]:
            for ca in range(N_CONN):
                ib = class_combo(s_other, ca)
                n = n_pairs[pop][ds_scat, ib]
                if n == 0: continue
                lift = sum_lift[pop][ds_scat, ib] / n
                print(f"    DS scattered − {s_label:<8} {CONN_LABELS[ca]:<14}  "
                      f"n={n:>7,}  ${lift*EV_TO_DOL*1000:>+8.1f}/1000h  "
                      f"({'DS wins' if lift > 0 else f'{s_label} wins'})")
        print()

    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
