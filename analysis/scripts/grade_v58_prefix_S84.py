"""
Session 84 — grade strategy_v58 vs v57 on the N=1000 prefix grid (500K hands).

The full-grid multi-gate grader (grade_v58_lo_pair_ds_maxtop_S84.py) auto-
fired NULL on all six gates (best lift $1.36/1000h at gate=5, below $2 NULL
threshold). This prefix grader runs at the best gate to confirm parity with
the noisier-label full grid and document NULL across both grids.

Approach (mirrors grade_v57_prefix_S83.py):
  - Iterate the first 500,000 canonical hands.
  - Compute v57 pick + v58 pick (at chosen gate) for each.
  - Look up EVs from oracle_grid_prefix500k_n1000.bin (N=1000 labels).
  - Sum match%, regret, and v58−v57 delta.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v58_prefix_S84.py
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

from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v58_lo_pair_ds_maxtop import (  # noqa: E402
    _detect_lo_pair_ds_maxtop_force_tmax,
)

GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session84"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "grade_v58_prefix_summary.json"

EV_TO_DOL = 10.0
N_PREFIX = 500_000

# Best gate per S84 Phase C full-grid grade: top_alt_rank ≥ 5 → $1.36/1000h
# whole-grid. We grade this on prefix for parity check.
GATE = 5

# Pre-committed thresholds (locked before grade runs).
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
    print(f"  grading {n_eval:,} prefix hands at gate=top_alt_rank≥{GATE}", flush=True)

    t0 = time.time()
    sum_v57_regret = 0.0
    sum_v58_regret = 0.0
    n_v57_match = 0
    n_v58_match = 0
    n_v58_changed = 0
    n_v58_fired = 0
    sum_delta_ev = 0.0

    for cid in range(n_eval):
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v57_pick = int(strategy_v57_lo_pair_defensive(hand_bytes))
        forced = _detect_lo_pair_ds_maxtop_force_tmax(hand_bytes, GATE)
        if forced is None:
            v58_pick = v57_pick
        else:
            n_v58_fired += 1
            v58_pick = int(forced)
            if v58_pick != v57_pick:
                n_v58_changed += 1

        evs_row = evs[cid]
        or_pick = int(np.argmax(evs_row))
        or_ev = float(evs_row[or_pick])
        v57_ev = float(evs_row[v57_pick])
        v58_ev = float(evs_row[v58_pick])
        v57_regret = max(0.0, or_ev - v57_ev)
        v58_regret = max(0.0, or_ev - v58_ev)
        sum_v57_regret += v57_regret
        sum_v58_regret += v58_regret
        sum_delta_ev += v58_ev - v57_ev
        if v57_pick == or_pick:
            n_v57_match += 1
        if v58_pick == or_pick:
            n_v58_match += 1

        if (cid + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            rate = (cid + 1) / elapsed
            eta = (n_eval - (cid + 1)) / rate
            print(f"  progress: {cid+1:,}/{n_eval:,}  rate={rate:,.0f} h/s  ETA={eta:.0f}s",
                  flush=True)

    elapsed = time.time() - t0
    v57_regret_dol = sum_v57_regret / n_eval * EV_TO_DOL * 1000
    v58_regret_dol = sum_v58_regret / n_eval * EV_TO_DOL * 1000
    lift_dol = sum_delta_ev / n_eval * EV_TO_DOL * 1000

    if lift_dol >= SHIP_LIFT_DOL_PER_1000H:
        verdict = "SHIP"
    elif lift_dol < NULL_LIFT_DOL_PER_1000H:
        verdict = "NULL"
    else:
        verdict = "MIXED"

    print(f"\n" + "="*70)
    print(f"S84 Phase C — v58 (gate=top_alt_rank≥{GATE}) PREFIX grid grade ({n_eval:,} hands)")
    print(f"="*70)
    print(f"  v57 match%:              {n_v57_match/n_eval*100:>6.2f}%  ({n_v57_match:,})")
    print(f"  v58 match%:              {n_v58_match/n_eval*100:>6.2f}%  ({n_v58_match:,})")
    print(f"  Δ match%:                {(n_v58_match - n_v57_match)/n_eval*100:>+6.2f}pp")
    print(f"  v57 regret $/1000h:      {v57_regret_dol:>+10.2f}")
    print(f"  v58 regret $/1000h:      {v58_regret_dol:>+10.2f}")
    print(f"  LIFT v58 over v57:       {lift_dol:>+10.2f} $/1000h (prefix)")
    print(f"  v58 rule-fires:          {n_v58_fired:,}")
    print(f"  v58 picks changed:       {n_v58_changed:,}")
    print(f"  wall: {elapsed:.1f}s")
    print(f"")
    print(f"  Pre-committed thresholds: SHIP ≥ ${SHIP_LIFT_DOL_PER_1000H:.0f}, "
          f"NULL < ${NULL_LIFT_DOL_PER_1000H:.0f}/1000h prefix")
    print(f"  >>> VERDICT: {verdict}")
    print(f"="*70)

    out = {
        "session": 84,
        "phase": "C-prefix",
        "n_eval": n_eval,
        "gate": GATE,
        "v57_match_pct": n_v57_match / n_eval * 100,
        "v58_match_pct": n_v58_match / n_eval * 100,
        "v57_regret_dol_per_1000h": v57_regret_dol,
        "v58_regret_dol_per_1000h": v58_regret_dol,
        "lift_dol_per_1000h": lift_dol,
        "n_v58_fired": n_v58_fired,
        "n_v58_changed": n_v58_changed,
        "verdict": verdict,
        "ship_threshold": SHIP_LIFT_DOL_PER_1000H,
        "null_threshold": NULL_LIFT_DOL_PER_1000H,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
