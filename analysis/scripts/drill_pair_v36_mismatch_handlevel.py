"""
Session 54 — Drill P2: pair zone hand-level mismatch inspection.

Drill P (aggregate) showed top mismatch: v36 picks mid_SS, oracle picks
bot_DS — 162,551 hands at $3,693 mean regret = $100/1000h whole-grid.

This drill extracts SAMPLE hands from this mismatch and characterizes the
structural difference. Goal: identify what features (suit alignment,
kicker structure, etc.) distinguish "pair-mid SS is right" from
"pair-bot DS is right" — informs Phase 2 feature design.

For each of the top sample hands:
  - print full hand (ranks + suits)
  - v36's chosen setting (top, mid, bot)
  - oracle's chosen setting (top, mid, bot)
  - structural delta (suit alignment, kicker ranks, etc.)

Also aggregate: for the v36=mid_SS, oracle=bot_DS mismatch:
  - How many singletons share a suit with the pair?
  - What's the pair-bot DS bot's typical kicker profile?
  - What suit pattern enables bot_DS?

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_pair_v36_mismatch_handlevel.py
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
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SETTING_HAND_INDICES,
)
from strategy_v36_dt import strategy_v36_dt  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}
SUIT_CHAR = {0: "♠", 1: "♥", 2: "♦", 3: "♣"}


def card_str(b):
    rank = (int(b) // 4) + 2
    suit = int(b) & 3
    return f"{RANK_CHAR[rank]}{SUIT_CHAR[suit]}"


def setting_to_pos(idx):
    return SETTING_HAND_INDICES[idx]  # (7,) — top, mid_a, mid_b, b1, b2, b3, b4


def main() -> int:
    print("=" * 88)
    print("Session 54 Drill P2: Pair zone hand-level mismatch inspection")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    pair_idx = np.where(cats == 1)[0]
    gf = read_oracle_grid(GRID_FULL, mode="memmap")

    # Find top-regret hands where v36=mid_SS and oracle=bot_DS
    print("\n[2/3] sweeping for v36=mid_SS oracle=bot_DS mismatches ...",
          flush=True)
    target_hands = []  # (regret, cid, hand_bytes, v36_idx, oracle_idx)
    n_processed = 0
    n_match = 0
    t0 = time.time()
    # For sake of time, just sample 500K — we don't need all of them
    sample_limit = 500_000
    for cid in pair_idx[:sample_limit]:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pair_rank = next(r for r in range(2, 15) if rc[r] == 2)
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v36_idx = int(strategy_v36_dt(h))

        # v36 mid_SS = pair-in-mid AND bot SS
        v36_pair_in_mid = bool(feats.mid_is_pair[v36_idx]) and int(feats.mid_pair_rank[v36_idx]) == pair_rank
        v36_SS = int(feats.bot_suit_profile[v36_idx]) == int(SUIT_PROFILE_SS)
        oracle_pair_in_bot = int(feats.bot_pair_rank[oracle_idx]) == pair_rank
        oracle_DS = int(feats.bot_suit_profile[oracle_idx]) == int(SUIT_PROFILE_DS)
        if not (v36_pair_in_mid and v36_SS and oracle_pair_in_bot and oracle_DS):
            n_processed += 1
            continue

        regret = float(rowf[oracle_idx]) - float(rowf[v36_idx])
        target_hands.append((regret, cid, h.copy(), v36_idx, oracle_idx, pair_rank))
        n_match += 1
        n_processed += 1

    print(f"  done in {time.time()-t0:.1f}s; n_processed={n_processed:,}, n_match={n_match:,}")

    # Sort by regret descending; sample top + middle + low for diversity
    target_hands.sort(key=lambda x: -x[0])
    sample_indices = list(range(0, min(20, len(target_hands))))  # top 20

    print(f"\n[3/3] inspecting top {len(sample_indices)} hands by regret ...\n")
    print("=" * 100)
    print("HAND-LEVEL INSPECTION: v36 picks mid_SS, oracle picks bot_DS")
    print("=" * 100)

    # Aggregates for feature signal extraction
    n_singletons_match_pair_suit = []
    pair_same_suit_count = 0
    n_total = 0

    for i in sample_indices:
        regret, cid, h, v36_idx, oracle_idx, pair_rank = target_hands[i]
        v36_pos = setting_to_pos(v36_idx)
        oracle_pos = setting_to_pos(oracle_idx)
        v36_top = h[v36_pos[0]]
        v36_mid = (h[v36_pos[1]], h[v36_pos[2]])
        v36_bot = tuple(h[p] for p in v36_pos[3:])
        oracle_top = h[oracle_pos[0]]
        oracle_mid = (h[oracle_pos[1]], h[oracle_pos[2]])
        oracle_bot = tuple(h[p] for p in oracle_pos[3:])
        hand_cards = " ".join(card_str(c) for c in h)
        print(f"\n  Hand {i+1} (cid={cid}): {hand_cards}  pair=P{RANK_CHAR[pair_rank]}  regret=${regret*10*1000:>+8.1f}/1000h")
        print(f"    v36 (mid_SS):   top={card_str(v36_top)}  "
              f"mid={card_str(v36_mid[0])} {card_str(v36_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in v36_bot)}")
        print(f"    oracle (bot_DS): top={card_str(oracle_top)}  "
              f"mid={card_str(oracle_mid[0])} {card_str(oracle_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in oracle_bot)}")

    # Aggregate for ALL matched hands
    print(f"\n── AGGREGATE STRUCTURAL FEATURES (all {n_match:,} mismatch hands) ──")
    pair_same_suit = 0
    sing_match_pair_suits = []  # how many sings share a suit with pair
    for regret, cid, h, v36_idx, oracle_idx, pair_rank in target_hands:
        ranks = (h // 4) + 2
        suits = h & 3
        pair_pos = [j for j in range(7) if int(ranks[j]) == pair_rank]
        sing_pos = [j for j in range(7) if int(ranks[j]) != pair_rank]
        pair_suits = {int(suits[p]) for p in pair_pos}
        if len(pair_suits) == 1:
            pair_same_suit += 1
        n_match_count = sum(1 for sp in sing_pos if int(suits[sp]) in pair_suits)
        sing_match_pair_suits.append(n_match_count)

    print(f"  Pair has same-suit (both cards same suit): {pair_same_suit:,} ({100*pair_same_suit/n_match:.1f}%)")
    print(f"  Pair has 2 distinct suits: {n_match-pair_same_suit:,} ({100*(n_match-pair_same_suit)/n_match:.1f}%)")
    print(f"\n  Distribution of '# singletons matching a pair-suit' (out of 5 sings):")
    cnt = Counter(sing_match_pair_suits)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    {k}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
