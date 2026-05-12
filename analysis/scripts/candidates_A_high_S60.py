"""
Session 60 — Candidate refinement rules for A-high cells.

Each candidate is a function (hand_bytes -> Optional[int]) that returns a
setting_idx when it fires and overrides v52 (= Rule 14 on A-high), or None
to pass through to v52.

Candidates target the top-3 leaky A-high cells (after Rule 14):
- DS_NO_JOINT  (n=415,800; $161.7/1000h WG remaining gap)
- DS_NO_MAXTOP (n=88,704; $55.1/1000h WG remaining gap)
- MS_ONLY      (n=59,136; $35.4/1000h WG remaining gap)

Naming: rule_A_<cell>_<intent>(hand) → Optional[int].
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

from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

ACE = 14


# ----------------------------------------------------------------------
# Helpers — enumerate A-on-top configs by bot suit profile
# ----------------------------------------------------------------------

def _enumerate_A_on_top_configs(hand_bytes):
    """For an A-high hand, enumerate the 15 (mid_a, mid_b) splits with A on
    top. For each, classify the bot's suit profile and the mid's suited-ness.

    Returns list of dicts:
      {ace_pos, mid_a, mid_b, bot_pos, bot_profile, mid_suited,
       mid_rank_sum, mid_high, bot_pair_high}

    bot_profile ∈ {"DS", "SS", "31", "RB", "4f"}
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]

    max_r = max(int_ranks)
    if max_r != ACE:
        return []
    ace_pos = int_ranks.index(ACE)
    others = [j for j in range(7) if j != ace_pos]

    configs = []
    for mid_a, mid_b in combinations(others, 2):
        bot_pos = [j for j in others if j not in (mid_a, mid_b)]
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
        # bot_pair_high: max higher-of-pair across bot's suited pairs.
        by_suit: dict = {}
        for p in bot_pos:
            by_suit.setdefault(int_suits[p], []).append(int_ranks[p])
        bot_pair_h = 0
        for s, rs in by_suit.items():
            if len(rs) >= 2:
                top = max(rs)
                if top > bot_pair_h:
                    bot_pair_h = top
        configs.append({
            "ace_pos": ace_pos, "mid_a": mid_a, "mid_b": mid_b,
            "bot_pos": tuple(bot_pos), "bot_profile": prof,
            "mid_suited": ms, "mid_rank_sum": mid_rank_sum,
            "mid_high": mid_high, "bot_pair_high": bot_pair_h,
        })
    return configs


def _is_A_high_no_pair(hand_bytes) -> bool:
    """True iff hand is A-high with 7 distinct ranks."""
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) or int((rc == 3).sum()) or int((rc == 2).sum()):
        return False
    return int(ranks.max()) == ACE


def _cell_for_hand(hand_bytes) -> str:
    """Return structural cell for an A-high hand. Same definition as the
    drill's cell_for_hand."""
    cfg = _enumerate_A_on_top_configs(hand_bytes)
    n_joint = sum(1 for c in cfg if c["bot_profile"] == "DS" and c["mid_suited"])
    n_DS_top = sum(1 for c in cfg if c["bot_profile"] == "DS")
    n_ms_top = sum(1 for c in cfg if c["mid_suited"])

    h = np.asarray(hand_bytes, dtype=np.uint8)
    suits = h & 3
    # Count DS-anywhere (top doesn't have to be A): C(7,4) subsets.
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


def _best_SSms_pick(configs) -> Optional[int]:
    """Among A-on-top + SS bot + ms_mid configs, return setting_idx of the
    one with highest mid_rank_sum (tiebreaker: highest mid_high). None if no
    such config exists."""
    candidates = [c for c in configs if c["bot_profile"] == "SS" and c["mid_suited"]]
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
    best = candidates[0]
    return int(_setting_index_from_tmb(best["ace_pos"], best["mid_a"], best["mid_b"]))


