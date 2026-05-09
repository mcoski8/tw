"""
Session 41 — Always-X structural baseline probe for three_pair.

three_pair = exactly 3 pairs in the 7-card hand + 1 singleton kicker.
1.9% of all hands; 114,400 in the canonical-hand population. Untouched
by gating in the v34_dt model — the largest unprobed structural category.

Population size (114K) is small enough to probe exhaustively, no sampling.

Setting structure for three_pair (always 3 pairs + 1 singleton):
  - Top = 1 card. If it's the singleton, all 3 pairs stay intact.
    If it's a pair member, one pair is split between top and somewhere.
  - Mid = 2 cards. Most natural: a paired mid (= one of the 3 pairs).
  - Bot = 4 cards. With paired mid, bot is the OTHER 2 pairs (8 distinct
    rank-suit cards arranged as 2-pair).

The structural question: which pair goes mid?

CANDIDATES TESTED (oracle ceiling AND heuristic-realizable):

  RA — top = singleton, mid = HIGHEST pair, bot = mid+low pairs (8 cards)
  RB — top = singleton, mid = MIDDLE pair, bot = high+low pairs
  RC — top = singleton, mid = LOWEST pair, bot = high+mid pairs
  RD — top = a pair member (split a pair), 'mid is paired' constraint
       on one of the OTHER 2 pairs. (i.e., put a pair card on top to
       boost top tier strength; this breaks one pair.)

Methodology rule (Session 38): report BOTH oracle ceiling AND
heuristic-realizable. For each rule, oracle ceiling = best feasible
setting in the constrained subspace; heuristic = deterministic suit-
aware bot-DS optimization within the constraint.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/verify_rule_X_v33_three_pair.py
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def _bot_suit_profile(bot_suits: list[int]) -> int:
    """Higher = better. DS=4, SS=3, rainbow=2, 3+1=1, 4-flush=0."""
    counts = [0, 0, 0, 0]
    for s in bot_suits:
        counts[s] += 1
    counts.sort(reverse=True)
    if counts[0] == 2 and counts[1] == 2:
        return 4
    if counts[0] == 2 and counts[1] == 1:
        return 3
    if counts[0] == 1:
        return 2
    if counts[0] == 3:
        return 1
    return 0


def _pick_paired_mid_setting(top_pos: int, pair_pos: tuple[int, int]) -> int:
    """When top is locked and mid is locked to a specific pair, the setting
    is fully determined (bot is the 4 leftover positions)."""
    return _setting_index_from_tmb(top_pos, pair_pos[0], pair_pos[1])


def main() -> int:
    print("=" * 80)
    print("Session 41: Always-X structural probe for three_pair")
    print("=" * 80)

    print("\n[1/5] loading feature_table for three_pair mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    mask_3p = (n_pairs == 3) & (n_trips == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = float(mask_3p.mean())
    n_3p = int(mask_3p.sum())
    print(f"  three_pair: {n_3p:,}  ({100*pop_share:.4f}%)")

    print("\n[2/5] loading canonical hands + oracle grid (memmap) ...",
          flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    three_pair_idx = np.where(mask_3p)[0]
    print(f"\n[3/5] walking entire {n_3p:,} three_pair population (no sampling)",
          flush=True)

    # Per-hand fields
    v33_evs = np.empty(n_3p, dtype=np.float64)
    oracle_evs = np.empty(n_3p, dtype=np.float64)

    # Oracle ceilings under each rule constraint
    ra_oracle_evs = np.full(n_3p, np.nan, dtype=np.float64)
    rb_oracle_evs = np.full(n_3p, np.nan, dtype=np.float64)
    rc_oracle_evs = np.full(n_3p, np.nan, dtype=np.float64)
    rd_oracle_evs = np.full(n_3p, np.nan, dtype=np.float64)

    # Heuristic deterministic picks
    ra_heur_evs = np.empty(n_3p, dtype=np.float64)
    rb_heur_evs = np.empty(n_3p, dtype=np.float64)
    rc_heur_evs = np.empty(n_3p, dtype=np.float64)

    # Per-hand identifiers
    high_pair_ranks = np.empty(n_3p, dtype=np.int8)
    mid_pair_ranks = np.empty(n_3p, dtype=np.int8)
    low_pair_ranks = np.empty(n_3p, dtype=np.int8)
    singleton_ranks = np.empty(n_3p, dtype=np.int8)

    # v33 sanity: does v33 already pick top=singleton?
    v33_top_eq_singleton = 0
    v33_mid_is_pair_count_by_which = defaultdict(int)  # 'high'/'mid'/'low'/'other'

    t0 = time.time()
    last_log = time.time()

    for i, cid in enumerate(three_pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11

        # Identify the 3 pair ranks (descending) and the singleton rank
        rank_counts = np.bincount(ranks, minlength=15)
        pair_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 2],
                            reverse=True)
        singleton_rank = next(r for r in range(2, 15)
                              if rank_counts[r] == 1)
        # Sanity (should always pass per the mask)
        assert len(pair_ranks) == 3
        assert sum(rank_counts) == 7

        hpr, mpr, lpr = pair_ranks  # high, middle, low
        high_pair_ranks[i] = hpr
        mid_pair_ranks[i] = mpr
        low_pair_ranks[i] = lpr
        singleton_ranks[i] = singleton_rank

        # Positions
        pos_high = sorted([j for j in range(7) if int(ranks[j]) == hpr])
        pos_mid = sorted([j for j in range(7) if int(ranks[j]) == mpr])
        pos_low = sorted([j for j in range(7) if int(ranks[j]) == lpr])
        pos_singleton = next(j for j in range(7)
                             if int(ranks[j]) == singleton_rank)

        evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
        oracle_evs[i] = evs_row.max()

        # v33 actual pick
        v33_pick = int(strategy_v33_rule6_trips(h))
        v33_evs[i] = evs_row[v33_pick]

        # v33 top diagnostic
        v33_top_idx = v33_pick // 15
        if int(ranks[v33_top_idx]) == singleton_rank:
            v33_top_eq_singleton += 1
        # v33 mid composition (the mid is determined by the setting decode)
        feats = setting_features_from_bytes(h)
        if bool(feats.mid_is_pair[v33_pick]):
            mid_pr = int(feats.mid_pair_rank[v33_pick])
            if mid_pr == hpr:
                v33_mid_is_pair_count_by_which["high"] += 1
            elif mid_pr == mpr:
                v33_mid_is_pair_count_by_which["mid"] += 1
            elif mid_pr == lpr:
                v33_mid_is_pair_count_by_which["low"] += 1
            else:
                v33_mid_is_pair_count_by_which["other_pair"] += 1
        else:
            v33_mid_is_pair_count_by_which["unpaired_mid"] += 1

        # ============================================================
        # Build oracle ceilings under each rule constraint.
        # Each rule constrains (top, mid, bot) — the bot is fully forced
        # given (top, mid).
        # ============================================================
        # RA: top=singleton, mid=high pair, bot=mid+low pairs.
        # Setting fully determined.
        ra_setting = _setting_index_from_tmb(pos_singleton,
                                             pos_high[0], pos_high[1])
        ra_oracle_evs[i] = float(evs_row[ra_setting])
        ra_heur_evs[i] = ra_oracle_evs[i]  # deterministic, ceiling = heur

        # RB: top=singleton, mid=middle pair, bot=high+low pairs.
        rb_setting = _setting_index_from_tmb(pos_singleton,
                                             pos_mid[0], pos_mid[1])
        rb_oracle_evs[i] = float(evs_row[rb_setting])
        rb_heur_evs[i] = rb_oracle_evs[i]

        # RC: top=singleton, mid=lowest pair, bot=high+mid pairs.
        rc_setting = _setting_index_from_tmb(pos_singleton,
                                             pos_low[0], pos_low[1])
        rc_oracle_evs[i] = float(evs_row[rc_setting])
        rc_heur_evs[i] = rc_oracle_evs[i]

        # RD: top = a pair member (break a pair to boost top tier).
        # Constraint: top is a pair member; mid_is_pair must hold for one
        # of the OTHER 2 pairs. Enumerate the 6 (top, mid_pair_choice)
        # combinations and take the oracle-best.
        rd_best = -np.inf
        for top_pair_ranks, top_pos_list, other_pairs in [
            (hpr, pos_high, [(mpr, pos_mid), (lpr, pos_low)]),
            (mpr, pos_mid, [(hpr, pos_high), (lpr, pos_low)]),
            (lpr, pos_low, [(hpr, pos_high), (mpr, pos_mid)]),
        ]:
            for top_pos in top_pos_list:
                for (other_rank, other_pos_list) in other_pairs:
                    s_idx = _setting_index_from_tmb(top_pos,
                                                    other_pos_list[0],
                                                    other_pos_list[1])
                    ev = float(evs_row[s_idx])
                    if ev > rd_best:
                        rd_best = ev
        rd_oracle_evs[i] = rd_best

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (n_3p - i - 1) / rate
            print(f"    progress {i+1:>7,}/{n_3p:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_3p/elapsed:.0f}/s)")

    # ============================================================
    # [4/5] Top-level summary
    # ============================================================
    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    v33_regret = oracle_evs - v33_evs
    ra_regret = oracle_evs - ra_oracle_evs
    rb_regret = oracle_evs - rb_oracle_evs
    rc_regret = oracle_evs - rc_oracle_evs
    rd_regret = oracle_evs - rd_oracle_evs

    print("\n" + "=" * 80)
    print("BASELINES")
    print("=" * 80)
    print(f"  v33 mean regret on three_pair: ${fmt_in(v33_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(v33_regret.mean()):+,.1f}/1000h whole-grid)")
    print(f"\n  v33 picks top = singleton: {v33_top_eq_singleton:,}/{n_3p:,}  "
          f"({100*v33_top_eq_singleton/n_3p:.1f}%)")
    print(f"  v33 mid composition:")
    for k, v in sorted(v33_mid_is_pair_count_by_which.items()):
        print(f"    mid={k:<14} {v:>7,}  ({100*v/n_3p:5.1f}%)")

    print("\n" + "=" * 80)
    print("ALWAYS-X CANDIDATES (oracle = ceiling = heuristic, since each")
    print("rule fully determines the setting given pair structure)")
    print("=" * 80)

    def _row(name, regret):
        delta = v33_regret.mean() - regret.mean()
        print(f"  {name:<40}  regret=${fmt_in(regret.mean()):+8,.1f}/1000h within-cat  "
              f"(${fmt_grid(regret.mean()):+6.1f}/1000h whole-grid)  "
              f"Δ vs v33: ${fmt_in(delta):+7.1f} within-cat  "
              f"(${fmt_grid(delta):+5.2f} whole-grid)")

    _row("v33 (production)", v33_regret)
    print(f"  {'─'*128}")
    _row("RA: top=sing, mid=HIGH pair", ra_regret)
    _row("RB: top=sing, mid=MID pair", rb_regret)
    _row("RC: top=sing, mid=LOW pair", rc_regret)
    _row("RD: top=pair-member, mid=other pair (oracle within RD)", rd_regret)

    # ============================================================
    # [5/5] Per-(high, mid, low) breakdown
    # ============================================================
    print("\n" + "=" * 80)
    print("PER-(high, mid, low) PAIR BREAKDOWN — sample size, best rule")
    print("=" * 80)
    print(f"  Total combinations: 286 (C(13,3)). Showing only cells with n>=20.")
    print(f"  Mean over each cell of the BEST rule's mean regret.")
    print()
    print(f"  {'pairs':<12}  {'n':>5}  "
          f"{'v33_$':>8}  {'RA_$':>8}  {'RB_$':>8}  "
          f"{'RC_$':>8}  {'RD_$':>8}  best")

    # Aggregate per (h, m, l) — collapse over singleton
    cells = defaultdict(list)
    for i in range(n_3p):
        cells[(int(high_pair_ranks[i]),
               int(mid_pair_ranks[i]),
               int(low_pair_ranks[i]))].append(i)

    rule_names = ["RA", "RB", "RC", "RD"]
    rule_regrets_arr = {"RA": ra_regret, "RB": rb_regret,
                         "RC": rc_regret, "RD": rd_regret}

    # Track which rule wins per cell
    rule_win_count = defaultdict(int)
    rule_total_lift_grid = defaultdict(float)

    rows = []
    for (h, m, l), idxs in sorted(cells.items()):
        if len(idxs) < 20:
            continue
        idxs_np = np.array(idxs, dtype=np.int64)
        v33_m = v33_regret[idxs_np].mean()
        ra_m = ra_regret[idxs_np].mean()
        rb_m = rb_regret[idxs_np].mean()
        rc_m = rc_regret[idxs_np].mean()
        rd_m = rd_regret[idxs_np].mean()
        rule_means = {"RA": ra_m, "RB": rb_m, "RC": rc_m, "RD": rd_m}
        best = min(rule_means, key=rule_means.get)
        rule_win_count[best] += len(idxs)
        # Lift in whole-grid $
        lift = (v33_m - rule_means[best]) * EV_TO_DOLLARS * 1000 * (
            len(idxs) / n_3p) * pop_share
        rule_total_lift_grid[best] += lift
        rows.append((h, m, l, len(idxs), v33_m, ra_m, rb_m, rc_m, rd_m, best))

    # Print rows for select rank combos (low/mid/high spread)
    for h, m, l, n, v33m, ram, rbm, rcm, rdm, best in rows[:40]:
        label = f"{RANK_CHARS[h]}{RANK_CHARS[m]}{RANK_CHARS[l]}"
        print(f"  {label:<12}  {n:>5,}  ${fmt_in(v33m):>+7.1f}  "
              f"${fmt_in(ram):>+7.1f}  ${fmt_in(rbm):>+7.1f}  "
              f"${fmt_in(rcm):>+7.1f}  ${fmt_in(rdm):>+7.1f}  {best}")
    if len(rows) > 40:
        print(f"  ... ({len(rows) - 40} more cells; see roll-up below)")

    print("\n" + "=" * 80)
    print("RULE-WINS ROLL-UP (across all cells with n≥20)")
    print("=" * 80)
    total_rule_hands = sum(rule_win_count.values())
    for rule in rule_names:
        n_won = rule_win_count[rule]
        pct = 100 * n_won / max(total_rule_hands, 1)
        lift = rule_total_lift_grid[rule]
        print(f"  {rule}: best on {n_won:>6,} hands ({pct:5.1f}%)  "
              f"cumulative whole-grid lift if chosen: ${lift:+.2f}/1000h")

    # ============================================================
    # Mixed strategy: choose best rule per (h, m, l) cell
    # ============================================================
    print("\n" + "=" * 80)
    print("'BEST PER CELL' MIXED STRATEGY (oracle-bound rule selection)")
    print("=" * 80)
    # If we could perfectly pick the best rule per cell:
    best_per_cell_evs = np.empty(n_3p, dtype=np.float64)
    rule_vec = {"RA": ra_oracle_evs, "RB": rb_oracle_evs,
                 "RC": rc_oracle_evs, "RD": rd_oracle_evs}
    for (h, m, l), idxs in cells.items():
        idxs_np = np.array(idxs, dtype=np.int64)
        # For tiny cells (<20), default to RC (most common winner — to be
        # confirmed; we'll re-pass below)
        rule_means = {r: (oracle_evs[idxs_np] - rule_vec[r][idxs_np]).mean()
                       for r in rule_names}
        best = min(rule_means, key=rule_means.get)
        best_per_cell_evs[idxs_np] = rule_vec[best][idxs_np]
    best_per_cell_regret = oracle_evs - best_per_cell_evs
    delta_best = v33_regret.mean() - best_per_cell_regret.mean()
    print(f"  Mean regret if always picking best-per-cell rule: "
          f"${fmt_in(best_per_cell_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(best_per_cell_regret.mean()):+,.1f}/1000h whole-grid)")
    print(f"  Δ vs v33: ${fmt_in(delta_best):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(delta_best):+,.1f}/1000h whole-grid)")

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • If one of RA/RB/RC has Δ > +$5/1000h whole-grid, that's Rule 7.")
    print("  • If RD wins on high-pair cells (e.g., AA-anything), there's a")
    print("    'split-a-pair-for-Ace-on-top' exception worth carving out.")
    print("  • If the per-cell mixed strategy lift > overall best single rule")
    print("    by >$5/1000h, the rule has rank-dependent structure and should")
    print("    ship as a small lookup table (like Rule 6 v35's per-rank table).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
