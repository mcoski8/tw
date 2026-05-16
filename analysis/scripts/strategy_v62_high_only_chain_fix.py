"""strategy_v62 — extended chain gate-out fix.

S87 (v61) gated out the v47→v48→v52 chain on HIGH_ONLY × DS_NO_JOINT × J-A
(+$98.67/1000h whole-grid lift). S88 audit revealed the SAME bleed pattern on
three more prefix-silent HIGH_ONLY cells:

  Cell                       n_target  v44→v52 chain bleed (per S88 audit)
  -----------------------------------  --------------------------------------
  HIGH_ONLY × DS_NO_MAXTOP × {K,A}     133,056   +$52.88/1000h
  HIGH_ONLY × MS_ONLY × {J-A}          107,520   +$31.51/1000h
  HIGH_ONLY × JOINT_HIGH × {K,A}       116,928   +$14.45/1000h
  -----------------------------------  --------------------------------------
  TOTAL                                357,504   +$98.84/1000h

Attribution: ~$99.55 / $98.84 = 99.7% of the bleed is from the v44→v47
transition. v47 (Rules 13-16, Q-high DS chain) is again the dominant source
across all four cells; v48 and v52 are essentially neutral on top of v47.

v62 extends v61's gate-out to cover all four cells: detect HIGH_ONLY × max ∈
{J,Q,K,A} × cell ∈ {DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH} and return
strategy_v44_dt directly, bypassing the v47→v48→v52 chain. Outside that gate,
v62 == v61 by construction (and v61 == v57 outside its own gate, so v62 == v57
outside the union of gates).

JOINT_MED, JOINT_LOW, NEITHER are NOT gated out — they were not audited in
S88 and may have different chain behavior. Same for max ≤ T (HIGH_ONLY-low
hands route through v52-defensive-low, a distinct firing mode).

USAGE
-----
    from strategy_v62_high_only_chain_fix import strategy_v62_high_only_chain_fix
    idx = strategy_v62_high_only_chain_fix(hand_bytes)

Self-test:
    python3 analysis/scripts/strategy_v62_high_only_chain_fix.py
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
from strategy_v61_high_only_ds_no_joint_fix import (  # noqa: E402
    strategy_v61_high_only_ds_no_joint_fix,
)
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)

# Target max ranks (J=11, Q=12, K=13, A=14) consistent with S87 v61 gate.
TARGET_MAX_RANKS = frozenset({11, 12, 13, 14})

# Cells the S88 audit confirmed bleed via v47.
# (Plus the S87 cell DS_NO_JOINT — included for v62 to be a strict superset
# of v61. JOINT_MED/JOINT_LOW/NEITHER are NOT included — unaudited.)
TARGET_CELLS = frozenset({"DS_NO_JOINT", "DS_NO_MAXTOP", "MS_ONLY",
                          "JOINT_HIGH"})


def _classify_high_only_cell(hand: np.ndarray):
    """Replicate the S71 cell taxonomy at inference time.

    Returns (cell_name, max_rank) if HIGH_ONLY (no pair/trips/quads).
    Returns (None, None) otherwise.
    """
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return (None, None)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    rc = np.bincount(np.asarray(int_ranks, dtype=np.int64), minlength=15)
    if int((rc >= 2).sum()) != 0:
        return (None, None)  # Not HIGH_ONLY

    max_rank = max(int_ranks)
    max_pos = int_ranks.index(max_rank)

    n_DS = 0
    n_DS_with_max_top = 0
    n_joint = 0
    best_ms_mid_high = 0

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
                mh = max(int_ranks[mid_pos[0]], int_ranks[mid_pos[1]])
                if mh > best_ms_mid_high:
                    best_ms_mid_high = mh

    n_ms_mid_with_max_top = 0
    for top_pos in range(7):
        if top_pos != max_pos:
            continue
        rest = [i for i in range(7) if i != top_pos]
        for mid_a, mid_b in combinations(rest, 2):
            if int_suits[mid_a] == int_suits[mid_b]:
                n_ms_mid_with_max_top += 1

    if n_joint > 0:
        if best_ms_mid_high >= 11:
            cell = "JOINT_HIGH"
        elif best_ms_mid_high >= 8:
            cell = "JOINT_MED"
        else:
            cell = "JOINT_LOW"
    elif n_DS_with_max_top > 0:
        cell = "DS_NO_JOINT"
    elif n_DS > 0:
        cell = "DS_NO_MAXTOP"
    elif n_ms_mid_with_max_top > 0:
        cell = "MS_ONLY"
    else:
        cell = "NEITHER"

    return (cell, max_rank)


def _is_v62_gated_cell(hand: np.ndarray) -> bool:
    """v62 gate: HIGH_ONLY × max ∈ {J-A} × cell ∈ S87+S88-audited set."""
    cell, max_rank = _classify_high_only_cell(hand)
    if cell is None:
        return False
    if max_rank not in TARGET_MAX_RANKS:
        return False
    return cell in TARGET_CELLS


def strategy_v62_high_only_chain_fix(hand: np.ndarray) -> int:
    """Return v44_dt pick when hand is in the v62-gated cell set; else v57.

    Equivalent to: v62 == v44_dt on gated cells; v62 == v57 elsewhere.
    Strict superset of v61's gate (v61 only gated DS_NO_JOINT).
    """
    if _is_v62_gated_cell(hand):
        return int(strategy_v44_dt(hand))
    return int(strategy_v57_lo_pair_defensive(hand))


if __name__ == "__main__":
    # Self-tests
    from tw_analysis.settings import parse_hand  # noqa: E402

    cases = [
        # (hand_str, expected_in_gate, description)
        ("Kc Qd 9c 8h 7h 6d 4s", True,
         "K-high, DS bot avail without joint — DS_NO_JOINT (S87 cell)"),
        ("Kc 5d 5h 9c 8h 7d 4s", False,
         "K-high but has a pair — NOT HIGH_ONLY"),
        ("Ac Kd Qh Js 9c 7d 4h", False,
         "A-high rainbow — no DS, no ms-mid + max-top — NEITHER cell"),
        ("9c 8d 7h 6s 5c 4h 3d", False,
         "9-high — below target band {J-A}"),
        # JOINT_HIGH: K-high, with DS bot + ms mid + Q/J in mid
        ("Kc Qc Jd Td 9d 8s 4s", True,
         "K-high, picks-construct JOINT (DS bot + ms mid + max top)"),
        # JOINT_MED case (best_ms_mid_high=10): should NOT gate
        # MS_ONLY: K-high, no DS available, has ms-mid + max-top
        ("Kc Qc 9d 8h 7s 5d 3h", True,
         "K-high, ms-mid candidate with K on top, no DS available — MS_ONLY"),
        # DS_NO_MAXTOP: K-high but K can't sit on top of any DS bot
        # (best constructed inline)
    ]
    print("Sanity tests:")
    for hstr, expected, desc in cases:
        cards = parse_hand(hstr)
        h = np.array([c.idx for c in cards], dtype=np.uint8)
        cell, max_rank = _classify_high_only_cell(h)
        in_gate = _is_v62_gated_cell(h)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        v62_pick = int(strategy_v62_high_only_chain_fix(h))
        v44_pick = int(strategy_v44_dt(h))
        v61_pick = int(strategy_v61_high_only_ds_no_joint_fix(h))
        marker = "OK " if in_gate == expected else "FAIL"
        print(f"  [{marker}] {desc}")
        print(f"      hand={hstr!r}  cell={cell} max={max_rank}  "
              f"in_v62_gate={in_gate} (expected {expected})")
        if in_gate:
            same = "v62==v44" if v62_pick == v44_pick else "v62!=v44 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v61={v61_pick} "
                  f"v62={v62_pick}  {same}")
        else:
            same = "v62==v57" if v62_pick == v57_pick else "v62!=v57 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v61={v61_pick} "
                  f"v62={v62_pick}  {same}")
