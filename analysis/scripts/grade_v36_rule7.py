#!/usr/bin/env python3
"""Grade v36 (v33 + Rule 7 high_only same-suit-mid heuristic) head-to-head
vs v33 on the full grid AND the prefix grid.

Drill probe (`probe_high_only_suited_mid_drill.py`) on 30K random
high_only hands: H1 (highest rank-sum same-suit mid) regressed
$-5.88/1000h whole-grid vs v33. This grader confirms (or contradicts) at
full-grid scale.

ALSO computes the oracle-bound ceiling for "always pick best same-suit
mid" on the full 1.2M high_only population — the human ceiling for a
hypothetical Rule 7 ship in the strategy guide (analogous to v35 vs v33
on Rule 6).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v36_rule7.py --grid full
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v36_rule7.py --grid prefix
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "analysis" / "src"))
sys.path.insert(0, str(REPO / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import compare_grades, grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

GRID_FULL = REPO / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = REPO / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = REPO / "data" / "canonical_hands.bin"
FT = REPO / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", choices=["full", "prefix"], default="full")
    ap.add_argument("--skip-oracle-bound", action="store_true",
                    help="Skip the oracle-bound full-population probe")
    args = ap.parse_args()

    grid_path = GRID_FULL if args.grid == "full" else GRID_PREFIX
    print(f"loading grid {grid_path.name} ...", flush=True)
    grid = read_oracle_grid(grid_path, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"  Grid: {len(grid):,}", flush=True)

    progress_every = 2_000_000 if args.grid == "full" else 200_000

    from strategy_v33_rule6_trips import strategy_v33_rule6_trips
    from strategy_v36_rule7_high_only import strategy_v36_rule7_high_only

    print("\nGrading v33 (production) ...", flush=True)
    res_v33 = grade_strategy(strategy_v33_rule6_trips, grid, ch,
                             label="v33 (production)",
                             progress_every=progress_every)
    print(res_v33.summary(), flush=True)

    print("\nGrading v36 (v33 + Rule 7 H1) ...", flush=True)
    res_v36 = grade_strategy(strategy_v36_rule7_high_only, grid, ch,
                             label="v36 (v33 + Rule 7)",
                             progress_every=progress_every)
    print(res_v36.summary(), flush=True)

    print("\n" + "=" * 70)
    print(f"v36 vs v33 ({args.grid} grid)")
    print("=" * 70)
    print(compare_grades(res_v33, res_v36))
    delta = res_v33.mean_regret - res_v36.mean_regret
    print(f"\nv36 vs v33: {delta:+.4f}  ≈ ${delta * 10 * 1000:+,.0f}/1000h",
          flush=True)
    print("  (positive = v36 improves; negative = v36 regresses)")

    # ------------------------------------------------------------
    # Oracle-bound ceiling on the full high_only population
    # ------------------------------------------------------------
    if not args.skip_oracle_bound and args.grid == "full":
        print("\n" + "=" * 70)
        print("ORACLE-BOUND CEILING — full high_only population (1.2M hands)")
        print("=" * 70)
        print("\n[1/3] loading feature_table for high_only mask ...",
              flush=True)
        ft = pd.read_parquet(FT, columns=["n_pairs", "n_trips", "n_quads"])
        n_pairs = ft["n_pairs"].to_numpy()
        n_trips_ft = ft["n_trips"].to_numpy()
        n_quads = ft["n_quads"].to_numpy()
        mask_ho = (n_pairs == 0) & (n_trips_ft == 0) & (n_quads == 0)
        n_total = len(ft)
        pop_share = float(mask_ho.mean())
        n_ho = int(mask_ho.sum())
        print(f"  high_only: {n_ho:,}  ({100*pop_share:.4f}%)")

        Y = np.asarray(grid.evs[:n_total])
        ho_idx = np.where(mask_ho)[0]

        from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb

        print(f"\n[2/3] enumerating same-suit mids on full {n_ho:,} "
              f"high_only hands ...", flush=True)

        v33_evs_ho = np.empty(n_ho, dtype=np.float64)
        v36_evs_ho = np.empty(n_ho, dtype=np.float64)
        oracle_ceiling_evs_ho = np.full(n_ho, np.nan, dtype=np.float64)
        oracle_evs_ho = np.empty(n_ho, dtype=np.float64)

        t0 = time.time()
        last_log = time.time()
        for k, cid in enumerate(ho_idx):
            h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
            ranks = (h // 4) + 2
            suits = h & 0b11
            evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
            oracle_evs_ho[k] = evs_row.max()
            v33_evs_ho[k] = evs_row[strategy_v33_rule6_trips(h)]
            v36_evs_ho[k] = evs_row[strategy_v36_rule7_high_only(h)]

            # Oracle-bound: best same-suit mid setting
            positions_by_rank_desc = sorted(range(7),
                                            key=lambda j: -int(ranks[j]))
            top_pos = positions_by_rank_desc[0]
            rem = [j for j in range(7) if j != top_pos]
            best = -np.inf
            any_suited = False
            for ai in range(6):
                for bi in range(ai + 1, 6):
                    a = rem[ai]
                    b = rem[bi]
                    if int(suits[a]) != int(suits[b]):
                        continue
                    any_suited = True
                    s_idx = int(_setting_index_from_tmb(top_pos, a, b))
                    ev = float(evs_row[s_idx])
                    if ev > best:
                        best = ev
            if any_suited:
                oracle_ceiling_evs_ho[k] = best

            if time.time() - last_log > 8:
                rate = (k + 1) / (time.time() - t0)
                eta_s = (n_ho - k - 1) / max(rate, 1.0)
                print(f"    progress {k+1:>8,}/{n_ho:,}  rate={rate:.0f}/s  "
                      f"eta {eta_s:.0f}s", flush=True)
                last_log = time.time()

        elapsed = time.time() - t0
        print(f"  done in {elapsed:.1f}s ({n_ho/elapsed:.0f}/s)")

        v33_regret_ho = oracle_evs_ho - v33_evs_ho
        v36_regret_ho = oracle_evs_ho - v36_evs_ho
        ceiling_avail = ~np.isnan(oracle_ceiling_evs_ho)
        oracle_eff = np.where(ceiling_avail, oracle_ceiling_evs_ho, v33_evs_ho)
        oracle_eff_regret = oracle_evs_ho - oracle_eff

        def fmt_in(x):
            return x * EV_TO_DOLLARS * 1000

        def fmt_grid(x):
            return x * EV_TO_DOLLARS * 1000 * pop_share

        print(f"\n[3/3] full high_only population summary "
              f"(n={n_ho:,}; same-suit mid available on "
              f"{int(ceiling_avail.sum()):,} = "
              f"{100*ceiling_avail.mean():.1f}%):")
        print(f"  v33 regret:                 ${fmt_in(v33_regret_ho.mean()):+9,.1f}/1000h within-cat  "
              f"(${fmt_grid(v33_regret_ho.mean()):+7,.1f}/1000h whole-grid)")
        print(f"  v36 regret:                 ${fmt_in(v36_regret_ho.mean()):+9,.1f}/1000h within-cat  "
              f"(${fmt_grid(v36_regret_ho.mean()):+7,.1f}/1000h whole-grid)")
        delta_v36 = v33_regret_ho.mean() - v36_regret_ho.mean()
        print(f"  Δ v36 vs v33 (heuristic):   ${fmt_in(delta_v36):+9,.1f}/1000h within-cat  "
              f"(${fmt_grid(delta_v36):+7,.1f}/1000h whole-grid)")
        print(f"  Oracle-bound ceiling regret: ${fmt_in(oracle_eff_regret.mean()):+9,.1f}/1000h within-cat  "
              f"(${fmt_grid(oracle_eff_regret.mean()):+7,.1f}/1000h whole-grid)")
        delta_ceil = v33_regret_ho.mean() - oracle_eff_regret.mean()
        print(f"  Δ ceiling vs v33:           ${fmt_in(delta_ceil):+9,.1f}/1000h within-cat  "
              f"(${fmt_grid(delta_ceil):+7,.1f}/1000h whole-grid)")
        print(f"\n  → Heuristic Rule 7 (production form): ${fmt_grid(delta_v36):+,.1f}/1000h whole-grid lift")
        print(f"  → Oracle-bound Rule 7 (human ceiling): ${fmt_grid(delta_ceil):+,.1f}/1000h whole-grid lift")
        print(f"  → Realization gap: ${fmt_grid(delta_ceil - delta_v36):+,.1f}/1000h whole-grid")

    return 0


if __name__ == "__main__":
    sys.exit(main())
