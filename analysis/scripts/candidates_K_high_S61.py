"""
Session 61 — Candidate refinement rules for K-high cells.

Each candidate is a function (hand_bytes -> Optional[int]) that returns a
setting_idx when it fires and overrides v52 (= Rule 15 on K-high since
v52's defensive triggers don't fire for K-high with s2 > 8), or None to
pass through to v52.

K-high differs structurally from A-high (S58 decision matrix):
  - Oracle drops K off top 34% in K × DS_NO_JOINT (vs 6% at A).
  - Oracle drops K off top 22% in K × MS_ONLY (vs 2% at A).
  - DS bot share in DS_NO_JOINT is 58% (vs 52% at A).
  - When best_DS_bot_pair_high == K (i.e., K is suited in the DS bot),
    oracle picks JOINT only 83% (vs 93%+ when DS_pair_high < K).
    This is the structural axis: "K as suited bot pair" is a signal to
    drop K off top.

Top-3 leaky cells (post-Rule-15) per Phase 2 audit (TBD; S58 baseline):
  - DS_NO_JOINT  (n=207,900; ≥$87/1000h WG remaining gap likely)
  - DS_NO_MAXTOP (n=44,352; ~$17/1000h WG)
  - MS_ONLY      (n=29,568; ~$10/1000h WG)

Naming: rule_K_<cell>_<intent>(hand) -> Optional[int].
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

KING = 13


# ----------------------------------------------------------------------
# Helpers — enumerate K-on-top configs by bot suit profile
# ----------------------------------------------------------------------

def _enumerate_max_on_top_configs(hand_bytes, max_rank: int):
    """For a hand with max == max_rank, enumerate the 15 (mid_a, mid_b)
    splits with max-on-top. Classify the bot's suit profile and the mid's
    suited-ness.

    Returns list of dicts:
      {top_pos, mid_a, mid_b, bot_pos, bot_profile, mid_suited,
       mid_rank_sum, mid_high, bot_pair_high}
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    if max(int_ranks) != max_rank:
        return []
    top_pos = int_ranks.index(max_rank)
    others = [j for j in range(7) if j != top_pos]
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
            "top_pos": top_pos, "mid_a": mid_a, "mid_b": mid_b,
            "bot_pos": tuple(bot_pos), "bot_profile": prof,
            "mid_suited": ms, "mid_rank_sum": mid_rank_sum,
            "mid_high": mid_high, "bot_pair_high": bot_pair_h,
        })
    return configs


def _enumerate_nonMax_top_DSms(hand_bytes, max_rank: int):
    """Enumerate (top=non-max, DS bot, ms_mid) configs. The max-rank may
    sit in bot or mid (most useful when max is in the DS bot pair).

    Returns list of dicts: {top_pos, top_rank, mid_a, mid_b, mid_high,
    mid_rank_sum, bot_pair_high, max_in_bot}.
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    if max(int_ranks) != max_rank:
        return []
    max_pos = int_ranks.index(max_rank)
    configs = []
    for top_pos in range(7):
        if top_pos == max_pos:
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
            max_in_bot = max_pos in bot_pos
            configs.append({
                "top_pos": top_pos, "top_rank": int_ranks[top_pos],
                "mid_a": mid_a, "mid_b": mid_b,
                "bot_pos": tuple(bot_pos),
                "mid_high": mid_high,
                "mid_rank_sum": int_ranks[mid_a] + int_ranks[mid_b],
                "bot_pair_high": bot_pair_h,
                "max_in_bot": max_in_bot,
            })
    return configs


def _enumerate_nonMax_top_anyBot_ms(hand_bytes, max_rank: int):
    """Enumerate (top=non-max, ANY bot, ms_mid) configs — used by MS_ONLY
    cell where DS bot is unavailable by construction.

    Returns list with bot_profile included.
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    if max(int_ranks) != max_rank:
        return []
    max_pos = int_ranks.index(max_rank)
    configs = []
    for top_pos in range(7):
        if top_pos == max_pos:
            continue
        others = [j for j in range(7) if j != top_pos]
        for mid_a, mid_b in combinations(others, 2):
            if int_suits[mid_a] != int_suits[mid_b]:
                continue
            bot_pos = [j for j in others if j not in (mid_a, mid_b)]
            bot_suits = [int_suits[p] for p in bot_pos]
            cnt = sorted(Counter(bot_suits).values(), reverse=True)
            if cnt == [2, 2]:
                prof = "DS"
            elif cnt == [2, 1, 1]:
                prof = "SS"
            elif cnt == [3, 1]:
                prof = "31"
            else:
                continue  # skip 4f / RB for now
            mid_high = max(int_ranks[mid_a], int_ranks[mid_b])
            configs.append({
                "top_pos": top_pos, "top_rank": int_ranks[top_pos],
                "mid_a": mid_a, "mid_b": mid_b,
                "bot_pos": tuple(bot_pos), "bot_profile": prof,
                "mid_high": mid_high,
                "mid_rank_sum": int_ranks[mid_a] + int_ranks[mid_b],
            })
    return configs


