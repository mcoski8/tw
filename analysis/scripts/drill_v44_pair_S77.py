"""
Session 77 PHASE 2 — Pair-only setting-rank deep-drill on v44_dt.

WHY THIS DRILL
--------------
S76 cross-category setting-rank diagnostic identified PAIR as the highest-
leverage next feature/rule target:

  * pair contributes $511.16/1000h to v44's $1,081 full-grid leak (47%)
  * $116.04/1000h sits in the STRUCTURE bucket (rank ≥10 = closeable)
  * pair STR gap_2nd = 0.2109 is SHARPER than high_only STR (0.1063)
  * pair STR has NEVER been drilled with the setting-rank lens
  * 59,355 hands in pair STR bucket

S66's pair drill (drill_pair_v44_S66.py) introduced a 6-cell structural
cell taxonomy (PBOT_DS_JOINT / PBOT_DS_PARTIAL / PMID_DS_MAXTOP /
PMID_DS_NOMAXTOP / PMID_SS_MAXTOP / PMID_OTHER) and a `classify_pick_pair`
mismatch labeler. S71 introduced the setting-rank NOISE/MID/STRUCTURE
bucketing lens. NEITHER applied the OTHER's lens. This script is their
PRODUCT: pair structural cells × setting-rank buckets.

The combined lens partitions pair's $511.16/1000h leak into:
  * (pair_rank_tier × cell × bucket) WG decomposition
  * gap_2nd / plateau width by (cell × bucket)
  * top mismatch CLASSES (S66 labels) per (cell × bucket)
  * sample distribution of the 5-non-pair-card suitedness profile,
    n_broadway, n_low, kicker_max within each cell

OUTPUTS
-------
  data/drill_v44_pair_S77_summary.json
  data/session77/drill_v44_pair_S77.log

ACCEPTANCE per S77 plan:
  * Top 3-5 STRUCTURE-bucket cells identified, each with explicit n hands
    + WG + top mismatch class.
  * At least one feature hypothesis (H6) with expected within-cat lift
    ≥$30/1000h queued for S78 v48_dt retrain.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_pair_S77.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_pair_S77.py --sample 5000
"""
from __future__ import annotations

import argparse
import json
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402

# Reuse S66's validated pair structural functions.
from drill_pair_v44_S66 import (  # noqa: E402
    compute_pair_structural,
    cell_for_pair_hand,
    classify_pick_pair,
    CELLS_ORDER,
)
from strategy_v44_dt import strategy_v44_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
OUT_JSON = ROOT / "data" / "drill_v44_pair_S77_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_SETTINGS = 105
EPS_REL = 0.005  # 0.5% of |ev_best| for plateau width

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

BUCKETS_ORDER = ["MATCH", "NOISE", "MID", "STRUCTURE"]

# Pair-rank coarse tiers (3 buckets: low/mid/high broadway).
PAIR_RANK_TIERS = ["LOW", "MID", "HIGH"]
def pair_rank_tier(pair_rank: int) -> str:
    if pair_rank <= 7:
        return "LOW"          # 22..77
    if pair_rank <= 10:
        return "MID"          # 88..TT
    return "HIGH"             # JJ..AA


def rank_bucket(rank: int) -> str:
    if rank == 1:
        return "MATCH"
    if rank <= 3:
        return "NOISE"
    if rank <= 9:
        return "MID"
    return "STRUCTURE"


def suit_profile_5(suits_5: list[int]) -> str:
    """Suitedness pattern of the 5 non-pair cards (4-suit partition)."""
    cnt = sorted(Counter(suits_5).values(), reverse=True)
    if cnt == [5]:
        return "5f"
    if cnt[:2] == [4, 1]:
        return "4f"
    if cnt[:2] == [3, 2]:
        return "32"
    if cnt[:2] == [3, 1]:
        return "31"
    if cnt[:3] == [2, 2, 1]:
        return "DS"
    return "SS"  # 2+1+1+1


