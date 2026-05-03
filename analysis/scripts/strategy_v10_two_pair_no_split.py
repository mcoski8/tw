"""
v10 — for two-pair hands, never split a pair.

Top-15 inspection on full 6M grid showed v8_hybrid bleeds $40-$45K/1000h per
hand on its worst two_pair plays. In every case the v8 setting splits one
of the pairs to form a "suited connector" mid, while the oracle keeps both
pairs intact (one of three no-split archetypes):
    1. Both pairs in bot. Mid = 2 kickers, top = 1 kicker.
    2. Higher pair in mid. Bot = lower pair + 2 kickers. Top = 1 kicker.
    3. Lower pair in mid. Bot = higher pair + 2 kickers. Top = 1 kicker.

v10 enumerates the no-split options and picks one by simple priority:
    (a) maximize top rank (Ace if present),
    (b) tie-break by bot DS-ness,
    (c) tie-break by mid pair > mid offsuit-broadway > mid other.

Falls back to v9.1 (which falls back to v8) on non-two-pair hands.
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

from strategy_v9_1_pair_to_bot_ds import strategy_v9_1_pair_to_bot_ds  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _bot_suit_profile(suits: list[int]) -> int:
    """0=rainbow, 1=SS, 2=DS, 3=3+1, 4=4-flush. Matches query.SUIT_PROFILE_*."""
    cnt = [0, 0, 0, 0]
    for s in suits:
        cnt[s] += 1
    s = sorted(cnt, reverse=True)
    if s == [2, 2, 0, 0]: return 2
    if s == [2, 1, 1, 0]: return 1
    if s == [1, 1, 1, 1]: return 0
    if s == [3, 1, 0, 0]: return 3
    if s == [4, 0, 0, 0]: return 4
    return -1


def _detect_v10_two_pair_setting(hand_bytes: np.ndarray) -> int | None:
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11
    rank_counts = np.bincount(ranks, minlength=15)

    # Exactly two pairs, no trips/quads.
    pair_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 2], reverse=True)
    if len(pair_ranks) != 2:
        return None
    n_trips_or_more = sum(rank_counts[r] >= 3 for r in range(2, 15))
    if n_trips_or_more > 0:
        return None
    higher_rank, lower_rank = pair_ranks[0], pair_ranks[1]

    # Indices of pair members + kickers.
    higher_idx = sorted(j for j in range(7) if ranks[j] == higher_rank)
    lower_idx = sorted(j for j in range(7) if ranks[j] == lower_rank)
    kicker_idx = sorted(j for j in range(7) if j not in (*higher_idx, *lower_idx))
    if len(kicker_idx) != 3:
        return None  # shouldn't happen for valid two_pair

    # Generate the 9 candidate no-split settings (3 archetypes × 3 top-kicker choices).
    candidates: list[tuple[int, int, int, int, int, int, int]] = []
    # tuple format: (setting_index, archetype, top_rank, bot_suit_profile_code, mid_kind_score, top_idx, key_for_ties)
    # mid_kind_score: 3=mid is pair, 2=mid is broadway-offsuit, 1=mid is suited-connector, 0=other

    for top_pos in (0, 1, 2):
        top_idx = kicker_idx[top_pos]
        other_kickers = [kicker_idx[i] for i in (0, 1, 2) if i != top_pos]
        # Archetype 1: both pairs in bot.
        # Mid = the 2 other_kickers. Bot = both pairs.
        # That uses 1 (top) + 2 (mid) + 4 (bot pairs) = 7 ✓
        bot1 = [*higher_idx, *lower_idx]
        mid1 = list(other_kickers)
        candidates.append(_score(hand_bytes, suits, ranks, top_idx, mid1, bot1, archetype=1))

        # Archetype 2: higher pair in mid, bot = lower pair + 2 other_kickers.
        # Uses 1 + 2 (higher pair) + 4 (lower pair + 2 kickers) = 7 ✓
        bot2 = [*lower_idx, *other_kickers]
        candidates.append(_score(hand_bytes, suits, ranks, top_idx, list(higher_idx), bot2, archetype=2))

        # Archetype 3: lower pair in mid, bot = higher pair + 2 other_kickers.
        bot3 = [*higher_idx, *other_kickers]
        candidates.append(_score(hand_bytes, suits, ranks, top_idx, list(lower_idx), bot3, archetype=3))

    # Pick best candidate by priority key (higher = better).
    candidates.sort(key=lambda x: x[6], reverse=True)
    return candidates[0][0]


def _score(
    hand_bytes: np.ndarray,
    suits: np.ndarray,
    ranks: np.ndarray,
    top_idx: int,
    mid_indices: list[int],
    bot_indices: list[int],
    archetype: int,
) -> tuple[int, int, int, int, int, int, int]:
    """Compute setting_index and a priority score."""
    # Mid must be exactly 2, bot exactly 4, all distinct, none == top_idx.
    used = {top_idx, *mid_indices, *bot_indices}
    assert len(used) == 7, f"mid+bot+top must cover 7 cards: {used}"
    setting_idx = _setting_index_from_tmb(top_idx, mid_indices[0], mid_indices[1])

    top_rank = int(ranks[top_idx])
    bot_suits = [int(suits[j]) for j in bot_indices]
    bot_profile = _bot_suit_profile(bot_suits)
    mid_ranks = [int(ranks[j]) for j in mid_indices]
    mid_suits = [int(suits[j]) for j in mid_indices]

    mid_is_pair = mid_ranks[0] == mid_ranks[1]
    mid_is_broadway = mid_ranks[0] >= 10 and mid_ranks[1] >= 10
    mid_is_suited_connector = (mid_suits[0] == mid_suits[1]) and abs(mid_ranks[0] - mid_ranks[1]) <= 2

    if mid_is_pair:
        mid_kind = 3
    elif mid_is_broadway:
        mid_kind = 2
    elif mid_is_suited_connector:
        mid_kind = 1
    else:
        mid_kind = 0

    # bot_score for ties: prefer DS (2), then SS (1), then rainbow (0), then 3+1 (-1), then 4-flush (-2).
    bot_score_lookup = {2: 2, 1: 1, 0: 0, 3: -1, 4: -2, -1: -3}
    bot_score = bot_score_lookup.get(bot_profile, -3)

    # Composite priority key:
    #   Highest weight: top_rank (Ace = 14, etc.)
    #   Next:           bot_score
    #   Next:           mid_kind
    #   Next:           archetype tie-break (prefer 1 over 2 over 3 — gives both-pairs-in-bot a slight edge)
    archetype_tiebreak = {1: 2, 2: 1, 3: 0}[archetype]
    key = (top_rank * 10000) + (bot_score * 100) + (mid_kind * 10) + archetype_tiebreak

    return (setting_idx, archetype, top_rank, bot_profile, mid_kind, top_idx, key)


def strategy_v10_two_pair_no_split(hand: np.ndarray) -> int:
    """v10: never split a two-pair, otherwise fall back to v9.1."""
    chosen = _detect_v10_two_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v9_1_pair_to_bot_ds(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    # Top-15 oracle picks should match v10 detector.
    test_cases = [
        ("7c 7d 8c 8d Jh Ks As", 104, "#1: 7788 + JKA → both pairs to bot"),
        ("6c 6d 8c 8h Js Kd As", 99, "#4: 6688 + JKA → 88 mid, 66+JK bot"),
        ("7c 7d 8c 8h Jc Qd Ah", 99, "#10: 7788 + JQA → 88 mid, 77+JQ bot DS"),
        ("6c 6d 8c 8h Jc Kd Ac", 99, "#15: 6688 + JKA → 88 mid, 66+JK bot DS"),
    ]
    for s, expected, note in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        chosen = _detect_v10_two_pair_setting(h)
        match = "✓" if chosen == expected else "✗"
        print(f"{match} {s}  detected={chosen}  expected={expected}  ({note})")
