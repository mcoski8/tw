"""
Rule-chain-grounded explanation layer (v3, post-Sprint-7-Phase-C).

For each hand the trainer compares THREE arrangements:

  * USER  — what the player submitted.
  * CHAIN — what the rule chain for the active profile picks. The chain is
            ``strategy_v3`` for the multiway/mfsuitaware/weighted profiles,
            and the per-profile overlay for OmahaFirst / TopDefensive
            (Sprint 7 Phase C, Session 15). Routed via
            ``encode_rules.strategy_for_profile``.
  * BEST  — what the live MC against the chosen profile says is optimal.

Each finding is grounded in the measured chain-vs-BR shape-agreement for
the active profile and the hand's category, baked into
``CHAIN_AGREEMENT_BY_PROFILE`` below.
"""
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import numpy as np

from trainer.src.dealer import card_rank, card_suit

# Allow tw_analysis + encode_rules import (analysis lives outside trainer).
REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SRC = REPO_ROOT / "analysis" / "src"
ANALYSIS_SCRIPTS = REPO_ROOT / "analysis" / "scripts"
for p in (str(ANALYSIS_SRC), str(ANALYSIS_SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.settings import Card  # noqa: E402
from tw_analysis.features import (  # noqa: E402
    CATEGORY_HIGH_ONLY, CATEGORY_PAIR, CATEGORY_TWO_PAIR,
    CATEGORY_THREE_PAIR, CATEGORY_TRIPS, CATEGORY_TRIPS_PAIR, CATEGORY_QUADS,
    hand_features_scalar, ID_TO_CATEGORY,
)
from encode_rules import (  # noqa: E402
    decode_tier_positions, strategy_for_profile,
)


# Per-profile chain-vs-BR shape-agreement, sourced from
# ``analysis/scripts/encode_rules.py`` and the Session 15 overlay-measurement
# pass. Multiway-robust agreement is from the full-6M run; per-profile
# agreement (mfsa, omaha, topdef, weighted) is from a 300K random sample
# (rng seed 42). Numbers are stable to ~0.05pp at this sample size.
CHAIN_AGREEMENT_BY_PROFILE = {
    # multiway = strategy_v3 vs multiway_robust mode (full 6M).
    "multiway": {
        "overall": 0.5616,
        CATEGORY_HIGH_ONLY:  0.3101,
        CATEGORY_PAIR:       0.6502,
        CATEGORY_TWO_PAIR:   0.6020,
        CATEGORY_THREE_PAIR: 0.7288,
        CATEGORY_TRIPS:      0.5639,
        CATEGORY_TRIPS_PAIR: 0.4612,
        CATEGORY_QUADS:      0.7920,
    },
    # mfsuitaware uses strategy_v3; agreement vs br_mfsuitaware (300K sample).
    "mfsuitaware": {
        "overall": 0.5551,
        CATEGORY_HIGH_ONLY:  0.3120,
        CATEGORY_PAIR:       0.6398,
        CATEGORY_TWO_PAIR:   0.5974,
        CATEGORY_THREE_PAIR: 0.7249,
        CATEGORY_TRIPS:      0.5575,
        CATEGORY_TRIPS_PAIR: 0.4522,
        CATEGORY_QUADS:      0.7984,
    },
    # weighted uses strategy_v3; agreement vs br_weighted (300K sample).
    "weighted": {
        "overall": 0.6198,
        CATEGORY_HIGH_ONLY:  0.3030,
        CATEGORY_PAIR:       0.7751,
        CATEGORY_TWO_PAIR:   0.5877,
        CATEGORY_THREE_PAIR: 0.6045,
        CATEGORY_TRIPS:      0.6348,
        CATEGORY_TRIPS_PAIR: 0.5785,
        CATEGORY_QUADS:      0.8371,
    },
    # omaha uses strategy_omaha_overlay; agreement vs br_omaha (300K sample).
    "omaha": {
        "overall": 0.5469,
        CATEGORY_HIGH_ONLY:  0.2585,
        CATEGORY_PAIR:       0.6349,
        CATEGORY_TWO_PAIR:   0.6325,
        CATEGORY_THREE_PAIR: 0.2996,
        CATEGORY_TRIPS:      0.6034,
        CATEGORY_TRIPS_PAIR: 0.5504,
        CATEGORY_QUADS:      0.8360,
    },
    # topdef uses strategy_topdef_overlay; agreement vs br_topdef (300K sample).
    "topdef": {
        "overall": 0.5014,
        CATEGORY_HIGH_ONLY:  0.2631,
        CATEGORY_PAIR:       0.5830,
        CATEGORY_TWO_PAIR:   0.5415,
        CATEGORY_THREE_PAIR: 0.7386,
        CATEGORY_TRIPS:      0.4951,
        CATEGORY_TRIPS_PAIR: 0.4041,
        CATEGORY_QUADS:      0.7472,
    },
}


def _severity(delta: float) -> Tuple[str, str]:
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
    title: str
    detail: str


@dataclass
class Feedback:
    user_ev: float
    best_ev: float
    delta: float
    severity: str
    severity_phrase: str
    is_match: bool
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# Setting-shape utilities. The "shape" is the rank-only composition of each
# tier — agreement-comparable across suit-equivalent settings.
# ---------------------------------------------------------------------------

def _hand_to_bytes_sorted(hand_strs: List[str]) -> np.ndarray:
    arr = np.array([Card.parse(s).idx for s in hand_strs], dtype=np.uint8)
    arr.sort()
    return arr


def _shape_from_cards(cards: List[str]) -> tuple:
    """(top_rank, sorted_mid_ranks_tuple, sorted_bot_ranks_tuple)."""
    top_r = card_rank(cards[0])
    mid_rs = tuple(sorted([card_rank(c) for c in cards[1:3]]))
    bot_rs = tuple(sorted([card_rank(c) for c in cards[3:7]]))
    return (top_r, mid_rs, bot_rs)


def _chain_arrangement(hand_strs: List[str], profile_id: str) -> List[str]:
    """Apply the active profile's chain and return cards in trainer order
    [top, m1, m2, b1..b4]."""
    sorted_bytes = _hand_to_bytes_sorted(hand_strs)
    setting_idx = strategy_for_profile(sorted_bytes, profile_id)
    top_pos, mid_pos, bot_pos = decode_tier_positions(setting_idx)
    sorted_cards = [str(Card(int(b))) for b in sorted_bytes]
    return [
        sorted_cards[top_pos],
        sorted_cards[mid_pos[0]], sorted_cards[mid_pos[1]],
        sorted_cards[bot_pos[0]], sorted_cards[bot_pos[1]],
        sorted_cards[bot_pos[2]], sorted_cards[bot_pos[3]],
    ]


def _hand_category(hand_strs: List[str]) -> str:
    bytes_ = [Card.parse(s).idx for s in hand_strs]
    hf = hand_features_scalar(bytes_)
    return ID_TO_CATEGORY[int(hf["category_id"])]


# ---------------------------------------------------------------------------
# Per-tier diff: which tier(s) of two settings have a different rank shape.
# ---------------------------------------------------------------------------

def _diff_tiers(s_a: tuple, s_b: tuple) -> List[str]:
    out = []
    if s_a[0] != s_b[0]:
        out.append("top")
    if s_a[1] != s_b[1]:
        out.append("middle")
    if s_a[2] != s_b[2]:
        out.append("bottom")
    return out


def _rank_seq(ranks: tuple) -> str:
    return "-".join(_RANK_NAMES[r] for r in ranks)


_RANK_NAMES = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
    10: "T", 11: "J", 12: "Q", 13: "K", 14: "A",
}


def _shape_phrase(s: tuple) -> str:
    return (
        f"top {_RANK_NAMES[s[0]]} | "
        f"mid {_rank_seq(s[1])} | "
        f"bot {_rank_seq(s[2])}"
    )


def _category_label(cat: str) -> str:
    return {
        CATEGORY_HIGH_ONLY:  "no-pair",
        CATEGORY_PAIR:       "pair",
        CATEGORY_TWO_PAIR:   "two-pair",
        CATEGORY_THREE_PAIR: "three-pair",
        CATEGORY_TRIPS:      "trips",
        CATEGORY_TRIPS_PAIR: "trips+pair (full-house shape)",
        CATEGORY_QUADS:      "quads",
    }.get(cat, cat)


# ---------------------------------------------------------------------------
# Supplementary structural detector (kept from v1 — still useful regardless
# of rule-chain comparison).
# ---------------------------------------------------------------------------

def _is_double_suited(tier_cards) -> bool:
    counts = sorted(Counter(card_suit(c) for c in tier_cards).values(),
                    reverse=True)
    return len(counts) >= 2 and counts[0] == 2 and counts[1] == 2


def _detect_isolated_bottom_suit(user: List[str], best: List[str]) -> Finding | None:
    u_bot, b_bot = user[3:7], best[3:7]
    if _is_double_suited(b_bot) and not _is_double_suited(u_bot):
        return Finding(
            title="Your bottom isn't double-suited.",
            detail=(
                "Omaha's 2+3 rule means the strongest bottom holdings have "
                "two pairs of suits (e.g. 2 spades + 2 hearts), giving you "
                "two independent flush draws. The solver found a 2+2 "
                "arrangement of your bottom cards."
            ),
        )
    u_sc = Counter(card_suit(c) for c in u_bot)
    b_sc = Counter(card_suit(c) for c in b_bot)
    if any(v >= 3 for v in u_sc.values()) and not any(v >= 3 for v in b_sc.values()):
        return Finding(
            title="You put 3+ of one suit in the bottom.",
            detail=(
                "Omaha lets you use only 2 of your 4 hole cards, so the "
                "3rd or 4th card of a suit can never reach the flush — "
                "those cards are wasted."
            ),
        )
    return None


# ---------------------------------------------------------------------------
# Core: build_feedback — three-way comparison + rule-chain context.
# ---------------------------------------------------------------------------

def build_feedback(
    user_cards: List[str],
    best_cards: List[str],
    user_ev: float,
    best_ev: float,
    is_match: bool,
    profile_id: str = "multiway",
) -> Feedback:
    delta = best_ev - user_ev
    severity, phrase = _severity(delta)

    # All 7 cards in play (ranks identical regardless of where the user put them).
    hand_strs = list(user_cards)

    chain_cards = _chain_arrangement(hand_strs, profile_id)
    chain_shape = _shape_from_cards(chain_cards)
    user_shape = _shape_from_cards(user_cards)
    best_shape = _shape_from_cards(best_cards)

    cat = _hand_category(hand_strs)
    profile_table = CHAIN_AGREEMENT_BY_PROFILE.get(
        profile_id, CHAIN_AGREEMENT_BY_PROFILE["multiway"])
    chain_acc = profile_table.get(cat, profile_table["overall"])
    cat_label = _category_label(cat)

    user_eq_chain = (user_shape == chain_shape)
    user_eq_best = (user_shape == best_shape)
    chain_eq_best = (chain_shape == best_shape)

    findings: List[Finding] = []

    if user_eq_best and chain_eq_best:
        # User matches both. Strongest possible signal.
        findings.append(Finding(
            title="Solver, rule chain, and your pick all agree.",
            detail=(
                f"The rule chain hits the solver's optimal on "
                f"{100*chain_acc:.0f}% of {cat_label} hands; this is one of "
                f"them, and you found it."
            ),
        ))
    elif user_eq_chain and not chain_eq_best:
        # User followed the chain but solver disagrees (~rule-chain failure).
        findings.append(Finding(
            title="You followed the rule chain — this hand is one of its misses.",
            detail=(
                f"The rule chain matches the solver on {100*chain_acc:.0f}% "
                f"of {cat_label} hands; this hand is in the remaining "
                f"{100*(1-chain_acc):.0f}%. Solver's pick: "
                f"{_shape_phrase(best_shape)}."
            ),
        ))
    elif user_eq_best and not user_eq_chain:
        # User beat the chain by finding the solver's answer.
        findings.append(Finding(
            title="You picked the solver's answer — better than the rule chain.",
            detail=(
                f"On {cat_label} hands the rule chain matches the solver "
                f"{100*chain_acc:.0f}% of the time; here it picked "
                f"{_shape_phrase(chain_shape)} but the solver wanted "
                f"{_shape_phrase(best_shape)}, which is what you played."
            ),
        ))
    elif chain_eq_best and not user_eq_chain:
        # Solver and chain agree, user differs.
        diffs = _diff_tiers(user_shape, best_shape)
        diff_str = ", ".join(diffs) if diffs else "tier composition"
        findings.append(Finding(
            title=(f"Your {diff_str} differs from both the rule chain and "
                   f"the solver."),
            detail=(
                f"Both agree on {_shape_phrase(best_shape)}. The rule chain "
                f"matches the solver on {100*chain_acc:.0f}% of {cat_label} "
                f"hands — this is one of those clean cases."
            ),
        ))
    else:
        # All three differ. Hardest case.
        findings.append(Finding(
            title="Your pick differs from both the rule chain and the solver.",
            detail=(
                f"Rule chain: {_shape_phrase(chain_shape)}. "
                f"Solver: {_shape_phrase(best_shape)}. "
                f"You played: {_shape_phrase(user_shape)}. "
                f"On {cat_label} hands the rule chain matches the solver "
                f"{100*chain_acc:.0f}% of the time, so neither line is "
                f"obviously dominant — likely an opponent-dependent decision."
            ),
        ))

    # Per-tier diff vs solver as a separate, concrete finding when not a match.
    if not user_eq_best:
        tier_diffs = _diff_tiers(user_shape, best_shape)
        if tier_diffs:
            findings.append(Finding(
                title=f"Different tier(s) from solver: {', '.join(tier_diffs)}.",
                detail=(
                    f"Your shape: {_shape_phrase(user_shape)}.  "
                    f"Solver shape: {_shape_phrase(best_shape)}."
                ),
            ))

    # Always-relevant supplementary detector: bottom-suit composition.
    bot_finding = _detect_isolated_bottom_suit(user_cards, best_cards)
    if bot_finding is not None:
        findings.append(bot_finding)

    if is_match:
        summary = (
            f"Perfect — your arrangement matches the solver (EV {best_ev:+.3f})."
        )
    elif delta < 0.01:
        summary = (
            f"Your arrangement differs from the solver but EVs are essentially "
            f"tied ({user_ev:+.3f} vs {best_ev:+.3f})."
        )
    else:
        summary = (
            f"Your EV was {user_ev:+.3f}; the solver's best was "
            f"{best_ev:+.3f} — a {phrase} of {delta:+.3f} points. "
            f"This is a {cat_label} hand; the rule chain matches the solver "
            f"{100*chain_acc:.0f}% of the time on this category."
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
