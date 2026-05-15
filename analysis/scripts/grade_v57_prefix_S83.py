"""
Session 83 — grade strategy_v57 vs v56 on the N=1000 prefix grid (500K hands).

This is the project's standard ship gate (S78 convention: +$5/1000h prefix-
grid lift required to ship). The full-grid grade in
`grade_v57_lo_pair_defensive_S83.py` already showed SHIP at gate=Q
(+$16.47/1000h whole-grid); this script confirms on the cleaner-label
prefix grid.

Approach:
  - Iterate the first 500,000 canonical hands.
  - Compute v56 pick + v57 pick (at gate=Q) for each.
  - Look up EVs from oracle_grid_prefix500k_n1000.bin (N=1000 labels).
  - Sum match%, regret, and v57−v56 delta.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v57_prefix_S83.py
"""
from __future__ import annotations

import json
import sys
import time
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

from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    _detect_lo_pair_defensive_pmid_swap,
)

GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session83"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "grade_v57_prefix_summary.json"

EV_TO_DOL = 10.0
N_PREFIX = 500_000

GATE = 12  # Q gate — winner from full-grid grade

# Pre-committed ship thresholds (locked before grade runs).
SHIP_LIFT_DOL_PER_1000H = 5.0
NULL_LIFT_DOL_PER_1000H = 2.0


def main() -> int:
    print(f"loading canonical hands ({CANON.name}) ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    print(f"loading PREFIX grid ({GRID_PREFIX.name}) ...", flush=True)
    grid = read_oracle_grid(GRID_PREFIX, mode="memmap")
    hands_arr = ch.hands
    evs = grid.evs
    n_records = len(grid)
    n_eval = min(n_records, N_PREFIX)
    assert n_eval == N_PREFIX, f"Expected {N_PREFIX} records, got {n_eval}"
    print(f"  grading {n_eval:,} prefix hands at gate=max_sing≤{GATE} (Q)", flush=True)

    t0 = time.time()
    sum_v56_regret = 0.0
    sum_v57_regret = 0.0
    n_v56_match = 0
    n_v57_match = 0
    n_v57_changed = 0
    n_v57_fired = 0
    sum_delta_ev = 0.0

    for cid in range(n_eval):
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v56_pick = int(strategy_v56_trips_hybrid(hand_bytes))
        forced = _detect_lo_pair_defensive_pmid_swap(hand_bytes, GATE)
        if forced is None:
            v57_pick = v56_pick
        else:
            n_v57_fired += 1
            v57_pick = int(forced)
            if v57_pick != v56_pick:
                n_v57_changed += 1

        evs_row = evs[cid]
        or_pick = int(np.argmax(evs_row))
        or_ev = float(evs_row[or_pick])
        v56_ev = float(evs_row[v56_pick])
        v57_ev = float(evs_row[v57_pick])
        v56_regret = max(0.0, or_ev - v56_ev)
        v57_regret = max(0.0, or_ev - v57_ev)
        sum_v56_regret += v56_regret
        sum_v57_regret += v57_regret
        sum_delta_ev += v57_ev - v56_ev
        if v56_pick == or_pick:
            n_v56_match += 1
        if v57_pick == or_pick:
            n_v57_match += 1

        if (cid + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (cid + 1) / elapsed
            eta = (n_eval - (cid + 1)) / rate
            print(f"  progress: {cid+1:,}/{n_eval:,}  rate={rate:,.0f} h/s  ETA={eta:.0f}s",
                  flush=True)

    elapsed = time.time() - t0
    v56_regret_dol = sum_v56_regret / n_eval * EV_TO_DOL * 1000
    v57_regret_dol = sum_v57_regret / n_eval * EV_TO_DOL * 1000
    lift_dol = sum_delta_ev / n_eval * EV_TO_DOL * 1000

    if lift_dol >= SHIP_LIFT_DOL_PER_1000H:
        verdict = "SHIP"
    elif lift_dol < NULL_LIFT_DOL_PER_1000H:
        verdict = "NULL"
    else:
        verdict = "MIXED"

    print(f"\n" + "="*70)
    print(f"S83 Phase C — v57 (gate=Q) PREFIX grid grade ({n_eval:,} hands)")
    print(f"="*70)
    print(f"  v56 match%:              {n_v56_match/n_eval*100:>6.2f}%  ({n_v56_match:,})")
    print(f"  v57 match%:              {n_v57_match/n_eval*100:>6.2f}%  ({n_v57_match:,})")
    print(f"  Δ match%:                {(n_v57_match - n_v56_match)/n_eval*100:>+6.2f}pp")
    print(f"  v56 regret $/1000h:      {v56_regret_dol:>+10.2f}")
    print(f"  v57 regret $/1000h:      {v57_regret_dol:>+10.2f}")
    print(f"  LIFT v57 over v56:       {lift_dol:>+10.2f} $/1000h (prefix)")
    print(f"  v57 rule-fires:          {n_v57_fired:,}")
    print(f"  v57 picks changed:       {n_v57_changed:,}")
    print(f"  wall: {elapsed:.1f}s")
    print(f"")
    print(f"  Pre-committed thresholds: SHIP ≥ ${SHIP_LIFT_DOL_PER_1000H:.0f}, "
          f"NULL < ${NULL_LIFT_DOL_PER_1000H:.0f}/1000h prefix")
    print(f"  >>> VERDICT: {verdict}")
    print(f"="*70)

    out = {
        "session": 83,
        "phase": "C-prefix",
        "n_eval": n_eval,
        "gate": GATE,
        "v56_match_pct": n_v56_match / n_eval * 100,
        "v57_match_pct": n_v57_match / n_eval * 100,
        "v56_regret_dol_per_1000h": v56_regret_dol,
        "v57_regret_dol_per_1000h": v57_regret_dol,
        "lift_dol_per_1000h": lift_dol,
        "n_v57_fired": n_v57_fired,
        "n_v57_changed": n_v57_changed,
        "verdict": verdict,
        "ship_threshold": SHIP_LIFT_DOL_PER_1000H,
        "null_threshold": NULL_LIFT_DOL_PER_1000H,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
