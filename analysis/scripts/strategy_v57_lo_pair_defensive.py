"""
v57 — v56 + Rule 29 (LOW pair defensive PMID_tnomax_DS swap).

Per Session 83 Phase B/B+ findings:

  Cell: LOW pair (rank 2-7) × PMID_DS_NOMAXTOP.
  v56 (= v52 for this cell) leaks $59.42/1000h whole-grid here, dominantly by
  picking PMID_tmax_SS (max kicker on top, single-suited bot) when oracle
  prefers PMID_tnomax_DS (drop max into bot, take a non-max singleton on top,
  use the DS bot).

  The discriminator is `max_sing` (the rank of the largest non-pair card):
    max_sing ≤ J → swap is right 89-93% of the time
    max_sing = Q → swap is right 77% of the time
    max_sing = K → swap is right 54% of the time
    max_sing = A → swap is WRONG 86% of the time (A-on-top is correct)

The rule: when (pair rank 2-7) AND (cell is PMID_DS_NOMAXTOP) AND
(max_sing ≤ GATE), force the setting where:
  - Both pair cards in mid
  - Bot is the 4-singleton subset forming the best DS pattern (must
    include max_sing per cell definition)
  - Top is the leftover singleton (which is NOT max_sing)

GATE is parameterized: build the strategy with a chosen max_sing cutoff,
grade at multiple gates to pick the winner.

Routes through v56 if any precondition fails.
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

from strategy_v56_trips_hybrid import strategy_v56_trips_hybrid  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}


def _detect_lo_pair_defensive_pmid_swap(
    hand: np.ndarray,
    max_sing_gate: int,
) -> Optional[int]:
    """Return the PMID_tnomax_DS setting index for hands matching the trigger,
    else None.

    Trigger conditions (all must be true):
      1. Hand is exactly a single pair (no quads, no trips, no other pairs).
      2. pair_rank is in LOW_PAIR_RANKS (2-7).
      3. max_sing (max non-pair card rank) <= max_sing_gate.
      4. Cell is PMID_DS_NOMAXTOP, i.e.:
         - n_PBOT_DS == 0 (no pair-to-bot DS achievable)
         - n_PMID_DS > 0 (at least one PMID DS config exists)
         - n_PMID_DS_w_maxtop == 0 (no DS config with max on top)

    If triggered, returns the setting index for:
      mid = pair_pos
      bot = 4 singletons forming the best DS pattern (includes max_sing
            since cell = PMID_DS_NOMAXTOP)
      top = leftover singleton

    The "best" DS config is the one whose bot_pair_high (max-of-suited-
    pair-tops in bot) is highest; ties broken by stable enumeration order.
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

    max_sing_rank = max(sing_ranks)
    if max_sing_rank > max_sing_gate:
        return None

    # --- Check: PBOT_DS not achievable (cell precondition 1) ---
    # PBOT_DS = bot contains pair (suits sa,sb) + 1 sing of suit sa + 1 of sb.
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

    # --- Check: PMID_DS achievable (cell precondition 2) AND
    #             no PMID_DS_w_maxtop (cell precondition 3) ---
    # Enumerate 4-subsets of 5 singletons → which form 2+2 suit pattern?
    # For each, track:
    #   - is_DS: yes/no
    #   - leftover (top) singleton index in sing_pos
    #   - bot_pair_high (max-of-pair-suit-tops in the 4 bot singletons)
    best_ds_config = None  # (bot_pair_high, top_local, bot_locals_tuple)
    any_ds_with_maxtop = False
    max_sing_local = sing_ranks.index(max_sing_rank)

    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        # This is a DS config.
        if top_local == max_sing_local:
            any_ds_with_maxtop = True
            continue  # skip — cell is NOMAXTOP, so this isn't our target config
        # Compute bot_pair_high
        by_suit = defaultdict(list)
        for k in bot_locals:
            by_suit[sing_suits[k]].append(sing_ranks[k])
        local_pair_high = 0
        for sgrp, rs in by_suit.items():
            if len(rs) >= 2:
                hi = max(rs)
                if hi > local_pair_high:
                    local_pair_high = hi
        if (best_ds_config is None
                or local_pair_high > best_ds_config[0]):
            best_ds_config = (local_pair_high, top_local, tuple(bot_locals))

    if any_ds_with_maxtop:
        return None  # cell is PMID_DS_MAXTOP, not our target cell
    if best_ds_config is None:
        return None  # no DS achievable → cell is PMID_SS_MAXTOP or PMID_OTHER

    # All preconditions met. Build setting.
    _, top_local, bot_locals_tuple = best_ds_config
    top_pos = sing_pos[top_local]
    return int(_setting_index_from_tmb(top_pos, pair_pos[0], pair_pos[1]))


def make_strategy_v57(max_sing_gate: int) -> Callable:
    """Build a v57 strategy with the given max_sing gate.

    max_sing_gate options (per S83 Phase B+):
      11 (J)  — conservative; ~5k fires, swap-right ~90%
      12 (Q)  — balanced;     ~35k fires, swap-right ~79%
      13 (K)  — aggressive;   ~86k fires, swap-right ~64%
    """
    def strategy_v57_lo_pair_defensive(hand: np.ndarray) -> int:
        forced = _detect_lo_pair_defensive_pmid_swap(hand, max_sing_gate)
        if forced is not None:
            return int(forced)
        return int(strategy_v56_trips_hybrid(hand))
    strategy_v57_lo_pair_defensive.__name__ = (
        f"strategy_v57_lo_pair_def_gate{max_sing_gate}"
    )
    return strategy_v57_lo_pair_defensive


# Default export uses Q gate (the back-of-envelope sweet spot from
# Phase B+ analysis). Multi-gate grading happens via the grader script.
strategy_v57_lo_pair_defensive = make_strategy_v57(max_sing_gate=12)


if __name__ == "__main__":
    # Sanity tests — known LOW × PMID_DS_NOMAXTOP hands should fire under
    # gate ≥ J; out-of-cell or A-max hands should NOT fire.
    from tw_analysis.settings import parse_hand

    test_cases = [
        # LOW pair 3, max_sing=Q (12) → should fire under Q+ gate
        ("3c 3d Qh 9s 8d 5c 4h", 12, True, "low pair 3, max=Q"),
        # LOW pair 5, max_sing=A (14) → should NOT fire under Q gate
        ("5c 5d Ah Th 8d 4c 2s", 12, False, "low pair 5, max=A — A above gate"),
        # HIGH pair (J) → should NEVER fire (not LOW)
        ("Jc Jd Qh 9s 8d 5c 4h", 13, False, "J-pair — not LOW"),
        # No pair → should NEVER fire
        ("Ac Kh Qd Jc Ts 9h 2d", 13, False, "high_only — not pair"),
    ]
    print("Sanity tests:")
    for s, gate, expect_fire, desc in test_cases:
        strat = make_strategy_v57(gate)
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        forced = _detect_lo_pair_defensive_pmid_swap(h, gate)
        fired = forced is not None
        ok = (fired == expect_fire)
        v56_pick = int(strategy_v56_trips_hybrid(h))
        v57_pick = int(strat(h))
        print(f"  [{'OK' if ok else 'FAIL'}] {desc}: gate={gate} "
              f"fired={fired} (expected {expect_fire})  "
              f"v56_pick={v56_pick} v57_pick={v57_pick}")
