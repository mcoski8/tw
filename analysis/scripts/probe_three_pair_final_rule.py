"""
Session 41 — Pin down the cleanest RA-vs-RB rule for three_pair.

The boundary probe established:
  - Always RA: +$18.36/1000h whole-grid
  - Always RB: +$24.94
  - "if high ≥ T": +$34.51 (best 1-condition rule found so far)
  - Oracle per-cell ceiling: +$71.18

The collapsed-by-high-pair table shows:
  high=A: RA wins 76% of cells  ← include A in the RA bucket
  high=K: RB wins 60%
  high=Q: RB wins 91%
  high=J: RB wins 89%
  high=T: RB wins 50%  ← borderline
  high≤9: RA wins ≥86%

So the cleanest rule is likely "if high ∈ {Q, K, J, T} then RB else RA"
which excludes Aces. This probe tests that and several other variants.

Outputs:
  1. Best 1-condition and 2-condition rules ranked
  2. Final A-2 reference table grouped by high pair rank
  3. Full deterministic strategy that the user can read off

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_three_pair_final_rule.py
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
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
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 41: pin down the cleanest RA-vs-RB rule for three_pair")
    print("=" * 80)

    print("\n[1/3] loading + walking population ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    mask_3p = ((ft["n_pairs"].to_numpy() == 3)
               & (ft["n_trips"].to_numpy() == 0)
               & (ft["n_quads"].to_numpy() == 0))
    n_total = len(ft)
    pop_share = float(mask_3p.mean())
    n_3p = int(mask_3p.sum())
    print(f"  three_pair: {n_3p:,}  ({100*pop_share:.4f}%)")

    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])
    three_pair_idx = np.where(mask_3p)[0]

    v33_evs = np.empty(n_3p, dtype=np.float64)
    oracle_evs = np.empty(n_3p, dtype=np.float64)
    ra_evs = np.empty(n_3p, dtype=np.float64)
    rb_evs = np.empty(n_3p, dtype=np.float64)
    high_pair_ranks = np.empty(n_3p, dtype=np.int8)
    mid_pair_ranks = np.empty(n_3p, dtype=np.int8)
    low_pair_ranks = np.empty(n_3p, dtype=np.int8)

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(three_pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        rank_counts = np.bincount(ranks, minlength=15)
        pair_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 2],
                            reverse=True)
        singleton_rank = next(r for r in range(2, 15)
                              if rank_counts[r] == 1)
        hpr, mpr, lpr = pair_ranks
        high_pair_ranks[i] = hpr
        mid_pair_ranks[i] = mpr
        low_pair_ranks[i] = lpr

        pos_high = sorted([j for j in range(7) if int(ranks[j]) == hpr])
        pos_mid = sorted([j for j in range(7) if int(ranks[j]) == mpr])
        pos_singleton = next(j for j in range(7)
                             if int(ranks[j]) == singleton_rank)

        evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
        oracle_evs[i] = evs_row.max()
        v33_evs[i] = evs_row[strategy_v33_rule6_trips(h)]
        ra_evs[i] = float(evs_row[
            _setting_index_from_tmb(pos_singleton, pos_high[0], pos_high[1])])
        rb_evs[i] = float(evs_row[
            _setting_index_from_tmb(pos_singleton, pos_mid[0], pos_mid[1])])

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (n_3p - i - 1) / rate
            print(f"    progress {i+1:>7,}/{n_3p:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()
    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_3p/elapsed:.0f}/s)")

    v33_regret = oracle_evs - v33_evs

    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    # ============================================================
    # [2/3] Test richer set of rules
    # ============================================================
    print("\n" + "=" * 80)
    print("RULE COMPARISON")
    print("=" * 80)

    candidates = {
        "always RA": lambda h, m, l: False,
        "always RB": lambda h, m, l: True,
        "RB if high in {Q, K}": lambda h, m, l: 12 <= h <= 13,
        "RB if high in {J, Q, K}": lambda h, m, l: 11 <= h <= 13,
        "RB if high in {T, J, Q, K}": lambda h, m, l: 10 <= h <= 13,
        "RB if high in {T, J, Q, K, A}": lambda h, m, l: h >= 10,
        "RB if high in {J, Q, K, A}": lambda h, m, l: h >= 11,
        # Sharper: separate Ace handling
        "RB if high in {T,J,Q,K} OR (high=A AND low<=5)":
            lambda h, m, l: (10 <= h <= 13) or (h == 14 and l <= 5),
        "RB if high in {T,J,Q,K} OR (high=A AND low<=4)":
            lambda h, m, l: (10 <= h <= 13) or (h == 14 and l <= 4),
        "RB if high in {T,J,Q,K} OR (high=A AND low<=3)":
            lambda h, m, l: (10 <= h <= 13) or (h == 14 and l <= 3),
        "RB if high in {T,J,Q,K} OR (high=A AND low<=2)":
            lambda h, m, l: (10 <= h <= 13) or (h == 14 and l == 2),
        # Try mid-pair cuts
        "RB if high>=T AND mid>=5":
            lambda h, m, l: (h >= 10) and (m >= 5),
        "RB if high>=T AND (h-l)>=5":
            lambda h, m, l: (h >= 10) and (h - l) >= 5,
        # Sharper still — case-by-case
        "RB if high in {Q,K,J} OR (T AND mid>=5) OR (A AND low<=4)":
            lambda h, m, l: (h in (11, 12, 13))
                            or (h == 10 and m >= 5)
                            or (h == 14 and l <= 4),
        "ORACLE per-cell best (ceiling)": None,
    }

    results = []
    for rule_name, fn in candidates.items():
        if fn is None:
            picked = np.maximum(ra_evs, rb_evs)
            agree = 100.0
        else:
            use_rb = np.array([fn(int(high_pair_ranks[i]),
                                  int(mid_pair_ranks[i]),
                                  int(low_pair_ranks[i]))
                               for i in range(n_3p)], dtype=bool)
            picked = np.where(use_rb, rb_evs, ra_evs)
            best_per_hand = np.maximum(ra_evs, rb_evs)
            agree = 100.0 * (picked == best_per_hand).mean()
        regret = oracle_evs - picked
        delta = v33_regret.mean() - regret.mean()
        results.append((rule_name, delta, agree))

    print(f"  {'rule':<60}  Δ vs v33 (whole-grid)  oracle agree")
    for name, d, a in results:
        print(f"  {name:<60}  ${fmt_grid(d):+6.2f}/1000h            {a:5.1f}%")

    # ============================================================
    # [3/3] Final A-2 reference table
    # ============================================================
    print("\n" + "=" * 80)
    print("FINAL A-2 REFERENCE TABLE (collapsed across mid+low)")
    print("=" * 80)

    cells = defaultdict(list)
    for i in range(n_3p):
        cells[(int(high_pair_ranks[i]),
               int(mid_pair_ranks[i]),
               int(low_pair_ranks[i]))].append(i)

    # For each (high, low) bucket: dominant rule
    print(f"\n  Per (high pair, lowest pair) — choose RA or RB:")
    print(f"  {'high':>4}  {'low':>4}  {'cells':>5}  {'n':>5}  "
          f"{'RA wins':>8}  {'RB wins':>8}  {'recommend':>9}")
    for h in range(14, 1, -1):
        for l in range(2, h):
            sub_cells = [(hh, mm, ll)
                         for (hh, mm, ll) in cells
                         if hh == h and ll == l]
            if not sub_cells:
                continue
            ra_total_regret = 0.0
            rb_total_regret = 0.0
            cell_count = 0
            hand_count = 0
            ra_wins_cells = 0
            for c in sub_cells:
                idxs = np.array(cells[c], dtype=np.int64)
                ra_m = (oracle_evs[idxs] - ra_evs[idxs]).mean()
                rb_m = (oracle_evs[idxs] - rb_evs[idxs]).mean()
                ra_total_regret += ra_m * len(idxs)
                rb_total_regret += rb_m * len(idxs)
                hand_count += len(idxs)
                cell_count += 1
                if ra_m < rb_m:
                    ra_wins_cells += 1
            ra_avg = ra_total_regret / hand_count
            rb_avg = rb_total_regret / hand_count
            recommend = "RA" if ra_avg < rb_avg else "RB"
            print(f"  {RANK_CHARS[h]:>4}  {RANK_CHARS[l]:>4}  "
                  f"{cell_count:>5}  {hand_count:>5,}  "
                  f"{ra_wins_cells:>4}/{cell_count:<3}  "
                  f"{cell_count - ra_wins_cells:>4}/{cell_count:<3}  "
                  f"{recommend:>9}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
