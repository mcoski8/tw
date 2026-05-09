"""
Session 42 deep-dive — characterize ALL two_pair oracle picks.

The two_pair split investigation found that 15-25% of oracle picks per cell
fall OUTSIDE the RA/RB/RC/SPL classes I tested. This drill enumerates the
ACTUAL oracle pick on every two_pair hand and categorizes by:
  - top_kind: "highest_sing" / "second_sing" / "lowest_sing" /
              "high_pair_member" / "low_pair_member"
  - mid_kind: "high_pair" / "low_pair" / "two_singletons" / "mixed_pair" /
              "pair_plus_sing" / "two_pair_members" / etc.

For each (high_pair, low_pair) cell, report the most common oracle pick
profile. Find structural patterns that the simpler RA/RB/RC analysis missed.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_oracle_picks_full.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402

GRID = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 42 deep-dive: characterize ALL two_pair oracle picks")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading two_pair mask + grid ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    mask = ((ft["n_pairs"].to_numpy() == 2)
            & (ft["n_trips"].to_numpy() == 0)
            & (ft["n_quads"].to_numpy() == 0))
    n_2p = int(mask.sum())
    two_pair_idx = np.where(mask)[0]
    print(f"  two_pair: {n_2p:,}")

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID, mode="memmap")

    print(f"\n[2/3] enumerating oracle pick per hand ...", flush=True)

    # Track per-cell pick distributions
    cell_top_kind = defaultdict(Counter)
    cell_mid_kind = defaultdict(Counter)
    cell_combined = defaultdict(Counter)

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(two_pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)
        H, L = pairs
        s_hi, s_mid_r, s_lo = sings

        row = np.asarray(grid.evs[int(cid)], dtype=np.float64)
        oracle_pick = int(np.argmax(row))
        feats = setting_features_from_bytes(h)

        top_idx = oracle_pick // 15
        top_rank = int(ranks[top_idx])

        # top_kind
        if top_rank == s_hi:
            top_kind = "hi_sing"
        elif top_rank == s_mid_r:
            top_kind = "mid_sing"
        elif top_rank == s_lo:
            top_kind = "lo_sing"
        elif top_rank == H:
            top_kind = "H_pair_mem"
        elif top_rank == L:
            top_kind = "L_pair_mem"
        else:
            top_kind = "other"

        # mid_kind
        if bool(feats.mid_is_pair[oracle_pick]):
            mid_pr = int(feats.mid_pair_rank[oracle_pick])
            if mid_pr == H:
                mid_kind = "H_pair"
            elif mid_pr == L:
                mid_kind = "L_pair"
            else:
                mid_kind = "other_pair"
        else:
            # Mid is unpaired. Decode mid cards by index.
            top_idx_ = oracle_pick // 15
            mid_combo_idx = oracle_pick % 15
            remaining = [j for j in range(7) if j != top_idx_]
            # Map mid_combo_idx (0..14) to (a, b) in remaining
            n = 0
            mid_a = mid_b = -1
            for a in range(6):
                for b in range(a + 1, 6):
                    if n == mid_combo_idx:
                        mid_a, mid_b = remaining[a], remaining[b]
                        break
                    n += 1
                if mid_a != -1:
                    break
            mid_a_rank = int(ranks[mid_a]) if mid_a >= 0 else 0
            mid_b_rank = int(ranks[mid_b]) if mid_b >= 0 else 0
            kinds = sorted([
                ("hi_sing" if r == s_hi else
                 "mid_sing" if r == s_mid_r else
                 "lo_sing" if r == s_lo else
                 "H_pair_mem" if r == H else
                 "L_pair_mem" if r == L else "other")
                for r in (mid_a_rank, mid_b_rank)
            ])
            if kinds == ["hi_sing", "mid_sing"]:
                mid_kind = "two_top_sings"
            elif kinds == ["lo_sing", "mid_sing"]:
                mid_kind = "two_low_sings"
            elif kinds == ["hi_sing", "lo_sing"]:
                mid_kind = "hi_lo_sings"
            elif "H_pair_mem" in kinds and "L_pair_mem" in kinds:
                mid_kind = "mixed_pair"
            elif "H_pair_mem" in kinds:
                mid_kind = "H_split_w_sing"
            elif "L_pair_mem" in kinds:
                mid_kind = "L_split_w_sing"
            else:
                mid_kind = "other_unpaired"

        cell_top_kind[(H, L)][top_kind] += 1
        cell_mid_kind[(H, L)][mid_kind] += 1
        cell_combined[(H, L)][f"{top_kind}/{mid_kind}"] += 1

        if time.time() - last_log > 15:
            rate = (i + 1) / (time.time() - t0)
            eta = (n_2p - i - 1) / rate
            print(f"    progress {i+1:>9,}/{n_2p:,}  rate={rate:.0f}/s  eta {eta:.0f}s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.0f}s")

    print(f"\n[3/3] PER-CELL ORACLE PROFILE")
    print(f"  Most common (top, mid) profile per cell + share")
    print(f"  {'cell':<6}  {'n':>7}  {'top1':>14}  {'top2':>14}  {'mid1':>14}  {'mid2':>14}  most_common_combo")

    summary = []
    for (H, L), combos in sorted(cell_combined.items(), key=lambda kv: (-kv[0][0], -kv[0][1])):
        n_cell = sum(combos.values())
        top1, top1_n = cell_top_kind[(H, L)].most_common(1)[0]
        try:
            top2, top2_n = cell_top_kind[(H, L)].most_common(2)[1]
        except IndexError:
            top2, top2_n = "—", 0
        mid1, mid1_n = cell_mid_kind[(H, L)].most_common(1)[0]
        try:
            mid2, mid2_n = cell_mid_kind[(H, L)].most_common(2)[1]
        except IndexError:
            mid2, mid2_n = "—", 0
        combo1, combo1_n = combos.most_common(1)[0]
        label = f"{RANK_CHARS[H]}{RANK_CHARS[L]}"
        print(f"  {label:<6}  {n_cell:>7,}  {top1:<10}{top1_n*100/n_cell:>4.0f}%  "
              f"{top2:<10}{top2_n*100/n_cell:>4.0f}%  "
              f"{mid1:<10}{mid1_n*100/n_cell:>4.0f}%  "
              f"{mid2:<10}{mid2_n*100/n_cell:>4.0f}%  "
              f"{combo1} ({combo1_n*100/n_cell:.0f}%)")
        summary.append({
            "H": H, "L": L, "n": n_cell,
            "top1": top1, "top1_pct": top1_n/n_cell,
            "mid1": mid1, "mid1_pct": mid1_n/n_cell,
            "combo1": combo1, "combo1_pct": combo1_n/n_cell,
        })

    # Roll-up
    print("\n  Overall top-kind distribution:")
    overall_top = Counter()
    overall_mid = Counter()
    for cell, ctr in cell_top_kind.items():
        for k, v in ctr.items():
            overall_top[k] += v
    for cell, ctr in cell_mid_kind.items():
        for k, v in ctr.items():
            overall_mid[k] += v
    total = sum(overall_top.values())
    for k, v in overall_top.most_common():
        print(f"    {k:<14}  {v:>9,}  {100*v/total:>5.1f}%")
    print("\n  Overall mid-kind distribution:")
    for k, v in overall_mid.most_common():
        print(f"    {k:<18}  {v:>9,}  {100*v/total:>5.1f}%")

    pd.DataFrame(summary).to_csv(
        ROOT / "data" / "session42_drills" / "two_pair_oracle_pick_profile.csv",
        index=False)
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
