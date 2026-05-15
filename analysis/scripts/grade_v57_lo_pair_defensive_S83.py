"""
Session 83 Phase C — grade strategy_v57_lo_pair_defensive at multiple gates.

Since v57 only changes picks on LOW × PMID_DS_NOMAXTOP hands (228,096 of
6,009,159 = 3.8% of grid), and all other hands route to v56 unchanged, the
whole-grid lift can be computed by iterating ONLY the 228k cell hands and
summing per-hand delta = ev[v57_pick] - ev[v56_pick].

Grades each gate ∈ {J, Q, K, A} and reports:
  - n hands fired
  - n hands "swap-right" (v57 closer to oracle than v56)
  - sum delta in EV units
  - lift in $/1000h whole-grid (= sum_delta / N_TOTAL_GRID * EV_TO_DOL * 1000)
  - v57 cell-leak vs v56 cell-leak

Ship gate per project convention: +$5/1000h prefix grid; we report full-grid
here as the cell hands are in the full grid not the 500K prefix.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v57_lo_pair_defensive_S83.py
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

from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    _detect_lo_pair_defensive_pmid_swap,
)

PARQUET_IN = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session83"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "grade_v57_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}
CELL_IDX_PMID_DS_NOMAXTOP = 3
GATES = [11, 12, 13, 14]  # J, Q, K, A

# PRE-COMMITTED SHIP THRESHOLDS (locked before grade is run) ---
SHIP_LIFT_DOLLARS_PER_1000H = 5.0   # full grid (project convention)
NULL_LIFT_DOLLARS_PER_1000H = 2.0   # below this = no signal
# MIXED in between → revisit alongside other candidates


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx"],
    )
    df = {col: tbl[col].to_numpy() for col in tbl.column_names}

    mask = (df["cell_idx"] == CELL_IDX_PMID_DS_NOMAXTOP) & np.isin(
        df["pair_rank"], list(LOW_PAIR_RANKS)
    )
    target_canonical_ids = df["canonical_id"][mask].astype(np.int64)
    target_oracle_idx = df["oracle_idx"][mask].astype(np.int64)
    n = len(target_canonical_ids)
    print(f"  LOW × PMID_DS_NOMAXTOP: {n:,} hands", flush=True)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs

    # --- Precompute v56 picks (one pass — shared across gates). ---
    print(f"precomputing v56 picks ({n:,} hands) ...", flush=True)
    t0 = time.time()
    v56_picks = np.empty(n, dtype=np.int16)
    for i in range(n):
        cid = int(target_canonical_ids[i])
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v56_picks[i] = int(strategy_v56_trips_hybrid(hand_bytes))
        if (i + 1) % 50_000 == 0:
            print(f"  v56 progress: {i+1:,}/{n:,}", flush=True)
    print(f"  done in {time.time()-t0:.1f}s", flush=True)

    # --- For each gate, compute per-hand delta and lift. ---
    per_gate = {}
    for gate in GATES:
        print(f"\n=== Gate = max_sing ≤ {gate} ===", flush=True)
        t0 = time.time()

        n_fired = 0
        n_changed = 0
        n_v57_closer = 0  # v57 closer to oracle than v56 (or equal-better)
        n_v57_worse = 0  # v57 worse than v56
        n_v57_match_oracle = 0  # v57 picks exactly oracle pick
        sum_delta_ev = 0.0
        sum_v56_regret = 0.0
        sum_v57_regret = 0.0

        for i in range(n):
            cid = int(target_canonical_ids[i])
            hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
            v56_pick = int(v56_picks[i])
            or_pick = int(target_oracle_idx[i])

            forced = _detect_lo_pair_defensive_pmid_swap(hand_bytes, gate)
            if forced is None:
                v57_pick = v56_pick
            else:
                n_fired += 1
                v57_pick = int(forced)
                if v57_pick != v56_pick:
                    n_changed += 1

            evs_row = evs[cid]
            or_ev = float(evs_row[or_pick])
            v56_ev = float(evs_row[v56_pick])
            v57_ev = float(evs_row[v57_pick])
            v56_regret = max(0.0, or_ev - v56_ev)
            v57_regret = max(0.0, or_ev - v57_ev)
            delta_ev = v57_ev - v56_ev

            sum_delta_ev += delta_ev
            sum_v56_regret += v56_regret
            sum_v57_regret += v57_regret

            if v57_pick != v56_pick:
                if v57_regret < v56_regret:
                    n_v57_closer += 1
                elif v57_regret > v56_regret:
                    n_v57_worse += 1
                if v57_pick == or_pick:
                    n_v57_match_oracle += 1

        elapsed = time.time() - t0
        lift_dol = sum_delta_ev / N_TOTAL_GRID * EV_TO_DOL * 1000
        cell_leak_v56 = sum_v56_regret / N_TOTAL_GRID * EV_TO_DOL * 1000
        cell_leak_v57 = sum_v57_regret / N_TOTAL_GRID * EV_TO_DOL * 1000

        # Pre-committed verdict
        if lift_dol >= SHIP_LIFT_DOLLARS_PER_1000H:
            verdict = "SHIP"
        elif lift_dol < NULL_LIFT_DOLLARS_PER_1000H:
            verdict = "NULL"
        else:
            verdict = "MIXED"

        print(f"  n_fired:                {n_fired:>10,}  ({n_fired/n*100:.1f}% of cell)")
        print(f"  n_changed (v57 != v56): {n_changed:>10,}")
        print(f"  n_v57_closer:           {n_v57_closer:>10,}  (v57 reduced regret)")
        print(f"  n_v57_worse:            {n_v57_worse:>10,}  (v57 increased regret)")
        print(f"  n_v57_match_oracle:     {n_v57_match_oracle:>10,}  (v57 == oracle pick)")
        print(f"  swap-right rate (changed only): {n_v57_closer/max(n_changed,1)*100:.1f}%")
        print(f"  sum delta EV:           {sum_delta_ev:>+10.2f}")
        print(f"  cell leak v56:          ${cell_leak_v56:>9.2f}/1000h whole-grid")
        print(f"  cell leak v57:          ${cell_leak_v57:>9.2f}/1000h whole-grid")
        print(f"  LIFT v57 over v56:      ${lift_dol:>+9.2f}/1000h whole-grid")
        print(f"  >>> VERDICT (pre-committed thresholds: SHIP ≥ ${SHIP_LIFT_DOLLARS_PER_1000H:.0f}, "
              f"NULL < ${NULL_LIFT_DOLLARS_PER_1000H:.0f}):  {verdict}")
        print(f"  wall: {elapsed:.1f}s", flush=True)

        per_gate[str(gate)] = {
            "gate_max_sing": gate,
            "n_fired": n_fired,
            "n_changed": n_changed,
            "n_v57_closer": n_v57_closer,
            "n_v57_worse": n_v57_worse,
            "n_v57_match_oracle": n_v57_match_oracle,
            "swap_right_rate_pct": n_v57_closer / max(n_changed, 1) * 100,
            "sum_delta_ev": sum_delta_ev,
            "cell_leak_v56_dol_per_1000h": cell_leak_v56,
            "cell_leak_v57_dol_per_1000h": cell_leak_v57,
            "lift_dol_per_1000h": lift_dol,
            "verdict": verdict,
        }

    # Sort gates by lift, pick best ship-eligible
    sorted_gates = sorted(per_gate.values(), key=lambda d: -d["lift_dol_per_1000h"])
    best = sorted_gates[0]
    print(f"\n" + "="*70)
    print(f"BEST GATE (by full-grid lift):  max_sing ≤ {best['gate_max_sing']}")
    print(f"  Lift over v56:      ${best['lift_dol_per_1000h']:+.2f}/1000h whole-grid")
    print(f"  Verdict:            {best['verdict']}")
    print(f"  n_changed:          {best['n_changed']:,}")
    print(f"  swap-right rate:    {best['swap_right_rate_pct']:.1f}%")
    print(f"="*70)

    out = {
        "session": 83,
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
