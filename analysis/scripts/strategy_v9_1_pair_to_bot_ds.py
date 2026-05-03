"""
v9.1 — refined pair-to-bot-DS rule.

Discriminator findings (analysis/scripts/q4_discriminator_diagnostic.py on
200K sampled canonical hands):

  Pair-rank Δ (mean A − B, negative = pair-to-bot wins):
    pair  2: -0.259  ($+2,585/1000h pair-to-bot)
    pair  3: -0.162  ($+1,620)
    pair  4: -0.117  ($+1,168)
    pair  5: -0.109  ($+1,092)
    pair  6: -0.028  ($+276)   ← marginal
    pair  7: +0.102  ($-1,021) ← pair-to-MID wins
    pair  8: +0.172  ($-1,722) ← pair-to-MID wins
    pair  9: +0.093  ($-928)   ← pair-to-MID wins
    pair  T: -0.034  ($+343)   ← marginal
    pair  J: -0.241  ($+2,406)
    pair  Q: -0.237  ($+2,373)

  Kicker symmetry (n_a, n_b) breakdown:
    (1,1): pair-bot wins +$1,068/1000h
    (2,2): pair-bot wins +$8,278/1000h  ← strong signal
    (2,1) / (1,2): pair-to-mid wins -$1,400/1000h
    (3,1) / (1,3): pair-bot wins +$850 / +$1,800

The U-shaped pair-rank pattern is striking: low pairs (2-5) and high
non-anchor pairs (J, Q) both prefer pair-to-bot, but mid pairs (6-9)
prefer pair-to-mid. Hypothesis: the mid-pair zone is where the pair
is "good enough" in mid (Hold'em pair) without being so high that
opponents are likely to have higher pairs that demand DS bot strength.

v9.1 gate:
  - Single pair in hand (no other pairs/trips/quads)
  - Pair rank in {2, 3, 4, 5, T, J, Q} (skip 6, 7, 8, 9)
  - Exactly one Ace
  - Pair has two distinct suits
  - Kicker symmetry (n_a, n_b) in {(1,1), (2,2)} (skip asymmetric (2,1)/(1,2))

Otherwise: fall back to v8_hybrid.
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

# Pair ranks where pair-to-bot-DS is the EV-positive routing.
# Skips 6-9 where pair-to-mid empirically wins.
EV_POSITIVE_PAIR_RANKS = {2, 3, 4, 5, 10, 11, 12}


def _detect_v9_1_setting(hand_bytes: np.ndarray) -> int | None:
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 0b11
    rank_counts = np.bincount(ranks, minlength=15)

    # Single pair, no trips/quads, pair in 2..12.
    total_multis = int(sum(rank_counts[r] >= 2 for r in range(2, 15)))
    if total_multis != 1:
        return None
    pair_rank = next(r for r in range(2, 15) if rank_counts[r] >= 2)
    if rank_counts[pair_rank] != 2:
        return None
    if pair_rank not in EV_POSITIVE_PAIR_RANKS:
        return None

    # Exactly one Ace.
    if rank_counts[14] != 1:
        return None

    # Pair has two distinct suits (otherwise can't anchor DS).
    pair_idx = [j for j in range(7) if ranks[j] == pair_rank]
    suit_a = int(suits[pair_idx[0]])
    suit_b = int(suits[pair_idx[1]])
    if suit_a == suit_b:
        return None

    ace_idx = next(j for j in range(7) if ranks[j] == 14)
    other = [j for j in range(7) if j not in (ace_idx, pair_idx[0], pair_idx[1])]
    n_a = sum(1 for j in other if int(suits[j]) == suit_a)
    n_b = sum(1 for j in other if int(suits[j]) == suit_b)

    # Kicker symmetry gate: only (1,1) or (2,2) — skip the asymmetric
    # (2,1)/(1,2) where pair-to-mid empirically wins.
    if (n_a, n_b) not in {(1, 1), (2, 2)}:
        return None

    # Pick the lowest-rank kicker of each pair-suit for the bot (so the
    # higher-rank kickers go to mid for stronger Hold'em mid play).
    kickers_a = [j for j in other if int(suits[j]) == suit_a]
    kickers_b = [j for j in other if int(suits[j]) == suit_b]

    def _key(i: int) -> int:
        return int(hand_bytes[i])

    kicker_a = min(kickers_a, key=_key)
    kicker_b = min(kickers_b, key=_key)
    if kicker_a == kicker_b:
        return None

    bot_set = {pair_idx[0], pair_idx[1], kicker_a, kicker_b}
    mid = [j for j in other if j not in bot_set]
    if len(mid) != 2:
        return None
    return _setting_index_from_tmb(ace_idx, mid[0], mid[1])


def strategy_v9_1_pair_to_bot_ds(hand: np.ndarray) -> int:
    """v9.1 — discriminator-tightened pair-to-bot-DS rule."""
    chosen = _detect_v9_1_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))


if __name__ == "__main__":
    from tw_analysis.settings import parse_hand
    test_cases = [
        # Top-10 single-pair Q archetype — should fire.
        ("3c 4d 8d 9c Qc Qd Ac", 99, "single pair Q + Ace + DS"),
        ("3c 6d Td Jc Qc Qd Ad", 99, "single pair Q + broadway kickers"),
        ("2c 4d 7d 9c Qc Qd Ac", 99, "single pair Q + Ace"),
        # Mid-pair (7) — should NOT fire (skipped by EV_POSITIVE_PAIR_RANKS)
        ("3c 4d 7c 7d 9h Td Ac", None, "single pair 7 — skip per discriminator"),
        # Asymmetric kickers (n_a=2, n_b=1) — should NOT fire
        # Pair = QQ, suits 0+1. Need 4 non-pair-non-ace cards with 2 suit_0 + 1 suit_1 + 1 other.
        # QcQd Ah + 3c 5c 4d 9s = 2 clubs + 1 diamond + 1 spade. n_a=2, n_b=1 — should not fire.
        ("Qc Qd Ah 3c 5c 4d 9s", None, "asymmetric (2,1) kickers"),
    ]
    for s, expected, note in test_cases:
        h = np.array([c.idx for c in parse_hand(s)], dtype=np.uint8)
        h.sort()
        chosen = _detect_v9_1_setting(h)
        match = "✓" if chosen == expected else "✗"
        print(f"{match} {s}  detected={chosen}  expected={expected}  ({note})")
