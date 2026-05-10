"""
Session 55 — Drill TP2: trips_pair hand-level mismatch inspection.

Drill TP (aggregate) showed top mismatch: v39 picks Pbot_SS while oracle
picks Pbot_DS — 10,398 hands at $3,580 mean regret = $6.20/1000h whole-grid
contribution from a single mismatch class.

This drill extracts SAMPLE hands and characterizes the structural delta.
Goal: identify what features distinguish "pair-bot SS" picks from
"pair-bot DS" picks within the trips_pair zone.

For top hands in (v39=Pbot_SS, oracle=Pbot_DS):
  - print full hand (ranks + suits)
  - v39's chosen setting (top, mid, bot)
  - oracle's chosen setting (top, mid, bot)

Aggregate signals across ALL matched hands:
  - Pair suit distribution: same-suit pair vs 2-distinct-suit pair
  - For each Pbot_DS-routing path, count how many singletons / trip cards
    are positioned to enable each path
  - Sing distribution: how many singletons share a suit with the pair

Routes that can yield Pbot_DS (when pair_in_bot, bot=DS):
  R1: bot = pair + 2 sings, where sings fill pair's 2 suits.
      Requires pair has 2 distinct suits AND one sing of each pair-suit.
  R2: bot = pair + 1 trip + 1 sing, suit-aligned with pair.
  R3: bot = pair + 2 trip cards, suit-aligned with pair.
  R4 (pair has same-suit, 2 of S1): bot = pair + 2 cards of single other
     suit S2. Both cards same suit ≠ S1.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_trips_pair_v39_mismatch_handlevel.py
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
from strategy_v39_dt import strategy_v39_dt  # noqa: E402

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


def main() -> int:
    print("=" * 88)
    print("Session 55 Drill TP2: Trips_pair hand-level mismatch inspection")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tp_idx = np.where(cats == 4)[0]
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print(f"  trips_pair n={len(tp_idx):,}")

    print("\n[2/3] sweeping for v39=Pbot_SS oracle=Pbot_DS mismatches ...",
          flush=True)
    target_hands = []
    n_processed = 0
    n_match = 0
    t0 = time.time()
    for cid in tp_idx:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        trip_rank = next(r for r in range(2, 15) if rc[r] == 3)
        pair_rank = next(r for r in range(2, 15) if rc[r] == 2)
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v39_idx = int(strategy_v39_dt(h))

        v39_Pbot = int(feats.bot_pair_rank[v39_idx]) == pair_rank
        v39_SS = int(feats.bot_suit_profile[v39_idx]) == int(SUIT_PROFILE_SS)
        oracle_Pbot = int(feats.bot_pair_rank[oracle_idx]) == pair_rank
        oracle_DS = int(feats.bot_suit_profile[oracle_idx]) == int(SUIT_PROFILE_DS)
        if not (v39_Pbot and v39_SS and oracle_Pbot and oracle_DS):
            n_processed += 1
            continue

        regret = float(rowf[oracle_idx]) - float(rowf[v39_idx])
        target_hands.append((regret, cid, h.copy(), v39_idx, oracle_idx,
                              trip_rank, pair_rank))
        n_match += 1
        n_processed += 1

    print(f"  done in {time.time()-t0:.1f}s; n_processed={n_processed:,}, n_match={n_match:,}")

    target_hands.sort(key=lambda x: -x[0])
    sample_indices = list(range(0, min(20, len(target_hands))))

    print(f"\n[3/3] inspecting top {len(sample_indices)} hands by regret ...\n")
    print("=" * 110)
    print("HAND-LEVEL INSPECTION: v39 picks Pbot_SS, oracle picks Pbot_DS")
    print("=" * 110)

    for i in sample_indices:
        regret, cid, h, v39_idx, oracle_idx, trip_rank, pair_rank = target_hands[i]
        v39_pos = setting_to_pos(v39_idx)
        oracle_pos = setting_to_pos(oracle_idx)
        v39_top = h[v39_pos[0]]
        v39_mid = (h[v39_pos[1]], h[v39_pos[2]])
        v39_bot = tuple(h[p] for p in v39_pos[3:])
        oracle_top = h[oracle_pos[0]]
        oracle_mid = (h[oracle_pos[1]], h[oracle_pos[2]])
        oracle_bot = tuple(h[p] for p in oracle_pos[3:])
        hand_cards = " ".join(card_str(c) for c in h)
        print(f"\n  Hand {i+1} (cid={cid}): {hand_cards}  trip={RANK_CHAR[trip_rank]} pair={RANK_CHAR[pair_rank]}  regret=${regret*10*1000:>+8.1f}/1000h")
        print(f"    v39 (Pbot_SS):    top={card_str(v39_top)}  "
              f"mid={card_str(v39_mid[0])} {card_str(v39_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in v39_bot)}")
        print(f"    oracle (Pbot_DS): top={card_str(oracle_top)}  "
              f"mid={card_str(oracle_mid[0])} {card_str(oracle_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in oracle_bot)}")

    # Aggregate signals
    print(f"\n── AGGREGATE STRUCTURAL FEATURES (all {n_match:,} mismatch hands) ──")
    pair_same_suit = 0
    pair_2distinct = 0
    sing_match_pair_suits = []
    trip_match_pair_suits = []
    routes_R1 = 0  # bot=pair+2 sings, sings in pair-suits (single-counted)
    routes_R2 = 0  # bot=pair+1 trip+1 sing, suit-aligned for DS
    routes_R3 = 0  # bot=pair+2 trip cards, suit-aligned for DS
    routes_R4 = 0  # pair_same_suit: bot=pair+2 cards of single other suit
    n_with_any_route = 0

    def is_ds_4cards(suits):
        c = Counter(suits)
        sv = sorted(c.values(), reverse=True)
        return sv[:2] == [2, 2]

    for regret, cid, h, v39_idx, oracle_idx, trip_rank, pair_rank in target_hands:
        ranks = (h // 4) + 2
        suits = h & 3
        pair_pos = [j for j in range(7) if int(ranks[j]) == pair_rank]
        trip_pos = [j for j in range(7) if int(ranks[j]) == trip_rank]
        sing_pos = [j for j in range(7) if int(ranks[j]) != pair_rank and int(ranks[j]) != trip_rank]
        pair_suits = [int(suits[p]) for p in pair_pos]

        if len(set(pair_suits)) == 1:
            pair_same_suit += 1
        else:
            pair_2distinct += 1

        sing_in_pair_suits = sum(1 for s in sing_pos if int(suits[s]) in pair_suits)
        trip_in_pair_suits = sum(1 for t in trip_pos if int(suits[t]) in pair_suits)
        sing_match_pair_suits.append(sing_in_pair_suits)
        trip_match_pair_suits.append(trip_in_pair_suits)

        any_route = False
        # R1: bot = pair + 2 sings
        for sa, sb in combinations(sing_pos, 2):
            bot_suits = pair_suits + [int(suits[sa]), int(suits[sb])]
            if is_ds_4cards(bot_suits):
                routes_R1 += 1
                any_route = True
                break
        # R2: bot = pair + 1 trip + 1 sing
        for tp in trip_pos:
            for sp in sing_pos:
                bot_suits = pair_suits + [int(suits[tp]), int(suits[sp])]
                if is_ds_4cards(bot_suits):
                    routes_R2 += 1
                    any_route = True
                    break
            else:
                continue
            break
        # R3: bot = pair + 2 trip cards
        for ta, tb in combinations(trip_pos, 2):
            bot_suits = pair_suits + [int(suits[ta]), int(suits[tb])]
            if is_ds_4cards(bot_suits):
                routes_R3 += 1
                any_route = True
                break
        if any_route:
            n_with_any_route += 1

    print(f"  Pair has same-suit: {pair_same_suit:,} ({100*pair_same_suit/n_match:.1f}%)")
    print(f"  Pair has 2 distinct suits: {pair_2distinct:,} ({100*pair_2distinct/n_match:.1f}%)")
    print()
    print(f"  Pbot_DS routes available (Pmid_DS / Psplit_DS not counted here):")
    print(f"    R1 (pair + 2 sings filling pair-suits): {routes_R1:,} ({100*routes_R1/n_match:.1f}%)")
    print(f"    R2 (pair + 1 trip + 1 sing):             {routes_R2:,} ({100*routes_R2/n_match:.1f}%)")
    print(f"    R3 (pair + 2 trip cards):                {routes_R3:,} ({100*routes_R3/n_match:.1f}%)")
    print(f"    Any route available:                     {n_with_any_route:,} ({100*n_with_any_route/n_match:.1f}%)")
    print()
    print(f"  Distribution of '# singletons in a pair-suit':")
    cnt = Counter(sing_match_pair_suits)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    {k}: {v:>6,} ({100*v/n_match:.1f}%)")
    print(f"  Distribution of '# trip cards in a pair-suit':")
    cnt = Counter(trip_match_pair_suits)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    {k}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
