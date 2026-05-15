"""
v60 candidate — v57 + Rule 21 (MID pair × PMID_DS_NOMAXTOP × max_sing ≤ gate ×
v57-picks-PMID_tmax-style → force best PMID_tnomax_DS).

CONTEXT (S86)
-------------
Direct extension of Rule 20 (S83 SHIP) to the next pair-rank tier.

Rule 20 fires on LOW pair (rank 2-7) × PMID_DS_NOMAXTOP × max_sing ≤ Q,
forcing the best PMID_tnomax_DS configuration. v60's Rule 21 fires on MID
pair (rank 8-10) × the same cell × max_sing ≤ gate, with the SAME forced
output (best tnomax_DS with mid = pair, top = best non-max singleton, bot
= 4 singletons forming DS pattern incl. max).

PHASE B/B+ FINDINGS (S86)
-------------------------
  Cell: MID × PMID_DS_NOMAXTOP, n=114,048 hands.
  v57 cell leak: $31.17/1000h whole-grid.
  Direction-residual (SWAP_TO_TNOMAX_DS): $22.98/1000h — clears SHIP by 4.6×.

  max_sing discriminator (within KEEP_TMAX ∪ SWAP_TO_TNOMAX_DS, all MID ranks):
    max_sing ≤ 9   → 84.3% swap-right (small population)
    max_sing ≤ 10  → ~78% swap-right
    max_sing ≤ 11  → ~75% swap-right
    max_sing ≤ 12  → ~65% swap-right
    max_sing ≤ 13  → ~51% swap-right (50/50)
    max_sing = 14  → 17.2% swap-right (rule should NOT fire)

  Per-rank softening with pair_rank:
    rank 8: max_sing=J → 83.8% (S83-like)
    rank 9: max_sing=J → 75.1%
    rank T: max_sing=J → 65.3% (softer)

S85 DESIGN PATTERN APPLIED
--------------------------
v57-pick restriction: only fire when v57's current pick is PMID_tmax-style
(top = max_sing, mid = pair). This excludes the 3.5% NOT_TMAX subset where
v57 already chose a tnomax variant. By S85 lesson, "don't override v57
when v57 is already in a non-tmax pick."

GATE OPTIONS
------------
Grade gates ∈ {10, 11, 12, 13, 14} via grader.

  gate=10 — fires on max_sing ≤ T; population ~3,290 cell hands; swap-right ~80%+
  gate=11 — fires on max_sing ≤ J; population ~13,930 cell hands; swap-right ~75%
  gate=12 — fires on max_sing ≤ Q; population ~33,930 cell hands; swap-right ~65%
  gate=13 — fires on max_sing ≤ K; population ~74,490 cell hands; swap-right ~51%
  gate=14 — fires on all; ~155,290 — but A skews to keep so rule turns negative

Routes through v57 (v56 + Rule 20) if any precondition fails.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
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
from tw_analysis.query import SETTING_HAND_INDICES  # noqa: E402

MID_PAIR_RANKS = {8, 9, 10}


def _v57_picked_pmid_tmax_style(
    hand: np.ndarray,
    v57_pick: int,
    pair_pos: list,
    max_sing_pos: int,
) -> bool:
    """Check if v57's chosen setting is "PMID_tmax-style" — i.e. top =
    max_sing position AND mid = pair positions. Captures both PMID_tmax_SS
    and PMID_tmax_31 (bot suit pattern can be anything).
    """
    positions = SETTING_HAND_INDICES[v57_pick]
    top_pos = int(positions[0])
    mid_a, mid_b = int(positions[1]), int(positions[2])
    if top_pos != max_sing_pos:
        return False
    if {mid_a, mid_b} != set(pair_pos):
        return False
    return True


def _detect_mid_pair_defensive_pmid_swap(
    hand: np.ndarray,
    max_sing_gate: int,
    v57_pick: Optional[int] = None,
) -> Optional[int]:
    """Return the PMID_tnomax_DS setting index for hands matching the trigger,
    else None.

    Trigger conditions (all must be true):
      1. Hand is exactly a single pair (no quads, no trips, no other pairs).
      2. pair_rank ∈ MID_PAIR_RANKS = {8, 9, T}.
      3. max_sing (max non-pair card rank) ≤ max_sing_gate.
      4. Cell is PMID_DS_NOMAXTOP, i.e.:
         - n_PBOT_DS == 0
         - n_PMID_DS > 0
         - n_PMID_DS_w_maxtop == 0
      5. (v57-pick restriction, S85 pattern) v57's current pick is
         PMID_tmax-style: top = max_sing position AND mid = pair positions.

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
    if pair_rank not in MID_PAIR_RANKS:
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

    # --- Cell precondition 1: PBOT_DS NOT achievable ---
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

    # --- Cell preconditions 2 & 3: PMID_DS achievable, no PMID_DS_w_maxtop ---
    best_ds_config = None  # (bot_pair_high, top_local, bot_locals_tuple)
    any_ds_with_maxtop = False
    max_sing_local = sing_ranks.index(max_sing_rank)

    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        # DS config.
        if top_local == max_sing_local:
            any_ds_with_maxtop = True
            continue  # skip — cell is NOMAXTOP, so this isn't our target config
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

    # --- v57-pick restriction (S85 design pattern) ---
    max_sing_pos = sing_pos[max_sing_local]
    if v57_pick is None:
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
    if not _v57_picked_pmid_tmax_style(h, v57_pick, pair_pos, max_sing_pos):
        return None  # v57 didn't pick tmax — don't override

    # All preconditions met. Build setting.
    _, top_local, bot_locals_tuple = best_ds_config
    top_pos = sing_pos[top_local]
    return int(_setting_index_from_tmb(top_pos, pair_pos[0], pair_pos[1]))


