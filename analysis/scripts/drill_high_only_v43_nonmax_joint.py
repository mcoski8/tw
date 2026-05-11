"""
Session 58 — Drill HO10 (supplementary): NON-MAX-TOP joint enumeration.

HO8 surfaced a key gap: at lower max-ranks (J/T/9/8) oracle increasingly
picks settings where:
  - top != max-rank  (the max card is moved INTO the bot or mid)
  - bot is still DS / 4f / SS
  - mid is still suited
v43's ho_v3 features only describe joint-with-top=max. Anything outside
that window is invisible to the model.

This drill enumerates per-hand:
  n_joint_topNonMax_DS_ms     — count of (top!=max, bot 2+2 DS, mid suited)
  best_top_rank_topNonMax     — highest non-max rank achievable as top in
                                  any non-max-top joint config
  best_mid_high_topNonMax     — best higher-of-suited-mid across non-max-top
                                  joint configs
  best_bot_pair_high_topNonMax— best higher-of-suited-pair (across both
                                  suited pairs in DS) across non-max-top
                                  joints
  n_topMax_4f_ms              — count of (top=max, bot 4-flush, mid suited)
  best_mid_high_topMax_4f_ms  — best mid_high in those configs
  n_topMax_DS_ms_high_mid_J   — joint-with-top=max where mid_high >= J(11)
  n_topMax_DS_ms_high_mid_K   — joint-with-top=max where mid_high >= K(13)

Cross-tab vs oracle picks to identify which of these axes is the strongest
predictor of oracle's actual pick at each max_rank.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v43_nonmax_joint.py
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402

CANON = ROOT / "data" / "canonical_hands.bin"
OUT_PARQUET = ROOT / "data" / "drill_ho_v43_nonmax_joint.parquet"
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def compute_nonmax_joint_features(hand_bytes):
    """Returns dict with the 8 supplementary signals."""
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    max_rank = max(int_ranks)
    max_pos = int_ranks.index(max_rank)

    n_joint_nonmax = 0
    best_top_rank_nonmax = 0
    best_mid_high_nonmax = 0
    best_bot_pair_high_nonmax = 0
    n_topMax_4f_ms = 0
    best_mid_high_topMax_4f_ms = 0
    n_topMax_joint_high_mid_J = 0
    n_topMax_joint_high_mid_K = 0

    # Enumerate ALL settings: top in {0..6}, mid_pair in C(remaining, 2)
    for top_pos in range(7):
        rest = [i for i in range(7) if i != top_pos]
        top_rank = int_ranks[top_pos]
        for mid_a, mid_b in combinations(rest, 2):
            if int_suits[mid_a] != int_suits[mid_b]:
                continue
            bot_pos = [i for i in rest if i != mid_a and i != mid_b]
            bs = [int_suits[i] for i in bot_pos]
            cnt = sorted(Counter(bs).values(), reverse=True)
            br = [int_ranks[i] for i in bot_pos]
            mid_high = max(int_ranks[mid_a], int_ranks[mid_b])

            if cnt == [2, 2]:  # DS
                if top_pos == max_pos:
                    # joint top=max
                    if mid_high >= 11:
                        n_topMax_joint_high_mid_J += 1
                    if mid_high >= 13:
                        n_topMax_joint_high_mid_K += 1
                else:
                    # joint top!=max (max is in bot or mid)
                    n_joint_nonmax += 1
                    if top_rank > best_top_rank_nonmax:
                        best_top_rank_nonmax = top_rank
                    if mid_high > best_mid_high_nonmax:
                        best_mid_high_nonmax = mid_high
                    by_suit = defaultdict(list)
                    for r, s in zip(br, bs):
                        by_suit[s].append(r)
                    bot_ph = max(max(rs) for rs in by_suit.values() if len(rs) >= 2)
                    if bot_ph > best_bot_pair_high_nonmax:
                        best_bot_pair_high_nonmax = bot_ph
            elif cnt == [4]:  # 4-flush
                if top_pos == max_pos:
                    n_topMax_4f_ms += 1
                    if mid_high > best_mid_high_topMax_4f_ms:
                        best_mid_high_topMax_4f_ms = mid_high

    return {
        "max_rank": max_rank,
        "n_joint_topNonMax": n_joint_nonmax,
        "best_top_rank_topNonMax": best_top_rank_nonmax,
        "best_mid_high_topNonMax": best_mid_high_nonmax,
        "best_bot_pair_high_topNonMax": best_bot_pair_high_nonmax,
        "n_topMax_4f_ms": n_topMax_4f_ms,
        "best_mid_high_topMax_4f_ms": best_mid_high_topMax_4f_ms,
        "n_topMax_DS_ms_high_mid_J": n_topMax_joint_high_mid_J,
        "n_topMax_DS_ms_high_mid_K": n_topMax_joint_high_mid_K,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 58 — Drill HO10: NON-MAX-TOP joint enumeration (supplementary)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/2] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]
    if args.sample > 0 and len(ho_idx) > args.sample:
        rng = np.random.default_rng(args.seed)
        ho_idx = np.sort(rng.choice(ho_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")
    n = len(ho_idx)
    print(f"  high_only n={n:,}")

    arr_cid = np.zeros(n, dtype=np.uint32)
    arr_max = np.zeros(n, dtype=np.int8)
    arr_n_joint_nonmax = np.zeros(n, dtype=np.int8)
    arr_best_top_nonmax = np.zeros(n, dtype=np.int8)
    arr_best_mid_high_nonmax = np.zeros(n, dtype=np.int8)
    arr_best_bot_ph_nonmax = np.zeros(n, dtype=np.int8)
    arr_n_4f_ms = np.zeros(n, dtype=np.int8)
    arr_best_mid_high_4f = np.zeros(n, dtype=np.int8)
    arr_n_joint_high_mid_J = np.zeros(n, dtype=np.int8)
    arr_n_joint_high_mid_K = np.zeros(n, dtype=np.int8)

    print("\n[2/2] enumerating per-hand ...", flush=True)
    t0 = time.time()
    for k, cid in enumerate(ho_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        f = compute_nonmax_joint_features(h)
        arr_cid[k] = cid
        arr_max[k] = f["max_rank"]
        arr_n_joint_nonmax[k] = f["n_joint_topNonMax"]
        arr_best_top_nonmax[k] = f["best_top_rank_topNonMax"]
        arr_best_mid_high_nonmax[k] = f["best_mid_high_topNonMax"]
        arr_best_bot_ph_nonmax[k] = f["best_bot_pair_high_topNonMax"]
        arr_n_4f_ms[k] = f["n_topMax_4f_ms"]
        arr_best_mid_high_4f[k] = f["best_mid_high_topMax_4f_ms"]
        arr_n_joint_high_mid_J[k] = f["n_topMax_DS_ms_high_mid_J"]
        arr_n_joint_high_mid_K[k] = f["n_topMax_DS_ms_high_mid_K"]
        if (k + 1) % 100_000 == 0:
            rate = (k + 1) / (time.time() - t0)
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"ETA {eta:>5.0f}s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s\n")

    table = pa.table({
        "canonical_id": pa.array(arr_cid, type=pa.uint32()),
        "max_rank": pa.array(arr_max, type=pa.int8()),
        "n_joint_topNonMax": pa.array(arr_n_joint_nonmax, type=pa.int8()),
        "best_top_rank_topNonMax": pa.array(arr_best_top_nonmax, type=pa.int8()),
        "best_mid_high_topNonMax": pa.array(arr_best_mid_high_nonmax, type=pa.int8()),
        "best_bot_pair_high_topNonMax": pa.array(arr_best_bot_ph_nonmax, type=pa.int8()),
        "n_topMax_4f_ms": pa.array(arr_n_4f_ms, type=pa.int8()),
        "best_mid_high_topMax_4f_ms": pa.array(arr_best_mid_high_4f, type=pa.int8()),
        "n_topMax_DS_ms_high_mid_J": pa.array(arr_n_joint_high_mid_J, type=pa.int8()),
        "n_topMax_DS_ms_high_mid_K": pa.array(arr_n_joint_high_mid_K, type=pa.int8()),
    })
    pq.write_table(table, OUT_PARQUET, compression="zstd",
                   compression_level=3, write_statistics=True)
    sz = OUT_PARQUET.stat().st_size / 1024 / 1024
    print(f"  wrote {OUT_PARQUET} ({sz:.2f} MB)")

    # Quick distributions
    print("\n— Distribution of n_joint_topNonMax across high_only hands —")
    cnt = Counter(arr_n_joint_nonmax.tolist())
    for k_ in sorted(cnt.keys()):
        print(f"  n_joint_topNonMax={k_:>3}: {cnt[k_]:>10,} ({100*cnt[k_]/n:.1f}%)")

    print("\n— per-max-rank: % of hands with n_joint_topNonMax > 0 —")
    for mr in sorted(set(arr_max.tolist()), reverse=True):
        mask = arr_max == mr
        n_in = mask.sum()
        n_with_nonmax = ((arr_n_joint_nonmax > 0) & mask).sum()
        n_with_4f = ((arr_n_4f_ms > 0) & mask).sum()
        n_high_mid_J = ((arr_n_joint_high_mid_J > 0) & mask).sum()
        n_high_mid_K = ((arr_n_joint_high_mid_K > 0) & mask).sum()
        print(f"  max={RANK_CHAR.get(mr, mr):>2}: n={n_in:>9,}  "
              f"n_joint_nonmax>0: {100*n_with_nonmax/n_in:>5.1f}%  "
              f"n_4f_ms_top_max>0: {100*n_with_4f/n_in:>5.1f}%  "
              f"joint_mid>=J: {100*n_high_mid_J/n_in:>5.1f}%  "
              f"joint_mid>=K: {100*n_high_mid_K/n_in:>5.1f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
