"""
Session 42 deep-dive — pair category (Rule 1 extension exploration).

The pair category is 46.6% of hands — the BIGGEST category. Rule 1 currently
fires on only 2.19% of hands (heavy gating: pair-rank ∈ 2-5 OR T-J-Q, has
Ace, balanced kickers, etc.). The other 44%+ of pair hands fall through
to v33's default (v8_hybrid).

Within v34_dt's residuals, pair has $754 share — biggest after high_only.
There must be additional structural rules.

This drill characterizes oracle picks across the pair population:
  - For each pair-rank, find oracle's preferred top/mid pattern
  - Identify sub-categories with consistent oracle preference
  - Test deterministic candidate rules

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_pair_rule1_extension.py
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
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
EV_TO_DOL = 10.0

RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 42 deep-dive: pair category (Rule 1 extension)")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading pair mask + grid ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads"])
    mask = ((ft["n_pairs"].to_numpy() == 1)
            & (ft["n_trips"].to_numpy() == 0)
            & (ft["n_quads"].to_numpy() == 0))
    n_pair = int(mask.sum())
    pair_idx = np.where(mask)[0]
    print(f"  pair: {n_pair:,}")
    pop_share = n_pair / len(ft)

    ch = read_canonical_hands(CANON, mode="memmap")
    grid = read_oracle_grid(GRID_FULL, mode="memmap")

    # Sample 100K hands for fast analysis
    sample_size = min(100_000, n_pair)
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(pair_idx, sample_size, replace=False)

    print(f"\n[2/3] characterizing oracle picks ({sample_size:,} sample) ...",
          flush=True)
    pair_rank_counts = defaultdict(Counter)  # by pair_rank → top_kind/mid_kind counter
    overall_top = Counter()
    overall_mid = Counter()
    overall_top_by_pair_rank = defaultdict(Counter)
    overall_mid_by_pair_rank = defaultdict(Counter)
    v33_loss_per_pair_rank = defaultdict(list)

    t0 = time.time()
    last_log = time.time()

    for i, cid in enumerate(sample_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)

        row = np.asarray(grid.evs[int(cid)], dtype=np.float64)
        oracle_pick = int(np.argmax(row))
        v33_pick = int(strategy_v37_rule7_three_pair(h))
        feats = setting_features_from_bytes(h)

        top_idx = oracle_pick // 15
        top_rank = int(ranks[top_idx])
        if top_rank == P:
            top_kind = "pair_member"
        else:
            # Map to "1st_sing" / "2nd_sing" / ...
            sings_idx = sings.index(top_rank)
            top_kind = f"s{sings_idx+1}"

        if bool(feats.mid_is_pair[oracle_pick]):
            mid_pr = int(feats.mid_pair_rank[oracle_pick])
            if mid_pr == P:
                mid_kind = "P_pair"
            else:
                mid_kind = "other_pair"
        else:
            mid_kind = "unpaired"

        overall_top[top_kind] += 1
        overall_mid[mid_kind] += 1
        overall_top_by_pair_rank[P][top_kind] += 1
        overall_mid_by_pair_rank[P][mid_kind] += 1
        v33_loss_per_pair_rank[P].append(row[oracle_pick] - row[v33_pick])

        if time.time() - last_log > 8:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>6,}/{sample_size:,}  rate={rate:.0f}/s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.0f}s")

    print(f"\n[3/3] PER-PAIR-RANK ORACLE PICK PROFILE")
    print(f"  Overall top distribution:")
    n_total = sum(overall_top.values())
    for k, v in overall_top.most_common():
        print(f"    {k:<14}  {v:>7,}  {100*v/n_total:>5.1f}%")
    print(f"\n  Overall mid distribution:")
    for k, v in overall_mid.most_common():
        print(f"    {k:<14}  {v:>7,}  {100*v/n_total:>5.1f}%")

    print(f"\n  By pair-rank:")
    print(f"  {'P':>2}  {'n':>6}  {'v33_loss_$':>10}  {'top1':>14}  "
          f"{'top2':>14}  {'mid1':>14}  {'mid2':>14}")
    for P in range(14, 1, -1):
        if P not in overall_top_by_pair_rank:
            continue
        cnt = overall_top_by_pair_rank[P]
        mid_cnt = overall_mid_by_pair_rank[P]
        n = sum(cnt.values())
        v33_loss_arr = np.array(v33_loss_per_pair_rank[P])
        v33_loss = v33_loss_arr.mean() * EV_TO_DOL * 1000
        top1, top1_n = cnt.most_common(1)[0]
        top2 = cnt.most_common(2)[1] if len(cnt) > 1 else ("—", 0)
        mid1, mid1_n = mid_cnt.most_common(1)[0]
        mid2 = mid_cnt.most_common(2)[1] if len(mid_cnt) > 1 else ("—", 0)
        print(f"  {RANK_CHARS[P]:>2}  {n:>6,}  ${v33_loss:>+8.1f}/h  "
              f"{top1:<8}{top1_n*100/n:>4.0f}%  "
              f"{top2[0]:<8}{top2[1]*100/n:>4.0f}%  "
              f"{mid1:<8}{mid1_n*100/n:>4.0f}%  "
              f"{mid2[0]:<8}{mid2[1]*100/n:>4.0f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
