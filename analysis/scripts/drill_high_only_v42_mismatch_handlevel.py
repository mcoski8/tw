"""
Session 57 — Drill HO4: high_only hand-level mismatch inspection on v42_dt.

Phase 1 (drill_high_only_zone_v42_diagnostic.py) showed that after S56's
ho_v2 features collapsed parts of the high_only zone, the SAME SS->DS
bot-suit-swap pattern is STILL the dominant residual:
  - v42 picks SS bot 46.07% vs oracle 32.04% (-14.0% absolute)
  - Largest single class: v42=tA_SS_mu, oracle=tA_DS_ms
        28,027 hands @ $7,534 = $35.14/1000h whole-grid (essentially
        UNCHANGED from v41's 28,014 hands — the ho_v2 features did NOT
        meaningfully collapse this exact class).
  - 2nd: tA_SS_mu -> tA_DS_mu  ($25.61, n=35,332) — bot-suit-only swap
  - 3rd: tA_SS_mu -> tA_SS_ms  ($23.68, n=33,559) — MID-SUIT-only swap
  - tK_SS_mu -> tK_DS_ms       ($17.05, n=13,229) — same pattern at K-top

Hypothesis: v42's ho_v2 features expose DS-BOT achievability but NOT
joint (DS bot + suited mid) achievability. The mid-suit-only swap class
shows mid suiting matters as a distinct axis. Joint feature shape:
"can we go DS bot AND keep mid suited at the same time?"

This drill: for each (v42=tA_SS_mu, oracle=tA_DS_ms) mismatch hand,
characterize:
  - n_DS_configs (any 2+2 bot)
  - n_DS_AND_mid_ms configs (bot 2+2 AND the 2 leftover-non-top cards
    share a suit)
  - max_top_rank achievable in (DS-only) configs
  - max_top_rank achievable in (DS + mid_ms) joint configs
  - oracle's chosen routing: does it use the joint or DS-only path?

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v42_mismatch_handlevel.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter
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
from strategy_v42_dt import strategy_v42_dt  # noqa: E402

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
    print("Session 57 Drill HO4: High_only hand-level mismatch inspection (v42_dt)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print(f"  high_only n={len(ho_idx):,}")

    print("\n[2/3] sweeping for v42=tA_SS_mu oracle=tA_DS_ms mismatches ...",
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
        v42_idx = int(strategy_v42_dt(h))

        v42_topA = is_top_rank(h, v42_idx, 14)
        v42_SS = int(feats.bot_suit_profile[v42_idx]) == int(SUIT_PROFILE_SS)
        v42_mu = is_mid_unsuited(h, v42_idx)
        oracle_topA = is_top_rank(h, oracle_idx, 14)
        oracle_DS = int(feats.bot_suit_profile[oracle_idx]) == int(SUIT_PROFILE_DS)
        oracle_ms = not is_mid_unsuited(h, oracle_idx)
        if not (v42_topA and v42_SS and v42_mu and oracle_topA and oracle_DS and oracle_ms):
            n_processed += 1
            continue

        regret = float(rowf[oracle_idx]) - float(rowf[v42_idx])
        target_hands.append((regret, cid, h.copy(), v42_idx, oracle_idx))
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
    print("HAND-LEVEL INSPECTION: v42 picks tA_SS_mu, oracle picks tA_DS_ms")
    print("=" * 110)

    for i in sample_indices:
        regret, cid, h, v42_idx, oracle_idx = target_hands[i]
        v42_pos = setting_to_pos(v42_idx)
        oracle_pos = setting_to_pos(oracle_idx)
        v42_top = h[v42_pos[0]]
        v42_mid = (h[v42_pos[1]], h[v42_pos[2]])
        v42_bot = tuple(h[p] for p in v42_pos[3:])
        oracle_top = h[oracle_pos[0]]
        oracle_mid = (h[oracle_pos[1]], h[oracle_pos[2]])
        oracle_bot = tuple(h[p] for p in oracle_pos[3:])
        hand_cards = " ".join(card_str(c) for c in h)
        print(f"\n  Hand {i+1} (cid={cid}): {hand_cards}  regret=${regret*10*1000:>+8.1f}/1000h")
        print(f"    v42    (tA_SS_mu): top={card_str(v42_top)}  "
              f"mid={card_str(v42_mid[0])} {card_str(v42_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in v42_bot)}")
        print(f"    oracle (tA_DS_ms): top={card_str(oracle_top)}  "
              f"mid={card_str(oracle_mid[0])} {card_str(oracle_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in oracle_bot)}")

    print(f"\n── AGGREGATE STRUCTURAL FEATURES (all {n_match:,} mismatch hands) ──")

    # For each hand, enumerate (bot 4-card subset, top from 3 leftovers).
    # Joint = bot is 2+2 DS AND the 2 non-top leftovers share a suit.
    n_DS_only_dist = []
    n_DS_AND_ms_dist = []
    DS_only_max_top_dist = []
    DS_AND_ms_max_top_dist = []
    DS_AND_ms_max_mid_high_dist = []
    DS_AND_ms_max_mid_sum_dist = []
    oracle_uses_joint = []
    oracle_mid_pair_high = []
    oracle_mid_pair_sum = []

    for regret, cid, h, v42_idx, oracle_idx in target_hands:
        ranks = (h // 4) + 2
        suits = h & 3
        int_ranks = [int(r) for r in ranks]
        int_suits = [int(s) for s in suits]

        n_DS_only = 0
        n_DS_AND_ms = 0
        DS_only_max_top = 0
        DS_AND_ms_max_top = 0
        DS_AND_ms_max_mid_high = 0
        DS_AND_ms_max_mid_sum = 0

        for bot_idx in combinations(range(7), 4):
            bs = [int_suits[i] for i in bot_idx]
            cnt = sorted(Counter(bs).values(), reverse=True)
            if cnt != [2, 2]:
                continue
            leftover_pos = [i for i in range(7) if i not in bot_idx]
            leftover_ranks = [int_ranks[i] for i in leftover_pos]
            leftover_suits = [int_suits[i] for i in leftover_pos]
            # For each (bot subset), enumerate top choice = each of 3 leftovers
            for top_choice in range(3):
                mid_pos = [j for j in range(3) if j != top_choice]
                top_rank = leftover_ranks[top_choice]
                mid_ranks = sorted([leftover_ranks[mid_pos[0]], leftover_ranks[mid_pos[1]]],
                                    reverse=True)
                mid_suits = (leftover_suits[mid_pos[0]], leftover_suits[mid_pos[1]])
                n_DS_only += 1
                if top_rank > DS_only_max_top:
                    DS_only_max_top = top_rank
                if mid_suits[0] == mid_suits[1]:
                    n_DS_AND_ms += 1
                    if top_rank > DS_AND_ms_max_top:
                        DS_AND_ms_max_top = top_rank
                    if mid_ranks[0] > DS_AND_ms_max_mid_high:
                        DS_AND_ms_max_mid_high = mid_ranks[0]
                    cur_sum = mid_ranks[0] + mid_ranks[1]
                    if cur_sum > DS_AND_ms_max_mid_sum:
                        DS_AND_ms_max_mid_sum = cur_sum

        n_DS_only_dist.append(n_DS_only)
        n_DS_AND_ms_dist.append(n_DS_AND_ms)
        DS_only_max_top_dist.append(DS_only_max_top)
        DS_AND_ms_max_top_dist.append(DS_AND_ms_max_top)
        DS_AND_ms_max_mid_high_dist.append(DS_AND_ms_max_mid_high)
        DS_AND_ms_max_mid_sum_dist.append(DS_AND_ms_max_mid_sum)

        # Oracle's actual mid (already known to be suited, top is Ace, bot is DS)
        opos = SETTING_HAND_INDICES[oracle_idx]
        omid_p1, omid_p2 = int(opos[1]), int(opos[2])
        oracle_mid_ranks = sorted([int_ranks[omid_p1], int_ranks[omid_p2]], reverse=True)
        oracle_mid_pair_high.append(oracle_mid_ranks[0])
        oracle_mid_pair_sum.append(oracle_mid_ranks[0] + oracle_mid_ranks[1])
        # Joint achievability is guaranteed (oracle picks tA_DS_ms), but check
        # whether the oracle's mid is the highest available mid pair.
        oracle_uses_joint.append(1)

    n = len(n_DS_only_dist)
    print(f"\n  n_DS_configs (any 2+2 bot, x3 top choices = TOTAL config count):")
    cnt = Counter(n_DS_only_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    n={k:>3}: {v:>6,} ({100*v/n:.1f}%)")

    print(f"\n  n_DS_AND_mid_ms_configs (joint: bot 2+2 AND non-top mid suited):")
    cnt = Counter(n_DS_AND_ms_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    n={k:>3}: {v:>6,} ({100*v/n:.1f}%)")

    print(f"\n  DS_only_max_top distribution (best top across ANY DS bot):")
    cnt = Counter(DS_only_max_top_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    max_top={RANK_CHAR.get(k, k):<2}: {v:>6,} ({100*v/n:.1f}%)")

    print(f"\n  DS_AND_ms_max_top distribution (best top in joint configs):")
    cnt = Counter(DS_AND_ms_max_top_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        label = RANK_CHAR.get(k, str(k)) if k > 0 else "0(none)"
        print(f"    max_top={label:<7}: {v:>6,} ({100*v/n:.1f}%)")

    print(f"\n  DS_AND_ms_max_mid_high distribution (best high-rank-of-suited-mid):")
    cnt = Counter(DS_AND_ms_max_mid_high_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        label = RANK_CHAR.get(k, str(k)) if k > 0 else "0(none)"
        print(f"    max_mid_high={label:<7}: {v:>6,} ({100*v/n:.1f}%)")

    print(f"\n  DS_AND_ms_max_mid_sum distribution (best sum of suited-mid pair):")
    cnt = Counter(DS_AND_ms_max_mid_sum_dist)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    max_mid_sum={k:>3}: {v:>6,} ({100*v/n:.1f}%)")

    print(f"\n  Oracle's actual mid pair high (= rank of higher card of the suited mid):")
    cnt = Counter(oracle_mid_pair_high)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    mid_high={RANK_CHAR.get(k, k):<2}: {v:>6,} ({100*v/n:.1f}%)")

    # Critical question: does oracle ALWAYS pick a JOINT (DS+ms) config that
    # leaves Ace on top AND has the best available suited mid?
    n_joint_with_topA = sum(1 for x in DS_AND_ms_max_top_dist if x == 14)
    print(f"\n  Joint configs with topA achievable: {n_joint_with_topA:,} ({100*n_joint_with_topA/n:.1f}%)")
    print(f"  (This should be 100% since oracle picks tA_DS_ms by definition.)")

    # How does oracle's mid_high compare to max_mid_high in joint configs?
    matches = sum(1 for o, m in zip(oracle_mid_pair_high, DS_AND_ms_max_mid_high_dist) if o == m)
    print(f"\n  Oracle's mid_high == DS_AND_ms_max_mid_high (best available): "
          f"{matches:,} ({100*matches/n:.1f}%)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
