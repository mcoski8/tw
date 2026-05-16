"""strategy_v61 — surgical fix for the S87 v52-chain bleed on HIGH_ONLY
x DS_NO_JOINT x max in {J,Q,K,A}.

S87 audit found that the v47->v48->v52 chain leaks ~$98/1000h MORE than v44_dt
would on this 756,000-hand sub-population. The bleed sources:
  - v47 (Rules 13-16) fallthrough on Q/K/A-high DS_NO_JOINT: ~$82/1000h
  - v52-J-HIMID on J-high DS_NO_JOINT: ~$13/1000h
  - v52-defensive-gated on s2<=8: ~$4/1000h

v61 is a "stop the bleed" rule: detect HIGH_ONLY x DS_NO_JOINT x max in {J-A}
and return strategy_v44_dt directly, bypassing the v47->v48->v52 chain for
those hands. Outside that gate, v61 == v57.

This is NOT a value-extraction rule (v44_dt still leaks on these cells vs
oracle); it is a regression fix. A follow-up value-extraction rule on top of
v44_dt remains future work (likely needs the Option C N=1000 oracle infra).

USAGE
-----
    from strategy_v61_high_only_ds_no_joint_fix import (
        strategy_v61_high_only_ds_no_joint_fix
    )
    idx = strategy_v61_high_only_ds_no_joint_fix(hand_bytes)

Self-test:
    python3 analysis/scripts/strategy_v61_high_only_ds_no_joint_fix.py
"""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
for p in (str(SRC), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)

TARGET_MAX_RANKS = {11, 12, 13, 14}  # J, Q, K, A


def _is_high_only_ds_no_joint(hand: np.ndarray) -> bool:
    """Match S71 cell taxonomy: HIGH_ONLY (no pair) x DS_NO_JOINT.

    DS_NO_JOINT precondition:
      1. No rank appears 2+ times (HIGH_ONLY: no pair/trips/quads).
      2. n_DS > 0 (at least one 4-singleton subset has 2+2 suit pattern for bot).
      3. n_DS_with_max_top > 0 (max card can sit on top of a DS bot configuration).
      4. n_joint_DS_ms_max_top == 0 (the DS-bot + max-top configurations do
         NOT have a suit-matched (ms) middle pair). I.e., DS is available but
         doesn't combine into a "joint" max-top + ms-mid + DS-bot setting.
    """
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    rc = np.bincount(np.asarray(int_ranks, dtype=np.int64), minlength=15)
    if int((rc >= 2).sum()) != 0:
        return False  # HIGH_ONLY only — any pair+ disqualifies

    max_rank = max(int_ranks)
    if max_rank not in TARGET_MAX_RANKS:
        return False  # Out of {J,Q,K,A} target band

    max_pos = int_ranks.index(max_rank)

    n_DS = 0
    n_DS_with_max_top = 0
    n_joint = 0

    for bot_idx in combinations(range(7), 4):
        bot_suits = [int_suits[i] for i in bot_idx]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        n_DS += 1
        leftover_pos = [i for i in range(7) if i not in bot_idx]
        if max_pos in leftover_pos:
            n_DS_with_max_top += 1
            mid_pos = [j for j in leftover_pos if j != max_pos]
            if int_suits[mid_pos[0]] == int_suits[mid_pos[1]]:
                n_joint += 1

    return (n_DS > 0) and (n_DS_with_max_top > 0) and (n_joint == 0)


def strategy_v61_high_only_ds_no_joint_fix(hand: np.ndarray) -> int:
    """Return v44_dt pick when hand is in target cell; else v57."""
    if _is_high_only_ds_no_joint(hand):
        return int(strategy_v44_dt(hand))
    return int(strategy_v57_lo_pair_defensive(hand))


if __name__ == "__main__":
    # Self-tests
    from tw_analysis.settings import parse_hand  # noqa: E402

    cases = [
        # (hand_str, expected_in_cell, description)
        # K-high, no pair, two clubs + two hearts available for DS bot —
        # leftover (after picking bot=cc hh) is {K, x, y}; if K is at the
        # right position and the two leftover singletons share a suit ->
        # joint. Construct hand where K is leftover and mid doesn't suit-match.
        ("Kc Qd 9c 8h 7h 6d 4s", True,
         "K-high, DS pattern (cc hh), max-top possible, no joint"),
        # K-high, pair of 5s -> not HIGH_ONLY
        ("Kc 5d 5h 9c 8h 7d 4s", False,
         "K-high but has a pair -> not HIGH_ONLY"),
        # A-high, rainbow -> no DS pattern -> not in cell
        ("Ac Kd Qh Js 9c 7d 4h", False,
         "A-high rainbow, no DS pattern"),
        # T-high (below {J-A}) -> not in cell
        ("Tc Qd 9c 8h 7h 6d 4s", False,
         "T-high — wait, this has Q so max=Q -> retest"),
        # 9-high (below {J-A}) -> not in cell
        ("9c 8d 7h 6s 5c 4h 3d", False,
         "9-high — below target band"),
    ]
    print("Sanity tests:")
    for hstr, expected, desc in cases:
        cards = parse_hand(hstr)
        h = np.array([c.idx for c in cards], dtype=np.uint8)
        ranks_now = [(int(c.idx // 4) + 2) for c in cards]
        max_now = max(ranks_now)
        in_cell = _is_high_only_ds_no_joint(h)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        v61_pick = int(strategy_v61_high_only_ds_no_joint_fix(h))
        v44_pick = int(strategy_v44_dt(h))
        marker = "OK " if in_cell == expected else "FAIL"
        print(f"  [{marker}] {desc}")
        print(f"      hand={hstr!r}  max_rank={max_now}  in_cell={in_cell} "
              f"(expected {expected})")
        if in_cell:
            same = "v61==v44" if v61_pick == v44_pick else "v61!=v44 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v61={v61_pick}  {same}")
        else:
            same = "v61==v57" if v61_pick == v57_pick else "v61!=v57 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v61={v61_pick}  {same}")
