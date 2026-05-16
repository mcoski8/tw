"""S95 Phase B — pre-drill v66 on N=200 + emit id list for Option C N=1000.

For each gate ∈ {NARROW, MEDIUM, WIDE}:
  1. Compute v66 picks on the candidate trips B_DS_AVAIL_LKR population.
  2. Compute N=200 baseline lift on changed hands.
  3. Save per-hand picks (v65/v66) for the grader.

For the engine sparse N=1000 generation, emit the id list at the WIDEST gate
(superset of NARROW + MEDIUM). NARROW and MEDIUM are strict subsets.

PRE-COMMITTED THRESHOLDS:
  SHIP   = N=200 lift ≥ $5 AND N=1000 lift ≥ $5
  NULL   = N=200 lift ≤ $1 AND N=1000 lift ≤ $1
  MIXED  = otherwise
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = HERE
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402

from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend,
)
from strategy_v66_trips_layout_a_force_ds_bot import (  # noqa: E402
    _detect_trips_layout_a_force_ds_bot,
    GATE_TRIGGERS,
)
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

DATA = ROOT / "data"
CANON = DATA / "canonical_hands.bin"
GRID_FULL = DATA / "oracle_grid_full_realistic_n200.bin"
PARQUET = DATA / "drill_trips_v44_per_hand_structural.parquet"
OUT_DIR = DATA / "session95"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_IDS = OUT_DIR / "v66_id_list_wide.txt"
OUT_PICKS = OUT_DIR / "v66_per_hand_picks.npz"
OUT_JSON = OUT_DIR / "phaseB_prepare_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159
GATES = ["NARROW", "MEDIUM", "WIDE"]


def main() -> int:
    print("S95 Phase B prepare — v66 picks + N=200 baseline + id list")
    print("=" * 80, flush=True)

    print("\nloading parquet (cell B_DS_AVAIL_LKR Layout-A agree v44 non-DS subset)")
    df = pd.read_parquet(PARQUET)
    c1 = df[df["cell_idx"] == 1]
    print(f"  cell B_DS_AVAIL_LKR: n={len(c1):,}")
    # We test v65 picks Layout A non-DS — for trips, v65 == v44_dt, so check
    # parquet's v44 columns directly.
    target = c1[(c1["v44_layout"] == 0) & (c1["v44_bot_suit"] != 0)].copy()
    print(f"  v44 picks Layout A non-DS: n={len(target):,}")

    canonical_ids = target["canonical_id"].astype(np.int64).to_numpy()
    n_target = len(canonical_ids)

    # Per-hand sub-bucket features (for fast gate filtering)
    ksc = target["kickers_max_suit_count"].astype(np.int8).to_numpy()
    nkts = target["n_kickers_in_trip_suits"].astype(np.int8).to_numpy()
    nbds = target["n_b_ds_routings"].astype(np.int8).to_numpy()

    # v65 = v44_idx for trips
    v65_pick = target["v44_idx"].astype(np.int16).to_numpy()

    # Load canonical hands + N=200 grid
    print("\nloading canonical_hands + N=200 grid")
    ch = read_canonical_hands(CANON, mode="memmap")
    hands_arr = ch.hands
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    evs = grid.evs
    print(f"  canonical: {len(hands_arr):,}, grid: {len(evs):,} rows")

    # Compute v66 picks at the WIDEST gate (superset). Then mask per-gate.
    print("\ncomputing v66 picks at WIDE (covers NARROW + MEDIUM as subsets)")
    t0 = time.time()
    wide_triggers = GATE_TRIGGERS["WIDE"]
    v66_pick_wide = np.empty(n_target, dtype=np.int16)
    fired_wide = np.zeros(n_target, dtype=bool)
    for i in range(n_target):
        cid = int(canonical_ids[i])
        h = np.asarray(hands_arr[cid], dtype=np.uint8)
        forced = _detect_trips_layout_a_force_ds_bot(h, wide_triggers)
        if forced is None:
            v66_pick_wide[i] = v65_pick[i]
        else:
            v66_pick_wide[i] = int(forced)
            fired_wide[i] = True
        if (i + 1) % 10_000 == 0:
            print(f"  v66: {i+1:,}/{n_target:,}", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  fired (WIDE): {int(fired_wide.sum()):,}")

    # Per-gate masks: a hand fires under gate G iff its (ksc, nkts, nbds) is in G's triggers
    gate_picks = {}
    gate_fired_masks = {}
    for gate_name in GATES:
        triggers = GATE_TRIGGERS[gate_name]
        # Build per-hand boolean mask
        mask = np.zeros(n_target, dtype=bool)
        for tk in triggers:
            mask |= ((ksc == tk[0]) & (nkts == tk[1]) & (nbds == tk[2]))
        # v66 pick for this gate
        v66_g = np.where(mask, v66_pick_wide, v65_pick)
        gate_picks[gate_name] = v66_g
        gate_fired_masks[gate_name] = mask
        n_fire = int(mask.sum())
        n_chg = int((v66_g != v65_pick).sum())
        print(f"  gate {gate_name}: fired={n_fire:,}, changed={n_chg:,}")

    # N=200 baseline lifts per gate
    print("\ncomputing N=200 lifts per gate")
    n200_baseline = {}
    for gate_name in GATES:
        v66_g = gate_picks[gate_name]
        sum_delta = 0.0
        n_v66_better = 0
        n_v66_worse = 0
        for i in range(n_target):
            cid = int(canonical_ids[i])
            evs_row = evs[cid]
            d = float(evs_row[int(v66_g[i])]) - float(evs_row[int(v65_pick[i])])
            sum_delta += d
            if d > 0: n_v66_better += 1
            elif d < 0: n_v66_worse += 1
        lift = sum_delta / N_TOTAL_GRID * EV_TO_DOL * 1000
        n_chg = int((v66_g != v65_pick).sum())
        n200_baseline[gate_name] = {
            "gate": gate_name,
            "n_changed": n_chg,
            "sum_delta_ev_n200": sum_delta,
            "lift_dol_per_1000h_n200": lift,
            "n_v66_better": n_v66_better,
            "n_v66_worse": n_v66_worse,
            "swap_right_rate": (n_v66_better / n_chg) if n_chg > 0 else 0.0,
        }
        print(f"  {gate_name}: n_changed={n_chg:,}  N=200 lift=${lift:+.2f}/1000h  "
              f"v66 better={n_v66_better:,} worse={n_v66_worse:,}  "
              f"swap-right={(n_v66_better/n_chg*100 if n_chg>0 else 0):.1f}%")

    # Write id list (changed hands at WIDE = superset of NARROW + MEDIUM)
    wide_changed_mask = gate_picks["WIDE"] != v65_pick
    wide_changed_ids = sorted(set(int(c) for c in canonical_ids[wide_changed_mask]))
    OUT_IDS.write_text("\n".join(str(i) for i in wide_changed_ids) + "\n")
    print(f"\nwrote {len(wide_changed_ids):,} ids to {OUT_IDS.relative_to(ROOT)}")
    print(f"  cid range: [{wide_changed_ids[0]}, {wide_changed_ids[-1]}]")

    # Save per-hand picks for the grader
    np.savez(
        OUT_PICKS,
        canonical_id=canonical_ids,
        v65_pick=v65_pick,
        v66_pick_narrow=gate_picks["NARROW"],
        v66_pick_medium=gate_picks["MEDIUM"],
        v66_pick_wide=gate_picks["WIDE"],
    )
    print(f"wrote per-hand picks to {OUT_PICKS.relative_to(ROOT)}")

    summary = {
        "session": 95,
        "phase": "B-prepare",
        "n_target_pop": int(n_target),
        "n_fired_wide": int(fired_wide.sum()),
        "per_gate_n200": n200_baseline,
        "id_list_path": str(OUT_IDS.relative_to(ROOT)),
        "picks_path": str(OUT_PICKS.relative_to(ROOT)),
        "note": (
            "id list is the set of canonical_ids where v66 at the WIDEST gate "
            "differs from v65. NARROW and MEDIUM are STRICT SUBSETS of this set."
        ),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nsummary -> {OUT_JSON.relative_to(ROOT)}")

    print("\n" + "=" * 80)
    print("N=200 PRE-COMMIT VERDICT (SHIP bar = ≥$5/1000h)")
    print("=" * 80)
    for gate_name in GATES:
        b = n200_baseline[gate_name]
        verdict = "SHIP-pending-N1000" if b["lift_dol_per_1000h_n200"] >= 5.0 else "BELOW-SHIP-BAR"
        print(f"  {gate_name}: lift=${b['lift_dol_per_1000h_n200']:+.2f}  swap-right={b['swap_right_rate']*100:.1f}%  -> {verdict}")

    print("\nNEXT: run engine for sparse N=1000 (~10-15 min wall at 25 hands/s on this hardware)")
    print("  ~/.cargo/bin/cargo run --release --bin tw-engine --manifest-path engine/Cargo.toml -- oracle-grid \\")
    print("    --canonical data/canonical_hands.bin \\")
    print("    --out data/session95/v66_n1000_sparse.bin \\")
    print("    --lookup data/lookup_table.bin \\")
    print("    --samples 1000 --seed 12648430 --opponent realistic \\")
    print("    --block-size 200 \\")
    print(f"    --id-list-file {OUT_IDS.relative_to(ROOT)}")
    print("\nTHEN: grade_v66_id_list_n1000_S95.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
