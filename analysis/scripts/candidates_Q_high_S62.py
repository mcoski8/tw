"""
Session 62 — Candidate refinement rules for Q-high cells.

Each candidate is a function (hand_bytes -> Optional[int]) that returns a
setting_idx when it fires and overrides v52 (= Rule 16 on Q-high since
v52's defensive triggers don't fire for Q-high with s2 > 8), or None to
pass through to v52.

Q-high differs structurally from K-high (S58 decision matrix):
  - Oracle drops Q off top 52% in Q × DS_NO_JOINT (vs K 34%, A 6%).
  - Oracle drops Q off top 20% in Q × JOINT_HIGH (vs K 10%, A 1%).
  - DS bot share in DSnj is 62% (vs K 58%, A 52%).
  - In Q × DSnj, top distribution is Q:48%, 2:15%, J:10%, 3:8%, T:4% —
    top=2 is a much bigger surface than at K (K's top=2 share was 7%).
  - In Q × JOINT_HIGH, mid_high distribution is J:45%, T:15%, 9:13%,
    8:8%, Q:8% — J-on-mid dominates within joints.
  - When best_DS_bot_pair_high == Q, oracle picks JOINT 70.6% (vs 83% K,
    93% A) — i.e. "Q-in-DS-pair" is a STRONGER drop-Q signal than at K.

Top-3 leaky cells (post-Rule-16) per Phase 2 audit (TBD; S58 baseline):
  - DS_NO_JOINT  (n=94,500; ~$87/1000h WG remaining gap likely; ratio
                  from K's $105.94 scaled by Q's structural drop-Q
                  aggressiveness)
  - DS_NO_MAXTOP (n=20,160; ~$8/1000h WG)
  - MS_ONLY      (n=13,440; ~$5/1000h WG)

Reuses helpers from candidates_K_high_S61.py (already max_rank parameterized):
  - _enumerate_max_on_top_configs(hand, max_rank)
  - _enumerate_nonMax_top_DSms(hand, max_rank)
  - _enumerate_nonMax_top_anyBot_ms(hand, max_rank)

Naming: rule_Q_<cell>_<intent>(hand) -> Optional[int].
"""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
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

from candidates_K_high_S61 import (  # noqa: E402
    _enumerate_max_on_top_configs,
    _enumerate_nonMax_top_DSms,
    _enumerate_nonMax_top_anyBot_ms,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

QUEEN = 12


# ----------------------------------------------------------------------
# Q-high cell tagging (mirrors _cell_for_hand_K with QUEEN substituted)
# ----------------------------------------------------------------------

def _is_Q_high_no_pair(hand_bytes) -> bool:
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) or int((rc == 3).sum()) or int((rc == 2).sum()):
        return False
    return int(ranks.max()) == QUEEN


def _cell_for_hand_Q(hand_bytes) -> str:
    """Same definition as drill_high_only_v44_deepdive.cell_for_hand,
    specialized to Q-high (max_rank=12)."""
    cfg = _enumerate_max_on_top_configs(hand_bytes, QUEEN)
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
# Q × DS_NO_JOINT — biggest opportunity (drop-Q play 52% per oracle)
# ----------------------------------------------------------------------

