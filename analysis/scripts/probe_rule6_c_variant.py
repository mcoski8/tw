"""
Session 38 — Priority A: Validate Rule 6's A-vs-C decision.

User's hypothesis: Rule 6's C variant (top = 3rd trip card when
trip_rank > max_kicker_rank) is suspect for low/mid trip ranks.

  * Putting a low trip card on top has only 1 out to pair (the unused
    "fourth" same-rank card, which the deck doesn't have because we
    already hold 3 of them — actually the top tier pulls from a 5-card
    community board, and a 7 on top wins on the board only when a 7
    appears on the board, ~1 in 8 outs).
  * Mean ev to "give up" by promoting a low trip to top is the lost
    bot contribution (suit synergy, connectivity, pair-on-board).

Current Rule 6 in v33:
  if trip_rank > max_kicker_rank → C variant (top = trip card)
  else                            → A variant (top = highest kicker)

Question this probe answers:
  Stratifying by (trip_rank, max_kicker_rank), what is the oracle EV of:
    (a) best C-variant setting (top = a trip card, mid = other 2 trips,
        bot = 4 kickers)
    (b) best A-variant setting (top = highest kicker, mid = 2 of 3
        trips, bot = 1 trip + 3 lower kickers)
    (c) v33's actual pick
  At which (trip_rank, max_kicker_rank) cells does C beat A?
  Does C dominate A only above some trip_rank threshold (e.g., > Q)?

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_rule6_c_variant.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from collections import defaultdict

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

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
SAMPLE_N = 30000
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 38: Probe Rule 6 A-vs-C variant (per trip_rank × max_kicker)")
    print("=" * 80)

    print("\n[1/4] loading feature_table for trips mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads", "trips_rank"])
    n_trips = ft["n_trips"].to_numpy()
    n_pairs = ft["n_pairs"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank_full = ft["trips_rank"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = float(mask_trips.mean())
    print(f"  pure trips: {int(mask_trips.sum()):,}  ({100*pop_share:.2f}%)")

    print("\n[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    trips_idx_full = np.where(mask_trips)[0]
    rng = np.random.RandomState(0)  # match probe_v33_trips's seed
    sample_pos = rng.choice(len(trips_idx_full), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = trips_idx_full[sample_pos]
    sample_trip_ranks = trips_rank_full[sample_canonical_ids]

    print(f"\n[3/4] enumerating A-best, C-best, oracle, v33 on {SAMPLE_N:,} hands",
          flush=True)
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

    a_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # best A-variant
    c_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # best C-variant
    oracle_evs = np.empty(SAMPLE_N, dtype=np.float64)
    v33_evs = np.empty(SAMPLE_N, dtype=np.float64)
    max_kicker_ranks = np.empty(SAMPLE_N, dtype=np.int8)

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        feats = setting_features_from_bytes(h)
        tr = int(sample_trip_ranks[i])
        ranks = (h // 4) + 2

        # max_kicker_rank: highest rank among non-trip cards
        non_trip_mask = ranks != tr
        max_kicker_ranks[i] = int(ranks[non_trip_mask].max())

        evs_row = np.asarray(Y[cid], dtype=np.float64)
        oracle_evs[i] = evs_row.max()
        v33_evs[i] = evs_row[int(strategy_v33_rule6_trips(h))]

        # A-variant: mid is paired at trip_rank AND top is NOT a trip card
        # (top_rank != tr).
        mask_a = feats.mid_is_pair & (feats.mid_pair_rank == tr) & (feats.top_rank != tr)
        if mask_a.any():
            cand = evs_row.copy()
            cand[~mask_a] = -np.inf
            a_evs[i] = cand.max()

        # C-variant: mid is paired at trip_rank AND top IS a trip card
        # (top_rank == tr).
        mask_c = feats.mid_is_pair & (feats.mid_pair_rank == tr) & (feats.top_rank == tr)
        if mask_c.any():
            cand = evs_row.copy()
            cand[~mask_c] = -np.inf
            c_evs[i] = cand.max()

        if time.time() - last_log > 5:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (SAMPLE_N - i - 1) / rate
            print(f"    progress {i+1:>6,}/{SAMPLE_N:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({SAMPLE_N/elapsed:.0f}/s)")

    # ============================================================
    # [4/4] Reports
    # ============================================================
    a_avail = ~np.isnan(a_evs)
    c_avail = ~np.isnan(c_evs)
    both = a_avail & c_avail

    def fmt_in(x): return x * EV_TO_DOLLARS * 1000
    def fmt_grid(x): return x * EV_TO_DOLLARS * 1000 * pop_share

    print("\n" + "=" * 80)
    print("AVAILABILITY")
    print("=" * 80)
    print(f"  A-variant available: {int(a_avail.sum()):,}/{SAMPLE_N:,}  "
          f"({100*a_avail.mean():.1f}%)")
    print(f"  C-variant available: {int(c_avail.sum()):,}/{SAMPLE_N:,}  "
          f"({100*c_avail.mean():.1f}%)")
    print(f"  BOTH available:      {int(both.sum()):,}/{SAMPLE_N:,}  "
          f"({100*both.mean():.1f}%)")

    print("\n" + "=" * 80)
    print("HEAD-TO-HEAD: best A-variant vs best C-variant (where both feasible)")
    print("=" * 80)
    a_only = a_evs[both]
    c_only = c_evs[both]
    or_only = oracle_evs[both]
    a_reg = (or_only - a_only).mean()
    c_reg = (or_only - c_only).mean()
    a_minus_c_ev = (a_only - c_only).mean()
    pct_c_wins = float((c_only > a_only).mean())
    print(f"  best-A regret vs oracle: ${fmt_in(a_reg):+,.1f}/1000h within-trips  "
          f"(${fmt_grid(a_reg):+,.1f}/1000h whole-grid)")
    print(f"  best-C regret vs oracle: ${fmt_in(c_reg):+,.1f}/1000h within-trips  "
          f"(${fmt_grid(c_reg):+,.1f}/1000h whole-grid)")
    print(f"  best-A − best-C mean EV: ${fmt_in(a_minus_c_ev):+,.1f}/1000h within-trips")
    print(f"  fraction of cells where C > A: {100*pct_c_wins:.1f}%")

    print("\n" + "=" * 80)
    print("PER trip_rank × max_kicker_rank: A-mean vs C-mean")
    print("=" * 80)
    print(f"  ranges: trip_rank ∈ [2..A], max_kicker ∈ [2..A]")
    print(f"  cells reported only when both A and C variants are feasible.")
    print(f"  C_pick (whole-grid $/1000h within this cell) — bigger is BETTER for C.")
    print(f"  star (*) = C beats A in mean EV in this cell.\n")
    print(f"  {'trip':>4}  {'mxK':>4}  {'n':>5}  {'A_$':>9}  {'C_$':>9}  "
          f"{'C-A_$':>9}  {'v33_$':>9}  {'oracle_$':>9}  {'C wins?':>7}")

    # Aggregate per (tr, mk) cell
    cells = defaultdict(list)
    for i in range(SAMPLE_N):
        if not both[i]:
            continue
        cells[(int(sample_trip_ranks[i]), int(max_kicker_ranks[i]))].append(i)

    summary_rows = []
    for tr in sorted({k[0] for k in cells.keys()}):
        for mk in sorted({k[1] for k in cells.keys() if k[0] == tr}):
            idxs = np.array(cells[(tr, mk)], dtype=np.int64)
            n_cell = len(idxs)
            if n_cell < 5:
                continue  # too few for stable estimate
            a_mean = a_evs[idxs].mean()
            c_mean = c_evs[idxs].mean()
            v33_mean = v33_evs[idxs].mean()
            or_mean = oracle_evs[idxs].mean()
            c_minus_a = c_mean - a_mean
            c_wins_in_cell = float((c_evs[idxs] > a_evs[idxs]).mean())
            star = "*" if c_minus_a > 0 else " "
            tr_c = RANK_CHARS[tr]
            mk_c = RANK_CHARS[mk]
            print(f"  {tr_c:>4}  {mk_c:>4}  {n_cell:>5,}  "
                  f"${fmt_in(a_mean):>+8.1f}  ${fmt_in(c_mean):>+8.1f}  "
                  f"${fmt_in(c_minus_a):>+8.1f}{star} "
                  f"${fmt_in(v33_mean):>+8.1f}  ${fmt_in(or_mean):>+8.1f}  "
                  f"{100*c_wins_in_cell:>5.1f}%")
            summary_rows.append((tr, mk, n_cell, a_mean, c_mean, c_minus_a))

    # ============================================================
    # ROLL-UPS
    # ============================================================
    print("\n" + "=" * 80)
    print("ROLL-UP: trip_rank > max_kicker_rank cells (where v33 currently picks C)")
    print("=" * 80)
    mask_c_fires = both & (sample_trip_ranks > max_kicker_ranks)
    if mask_c_fires.sum() > 0:
        a_in = a_evs[mask_c_fires]
        c_in = c_evs[mask_c_fires]
        delta = (c_in - a_in).mean()
        print(f"  n={int(mask_c_fires.sum()):,}  fires {100*mask_c_fires.mean():.1f}% of trips sample")
        print(f"  best-A EV mean: {a_in.mean():+.4f}")
        print(f"  best-C EV mean: {c_in.mean():+.4f}")
        print(f"  C − A mean EV: {delta:+.4f}  "
              f"(${fmt_in(delta):+,.1f}/1000h within-trips, "
              f"${fmt_grid(delta * mask_c_fires.mean() / both.mean() if both.mean()>0 else 0):+,.2f}/1000h whole-grid hypothetical)")
        print(f"  Positive ⇒ v33's C-when-trip>maxK is correct on average.")
        print(f"  Negative ⇒ v34 should switch this cell to A.")

    # By trip rank: aggregate over all max_kicker for that rank
    print("\n" + "=" * 80)
    print("ROLL-UP per trip_rank (over ALL max_kicker_rank where C feasible)")
    print("=" * 80)
    print(f"  {'trip':>4}  {'n':>6}  {'A_$':>9}  {'C_$':>9}  {'C-A_$':>9}  {'%C>A':>5}")
    for tr in range(2, 15):
        mask = (sample_trip_ranks == tr) & both
        n_cell = int(mask.sum())
        if n_cell < 5:
            continue
        a_mean = a_evs[mask].mean()
        c_mean = c_evs[mask].mean()
        delta = c_mean - a_mean
        pct_c = 100 * float((c_evs[mask] > a_evs[mask]).mean())
        star = "*" if delta > 0 else " "
        print(f"  {RANK_CHARS[tr]:>4}  {n_cell:>6,}  ${fmt_in(a_mean):>+8.1f}  "
              f"${fmt_in(c_mean):>+8.1f}  ${fmt_in(delta):>+8.1f}{star} {pct_c:>4.1f}%")

    print("\n" + "=" * 80)
    print("HYPOTHESIS-DRIVEN ROLL-UPS")
    print("=" * 80)
    # User hypothesis: C is dominated for trip_rank ≤ Q (12).
    for thresh in [9, 10, 11, 12, 13]:
        mask = (sample_trip_ranks <= thresh) & both
        if mask.sum() < 5:
            continue
        a_mean = a_evs[mask].mean()
        c_mean = c_evs[mask].mean()
        delta = c_mean - a_mean
        pct_c = 100 * float((c_evs[mask] > a_evs[mask]).mean())
        print(f"  trip_rank ≤ {RANK_CHARS[thresh]}: n={int(mask.sum()):,}  "
              f"A=${fmt_in(a_mean):+.1f}  C=${fmt_in(c_mean):+.1f}  "
              f"C−A=${fmt_in(delta):+.1f}  %C>A={pct_c:.1f}%")
    # And trip_rank ≥ K (13)
    for thresh in [13, 14]:
        mask = (sample_trip_ranks >= thresh) & both
        if mask.sum() < 5:
            continue
        a_mean = a_evs[mask].mean()
        c_mean = c_evs[mask].mean()
        delta = c_mean - a_mean
        pct_c = 100 * float((c_evs[mask] > a_evs[mask]).mean())
        print(f"  trip_rank ≥ {RANK_CHARS[thresh]}: n={int(mask.sum()):,}  "
              f"A=${fmt_in(a_mean):+.1f}  C=${fmt_in(c_mean):+.1f}  "
              f"C−A=${fmt_in(delta):+.1f}  %C>A={pct_c:.1f}%")

    print("\n" + "=" * 80)
    print("PROJECTED v34 IMPROVEMENT IF WE FLIP C→A FOR DOMINATED CELLS")
    print("=" * 80)
    # Cells where v33 picks C (because trip_rank > max_kicker), but A>C in
    # that cell on average. Flip those to A.
    # Approximate: assume v33's pick equals best-C in C-fire cells.
    # Compare: replace v33_ev with best-A in cells where best-A > best-C.
    fire = sample_trip_ranks > max_kicker_ranks  # v33 picks C variant
    feas = both & fire
    delta_each = a_evs - c_evs  # negative ⇒ A<C, positive ⇒ A>C
    flip_to_a = feas & (delta_each > 0)
    n_flip = int(flip_to_a.sum())
    if n_flip > 0:
        gain_each = delta_each[flip_to_a]  # positive
        # Mean gain over the *whole* trips sample (only flips contribute)
        mean_gain_trips = gain_each.sum() / SAMPLE_N
        print(f"  cells where best-A > best-C among v33-C-picks: {n_flip:,}/"
              f"{int(feas.sum()):,} ({100*n_flip/max(int(feas.sum()),1):.1f}% of C-fire feasible)")
        print(f"  mean gain over trips sample: {mean_gain_trips:+.4f}")
        print(f"  projected within-trips gain: ${fmt_in(mean_gain_trips):+,.1f}/1000h")
        print(f"  projected whole-grid gain:  ${fmt_grid(mean_gain_trips):+,.2f}/1000h")
    else:
        print(f"  No cells where flipping C→A would help. v33's C choice is optimal.")

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • If C-A is positive at high trip ranks (K, A) and negative at low/mid")
    print("    ranks, user's hypothesis is correct: simplify Rule 6 to use A unless")
    print("    trip_rank ≥ some threshold (likely ≥ K).")
    print("  • If projected v34 gain is meaningful (≥ $5/1000h whole-grid), build")
    print("    v34_rule6_v2 with the cleaner threshold.")
    print("  • If C-A is positive across all cells where v33 picks it, v33's C")
    print("    decision is optimal — no flip needed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