SUIT_PROFILE_5_ORDER = ["DS", "SS", "32", "31", "4f", "5f"]


def compute_hand_structural_minimal_pair(hand_bytes):
    """Per-S77 pair structural decomposition.

    Returns dict with:
      pair_rank, pair_rank_tier, cell (S66),
      max_sing_rank, max_sing_in_pair_suit (bool),
      n_PBOT_DS, n_PBOT_DS_w_msmid_maxtop,
      n_PMID_DS, n_PMID_DS_w_maxtop, n_PMID_SS_w_maxtop,
      best_PBOT_DS_mid_high, best_PMID_DS_bot_pair_high,
      non_pair_suit_profile (DS/SS/32/31/4f/5f over 5 non-pair cards),
      non_pair_n_broadway (count of T-A among 5 non-pair),
      non_pair_n_low (count of 2-5 among 5 non-pair),
      kicker_max_rank,
      kicker_max_in_pair_suit (bool),
      n_in_pair_suit_a, n_in_pair_suit_b  (kicker-suit alignment).
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    # Pair (rank with count == 2)
    rc = Counter(int_ranks)
    pair_rank = next(r for r, c in rc.items() if c == 2)
    pair_pos = [i for i in range(7) if int_ranks[i] == pair_rank]
    pair_suits = (int_suits[pair_pos[0]], int_suits[pair_pos[1]])
    sa, sb = pair_suits  # always distinct by deck construction

    # 5 non-pair cards
    sing_pos = [i for i in range(7) if i not in pair_pos]
    sing_ranks = [int_ranks[i] for i in sing_pos]
    sing_suits = [int_suits[i] for i in sing_pos]

    max_sing_rank = max(sing_ranks)
    max_sing_local = sing_ranks.index(max_sing_rank)
    max_sing_suit = sing_suits[max_sing_local]
    kicker_max_in_pair_suit = max_sing_suit in (sa, sb)

    # 5-card suitedness profile (suit partition pattern)
    np_suit_profile = suit_profile_5(sing_suits)

    np_n_broadway = sum(1 for r in sing_ranks if r >= 10)  # T-A
    np_n_low = sum(1 for r in sing_ranks if r <= 5)         # 2-5
    n_in_a = sum(1 for s in sing_suits if s == sa)
    n_in_b = sum(1 for s in sing_suits if s == sb)

    # Re-use S66 structural counts (validated in S66/S67).
    s66 = compute_pair_structural(hand_bytes)
    cell = cell_for_pair_hand(s66)

    return {
        "pair_rank": pair_rank,
        "pair_rank_tier": pair_rank_tier(pair_rank),
        "cell": cell,
        "max_sing_rank": max_sing_rank,
        "kicker_max_in_pair_suit": bool(kicker_max_in_pair_suit),
        "n_PBOT_DS": s66["n_PBOT_DS"],
        "n_PBOT_DS_w_msmid_maxtop": s66["n_PBOT_DS_w_msmid_maxtop"],
        "n_PMID_DS": s66["n_PMID_DS"],
        "n_PMID_DS_w_maxtop": s66["n_PMID_DS_w_maxtop"],
        "n_PMID_SS_w_maxtop": s66["n_PMID_SS_w_maxtop"],
        "best_PBOT_DS_mid_high": s66["best_PBOT_DS_mid_high"],
        "best_PMID_DS_bot_pair_high": s66["best_PMID_DS_bot_pair_high"],
        "non_pair_suit_profile": np_suit_profile,
        "non_pair_n_broadway": np_n_broadway,
        "non_pair_n_low": np_n_low,
        "kicker_max_rank": max_sing_rank,
        "n_in_pair_suit_a": n_in_a,
        "n_in_pair_suit_b": n_in_b,
        # Pass through pair-pos so caller can re-use struct in classify_pick_pair.
        "_s66": s66,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample pair hands to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 100)
    print("Session 77 PHASE 2 — Pair-only setting-rank deep-drill on v44_dt")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("Lens: (pair_rank_tier × S66 cell) × NOISE/MID/STRUCTURE setting-rank bucket.\n")

    print("[1/3] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    pair_idx = np.where(cats == 1)[0]
    n_pair = len(pair_idx)
    print(f"  pair hands: {n_pair:,}")

    if args.sample > 0 and n_pair > args.sample:
        rng = np.random.default_rng(args.seed)
        pair_idx = np.sort(rng.choice(pair_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {len(pair_idx):,}]")

    print("\n[2/3] loading oracle grid (memmap) ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    n = len(pair_idx)

    # Aggregations.
    # Primary cell key = (pair_rank_tier, cell)
    cell_stats = defaultdict(lambda: {
        "n": 0,
        "sum_regret": 0.0,
        "n_by_bucket": Counter(),
        "regret_by_bucket": defaultdict(float),
        "mismatch_by_bucket": defaultdict(Counter),
        "regret_by_mismatch_bucket": defaultdict(lambda: defaultdict(float)),
        "rank_histogram": Counter(),
        "gap_2nd_by_bucket": defaultdict(list),
        "gap_3rd_by_bucket": defaultdict(list),
        "n_within_eps_by_bucket": defaultdict(list),
        # Secondary axes — sample distributions per bucket (cap to 5000/bucket).
        "suit_profile_by_bucket": defaultdict(Counter),
        "n_broadway_by_bucket": defaultdict(Counter),
        "n_low_by_bucket": defaultdict(Counter),
        "kicker_max_by_bucket": defaultdict(Counter),
        "kicker_in_psuit_by_bucket": defaultdict(Counter),  # True/False
        # Track exact pair_rank distribution within tier×cell.
        "pair_rank_dist": Counter(),
    })

    # Per-tier rollup.
    tier_stats = defaultdict(lambda: {
        "n": 0, "sum_regret": 0.0,
        "n_by_bucket": Counter(),
        "regret_by_bucket": defaultdict(float),
    })

    # Per-cell rollup (across all pair_rank_tiers).
    cell_only_stats = defaultdict(lambda: {
        "n": 0, "sum_regret": 0.0,
        "n_by_bucket": Counter(),
        "regret_by_bucket": defaultdict(float),
    })

    print("\n[3/3] sweeping per-hand v44 vs oracle + structural decomposition ...",
          flush=True)
    t0 = time.time()
    last_log = t0
    for k, cid in enumerate(pair_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)

        # Setting-rank lens.
        sort_desc = np.argsort(-rowf)
        oracle_idx = int(sort_desc[0])
        ev_best = float(rowf[oracle_idx])
        ev_2nd = float(rowf[sort_desc[1]])
        ev_3rd = float(rowf[sort_desc[2]])
        v44_idx = int(strategy_v44_dt(h))
        ev_v44 = float(rowf[v44_idx])
        v44_rank = int((rowf > ev_v44).sum()) + 1
        regret = ev_best - ev_v44
        thresh = abs(ev_best) * EPS_REL
        n_within_eps = int((rowf >= ev_best - thresh).sum())

        # Structural decomposition.
        struct = compute_hand_structural_minimal_pair(h)
        tier = struct["pair_rank_tier"]
        cell = struct["cell"]
        bucket = rank_bucket(v44_rank)

        # Mismatch classification (use S66's classifier with same struct).
        if bucket != "MATCH":
            feats = setting_features_from_bytes(h)
            v44_det = classify_pick_pair(h, feats, v44_idx, struct["_s66"])
            or_det = classify_pick_pair(h, feats, oracle_idx, struct["_s66"])
            v44_class = v44_det["class_label"]
            or_class = or_det["class_label"]
        else:
            v44_class = None
            or_class = None

        # Accumulate.
        key = (tier, cell)
        st = cell_stats[key]
        st["n"] += 1
        st["sum_regret"] += regret
        st["n_by_bucket"][bucket] += 1
        st["regret_by_bucket"][bucket] += regret
        st["rank_histogram"][min(v44_rank, 20)] += 1
        st["pair_rank_dist"][struct["pair_rank"]] += 1
        st["suit_profile_by_bucket"][bucket][struct["non_pair_suit_profile"]] += 1
        st["n_broadway_by_bucket"][bucket][struct["non_pair_n_broadway"]] += 1
        st["n_low_by_bucket"][bucket][struct["non_pair_n_low"]] += 1
        st["kicker_max_by_bucket"][bucket][struct["kicker_max_rank"]] += 1
        st["kicker_in_psuit_by_bucket"][bucket][struct["kicker_max_in_pair_suit"]] += 1
        if bucket != "MATCH" and v44_class is not None:
            st["mismatch_by_bucket"][bucket][(v44_class, or_class)] += 1
            st["regret_by_mismatch_bucket"][bucket][(v44_class, or_class)] += regret
        if len(st["gap_2nd_by_bucket"][bucket]) < 5000:
            st["gap_2nd_by_bucket"][bucket].append(ev_best - ev_2nd)
        if len(st["gap_3rd_by_bucket"][bucket]) < 5000:
            st["gap_3rd_by_bucket"][bucket].append(ev_best - ev_3rd)
        if len(st["n_within_eps_by_bucket"][bucket]) < 5000:
            st["n_within_eps_by_bucket"][bucket].append(n_within_eps)

        ts = tier_stats[tier]
        ts["n"] += 1
        ts["sum_regret"] += regret
        ts["n_by_bucket"][bucket] += 1
        ts["regret_by_bucket"][bucket] += regret

        cs = cell_only_stats[cell]
        cs["n"] += 1
        cs["sum_regret"] += regret
        cs["n_by_bucket"][bucket] += 1
        cs["regret_by_bucket"][bucket] += regret

        now = time.time()
        if (k + 1) % 50_000 == 0 or now - last_log > 20:
            elapsed = now - t0
            rate = (k + 1) / elapsed if elapsed > 0 else 0
            eta = (n - k - 1) / rate if rate > 0 else 0
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)
            last_log = now

    wall = time.time() - t0
    print(f"  done in {wall:.1f}s ({wall/60:.1f} min)\n", flush=True)

    # ===========================================================
    # P_S77_OUT_1 — Cell × bucket WG decomposition (primary)
    # ===========================================================
    print("=" * 116)
    print("P_S77_OUT_1: SETTING-RANK BUCKET WG DECOMPOSITION (per pair_rank_tier × cell)")
    print("=" * 116)
    print(f"  {'tier':<6} {'cell':<18} {'n':>9} "
          f"{'MATCH%':>7} {'NOISE%':>7} {'MID%':>7} {'STR%':>7} "
          f"{'NOISE $':>9} {'MID $':>9} {'STR $':>9} {'TOTAL $':>9}")
    sorted_keys = sorted(
        cell_stats.keys(),
        key=lambda kk: (PAIR_RANK_TIERS.index(kk[0]), CELLS_ORDER.index(kk[1]))
    )
    for tier, cell in sorted_keys:
        st = cell_stats[(tier, cell)]
        nn = st["n"]
        if nn == 0:
            continue
        pcts = {b: 100 * st["n_by_bucket"].get(b, 0) / nn for b in BUCKETS_ORDER}
        wgs = {b: st["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
               for b in BUCKETS_ORDER}
        total_wg = st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"  {tier:<6} {cell:<18} {nn:>9,} "
              f"{pcts['MATCH']:>6.1f}% {pcts['NOISE']:>6.1f}% "
              f"{pcts['MID']:>6.1f}% {pcts['STRUCTURE']:>6.1f}% "
              f"${wgs['NOISE']:>+8.2f} ${wgs['MID']:>+8.2f} "
              f"${wgs['STRUCTURE']:>+8.2f} ${total_wg:>+8.2f}")

    print("\n  Per pair_rank_tier rollup:")
    print(f"    {'tier':<6} {'n':>9} {'MATCH%':>7} "
          f"{'NOISE $':>9} {'MID $':>9} {'STR $':>9} {'TOTAL $':>9}")
    for tier in PAIR_RANK_TIERS:
        ts = tier_stats.get(tier)
        if ts is None or ts["n"] == 0:
            continue
        nn = ts["n"]
        pct_match = 100 * ts["n_by_bucket"].get("MATCH", 0) / nn
        wgs = {b: ts["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
               for b in BUCKETS_ORDER}
        total_wg = ts["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"    {tier:<6} {nn:>9,} {pct_match:>6.1f}% "
              f"${wgs['NOISE']:>+8.2f} ${wgs['MID']:>+8.2f} "
              f"${wgs['STRUCTURE']:>+8.2f} ${total_wg:>+8.2f}")

    print("\n  Per cell rollup (across all pair_rank_tiers):")
    print(f"    {'cell':<18} {'n':>9} {'MATCH%':>7} "
          f"{'NOISE $':>9} {'MID $':>9} {'STR $':>9} {'TOTAL $':>9}")
    for cell in CELLS_ORDER:
        cs = cell_only_stats.get(cell)
        if cs is None or cs["n"] == 0:
            continue
        nn = cs["n"]
        pct_match = 100 * cs["n_by_bucket"].get("MATCH", 0) / nn
        wgs = {b: cs["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
               for b in BUCKETS_ORDER}
        total_wg = cs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
        print(f"    {cell:<18} {nn:>9,} {pct_match:>6.1f}% "
              f"${wgs['NOISE']:>+8.2f} ${wgs['MID']:>+8.2f} "
              f"${wgs['STRUCTURE']:>+8.2f} ${total_wg:>+8.2f}")

    grand_n = sum(ts["n"] for ts in tier_stats.values())
    grand_buckets_n = Counter()
    grand_buckets_wg = defaultdict(float)
    for ts in tier_stats.values():
        for b in BUCKETS_ORDER:
            grand_buckets_n[b] += ts["n_by_bucket"].get(b, 0)
            grand_buckets_wg[b] += (ts["regret_by_bucket"].get(b, 0.0)
                                     * EV_TO_DOL * 1000 / N_TOTAL_GRID)
    print("\n  GRAND TOTAL across all pair hands:")
    print(f"    {'bucket':<12} {'n':>10} {'pct':>7} {'wg $':>9}")
    total_wg_all = sum(grand_buckets_wg.values())
    for b in BUCKETS_ORDER:
        nc = grand_buckets_n[b]
        pct = 100 * nc / grand_n if grand_n else 0
        wg = grand_buckets_wg[b]
        pct_wg = 100 * wg / total_wg_all if total_wg_all else 0
        print(f"    {b:<12} {nc:>10,} {pct:>6.1f}% ${wg:>+8.2f}  ({pct_wg:>4.1f}% of WG)")
    print(f"    {'TOTAL':<12} {grand_n:>10,}        ${total_wg_all:>+8.2f}")

    # ===========================================================
    # P_S77_OUT_2 — Top STRUCTURE-bucket cells (the v45+ targets)
    # ===========================================================
    print("\n" + "=" * 116)
    print("P_S77_OUT_2: TOP STRUCTURE-BUCKET CELLS (sorted by STRUCTURE $/1000h)")
    print("=" * 116)
    cells_by_str_wg = []
    for (tier, cell), st in cell_stats.items():
        str_wg = st["regret_by_bucket"].get("STRUCTURE", 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        cells_by_str_wg.append(((tier, cell), st["n"], str_wg))
    cells_by_str_wg.sort(key=lambda x: -x[2])

    print(f"  {'rank':>4} {'tier':<6} {'cell':<18} {'n_cell':>9} "
          f"{'n_STR':>7} {'STR%':>6} {'STR $':>9} {'gap_2nd_med':>11} "
          f"{'plateau_med':>11}")
    for i, ((tier, cell), nn, str_wg) in enumerate(cells_by_str_wg[:15], 1):
        st = cell_stats[(tier, cell)]
        n_str = st["n_by_bucket"].get("STRUCTURE", 0)
        str_pct = 100 * n_str / nn if nn else 0
        gaps = st["gap_2nd_by_bucket"].get("STRUCTURE", [])
        gap_med = float(np.median(gaps)) if gaps else 0.0
        plateau = st["n_within_eps_by_bucket"].get("STRUCTURE", [])
        plateau_med = float(np.median(plateau)) if plateau else 0.0
        print(f"  {i:>4} {tier:<6} {cell:<18} {nn:>9,} "
              f"{n_str:>7,} {str_pct:>5.1f}% ${str_wg:>+8.2f} "
              f"{gap_med:>10.4f}  {plateau_med:>10.1f}")

    # ===========================================================
    # P_S77_OUT_3 — Top mismatch classes for top STR-bucket cells
    # ===========================================================
    print("\n" + "=" * 116)
    print("P_S77_OUT_3: TOP MISMATCH CLASSES PER (tier, cell, STRUCTURE bucket)")
    print("=" * 116)
    print("  Format: v44_pick -> oracle_pick    n=#  mean=$/hand  wg=$/1000h\n")
    for (tier, cell), nn, str_wg in cells_by_str_wg[:8]:
        st = cell_stats[(tier, cell)]
        mismatches = st["regret_by_mismatch_bucket"].get("STRUCTURE", {})
        if not mismatches:
            continue
        ranked = sorted(mismatches.items(), key=lambda x: -x[1])
        bucket_n = st["n_by_bucket"]["STRUCTURE"]
        print(f"  ── tier={tier} cell={cell}  n_STR={bucket_n:,} "
              f"wg=${str_wg:.2f} ──")
        for (vc, oc), reg in ranked[:6]:
            cnt = st["mismatch_by_bucket"]["STRUCTURE"][(vc, oc)]
            mean_reg = reg / cnt * EV_TO_DOL * 1000
            wg = reg * EV_TO_DOL * 1000 / N_TOTAL_GRID
            print(f"    {vc:<24} -> {oc:<24} n={cnt:>6,} "
                  f"mean=${mean_reg:>+7.0f} wg=${wg:>+6.2f}")
        print()

    # ===========================================================
    # P_S77_OUT_4 — Secondary axes: structural fingerprint per top cell
    # ===========================================================
    print("=" * 116)
    print("P_S77_OUT_4: STRUCTURAL FINGERPRINT PER TOP STR-BUCKET CELL")
    print("=" * 116)
    for (tier, cell), nn, str_wg in cells_by_str_wg[:6]:
        st = cell_stats[(tier, cell)]
        n_str = st["n_by_bucket"].get("STRUCTURE", 0)
        if n_str == 0:
            continue
        print(f"\n  ── tier={tier} cell={cell}  n_STR={n_str:,} wg=${str_wg:.2f} ──")
        sp = st["suit_profile_by_bucket"]["STRUCTURE"]
        nb = st["n_broadway_by_bucket"]["STRUCTURE"]
        nl = st["n_low_by_bucket"]["STRUCTURE"]
        km = st["kicker_max_by_bucket"]["STRUCTURE"]
        kp = st["kicker_in_psuit_by_bucket"]["STRUCTURE"]
        prd = st["pair_rank_dist"]

        total = sum(sp.values()) or 1
        print("    non_pair suit profile (5 non-pair cards):")
        for sprof in SUIT_PROFILE_5_ORDER:
            c = sp.get(sprof, 0)
            if c:
                print(f"      {sprof:<5} {c:>7,}  {100*c/total:>5.1f}%")
        print(f"    non_pair n_broadway (T-A count):")
        for nbr in range(6):
            c = nb.get(nbr, 0)
            if c:
                print(f"      ={nbr}    {c:>7,}  {100*c/total:>5.1f}%")
        print(f"    non_pair n_low (2-5 count):")
        for nlo in range(6):
            c = nl.get(nlo, 0)
            if c:
                print(f"      ={nlo}    {c:>7,}  {100*c/total:>5.1f}%")
        print(f"    kicker_max_rank (max non-pair rank):")
        for r in sorted(km.keys(), reverse=True):
            c = km[r]
            if c:
                print(f"      ={RANK_CHAR.get(r, r):>3}  {c:>7,}  {100*c/total:>5.1f}%")
        c_in = kp.get(True, 0)
        c_out = kp.get(False, 0)
        print(f"    kicker_max suit ∈ pair_suits:")
        print(f"      True   {c_in:>7,}  {100*c_in/total:>5.1f}%")
        print(f"      False  {c_out:>7,}  {100*c_out/total:>5.1f}%")
        # Exact pair ranks within this cell (whole-cell, not STR-only)
        n_cell = st["n"]
        print(f"    pair_rank distribution within (tier,cell), n={n_cell:,}:")
        for r in sorted(prd.keys(), reverse=True):
            c = prd[r]
            if c:
                print(f"      ={RANK_CHAR.get(r, r):>3}  {c:>7,}  {100*c/n_cell:>5.1f}%")

    # ===========================================================
    # P_S77_OUT_5 — gap_2nd / plateau width per bucket per top cell
    # ===========================================================
    print("\n" + "=" * 116)
    print("P_S77_OUT_5: EV-GAP STRUCTURE BY BUCKET (top 5 cells)")
    print("=" * 116)
    print("  gap_2nd = ev_best - ev_2nd  (sharpness of optimum)")
    print("  plateau = # of settings within 0.5% of ev_best.\n")
    for (tier, cell), nn, str_wg in cells_by_str_wg[:5]:
        st = cell_stats[(tier, cell)]
        print(f"  ── tier={tier} cell={cell}  n={nn:,} ──")
        for b in BUCKETS_ORDER:
            gaps = st["gap_2nd_by_bucket"].get(b, [])
            gaps3 = st["gap_3rd_by_bucket"].get(b, [])
            plats = st["n_within_eps_by_bucket"].get(b, [])
            if not gaps:
                continue
            print(f"    {b:<10} (sampled n={len(gaps):,})  "
                  f"gap_2nd mean={np.mean(gaps):.4f} med={np.median(gaps):.4f}   "
                  f"gap_3rd mean={np.mean(gaps3):.4f}   "
                  f"plateau med={np.median(plats):.2f}")

    # ===========================================================
    # Persistence
    # ===========================================================
    print(f"\n[writing summary JSON to {OUT_JSON}] ...", flush=True)
    summary = {
        "n_pair_hands_swept": int(n),
        "n_total_grid": N_TOTAL_GRID,
        "wall_seconds": float(wall),
        "pair_rank_tiers": PAIR_RANK_TIERS,
        "cells_order": list(CELLS_ORDER),
        "buckets_order": BUCKETS_ORDER,
        "suit_profile_5_order": SUIT_PROFILE_5_ORDER,
        "grand_buckets": {
            b: {"n": int(grand_buckets_n[b]),
                "wg": float(grand_buckets_wg[b])}
            for b in BUCKETS_ORDER
        },
        "grand_n": int(grand_n),
        "tier_stats": {},
        "cell_only_stats": {},
        "cell_stats": {},
        "top_str_cells": [
            {"tier": t, "cell": c, "n_cell": int(nn),
             "n_str": int(cell_stats[(t, c)]["n_by_bucket"].get("STRUCTURE", 0)),
             "str_wg_dollars": float(wg)}
            for (t, c), nn, wg in cells_by_str_wg[:15]
        ],
    }
    for tier, ts in tier_stats.items():
        summary["tier_stats"][tier] = {
            "n": int(ts["n"]),
            "total_wg": float(ts["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
            "n_by_bucket": {b: int(ts["n_by_bucket"].get(b, 0))
                            for b in BUCKETS_ORDER},
            "wg_by_bucket": {b: float(ts["regret_by_bucket"].get(b, 0.0)
                                       * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                              for b in BUCKETS_ORDER},
        }
    for cell, cs in cell_only_stats.items():
        summary["cell_only_stats"][cell] = {
            "n": int(cs["n"]),
            "total_wg": float(cs["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
            "n_by_bucket": {b: int(cs["n_by_bucket"].get(b, 0))
                            for b in BUCKETS_ORDER},
            "wg_by_bucket": {b: float(cs["regret_by_bucket"].get(b, 0.0)
                                       * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                              for b in BUCKETS_ORDER},
        }
    for (tier, cell), st in cell_stats.items():
        key = f"{tier}|{cell}"
        summary["cell_stats"][key] = {
            "n": int(st["n"]),
            "total_wg": float(st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
            "n_by_bucket": {b: int(st["n_by_bucket"].get(b, 0))
                            for b in BUCKETS_ORDER},
            "wg_by_bucket": {b: float(st["regret_by_bucket"].get(b, 0.0)
                                       * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                              for b in BUCKETS_ORDER},
            "rank_histogram": {str(r): int(c)
                               for r, c in st["rank_histogram"].items()},
            "pair_rank_dist": {str(r): int(c)
                               for r, c in st["pair_rank_dist"].items()},
            "gap_2nd_stats_by_bucket": {
                b: {
                    "n_sampled": int(len(st["gap_2nd_by_bucket"].get(b, []))),
                    "mean": float(np.mean(st["gap_2nd_by_bucket"][b]))
                            if st["gap_2nd_by_bucket"].get(b) else 0.0,
                    "median": float(np.median(st["gap_2nd_by_bucket"][b]))
                              if st["gap_2nd_by_bucket"].get(b) else 0.0,
                }
                for b in BUCKETS_ORDER
                if st["gap_2nd_by_bucket"].get(b)
            },
            "plateau_stats_by_bucket": {
                b: {
                    "mean": float(np.mean(st["n_within_eps_by_bucket"][b]))
                            if st["n_within_eps_by_bucket"].get(b) else 0.0,
                    "median": float(np.median(st["n_within_eps_by_bucket"][b]))
                              if st["n_within_eps_by_bucket"].get(b) else 0.0,
                }
                for b in BUCKETS_ORDER
                if st["n_within_eps_by_bucket"].get(b)
            },
            "top_mismatches_by_bucket": {
                b: [
                    {
                        "v44_class": vc,
                        "oracle_class": oc,
                        "n": int(st["mismatch_by_bucket"][b][(vc, oc)]),
                        "wg_dollars": float(reg * EV_TO_DOL * 1000 / N_TOTAL_GRID),
                        "mean_regret_dollars": float(
                            reg / st["mismatch_by_bucket"][b][(vc, oc)]
                            * EV_TO_DOL * 1000),
                    }
                    for (vc, oc), reg in sorted(
                        st["regret_by_mismatch_bucket"].get(b, {}).items(),
                        key=lambda x: -x[1])[:10]
                ]
                for b in ("STRUCTURE", "MID", "NOISE")
                if st["regret_by_mismatch_bucket"].get(b)
            },
            "suit_profile_dist_by_bucket": {
                b: {sp: int(c) for sp, c in d.items()}
                for b, d in st["suit_profile_by_bucket"].items()
            },
            "n_broadway_dist_by_bucket": {
                b: {str(k): int(c) for k, c in d.items()}
                for b, d in st["n_broadway_by_bucket"].items()
            },
            "n_low_dist_by_bucket": {
                b: {str(k): int(c) for k, c in d.items()}
                for b, d in st["n_low_by_bucket"].items()
            },
            "kicker_max_dist_by_bucket": {
                b: {str(k): int(c) for k, c in d.items()}
                for b, d in st["kicker_max_by_bucket"].items()
            },
            "kicker_in_psuit_dist_by_bucket": {
                b: {str(bool(k)): int(c) for k, c in d.items()}
                for b, d in st["kicker_in_psuit_by_bucket"].items()
            },
        }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  wrote summary JSON ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
