"""
Session 41 — Priority A: always-X structural baseline probe for high_only.

high_only = no pair, no trip, no quad in the 7-card hand. ~20.4% of all
hands; $572/1000h whole-grid is the largest residual in the v34_dt model.
Two prior hand-coded rule attempts archived (-$1,745 v11 omaha-first,
-$296 v15 DS-patch); the user's note in Session 30 was: "high_only and
trips categories resisted hand-coded rules." Trips broke through with
Rule 6 in Session 37; this probe asks the same of high_only.

Production v33 routing for high_only:
  v33 → v28 → v14 → v8_hybrid → strategy_v3 → _hi_only_pick
  _hi_only_pick: top = highest singleton (always), then enumerate 15
  (mid, bot) splits scored by:
    mid_suited+connected (+6) > mid_suited (+4) > mid_connected (+2)
    bot_DS (+5), bot_run≥4 (+2), bot_n_bw≥2 (+1)
    mid_rank_sum/100 as tiebreaker

Three always-X candidates tested:

  X1 — top is highest singleton.
       (v3 already enforces this — the probe is a confirmation test.)

  X2 — top is highest AND mid is the two next-highest cards.
       The simplest possible rule: rank-down 1-2-4. No mid-suited or
       bot-DS optimization at all.

  X3 — top is highest AND mid is suited if a suited mid exists in the
       remaining 6 cards.
       Formalizes v3's mid-suited preference as a hard rule.

Each candidate's oracle ceiling is computed by restricting the 105
oracle EVs to the X-conforming subset and taking the max. Compared to:
  - v33's actual pick (production heuristic)
  - the unconstrained oracle (best of all 105)

The Session 38 methodology rule applies: report BOTH oracle ceiling AND
heuristic-realizable headline. For X2, the heuristic IS the constraint
(deterministic). For X3, the heuristic is "mid suited if available, else
v3's mid pick".

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/verify_rule_X_v33_high_only.py
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402
from tw_analysis.settings import decode_setting, Card, NUM_SETTINGS  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
SAMPLE_N = 30000


def _hand_top3_ranks_positions(h: np.ndarray) -> tuple[list[int], list[int]]:
    """Return (top3 ranks descending, top3 positions in original-hand order
    descending by rank). For high_only hands, all 7 ranks are distinct, so
    'top 3' is unambiguous (indices 0..2 of rank-sorted-desc)."""
    ranks = (h // 4) + 2
    positions_by_rank_desc = sorted(range(7), key=lambda j: -int(ranks[j]))
    top3_pos = positions_by_rank_desc[:3]
    top3_ranks = [int(ranks[p]) for p in top3_pos]
    return top3_ranks, top3_pos


def main() -> int:
    print("=" * 80)
    print("Session 41: Always-X structural probe for high_only")
    print("=" * 80)

    print("\n[1/5] loading feature_table for high_only mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    mask_ho = (n_pairs == 0) & (n_trips == 0) & (n_quads == 0)
    n_total = len(ft)
    n_ho = int(mask_ho.sum())
    pop_share = float(mask_ho.mean())
    print(f"  total canonical hands: {n_total:,}")
    print(f"  high_only: {n_ho:,}  ({100*pop_share:.4f}%)")

    print("\n[2/5] loading canonical hands + oracle grid (memmap) ...",
          flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    ho_idx_full = np.where(mask_ho)[0]
    rng = np.random.RandomState(0)
    sample_pos = rng.choice(len(ho_idx_full), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = ho_idx_full[sample_pos]

    print(f"\n[3/5] sample of {SAMPLE_N:,} high_only hands "
          f"(of {n_ho:,} total)")

    print("\n[4/5] importing v33 (production) and walking sample ...",
          flush=True)
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

    # Per-hand fields
    v33_evs = np.empty(SAMPLE_N, dtype=np.float64)
    oracle_evs = np.empty(SAMPLE_N, dtype=np.float64)
    v33_pick_idx = np.empty(SAMPLE_N, dtype=np.int32)

    # X1: top = rank-max singleton.
    x1_ceiling_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)
    v33_satisfies_x1 = np.zeros(SAMPLE_N, dtype=bool)

    # X2: top = rank-max AND mid = next two highest (deterministic).
    x2_pick_evs = np.empty(SAMPLE_N, dtype=np.float64)
    v33_satisfies_x2 = np.zeros(SAMPLE_N, dtype=bool)

    # X3: top = rank-max AND mid suited (if any suited mid exists in
    # remaining 6 cards). Heuristic: among the 15 (mid, bot) splits
    # satisfying X1, take any with mid-suited; else v33's pick.
    x3_ceiling_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)
    x3_heur_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)
    x3_avail = np.zeros(SAMPLE_N, dtype=bool)
    v33_satisfies_x3 = np.zeros(SAMPLE_N, dtype=bool)

    # Top-rank distribution of v33 picks (sanity)
    v33_top_rank_eq_max = 0

    t0 = time.time()
    last_log = time.time()

    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11

        feats = setting_features_from_bytes(h)
        evs_row = np.asarray(Y[cid], dtype=np.float64)
        oracle_evs[i] = evs_row.max()

        # v33 pick
        v33_pick = int(strategy_v33_rule6_trips(h))
        v33_pick_idx[i] = v33_pick
        v33_evs[i] = evs_row[v33_pick]

        # Top-rank-max identification — for high_only, all 7 ranks are
        # distinct so the top singleton is unique.
        top3_ranks, top3_pos = _hand_top3_ranks_positions(h)
        rank_max = top3_ranks[0]
        rank2 = top3_ranks[1]
        rank3 = top3_ranks[2]
        pos_max = top3_pos[0]
        pos2 = top3_pos[1]
        pos3 = top3_pos[2]

        # ============================================================
        # X1: top must be the rank-max card.
        # ============================================================
        # In setting features, top_rank == rank_max is the constraint.
        mask_x1 = (feats.top_rank == rank_max)
        if mask_x1.any():
            cand = evs_row.copy()
            cand[~mask_x1] = -np.inf
            x1_ceiling_evs[i] = cand.max()
        v33_satisfies_x1[i] = bool(int(feats.top_rank[v33_pick]) == rank_max)
        if v33_satisfies_x1[i]:
            v33_top_rank_eq_max += 1

        # ============================================================
        # X2: top = rank_max AND mid = {rank2, rank3}.
        # Setting index can be computed directly from positions.
        # ============================================================
        # Use positions in the original 7-card hand. Build setting index
        # via top_pos × 15 + mid_combo.
        # _MID_PAIRS enumerates (a, b) with a in 0..5, b in (a+1)..5 over
        # the remaining-6 indices after removing top.
        from strategy_v9_pair_to_bot_ds import (
            _setting_index_from_tmb,
        )  # noqa: E402
        x2_pick = int(_setting_index_from_tmb(pos_max, pos2, pos3))
        x2_pick_evs[i] = evs_row[x2_pick]
        v33_satisfies_x2[i] = (v33_pick == x2_pick)

        # ============================================================
        # X3: top = rank_max AND mid is suited (any 2 cards from remaining
        # 6 with same suit).
        # Find all (mid_a, mid_b) with mid_a, mid_b in remaining-6 of
        # same suit. Among those, take oracle-best (ceiling) and a
        # heuristic pick (highest rank-sum suited mid).
        # ============================================================
        remaining_pos = [j for j in range(7) if j != pos_max]
        suited_pairs = []
        for ai in range(6):
            for bi in range(ai + 1, 6):
                a_pos = remaining_pos[ai]
                b_pos = remaining_pos[bi]
                if int(suits[a_pos]) == int(suits[b_pos]):
                    suited_pairs.append((a_pos, b_pos))
        if suited_pairs:
            x3_avail[i] = True
            # Ceiling: max EV among suited-mid settings
            best_ev = -np.inf
            best_setting = -1
            heur_best_sum = -1
            heur_pick = -1
            for (a_pos, b_pos) in suited_pairs:
                s_idx = int(_setting_index_from_tmb(pos_max, a_pos, b_pos))
                ev = float(evs_row[s_idx])
                if ev > best_ev:
                    best_ev = ev
                    best_setting = s_idx
                # Heuristic: highest mid rank-sum among suited mids
                rsum = int(ranks[a_pos]) + int(ranks[b_pos])
                if rsum > heur_best_sum:
                    heur_best_sum = rsum
                    heur_pick = s_idx
            x3_ceiling_evs[i] = best_ev
            x3_heur_evs[i] = float(evs_row[heur_pick])
            v33_satisfies_x3[i] = (v33_pick == best_setting) or (
                int(feats.top_rank[v33_pick]) == rank_max
                and bool(feats.mid_is_pair[v33_pick]) is False  # not a pair (impossible in high_only)
                and int(suits[v33_pick // 15]) == int(suits[v33_pick // 15])  # placeholder
            )

        if time.time() - last_log > 5:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (SAMPLE_N - i - 1) / rate
            print(f"    progress {i+1:>6,}/{SAMPLE_N:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({SAMPLE_N/elapsed:.0f}/s)")

    # ============================================================
    # [5/5] Reports
    # ============================================================
    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    v33_regret = oracle_evs - v33_evs

    print("\n" + "=" * 80)
    print("BASELINES")
    print("=" * 80)
    print(f"  v33 mean regret on high_only: ${fmt_in(v33_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(v33_regret.mean()):+,.1f}/1000h whole-grid)")
    print(f"  v33 picks rank-max top: {v33_top_rank_eq_max:,}/{SAMPLE_N:,}  "
          f"({100*v33_top_rank_eq_max/SAMPLE_N:.1f}%)")

    # ============================================================
    # X1: top = rank-max
    # ============================================================
    print("\n" + "=" * 80)
    print("X1 — Always: top = highest-rank card")
    print("=" * 80)
    x1_avail = ~np.isnan(x1_ceiling_evs)
    print(f"  X1 feasible: {int(x1_avail.sum()):,}/{SAMPLE_N:,}  "
          f"({100*x1_avail.mean():.1f}%)  "
          f"(should be 100% — every hand has a unique max)")
    x1_regret = oracle_evs - x1_ceiling_evs
    print(f"  X1 ORACLE CEILING regret:  ${fmt_in(x1_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(x1_regret.mean()):+,.1f}/1000h whole-grid)")
    delta_x1 = v33_regret.mean() - x1_regret.mean()
    print(f"  Δ vs v33 (positive = improvement): ${fmt_in(delta_x1):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(delta_x1):+,.1f}/1000h whole-grid)")
    print(f"  v33 already satisfies X1 on {100*v33_satisfies_x1.mean():.1f}% of high_only hands.")

    # ============================================================
    # X2: top = rank-max AND mid = {rank-2, rank-3}
    # ============================================================
    print("\n" + "=" * 80)
    print("X2 — Always: top = rank-max, mid = next-two-highest "
          "(rank-down 1-2-4 split)")
    print("=" * 80)
    x2_regret = oracle_evs - x2_pick_evs
    print(f"  X2 deterministic pick regret: ${fmt_in(x2_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(x2_regret.mean()):+,.1f}/1000h whole-grid)")
    delta_x2 = v33_regret.mean() - x2_regret.mean()
    print(f"  Δ vs v33: ${fmt_in(delta_x2):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(delta_x2):+,.1f}/1000h whole-grid)")
    print(f"  v33 picks the X2 setting on {100*v33_satisfies_x2.mean():.1f}% of hands.")

    # ============================================================
    # X3: top = rank-max AND mid is suited (when feasible)
    # ============================================================
    print("\n" + "=" * 80)
    print("X3 — Always: top = rank-max, mid is suited (when feasible)")
    print("=" * 80)
    print(f"  X3 feasible (any suited pair in remaining 6): "
          f"{int(x3_avail.sum()):,}/{SAMPLE_N:,}  ({100*x3_avail.mean():.1f}%)")
    if x3_avail.any():
        # Effective: X3 ceiling where feasible, else v33 (no rule applies)
        x3_eff_ceiling = np.where(x3_avail, x3_ceiling_evs, v33_evs)
        x3_eff_heur = np.where(x3_avail, x3_heur_evs, v33_evs)
        x3_ceil_regret = oracle_evs - x3_eff_ceiling
        x3_heur_regret = oracle_evs - x3_eff_heur
        print(f"  X3 ORACLE CEILING regret (X3 where feasible, v33 else): "
              f"${fmt_in(x3_ceil_regret.mean()):+,.1f}/1000h within-cat  "
              f"(${fmt_grid(x3_ceil_regret.mean()):+,.1f}/1000h whole-grid)")
        delta_x3_ceil = v33_regret.mean() - x3_ceil_regret.mean()
        print(f"  Δ vs v33 (ceiling): ${fmt_in(delta_x3_ceil):+,.1f}/1000h within-cat  "
              f"(${fmt_grid(delta_x3_ceil):+,.1f}/1000h whole-grid)")
        print(f"  X3 HEURISTIC (highest-rank-sum suited mid) regret: "
              f"${fmt_in(x3_heur_regret.mean()):+,.1f}/1000h within-cat  "
              f"(${fmt_grid(x3_heur_regret.mean()):+,.1f}/1000h whole-grid)")
        delta_x3_heur = v33_regret.mean() - x3_heur_regret.mean()
        print(f"  Δ vs v33 (heuristic): ${fmt_in(delta_x3_heur):+,.1f}/1000h within-cat  "
              f"(${fmt_grid(delta_x3_heur):+,.1f}/1000h whole-grid)")

    # ============================================================
    # Stratify v33 vs X2 by hand-strength buckets (max-rank)
    # ============================================================
    print("\n" + "=" * 80)
    print("PER-MAX-RANK breakdown: where does X2 vs v33 win/lose?")
    print("=" * 80)
    print(f"  {'max_rank':>8}  {'n':>5}  {'v33_$':>8}  {'X2_$':>8}  "
          f"{'X2-v33_$':>9}")
    sample_max_rank = np.empty(SAMPLE_N, dtype=np.int8)
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        sample_max_rank[i] = int(ranks.max())
    RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
                  9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}
    for r in range(8, 15):
        m = sample_max_rank == r
        n_m = int(m.sum())
        if n_m < 30:
            continue
        v33_r = v33_regret[m].mean()
        x2_r = x2_regret[m].mean()
        gap = v33_r - x2_r
        print(f"  {RANK_CHARS[r]:>8}  {n_m:>5,}  "
              f"${fmt_in(v33_r):>+7.1f}  ${fmt_in(x2_r):>+7.1f}  "
              f"${fmt_in(gap):>+8.1f}")

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • If X1 ceiling regret ≈ v33 regret AND v33 satisfies X1 ≥99%,")
    print("    'top = highest' is already implicit in v33 — confirmation only.")
    print("  • If X2 deterministic regret < v33 regret, the rank-down rule beats")
    print("    v3's heuristic and could ship as Rule 7 (high_only).")
    print("  • If X3 heuristic regret < v33 regret, mid-suited is the lever and")
    print("    a sharper version could be Rule 7.")
    print("  • If all three losing vs v33, high_only resists rule extraction —")
    print("    confirms Session 30's note. ML (already shipping) is the path.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
