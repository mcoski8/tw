"""
Session 45 — Drill B: J-low two_pair DS-bot vs both-pairs-intact (within-hand).

Question (from S44 closure): two_pair was declared "ML territory" twice
(S42 overnight + S43 Q4). The S44 suit-dominance finding (DS-scattered ≥
all non-DS within-hand in J-low no-pair) raises a fresh question: does
DS-bot beat keeping both pairs intact in two_pair, even at the cost of
breaking one or both pairs?

Population: cat=two_pair (n_pairs=2, no trip/quad), max_rank ≤ J. Both
pairs are J-or-lower. Hand has 7 cards = 2+2+1+1+1 (two pairs HH+LL +
3 singletons).

Within-hand pairwise classes. Each hand has two pairs (HH = high pair,
LL = low pair). For each setting, classify by where each pair sits:

  pair_state of {HH, LL}:
    'mid' = both members of that pair are in mid (mid_is_pair == True for
            that rank)
    'bot' = both members of that pair are in bot (bot has that rank twice)
    'split' = pair members in different positions

  Aggregate pair_state into a 4-bin partition:
    BOTH_INTACT      both pairs intact (each is mid OR bot)
    SPLIT_LOW        HH intact, LL split
    SPLIT_HIGH       LL intact, HH split
    BOTH_SPLIT       both pairs split

  Cross with bot suit (DS / non-DS) → 8 classes:

    B1  BOTH_INTACT + DS-bot
    B2  BOTH_INTACT + non-DS-bot
    B3  SPLIT_LOW + DS-bot       (kept HH, broke LL for DS)
    B4  SPLIT_LOW + non-DS-bot
    B5  SPLIT_HIGH + DS-bot      (kept LL, broke HH for DS — unusual)
    B6  SPLIT_HIGH + non-DS-bot
    B7  BOTH_SPLIT + DS-bot      (sacrificed both for DS)
    B8  BOTH_SPLIT + non-DS-bot

Headline pairwise comparisons (within-hand):
  B3 - B2 : split LL for DS vs both-pairs-intact non-DS  (cheapest pair-break)
  B5 - B2 : split HH for DS vs both-pairs-intact non-DS  (more expensive)
  B7 - B2 : split BOTH for DS vs both-pairs-intact non-DS (most expensive)
  B1 - B2 : DS premium WITHIN both-pairs-intact (suit-aware bot when both
            pairs stay together — analogue of A1-A2 in Drill A)
  B3 - B1 : split LL for DS vs both-intact + DS  (does breaking LL ever
            beat a both-intact DS-achievable case?)

Validation: full grid (N=200) + prefix grid (N=1000).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_J_low_two_pair_DS_break.py
"""
from __future__ import annotations

import argparse
import sys
import time
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
    SUIT_PROFILE_DS,
)

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}

# Pair-state code per (pair, position):
#   0 = mid,  1 = bot,  2 = split
# Aggregate (HH_state, LL_state) → 4-bin:
#   BOTH_INTACT (0)  : HH ∈ {mid,bot} AND LL ∈ {mid,bot}
#   SPLIT_LOW   (1)  : HH intact, LL split
#   SPLIT_HIGH  (2)  : LL intact, HH split
#   BOTH_SPLIT  (3)
N_CLASSES = 8
CLASS_LABELS = {
    0: "B1 both-intact + DS",
    1: "B2 both-intact + non-DS",
    2: "B3 split-LL + DS",
    3: "B4 split-LL + non-DS",
    4: "B5 split-HH + DS",
    5: "B6 split-HH + non-DS",
    6: "B7 both-split + DS",
    7: "B8 both-split + non-DS",
}


