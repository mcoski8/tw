"""
Session 39 — Verify the v35_rule6_v3 boundary on a HUMAN-DECISION basis.

The Session 38 sweep (`probe_v34_sweep.py`) showed the v33/v34 heuristic-A
optimizer (suit_profile, rank_sum, longest_run) cannot cash a sharper
boundary — best heuristic gain across 13 thresholds was +$0.57/1000h
whole-grid. This script asks the *different* question:

  If a HUMAN follows v35_rule6_v3 and picks the BEST A-variant cell
  (oracle-best A), how does that compare to a HUMAN following v33 and
  picking the best A pick within v33's boundary?

This is the "strategy guide ceiling" — what a thoughtful player can in
principle achieve at the table by reading the guide, not what the
production heuristic-A bot achieves.

Outputs four numbers on the 30K trips probe:

  v33 oracle-bound  : pick best-A or best-C as v33's boundary dictates
  v35 oracle-bound  : pick best-A or best-C as v35's boundary dictates
  v33 heuristic     : v33's actual production pick (heuristic-A)
  v35 heuristic     : v35's actual production pick (heuristic-A; same
                      bot-DS optimizer as v33, only the boundary is sharper)

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/verify_rule6_v3_human.py
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
from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402
from strategy_v35_rule6_v3 import strategy_v35_rule6_v3, _v35_pick_c  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
SAMPLE_N = 30000
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 39: verify v35_rule6_v3 (sharper boundary) on HUMAN-DECISION basis")
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
    print(f"  pure trips: {int(mask_trips.sum()):,}  ({100*pop_share:.4f}%)")

    print("\n[2/4] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    trips_idx_full = np.where(mask_trips)[0]
    rng = np.random.RandomState(0)
    sample_pos = rng.choice(len(trips_idx_full), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = trips_idx_full[sample_pos]
    sample_trip_ranks = trips_rank_full[sample_canonical_ids]

    print(f"\n[3/4] enumerating per-hand on {SAMPLE_N:,} hands ...", flush=True)

    bestA = np.full(SAMPLE_N, np.nan, dtype=np.float64)
    bestC = np.full(SAMPLE_N, np.nan, dtype=np.float64)
    oracle_evs = np.empty(SAMPLE_N, dtype=np.float64)
    v33_heur_evs = np.empty(SAMPLE_N, dtype=np.float64)
    v35_heur_evs = np.empty(SAMPLE_N, dtype=np.float64)
    v33_pick_c = np.zeros(SAMPLE_N, dtype=np.bool_)
    v35_pick_c = np.zeros(SAMPLE_N, dtype=np.bool_)
    max_kicker_ranks = np.empty(SAMPLE_N, dtype=np.int8)

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        feats = setting_features_from_bytes(h)
        tr = int(sample_trip_ranks[i])
        ranks = (h // 4) + 2

        non_trip_mask = ranks != tr
        kickers_ranks = sorted([int(r) for r in ranks[non_trip_mask]], reverse=True)
        max_kicker_ranks[i] = kickers_ranks[0]

        evs_row = np.asarray(Y[cid], dtype=np.float64)
        oracle_evs[i] = evs_row.max()
        v33_heur_evs[i] = evs_row[int(strategy_v33_rule6_trips(h))]
        v35_heur_evs[i] = evs_row[int(strategy_v35_rule6_v3(h))]
        v33_pick_c[i] = tr > kickers_ranks[0]
        v35_pick_c[i] = _v35_pick_c(tr, kickers_ranks)

        mask_a = feats.mid_is_pair & (feats.mid_pair_rank == tr) & (feats.top_rank != tr)
        if mask_a.any():
            cand = evs_row.copy()
            cand[~mask_a] = -np.inf
            bestA[i] = cand.max()

        mask_c = feats.mid_is_pair & (feats.mid_pair_rank == tr) & (feats.top_rank == tr)
        if mask_c.any():
            cand = evs_row.copy()
            cand[~mask_c] = -np.inf
            bestC[i] = cand.max()

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
    a_avail = ~np.isnan(bestA)
    c_avail = ~np.isnan(bestC)
    both = a_avail & c_avail

    def fmt_in(x): return x * EV_TO_DOLLARS * 1000
    def fmt_grid(x): return x * EV_TO_DOLLARS * 1000 * pop_share

    # "Oracle-bound" = best-A if rule says A, best-C if rule says C.
    # Where the chosen branch is infeasible (rare), fall back to the other.
    def oracle_bound(picks_c: np.ndarray) -> np.ndarray:
        out = np.where(picks_c, bestC, bestA)
        # If chosen branch infeasible, use the other
        mask_c_chosen_but_unavail = picks_c & ~c_avail
        out[mask_c_chosen_but_unavail] = bestA[mask_c_chosen_but_unavail]
        mask_a_chosen_but_unavail = (~picks_c) & ~a_avail
        out[mask_a_chosen_but_unavail] = bestC[mask_a_chosen_but_unavail]
        return out

    v33_oracle = oracle_bound(v33_pick_c)
    v35_oracle = oracle_bound(v35_pick_c)

    print("\n" + "=" * 80)
    print("HEADLINE: v35 vs v33, oracle-bound (human ceiling) and heuristic (bot)")
    print("=" * 80)

    def report(name: str, evs: np.ndarray, baseline: np.ndarray | None = None):
        # Filter NaNs for safety
        valid = ~np.isnan(evs)
        m = evs[valid].mean()
        within = fmt_in(m)
        whole = fmt_grid(m)
        s = f"  {name:<32}  EV={m:+.4f}   ${within:+,.1f}/1000h trips   ${whole:+,.2f}/1000h whole-grid"
        if baseline is not None:
            d = m - baseline[valid].mean()
            s += f"   Δvs base ${fmt_in(d):+,.1f}/${fmt_grid(d):+,.2f}"
        print(s)

    print("\n[A] Oracle-bound (HUMAN can pick best-A or best-C within boundary):")
    report("v33 oracle-bound", v33_oracle)
    report("v35 oracle-bound", v35_oracle, baseline=v33_oracle)
    report("Pure oracle (boundary-free)", oracle_evs, baseline=v33_oracle)

    print("\n[B] Heuristic (PRODUCTION BOT picks via bot-DS optimizer):")
    report("v33 heuristic (production)", v33_heur_evs)
    report("v35 heuristic (sharper bound)", v35_heur_evs, baseline=v33_heur_evs)

    # ------------------------------------------------------------
    # Where v35 differs from v33 (cells where the boundary changed)
    # ------------------------------------------------------------
    diff = v33_pick_c != v35_pick_c
    n_diff = int(diff.sum())
    print(f"\n[C] Cells where v33 and v35 disagree on A-vs-C: "
          f"{n_diff:,}/{SAMPLE_N:,} ({100*n_diff/SAMPLE_N:.2f}%)")
    if n_diff > 0:
        print("\n  Within the disagreement subset:")
        v33_in = v33_oracle[diff]
        v35_in = v35_oracle[diff]
        v33_h = v33_heur_evs[diff]
        v35_h = v35_heur_evs[diff]
        m33o = v33_in[~np.isnan(v33_in)].mean()
        m35o = v35_in[~np.isnan(v35_in)].mean()
        m33h = v33_h.mean()
        m35h = v35_h.mean()
        # Express the gain on the WHOLE-trips sample (not just the diff subset)
        gain_oracle = (m35o - m33o) * (n_diff / SAMPLE_N)
        gain_heur = (m35h - m33h) * (n_diff / SAMPLE_N)
        print(f"  v33 oracle-bound on diff subset: ${fmt_in(m33o):+,.1f}/1000h trips")
        print(f"  v35 oracle-bound on diff subset: ${fmt_in(m35o):+,.1f}/1000h trips  "
              f"(Δ ${fmt_in(m35o - m33o):+,.1f}/1000h trips, "
              f"${fmt_grid(gain_oracle):+,.2f}/1000h whole-grid amortized)")
        print(f"  v33 heuristic   on diff subset: ${fmt_in(m33h):+,.1f}/1000h trips")
        print(f"  v35 heuristic   on diff subset: ${fmt_in(m35h):+,.1f}/1000h trips  "
              f"(Δ ${fmt_in(m35h - m33h):+,.1f}/1000h trips, "
              f"${fmt_grid(gain_heur):+,.2f}/1000h whole-grid amortized)")

    # ------------------------------------------------------------
    # Per-trip-rank breakdown of oracle-bound v35 vs v33
    # ------------------------------------------------------------
    print("\n[D] Per-trip-rank: v33 oracle-bound vs v35 oracle-bound")
    print(f"  {'trip':>4}  {'n':>6}  {'v33_$':>9}  {'v35_$':>9}  {'Δ_trips':>9}  {'Δ_grid':>8}")
    for tr in range(2, 15):
        mask = (sample_trip_ranks == tr) & both
        n_cell = int(mask.sum())
        if n_cell < 5:
            continue
        m33 = v33_oracle[mask].mean()
        m35 = v35_oracle[mask].mean()
        delta = m35 - m33
        # Grid-level contribution: delta × (n_cell/SAMPLE_N) × pop_share × scaling
        grid_contrib = delta * (n_cell / SAMPLE_N) * EV_TO_DOLLARS * 1000 * pop_share
        star = "*" if abs(delta) > 1e-6 else " "
        print(f"  {RANK_CHARS[tr]:>4}  {n_cell:>6,}  ${fmt_in(m33):>+8.1f}  "
              f"${fmt_in(m35):>+8.1f}  ${fmt_in(delta):>+8.1f}{star} ${grid_contrib:>+7.2f}")

    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print("  • The [A] block is the HUMAN-PLAY ceiling — what someone reading the")
    print("    sharper rule and choosing the best feasible A or C pick can achieve.")
    print("    If v35 oracle-bound > v33 oracle-bound, the new boundary is genuinely")
    print("    sharper and should ship in STRATEGY_GUIDE.md.")
    print("  • The [B] block is what the production bot achieves with v33's heuristic-A")
    print("    bot-DS optimizer. Session 38's sweep already showed this delta is small")
    print("    (~$0.57/1000h max) — the heuristic-A is the rate-limiting step.")
    print("  • The shipping decision: ship v35 in the strategy guide for HUMANS even")
    print("    if the runtime keeps v33 (or a future ML A-vs-C tree). Methodology rule")
    print("    Session 39 NEW: human strategy guide can be sharper than production bot.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
