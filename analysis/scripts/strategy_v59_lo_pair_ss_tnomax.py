"""
v59 candidate (v2 — restricted) — v57 + Rule 21 (LOW pair × PMID_SS_MAXTOP
× max_sing ≤ gate × v57-picks-PMID_tmax_SS → force PMID_tnomax with best
bot config).

v59_v1 (initial) fired on ALL cell hands at max_sing ≤ gate. Full-grid grader
auto-fired NULL across all gates (best lift was -$1.51 at gate=9, with 12%
swap-right). The rule was firing on:
  - OTHER hands (v57 already picks tnomax) — overriding v57's variant pick
    with my (possibly different) heuristic pick.
  - SWAP_TO_PBOT_SS hands (oracle wants PBOT) — forcing tnomax when oracle
    wants pair-in-bot. Pure harm.

v59_v2 restricts the rule to fire ONLY when v57 picks PMID_tmax_SS. This
restricts the affected population to {KEEP_PMID_TMAX, SWAP_TO_PBOT_SS,
SWAP_TO_PMID_TNOMAX}. The rule is right for SWAP_TO_PMID_TNOMAX, wrong
for the other two; ship depends on whether the gate concentrates the
correct population.

Per Session 85 Phase B/B+ findings:

  Cell: LOW pair (rank 2-7) × PMID_SS_MAXTOP, n=85,536 hands.

  Under PRODUCTION v57:
    - 54.1% KEEP_PMID_TMAX  (v57 picks PMID_tmax_SS, oracle agrees) — $0/1000h
    - 17.5% SWAP_TO_PBOT_SS (v57 picks PMID_tmax_SS, oracle wants PBOT_SS_*) — $6.98
    - 13.1% SWAP_TO_PMID_TNOMAX (v57 picks PMID_tmax_SS, oracle wants tnomax) — $4.36
    - 15.2% OTHER (v57 picks something other than PMID_tmax_SS) — $3.99
    Total cell residual: $15.33/1000h whole-grid.

  Top discriminator for SWAP_TO_PMID_TNOMAX direction: `max_sing`.
  Per-value swap-rate (within KEEP_PMID_TMAX ∪ SWAP_TO_PMID_TNOMAX):
    max_sing  KEEP   SWAP_TNOMAX   swap_pct
      14 (A)  26,482    757         2.8%  ← never swap on A
      13 (K)  13,580  4,104        23.2%
      12 (Q)   5,644  5,197        47.9%  ← inflection (50/50)
      11 (J)     331    664        66.7%
      10 (T)     146    323        68.9%
       9         70    135        65.9%
       8         27     47        63.5%

  At max_sing ≤ J (11), 67% of "v57 picks tmax_SS" hands prefer tnomax.
  At max_sing = Q (12), 50/50 — no signal.
  At max_sing ≥ K (13), tmax is correct.

  IMPORTANT: This discriminator is SOFT (peak ~67% vs S83's 92.8%). The
  cell's structural rotational margin is large ($15.33/1000h residual)
  but the discriminator only resolves ~5,800 of the cell's 85,536 hands
  with a profitable swap. Combined with PBOT-side-channel contamination
  (rule may incorrectly route PBOT-preferred hands to PMID_tnomax), the
  expected lift is small. Pre-committed thresholds in code; NULL is the
  default expectation unless a sharp gate emerges.

GATE OPTIONS
------------
  gate=14 — always-fire (every LOW × PMID_SS_MAXTOP hand)
  gate=13 — fires on max_sing ≤ K (excludes Aces)
  gate=12 — fires on max_sing ≤ Q (excludes Aces, Kings)
  gate=11 — fires on max_sing ≤ J (excludes Aces, Kings, Queens)
  gate=10 — fires on max_sing ≤ T
  gate=9  — fires on max_sing ≤ 9

Routes through v57 (which routes through v56) if any precondition fails.

DEFINITION OF "BEST tnomax"
---------------------------
Among all PMID configurations where top is a NON-max singleton:
  1. Compute bot_pair_high (rank of the higher-of-suited-pair-cards in bot).
     For SS bot: max of higher-of-each-2-suited-cards.
     For 31 bot: max of higher-of-the-3-suited-cards.
     For RB / 4f: 0 (no flush draw).
  2. Pick the config with highest bot_pair_high.
  3. Tiebreak by highest top-rank (= prefer stronger top among tnomax choices).
  4. Tiebreak by stable enumeration order.

If no PMID_tnomax config exists (n_PMID_DS_w_maxtop > 0 only — i.e., max
HAS to be on top), rule does not fire. But this is excluded by cell
precondition (n_PMID_DS == 0, so tnomax configs are NOT bound to DS-only).
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

LOW_PAIR_RANKS = {2, 3, 4, 5, 6, 7}


def _v57_picked_pmid_tmax_ss(
    hand: np.ndarray,
    v57_pick: int,
    pair_pos: list,
    max_sing_pos: int,
) -> bool:
    """Check if v57's chosen setting is PMID_tmax_SS for this hand.

    PMID_tmax_SS means:
      - top position == max_sing position
      - mid contains both pair cards
      - bot suits form 2+1+1 pattern (single-suited bot)
    """
    positions = SETTING_HAND_INDICES[v57_pick]
    top_pos = int(positions[0])
    mid_a, mid_b = int(positions[1]), int(positions[2])
    bot_pos = (int(positions[3]), int(positions[4]),
               int(positions[5]), int(positions[6]))

    if top_pos != max_sing_pos:
        return False
    if {mid_a, mid_b} != set(pair_pos):
        return False
    # Bot suits check
    suits = hand & 3
    bot_suits = sorted(Counter(int(suits[p]) for p in bot_pos).values(),
                       reverse=True)
    return bot_suits == [2, 1, 1]


def _detect_lo_pair_ss_force_tnomax(
    hand: np.ndarray,
    max_sing_gate: int,
    v57_pick: Optional[int] = None,
) -> Optional[int]:
    """Return the PMID_tnomax_best setting index for hands matching the
    trigger, else None.

    Trigger conditions (all must be true):
      1. Hand is exactly a single pair (no quads, no trips, no other pairs).
      2. pair_rank ∈ LOW_PAIR_RANKS (2-7).
      3. max_sing (rank of highest non-pair card) ≤ max_sing_gate.
      4. Cell is PMID_SS_MAXTOP, i.e.:
         - n_PBOT_DS == 0
         - n_PMID_DS == 0   (no PMID-DS config at all)
         - n_PMID_SS_w_maxtop > 0  (PMID with SS bot and max-on-top exists)
      5. A PMID_tnomax config exists (at least one valid top_local != max).
      6. (v2 restriction) v57's current pick IS PMID_tmax_SS. The rule only
         flips the swap-eligible population; it never overrides v57 when v57
         chose a different config. v57_pick is computed lazily and only
         passed if all earlier preconditions pass.

    If triggered, returns the setting index for the BEST tnomax config:
      mid = pair_pos
      top = the non-max singleton giving the highest (bot_pair_high, top_rank)
      bot = the 4 other singletons (always includes max)
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

    # --- Enumerate PMID configs:
    # For each top_local, check bot suit pattern. Classify:
    #   - DS (2+2)  : if ANY DS exists → cell is PMID_DS_*, not our target.
    #   - SS (2+1+1): track best (bot_pair_high, top_rank) for tnomax variants.
    #   - 31 (3+1)  : same.
    #   - RB / 4f   : bot_pair_high = 0 (no flush-draw pair-anchor).
    # Also require: at least one SS_w_maxtop config exists (cell precondition).
    max_sing_local = sing_ranks.index(max_sing_rank)

    any_ds = False
    any_ss_w_maxtop = False

    # Best tnomax candidate: (bot_pair_high, top_rank, top_local, suit_class_rank)
    # suit_class_rank: prefer SS over 31 over RB/4f as a tiebreak (lower is better).
    best_tnomax = None  # (-bph, -top_rank, suit_class_rank, top_local)

    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits_arr = [sing_suits[k] for k in bot_locals]
        cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)

        is_DS = (cnt == [2, 2])
        is_SS = (cnt == [2, 1, 1])
        is_31 = (cnt == [3, 1])
        # is_RB / is_4f covered by else.

        if is_DS:
            any_ds = True
            continue  # cell is PMID_DS_*, not our target
        if is_SS and top_local == max_sing_local:
            any_ss_w_maxtop = True

        if top_local == max_sing_local:
            continue  # we want tnomax candidates only

        # Compute bot_pair_high
        by_suit = defaultdict(list)
        for k in bot_locals:
            by_suit[sing_suits[k]].append(sing_ranks[k])
        if is_SS:
            # find the suit with 2 cards → its higher card is bph
            local_bph = 0
            for s, rs in by_suit.items():
                if len(rs) == 2:
                    local_bph = max(rs)
                    break
            suit_class = 0  # SS preferred
        elif is_31:
            local_bph = 0
            for s, rs in by_suit.items():
                if len(rs) == 3:
                    local_bph = max(rs)  # high of the triple
                    break
            suit_class = 1  # 31 second-preferred
        else:
            local_bph = 0
            suit_class = 2  # RB / 4f weakest

        top_rank_here = sing_ranks[top_local]
        # Sort key: maximize bph, then top_rank, then prefer lower suit_class
        # (note we want LARGEST bph first → store -bph)
        key = (-local_bph, -top_rank_here, suit_class, top_local)
        if best_tnomax is None or key < best_tnomax:
            best_tnomax = key

    # --- Cell preconditions enforcement ---
    if any_ds:
        return None  # cell is PMID_DS_*, not PMID_SS_MAXTOP
    if not any_ss_w_maxtop:
        # PMID_SS_w_maxtop must exist by cell definition. If none, cell is
        # PMID_OTHER (RB/4f-only), not our target.
        return None
    if best_tnomax is None:
        return None  # no tnomax candidate (shouldn't happen if SS_maxtop exists)

    # --- v2 restriction: check v57's pick is PMID_tmax_SS ---
    max_sing_pos = sing_pos[max_sing_local]
    if v57_pick is None:
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
    if not _v57_picked_pmid_tmax_ss(h, v57_pick, pair_pos, max_sing_pos):
        return None  # v57 didn't pick tmax_SS — don't override

    # Build the chosen setting.
    _, _, _, top_local = best_tnomax
    top_pos = sing_pos[top_local]
    return int(_setting_index_from_tmb(top_pos, pair_pos[0], pair_pos[1]))


