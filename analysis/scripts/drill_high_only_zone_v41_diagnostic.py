"""
Session 56 — Drill HO: High_only zone v41_dt diagnostic (Phase 1).

Goal: identify v41_dt's structural blind spots in the high_only category
(cat=0, 7 distinct ranks, no pair / no trip / no quad). Within-category
regret is $2,796/1000h in v41_dt — by FAR the largest remaining ML
residual at ~63% of v41's whole-grid regret ($1,131/1000h whole-grid).

User-direction (Session 55 → Session 56): high_only is NOT primarily a
suit-routing problem. Different feature types likely needed —
top-card placement, broadway connectivity, mid-strength quality.

Methodology: Session 54/55 playbook applied to high_only.
1. Sweep all high_only hands.
2. For each: compute v41_dt pick, oracle pick, regret.
3. Classify both by (top_rank × bot_suit_profile × mid_state).
   top_rank   = which of the 7 ranks is placed on top (the SETTING choice).
   bot_suit   = bot's suit profile.
   mid_state  = mid suited (m=ss) vs unsuited (m=rb), with a `mid_top_rank`
                bucket (broadway/non-broadway).
4. Stratify by (h1, h2) = (highest rank in hand, 2nd-highest in hand).
5. Find cells / mismatches where v41 systematically misroutes.

Reports:
  - Per-cell (h1, h2) regret breakdown for v41_dt
  - Aggregate (v41_class → oracle_class) mismatch matrix
  - Deep dive on top mismatch — which (h1, h2) cells exhibit it
  - Overall class distribution v41 vs oracle

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_zone_v41_diagnostic.py
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
    SETTING_HAND_INDICES,
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)
from strategy_v41_dt import strategy_v41_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}

SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS", SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "RB", SUIT_PROFILE_THREE_ONE: "31",
    SUIT_PROFILE_FOUR_FLUSH: "4f",
}


def classify_pick(hand_bytes, feats, idx: int) -> str:
    """Classify a high_only setting by (top_rank × bot_suit × mid_suited).

    top_rank   : rank of the 1 top card (2..14)
    bot_suit   : DS / SS / RB / 31 / 4f
    mid_suited : "ms" if mid 2 cards share suit, "mu" otherwise
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = pos[1:3]
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    top_rank = int(ranks[top_pos])
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_lbl = "ms" if mid_suits[0] == mid_suits[1] else "mu"
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    return f"t{RANK_CHAR[top_rank]}_{suit_lbl}_{mid_lbl}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 56 Drill HO: High_only zone v41_dt diagnostic")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]  # cat 0 = high_only
    n_ho = len(ho_idx)
    print(f"  high_only hands: {n_ho:,}")

    if args.sample > 0 and n_ho > args.sample:
        rng = np.random.default_rng(args.seed)
        ho_idx = np.sort(rng.choice(ho_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[2/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "v41_class_dist": Counter(),
        "oracle_class_dist": Counter(),
        "mismatch": Counter(),
        "mismatch_regret": defaultdict(float),
    })

    print("\n[3/4] per-hand v41_dt vs oracle classification ...", flush=True)
    t0 = time.time()
    n_processed = 0
    for cid in ho_idx:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        ranks_sorted = np.sort(ranks)[::-1]
        h1 = int(ranks_sorted[0])
        h2 = int(ranks_sorted[1])

        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v41_idx = int(strategy_v41_dt(h))

        v41_class = classify_pick(h, feats, v41_idx)
        oracle_class = classify_pick(h, feats, oracle_idx)
        regret = float(rowf[oracle_idx]) - float(rowf[v41_idx])

        cell = cell_stats[(h1, h2)]
        cell["n"] += 1
        cell["sum_regret"] += regret
        cell["v41_class_dist"][v41_class] += 1
        cell["oracle_class_dist"][oracle_class] += 1
        if v41_class != oracle_class:
            cell["mismatch"][(v41_class, oracle_class)] += 1
            cell["mismatch_regret"][(v41_class, oracle_class)] += regret

        n_processed += 1
        if n_processed % 50000 == 0:
            rate = n_processed / (time.time() - t0)
            eta = (len(ho_idx) - n_processed) / rate
            print(f"    progress {n_processed:>8,}/{len(ho_idx):,}  "
                  f"rate={rate:.0f}/s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    n_total_grid = 6_009_159

    # 1. Top cells by total regret
    print("=" * 110)
    print("TOP HIGH_ONLY (h1, h2) CELLS BY WHOLE-GRID REGRET CONTRIBUTION (v41_dt vs oracle)")
    print("=" * 110)
    cell_list = sorted(cell_stats.items(), key=lambda x: -x[1]["sum_regret"])
    print(f"  {'h1':>3} {'h2':>3} {'n':>7} {'mean_reg':>10} {'wg_contrib':>11}  "
          f"{'top mismatch':<48} {'mismatch_n':>10} {'mismatch_contrib':>16}")
    for (h1, h2), st in cell_list[:30]:
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
        print(f"  {RANK_CHAR[h1]:>3} {RANK_CHAR[h2]:>3} {st['n']:>7,} "
              f"${mean_reg:>+8.1f} ${wg:>+9.2f}  {top_label:<48} {top_n:>10,} ${top_wg:>+12.2f}")

    # 2. Aggregate mismatch matrix
    print("\n" + "=" * 110)
    print("AGGREGATE MISMATCH MATRIX (across all high_only cells)")
    print("=" * 110)
    agg_mismatch = defaultdict(lambda: {"n": 0, "regret": 0.0})
    for _, st in cell_stats.items():
        for k, n in st["mismatch"].items():
            agg_mismatch[k]["n"] += n
            agg_mismatch[k]["regret"] += st["mismatch_regret"][k]

    ranked = sorted(agg_mismatch.items(), key=lambda x: -x[1]["regret"])
    print(f"  {'v41_pick':<22} {'oracle_pick':<22} {'n':>10} {'mean_reg':>10} {'wg_contrib':>12}")
    total_mismatch_contrib = 0.0
    for (vc, oc), st in ranked[:30]:
        if st["n"] == 0: continue
        mean_reg = st["regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["regret"] * EV_TO_DOL * 1000 / n_total_grid
        total_mismatch_contrib += wg
        print(f"  {vc:<22} {oc:<22} {st['n']:>10,} ${mean_reg:>+8.1f} ${wg:>+10.2f}")
    print(f"  Top-30 mismatch cumulative: ${total_mismatch_contrib:>+10.2f}/1000h")
    total_all_mismatch = sum(st["regret"] for st in agg_mismatch.values()) * EV_TO_DOL * 1000 / n_total_grid
    print(f"  ALL mismatches total contrib:  ${total_all_mismatch:>+10.2f}/1000h")

    # 2b. Aggregate mismatch by TOP-RANK swap only (collapse suit/mid)
    print("\n" + "=" * 110)
    print("AGGREGATE TOP-RANK SWAP (collapsed across bot suit + mid suited)")
    print("=" * 110)
    top_swap = defaultdict(lambda: {"n": 0, "regret": 0.0})
    for (vc, oc), st in agg_mismatch.items():
        # extract top rank tokens like 't<R>' from vc and oc
        v_top = vc.split("_", 1)[0]
        o_top = oc.split("_", 1)[0]
        key = (v_top, o_top)
        top_swap[key]["n"] += st["n"]
        top_swap[key]["regret"] += st["regret"]
    ts_ranked = sorted(top_swap.items(), key=lambda x: -x[1]["regret"])
    print(f"  {'v41_top':<10} {'oracle_top':<10} {'n':>10} {'mean_reg':>10} {'wg_contrib':>12}")
    for (vt, ot), st in ts_ranked[:25]:
        if st["n"] == 0: continue
        mean_reg = st["regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["regret"] * EV_TO_DOL * 1000 / n_total_grid
        print(f"  {vt:<10} {ot:<10} {st['n']:>10,} ${mean_reg:>+8.1f} ${wg:>+10.2f}")

    # 2c. Aggregate mismatch by SUIT-PROFILE swap only (collapse top + mid)
    print("\n" + "=" * 110)
    print("AGGREGATE BOT-SUIT-PROFILE SWAP (collapsed across top rank + mid suited)")
    print("=" * 110)
    suit_swap = defaultdict(lambda: {"n": 0, "regret": 0.0})
    for (vc, oc), st in agg_mismatch.items():
        # vc like "tA_DS_ms" -> suit token is parts[1]
        v_parts = vc.split("_")
        o_parts = oc.split("_")
        v_suit = v_parts[1] if len(v_parts) >= 2 else "?"
        o_suit = o_parts[1] if len(o_parts) >= 2 else "?"
        key = (v_suit, o_suit)
        suit_swap[key]["n"] += st["n"]
        suit_swap[key]["regret"] += st["regret"]
    ss_ranked = sorted(suit_swap.items(), key=lambda x: -x[1]["regret"])
    print(f"  {'v41_bot':<10} {'oracle_bot':<10} {'n':>10} {'mean_reg':>10} {'wg_contrib':>12}")
    for (vt, ot), st in ss_ranked[:20]:
        if st["n"] == 0: continue
        mean_reg = st["regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["regret"] * EV_TO_DOL * 1000 / n_total_grid
        print(f"  {vt:<10} {ot:<10} {st['n']:>10,} ${mean_reg:>+8.1f} ${wg:>+10.2f}")

    # 3. Deep dive on top mismatch (full-class)
    if ranked:
        top_k = ranked[0][0]
        top_v, top_o = top_k
        print(f"\n── DEEP DIVE: top mismatch  v41={top_v}  oracle={top_o} ──")
        cells_with_mismatch = [(mp, st["mismatch"][top_k], st["mismatch_regret"][top_k])
                                 for mp, st in cell_stats.items()
                                 if top_k in st["mismatch"]]
        cells_with_mismatch.sort(key=lambda x: -x[2])
        print(f"  Top (h1, h2) cells exhibiting this mismatch:")
        for (h1, h2), n, reg in cells_with_mismatch[:15]:
            mean_reg = reg / n * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / n_total_grid
            print(f"    h1={RANK_CHAR[h1]:>2} h2={RANK_CHAR[h2]:>2}: {n:>5,} hands "
                  f"mean=${mean_reg:>+8.1f}  wg=${wg:>+8.2f}")

    # 4. Class distribution overall (full-class)
    print("\n" + "=" * 110)
    print("OVERALL CLASS DISTRIBUTION (v41 picks vs oracle picks)")
    print("=" * 110)
    agg_v41 = Counter()
    agg_oracle = Counter()
    for _, st in cell_stats.items():
        agg_v41.update(st["v41_class_dist"])
        agg_oracle.update(st["oracle_class_dist"])
    total = sum(agg_v41.values())
    all_classes = sorted(set(agg_v41.keys()) | set(agg_oracle.keys()),
                         key=lambda c: -(agg_v41[c] + agg_oracle[c]))
    print(f"  {'class':<22} {'v41_n':>10} {'v41_pct':>10} {'oracle_n':>10} {'oracle_pct':>11} {'v41-oracle':>12}")
    for c in all_classes[:40]:
        vn = agg_v41[c]
        on = agg_oracle[c]
        vp = 100*vn/total if total else 0
        op = 100*on/total if total else 0
        diff = vp - op
        print(f"  {c:<22} {vn:>10,} {vp:>9.2f}% {on:>10,} {op:>10.2f}% {diff:>+11.2f}%")

    # 4b. Class dist collapsed by top-rank only
    print("\n" + "-" * 70)
    print("CLASS DIST collapsed to TOP-RANK only (which card on top)")
    print("-" * 70)
    v41_top = Counter()
    oracle_top = Counter()
    for c, n in agg_v41.items():
        v41_top[c.split("_", 1)[0]] += n
    for c, n in agg_oracle.items():
        oracle_top[c.split("_", 1)[0]] += n
    keys = sorted(set(v41_top.keys()) | set(oracle_top.keys()))
    print(f"  {'top':<6} {'v41_n':>10} {'v41_pct':>10} {'oracle_n':>10} {'oracle_pct':>11} {'v41-oracle':>12}")
    for k in keys:
        vn = v41_top[k]; on = oracle_top[k]
        vp = 100*vn/total if total else 0
        op = 100*on/total if total else 0
        diff = vp - op
        print(f"  {k:<6} {vn:>10,} {vp:>9.2f}% {on:>10,} {op:>10.2f}% {diff:>+11.2f}%")

    # 4c. Class dist collapsed by bot-suit-profile only
    print("\n" + "-" * 70)
    print("CLASS DIST collapsed to BOT-SUIT-PROFILE only")
    print("-" * 70)
    v41_suit = Counter()
    oracle_suit = Counter()
    for c, n in agg_v41.items():
        v41_suit[c.split("_")[1] if "_" in c else "?"] += n
    for c, n in agg_oracle.items():
        oracle_suit[c.split("_")[1] if "_" in c else "?"] += n
    keys = sorted(set(v41_suit.keys()) | set(oracle_suit.keys()))
    print(f"  {'suit':<6} {'v41_n':>10} {'v41_pct':>10} {'oracle_n':>10} {'oracle_pct':>11} {'v41-oracle':>12}")
    for k in keys:
        vn = v41_suit[k]; on = oracle_suit[k]
        vp = 100*vn/total if total else 0
        op = 100*on/total if total else 0
        diff = vp - op
        print(f"  {k:<6} {vn:>10,} {vp:>9.2f}% {on:>10,} {op:>10.2f}% {diff:>+11.2f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
