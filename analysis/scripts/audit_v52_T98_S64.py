"""
Session 64 — Phase 2: v52 audit at T/9/8-high.

Goals:
  1. Sanity-check Rules 25/26/27 by reproducing v52 vs v47 across max ∈ {10, 9, 8}.
     Expected: T ~+$8, 9 ~+$3, 8 ~+$0.6 (per S53 OVERNIGHT report attribution).
  2. Cell-by-cell audit of v52 vs oracle (and vs v44) at each of T/9/8.
     Reports within-cell gap, WG gap, v44 catch-up.

Reuses the test_rule_catalog harness verbatim. Total runtime <1 minute since
the combined T/9/8 population is only 25,740 hands.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_rule_catalog import (  # noqa: E402
    _load_data,
    test_rule_on_cell,
    ALL_CELLS,
    RANK_CHAR,
)
from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402
from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402

EV_TO_DOL = 10.0
N_TOTAL = 6_009_159


def compare_v52_v47_by_max(ch, gf, cids, max_arr, max_rank: int) -> dict:
    """v52 vs v47 lift at a given max_rank. Returns dict with WG, within-pop $, n."""
    mask = max_arr == max_rank
    idxs = np.where(mask)[0]
    n = len(idxs)
    if n == 0:
        return {"max_rank": max_rank, "n": 0, "wg": 0.0, "within": 0.0}
    v52_evs = np.empty(n, dtype=np.float64)
    v47_evs = np.empty(n, dtype=np.float64)
    for k, i in enumerate(idxs):
        cid = int(cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        v52_evs[k] = float(gf.evs[cid][int(strategy_v52_full_high_only_handler(h))])
        v47_evs[k] = float(gf.evs[cid][int(strategy_v47_rule16_Qhigh_DS(h))])
    within = (v52_evs.mean() - v47_evs.mean()) * EV_TO_DOL * 1000
    wg = (v52_evs - v47_evs).sum() * EV_TO_DOL * 1000 / N_TOTAL
    return {"max_rank": max_rank, "n": n,
            "within_pop": within, "wg": wg,
            "v52_mean_ev": float(v52_evs.mean()),
            "v47_mean_ev": float(v47_evs.mean())}


def phase2_sanity() -> dict:
    """Sanity: v52 vs v47 per max_rank ∈ {10, 9, 8, 7}. Compare to S53 expectation."""
    print("=" * 88)
    print("Session 64 Phase 2 — v52 vs v47 by max_rank (Rules 25/26/27 attribution)")
    print("=" * 88)
    print("S53 OVERNIGHT expectation: T ~+$8.24, 9 ~+$3.26, 8 ~+$0.56 (per CURRENT_PHASE).")
    print()
    data = _load_data()
    df = data["df"]; ch = data["ch"]; gf = data["gf"]
    cids = df["canonical_id"].to_numpy()
    max_arr = df["max_rank"].to_numpy()

    results = {}
    total_wg = 0.0
    for mr in [10, 9, 8, 7]:
        r = compare_v52_v47_by_max(ch, gf, cids, max_arr, mr)
        results[mr] = r
        if r["n"] > 0:
            print(f"  max={RANK_CHAR[mr]}  n={r['n']:>7,}  "
                  f"within_pop=${r['within_pop']:+8.2f}/1000h  "
                  f"WG=${r['wg']:+7.2f}/1000h")
            total_wg += r["wg"]
        else:
            print(f"  max={RANK_CHAR[mr]}  (empty)")
    print(f"  ====================================================================")
    print(f"  TOTAL T/9/8/7 WG = ${total_wg:+.2f}/1000h")
    print(f"  Expected ≈ $8.24 + $3.26 + $0.56 + (~$0 for 7) ≈ $12.06.")
    return results


def phase2_cell_audit(max_rank: int) -> dict:
    """Cell-by-cell audit at a given max_rank. Reports v52→oracle gap and
    v52→v44 catch-up per cell."""
    print()
    print("-" * 88)
    print(f"  Cell-by-cell audit on max={RANK_CHAR[max_rank]}-high")
    print("-" * 88)
    results = {}
    total_gap_wg = 0.0
    total_v44_gap_wg = 0.0
    for cell in ALL_CELLS:
        try:
            # baseline = v52 (= "what's already in chain"); rule = v52 (no-op rule)
            r = test_rule_on_cell(
                rule_fn=strategy_v52_full_high_only_handler,
                max_rank=max_rank,
                cell=cell,
                baseline_fn=strategy_v52_full_high_only_handler,
                label=f"v52/max={RANK_CHAR[max_rank]}/{cell}",
                progress=False,
            )
            gap_within = (r.oracle_ceiling_ev - r.baseline_mean_ev) * EV_TO_DOL * 1000
            gap_wg = (r.oracle_ceiling_ev - r.baseline_mean_ev) * r.n_hands * EV_TO_DOL * 1000 / N_TOTAL
            v44_gap_within = (r.oracle_ceiling_ev - r.v44_mean_ev) * EV_TO_DOL * 1000
            v44_gap_wg = (r.oracle_ceiling_ev - r.v44_mean_ev) * r.n_hands * EV_TO_DOL * 1000 / N_TOTAL
            print(f"  cell={cell:<14} n={r.n_hands:>6,}  "
                  f"v52_ev={r.baseline_mean_ev:+.4f}  oracle_ev={r.oracle_ceiling_ev:+.4f}  "
                  f"gap=${gap_within:>+8.2f}/1k  WG=${gap_wg:>+7.2f}  "
                  f"v44_gap_WG=${v44_gap_wg:>+6.2f}")
            results[cell] = {
                "n": r.n_hands,
                "v52_mean_ev": r.baseline_mean_ev,
                "oracle_mean_ev": r.oracle_ceiling_ev,
                "v44_mean_ev": r.v44_mean_ev,
                "gap_within_cell": gap_within,
                "gap_wg": gap_wg,
                "v44_gap_within_cell": v44_gap_within,
                "v44_gap_wg": v44_gap_wg,
            }
            total_gap_wg += gap_wg
            total_v44_gap_wg += v44_gap_wg
        except ValueError as e:
            print(f"  cell={cell:<14} (empty: {e})")
    print(f"  --------------------------------------------------------------")
    print(f"  TOTAL max={RANK_CHAR[max_rank]}: gap_to_oracle_WG=${total_gap_wg:+.2f}  "
          f"v44_gap_WG=${total_v44_gap_wg:+.2f}")
    return results


def main():
    # Phase 2a — Rules 25/26/27 sanity check
    sanity = phase2_sanity()

    # Phase 2b — Cell-by-cell audit per max_rank
    cell_audits = {}
    for mr in [10, 9, 8]:
        cell_audits[mr] = phase2_cell_audit(mr)

    print()
    print("=" * 88)
    print("Phase 2 SUMMARY")
    print("=" * 88)
    print()
    print("Rules 25/26/27 attribution (v52 vs v47 by max_rank):")
    for mr in [10, 9, 8, 7]:
        if mr in sanity and sanity[mr]["n"] > 0:
            print(f"  max={RANK_CHAR[mr]}  n={sanity[mr]['n']:>6,}  "
                  f"WG=${sanity[mr]['wg']:+7.2f}/1000h")

    print()
    print("Cell distribution and v52→oracle gap (by max_rank × cell):")
    print(f"  {'max':>4} {'cell':<14} {'n':>7} {'gap_within':>12} {'gap_WG':>9} {'v44_gap_WG':>11}")
    for mr in [10, 9, 8]:
        for cell, ca in cell_audits[mr].items():
            print(f"  {RANK_CHAR[mr]:>4} {cell:<14} {ca['n']:>7,} "
                  f"${ca['gap_within_cell']:>+10.2f} ${ca['gap_wg']:>+7.2f} "
                  f"${ca['v44_gap_wg']:>+9.2f}")


if __name__ == "__main__":
    main()