def _best_31ms_pick(configs) -> Optional[int]:
    candidates = [c for c in configs if c["bot_profile"] == "31" and c["mid_suited"]]
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
    best = candidates[0]
    return int(_setting_index_from_tmb(best["ace_pos"], best["mid_a"], best["mid_b"]))


def _best_4fms_pick(configs) -> Optional[int]:
    candidates = [c for c in configs if c["bot_profile"] == "4f" and c["mid_suited"]]
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
    best = candidates[0]
    return int(_setting_index_from_tmb(best["ace_pos"], best["mid_a"], best["mid_b"]))


def _best_DSmu_pick(configs) -> Optional[int]:
    """Rule 14's pick: highest mid_rank_sum among A-top + DS bot configs."""
    candidates = [c for c in configs if c["bot_profile"] == "DS"]
    if not candidates:
        return None
    candidates.sort(key=lambda c: -c["mid_rank_sum"])
    best = candidates[0]
    return int(_setting_index_from_tmb(best["ace_pos"], best["mid_a"], best["mid_b"]))


def _ms_mid_high(configs, bot_profile) -> int:
    """Best mid_high among A-top + <bot_profile> + ms_mid configs. 0 if none."""
    candidates = [c for c in configs
                  if c["bot_profile"] == bot_profile and c["mid_suited"]]
    if not candidates:
        return 0
    return max(c["mid_high"] for c in candidates)


# ----------------------------------------------------------------------
# DS_NO_JOINT candidates — biggest opportunity ($161.7/1k WG remaining)
# ----------------------------------------------------------------------

def rule_A_DSnj_take_SSms_any(hand_bytes) -> Optional[int]:
    """C1: In A × DS_NO_JOINT, if A-top + SS bot + ms_mid achievable, take it
    (highest mid_rank_sum). Fires regardless of mid_high quality.

    PRINCIPLE: oracle picks tA_SS_ms 27.9% of cell — Rule 14 picks tA_DS_mu
    100%. Switching to SS+ms whenever achievable should capture a large
    fraction of that 27.9% population.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_JOINT":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    return _best_SSms_pick(configs)


def rule_A_DSnj_take_SSms_J(hand_bytes) -> Optional[int]:
    """C2: Same as C1 but only fire when SS+ms_mid mid_high ≥ J.

    PRINCIPLE: gate the SS_ms switch on mid quality. Avoids switching when
    the suited mid is low (e.g., 5-6 suited) and DS bot pair has more value.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_JOINT":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    if _ms_mid_high(configs, "SS") < 11:
        return None
    return _best_SSms_pick(configs)


def rule_A_DSnj_take_SSms_T(hand_bytes) -> Optional[int]:
    """C3: Same as C1 but only fire when SS+ms_mid mid_high ≥ T.

    PRINCIPLE: looser quality gate than C2; trade more population for
    potentially less-clean lift.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_JOINT":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    if _ms_mid_high(configs, "SS") < 10:
        return None
    return _best_SSms_pick(configs)


def rule_A_DSnj_take_SSms_beats_DSpair(hand_bytes) -> Optional[int]:
    """C4: In A × DS_NO_JOINT, prefer SS+ms_mid over DS+mu_mid when SS_ms
    mid_high > best DS bot pair_high.

    PRINCIPLE: a high suited-mid card (e.g., J or Q suited mid) beats a low
    DS bot pair (e.g., 5-pair-with-side-pair). Compares quality directly.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_JOINT":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    ss_ms = [c for c in configs if c["bot_profile"] == "SS" and c["mid_suited"]]
    ds = [c for c in configs if c["bot_profile"] == "DS"]
    if not ss_ms or not ds:
        return None
    best_ss_ms_mid_high = max(c["mid_high"] for c in ss_ms)
    best_ds_pair_high = max(c["bot_pair_high"] for c in ds)
    if best_ss_ms_mid_high > best_ds_pair_high:
        return _best_SSms_pick(configs)
    return None