def make_strategy_v60(max_sing_gate: int) -> Callable:
    """Build a v60 strategy with the given max_sing gate.

    max_sing_gate options (per S86 Phase B+):
      10 (T) — fires on ~3.3k cell hands; swap-right ~80%
      11 (J) — fires on ~13.9k cell hands; swap-right ~75%
      12 (Q) — fires on ~33.9k cell hands; swap-right ~65%
      13 (K) — fires on ~74.5k cell hands; swap-right ~51% (50/50)
      14 (A) — fires on entire cell; swap-right ~33% (rule wrong-biased)
    """
    def strategy_v60_mid_pair_ds_nomaxtop(hand: np.ndarray) -> int:
        forced = _detect_mid_pair_defensive_pmid_swap(hand, max_sing_gate)
        if forced is not None:
            return int(forced)
        return int(strategy_v57_lo_pair_defensive(hand))
    strategy_v60_mid_pair_ds_nomaxtop.__name__ = (
        f"strategy_v60_mid_pair_ds_nomaxtop_gate{max_sing_gate}"
    )
    return strategy_v60_mid_pair_ds_nomaxtop


# Default export: gate=11 (J — best expected swap-right ratio at a
# non-trivial population per Phase B+). Multi-gate grading via grader.
strategy_v60_mid_pair_ds_nomaxtop = make_strategy_v60(max_sing_gate=11)


if __name__ == "__main__":
    # Sanity tests
    from tw_analysis.settings import parse_hand
    from strategy_v57_lo_pair_defensive import strategy_v57_lo_pair_defensive

    test_cases = [
        # MID pair 8, max=J, PMID_DS_NOMAXTOP cell — should fire at gate ≥ 11
        # Hand: 8c 8d Jh 7h 6s 5s 4c
        # pair suits c,d; singletons J(h) 7(h) 6(s) 5(s) 4(c)
        # PBOT_DS: need sing of suit c AND d. Have c (4c) but no d → 0 ✓
        # PMID_DS: 4-subset 2+2? excl Jh: 7h 6s 5s 4c → h,s,s,c = 1+2+1 SS, not DS
        #   excl 7h: J 6 5 4 → h,s,s,c = SS, not DS
        #   excl 6s: J 7 5 4 → h,h,s,c = 2+1+1 SS, not DS
        #   excl 5s: J 7 6 4 → h,h,s,c = SS, not DS
        #   excl 4c: J 7 6 5 → h,h,s,s = 2+2 DS ✓!
        # So PMID_DS exists with top=4c. Max-sing is J(h). Is there PMID_DS w/maxtop?
        # If top=J, bot = 7h 6s 5s 4c = SS, not DS. So n_PMID_DS_w_maxtop=0. ✓
        # → Cell = PMID_DS_NOMAXTOP, max_sing=J → fires at gate ≥ 11.
        ("8c 8d Jh 7h 6s 5s 4c", 11, True, "MID pair 8, max=J, PMID_DS_NOMAXTOP"),
        # Same hand at gate=10 → max=J above → no fire
        ("8c 8d Jh 7h 6s 5s 4c", 10, False, "max=J above gate 10"),
        # LOW pair (3c 3d Jh ...) → not MID
        ("3c 3d Jh 7h 6s 5s 4c", 11, False, "low pair — not MID"),
        # HIGH pair (Jc Jd 8h ...) → not MID
        ("Jc Jd 8h 7h 6s 5s 4c", 13, False, "J-pair — not MID"),
        # No pair
        ("Ac Kh Qd Jc Ts 9h 2d", 13, False, "high_only — not pair"),
    ]
    print("Sanity tests:")
    for s, gate, expect_fire, desc in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        forced = _detect_mid_pair_defensive_pmid_swap(h, gate)
        fired = forced is not None
        ok = (fired == expect_fire)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        strat = make_strategy_v60(gate)
        v60_pick = int(strat(h))
        print(f"  [{'OK' if ok else 'FAIL'}] {desc}: gate={gate} "
              f"fired={fired} (expected {expect_fire})  "
              f"v57_pick={v57_pick} v60_pick={v60_pick}")
