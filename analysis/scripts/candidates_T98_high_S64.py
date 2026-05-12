"""
Session 64 — Candidate refinement rules for T/9/8-high cells.

STRUCTURAL INVERSION at T/9/8:
  v52 fires Rules 25/26/27 — ALWAYS-DEFENSIVE (lowest-on-top + DS HIMID, or SS
  fallback). This is the inverse of v52's J/Q/K/A path (max-on-top + DS HIMID).
  So candidates here cannot test "drop max" — that's the baseline. The candidate
  space instead tests:
    - Lowest-on-top tiebreaker refinements (HIBOT vs HIMID, suit choice)
    - Second-lowest-on-top alternative (lift the "floor")
    - Selective max-on-top return at JOINT cells (where structural opportunity
      for max-on-top + DS + ms exists)
    - Gated max-on-top in DSnj (when DS bot pair_high is competitive)
    - DS-vs-SS bot preference (SS_ms over DS_mu when ms_mid is strong)

Baseline = v52_full_high_only_handler. Each candidate returns None to pass
through to v52, or an int setting_idx when it fires.

S58 decision matrix highlights (rows 203-220):
  T × DSnj: TOP 2:34% 3:19% T:11% 4:10% 9:6%. BOT DS:68% SS:25% 31:7%.
            MID suited 60.9% (T moves to mid pair).
  9 × DSnj: TOP 2:41% 3:22% 4:11% etc. 9 rarely on top.
  8 × DSnj: extreme version of 9.

  Implication: oracle keeps T/9/8 on top ~11%/~4%/<3% in DSnj. v52 keeps them
  on top 0%. The 11% T-on-top slice IS the biggest single mis-match — but
  identifying which 11% requires a gate that doesn't over-fire.
"""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Optional, Callable

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from candidates_K_high_S61 import _enumerate_max_on_top_configs  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


# -----------------------------------------------------------------------------
# Cell tagging — generic over max_rank ∈ {10, 9, 8}
# -----------------------------------------------------------------------------

def _is_low_max_no_pair(hand_bytes, max_rank: int) -> bool:
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) or int((rc == 3).sum()) or int((rc == 2).sum()):
        return False
    return int(ranks.max()) == max_rank


def _cell_for_hand(hand_bytes, max_rank: int) -> str:
    """Same definition as drill_high_only_v44_deepdive.cell_for_hand,
    parameterized by max_rank."""
    cfg = _enumerate_max_on_top_configs(hand_bytes, max_rank)
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


