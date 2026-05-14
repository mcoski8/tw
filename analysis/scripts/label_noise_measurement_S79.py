#!/usr/bin/env python3
"""Session 79 — Label-noise measurement on the existing 500K N=1000 prefix
grid vs the same 500K hands labeled at N=200 in the full grid.

For each of the first 500K canonical hands:
    v44_pick    = strategy_v44_dt(hand)
    n200_pick   = argmax of full_evs[i]       (N=200 labels)
    n1000_pick  = argmax of prefix_evs[i]     (N=1000 labels)
    n200_match  = (v44_pick == n200_pick)
    n1000_match = (v44_pick == n1000_pick)

The match-rate shift (n1000_match - n200_match) is the load-bearing metric.
If labels are noisy and v44 is "actually correct" more often than the N=200
labels say, the N=1000 labels should agree with v44 more often, shifting
match rate up. If labels are stable, the shift should be near zero and the
65 vs 95 gap is real model error.

Aggregations:
  - Overall pct(n200_match), pct(n1000_match), shift
  - By v44_rank_n200 bucket (S76 lens: MATCH / NOISE / MID / STRUCTURE)
  - By hand category (high_only, pair, two_pair, trips, trips_pair,
    three_pair, quads, composite)

Output: data/label_noise_S79_summary.json

Usage:
    PYTHONUNBUFFERED=1 python3 -u analysis/scripts/label_noise_measurement_S79.py
    PYTHONUNBUFFERED=1 python3 -u analysis/scripts/label_noise_measurement_S79.py --sample 50000
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
sys.path.insert(0, str(ROOT / "analysis" / "src"))
sys.path.insert(0, str(ROOT / "analysis" / "scripts"))

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.grade_strategy import CATEGORY_NAMES, categorize_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from strategy_v44_dt import strategy_v44_dt  # noqa: E402

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
OUT_JSON = ROOT / "data" / "label_noise_S79_summary.json"

EV_TO_DOLLARS = 10.0  # match grade_v44_dt's convention (mean_regret * 10 * 1000 = $/1000h)

BUCKETS_ORDER = ["MATCH", "NOISE", "MID", "STRUCTURE"]


def rank_bucket(rank: int) -> str:
    """S76 convention. rank==1 means v44 == oracle argmax."""
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
                    help="If >0, sub-sample N prefix hands (uniform random) for fast iteration.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--progress-every", type=int, default=50_000)
    args = ap.parse_args()

    print("=" * 100)
    print("Session 79 — Label-noise measurement (N=200 vs N=1000 on shared 500K prefix)")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading prefix N=1000 grid (memmap)...", flush=True)
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    n_prefix = len(gp)
    print(f"  prefix grid: n_records={n_prefix:,}, samples={gp.header.samples}, "
          f"opp={gp.header.opp_label}", flush=True)

    print("\n[2/4] loading full N=200 grid (memmap, first {n_prefix} rows)...".format(
        n_prefix=n_prefix), flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    if len(gf) < n_prefix:
        print(f"ERROR: full grid has only {len(gf)} rows, expected >= {n_prefix}.", flush=True)
        return 1
    print(f"  full grid: n_records={len(gf):,}, samples={gf.header.samples}, "
          f"opp={gf.header.opp_label}", flush=True)

    # Verify the same hands: first n_prefix canonical_ids should match.
    ids_prefix = np.asarray(gp.canonical_ids[:1000], dtype=np.uint32)
    ids_full = np.asarray(gf.canonical_ids[:1000], dtype=np.uint32)
    if not np.array_equal(ids_prefix, ids_full):
        print("ERROR: prefix and full grid canonical_ids disagree in first 1000 rows.",
              flush=True)
        return 1
    print("  ✓ canonical_ids align between prefix and full (first 1000 spot-checked).",
          flush=True)

    print("\n[3/4] loading canonical hands + categorizing...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    if len(ch) < n_prefix:
        print(f"ERROR: canonical hands has {len(ch)} rows, expected >= {n_prefix}.",
              flush=True)
        return 1
    cats = categorize_hands(np.asarray(ch.hands[:n_prefix]))
    print(f"  categorized {n_prefix:,} hands.", flush=True)
    cat_counts = Counter(int(c) for c in cats)
    for code in range(8):
        print(f"    cat {code} {CATEGORY_NAMES[code]:<12} n={cat_counts.get(code, 0):,}")

    # Select which row positions to sweep
    if args.sample > 0 and args.sample < n_prefix:
        rng = np.random.default_rng(args.seed)
        sample_idx = np.sort(rng.choice(n_prefix, size=args.sample, replace=False))
        print(f"\n  [sample mode] sweeping {args.sample:,} rows", flush=True)
    else:
        sample_idx = np.arange(n_prefix, dtype=np.int64)
        print(f"\n  sweeping all {n_prefix:,} rows", flush=True)

    n_sweep = len(sample_idx)

    # Per-hand outputs
    v44_picks = np.empty(n_sweep, dtype=np.int16)
    n200_picks = np.empty(n_sweep, dtype=np.int16)
    n1000_picks = np.empty(n_sweep, dtype=np.int16)
    v44_rank_n200 = np.empty(n_sweep, dtype=np.int16)
    regret_n200 = np.empty(n_sweep, dtype=np.float32)
    regret_n1000 = np.empty(n_sweep, dtype=np.float32)
    cats_sweep = cats[sample_idx].astype(np.int8)

    print("\n[4/4] sweeping per-hand v44 vs N=200 vs N=1000 ...", flush=True)
    t0 = time.time()
    hands_arr = ch.hands
    evs_prefix = gp.evs
    evs_full = gf.evs
    for pos in range(n_sweep):
        row = int(sample_idx[pos])
        hand = np.asarray(hands_arr[row], dtype=np.uint8)
        v44_pick = int(strategy_v44_dt(hand))

        # N=200 labels (full grid row at the same canonical_id)
        full_row = np.asarray(evs_full[row], dtype=np.float64)
        n200_pick = int(full_row.argmax())
        ev_v44_n200 = float(full_row[v44_pick])
        rank_n200 = int((full_row > ev_v44_n200).sum()) + 1
        regret_n200_h = float(full_row[n200_pick]) - ev_v44_n200

        # N=1000 labels (prefix grid row)
        pref_row = np.asarray(evs_prefix[row], dtype=np.float64)
        n1000_pick = int(pref_row.argmax())
        ev_v44_n1000 = float(pref_row[v44_pick])
        regret_n1000_h = float(pref_row[n1000_pick]) - ev_v44_n1000

        v44_picks[pos] = v44_pick
        n200_picks[pos] = n200_pick
        n1000_picks[pos] = n1000_pick
        v44_rank_n200[pos] = rank_n200
        regret_n200[pos] = regret_n200_h
        regret_n1000[pos] = regret_n1000_h

        if args.progress_every and (pos + 1) % args.progress_every == 0:
            elapsed = time.time() - t0
            rate = (pos + 1) / elapsed
            eta = (n_sweep - pos - 1) / rate if rate > 0 else 0.0
            print(f"    progress {pos+1:>8,}/{n_sweep:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s", flush=True)

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_sweep / elapsed:.0f} hands/s)\n", flush=True)

    # ---------------------------------------------------------------
    # AGGREGATIONS
    # ---------------------------------------------------------------
    n200_match = (v44_picks == n200_picks)
    n1000_match = (v44_picks == n1000_picks)

    pct_n200_match = 100.0 * n200_match.mean()
    pct_n1000_match = 100.0 * n1000_match.mean()
    shift_pp = pct_n1000_match - pct_n200_match

    mean_regret_n200 = float(regret_n200.mean())
    mean_regret_n1000 = float(regret_n1000.mean())
    dol_regret_n200 = mean_regret_n200 * EV_TO_DOLLARS * 1000
    dol_regret_n1000 = mean_regret_n1000 * EV_TO_DOLLARS * 1000

    # Disagreement among ORACLE picks themselves: how often does the N=200
    # argmax differ from the N=1000 argmax (independent of v44)? This is
    # the rawest possible label-noise indicator.
    oracle_self_match = float((n200_picks == n1000_picks).mean()) * 100.0

    print("=" * 100)
    print("OVERALL — Label-noise measurement")
    print("=" * 100)
    print(f"  hands swept:                       {n_sweep:,}")
    print(f"  v44 vs N=200 match rate:           {pct_n200_match:>6.2f}%")
    print(f"  v44 vs N=1000 match rate:          {pct_n1000_match:>6.2f}%")
    print(f"  shift (n1000 − n200):              {shift_pp:>+6.2f}pp")
    print()
    print(f"  v44 mean regret (vs N=200):        {mean_regret_n200:+.4f}  ≈ ${dol_regret_n200:+,.0f}/1000h")
    print(f"  v44 mean regret (vs N=1000):       {mean_regret_n1000:+.4f}  ≈ ${dol_regret_n1000:+,.0f}/1000h")
    print()
    print(f"  oracle self-agreement (N=200 == N=1000 argmax):  {oracle_self_match:>6.2f}%")
    print()

    # ---------------------------------------------------------------
    # BY SETTING-RANK BUCKET (v44_rank against N=200 oracle)
    # ---------------------------------------------------------------
    bucket_stats = {}
    for b in BUCKETS_ORDER:
        bucket_stats[b] = {"n": 0, "n200_match": 0, "n1000_match": 0,
                           "regret_n200_sum": 0.0, "regret_n1000_sum": 0.0}

    for pos in range(n_sweep):
        b = rank_bucket(int(v44_rank_n200[pos]))
        st = bucket_stats[b]
        st["n"] += 1
        if n200_match[pos]:
            st["n200_match"] += 1
        if n1000_match[pos]:
            st["n1000_match"] += 1
        st["regret_n200_sum"] += float(regret_n200[pos])
        st["regret_n1000_sum"] += float(regret_n1000[pos])

    print("=" * 100)
    print("BY SETTING-RANK BUCKET (v44 rank against N=200 oracle)")
    print("=" * 100)
    print(f"  {'bucket':<11} {'n':>9} {'pct':>6} {'n200_match%':>12} {'n1000_match%':>13} {'shift_pp':>10} "
          f"{'n200_$/1000h':>14} {'n1000_$/1000h':>15}")
    bucket_summary = {}
    for b in BUCKETS_ORDER:
        st = bucket_stats[b]
        n = st["n"]
        if n == 0:
            print(f"  {b:<11} {n:>9,} {'-':>6} {'-':>12} {'-':>13} {'-':>10}")
            bucket_summary[b] = {"n": 0}
            continue
        pct_share = 100.0 * n / n_sweep
        n200_pct = 100.0 * st["n200_match"] / n
        n1000_pct = 100.0 * st["n1000_match"] / n
        shift = n1000_pct - n200_pct
        r200_dol = (st["regret_n200_sum"] / n) * EV_TO_DOLLARS * 1000
        r1000_dol = (st["regret_n1000_sum"] / n) * EV_TO_DOLLARS * 1000
        print(f"  {b:<11} {n:>9,} {pct_share:>5.1f}% {n200_pct:>11.2f}% {n1000_pct:>12.2f}% "
              f"{shift:>+9.2f}pp {r200_dol:>13,.0f} {r1000_dol:>14,.0f}")
        bucket_summary[b] = {
            "n": n,
            "pct_share": pct_share,
            "n200_match_pct": n200_pct,
            "n1000_match_pct": n1000_pct,
            "shift_pp": shift,
            "n200_dol_per_1000h": r200_dol,
            "n1000_dol_per_1000h": r1000_dol,
        }

    # ---------------------------------------------------------------
    # BY HAND CATEGORY
    # ---------------------------------------------------------------
    cat_stats = defaultdict(lambda: {"n": 0, "n200_match": 0, "n1000_match": 0,
                                      "regret_n200_sum": 0.0, "regret_n1000_sum": 0.0})
    for pos in range(n_sweep):
        c = int(cats_sweep[pos])
        st = cat_stats[c]
        st["n"] += 1
        if n200_match[pos]:
            st["n200_match"] += 1
        if n1000_match[pos]:
            st["n1000_match"] += 1
        st["regret_n200_sum"] += float(regret_n200[pos])
        st["regret_n1000_sum"] += float(regret_n1000[pos])

    print()
    print("=" * 100)
    print("BY HAND CATEGORY")
    print("=" * 100)
    print(f"  {'category':<12} {'n':>9} {'pct':>6} {'n200_match%':>12} {'n1000_match%':>13} {'shift_pp':>10} "
          f"{'n200_$/1000h':>14} {'n1000_$/1000h':>15}")
    category_summary = {}
    for code in range(8):
        if code not in cat_stats:
            continue
        st = cat_stats[code]
        n = st["n"]
        if n == 0:
            continue
        name = CATEGORY_NAMES[code]
        pct_share = 100.0 * n / n_sweep
        n200_pct = 100.0 * st["n200_match"] / n
        n1000_pct = 100.0 * st["n1000_match"] / n
        shift = n1000_pct - n200_pct
        r200_dol = (st["regret_n200_sum"] / n) * EV_TO_DOLLARS * 1000
        r1000_dol = (st["regret_n1000_sum"] / n) * EV_TO_DOLLARS * 1000
        print(f"  {name:<12} {n:>9,} {pct_share:>5.1f}% {n200_pct:>11.2f}% {n1000_pct:>12.2f}% "
              f"{shift:>+9.2f}pp {r200_dol:>13,.0f} {r1000_dol:>14,.0f}")
        category_summary[name] = {
            "code": code,
            "n": n,
            "pct_share": pct_share,
            "n200_match_pct": n200_pct,
            "n1000_match_pct": n1000_pct,
            "shift_pp": shift,
            "n200_dol_per_1000h": r200_dol,
            "n1000_dol_per_1000h": r1000_dol,
        }

    # ---------------------------------------------------------------
    # DECISION CRITERION (pre-committed in CURRENT_PHASE.md S79)
    # ---------------------------------------------------------------
    if shift_pp >= 5.0:
        verdict = "A_PATH"
        verdict_text = (
            "A-PATH VERDICT — label noise is materially shifting which setting is 'optimal'. "
            "Match-rate shift ≥ +5pp confirms N=1000 expansion is high-ROI. "
            "Plan: targeted N=1000 grid expansion (Option A)."
        )
    elif shift_pp < 2.0:
        verdict = "C_PATH"
        verdict_text = (
            "C-PATH VERDICT — labels are mostly stable. Match-rate shift < +2pp implies "
            "the 65→95 gap is real model error, not label noise. "
            "Plan: high-capacity gradient boosting retry (Option C: depth=10-12, n_est=1000-2000)."
        )
    else:
        verdict = "MIXED"
        verdict_text = (
            f"MIXED — shift of {shift_pp:+.2f}pp is in the +2..+5pp ambiguous zone. "
            "Neither path pre-committed; surface options to user before next investment."
        )

    print()
    print("=" * 100)
    print("DECISION CRITERION (pre-committed in CURRENT_PHASE.md S79)")
    print("=" * 100)
    print(f"  match-rate shift  (n1000 − n200):  {shift_pp:+.2f}pp")
    print(f"  thresholds:  A-PATH ≥ +5pp   |   C-PATH < +2pp   |   MIXED [+2pp, +5pp)")
    print()
    print(f"  VERDICT: {verdict}")
    print(f"  {verdict_text}")
    print()

    # ---------------------------------------------------------------
    # Save summary JSON
    # ---------------------------------------------------------------
    summary = {
        "schema_version": 1,
        "session": 79,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "input_files": {
            "prefix_n1000_grid": str(GRID_PREFIX.relative_to(ROOT)),
            "full_n200_grid": str(GRID_FULL.relative_to(ROOT)),
            "canonical_hands": str(CANON.relative_to(ROOT)),
        },
        "n_hands_swept": n_sweep,
        "sample_mode": args.sample > 0,
        "sample_size_arg": args.sample,
        "overall": {
            "pct_n200_match": pct_n200_match,
            "pct_n1000_match": pct_n1000_match,
            "shift_pp": shift_pp,
            "oracle_self_match_pct": oracle_self_match,
            "mean_regret_n200": mean_regret_n200,
            "mean_regret_n1000": mean_regret_n1000,
            "dol_per_1000h_n200": dol_regret_n200,
            "dol_per_1000h_n1000": dol_regret_n1000,
        },
        "by_rank_bucket": bucket_summary,
        "by_category": category_summary,
        "decision": {
            "verdict": verdict,
            "text": verdict_text,
            "criterion": {
                "A_PATH": "shift_pp >= 5.0",
                "C_PATH": "shift_pp < 2.0",
                "MIXED": "2.0 <= shift_pp < 5.0",
            },
        },
        "elapsed_sec": elapsed,
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2))
    print(f"  wrote summary JSON: {OUT_JSON}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
