"""strategy_v63 — full HIGH_ONLY × {J-A} chain gate-out.

S87 (v61) gated DS_NO_JOINT × {J-A}: +$98.67/1000h.
S88 (v62) extended to DS_NO_MAXTOP / MS_ONLY / JOINT_HIGH × {J-A}: +$98.84.
S89 (v63) closes out the remaining two prefix-silent HIGH_ONLY × {J-A}
cells:

  Cell                       n_target  v44→v52 chain bleed (per S89 audit)
  -----------------------------------  --------------------------------------
  HIGH_ONLY × JOINT_MED × {J-A}         44,562   +$8.24/1000h
  HIGH_ONLY × JOINT_LOW × {J-A}          3,570   +$1.85/1000h
  -----------------------------------  --------------------------------------
  TOTAL                                 48,132   +$10.09/1000h

S89 layer attribution: $9.68/$10.09 = 96% of the bleed is from the v44→v47
transition. Same culprit as S87/S88 (v47 Rules 13-16). v47→v48 contributes
−$0.44 (minor improvement), v48→v52 contributes +$0.85 (small but
non-negligible v52-defensive-gated + v52-J-HIMID bleed).

v63 extends v62's gate to cover all 6 non-empty HIGH_ONLY × {J-A} cells.
NEITHER × {J-A} is structurally empty (proven: HIGH_ONLY with max ∈ {J-A}
must have ≥2 cards of one non-max suit, so n_ms_mid_with_max_top ≥ 1),
so v63 effectively gates ALL HIGH_ONLY × {J-A} hands.

JOINT_MED, JOINT_LOW have small individual leak ($1.85-$8.24/1000h) but the
mechanism is identical to S87/S88 — v47 fallthrough is net-negative across
the entire HIGH_ONLY × {J-A} zone.

Outside the gate (HIGH_ONLY × max ≤ T routes through v52-defensive-low; all
other categories), v63 == v62 by construction (and v62 == v57 outside its
gate, so v63 == v57 outside the union of all three gates).

USAGE
-----
    from strategy_v63_high_only_chain_fix_full import (
        strategy_v63_high_only_chain_fix_full,
    )
    idx = strategy_v63_high_only_chain_fix_full(hand_bytes)

Self-test:
    python3 analysis/scripts/strategy_v63_high_only_chain_fix_full.py
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
from strategy_v62_high_only_chain_fix import (  # noqa: E402
    strategy_v62_high_only_chain_fix,
)
from strategy_v57_lo_pair_defensive import (  # noqa: E402
    strategy_v57_lo_pair_defensive,
)

# Target max ranks (J=11, Q=12, K=13, A=14) — same as v61/v62.
TARGET_MAX_RANKS = frozenset({11, 12, 13, 14})

# v63 gates ALL non-empty HIGH_ONLY cells in the {J-A} max-rank band.
# NEITHER × {J-A} is structurally empty (proof: any HIGH_ONLY hand with
# all distinct ranks has n_ms_mid_with_max_top ≥ 1 because the remaining
# 6 non-max cards can't span 4 distinct suits).
TARGET_CELLS = frozenset({"DS_NO_JOINT", "DS_NO_MAXTOP", "MS_ONLY",
                          "JOINT_HIGH", "JOINT_MED", "JOINT_LOW"})


def _classify_high_only_cell(hand: np.ndarray):
    """Replicate the S71 cell taxonomy at inference time.

    Returns (cell_name, max_rank) if HIGH_ONLY (no pair/trips/quads).
    Returns (None, None) otherwise.

    Identical to the function in strategy_v62 — duplicated here so v63 is
    self-contained.
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


def _is_v63_gated_cell(hand: np.ndarray) -> bool:
    """v63 gate: HIGH_ONLY × max ∈ {J-A} × cell ∈ all 6 audited cells."""
    cell, max_rank = _classify_high_only_cell(hand)
    if cell is None:
        return False
    if max_rank not in TARGET_MAX_RANKS:
        return False
    return cell in TARGET_CELLS


def strategy_v63_high_only_chain_fix_full(hand: np.ndarray) -> int:
    """Return v44_dt pick when hand is in the v63-gated cell set; else v57.

    Equivalent to: v63 == v44_dt on gated cells; v63 == v57 elsewhere.
    Strict superset of v62's gate (v62 covered 4 cells; v63 covers all 6
    non-empty HIGH_ONLY × {J-A} cells).
    """
    if _is_v63_gated_cell(hand):
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
        ("9c 8d 7h 6s 5c 4h 3d", False,
         "9-high — below target band {J-A}"),
        ("Kc Qc Jd Td 9d 8s 4s", True,
         "K-high JOINT_HIGH-style (DS bot + ms mid + max top + max mid_high)"),
        ("Kc Qc 9d 8h 7s 5d 3h", True,
         "K-high, MS_ONLY"),
    ]
    print("Sanity tests:")
    for hstr, expected, desc in cases:
        cards = parse_hand(hstr)
        h = np.array([c.idx for c in cards], dtype=np.uint8)
        cell, max_rank = _classify_high_only_cell(h)
        in_gate = _is_v63_gated_cell(h)
        v57_pick = int(strategy_v57_lo_pair_defensive(h))
        v62_pick = int(strategy_v62_high_only_chain_fix(h))
        v63_pick = int(strategy_v63_high_only_chain_fix_full(h))
        v44_pick = int(strategy_v44_dt(h))
        marker = "OK " if in_gate == expected else "FAIL"
        print(f"  [{marker}] {desc}")
        print(f"      hand={hstr!r}  cell={cell} max={max_rank}  "
              f"in_v63_gate={in_gate} (expected {expected})")
        if in_gate:
            same = "v63==v44" if v63_pick == v44_pick else "v63!=v44 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v62={v62_pick} "
                  f"v63={v63_pick}  {same}")
        else:
            same = "v63==v57" if v63_pick == v57_pick else "v63!=v57 (?!)"
            print(f"      v44={v44_pick} v57={v57_pick} v62={v62_pick} "
                  f"v63={v63_pick}  {same}")