def make_strategy_v59(max_sing_gate: int) -> Callable:
    """Build a v59 strategy with the given max_sing gate.

    max_sing_gate options (per S85 Phase B+):
      9   — fires on ~205 cell hands; tiniest population
      10  — fires on ~469 cell hands
      11  — fires on ~995 cell hands; ~67% swap-right
      12  — fires on ~10,800 cell hands; ~48% (coin-flip — likely NULL)
      13  — fires on ~28,500 cell hands; ~23% (wrong-bias — likely negative)
      14  — fires on entire cell, ~60,000 hands; ~17% (heavily wrong)
    """
    def strategy_v59_lo_pair_ss_tnomax(hand: np.ndarray) -> int:
        forced = _detect_lo_pair_ss_force_tnomax(hand, max_sing_gate)
        if forced is not None:
            return int(forced)
        return int(strategy_v57_lo_pair_defensive(hand))
    strategy_v59_lo_pair_ss_tnomax.__name__ = (
        f"strategy_v59_lo_pair_ss_tnomax_gate{max_sing_gate}"
    )
    return strategy_v59_lo_pair_ss_tnomax


# Default export: max_sing_gate=11 (best swap-right rate on a non-trivial
# population per Phase B+). Multi-gate grading via grader script.
strategy_v59_lo_pair_ss_tnomax = make_strategy_v59(max_sing_gate=11)


