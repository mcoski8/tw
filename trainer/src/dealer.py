"""
Random 7-card dealer for the trainer.

Cards are represented as two-character strings like "As" (ace of spades),
"Kh" (king of hearts). Ranks: 2..9, T, J, Q, K, A. Suits: c,d,h,s.
This matches the engine's CLI format (see engine/src/card.rs).
"""
from __future__ import annotations

import random
from typing import List

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS = ["c", "d", "h", "s"]


def full_deck() -> List[str]:
    return [r + s for r in RANKS for s in SUITS]


def deal_hand(rng: random.Random | None = None) -> List[str]:
    """Return a random 7-card hand as a list of "Rs" strings."""
    rng = rng or random.SystemRandom()
    return rng.sample(full_deck(), 7)


def card_rank(card: str) -> int:
    """Rank of a card as an integer: 2=2, T=10, A=14."""
    r = card[0]
    if r.isdigit():
        return int(r)
    return {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}[r]


def card_suit(card: str) -> str:
    return card[1]
