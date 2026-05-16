"""
v66 candidate — v65 + Rule 26 (trips × B_DS_AVAIL_LKR × intra-Layout-A
force-best-DS-bot).

CONTEXT (S95)
-------------
S94 closed the bucket-level rule-extraction lever as STRUCTURALLY SATURATED
across all 10 within-v44_dt residual cells (max sub-bucket trigger predictivity
57.5%, below Rule 25's 62% anchor). The Phase A.2 follow-up identified
**trips B_DS_AVAIL_LKR intra-Layout-A bot_suit** as the only OPEN candidate
showing Rule-20-style intra-layout signal: $19.49/1000h aggregate when v44
picks Layout A with non-DS bot but oracle picks Layout A with DS bot
(25,905 hands).

S95 Phase A re-confirmed (note: actual JSON numbers, the resume prompt's
n=210/n=370 lines had transcription typos):

  sub-bucket (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings)
   ksc | nkts | nbds |      n |  or_ds |     P |    wg
     2 |    4 |    1 |  1,618 |  1,618 | 100.0% | $1.12
     3 |    4 |    1 |  6,542 |  5,757 |  88.0% | $4.77
     2 |    4 |    3 |  6,912 |  4,337 |  62.7% | $4.18
     2 |    3 |    1 | 29,465 | 13,588 |  46.1% | $12.58
     2 |    2 |    1 |  5,791 |    605 |  10.4% | $0.55
     1 |    3 |    3 |  6,705 |      0 |   0.0% | $0.74

  Per-gate aggregation (over the "v44 picks non-DS bot in Layout A" pop):
    NARROW  [(2,4,1)+(3,4,1)]:           n= 8,160  meanP=90.4%  wg=$ 5.89
    MEDIUM  [+ (2,4,3)]:                 n=15,072  meanP=77.7%  wg=$10.07
    WIDE    [+ (2,3,1)]:                 n=44,537  meanP=56.8%  wg=$22.64

RULE 26 — DEFINITION
--------------------
Trigger conditions (all must be true):
  1. Hand is exactly trips (one trip, no quads, no pairs).
  2. Hand is in cell B_DS_AVAIL_LKR:
       b_ds_avail (= n_b_ds_routings > 0) AND best_b_ds_kicker_2nd_rank < 10
  3. Sub-bucket (kickers_max_suit_count, n_kickers_in_trip_suits,
     n_b_ds_routings) is in the active gate.
  4. v44_dt picks Layout A with non-DS bot (= top is a kicker, mid is 2
     trip cards, bot is 1 trip + 3 kickers with bot-suit ≠ DS).

If triggered, returns the setting index for the BEST Layout-A DS-bot config:
  top = chosen kicker (the one left over after bot fills)
  mid = 2 of the 3 trip cards
  bot = 1 trip card + 3 kickers, forming a 2+2 suit pattern

"Best" picker criterion (TOP_HIGH then pair-tops): pick the DS-bot Layout-A
config whose TOP rank is highest; among those tied on top rank, prefer
highest bot pair-top, then second pair-top.

**PICKER-CRITERION CHOICE (S95 FINDING)**: The naive Rule-20-style
"bot_pair_high desc, then top_rank desc" criterion that worked for the pair
rules (Rules 20 + 25) gets only 7.5%-13.8% exact-match with oracle in this
cell. Empirical picker sweep (picker_sweep_v66_S95.py) found that
**TOP_HIGH_then_pair_tops** lifts exact-match to 85.2% (NARROW) — because
for trips, the top tier's 1-card kicker dominates by scoring as a Hold'em
1+5; oracle puts the highest kicker on top. This is opposite to the pair
rules where the top is a "leftover singleton not-max-sing".

GATES
-----
  NARROW — [(2,4,1), (3,4,1)]            (~8,160 changed hands)
  MEDIUM — [+ (2,4,3)]                   (~15,072 changed hands)
  WIDE   — [+ (2,3,1)]                   (~44,537 changed hands)

Routes through v65 if any precondition fails.

DESIGN NOTES (Rule-20-style analog)
-----------------------------------
Rule 20 (LOW pair × PMID_DS_NOMAXTOP) forces "best DS configuration by
bot_pair_high" — analogous deterministic intra-cell pick. Trigger
predictivity ~89-93% supports clean SHIP. Rule 25 (MID pair × same cell)
extends to lower predictivity (62%) with smaller per-hand lift but still SHIPS.

Rule 26's trigger predictivity at the (3,4,1) sub-bucket is 88% on 6,542 hands
($4.77 wg). The NARROW gate at (2,4,1)+(3,4,1) is 90% on 8,160 hands ($5.89
wg). MEDIUM and WIDE are lower predictivity but more wg — exact ship-vs-MIXED
verdict is an empirical question for the two-grid grader.
"""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Optional, Callable, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from tw_analysis.query import SETTING_HAND_INDICES  # noqa: E402


