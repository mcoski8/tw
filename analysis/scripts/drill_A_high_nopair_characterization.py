"""
Session 50 — Drill K: A-high no-pair characterization (Phase 1).

Goal: understand what oracle picks for A-high no-pair hands and where v44
is leaving money on the table.

Population: cat=high_only AND max_rank=14 (Ace).

For each hand, classify oracle pick by structural features:
  - Top card: is it the Ace? (S43 Q1 said ~96%)
  - Bot suit profile: DS / SS / 4-flush / 3+1 / rainbow
  - Bot connectivity (S44 schema): run-4 / one-gap-4 / etc.
  - Mid composition: 2 highest non-A cards? mid-rank? low?

Also compute v44 vs oracle deltas, stratified by 2nd-highest card (K, Q,
J, T, 9, ...). The "v44 vs best-in-class" lens (S46) identifies cross-class
override opportunities.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_A_high_nopair_characterization.py
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
    SUIT_PROFILE_LABELS,
)
from drill_bot_suit_run_priority import (  # noqa: E402
    compute_connectivity_classes,
    CONN_LABELS,
)
from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 50 Drill K: A-high no-pair characterization (Phase 1)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    ho_idx = np.where(cats == 0)[0]
    print(f"  cat=high_only: {len(ho_idx):,}")

    print("\n[2/4] filtering to A-high (max_rank=14) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    second_high = []  # 2nd highest rank for stratification
    for cid in ho_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) != 14:
            continue
        # 2nd highest rank
        sorted_ranks = sorted(int(r) for r in ranks)
        s2 = sorted_ranks[-2]  # 2nd from top
        scope_cids.append(int(cid))
        second_high.append(s2)
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    second_high = np.asarray(second_high, dtype=np.int8)
    print(f"  A-high no-pair scope: {len(scope_cids):,}  "
          f"({100*len(scope_cids)/n_total:.4f}% of grid)")
    print(f"  2nd-highest distribution:")
    for r in range(2, 14):
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

    # Accumulators
    SUIT_LABELS = {
        SUIT_PROFILE_DS: "DS",
        SUIT_PROFILE_SS: "SS",
        SUIT_PROFILE_RAINBOW: "rainbow",
        SUIT_PROFILE_THREE_ONE: "3+1",
        SUIT_PROFILE_FOUR_FLUSH: "4-flush",
    }

    # Oracle pick distributions
    oracle_top_is_A = 0
    oracle_top_distribution = Counter()  # top rank
    oracle_bot_suit_dist = Counter()
    oracle_bot_conn_dist = Counter()
    # Cross: oracle bot (suit, conn)
    oracle_bot_cross = Counter()

    # v44 pick distributions
    v44_top_is_A = 0
    v44_top_distribution = Counter()
    v44_bot_suit_dist = Counter()
    v44_bot_conn_dist = Counter()

    # v44 vs oracle regret
    sum_v44_ev = 0.0
    sum_oracle_ev = 0.0
    n_processed = 0
    n_v44_eq_oracle = 0
    regret_buckets = Counter()  # bucketed regret amounts

    # Per-2nd-highest stratification
    by_s2 = defaultdict(lambda: {
        "n": 0, "sum_v44": 0.0, "sum_oracle": 0.0, "n_eq": 0,
        "oracle_bot_suit": Counter(), "v44_bot_suit": Counter(),
    })

    # "best-in-class minus v44" lens — for each (suit, conn) class,
    # accumulate (best_in_class_ev - v44_ev) and n_co_achievable.
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
        # Find Ace position
        ace_positions = [j for j in range(7) if int(ranks[j]) == 14]
        # Should be exactly 1 (high_only)
        ace_pos = ace_positions[0] if ace_positions else -1

        feats = setting_features_from_bytes(h)
        conn = compute_connectivity_classes(h)

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v44_idx = int(strategy_v44_rule13_three_pair_DS(h))

        oracle_ev = float(rowf[oracle_idx])
        v44_ev = float(rowf[v44_idx])
        sum_oracle_ev += oracle_ev
        sum_v44_ev += v44_ev
        n_processed += 1
        if oracle_idx == v44_idx:
            n_v44_eq_oracle += 1
        regret = oracle_ev - v44_ev
        # Bucket regret in 0.1 EV chunks ($1/1000h)
        bucket = round(regret * 10) / 10
        regret_buckets[bucket] += 1

        # Oracle pick classification
        oracle_top_pos = oracle_idx // 15
        oracle_top_rank = int(ranks[oracle_top_pos])
        oracle_top_distribution[oracle_top_rank] += 1
        if oracle_top_pos == ace_pos:
            oracle_top_is_A += 1
        oracle_bot_suit = int(feats.bot_suit_profile[oracle_idx])
        oracle_bot_conn = int(conn[oracle_idx])
        oracle_bot_suit_dist[oracle_bot_suit] += 1
        if oracle_bot_conn >= 0:
            oracle_bot_conn_dist[oracle_bot_conn] += 1
            oracle_bot_cross[(oracle_bot_suit, oracle_bot_conn)] += 1

        # v44 pick classification
        v44_top_pos = v44_idx // 15
        v44_top_rank = int(ranks[v44_top_pos])
        v44_top_distribution[v44_top_rank] += 1
        if v44_top_pos == ace_pos:
            v44_top_is_A += 1
        v44_bot_suit = int(feats.bot_suit_profile[v44_idx])
        v44_bot_conn = int(conn[v44_idx])
        v44_bot_suit_dist[v44_bot_suit] += 1
        if v44_bot_conn >= 0:
            v44_bot_conn_dist[v44_bot_conn] += 1

        # Stratification by s2
        s2_stats = by_s2[s2]
        s2_stats["n"] += 1
        s2_stats["sum_v44"] += v44_ev
        s2_stats["sum_oracle"] += oracle_ev
        if oracle_idx == v44_idx:
            s2_stats["n_eq"] += 1
        s2_stats["oracle_bot_suit"][oracle_bot_suit] += 1
        s2_stats["v44_bot_suit"][v44_bot_suit] += 1

        # "best-in-class minus v44" lens — for each suit-class, find
        # best EV among settings with that bot suit. Compare to v44.
        for suit_code in (SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
                            SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH):
            mask = feats.bot_suit_profile == suit_code
            if mask.any():
                best_ev = float(rowf[mask].max())
                sum_lift_class[suit_code] += (best_ev - v44_ev)
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

    mean_v44 = sum_v44_ev / n_processed
    mean_oracle = sum_oracle_ev / n_processed
    mean_regret = mean_oracle - mean_v44
    print(f"\n  v44 mean EV per hand:      ${mean_v44 * EV_TO_DOL:>+10.2f}")
    print(f"  Oracle mean EV per hand:   ${mean_oracle * EV_TO_DOL:>+10.2f}")
    print(f"  Mean regret:               ${mean_regret * EV_TO_DOL * 1000:>+8.1f}/1000h within A-high no-pair")
    print(f"  Whole-grid contribution:   ${mean_regret * EV_TO_DOL * 1000 * n_processed / n_total:>+8.1f}/1000h")
    print(f"  v44 == oracle:             {n_v44_eq_oracle:>7,}  ({100*n_v44_eq_oracle/n_processed:.1f}%)")

    print(f"\n── ORACLE TOP-CARD DISTRIBUTION ──")
    print(f"  Oracle picks Ace on top: {oracle_top_is_A:,} ({100*oracle_top_is_A/n_processed:.2f}%)")
    print(f"  Top-card rank distribution (oracle):")
    for r in range(14, 1, -1):
        n = oracle_top_distribution.get(r, 0)
        if n > 0:
            print(f"    {RANK_CHAR[r]}: {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── v44 TOP-CARD DISTRIBUTION ──")
    print(f"  v44 picks Ace on top: {v44_top_is_A:,} ({100*v44_top_is_A/n_processed:.2f}%)")
    print(f"  Top-card rank distribution (v44):")
    for r in range(14, 1, -1):
        n = v44_top_distribution.get(r, 0)
        if n > 0:
            print(f"    {RANK_CHAR[r]}: {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── ORACLE BOT SUIT PROFILE DISTRIBUTION ──")
    for code, label in SUIT_LABELS.items():
        n = oracle_bot_suit_dist.get(code, 0)
        print(f"  {label:<10}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── v44 BOT SUIT PROFILE DISTRIBUTION ──")
    for code, label in SUIT_LABELS.items():
        n = v44_bot_suit_dist.get(code, 0)
        print(f"  {label:<10}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── ORACLE BOT CONNECTIVITY DISTRIBUTION ──")
    for code in sorted(oracle_bot_conn_dist.keys()):
        n = oracle_bot_conn_dist[code]
        label = CONN_LABELS.get(code, f"unknown({code})")
        print(f"  {label:<14}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── BEST-IN-CLASS MINUS v44 (within-hand pairwise lens, S46) ──")
    print(f"  For each suit-class, lift of best-in-class over v44 (averaged across hands where class achievable):")
    print(f"  {'class':<10} {'n_co':>9}  {'lift_vs_v44':>14}  {'whole_grid_full':>18}")
    print("-" * 65)
    for code, label in SUIT_LABELS.items():
        n = n_lift_class[code]
        if n == 0: continue
        mean_lift = sum_lift_class[code] / n
        # whole-grid contribution: lift × coverage × scope_share
        coverage = n / n_processed
        scope_share = n_processed / n_total
        wg_lift = mean_lift * EV_TO_DOL * 1000 * coverage * scope_share
        print(f"  {label:<10} {n:>9,}  ${mean_lift*EV_TO_DOL*1000:>+11.1f}  ${wg_lift:>+15.2f}")

    print(f"\n── ORACLE BOT (suit, conn) CROSS-DISTRIBUTION (top 15 cells) ──")
    for (suit, conn), n in sorted(oracle_bot_cross.items(), key=lambda x: -x[1])[:15]:
        suit_lbl = SUIT_LABELS.get(suit, '?')
        conn_lbl = CONN_LABELS.get(conn, '?')
        print(f"    {suit_lbl:<10} × {conn_lbl:<14}  {n:>7,}  ({100*n/n_processed:>5.2f}%)")

    print(f"\n── REGRET DISTRIBUTION (top buckets) ──")
    print(f"  How much money is left on the table per hand?")
    sorted_buckets = sorted(regret_buckets.items())
    cum = 0
    for bucket, cnt in sorted_buckets[:20]:
        cum += cnt
        print(f"    regret ≤ ${bucket*EV_TO_DOL:+5.1f}  n={cnt:>6,}  cum={cum:>7,} "
              f"({100*cum/n_processed:>5.1f}%)")

    print(f"\n── PER-2nd-HIGHEST STRATIFICATION ──")
    print(f"  {'2nd':<3} {'n':>7} {'mean_v44':>9} {'mean_oracle':>12} "
          f"{'regret($/1000h)':>17} {'eq%':>6} "
          f"{'oracle_DS%':>11} {'v44_DS%':>9}")
    for s2 in range(13, 1, -1):
        if by_s2[s2]["n"] == 0: continue
        st = by_s2[s2]
        mean_v44_s2 = st["sum_v44"] / st["n"]
        mean_oracle_s2 = st["sum_oracle"] / st["n"]
        regret_s2 = (mean_oracle_s2 - mean_v44_s2) * EV_TO_DOL * 1000
        eq_pct = 100 * st["n_eq"] / st["n"]
        ds_oracle_pct = 100 * st["oracle_bot_suit"].get(SUIT_PROFILE_DS, 0) / st["n"]
        ds_v44_pct = 100 * st["v44_bot_suit"].get(SUIT_PROFILE_DS, 0) / st["n"]
        print(f"  {RANK_CHAR[s2]:<3} {st['n']:>7,} ${mean_v44_s2*EV_TO_DOL:>+7.2f} "
              f"${mean_oracle_s2*EV_TO_DOL:>+10.2f} ${regret_s2:>+13.1f} "
              f"{eq_pct:>5.1f}% {ds_oracle_pct:>9.1f}% {ds_v44_pct:>7.1f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
