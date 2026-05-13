"""
Session 76 PHASE 2 — Category-agnostic setting-rank diagnostic across all 8
hand categories on v44_dt.

WHY THIS DRILL
--------------
S75 closed Option B (gradient boosting at moderate capacity) with a decisive
NULL. The entire single-model ML track is exhausted at v44's saturating
regime — but the four sessions of NULL/partial work were all on high_only's
H1-H5 hypothesis cascade. We have NOT applied the S71 setting-rank lens
(NOISE/MID/STRUCTURE bucketing) to the OTHER 7 categories.

The S71 lens partitions a category's residual WG into:
  - NOISE leak    (v44 rank 2-3): irreducible vs N=200 oracle noise
  - MID leak      (v44 rank 4-9): marginal feature-engineering potential
  - STRUCTURE leak (v44 rank ≥10): testable missing-signal hypothesis

For high_only S71 found ~$148/1000h of STRUCTURE leak; H1 captured $24
(~16%), H2 captured $0. ~$123 remained closeable in axes not surfaced by
H1-H5.

This drill asks the same question for the other 7 categories:
  * Where does the closeable structure-leak signal live?
  * Are some categories noise-ceiling-limited (Option A territory) while
    others have closeable structure leak (Option D territory)?
  * Do the rule-chain-shipped categories (trips via v56, two_pair via v55)
    still have residual STRUCTURE leak that a v57 rule could attack?

OUTPUT
------
A per-category table of:
  * n hands
  * MATCH / NOISE / MID / STRUCTURE bucket distribution (count and %)
  * $/1000h WG by bucket
  * mean & median gap_2nd (sharpness of optimum) per bucket
  * n_within_eps mean (plateau width) per bucket

A summary JSON at data/drill_v44_setting_rank_all_cats_S76_summary.json.

NO category-specific structural cell taxonomy is computed — that is the
follow-up drill for whichever category shows the highest STRUCTURE-bucket
signal.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_setting_rank_all_cats_S76.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_setting_rank_all_cats_S76.py --sample 100000
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_setting_rank_all_cats_S76.py --categories 1,5,7   # pair / three_pair / composite only
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
from tw_analysis.grade_strategy import categorize_hands, CATEGORY_NAMES  # noqa: E402
from strategy_v44_dt import strategy_v44_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
OUT_JSON = ROOT / "data" / "drill_v44_setting_rank_all_cats_S76_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
N_SETTINGS = 105

BUCKETS_ORDER = ["MATCH", "NOISE", "MID", "STRUCTURE"]
EPS_REL = 0.005  # 0.5% of |ev_best| for plateau width


def rank_bucket(rank: int) -> str:
    if rank == 1:
        return "MATCH"
    if rank <= 3:
        return "NOISE"
    if rank <= 9:
        return "MID"
    return "STRUCTURE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, sub-sample hands per-category to speed up debugging.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--categories", type=str, default="",
                    help="Comma-separated category codes to include (default: all 0-7).")
    args = ap.parse_args()

    print("=" * 100)
    print("Session 76 PHASE 2 — Setting-rank diagnostic ACROSS ALL CATEGORIES on v44_dt")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("Lens: NOISE (rank 2-3) / MID (rank 4-9) / STRUCTURE (rank >=10) per category.")
    print("Goal: identify where closeable structure-leak signal lives outside high_only.\n")

    selected_cats = None
    if args.categories:
        selected_cats = set(int(x) for x in args.categories.split(",") if x.strip())
        print(f"  Restricting to category codes: {sorted(selected_cats)}")
        print(f"  Names: {[CATEGORY_NAMES[c] for c in sorted(selected_cats)]}\n")

    print("[1/3] loading canonical hands + categorizing...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(cats)
    print(f"  hands: {n_total:,}")
    per_cat_counts = Counter(int(c) for c in cats)
    for code in range(8):
        if selected_cats is not None and code not in selected_cats:
            continue
        print(f"    cat {code} {CATEGORY_NAMES[code]:<12} n={per_cat_counts.get(code, 0):,}")

    # Per-category index lists
    cat_idx_lists: dict[int, np.ndarray] = {}
    for code in range(8):
        if selected_cats is not None and code not in selected_cats:
            continue
        idx = np.where(cats == code)[0]
        if args.sample > 0 and len(idx) > args.sample:
            rng = np.random.default_rng(args.seed + code)
            idx = np.sort(rng.choice(idx, size=args.sample, replace=False))
            print(f"    [sample mode for cat {code}: {args.sample:,}]")
        cat_idx_lists[code] = idx

    all_idx = np.sort(np.concatenate(list(cat_idx_lists.values())))
    print(f"\n  total hands to sweep: {len(all_idx):,}")

    print("\n[2/3] loading oracle grid (memmap)...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    # Aggregations
    cat_stats: dict[int, dict] = {}
    for code in cat_idx_lists:
        cat_stats[code] = {
            "n": 0,
            "sum_regret": 0.0,
            "n_by_bucket": Counter(),
            "regret_by_bucket": defaultdict(float),
            "rank_histogram": Counter(),
            "gap_2nd_by_bucket": defaultdict(list),
            "gap_3rd_by_bucket": defaultdict(list),
            "n_within_eps_by_bucket": defaultdict(list),
            "max_samples_per_bucket": 5000,
        }

    print("\n[3/3] sweeping per-hand v44 vs oracle ...", flush=True)
    t0 = time.time()
    n_done = 0
    n_total_sweep = len(all_idx)

    for cid_int in all_idx:
        cid = int(cid_int)
        code = int(cats[cid])
        st = cat_stats[code]
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
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
        bucket = rank_bucket(v44_rank)

        st["n"] += 1
        st["sum_regret"] += regret
        st["n_by_bucket"][bucket] += 1
        st["regret_by_bucket"][bucket] += regret
        st["rank_histogram"][min(v44_rank, 20)] += 1
        max_s = st["max_samples_per_bucket"]
        if len(st["gap_2nd_by_bucket"][bucket]) < max_s:
            st["gap_2nd_by_bucket"][bucket].append(ev_best - ev_2nd)
            st["gap_3rd_by_bucket"][bucket].append(ev_best - ev_3rd)
            st["n_within_eps_by_bucket"][bucket].append(n_within_eps)

        n_done += 1
        if n_done % 200_000 == 0:
            elapsed = time.time() - t0
            rate = n_done / elapsed
            eta = (n_total_sweep - n_done) / rate
            print(f"    progress {n_done:>8,}/{n_total_sweep:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # =================================================================
    # OUTPUT 1: Per-category bucket distribution + WG breakdown
    # =================================================================
    print("=" * 110)
    print("S76_OUT_1: PER-CATEGORY NOISE/MID/STRUCTURE BUCKET DISTRIBUTION + WG")
    print("=" * 110)
    print("  WG normalized to $/1000h share of FULL grid (6,009,159 hands).")
    print("  bucket_$/1000h = sum(regret_in_bucket) * 10 * 1000 / 6_009_159 .\n")

    print(f"  {'cat':<12} {'n':>10} {'MATCH%':>7} {'NOISE%':>7} {'MID%':>7} {'STR%':>7} "
          f"{'NOISE $':>9} {'MID $':>9} {'STR $':>9} {'TOTAL $':>9} {'STR/TOT':>8}")

    per_cat_totwg = {}
    for code in sorted(cat_stats):
        st = cat_stats[code]
        nn = st["n"]
        if nn == 0:
            continue
        pcts = {b: 100 * st["n_by_bucket"].get(b, 0) / nn for b in BUCKETS_ORDER}
        wgs = {b: st["regret_by_bucket"].get(b, 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
               for b in BUCKETS_ORDER}
        total_wg = sum(wgs.values())
        str_share = 100 * wgs["STRUCTURE"] / total_wg if total_wg > 0 else 0.0
        per_cat_totwg[code] = total_wg
        print(f"  {CATEGORY_NAMES[code]:<12} {nn:>10,} {pcts['MATCH']:>6.1f}% "
              f"{pcts['NOISE']:>6.1f}% {pcts['MID']:>6.1f}% {pcts['STRUCTURE']:>6.1f}% "
              f"${wgs['NOISE']:>+8.2f} ${wgs['MID']:>+8.2f} ${wgs['STRUCTURE']:>+8.2f} "
              f"${total_wg:>+8.2f} {str_share:>6.1f}%")

    # =================================================================
    # OUTPUT 2: Per-bucket gap_2nd + plateau-width stats per category
    # =================================================================
    print("\n" + "=" * 110)
    print("S76_OUT_2: GAP_2ND (sharpness of optimum) + PLATEAU WIDTH PER CATEGORY × BUCKET")
    print("=" * 110)
    print("  Sharp optimum + STRUCTURE bucket = strong closeable-leak signature.")
    print("  Flat optimum (gap_2nd ~ 0) + NOISE bucket = irreducible label noise.\n")

    for code in sorted(cat_stats):
        st = cat_stats[code]
        nn = st["n"]
        if nn == 0:
            continue
        print(f"\n  ── cat {code} {CATEGORY_NAMES[code]}  n={nn:,} ──")
        print(f"    {'bucket':<10} {'n_in_bucket':>12} {'sampled':>9} "
              f"{'gap2_mean':>11} {'gap2_med':>10} {'gap3_mean':>10} "
              f"{'plateau_mean':>13}")
        for b in BUCKETS_ORDER:
            n_b = st["n_by_bucket"].get(b, 0)
            if n_b == 0:
                continue
            gaps2 = st["gap_2nd_by_bucket"].get(b, [])
            gaps3 = st["gap_3rd_by_bucket"].get(b, [])
            plateaus = st["n_within_eps_by_bucket"].get(b, [])
            if not gaps2:
                continue
            print(f"    {b:<10} {n_b:>12,} {len(gaps2):>9,} "
                  f"{float(np.mean(gaps2)):>11.4f} {float(np.median(gaps2)):>10.4f} "
                  f"{float(np.mean(gaps3)):>10.4f} {float(np.mean(plateaus)):>13.2f}")

    # =================================================================
    # OUTPUT 3: Rank histogram per category (top 20 ranks)
    # =================================================================
    print("\n" + "=" * 110)
    print("S76_OUT_3: V44 SETTING-RANK HISTOGRAM PER CATEGORY (rank 1..20, cumulative %)")
    print("=" * 110)
    for code in sorted(cat_stats):
        st = cat_stats[code]
        nn = st["n"]
        if nn == 0:
            continue
        print(f"\n  ── cat {code} {CATEGORY_NAMES[code]}  n={nn:,} ──")
        print(f"    {'rank':>5} {'count':>10} {'pct':>7} {'cum %':>7}")
        cum = 0.0
        for r in range(1, 21):
            c = st["rank_histogram"].get(r, 0)
            pct = 100 * c / nn
            cum += pct
            label = "≥20" if r == 20 else str(r)
            print(f"    {label:>5} {c:>10,} {pct:>6.2f}% {cum:>6.2f}%")

    # =================================================================
    # OUTPUT 4: Cross-category ranking + recommendations
    # =================================================================
    print("\n" + "=" * 110)
    print("S76_OUT_4: CROSS-CATEGORY STRUCTURE-LEAK RANKING (where to drill next)")
    print("=" * 110)
    rows = []
    for code, st in cat_stats.items():
        nn = st["n"]
        if nn == 0:
            continue
        wg_str = st["regret_by_bucket"].get("STRUCTURE", 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        wg_noise = st["regret_by_bucket"].get("NOISE", 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        wg_mid = st["regret_by_bucket"].get("MID", 0.0) * EV_TO_DOL * 1000 / N_TOTAL_GRID
        wg_tot = wg_str + wg_noise + wg_mid
        rows.append({
            "code": code,
            "name": CATEGORY_NAMES[code],
            "n": nn,
            "wg_str": wg_str,
            "wg_noise": wg_noise,
            "wg_mid": wg_mid,
            "wg_tot": wg_tot,
            "str_share": (wg_str / wg_tot * 100) if wg_tot > 0 else 0.0,
        })

    rows_by_str = sorted(rows, key=lambda r: -r["wg_str"])
    print("\n  Ranked by STRUCTURE-bucket $/1000h (highest = best Option D candidate):")
    print(f"  {'rank':>4} {'cat':<12} {'STR $':>9} {'NOISE $':>9} {'MID $':>9} {'TOT $':>9} {'STR/TOT':>8}")
    for i, r in enumerate(rows_by_str, 1):
        print(f"  {i:>4} {r['name']:<12} ${r['wg_str']:>+8.2f} ${r['wg_noise']:>+8.2f} "
              f"${r['wg_mid']:>+8.2f} ${r['wg_tot']:>+8.2f} {r['str_share']:>6.1f}%")

    rows_by_noise = sorted(rows, key=lambda r: -r["wg_noise"])
    print("\n  Ranked by NOISE-bucket $/1000h (highest = best Option A candidate):")
    print(f"  {'rank':>4} {'cat':<12} {'NOISE $':>9} {'STR $':>9} {'TOT $':>9} {'NOISE/TOT':>10}")
    for i, r in enumerate(rows_by_noise, 1):
        noise_share = (r["wg_noise"] / r["wg_tot"] * 100) if r["wg_tot"] > 0 else 0.0
        print(f"  {i:>4} {r['name']:<12} ${r['wg_noise']:>+8.2f} ${r['wg_str']:>+8.2f} "
              f"${r['wg_tot']:>+8.2f} {noise_share:>8.1f}%")

    # =================================================================
    # Persistence
    # =================================================================
    summary = {
        "session": 76,
        "n_hands_swept": int(n_done),
        "n_total_grid": N_TOTAL_GRID,
        "eps_rel": EPS_REL,
        "categories": {},
        "ranking": {
            "by_structure_wg": [{"code": r["code"], "name": r["name"],
                                 "wg_str": float(r["wg_str"]),
                                 "wg_noise": float(r["wg_noise"]),
                                 "wg_mid": float(r["wg_mid"]),
                                 "wg_tot": float(r["wg_tot"]),
                                 "str_share_pct": float(r["str_share"])}
                                for r in rows_by_str],
            "by_noise_wg": [{"code": r["code"], "name": r["name"],
                             "wg_noise": float(r["wg_noise"]),
                             "wg_str": float(r["wg_str"]),
                             "wg_tot": float(r["wg_tot"])}
                            for r in rows_by_noise],
        },
    }
    for code, st in cat_stats.items():
        nn = st["n"]
        if nn == 0:
            continue
        summary["categories"][str(code)] = {
            "name": CATEGORY_NAMES[code],
            "n": int(nn),
            "sum_regret": float(st["sum_regret"]),
            "total_wg": float(st["sum_regret"] * EV_TO_DOL * 1000 / N_TOTAL_GRID),
            "n_by_bucket": {b: int(st["n_by_bucket"].get(b, 0)) for b in BUCKETS_ORDER},
            "wg_by_bucket": {b: float(st["regret_by_bucket"].get(b, 0.0)
                                       * EV_TO_DOL * 1000 / N_TOTAL_GRID)
                             for b in BUCKETS_ORDER},
            "rank_histogram": {str(r): int(c) for r, c in st["rank_histogram"].items()},
            "gap_2nd_stats_by_bucket": {
                b: {
                    "n_sampled": int(len(st["gap_2nd_by_bucket"].get(b, []))),
                    "mean": float(np.mean(st["gap_2nd_by_bucket"][b]))
                            if st["gap_2nd_by_bucket"].get(b) else 0.0,
                    "median": float(np.median(st["gap_2nd_by_bucket"][b]))
                              if st["gap_2nd_by_bucket"].get(b) else 0.0,
                }
                for b in BUCKETS_ORDER if st["gap_2nd_by_bucket"].get(b)
            },
            "plateau_mean_by_bucket": {
                b: float(np.mean(st["n_within_eps_by_bucket"][b]))
                for b in BUCKETS_ORDER if st["n_within_eps_by_bucket"].get(b)
            },
        }

    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  wrote summary JSON to {OUT_JSON} ({OUT_JSON.stat().st_size / 1024:.1f} KB)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
