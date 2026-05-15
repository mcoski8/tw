"""
Session 86 — multi-gate prefix grader for strategy_v60_mid_pair_ds_nomaxtop.

CONTEXT
-------
Full-grid grader (grade_v60_mid_pair_ds_nomaxtop_S86.py) reported:
  Gate 10:  +$1.63 (NULL)
  Gate 11:  +$4.85 (MIXED — just below SHIP)
  Gate 12:  +$6.43 (SHIP) ← best
  Gate 13:  -$0.08 (NULL)
  Gate 14: -$54.47 (NULL)

Per the S84 two-grid-confirmation standard, SHIP requires BOTH full-grid lift
≥ $5 AND prefix-grid lift ≥ $5. The full grid is decisive at gate 12; this
script confirms whether the prefix grid agrees.

WHAT THIS DOES
--------------
Run all gates ∈ {10, 11, 12, 13, 14} on the prefix grid (N=1000 labels,
~500K hands). Map the lift surface. Pre-committed thresholds.

PRE-COMMITTED VERDICTS (locked in code BEFORE this script runs):
  SHIP_LIFT_DOL_PER_1000H = 5.0
  NULL_LIFT_DOL_PER_1000H = 2.0
  MIXED in between
  S84 refinement: SHIP requires BOTH grids ≥ $5.

USAGE
-----
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v60_prefix_multigate_S86.py
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
from strategy_v60_mid_pair_ds_nomaxtop import (  # noqa: E402
    _detect_mid_pair_defensive_pmid_swap,
)

GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"

OUT_DIR = ROOT / "data" / "session86"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "grade_v60_prefix_multigate_summary.json"

EV_TO_DOL = 10.0
N_PREFIX = 500_000

GATES = [10, 11, 12, 13, 14]

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
    assert n_eval == N_PREFIX

    print(f"precomputing v57 picks + oracle picks on {n_eval:,} hands ...",
          flush=True)
    t0 = time.time()
    v57_picks = np.empty(n_eval, dtype=np.int16)
    or_picks = np.empty(n_eval, dtype=np.int16)
    v57_evs = np.empty(n_eval, dtype=np.float64)
    or_evs = np.empty(n_eval, dtype=np.float64)
    for cid in range(n_eval):
        hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
        v57_picks[cid] = int(strategy_v57_lo_pair_defensive(hand_bytes))
        evs_row = evs[cid]
        or_picks[cid] = int(np.argmax(evs_row))
        v57_evs[cid] = float(evs_row[v57_picks[cid]])
        or_evs[cid] = float(evs_row[or_picks[cid]])
        if (cid + 1) % 100_000 == 0:
            elapsed = time.time() - t0
            rate = (cid + 1) / elapsed
            print(f"  v57 precompute: {cid+1:,}/{n_eval:,}  rate={rate:,.0f} h/s",
                  flush=True)
    print(f"  v57 precompute done in {time.time()-t0:.1f}s", flush=True)

    per_gate = {}
    for gate in GATES:
        print(f"\n=== PREFIX Gate = max_sing ≤ {gate} ===", flush=True)
        t0 = time.time()

        n_fired = 0
        n_changed = 0
        n_v60_closer = 0
        n_v60_worse = 0
        sum_delta_ev = 0.0
        sum_v57_regret = 0.0
        sum_v60_regret = 0.0
        n_v57_match = 0
        n_v60_match = 0

        for cid in range(n_eval):
            hand_bytes = np.asarray(hands_arr[cid], dtype=np.uint8)
            v57_pick = int(v57_picks[cid])
            or_pick = int(or_picks[cid])

            forced = _detect_mid_pair_defensive_pmid_swap(
                hand_bytes, gate, v57_pick=v57_pick)
            if forced is None:
                v60_pick = v57_pick
            else:
                n_fired += 1
                v60_pick = int(forced)
                if v60_pick != v57_pick:
                    n_changed += 1

            evs_row = evs[cid]
            or_ev = float(or_evs[cid])
            v57_ev = float(v57_evs[cid])
            v60_ev = float(evs_row[v60_pick])
            v57_regret = max(0.0, or_ev - v57_ev)
            v60_regret = max(0.0, or_ev - v60_ev)
            delta_ev = v60_ev - v57_ev

            sum_delta_ev += delta_ev
            sum_v57_regret += v57_regret
            sum_v60_regret += v60_regret

            if v57_pick == or_pick: n_v57_match += 1
            if v60_pick == or_pick: n_v60_match += 1

            if v60_pick != v57_pick:
                if v60_regret < v57_regret:
                    n_v60_closer += 1
                elif v60_regret > v57_regret:
                    n_v60_worse += 1

            if (cid + 1) % 100_000 == 0:
                elapsed = time.time() - t0
                rate = (cid + 1) / elapsed
                eta = (n_eval - (cid + 1)) / rate
                print(f"  gate={gate}  progress: {cid+1:,}/{n_eval:,}  "
                      f"rate={rate:,.0f} h/s  ETA={eta:.0f}s", flush=True)

        elapsed = time.time() - t0
        lift_dol = sum_delta_ev / n_eval * EV_TO_DOL * 1000
        regret_v57 = sum_v57_regret / n_eval * EV_TO_DOL * 1000
        regret_v60 = sum_v60_regret / n_eval * EV_TO_DOL * 1000

        if lift_dol >= SHIP_LIFT_DOL_PER_1000H:
            verdict = "SHIP"
        elif lift_dol < NULL_LIFT_DOL_PER_1000H:
            verdict = "NULL"
        else:
            verdict = "MIXED"

        print(f"  n_fired:                {n_fired:>10,}")
        print(f"  n_changed:              {n_changed:>10,}")
        print(f"  n_v60_closer:           {n_v60_closer:>10,}")
        print(f"  n_v60_worse:            {n_v60_worse:>10,}")
        print(f"  swap-right rate (changed only): {n_v60_closer/max(n_changed,1)*100:.1f}%")
        print(f"  v57 match%:             {n_v57_match/n_eval*100:>6.2f}%")
        print(f"  v60 match%:             {n_v60_match/n_eval*100:>6.2f}%")
        print(f"  v57 regret:             ${regret_v57:>9.2f}/1000h prefix")
        print(f"  v60 regret:             ${regret_v60:>9.2f}/1000h prefix")
        print(f"  LIFT v60 over v57:      ${lift_dol:>+9.2f}/1000h prefix")
        print(f"  >>> VERDICT: {verdict}")
        print(f"  wall: {elapsed:.1f}s", flush=True)

        per_gate[str(gate)] = {
            "gate_max_sing": gate,
            "n_fired": n_fired,
            "n_changed": n_changed,
            "n_v60_closer": n_v60_closer,
            "n_v60_worse": n_v60_worse,
            "swap_right_rate_pct": n_v60_closer / max(n_changed, 1) * 100,
            "v57_match_pct": n_v57_match / n_eval * 100,
            "v60_match_pct": n_v60_match / n_eval * 100,
            "v57_regret_dol_per_1000h_prefix": regret_v57,
            "v60_regret_dol_per_1000h_prefix": regret_v60,
            "lift_dol_per_1000h_prefix": lift_dol,
            "verdict": verdict,
        }

    sorted_gates = sorted(per_gate.values(),
                          key=lambda d: -d["lift_dol_per_1000h_prefix"])
    best = sorted_gates[0]
    print(f"\n" + "="*70)
    print(f"BEST GATE (by PREFIX lift): max_sing ≤ {best['gate_max_sing']}")
    print(f"  Lift over v57 (prefix): ${best['lift_dol_per_1000h_prefix']:+.2f}/1000h")
    print(f"  Verdict:                {best['verdict']}")
    print(f"="*70)

    out = {
        "session": 86,
        "phase": "C-prefix-multigate",
        "n_eval": n_eval,
        "ship_threshold": SHIP_LIFT_DOL_PER_1000H,
        "null_threshold": NULL_LIFT_DOL_PER_1000H,
        "per_gate": per_gate,
        "best_gate": best,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nsummary written to {OUT_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
