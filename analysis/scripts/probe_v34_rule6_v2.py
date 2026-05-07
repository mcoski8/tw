"""
Session 38 — quick empirical check of v34 (Rule 6 v2) vs v33 + v28 on a trips
sample. Same 30K random trips sample as probe_v33_trips and verify_rule6_v14.
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

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
EV_TO_DOLLARS = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("loading feature_table for trips mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads", "trips_rank"])
    n_trips = ft["n_trips"].to_numpy()
    n_pairs = ft["n_pairs"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank_full = ft["trips_rank"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = float(mask_trips.mean())

    print("loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    trips_idx = np.where(mask_trips)[0]
    rng = np.random.RandomState(0)  # match other probes
    SAMPLE_N = 30000
    sample_pos = rng.choice(len(trips_idx), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = trips_idx[sample_pos]
    sample_trip_ranks = trips_rank_full[sample_canonical_ids]

    from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow  # noqa: E402
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402
    from strategy_v34_rule6_v2 import strategy_v34_rule6_v2  # noqa: E402

    print(f"\nrunning v28, v33, v34 on {SAMPLE_N:,} trips hands ...", flush=True)
    t0 = time.time()
    v28_ev = np.empty(SAMPLE_N, dtype=np.float64)
    v33_ev = np.empty(SAMPLE_N, dtype=np.float64)
    v34_ev = np.empty(SAMPLE_N, dtype=np.float64)
    oracle_ev = np.empty(SAMPLE_N, dtype=np.float64)
    n_changed_33_34 = 0
    last_log = time.time()
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        evs = np.asarray(Y[cid], dtype=np.float64)
        oracle_ev[i] = evs.max()
        s28 = int(strategy_v28_rule5_rainbow(h))
        s33 = int(strategy_v33_rule6_trips(h))
        s34 = int(strategy_v34_rule6_v2(h))
        v28_ev[i] = evs[s28]
        v33_ev[i] = evs[s33]
        v34_ev[i] = evs[s34]
        if s34 != s33:
            n_changed_33_34 += 1
        if time.time() - last_log > 5:
            rate = (i + 1) / (time.time() - t0)
            print(f"  progress {i+1:>6,}/{SAMPLE_N:,}  rate={rate:.0f}/s",
                  flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({SAMPLE_N/elapsed:.0f}/s)")

    v28_reg = (oracle_ev - v28_ev).mean()
    v33_reg = (oracle_ev - v33_ev).mean()
    v34_reg = (oracle_ev - v34_ev).mean()
    delta_v33_v28 = v28_reg - v33_reg  # v33's gain over v28
    delta_v34_v28 = v28_reg - v34_reg
    delta_v34_v33 = v33_reg - v34_reg

    def fmt_in(x): return x * EV_TO_DOLLARS * 1000
    def fmt_grid(x): return x * EV_TO_DOLLARS * 1000 * pop_share

    print("\n" + "=" * 70)
    print("RULE 6 v2 EMPIRICAL CHECK on pure-trips sample")
    print("=" * 70)
    print(f"  Hands changed v33→v34: {n_changed_33_34:>6,}/{SAMPLE_N:,}  "
          f"({100*n_changed_33_34/SAMPLE_N:.1f}%)")
    print()
    print(f"  v28 mean regret: {v28_reg:+.4f}  "
          f"(${fmt_in(v28_reg):+,.0f}/1000h within-trips, "
          f"${fmt_grid(v28_reg):+,.1f}/1000h whole-grid)")
    print(f"  v33 mean regret: {v33_reg:+.4f}  "
          f"(${fmt_in(v33_reg):+,.0f}/1000h within-trips, "
          f"${fmt_grid(v33_reg):+,.1f}/1000h whole-grid)")
    print(f"  v34 mean regret: {v34_reg:+.4f}  "
          f"(${fmt_in(v34_reg):+,.0f}/1000h within-trips, "
          f"${fmt_grid(v34_reg):+,.1f}/1000h whole-grid)")
    print()
    print(f"  v33 vs v28: {delta_v33_v28:+.4f}  "
          f"(${fmt_grid(delta_v33_v28):+,.1f}/1000h whole-grid)")
    print(f"  v34 vs v28: {delta_v34_v28:+.4f}  "
          f"(${fmt_grid(delta_v34_v28):+,.1f}/1000h whole-grid)")
    print(f"  v34 vs v33: {delta_v34_v33:+.4f}  "
          f"(${fmt_grid(delta_v34_v33):+,.1f}/1000h whole-grid)")
    print()
    print(f"  Always-A∪C oracle ceiling: $+197/1000h whole-grid (Rule 6 v14 probe)")
    print(f"  v33 captured: ${fmt_grid(delta_v33_v28):.0f}/1000h "
          f"({100*fmt_grid(delta_v33_v28)/197:.0f}%)")
    print(f"  v34 captured: ${fmt_grid(delta_v34_v28):.0f}/1000h "
          f"({100*fmt_grid(delta_v34_v28)/197:.0f}%)")

    # Per trip-rank breakdown
    print("\n" + "=" * 70)
    print("Per trip_rank: v33_$ vs v34_$ vs delta")
    print("=" * 70)
    print(f"  {'tr':>3}  {'n':>5}  {'v33_$':>9}  {'v34_$':>9}  {'Δ_$':>9}  {'changed%':>8}")
    for tr in range(2, 15):
        m = sample_trip_ranks == tr
        n_m = int(m.sum())
        if n_m == 0:
            continue
        v33_r = (oracle_ev[m] - v33_ev[m]).mean()
        v34_r = (oracle_ev[m] - v34_ev[m]).mean()
        # changed proportion within this trip rank
        ch_count = int(((v34_ev[m] != v33_ev[m]).sum()))
        gap = v33_r - v34_r  # positive = v34 better
        v33_dol = fmt_in(v33_r)
        v34_dol = fmt_in(v34_r)
        gap_dol = fmt_in(gap)
        star = "*" if abs(gap_dol) > 50 else " "
        print(f"  {RANK_CHARS[tr]:>3}  {n_m:>5,}  ${v33_dol:>+8.1f}  "
              f"${v34_dol:>+8.1f}  ${gap_dol:>+8.1f}{star} {100*ch_count/n_m:>6.1f}%")

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    if delta_v34_v33 > 0:
        ggrid = fmt_grid(delta_v34_v33)
        print(f"  v34 BEATS v33 by ${ggrid:+,.1f}/1000h whole-grid on the probe.")
        if ggrid >= 5:
            print(f"  Re-grade on full grid + prefix; if headline holds, ship v34.")
        else:
            print(f"  Gain is small (<$5/1000h). Worth re-grading but ship is borderline.")
    else:
        print(f"  v34 does NOT beat v33 on the probe. v33's boundary stands.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
