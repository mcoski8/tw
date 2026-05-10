"""
Session 53 OVERNIGHT — v52 = v47 + comprehensive high_only handler.

Per detailed mini-drill (per-(max, s2) characterization), oracle top-card
distribution by max for high_only no-pair:

| max | max-on-top% | top=2% | top≤4% |
|---|---:|---:|---:|
| A | 93%      | 0.3%   | <1%   |
| K | 66%      | 7%     | ~12%  |
| Q | 49%      | 16%    | ~24%  |
| J | 27%      | 28%    | ~49%  |
| T | 15%      | 35%    | ~63%  |
| 9 | 7%       | 42%    | ~74%  |
| 8 | 3%       | 45%    | ~86%  |

Insight: for max ≤ T, defensive (lowest-on-top) is the right structure
on 62-86% of hands. v48's HIMID forces max-on-top — wrong on majority.

v52 design:
  Rule 14 (A-high HIMID): unchanged, fires first
  Rule 15 (K-high HIMID): unchanged
  Rule 16 (Q-high HIMID): unchanged
  Rule 17 (J-high HIMID): keep — borderline, J-on-top is 27% optimal
  Rule 22 (Q-high defensive 2nd≤8): fires before Rule 16's effect
  Rule 23 (K-high defensive 2nd≤8)
  Rule 24 (J-high defensive 2nd≤8)
  Rule 25 (T-high always defensive)
  Rule 26 (9-high always defensive)
  Rule 27 (8-high always defensive)
  Rule 28 (7-high always defensive)

Setting builder for ALL defensive rules: lowest-on-top + DS-bot HIMID
(or SS fallback). Same template as Rule 22.

This SUPERSEDES v48's Rules 18-21 (T/9/8/7 HIMID) which were
predominantly wrong.

Chain order matters: defensive rules fire FIRST for hands where they
apply. v47's existing Rules 14-16 are bypassed by Rule 22's defensive
override on hands meeting both conditions.
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

from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

# Defensive zones:
# Rules 25-28: max ∈ {7,8,9,10} → ALWAYS defensive (no s2 gate)
LOW_MAX_DEFENSIVE = {7, 8, 9, 10}
# Rules 22-24: max ∈ {J,Q,K} → defensive when 2nd-high ≤ 8
GATED_DEFENSIVE_MAX = {11, 12, 13}
GATED_S2_THRESHOLD = 8

# Rule 17: J-high HIMID (offensive) — fires when defensive doesn't
J_HIGH_OFFENSIVE = 11


def _build_himid_setting(hand: np.ndarray, top_pos: int,
                          others: list) -> Optional[int]:
    """Build a HIMID setting given top_pos and the list of other 6 positions.
    Picks DS bot first (HIMID tie-break), else SS bot, else None.
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3

    ds_options = []
    ss_options = []
    for mid_a, mid_b in combinations(others, 2):
        bot_pos = sorted(j for j in others if j not in (mid_a, mid_b))
        bot_suits = [int(suits[p]) for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        mid_rank_sum = int(ranks[mid_a]) + int(ranks[mid_b])
        if cnt == [2, 2]:
            ds_options.append((mid_rank_sum, mid_a, mid_b))
        elif cnt == [2, 1, 1]:
            ss_options.append((mid_rank_sum, mid_a, mid_b))

    if ds_options:
        ds_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ds_options[0]
        return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))
    if ss_options:
        ss_options.sort(key=lambda x: -x[0])
        _, mid_a, mid_b = ss_options[0]
        return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))
    return None


def _detect_v52_high_only(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    if int((rc == 4).sum()) != 0: return None
    if int((rc == 3).sum()) != 0: return None
    if int((rc == 2).sum()) != 0: return None
    max_r = int(ranks.max())
    if max_r < 7:
        return None  # too low for our rules

    sorted_ranks = sorted(int(r) for r in ranks)
    s2 = sorted_ranks[-2]

    # 1. Defensive (lowest-on-top) trigger
    use_defensive = False
    if max_r in LOW_MAX_DEFENSIVE:
        use_defensive = True
    elif max_r in GATED_DEFENSIVE_MAX and s2 <= GATED_S2_THRESHOLD:
        use_defensive = True

    if use_defensive:
        lowest_pos = min(range(7), key=lambda j: int(ranks[j]))
        others = [j for j in range(7) if j != lowest_pos]
        return _build_himid_setting(hand, lowest_pos, others)

    # 2. J-high HIMID (offensive) — fires for J-high when not defensive
    if max_r == J_HIGH_OFFENSIVE:
        max_pos = next(j for j in range(7) if int(ranks[j]) == max_r)
        others = [j for j in range(7) if j != max_pos]
        return _build_himid_setting(hand, max_pos, others)

    # max ∈ {Q, K, A} with s2 > 8: let v47 handle (Rules 14-16 HIMID)
    return None


def strategy_v52_full_high_only_handler(hand: np.ndarray) -> int:
    chosen = _detect_v52_high_only(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v47_rule16_Qhigh_DS(hand))