# ----------------------------------------------------------------------
# DS_NO_MAXTOP candidates (n=88,704; $55.1/1k WG gap remaining)
# ----------------------------------------------------------------------

def rule_A_DSnm_take_SSms_any(hand_bytes) -> Optional[int]:
    """C5: In A × DS_NO_MAXTOP, prefer A-top + SS bot + ms_mid over Rule 14's
    A-top + SS+mu pick (Rule 14 falls back to SS+mu in this cell)."""
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_MAXTOP":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    return _best_SSms_pick(configs)


def rule_A_DSnm_take_31ms_when_no_SSms(hand_bytes) -> Optional[int]:
    """C6: In A × DS_NO_MAXTOP, if no SS+ms_mid available, try 31+ms_mid.

    PRINCIPLE: oracle picks 31 bot 30% in DS_NO_MAXTOP (S58 matrix). Rule 14
    falls back to SS+HIMID (or None if no SS) and ignores 31 bot entirely.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_MAXTOP":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    if any(c["bot_profile"] == "SS" and c["mid_suited"] for c in configs):
        return None  # let SSms candidate or v52 handle
    return _best_31ms_pick(configs)


# ----------------------------------------------------------------------
# MS_ONLY candidates (n=59,136; $35.4/1k WG gap)
# ----------------------------------------------------------------------

def rule_A_MSonly_take_31ms_when_no_SSms(hand_bytes) -> Optional[int]:
    """C7: In A × MS_ONLY, if A-top SS+ms not achievable but 31+ms is,
    take 31+ms HIMID instead of Rule 14's fallback.

    PRINCIPLE: oracle picks 31 bot 41% in MS_ONLY (S58 matrix). Rule 14
    picks SS_HIMID where available; falls through where neither DS nor SS.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "MS_ONLY":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    if any(c["bot_profile"] == "SS" and c["mid_suited"] for c in configs):
        return None
    return _best_31ms_pick(configs)


def rule_A_MSonly_take_31ms_any(hand_bytes) -> Optional[int]:
    """C8: In A × MS_ONLY, take A-top + 31+ms whenever achievable (even if
    SS+ms also achievable). Tests whether 31_ms is just-generally better
    than SS+HIMID-mu in this cell."""
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "MS_ONLY":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    return _best_31ms_pick(configs)


# ----------------------------------------------------------------------
# Second pass — informed by C1-C8 null results.
# Lesson: switching DS→SS+ms whenever achievable is net-negative. Try (a)
# the "drop A off top" alternative oracle takes 2.1% in DSnj, and (b) a
# within-class Rule-14-tiebreaker variant (HIBOT instead of HIMID).
# ----------------------------------------------------------------------

