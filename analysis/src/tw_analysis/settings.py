"""
Card and hand-setting utilities — mirror of ``engine/src/card.rs`` and
``engine/src/setting.rs``.

The Rust solver enumerates the 105 ways to split a 7-card hand into
(top=1, mid=2, bot=4) using an outer loop over the top-card index
(0..7) and an inner double loop over (a, b) with ``a < b`` drawn from
the remaining 6 cards. Middle and bottom tiers are then sorted
descending by the packed card index. The ``best_setting_index`` stored
in a best-response record is the position within this enumeration — to
recover the chosen setting you must supply the 7-card hand in the same
order the Rust engine used.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

NUM_SETTINGS = 105
HAND_SIZE = 7
RANK_MIN = 2  # 2
RANK_MAX = 14  # Ace

_RANK_CHARS = "23456789TJQKA"  # index 0 -> rank 2, index 12 -> rank 14
_SUIT_CHARS = "cdhs"            # 0=Clubs, 1=Diamonds, 2=Hearts, 3=Spades
_CHAR_TO_RANK = {c: r for r, c in enumerate(_RANK_CHARS, start=RANK_MIN)}
_CHAR_TO_SUIT = {c: i for i, c in enumerate(_SUIT_CHARS)}


@dataclass(frozen=True, order=True)
class Card:
    """Packed card matching ``engine/src/card.rs::Card(u8)``.

    ``idx = (rank - 2) * 4 + suit``, in 0..52. Ordering by ``idx`` matches
    the Rust engine's ``cmp`` on ``Card.0`` — the solver uses that ordering
    when sorting mid/bot tiers, so mirroring it is mandatory.
    """

    idx: int

    def __post_init__(self) -> None:
        if not 0 <= self.idx < 52:
            raise ValueError(f"card index {self.idx} out of range 0..52")

    @classmethod
    def from_rank_suit(cls, rank: int, suit: int) -> "Card":
        if not RANK_MIN <= rank <= RANK_MAX:
            raise ValueError(f"rank {rank} out of range {RANK_MIN}..{RANK_MAX}")
        if not 0 <= suit <= 3:
            raise ValueError(f"suit {suit} out of range 0..3")
        return cls((rank - RANK_MIN) * 4 + suit)

    @classmethod
    def parse(cls, s: str) -> "Card":
        if len(s) != 2:
            raise ValueError(f"card string must be 2 chars, got {s!r}")
        r = _CHAR_TO_RANK.get(s[0])
        if r is None:
            raise ValueError(f"bad rank character in {s!r}")
        su = _CHAR_TO_SUIT.get(s[1])
        if su is None:
            raise ValueError(f"bad suit character in {s!r}")
        return cls.from_rank_suit(r, su)

    @property
    def rank(self) -> int:
        return self.idx // 4 + RANK_MIN

    @property
    def suit(self) -> int:
        return self.idx % 4

    def __str__(self) -> str:
        return f"{_RANK_CHARS[self.rank - RANK_MIN]}{_SUIT_CHARS[self.suit]}"

    def __repr__(self) -> str:
        return f"Card({self.idx}, '{self}')"


def parse_hand(s: str) -> list[Card]:
    """Parse a whitespace-separated 7-card string: e.g. 'As Kh Qd Jc Ts 9h 2d'."""
    return [Card.parse(tok) for tok in s.split()]


@dataclass(frozen=True)
class HandSetting:
    top: Card
    mid: tuple[Card, Card]
    bot: tuple[Card, Card, Card, Card]

    def __str__(self) -> str:
        return (
            f"top [{self.top}]  "
            f"mid [{self.mid[0]} {self.mid[1]}]  "
            f"bot [{self.bot[0]} {self.bot[1]} {self.bot[2]} {self.bot[3]}]"
        )

    def all_cards(self) -> tuple[Card, ...]:
        return (self.top, *self.mid, *self.bot)


# Middle-pair enumeration: (a, b) with a in 0..6, b in (a+1)..6. 15 pairs.
_MID_PAIRS: tuple[tuple[int, int], ...] = tuple(
    (a, b) for a in range(6) for b in range(a + 1, 6)
)
assert len(_MID_PAIRS) == 15


def _sort_desc(cards: Iterable[Card]) -> tuple[Card, ...]:
    return tuple(sorted(cards, key=lambda c: c.idx, reverse=True))


def decode_setting(hand: Sequence[Card], index: int) -> HandSetting:
    """
    Return the ``HandSetting`` at ``index`` within the Rust enumeration of
    ``hand`` — without materializing the full 105-element list.

    ``hand`` must be exactly 7 cards, in the same order the Rust engine used
    when producing ``index`` (i.e. canonical-hand order).
    """
    if len(hand) != HAND_SIZE:
        raise ValueError(f"hand must be {HAND_SIZE} cards, got {len(hand)}")
    if not 0 <= index < NUM_SETTINGS:
        raise ValueError(f"setting index {index} out of range 0..{NUM_SETTINGS}")

    top_i, mid_combo_i = divmod(index, 15)
    a, b = _MID_PAIRS[mid_combo_i]

    remaining = [hand[i] for i in range(HAND_SIZE) if i != top_i]
    mid = _sort_desc((remaining[a], remaining[b]))
    bot = _sort_desc(remaining[j] for j in range(6) if j != a and j != b)

    return HandSetting(
        top=hand[top_i],
        mid=(mid[0], mid[1]),
        bot=(bot[0], bot[1], bot[2], bot[3]),
    )


def all_settings(hand: Sequence[Card]) -> list[HandSetting]:
    """
    Enumerate all 105 settings for ``hand`` in the same order as
    ``engine/src/setting.rs::all_settings``.
    """
    if len(hand) != HAND_SIZE:
        raise ValueError(f"hand must be {HAND_SIZE} cards, got {len(hand)}")
    return [decode_setting(hand, i) for i in range(NUM_SETTINGS)]
