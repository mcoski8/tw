"""
Session 42 — Map the RA-vs-RB-vs-RC boundary for two_pair across all 78
(high_pair, low_pair) cells.

Background: `verify_rule_X_v33_two_pair.py` (full 1.34M two_pair walk):
  - v33 baseline: $3,371/1000h within-cat ($751/1000h whole-grid)
  - TP_RA (mid=HIGH pair):   regret $3,765 →  Δ -$87.71 whole-grid
  - TP_RB (mid=LOW pair):    regret $3,063 →  Δ +$68.46 whole-grid ★
  - TP_RC (double-pair bot): regret $12,294 → Δ -$1,988  whole-grid
  - Best-per-cell mix (oracle): $2,365 → Δ +$223.9 whole-grid
  - Per-cell winners: RA on 43.6% of hands, RB on 47.4%, RC on 9%
  - Pattern from cell printout: RC wins on (high≤5, low≤3) territory;
    RB wins on (high≥T) territory; RA wins in 6..9 high range.

This probe produces:
  1. Complete 78-cell table with v33, RA, RB, RC regrets per cell.
  2. Best-of-{RA,RB,RC} per cell (ceiling reference).
  3. Boundary rule search — single-condition + 2-condition rules of the
     form "if X then RB elif Y then RC else RA" (and permutations).
  4. Heuristic-realizable headline of the chosen boundary rule.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_two_pair_boundary.py
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
    print("Session 42: full RA-vs-RB-vs-RC boundary map for two_pair")
    print("=" * 80)

    print("\n[1/4] loading two_pair mask + grid ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    mask_2p = ((ft["n_pairs"].to_numpy() == 2)
               & (ft["n_trips"].to_numpy() == 0)
               & (ft["n_quads"].to_numpy() == 0))
    n_total = len(ft)
    pop_share = float(mask_2p.mean())
    n_2p = int(mask_2p.sum())
    print(f"  two_pair: {n_2p:,}  ({100*pop_share:.4f}%)")

    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])
    two_pair_idx = np.where(mask_2p)[0]

    print(f"\n[2/4] walking entire {n_2p:,} two_pair population", flush=True)

    v33_evs = np.empty(n_2p, dtype=np.float64)
    oracle_evs = np.empty(n_2p, dtype=np.float64)
    ra_evs = np.empty(n_2p, dtype=np.float64)
    rb_evs = np.empty(n_2p, dtype=np.float64)
    rc_evs = np.empty(n_2p, dtype=np.float64)

    high_pair_ranks = np.empty(n_2p, dtype=np.int8)
    low_pair_ranks = np.empty(n_2p, dtype=np.int8)
    sing_high_ranks = np.empty(n_2p, dtype=np.int8)
    sing_low_ranks = np.empty(n_2p, dtype=np.int8)

    t0 = time.time()
    last_log = time.time()

    for i, cid in enumerate(two_pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        rank_counts = np.bincount(ranks, minlength=15)
        pair_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 2],
                            reverse=True)
        sing_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 1],
                            reverse=True)
        hpr, lpr = pair_ranks
        s_hi, s_mid_r, s_lo = sing_ranks

        high_pair_ranks[i] = hpr
        low_pair_ranks[i] = lpr
        sing_high_ranks[i] = s_hi
        sing_low_ranks[i] = s_lo

        pos_hi_pair = sorted([j for j in range(7) if int(ranks[j]) == hpr])
        pos_lo_pair = sorted([j for j in range(7) if int(ranks[j]) == lpr])
        pos_s_hi = next(j for j in range(7) if int(ranks[j]) == s_hi)
        pos_s_mid = next(j for j in range(7) if int(ranks[j]) == s_mid_r)
        pos_s_lo = next(j for j in range(7) if int(ranks[j]) == s_lo)

        evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
        oracle_evs[i] = evs_row.max()
        v33_evs[i] = evs_row[strategy_v33_rule6_trips(h)]

        ra_setting = _setting_index_from_tmb(pos_s_hi,
                                             pos_hi_pair[0], pos_hi_pair[1])
        rb_setting = _setting_index_from_tmb(pos_s_hi,
                                             pos_lo_pair[0], pos_lo_pair[1])
        rc_setting = _setting_index_from_tmb(pos_s_hi, pos_s_mid, pos_s_lo)

        ra_evs[i] = float(evs_row[ra_setting])
        rb_evs[i] = float(evs_row[rb_setting])
        rc_evs[i] = float(evs_row[rc_setting])

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (n_2p - i - 1) / rate
            print(f"    progress {i+1:>9,}/{n_2p:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_2p/elapsed:.0f}/s)")

    v33_regret = oracle_evs - v33_evs
    ra_regret = oracle_evs - ra_evs
    rb_regret = oracle_evs - rb_evs
    rc_regret = oracle_evs - rc_evs

    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    # ============================================================
    # [3/4] All 78 cells
    # ============================================================
    cells = defaultdict(list)
    for i in range(n_2p):
        cells[(int(high_pair_ranks[i]), int(low_pair_ranks[i]))].append(i)

    print(f"\n[3/4] All {len(cells)} (high, low) cells with sample sizes "
          f"+ best rule per cell", flush=True)

    cell_table = []
    for (h, l), idxs in cells.items():
        idxs_np = np.array(idxs, dtype=np.int64)
        v33_m = v33_regret[idxs_np].mean()
        ra_m = ra_regret[idxs_np].mean()
        rb_m = rb_regret[idxs_np].mean()
        rc_m = rc_regret[idxs_np].mean()
        means = {"RA": ra_m, "RB": rb_m, "RC": rc_m}
        best = min(means, key=means.get)
        cell_table.append({
            "high": h, "low": l, "n": len(idxs),
            "v33": v33_m, "RA": ra_m, "RB": rb_m, "RC": rc_m,
            "best": best,
        })

    df = pd.DataFrame(cell_table)

    # ============================================================
    # Find a clean boundary rule
    # ============================================================
    print("\n" + "=" * 80)
    print("BOUNDARY RULE SEARCH")
    print("=" * 80)

    # Each rule is a function (high, low) -> 'RA' | 'RB' | 'RC'
    candidates = {
        "always RA": lambda h, l: "RA",
        "always RB": lambda h, l: "RB",
        "always RC": lambda h, l: "RC",
        "RB if high >= K else RA":
            lambda h, l: "RB" if h >= 13 else "RA",
        "RB if high >= Q else RA":
            lambda h, l: "RB" if h >= 12 else "RA",
        "RB if high >= J else RA":
            lambda h, l: "RB" if h >= 11 else "RA",
        "RB if high >= T else RA":
            lambda h, l: "RB" if h >= 10 else "RA",
        "RB if high >= 9 else RA":
            lambda h, l: "RB" if h >= 9 else "RA",
        "RB if high >= 8 else RA":
            lambda h, l: "RB" if h >= 8 else "RA",
        # Mirror three_pair rule shape (high broadway non-A on bot)
        "RB if T<=high<=K else RA  (three_pair-style)":
            lambda h, l: "RB" if 10 <= h <= 13 else "RA",
        # Add A handling: maybe AA stays in mid
        "RB if high>=T AND high!=A else RA":
            lambda h, l: "RB" if (h >= 10 and h < 14) else "RA",
        # 3-way with RC tail
        "RC if high<=4 elif high>=T then RB else RA":
            lambda h, l: ("RC" if h <= 4 else
                          ("RB" if h >= 10 else "RA")),
        "RC if high<=5 elif high>=T then RB else RA":
            lambda h, l: ("RC" if h <= 5 else
                          ("RB" if h >= 10 else "RA")),
        "RC if high<=4 elif high>=T (excl A) then RB else RA":
            lambda h, l: ("RC" if h <= 4 else
                          ("RB" if 10 <= h < 14 else "RA")),
        "RC if (high<=5 AND low<=3) elif high>=T then RB else RA":
            lambda h, l: ("RC" if (h <= 5 and l <= 3) else
                          ("RB" if h >= 10 else "RA")),
        "RC if (high+low)<=7 elif high>=T then RB else RA":
            lambda h, l: ("RC" if (h + l) <= 7 else
                          ("RB" if h >= 10 else "RA")),
        "RC if (high+low)<=8 elif high>=T then RB else RA":
            lambda h, l: ("RC" if (h + l) <= 8 else
                          ("RB" if h >= 10 else "RA")),
        # Sanity / simple options
        "RB if low<=5 else RA":
            lambda h, l: "RB" if l <= 5 else "RA",
        "RA if high+low>=15 else RB":
            lambda h, l: "RA" if (h + l) >= 15 else "RB",
        "ORACLE per-cell best (ceiling)": None,
    }

    for rule_name, fn in candidates.items():
        if fn is None:
            picked_ev = np.maximum.reduce([ra_evs, rb_evs, rc_evs])
        else:
            choice = np.empty(n_2p, dtype="<U2")
            for i in range(n_2p):
                choice[i] = fn(int(high_pair_ranks[i]),
                                int(low_pair_ranks[i]))
            picked_ev = np.where(choice == "RA", ra_evs,
                                 np.where(choice == "RB", rb_evs, rc_evs))

        regret = oracle_evs - picked_ev
        delta = v33_regret.mean() - regret.mean()
        marker = "★ ceiling" if fn is None else ""
        print(f"  {rule_name:<60}  Δ vs v33: ${fmt_grid(delta):+7.2f}/1000h "
              f"whole-grid  (${fmt_in(delta):+9.1f} within-cat)   {marker}")

    # ============================================================
    # [4/4] Full 78-cell table sorted by high desc, low desc
    # ============================================================
    print("\n" + "=" * 80)
    print("FULL TABLE: every (high, low) cell, sorted by pair ranks")
    print("=" * 80)
    print(f"  pair    n        v33$       RA$       RB$       RC$    best")
    df_sorted = df.sort_values(["high", "low"], ascending=[False, False])
    for _, r in df_sorted.iterrows():
        label = f"{RANK_CHARS[int(r['high'])]}{RANK_CHARS[int(r['low'])]}"
        print(f"  {label:<5}  {int(r['n']):>7,}  "
              f"${fmt_in(r['v33']):>+8.1f}  "
              f"${fmt_in(r['RA']):>+8.1f}  "
              f"${fmt_in(r['RB']):>+8.1f}  "
              f"${fmt_in(r['RC']):>+8.1f}  "
              f"{r['best']:<3}")

    # ============================================================
    # Compact pair-rank summary (collapsed by high-pair only)
    # ============================================================
    print("\n" + "=" * 80)
    print("COLLAPSED-BY-HIGH-PAIR: best rule frequency + mean lift")
    print("=" * 80)
    print(f"  high  cells  RA_wins  RB_wins  RC_wins   sum_n        v33$_mean    best$_mean")
    for h in range(14, 1, -1):
        sub = df[df["high"] == h]
        if len(sub) == 0:
            continue
        ra_w = int((sub["best"] == "RA").sum())
        rb_w = int((sub["best"] == "RB").sum())
        rc_w = int((sub["best"] == "RC").sum())
        n = int(sub["n"].sum())
        v33_avg = (sub["v33"] * sub["n"]).sum() / n
        # Best-per-cell weighted mean
        best_means = sub.apply(lambda row: min(row["RA"], row["RB"],
                                                row["RC"]) * row["n"], axis=1)
        best_avg = best_means.sum() / n
        print(f"  {RANK_CHARS[h]:>4}  {len(sub):>5,}  {ra_w:>7}  {rb_w:>7}  "
              f"{rc_w:>7}  {n:>9,}  ${fmt_in(v33_avg):>+10.1f}  "
              f"${fmt_in(best_avg):>+10.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
