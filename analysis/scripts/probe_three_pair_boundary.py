"""
Session 41 — Map the RA-vs-RB boundary for three_pair across all 286
(high_pair, middle_pair, low_pair) cells.

Background: `verify_rule_X_v33_three_pair.py` established that on the
full 114K three_pair population:
  - RA (top=singleton, mid=HIGHEST pair) lifts +$18.36/1000h whole-grid
  - RB (top=singleton, mid=MIDDLE pair) lifts +$24.94/1000h whole-grid
  - Best-per-cell mix lifts +$54.00/1000h (ceiling) — RA on some cells,
    RB on others
  - RC, RD always regress

This probe produces:
  1. The complete 286-cell table with v33, RA, RB regrets per cell.
  2. A boundary rule (e.g., "if high_pair_rank ≤ X then RA, else RB")
     that captures the most of the +$54 ceiling.
  3. Heuristic-realizable headline of the chosen boundary rule on the
     full 114K population.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_three_pair_boundary.py
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
    print("Session 41: full RA-vs-RB boundary map for three_pair")
    print("=" * 80)

    print("\n[1/4] loading three_pair mask + grid ...", flush=True)
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

    print(f"\n[2/4] walking entire {n_3p:,} three_pair population", flush=True)

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
        pos_low = sorted([j for j in range(7) if int(ranks[j]) == lpr])
        pos_singleton = next(j for j in range(7)
                             if int(ranks[j]) == singleton_rank)

        evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
        oracle_evs[i] = evs_row.max()
        v33_evs[i] = evs_row[strategy_v33_rule6_trips(h)]

        ra_setting = _setting_index_from_tmb(pos_singleton, pos_high[0],
                                             pos_high[1])
        rb_setting = _setting_index_from_tmb(pos_singleton, pos_mid[0],
                                             pos_mid[1])
        ra_evs[i] = float(evs_row[ra_setting])
        rb_evs[i] = float(evs_row[rb_setting])

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (n_3p - i - 1) / rate
            print(f"    progress {i+1:>7,}/{n_3p:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_3p/elapsed:.0f}/s)")

    v33_regret = oracle_evs - v33_evs
    ra_regret = oracle_evs - ra_evs
    rb_regret = oracle_evs - rb_evs

    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    # ============================================================
    # [3/4] All 286 cells
    # ============================================================
    cells = defaultdict(list)
    for i in range(n_3p):
        cells[(int(high_pair_ranks[i]),
               int(mid_pair_ranks[i]),
               int(low_pair_ranks[i]))].append(i)

    print(f"\n[3/4] All {len(cells)} (high, mid, low) cells with sample sizes "
          f"+ best rule per cell", flush=True)

    cell_table = []
    for (h, m, l), idxs in cells.items():
        idxs_np = np.array(idxs, dtype=np.int64)
        v33_m = v33_regret[idxs_np].mean()
        ra_m = ra_regret[idxs_np].mean()
        rb_m = rb_regret[idxs_np].mean()
        # Standard error for the RA vs RB difference
        diff = ra_regret[idxs_np] - rb_regret[idxs_np]  # > 0 means RB better
        diff_mean = diff.mean()
        diff_se = diff.std() / np.sqrt(len(idxs_np)) if len(idxs_np) > 1 else 0.0
        cell_table.append({
            "high": h, "mid": m, "low": l, "n": len(idxs),
            "v33": v33_m, "RA": ra_m, "RB": rb_m,
            "RB_minus_RA": rb_m - ra_m,
            "diff_mean_ev": diff_mean,
            "diff_se": diff_se,
        })

    df = pd.DataFrame(cell_table)
    df["best"] = np.where(df["RB_minus_RA"] < 0, "RB", "RA")

    # ============================================================
    # Find a clean boundary rule
    # ============================================================
    print("\n" + "=" * 80)
    print("BOUNDARY RULE SEARCH")
    print("=" * 80)
    print("Tested rules (all of form 'if condition then RB else RA'):")
    print()

    # Each rule is a function (high, mid, low) -> True/False (True = use RB)
    candidates = {
        "always RA": lambda h, m, l: False,
        "always RB": lambda h, m, l: True,
        "if high >= K (13)": lambda h, m, l: h >= 13,
        "if high >= Q (12)": lambda h, m, l: h >= 12,
        "if high >= J (11)": lambda h, m, l: h >= 11,
        "if high >= T (10)": lambda h, m, l: h >= 10,
        "if high >= 9": lambda h, m, l: h >= 9,
        "if high >= 8": lambda h, m, l: h >= 8,
        "if high >= 7": lambda h, m, l: h >= 7,
        "if mid >= 7": lambda h, m, l: m >= 7,
        "if mid >= 8": lambda h, m, l: m >= 8,
        "if mid >= 9": lambda h, m, l: m >= 9,
        "if mid >= T (10)": lambda h, m, l: m >= 10,
        "if low >= 5": lambda h, m, l: l >= 5,
        "if low >= 6": lambda h, m, l: l >= 6,
        "if (h+m+l) >= 24": lambda h, m, l: (h+m+l) >= 24,
        "if (h+m+l) >= 21": lambda h, m, l: (h+m+l) >= 21,
        "if h-l <= 4 (close pairs)": lambda h, m, l: (h-l) <= 4,
        "if h-l <= 6": lambda h, m, l: (h-l) <= 6,
        "if mid >= 7 AND high >= T": lambda h, m, l: (m >= 7) and (h >= 10),
        "if mid - low <= 2 (close low/mid)": lambda h, m, l: (m - l) <= 2,
        "if mid - low <= 1": lambda h, m, l: (m - l) <= 1,
        "ORACLE per-cell best (ceiling)": None,  # special-cased below
    }

    for rule_name, fn in candidates.items():
        if fn is None:
            # Oracle ceiling: per-hand best of (RA, RB)
            picked_ev = np.maximum(ra_evs, rb_evs)
        else:
            use_rb = np.array([fn(int(high_pair_ranks[i]),
                                  int(mid_pair_ranks[i]),
                                  int(low_pair_ranks[i]))
                               for i in range(n_3p)], dtype=bool)
            picked_ev = np.where(use_rb, rb_evs, ra_evs)

        regret = oracle_evs - picked_ev
        delta = v33_regret.mean() - regret.mean()
        agreement_with_oracle = float(
            (np.where(use_rb, rb_evs, ra_evs) == np.maximum(ra_evs, rb_evs)
             ).mean()) if fn is not None else 1.0
        print(f"  {rule_name:<40}  Δ vs v33: ${fmt_grid(delta):+6.2f}/1000h whole-grid  "
              f"(${fmt_in(delta):+8.1f} within-cat)"
              + (f"   per-hand ↔ oracle: {100*agreement_with_oracle:.1f}%"
                 if fn is not None else "    ★ oracle-bound ceiling"))

    # ============================================================
    # [4/4] All 286 cells printed (sorted by high desc, mid desc, low desc)
    # ============================================================
    print("\n" + "=" * 80)
    print("FULL TABLE: every (high, mid, low) cell, sorted by pair ranks")
    print("=" * 80)
    print(f"  pairs  n      v33_$     RA_$     RB_$    RB-RA_$  best  "
          f"|diff|/SE")
    df_sorted = df.sort_values(["high", "mid", "low"],
                               ascending=[False, False, False])
    for _, r in df_sorted.iterrows():
        label = f"{RANK_CHARS[int(r['high'])]}{RANK_CHARS[int(r['mid'])]}"\
                f"{RANK_CHARS[int(r['low'])]}"
        z = (abs(r["diff_mean_ev"]) / r["diff_se"]
             if r["diff_se"] > 0 else 0.0)
        print(f"  {label:<5}  {int(r['n']):>4,}  "
              f"${fmt_in(r['v33']):>+7.1f}  "
              f"${fmt_in(r['RA']):>+7.1f}  "
              f"${fmt_in(r['RB']):>+7.1f}  "
              f"${fmt_in(r['RB']-r['RA']):>+7.1f}  "
              f"{r['best']:<3}  "
              f"{z:>5.2f}")

    # ============================================================
    # Compact pair-rank summary (collapsed by high-pair only)
    # ============================================================
    print("\n" + "=" * 80)
    print("COLLAPSED-BY-HIGH-PAIR: percentage of cells where RB beats RA")
    print("=" * 80)
    print(f"  high  cells  RB_wins   pct_RB   mean_RB-RA_$")
    for h in range(14, 1, -1):
        sub = df[df["high"] == h]
        if len(sub) == 0:
            continue
        n_rb = int((sub["best"] == "RB").sum())
        diff_dollars = fmt_in(sub["RB_minus_RA"].mean())
        print(f"  {RANK_CHARS[h]:>4}  {len(sub):>5,}  {n_rb:>7}   "
              f"{100*n_rb/len(sub):>5.1f}%   ${diff_dollars:>+7.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
