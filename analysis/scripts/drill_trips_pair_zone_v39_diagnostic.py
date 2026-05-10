"""
Session 55 — Drill TP: Trips_pair zone v39_dt diagnostic (Phase 1).

Goal: identify v39_dt's structural blind spots in the trips_pair category
(cat=4, 1 trip + 1 pair + 2 singletons = 7 cards). Within-category regret
is $909/1000h in v39_dt, the largest remaining ML residual after the pair
zone collapsed in Session 54.

Methodology: Session 54 playbook applied to trips_pair.
1. Sweep all trips_pair hands.
2. For each: compute v39_dt pick, oracle pick, regret.
3. Classify both by (pair_state × bot_suit_profile). Trip placement is
   highly correlated with pair placement (pair_in_mid ⇒ trip_in_bot;
   pair_in_bot ⇒ trip_split).
4. Stratify by (trip_rank, pair_rank) cell.
5. Find cells / mismatches where v39 systematically misroutes.

Reports:
  - Per-cell (trip, pair) regret breakdown for v39_dt
  - v39_dt class distribution vs oracle class distribution per cell
  - Aggregate (v39_class → oracle_class) mismatch matrix
  - Deep dive on top mismatch — which (trip, pair) cells exhibit it

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_pair_zone_v39_diagnostic.py
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
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)
from strategy_v39_dt import strategy_v39_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}

SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS", SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "rainbow", SUIT_PROFILE_THREE_ONE: "3+1",
    SUIT_PROFILE_FOUR_FLUSH: "4-flush",
}


def classify_pick(feats, idx: int, pair_rank: int) -> str:
    """Classify a setting by (pair_state × bot_suit_profile).
    Trip placement is implicit:
      pair_in_mid -> trip likely in bot
      pair_in_bot -> trip split
    """
    pair_in_mid = bool(feats.mid_is_pair[idx]) and int(feats.mid_pair_rank[idx]) == pair_rank
    pair_in_bot = int(feats.bot_pair_rank[idx]) == pair_rank
    if pair_in_mid:
        ps = "Pmid"
    elif pair_in_bot:
        ps = "Pbot"
    else:
        ps = "Psplit"
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    return f"{ps}_{suit_lbl}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 55 Drill TP: Trips_pair zone v39_dt diagnostic")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tp_idx = np.where(cats == 4)[0]  # cat 4 = trips_pair
    n_tp = len(tp_idx)
    print(f"  trips_pair hands: {n_tp:,}")

    if args.sample > 0 and n_tp > args.sample:
        rng = np.random.default_rng(args.seed)
        tp_idx = np.sort(rng.choice(tp_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "v39_class_dist": Counter(),
        "oracle_class_dist": Counter(),
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
    })

    print("\n[3/4] per-hand v39_dt vs oracle classification ...", flush=True)
    t0 = time.time()
    n_processed = 0
    for cid in tp_idx:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
        pair_rank = next(r for r in range(2, 15) if rc[r] == 2)

        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v39_idx = int(strategy_v39_dt(h))

        v39_class = classify_pick(feats, v39_idx, pair_rank)
        oracle_class = classify_pick(feats, oracle_idx, pair_rank)
        regret = float(rowf[oracle_idx]) - float(rowf[v39_idx])

        cell = cell_stats[(trip_rank, pair_rank)]
        cell["n"] += 1
        cell["sum_regret"] += regret
        cell["v39_class_dist"][v39_class] += 1
        cell["oracle_class_dist"][oracle_class] += 1
        if v39_class != oracle_class:
            cell["mismatch"][(v39_class, oracle_class)] += 1
            cell["mismatch_regret"][(v39_class, oracle_class)] += regret

        n_processed += 1
        if n_processed % 50000 == 0:
            rate = n_processed / (time.time() - t0)
            print(f"    progress {n_processed:>8,}/{len(tp_idx):,}  rate={rate:.0f}/s",
                  flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    n_total_grid = 6_009_159

    # 1. Top cells by total regret
    print("=" * 110)
    print("TOP TRIPS_PAIR CELLS BY WHOLE-GRID REGRET CONTRIBUTION (v39_dt vs oracle)")
    print("=" * 110)
    cell_list = sorted(cell_stats.items(), key=lambda x: -x[1]["sum_regret"])
    print(f"  {'trip':>4} {'pair':>4} {'n':>7} {'mean_reg':>10} {'wg_contrib':>11}  "
          f"{'top mismatch':<35} {'mismatch_n':>10} {'mismatch_contrib':>16}")
    for (tr, pr), st in cell_list[:30]:
        if st["n"] == 0:
            continue
        mean_reg = st["sum_regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["sum_regret"] * EV_TO_DOL * 1000 / n_total_grid
        if st["mismatch_regret"]:
            (top_v, top_o), top_reg = max(st["mismatch_regret"].items(),
                                            key=lambda x: x[1])
            top_n = st["mismatch"][(top_v, top_o)]
            top_label = f"{top_v} -> {top_o}"
            top_wg = top_reg * EV_TO_DOL * 1000 / n_total_grid
        else:
            top_label = "(no mismatch)"
            top_n = 0
            top_wg = 0.0
        print(f"  {RANK_CHAR[tr]:>4} {RANK_CHAR[pr]:>4} {st['n']:>7,} "
              f"${mean_reg:>+8.1f} ${wg:>+9.2f}  {top_label:<35} {top_n:>10,} ${top_wg:>+12.2f}")

    # 2. Aggregate mismatch matrix
    print("\n" + "=" * 110)
    print("AGGREGATE MISMATCH MATRIX (across all trips_pair cells)")
    print("=" * 110)
    agg_mismatch = defaultdict(lambda: {"n": 0, "regret": 0.0})
    for (tr, pr), st in cell_stats.items():
        for k, n in st["mismatch"].items():
            agg_mismatch[k]["n"] += n
            agg_mismatch[k]["regret"] += st["mismatch_regret"][k]

    ranked = sorted(agg_mismatch.items(), key=lambda x: -x[1]["regret"])
    print(f"  {'v39_pick':<16} {'oracle_pick':<16} {'n':>10} {'mean_reg':>10} {'wg_contrib':>12}")
    total_mismatch_contrib = 0.0
    for (vc, oc), st in ranked[:25]:
        if st["n"] == 0: continue
        mean_reg = st["regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["regret"] * EV_TO_DOL * 1000 / n_total_grid
        total_mismatch_contrib += wg
        print(f"  {vc:<16} {oc:<16} {st['n']:>10,} ${mean_reg:>+8.1f} ${wg:>+10.2f}")
    print(f"  Top-25 mismatch cumulative: ${total_mismatch_contrib:>+10.2f}/1000h")
    total_all_mismatch = sum(st["regret"] for st in agg_mismatch.values()) * EV_TO_DOL * 1000 / n_total_grid
    print(f"  ALL mismatches total contrib:  ${total_all_mismatch:>+10.2f}/1000h")

    # 3. Deep dive on top mismatch
    if ranked:
        top_k = ranked[0][0]
        top_v, top_o = top_k
        print(f"\n── DEEP DIVE: top mismatch  v39={top_v}  oracle={top_o} ──")
        cells_with_mismatch = [(mp, st["mismatch"][top_k], st["mismatch_regret"][top_k])
                                 for mp, st in cell_stats.items()
                                 if top_k in st["mismatch"]]
        cells_with_mismatch.sort(key=lambda x: -x[2])
        print(f"  Top (trip, pair) cells exhibiting this mismatch:")
        for (tr, pr), n, reg in cells_with_mismatch[:15]:
            mean_reg = reg / n * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / n_total_grid
            print(f"    trip={RANK_CHAR[tr]:>2} pair={RANK_CHAR[pr]:>2}: {n:>5,} hands "
                  f"mean=${mean_reg:>+8.1f}  wg=${wg:>+8.2f}")

    # 4. Class distribution overall
    print("\n" + "=" * 110)
    print("OVERALL CLASS DISTRIBUTION (v39 picks vs oracle picks)")
    print("=" * 110)
    agg_v39 = Counter()
    agg_oracle = Counter()
    for (tr, pr), st in cell_stats.items():
        agg_v39.update(st["v39_class_dist"])
        agg_oracle.update(st["oracle_class_dist"])
    total = sum(agg_v39.values())
    all_classes = sorted(set(agg_v39.keys()) | set(agg_oracle.keys()))
    print(f"  {'class':<18} {'v39_n':>10} {'v39_pct':>10} {'oracle_n':>10} {'oracle_pct':>11} {'v39-oracle':>12}")
    for c in all_classes:
        vn = agg_v39[c]
        on = agg_oracle[c]
        vp = 100*vn/total if total else 0
        op = 100*on/total if total else 0
        diff = vp - op
        print(f"  {c:<18} {vn:>10,} {vp:>9.2f}% {on:>10,} {op:>10.2f}% {diff:>+11.2f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
