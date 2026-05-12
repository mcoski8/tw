"""
Session 67 — C_PAIR_3 rule candidates (6/7/8/9-pair PBOT-take).

Three sub-variants of "if pair_rank ∈ {6,7,8,9} AND pair-to-bot DS
achievable → take the best pair-to-bot-DS setting":

  C_PAIR_3a — simple: fires on any PBOT_DS-feasible hand at pair ∈ {6,7,8,9}.
  C_PAIR_3b — gated:  fires only when the chosen setting's mid_high ≥ T_MID
                       (T_MID default = 11 = J; controls "mid strong enough"
                       since oracle's preferred class is PBOT_tmax_DS_ms
                       which has a high-mid).
  C_PAIR_3c — joint:  fires only when JOINT setting is achievable
                       (= max_sing on top AND ms_mid AND DS bot all
                        simultaneously). Most surgical, smallest fire
                        region.

Setting builder priority (within "PBOT_DS achievable"):
  1. JOINT setting (top=max_sing, mid=ms, bot=pair+DS-kickers). Prefer the
     joint with HIGHEST mid_high.
  2. Next: top=max_sing + non-ms mid. Choose kickers to MINIMIZE bot rank
     sum (leaves high cards in mid).
  3. Else: top=lowest leftover, mid=2 remaining (Rule 11's fallback design).

For C_PAIR_3 the baseline is v52 (the production rule chain). When the
rule doesn't fire OR isn't applicable, the rule function returns None and
the harness uses v52's pick for the hand.

NOTE: These are CANDIDATE strategy functions; they do NOT inherit from
v52 and are NOT shipped. The harness composes (rule -> v52 fallback) at
test time. A shipping version would import v52 and call it on fallback.
"""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

PAIR_RANKS_3 = {6, 7, 8, 9}


def _enumerate_pbot_ds(hand_bytes: np.ndarray, allowed_pair_ranks: set) -> Optional[dict]:
    """Find pair-to-bot DS configurations for a pair hand.

    Returns dict with:
      pair_rank, pair_pos (tuple), pair_suits (tuple), sing_pos (list of 5),
      sing_ranks (list of 5), max_sing_local (int 0..4), max_sing_pos (int),
      configs: list of dicts, each with:
        - kicker_a_local, kicker_b_local (singleton local indices in bot)
        - leftover_locals (3 singleton locals NOT in bot)
        - bot_pos (4 positions)
        - has_maxtop (bool: max_sing in leftover)
        - has_ms_mid (bool: 2 leftover non-max same suit)
        - joint (bool: has_maxtop AND has_ms_mid)
        - mid_high (int): highest non-max rank in mid (= second-highest leftover if joint)
    Or None if pair gate fails / no PBOT_DS achievable.
    """
    h = np.asarray(hand_bytes, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks, minlength=15)
    n_quads = int((rc == 4).sum())
    n_trips = int((rc == 3).sum())
    n_pairs = int((rc == 2).sum())
    if n_quads != 0 or n_trips != 0 or n_pairs != 1:
        return None
    pair_rank = int(np.argmax(rc == 2))
    if pair_rank not in allowed_pair_ranks:
        return None
    pair_pos = [i for i in range(7) if int(ranks[i]) == pair_rank]
    if len(pair_pos) != 2:
        return None
    sa = int(suits[pair_pos[0]])
    sb = int(suits[pair_pos[1]])
    if sa == sb:
        return None  # pair shares suit — can't anchor DS

    sing_pos = [i for i in range(7) if i not in pair_pos]
    sing_ranks = [int(ranks[i]) for i in sing_pos]
    sing_suits = [int(suits[i]) for i in sing_pos]
    max_sing_local = sing_ranks.index(max(sing_ranks))

    # Enumerate (ka, kb): ka local index of singleton of suit sa, kb of suit sb.
    kickers_a = [k for k in range(5) if sing_suits[k] == sa]
    kickers_b = [k for k in range(5) if sing_suits[k] == sb]
    configs = []
    for ka in kickers_a:
        for kb in kickers_b:
            if ka == kb:
                continue
            leftover = [k for k in range(5) if k not in (ka, kb)]
            assert len(leftover) == 3
            has_maxtop = (max_sing_local in leftover)
            if has_maxtop:
                non_max_left = [k for k in leftover if k != max_sing_local]
                has_ms_mid = sing_suits[non_max_left[0]] == sing_suits[non_max_left[1]]
                mid_ranks = sorted([sing_ranks[non_max_left[0]],
                                    sing_ranks[non_max_left[1]]], reverse=True)
                mid_high = mid_ranks[0]
            else:
                # max_sing is in bot; mid = 2 of leftover, top = 1 of leftover.
                # mid_high = highest leftover that isn't going to top.
                # Try top=lowest, mid=top 2 remaining (Rule 11's design).
                sorted_leftover = sorted(leftover, key=lambda k: sing_ranks[k])
                top_local = sorted_leftover[0]
                mid_locals = sorted_leftover[1:]
                has_ms_mid = sing_suits[mid_locals[0]] == sing_suits[mid_locals[1]]
                mid_high = max(sing_ranks[mid_locals[0]],
                               sing_ranks[mid_locals[1]])
            joint = has_maxtop and has_ms_mid
            bot_pos = [pair_pos[0], pair_pos[1],
                       sing_pos[ka], sing_pos[kb]]
            configs.append({
                "ka": ka, "kb": kb,
                "leftover": leftover,
                "has_maxtop": has_maxtop,
                "has_ms_mid": has_ms_mid,
                "joint": joint,
                "mid_high": mid_high,
                "kicker_a_rank": sing_ranks[ka],
                "kicker_b_rank": sing_ranks[kb],
            })
    if not configs:
        return None

    return {
        "pair_rank": pair_rank,
        "pair_pos": tuple(pair_pos),
        "pair_suits": (sa, sb),
        "sing_pos": sing_pos,
        "sing_ranks": sing_ranks,
        "sing_suits": sing_suits,
        "max_sing_local": max_sing_local,
        "max_sing_pos": sing_pos[max_sing_local],
        "configs": configs,
    }


