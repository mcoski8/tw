"""
Session 63 — Rule 17 cell-by-cell audit + sanity check.

Phase 2 sanity check: Rule 17 (J-high HIMID, inlined into
strategy_v48_rules17_21_high_only_HIMID) vs its pre-Rule-17 predecessor
(strategy_v47_rule16_Qhigh_DS) on all 6 J-high cells. Expect total
whole-grid lift ≈ +$17/1000h (S53 shipped lift), within ±10%
(i.e., $15.30 to $18.70).

NOTE on Rule 24 overlap: v48 fires Rule 17 (J-HIMID) on EVERY J-high
hand. v52 superseded that with Rule 24 (defensive lowest-on-top) when
s2 ≤ 8. The +$17 "shipped lift" was measured when v48 was the
strategy — i.e., on the whole J-high zone w/o Rule 24 carve-out — so
the standard v48 vs v47 comparison reproduces it.

Phase 2b audit: how much does v52 (= Rule 17 on s2>8 J-high + Rule 24
on s2≤8 J-high) leak per cell to oracle? Identify leaky cells. Also
report a separate s2 > 8 subset slice to disambiguate Rule 17 vs
Rule 24 fire regions.
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

from test_rule_catalog import test_rule_on_cell, ALL_CELLS, _load_data  # noqa: E402
from strategy_v48_rules17_21_high_only_HIMID import strategy_v48_rules17_21_high_only_HIMID  # noqa: E402
from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402
from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402

J = 11


def sanity_rule17():
    """Sanity: strategy_v48 (= v47 + Rules 17-21) vs strategy_v47 on
    J-high (max=11). On max=11 v48 fires Rule 17 on every hand; v47
    does nothing. Difference is Rule 17's shipped lift.
    """
    print("=" * 88)
    print("PHASE 2 SANITY — Rule 17 vs pre-Rule-17 predecessor (v47_rule16_Qhigh_DS)")
    print("Strategy v48 inlines Rules 17-21; on max=J only Rule 17 fires.")
    print("Expected: ~+$17/1000h whole-grid on J-high (S53 shipped lift).")
    print("Acceptance window: $15.30 to $18.70 (±10%).")
    print("=" * 88)
    total_wg = 0.0
    total_n = 0
    rows = []
    for cell in ALL_CELLS:
        try:
            r = test_rule_on_cell(
                rule_fn=strategy_v48_rules17_21_high_only_HIMID,
                max_rank=J,
                cell=cell,
                baseline_fn=strategy_v47_rule16_Qhigh_DS,
                label=f"sanity_rule17/{cell}",
                progress=False,
            )
            r.print_summary()
            total_wg += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
            rows.append((cell, r.n_hands, r.lift_vs_baseline_whole_grid))
        except ValueError as e:
            print(f"  [skip] cell={cell}: {e}")

    print(f"\n  ==> Phase 2 sanity total J-high whole-grid lift: ${total_wg:+.2f}/1000h "
          f"(n={total_n:,})")
    print("      Expected ~+$17/1000h. Acceptance window: $15.30 to $18.70.")
    print("\n  Per-cell sanity contribution to whole-grid lift:")
    for cell, n, wg in rows:
        print(f"    {cell:<14}  n={n:>7,}  +${wg:+7.2f}/1000h WG")
    return total_wg


def audit_v52_J_high():
    """Audit v52 cell-by-cell on J-high. baseline=rule_fn=v52 means
    lift_vs_baseline = 0 by construction; we read rule_mean_ev vs oracle
    to find leaky cells.

    Note: v52 on J-high is a *mixture* — Rule 17 (J-on-top HIMID) fires
    on s2 > 8 hands, Rule 24 (defensive lowest-on-top) on s2 ≤ 8.
    """
    print("\n" + "=" * 88)
    print("PHASE 2b AUDIT — v52 vs oracle on J-high cells")
    print("(baseline = rule = v52; mean_ev gap to oracle read directly)")
    print("=" * 88)

    rows = []
    for cell in ALL_CELLS:
        try:
            r = test_rule_on_cell(
                rule_fn=strategy_v52_full_high_only_handler,
                max_rank=J,
                cell=cell,
                baseline_fn=strategy_v52_full_high_only_handler,
                label=f"audit_v52_J/{cell}",
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

    print("\n  J-high audit summary table:")
    print(f"    {'cell':<14} {'n':>8} {'v52_gap_$/1k_within':>22} "
          f"{'v52_gap_$/1k_WG':>18} {'v44_gap_$/1k_WG':>18}")
    total_v52_wg = 0.0
    total_v44_wg = 0.0
    for r in rows:
        total_v52_wg += r["gap_wg"]
        total_v44_wg += r["v44_gap_wg"]
        print(f"    {r['cell']:<14} {r['n_hands']:>8,} ${r['gap_within']:>19.1f}    "
              f"${r['gap_wg']:>15.2f}    ${r['v44_gap_wg']:>15.2f}")
    print(f"\n  J-high TOTAL: v52→oracle gap ${total_v52_wg:.2f}/1000h WG  |  "
          f"v44→oracle gap ${total_v44_wg:.2f}/1000h WG")
    return rows


def disambiguate_rule17_vs_rule24():
    """Slice J-high by s2 (second-highest rank) to disambiguate Rule 17
    (offensive, s2 > 8) vs Rule 24 (defensive, s2 ≤ 8) fire regions.

    Uses the parquet's per-row data directly rather than the test harness
    since this is just a population/leak split, not a rule comparison.
    """
    print("\n" + "=" * 88)
    print("PHASE 2c — Rule 17 vs Rule 24 fire-region disambiguation on J-high")
    print("Split J-high by s2 (second-highest rank): s2 ≤ 8 → Rule 24,")
    print("s2 > 8 → Rule 17.")
    print("=" * 88)

    data = _load_data()
    df = data["df"]
    ch = data["ch"]
    gf = data["gf"]

    mask = (df["max_rank"].to_numpy() == J)
    sub = df[mask].reset_index(drop=True)
    n = len(sub)
    cids = sub["canonical_id"].to_numpy()
    oracle_idxs = sub["oracle_idx"].to_numpy()
    v44_idxs = sub["v44_idx"].to_numpy()

    # Compute s2 (second-highest rank) for each hand
    s2_arr = np.zeros(n, dtype=np.int16)
    v52_evs = np.empty(n, dtype=np.float64)
    oracle_evs = np.empty(n, dtype=np.float64)
    v44_evs = np.empty(n, dtype=np.float64)
    for i in range(n):
        cid = int(cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        sr = sorted(int(r) for r in ranks)
        s2_arr[i] = sr[-2]
        rowf = gf.evs[cid]
        v52_idx = int(strategy_v52_full_high_only_handler(h))
        v52_evs[i] = float(rowf[v52_idx])
        oracle_evs[i] = float(rowf[int(oracle_idxs[i])])
        v44_evs[i] = float(rowf[int(v44_idxs[i])])

    EV_TO_DOL = 10.0
    N_TOTAL = 6_009_159
    for label, mask_subset in [
        ("ALL J-high",       np.ones(n, dtype=bool)),
        ("J-high s2 > 8  (Rule 17 fire region)",   s2_arr > 8),
        ("J-high s2 <= 8 (Rule 24 fire region)", s2_arr <= 8),
    ]:
        nn = int(mask_subset.sum())
        if nn == 0:
            print(f"  [{label}] empty")
            continue
        v52_m = v52_evs[mask_subset].mean()
        ora_m = oracle_evs[mask_subset].mean()
        v44_m = v44_evs[mask_subset].mean()
        gap_within = (ora_m - v52_m) * EV_TO_DOL * 1000
        gap_wg = (ora_m - v52_m) * EV_TO_DOL * 1000 * nn / N_TOTAL
        v44_gap_within = (ora_m - v44_m) * EV_TO_DOL * 1000
        v44_gap_wg = (ora_m - v44_m) * EV_TO_DOL * 1000 * nn / N_TOTAL
        print(f"\n  [{label}]  n={nn:,}  ({100*nn/n:.1f}% of J-high)")
        print(f"    mean_ev: v52={v52_m:+.4f}  v44={v44_m:+.4f}  oracle={ora_m:+.4f}")
        print(f"    v52 gap: ${gap_within:8.1f}/1000h within  ${gap_wg:7.2f}/1000h WG")
        print(f"    v44 gap: ${v44_gap_within:8.1f}/1000h within  ${v44_gap_wg:7.2f}/1000h WG")


if __name__ == "__main__":
    print("\n" + "*" * 88)
    print("Session 63 — Rule 17 sanity + J-high cell audit")
    print("*" * 88 + "\n")
    sanity_total = sanity_rule17()
    audit_rows = audit_v52_J_high()
    disambiguate_rule17_vs_rule24()
    print("\n" + "*" * 88)
    print(f"Sanity check total: ${sanity_total:+.2f}/1000h "
          f"(target ~$17, acceptance $15.30–$18.70)")
    if 15.30 <= sanity_total <= 18.70:
        print("ACCEPTED.")
    else:
        print("OUTSIDE WINDOW — investigate harness or strategy delta before proceeding.")
    print("*" * 88)
