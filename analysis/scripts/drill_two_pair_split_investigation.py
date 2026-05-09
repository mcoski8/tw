"""
Session 42 overnight — two_pair split-allowing rule investigation.

The deferred two_pair Rule 8 candidate ("RC if h<=4, RB if T<=h<=K, else RA")
won +$197/1000h on full grid but lost -$512/1000h on prefix because v33's
underlying logic SPLITS pairs on weak hands, and the prefix is heavily
biased toward weak hands. This investigation identifies WHICH cells
benefit from splitting and tries to build a rule that allows splitting
where appropriate.

For each two_pair hand we compute EVs under:
  - RA: top=hi-sing, mid=HIGH pair, bot=LOW pair + 2 singles
  - RB: top=hi-sing, mid=LOW pair, bot=HIGH pair + 2 singles
  - RC: top=hi-sing, mid=2 lo-singletons, bot=HIGH+LOW pairs (double-pair-bot)
  - SPLIT_oracle: oracle within "mid is one card from each pair" subspace
    (= 1 H-pair-member + 1 L-pair-member; 4 such mid combos × 3 top choices)

For each (high, low) cell we report:
  - best of {RA, RB, RC, SPLIT} per cell
  - oracle agreement %
  - cell pop
  - lift if we ship "best per cell"

Then we test composite rules:
  - "RC if h<=4 elif T<=h<=K then RB else RA"  (the deferred rule, no split)
  - "split if h<=N or both pairs<=M else (RA/RB/RC by tier)"
  - various split-allowing variants

Goal: find a rule that wins on BOTH grids by >+$50/1000h whole-grid.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_split_investigation.py
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOL = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 42 overnight: two_pair split-allowing investigation")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading two_pair mask + grids ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    mask_2p = ((ft["n_pairs"].to_numpy() == 2)
               & (ft["n_trips"].to_numpy() == 0)
               & (ft["n_quads"].to_numpy() == 0))
    n_total = len(ft)
    pop_share_full = float(mask_2p.mean())
    n_2p = int(mask_2p.sum())
    two_pair_idx = np.where(mask_2p)[0]
    print(f"  two_pair: {n_2p:,}  ({100*pop_share_full:.4f}%)")

    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    in_pref = two_pair_idx < 500_000
    n_in_pref = int(in_pref.sum())
    pop_share_pref = n_in_pref / 500_000
    print(f"  in prefix: {n_in_pref:,}  ({100*pop_share_pref:.4f}%)")

    print(f"\n[2/4] computing per-hand EVs ({n_2p:,} hands × 4-5 settings ...",
          flush=True)
    full_v33_evs = np.zeros(n_2p)
    full_oracle_evs = np.zeros(n_2p)
    full_RA = np.zeros(n_2p)
    full_RB = np.zeros(n_2p)
    full_RC = np.zeros(n_2p)
    full_SPLIT_oc = np.zeros(n_2p)  # oracle within split-mid subspace

    pref_v33_evs = np.full(n_2p, np.nan)
    pref_oracle_evs = np.full(n_2p, np.nan)
    pref_RA = np.full(n_2p, np.nan)
    pref_RB = np.full(n_2p, np.nan)
    pref_RC = np.full(n_2p, np.nan)
    pref_SPLIT_oc = np.full(n_2p, np.nan)

    h_arr = np.zeros(n_2p, dtype=np.int8)
    l_arr = np.zeros(n_2p, dtype=np.int8)
    oracle_class = np.zeros(n_2p, dtype=np.int8)  # 0=RA, 1=RB, 2=RC, 3=SPLIT, 4=other

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(two_pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)
        hpr, lpr = pairs
        s_hi, s_mid_r, s_lo = sings
        h_arr[i] = hpr
        l_arr[i] = lpr
        pos_H = sorted(j for j in range(7) if int(ranks[j]) == hpr)
        pos_L = sorted(j for j in range(7) if int(ranks[j]) == lpr)
        pos_shi = next(j for j in range(7) if int(ranks[j]) == s_hi)
        pos_smid = next(j for j in range(7) if int(ranks[j]) == s_mid_r)
        pos_slo = next(j for j in range(7) if int(ranks[j]) == s_lo)

        ra_s = _setting_index_from_tmb(pos_shi, pos_H[0], pos_H[1])
        rb_s = _setting_index_from_tmb(pos_shi, pos_L[0], pos_L[1])
        rc_s = _setting_index_from_tmb(pos_shi, pos_smid, pos_slo)

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v33_evs[i] = rowf[int(strategy_v33_rule6_trips(h))]
        full_oracle_evs[i] = rowf.max()
        full_RA[i] = rowf[ra_s]
        full_RB[i] = rowf[rb_s]
        full_RC[i] = rowf[rc_s]

        # SPLIT oracle: mid = 1 H-pair-member + 1 L-pair-member.
        # 2 H-pair-members × 2 L-pair-members = 4 mid combos × 3 top choices
        #  = 12 settings, but top choices are constrained to non-pair-mem.
        # Top can be any of the 3 singletons OR a pair member (split-with-top).
        # To stay clean, "SPLIT" = mid is mixed (1 H + 1 L), top is any singleton.
        split_best = -np.inf
        for mid_h in pos_H:
            for mid_l in pos_L:
                mid_a, mid_b = sorted([mid_h, mid_l])
                for top_pos in [pos_shi, pos_smid, pos_slo]:
                    if top_pos == mid_a or top_pos == mid_b:
                        continue
                    s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                    split_best = max(split_best, float(rowf[s]))
        full_SPLIT_oc[i] = split_best

        # Determine which class oracle prefers
        # Find argmax on full row, then categorize by setting
        oracle_pick = int(np.argmax(rowf))
        # Decode top, mid
        top_idx = oracle_pick // 15
        # Map to class:
        if rowf[oracle_pick] - rowf[ra_s] < 1e-6: oracle_class[i] = 0  # RA-equivalent
        elif rowf[oracle_pick] - rowf[rb_s] < 1e-6: oracle_class[i] = 1
        elif rowf[oracle_pick] - rowf[rc_s] < 1e-6: oracle_class[i] = 2
        elif rowf[oracle_pick] - split_best < 1e-6: oracle_class[i] = 3
        else: oracle_class[i] = 4

        if in_pref[i]:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v33_evs[i] = rowp[int(strategy_v33_rule6_trips(h))]
            pref_oracle_evs[i] = rowp.max()
            pref_RA[i] = rowp[ra_s]
            pref_RB[i] = rowp[rb_s]
            pref_RC[i] = rowp[rc_s]
            split_best_p = -np.inf
            for mid_h in pos_H:
                for mid_l in pos_L:
                    mid_a, mid_b = sorted([mid_h, mid_l])
                    for top_pos in [pos_shi, pos_smid, pos_slo]:
                        if top_pos == mid_a or top_pos == mid_b:
                            continue
                        s = _setting_index_from_tmb(top_pos, mid_a, mid_b)
                        split_best_p = max(split_best_p, float(rowp[s]))
            pref_SPLIT_oc[i] = split_best_p

        if time.time() - last_log > 15:
            rate = (i + 1) / (time.time() - t0)
            eta = (n_2p - i - 1) / rate
            print(f"    progress {i+1:>9,}/{n_2p:,}  rate={rate:.0f}/s  eta {eta:.0f}s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.0f}s ({n_2p/(time.time()-t0):.0f}/s)")

    # ============================================================
    # Per-cell analysis
    # ============================================================
    print(f"\n[3/4] per-cell oracle-class breakdown ...", flush=True)
    cells = defaultdict(list)
    for i in range(n_2p):
        cells[(int(h_arr[i]), int(l_arr[i]))].append(i)

    print(f"\n  Per-cell oracle-class shares (FULL grid, sorted by H desc, L desc):")
    print(f"  {'pair':<6}  {'n':>6}  {'RA%':>6}  {'RB%':>6}  {'RC%':>6}  {'SPL%':>6}  best_class  best_$  v33$")

    cell_table = []
    for (H, L), idxs in sorted(cells.items(), key=lambda kv: (-kv[0][0], -kv[0][1])):
        idxs_np = np.array(idxs, dtype=np.int64)
        n = len(idxs_np)
        ocs = oracle_class[idxs_np]
        ra_pct = float((ocs == 0).mean())
        rb_pct = float((ocs == 1).mean())
        rc_pct = float((ocs == 2).mean())
        spl_pct = float((ocs == 3).mean())
        # Per-class regret on this cell
        v33_m = (full_oracle_evs[idxs_np] - full_v33_evs[idxs_np]).mean()
        ra_m = (full_oracle_evs[idxs_np] - full_RA[idxs_np]).mean()
        rb_m = (full_oracle_evs[idxs_np] - full_RB[idxs_np]).mean()
        rc_m = (full_oracle_evs[idxs_np] - full_RC[idxs_np]).mean()
        spl_m = (full_oracle_evs[idxs_np] - full_SPLIT_oc[idxs_np]).mean()
        means = {"RA": ra_m, "RB": rb_m, "RC": rc_m, "SPL": spl_m}
        best = min(means, key=means.get)
        cell_table.append({
            "H": H, "L": L, "n": n,
            "RA_pct": ra_pct, "RB_pct": rb_pct, "RC_pct": rc_pct, "SPL_pct": spl_pct,
            "v33_m": v33_m, "RA_m": ra_m, "RB_m": rb_m, "RC_m": rc_m, "SPL_m": spl_m,
            "best": best,
        })
        if H >= 10 or H <= 5 or L <= 4:  # show interesting cells
            label = f"{RANK_CHARS[H]}{RANK_CHARS[L]}"
            print(f"  {label:<6}  {n:>6,}  {100*ra_pct:>5.1f}%  {100*rb_pct:>5.1f}%  "
                  f"{100*rc_pct:>5.1f}%  {100*spl_pct:>5.1f}%  {best:<10}  "
                  f"${means[best]*EV_TO_DOL*1000:>+8.1f}  ${v33_m*EV_TO_DOL*1000:>+8.1f}")

    df = pd.DataFrame(cell_table)
    df["lift_vs_v33"] = df.apply(
        lambda r: (r["v33_m"] - {"RA": r["RA_m"], "RB": r["RB_m"], "RC": r["RC_m"], "SPL": r["SPL_m"]}[r["best"]]) * EV_TO_DOL * 1000,
        axis=1
    )
    print(f"\n  Cells where SPLIT wins (best_class=SPL): "
          f"{int((df['best'] == 'SPL').sum())} / {len(df)}")
    spl_cells = df[df["best"] == "SPL"]
    if len(spl_cells) > 0:
        print(f"\n  SPLIT-winning cells:")
        print(f"  {'pair':<6}  {'n':>6}  {'SPL%':>6}  {'v33$':>9}  {'best_$':>9}  {'lift':>8}")
        for _, r in spl_cells.sort_values("lift_vs_v33", ascending=False).iterrows():
            label = f"{RANK_CHARS[int(r['H'])]}{RANK_CHARS[int(r['L'])]}"
            print(f"  {label:<6}  {int(r['n']):>6,}  {100*r['SPL_pct']:>5.1f}%  "
                  f"${r['v33_m']*EV_TO_DOL*1000:>+8.1f}  ${r['SPL_m']*EV_TO_DOL*1000:>+8.1f}  "
                  f"${r['lift_vs_v33']:>+7.1f}")

    # ============================================================
    # Boundary search incorporating SPLIT
    # ============================================================
    print(f"\n[4/4] BOUNDARY RULE SEARCH (full + prefix)", flush=True)
    print(f"  {'rule':<70}  {'full_Δ_grid':>14}  {'pref_Δ_grid':>14}")

    full_v33_reg = full_oracle_evs - full_v33_evs
    pref_v33_reg = pref_oracle_evs[in_pref] - pref_v33_evs[in_pref]

    def evaluate(rule_fn, label):
        # rule_fn returns 'RA', 'RB', 'RC', 'SPL'
        pick = np.empty(n_2p, dtype="<U3")
        for i in range(n_2p):
            pick[i] = rule_fn(int(h_arr[i]), int(l_arr[i]))
        full_picked = np.where(pick == "RA", full_RA,
                               np.where(pick == "RB", full_RB,
                                        np.where(pick == "RC", full_RC, full_SPLIT_oc)))
        full_reg = full_oracle_evs - full_picked
        full_delta = (full_v33_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full

        pref_picked = np.where(pick[in_pref] == "RA", pref_RA[in_pref],
                               np.where(pick[in_pref] == "RB", pref_RB[in_pref],
                                        np.where(pick[in_pref] == "RC", pref_RC[in_pref],
                                                 pref_SPLIT_oc[in_pref])))
        pref_reg = pref_oracle_evs[in_pref] - pref_picked
        pref_delta = (pref_v33_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
        marker = "★" if (full_delta > 50 and pref_delta > 0) else ""
        print(f"  {label:<70}  ${full_delta:>+12.2f}  ${pref_delta:>+12.2f}  {marker}")

    # Original deferred rule
    evaluate(lambda h, l: "RC" if h <= 4 else ("RB" if 10 <= h <= 13 else "RA"),
             "DEFERRED Rule: RC if h<=4 elif T<=h<=K then RB else RA")
    # Split-allowing variants (all use oracle-within-split, so these are oracle-bound)
    evaluate(lambda h, l: "SPL" if h <= 4 else ("RC" if h <= 4 else ("RB" if 10 <= h <= 13 else "RA")),
             "ORACLE: SPL if h<=4 elif T<=h<=K then RB else RA")
    evaluate(lambda h, l: "SPL" if h <= 5 else ("RB" if 10 <= h <= 13 else "RA"),
             "ORACLE: SPL if h<=5 elif T<=h<=K then RB else RA")
    evaluate(lambda h, l: "SPL" if (h + l) <= 8 else ("RC" if h <= 4 else ("RB" if 10 <= h <= 13 else "RA")),
             "ORACLE: SPL if h+l<=8 elif h<=4 then RC elif T<=h<=K then RB else RA")
    evaluate(lambda h, l: "SPL" if h <= 4 and l <= 3 else ("RB" if 10 <= h <= 13 else "RA"),
             "ORACLE: SPL if h<=4 AND l<=3 elif T<=h<=K then RB else RA")
    evaluate(lambda h, l: "SPL" if h <= 6 else ("RB" if 10 <= h <= 13 else "RA"),
             "ORACLE: SPL if h<=6 elif T<=h<=K then RB else RA")
    # Universal split
    evaluate(lambda h, l: "SPL", "ORACLE: always SPL (oracle within split-mid)")
    # Best-per-cell
    cell_best = {(int(r["H"]), int(r["L"])): r["best"] for _, r in df.iterrows()}
    evaluate(lambda h, l: cell_best.get((h, l), "RA"),
             "ORACLE: best per cell (78-cell lookup)")

    # Save cell table
    out_dir = ROOT / "data" / "session42_drills"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "two_pair_split_cell_table.csv", index=False)
    print(f"\n  Cell table saved to {out_dir / 'two_pair_split_cell_table.csv'}")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
