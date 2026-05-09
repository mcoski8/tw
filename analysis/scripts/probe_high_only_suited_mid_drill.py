"""
Session 41 — drill into X3: which same-suit mid does the oracle prefer?

Setup (same as `verify_rule_X_v33_high_only.py`): 30K random high_only
hands, RandomState(0). For each hand:

  1. top is locked = highest-rank card (always; v3/v33 already do this).
  2. Among the remaining 6 cards, enumerate every (mid_a, mid_b) where
     mid_a and mid_b share a suit ("same-suit mid candidates").
  3. For each candidate, compute the oracle EV at that setting AND a
     pile of features describing the candidate.
  4. Identify the oracle-best same-suit mid; compare to v33's pick and
     several heuristic candidates.

The goal: find a single feature (or simple combination) that, when used
as the tiebreaker among same-suit mids, captures most of the X3 oracle
ceiling ($355/1000h whole-grid).

Heuristic candidates tested:
  H1: highest mid_rank_sum                     (already tested in X3 — −$6)
  H2: mid_connected (gap≤1) first, else H1
  H3: bot DS feasible first, else H1
  H4: mid contains broadway (rank ≥10) first, else H1
  H5: mid is connected AND bot is DS, else H2, else H1
  H6: mid_rank_sum + 5*mid_connected + 3*bot_DS  (continuous score)

Each heuristic is graded by mean regret on the 30K high_only sample.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_high_only_suited_mid_drill.py
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

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
SAMPLE_N = 30000


def _bot_suit_profile(bot_suits: list[int]) -> int:
    """Higher = better Omaha 2+3 fit. DS=4, SS=3, rainbow=2, 3+1=1, 4-flush=0."""
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


def main() -> int:
    print("=" * 80)
    print("Session 41: drill X3 — which same-suit mid does the oracle prefer?")
    print("=" * 80)

    print("\n[1/4] loading feature_table for high_only mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    mask_ho = (n_pairs == 0) & (n_trips == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = float(mask_ho.mean())
    print(f"  high_only: {int(mask_ho.sum()):,}  ({100*pop_share:.4f}%)")

    print("\n[2/4] loading canonical hands + oracle grid (memmap) ...",
          flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    ho_idx_full = np.where(mask_ho)[0]
    rng = np.random.RandomState(0)
    sample_pos = rng.choice(len(ho_idx_full), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = ho_idx_full[sample_pos]

    print(f"\n[3/4] enumerating same-suit mid candidates per hand ...",
          flush=True)
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

    # Per-hand quantities
    v33_evs = np.empty(SAMPLE_N, dtype=np.float64)
    oracle_evs = np.empty(SAMPLE_N, dtype=np.float64)
    best_suited_mid_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)

    # Heuristic picks (each delivers an EV per hand)
    h1_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # highest rank-sum
    h2_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # connected first
    h3_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # bot_DS first
    h4_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # broadway first
    h5_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # connected+DS combo
    h6_evs = np.full(SAMPLE_N, np.nan, dtype=np.float64)  # composite score

    # Whether v33's pick is itself a same-suit mid
    v33_picks_suited_mid = np.zeros(SAMPLE_N, dtype=bool)
    n_suited_candidates = np.zeros(SAMPLE_N, dtype=np.int8)

    # For feature-importance: collect (cand_count, oracle_index, candidate
    # features) only on hands with ≥2 suited candidates.
    # For each suited candidate: rank_sum, connected (gap≤1), broadway,
    # bot_DS, mid_suit_matches_bot_majority.
    feat_records = []  # list of dicts

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        evs_row = np.asarray(Y[cid], dtype=np.float64)
        oracle_evs[i] = evs_row.max()

        v33_pick = int(strategy_v33_rule6_trips(h))
        v33_evs[i] = evs_row[v33_pick]
        feats = setting_features_from_bytes(h)
        # Detect if v33's mid is same-suit (mid is_pair would be False
        # since this is high_only; we need the per-setting bot_suits or
        # mid suits directly)
        # v33_pick decoded: top_idx, mid_combo
        top_idx = v33_pick // 15
        # mid combo enumerates remaining-6 indices
        from tw_analysis.settings import _MID_PAIRS  # noqa: E402
        mid_combo = v33_pick % 15
        mc_a, mc_b = _MID_PAIRS[mid_combo]
        remaining_pos = [j for j in range(7) if j != top_idx]
        v33_mid_a = remaining_pos[mc_a]
        v33_mid_b = remaining_pos[mc_b]
        v33_picks_suited_mid[i] = (int(suits[v33_mid_a])
                                   == int(suits[v33_mid_b]))

        # Identify highest-rank singleton (top is fixed there for X1)
        positions_by_rank_desc = sorted(range(7), key=lambda j: -int(ranks[j]))
        top_pos = positions_by_rank_desc[0]
        rem = [j for j in range(7) if j != top_pos]

        # Enumerate same-suit mid candidates from remaining 6
        cands = []  # list of dicts per candidate
        for ai in range(6):
            for bi in range(ai + 1, 6):
                a = rem[ai]
                b = rem[bi]
                if int(suits[a]) != int(suits[b]):
                    continue
                bot_pos = [r for r in rem if r != a and r != b]
                bot_suits = [int(suits[p]) for p in bot_pos]
                bot_ranks = sorted(int(ranks[p]) for p in bot_pos)
                ra, rb = int(ranks[a]), int(ranks[b])
                rank_sum = ra + rb
                rank_max = max(ra, rb)
                rank_min = min(ra, rb)
                gap = rank_max - rank_min
                connected = gap <= 1
                gap_le_2 = gap <= 2
                broadway = (rank_max >= 10) or (rank_min >= 10)
                bot_profile = _bot_suit_profile(bot_suits)
                bot_ds = (bot_profile == 4)
                # Mid suit matches majority bot suit?
                mid_suit = int(suits[a])
                bot_suit_counts = [bot_suits.count(s) for s in range(4)]
                mid_suit_in_bot = bot_suit_counts[mid_suit]

                s_idx = int(_setting_index_from_tmb(top_pos, a, b))
                ev = float(evs_row[s_idx])

                cands.append({
                    "a": a, "b": b, "setting_idx": s_idx, "ev": ev,
                    "rank_sum": rank_sum, "rank_max": rank_max,
                    "connected": connected, "gap_le_2": gap_le_2,
                    "broadway": broadway, "bot_ds": bot_ds,
                    "bot_profile": bot_profile,
                    "mid_suit_in_bot": mid_suit_in_bot,
                    "gap": gap,
                })

        n_suited_candidates[i] = len(cands)
        if not cands:
            continue

        # Oracle-best among same-suit mids
        best_cand = max(cands, key=lambda c: c["ev"])
        best_suited_mid_evs[i] = best_cand["ev"]

        # Heuristic 1: highest rank_sum (tiebreak: highest rank_max, then ev order — irrelevant since deterministic)
        h1 = max(cands, key=lambda c: (c["rank_sum"], c["rank_max"]))
        h1_evs[i] = h1["ev"]

        # Heuristic 2: connected first (gap<=1), then highest rank_sum
        h2 = max(cands, key=lambda c: (1 if c["connected"] else 0, c["rank_sum"]))
        h2_evs[i] = h2["ev"]

        # Heuristic 3: bot_DS first, then highest rank_sum
        h3 = max(cands, key=lambda c: (1 if c["bot_ds"] else 0, c["rank_sum"]))
        h3_evs[i] = h3["ev"]

        # Heuristic 4: broadway first (any card >= T), then rank_sum
        h4 = max(cands, key=lambda c: (1 if c["broadway"] else 0, c["rank_sum"]))
        h4_evs[i] = h4["ev"]

        # Heuristic 5: connected AND bot_DS first; else connected; else rank_sum
        h5 = max(cands, key=lambda c: (
            1 if (c["connected"] and c["bot_ds"]) else 0,
            1 if c["connected"] else 0,
            1 if c["bot_ds"] else 0,
            c["rank_sum"],
        ))
        h5_evs[i] = h5["ev"]

        # Heuristic 6: composite score
        def _score(c):
            return (c["rank_sum"]
                    + (5 if c["connected"] else 0)
                    + (3 if c["bot_ds"] else 0)
                    + (2 if c["broadway"] else 0))
        h6 = max(cands, key=_score)
        h6_evs[i] = h6["ev"]

        # Save feature records for hands with ≥2 candidates: record
        # whether this candidate is the oracle-best, and its features.
        if len(cands) >= 2:
            best_idx = cands.index(best_cand)
            for k, c in enumerate(cands):
                feat_records.append({
                    "hand_i": i,
                    "n_cands": len(cands),
                    "is_best": k == best_idx,
                    "rank_sum": c["rank_sum"],
                    "rank_max": c["rank_max"],
                    "connected": int(c["connected"]),
                    "gap_le_2": int(c["gap_le_2"]),
                    "broadway": int(c["broadway"]),
                    "bot_ds": int(c["bot_ds"]),
                    "bot_profile": c["bot_profile"],
                    "ev": c["ev"],
                })

        if time.time() - last_log > 5:
            rate = (i + 1) / (time.time() - t0)
            eta_s = (SAMPLE_N - i - 1) / rate
            print(f"    progress {i+1:>6,}/{SAMPLE_N:,}  rate={rate:.0f}/s  "
                  f"eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({SAMPLE_N/elapsed:.0f}/s)")

    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    # ============================================================
    # [4/4] Reports
    # ============================================================
    print("\n" + "=" * 80)
    print("BASELINES")
    print("=" * 80)
    v33_regret = oracle_evs - v33_evs
    print(f"  v33 mean regret on high_only: ${fmt_in(v33_regret.mean()):+,.1f}/1000h within-cat  "
          f"(${fmt_grid(v33_regret.mean()):+,.1f}/1000h whole-grid)")

    print(f"\n  Same-suit mid candidates per hand:")
    print(f"    mean: {n_suited_candidates.mean():.2f}")
    print(f"    distribution:")
    for n in range(0, 16):
        c = int((n_suited_candidates == n).sum())
        if c == 0:
            continue
        print(f"      {n}: {c:>5,} ({100*c/SAMPLE_N:>4.1f}%)")

    print(f"\n  v33 picks a same-suit mid: {int(v33_picks_suited_mid.sum()):,}/{SAMPLE_N:,}  "
          f"({100*v33_picks_suited_mid.mean():.1f}%)")

    # ============================================================
    # Heuristic comparison
    # ============================================================
    print("\n" + "=" * 80)
    print("HEURISTIC COMPARISON: pick a same-suit mid via various rules")
    print("    (effective EV = heuristic EV where ≥1 same-suit mid exists, else v33)")
    print("=" * 80)

    suited_avail = ~np.isnan(best_suited_mid_evs)

    def _eval_heuristic(name: str, h_evs: np.ndarray):
        eff = np.where(suited_avail & ~np.isnan(h_evs), h_evs, v33_evs)
        regret = oracle_evs - eff
        delta = v33_regret.mean() - regret.mean()
        print(f"  {name:<46}  regret=${fmt_in(regret.mean()):>+7.1f}  "
              f"Δ vs v33: ${fmt_in(delta):>+6.1f} within-cat  "
              f"(${fmt_grid(delta):>+5.2f} whole-grid)")
        return delta

    print(f"  {'rule':<46}  {'regret':>14}  {'Δ vs v33':>10}")
    _eval_heuristic("v33 production (baseline)", v33_evs)
    print(f"  {'─'*78}")
    _eval_heuristic("oracle ceiling (best same-suit mid)", best_suited_mid_evs)
    print(f"  {'─'*78}")
    _eval_heuristic("H1: highest rank_sum same-suit mid", h1_evs)
    _eval_heuristic("H2: connected (gap≤1) first, else H1", h2_evs)
    _eval_heuristic("H3: bot_DS first, else H1", h3_evs)
    _eval_heuristic("H4: broadway first, else H1", h4_evs)
    _eval_heuristic("H5: connected+DS, else connected, else H1", h5_evs)
    _eval_heuristic("H6: composite (rank_sum + 5*conn + 3*ds + 2*bw)", h6_evs)

    # ============================================================
    # Feature-importance: among hands with ≥2 same-suit candidates,
    # what feature best discriminates the oracle-best?
    # ============================================================
    if feat_records:
        df = pd.DataFrame(feat_records)
        print("\n" + "=" * 80)
        print("FEATURE-IMPORTANCE on hands with ≥2 same-suit candidates")
        print(f"  (n={int(df['hand_i'].nunique()):,} hands, "
              f"{len(df):,} candidate-rows)")
        print("=" * 80)

        # For each feature, compute: P(is_best | feature=1) vs P(is_best | feature=0)
        for feat in ["connected", "gap_le_2", "broadway", "bot_ds"]:
            p_best_when_1 = df[df[feat] == 1]["is_best"].mean()
            p_best_when_0 = df[df[feat] == 0]["is_best"].mean()
            print(f"  P(is_best | {feat:<12}=1) = {p_best_when_1:.3f}  "
                  f"P(is_best | =0) = {p_best_when_0:.3f}  "
                  f"lift = {p_best_when_1 - p_best_when_0:+.3f}")

        # Also for rank_sum: percentile of best-candidate's rank_sum within
        # its hand
        print(f"\n  Rank-sum percentile of oracle-best within hand:")
        groups = df.groupby("hand_i")
        best_rank_sum_pctile = []
        for hand_i, group in groups:
            best_row = group[group["is_best"]]
            if len(best_row) == 0 or len(group) < 2:
                continue
            best_rs = best_row["rank_sum"].iloc[0]
            pct = (group["rank_sum"] <= best_rs).mean()
            best_rank_sum_pctile.append(pct)
        if best_rank_sum_pctile:
            arr = np.array(best_rank_sum_pctile)
            print(f"    mean: {arr.mean():.3f}  "
                  f"(0.5 = random; 1.0 = always highest rank_sum)")
            print(f"    fraction where best-cand has highest rank_sum: "
                  f"{(arr == 1.0).mean():.3f}")

        # Stratify P(is_best) by (connected, bot_ds) joint cells
        print(f"\n  P(is_best) by (connected × bot_ds) joint cell:")
        joint = df.groupby(["connected", "bot_ds"])["is_best"].agg(["count", "mean"])
        print(joint)

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • If H2/H3/H5 has Δ > $50/1000h whole-grid vs v33, that's the rule.")
    print("    Ship it as the same-suit-mid tiebreaker.")
    print("  • If all heuristics tie or regress, there's no clean rule —")
    print("    the within-suited-mid signal is multivariate and ML-only.")
    print("    (Rule 7 'pick a same-suit mid' would still be teachable but")
    print("     'which one' falls back to the existing v33 score.)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
