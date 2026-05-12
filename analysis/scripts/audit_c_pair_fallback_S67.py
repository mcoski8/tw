"""
Session 67 Phase 3 — fallback experiments after C_PAIR_3 falsification.

Tests two follow-ups:
  1. C_PAIR_3b at stricter mid thresholds (T=13=K, T=14=A) — does
     a stronger "mid must be very high" gate make blanket PBOT-take
     EV-positive?
  2. C_PAIR_5 — Q-pair-only PBOT-take on PBOT_DS_PARTIAL (where the
     v52 baseline residual is the single largest pair cell at $54 WG).

If either clears T2 we proceed to non-targeted regression. If both T3
the verdict is "pair PBOT-routing is ML-only at catalog granularity"
(mirrors high_only S60-S64 outcome).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis" / "src"))

from test_rule_catalog_pair import test_rule_on_cell, RANK_CHAR  # noqa: E402
from strategy_v53_c_pair_3 import (  # noqa: E402
    _enumerate_pbot_ds, _choose_best_pbot_ds_config, _build_setting_from_config,
    make_rule_c_pair_3b,
)


# -- C_PAIR_5: Q-pair PBOT-take on PBOT_DS_PARTIAL (and JOINT for completeness)
def rule_c_pair_5_qpair(hand_bytes: np.ndarray) -> Optional[int]:
    """Q-pair AND PBOT_DS achievable → take best pair-to-bot-DS construction."""
    info = _enumerate_pbot_ds(hand_bytes, allowed_pair_ranks={12})
    if info is None:
        return None
    cfg = _choose_best_pbot_ds_config(info)
    if cfg is None:
        return None
    return _build_setting_from_config(info, cfg)


def rule_c_pair_5_qpair_joint(hand_bytes: np.ndarray) -> Optional[int]:
    """Q-pair + JOINT only."""
    info = _enumerate_pbot_ds(hand_bytes, allowed_pair_ranks={12})
    if info is None:
        return None
    joints = [c for c in info["configs"] if c["joint"]]
    if not joints:
        return None
    cfg = max(joints, key=lambda c: c["mid_high"])
    return _build_setting_from_config(info, cfg)


def run_audit(rule_fn, label, pair_ranks, cells):
    print("\n" + "=" * 90)
    print(f"AUDITING: {label}")
    print("=" * 90)
    total_wg = 0.0
    total_n = 0
    total_fires = 0
    weighted_cap_sum = 0.0
    weighted_cap_w = 0.0
    by_cell = {}
    for pr in pair_ranks:
        for cell in cells:
            try:
                r = test_rule_on_cell(rule_fn, pr, cell,
                                      label=f"{label}/p{RANK_CHAR[pr]}/{cell}")
            except ValueError as e:
                print(f"  [skip] (pair={RANK_CHAR[pr]}, cell={cell}): {e}")
                continue
            r.print_summary()
            total_wg += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
            total_fires += r.n_rule_fires
            gap_w = max(r.oracle_ceiling_ev - r.baseline_mean_ev, 0)
            weighted_cap_sum += r.capture_pct_vs_baseline * gap_w * r.n_hands
            weighted_cap_w += gap_w * r.n_hands
            by_cell[f"p{RANK_CHAR[pr]}|{cell}"] = {
                "n_hands": r.n_hands,
                "n_rule_fires": r.n_rule_fires,
                "fire_pct": 100 * r.n_rule_fires / r.n_hands,
                "capture_vs_baseline_pct": r.capture_pct_vs_baseline,
                "lift_within_cell_per_1000h": r.lift_vs_baseline_within_cell,
                "lift_whole_grid_per_1000h": r.lift_vs_baseline_whole_grid,
            }
    cap_w = weighted_cap_sum / weighted_cap_w if weighted_cap_w > 0 else 0.0
    t1_ok = (cap_w >= 40.0) and (total_wg > 0)
    t2_ok = t1_ok and (total_wg >= 5.0)
    if t2_ok:
        verdict = "T2 — production-ship CANDIDATE"
    elif t1_ok:
        verdict = "T1 — catalog-worthy"
    elif total_wg > 0:
        verdict = "Below T1 — positive but small or low-capture"
    else:
        verdict = "T3 — net-negative"
    print(f"\n  {label} AGGREGATE")
    print(f"    n_hands              : {total_n:,}")
    print(f"    n_rule_fires         : {total_fires:,} ({100*total_fires/max(total_n,1):.1f}%)")
    print(f"    weighted-avg capture : {cap_w:+.2f}%")
    print(f"    SUM whole-grid lift  : ${total_wg:+.2f}/1000h WG")
    print(f"    VERDICT              : {verdict}")
    return {
        "label": label,
        "total_n_hands": total_n,
        "total_n_rule_fires": total_fires,
        "weighted_avg_capture_pct": cap_w,
        "total_wg_lift_per_1000h": total_wg,
        "verdict": verdict,
        "by_cell": by_cell,
    }


def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 90)
    print("Session 67 Phase 3 — fallback experiments")
    print(f"Started: {started}")
    print("=" * 90)

    results = {}

    # (1) C_PAIR_3b with stricter mid threshold T=13=K
    print("\n## Block 1: C_PAIR_3b at higher mid thresholds (sub-variant tightening)")
    for t_mid in [12, 13, 14]:  # Q, K, A
        rule = make_rule_c_pair_3b(t_mid)
        label = f"C_PAIR_3b (mid≥{RANK_CHAR[t_mid]})"
        results[label] = run_audit(
            rule, label,
            pair_ranks=[6, 7, 8, 9],
            cells=["PBOT_DS_JOINT", "PBOT_DS_PARTIAL"],
        )

    # (2) C_PAIR_5: Q-pair PBOT-take
    print("\n## Block 2: C_PAIR_5 (Q-pair PBOT-take)")
    results["C_PAIR_5_qpair_simple"] = run_audit(
        rule_c_pair_5_qpair, "C_PAIR_5 (Q-pair simple)",
        pair_ranks=[12],
        cells=["PBOT_DS_JOINT", "PBOT_DS_PARTIAL"],
    )
    results["C_PAIR_5_qpair_joint"] = run_audit(
        rule_c_pair_5_qpair_joint, "C_PAIR_5 (Q-pair joint-only)",
        pair_ranks=[12],
        cells=["PBOT_DS_JOINT", "PBOT_DS_PARTIAL"],
    )

    out_path = ROOT / "data" / "session67" / "c_pair_fallback_summary.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Wrote summary JSON: {out_path}")

    print("\n" + "=" * 90)
    print("FINAL TABLE — fallback variants")
    print("=" * 90)
    print(f"  {'variant':<40} {'fires':>9} {'capture':>9} {'WG lift':>12} {'verdict':<20}")
    for label, summ in results.items():
        print(f"  {label:<40} {summ['total_n_rule_fires']:>9,} "
              f"{summ['weighted_avg_capture_pct']:>+8.2f}% "
              f"${summ['total_wg_lift_per_1000h']:>+10.2f} "
              f"{summ['verdict'][:19]:<20}")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
