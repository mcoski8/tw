"""
Heuristic explanation layer (v1, pre-Sprint-7).

Given the user's submitted arrangement, the solver's best arrangement, and
the full 105-setting EV table, produce human-readable feedback:

  * Severity tag (trivial / minor / moderate / major) based on EV delta
  * Concrete structural diff: which cards moved between tiers
  * A small library of common-mistake detectors that fire when a pattern
    is present in the user's arrangement but not in the best arrangement

This is NOT solver-derived pattern mining. That's Sprint 7, when all 4
opponent models are on disk. The rules below are hand-written heuristics
based on the game rules and the Omaha 2+3 constraint. They'll be replaced
or augmented as Sprint 7 mines real patterns from the .bin data.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple

from trainer.src.dealer import card_rank, card_suit


def _severity(delta: float) -> Tuple[str, str]:
    """Return (tag, plain-English phrase) based on EV gap in points.

    Phrase does NOT include a leading article — the caller wraps it.
    """
    d = abs(delta)
    if d < 0.10:
        return "trivial", "essentially equivalent to the solver's pick"
    if d < 0.50:
        return "minor", "small EV miss"
    if d < 2.00:
        return "moderate", "meaningful EV miss"
    return "major", "large EV miss — this hand has a much better arrangement"


@dataclass
class Finding:
    """One observation for the user. Ordered most-severe-first in output."""
    title: str            # one-line headline, e.g. "You split a pair."
    detail: str           # longer plain-English description


@dataclass
class Feedback:
    user_ev: float
    best_ev: float
    delta: float          # best_ev - user_ev (>= 0)
    severity: str         # "trivial" | "minor" | "moderate" | "major"
    severity_phrase: str  # human-readable
    is_match: bool        # True iff user's setting index matches best
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""     # one-paragraph synthesis


def _tiers(cards: List[str]) -> Tuple[str, Tuple[str, str], Tuple[str, str, str, str]]:
    return cards[0], (cards[1], cards[2]), (cards[3], cards[4], cards[5], cards[6])


def _find_pairs(cards: List[str]) -> List[str]:
    """Return list of ranks (as strings) that appear ≥2 times in the given cards."""
    rank_count = Counter(card_rank(c) for c in cards)
    return [r for r, n in rank_count.items() if n >= 2]


def _tier_of(card: str, cards: List[str]) -> str:
    i = cards.index(card)
    if i == 0:
        return "top"
    if i in (1, 2):
        return "middle"
    return "bottom"


def _suit_counts(tier_cards) -> Counter:
    return Counter(card_suit(c) for c in tier_cards)


# --------------------------------------------------------------------------
# Detectors. Each returns a Finding or None, comparing user vs best.
# --------------------------------------------------------------------------

def detect_split_pair(user: List[str], best: List[str]) -> Finding | None:
    """User split a pair across tiers that the solver kept together."""
    best_pairs = _find_pairs(best)
    user_pairs = _find_pairs(user)
    # Pairs the solver DID play together.
    for rank_val in best_pairs:
        pair_cards_in_best = [c for c in best if card_rank(c) == rank_val]
        best_tiers = {_tier_of(c, best) for c in pair_cards_in_best}
        if len(best_tiers) > 1:
            continue  # solver also split this pair — not a user-specific error
        # How did the user place them?
        pair_cards_in_user = [c for c in user if card_rank(c) == rank_val]
        user_tiers = {_tier_of(c, user) for c in pair_cards_in_user}
        if len(user_tiers) > 1:
            rank_names = {14: "aces", 13: "kings", 12: "queens", 11: "jacks", 10: "tens"}
            name = rank_names.get(rank_val, f"{rank_val}s")
            return Finding(
                title=f"You split a pair of {name}.",
                detail=(
                    f"The solver kept the pair of {name} together in one tier. "
                    "Pairs usually produce more EV when combined — two of a "
                    "rank in Omaha (bottom) qualify as the hand's two 'from hole' "
                    "cards, and in Hold'em tiers (top/middle) they form a pair "
                    "immediately regardless of board."
                ),
            )
    _ = user_pairs  # reserved for a future "you created a pair that shouldn't exist" check
    return None


def detect_isolated_bottom_suit(user: List[str], best: List[str]) -> Finding | None:
    """
    In Omaha (bottom), you must use EXACTLY 2 from hole + 3 from board.
    A tier with 0, 1, or 3+ cards of a suit has no 'clean' flush
    contribution. Specifically:
      * 0-suited of any suit: no flush possible in that suit.
      * 1-suited: no flush possible (need 2 from hole).
      * 3+-suited of one suit: you only ever use 2, so the extras are
        burned cards removed from the deck for nothing.
    The strongest Omaha configuration is double-suited (2+2) — two flush
    draws. If the solver's bottom has a double-suited layout and yours
    doesn't, call that out.
    """
    u_bot = user[3:7]
    b_bot = best[3:7]
    u_sc = _suit_counts(u_bot)
    b_sc = _suit_counts(b_bot)

    def is_double_suited(sc: Counter) -> bool:
        vals = sorted(sc.values(), reverse=True)
        return vals[:2] == [2, 2]

    if is_double_suited(b_sc) and not is_double_suited(u_sc):
        return Finding(
            title="Your bottom isn't double-suited.",
            detail=(
                "Omaha's 2+3 rule means the strongest bottom holdings have "
                "two pairs of suits (e.g. two spades + two hearts), giving "
                "you two independent flush draws. The solver found a way to "
                "arrange your four bottom cards as 2+2. Look for suit pairs "
                "when setting the bottom."
            ),
        )

    def has_three_of_a_suit(sc: Counter) -> bool:
        return any(v >= 3 for v in sc.values())

    if has_three_of_a_suit(u_sc) and not has_three_of_a_suit(b_sc):
        return Finding(
            title="You put 3+ of one suit in the bottom.",
            detail=(
                "In Omaha you only ever use 2 of your 4 hole cards, so the "
                "3rd (or 4th) card of a suit can never reach the flush. "
                "Those extras also remove suited cards from the deck, "
                "shrinking the board's chance of cooperating. The solver "
                "spread the suits more evenly."
            ),
        )
    return None


def detect_wrong_top_card(user: List[str], best: List[str]) -> Finding | None:
    """
    Top is a 1-card Hold'em tier. The solver's top is almost always one of
    the two highest cards in the hand (often the Ace). If the user put a
    notably weaker card on top, flag it.
    """
    if user[0] == best[0]:
        return None
    user_top_rank = card_rank(user[0])
    best_top_rank = card_rank(best[0])
    if best_top_rank - user_top_rank >= 2:
        return Finding(
            title=f"You put {user[0]} on top instead of a higher card.",
            detail=(
                f"The solver chose {best[0]} for the top tier — it's "
                f"{best_top_rank - user_top_rank} rank(s) stronger. Top plays "
                "as 1-card Hold'em (uses the 5-card board), so the single "
                "card's own rank matters most. Lower cards play the board "
                "more often and chop."
            ),
        )
    return None


def detect_tier_swap(user: List[str], best: List[str]) -> Finding | None:
    """
    If the user's middle and bottom are internally strong in total rank but
    in the wrong tier (e.g. their strongest 4 are in middle/top rather than
    bottom), note that swapping tiers would help.
    """
    u_mid_ranks = [card_rank(c) for c in user[1:3]]
    u_bot_ranks = [card_rank(c) for c in user[3:7]]
    b_mid_ranks = [card_rank(c) for c in best[1:3]]
    b_bot_ranks = [card_rank(c) for c in best[3:7]]

    if sorted(u_mid_ranks) == sorted(b_bot_ranks[:2]) and \
       sorted(u_bot_ranks)[-2:] == sorted(b_mid_ranks):
        return Finding(
            title="You may have the middle and bottom tiers swapped.",
            detail=(
                "Your middle cards look like the solver's bottom-pair "
                "selections and vice versa. Bottom scores 3 points per board "
                "(vs 2 for middle), so stronger pairings generally belong "
                "there — unless the Omaha 2+3 rule makes them less effective "
                "than in Hold'em middle."
            ),
        )
    return None


# --------------------------------------------------------------------------
# Entry point.
# --------------------------------------------------------------------------

def build_feedback(
    user_cards: List[str],
    best_cards: List[str],
    user_ev: float,
    best_ev: float,
    is_match: bool,
) -> Feedback:
    delta = best_ev - user_ev
    severity, phrase = _severity(delta)

    findings: List[Finding] = []
    if not is_match:
        for detector in (
            detect_split_pair,
            detect_isolated_bottom_suit,
            detect_wrong_top_card,
            detect_tier_swap,
        ):
            f = detector(user_cards, best_cards)
            if f is not None:
                findings.append(f)

    if is_match:
        summary = (
            f"Perfect — your arrangement matches the solver's best response "
            f"(EV {best_ev:+.3f}). "
        )
    else:
        if delta < 0.01:
            summary = (
                f"Your arrangement isn't identical to the solver's, but the "
                f"EVs are essentially tied ({user_ev:+.3f} vs {best_ev:+.3f}, "
                f"delta {delta:+.3f})."
            )
        else:
            summary = (
                f"Your EV was {user_ev:+.3f}; the solver's best was "
                f"{best_ev:+.3f} — a {phrase} of {delta:+.3f} points."
            )

    return Feedback(
        user_ev=user_ev,
        best_ev=best_ev,
        delta=delta,
        severity=severity,
        severity_phrase=phrase,
        is_match=is_match,
        findings=findings,
        summary=summary,
    )
