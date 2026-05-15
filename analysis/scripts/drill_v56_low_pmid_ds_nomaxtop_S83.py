"""
Session 83 Phase B — under-rule-covered weak-hand drill.

CONTEXT
-------
S82 closed the A-path (oracle-label-quality lever) at v44 capacity. S83 picked
Option D-revised (per user direction): focus rule-chain extension on the
under-rule-covered weak-hand zone rather than min-maxing well-covered
categories.

S77 identified the top under-covered cell as LOW pair (rank 2-7) ×
PMID_DS_NOMAXTOP, carrying $31.00/1000h STRUCTURE leak under v44_dt. The
dominant v44 mismatch was `SPLIT_tmax_SS_mu → PMID` (v44 splits the low
pair onto top instead of keeping pair in middle).

BUT: production v56_trips_hybrid routes these hands through v52 (the rule
chain), NOT v44_dt. We need to confirm whether v52's pick has the same
SPLIT mistake pattern, a different one, or has already partially closed
the leak via different routing.

This drill:
  1. Loads S77's per-hand parquet (has canonical_id, cell_idx, oracle pick,
     regret for every PAIR hand).
  2. Filters to LOW (rank 2-7) × PMID_DS_NOMAXTOP (cell_idx 3).
  3. Runs strategy_v56_trips_hybrid on each filtered hand.
  4. Classifies v56's pick via the S66/S77 classify_pick_pair taxonomy
     (PMID/PBOT/SPLIT × top_type × bot_suit).
  5. Aggregates (v56_class, oracle_class) by count + total leak $.
  6. Reports the dominant mismatch pattern under PRODUCTION v56 — the
     defensive routing pattern Phase C would extract into a rule.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v56_low_pmid_ds_nomaxtop_S83.py

OUTPUT
------
  data/session83/drill_v56_low_pmid_ds_nomaxtop_summary.json  (machine-readable)
  Console: top mismatch table + comparison to v44 baseline.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.query import setting_features_from_bytes  # noqa: E402

# Reuse S66's pair-cell classifier + pick classifier (avoids re-deriving
# the taxonomy — gives identical class_label strings as S77).
from drill_pair_v44_S66 import (  # noqa: E402
    compute_pair_structural,
    cell_for_pair_hand,
    classify_pick_pair,
    CELLS_ORDER,
    RANK_CHAR,
)

from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session83"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "drill_v56_low_pmid_ds_nomaxtop_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159  # canonical-equal $/1000h whole-grid normalizer

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}
CELL_PMID_DS_NOMAXTOP_IDX = CELLS_ORDER.index("PMID_DS_NOMAXTOP")  # = 3

# S77's bucket thresholds (eps_rel relative to oracle_ev) for parity.
EPS_REL = 0.005


def main() -> int:
    print(f"loading S77 per-hand parquet: {PARQUET_IN.name} ...", flush=True)
    t0 = time.time()
    tbl = pq.read_table(
        PARQUET_IN,
        columns=[
            "canonical_id", "pair_rank", "cell_idx",
            "v44_idx", "oracle_idx", "regret",
        ],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}
    print(f"  loaded {len(df['canonical_id']):,} pair rows in {time.time()-t0:.1f}s",
          flush=True)

    # Build the LOW × PMID_DS_NOMAXTOP mask.
    mask = (df["cell_idx"] == CELL_PMID_DS_NOMAXTOP_IDX) & np.isin(
        df["pair_rank"], list(LOW_PAIR_RANKS)
    )
    n_target = int(mask.sum())
    print(f"  LOW × PMID_DS_NOMAXTOP hands: {n_target:,}", flush=True)
    assert n_target > 0, "Empty filter — check cell_idx convention!"

    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_v44_idx = df["v44_idx"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    target_regret_v44 = df["regret"][mask].astype(np.float64)
    target_pair_rank = df["pair_rank"][mask].astype(np.int64)

    # Load canonical hands + oracle grid for v56 pick + per-hand EVs.
    print(f"loading canonical hands ({CANON.name}) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"loading oracle grid ({GRID_FULL.name}) ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands  # (N, 7) uint8
    evs = grid.evs        # (N, 105) float

    # --- Run v56_trips_hybrid on the target subset; classify each pick. ---
    print(f"\nRunning v56 + classifying picks on {n_target:,} hands ...",
          flush=True)
    t0 = time.time()
    last = t0

    v56_idx_arr = np.empty(n_target, dtype=np.int16)
    v56_class = [""] * n_target
    or_class = [""] * n_target
    leak_v56 = np.empty(n_target, dtype=np.float64)
    bucket_codes = np.empty(n_target, dtype=np.int8)  # 0=MATCH 1=NOISE 2=MID 3=STRUCTURE

    for i in range(n_target):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        # v56 pick
        v56_pick = int(strategy_v56_trips_hybrid(hand_bytes))
        v56_idx_arr[i] = v56_pick
        # oracle pick from parquet
        or_pick = int(target_oracle_idx[i])
        # EVs for leak computation
        evs_row = evs[cid]  # (105,)
        or_ev = float(evs_row[or_pick])
        v56_ev = float(evs_row[v56_pick])
        regret = max(0.0, or_ev - v56_ev)
        leak_v56[i] = regret

        # Bucket using same rule as S77 (relative to |or_ev|, eps_rel=0.005).
        if regret == 0.0:
            bucket_codes[i] = 0  # MATCH
        else:
            denom = max(abs(or_ev), 1e-12)
            rel = regret / denom
            if rel <= EPS_REL:
                bucket_codes[i] = 1  # NOISE
            elif rel <= 5 * EPS_REL:
                bucket_codes[i] = 2  # MID
            else:
                bucket_codes[i] = 3  # STRUCTURE

        # Classify v56 and oracle picks using S66 taxonomy
        struct = compute_pair_structural(hand_bytes)
        feats = setting_features_from_bytes(hand_bytes)
        v56_det = classify_pick_pair(hand_bytes, feats, v56_pick, struct)
        or_det = classify_pick_pair(hand_bytes, feats, or_pick, struct)
        v56_class[i] = v56_det["class_label"]
        or_class[i] = or_det["class_label"]

        if (i + 1) % 20_000 == 0 or i == n_target - 1:
            now = time.time()
            rate = (i + 1) / (now - t0)
            eta = (n_target - (i + 1)) / max(rate, 1e-9)
            print(f"  {i+1:,}/{n_target:,}  rate={rate:,.0f} hands/s  ETA={eta:.0f}s",
                  flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n", flush=True)

    # --- Aggregation ---
    bucket_names = ["MATCH", "NOISE", "MID", "STRUCTURE"]
    pair_placement_v56 = np.array([c.split("_")[0] for c in v56_class])
    pair_placement_or = np.array([c.split("_")[0] for c in or_class])

    # 1. Per-bucket cell totals
    bucket_summary = {}
    for b_code, b_name in enumerate(bucket_names):
        bmask = bucket_codes == b_code
        n_b = int(bmask.sum())
        sum_regret = float(leak_v56[bmask].sum())
        wg_dollars = sum_regret / N_TOTAL_GRID * EV_TO_DOL * 1000
        bucket_summary[b_name] = {
            "n": n_b,
            "sum_regret": sum_regret,
            "wg_dollars": wg_dollars,
        }

    # 2. Mismatch table by bucket (focus on STRUCTURE first)
    mismatch_by_bucket = {}
    for b_code, b_name in enumerate(bucket_names):
        if b_name == "MATCH":
            continue
        bmask = bucket_codes == b_code
        idxs = np.where(bmask)[0]
        counter = Counter()
        regret_acc = defaultdict(float)
        for i in idxs:
            key = (v56_class[i], or_class[i])
            counter[key] += 1
            regret_acc[key] += float(leak_v56[i])
        rows = []
        for key, cnt in counter.most_common():
            sum_r = regret_acc[key]
            rows.append({
                "v56_class": key[0],
                "oracle_class": key[1],
                "n": cnt,
                "sum_regret": sum_r,
                "wg_dollars": sum_r / N_TOTAL_GRID * EV_TO_DOL * 1000,
                "mean_regret_dollars": sum_r / cnt * EV_TO_DOL,
            })
        rows.sort(key=lambda r: -r["wg_dollars"])
        mismatch_by_bucket[b_name] = rows[:15]

    # 3. Placement-level cross-tab (PMID/PBOT/SPLIT × PMID/PBOT/SPLIT)
    placements = ["PMID", "PBOT", "SPLIT"]
    placement_xtab_n = {p: {q: 0 for q in placements} for p in placements}
    placement_xtab_wg = {p: {q: 0.0 for q in placements} for p in placements}
    for i in range(n_target):
        p = pair_placement_v56[i]
        q = pair_placement_or[i]
        placement_xtab_n[p][q] += 1
        placement_xtab_wg[p][q] += float(leak_v56[i])
    for p in placements:
        for q in placements:
            placement_xtab_wg[p][q] = (
                placement_xtab_wg[p][q] / N_TOTAL_GRID * EV_TO_DOL * 1000
            )

    # 4. Per-pair-rank breakdown
    per_rank = {}
    for r in sorted(LOW_PAIR_RANKS):
        rmask = target_pair_rank == r
        n_r = int(rmask.sum())
        sum_r = float(leak_v56[rmask].sum())
        match_n = int(((bucket_codes == 0) & rmask).sum())
        struct_n = int(((bucket_codes == 3) & rmask).sum())
        struct_wg = (
            float(leak_v56[(bucket_codes == 3) & rmask].sum())
            / N_TOTAL_GRID * EV_TO_DOL * 1000
        )
        per_rank[str(r)] = {
            "n": n_r,
            "wg_total": sum_r / N_TOTAL_GRID * EV_TO_DOL * 1000,
            "match_pct": match_n / max(n_r, 1) * 100,
            "structure_n": struct_n,
            "structure_wg_dollars": struct_wg,
        }

    # 5. v56-vs-v44 comparison: how much of v44's leak does v56 inherit /
    #    avoid / amplify on the same hands?
    total_v44_leak = float(target_regret_v44.sum()) / N_TOTAL_GRID * EV_TO_DOL * 1000
    total_v56_leak = float(leak_v56.sum()) / N_TOTAL_GRID * EV_TO_DOL * 1000

    # --- Console output ---
    print("=" * 80)
    print(f"S83 Phase B — LOW × PMID_DS_NOMAXTOP  (n={n_target:,} hands)")
    print("=" * 80)
    print(f"\nTotal leak under v44_dt (S77): ${total_v44_leak:.2f}/1000h whole-grid")
    print(f"Total leak under v56_trips_hybrid (this drill): ${total_v56_leak:.2f}/1000h")
    print(f"Δ (v56 − v44): ${total_v56_leak - total_v44_leak:+.2f}/1000h")

    print(f"\nBucket distribution under v56:")
    print(f"  {'bucket':<10}{'n':>10}{'wg_dollars':>15}")
    for b_name in bucket_names:
        s = bucket_summary[b_name]
        print(f"  {b_name:<10}{s['n']:>10,}{s['wg_dollars']:>14.2f}")

    print(f"\nPlacement cross-tab (rows = v56 pick, cols = oracle pick):")
    print(f"  {'v56\\or':<10}{'PMID':>14}{'PBOT':>14}{'SPLIT':>14}")
    for p in placements:
        cells = []
        for q in placements:
            n_pq = placement_xtab_n[p][q]
            wg_pq = placement_xtab_wg[p][q]
            cells.append(f"{n_pq:>7,} (${wg_pq:>4.1f})")
        print(f"  {p:<10}" + "".join(f"{c:>14}" for c in cells))

    print(f"\nPer-pair-rank breakdown under v56:")
    print(f"  {'rank':<6}{'n':>10}{'wg_total':>12}{'match%':>10}{'STRUCT n':>10}{'STRUCT $/1000h':>16}")
    for r_str in sorted(per_rank.keys(), key=int):
        r = int(r_str)
        d = per_rank[r_str]
        print(f"  {RANK_CHAR[r]:<6}{d['n']:>10,}{d['wg_total']:>12.2f}"
              f"{d['match_pct']:>9.1f}%{d['structure_n']:>10,}"
              f"{d['structure_wg_dollars']:>15.2f}")

    print(f"\nTop STRUCTURE-bucket mismatches under v56 (sorted by $/1000h):")
    print(f"  {'v56_class':<28}{'oracle_class':<28}{'n':>8}{'$/1000h':>10}{'mean$':>11}")
    for row in mismatch_by_bucket.get("STRUCTURE", [])[:12]:
        print(f"  {row['v56_class']:<28}{row['oracle_class']:<28}"
              f"{row['n']:>8,}{row['wg_dollars']:>10.2f}{row['mean_regret_dollars']:>11.0f}")

    print(f"\nTop MID-bucket mismatches under v56 (sorted by $/1000h):")
    print(f"  {'v56_class':<28}{'oracle_class':<28}{'n':>8}{'$/1000h':>10}{'mean$':>11}")
    for row in mismatch_by_bucket.get("MID", [])[:8]:
        print(f"  {row['v56_class']:<28}{row['oracle_class']:<28}"
              f"{row['n']:>8,}{row['wg_dollars']:>10.2f}{row['mean_regret_dollars']:>11.0f}")

    # --- Persist summary ---
    out = {
        "session": 83,
        "cell": "LOW × PMID_DS_NOMAXTOP",
        "low_pair_ranks": sorted(LOW_PAIR_RANKS),
        "n_target_hands": n_target,
        "total_v44_leak_dollars_per_1000h": total_v44_leak,
        "total_v56_leak_dollars_per_1000h": total_v56_leak,
        "bucket_summary_under_v56": bucket_summary,
        "placement_xtab_n_under_v56": placement_xtab_n,
        "placement_xtab_wg_dollars_under_v56": placement_xtab_wg,
        "per_pair_rank_under_v56": per_rank,
        "mismatch_top_by_bucket_under_v56": mismatch_by_bucket,
        "eps_rel": EPS_REL,
        "n_total_grid": N_TOTAL_GRID,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
