"""
Session 51 — Drill M: K-high no-pair characterization (Phase 1).

Same methodology as Drill K (A-high) but for K-high.

Population: cat=high_only AND max_rank=13 (King), no Ace present.

Key question: does v45's Rule 14 (A-high) generalize to K-high?
- K wins top tier ~50% vs random opp (loses to A, wins vs Q-or-lower)
- So K-on-top is borderline; oracle may sometimes prefer K elsewhere
- The HIMID heuristic may or may not transfer

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_K_high_nopair_characterization.py
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS,
    SUIT_PROFILE_SS,
    SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE,
    SUIT_PROFILE_FOUR_FLUSH,
)
from drill_bot_suit_run_priority import (  # noqa: E402
    compute_connectivity_classes, CONN_LABELS,
)
from strategy_v45_rule14_Ahigh_DS import strategy_v45_rule14_Ahigh_DS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}
KING = 13


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 51 Drill M: K-high no-pair characterization (Phase 1)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    ho_idx = np.where(cats == 0)[0]

    print("\n[2/4] filtering to K-high (max_rank=K) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    second_high = []
    for cid in ho_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) != KING:
            continue
        sorted_ranks = sorted(int(r) for r in ranks)
        s2 = sorted_ranks[-2]
        scope_cids.append(int(cid))
        second_high.append(s2)
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    second_high = np.asarray(second_high, dtype=np.int8)
    print(f"  K-high no-pair scope: {len(scope_cids):,}  "
          f"({100*len(scope_cids)/n_total:.4f}% of grid)")
    print(f"  2nd-highest distribution:")
    for r in range(2, 13):
        n = int((second_high == r).sum())
        if n > 0:
            print(f"    2nd={RANK_CHAR[r]}: {n:>7,}  ({100*n/len(scope_cids):>5.2f}%)")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        idx_sorted = np.sort(idx)
        scope_cids = scope_cids[idx_sorted]
        second_high = second_high[idx_sorted]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    SUIT_LABELS = {
        SUIT_PROFILE_DS: "DS",
        SUIT_PROFILE_SS: "SS",
        SUIT_PROFILE_RAINBOW: "rainbow",
        SUIT_PROFILE_THREE_ONE: "3+1",
        SUIT_PROFILE_FOUR_FLUSH: "4-flush",
    }

    oracle_top_is_K = 0
    oracle_top_distribution = Counter()
    oracle_bot_suit_dist = Counter()
    oracle_bot_conn_dist = Counter()

    v45_top_is_K = 0
    v45_top_distribution = Counter()
    v45_bot_suit_dist = Counter()

    sum_v45_ev = 0.0
    sum_oracle_ev = 0.0
    n_processed = 0
    n_v45_eq_oracle = 0

    by_s2 = defaultdict(lambda: {
        "n": 0, "sum_v45": 0.0, "sum_oracle": 0.0, "n_eq": 0,
        "oracle_top_K": 0, "oracle_DS": 0, "v45_DS": 0,
    })

    sum_lift_class = defaultdict(float)
    n_lift_class = defaultdict(int)

    print("\n[4/4] per-hand characterization ...", flush=True)
    t0 = time.time()
    n_total_scope = len(scope_cids)
    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        s2 = int(second_high[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        king_pos = next((j for j in range(7) if int(ranks[j]) == KING), -1)

        feats = setting_features_from_bytes(h)
        conn = compute_connectivity_classes(h)

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v45_idx = int(strategy_v45_rule14_Ahigh_DS(h))

        oracle_ev = float(rowf[oracle_idx])
        v45_ev = float(rowf[v45_idx])
        sum_oracle_ev += oracle_ev
        sum_v45_ev += v45_ev
        n_processed += 1
        if oracle_idx == v45_idx:
            n_v45_eq_oracle += 1

        oracle_top_pos = oracle_idx // 15
        oracle_top_rank = int(ranks[oracle_top_pos])
        oracle_top_distribution[oracle_top_rank] += 1
        if oracle_top_pos == king_pos:
            oracle_top_is_K += 1
        oracle_bot_suit = int(feats.bot_suit_profile[oracle_idx])
        oracle_bot_conn = int(conn[oracle_idx])
        oracle_bot_suit_dist[oracle_bot_suit] += 1
        if oracle_bot_conn >= 0:
            oracle_bot_conn_dist[oracle_bot_conn] += 1

        v45_top_pos = v45_idx // 15
        v45_top_rank = int(ranks[v45_top_pos])
        v45_top_distribution[v45_top_rank] += 1
        if v45_top_pos == king_pos:
            v45_top_is_K += 1
        v45_bot_suit = int(feats.bot_suit_profile[v45_idx])
        v45_bot_suit_dist[v45_bot_suit] += 1

        s2_stats = by_s2[s2]
        s2_stats["n"] += 1
        s2_stats["sum_v45"] += v45_ev
        s2_stats["sum_oracle"] += oracle_ev
        if oracle_idx == v45_idx:
            s2_stats["n_eq"] += 1
        if oracle_top_pos == king_pos:
            s2_stats["oracle_top_K"] += 1
        if oracle_bot_suit == SUIT_PROFILE_DS:
            s2_stats["oracle_DS"] += 1
        if v45_bot_suit == SUIT_PROFILE_DS:
            s2_stats["v45_DS"] += 1

        for suit_code in (SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
                            SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH):
            mask = feats.bot_suit_profile == suit_code
            if mask.any():
                best_ev = float(rowf[mask].max())
                sum_lift_class[suit_code] += (best_ev - v45_ev)
                n_lift_class[suit_code] += 1

        if (i + 1) % 20000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # ── REPORTING ──
    print("=" * 100)
    print(f"AGGREGATE RESULTS (n_hands={n_processed:,})")
    print("=" * 100)

    mean_v45 = sum_v45_ev / n_processed
    mean_oracle = sum_oracle_ev / n_processed
    mean_regret = mean_oracle - mean_v45
    print(f"\n  v45 mean EV per hand:      ${mean_v45 * EV_TO_DOL:>+10.2f}")
    print(f"  Oracle mean EV per hand:   ${mean_oracle * EV_TO_DOL:>+10.2f}")
    print(f"  Mean regret:               ${mean_regret * EV_TO_DOL * 1000:>+8.1f}/1000h within K-high no-pair")
    print(f"  Whole-grid contribution:   ${mean_regret * EV_TO_DOL * 1000 * n_processed / n_total:>+8.1f}/1000h")
    print(f"  v45 == oracle:             {n_v45_eq_oracle:>7,}  ({100*n_v45_eq_oracle/n_processed:.1f}%)")

    print(f"\n── ORACLE TOP-CARD DISTRIBUTION ──")
    print(f"  Oracle picks K on top: {oracle_top_is_K:,} ({100*oracle_top_is_K/n_processed:.2f}%)")
    print(f"  Top-card rank distribution (oracle):")
    for r in range(13, 1, -1):
        n = oracle_top_distribution.get(r, 0)
        if n > 0:
            print(f"    {RANK_CHAR[r]}: {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── v45 TOP-CARD DISTRIBUTION ──")
    print(f"  v45 picks K on top: {v45_top_is_K:,} ({100*v45_top_is_K/n_processed:.2f}%)")
    print(f"  Top-card rank distribution (v45):")
    for r in range(13, 1, -1):
        n = v45_top_distribution.get(r, 0)
        if n > 0:
            print(f"    {RANK_CHAR[r]}: {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── ORACLE BOT SUIT PROFILE DISTRIBUTION ──")
    for code, label in SUIT_LABELS.items():
        n = oracle_bot_suit_dist.get(code, 0)
        print(f"  {label:<10}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── v45 BOT SUIT PROFILE DISTRIBUTION ──")
    for code, label in SUIT_LABELS.items():
        n = v45_bot_suit_dist.get(code, 0)
        print(f"  {label:<10}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── ORACLE BOT CONNECTIVITY DISTRIBUTION ──")
    for code in sorted(oracle_bot_conn_dist.keys()):
        n = oracle_bot_conn_dist[code]
        label = CONN_LABELS.get(code, f"unknown({code})")
        print(f"  {label:<14}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── BEST-IN-CLASS MINUS v45 (S46 lens) ──")
    print(f"  {'class':<10} {'n_co':>9}  {'lift_vs_v45':>14}  {'whole_grid_full':>18}")
    print("-" * 65)
    for code, label in SUIT_LABELS.items():
        n = n_lift_class[code]
        if n == 0: continue
        mean_lift = sum_lift_class[code] / n
        coverage = n / n_processed
        scope_share = n_processed / n_total
        wg_lift = mean_lift * EV_TO_DOL * 1000 * coverage * scope_share
        print(f"  {label:<10} {n:>9,}  ${mean_lift*EV_TO_DOL*1000:>+11.1f}  ${wg_lift:>+15.2f}")

    print(f"\n── PER-2nd-HIGHEST STRATIFICATION ──")
    print(f"  {'2nd':<3} {'n':>7} {'mean_v45':>9} {'mean_oracle':>12} "
          f"{'regret($/1000h)':>17} {'eq%':>6} {'oc_top_K%':>10} "
          f"{'oc_DS%':>8} {'v45_DS%':>9}")
    for s2 in range(12, 1, -1):
        if by_s2[s2]["n"] == 0: continue
        st = by_s2[s2]
        mean_v45_s2 = st["sum_v45"] / st["n"]
        mean_oracle_s2 = st["sum_oracle"] / st["n"]
        regret_s2 = (mean_oracle_s2 - mean_v45_s2) * EV_TO_DOL * 1000
        eq_pct = 100 * st["n_eq"] / st["n"]
        topK_pct = 100 * st["oracle_top_K"] / st["n"]
        ds_oracle_pct = 100 * st["oracle_DS"] / st["n"]
        ds_v45_pct = 100 * st["v45_DS"] / st["n"]
        print(f"  {RANK_CHAR[s2]:<3} {st['n']:>7,} ${mean_v45_s2*EV_TO_DOL:>+7.2f} "
              f"${mean_oracle_s2*EV_TO_DOL:>+10.2f} ${regret_s2:>+13.1f} "
              f"{eq_pct:>5.1f}% {topK_pct:>9.1f}% {ds_oracle_pct:>6.1f}% {ds_v45_pct:>7.1f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