def _enumerate_top_at_pos(hand_bytes, top_pos: int):
    """Enumerate the 15 (mid_a, mid_b, bot) splits given a fixed top_pos.
    Returns list of dicts with profile, mid_suited, mid_rank_sum, mid_high,
    bot_pair_high. Generic alternative to _enumerate_max_on_top_configs
    (which forces top=max). Used by lowest-on-top variant candidates."""
    h = np.asarray(hand_bytes, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    others = [j for j in range(7) if j != top_pos]
    configs = []
    for mid_a, mid_b in combinations(others, 2):
        bot_pos = sorted(j for j in others if j not in (mid_a, mid_b))
        bot_suits = [int_suits[p] for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt == [2, 2]:
            prof = "DS"
        elif cnt == [2, 1, 1]:
            prof = "SS"
        elif cnt == [3, 1]:
            prof = "31"
        elif cnt == [4]:
            prof = "4f"
        elif cnt == [1, 1, 1, 1]:
            prof = "RB"
        else:
            prof = "?"
        ms = int_suits[mid_a] == int_suits[mid_b]
        mid_rank_sum = int_ranks[mid_a] + int_ranks[mid_b]
        mid_high = max(int_ranks[mid_a], int_ranks[mid_b])
        by_suit: dict = {}
        for p in bot_pos:
            by_suit.setdefault(int_suits[p], []).append(int_ranks[p])
        bot_pair_h = max((max(rs) for rs in by_suit.values() if len(rs) >= 2),
                          default=0)
        configs.append({
            "top_pos": top_pos, "mid_a": mid_a, "mid_b": mid_b,
            "bot_pos": tuple(bot_pos), "bot_profile": prof,
            "mid_suited": ms, "mid_rank_sum": mid_rank_sum,
            "mid_high": mid_high, "bot_pair_high": bot_pair_h,
        })
    return configs


# -----------------------------------------------------------------------------
# Candidate factories — each parameterized by max_rank ∈ {10, 9, 8}
# -----------------------------------------------------------------------------

def make_rule_DSnj_maxtop_DS_HIMID(max_rank: int) -> Callable:
    """C1: in DSnj, take max-on-top + DS bot + HIMID mid_unsuited
    (mid is unsuited since JOINT is not achievable in DSnj). Always-fires
    inversion of v52's defensive baseline.

    PRINCIPLE: tests whether ANY max-on-top in T/9/8 DSnj is worthwhile.
    Oracle keeps T/9/8 on top ~11%/~4%/<3%. Expected: catastrophic over-fire.
    """
    def rule(hand_bytes):
        if not _is_low_max_no_pair(hand_bytes, max_rank):
            return None
        if _cell_for_hand(hand_bytes, max_rank) != "DS_NO_JOINT":
            return None
        cfg = _enumerate_max_on_top_configs(hand_bytes, max_rank)
        ds = [c for c in cfg if c["bot_profile"] == "DS"]
        if not ds:
            return None
        ds.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
        best = ds[0]
        return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
    return rule


def make_rule_DSnj_maxtop_when_DSpair_geq_max(max_rank: int) -> Callable:
    """C2: in DSnj, gate max-on-top + DS HIMID to only when DS bot pair_high
    == max_rank (i.e., max is in the DS suited pair in bot). This is a
    weird-looking gate — max-on-top while max ALSO in DS bot pair means
    max is duplicated? Wait, no: max is at top_pos, others contain another
    suited pair where the pair_high equals max_rank. But max_rank is unique
    in the hand. So bot_pair_high == max_rank means the DS bot has a suited
    pair with top card = max_rank — impossible since max_rank is at top.

    So this candidate STRUCTURALLY NEVER FIRES at max-on-top. Replace gate
    with: bot_pair_high ≥ max_rank − 2 (a competitive DS bot pair).

    PRINCIPLE: targets the small fraction where keeping max on top is
    right because the DS bot's pair is competitive in absolute terms.
    """
    pair_thresh = max_rank - 2  # competitive DS bot pair
    def rule(hand_bytes):
        if not _is_low_max_no_pair(hand_bytes, max_rank):
            return None
        if _cell_for_hand(hand_bytes, max_rank) != "DS_NO_JOINT":
            return None
        cfg = _enumerate_max_on_top_configs(hand_bytes, max_rank)
        ds = [c for c in cfg if c["bot_profile"] == "DS"
              and c["bot_pair_high"] >= pair_thresh]
        if not ds:
            return None
        ds.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
        best = ds[0]
        return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
    return rule


def make_rule_DSnj_HIBOT_control(max_rank: int) -> Callable:
    """C3: lowest-on-top + DS HIBOT (highest bot_pair_high) instead of v52's
    HIMID. 5th retrospective HIBOT control test.

    PRINCIPLE: A C10 (Rule 14), K C_K6 (Rule 15), Q C_Q7 (Rule 16), J C_J7
    (Rule 17) all confirmed HIMID > HIBOT. This is the FIFTH check, on
    the always-defensive rule family (Rules 25/26/27) where the rule design
    is structurally different. If HIBOT loses again, that's a clean
    cross-family confirmation of HIMID's correctness.
    """
    def rule(hand_bytes):
        if not _is_low_max_no_pair(hand_bytes, max_rank):
            return None
        if _cell_for_hand(hand_bytes, max_rank) != "DS_NO_JOINT":
            return None
        h = np.asarray(hand_bytes, dtype=np.uint8)
        ranks = (h // 4) + 2
        int_ranks = [int(r) for r in ranks]
        lowest_rank = min(int_ranks)
        lowest_pos = int_ranks.index(lowest_rank)
        cfg = _enumerate_top_at_pos(hand_bytes, lowest_pos)
        ds = [c for c in cfg if c["bot_profile"] == "DS"]
        if not ds:
            return None
        ds.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
        best = ds[0]
        return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
    return rule


def make_rule_DSnj_2ndLowest_top(max_rank: int) -> Callable:
    """C4: take second-lowest rank on top + DS HIMID, instead of lowest.
    PRINCIPLE: per S58 row 204 (T × DSnj), oracle picks top 2:34% AND
    3:19%. v52 always picks the absolute-lowest; this candidate tries
    second-lowest. Tests whether the "always lowest" rule is too rigid.
    """
    def rule(hand_bytes):
        if not _is_low_max_no_pair(hand_bytes, max_rank):
            return None
        if _cell_for_hand(hand_bytes, max_rank) != "DS_NO_JOINT":
            return None
        h = np.asarray(hand_bytes, dtype=np.uint8)
        ranks = (h // 4) + 2
        int_ranks = [int(r) for r in ranks]
        sorted_pos = sorted(range(7), key=lambda j: int_ranks[j])
        second_lowest_pos = sorted_pos[1]
        cfg = _enumerate_top_at_pos(hand_bytes, second_lowest_pos)
        ds = [c for c in cfg if c["bot_profile"] == "DS"]
        if ds:
            ds.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
            best = ds[0]
            return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
        ss = [c for c in cfg if c["bot_profile"] == "SS"]
        if ss:
            ss.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
            best = ss[0]
            return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
        return None
    return rule


def make_rule_JOINT_maxtop_DSms(max_rank: int) -> Callable:
    """C5: at JOINT_MED/JOINT_LOW cells, take max-on-top + DS bot + ms_mid
    (joint config) instead of v52's defensive lowest-on-top.

    PRINCIPLE: v52 blanket-defensives at max ∈ {7..10}, but in JOINT cells
    the max-on-top + JOINT structure remains achievable. At higher max
    (A/K/Q/J) joint cells are oracle's preferred play; at low max it's
    unclear. This candidate tests whether v52 should re-introduce max-on-top
    JOINT picks at low max-ranks where structurally available.
    """
    def rule(hand_bytes):
        if not _is_low_max_no_pair(hand_bytes, max_rank):
            return None
        cell = _cell_for_hand(hand_bytes, max_rank)
        if cell not in ("JOINT_MED", "JOINT_LOW"):
            return None
        cfg = _enumerate_max_on_top_configs(hand_bytes, max_rank)
        joint = [c for c in cfg if c["bot_profile"] == "DS" and c["mid_suited"]]
        if not joint:
            return None
        joint.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
        best = joint[0]
        return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
    return rule


def make_rule_DSnj_SSms_when_ms_high(max_rank: int) -> Callable:
    """C6: in DSnj, switch lowest-on-top + DS bot → lowest-on-top + SS bot
    with ms_mid when ms_mid_high ≥ 8. Mirror of C_K4/C_Q5/C_J5 SS_ms pattern
    but applied to the defensive (lowest-on-top) variant.

    PRINCIPLE: at T/9/8 DSnj, S58 says oracle picks ms_mid 60.9% (T) — v52's
    lowest-on-top + DS HIMID picks mu_mid 100%. Switching to SS+ms when
    a strong ms_mid exists may capture some of the suited-mid share.
    CAUTION: at all higher max-ranks the SSms switch lost money. Expected
    negative here too, with the question being whether the magnitude is
    different at the defensive baseline.
    """
    def rule(hand_bytes):
        if not _is_low_max_no_pair(hand_bytes, max_rank):
            return None
        if _cell_for_hand(hand_bytes, max_rank) != "DS_NO_JOINT":
            return None
        h = np.asarray(hand_bytes, dtype=np.uint8)
        ranks = (h // 4) + 2
        int_ranks = [int(r) for r in ranks]
        lowest_pos = int_ranks.index(min(int_ranks))
        cfg = _enumerate_top_at_pos(hand_bytes, lowest_pos)
        ss_ms = [c for c in cfg if c["bot_profile"] == "SS" and c["mid_suited"]
                 and c["mid_high"] >= 8]
        if not ss_ms:
            return None
        ss_ms.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
        best = ss_ms[0]
        return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))
    return rule


# -----------------------------------------------------------------------------
# Registry — one entry per (candidate_family, max_rank, target_cell) test point.
#
# Coverage strategy:
#   - All 6 candidate families tested at T-high (the biggest leak, $12.99 WG).
#   - Best families (C1/C3/C5) mirrored at 9-high to confirm pattern.
#   - HIBOT control mirrored at 8-high as final cross-rank confirmation.
# -----------------------------------------------------------------------------

CANDIDATES = {
    # T-high (max=10), DS_NO_JOINT (n=12,600, $8.03/1000h WG gap)
    "C_T1_DSnj_maxtop_DSmu_HIMID":             (make_rule_DSnj_maxtop_DS_HIMID(10),             "DS_NO_JOINT", 10),
    "C_T2_DSnj_maxtop_when_DSpair_geq_maxM2":  (make_rule_DSnj_maxtop_when_DSpair_geq_max(10),  "DS_NO_JOINT", 10),
    "C_T3_DSnj_HIBOT_control":                 (make_rule_DSnj_HIBOT_control(10),               "DS_NO_JOINT", 10),
    "C_T4_DSnj_2ndLowest_top":                 (make_rule_DSnj_2ndLowest_top(10),               "DS_NO_JOINT", 10),
    "C_T6_DSnj_SSms_when_ms_high":             (make_rule_DSnj_SSms_when_ms_high(10),           "DS_NO_JOINT", 10),
    # T-high, JOINT_MED (n=2,835, $1.82/1000h WG gap)
    "C_T5_JOINT_maxtop_DSms":                  (make_rule_JOINT_maxtop_DSms(10),                "JOINT_MED",   10),
    # 9-high (max=9), DS_NO_JOINT (n=3,150, $1.87/1000h WG gap)
    "C_91_DSnj_maxtop_DSmu_HIMID":             (make_rule_DSnj_maxtop_DS_HIMID(9),              "DS_NO_JOINT", 9),
    "C_93_DSnj_HIBOT_control":                 (make_rule_DSnj_HIBOT_control(9),                "DS_NO_JOINT", 9),
    "C_94_DSnj_2ndLowest_top":                 (make_rule_DSnj_2ndLowest_top(9),                "DS_NO_JOINT", 9),
    "C_95_JOINT_maxtop_DSms":                  (make_rule_JOINT_maxtop_DSms(9),                 "JOINT_MED",   9),
    # 8-high (max=8), DS_NO_JOINT (n=450, $0.26/1000h WG gap)
    "C_81_DSnj_maxtop_DSmu_HIMID":             (make_rule_DSnj_maxtop_DS_HIMID(8),              "DS_NO_JOINT", 8),
    "C_83_DSnj_HIBOT_control":                 (make_rule_DSnj_HIBOT_control(8),                "DS_NO_JOINT", 8),
}
