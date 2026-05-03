"""
v9.2 — extend v9.1's pair-to-bot-DS gate to also cover asymmetric (1,3) and
(3,1) kicker distributions, which the Q4 discriminator showed are also
EV-positive for pair-to-bot ($850-$1,800/1000h gain), just smaller than
the (1,1) and (2,2) symmetric cases.

Discriminator data (200K random sample):
  (n_a, n_b) = (1, 1): pair-bot wins +$1,068/1000h  [v9.1 fires]
  (n_a, n_b) = (2, 2): pair-bot wins +$8,278/1000h  [v9.1 fires]
  (n_a, n_b) = (1, 3): pair-bot wins +$1,818/1000h  [v9.1 SKIPS — added in v9.2]
  (n_a, n_b) = (3, 1): pair-bot wins +$851/1000h    [v9.1 SKIPS — added in v9.2]
  (n_a, n_b) = (2, 1): pair-to-MID wins -$1,404/1000h  [v9.1 skips — keep skipping]
  (n_a, n_b) = (1, 2): pair-to-MID wins -$493/1000h    [v9.1 skips — keep skipping]

For (1,3) / (3,1): kicker placement requires care. Pair-suits are X (1 kicker)
and Y (3 kickers). Bot needs 2 of suit_X + 2 of suit_Y. The pair contributes
1 of each suit. So bot kickers must be 1 of suit_X (the only one) + 1 of
suit_Y (one of three). That leaves the other 2 suit_Y kickers + 0 suit_X
for mid. Mid is 2 cards both of suit_Y — a suited mid! Surprisingly strong
Hold'em mid.

Other gates unchanged (pair rank ∈ {2-5, T-J-Q}, single Ace, two pair-suits).
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
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

EV_POSITIVE_PAIR_RANKS = {2, 3, 4, 5, 10, 11, 12}
# v9.2 widened: (1,1), (2,2), (1,3), (3,1) — symmetric OR strongly-asymmetric.
EV_POSITIVE_KICKER_DISTRIBUTIONS = {(1, 1), (2, 2), (1, 3), (3, 1)}


def _detect_v9_2_setting(hand_bytes: np.ndarray) -> int | None:
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11
    rank_counts = np.bincount(ranks, minlength=15)

    total_multis = int(sum(rank_counts[r] >= 2 for r in range(2, 15)))
    if total_multis != 1:
        return None
    pair_rank = next(r for r in range(2, 15) if rank_counts[r] >= 2)
    if rank_counts[pair_rank] != 2:
        return None
    if pair_rank not in EV_POSITIVE_PAIR_RANKS:
        return None
    if rank_counts[14] != 1:
        return None

    pair_idx = [j for j in range(7) if ranks[j] == pair_rank]
    suit_a = int(suits[pair_idx[0]])
    suit_b = int(suits[pair_idx[1]])
    if suit_a == suit_b:
        return None

    ace_idx = next(j for j in range(7) if ranks[j] == 14)
    other = [j for j in range(7) if j not in (ace_idx, pair_idx[0], pair_idx[1])]
    n_a = sum(1 for j in other if int(suits[j]) == suit_a)
    n_b = sum(1 for j in other if int(suits[j]) == suit_b)

    if (n_a, n_b) not in EV_POSITIVE_KICKER_DISTRIBUTIONS:
        return None

    kickers_a = [j for j in other if int(suits[j]) == suit_a]
    kickers_b = [j for j in other if int(suits[j]) == suit_b]
    if not kickers_a or not kickers_b:
        return None

    def _key(i: int) -> int:
        return int(hand_bytes[i])

    # For (1,1) and (2,2) we keep v9.1's "lowest kicker each suit to bot".
    # For (1,3) and (3,1) the singleton suit is forced; pick the lowest
    # of the 3-suit kickers to join the bot, leaving the 2 highest of the
    # 3-suit kickers in mid (suited mid — strong Hold'em).
    kicker_a = min(kickers_a, key=_key)
    kicker_b = min(kickers_b, key=_key)
    if kicker_a == kicker_b:
        return None

    bot_set = {pair_idx[0], pair_idx[1], kicker_a, kicker_b}
    mid = [j for j in other if j not in bot_set]
    if len(mid) != 2:
        return None
    return _setting_index_from_tmb(ace_idx, mid[0], mid[1])


def strategy_v9_2_pair_to_bot_ds(hand: np.ndarray) -> int:
    chosen = _detect_v9_2_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))
