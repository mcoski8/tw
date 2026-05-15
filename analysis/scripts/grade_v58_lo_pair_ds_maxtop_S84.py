"""
Session 84 Phase C — grade strategy_v58_lo_pair_ds_maxtop at multiple gates
(full grid, cell hands only).

Since v58 only changes picks on LOW × PMID_DS_MAXTOP hands (128,304 of
6,009,159 = 2.1% of grid), and all other hands route to v57 unchanged, the
whole-grid lift can be computed by iterating ONLY the 128k cell hands and
summing per-hand delta = ev[v58_pick] - ev[v57_pick].

Grades each top_alt_rank gate ∈ {2, 5, 6, 7, 8, 9} and reports:
  - n hands fired
  - n hands "swap-right" (v58 closer to oracle than v57)
  - sum delta in EV units
  - lift in $/1000h whole-grid
  - cell-leak under v57 vs v58

Pre-committed thresholds (locked in code BEFORE this script runs):
  SHIP_LIFT_DOLLARS_PER_1000H = 5.0   # full grid (project convention)
  NULL_LIFT_DOLLARS_PER_1000H = 2.0   # below this = no signal
  MIXED in between → revisit alongside other candidates

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v58_lo_pair_ds_maxtop_S84.py
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
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
from strategy_v58_lo_pair_ds_maxtop import (  # noqa: E402
    _detect_lo_pair_ds_maxtop_force_tmax,
)

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session84"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "grade_v58_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}
CELL_IDX_PMID_DS_MAXTOP = 2

# Gates to grade (top_alt_rank thresholds)
GATES = [2, 5, 6, 7, 8, 9]

# --- PRE-COMMITTED SHIP THRESHOLDS (locked before grade is run) ---
SHIP_LIFT_DOLLARS_PER_1000H = 5.0   # full grid (project convention, S78/S83)
NULL_LIFT_DOLLARS_PER_1000H = 2.0   # below this = no signal
# MIXED in between


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_DS_MAXTOP) & np.isin(
        df["pair_rank"], list(LOW_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    n = len(target_canonical_ids)
    print(f"  LOW × PMID_DS_MAXTOP: {n:,} hands", flush=True)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs

    # Precompute v57 picks (one pass — shared across gates).
    print(f"precomputing v57 picks ({n:,} hands) ...", flush=True)
    t0 = time.time()
    v57_picks = np.empty(n, dtype=np.int16)
    for i in range(n):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v57_picks[i] = int(strategy_v57_lo_pair_defensive(hand_bytes))
        if (i + 1) % 30_000 == 0:
            print(f"  v57 progress: {i+1:,}/{n:,}", flush=True)
    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    per_gate = {}
    for gate in GATES:
        print(f"\n=== Gate = top_alt_rank ≥ {gate} ===", flush=True)
        t0 = time.time()

        n_fired = 0
        n_changed = 0
        n_v58_closer = 0
        n_v58_worse = 0
        n_v58_match_oracle = 0
        sum_delta_ev = 0.0
        sum_v57_regret = 0.0
        sum_v58_regret = 0.0

        for i in range(n):
            cid = int(target_canonical_ids[i])
            hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
            v57_pick = int(v57_picks[i])
            or_pick = int(target_oracle_idx[i])

            forced = _detect_lo_pair_ds_maxtop_force_tmax(hand_bytes, gate)
            if forced is None:
                v58_pick = v57_pick
            else:
                n_fired += 1
                v58_pick = int(forced)
                if v58_pick != v57_pick:
                    n_changed += 1

            evs_row = evs[cid]
            or_ev = float(evs_row[or_pick])
            v57_ev = float(evs_row[v57_pick])
            v58_ev = float(evs_row[v58_pick])
            v57_regret = max(0.0, or_ev - v57_ev)
            v58_regret = max(0.0, or_ev - v58_ev)
            delta_ev = v58_ev - v57_ev

            sum_delta_ev += delta_ev
            sum_v57_regret += v57_regret
            sum_v58_regret += v58_regret

            if v58_pick != v57_pick:
                if v58_regret < v57_regret:
                    n_v58_closer += 1
                elif v58_regret > v57_regret:
                    n_v58_worse += 1
                if v58_pick == or_pick:
                    n_v58_match_oracle += 1

        elapsed = time.time() - t0
        lift_dol = sum_delta_ev / N_TOTAL_GRID * EV_TO_DOL * 1000
        cell_leak_v57 = sum_v57_regret / N_TOTAL_GRID * EV_TO_DOL * 1000
        cell_leak_v58 = sum_v58_regret / N_TOTAL_GRID * EV_TO_DOL * 1000

        if lift_dol >= SHIP_LIFT_DOLLARS_PER_1000H:
            verdict = "SHIP"
        elif lift_dol < NULL_LIFT_DOLLARS_PER_1000H:
            verdict = "NULL"
        else:
            verdict = "MIXED"

        print(f"  n_fired:                {n_fired:>10,}  ({n_fired/n*100:.1f}% of cell)")
        print(f"  n_changed (v58 != v57): {n_changed:>10,}")
        print(f"  n_v58_closer:           {n_v58_closer:>10,}  (v58 reduced regret)")
        print(f"  n_v58_worse:            {n_v58_worse:>10,}  (v58 increased regret)")
        print(f"  n_v58_match_oracle:     {n_v58_match_oracle:>10,}  (v58 == oracle pick)")
        print(f"  swap-right rate (changed only): {n_v58_closer/max(n_changed,1)*100:.1f}%")
        print(f"  sum delta EV:           {sum_delta_ev:>+10.2f}")
        print(f"  cell leak v57:          ${cell_leak_v57:>9.2f}/1000h whole-grid")
        print(f"  cell leak v58:          ${cell_leak_v58:>9.2f}/1000h whole-grid")
        print(f"  LIFT v58 over v57:      ${lift_dol:>+9.2f}/1000h whole-grid")
        print(f"  >>> VERDICT (pre-committed: SHIP ≥ ${SHIP_LIFT_DOLLARS_PER_1000H:.0f}, "
              f"NULL < ${NULL_LIFT_DOLLARS_PER_1000H:.0f}):  {verdict}")
        print(f"  wall: {elapsed:.1f}s", flush=True)

        per_gate[str(gate)] = {
            "gate_top_alt_rank": gate,
            "n_fired": n_fired,
            "n_changed": n_changed,
            "n_v58_closer": n_v58_closer,
            "n_v58_worse": n_v58_worse,
            "n_v58_match_oracle": n_v58_match_oracle,
            "swap_right_rate_pct": n_v58_closer / max(n_changed, 1) * 100,
            "sum_delta_ev": sum_delta_ev,
            "cell_leak_v57_dol_per_1000h": cell_leak_v57,
            "cell_leak_v58_dol_per_1000h": cell_leak_v58,
            "lift_dol_per_1000h": lift_dol,
            "verdict": verdict,
        }

    # Pick best ship-eligible
    sorted_gates = sorted(per_gate.values(), key=lambda d: -d["lift_dol_per_1000h"])
    best = sorted_gates[0]
    print(f"\n" + "="*70)
    print(f"BEST GATE (by full-grid lift):  top_alt_rank ≥ {best['gate_top_alt_rank']}")
    print(f"  Lift over v57:      ${best['lift_dol_per_1000h']:+.2f}/1000h whole-grid")
    print(f"  Verdict:            {best['verdict']}")
    print(f"  n_changed:          {best['n_changed']:,}")
    print(f"  swap-right rate:    {best['swap_right_rate_pct']:.1f}%")
    print(f"="*70)

    # Aggregate verdict for the candidate (best gate verdict)
    print(f"\nOverall S84 candidate verdict: {best['verdict']}")
    if best["verdict"] == "NULL":
        print(f"  Rationale: best full-grid lift ${best['lift_dol_per_1000h']:.2f} "
              f"< NULL threshold ${NULL_LIFT_DOLLARS_PER_1000H:.0f}/1000h")
    elif best["verdict"] == "MIXED":
        print(f"  Rationale: best full-grid lift ${best['lift_dol_per_1000h']:.2f} "
              f"between NULL ${NULL_LIFT_DOLLARS_PER_1000H:.0f} and "
              f"SHIP ${SHIP_LIFT_DOLLARS_PER_1000H:.0f} thresholds")
    elif best["verdict"] == "SHIP":
        print(f"  Rationale: best full-grid lift ${best['lift_dol_per_1000h']:.2f} "
              f"≥ SHIP threshold ${SHIP_LIFT_DOLLARS_PER_1000H:.0f}/1000h")
        print(f"  Next step: prefix grade at this gate (grade_v58_prefix_S84.py)")

    out = {
        "session": 84,
        "phase": "C",
        "ship_threshold_dol_per_1000h": SHIP_LIFT_DOLLARS_PER_1000H,
        "null_threshold_dol_per_1000h": NULL_LIFT_DOLLARS_PER_1000H,
        "n_cell_hands": n,
        "per_gate": per_gate,
        "best_gate": best,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
