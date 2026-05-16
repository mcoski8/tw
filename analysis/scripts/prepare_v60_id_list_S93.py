"""S93 Phase C-1 — prepare canonical_id list for retroactive v60 validation.

S86 left v60_mid_pair_ds_nomaxtop in MIXED-by-methodology status: at gate=12
(max_sing ≤ Q) the full-grid N=200 lift over v57 was +$6.43/1000h (SHIP), but
the prefix N=1000 grid was silent because the cell (MID × PMID_DS_NOMAXTOP)
sits at cid_min 593,072 — entirely outside the prefix range [0, 500,000).

This script walks the MID × PMID_DS_NOMAXTOP cell, identifies the 32,304
canonical_ids where v60-gate12 changes v57's pick, and writes them to a
text file usable by the engine's --id-list-file mode. It also computes the
N=200 baseline lift on those same hands (sanity-confirms +$6.43) for later
two-grid comparison.

Output:
  data/session93/v60_gate12_changed_ids.txt   — id list (one int per line)
  data/session93/v60_n200_baseline.json       — N=200 lift baselines per gate

NEXT STEP: invoke engine via --id-list-file, then run
grade_v60_id_list_n1000_S93.py.

USAGE:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/prepare_v60_id_list_S93.py
"""
from __future__ import annotations

import json
import sys
import time
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

from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v60_mid_pair_ds_nomaxtop import (  # noqa: E402
    _detect_mid_pair_defensive_pmid_swap,
)

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session93"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_IDS = OUT_DIR / "v60_gate12_changed_ids.txt"
OUT_JSON = OUT_DIR / "v60_n200_baseline.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

MID_PAIR_RANKS = {8, 9, 10}
CELL_IDX_PMID_DS_NOMAXTOP = 3

# Grade all three sub-SHIPpable gates (13/14 already NULL at N=200; skip).
GATES = [10, 11, 12]
PRIMARY_GATE = 12  # the SHIPpable gate at N=200; defines the id list.


