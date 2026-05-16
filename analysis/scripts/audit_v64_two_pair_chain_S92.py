"""S92 — chain audit: layer-by-layer attribution for two_pair cells.

The S87/S88/S89/S90/S91 chain-audit pattern, transferred to two_pair. The
production chain for two_pair hands is:

  v64 ── HIGH_ONLY gate-out (doesn't fire on two_pair)
   └── v57 ── LOW single-pair PMID Rule 29 (doesn't fire on two_pair)
        └── v56 ── trips_hybrid (doesn't fire on two_pair)
             └── v55 ── two_pair_hybrid: BLANKET routes all two_pair → v44_dt
                  └── v54 ── pair_hybrid: PBOT_DS single-pair only (no fire)
                       └── v53 ── qpair_joint_pbot (no fire)
                            └── v52 ── HIGH_ONLY handler (rc==2 gate, no fire)
                                 └── v51 ── (HIGH_ONLY)
                                      └── v50/v48/v47/v46/v45 (HIGH_ONLY)
                                           └── v44_RULE13 ── three_pair_DS handler
                                                └── v43 ── two_pair_DS_intact (the
                                                     v44_RULE13 chain layer that
                                                     would activate WITHIN v44_RULE13)
                                                     └── ... base chain

For two_pair hands, the chain machinery is DIFFERENT from the LOW pair
case in S91:

  * In S91 (LOW pair), v54 routes PBOT_DS two thirds of cells to v44_dt
    SELECTIVELY. The PMID cells fall through to v53/v52/.../v44_RULE13.
    The chain ACTIVELY DOES WORK on PMID cells.

  * In S92 (two_pair), v55 routes 100% of two_pair to v44_dt
    UNCONDITIONALLY. The chain NEVER activates on production picks.

Therefore the chain audit shows ABSORPTION, not residual bleed:

  v44_dt          : ML champion baseline
  v44_RULE13      : the chain fallthrough pick (= what v54 returns for
                    two_pair, since pair-gate is single-pair-only)
                    Predicted: LARGE BLEED vs v44_dt — same architectural
                    pattern as S91 LOW pair.
  v54             : ≡ v44_RULE13 on two_pair (pair gate doesn't fire)
                    Predicted: Δ_v54_vs_v44_RULE = $0.00
  v55             : v55's blanket routing → v44_dt on every two_pair
                    Predicted: Δ_v55_vs_v54 = -ALL_OF_THE_BLEED
                    Predicted: v55 leak ≡ v44_dt leak
  v56             : trips gate doesn't fire on two_pair
                    Predicted: Δ_v56_vs_v55 = $0.00
  v57             : LOW single-pair gate doesn't fire on two_pair
                    Predicted: Δ_v57_vs_v56 = $0.00
  v64             : HIGH_ONLY gate doesn't fire on two_pair
                    Predicted: Δ_v64_vs_v57 = $0.00

CRITICAL CONCLUSION: The chain-audit pattern cannot find a SHIP candidate
within two_pair. v55 has already collapsed the chain. Any v65 candidate
would need to beat v44_dt on a sub-cell — that's NOT chain-audit; that's
rule extraction (Option D-revised pattern), and S69 already confirmed v44
dominates every two_pair cell.

This script PRODUCES the architectural snapshot:
  - Quantify v44_RULE13 chain bleed magnitude on two_pair (vs v44_dt)
  - Confirm v55 absorbs 100% of it
  - Confirm v56/v57/v64 are inert on two_pair
  - Per-cell × hi_pair × max_sing breakdown for the snapshot
"""
from __future__ import annotations

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
from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v44_rule13_three_pair_DS import (  # noqa: E402
    strategy_v44_rule13_three_pair_DS,
)
from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid  # noqa: E402
from strategy_v55_two_pair_hybrid import (  # noqa: E402
    strategy_v55_two_pair_hybrid,
)
from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v64_high_only_chain_fix_zone import (  # noqa: E402
    strategy_v64_high_only_chain_fix_zone,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
PARQUET_TWO_PAIR = ROOT / "data" / "drill_two_pair_v44_per_hand_structural.parquet"

EV_TO_DOL = 10.0
N_PREFIX = 500_000

CELL_NAMES = {0: "LAYOUT_A_DS", 1: "LAYOUT_C_DS",
              2: "LAYOUT_B_DS", 3: "LAYOUT_A_SS",
              4: "LAYOUT_C_SS_ONLY", 5: "LAYOUT_B_SS_ONLY"}


def main() -> int:
    print("=" * 130)
    print("S92 chain audit — two_pair, layer-by-layer attribution (N=1000 prefix)")
    print("=" * 130)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/3] loading two_pair × prefix subset ...", flush=True)
    table = pq.read_table(
        PARQUET_TWO_PAIR,
        columns=["canonical_id", "hi_pair_rank", "lo_pair_rank",
                 "max_sing_rank", "cell_idx", "v44_idx", "regret"]
    )
    df = table.to_pandas()
    df = df[df["canonical_id"] < N_PREFIX].reset_index(drop=True)
    print(f"  loaded {len(df):,} two_pair × prefix hands")
    print()

    print("[2/3] evaluating layer strategies + EV on prefix grid ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    n = len(df)
    v44_dt_idx = df["v44_idx"].to_numpy()
    v44_rule_idx = np.zeros(n, dtype=np.int16)
    v54_idx = np.zeros(n, dtype=np.int16)
    v55_idx = np.zeros(n, dtype=np.int16)
    v56_idx = np.zeros(n, dtype=np.int16)
    v57_idx = np.zeros(n, dtype=np.int16)
    v64_idx = np.zeros(n, dtype=np.int16)

    ev_v44_dt = np.zeros(n, dtype=np.float32)
    ev_v44_rule = np.zeros(n, dtype=np.float32)
    ev_v54 = np.zeros(n, dtype=np.float32)
    ev_v55 = np.zeros(n, dtype=np.float32)
    ev_v56 = np.zeros(n, dtype=np.float32)
    ev_v57 = np.zeros(n, dtype=np.float32)
    ev_v64 = np.zeros(n, dtype=np.float32)
    ev_best = np.zeros(n, dtype=np.float32)

    cids = df["canonical_id"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowp = np.asarray(gp.evs[cid], dtype=np.float64)
        ev_best[k] = float(rowp.max())
        ev_v44_dt[k] = float(rowp[int(v44_dt_idx[k])])
        i_rule = int(strategy_v44_rule13_three_pair_DS(h))
        i_v54 = int(strategy_v54_pair_hybrid(h))
        i_v55 = int(strategy_v55_two_pair_hybrid(h))
        i_v56 = int(strategy_v56_trips_hybrid(h))
        i_v57 = int(strategy_v57_lo_pair_defensive(h))
        i_v64 = int(strategy_v64_high_only_chain_fix_zone(h))
        v44_rule_idx[k] = i_rule
        v54_idx[k] = i_v54
        v55_idx[k] = i_v55
        v56_idx[k] = i_v56
        v57_idx[k] = i_v57
        v64_idx[k] = i_v64
        ev_v44_rule[k] = float(rowp[i_rule])
        ev_v54[k] = float(rowp[i_v54])
        ev_v55[k] = float(rowp[i_v55])
        ev_v56[k] = float(rowp[i_v56])
        ev_v57[k] = float(rowp[i_v57])
        ev_v64[k] = float(rowp[i_v64])
        if (k + 1) % 25_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>9,}/{n:,}  rate={rate:>5.0f}/s  ETA={eta:>4.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    df["regret_v44_dt"] = ev_best - ev_v44_dt
    df["regret_v44_rule"] = ev_best - ev_v44_rule
    df["regret_v54"] = ev_best - ev_v54
    df["regret_v55"] = ev_best - ev_v55
    df["regret_v56"] = ev_best - ev_v56
    df["regret_v57"] = ev_best - ev_v57
    df["regret_v64"] = ev_best - ev_v64

    print("[3/3] results — layer transitions per cell × max_sing")
    print("=" * 145)
    print("LAYER TRANSITIONS (prefix N=1000, /1000h leak on prefix subset)")
    print("Format: $ leak per layer; Δ shows whether transition LIFTS (negative) or BLEEDS (positive).")
    print("  v44_dt:   strategy_v44_dt (ML champion)")
    print("  v44_RULE: strategy_v44_rule13_three_pair_DS (chain fallthrough)")
    print("  v54:      pair_hybrid (single-pair PBOT_DS → v44_dt; no fire on two_pair)")
    print("  v55:      two_pair_hybrid (BLANKET two_pair → v44_dt)")
    print("  v56:      trips_hybrid (no fire on two_pair)")
    print("  v57:      v56 + LOW pair Rule 29 (no fire on two_pair)")
    print("  v64:      v57 + HIGH_ONLY gate-outs (no fire on two_pair)")
    print("=" * 145)
    print(f"{'cell':<22} {'max':>4} {'n_pref':>7} "
          f"{'v44_dt':>8} {'v44RUL':>8} {'v54':>8} {'v55':>8} "
          f"{'v56':>8} {'v57':>8} {'v64':>8} "
          f"{'RUL-dt':>8} {'55-RUL':>8}")
    grand = {k: 0.0 for k in
             ["v44_dt", "v44_rule", "v54", "v55", "v56", "v57", "v64"]}
    for ci in sorted(CELL_NAMES):
        for ms in range(4, 15):
            seg = df[(df["cell_idx"] == ci) & (df["max_sing_rank"] == ms)]
            if len(seg) == 0:
                continue
            leaks = {}
            for k in ["v44_dt", "v44_rule", "v54", "v55", "v56", "v57", "v64"]:
                leaks[k] = (seg[f"regret_{k}"].sum() * EV_TO_DOL * 1000
                            / N_PREFIX)
                grand[k] += leaks[k]
            d_rul_dt = leaks["v44_rule"] - leaks["v44_dt"]
            d_55_rul = leaks["v55"] - leaks["v44_rule"]
            print(f"{CELL_NAMES[ci]:<22} {ms:>4} {len(seg):>7,} "
                  f"${leaks['v44_dt']:>+6.2f} ${leaks['v44_rule']:>+6.2f} "
                  f"${leaks['v54']:>+6.2f} ${leaks['v55']:>+6.2f} "
                  f"${leaks['v56']:>+6.2f} ${leaks['v57']:>+6.2f} "
                  f"${leaks['v64']:>+6.2f} "
                  f"${d_rul_dt:>+6.2f} ${d_55_rul:>+6.2f}")

    print(f"{'TOTAL':<22} {'':>4} {len(df):>7,} "
          f"${grand['v44_dt']:>+6.2f} ${grand['v44_rule']:>+6.2f} "
          f"${grand['v54']:>+6.2f} ${grand['v55']:>+6.2f} "
          f"${grand['v56']:>+6.2f} ${grand['v57']:>+6.2f} "
          f"${grand['v64']:>+6.2f} "
          f"${grand['v44_rule']-grand['v44_dt']:>+6.2f} "
          f"${grand['v55']-grand['v44_rule']:>+6.2f}")

    print()
    print("=" * 145)
    print("LAYER ATTRIBUTION SUMMARY (two_pair, prefix N=1000)")
    print("=" * 145)
    print(f"  v44_dt total leak:         ${grand['v44_dt']:>+7.2f}/1000h "
          f"(ML champion baseline)")
    print(f"  v44_RULE13 chain leak:     ${grand['v44_rule']:>+7.2f}/1000h  "
          f"(Δ vs v44_dt: ${grand['v44_rule']-grand['v44_dt']:>+7.2f})")
    print(f"  v54 (pair_hybrid) leak:    ${grand['v54']:>+7.2f}/1000h  "
          f"(Δ vs v44_RULE: ${grand['v54']-grand['v44_rule']:>+7.2f})")
    print(f"  v55 (two_pair_hybrid):     ${grand['v55']:>+7.2f}/1000h  "
          f"(Δ vs v54: ${grand['v55']-grand['v54']:>+7.2f})")
    print(f"  v56 (trips_hybrid):        ${grand['v56']:>+7.2f}/1000h  "
          f"(Δ vs v55: ${grand['v56']-grand['v55']:>+7.2f})")
    print(f"  v57 (+ Rule 29):           ${grand['v57']:>+7.2f}/1000h  "
          f"(Δ vs v56: ${grand['v57']-grand['v56']:>+7.2f})")
    print(f"  v64 (production):          ${grand['v64']:>+7.2f}/1000h  "
          f"(Δ vs v57: ${grand['v64']-grand['v57']:>+7.2f})")
    print()
    print("  ARCHITECTURAL INTERPRETATION:")
    print("    Δ_v44_RULE_vs_v44_dt > 0  → v44_RULE13 chain BLEEDS vs v44_dt on two_pair")
    print("                                 (same architectural pattern as S91 LOW pair).")
    print("    Δ_v54_vs_v44_RULE     ≈ 0  → v54 pair_hybrid INERT on two_pair (single-pair-only gate).")
    print("    Δ_v55_vs_v54         < 0  → v55 blanket routing ABSORBS the chain bleed:")
    print("                                 routes 100% of two_pair → v44_dt.")
    print("    Δ_v56_vs_v55         = 0  → v56 trips-only gate INERT.")
    print("    Δ_v57_vs_v56         = 0  → v57 LOW single-pair gate INERT.")
    print("    Δ_v64_vs_v57         = 0  → v64 HIGH_ONLY gate INERT.")
    print()
    print("  IMPLICATION FOR CHAIN-AUDIT PATTERN:")
    print("    The chain has been FULLY COLLAPSED by v55's blanket routing.")
    print("    There is no per-sub-cell residual where any chain layer bleeds vs")
    print("    v44_dt — the production strategy IS v44_dt for two_pair.")
    print("    Therefore no v65 candidate can be designed from the chain-audit")
    print("    pattern: there is nothing to gate out.")
    print()
    print("    Any further EV recovery within two_pair would require BEATING")
    print("    v44_dt on a sub-cell. This is rule extraction (Option D-revised),")
    print("    NOT chain audit. S69 (the design rationale for v55) explicitly")
    print("    tested all catalog candidates and confirmed v44_dt dominates")
    print("    every two_pair cell.")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
