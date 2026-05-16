"""S88 chain bleed audit — identify which rule layer (v44->v47->v48->v52)
is responsible for the $98/1000h bleed across the next-tier HIGH_ONLY cells
(DS_NO_MAXTOP × {K,A}, MS_ONLY × {J-A}, JOINT_HIGH × {K,A}).

Method: evaluate v44_dt, v47, v48, v52 on the cell hands. Compute per-version
cell leak. The transition that introduces the bleed is the bad rule layer.
This is the same pattern S87 used; v52 == v57 == v61 on these cells (v61
gate-out only fires on DS_NO_JOINT × J-A, not these).

Output:
  - per-cell × rank layer attribution
  - by v52 firing mode within each cell (defensive-low / defensive-gated /
    J-HIMID / fallthrough)
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
from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402
from strategy_v48_rules17_21_high_only_HIMID import (  # noqa: E402
    strategy_v48_rules17_21_high_only_HIMID,
)
from strategy_v52_full_high_only_handler import (  # noqa: E402
    strategy_v52_full_high_only_handler,
    LOW_MAX_DEFENSIVE,
    GATED_DEFENSIVE_MAX,
    GATED_S2_THRESHOLD,
    J_HIGH_OFFENSIVE,
)

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
PARQUET_S71 = ROOT / "data" / "drill_v44_high_only_S71_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

CELL_NAMES = {0: "JOINT_HIGH", 1: "JOINT_MED", 2: "JOINT_LOW",
              3: "DS_NO_JOINT", 4: "DS_NO_MAXTOP", 5: "MS_ONLY",
              6: "NEITHER"}

TARGETS = [
    (4, (13, 14)),          # DS_NO_MAXTOP × {K, A}
    (5, (11, 12, 13, 14)),  # MS_ONLY × {J, Q, K, A}
    (0, (13, 14)),          # JOINT_HIGH × {K, A}
]
RANK_CHAR = {11: "J", 12: "Q", 13: "K", 14: "A"}


def v52_firing_mode(h: np.ndarray) -> str:
    """Classify which v52 branch fires on a hand (or 'fallthrough')."""
    ranks = (h // 4) + 2
    rc = np.bincount(ranks.astype(int), minlength=15)
    if int((rc >= 2).sum()) != 0:
        return "not-high-only"
    max_r = int(ranks.max())
    if max_r < 7:
        return "v52-skip-too-low"
    sorted_ranks = sorted(int(r) for r in ranks)
    s2 = sorted_ranks[-2]
    if max_r in LOW_MAX_DEFENSIVE:
        return "v52-defensive-low"
    if max_r in GATED_DEFENSIVE_MAX and s2 <= GATED_S2_THRESHOLD:
        return "v52-defensive-gated"
    if max_r == J_HIGH_OFFENSIVE:
        return "v52-J-HIMID"
    return "v52-fallthrough"


def main() -> int:
    print("=" * 100)
    print("S88 chain bleed audit — per-layer attribution on next-tier HIGH_ONLY cells")
    print("=" * 100)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()

    print("[1/4] loading S71 parquet + filtering ...", flush=True)
    table = pq.read_table(PARQUET_S71,
                          columns=["canonical_id", "max_rank", "cell_idx",
                                   "v44_idx", "oracle_idx", "regret",
                                   "ev_best", "ev_v44"])
    df = table.to_pandas()
    target_mask = np.zeros(len(df), dtype=bool)
    for cidx, ranks in TARGETS:
        target_mask |= (df["cell_idx"] == cidx) & (df["max_rank"].isin(ranks))
    sub = df[target_mask].copy().reset_index(drop=True)
    print(f"  filtered to {len(sub):,} hands across S88 target cells")
    print()

    print("[2/4] loading canonical hands + oracle grid ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")
    print()

    print(f"[3/4] evaluating v47/v48/v52 + classifying firing mode ...", flush=True)
    n = len(sub)
    v47_ev = np.zeros(n, dtype=np.float32)
    v48_ev = np.zeros(n, dtype=np.float32)
    v52_ev = np.zeros(n, dtype=np.float32)
    firing_mode = np.empty(n, dtype=object)

    cids = sub["canonical_id"].to_numpy()
    t0 = time.time()
    for k in range(n):
        cid = int(cids[k])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v47_ev[k] = float(rowf[int(strategy_v47_rule16_Qhigh_DS(h))])
        v48_ev[k] = float(rowf[int(strategy_v48_rules17_21_high_only_HIMID(h))])
        v52_ev[k] = float(rowf[int(strategy_v52_full_high_only_handler(h))])
        firing_mode[k] = v52_firing_mode(h)
        if (k + 1) % 50_000 == 0:
            elapsed = time.time() - t0
            print(f"    {k+1:>7,}/{n:,} ({elapsed:.1f}s)", flush=True)
    print(f"  done in {time.time()-t0:.1f}s")
    print()

    sub["v47_ev"] = v47_ev
    sub["v48_ev"] = v48_ev
    sub["v52_ev"] = v52_ev
    sub["firing_mode"] = firing_mode
    sub["v47_regret"] = sub["ev_best"] - sub["v47_ev"]
    sub["v48_regret"] = sub["ev_best"] - sub["v48_ev"]
    sub["v52_regret"] = sub["ev_best"] - sub["v52_ev"]

    # === Per-cell × rank layer attribution ===
    print("[4/4] results")
    print("=" * 120)
    print("LAYER ATTRIBUTION — total leak per strategy version (per cell × rank)")
    print("=" * 120)
    print(f"{'cell':>15} {'rank':>4} {'n':>8} "
          f"{'v44 $':>8} {'v47 $':>8} {'v48 $':>8} {'v52 $':>8} "
          f"{'v44→v47 Δ':>11} {'v47→v48 Δ':>11} {'v48→v52 Δ':>11}")

    total_47, total_48, total_52 = 0.0, 0.0, 0.0
    for cidx, ranks in TARGETS:
        for r in ranks:
            seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"] == r)]
            if len(seg) == 0:
                continue
            v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v47_leak = seg["v47_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v48_leak = seg["v48_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v52_leak = seg["v52_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            d_47 = v47_leak - v44_leak
            d_48 = v48_leak - v47_leak
            d_52 = v52_leak - v48_leak
            print(f"{CELL_NAMES[cidx]:>15} {RANK_CHAR[r]:>4} {len(seg):>8,} "
                  f"${v44_leak:>+6.2f} ${v47_leak:>+6.2f} ${v48_leak:>+6.2f} "
                  f"${v52_leak:>+6.2f} "
                  f"${d_47:>+9.2f} ${d_48:>+9.2f} ${d_52:>+9.2f}")
            total_47 += d_47
            total_48 += d_48
            total_52 += d_52

    print()
    print(f"  Σ Δ across all S88 cells: "
          f"v44→v47 = ${total_47:+.2f}, v47→v48 = ${total_48:+.2f}, "
          f"v48→v52 = ${total_52:+.2f}")
    print(f"  Total chain bleed (v44→v52): ${total_47+total_48+total_52:+.2f}/1000h")
    print()
    print("  (Positive Δ = layer made leak WORSE. Negative Δ = layer made leak BETTER.)")
    print()

    # === Per-cell roll-up ===
    print("=" * 120)
    print("ROLLED UP per cell (across all target ranks)")
    print("=" * 120)
    print(f"{'cell':>15} {'n':>8} {'v44 $':>8} {'v47 $':>8} "
          f"{'v48 $':>8} {'v52 $':>8} "
          f"{'v44→v47 Δ':>11} {'v47→v48 Δ':>11} {'v48→v52 Δ':>11}")
    for cidx, ranks in TARGETS:
        seg = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"].isin(ranks))]
        if len(seg) == 0:
            continue
        v44_leak = seg["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v47_leak = seg["v47_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v48_leak = seg["v48_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        v52_leak = seg["v52_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
        d_47 = v47_leak - v44_leak
        d_48 = v48_leak - v47_leak
        d_52 = v52_leak - v48_leak
        print(f"{CELL_NAMES[cidx]:>15} {len(seg):>8,} "
              f"${v44_leak:>+6.2f} ${v47_leak:>+6.2f} ${v48_leak:>+6.2f} "
              f"${v52_leak:>+6.2f} "
              f"${d_47:>+9.2f} ${d_48:>+9.2f} ${d_52:>+9.2f}")

    # === Firing mode breakdown per cell ===
    print()
    print("=" * 120)
    print("V52 FIRING MODE — leak attribution by which v52 branch fires (per cell)")
    print("=" * 120)
    for cidx, ranks in TARGETS:
        cell = CELL_NAMES[cidx]
        seg_cell = sub[(sub["cell_idx"] == cidx) & (sub["max_rank"].isin(ranks))]
        if len(seg_cell) == 0:
            continue
        print(f"--- {cell} (n={len(seg_cell):,}) ---")
        print(f"  {'mode':>22} {'n':>8} {'pct':>6} "
              f"{'v44 leak $':>11} {'v52 leak $':>11} {'Δ vs v44':>10}")
        modes = seg_cell["firing_mode"].unique()
        for mode in modes:
            sub2 = seg_cell[seg_cell["firing_mode"] == mode]
            v44_leak = sub2["regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            v52_leak = sub2["v52_regret"].sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
            delta = v52_leak - v44_leak
            print(f"  {mode:>22} {len(sub2):>8,} "
                  f"{100*len(sub2)/len(seg_cell):>5.1f}% "
                  f"${v44_leak:>+9.2f} ${v52_leak:>+9.2f} ${delta:>+8.2f}")
        print()

    # === Net bleed by mode (rolled up across all S88 cells) ===
    print("=" * 120)
    print("NET BLEED BY FIRING MODE (rolled up across all S88 cells)")
    print("=" * 120)
    print(f"  {'mode':>22} {'n':>10} {'v44 leak $':>11} {'v52 leak $':>11} "
          f"{'Δ (bleed)':>11}")
    mode_stats = sub.groupby("firing_mode").agg(
        n=("regret", "size"),
        v44_sum=("regret", "sum"),
        v52_sum=("v52_regret", "sum"),
    )
    mode_stats["v44_leak_$"] = mode_stats["v44_sum"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
    mode_stats["v52_leak_$"] = mode_stats["v52_sum"] * EV_TO_DOL * 1000 / N_TOTAL_GRID
    mode_stats["bleed_$"] = mode_stats["v52_leak_$"] - mode_stats["v44_leak_$"]
    mode_stats = mode_stats.sort_values("bleed_$", ascending=False)
    for mode, row in mode_stats.iterrows():
        print(f"  {mode:>22} {int(row['n']):>10,} "
              f"${row['v44_leak_$']:>+9.2f} ${row['v52_leak_$']:>+9.2f} "
              f"${row['bleed_$']:>+9.2f}")
    print()
    total_bleed = mode_stats["bleed_$"].sum()
    print(f"  TOTAL BLEED (sum of v52 − v44 leak across S88 cells): "
          f"${total_bleed:+.2f}/1000h")

    print()
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