def main() -> int:
    print("loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_DS_NOMAXTOP) & np.isin(
        df["pair_rank"], list(MID_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    n_cell = len(target_canonical_ids)
    print(f"  MID × PMID_DS_NOMAXTOP cell hands: {n_cell:,}", flush=True)
    print(f"  cid range: [{target_canonical_ids.min()}, {target_canonical_ids.max()}]")

    print("loading canonical hands + full N=200 oracle grid ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs
    print(f"  n canonical: {len(hands_arr):,}, n grid rows: {len(evs):,}")

    # Precompute v57 picks once.
    print(f"\nprecomputing v57 picks on {n_cell:,} cell hands ...", flush=True)
    t0 = time.time()
    v57_picks = np.empty(n_cell, dtype=np.int16)
    for i in range(n_cell):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v57_picks[i] = int(strategy_v57_lo_pair_defensive(hand_bytes))
        if (i + 1) % 30_000 == 0:
            print(f"  v57: {i+1:,}/{n_cell:,}", flush=True)
    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    # For each gate ∈ {10, 11, 12}, compute v60 picks. Higher gates are
    # supersets, so we record per-gate fire/change masks.
    print("\ncomputing v60 picks at gates 10/11/12 ...", flush=True)
    t0 = time.time()
    v60_picks_by_gate = {g: np.empty(n_cell, dtype=np.int16) for g in GATES}
    fired_by_gate = {g: np.zeros(n_cell, dtype=bool) for g in GATES}
    for i in range(n_cell):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v57_pick = int(v57_picks[i])
        for g in GATES:
            forced = _detect_mid_pair_defensive_pmid_swap(
                hand_bytes, g, v57_pick=v57_pick
            )
            if forced is None:
                v60_picks_by_gate[g][i] = v57_pick
            else:
                v60_picks_by_gate[g][i] = int(forced)
                fired_by_gate[g][i] = True
        if (i + 1) % 30_000 == 0:
            print(f"  v60: {i+1:,}/{n_cell:,}", flush=True)
    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    # Per-gate population sanity counts
    for g in GATES:
        n_fire = int(fired_by_gate[g].sum())
        n_chg = int((v60_picks_by_gate[g] != v57_picks).sum())
        print(f"  gate {g}: fired={n_fire:,}  changed={n_chg:,}")

    # Compute N=200 lifts per gate on the FULL CELL — same as S86 grader, for
    # baseline reproduction.
    print("\ncomputing N=200 lifts per gate (sanity check vs S86) ...",
          flush=True)
    n200_baseline = {}
    for g in GATES:
        sum_delta = 0.0
        v60_picks_g = v60_picks_by_gate[g]
        for i in range(n_cell):
            cid = int(target_canonical_ids[i])
            evs_row = evs[cid]
            sum_delta += float(evs_row[int(v60_picks_g[i])]) - float(
                evs_row[int(v57_picks[i])]
            )
        lift_dol = sum_delta / N_TOTAL_GRID * EV_TO_DOL * 1000
        n_chg = int((v60_picks_g != v57_picks).sum())
        n200_baseline[str(g)] = {
            "gate_max_sing": g,
            "n_changed": n_chg,
            "sum_delta_ev_n200": sum_delta,
            "lift_dol_per_1000h_n200": lift_dol,
        }
        print(f"  gate {g}: n_changed={n_chg:>6,}  N=200 lift=${lift_dol:+.2f}/1000h")

    # Write the id list — at PRIMARY_GATE (gate=12), the superset that contains
    # gates 10 and 11's changed hands as subsets. Sorted asc + deduped.
    primary_changed_mask = v60_picks_by_gate[PRIMARY_GATE] != v57_picks
    primary_ids = sorted(set(int(c) for c in target_canonical_ids[primary_changed_mask]))
    OUT_IDS.write_text("\n".join(str(i) for i in primary_ids) + "\n")
    print(f"\nwrote {len(primary_ids):,} ids to {OUT_IDS.relative_to(ROOT)}")
    print(f"  cid range: [{primary_ids[0]}, {primary_ids[-1]}]")

    # Also serialise per-hand picks (for the grader to use directly)
    OUT_PICKS = OUT_DIR / "v60_per_hand_picks.npz"
    np.savez(
        OUT_PICKS,
        canonical_id=target_canonical_ids,
        v57_pick=v57_picks,
        v60_pick_g10=v60_picks_by_gate[10],
        v60_pick_g11=v60_picks_by_gate[11],
        v60_pick_g12=v60_picks_by_gate[12],
    )
    print(f"wrote per-hand picks to {OUT_PICKS.relative_to(ROOT)}")

    summary = {
        "session": 93,
        "phase": "C-1-prepare",
        "n_cell_hands": n_cell,
        "n_primary_changed": int(primary_changed_mask.sum()),
        "primary_gate": PRIMARY_GATE,
        "per_gate_n200": n200_baseline,
        "id_list_path": str(OUT_IDS.relative_to(ROOT)),
        "picks_path": str(OUT_PICKS.relative_to(ROOT)),
        "note": (
            "id list is the set of canonical_ids where v60 at PRIMARY_GATE=12 "
            "differs from v57. Gates 10 and 11 are STRICT SUBSETS of this set "
            "since gate condition is max_sing ≤ gate (monotone in gate)."
        ),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}")

    print("\nNEXT: run engine with this id list to generate sparse N=1000 grid.")
    print("  engine/target/release/tw-engine oracle-grid \\")
    print("    --canonical data/canonical_hands.bin \\")
    print("    --out data/session93/v60_n1000_sparse.bin \\")
    print("    --lookup data/lookup_table.bin \\")
    print("    --samples 1000 --seed 12648430 --opponent realistic \\")
    print("    --block-size 200 \\")
    print(f"    --id-list-file {OUT_IDS.relative_to(ROOT)}")
    print("\nTHEN: grade_v60_id_list_n1000_S93.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
