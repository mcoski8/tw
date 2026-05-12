"""
Session 63 — Candidate refinement rules for J-high cells.

Each candidate is a function (hand_bytes -> Optional[int]) that returns a
setting_idx when it fires and overrides v52, or None to pass through to v52.

J-high differs structurally from Q-high (S58 decision matrix):
  - Oracle drops J off top 76% in J × DS_NO_JOINT (vs Q 52%, K 34%, A 6%).
    MOST aggressive drop-max profile of all high zones tested so far.
  - Oracle drops J off top 44% in J × JOINT_MED (vs Q 20% in JOINT_HIGH).
  - In J × DSnj per S58: top distribution is J:24%, 2:27%, 3:14%, etc.
    top=2 is now BIGGER than J-on-top (a structural inversion not present
    at Q/K/A). top=2 + top=3 combined ≈ 41%.
  - When best_DS_bot_pair_high == J (J-in-DS-pair), oracle picks JOINT
    only ~46% (vs 70.6% Q, 83% K, 93% A) — STRONGEST drop-J signal yet.

STRUCTURAL TWIST at J-high (not present at A/K/Q):
  v52 fires Rule 24 (defensive lowest-on-top + DS HIMID) when s2 ≤ 8 for
  J-high hands. v52 fires Rule 17 (J-on-top HIMID) when s2 > 8 for J-high.
  So v52 is TWO different code paths on J-high. Candidates fire only when
  they decide to; v52 (whichever sub-rule applies) is the baseline.

Top-3 leaky cells (post-Rule-17 / Rule 24) per Phase 2 audit (TBD):
  - DS_NO_JOINT  (n=37,800 = 62.9% of J-high; biggest leak)
  - DS_NO_MAXTOP (n=8,064)
  - MS_ONLY      (n=5,376)

Reuses helpers from candidates_K_high_S61.py (parameterized by max_rank):
  - _enumerate_max_on_top_configs(hand, max_rank)
  - _enumerate_nonMax_top_DSms(hand, max_rank)
  - _enumerate_nonMax_top_anyBot_ms(hand, max_rank)

Naming: rule_J_<cell>_<intent>(hand) -> Optional[int].
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from collections import Counter
from itertools import combinations

from candidates_K_high_S61 import (  # noqa: E402
    _enumerate_max_on_top_configs,
    _enumerate_nonMax_top_DSms,
    _enumerate_nonMax_top_anyBot_ms,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

JACK = 11


# ----------------------------------------------------------------------
# J-high cell tagging (mirrors _cell_for_hand_Q with JACK substituted)
# ----------------------------------------------------------------------

def _is_J_high_no_pair(hand_bytes) -> bool:
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) or int((rc == 3).sum()) or int((rc == 2).sum()):
        return False
    return int(ranks.max()) == JACK


def _cell_for_hand_J(hand_bytes) -> str:
    """Same definition as drill_high_only_v44_deepdive.cell_for_hand,
    specialized to J-high (max_rank=11)."""
    cfg = _enumerate_max_on_top_configs(hand_bytes, JACK)
    n_joint = sum(1 for c in cfg if c["bot_profile"] == "DS" and c["mid_suited"])
    n_DS_top = sum(1 for c in cfg if c["bot_profile"] == "DS")
    n_ms_top = sum(1 for c in cfg if c["mid_suited"])

    h = np.asarray(hand_bytes, dtype=np.uint8)
    suits = h & 3
    n_DS_any = 0
    for bot_idx in combinations(range(7), 4):
        bs = [int(suits[i]) for i in bot_idx]
        if sorted(Counter(bs).values(), reverse=True) == [2, 2]:
            n_DS_any += 1

    if n_joint > 0:
        best_ms_mid_high = max((c["mid_high"] for c in cfg
                                 if c["bot_profile"] == "DS" and c["mid_suited"]),
                                default=0)
        if best_ms_mid_high >= 11:
            return "JOINT_HIGH"
        if best_ms_mid_high >= 8:
            return "JOINT_MED"
        return "JOINT_LOW"
    if n_DS_top > 0:
        return "DS_NO_JOINT"
    if n_DS_any > 0:
        return "DS_NO_MAXTOP"
    if n_ms_top > 0:
        return "MS_ONLY"
    return "NEITHER"


# ----------------------------------------------------------------------
# J × DS_NO_JOINT — biggest opportunity (drop-J play 76% per oracle)
# ----------------------------------------------------------------------

def rule_J_DSnj_drop_J_low_top_DSms(hand_bytes) -> Optional[int]:
    """C_J1: In J × DS_NO_JOINT, if (top ∈ {2..7}, DS bot, ms_mid_high ≥ 9)
    achievable, take the lowest-top variant with the highest mid_rank_sum.

    PRINCIPLE: oracle drops J off top 76% in this cell — the MOST aggressive
    drop-max profile yet tested. Threshold dropped to 9 (vs Q's T) since
    J's mid_high pool skews lower (max non-J rank is 10).
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "DS_NO_JOINT":
        return None
    nonJ = _enumerate_nonMax_top_DSms(hand_bytes, JACK)
    low_top = [c for c in nonJ if c["top_rank"] <= 7 and c["mid_high"] >= 9]
    if not low_top:
        return None
    low_top.sort(key=lambda c: (c["top_rank"], -c["mid_rank_sum"], -c["bot_pair_high"]))
    best = low_top[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_J_DSnj_take_2top_DSms(hand_bytes) -> Optional[int]:
    """C_J2: In J × DS_NO_JOINT, surgical top=2 + DS bot + ms_mid_high ≥ 9.

    PRINCIPLE: 2-on-top is oracle's BIGGEST specific non-J top in J × DSnj
    at ~27% rate (vs Q's 15%, K's 7%). At J, top=2 is even bigger than
    J-on-top (24%). Mirror of C_Q4 with the most aggressive surface to date.
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "DS_NO_JOINT":
        return None
    nonJ = _enumerate_nonMax_top_DSms(hand_bytes, JACK)
    twos = [c for c in nonJ if c["top_rank"] == 2 and c["mid_high"] >= 9]
    if not twos:
        return None
    twos.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
    best = twos[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_J_DSnj_take_3top_DSms(hand_bytes) -> Optional[int]:
    """C_J3: In J × DS_NO_JOINT, surgical top=3 + DS bot + ms_mid_high ≥ 9.

    PRINCIPLE: 3-on-top is oracle's second-biggest specific drop in J × DSnj
    at ~14%. Combined with C_J2's top=2 (~27%), surgical low-top targeting
    addresses 41% of oracle's drop-J behavior.
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "DS_NO_JOINT":
        return None
    nonJ = _enumerate_nonMax_top_DSms(hand_bytes, JACK)
    threes = [c for c in nonJ if c["top_rank"] == 3 and c["mid_high"] >= 9]
    if not threes:
        return None
    threes.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
    best = threes[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_J_DSnj_drop_J_when_J_in_DSpair(hand_bytes) -> Optional[int]:
    """C_J4: In J × DS_NO_JOINT, when (top=non-J, DS bot containing J as
    part of a suited pair, ms_mid_high ≥ 8) achievable, take it.

    PRINCIPLE: S58 Obs 1 — when best_DS_bot_pair_high == J, oracle picks
    JOINT only 46% (vs 70.6% Q, 83% K, 93% A). The J-in-DS-pair signal
    is the STRONGEST drop-max signal across all max-ranks. Mid_high gate
    relaxed to ≥ 8 since J's pool skews low.
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "DS_NO_JOINT":
        return None
    nonJ = _enumerate_nonMax_top_DSms(hand_bytes, JACK)
    J_pair = [c for c in nonJ if c["bot_pair_high"] == JACK and c["mid_high"] >= 8]
    if not J_pair:
        return None
    J_pair.sort(key=lambda c: (-c["mid_rank_sum"], c["top_rank"]))
    best = J_pair[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_J_DSnj_SSms_when_high(hand_bytes) -> Optional[int]:
    """C_J5: In J × DS_NO_JOINT, switch J-top DS_mu → J-top SS_ms when
    SS_ms mid_high ≥ T. Mirrors C_Q5 / C_K4.

    PRINCIPLE: same as Q-high — oracle picks ms_mid for a sizeable share
    in DSnj. Mid_high gate ≥ T (instead of Q's J) reflects J's lower pool.
    CAUTION: at Q this was −$2/1000h WG; at K it was −$13.
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "DS_NO_JOINT":
        return None
    cfg = _enumerate_max_on_top_configs(hand_bytes, JACK)
    ss_ms = [c for c in cfg if c["bot_profile"] == "SS" and c["mid_suited"]
             and c["mid_high"] >= 10]
    if not ss_ms:
        return None
    ss_ms.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
    best = ss_ms[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# J × MS_ONLY — secondary opportunity
# ----------------------------------------------------------------------

def rule_J_MSonly_drop_J(hand_bytes) -> Optional[int]:
    """C_J6: In J × MS_ONLY, if (top=non-J with rank ≤ 7, ms_mid_high ≥ 9,
    SS or 31 bot) achievable, take it.

    PRINCIPLE: at K × MSonly oracle drops K 22%; at Q × MSonly we expected
    higher (C_Q6 fired 85.8% catastrophically). At J × MSonly oracle is
    expected to drop J at a still-higher rate. Tight gate (top ≤ 7,
    mid_high ≥ 9) tries to avoid the C_K5 / C_Q6 over-fire pattern.
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "MS_ONLY":
        return None
    nonJ = _enumerate_nonMax_top_anyBot_ms(hand_bytes, JACK)
    cands = [c for c in nonJ if c["top_rank"] <= 7 and c["mid_high"] >= 9]
    if not cands:
        return None
    suit_pri = {"SS": 0, "31": 1}
    cands.sort(key=lambda c: (suit_pri.get(c["bot_profile"], 2),
                                c["top_rank"], -c["mid_rank_sum"]))
    best = cands[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# J × DS_NO_JOINT — negative control (4th retrospective HIMID validation)
# ----------------------------------------------------------------------

def rule_J_DSnj_HIBOT_tiebreaker(hand_bytes) -> Optional[int]:
    """C_J7: In J × DS_NO_JOINT, pick J-top + DS bot with highest
    bot_pair_high (HIBOT) instead of Rule 17's HIMID tiebreaker.

    PRINCIPLE: negative control. Expected fourth retrospective validation
    of HIMID design choice (A C10, K C_K6, Q C_Q7 all confirmed HIMID > HIBOT).
    """
    if not _is_J_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_J(hand_bytes) != "DS_NO_JOINT":
        return None
    cfg = _enumerate_max_on_top_configs(hand_bytes, JACK)
    ds = [c for c in cfg if c["bot_profile"] == "DS"]
    if not ds:
        return None
    ds.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
    best = ds[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# Registry for the test runner
CANDIDATES = {
    # J × DS_NO_JOINT (5 candidates — biggest cell)
    "C_J1_DSnj_drop_J_low_top_DSms": (rule_J_DSnj_drop_J_low_top_DSms, "DS_NO_JOINT"),
    "C_J2_DSnj_take_2top_DSms": (rule_J_DSnj_take_2top_DSms, "DS_NO_JOINT"),
    "C_J3_DSnj_take_3top_DSms": (rule_J_DSnj_take_3top_DSms, "DS_NO_JOINT"),
    "C_J4_DSnj_drop_J_when_J_in_DSpair": (rule_J_DSnj_drop_J_when_J_in_DSpair, "DS_NO_JOINT"),
    "C_J5_DSnj_SSms_when_high": (rule_J_DSnj_SSms_when_high, "DS_NO_JOINT"),
    # J × MS_ONLY
    "C_J6_MSonly_drop_J": (rule_J_MSonly_drop_J, "MS_ONLY"),
    # Negative control
    "C_J7_DSnj_HIBOT_tiebreaker": (rule_J_DSnj_HIBOT_tiebreaker, "DS_NO_JOINT"),
}
