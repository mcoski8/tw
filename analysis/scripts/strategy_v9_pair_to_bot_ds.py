"""
v9_pair_to_bot_ds: when a hand has [pair (rank ≤ Q) + ace singleton + DS-bot
feasibility with the pair as the suit anchor], play [top=ace, mid=non-pair
leftover, bot=pair+two suit-matched kickers in DS pattern]. Otherwise fall
back to v8_hybrid.

Hypothesis from Q4 top-10 inspection: the oracle's argmax on these hands is
universally a pair-to-bot-DS setting, but v3/v8 reflexively put the pair in
mid, leaving $26-28K/1000h on the table per hand. Aggregate Q4 said B wins
in ~20.5% of hands (~906K).

This v9 captures only the 'B-wins' clear-archetype subset; further nuance
(exactly when AA-to-bot is right, KK-to-bot edge cases, etc.) is left for
v10+ once we see the v9 grid-graded numbers.
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

# Pair (a, b) with 0 <= a < b < 6 → mid_combo_index in 0..14.
# Mirrors _MID_PAIRS in tw_analysis.settings.
_MID_PAIR_INDEX = {}
_n = 0
for _a in range(6):
    for _b in range(_a + 1, 6):
        _MID_PAIR_INDEX[(_a, _b)] = _n
        _n += 1


def _setting_index_from_tmb(top_idx: int, mid_orig_a: int, mid_orig_b: int) -> int:
    """Reverse of decode_setting: given (top_idx, two mid indices in original
    7-card-hand order with mid_orig_a < mid_orig_b), return the setting_index
    (0..104) the engine uses.

    Mirrors the enumeration in `engine/src/setting.rs` and
    `tw_analysis.settings.decode_setting`.
    """
    if top_idx < 0 or top_idx >= 7:
        raise ValueError(f"top_idx must be 0..6, got {top_idx}")
    if mid_orig_a == top_idx or mid_orig_b == top_idx:
        raise ValueError("mid index collides with top_idx")
    if mid_orig_a == mid_orig_b:
        raise ValueError("mid indices must differ")
    if mid_orig_a > mid_orig_b:
        mid_orig_a, mid_orig_b = mid_orig_b, mid_orig_a
    # Map original indices to positions in the "remaining 6" list.
    remaining = [i for i in range(7) if i != top_idx]
    a = remaining.index(mid_orig_a)
    b = remaining.index(mid_orig_b)
    return top_idx * 15 + _MID_PAIR_INDEX[(a, b)]


def _detect_pair_to_bot_ds_setting(hand_bytes: np.ndarray) -> int | None:
    """If hand qualifies as a pair-to-bot-DS candidate, return the chosen
    setting_index; else None.

    Qualification:
      - hand has exactly one pair of rank in 2..12 (i.e. NOT KK or AA),
      - hand has at least one Ace,
      - the pair has two distinct suits (so it can anchor a DS bot),
      - among the 4 non-pair, non-Ace cards, at least one matches each
        of the pair's two suits (so a 2+2 DS bot is constructible).

    Choice:
      - top = the (highest-index) Ace,
      - bot = the two pair members + the highest-rank kicker matching
        each of the pair's two suits,
      - mid = the remaining two cards.
    """
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11

    rank_counts = np.bincount(ranks, minlength=15)

    # Strict gate: exactly ONE pair anywhere in the hand (rank 2..14), no
    # trips/quads, and the pair is in rank 2..12 (not KK/AA which the
    # locked-profile-style rules want kept in mid).
    total_multis = int(sum(rank_counts[r] >= 2 for r in range(2, 15)))
    if total_multis != 1:
        # Two-pair / three-pair / trips_pair / etc. — different archetype,
        # out of v9's scope. Multi-pair extensions are a future v10.
        return None
    multi_rank = next(r for r in range(2, 15) if rank_counts[r] >= 2)
    if multi_rank > 12:
        return None  # KK or AA — keep in mid per locked-profile preference.
    if rank_counts[multi_rank] != 2:
        return None  # trip/quad — different routing problem.
    pair_rank = multi_rank

    # Need an Ace.
    if rank_counts[14] < 1:
        return None
    # If multiple Aces (AA or trips of A), out of scope — that's a different
    # archetype (locked profile says AA stays in mid).
    if rank_counts[14] > 1:
        return None

    # Indices of pair members, the Ace, and the rest.
    pair_indices = [i for i in range(7) if ranks[i] == pair_rank]
    ace_idx = next(i for i in range(7) if ranks[i] == 14)
    pair_a, pair_b = pair_indices[0], pair_indices[1]
    suit_a = suits[pair_a]
    suit_b = suits[pair_b]
    if suit_a == suit_b:
        return None  # pair shares suit, can't anchor DS

    other_indices = [i for i in range(7) if i not in (ace_idx, pair_a, pair_b)]
    if len(other_indices) != 4:
        return None  # malformed

    # Find a kicker matching each pair-suit.
    kickers_a = [i for i in other_indices if suits[i] == suit_a]
    kickers_b = [i for i in other_indices if suits[i] == suit_b]
    if not kickers_a or not kickers_b:
        return None

    # Pick the LOWEST-rank kicker of each suit for the bot — empirically the
    # oracle prefers giving high kickers to the MID (where Hold'em plays them
    # as standalone pairing/flush draws more often), since the bot is already
    # anchored by the pair so its kickers' marginal value is small.
    def _key(i: int) -> int:
        return int(hand_bytes[i])
    kicker_a = min(kickers_a, key=_key)
    kicker_b = min(kickers_b, key=_key)
    if kicker_a == kicker_b:
        return None  # somehow they're the same card (shouldn't happen)

    # Mid is the two leftover non-pair, non-Ace cards.
    bot_set = {pair_a, pair_b, kicker_a, kicker_b}
    mid = [i for i in other_indices if i not in bot_set]
    if len(mid) != 2:
        return None
    return _setting_index_from_tmb(ace_idx, mid[0], mid[1])


def strategy_v9_pair_to_bot_ds(hand: np.ndarray) -> int:
    """v9 — pair-to-bot-for-DS rule, with v8_hybrid as fallback.

    Receives the canonical (sorted-ascending) 7-byte hand array and returns
    a setting_index in 0..104.
    """
    chosen = _detect_pair_to_bot_ds_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))


if __name__ == "__main__":
    # Quick smoke: the canonical hand 425562 (2c 2d 6c Td Qc Qd Ah)
    # should pick the oracle's setting 99 if v9 detects the archetype
    # and routes correctly. The hand has TWO pairs (QQ + 22) so it
    # falls outside v9's exact-one-pair gate — confirming we need a v10
    # extension to handle multi-pair archetypes.
    test_hands = [
        ("3c 4d 8d 9c Qc Qd Ac", 99),  # 3546583 — single pair Q + Ace
        ("3c 6d Td Jc Qc Qd Ad", 99),  # 4104257 — single pair Q + Ace
        ("2c 4d 7d 9c Qc Qd Ac", 99),  # 1923068 — single pair Q + Ace
    ]
    from tw_analysis.settings import parse_hand
    for s, expected in test_hands:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        chosen = _detect_pair_to_bot_ds_setting(h)
        print(f"hand={s}  v9 detected={chosen}  expected_oracle={expected}  match={chosen == expected}")
