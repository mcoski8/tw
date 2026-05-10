"""
Session 54 — Drill P: Pair zone v36_dt diagnostic (where the ML is blind).

Goal: identify the ML's structural blind spots in the pair category. Where
does v36_dt's pick differ from oracle's pick, and what structural features
distinguish the right pick from the wrong one?

The v36_dt model has 1.06M leaves at 83 features. Capacity-only retrain
hit saturation (depth=38 ml=1 = depth=36 ml=1). Future ML lift requires
NEW features that aren't currently captured.

Approach:
1. Sweep all 2.8M pair hands
2. For each: compute v36_dt pick, oracle pick, regret
3. Classify both by (pair_state × bot_suit_profile)
4. Stratify by (max_rank, pair_rank) cell
5. Find cells where:
   - v36_dt's structural class differs from oracle's class
   - Per-hand regret is high
   - These are the highest-leverage targets for new features

Reports:
  - Per-cell (max, pair) regret breakdown for v36_dt
  - v36_dt class distribution vs oracle class distribution per cell
  - Top mismatches (v36_dt picks class X, oracle picks class Y) by total
    regret contribution
  - Hand-level features within top mismatches (suit alignment, kicker
    distribution) that could become new gated features

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_pair_zone_v36_diagnostic.py
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
from strategy_v36_dt import strategy_v36_dt  # noqa: E402

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
    """Classify a setting by (pair_state × bot_suit_profile)."""
    pair_in_mid = bool(feats.mid_is_pair[idx]) and int(feats.mid_pair_rank[idx]) == pair_rank
    pair_in_bot = int(feats.bot_pair_rank[idx]) == pair_rank
    if pair_in_mid:
        ps = "mid"
    elif pair_in_bot:
        ps = "bot"
    else:
        ps = "split"
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    return f"{ps}_{suit_lbl}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 54 Drill P: Pair zone v36_dt diagnostic")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    pair_idx = np.where(cats == 1)[0]
    n_pair = len(pair_idx)
    print(f"  pair hands: {n_pair:,}")

    if args.sample > 0 and n_pair > args.sample:
        rng = np.random.default_rng(args.seed)
        pair_idx = np.sort(rng.choice(pair_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    # Per-(max, pair) cell stats
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "v36_class_dist": Counter(),
        "oracle_class_dist": Counter(),
        "mismatch": Counter(),  # (v36_class, oracle_class) -> count
        "mismatch_regret": defaultdict(float),  # (v36_class, oracle_class) -> sum_regret
    })

    print("\n[3/4] per-hand v36_dt vs oracle classification ...", flush=True)
    t0 = time.time()
    n_processed = 0
    for cid in pair_idx:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pair_rank = next(r for r in range(2, 15) if rc[r] == 2)
        max_r = int(ranks.max())

        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v36_idx = int(strategy_v36_dt(h))

        v36_class = classify_pick(feats, v36_idx, pair_rank)
        oracle_class = classify_pick(feats, oracle_idx, pair_rank)
        regret = float(rowf[oracle_idx]) - float(rowf[v36_idx])

        cell = cell_stats[(max_r, pair_rank)]
        cell["n"] += 1
        cell["sum_regret"] += regret
        cell["v36_class_dist"][v36_class] += 1
        cell["oracle_class_dist"][oracle_class] += 1
        if v36_class != oracle_class:
            cell["mismatch"][(v36_class, oracle_class)] += 1
            cell["mismatch_regret"][(v36_class, oracle_class)] += regret

        n_processed += 1
        if n_processed % 200000 == 0:
            rate = n_processed / (time.time() - t0)
            print(f"    progress {n_processed:>8,}/{len(pair_idx):,}  rate={rate:.0f}/s",
                  flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ── Reporting ──
    n_total_grid = 6_009_159

    # 1. Top cells by total regret
    print("=" * 100)
    print("TOP PAIR CELLS BY WHOLE-GRID REGRET CONTRIBUTION (v36_dt vs oracle)")
    print("=" * 100)
    cell_list = sorted(cell_stats.items(),
                        key=lambda x: -x[1]["sum_regret"])
    print(f"  {'max':>3} {'pair':>4} {'n':>7} {'mean_reg':>10} {'wg_contrib':>11}  {'top mismatch':<35} {'mismatch_n':>10} {'mismatch_contrib':>16}")
    for (max_r, pair_r), st in cell_list[:25]:
        if st["n"] == 0:
            continue
        mean_reg = st["sum_regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["sum_regret"] * EV_TO_DOL * 1000 / n_total_grid
        # Top mismatch in this cell
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
        print(f"  {RANK_CHAR[max_r]:>3} {RANK_CHAR[pair_r]:>4} {st['n']:>7,} "
              f"${mean_reg:>+8.1f} ${wg:>+9.2f}  {top_label:<35} {top_n:>10,} ${top_wg:>+12.2f}")

    # 2. Aggregate mismatch (v36_class -> oracle_class) across ALL pair cells
    print("\n" + "=" * 100)
    print("AGGREGATE MISMATCH MATRIX (across all pair cells)")
    print("=" * 100)
    agg_mismatch = defaultdict(lambda: {"n": 0, "regret": 0.0})
    for (mr, pr), st in cell_stats.items():
        for k, n in st["mismatch"].items():
            agg_mismatch[k]["n"] += n
            agg_mismatch[k]["regret"] += st["mismatch_regret"][k]

    ranked = sorted(agg_mismatch.items(), key=lambda x: -x[1]["regret"])
    print(f"  {'v36_pick':<14} {'oracle_pick':<14} {'n':>10} {'mean_reg':>10} {'wg_contrib':>12}")
    total_mismatch_contrib = 0.0
    for (vc, oc), st in ranked[:25]:
        if st["n"] == 0: continue
        mean_reg = st["regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["regret"] * EV_TO_DOL * 1000 / n_total_grid
        total_mismatch_contrib += wg
        print(f"  {vc:<14} {oc:<14} {st['n']:>10,} ${mean_reg:>+8.1f} ${wg:>+10.2f}")
    print(f"  Top-25 mismatch cumulative: ${total_mismatch_contrib:>+10.2f}/1000h")
    total_all_mismatch = sum(st["regret"] for st in agg_mismatch.values()) * EV_TO_DOL * 1000 / n_total_grid
    print(f"  ALL mismatches total contrib:  ${total_all_mismatch:>+10.2f}/1000h")

    # 3. Sub-classes within top mismatch — drill down
    if ranked:
        top_k = ranked[0][0]  # most expensive mismatch
        top_v, top_o = top_k
        print(f"\n── DEEP DIVE: top mismatch  v36={top_v}  oracle={top_o} ──")
        # Sub-stratify by (max, pair)
        cells_with_mismatch = [(mp, st["mismatch"][top_k], st["mismatch_regret"][top_k])
                                 for mp, st in cell_stats.items()
                                 if top_k in st["mismatch"]]
        cells_with_mismatch.sort(key=lambda x: -x[2])
        print(f"  Top (max, pair) cells exhibiting this mismatch:")
        for (mr, pr), n, reg in cells_with_mismatch[:15]:
            mean_reg = reg / n * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / n_total_grid
            print(f"    max={RANK_CHAR[mr]:>2} pair={RANK_CHAR[pr]:>2}: {n:>5,} hands "
                  f"mean=${mean_reg:>+8.1f}  wg=${wg:>+8.2f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
