"""
Session 86 Phase B — drill v57 on MID × PMID_DS_NOMAXTOP.

CONTEXT
-------
S83 shipped v57 = v56 + Rule 20 (LOW pair × PMID_DS_NOMAXTOP × max_sing ≤ Q).
S84 MIXED on LOW × PMID_DS_MAXTOP (different cell shape, didn't ship).
S85 NULL on LOW × PMID_SS_MAXTOP (cell residual fragmented across 3 directions).

S86 default target: extend Rule 20's pattern from LOW pair (2-7) to MID pair
(8-T) on the SAME structural cell (PMID_DS_NOMAXTOP). This is the most
likely-to-ship next cell because it inherits S83's known-working structural
premise (sharp discriminator + single dominant swap direction).

S77 Phase A findings for MID × PMID_DS_NOMAXTOP:
  - 114,048 hands (38,016 per pair_rank, ranks 8/9/T)
  - v44 leak: $27.26/1000h whole-grid (comparable to S83's cell)
  - Top mismatch is the SAME shape as S83:
      v44=PMID_tmax_SS → oracle=PMID_tnomax_DS:
        rank 8: 5,412 hands ($2.81); rank 9: 5,552 ($2.83); rank T: 4,806 ($2.45)
        → combined 15,770 hands @ $8.09/1000h under v44
  - PBOT side-channel grows with pair rank — at rank T,
    PBOT_tmax_SS_ms/mu mismatches combine to ~$1.25 (vs ~$0.47 at rank 8).

CELL precondition:
  - n_PBOT_DS == 0  AND
  - n_PMID_DS > 0  AND
  - n_PMID_DS_w_maxtop == 0

Rule 20 cannot fire here (its pair_rank gate is LOW {2,3,4,5,6,7}). So
v57 = v56 = v52 on this cell, and we drill v57 (production) to characterise
residual leak structure under PRODUCTION.

EARLY-OUT CHECK
---------------
Per S85 lesson: if v57 residual leak < $5/1000h whole-grid, no single rule
can ship (ceiling argument). In that case, pivot to LOW × PMID_OTHER or
HIGH_ONLY × J-low.

WHAT WE DO
----------
  1. Load S77's per-hand parquet.
  2. Filter to MID (rank 8-T) × PMID_DS_NOMAXTOP (cell_idx 3).
  3. Run strategy_v57_lo_pair_defensive on each filtered hand.
  4. Classify v57's pick + oracle's pick via classify_pick_pair taxonomy.
  5. Aggregate (v57_class, oracle_class) by count + total leak $.
  6. Sanity-check: Rule 20 fires 0 times on the cell.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v57_mid_pmid_ds_nomaxtop_S86.py

OUTPUT
------
  data/session86/drill_v57_mid_pmid_ds_nomaxtop_summary.json
  Console: bucket distribution, placement cross-tab, top mismatch table,
           per-pair-rank breakdown, v57-vs-v44 comparison, Rule-20 fire count.
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

from drill_pair_v44_S66 import (  # noqa: E402
    compute_pair_structural,
    cell_for_pair_hand,
    classify_pick_pair,
    CELLS_ORDER,
    RANK_CHAR,
)

from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
    _detect_lo_pair_defensive_pmid_swap,
)

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session86"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "drill_v57_mid_pmid_ds_nomaxtop_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

MID_PAIR_RANKS = {8, 9, 10}
CELL_PMID_DS_NOMAXTOP_IDX = CELLS_ORDER.index("PMID_DS_NOMAXTOP")  # = 3

EPS_REL = 0.005  # matches S77 / S83 / S84 / S85

EARLY_OUT_THRESHOLD = 5.0


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

    mask = (df["cell_idx"] == CELL_PMID_DS_NOMAXTOP_IDX) & np.isin(
        df["pair_rank"], list(MID_PAIR_RANKS)
    )
    n_target = int(mask.sum())
    print(f"  MID × PMID_DS_NOMAXTOP hands: {n_target:,}", flush=True)
    assert n_target > 0, "Empty filter — check cell_idx convention!"

    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_v44_idx = df["v44_idx"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    target_regret_v44 = df["regret"][mask].astype(np.float64)
    target_pair_rank = df["pair_rank"][mask].astype(np.int64)

    print(f"loading canonical hands ({CANON.name}) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"loading oracle grid ({GRID_FULL.name}) ...", flush=True)
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands  # (N, 7) uint8
    evs = grid.evs        # (N, 105) float

    print(f"\nRunning v57 + classifying picks on {n_target:,} hands ...",
          flush=True)
    t0 = time.time()

    v57_idx_arr = np.empty(n_target, dtype=np.int16)
    v57_class = [""] * n_target
    or_class = [""] * n_target
    leak_v57 = np.empty(n_target, dtype=np.float64)
    bucket_codes = np.empty(n_target, dtype=np.int8)
    rule20_fires_on_cell = 0  # sanity counter — should be 0 (LOW gate excludes MID)

    for i in range(n_target):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)

        # Sanity: Rule 20 (max gate 14) must NOT fire on MID pair.
        if _detect_lo_pair_defensive_pmid_swap(hand_bytes, 14) is not None:
            rule20_fires_on_cell += 1

        v57_pick = int(strategy_v57_lo_pair_defensive(hand_bytes))
        v57_idx_arr[i] = v57_pick
        or_pick = int(target_oracle_idx[i])
        evs_row = evs[cid]
        or_ev = float(evs_row[or_pick])
        v57_ev = float(evs_row[v57_pick])
        regret = max(0.0, or_ev - v57_ev)
        leak_v57[i] = regret

        if regret == 0.0:
            bucket_codes[i] = 0
        else:
            denom = max(abs(or_ev), 1e-12)
            rel = regret / denom
            if rel <= EPS_REL:
                bucket_codes[i] = 1
            elif rel <= 5 * EPS_REL:
                bucket_codes[i] = 2
            else:
                bucket_codes[i] = 3

        struct = compute_pair_structural(hand_bytes)
        feats = setting_features_from_bytes(hand_bytes)
        v57_det = classify_pick_pair(hand_bytes, feats, v57_pick, struct)
        or_det = classify_pick_pair(hand_bytes, feats, or_pick, struct)
        v57_class[i] = v57_det["class_label"]
        or_class[i] = or_det["class_label"]

        if (i + 1) % 20_000 == 0 or i == n_target - 1:
            now = time.time()
            rate = (i + 1) / (now - t0)
            eta = (n_target - (i + 1)) / max(rate, 1e-9)
            print(f"  {i+1:,}/{n_target:,}  rate={rate:,.0f} hands/s  ETA={eta:.0f}s",
                  flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n", flush=True)

    print(f"sanity: Rule 20 (gate=A) fires on MID pair cell: {rule20_fires_on_cell:,}")
    print(f"        expected: 0  (Rule 20 pair_rank gate excludes MID 8-T)")
    if rule20_fires_on_cell != 0:
        print(f"  WARNING: Rule 20 fired {rule20_fires_on_cell} times — gate bug?",
              flush=True)

    bucket_names = ["MATCH", "NOISE", "MID", "STRUCTURE"]
    pair_placement_v57 = np.array([c.split("_")[0] for c in v57_class])
    pair_placement_or = np.array([c.split("_")[0] for c in or_class])

    bucket_summary = {}
    for b_code, b_name in enumerate(bucket_names):
        bmask = bucket_codes == b_code
        n_b = int(bmask.sum())
        sum_regret = float(leak_v57[bmask].sum())
        wg_dollars = sum_regret / N_TOTAL_GRID * EV_TO_DOL * 1000
        bucket_summary[b_name] = {
            "n": n_b,
            "sum_regret": sum_regret,
            "wg_dollars": wg_dollars,
        }

    mismatch_by_bucket = {}
    for b_code, b_name in enumerate(bucket_names):
        if b_name == "MATCH":
            continue
        bmask = bucket_codes == b_code
        idxs = np.where(bmask)[0]
        counter = Counter()
        regret_acc = defaultdict(float)
        for i in idxs:
            key = (v57_class[i], or_class[i])
            counter[key] += 1
            regret_acc[key] += float(leak_v57[i])
        rows = []
        for key, cnt in counter.most_common():
            sum_r = regret_acc[key]
            rows.append({
                "v57_class": key[0],
                "oracle_class": key[1],
                "n": cnt,
                "sum_regret": sum_r,
                "wg_dollars": sum_r / N_TOTAL_GRID * EV_TO_DOL * 1000,
                "mean_regret_dollars": sum_r / cnt * EV_TO_DOL,
            })
        rows.sort(key=lambda r: -r["wg_dollars"])
        mismatch_by_bucket[b_name] = rows[:15]

    placements = ["PMID", "PBOT", "SPLIT"]
    placement_xtab_n = {p: {q: 0 for q in placements} for p in placements}
    placement_xtab_wg = {p: {q: 0.0 for q in placements} for p in placements}
    for i in range(n_target):
        p = pair_placement_v57[i]
        q = pair_placement_or[i]
        placement_xtab_n[p][q] += 1
        placement_xtab_wg[p][q] += float(leak_v57[i])
    for p in placements:
        for q in placements:
            placement_xtab_wg[p][q] = (
                placement_xtab_wg[p][q] / N_TOTAL_GRID * EV_TO_DOL * 1000
            )

    per_rank = {}
    for r in sorted(MID_PAIR_RANKS):
        rmask = target_pair_rank == r
        n_r = int(rmask.sum())
        sum_r = float(leak_v57[rmask].sum())
        match_n = int(((bucket_codes == 0) & rmask).sum())
        struct_n = int(((bucket_codes == 3) & rmask).sum())
        struct_wg = (
            float(leak_v57[(bucket_codes == 3) & rmask].sum())
            / N_TOTAL_GRID * EV_TO_DOL * 1000
        )
        per_rank[str(r)] = {
            "n": n_r,
            "wg_total": sum_r / N_TOTAL_GRID * EV_TO_DOL * 1000,
            "match_pct": match_n / max(n_r, 1) * 100,
            "structure_n": struct_n,
            "structure_wg_dollars": struct_wg,
        }

    total_v44_leak = float(target_regret_v44.sum()) / N_TOTAL_GRID * EV_TO_DOL * 1000
    total_v57_leak = float(leak_v57.sum()) / N_TOTAL_GRID * EV_TO_DOL * 1000

    print("=" * 80)
    print(f"S86 Phase B — MID × PMID_DS_NOMAXTOP  (n={n_target:,} hands)")
    print("=" * 80)
    print(f"\nTotal leak under v44_dt (S77): ${total_v44_leak:.2f}/1000h whole-grid")
    print(f"Total leak under v57 (this drill): ${total_v57_leak:.2f}/1000h")
    print(f"Δ (v57 − v44): ${total_v57_leak - total_v44_leak:+.2f}/1000h")

    print(f"\nBucket distribution under v57:")
    print(f"  {'bucket':<10}{'n':>10}{'wg_dollars':>15}")
    for b_name in bucket_names:
        s = bucket_summary[b_name]
        print(f"  {b_name:<10}{s['n']:>10,}{s['wg_dollars']:>14.2f}")

    print(f"\nPlacement cross-tab (rows = v57 pick, cols = oracle pick):")
    print(f"  {'v57\\or':<10}{'PMID':>16}{'PBOT':>16}{'SPLIT':>16}")
    for p in placements:
        cells = []
        for q in placements:
            n_pq = placement_xtab_n[p][q]
            wg_pq = placement_xtab_wg[p][q]
            cells.append(f"{n_pq:>7,} (${wg_pq:>5.2f})")
        print(f"  {p:<10}" + "".join(f"{c:>16}" for c in cells))

    print(f"\nPer-pair-rank breakdown under v57:")
    print(f"  {'rank':<6}{'n':>10}{'wg_total':>12}{'match%':>10}{'STRUCT n':>10}{'STRUCT $/1000h':>16}")
    for r_str in sorted(per_rank.keys(), key=int):
        r = int(r_str)
        d = per_rank[r_str]
        print(f"  {RANK_CHAR[r]:<6}{d['n']:>10,}{d['wg_total']:>12.2f}"
              f"{d['match_pct']:>9.1f}%{d['structure_n']:>10,}"
              f"{d['structure_wg_dollars']:>15.2f}")

    print(f"\nTop STRUCTURE-bucket mismatches under v57 (sorted by $/1000h):")
    print(f"  {'v57_class':<28}{'oracle_class':<28}{'n':>8}{'$/1000h':>10}{'mean$':>11}")
    for row in mismatch_by_bucket.get("STRUCTURE", [])[:12]:
        print(f"  {row['v57_class']:<28}{row['oracle_class']:<28}"
              f"{row['n']:>8,}{row['wg_dollars']:>10.2f}{row['mean_regret_dollars']:>11.0f}")

    print(f"\nTop MID-bucket mismatches under v57 (sorted by $/1000h):")
    print(f"  {'v57_class':<28}{'oracle_class':<28}{'n':>8}{'$/1000h':>10}{'mean$':>11}")
    for row in mismatch_by_bucket.get("MID", [])[:8]:
        print(f"  {row['v57_class']:<28}{row['oracle_class']:<28}"
              f"{row['n']:>8,}{row['wg_dollars']:>10.2f}{row['mean_regret_dollars']:>11.0f}")

    # ---- Addressable-direction-residual snapshot (S86 NEW per S85 methodology) ----
    # Direction of interest (Rule 20 analog): v57_class=PMID_tmax_SS → oracle=PMID_tnomax_DS.
    # Track total $/1000h on this single direction as the SHIP-ceiling.
    direction_n = 0
    direction_regret = 0.0
    for i in range(n_target):
        if v57_class[i] == "PMID_tmax_SS" and or_class[i] == "PMID_tnomax_DS":
            direction_n += 1
            direction_regret += float(leak_v57[i])
    direction_dollars = direction_regret / N_TOTAL_GRID * EV_TO_DOL * 1000

    print("\n" + "=" * 80)
    print("EARLY-OUT CEILING CHECK (S86, S85 methodology)")
    print("=" * 80)
    print(f"v57 total cell leak:                ${total_v57_leak:.2f}/1000h whole-grid")
    print(f"v57 STRUCTURE bucket leak:          ${bucket_summary['STRUCTURE']['wg_dollars']:.2f}/1000h")
    print(f"PMID_tmax_SS→PMID_tnomax_DS direction-residual: ${direction_dollars:.2f}/1000h "
          f"({direction_n:,} hands)")
    print(f"SHIP threshold:                     ${EARLY_OUT_THRESHOLD:.2f}/1000h whole-grid")
    if total_v57_leak < EARLY_OUT_THRESHOLD:
        ceiling_verdict = "EARLY-OUT-PIVOT"
        print(f"VERDICT: {ceiling_verdict} — total cell leak below SHIP threshold;")
        print(f"         no single rule can clear $5 by ceiling argument.")
    elif direction_dollars < EARLY_OUT_THRESHOLD:
        ceiling_verdict = "EARLY-OUT-PIVOT-DIRECTION"
        print(f"VERDICT: {ceiling_verdict} — Rule 20-analog direction-residual below SHIP;")
        print(f"         even perfect rule accuracy on the swap direction cannot clear $5.")
    elif bucket_summary['STRUCTURE']['wg_dollars'] < EARLY_OUT_THRESHOLD:
        ceiling_verdict = "EARLY-OUT-PIVOT-STRUCTURE"
        print(f"VERDICT: {ceiling_verdict} — STRUCTURE bucket below threshold;")
    else:
        ceiling_verdict = "PROCEED-PHASE-B+"
        print(f"VERDICT: {ceiling_verdict} — cell + direction residual both clear SHIP ceiling;")
        print(f"         proceed to discriminator drill.")

    out = {
        "session": 86,
        "cell": "MID × PMID_DS_NOMAXTOP",
        "cell_idx": CELL_PMID_DS_NOMAXTOP_IDX,
        "mid_pair_ranks": sorted(MID_PAIR_RANKS),
        "n_target_hands": n_target,
        "rule20_fires_on_cell": rule20_fires_on_cell,
        "rule20_fires_expected": 0,
        "total_v44_leak_dollars_per_1000h": total_v44_leak,
        "total_v57_leak_dollars_per_1000h": total_v57_leak,
        "bucket_summary_under_v57": bucket_summary,
        "placement_xtab_n_under_v57": placement_xtab_n,
        "placement_xtab_wg_dollars_under_v57": placement_xtab_wg,
        "per_pair_rank_under_v57": per_rank,
        "mismatch_top_by_bucket_under_v57": mismatch_by_bucket,
        "rule20_analog_direction": {
            "v57_class": "PMID_tmax_SS",
            "oracle_class": "PMID_tnomax_DS",
            "n": direction_n,
            "wg_dollars": direction_dollars,
        },
        "eps_rel": EPS_REL,
        "n_total_grid": N_TOTAL_GRID,
        "early_out_threshold_dollars": EARLY_OUT_THRESHOLD,
        "early_out_verdict": ceiling_verdict,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
