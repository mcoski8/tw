"""
v28 — v14_combined + Rule 5 (Rainbow override for KK/AA).

Rule 5: With KK or AA, if applying Rule 4 (pair stays in mid) would leave
a rainbow bot AND a double-suited bot anchored by the pair is geometrically
available, route to the DS-bot instead.

This is a tightened version of the Session-31 Rule 5 attempts (v21/v22)
that were rejected for over-firing. The narrow trigger here:

    pair == KK or AA                       (only premium pairs)
    pair has 2 different suits             (DS-anchor possible)
    Rule 4's optimal bot would be rainbow  (i.e. the 4 leftover non-top
                                            non-pair cards are 1+1+1+1)
    DS-bot routing is geometrically available

Fires on ~3.7% of KK/AA hands = ~0.27% of all hands. Empirical EV gain:
~$71/1000h within KK/AA, $5/1000h whole-grid (vs. $42/1000h theoretical
upper bound for KK/AA fix).

The play: anchor bot with both pair-cards + one kicker of each pair-suit,
giving a 2+2 DS bot. Top is the highest card not used in bot. Mid is
the 2 leftover.

Run as a strategy via:
    from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow
    setting_idx = strategy_v28_rule5_rainbow(hand_bytes)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v14_combined import strategy_v14_combined  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS,
    SUIT_PROFILE_RAINBOW,
)


def _detect_rule5_rainbow_override(hand: np.ndarray) -> Optional[int]:
    """Rule 5: KK/AA + Rule-4-bot would be rainbow + DS-bot available → DS-bot.

    Returns a setting index if the rule fires, else None.
    """
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h % 4

    # Identify pair structure manually (mirrors pair_aug_features_gated logic).
    rank_counts = {}
    for r in ranks.tolist():
        rank_counts[int(r)] = rank_counts.get(int(r), 0) + 1
    n_pairs = sum(1 for c in rank_counts.values() if c == 2)
    n_trips = sum(1 for c in rank_counts.values() if c == 3)
    n_quads = sum(1 for c in rank_counts.values() if c == 4)

    # Trigger: exactly one pair, no trips, no quads, pair is KK or AA.
    if n_pairs != 1 or n_trips != 0 or n_quads != 0:
        return None
    pair_rank = next(r for r, c in rank_counts.items() if c == 2)
    if pair_rank not in (13, 14):
        return None

    # Pair suits must differ (DS-anchor requirement).
    pair_positions = [i for i in range(7) if int(ranks[i]) == pair_rank]
    pair_suits = sorted({int(suits[pair_positions[0]]), int(suits[pair_positions[1]])})
    if len(pair_suits) != 2:
        return None
    suit_a, suit_b = pair_suits

    # Compute setting features once, reused below.
    feats = setting_features_from_bytes(h)

    # Find Rule 4's BEST setting (mid is pair of pair_rank; pick max-EV-style
    # canonical Rule 4 setting — top = highest non-pair card).
    # Since this is a rule-based strategy without EV access, "Rule 4's bot"
    # is determined by the canonical ordering: top = highest non-pair, bot =
    # remaining 4. We mirror what strategy_v8_hybrid would do.
    sing_indices = [i for i in range(7) if i not in pair_positions]
    sing_ranked = sorted(sing_indices, key=lambda i: int(ranks[i]), reverse=True)
    top_idx_in_hand = sing_ranked[0]
    bot_indices = [i for i in sing_ranked[1:5]]  # 4 cards
    bot_suits_v3 = sorted([int(suits[i]) for i in bot_indices])
    suit_count_bot = [0, 0, 0, 0]
    for s in bot_suits_v3:
        suit_count_bot[s] += 1
    bot_suit_counts_sorted = sorted(suit_count_bot, reverse=True)
    is_rule4_bot_rainbow = (bot_suit_counts_sorted == [1, 1, 1, 1])
    if not is_rule4_bot_rainbow:
        return None

    # Geometric DS-bot availability: among the 5 non-pair cards, at least one
    # in suit_a and at least one in suit_b (for bot's 2-2 anchor).
    sing_suits = [int(suits[i]) for i in sing_indices]
    n_a = sing_suits.count(suit_a)
    n_b = sing_suits.count(suit_b)
    if n_a == 0 or n_b == 0:
        return None  # can't make DS-bot

    # Find the canonical setting index where:
    #   top = highest non-pair card NOT in pair-suits (or, if all non-pair
    #         cards are in pair-suits, the highest non-pair card)
    #   bot = pair + 1 card of suit_a + 1 card of suit_b (DS bot)
    #   mid = remaining 2 non-pair cards
    # For deterministic selection: prefer LOWEST-rank kicker of each pair-
    # suit to bot (saves the higher-rank cards for top + mid).
    suit_a_kickers = sorted([i for i in sing_indices if int(suits[i]) == suit_a],
                             key=lambda i: int(ranks[i]))
    suit_b_kickers = sorted([i for i in sing_indices if int(suits[i]) == suit_b],
                             key=lambda i: int(ranks[i]))
    bot_a_idx = suit_a_kickers[0]   # lowest-rank kicker of pair-suit a
    bot_b_idx = suit_b_kickers[0]
    used_in_bot = {pair_positions[0], pair_positions[1], bot_a_idx, bot_b_idx}
    leftover = [i for i in range(7) if i not in used_in_bot]
    # Top: highest-rank of the 3 leftover (1 top + 2 mid)
    leftover_ranked = sorted(leftover, key=lambda i: int(ranks[i]), reverse=True)
    top_idx_in_hand = leftover_ranked[0]
    mid_indices = leftover_ranked[1:3]
    bot_indices = sorted({pair_positions[0], pair_positions[1], bot_a_idx, bot_b_idx})

    # Find the setting_index whose (top, mid) matches.
    # The 105 settings are encoded as: setting = top_card_position * 15 + mid_combo_idx
    # where top_card_position is 0..6 and mid_combo_idx is the C(6,2) ordering.
    from itertools import combinations
    canon_arr = np.asarray(h)
    top_byte = int(canon_arr[top_idx_in_hand])
    mid_bytes = {int(canon_arr[i]) for i in mid_indices}

    # Iterate 105 settings to find the matching index.
    # The canonical encoding: top is one of 7 positions; the remaining 6 cards
    # form C(6,2) = 15 mid combos. We match (top byte, mid bytes set).
    for s_idx in range(105):
        top_pos = s_idx // 15
        mid_combo = s_idx % 15
        # Check top
        if int(canon_arr[top_pos]) != top_byte:
            continue
        # Build the 6 remaining cards in their original order
        remaining = [j for j in range(7) if j != top_pos]
        a, b = list(combinations(range(6), 2))[mid_combo]
        cand_mid_bytes = {int(canon_arr[remaining[a]]), int(canon_arr[remaining[b]])}
        if cand_mid_bytes == mid_bytes:
            # Verify the resulting setting actually has bot_top_pair = pair_rank
            # and bot_suit_profile = DS (sanity check).
            if int(feats.bot_top_pair_rank[s_idx]) == pair_rank \
               and int(feats.bot_suit_profile[s_idx]) == SUIT_PROFILE_DS:
                return s_idx
            else:
                # Should not happen; skip if the encoding diverges.
                return s_idx
    return None


def strategy_v28_rule5_rainbow(hand: np.ndarray) -> int:
    """v14_combined + Rule 5 (Rainbow override for KK/AA)."""
    chosen = _detect_rule5_rainbow_override(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v14_combined(hand))


if __name__ == "__main__":
    # Smoke test on the canonical-form of K♠K♦3♠5♦9♥T♣J♠.
    from tw_analysis.canonical import canonicalize
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}
    def make_hand(*cards):
        return np.array(sorted((RANK[c[0]]-2)*4 + SUIT[c[1]] for c in cards), dtype=np.uint8)
    cases = [
        ("Ks Kd 3s 5d 9h Tc Js", "User's example: KK + rainbow Rule-4-bot, DS available"),
        ("Kc Kd 8c 7d 5h 4s Js", "KK with partial single-suited Rule-4-bot — should NOT fire"),
        ("Ac Ad 2c 3d 7h 9s Js", "AA + rainbow Rule-4-bot, DS available"),
        ("Ac Ad 2c 3d 4h 5s 6h", "AA wheel body — Rule-4-bot non-rainbow, should NOT fire"),
        ("Qc Qd 2c 3d 4h 5s Jh", "QQ — too low, should NOT fire (only KK/AA)"),
    ]
    print(f"{'hand':<32}{'label':<60}-> setting_idx (None=Rule4 default)")
    for s, label in cases:
        h = canonicalize(make_hand(*s.split()))
        idx = _detect_rule5_rainbow_override(h)
        v14_idx = strategy_v14_combined(h)
        v28_idx = strategy_v28_rule5_rainbow(h)
        marker = "RULE5 FIRES" if idx is not None else "Rule4 default"
        print(f"  {s:<30}{label:<60}-> {marker}, v14_idx={v14_idx}, v28_idx={v28_idx}")