def _is_K_high_no_pair(hand_bytes) -> bool:
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return False
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) or int((rc == 3).sum()) or int((rc == 2).sum()):
        return False
    return int(ranks.max()) == KING


def _cell_for_hand_K(hand_bytes) -> str:
    """Same definition as drill_high_only_v44_deepdive.cell_for_hand,
    specialized to K-high."""
    cfg = _enumerate_max_on_top_configs(hand_bytes, KING)
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
# K × DS_NO_JOINT — biggest opportunity (drop-K play 34% per oracle)
# ----------------------------------------------------------------------

def rule_K_DSnj_drop_K_low_top_DSms(hand_bytes) -> Optional[int]:
    """C_K1: In K × DS_NO_JOINT, if (top ∈ {2..7}, DS bot, ms_mid_high ≥ J)
    achievable, take the lowest-top variant with the highest mid_rank_sum.

    PRINCIPLE: oracle drops K off top 34% in this cell, picking top in
    {2:7%, 3:3%, 4:?%}. Among drops, the typical winner has DS bot + ms
    mid + low top. Tight gate: require ms_mid_high ≥ J so we only fire
    when the alt mid is actually competitive.
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "DS_NO_JOINT":
        return None
    nonK = _enumerate_nonMax_top_DSms(hand_bytes, KING)
    low_top = [c for c in nonK if c["top_rank"] <= 7 and c["mid_high"] >= 11]
    if not low_top:
        return None
    low_top.sort(key=lambda c: (c["top_rank"], -c["mid_rank_sum"], -c["bot_pair_high"]))
    best = low_top[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_K_DSnj_drop_K_when_K_in_DSpair(hand_bytes) -> Optional[int]:
    """C_K2: In K × DS_NO_JOINT, if a (top=non-K, DS bot containing K as
    part of a suited pair, ms_mid) is achievable, take it.

    PRINCIPLE: S58 Observation 1 — when best_DS_bot_pair_high == max_rank,
    oracle picks DS_NONJOINT with K-in-bot-pair more often. Tighter gate
    than C_K1 because the structural axis is precise: "K becomes a suited
    pair in the DS bot."
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "DS_NO_JOINT":
        return None
    nonK = _enumerate_nonMax_top_DSms(hand_bytes, KING)
    K_pair = [c for c in nonK if c["bot_pair_high"] == KING and c["mid_high"] >= 9]
    if not K_pair:
        return None
    K_pair.sort(key=lambda c: (-c["mid_rank_sum"], c["top_rank"]))
    best = K_pair[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_K_DSnj_take_Qtop_DSms(hand_bytes) -> Optional[int]:
    """C_K3: In K × DS_NO_JOINT, prefer (top=Q, DS bot, ms_mid_high ≥ J).

    PRINCIPLE: oracle picks Q on top 12% in K × DSnj — the most common
    non-K top. Targeting Q-on-top specifically matches a known oracle
    move and is a tighter alternative to C_K1's "anything ≤ 7" gate.
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "DS_NO_JOINT":
        return None
    nonK = _enumerate_nonMax_top_DSms(hand_bytes, KING)
    qtop = [c for c in nonK if c["top_rank"] == 12 and c["mid_high"] >= 11]
    if not qtop:
        return None
    qtop.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
    best = qtop[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


def rule_K_DSnj_SSms_when_high(hand_bytes) -> Optional[int]:
    """C_K4: In K × DS_NO_JOINT, switch K-top DS_mu → K-top SS_ms when
    SS_ms mid_high ≥ J. Mirrors A-high C2/C3 but for K.

    PRINCIPLE: oracle picks ms_mid 51% in K × DSnj (vs Rule 15's 0% —
    Rule 15 is K-top + DS bot HIMID, mid_unsuited). Switching to SS_ms
    on a tight quality gate may capture some of the 51% gap. CAUTION:
    A-high analog (C2 with mid_high ≥ J) was net-negative; K may differ.
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "DS_NO_JOINT":
        return None
    cfg = _enumerate_max_on_top_configs(hand_bytes, KING)
    ss_ms = [c for c in cfg if c["bot_profile"] == "SS" and c["mid_suited"]
             and c["mid_high"] >= 11]
    if not ss_ms:
        return None
    ss_ms.sort(key=lambda c: (-c["mid_rank_sum"], -c["mid_high"]))
    best = ss_ms[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# K × MS_ONLY — secondary opportunity (drop-K 22%)
# ----------------------------------------------------------------------

def rule_K_MSonly_drop_K(hand_bytes) -> Optional[int]:
    """C_K5: In K × MS_ONLY, if (top=non-K with rank ≤ 7, ms_mid_high ≥ J,
    SS or 31 bot) achievable, take it (lowest top tiebroken by mid_rank_sum).

    PRINCIPLE: oracle drops K off top 22% in K × MSonly (vs 2% at A);
    v52 keeps K on top ~97%. The strict tight gate (low top + strong ms
    mid) tries to match oracle's actual drop-K behavior.
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "MS_ONLY":
        return None
    nonK = _enumerate_nonMax_top_anyBot_ms(hand_bytes, KING)
    cands = [c for c in nonK if c["top_rank"] <= 7 and c["mid_high"] >= 11]
    if not cands:
        return None
    # Prefer SS bot first, then 31, then by lowest top + highest mid_rank_sum
    suit_pri = {"SS": 0, "31": 1}
    cands.sort(key=lambda c: (suit_pri.get(c["bot_profile"], 2),
                                c["top_rank"], -c["mid_rank_sum"]))
    best = cands[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# K × DS_NO_JOINT — negative control (mirror of A-high C10)
# ----------------------------------------------------------------------

def rule_K_DSnj_HIBOT_tiebreaker(hand_bytes) -> Optional[int]:
    """C_K6: In K × DS_NO_JOINT, pick K-top + DS bot with highest
    bot_pair_high (HIBOT) instead of Rule 15's HIMID tiebreaker.

    PRINCIPLE: negative control. C10 confirmed Rule 14's HIMID design
    on A-high; same test for K. Expected to fail (HIMID > HIBOT).
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "DS_NO_JOINT":
        return None
    cfg = _enumerate_max_on_top_configs(hand_bytes, KING)
    ds = [c for c in cfg if c["bot_profile"] == "DS"]
    if not ds:
        return None
    ds.sort(key=lambda c: (-c["bot_pair_high"], -c["mid_rank_sum"]))
    best = ds[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# ----------------------------------------------------------------------
# K × DS_NO_JOINT — extra: drop K to 2-on-top (oracle's most common
# specific drop choice at K, ~7%)
# ----------------------------------------------------------------------

def rule_K_DSnj_drop_K_to_2top_DSms(hand_bytes) -> Optional[int]:
    """C_K7: In K × DS_NO_JOINT, if (top=2, DS bot, ms_mid_high ≥ T)
    achievable, take it.

    PRINCIPLE: 2-on-top is oracle's most frequent specific drop choice
    in K × DSnj (7% rate). Surgically targeting top=2 may yield a
    cleaner gate than C_K1's "any low top" gate.
    """
    if not _is_K_high_no_pair(hand_bytes):
        return None
    if _cell_for_hand_K(hand_bytes) != "DS_NO_JOINT":
        return None
    nonK = _enumerate_nonMax_top_DSms(hand_bytes, KING)
    twos = [c for c in nonK if c["top_rank"] == 2 and c["mid_high"] >= 10]
    if not twos:
        return None
    twos.sort(key=lambda c: (-c["mid_rank_sum"], -c["bot_pair_high"]))
    best = twos[0]
    return int(_setting_index_from_tmb(best["top_pos"], best["mid_a"], best["mid_b"]))


# Registry for the test runner
CANDIDATES = {
    # K × DS_NO_JOINT (5 candidates — biggest cell)
    "C_K1_DSnj_drop_K_low_top_DSms": (rule_K_DSnj_drop_K_low_top_DSms, "DS_NO_JOINT"),
    "C_K2_DSnj_drop_K_when_K_in_DSpair": (rule_K_DSnj_drop_K_when_K_in_DSpair, "DS_NO_JOINT"),
    "C_K3_DSnj_take_Qtop_DSms": (rule_K_DSnj_take_Qtop_DSms, "DS_NO_JOINT"),
    "C_K4_DSnj_SSms_when_high": (rule_K_DSnj_SSms_when_high, "DS_NO_JOINT"),
    "C_K7_DSnj_drop_K_to_2top_DSms": (rule_K_DSnj_drop_K_to_2top_DSms, "DS_NO_JOINT"),
    # K × MS_ONLY
    "C_K5_MSonly_drop_K": (rule_K_MSonly_drop_K, "MS_ONLY"),
    # Negative control
    "C_K6_DSnj_HIBOT_tiebreaker": (rule_K_DSnj_HIBOT_tiebreaker, "DS_NO_JOINT"),
}
