"""
Session 86 Phase B+ — feature discriminator for the MID pair PMID-swap rule.

CONTEXT (from Phase B in same session):
  Cell: MID pair (rank 8-T) × PMID_DS_NOMAXTOP, n=114,048 hands.
  v57 cell leak: $31.17/1000h whole-grid.
  100% PMID placement under v57 (no SPLIT, no PBOT).
  Top STRUCTURE-bucket mismatches under v57:
    - PMID_tmax_SS  → PMID_tnomax_DS   23,657 hands  $14.72  ← Rule 20 analog #1
    - PMID_tmax_31  → PMID_tnomax_DS   13,166 hands  $8.21   ← NEW vs S83 (LOW)
    - PMID_tmax_SS  → PMID_tnomax_SS    5,513 hands  $2.46
    - PMID_tmax_SS  → PBOT_tmax_SS_ms   3,736 hands  $1.80   ← PBOT side-channel
    - PMID_tmax_SS  → PBOT_tmax_SS_mu   2,169 hands  $0.93

  ADDRESSABLE-DIRECTION-RESIDUAL (per S85 ceiling check):
    PMID_tmax_SS → PMID_tnomax_DS only: $14.75/1000h whole-grid
    PMID_tmax_{SS,31} → PMID_tnomax_DS combined: ~$22.96/1000h
    Both clear $5 SHIP threshold — proceed.

QUESTION:
  What per-hand feature discriminates the swap-target hands (Pop SWAP) from
  the keep-v57 hands (Pop KEEP) on this MID pair cell?

POPULATIONS (analogous to S85's expanded scheme):
  KEEP_TMAX:          v57 in {PMID_tmax_SS, PMID_tmax_31}  AND
                      oracle = v57_lbl
                      (oracle agrees with v57's tmax-on-top)
  SWAP_TO_TNOMAX_DS:  v57 in {PMID_tmax_SS, PMID_tmax_31}  AND
                      oracle = PMID_tnomax_DS
                      (Rule 20 analog target — the primary swap direction)
  SWAP_TO_PBOT_SS:    v57 in {PMID_tmax_SS, PMID_tmax_31}  AND
                      oracle ∈ {PBOT_tmax_SS_mu, PBOT_tmax_SS_ms,
                                PBOT_tnomax_SS_ms, PBOT_tnomax_SS_mu,
                                PBOT_tmax_31_*}
                      (PBOT side-channel — competing direction)
  OTHER:              everything else (v57 disagrees with oracle in some
                      other way, or v57 is not tmax_SS / tmax_31)

For each candidate discriminator, compare KEEP_TMAX vs SWAP_TO_TNOMAX_DS
mean/median and per-value swap-pct. The discriminator that maximally
separates is the rule gate.

We do the same for SWAP_TO_PBOT_SS as a sanity check on the side-channel.

S85 ceiling check is applied at end:
  addressable-direction-residual_SWAP_TNOMAX_DS = sum(regret in that pop)
                                                  / N_TOTAL_GRID * EV * 1000
  if < $5 → CEILING-NULL → pivot.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v57_mid_pmid_ds_swap_discriminator_S86.py
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
    classify_pick_pair,
    CELLS_ORDER,
    RANK_CHAR,
)

from strategy_v57_lo_pair_defensive import strategy_v57_lo_pair_defensive  # noqa: E402

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session86"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "drill_v57_mid_pmid_ds_swap_discriminator_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

MID_PAIR_RANKS = {8, 9, 10}
CELL_IDX_PMID_DS_NOMAXTOP = CELLS_ORDER.index("PMID_DS_NOMAXTOP")  # 3

SWAP_FROM_LBLS = {"PMID_tmax_SS", "PMID_tmax_31"}
PBOT_SS_LBLS = {
    "PBOT_tmax_SS_mu", "PBOT_tmax_SS_ms",
    "PBOT_tnomax_SS_ms", "PBOT_tnomax_SS_mu",
    "PBOT_tmax_31_mu", "PBOT_tmax_31_ms",
}
SHIP_CEILING_DOLLARS = 5.0


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx", "regret"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_DS_NOMAXTOP) & np.isin(
        df["pair_rank"], list(MID_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    target_pair_rank = df["pair_rank"][mask].astype(np.int64)
    n = len(target_canonical_ids)
    print(f"  MID × PMID_DS_NOMAXTOP: {n:,} hands", flush=True)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs

    print(f"running v57 + classifying + extracting features ...", flush=True)
    t0 = time.time()

    pop_records = []
    for i in range(n):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        or_pick = int(target_oracle_idx[i])
        v57_pick = int(strategy_v57_lo_pair_defensive(hand_bytes))

        struct = compute_pair_structural(hand_bytes)
        feats = setting_features_from_bytes(hand_bytes)
        v57_det = classify_pick_pair(hand_bytes, feats, v57_pick, struct)
        or_det = classify_pick_pair(hand_bytes, feats, or_pick, struct)
        v57_lbl = v57_det["class_label"]
        or_lbl = or_det["class_label"]

        evs_row = evs[cid]
        regret = max(0.0, float(evs_row[or_pick]) - float(evs_row[v57_pick]))

        # Determine population.
        if v57_lbl not in SWAP_FROM_LBLS:
            pop = "NOT_TMAX"  # v57 picked something other than tmax_SS / tmax_31
        elif or_lbl == v57_lbl:
            pop = "KEEP_TMAX"
        elif or_lbl == "PMID_tnomax_DS":
            pop = "SWAP_TO_TNOMAX_DS"
        elif or_lbl in PBOT_SS_LBLS:
            pop = "SWAP_TO_PBOT_SS"
        else:
            pop = "OTHER"

        # Discriminator features
        max_sing = int(struct["max_sing_rank"])
        sing_ranks = list(struct["sing_ranks"])
        sorted_sing = sorted(sing_ranks, reverse=True)
        second_max_sing = int(sorted_sing[1]) if len(sorted_sing) > 1 else 0
        third_max_sing = int(sorted_sing[2]) if len(sorted_sing) > 2 else 0
        ds_bot_pair_high = int(struct["best_PMID_DS_bot_pair_high"])
        pair_rank = int(struct["pair_rank"])
        max_gap = max_sing - second_max_sing
        ds_upgrade = ds_bot_pair_high - second_max_sing
        ds_upgrade_vs_max = ds_bot_pair_high - max_sing

        pop_records.append({
            "pop": pop,
            "v57_lbl": v57_lbl,
            "or_lbl": or_lbl,
            "regret": regret,
            "pair_rank": pair_rank,
            "max_sing": max_sing,
            "second_max_sing": second_max_sing,
            "third_max_sing": third_max_sing,
            "ds_bot_pair_high": ds_bot_pair_high,
            "max_gap": max_gap,
            "ds_upgrade": ds_upgrade,
            "ds_upgrade_vs_max": ds_upgrade_vs_max,
        })

        if (i + 1) % 30_000 == 0:
            print(f"  scanned {i+1:,}/{n:,}", flush=True)

    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    # --- Pop counts + leak ---
    pop_counts = Counter(r["pop"] for r in pop_records)
    pop_regret = defaultdict(float)
    for r in pop_records:
        pop_regret[r["pop"]] += r["regret"]

    print(f"\nPopulation summary on MID × PMID_DS_NOMAXTOP (n={n:,}):")
    print(f"  {'population':<22}{'n':>8}{'% of cell':>11}{'$/1000h':>10}")
    for pop in ["KEEP_TMAX", "SWAP_TO_TNOMAX_DS", "SWAP_TO_PBOT_SS",
                "OTHER", "NOT_TMAX"]:
        cnt = pop_counts.get(pop, 0)
        rg = pop_regret.get(pop, 0.0)
        dol = rg / N_TOTAL_GRID * EV_TO_DOL * 1000
        pct = cnt / max(n, 1) * 100
        print(f"  {pop:<22}{cnt:>8,}{pct:>10.1f}%{dol:>10.2f}")

    swap_tnomax_dollars = pop_regret["SWAP_TO_TNOMAX_DS"] / N_TOTAL_GRID * EV_TO_DOL * 1000
    swap_pbot_dollars = pop_regret["SWAP_TO_PBOT_SS"] / N_TOTAL_GRID * EV_TO_DOL * 1000

    # --- Discriminator analysis: KEEP_TMAX vs SWAP_TO_TNOMAX_DS ---
    feature_names = ["pair_rank", "max_sing", "second_max_sing",
                     "third_max_sing", "ds_bot_pair_high",
                     "max_gap", "ds_upgrade", "ds_upgrade_vs_max"]

    def disc_table(pop_a, pop_b, feature):
        a_vals = [r[feature] for r in pop_records if r["pop"] == pop_a]
        b_vals = [r[feature] for r in pop_records if r["pop"] == pop_b]
        a_arr = np.array(a_vals) if a_vals else np.array([0])
        b_arr = np.array(b_vals) if b_vals else np.array([0])
        a_hist = Counter(a_vals)
        b_hist = Counter(b_vals)
        all_vals = sorted(set(a_hist) | set(b_hist))
        rows = []
        for v in all_vals:
            k = a_hist.get(v, 0)
            s = b_hist.get(v, 0)
            tot = k + s
            swap_pct = s / max(tot, 1) * 100
            rows.append({
                "val": v,
                "a_n": k,
                "b_n": s,
                "swap_pct_within_pair": swap_pct,
            })
        return {
            "pop_a": pop_a,
            "pop_b": pop_b,
            "a_mean": float(a_arr.mean()),
            "a_median": float(np.median(a_arr)),
            "b_mean": float(b_arr.mean()),
            "b_median": float(np.median(b_arr)),
            "delta": float(b_arr.mean() - a_arr.mean()),
            "rows": rows,
        }

    print(f"\nDiscriminator: KEEP_TMAX vs SWAP_TO_TNOMAX_DS")
    print(f"  {'feature':<22}{'keep_mean':>12}{'swap_mean':>12}{'Δ':>10}")
    tnomax_disc_tables = {}
    for fname in feature_names:
        d = disc_table("KEEP_TMAX", "SWAP_TO_TNOMAX_DS", fname)
        tnomax_disc_tables[fname] = d
        print(f"  {fname:<22}{d['a_mean']:>12.2f}{d['b_mean']:>12.2f}{d['delta']:>+10.2f}")

    # Print full per-value histogram for max_sing (the Rule 20 analog discriminator)
    print(f"\n  === max_sing per-value (within KEEP_TMAX ∪ SWAP_TO_TNOMAX_DS) ===")
    print(f"  {'val':>4}{'rank':>5}{'KEEP':>8}{'SWAP':>8}{'swap%':>9}")
    for r in tnomax_disc_tables["max_sing"]["rows"]:
        v = r["val"]
        print(f"  {v:>4}{RANK_CHAR[v]:>5}{r['a_n']:>8,}{r['b_n']:>8,}"
              f"{r['swap_pct_within_pair']:>8.1f}%")

    print(f"\nDiscriminator: KEEP_TMAX vs SWAP_TO_PBOT_SS (side-channel)")
    print(f"  {'feature':<22}{'keep_mean':>12}{'pbot_mean':>12}{'Δ':>10}")
    pbot_disc_tables = {}
    for fname in feature_names:
        d = disc_table("KEEP_TMAX", "SWAP_TO_PBOT_SS", fname)
        pbot_disc_tables[fname] = d
        print(f"  {fname:<22}{d['a_mean']:>12.2f}{d['b_mean']:>12.2f}{d['delta']:>+10.2f}")

    # --- Per-pair-rank breakdown of swap-pct at the best gate ---
    # We expect rank to shift the optimal max_sing gate.
    print(f"\nPer-pair-rank max_sing distribution (KEEP vs SWAP_TNOMAX_DS):")
    for r_rank in sorted(MID_PAIR_RANKS):
        r_keep = [r["max_sing"] for r in pop_records
                  if r["pop"] == "KEEP_TMAX" and r["pair_rank"] == r_rank]
        r_swap = [r["max_sing"] for r in pop_records
                  if r["pop"] == "SWAP_TO_TNOMAX_DS" and r["pair_rank"] == r_rank]
        keep_hist = Counter(r_keep)
        swap_hist = Counter(r_swap)
        all_vals = sorted(set(keep_hist) | set(swap_hist))
        print(f"\n  pair_rank = {RANK_CHAR[r_rank]} ({r_rank})")
        print(f"  {'max':>4}{'rank':>5}{'KEEP':>8}{'SWAP':>8}{'swap%':>9}")
        for v in all_vals:
            k = keep_hist.get(v, 0)
            s = swap_hist.get(v, 0)
            tot = k + s
            pct = s / max(tot, 1) * 100
            print(f"  {v:>4}{RANK_CHAR[v]:>5}{k:>8,}{s:>8,}{pct:>8.1f}%")

    # --- Addressable-direction-residual SHIP-ceiling check (S85 lesson) ---
    print("\n" + "=" * 80)
    print("ADDRESSABLE-DIRECTION-RESIDUAL CHECK (S85 methodology)")
    print("=" * 80)
    print(f"SWAP_TO_TNOMAX_DS direction-residual:  ${swap_tnomax_dollars:.2f}/1000h whole-grid")
    print(f"SWAP_TO_PBOT_SS direction-residual:    ${swap_pbot_dollars:.2f}/1000h whole-grid")
    print(f"SHIP threshold (per-grid):             ${SHIP_CEILING_DOLLARS:.2f}/1000h")
    if swap_tnomax_dollars >= SHIP_CEILING_DOLLARS:
        verdict = "PROCEED-PHASE-C"
        print(f"VERDICT: {verdict} — primary direction-residual clears SHIP ceiling.")
        print(f"         Even partial accuracy on swap-direction can clear $5.")
    else:
        verdict = "CEILING-NULL-PIVOT"
        print(f"VERDICT: {verdict} — direction-residual below SHIP threshold.")
        print(f"         No single-direction rule can clear $5 by ceiling argument.")

    out = {
        "session": 86,
        "phase": "B+",
        "cell": "MID × PMID_DS_NOMAXTOP",
        "mid_pair_ranks": sorted(MID_PAIR_RANKS),
        "n_target_hands": n,
        "pop_counts": dict(pop_counts),
        "pop_regret_dollars": {
            k: v / N_TOTAL_GRID * EV_TO_DOL * 1000 for k, v in pop_regret.items()
        },
        "swap_to_tnomax_ds_dollars": swap_tnomax_dollars,
        "swap_to_pbot_ss_dollars": swap_pbot_dollars,
        "ship_ceiling_dollars": SHIP_CEILING_DOLLARS,
        "verdict": verdict,
        "discriminator_tnomax": tnomax_disc_tables,
        "discriminator_pbot": pbot_disc_tables,
        "n_total_grid": N_TOTAL_GRID,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