# Gate triggers (set of (kickers_max_suit_count, n_kickers_in_trip_suits,
# n_b_ds_routings)). Locked from S95 Phase A.
_NARROW: Tuple[Tuple[int, int, int], ...] = (
    (2, 4, 1),
    (3, 4, 1),
)
_MEDIUM: Tuple[Tuple[int, int, int], ...] = _NARROW + ((2, 4, 3),)
_WIDE: Tuple[Tuple[int, int, int], ...] = _MEDIUM + ((2, 3, 1),)

GATE_TRIGGERS = {
    "NARROW": frozenset(_NARROW),
    "MEDIUM": frozenset(_MEDIUM),
    "WIDE": frozenset(_WIDE),
}


def _v44_pick_is_layout_a_non_ds(
    hand: np.ndarray,
    v44_pick: int,
    trip_pos_set: set,
) -> bool:
    """Return True iff v44_dt's chosen setting is Layout A (top=kicker,
    mid=2 trip cards, bot=1 trip + 3 kickers) with a non-DS bot.

    Layout A signature:
      top is a kicker (NOT in trip_pos_set)
      mid contains BOTH cards in trip_pos_set's 2-of-3 subset
      bot contains the third trip card + 3 kickers

    Bot suit pattern: collect 4 bot cards' suits, count, sorted desc.
      DS = [2, 2]
      non-DS = anything else.
    """
    positions = SETTING_HAND_INDICES[v44_pick]
    top_pos = int(positions[0])
    mid_a, mid_b = int(positions[1]), int(positions[2])
    bot_positions = [int(p) for p in positions[3:7]]

    # Layout A: top is kicker, mid is 2 trip cards
    if top_pos in trip_pos_set:
        return False
    if not (mid_a in trip_pos_set and mid_b in trip_pos_set):
        return False

    # bot suit pattern
    suits = hand & 3
    bot_suits = [int(suits[p]) for p in bot_positions]
    cnt = sorted(Counter(bot_suits).values(), reverse=True)
    if cnt == [2, 2]:
        return False  # bot is DS — v44 already in target
    return True


