"""
Session 55 — Drill T2P2: two_pair hand-level mismatch inspection.

Drill T2P (aggregate) showed top mismatch: v39 picks Hbot_Lmid_SS,
oracle picks Hmid_Lbot_SS — 56,206 hands at $2,655 mean regret = $24.84
/1000h whole-grid contribution. This is an "anchor swap" — both layouts
have SS bot, but oracle prefers low-pair on bot.

Second largest is Hbot_Lmid_SS → Hbot_Lmid_DS — $12.77 whole-grid, same
anchor but suit-upgrade.

This drill extracts SAMPLE hands from the top mismatch class and
characterizes the structural delta. Goal: identify what signal
distinguishes "high-pair on bot SS is right" from "low-pair on bot SS
is right" (or DS upgrade).

Aggregate signals across ALL matched hands:
  - Pair suit overlap (do high and low pair share a suit?)
  - Singleton suit distribution: how do sings align with each pair's suits?
  - Layout B (Hmid_Lbot) DS-routing count
  - Layout C (Hbot_Lmid) DS-routing count
  - Best top rank in Layout B vs Layout C
  - High-pair rank gap (gap between high-pair and middle singleton, etc.)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_v39_mismatch_handlevel.py
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


def is_layout(hand_bytes, idx, hi_pair, lo_pair, hi_state_want, lo_state_want):
    """Return True if setting `idx` matches the desired anchor configuration."""
    pos = SETTING_HAND_INDICES[idx]
    mid_pos = pos[1:3]
    bot_pos = pos[3:7]
    ranks = (hand_bytes // 4) + 2
    h_mid = int((ranks[mid_pos] == hi_pair).sum())
    h_bot = int((ranks[bot_pos] == hi_pair).sum())
    l_mid = int((ranks[mid_pos] == lo_pair).sum())
    l_bot = int((ranks[bot_pos] == lo_pair).sum())
    if hi_state_want == "mid" and h_mid != 2: return False
    if hi_state_want == "bot" and h_bot != 2: return False
    if lo_state_want == "mid" and l_mid != 2: return False
    if lo_state_want == "bot" and l_bot != 2: return False
    return True


def main() -> int:
    print("=" * 88)
    print("Session 55 Drill T2P2: Two_pair hand-level mismatch inspection")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    t2p_idx = np.where(cats == 2)[0]
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print(f"  two_pair n={len(t2p_idx):,}")

    print("\n[2/3] sweeping for v39=Hbot_Lmid_SS oracle=Hmid_Lbot_SS mismatches ...",
          flush=True)
    target_hands = []
    n_processed = 0
    n_match = 0
    t0 = time.time()
    # Cap at 500K for speed; we have enough hands to find statistics
    sample_limit = 500_000
    for cid in t2p_idx[:sample_limit]:
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        pair_ranks = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        hi_pair, lo_pair = pair_ranks[0], pair_ranks[1]
        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v39_idx = int(strategy_v39_dt(h))

        # v39 = Hbot_Lmid_SS, oracle = Hmid_Lbot_SS
        v39_layout_C = is_layout(h, v39_idx, hi_pair, lo_pair, "bot", "mid")
        v39_SS = int(feats.bot_suit_profile[v39_idx]) == int(SUIT_PROFILE_SS)
        oracle_layout_B = is_layout(h, oracle_idx, hi_pair, lo_pair, "mid", "bot")
        oracle_SS = int(feats.bot_suit_profile[oracle_idx]) == int(SUIT_PROFILE_SS)
        if not (v39_layout_C and v39_SS and oracle_layout_B and oracle_SS):
            n_processed += 1
            continue

        regret = float(rowf[oracle_idx]) - float(rowf[v39_idx])
        target_hands.append((regret, cid, h.copy(), v39_idx, oracle_idx,
                              hi_pair, lo_pair))
        n_match += 1
        n_processed += 1

    print(f"  done in {time.time()-t0:.1f}s; n_processed={n_processed:,}, n_match={n_match:,}")

    target_hands.sort(key=lambda x: -x[0])
    sample_indices = list(range(0, min(20, len(target_hands))))

    print(f"\n[3/3] inspecting top {len(sample_indices)} hands by regret ...\n")
    print("=" * 110)
    print("HAND-LEVEL INSPECTION: v39 picks Hbot_Lmid_SS, oracle picks Hmid_Lbot_SS")
    print("=" * 110)

    for i in sample_indices:
        regret, cid, h, v39_idx, oracle_idx, hi_pair, lo_pair = target_hands[i]
        v39_pos = setting_to_pos(v39_idx)
        oracle_pos = setting_to_pos(oracle_idx)
        v39_top = h[v39_pos[0]]
        v39_mid = (h[v39_pos[1]], h[v39_pos[2]])
        v39_bot = tuple(h[p] for p in v39_pos[3:])
        oracle_top = h[oracle_pos[0]]
        oracle_mid = (h[oracle_pos[1]], h[oracle_pos[2]])
        oracle_bot = tuple(h[p] for p in oracle_pos[3:])
        hand_cards = " ".join(card_str(c) for c in h)
        print(f"\n  Hand {i+1} (cid={cid}): {hand_cards}  hi={RANK_CHAR[hi_pair]} lo={RANK_CHAR[lo_pair]}  regret=${regret*10*1000:>+8.1f}/1000h")
        print(f"    v39 (Hbot_Lmid_SS):   top={card_str(v39_top)}  "
              f"mid={card_str(v39_mid[0])} {card_str(v39_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in v39_bot)}")
        print(f"    oracle (Hmid_Lbot_SS): top={card_str(oracle_top)}  "
              f"mid={card_str(oracle_mid[0])} {card_str(oracle_mid[1])}  "
              f"bot={' '.join(card_str(c) for c in oracle_bot)}")

    # Aggregate signals
    print(f"\n── AGGREGATE STRUCTURAL FEATURES (all {n_match:,} mismatch hands) ──")

    # For each hand compute:
    #   - hi_pair_suits and lo_pair_suits
    #   - n_sings_in_hi_pair_suits, n_sings_in_lo_pair_suits
    #   - Layout B (Hmid_Lbot): bot = LL + 2 sings; how many of C(3,2)=3 sing-pair
    #     choices yield SS bot? DS bot?
    #   - Layout C (Hbot_Lmid): bot = HH + 2 sings; how many of C(3,2) sing-pair
    #     choices yield SS bot? DS bot?
    layout_B_SS_count = []
    layout_B_DS_count = []
    layout_C_SS_count = []
    layout_C_DS_count = []
    layout_B_best_top = []
    layout_C_best_top = []
    pair_suit_overlap = []
    sing_match_hi_count = []
    sing_match_lo_count = []

    def bot_profile(suits):
        c = Counter(suits)
        sv = sorted(c.values(), reverse=True)
        if sv[:2] == [2, 2]:
            return "DS"
        elif sv[0] == 2 and sv[1] == 1:
            return "SS"
        elif sv[0] == 1:
            return "rainbow"
        elif sv[0] == 3:
            return "3+1"
        elif sv[0] == 4:
            return "4-flush"
        return "?"

    for regret, cid, h, v39_idx, oracle_idx, hi_pair, lo_pair in target_hands:
        ranks = (h // 4) + 2
        suits = h & 3
        hi_pos = [j for j in range(7) if int(ranks[j]) == hi_pair]
        lo_pos = [j for j in range(7) if int(ranks[j]) == lo_pair]
        sing_pos = [j for j in range(7) if j not in hi_pos and j not in lo_pos]
        hi_suits = [int(suits[p]) for p in hi_pos]
        lo_suits = [int(suits[p]) for p in lo_pos]
        sing_suits = [int(suits[p]) for p in sing_pos]
        sing_ranks = [int(ranks[p]) for p in sing_pos]

        overlap = len(set(hi_suits) & set(lo_suits))
        pair_suit_overlap.append(overlap)
        n_sing_hi = sum(1 for s in sing_suits if s in set(hi_suits))
        n_sing_lo = sum(1 for s in sing_suits if s in set(lo_suits))
        sing_match_hi_count.append(n_sing_hi)
        sing_match_lo_count.append(n_sing_lo)

        # Layout B: bot = LL + 2 sings (3 choices of 2 sings)
        lb_ss = 0; lb_ds = 0; lb_best_top = 0
        for sa_i, sb_i in combinations(range(3), 2):
            bot_s = lo_suits + [sing_suits[sa_i], sing_suits[sb_i]]
            prof = bot_profile(bot_s)
            if prof == "SS": lb_ss += 1
            if prof == "DS": lb_ds += 1
            # Top = the leftover singleton
            leftover_idx = [j for j in range(3) if j != sa_i and j != sb_i][0]
            if prof in ("SS", "DS") and sing_ranks[leftover_idx] > lb_best_top:
                lb_best_top = sing_ranks[leftover_idx]
        layout_B_SS_count.append(lb_ss)
        layout_B_DS_count.append(lb_ds)
        layout_B_best_top.append(lb_best_top)

        # Layout C: bot = HH + 2 sings
        lc_ss = 0; lc_ds = 0; lc_best_top = 0
        for sa_i, sb_i in combinations(range(3), 2):
            bot_s = hi_suits + [sing_suits[sa_i], sing_suits[sb_i]]
            prof = bot_profile(bot_s)
            if prof == "SS": lc_ss += 1
            if prof == "DS": lc_ds += 1
            leftover_idx = [j for j in range(3) if j != sa_i and j != sb_i][0]
            if prof in ("SS", "DS") and sing_ranks[leftover_idx] > lc_best_top:
                lc_best_top = sing_ranks[leftover_idx]
        layout_C_SS_count.append(lc_ss)
        layout_C_DS_count.append(lc_ds)
        layout_C_best_top.append(lc_best_top)

    print(f"  Pair-suit overlap (high & low pair share a suit):")
    cnt = Counter(pair_suit_overlap)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    overlap={k}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\n  Singletons matching hi-pair suits (count distribution):")
    cnt = Counter(sing_match_hi_count)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    n_sing_in_hi={k}: {v:>6,} ({100*v/n_match:.1f}%)")
    print(f"\n  Singletons matching lo-pair suits (count distribution):")
    cnt = Counter(sing_match_lo_count)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    n_sing_in_lo={k}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\n  Layout B (Hmid_Lbot, bot=LL+2 sings): suit profile dist of bot options")
    print(f"    n_SS_routings: ", Counter(layout_B_SS_count))
    print(f"    n_DS_routings: ", Counter(layout_B_DS_count))
    print(f"  Layout C (Hbot_Lmid, bot=HH+2 sings): suit profile dist of bot options")
    print(f"    n_SS_routings: ", Counter(layout_C_SS_count))
    print(f"    n_DS_routings: ", Counter(layout_C_DS_count))

    print(f"\n  Layout B best top rank (across SS/DS routings):")
    cnt = Counter(layout_B_best_top)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    top_rank={RANK_CHAR.get(k, k):<2}: {v:>6,} ({100*v/n_match:.1f}%)")
    print(f"\n  Layout C best top rank (across SS/DS routings):")
    cnt = Counter(layout_C_best_top)
    for k in sorted(cnt.keys()):
        v = cnt[k]
        print(f"    top_rank={RANK_CHAR.get(k, k):<2}: {v:>6,} ({100*v/n_match:.1f}%)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
