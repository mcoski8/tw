"""
Session 86 Phase C — grade strategy_v60_mid_pair_ds_nomaxtop at multiple gates
(full grid, cell hands only).

Since v60 only changes picks on MID × PMID_DS_NOMAXTOP hands (114,048 of
6,009,159 = 1.9% of grid), and all other hands route to v57 unchanged, the
whole-grid lift can be computed by iterating ONLY the cell hands and
summing per-hand delta = ev[v60_pick] - ev[v57_pick].

Grades each max_sing gate ∈ {10, 11, 12, 13, 14} and reports:
  - n hands fired
  - n hands "swap-right" (v60 closer to oracle than v57)
  - sum delta in EV units
  - lift in $/1000h whole-grid
  - cell-leak under v57 vs v60

PRE-COMMITTED THRESHOLDS (locked in code BEFORE this script runs):
  SHIP_LIFT_DOLLARS_PER_1000H = 5.0   # full grid (project convention, S78/S83)
  NULL_LIFT_DOLLARS_PER_1000H = 2.0   # below this = no signal
  MIXED in between
  S84 refinement: SHIP requires BOTH full-grid lift ≥ $5 AND prefix-grid
  lift ≥ $5 (the two-grid-confirmation standard).

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v60_mid_pair_ds_nomaxtop_S86.py
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

OUT_DIR = ROOT / "data" / "session86"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "grade_v60_summary.json"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

MID_PAIR_RANKS = {8, 9, 10}
CELL_IDX_PMID_DS_NOMAXTOP = 3

GATES = [10, 11, 12, 13, 14]

# --- PRE-COMMITTED SHIP THRESHOLDS (locked before grade is run) ---
SHIP_LIFT_DOLLARS_PER_1000H = 5.0
NULL_LIFT_DOLLARS_PER_1000H = 2.0
# S84 refinement: full-grid SHIP is necessary BUT not sufficient — also requires
# prefix-grid SHIP (graded separately by grade_v60_prefix_multigate_S86.py).


def main() -> int:
    print(f"loading parquet ...", flush=True)
    tbl = pq.read_table(
        PARQUET_IN,
        columns=["canonical_id", "pair_rank", "cell_idx",
                 "v44_idx", "oracle_idx"],
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
        print(f"\n=== Gate = max_sing ≤ {gate} ===", flush=True)
        t0 = time.time()

        n_fired = 0
        n_changed = 0
        n_v60_closer = 0
        n_v60_worse = 0
        n_v60_match_oracle = 0
        sum_delta_ev = 0.0
        sum_v57_regret = 0.0
        sum_v60_regret = 0.0
        # Per-rank tracking
        rank_fired = {r: 0 for r in MID_PAIR_RANKS}
        rank_changed = {r: 0 for r in MID_PAIR_RANKS}
        rank_closer = {r: 0 for r in MID_PAIR_RANKS}
        rank_delta = {r: 0.0 for r in MID_PAIR_RANKS}

        for i in range(n):
            cid = int(target_canonical_ids[i])
            hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
            v57_pick = int(v57_picks[i])
            or_pick = int(target_oracle_idx[i])
            pr = int(target_pair_rank[i])

            forced = _detect_mid_pair_defensive_pmid_swap(
                hand_bytes, gate, v57_pick=v57_pick)
            if forced is None:
                v60_pick = v57_pick
            else:
                n_fired += 1
                rank_fired[pr] += 1
                v60_pick = int(forced)
                if v60_pick != v57_pick:
                    n_changed += 1
                    rank_changed[pr] += 1

            evs_row = evs[cid]
            or_ev = float(evs_row[or_pick])
            v57_ev = float(evs_row[v57_pick])
            v60_ev = float(evs_row[v60_pick])
            v57_regret = max(0.0, or_ev - v57_ev)
            v60_regret = max(0.0, or_ev - v60_ev)
            delta_ev = v60_ev - v57_ev

            sum_delta_ev += delta_ev
            sum_v57_regret += v57_regret
            sum_v60_regret += v60_regret
            rank_delta[pr] += delta_ev

            if v60_pick != v57_pick:
                if v60_regret < v57_regret:
                    n_v60_closer += 1
                    rank_closer[pr] += 1
                elif v60_regret > v57_regret:
                    n_v60_worse += 1
                if v60_pick == or_pick:
                    n_v60_match_oracle += 1

        elapsed = time.time() - t0
        lift_dol = sum_delta_ev / N_TOTAL_GRID * EV_TO_DOL * 1000
        cell_leak_v57 = sum_v57_regret / N_TOTAL_GRID * EV_TO_DOL * 1000
        cell_leak_v60 = sum_v60_regret / N_TOTAL_GRID * EV_TO_DOL * 1000

        if lift_dol >= SHIP_LIFT_DOLLARS_PER_1000H:
            verdict = "SHIP"
        elif lift_dol < NULL_LIFT_DOLLARS_PER_1000H:
            verdict = "NULL"
        else:
            verdict = "MIXED"

        print(f"  n_fired:                {n_fired:>10,}  ({n_fired/n*100:.1f}% of cell)")
        print(f"  n_changed (v60 != v57): {n_changed:>10,}")
        print(f"  n_v60_closer:           {n_v60_closer:>10,}  (v60 reduced regret)")
        print(f"  n_v60_worse:            {n_v60_worse:>10,}  (v60 increased regret)")
        print(f"  n_v60_match_oracle:     {n_v60_match_oracle:>10,}  (v60 == oracle pick)")
        print(f"  swap-right rate (changed only): {n_v60_closer/max(n_changed,1)*100:.1f}%")
        print(f"  sum delta EV:           {sum_delta_ev:>+10.2f}")
        print(f"  cell leak v57:          ${cell_leak_v57:>9.2f}/1000h whole-grid")
        print(f"  cell leak v60:          ${cell_leak_v60:>9.2f}/1000h whole-grid")
        print(f"  LIFT v60 over v57:      ${lift_dol:>+9.2f}/1000h whole-grid")
        print(f"  Per-rank lift breakdown:")
        for pr in sorted(MID_PAIR_RANKS):
            rd = rank_delta[pr] / N_TOTAL_GRID * EV_TO_DOL * 1000
            print(f"    rank {pr}: fired={rank_fired[pr]:>6,}  "
                  f"changed={rank_changed[pr]:>6,}  "
                  f"closer={rank_closer[pr]:>6,}  "
                  f"lift=${rd:>+6.2f}/1000h")
        print(f"  >>> VERDICT (pre-committed: SHIP ≥ ${SHIP_LIFT_DOLLARS_PER_1000H:.0f}, "
              f"NULL < ${NULL_LIFT_DOLLARS_PER_1000H:.0f}):  {verdict}")
        print(f"  wall: {elapsed:.1f}s", flush=True)

        per_gate[str(gate)] = {
            "gate_max_sing": gate,
            "n_fired": n_fired,
            "n_changed": n_changed,
            "n_v60_closer": n_v60_closer,
            "n_v60_worse": n_v60_worse,
            "n_v60_match_oracle": n_v60_match_oracle,
            "swap_right_rate_pct": n_v60_closer / max(n_changed, 1) * 100,
            "sum_delta_ev": sum_delta_ev,
            "cell_leak_v57_dol_per_1000h": cell_leak_v57,
            "cell_leak_v60_dol_per_1000h": cell_leak_v60,
            "lift_dol_per_1000h": lift_dol,
            "verdict": verdict,
            "per_rank_lift_dol_per_1000h": {
                str(pr): rank_delta[pr] / N_TOTAL_GRID * EV_TO_DOL * 1000
                for pr in MID_PAIR_RANKS
            },
            "per_rank_fired": {str(pr): rank_fired[pr] for pr in MID_PAIR_RANKS},
            "per_rank_changed": {str(pr): rank_changed[pr] for pr in MID_PAIR_RANKS},
            "per_rank_closer": {str(pr): rank_closer[pr] for pr in MID_PAIR_RANKS},
        }

    sorted_gates = sorted(per_gate.values(), key=lambda d: -d["lift_dol_per_1000h"])
    best = sorted_gates[0]
    print(f"\n" + "="*70)
    print(f"BEST GATE (by full-grid lift):  max_sing ≤ {best['gate_max_sing']}")
    print(f"  Lift over v57:      ${best['lift_dol_per_1000h']:+.2f}/1000h whole-grid")
    print(f"  Verdict:            {best['verdict']}")
    print(f"  n_changed:          {best['n_changed']:,}")
    print(f"  swap-right rate:    {best['swap_right_rate_pct']:.1f}%")
    print(f"="*70)

    print(f"\nOverall S86 candidate verdict (full grid only): {best['verdict']}")
    if best["verdict"] == "NULL":
        print(f"  Rationale: best full-grid lift ${best['lift_dol_per_1000h']:.2f} "
              f"< NULL threshold ${NULL_LIFT_DOLLARS_PER_1000H:.0f}/1000h")
        print(f"  By S84's two-grid standard, full-grid NULL implies overall NULL")
        print(f"  unless prefix shows strong signal (which would make it MIXED).")
    elif best["verdict"] == "MIXED":
        print(f"  Rationale: best full-grid lift ${best['lift_dol_per_1000h']:.2f} "
              f"between NULL ${NULL_LIFT_DOLLARS_PER_1000H:.0f} and "
              f"SHIP ${SHIP_LIFT_DOLLARS_PER_1000H:.0f} thresholds")
    elif best["verdict"] == "SHIP":
        print(f"  Rationale: best full-grid lift ${best['lift_dol_per_1000h']:.2f} "
              f"≥ SHIP threshold ${SHIP_LIFT_DOLLARS_PER_1000H:.0f}/1000h")
        print(f"  Next step: prefix multi-gate grade — both grids must clear $5 to SHIP.")

    out = {
        "session": 86,
        "phase": "C-1",
        "grid": "full_n200",
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
