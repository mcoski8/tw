"""S91 — chain audit: layer-by-layer attribution for LOW pair PMID cells.

The S87/S88/S89/S90 chain audit pattern, transferred to LOW pair. The
production chain for LOW pair PMID hands is:

  v64 ── HIGH_ONLY gate-out (doesn't fire on pair)
   └── v57 ── LOW × PMID_DS_NOMAXTOP × max_sing ≤ Q → forced setting; else:
       └── v56 ── trips_hybrid (doesn't fire on pair)
            └── v55 ── two_pair_hybrid (doesn't fire on pair)
                 └── v54 ── pair_hybrid: PBOT_DS → v44_dt; else:
                      └── v53 ── qpair_joint_pbot (Q-pair only)
                           └── v52 ── HIGH_ONLY handler (doesn't fire on pair, has rc==2 guard)
                                └── v51 ── (HIGH_ONLY)
                                     └── v50 ── (HIGH_ONLY)
                                          └── v48 ── (HIGH_ONLY)
                                               └── v47 ── Q-high DS (rc==2 guard, doesn't fire on pair)
                                                    └── v46 ── K-high DS (rc==2 guard)
                                                         └── v45 ── A-high DS (rc==2 guard)
                                                              └── v44_RULE13 ── three_pair_DS handler
                                                                   └── v43 ── two_pair_DS_intact
                                                                        └── v42 ── jpair_pbot_ds (J-pair only)
                                                                             └── ... rule chain to base

For LOW pair PMID hands (where v54 falls through to v53/v52 chain), production
effectively returns the v44_RULE13 chain pick — NOT v44_dt!

This is a CRITICAL discovery for S91. The "chain" the S87-S90 audit identified
as bleeding (v47 → v48 → v52) does not fire on pair hands at all (rc==2
guards). The pair-route v44_RULE13 chain is a completely separate machinery
from v44_dt.

This script measures per-cell × max_sing:
  - v44_dt pick
  - v44_RULE13 pick (= v54 PMID-route pick = v53 pick since Q-pair-only check fails for LOW)
  - v57 pick (= Rule 29 if it fires; else v44_RULE13)
  - v64 pick (= v57 for LOW pair, since HIGH_ONLY gate doesn't fire)

Disagreement rates between layers tell us where the chain machinery actually
does something. Per-cell LIFT/BLEED quantifies whether that machinery is net-
positive on each subset.
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
from strategy_v53_qpair_joint_pbot import (  # noqa: E402
    strategy_v53_qpair_joint_pbot,
)
from strategy_v54_pair_hybrid import strategy_v54_pair_hybrid  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v64_high_only_chain_fix_zone import (  # noqa: E402
    strategy_v64_high_only_chain_fix_zone,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
PARQUET_PAIR = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"

EV_TO_DOL = 10.0
N_PREFIX = 500_000

CELL_NAMES = {0: "PBOT_DS_JOINT", 1: "PBOT_DS_PARTIAL",
              2: "PMID_DS_MAXTOP", 3: "PMID_DS_NOMAXTOP",
              4: "PMID_SS_MAXTOP", 5: "PMID_OTHER"}

LOW_PAIR_RANKS = (2, 3, 4, 5, 6, 7)


def main() -> int:
    print("=" * 100)
    print("S91 chain audit — LOW pair, layer-by-layer attribution (N=1000 prefix)")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/3] loading LOW pair × prefix subset ...", flush=True)
    table = pq.read_table(
        PARQUET_PAIR,
        columns=["canonical_id", "pair_rank", "max_sing_rank", "cell_idx",
                 "v44_idx", "regret"]
    )
    df = table.to_pandas()
    df = df[(df["pair_rank"].isin(LOW_PAIR_RANKS)) &
            (df["canonical_id"] < N_PREFIX)].reset_index(drop=True)
    print(f"  loaded {len(df):,} LOW × prefix hands")
    print()

    print("[2/3] evaluating layer strategies + EV on prefix grid ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    n = len(df)
    v44_dt_idx = df["v44_idx"].to_numpy()
    v44_rule_idx = np.zeros(n, dtype=np.int16)
    v54_idx = np.zeros(n, dtype=np.int16)
    v57_idx = np.zeros(n, dtype=np.int16)
    v64_idx = np.zeros(n, dtype=np.int16)

    ev_v44_dt = np.zeros(n, dtype=np.float32)
    ev_v44_rule = np.zeros(n, dtype=np.float32)
    ev_v54 = np.zeros(n, dtype=np.float32)
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
        i_v57 = int(strategy_v57_lo_pair_defensive(h))
        i_v64 = int(strategy_v64_high_only_chain_fix_zone(h))
        v44_rule_idx[k] = i_rule
        v54_idx[k] = i_v54
        v57_idx[k] = i_v57
        v64_idx[k] = i_v64
        ev_v44_rule[k] = float(rowp[i_rule])
        ev_v54[k] = float(rowp[i_v54])
        ev_v57[k] = float(rowp[i_v57])
        ev_v64[k] = float(rowp[i_v64])
        if (k + 1) % 30_000 == 0:
            elapsed = time.time() - t0
            rate = (k + 1) / elapsed
            eta = (n - k - 1) / rate
            print(f"    {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  ETA={eta:>4.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    df["v44_rule_idx"] = v44_rule_idx
    df["v54_idx"] = v54_idx
    df["v57_idx"] = v57_idx
    df["v64_idx"] = v64_idx

    df["regret_v44_dt"] = ev_best - ev_v44_dt
    df["regret_v44_rule"] = ev_best - ev_v44_rule
    df["regret_v54"] = ev_best - ev_v54
    df["regret_v57"] = ev_best - ev_v57
    df["regret_v64"] = ev_best - ev_v64

    print("[3/3] results — layer transitions per cell × max_sing")
    print("=" * 130)
    print("LAYER TRANSITIONS (prefix N=1000, hands per sub-cell, EV)")
    print("Format: leak $/1000h on prefix subset. Smaller = better.")
    print("Layer Δ columns show whether each layer transition LIFTS (negative) or BLEEDS (positive) over previous.")
    print("  v44_dt:   strategy_v44_dt (ML champion)")
    print("  v44_RULE: strategy_v44_rule13_three_pair_DS (= what the v52 → v47 → v46 → v45 chain falls through to)")
    print("  v54:      v54 routing (PBOT_DS → v44_dt; else falls through to v53/v52/.../v44_RULE)")
    print("  v57:      v54 + Rule 29 (LOW × PMID_DS_NOMAXTOP × max_sing ≤ Q)")
    print("  v64:      v57 + HIGH_ONLY gate-outs (none of which fire on pair hands)")
    print("=" * 130)
    print(f"{'cell':<20} {'max':>4} {'n_pref':>7} "
          f"{'v44_dt':>8} {'v44RUL':>8} {'v54':>8} {'v57':>8} {'v64':>8} "
          f"{'RUL-dt':>8} {'54-RUL':>8} {'57-54':>8} {'64-57':>8}")
    grand = {k: 0.0 for k in ["v44_dt","v44_rule","v54","v57","v64"]}
    for ci in range(6):
        for ms in range(2, 15):
            seg = df[(df["cell_idx"] == ci) & (df["max_sing_rank"] == ms)]
            if len(seg) == 0:
                continue
            leaks = {}
            for k in ["v44_dt","v44_rule","v54","v57","v64"]:
                leaks[k] = seg[f"regret_{k}"].sum() * EV_TO_DOL * 1000 / N_PREFIX
                grand[k] += leaks[k]
            d_rul_dt = leaks["v44_rule"] - leaks["v44_dt"]
            d_54_rul = leaks["v54"] - leaks["v44_rule"]
            d_57_54 = leaks["v57"] - leaks["v54"]
            d_64_57 = leaks["v64"] - leaks["v57"]
            print(f"{CELL_NAMES[ci]:<20} {ms:>4} {len(seg):>7,} "
                  f"${leaks['v44_dt']:>+6.2f} ${leaks['v44_rule']:>+6.2f} "
                  f"${leaks['v54']:>+6.2f} ${leaks['v57']:>+6.2f} ${leaks['v64']:>+6.2f} "
                  f"${d_rul_dt:>+6.2f} ${d_54_rul:>+6.2f} ${d_57_54:>+6.2f} ${d_64_57:>+6.2f}")

    print(f"{'TOTAL':<20} {'':>4} {len(df):>7,} "
          f"${grand['v44_dt']:>+6.2f} ${grand['v44_rule']:>+6.2f} "
          f"${grand['v54']:>+6.2f} ${grand['v57']:>+6.2f} ${grand['v64']:>+6.2f} "
          f"${grand['v44_rule']-grand['v44_dt']:>+6.2f} "
          f"${grand['v54']-grand['v44_rule']:>+6.2f} "
          f"${grand['v57']-grand['v54']:>+6.2f} "
          f"${grand['v64']-grand['v57']:>+6.2f}")

    print()
    print("=" * 130)
    print("LAYER ATTRIBUTION SUMMARY (LOW pair, prefix N=1000)")
    print("=" * 130)
    print(f"  v44_dt total leak:         ${grand['v44_dt']:>+7.2f}/1000h")
    print(f"  v44_RULE13 chain leak:     ${grand['v44_rule']:>+7.2f}/1000h  "
          f"(Δ vs v44_dt: ${grand['v44_rule']-grand['v44_dt']:>+7.2f})")
    print(f"  v54 (pair_hybrid) leak:    ${grand['v54']:>+7.2f}/1000h  "
          f"(Δ vs v44_RULE: ${grand['v54']-grand['v44_rule']:>+7.2f})")
    print(f"  v57 (+Rule 29) leak:       ${grand['v57']:>+7.2f}/1000h  "
          f"(Δ vs v54: ${grand['v57']-grand['v54']:>+7.2f})")
    print(f"  v64 (production) leak:     ${grand['v64']:>+7.2f}/1000h  "
          f"(Δ vs v57: ${grand['v64']-grand['v57']:>+7.2f})")
    print()
    print("  Interpretation:")
    print("    Δ_v44_RULE_vs_v44_dt < 0  → v44_RULE13 chain BEATS v44_dt overall on LOW pair")
    print("                                 (i.e. the rule-based chain machinery is net-positive,")
    print("                                  not net-negative like S87-S90 found for HIGH_ONLY).")
    print("    Δ_v54_vs_v44_RULE     < 0  → v54's PBOT_DS routing to v44_dt LIFTS over pure chain")
    print("                                 (= the hybrid routing decision is correct).")
    print("    Δ_v57_vs_v54         < 0  → Rule 29 LIFTS over v54 (confirming S83 ship).")
    print("    Δ_v64_vs_v57         ≈ 0  → HIGH_ONLY gates don't fire on pair (expected).")
    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
