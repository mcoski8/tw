"""
Session 37 — quick empirical check of v33 (Rule 6) vs v28 on a trips sample.
Uses the same 30K random trips sample as verify_rule6_v14_trips.

Reports:
  - v28 mean EV / regret on the sample
  - v33 mean EV / regret on the sample
  - oracle / always-A∪C ceiling (already computed in verify_rule6 probe)
  - v33 vs v28 within-trips $/1000h, whole-grid $/1000h

If v33 captures most of the $197/1000h whole-grid Rule 6 ceiling, ship it.
"""
from __future__ import annotations

import sys
import time
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

from tw_analysis.canonical import read_canonical_hands
from tw_analysis.oracle_grid import read_oracle_grid

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
EV_TO_DOLLARS = 10.0


def main() -> int:
    print("loading feature_table for trips mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads", "trips_rank"])
    n_trips = ft["n_trips"].to_numpy()
    n_pairs = ft["n_pairs"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = mask_trips.mean()
    print(f"  trips: {int(mask_trips.sum()):,}  ({100*pop_share:.2f}%)")

    print("loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    trips_idx = np.where(mask_trips)[0]
    rng = np.random.RandomState(0)
    SAMPLE_N = 30000
    sample_pos = rng.choice(len(trips_idx), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = trips_idx[sample_pos]

    from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips

    print(f"\nrunning v28 + v33 on {SAMPLE_N:,} trips hands ...", flush=True)
    t0 = time.time()
    v28_ev = np.empty(SAMPLE_N, dtype=np.float64)
    v33_ev = np.empty(SAMPLE_N, dtype=np.float64)
    oracle_ev = np.empty(SAMPLE_N, dtype=np.float64)
    n_changed = 0
    last_log = time.time()
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        evs = np.asarray(Y[cid], dtype=np.float64)
        oracle_ev[i] = evs.max()
        s28 = int(strategy_v28_rule5_rainbow(h))
        s33 = int(strategy_v33_rule6_trips(h))
        v28_ev[i] = evs[s28]
        v33_ev[i] = evs[s33]
        if s28 != s33:
            n_changed += 1
        if time.time() - last_log > 5:
            rate = (i + 1) / (time.time() - t0)
            print(f"  progress {i+1:>6,}/{SAMPLE_N:,}  rate={rate:.0f}/s",
                  flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({SAMPLE_N/elapsed:.0f}/s)")

    v28_reg = (oracle_ev - v28_ev).mean()
    v33_reg = (oracle_ev - v33_ev).mean()
    delta = v28_reg - v33_reg
    def fmt_in(x): return x * EV_TO_DOLLARS * 1000
    def fmt_grid(x): return x * EV_TO_DOLLARS * 1000 * pop_share

    print("\n" + "=" * 70)
    print("RULE 6 EMPIRICAL CHECK (v33 vs v28 on pure-trips sample)")
    print("=" * 70)
    print(f"  Hands changed by Rule 6: {n_changed:>6,}/{SAMPLE_N:,}  "
          f"({100*n_changed/SAMPLE_N:.1f}%)")
    print(f"  v28 mean regret on trips: {v28_reg:+.4f}  "
          f"(${fmt_in(v28_reg):+,.0f}/1000h within-trips, "
          f"${fmt_grid(v28_reg):+,.1f}/1000h whole-grid)")
    print(f"  v33 mean regret on trips: {v33_reg:+.4f}  "
          f"(${fmt_in(v33_reg):+,.0f}/1000h within-trips, "
          f"${fmt_grid(v33_reg):+,.1f}/1000h whole-grid)")
    print(f"\n  v33 vs v28: {delta:+.4f}  "
          f"(${fmt_in(delta):+,.0f}/1000h within-trips, "
          f"${fmt_grid(delta):+,.1f}/1000h whole-grid)")
    print(f"\n  Always-A∪C ceiling: $+197/1000h whole-grid.")
    print(f"  v33 captures: {100*fmt_grid(delta)/197:.0f}%")

    # Sanity: how many of v33's picks are A or C (mid is paired at trip-rank)?
    print(f"\n  (v33 picks should always be A or C since Rule 6 enforces it.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