def _choose_best_pbot_ds_config(info: dict) -> Optional[dict]:
    """Choose the best PBOT_DS config from info["configs"] using the
    priority:
      1. Joint setting with highest mid_high.
      2. Else max_sing-on-top non-ms with lowest bot-rank-sum.
      3. Else (max_sing in bot) lowest bot-rank-sum.
    Returns the chosen config dict or None if configs is empty.
    """
    configs = info["configs"]
    if not configs:
        return None
    joints = [c for c in configs if c["joint"]]
    if joints:
        return max(joints, key=lambda c: c["mid_high"])
    maxtop_only = [c for c in configs if c["has_maxtop"]]
    if maxtop_only:
        return min(maxtop_only,
                   key=lambda c: c["kicker_a_rank"] + c["kicker_b_rank"])
    return min(configs,
               key=lambda c: c["kicker_a_rank"] + c["kicker_b_rank"])


def _build_setting_from_config(info: dict, cfg: dict) -> int:
    """Build the engine setting_index from the chosen config."""
    sing_pos = info["sing_pos"]
    sing_ranks = info["sing_ranks"]
    sing_suits = info["sing_suits"]
    max_sing_local = info["max_sing_local"]

    ka_pos = sing_pos[cfg["ka"]]
    kb_pos = sing_pos[cfg["kb"]]
    leftover_locals = cfg["leftover"]

    if cfg["has_maxtop"]:
        top_pos = sing_pos[max_sing_local]
        mid_locals = [k for k in leftover_locals if k != max_sing_local]
    else:
        # max_sing is in bot (= ka or kb). Top = lowest of leftover; mid = 2 high.
        sorted_left = sorted(leftover_locals, key=lambda k: sing_ranks[k])
        top_pos = sing_pos[sorted_left[0]]
        mid_locals = sorted_left[1:]

    mid_pos = sorted([sing_pos[mid_locals[0]], sing_pos[mid_locals[1]]])
    return _setting_index_from_tmb(top_pos, mid_pos[0], mid_pos[1])


# ============================================================
# Three sub-variant rule functions for the catalog harness.
# Each returns Optional[int] — None means rule doesn't fire.
# ============================================================

def rule_c_pair_3a(hand_bytes: np.ndarray) -> Optional[int]:
    """C_PAIR_3a — simple: pair ∈ {6,7,8,9} AND PBOT_DS achievable → take
    best pair-to-bot-DS construction."""
    info = _enumerate_pbot_ds(hand_bytes, PAIR_RANKS_3)
    if info is None:
        return None
    cfg = _choose_best_pbot_ds_config(info)
    if cfg is None:
        return None
    return _build_setting_from_config(info, cfg)


def make_rule_c_pair_3b(t_mid: int = 11):
    """C_PAIR_3b — gated: same as 3a but only fires when the chosen
    construction has mid_high ≥ t_mid (default J=11)."""
    def rule(hand_bytes: np.ndarray) -> Optional[int]:
        info = _enumerate_pbot_ds(hand_bytes, PAIR_RANKS_3)
        if info is None:
            return None
        cfg = _choose_best_pbot_ds_config(info)
        if cfg is None or cfg["mid_high"] < t_mid:
            return None
        return _build_setting_from_config(info, cfg)
    rule.__name__ = f"rule_c_pair_3b_mid{t_mid}"
    return rule


def rule_c_pair_3c(hand_bytes: np.ndarray) -> Optional[int]:
    """C_PAIR_3c — joint only: pair ∈ {6,7,8,9} AND JOINT (max_sing on top
    + ms mid + DS bot all achievable) → take joint with highest mid_high."""
    info = _enumerate_pbot_ds(hand_bytes, PAIR_RANKS_3)
    if info is None:
        return None
    joints = [c for c in info["configs"] if c["joint"]]
    if not joints:
        return None
    cfg = max(joints, key=lambda c: c["mid_high"])
    return _build_setting_from_config(info, cfg)


if __name__ == "__main__":
    # Quick smoke test: deal a 6-pair hand and check the rule fires.
    from tw_analysis.settings import parse_hand
    test_hands = [
        # 6-pair (suits c, h), kickers needed: suit-c + suit-h, both available
        "6c 6h 8c Td Jc Qd Kh",
        # 7-pair (suits c, h), DS feasible
        "7c 7h 9c Td Jc Qh As",
        # 9-pair (suits d, s), DS feasible, joint should work
        "9d 9s 2c 5h Td Jc Qs",
    ]
    for s in test_hands:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        for fn, name in [(rule_c_pair_3a, "3a"),
                          (make_rule_c_pair_3b(11), "3b_J"),
                          (rule_c_pair_3c, "3c")]:
            chosen = fn(h)
            print(f"  {name}({s}) -> {chosen}")
