"""
Session 46 — v42 = v41 + Rule 11 (J-pair pair-to-bot + DS).

Drill A's per-pair-rank breakdown showed a sharp positive flip at P=J:
A5 − A2 = +$2,975/1000h within-hand (vs negative for P=2..T). Drill D
(focused J-pair-J drill) confirmed the apples-to-apples comparison
A5 − A1 = +$1,004/1000h, and v41 picks A5 0% of the time. The expected
whole-grid lift from overriding v41 with pair-to-bot DS at J-pair-J is
~+$11/1000h (full grid; J-pair-J has zero prefix coverage so prefix is
unchanged).

Rule 11 — trigger:
  cat == pair               AND
  P == 11                   AND  (pair_rank = J)
  max_rank == 11            AND  (max card = J)
  DS-bot achievable with both pair members in bot

Setting builder:
  Both J's go to BOT.
  Among the 5 non-pair singletons, pick 2 to also go to BOT such that
  the bot's 4-card suit pattern is 2+2 (DS).
    Case A: J's same suit X
      → need 2 singletons of the same non-X suit Y. If multiple Y choices
        or multiple sing-pairs available, pick the lowest-rank pair (to
        keep mid strong).
    Case B: J's different suits X, Y
      → need 1 singleton of suit X + 1 singleton of suit Y. Pick the
        lowest-rank of each.
  TOP = lowest-rank singleton among the remaining 3 (preserves v41's
        weak-hand top-inversion intent).
  MID = the 2 remaining singletons.

If DS-bot with pair-in-bot is NOT achievable, fall through to v41.

Validation: full grid (N=200) only — J-pair-J has zero prefix coverage
(no J-pair-J hand falls in canonical IDs < 500K). Prefix score is
unchanged because Rule 11 fires on 0 prefix hands. Same precedent as
high_only-zero-prefix from S43.
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

from strategy_v41_rule10_v3_ds import strategy_v41_rule10_v3_ds  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

P_J = 11


def _detect_rule11_jpair_pbot_ds(hand: np.ndarray) -> Optional[int]:
    h = np.asarray(hand, dtype=np.uint8)
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
    if int(ranks.max()) != P_J:
        return None
    if rc[P_J] != 2:
        return None  # the pair must be J's
    pair_pos = [j for j in range(7) if int(ranks[j]) == P_J]
    if len(pair_pos) != 2:
        return None
    sing_pos = sorted([j for j in range(7) if int(ranks[j]) != P_J],
                       key=lambda j: (-int(ranks[j]), j))
    # sing_pos sorted by rank desc; sing_pos[-1] is lowest

    j_suit_a = int(suits[pair_pos[0]])
    j_suit_b = int(suits[pair_pos[1]])

    # Find candidate (bot_sing_a, bot_sing_b) pairs that complete DS.
    # Pick the candidate that minimizes (rank_a + rank_b) i.e. the
    # lowest-rank pair (keeps mid strength).
    best_bot_sings = None
    best_rank_sum = None

    if j_suit_a == j_suit_b:
        # Same-suit J's: need 2 singletons of same non-X suit
        X = j_suit_a
        for Y in range(4):
            if Y == X:
                continue
            sings_Y = [sp for sp in sing_pos if int(suits[sp]) == Y]
            if len(sings_Y) < 2:
                continue
            # Try lowest-2 of suit Y
            cand = sorted(sings_Y, key=lambda sp: int(ranks[sp]))[:2]
            rank_sum = int(ranks[cand[0]]) + int(ranks[cand[1]])
            if best_rank_sum is None or rank_sum < best_rank_sum:
                best_rank_sum = rank_sum
                best_bot_sings = cand
    else:
        # Different-suit J's: need 1 of suit X + 1 of suit Y
        X, Y = j_suit_a, j_suit_b
        sings_X = [sp for sp in sing_pos if int(suits[sp]) == X]
        sings_Y = [sp for sp in sing_pos if int(suits[sp]) == Y]
        if not sings_X or not sings_Y:
            return None
        sx = min(sings_X, key=lambda sp: int(ranks[sp]))
        sy = min(sings_Y, key=lambda sp: int(ranks[sp]))
        best_bot_sings = sorted([sx, sy])
        best_rank_sum = int(ranks[sx]) + int(ranks[sy])

    if best_bot_sings is None:
        return None

    used = set(best_bot_sings) | set(pair_pos)
    remaining = [sp for sp in sing_pos if sp not in used]
    if len(remaining) != 3:
        return None
    # Top = lowest-rank of remaining 3
    top_pos = remaining[-1]
    mid_pos = sorted([remaining[0], remaining[1]])
    return int(_setting_index_from_tmb(top_pos, mid_pos[0], mid_pos[1]))


def strategy_v42_rule11_jpair_pbot_ds(hand: np.ndarray) -> int:
    chosen = _detect_rule11_jpair_pbot_ds(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v41_rule10_v3_ds(hand))
