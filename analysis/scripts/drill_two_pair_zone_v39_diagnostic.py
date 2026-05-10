"""
Session 55 — Drill T2P: Two_pair zone v39_dt diagnostic (Phase 1).

Within-category regret in v39_dt = $918/1000h. Two_pair structure:
2 pairs + 3 singletons (2+2+1+1+1=7 cards). Bigger search space than
trips_pair due to multiple anchor placements.

Goal: identify v39_dt's structural blind spots in the two_pair zone.
Apply same playbook as Drill TP/P.

Classify by (anchor_state × bot_suit_profile):
  anchor_state ∈ {Hmid, Hbot, Lmid, Lbot, both_bot, split}
    Hmid = high-pair in mid intact
    Hbot = high-pair in bot intact (without low-pair in bot)
    Lmid = low-pair in mid intact
    Lbot = low-pair in bot intact (without high-pair in bot)
    both_bot = both pairs in bot (anchor "Layout A": bot = HH+LL)
    split = otherwise (some pair split across tiers)

Stratify by (high_pair_rank, low_pair_rank) cell.

Reports:
  - Per-cell regret breakdown
  - Aggregate (v39_class → oracle_class) mismatch matrix
  - Deep dive on top mismatch

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_zone_v39_diagnostic.py
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


def classify_pick(hand_bytes, feats, idx: int, hi_pair: int, lo_pair: int) -> str:
    """Classify by (anchor_state × bot_suit_profile) using per-tier pair-position counts.

    H_state ∈ {Hmid, Hbot, Hsplit}: where both high-pair cards live (intact in mid/bot
        or split). H_top isn't possible (top=1 card).
    L_state ∈ {Lmid, Lbot, Lsplit}: same for low pair.
    Combined: "Hmid_Lbot", "Hbot_Lmid", "Hbot_Lbot" (both in bot), "Hmid_Lsplit",
    "Hsplit_Lbot", etc.
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = pos[0]
    mid_pos = pos[1:3]
    bot_pos = pos[3:7]
    ranks = (hand_bytes // 4) + 2
    h_top = int(ranks[top_pos] == hi_pair)
    h_mid = int((ranks[mid_pos] == hi_pair).sum())
    h_bot = int((ranks[bot_pos] == hi_pair).sum())
    l_top = int(ranks[top_pos] == lo_pair)
    l_mid = int((ranks[mid_pos] == lo_pair).sum())
    l_bot = int((ranks[bot_pos] == lo_pair).sum())

    if h_mid == 2:
        h_state = "Hmid"
    elif h_bot == 2:
        h_state = "Hbot"
    else:
        h_state = "Hsplit"
    if l_mid == 2:
        l_state = "Lmid"
    elif l_bot == 2:
        l_state = "Lbot"
    else:
        l_state = "Lsplit"
    anchor = f"{h_state}_{l_state}"
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    return f"{anchor}_{suit_lbl}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 55 Drill T2P: Two_pair zone v39_dt diagnostic")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    t2p_idx = np.where(cats == 2)[0]
    n_t2p = len(t2p_idx)
    print(f"  two_pair hands: {n_t2p:,}")

    if args.sample > 0 and n_t2p > args.sample:
        rng = np.random.default_rng(args.seed)
        t2p_idx = np.sort(rng.choice(t2p_idx, size=args.sample, replace=False))
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
    for cid in t2p_idx:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pair_ranks = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        hi_pair, lo_pair = pair_ranks[0], pair_ranks[1]

        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v39_idx = int(strategy_v39_dt(h))

        v39_class = classify_pick(h, feats, v39_idx, hi_pair, lo_pair)
        oracle_class = classify_pick(h, feats, oracle_idx, hi_pair, lo_pair)
        regret = float(rowf[oracle_idx]) - float(rowf[v39_idx])

        cell = cell_stats[(hi_pair, lo_pair)]
        cell["n"] += 1
        cell["sum_regret"] += regret
        cell["v39_class_dist"][v39_class] += 1
        cell["oracle_class_dist"][oracle_class] += 1
        if v39_class != oracle_class:
            cell["mismatch"][(v39_class, oracle_class)] += 1
            cell["mismatch_regret"][(v39_class, oracle_class)] += regret

        n_processed += 1
        if n_processed % 100000 == 0:
            rate = n_processed / (time.time() - t0)
            print(f"    progress {n_processed:>8,}/{len(t2p_idx):,}  rate={rate:.0f}/s",
                  flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    n_total_grid = 6_009_159

    # 1. Top cells
    print("=" * 110)
    print("TOP TWO_PAIR CELLS BY WHOLE-GRID REGRET CONTRIBUTION (v39_dt vs oracle)")
    print("=" * 110)
    cell_list = sorted(cell_stats.items(), key=lambda x: -x[1]["sum_regret"])
    print(f"  {'hi':>3} {'lo':>3} {'n':>7} {'mean_reg':>10} {'wg_contrib':>11}  "
          f"{'top mismatch':<37} {'mismatch_n':>10} {'mismatch_contrib':>16}")
    for (hi, lo), st in cell_list[:30]:
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
        print(f"  {RANK_CHAR[hi]:>3} {RANK_CHAR[lo]:>3} {st['n']:>7,} "
              f"${mean_reg:>+8.1f} ${wg:>+9.2f}  {top_label:<37} {top_n:>10,} ${top_wg:>+12.2f}")

    # 2. Aggregate mismatch
    print("\n" + "=" * 110)
    print("AGGREGATE MISMATCH MATRIX (across all two_pair cells)")
    print("=" * 110)
    agg_mismatch = defaultdict(lambda: {"n": 0, "regret": 0.0})
    for (hi, lo), st in cell_stats.items():
        for k, n in st["mismatch"].items():
            agg_mismatch[k]["n"] += n
            agg_mismatch[k]["regret"] += st["mismatch_regret"][k]

    ranked = sorted(agg_mismatch.items(), key=lambda x: -x[1]["regret"])
    print(f"  {'v39_pick':<18} {'oracle_pick':<18} {'n':>10} {'mean_reg':>10} {'wg_contrib':>12}")
    total_mismatch_contrib = 0.0
    for (vc, oc), st in ranked[:25]:
        if st["n"] == 0: continue
        mean_reg = st["regret"] / st["n"] * EV_TO_DOL * 1000
        wg = st["regret"] * EV_TO_DOL * 1000 / n_total_grid
        total_mismatch_contrib += wg
        print(f"  {vc:<18} {oc:<18} {st['n']:>10,} ${mean_reg:>+8.1f} ${wg:>+10.2f}")
    print(f"  Top-25 mismatch cumulative: ${total_mismatch_contrib:>+10.2f}/1000h")
    total_all_mismatch = sum(st["regret"] for st in agg_mismatch.values()) * EV_TO_DOL * 1000 / n_total_grid
    print(f"  ALL mismatches total contrib:  ${total_all_mismatch:>+10.2f}/1000h")

    # 3. Deep dive
    if ranked:
        top_k = ranked[0][0]
        top_v, top_o = top_k
        print(f"\n── DEEP DIVE: top mismatch  v39={top_v}  oracle={top_o} ──")
        cells_with_mismatch = [(hl, st["mismatch"][top_k], st["mismatch_regret"][top_k])
                                 for hl, st in cell_stats.items()
                                 if top_k in st["mismatch"]]
        cells_with_mismatch.sort(key=lambda x: -x[2])
        print(f"  Top (hi, lo) cells exhibiting this mismatch:")
        for (hi, lo), n, reg in cells_with_mismatch[:15]:
            mean_reg = reg / n * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / n_total_grid
            print(f"    hi={RANK_CHAR[hi]:>2} lo={RANK_CHAR[lo]:>2}: {n:>5,} hands "
                  f"mean=${mean_reg:>+8.1f}  wg=${wg:>+8.2f}")

    # 4. Class dist
    print("\n" + "=" * 110)
    print("OVERALL CLASS DISTRIBUTION (v39 picks vs oracle picks)")
    print("=" * 110)
    agg_v39 = Counter()
    agg_oracle = Counter()
    for (hi, lo), st in cell_stats.items():
        agg_v39.update(st["v39_class_dist"])
        agg_oracle.update(st["oracle_class_dist"])
    total = sum(agg_v39.values())
    all_classes = sorted(set(agg_v39.keys()) | set(agg_oracle.keys()))
    print(f"  {'class':<30} {'v39_n':>10} {'v39_pct':>10} {'oracle_n':>10} {'oracle_pct':>11} {'v39-oracle':>12}")
    for c in all_classes:
        vn = agg_v39[c]
        on = agg_oracle[c]
        vp = 100*vn/total if total else 0
        op = 100*on/total if total else 0
        diff = vp - op
        print(f"  {c:<30} {vn:>10,} {vp:>9.2f}% {on:>10,} {op:>10.2f}% {diff:>+11.2f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
