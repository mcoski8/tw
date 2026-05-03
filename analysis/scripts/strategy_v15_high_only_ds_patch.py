"""
v15 — patch v8's bot on high_only hands when v8 picks a non-DS bot but a
DS-feasible setting exists.

Discriminator findings (200K-sample on 1.2M high_only hands):
  Oracle picks DS bot 52% of the time on high_only.
  v8's pct_optimal on high_only is 19.8% — most v8 misses are because
  v8 chose rainbow / 3+1 / 4-flush bot when DS was available.
  Sacrifice-top is rare (only 12% of all high_only oracle picks);
  most of the time the top stays "obvious" — high card.

v15 logic:
  1. Hand is high_only AND v8 picks a non-DS bot.
  2. Enumerate the 105 settings, find ones with DS bot.
  3. Among DS-bot settings, pick by simple score:
       bot_rank_sum + bot_connectivity_bonus + mid_kind_bonus + top_rank
  4. Otherwise (no DS-feasible setting OR v8 already picks DS bot):
     return v8's choice unchanged.

This is a tighter "patch" rule than v11's broad sacrifice-top rule.
Falls back to v14 for non-high_only hands.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from strategy_v8_hybrid import strategy_v8_hybrid  # noqa: E402
from strategy_v14_combined import strategy_v14_combined  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    SUIT_PROFILE_DS,
    SUIT_PROFILE_SS,
    setting_features_from_bytes,
)


def _detect_v15_high_only_setting(hand_bytes: np.ndarray) -> int | None:
    ranks = (hand_bytes // 4) + 2
    rank_counts = np.bincount(ranks, minlength=15)

    # high_only = no pair/trip/quad
    if any(rank_counts[r] >= 2 for r in range(2, 15)):
        return None

    feats = setting_features_from_bytes(hand_bytes)
    v8_idx = int(strategy_v8_hybrid(hand_bytes))
    v8_bot_profile = int(feats.bot_suit_profile[v8_idx])

    # If v8 already picks DS bot, no upgrade.
    if v8_bot_profile == SUIT_PROFILE_DS:
        return None

    # Find DS-bot settings.
    ds_mask = feats.bot_suit_profile == SUIT_PROFILE_DS
    if not ds_mask.any():
        return None  # no DS-feasible setting

    # Among DS-bot settings, score each:
    # priority: bot_rank_sum * 10 + bot_longest_run * 80 + mid_kind_bonus + top_rank
    # mid_kind_bonus: +50 if mid_is_pair (impossible here since no pair in hand),
    #                  +30 if mid is broadway, +10 if suited, 0 else
    # We want simple defendable choice; v8 already does the obvious play, so
    # we just want best DS replacement.

    # Compute bot_rank_sum and connectivity per setting
    # For each setting i with mask_a[i] true, the bot ranks are at
    # SETTING_HAND_INDICES[i, 3:7] applied to hand_bytes.
    from tw_analysis.query import SETTING_HAND_INDICES
    permuted = hand_bytes[SETTING_HAND_INDICES]  # (105, 7)
    bot_bytes = permuted[:, 3:]  # (105, 4)
    bot_ranks_arr = (bot_bytes // 4 + 2).astype(np.int8)  # (105, 4)
    bot_rank_sum = bot_ranks_arr.sum(axis=1)  # (105,)
    # Already have bot_longest_run in feats.

    # Mid features
    mid_ranks = (permuted[:, 1:3] // 4 + 2).astype(np.int8)
    mid_suits = permuted[:, 1:3] & 0b11
    mid_both_broadway = (mid_ranks[:, 0] >= 10) & (mid_ranks[:, 1] >= 10)
    mid_suited = mid_suits[:, 0] == mid_suits[:, 1]

    mid_kind = np.where(
        mid_both_broadway & mid_suited, 40,
        np.where(mid_both_broadway, 30, np.where(mid_suited, 10, 0))
    )

    # Composite score per setting (higher = better)
    score = (
        bot_rank_sum.astype(np.int32) * 10
        + feats.bot_longest_run.astype(np.int32) * 80
        + mid_kind.astype(np.int32)
        + feats.top_rank.astype(np.int32)
    )
    # Mask out non-DS bot settings: set their score to -inf.
    score_masked = np.where(ds_mask, score, -10**9)
    best_idx = int(score_masked.argmax())
    return best_idx


def strategy_v15_high_only_ds_patch(hand: np.ndarray) -> int:
    """v15: patch v8's high_only bot when DS upgrade is available."""
    chosen = _detect_v15_high_only_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v14_combined(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    from tw_analysis.canonical import read_canonical_hands
    test_cases = [
        # Top-15 v10 misses on high_only — these have v8 picking weird stuff.
        ("2c 3c 4d 7h 9s Jc Qd", "expect DS bot like Qd Jc 4d 3c"),
        ("4c 5d 7d 9h Jc Qs Kh", "expect DS bot"),
    ]
    for s, note in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        v8 = strategy_v8_hybrid(h)
        v15 = _detect_v15_high_only_setting(h)
        print(f"hand={s}  v8={v8}  v15_picks={v15}  ({note})")
