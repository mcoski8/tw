"""
Session 37 — Path B: Rule 6 verification.

Distill_v29_trips (Session 36) showed that v29 was $85/1000h whole-grid
WORSE than always-A_paired_mid on pure trips. v29 picks A on only 79.9%
of trips; the 20.1% deviations are systematically wrong.

Question for v14_combined (the human-memorizable rule chain): does it
already enforce A_paired_mid on pure trips? If not, codifying that rule
(call it Rule 6) is a free win for the human strategy.

Tracing v14:
  detect_v12_trips_pair → fires only on trips_pair, not pure trips
  detect_v10_two_pair    → no
  detect_v9_2_single_pair → no
  fallback                → strategy_v8_hybrid
v8_hybrid for pure trips (not high_only, not is_one_pair):
  → strategy_v7_regression (a learned tree, NOT a hand-coded A_paired_mid rule)

So pure-trips routing in v14 is whatever v7_regression learned. This script
empirically checks whether v7_regression happens to always pick A_paired_mid,
and quantifies the gap to the always-A baseline using the oracle grid.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/verify_rule6_v14_trips.py
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
from tw_analysis.query import setting_features_from_bytes, SUIT_PROFILE_DS  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0


def main() -> int:
    print("=" * 80)
    print("Session 37: Verify Rule 6 (Always A_paired_mid for pure trips) in v14")
    print("=" * 80)

    print("\n[1/5] loading feature_table for trips mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads", "trips_rank"])
    n_trips = ft["n_trips"].to_numpy()
    n_pairs = ft["n_pairs"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank_full = ft["trips_rank"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    n_total = len(ft)
    n_trips_hands = int(mask_trips.sum())
    print(f"  total hands: {n_total:,}")
    print(f"  pure trips:  {n_trips_hands:,}  ({100*mask_trips.mean():.2f}%)")

    print("\n[2/5] loading canonical hands + oracle grid (memmap) ...", flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])
    print(f"  Y: {Y.shape}")

    trips_idx = np.where(mask_trips)[0]
    trips_ranks = trips_rank_full[trips_idx]

    # Sample size — full 328K is feasible; v14 calls per-hand ~ms-scale via
    # learned trees, so 328K * v14 = ~3-5 min. We use a 30K sample for speed
    # and a tighter trips_rank-stratified sample.
    rng = np.random.RandomState(0)
    SAMPLE_N = 30000
    if SAMPLE_N >= len(trips_idx):
        sample_pos = np.arange(len(trips_idx))
    else:
        sample_pos = rng.choice(len(trips_idx), SAMPLE_N, replace=False)
        sample_pos.sort()
    sample_canonical_ids = trips_idx[sample_pos]
    sample_ranks = trips_ranks[sample_pos]
    print(f"\n[3/5] sample of {len(sample_pos):,} pure-trips hands "
          f"(of {n_trips_hands:,} total)", flush=True)

    print("\n[4/5] importing v14_combined and walking sample ...", flush=True)
    from strategy_v14_combined import strategy_v14_combined  # noqa: E402

    n_pick_a = 0   # mid is pair-of-trip-rank, top != trip-rank
    n_pick_b = 0   # bot has 2 trip-rank cards (and not C)
    n_pick_c = 0   # top is trip-rank AND mid is pair-of-trip-rank
    n_pick_other = 0

    v14_picks = np.empty(len(sample_pos), dtype=np.int32)
    v14_evs = np.empty(len(sample_pos), dtype=np.float64)
    a_evs = np.full(len(sample_pos), np.nan, dtype=np.float64)
    a_picks = np.full(len(sample_pos), -1, dtype=np.int32)
    ac_evs = np.full(len(sample_pos), np.nan, dtype=np.float64)
    oracle_evs = np.empty(len(sample_pos), dtype=np.float64)

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        # canonical hands are already sorted; v14 expects sorted bytes
        feats = setting_features_from_bytes(h)
        tr = int(sample_ranks[i])

        pick = int(strategy_v14_combined(h))
        v14_picks[i] = pick

        evs_row = np.asarray(Y[cid], dtype=np.float64)
        v14_evs[i] = evs_row[pick]
        oracle_evs[i] = evs_row.max()

        # Categorize v14's pick using setting features
        is_mid_pair_trip = bool(feats.mid_is_pair[pick]) and int(feats.mid_pair_rank[pick]) == tr
        is_top_trip = int(feats.top_rank[pick]) == tr
        is_bot_pair_trip = int(feats.bot_top_pair_rank[pick]) == tr

        if is_mid_pair_trip and is_top_trip:
            n_pick_c += 1
        elif is_mid_pair_trip:
            n_pick_a += 1
        elif is_bot_pair_trip:
            n_pick_b += 1
        else:
            n_pick_other += 1

        # Always-A_paired_mid: mid is paired at trip_rank AND top != trip_rank.
        mask_a = (feats.mid_is_pair
                  & (feats.mid_pair_rank == tr)
                  & (feats.top_rank != tr))
        if mask_a.any():
            cand_evs = evs_row.copy()
            cand_evs[~mask_a] = -np.inf
            a_pick = int(cand_evs.argmax())
            a_picks[i] = a_pick
            a_evs[i] = cand_evs[a_pick]

        # Always-A∪C (mid_is_pair_of_trip_rank, top free): the third trip
        # card NEVER goes to bot. This is the cleanest "Rule 6" formulation.
        mask_ac = (feats.mid_is_pair & (feats.mid_pair_rank == tr))
        if mask_ac.any():
            cand_evs = evs_row.copy()
            cand_evs[~mask_ac] = -np.inf
            ac_evs[i] = cand_evs[int(cand_evs.argmax())]

        if time.time() - last_log > 5:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (len(sample_pos) - i - 1) / rate
            print(f"    progress {i+1:>6,}/{len(sample_pos):,}  "
                  f"rate={rate:.0f}/s  eta {eta_s:.0f}s",
                  flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({len(sample_pos)/elapsed:.0f}/s)")

    # ============================================================
    # [5/5] Report
    # ============================================================
    n = len(sample_pos)
    pct = lambda k: 100.0 * k / n  # noqa: E731
    print("\n" + "=" * 80)
    print("PICK DISTRIBUTION (v14_combined on pure-trips sample)")
    print("=" * 80)
    print(f"  A_paired_mid (mid=trip pair, top != trip): {n_pick_a:>6,}  ({pct(n_pick_a):5.2f}%)")
    print(f"  C_top_trip   (top=trip, mid=trip pair):    {n_pick_c:>6,}  ({pct(n_pick_c):5.2f}%)")
    print(f"  B_bot_pair_trip (bot has 2 trip cards):    {n_pick_b:>6,}  ({pct(n_pick_b):5.2f}%)")
    print(f"  Other (trips not paired anywhere):         {n_pick_other:>6,}  ({pct(n_pick_other):5.2f}%)")
    print()
    a_or_c = n_pick_a + n_pick_c
    print(f"  v14 picks A∪C (any setting with mid=trip pair): "
          f"{a_or_c:>6,}  ({pct(a_or_c):5.2f}%)")
    print(f"  → For comparison v29 picks A on 79.9% (no C breakdown).")

    print("\n" + "=" * 80)
    print("EV COMPARISON (within-trips $/1000h)")
    print("=" * 80)
    pop_share = mask_trips.mean()
    def whole_grid(reg_mean):
        return reg_mean * EV_TO_DOLLARS * 1000 * pop_share

    v14_regret_each = oracle_evs - v14_evs
    a_avail = ~np.isnan(a_evs)
    # Effective regret: pick A when available else fall back to v14
    a_effective_ev = np.where(a_avail, a_evs, v14_evs)
    a_eff_regret = oracle_evs - a_effective_ev

    print(f"  v14 mean regret on trips: {v14_regret_each.mean():+.4f}  "
          f"(${v14_regret_each.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips, "
          f"${whole_grid(v14_regret_each.mean()):+,.1f}/1000h whole-grid)")
    print(f"  Always-A regret (else v14): {a_eff_regret.mean():+.4f}  "
          f"(${a_eff_regret.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips, "
          f"${whole_grid(a_eff_regret.mean()):+,.1f}/1000h whole-grid)")
    delta = v14_regret_each.mean() - a_eff_regret.mean()
    print(f"\n  v14 vs Always-A: {delta:+.4f}  "
          f"(${delta*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips, "
          f"${whole_grid(delta):+,.1f}/1000h whole-grid)")
    print(f"  Positive ⇒ Rule 6 (always A_paired_mid) would HELP v14")
    print(f"  Negative ⇒ v14 already encodes something at least as good as A")

    # The cleaner formulation: "Always mid_is_pair_of_trip_rank" (A or C).
    ac_avail = ~np.isnan(ac_evs)
    ac_effective_ev = np.where(ac_avail, ac_evs, v14_evs)
    ac_eff_regret = oracle_evs - ac_effective_ev
    print(f"\n  Always-A∪C (mid=trip pair, top free) regret: {ac_eff_regret.mean():+.4f}  "
          f"(${ac_eff_regret.mean()*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips, "
          f"${whole_grid(ac_eff_regret.mean()):+,.1f}/1000h whole-grid)")
    delta_ac = v14_regret_each.mean() - ac_eff_regret.mean()
    print(f"  v14 vs Always-A∪C: {delta_ac:+.4f}  "
          f"(${delta_ac*EV_TO_DOLLARS*1000:+,.0f}/1000h within-trips, "
          f"${whole_grid(delta_ac):+,.1f}/1000h whole-grid)")
    print(f"  → This is the 'Rule 6' formulation: NEVER put the 3rd trip card on bot.")

    # Per-rank stratification
    print("\n" + "=" * 80)
    print("Per trips_rank: pick distribution + Always-A advantage")
    print("=" * 80)
    print(f"  {'rank':>4}  {'n':>5}  {'%A':>5}  {'%C':>5}  {'%B':>5}  {'%oth':>5}  "
          f"{'v14_$':>8}  {'A_$':>8}  {'gap_$':>8}")
    for r in range(2, 15):
        m = sample_ranks == r
        n_m = int(m.sum())
        if n_m == 0:
            continue
        # Recompute pick categories for this rank
        a_count = c_count = b_count = o_count = 0
        for i in np.where(m)[0]:
            cid = int(sample_canonical_ids[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            feats = setting_features_from_bytes(h)
            pick = int(v14_picks[i])
            tr = int(sample_ranks[i])
            is_mid_pair_trip = bool(feats.mid_is_pair[pick]) and int(feats.mid_pair_rank[pick]) == tr
            is_top_trip = int(feats.top_rank[pick]) == tr
            is_bot_pair_trip = int(feats.bot_top_pair_rank[pick]) == tr
            if is_mid_pair_trip and is_top_trip:
                c_count += 1
            elif is_mid_pair_trip:
                a_count += 1
            elif is_bot_pair_trip:
                b_count += 1
            else:
                o_count += 1

        v14_r = v14_regret_each[m].mean()
        a_r = a_eff_regret[m].mean()
        gap = v14_r - a_r
        share_r = n_m / len(sample_pos)
        v14_dol = v14_r * EV_TO_DOLLARS * 1000
        a_dol = a_r * EV_TO_DOLLARS * 1000
        gap_dol = gap * EV_TO_DOLLARS * 1000
        print(f"  {r:>4}  {n_m:>5,}  {100*a_count/n_m:>4.1f}%  "
              f"{100*c_count/n_m:>4.1f}%  {100*b_count/n_m:>4.1f}%  {100*o_count/n_m:>4.1f}%  "
              f"${v14_dol:>+6.1f}  ${a_dol:>+6.1f}  ${gap_dol:>+6.1f}")

    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    if a_or_c >= 0.99 * n:
        print("  v14 already always picks mid=trip-pair (A or C). Rule 6 is implicit.")
    elif a_or_c >= 0.95 * n:
        print(f"  v14 picks A∪C on {pct(a_or_c):.1f}% of trips. Mostly there but")
        print(f"  not 100% — codifying Rule 6 might pick up the residual.")
    else:
        print(f"  v14 picks A∪C on only {pct(a_or_c):.1f}% of trips. Rule 6 is")
        print(f"  NOT implicitly enforced — codifying it would change v14's behavior.")
    print(f"  Always-A vs v14 advantage: ${whole_grid(delta):+,.1f}/1000h whole-grid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