def _detect_trips_layout_a_force_ds_bot(
    hand: np.ndarray,
    gate_triggers: frozenset,
    v65_pick: Optional[int] = None,
) -> Optional[int]:
    """If hand matches trigger and v65 picks Layout-A-non-DS, return the
    best Layout-A DS-bot setting index. Else None."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks.astype(int), minlength=15)

    # Hand structure: exactly trips
    if int((rc == 4).sum()) != 0: return None
    if int((rc == 3).sum()) != 1: return None
    if int((rc == 2).sum()) != 0: return None

    trip_rank = int(np.where(rc == 3)[0][0])
    trip_pos = [int(i) for i in range(7) if int(ranks[i]) == trip_rank]
    kicker_pos = [int(i) for i in range(7) if int(ranks[i]) != trip_rank]
    assert len(trip_pos) == 3 and len(kicker_pos) == 4

    trip_suits = tuple(sorted(int(suits[p]) for p in trip_pos))
    # Trip cards occupy 3 distinct suits (always true for trips)
    if len(set(trip_suits)) != 3:
        return None

    kicker_ranks = [int(ranks[p]) for p in kicker_pos]
    kicker_suits = [int(suits[p]) for p in kicker_pos]

    # Cell features: B-DS availability + best 2nd-kicker rank
    n_b_ds_routings = 0
    best_b_ds_kicker_2nd = 0
    best_b_ds_kicker_max = 0
    for a, b in combinations(trip_suits, 2):
        ka_ranks = [kicker_ranks[i] for i in range(4) if kicker_suits[i] == a]
        kb_ranks = [kicker_ranks[i] for i in range(4) if kicker_suits[i] == b]
        if not ka_ranks or not kb_ranks:
            continue
        n_b_ds_routings += 1
        for ra in ka_ranks:
            for rb in kb_ranks:
                rk_max = max(ra, rb)
                rk_2nd = min(ra, rb)
                if (rk_max, rk_2nd) > (best_b_ds_kicker_max, best_b_ds_kicker_2nd):
                    best_b_ds_kicker_max = rk_max
                    best_b_ds_kicker_2nd = rk_2nd

    # Cell precondition: B_DS_AVAIL_LKR
    if n_b_ds_routings == 0:
        return None
    if best_b_ds_kicker_2nd >= 10:
        return None  # HKR cell, not LKR

    # Sub-bucket features
    kicker_suit_counts = Counter(kicker_suits)
    kickers_max_suit_count = max(kicker_suit_counts.values())
    n_kickers_in_trip_suits = sum(1 for s in kicker_suits if s in trip_suits)

    # Trigger filter
    trigger_key = (
        int(kickers_max_suit_count),
        int(n_kickers_in_trip_suits),
        int(n_b_ds_routings),
    )
    if trigger_key not in gate_triggers:
        return None

    # v65 pick must be Layout A with non-DS bot
    trip_pos_set = set(trip_pos)
    if v65_pick is None:
        v65_pick = int(strategy_v65_mid_pair_chain_extend(h))
    if not _v44_pick_is_layout_a_non_ds(h, v65_pick, trip_pos_set):
        return None

    # Enumerate Layout-A DS-bot settings, pick the best by
    # TOP_HIGH then (bot_pair_high desc, bot_pair_2nd desc).
    # See S95 picker-sweep finding: TOP_HIGH wins 85.2% exact-match in NARROW;
    # naive bot_pair_high-first gets only 7.5%.
    best_key = None
    best_setting = None

    for bot_trip_local in range(3):
        bot_trip_pos = trip_pos[bot_trip_local]
        mid_trip_locals = sorted(i for i in range(3) if i != bot_trip_local)
        mid_a_pos = trip_pos[mid_trip_locals[0]]
        mid_b_pos = trip_pos[mid_trip_locals[1]]
        bot_trip_suit = int(suits[bot_trip_pos])

        for top_kicker_local in range(4):
            bot_kicker_locals = [k for k in range(4) if k != top_kicker_local]
            bot_kicker_pos_list = [kicker_pos[k] for k in bot_kicker_locals]
            bot_kicker_suits = [int(suits[p]) for p in bot_kicker_pos_list]
            bot_kicker_ranks = [int(ranks[p]) for p in bot_kicker_pos_list]

            # Bot suit pattern: trip + 3 kickers
            bot_suits_arr = [bot_trip_suit] + bot_kicker_suits
            cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
            if cnt != [2, 2]:
                continue
            # DS bot.

            # Compute pair-tops in bot (max rank per suit, for suits with >=2 cards).
            by_suit = {}
            by_suit.setdefault(bot_trip_suit, []).append(int(ranks[bot_trip_pos]))
            for r, s in zip(bot_kicker_ranks, bot_kicker_suits):
                by_suit.setdefault(s, []).append(r)
            pair_tops = sorted(
                (max(rs) for rs in by_suit.values() if len(rs) >= 2),
                reverse=True,
            )
            top_rank = int(ranks[kicker_pos[top_kicker_local]])

            # TOP_HIGH-first key: maximize top_rank, then secondary pair-tops.
            key = (
                top_rank,
                pair_tops[0],
                pair_tops[1] if len(pair_tops) > 1 else 0,
            )
            if best_key is None or key > best_key:
                best_key = key
                best_setting = (
                    kicker_pos[top_kicker_local],
                    mid_a_pos,
                    mid_b_pos,
                )

    if best_setting is None:
        return None  # no Layout-A DS-bot achievable; leave v65 pick alone

    top_pos, mid_a, mid_b = best_setting
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def make_strategy_v66(gate: str) -> Callable:
    """Build a v66 strategy with the given gate."""
    triggers = GATE_TRIGGERS[gate]

    def strategy_v66_trips_layout_a_force_ds_bot(hand: np.ndarray) -> int:
        forced = _detect_trips_layout_a_force_ds_bot(hand, triggers)
        if forced is not None:
            return int(forced)
        return int(strategy_v65_mid_pair_chain_extend(hand))

    strategy_v66_trips_layout_a_force_ds_bot.__name__ = (
        f"strategy_v66_trips_layout_a_force_ds_bot_gate_{gate}"
    )
    return strategy_v66_trips_layout_a_force_ds_bot


# Default export uses NARROW gate (highest predictivity). Multi-gate
# grading via grader.
strategy_v66_trips_layout_a_force_ds_bot = make_strategy_v66(gate="NARROW")


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand

    # Sanity tests
    test_cases = [
        # Trips with kickers structured for B_DS_AVAIL_LKR + (3,4,1) trigger
        # Trip = 9, suits c,d,h. kickers = J(s) 8(c) 5(c) 3(d): ksc=2 (c=2),
        # nkts=3 (J in s is not trip-suit, 8c,5c,3d are in trip-suits = 3 kickers)
        # → (ksc=2, nkts=3, nbds=?). For nbds we need pairs of trip-suits both
        # of which have a kicker. (c,d): yes (8c+3d). (c,h): no (no h kicker).
        # (d,h): no. So nbds=1. Not in NARROW (which is (2,4,1)/(3,4,1)).
        ("9c 9d 9h Js 8c 5c 3d", "NARROW", "trip 9, ksc=2 nkts=3 nbds=1 — not in NARROW"),
        # Trip = 9, all kickers in trip suits, kicker max suit = 2
        # Try: 9c 9d 9h Jc 8d 5h 3c → suits c,d,h,h. ksc=2(c=2 or h=2), nkts=4
        # nbds: (c,d): c(Jc,3c), d(8d) → yes; (c,h): c, h(5h) → yes; (d,h): d, h → yes. nbds=3.
        # → (2,4,3) → not in NARROW
        ("9c 9d 9h Jc 8d 5h 3c", "NARROW", "trip 9, ksc=2 nkts=4 nbds=3 — not in NARROW (medium)"),
        # Same hand with MEDIUM
        ("9c 9d 9h Jc 8d 5h 3c", "MEDIUM", "trip 9, ksc=2 nkts=4 nbds=3 — in MEDIUM"),
        # Non-trips
        ("9c 9d Jh Ts 8d 5c 3d", "WIDE", "pair 9 — not trips"),
        # Trips but high-card kicker (HKR not LKR cell)
        ("9c 9d 9h Ad Kc 5c 3d", "WIDE", "trips 9 with A+K kickers — check HKR/LKR"),
    ]
    print("Sanity tests:")
    for hstr, gate, desc in test_cases:
        cards = parse_hand(hstr)
        h = np.array([c.idx for c in cards], dtype=np.uint8)
        v65 = int(strategy_v65_mid_pair_chain_extend(h))
        strat = make_strategy_v66(gate)
        v66 = int(strat(h))
        forced = _detect_trips_layout_a_force_ds_bot(h, GATE_TRIGGERS[gate])
        fired = forced is not None
        changed = v66 != v65
        print(f"  {desc} (gate={gate}):")
        print(f"    v65={v65} v66={v66} fired={fired} changed={changed}")