if __name__ == "__main__":
    # Sanity tests
    from tw_analysis.settings import parse_hand
    from strategy_v57_lo_pair_defensive import strategy_v57_lo_pair_defensive

    # Construct a LOW × PMID_SS_MAXTOP hand:
    # pair 3c 3d (suits c,d). Need n_PBOT_DS == 0 (no singleton of suit c
    # AND of suit d simultaneously), n_PMID_DS == 0 (no 4-subset of singletons
    # with 2+2 pattern), and n_PMID_SS_w_maxtop > 0 (at least one 4-subset
    # excluding max gives 2+1+1 pattern).
    # Try: pair 3c 3d, singletons Th 8h 7s 6s 2s. suits: h, h, s, s, s.
    #   max_sing = T (h). Excluding T: 8h 7s 6s 2s → suits h, s, s, s → 1+3 (31). NOT SS.
    # Try: pair 3c 3d, singletons Jh 8h 7s 4s 2s. suits: h, h, s, s, s.
    #   max=J(h). Excl J: 8h 7s 4s 2s → suits h, s, s, s = 1+3 (31). NOT SS.
    # Try: pair 3c 3d, singletons Jh 8h 7s 4s 6c. suits: h, h, s, s, c.
    #   max=J(h). Excl J: 8h 7s 4s 6c → suits h, s, s, c = 1+2+1 (SS!). 2+1+1 ✓
    #   PBOT_DS: needs singleton of suit c AND of suit d. We have c (6c) but no d. → 0 ✓.
    #   PMID_DS: any 4-subset 2+2? subsets:
    #     {Jh,8h,7s,4s} (excl 6c): h,h,s,s = 2+2 DS ← would be cell PMID_DS_*!
    # Fix: try pair 3c 3d, singletons Jh 8h 7d 4s 6c. suits h, h, d, s, c.
    #   max=J(h). Excl J: 8h 7d 4s 6c → h, d, s, c = 1+1+1+1 (RB). Not SS.
    # Try: pair 3c 3d, singletons Jh 8s 7h 4d 6c. suits h, s, h, d, c.
    #   max=J(h). Excl J: 8s 7h 4d 6c → s, h, d, c = RB. Not SS.
    # Try: pair 3c 3d, singletons Jh 8h 7s 4d 6c. suits h, h, s, d, c.
    #   max=J(h). Excl J: 8h 7s 4d 6c → h, s, d, c = RB. Not SS.
    # Try: pair 3c 3d, singletons Jh 8h 7h 4s 6c. suits h, h, h, s, c.
    #   max=J(h). Excl J: 8h 7h 4s 6c → h, h, s, c = 2+1+1 SS ✓!
    #   PBOT_DS: need sing of suit c AND d. Have c (6c) but no d. → 0 ✓.
    #   PMID_DS: 4-subset 2+2?
    #     {Jh,8h,7h,4s}: h×3, s×1 = 3+1, not DS.
    #     {Jh,8h,7h,6c}: h×3, c×1 = 3+1, not DS.
    #     {Jh,8h,4s,6c}: h,h,s,c = 2+1+1 SS, not DS.
    #     {Jh,7h,4s,6c}: h,h,s,c = SS.
    #     {8h,7h,4s,6c}: h,h,s,c = SS.
    #   No DS → n_PMID_DS == 0 ✓. Cell is PMID_SS_MAXTOP ✓!
    # max_sing = J → fires at gate ≥ 11.
    test_cases = [
        # LOW pair 3, max=J → fires at gate 11
        ("3c 3d Jh 8h 7h 4s 6c", 11, True, "low pair 3, max=J, PMID_SS_MAXTOP"),
        # Same hand, gate=10 → max=J above gate → no fire
        ("3c 3d Jh 8h 7h 4s 6c", 10, False, "max=J above gate 10 → no fire"),
        # HIGH pair (Jc Jd) → not LOW
        ("Jc Jd 8h 7h 4s 6c 2h", 13, False, "J-pair — not LOW"),
        # No pair
        ("Ac Kh Qd Jc Ts 9h 2d", 13, False, "high_only — not pair"),
        # LOW pair 5, max=A → max above gate 11 → no fire
        ("5c 5d Ah 8h 7h 4s 6c", 11, False, "max=A above gate 11"),
    ]
    print("Sanity tests:")
    for s, gate, expect_fire, desc in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        forced = _detect_lo_pair_ss_force_tnomax(h, gate)
        fired = forced is not None
        ok = (fired == expect_fire)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        strat = make_strategy_v59(gate)
        v59_pick = int(strat(h))
        print(f"  [{'OK' if ok else 'FAIL'}] {desc}: gate={gate} "
              f"fired={fired} (expected {expect_fire})  "
              f"v57_pick={v57_pick} v59_pick={v59_pick}")