def rule_Q_DSnj_drop_Q_low_top_DSms(hand_bytes) -> Optional[int]:
    """C_Q1: In Q × DS_NO_JOINT, if (top ∈ {2..7}, DS bot, ms_mid_high ≥ T)
    achievable, take the lowest-top variant with the highest mid_rank_sum.

    PRINCIPLE: oracle drops Q off top 52% in this cell, with top
    distribution {2:15%, 3:8%, 4:?%, J:10%, T:4%}. The low-top portion
    (top ≤ 7) is ~30% of all Q × DSnj. Tight gate: require ms_mid_high
    ≥ T (one rank softer than C_K1's J bar since Q's mid_high pool
    skews lower than K's).
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "DS_NO_JOINT":
        return None
    nonQ = _enumerate_nonMax_top_DSms(hand_bytes, QUEEN)
    low_top = [c for c in nonQ if c["top_rank"] <= 7 and c["mid_high"] >= 10]
    if not low_top:
        return None
    low_top.sort(key=lambda c: (c["top_rank"], -c["mid_rank_sum"], -c["bot_pair_high"]))
    best = low_top[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_Q_DSnj_take_Jtop_DSms(hand_bytes) -> Optional[int]:
    """C_Q2: In Q × DS_NO_JOINT, prefer (top=J, DS bot, ms_mid_high ≥ T).

    PRINCIPLE: oracle picks J on top 10% in Q × DSnj — the most common
    non-Q non-low-card top. Mirror of C_K3 (which targeted Q-on-top in K
    × DSnj at 12%). J is the natural drop-Q-by-one-rank pick and pairs
    well with high ms_mid.
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "DS_NO_JOINT":
        return None
    nonQ = _enumerate_nonMax_top_DSms(hand_bytes, QUEEN)
    jtop = [c for c in nonQ if c["top_rank"] == 11 and c["mid_high"] >= 10]
    if not jtop:
        return None
    jtop.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
    best = jtop[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_Q_DSnj_drop_Q_when_Q_in_DSpair(hand_bytes) -> Optional[int]:
    """C_Q3: In Q × DS_NO_JOINT, when a (top=non-Q, DS bot containing Q
    as part of a suited pair, ms_mid_high ≥ 9) is achievable, take it.

    PRINCIPLE: S58 Observation 1 — when best_DS_bot_pair_high == Q,
    oracle picks JOINT only 70.6% (vs 83% K, 93% A). The Q-in-DS-pair
    signal is STRONGER at Q than K. Mirror of C_K2 with same gate.
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "DS_NO_JOINT":
        return None
    nonQ = _enumerate_nonMax_top_DSms(hand_bytes, QUEEN)
    Q_pair = [c for c in nonQ if c["bot_pair_high"] == QUEEN and c["mid_high"] >= 9]
    if not Q_pair:
        return None
    Q_pair.sort(key=lambda c: (-c["mid_rank_sum"], c["top_rank"]))
    best = Q_pair[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_Q_DSnj_drop_Q_to_2top_DSms(hand_bytes) -> Optional[int]:
    """C_Q4: In Q × DS_NO_JOINT, if (top=2, DS bot, ms_mid_high ≥ T)
    achievable, take it.

    PRINCIPLE: 2-on-top is oracle's BIGGEST specific non-Q top in
    Q × DSnj at 15% rate (vs K's 7%). Surgical targeting of top=2 with
    a strong ms_mid is the cleanest gate aligned with the oracle's
    documented "defensive 2-on-top" play at Q-high.
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "DS_NO_JOINT":
        return None
    nonQ = _enumerate_nonMax_top_DSms(hand_bytes, QUEEN)
    twos = [c for c in nonQ if c["top_rank"] == 2 and c["mid_high"] >= 10]
    if not twos:
        return None
    twos.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
    best = twos[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_Q_DSnj_SSms_when_high(hand_bytes) -> Optional[int]:
    """C_Q5: In Q × DS_NO_JOINT, switch Q-top DS_mu → Q-top SS_ms when
    SS_ms mid_high ≥ J. Mirrors C_K4 / A-high C2.

    PRINCIPLE: oracle picks ms_mid 56.4% in Q × DSnj (vs K's 51%) —
    the largest ms_mid share of the three high zones. Rule 16 (= v52
    on Q-high) is Q-top + DS + mu_mid; switching to SS_ms on a tight
    quality gate might capture some of the 56% gap. CAUTION: at K
    this candidate (C_K4) was net-negative (−$13/1000h WG); Q's
    higher ms_mid share doesn't necessarily mean the gate picks the
    right subset.
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "DS_NO_JOINT":
        return None
    cfg = _enumerate_max_on_top_configs(hand_bytes, QUEEN)
    ss_ms = [c for c in cfg if c["bot_profile"] == "SS" and c["mid_suited"]
             and c["mid_high"] >= 11]
    if not ss_ms:
        return None
    ss_ms.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
    best = ss_ms[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# Q × MS_ONLY — secondary opportunity (drop-Q rate higher than K)
# ----------------------------------------------------------------------

def rule_Q_MSonly_drop_Q(hand_bytes) -> Optional[int]:
    """C_Q6: In Q × MS_ONLY, if (top=non-Q with rank ≤ 7, ms_mid_high ≥ T,
    SS or 31 bot) achievable, take it.

    PRINCIPLE: at K × MSonly oracle drops K 22%; at Q × MSonly oracle
    is expected to drop Q at a HIGHER rate (extrapolating the pattern
    A 2% → K 22% → Q ~30%+). Tighter gate than C_K5 (top ≤ 7,
    mid_high ≥ T) to learn from K's 82.7% over-fire catastrophe.
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "MS_ONLY":
        return None
    nonQ = _enumerate_nonMax_top_anyBot_ms(hand_bytes, QUEEN)
    cands = [c for c in nonQ if c["top_rank"] <= 7 and c["mid_high"] >= 10]
    if not cands:
        return None
    suit_pri = {"SS": 0, "31": 1}
    cands.sort(key=lambda c: (suit_pri.get(c["bot_profile"], 2),
                                c["top_rank"], -c["mid_rank_sum"]))
    best = cands[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# Q × DS_NO_JOINT — negative control (mirror of A-high C10 / K-high C_K6)
# ----------------------------------------------------------------------

def rule_Q_DSnj_HIBOT_tiebreaker(hand_bytes) -> Optional[int]:
    """C_Q7: In Q × DS_NO_JOINT, pick Q-top + DS bot with highest
    bot_pair_high (HIBOT) instead of Rule 16's HIMID tiebreaker.

    PRINCIPLE: negative control. C10 confirmed Rule 14's HIMID on A;
    C_K6 confirmed Rule 15's HIMID on K. Same test for Rule 16.
    Expected to fail (HIMID > HIBOT) — third retrospective validation
    of the HIMID design choice.
    """
    if not _is_Q_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_Q(hand_bytes) != "DS_NO_JOINT":
        return None
    cfg = _enumerate_max_on_top_configs(hand_bytes, QUEEN)
    ds = [c for c in cfg if c["bot_profile"] == "DS"]
    if not ds:
        return None
    ds.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
    best = ds[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# Registry for the test runner
CANDIDATES = {
    # Q × DS_NO_JOINT (5 candidates — biggest cell)
    "C_Q1_DSnj_drop_Q_low_top_DSms": (rule_Q_DSnj_drop_Q_low_top_DSms, "DS_NO_JOINT"),
    "C_Q2_DSnj_take_Jtop_DSms": (rule_Q_DSnj_take_Jtop_DSms, "DS_NO_JOINT"),
    "C_Q3_DSnj_drop_Q_when_Q_in_DSpair": (rule_Q_DSnj_drop_Q_when_Q_in_DSpair, "DS_NO_JOINT"),
    "C_Q4_DSnj_drop_Q_to_2top_DSms": (rule_Q_DSnj_drop_Q_to_2top_DSms, "DS_NO_JOINT"),
    "C_Q5_DSnj_SSms_when_high": (rule_Q_DSnj_SSms_when_high, "DS_NO_JOINT"),
    # Q × MS_ONLY
    "C_Q6_MSonly_drop_Q": (rule_Q_MSonly_drop_Q, "MS_ONLY"),
    # Negative control
    "C_Q7_DSnj_HIBOT_tiebreaker": (rule_Q_DSnj_HIBOT_tiebreaker, "DS_NO_JOINT"),
}
