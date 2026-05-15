"""
v58 candidate — v57 + Rule 21 (LOW pair × PMID_DS_MAXTOP × top_alt_rank ≥ gate
                                → force PMID_tmax_DS).

Per Session 84 Phase B/B+ findings:

  Cell: LOW pair (rank 2-7) × PMID_DS_MAXTOP, n=128,304 hands.

  Under PRODUCTION v57:
    - 81.3% MATCH (v57 picks tmax_DS, oracle agrees)
    - 4.5%  KEEP_TNOMAX (v57 picks tnomax_DS, oracle agrees)
    - 3.6%  SWAP_TO_TMAX  (v57 picks tnomax_DS, oracle wants tmax_DS) — $2.42 leak
    - 5.2%  SWAP_TO_TNOMAX (v57 picks tmax_DS, oracle wants tnomax_DS) — $2.06 leak
    - 5.5%  OTHER

  Top discriminator for the SWAP_TO_TMAX direction: `top_alt_rank` (rank of
  leftover singleton in the best tnomax_DS config, i.e., the "alternative
  top" if v57 had taken tnomax_DS instead). When top_alt_rank is HIGH (the
  alternative top is itself strong), oracle prefers tmax_DS (= max on top,
  DS bot without max). When top_alt_rank is LOW (alternative top is weak),
  oracle prefers tnomax_DS (max in bot, weak singleton on top).

  Per-value (within SWAP_TO_TMAX ∪ KEEP_TNOMAX populations):
    top_alt = 2: swap-right 23.9%
    top_alt = 3: 33.1%
    top_alt = 4: 44.1%
    top_alt = 5: 56.2%
    top_alt = 6: 64.8%
    top_alt = 7: 66.5%
    top_alt = 8: 62.9%
    top_alt = 9: 67.2%

  Rule: when (LOW pair) AND (cell = PMID_DS_MAXTOP) AND (top_alt_rank ≥ gate),
  force PMID_tmax_DS (max on top, pair in mid, best DS bot excluding max).

  IMPORTANT: The discriminator is weaker than S83's max_sing (peak 67%
  vs S83's 90%+). The cell-leak ceiling is ~$4.5/1000h whole-grid. This
  rule is graded with pre-committed thresholds; NULL is the expected
  outcome unless a sharp gate emerges.

GATE OPTIONS
------------
  gate=2:  always-fire (any top_alt_rank ≥ 2, i.e., the entire cell)
  gate=5,6,7,8,9:  progressively more selective

Routes through v57 (which routes through v56) if any precondition fails.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Optional, Callable

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}


def _detect_lo_pair_ds_maxtop_force_tmax(
    hand: np.ndarray,
    top_alt_rank_gate: int,
) -> Optional[int]:
    """Return the PMID_tmax_DS setting index for hands matching the trigger,
    else None.

    Trigger conditions (all must be true):
      1. Hand is exactly a single pair (no quads, no trips, no other pairs).
      2. pair_rank ∈ LOW_PAIR_RANKS (2-7).
      3. Cell is PMID_DS_MAXTOP, i.e.:
         - n_PBOT_DS == 0   (no pair-to-bot DS achievable)
         - n_PMID_DS_w_maxtop > 0  (at least one DS config has max on top)
      4. top_alt_rank ≥ top_alt_rank_gate. top_alt_rank is the rank of the
         leftover singleton in the BEST tnomax_DS config (= the singleton
         we'd put on top if we took max-in-bot). If no tnomax_DS config
         exists (n_PMID_DS_w_maxtop is the only DS option), top_alt_rank
         is undefined and the rule does NOT fire (no ambiguity exists).

    If triggered, returns the setting index for:
      mid = pair_pos
      bot = the 4-singleton subset forming the best DS config WHERE max is
            in top (= excluded from bot)
      top = max_sing
    """
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks.astype(int), minlength=15)
    if int((rc == 4).sum()) != 0: return None
    if int((rc == 3).sum()) != 0: return None
    if int((rc == 2).sum()) != 1: return None  # exactly one pair

    pair_rank = int(np.where(rc == 2)[0][0])
    if pair_rank not in LOW_PAIR_RANKS:
        return None

    pair_pos = [int(i) for i in range(7) if int(ranks[i]) == pair_rank]
    sing_pos = [int(i) for i in range(7) if int(ranks[i]) != pair_rank]
    assert len(pair_pos) == 2 and len(sing_pos) == 5

    sing_ranks = [int(ranks[p]) for p in sing_pos]
    sing_suits = [int(suits[p]) for p in sing_pos]
    pair_suits = (int(suits[pair_pos[0]]), int(suits[pair_pos[1]]))
    sa, sb = pair_suits

    # --- Check: PBOT_DS not achievable (cell precondition 1) ---
    pbot_ds_achievable = False
    for k_a in [k for k, s in enumerate(sing_suits) if s == sa]:
        for k_b in [k for k, s in enumerate(sing_suits) if s == sb]:
            if k_a != k_b:
                pbot_ds_achievable = True
                break
        if pbot_ds_achievable:
            break
    if pbot_ds_achievable:
        return None

    # --- Enumerate PMID DS configs, split by tmax vs tnomax ---
    max_sing_rank = max(sing_ranks)
    max_sing_local = sing_ranks.index(max_sing_rank)

    best_tmax_config = None    # (bot_pair_high, top_local, bot_locals_tuple)
    best_tnomax_config = None  # (bot_pair_high, top_local, bot_locals_tuple)

    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        by_suit = defaultdict(list)
        for k in bot_locals:
            by_suit[sing_suits[k]].append(sing_ranks[k])
        local_pair_high = 0
        for sgrp, rs in by_suit.items():
            if len(rs) >= 2:
                hi = max(rs)
                if hi > local_pair_high:
                    local_pair_high = hi
        if top_local == max_sing_local:
            if best_tmax_config is None or local_pair_high > best_tmax_config[0]:
                best_tmax_config = (local_pair_high, top_local, tuple(bot_locals))
        else:
            if best_tnomax_config is None or local_pair_high > best_tnomax_config[0]:
                best_tnomax_config = (local_pair_high, top_local, tuple(bot_locals))

    # --- Cell precondition: n_PMID_DS_w_maxtop > 0 ---
    if best_tmax_config is None:
        return None  # cell is NOT PMID_DS_MAXTOP

    # --- Gate: need a tnomax_DS to have a "top_alt" to compare to ---
    # If best_tnomax_config is None, there's no swap-back risk, but also
    # no ambiguity for v57 to misroute → rule still has no incremental signal.
    # Conservative choice: do not fire if tnomax_DS not achievable.
    if best_tnomax_config is None:
        return None

    # top_alt_rank = rank of the leftover singleton in best_tnomax_config
    top_alt_local = best_tnomax_config[1]
    top_alt_rank = sing_ranks[top_alt_local]
    if top_alt_rank < top_alt_rank_gate:
        return None

    # All preconditions met. Build PMID_tmax_DS setting:
    #   top = max_sing
    #   mid = pair (both cards)
    #   bot = best_tmax_config's bot_locals
    _, top_local, bot_locals_tuple = best_tmax_config
    top_pos = sing_pos[top_local]
    return int(_setting_index_from_tmb(top_pos, pair_pos[0], pair_pos[1]))


def make_strategy_v58(top_alt_rank_gate: int) -> Callable:
    """Build a v58 strategy with the given top_alt_rank gate.

    top_alt_rank_gate options (per S84 Phase B+):
      2  — always-fire (every cell hand with a tnomax_DS alternative)
      5  — ~56% swap-right
      6  — ~65% swap-right
      7  — ~66% swap-right
      8  — ~63% swap-right
      9  — ~67% swap-right (smallest population)
    """
    def strategy_v58_lo_pair_ds_maxtop(hand: np.ndarray) -> int:
        forced = _detect_lo_pair_ds_maxtop_force_tmax(hand, top_alt_rank_gate)
        if forced is not None:
            return int(forced)
        return int(strategy_v57_lo_pair_defensive(hand))
    strategy_v58_lo_pair_ds_maxtop.__name__ = (
        f"strategy_v58_lo_pair_ds_maxtop_gate{top_alt_rank_gate}"
    )
    return strategy_v58_lo_pair_ds_maxtop


# Default export: top_alt_rank_gate=7 (best swap-right rate on a non-trivial
# population per Phase B+). Multi-gate grading via grader script.
strategy_v58_lo_pair_ds_maxtop = make_strategy_v58(top_alt_rank_gate=7)


if __name__ == "__main__":
    # Sanity tests
    from tw_analysis.settings import parse_hand
    from strategy_v57_lo_pair_defensive import strategy_v57_lo_pair_defensive

    # Construct a LOW × PMID_DS_MAXTOP hand:
    # pair 5c 5d (suits c,d). Singletons need 2+2 DS pattern with max on top.
    # Try: 5c 5d Kh 9h 8s 7s 2c (max=K=h; singletons h,h,s,s,c → 2h+2s+1c).
    # 4 singletons excluding max (K): 9h 8s 7s 2c → suits h,s,s,c (1+2+1 = 31). NOT DS.
    # Try: pair 5c 5d, singletons: Kh Th 7s 4s 9c. excl K: Th 7s 4s 9c → h,s,s,c = 1+2+1. Not DS.
    # Try: pair 5c 5d, singletons: Kh Th 7s 4s 9h. K=max. excl K: Th 7s 4s 9h → h,s,s,h = 2h+2s = DS! ✓
    # And n_PBOT_DS = 0 (need a singleton of suit c AND of suit d, but singletons are h,h,s,s,h).
    # n_PMID_DS_w_maxtop > 0: yes (above).
    # Tnomax DS configs: any top_local != max_local where the other 4 form 2+2?
    # singletons: Kh(max) Th 7s 4s 9h. Try top=Th (local 1): bot=K,7,4,9 → h,s,s,h = DS! ✓
    #   top_alt_rank = 10 (T)
    # Try top=7s: bot = K,T,4,9 → h,h,s,h = 3+1. Not DS.
    # Try top=4s: bot = K,T,7,9 → h,h,s,h = 3+1. Not DS.
    # Try top=9h: bot = K,T,7,4 → h,h,s,s = DS. top_alt_rank=9.
    # Best tnomax_DS: bot_pair_high = max of {K from top=T config, K from top=9 config}.
    # Both top=T (top_alt=10, bot pair_high=K=13) and top=9h (top_alt=9, pair_high=K).
    # Best is top=T (highest top_alt with same bot_pair_high). Actually we pick by bot_pair_high.
    # bot_pair_high for top=Th: bot is K(h), 7(s), 4(s), 9(h). Suits: h has [K,9]=K, s has [7,4]=7.
    # pair_high = max(K, 7) = K = 13.
    # bot_pair_high for top=9h: bot is K(h), T(h), 7(s), 4(s). h has [K,T]=K, s has [7,4]=7. pair_high=K=13.
    # Tie. Code picks first-seen (top=Th if iterated lower-first).

    test_cases = [
        # LOW pair 5, max=K, top_alt=T (>=gate 9, 8, 7) → should fire
        ("5c 5d Kh Th 7s 4s 9h", 7, True, "low pair 5, K-max, top_alt=T → fire at gate 7"),
        # Same hand, gate=12 (very strict) → should NOT fire
        ("5c 5d Kh Th 7s 4s 9h", 12, False, "low pair 5, top_alt=T < gate 12 → no fire"),
        # HIGH pair (Jc Jd) → should NEVER fire (not LOW)
        ("Jc Jd Kh Th 7s 4s 9h", 2, False, "J-pair — not LOW"),
        # No pair → should NEVER fire
        ("Ac Kh Qd Jc Ts 9h 2d", 2, False, "high_only — not pair"),
    ]
    print("Sanity tests:")
    for s, gate, expect_fire, desc in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        forced = _detect_lo_pair_ds_maxtop_force_tmax(h, gate)
        fired = forced is not None
        ok = (fired == expect_fire)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        strat = make_strategy_v58(gate)
        v58_pick = int(strat(h))
        print(f"  [{'OK' if ok else 'FAIL'}] {desc}: gate={gate} "
              f"fired={fired} (expected {expect_fire})  "
              f"v57_pick={v57_pick} v58_pick={v58_pick}")
