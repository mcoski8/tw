"""
Session 42 — Always-X structural baseline probe for two_pair.

two_pair = exactly 2 pairs in the 7-card hand + 3 singletons.
22.3% of all hands; 1,338,480 hands in the canonical population. Already
heavily ML-engineered in v34_dt (gated `tp_*_g` features); within-cat
residual = $218/1000h whole-grid.

Setting structure for two_pair (4 pair-cards + 3 singleton-cards):

  (A) MID IS PAIRED ("no-split"):
      top = 1 of 3 singletons
      mid = both members of one of the 2 pairs (high or low)
      bot = the OTHER pair + the 2 remaining singletons (4 cards)
      → 3 (top choice) × 2 (which pair to mid) = 6 configurations.

  (B) MID IS UNPAIRED ("double-pair bot"):
      top = 1 of 3 singletons
      mid = 2 of the remaining 2 singletons (only 1 way to pick 2 of 2)
      bot = HIGH pair + LOW pair (4 cards = both pairs intact)
      → 3 (top choice) configurations.

  (C) SPLIT A PAIR (top = pair member):
      top = a high-pair-member or a low-pair-member
      Various mid/bot combinations.

CANDIDATES (mirrors the three_pair template, oracle ceiling AND
heuristic-realizable):

  TP_RA — top = HIGHEST singleton, mid = HIGH pair, bot = LOW pair + 2
          remaining singletons.
  TP_RB — top = HIGHEST singleton, mid = LOW pair,  bot = HIGH pair + 2
          remaining singletons.
  TP_RC — top = HIGHEST singleton, mid = 2 LOWER singletons,
          bot = HIGH pair + LOW pair (double-pair bot).
  TP_RD — top = a HIGH-pair member (split high pair). Oracle ceiling
          within the constraint.
  TP_RE — top = a LOW-pair member (split low pair).  Oracle ceiling
          within the constraint.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/verify_rule_X_v33_two_pair.py
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


def main() -> int:
    print("=" * 80)
    print("Session 42: Always-X structural probe for two_pair")
    print("=" * 80)

    print("\n[1/5] loading feature_table for two_pair mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    mask_2p = (n_pairs == 2) & (n_trips == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = float(mask_2p.mean())
    n_2p = int(mask_2p.sum())
    print(f"  two_pair: {n_2p:,}  ({100*pop_share:.4f}%)")

    print("\n[2/5] loading canonical hands + oracle grid (memmap) ...",
          flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    two_pair_idx = np.where(mask_2p)[0]
    print(f"\n[3/5] walking entire {n_2p:,} two_pair population (no sampling)",
          flush=True)

    # Per-hand rule-EV arrays (oracle within rule = heuristic for fully
    # determined rules; oracle for split rules with choice space)
    v33_evs = np.empty(n_2p, dtype=np.float64)
    oracle_evs = np.empty(n_2p, dtype=np.float64)

    ra_evs = np.empty(n_2p, dtype=np.float64)  # heuristic = ceiling (det.)
    rb_evs = np.empty(n_2p, dtype=np.float64)
    rc_evs = np.empty(n_2p, dtype=np.float64)
    rd_oracle_evs = np.empty(n_2p, dtype=np.float64)
    re_oracle_evs = np.empty(n_2p, dtype=np.float64)

    # Per-hand identifiers
    high_pair_ranks = np.empty(n_2p, dtype=np.int8)
    low_pair_ranks = np.empty(n_2p, dtype=np.int8)
    sing_high_ranks = np.empty(n_2p, dtype=np.int8)
    sing_mid_ranks = np.empty(n_2p, dtype=np.int8)
    sing_low_ranks = np.empty(n_2p, dtype=np.int8)

    # v33 diagnostics
    v33_top_count = defaultdict(int)  # 'highest_sing','mid_sing','low_sing','high_pair_mem','low_pair_mem'
    v33_mid_count = defaultdict(int)  # 'high_pair','low_pair','two_singletons','split'

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
        assert len(pair_ranks) == 2
        assert len(sing_ranks) == 3

        hpr, lpr = pair_ranks
        s_hi, s_mid_r, s_lo = sing_ranks

        high_pair_ranks[i] = hpr
        low_pair_ranks[i] = lpr
        sing_high_ranks[i] = s_hi
        sing_mid_ranks[i] = s_mid_r
        sing_low_ranks[i] = s_lo

        # Positions
        pos_hi_pair = sorted([j for j in range(7) if int(ranks[j]) == hpr])
        pos_lo_pair = sorted([j for j in range(7) if int(ranks[j]) == lpr])
        pos_s_hi = next(j for j in range(7) if int(ranks[j]) == s_hi)
        pos_s_mid = next(j for j in range(7) if int(ranks[j]) == s_mid_r)
        pos_s_lo = next(j for j in range(7) if int(ranks[j]) == s_lo)

        evs_row = np.asarray(Y[int(cid)], dtype=np.float64)
        oracle_evs[i] = evs_row.max()

        # v33 actual pick + diagnostics
        v33_pick = int(strategy_v33_rule6_trips(h))
        v33_evs[i] = evs_row[v33_pick]
        v33_top_idx = v33_pick // 15
        top_rank = int(ranks[v33_top_idx])
        if v33_top_idx == pos_s_hi:
            v33_top_count["highest_sing"] += 1
        elif v33_top_idx == pos_s_mid:
            v33_top_count["mid_sing"] += 1
        elif v33_top_idx == pos_s_lo:
            v33_top_count["low_sing"] += 1
        elif top_rank == hpr:
            v33_top_count["high_pair_mem"] += 1
        elif top_rank == lpr:
            v33_top_count["low_pair_mem"] += 1
        else:
            v33_top_count["other"] += 1

        feats = setting_features_from_bytes(h)
        if bool(feats.mid_is_pair[v33_pick]):
            mid_pr = int(feats.mid_pair_rank[v33_pick])
            if mid_pr == hpr:
                v33_mid_count["high_pair"] += 1
            elif mid_pr == lpr:
                v33_mid_count["low_pair"] += 1
            else:
                v33_mid_count["other_paired_mid"] += 1
        else:
            v33_mid_count["unpaired_mid"] += 1

        # Detect split (top is a pair member)
        if top_rank in (hpr, lpr):
            v33_mid_count["[top_was_split]"] += 1

        # ============================================================
        # TP_RA: top=highest singleton, mid=HIGH pair → fully determined.
        # ============================================================
        ra_setting = _setting_index_from_tmb(pos_s_hi,
                                             pos_hi_pair[0], pos_hi_pair[1])
        ra_evs[i] = float(evs_row[ra_setting])

        # TP_RB: top=highest singleton, mid=LOW pair.
        rb_setting = _setting_index_from_tmb(pos_s_hi,
                                             pos_lo_pair[0], pos_lo_pair[1])
        rb_evs[i] = float(evs_row[rb_setting])

        # TP_RC: top=highest singleton, mid=2 lower singletons (mid + low).
        rc_setting = _setting_index_from_tmb(pos_s_hi,
                                             pos_s_mid, pos_s_lo)
        rc_evs[i] = float(evs_row[rc_setting])

        # ============================================================
        # TP_RD: top = a HIGH-pair member (split high pair).
        # Oracle within constraint: enumerate (top in {hi_pair_mem_a,
        # hi_pair_mem_b}) × (mid is one of {low_pair, two_other_singletons,
        # remaining hi-pair member + 1 singleton, etc.}). For tractability
        # we enumerate over all 15 mid-combos given each top choice and
        # take the max EV.
        # ============================================================
        rd_best = -np.inf
        for top_pos in pos_hi_pair:
            # Setting indices for this top: 15 combos. evs_row[top_pos*15:
            # top_pos*15+15] gives them.
            block = evs_row[top_pos * 15:top_pos * 15 + 15]
            v = float(block.max())
            if v > rd_best:
                rd_best = v
        rd_oracle_evs[i] = rd_best

        # TP_RE: top = a LOW-pair member.
        re_best = -np.inf
        for top_pos in pos_lo_pair:
            block = evs_row[top_pos * 15:top_pos * 15 + 15]
            v = float(block.max())
            if v > re_best:
                re_best = v
        re_oracle_evs[i] = re_best

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (n_2p - i - 1) / rate
            print(f"    progress {i+1:>9,}/{n_2p:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_2p/elapsed:.0f}/s)")

    # ============================================================
    # [4/5] Top-level summary
    # ============================================================
    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    v33_regret = oracle_evs - v33_evs
    ra_regret = oracle_evs - ra_evs
    rb_regret = oracle_evs - rb_evs
    rc_regret = oracle_evs - rc_evs
    rd_regret = oracle_evs - rd_oracle_evs
    re_regret = oracle_evs - re_oracle_evs

    print("\n" + "=" * 80)
    print("BASELINES")
    print("=" * 80)
    print(f"  v33 mean regret on two_pair: ${fmt_in(v33_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(v33_regret.mean()):+,.1f}/1000h whole-grid)")
    print(f"\n  v33 top placement:")
    for k, v in sorted(v33_top_count.items(), key=lambda kv: -kv[1]):
        print(f"    top={k:<18} {v:>9,}  ({100*v/n_2p:5.1f}%)")
    print(f"\n  v33 mid composition:")
    for k, v in sorted(v33_mid_count.items(), key=lambda kv: -kv[1]):
        print(f"    mid={k:<18} {v:>9,}  ({100*v/n_2p:5.1f}%)")

    print("\n" + "=" * 80)
    print("ALWAYS-X CANDIDATES")
    print("=" * 80)

    def _row(name, regret, kind="heur"):
        delta = v33_regret.mean() - regret.mean()
        print(f"  {name:<60}  regret=${fmt_in(regret.mean()):+9,.1f}/1000h within-cat  "
              f"(${fmt_grid(regret.mean()):+8.1f}/1000h whole-grid)  "
              f"Δ vs v33: ${fmt_in(delta):+8.1f} within-cat  "
              f"(${fmt_grid(delta):+6.2f} whole-grid)  [{kind}]")

    _row("v33 (production)", v33_regret, kind="actual")
    print(f"  {'─'*150}")
    _row("TP_RA: top=hi_sing, mid=HIGH pair, bot=LO+2sing", ra_regret)
    _row("TP_RB: top=hi_sing, mid=LOW pair,  bot=HI+2sing", rb_regret)
    _row("TP_RC: top=hi_sing, mid=2 lo-sings, bot=HI+LO  ", rc_regret)
    _row("TP_RD: top=HI-pair-mem (split high) [oracle within]", rd_regret,
         kind="oracle")
    _row("TP_RE: top=LO-pair-mem (split low)  [oracle within]", re_regret,
         kind="oracle")

    # ============================================================
    # [5/5] Per-(high_pair, low_pair) breakdown — 78 cells
    # ============================================================
    print("\n" + "=" * 80)
    print("PER-(high_pair, low_pair) BREAKDOWN")
    print("=" * 80)
    print(f"  Total combinations: 78 (C(13,2)). Showing cells with n>=200.")
    print(f"  Best of {{RA, RB, RC}} per cell (deterministic-realizable only).")
    print()
    print(f"  {'pair':<8}  {'n':>7}  "
          f"{'v33$':>8}  {'RA$':>8}  {'RB$':>8}  {'RC$':>8}  best")

    cells = defaultdict(list)
    for i in range(n_2p):
        cells[(int(high_pair_ranks[i]),
               int(low_pair_ranks[i]))].append(i)

    rule_names_det = ["RA", "RB", "RC"]
    rule_regrets_det = {"RA": ra_regret, "RB": rb_regret, "RC": rc_regret}

    rule_win_count = defaultdict(int)
    rule_total_lift_grid = defaultdict(float)
    rows = []
    for (h, l), idxs in sorted(cells.items()):
        if len(idxs) < 200:
            continue
        idxs_np = np.array(idxs, dtype=np.int64)
        v33_m = v33_regret[idxs_np].mean()
        means = {r: rule_regrets_det[r][idxs_np].mean() for r in rule_names_det}
        best = min(means, key=means.get)
        rule_win_count[best] += len(idxs)
        lift = (v33_m - means[best]) * EV_TO_DOLLARS * 1000 * (
            len(idxs) / n_2p) * pop_share
        rule_total_lift_grid[best] += lift
        rows.append((h, l, len(idxs), v33_m, means["RA"], means["RB"],
                     means["RC"], best))

    for h, l, n, v33m, ram, rbm, rcm, best in rows[:30]:
        label = f"{RANK_CHARS[h]}{RANK_CHARS[l]}"
        print(f"  {label:<8}  {n:>7,}  ${fmt_in(v33m):>+7.1f}  "
              f"${fmt_in(ram):>+7.1f}  ${fmt_in(rbm):>+7.1f}  "
              f"${fmt_in(rcm):>+7.1f}  {best}")
    if len(rows) > 30:
        print(f"  ... ({len(rows) - 30} more cells; see roll-up)")

    print("\n" + "=" * 80)
    print("RULE-WINS ROLL-UP (cells with n>=200)")
    print("=" * 80)
    total_rule_hands = sum(rule_win_count.values())
    for rule in rule_names_det:
        n_won = rule_win_count[rule]
        pct = 100 * n_won / max(total_rule_hands, 1)
        lift = rule_total_lift_grid[rule]
        print(f"  {rule}: best on {n_won:>9,} hands ({pct:5.1f}%)  "
              f"cumulative whole-grid lift if chosen: ${lift:+.2f}/1000h")

    print("\n" + "=" * 80)
    print("'BEST PER CELL' MIXED STRATEGY (within {RA, RB, RC})")
    print("=" * 80)
    best_per_cell_evs = np.empty(n_2p, dtype=np.float64)
    rule_vec = {"RA": ra_evs, "RB": rb_evs, "RC": rc_evs}
    for (h, l), idxs in cells.items():
        idxs_np = np.array(idxs, dtype=np.int64)
        means = {r: (oracle_evs[idxs_np] - rule_vec[r][idxs_np]).mean()
                 for r in rule_names_det}
        best = min(means, key=means.get)
        best_per_cell_evs[idxs_np] = rule_vec[best][idxs_np]
    best_per_cell_regret = oracle_evs - best_per_cell_evs
    delta_best = v33_regret.mean() - best_per_cell_regret.mean()
    print(f"  Mean regret if always picking best-per-cell rule (det.): "
          f"${fmt_in(best_per_cell_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(best_per_cell_regret.mean()):+,.1f}/1000h whole-grid)")
    print(f"  Δ vs v33: ${fmt_in(delta_best):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(delta_best):+,.1f}/1000h whole-grid)")

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • If one of TP_RA/TP_RB/TP_RC has Δ > +$5/1000h whole-grid,")
    print("    that's the Rule 8 candidate. Mid-of-best-rule preferred.")
    print("  • Compare TP_RC (double-pair-bot) vs TP_RA — if TP_RC dominates")
    print("    on low-pair cells (high pair = 5..8), there's a depressed-pair")
    print("    'protect both pairs in bot' regime worth carving out.")
    print("  • Split-pair oracle ceilings (TP_RD/TP_RE) report HOW MUCH ev is")
    print("    available if we let the split rule fire. Heuristic capture =")
    print("    much lower; if oracle ceiling is small there's no split-pair")
    print("    rule worth engineering.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
