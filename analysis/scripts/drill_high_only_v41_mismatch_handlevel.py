"""
Session 56 — Drill HO2: high_only hand-level mismatch inspection.

Drill HO (aggregate) — full 1.23M sweep — confirmed:
  - SS->DS suit-profile swap = 236,205 hands @ $5,344 = $210.08/1000h
    whole-grid (44% of all high_only mismatch contribution).
  - Top single-class mismatch: v41=tA_SS_mu, oracle=tA_DS_ms — 28,014
    hands @ $7,774 mean regret = $36.24/1000h whole-grid.
  - 92% of high_only residual is in the top 6 (h1,h2) broadway cells:
    A-K $143.64, K-Q $92.08, A-Q $75.35, Q-J $50.58, K-J $44.09, A-J $36.18.

This drill extracts the top-20 hands of (v41=tA_SS_mu, oracle=tA_DS_ms)
and characterizes the structural delta. Goal: identify what features
distinguish "Ace top + SS bot + unsuited mid" picks from "Ace top + DS
bot + suited mid" picks within high_only.

For top hands:
  - print full hand (ranks + suits)
  - v41's chosen setting (top, mid, bot)
  - oracle's chosen setting (top, mid, bot)

Aggregate signals across ALL matched hands:
  - n DS-bot configs achievable (C(7,4)=35 enumerated, filtered to 2+2)
  - max_top_rank achievable while keeping bot DS
  - max_mid_sum achievable while keeping bot DS
  - whether oracle's chosen DS bot uses the maximum-rank top across
    DS configs

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v41_mismatch_handlevel.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SETTING_HAND_INDICES,
    SUIT_PROFILE_DS, SUIT_PROFILE_SS,
)
from strategy_v41_dt import strategy_v41_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}
SUIT_CHAR = {0: "s", 1: "h", 2: "d", 3: "c"}


def card_str(b):
    rank = (int(b) // 4) + 2
    suit = int(b) & 3
    return f"{RANK_CHAR[rank]}{SUIT_CHAR[suit]}"


def setting_to_pos(idx):
    return SETTING_HAND_INDICES[idx]


def is_top_rank(hand_bytes, idx, want_rank: int) -> bool:
    pos = SETTING_HAND_INDICES[idx]
    ranks = (hand_bytes // 4) + 2
    return int(ranks[int(pos[0])]) == want_rank


def is_mid_unsuited(hand_bytes, idx) -> bool:
    pos = SETTING_HAND_INDICES[idx]
    suits = hand_bytes & 3
    return int(suits[int(pos[1])]) != int(suits[int(pos[2])])


def main() -> int:
    print("=" * 88)
    print("Session 56 Drill HO2: High_only hand-level mismatch inspection")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print(f"  high_only n={len(ho_idx):,}")

    print("\n[2/3] sweeping for v41=tA_SS_mu oracle=tA_DS_ms mismatches ...",
          flush=True)
    target_hands = []
    n_processed = 0
    n_match = 0
    t0 = time.time()
    for cid in ho_idx:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v41_idx = int(strategy_v41_dt(h))

        # v41: top=A, bot=SS, mid unsuited
        v41_topA = is_top_rank(h, v41_idx, 14)
        v41_SS = int(feats.bot_suit_profile[v41_idx]) == int(SUIT_PROFILE_SS)
        v41_mu = is_mid_unsuited(h, v41_idx)
        # oracle: top=A, bot=DS, mid suited
        oracle_topA = is_top_rank(h, oracle_idx, 14)
        oracle_DS = int(feats.bot_suit_profile[oracle_idx]) == int(SUIT_PROFILE_DS)
        oracle_ms = not is_mid_unsuited(h, oracle_idx)
        if not (v41_topA and v41_SS and v41_mu and oracle_topA and oracle_DS and oracle_ms):
            n_processed += 1
            continue

        regret = float(rowf[oracle_idx]) - float(rowf[v41_idx])
        target_hands.append((regret, cid, h.copy(), v41_idx, oracle_idx))
        n_match += 1
        n_processed += 1
        if n_processed % 200000 == 0:
            print(f"    progress {n_processed:>7,}/{len(ho_idx):,}  "
                  f"matched={n_match:,}  rate={n_processed/(time.time()-t0):.0f}/s",
                  flush=True)

    print(f"  done in {time.time()-t0:.1f}s; n_processed={n_processed:,}, n_match={n_match:,}")

    target_hands.sort(key=lambda x: -x[0])
    sample_indices = list(range(0, min(20, len(target_hands))))

    print(f"\n[3/3] inspecting top {len(sample_indices)} hands by regret ...\n")
    print("=" * 110)
    print("HAND-LEVEL INSPECTION: v41 picks tA_SS_mu, oracle picks tA_DS_ms")
    print("=" * 110)

    for i in sample_indices:
        regret, cid, h, v41_idx, oracle_idx = target_hands[i]
        v41_pos = setting_to_pos(v41_idx)
        oracle_pos = setting_to_pos(oracle_idx)
        v41_top = h[v41_pos[0]]
        v41_mid = (h[v41_pos[1]], h[v41_pos[2]])
        v41_bot = tuple(h[p] for p in v41_pos[3:])
        oracle_top = h[oracle_pos[0]]
        oracle_mid = (h[oracle_pos[1]], h[oracle_pos[2]])
        oracle_bot = tuple(h[p] for p in oracle_pos[3:])
        hand_cards = " ".join(card_str(c) for c in h)
        print(f"\n  Hand {i+1} (cid={cid}): {hand_cards}  regret=${regret*10*1000:>+8.1f}/1000h")
        print(f"    v41    (tA_SS_mu): top={card_str(v41_top)}  "
              f"mid={card_str(v41_mid[0])} {card_str(v41_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in v41_bot)}")
        print(f"    oracle (tA_DS_ms): top={card_str(oracle_top)}  "
              f"mid={card_str(oracle_mid[0])} {card_str(oracle_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in oracle_bot)}")

    # Aggregate signals across all matched hands.
    print(f"\n── AGGREGATE STRUCTURAL FEATURES (all {n_match:,} mismatch hands) ──")

    n_DS_configs_dist = []
    max_top_rank_dist = []
    min_top_rank_dist = []
    max_mid_sum_dist = []
    oracle_uses_max_top = []
    oracle_uses_min_top = []
    suit_dist_4321 = Counter()  # canonical suit distribution counts (e.g. (3,2,1,1))

    for regret, cid, h, v41_idx, oracle_idx in target_hands:
        ranks = (h // 4) + 2
        suits = h & 3
        int_ranks = [int(r) for r in ranks]
        int_suits = [int(s) for s in suits]
        # canonical suit distribution
        sc = Counter(int_suits)
        sd = tuple(sorted(sc.values(), reverse=True))
        suit_dist_4321[sd] += 1

        # Enumerate DS bot configs.
        n_cfg = 0
        max_top = 0
        min_top = 99
        max_mid_sum = 0
        for bot_idx in combinations(range(7), 4):
            bs = [int_suits[i] for i in bot_idx]
            cnt = sorted(Counter(bs).values(), reverse=True)
            if cnt != [2, 2]:
                continue
            n_cfg += 1
            leftover = [i for i in range(7) if i not in bot_idx]
            lr = sorted([int_ranks[i] for i in leftover], reverse=True)
            cfg_max_top = lr[0]
            cfg_min_top = lr[2]
            cfg_max_mid_sum = lr[0] + lr[1]
            if cfg_max_top > max_top: max_top = cfg_max_top
            if cfg_min_top < min_top: min_top = cfg_min_top
            if cfg_max_mid_sum > max_mid_sum: max_mid_sum = cfg_max_mid_sum
        n_DS_configs_dist.append(n_cfg)
        max_top_rank_dist.append(max_top)
        min_top_rank_dist.append(min_top if min_top != 99 else 0)
        max_mid_sum_dist.append(max_mid_sum)

        # Did oracle pick a DS config with the max_top rank?
        opos = SETTING_HAND_INDICES[oracle_idx]
        oracle_top_rank = int(int_ranks[int(opos[0])])
        oracle_uses_max_top.append(oracle_top_rank == max_top)
        oracle_uses_min_top.append(oracle_top_rank == min_top)

    print(f"\n  ho_v2_bot_DS_n_configs distribution:")
    cnt = Counter(n_DS_configs_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    n_configs={k:>2}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\n  ho_v2_bot_DS_max_top_rank distribution (best top achievable across DS):")
    cnt = Counter(max_top_rank_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    max_top={RANK_CHAR.get(k, k):<2}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\n  ho_v2_bot_DS_min_top_rank distribution:")
    cnt = Counter(min_top_rank_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    min_top={RANK_CHAR.get(k, k):<2}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\n  ho_v2_bot_DS_max_mid_sum distribution:")
    cnt = Counter(max_mid_sum_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    max_mid_sum={k:>2}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\n  Oracle's chosen top == max_top across DS configs?")
    oracle_max_pct = 100 * sum(oracle_uses_max_top) / n_match
    oracle_min_pct = 100 * sum(oracle_uses_min_top) / n_match
    print(f"    oracle top is max_top:  {sum(oracle_uses_max_top):>6,} ({oracle_max_pct:.1f}%)")
    print(f"    oracle top is min_top:  {sum(oracle_uses_min_top):>6,} ({oracle_min_pct:.1f}%)")

    print(f"\n  Canonical 7-card suit distribution among mismatch hands:")
    for sd, n in suit_dist_4321.most_common():
        print(f"    {str(sd):<14} {n:>6,} ({100*n/n_match:.1f}%)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