def classify_settings(hand_bytes: np.ndarray, P_hi: int, P_lo: int) -> np.ndarray:
    """Per-setting class index (105,), int8, -1 for invalid (shouldn't happen
    for cat=two_pair).
    """
    feats = setting_features_from_bytes(hand_bytes)
    permuted = hand_bytes[SETTING_HAND_INDICES]  # (105, 7)
    # Position counts of each pair-rank in {top, mid, bot}
    bot_bytes = permuted[:, 3:]  # (105, 4)
    bot_ranks = (bot_bytes // 4 + 2).astype(np.int8)
    mid_bytes = permuted[:, 1:3]  # (105, 2)
    mid_ranks = (mid_bytes // 4 + 2).astype(np.int8)
    top_byte = permuted[:, 0:1]
    top_rank = (top_byte // 4 + 2).astype(np.int8)  # (105, 1)

    def pair_state(P):
        # State per pair P: 0=mid (both in mid), 1=bot (both in bot), 2=split
        n_in_mid = (mid_ranks == P).sum(axis=1)  # (105,)
        n_in_bot = (bot_ranks == P).sum(axis=1)
        st = np.full(105, 2, dtype=np.int8)  # default split
        st[n_in_mid == 2] = 0
        st[n_in_bot == 2] = 1
        return st

    hh_state = pair_state(P_hi)
    ll_state = pair_state(P_lo)

    # Aggregate into 4-bin
    intact_hh = hh_state != 2
    intact_ll = ll_state != 2
    agg = np.where(intact_hh & intact_ll, 0,
            np.where(intact_hh & ~intact_ll, 1,
              np.where(~intact_hh & intact_ll, 2, 3))).astype(np.int8)

    is_ds = feats.bot_suit_profile == SUIT_PROFILE_DS

    classes = np.full(105, -1, dtype=np.int8)
    classes[(agg == 0) & is_ds] = 0
    classes[(agg == 0) & ~is_ds] = 1
    classes[(agg == 1) & is_ds] = 2
    classes[(agg == 1) & ~is_ds] = 3
    classes[(agg == 2) & is_ds] = 4
    classes[(agg == 2) & ~is_ds] = 5
    classes[(agg == 3) & is_ds] = 6
    classes[(agg == 3) & ~is_ds] = 7
    return classes


def fmt_dollar(x):
    if np.isnan(x):
        return "       n/a"
    return f"${x:>+9.1f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 45 Drill B: J-low two_pair DS-bot vs both-pairs-intact")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    tp_idx = np.where(cats == 2)[0]
    print(f"  total hands: {n_total:,}")
    print(f"  cat=two_pair: {len(tp_idx):,}")

    print("\n[2/4] filtering to J-low two_pair (max_r ≤ 11) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    p_hi = []
    p_lo = []
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) > 11:
            continue
        rc = np.bincount(ranks, minlength=15)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        if len(pairs) != 2:
            continue
        scope_cids.append(int(cid))
        p_hi.append(pairs[0])
        p_lo.append(pairs[1])
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    p_hi = np.asarray(p_hi, dtype=np.int8)
    p_lo = np.asarray(p_lo, dtype=np.int8)
    print(f"  J-low two_pair scope: {len(scope_cids):,}")
    print(f"  P_hi distribution:")
    for P in range(3, 12):
        n = (p_hi == P).sum()
        if n > 0:
            print(f"    P_hi={RANK_CHAR[P]}: {n:>6,}  ({100*n/len(scope_cids):>5.2f}%)")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        keep = []
        unique_pairs = sorted(set(zip(p_hi.tolist(), p_lo.tolist())))
        for (PH, PL) in unique_pairs:
            mask = (p_hi == PH) & (p_lo == PL)
            idx = np.where(mask)[0]
            if len(idx) > args.sample:
                idx = rng.choice(idx, size=args.sample, replace=False)
            keep.extend(idx.tolist())
        keep = np.asarray(sorted(keep))
        scope_cids = scope_cids[keep]
        p_hi = p_hi[keep]
        p_lo = p_lo[keep]
        print(f"  [sample mode: capped each (P_hi, P_lo) cell at {args.sample}; "
              f"total={len(scope_cids):,}]")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    sum_lift_full = np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)
    n_pairs_full = np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)
    n_ach_full = np.zeros(N_CLASSES, dtype=np.int64)
    n_hands_full = 0
    sum_lift_pref = np.zeros((N_CLASSES, N_CLASSES), dtype=np.float64)
    n_pairs_pref = np.zeros((N_CLASSES, N_CLASSES), dtype=np.int64)
    n_ach_pref = np.zeros(N_CLASSES, dtype=np.int64)
    n_hands_pref = 0

    print("\n[4/4] per-hand within-hand pairwise enumeration ...", flush=True)
    t0 = time.time()
    n_total_scope = len(scope_cids)
    for i in range(n_total_scope):
        cid = int(scope_cids[i])
        PH = int(p_hi[i])
        PL = int(p_lo[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        classes = classify_settings(h, PH, PL)

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        best_full = np.full(N_CLASSES, np.nan, dtype=np.float64)
        for k in range(N_CLASSES):
            mask = classes == k
            if mask.any():
                best_full[k] = float(rowf[mask].max())
        avail = ~np.isnan(best_full)
        if avail.sum() >= 2:
            diff = best_full[:, None] - best_full[None, :]
            both = avail[:, None] & avail[None, :]
            sum_lift_full += np.where(both, diff, 0.0)
            n_pairs_full += both.astype(np.int64)
        n_ach_full += avail.astype(np.int64)
        n_hands_full += 1

        if cid < 500_000:
            rowp = np.asarray(gp.evs[cid], dtype=np.float64)
            best_pref = np.full(N_CLASSES, np.nan, dtype=np.float64)
            for k in range(N_CLASSES):
                mask = classes == k
                if mask.any():
                    best_pref[k] = float(rowp[mask].max())
            avail_p = ~np.isnan(best_pref)
            if avail_p.sum() >= 2:
                diff_p = best_pref[:, None] - best_pref[None, :]
                both_p = avail_p[:, None] & avail_p[None, :]
                sum_lift_pref += np.where(both_p, diff_p, 0.0)
                n_pairs_pref += both_p.astype(np.int64)
            n_ach_pref += avail_p.astype(np.int64)
            n_hands_pref += 1

        if (i + 1) % 5000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total_scope:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    def report(label, n_h, sum_lift, n_pairs, n_ach):
        print("=" * 100)
        print(f"AGGREGATE: {label}  (n_hands={n_h:,})")
        print("=" * 100)
        if n_h == 0:
            print("  (no hands)\n")
            return

        print(f"\n── ACHIEVABILITY (% of hands where class achievable) ──")
        for k in range(N_CLASSES):
            pct = 100 * n_ach[k] / n_h
            print(f"  {CLASS_LABELS[k]:<28}  {n_ach[k]:>7,}  ({pct:>5.1f}%)")

        print(f"\n── PAIRWISE LIFT MATRIX  EV(row) − EV(col) in $/1000h ──")
        with np.errstate(invalid="ignore", divide="ignore"):
            lift = sum_lift / np.where(n_pairs > 0, n_pairs, 1)
        lift_dol = lift * EV_TO_DOL * 1000
        print(f"  {'row\\col':<28}  " + "  ".join(
            f"{f'B{j+1}':>10}" for j in range(N_CLASSES)))
        for i in range(N_CLASSES):
            row_str = f"  {CLASS_LABELS[i]:<28}  "
            for j in range(N_CLASSES):
                if i == j or n_pairs[i, j] == 0:
                    row_str += f"  {'─':>10}"
                else:
                    row_str += f"  {lift_dol[i, j]:>+10.1f}"
            print(row_str)

        print(f"\n── HEADLINE COMPARISONS (within-hand, $/1000h lift = row−col) ──")
        headline = [
            (2, 1, "B3 − B2: split-LL for DS  vs both-intact non-DS  (cheap break)"),
            (4, 1, "B5 − B2: split-HH for DS  vs both-intact non-DS  (expensive break)"),
            (6, 1, "B7 − B2: both-split for DS vs both-intact non-DS  (most expensive)"),
            (0, 1, "B1 − B2: DS premium WITHIN both-intact (suit-aware bot)"),
            (2, 0, "B3 − B1: split-LL DS  vs both-intact DS"),
            (4, 0, "B5 − B1: split-HH DS  vs both-intact DS"),
            (2, 3, "B3 − B4: DS premium WITHIN split-LL"),
            (4, 5, "B5 − B6: DS premium WITHIN split-HH"),
            (6, 7, "B7 − B8: DS premium WITHIN both-split"),
            (3, 1, "B4 − B2: split-LL non-DS vs both-intact non-DS (pair-break cost only)"),
            (5, 1, "B6 − B2: split-HH non-DS vs both-intact non-DS"),
        ]
        for i, j, label in headline:
            n = n_pairs[i, j]
            if n == 0:
                print(f"  {label}: n=0 (no co-achievable hands)")
                continue
            lf = sum_lift[i, j] / n * EV_TO_DOL * 1000
            verdict = "row wins" if lf > 0 else "col wins"
            print(f"  {label}")
            print(f"    n_co-achievable = {n:>7,}  |  lift = ${lf:>+9.1f}/1000h  ({verdict})")

    report("FULL GRID  (N=200)", n_hands_full, sum_lift_full, n_pairs_full, n_ach_full)
    print()
    report("PREFIX GRID (N=1000)", n_hands_pref, sum_lift_pref, n_pairs_pref, n_ach_pref)

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
