"""
Session 61 — Rule 15 cell-by-cell audit + sanity check.

Phase 2 sanity check: Rule 15 (strategy_v46_rule15_Khigh_DS) vs its
pre-Rule-15 predecessor (strategy_v45_rule14_Ahigh_DS) on all 6 K-high
cells. Expect total whole-grid lift ≈ +$51/1000h (S51 shipped lift),
within ±10% (i.e., $46–$56).

Phase 2b audit: how much does v52 (= Rule 15 on K-high since v52's
defensive triggers don't fire for K-high with s2 > 8) leak per cell to
oracle? Identify leaky cells (expected: K × DS_NO_JOINT dominant).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_rule_catalog import test_rule_on_cell, ALL_CELLS  # noqa: E402
from strategy_v46_rule15_Khigh_DS import strategy_v46_rule15_Khigh_DS  # noqa: E402
from strategy_v45_rule14_Ahigh_DS import strategy_v45_rule14_Ahigh_DS  # noqa: E402
from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402

K = 13


def sanity_rule15():
    print("=" * 88)
    print("PHASE 2 SANITY — Rule 15 vs pre-Rule-15 predecessor (v45_rule14_Ahigh_DS)")
    print("Expected: ~+$51/1000h whole-grid on K-high (S51 shipped lift).")
    print("=" * 88)
    total_wg = 0.0
    total_n = 0
    rows = []
    for cell in ALL_CELLS:
        try:
            r = test_rule_on_cell(
                rule_fn=strategy_v46_rule15_Khigh_DS,
                max_rank=K,
                cell=cell,
                baseline_fn=strategy_v45_rule14_Ahigh_DS,
                label=f"sanity_rule15/{cell}",
                progress=False,
            )
            r.print_summary()
            total_wg += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
            rows.append((cell, r.n_hands, r.lift_vs_baseline_whole_grid))
        except ValueError as e:
            print(f"  [skip] cell={cell}: {e}")

    print(f"\n  ==> Phase 2 sanity total K-high whole-grid lift: ${total_wg:+.2f}/1000h "
          f"(n={total_n:,})")
    print("      Expected ~+$51/1000h. Acceptance window: $46 to $56.")
    print("\n  Per-cell sanity contribution to whole-grid lift:")
    for cell, n, wg in rows:
        print(f"    {cell:<14}  n={n:>7,}  +${wg:+7.2f}/1000h WG")
    return total_wg


def audit_v52_K_high():
    """Audit v52 cell-by-cell on K-high. baseline=rule_fn=v52 means
    lift_vs_baseline = 0 by construction; we read rule_mean_ev vs oracle
    to find leaky cells."""
    print("\n" + "=" * 88)
    print("PHASE 2b AUDIT — v52 vs oracle on K-high cells")
    print("(baseline = rule = v52, so we read mean_ev gap to oracle directly)")
    print("=" * 88)

    rows = []
    for cell in ALL_CELLS:
        try:
            r = test_rule_on_cell(
                rule_fn=strategy_v52_full_high_only_handler,
                max_rank=K,
                cell=cell,
                baseline_fn=strategy_v52_full_high_only_handler,
                label=f"audit_v52_K/{cell}",
                progress=False,
            )
            print(f"\n  Cell={cell:<14} n={r.n_hands:>7,}  "
                  f"v52_mean_ev={r.rule_mean_ev:+.4f}  "
                  f"v44_mean_ev={r.v44_mean_ev:+.4f}  "
                  f"oracle={r.oracle_ceiling_ev:+.4f}")
            gap_within = (r.oracle_ceiling_ev - r.rule_mean_ev) * 10000
            gap_wg = (r.oracle_ceiling_ev - r.rule_mean_ev) * 10000 * r.n_hands / 6_009_159
            v44_gap_within = (r.oracle_ceiling_ev - r.v44_mean_ev) * 10000
            v44_gap_wg = (r.oracle_ceiling_ev - r.v44_mean_ev) * 10000 * r.n_hands / 6_009_159
            print(f"    v52_gap: ${gap_within:7.1f}/1000h within-cell  "
                  f"${gap_wg:6.2f}/1000h WG")
            print(f"    v44_gap: ${v44_gap_within:7.1f}/1000h within-cell  "
                  f"${v44_gap_wg:6.2f}/1000h WG")
            print(f"    pct_optimal: v52={r.rule_pct_optimal:.2f}%  "
                  f"v44={r.v44_pct_optimal:.2f}%")
            rows.append({
                "cell": cell, "n_hands": r.n_hands,
                "v52_mean": r.rule_mean_ev, "v44_mean": r.v44_mean_ev,
                "oracle": r.oracle_ceiling_ev,
                "gap_within": gap_within, "gap_wg": gap_wg,
                "v44_gap_within": v44_gap_within, "v44_gap_wg": v44_gap_wg,
                "v52_pct": r.rule_pct_optimal, "v44_pct": r.v44_pct_optimal,
            })
        except ValueError as e:
            print(f"  [skip] cell={cell}: {e}")

    print("\n  K-high audit summary table:")
    print(f"    {'cell':<14} {'n':>8} {'v52_gap_$/1k_within':>22} "
          f"{'v52_gap_$/1k_WG':>18} {'v44_gap_$/1k_WG':>18}")
    total_v52_wg = 0.0
    total_v44_wg = 0.0
    for r in rows:
        total_v52_wg += r["gap_wg"]
        total_v44_wg += r["v44_gap_wg"]
        print(f"    {r['cell']:<14} {r['n_hands']:>8,} ${r['gap_within']:>19.1f}    "
              f"${r['gap_wg']:>15.2f}    ${r['v44_gap_wg']:>15.2f}")
    print(f"\n  K-high TOTAL: v52→oracle gap ${total_v52_wg:.2f}/1000h WG  |  "
          f"v44→oracle gap ${total_v44_wg:.2f}/1000h WG")
    return rows


if __name__ == "__main__":
    print("\n" + "*" * 88)
    print("Session 61 — Rule 15 sanity + K-high cell audit")
    print("*" * 88 + "\n")
    sanity_total = sanity_rule15()
    audit_rows = audit_v52_K_high()
    print("\n" + "*" * 88)
    print(f"Sanity check total: ${sanity_total:+.2f}/1000h "
          f"(target ~$51, acceptance $46–$56)")
    if 46.0 <= sanity_total <= 56.0:
        print("ACCEPTED.")
    else:
        print("REJECTED — investigate harness or strategy delta before proceeding.")
    print("*" * 88)