def _enumerate_nonA_top_DSms(hand_bytes):
    """Enumerate configs with (top=non-A rank, DS bot, ms_mid). A may be in
    bot or mid. Returns list of dicts with top_pos, top_rank, mid_a, mid_b,
    mid_high, bot_pair_high."""
    h = np.asarray(hand_bytes, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    max_r = max(int_ranks)
    if max_r != ACE:
        return []
    ace_pos = int_ranks.index(ACE)

    configs = []
    for top_pos in range(7):
        if top_pos == ace_pos:
            continue
        others = [j for j in range(7) if j != top_pos]
        for mid_a, mid_b in combinations(others, 2):
            if int_suits[mid_a] != int_suits[mid_b]:
                continue
            bot_pos = [j for j in others if j not in (mid_a, mid_b)]
            bot_suits = [int_suits[p] for p in bot_pos]
            cnt = sorted(Counter(bot_suits).values(), reverse=True)
            if cnt != [2, 2]:
                continue
            by_suit: dict = {}
            for p in bot_pos:
                by_suit.setdefault(int_suits[p], []).append(int_ranks[p])
            bot_pair_h = 0
            for s, rs in by_suit.items():
                if len(rs) >= 2:
                    top = max(rs)
                    if top > bot_pair_h:
                        bot_pair_h = top
            mid_high = max(int_ranks[mid_a], int_ranks[mid_b])
            configs.append({
                "top_pos": top_pos, "top_rank": int_ranks[top_pos],
                "mid_a": mid_a, "mid_b": mid_b,
                "bot_pos": tuple(bot_pos),
                "mid_high": mid_high,
                "mid_rank_sum": int_ranks[mid_a] + int_ranks[mid_b],
                "bot_pair_high": bot_pair_h,
            })
    return configs


def rule_A_DSnj_drop_A_for_AK_DSms(hand_bytes) -> Optional[int]:
    """C9: In A × DS_NO_JOINT, if (top=non-A, DS bot containing A as part of
    a high suited pair (pair_high ≥ J), ms_mid) is achievable, take it.

    PRINCIPLE: oracle picks tK_DS_ms 2.1% in DSnj; that subset has A in the
    bot as a suited pair (e.g., A-K or A-Q suited). Gate on pair_high ≥ J to
    avoid firing when A pairs with a low card.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_JOINT":
        return None
    nonA = _enumerate_nonA_top_DSms(hand_bytes)
    high_pair = [c for c in nonA if c["bot_pair_high"] >= 11]
    if not high_pair:
        return None
    high_pair.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
    best = high_pair[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_A_DSnj_HIBOT_tiebreaker(hand_bytes) -> Optional[int]:
    """C10: In A × DS_NO_JOINT, pick A-top + DS bot with highest bot_pair_high
    (HIBOT tiebreaker) instead of Rule 14's highest mid_rank_sum (HIMID).

    PRINCIPLE: within-class mismatch (tA_DS_mu → tA_DS_mu) covers 65,080
    hands at $3,149/cell mean regret. Rule 14's HIMID is one tiebreaker;
    HIBOT (favoring strongest bot pair) is the other. Test which is better.
    """
    if not _is_A_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand(hand_bytes) != "DS_NO_JOINT":
        return None
    configs = _enumerate_A_on_top_configs(hand_bytes)
    ds = [c for c in configs if c["bot_profile"] == "DS"]
    if not ds:
        return None
    ds.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
    best = ds[0]
    return int(_setting_index_from_tmb(best["ace_pos"], best["mid_a"], best["mid_b"]))


# Registry for the test runner
CANDIDATES = {
    # DS_NO_JOINT
    "C1_DSnj_SSms_any": (rule_A_DSnj_take_SSms_any, "DS_NO_JOINT"),
    "C2_DSnj_SSms_J": (rule_A_DSnj_take_SSms_J, "DS_NO_JOINT"),
    "C3_DSnj_SSms_T": (rule_A_DSnj_take_SSms_T, "DS_NO_JOINT"),
    "C4_DSnj_SSms_beats_DSpair": (rule_A_DSnj_take_SSms_beats_DSpair, "DS_NO_JOINT"),
    # DS_NO_MAXTOP
    "C5_DSnm_SSms_any": (rule_A_DSnm_take_SSms_any, "DS_NO_MAXTOP"),
    "C6_DSnm_31ms_when_no_SSms": (rule_A_DSnm_take_31ms_when_no_SSms, "DS_NO_MAXTOP"),
    # MS_ONLY
    "C7_MSonly_31ms_when_no_SSms": (rule_A_MSonly_take_31ms_when_no_SSms, "MS_ONLY"),
    "C8_MSonly_31ms_any": (rule_A_MSonly_take_31ms_any, "MS_ONLY"),
    # Second pass (S60 informed retry)
    "C9_DSnj_drop_A_for_AK_DSms": (rule_A_DSnj_drop_A_for_AK_DSms, "DS_NO_JOINT"),
    "C10_DSnj_HIBOT_tiebreaker": (rule_A_DSnj_HIBOT_tiebreaker, "DS_NO_JOINT"),
}
