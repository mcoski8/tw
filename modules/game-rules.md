# Game Rules & Hand Rankings — Canonical Reference

> **Status:** Authoritative. If this doc disagrees with code, code is wrong.
> **Last verified against authoritative sources:** 2026-04-17
>
> Sources:
> - Texas Hold'em hole-card play: [Wikipedia — Texas hold 'em](https://en.wikipedia.org/wiki/Texas_hold_%27em)
> - Omaha 2+3 rule: [Wikipedia — Omaha hold 'em](https://en.wikipedia.org/wiki/Omaha_hold_%27em)
> - Hand ranking tiebreakers: [Wikipedia — List of poker hands](https://en.wikipedia.org/wiki/List_of_poker_hands)

This document is the single source of truth for:
1. Which hole cards may/must be used in each of our three tiers
2. The poker hand-ranking hierarchy
3. Every per-category tiebreaker rule

These rules are **non-negotiable correctness requirements**. Any change to the evaluator that could alter any assertion in this document is a regression and must be rejected.

---

## 1. Tier-Specific Card-Usage Rules

Our variant deals each player 7 cards and arranges them into three tiers. There are TWO 5-card community boards, and every tier is evaluated independently on each board.

### 1.1 Top Tier — 1 hole card + 5 board cards (Texas Hold'em rules)

- Player sets exactly 1 hole card as their "top".
- On each board, the player's top-tier hand is the **best 5-card poker hand** that can be formed from the 6 available cards (1 hole + 5 board).
- The player **may use the hole card or not** — "playing the board" is legal.
  - Example: Hole = 2♣, Board = A♠ K♠ Q♠ J♠ T♠. Best 5 = A-K-Q-J-T of spades (royal flush) — the 2♣ is unused. Both players play the board → chop.
- Search space: C(6,5) = **6 five-card hands**.

### 1.2 Middle Tier — 2 hole cards + 5 board cards (Texas Hold'em rules)

- Player sets exactly 2 hole cards as their "middle".
- On each board, best 5-card hand from 7 available cards (2 hole + 5 board).
- The player **may use 0, 1, or 2 hole cards** — whichever produces the strongest hand ([Wikipedia](https://en.wikipedia.org/wiki/Texas_hold_%27em): *"A player may use both of their own two hole cards, only one, or none at all."*).
- Subtle cases this enables:
  - **4-to-a-suit board** + 1 suited hole card → **flush legal** (1 hole + 4 board = 5 suited). This is the defining difference from Omaha.
  - **4-to-a-straight board** + 1 connector in hole → **straight legal** (1 hole + 4 board).
  - **Board itself is the best 5** → both players "play the board" → chop unless one player's hole makes a better 5.
- Search space: C(7,5) = **21 five-card hands**.

### 1.3 Bottom Tier — 4 hole cards + 5 board cards (Pot-Limit Omaha rules)

- Player sets exactly 4 hole cards as their "bottom".
- On each board, best 5-card hand formed by using **exactly 2 cards from the 4-card hole AND exactly 3 cards from the 5-card board**.
- Hard requirement ([Wikipedia](https://en.wikipedia.org/wiki/Omaha_hold_%27em)): *"each player's hand is the best five-card hand made from exactly three of the five cards on the board, plus exactly two of the player's own cards."*
- Consequences — every one of these is a **frequent bug source**:
  - **Flushes require TWO suited cards in hole and THREE suited on board.** 4 suited cards in hole + 4 suited cards on board ≠ automatic flush; you still must use 2+3. With 4 hole spades and only 2 board spades, the flush is **impossible** under Omaha rules even though Hold'em would have one.
  - **Straights require TWO hole cards bridging three board cards.** A 4-to-a-straight board + 1 hole-connector does **NOT** make a straight. You need 2 hole cards that, combined with 3 board cards, form 5 consecutive ranks.
  - **Trips/quads in hole cap at 2.** Holding JJJ+5 + any board gives you at most a pair of jacks — the third and fourth J cannot play. Four aces in hole + any board gives at most one pair of aces used (with 1 kicker from hole = 2 hole cards, plus 3 board).
  - **Inverse**: 1 ace in hole + trip aces on board = **quads** (pick A + kicker from hole, all 3 board aces → 4 aces). 0 aces in hole + trip aces on board = trips max.
  - **Playing the board is impossible in Omaha.** You must integrate 2 hole cards.
- Search space: C(4,2) × C(5,3) = 6 × 10 = **60 five-card hands**.

### 1.4 Contrast Summary

| Tier | Hole | Board | Rule | 5-card hands searched |
|------|------|-------|------|-----------------------|
| Top | 1 | 5 | Hold'em: use 0 or 1 from hole | 6 |
| Middle | 2 | 5 | Hold'em: use 0, 1, or 2 from hole | 21 |
| Bottom | 4 | 5 | Omaha PLO: use **exactly 2** from hole + **exactly 3** from board | 60 |

---

## 2. Hand Rankings — High to Low

Our variant uses standard high-only poker rankings (no lowball, no wildcards, no royalties). The 9 categories we implement, strongest to weakest:

| # | Category | Internal const | Description |
|---|----------|----------------|-------------|
| 1 | **Straight Flush** (incl. Royal) | `CAT_STRAIGHT_FLUSH = 9` | 5 consecutive same-suit. Royal = A-K-Q-J-T suited (top of this slot). |
| 2 | **Four of a Kind** | `CAT_QUADS = 8` | 4 cards of same rank + 1 kicker |
| 3 | **Full House** | `CAT_FULL_HOUSE = 7` | 3 of one rank + 2 of another |
| 4 | **Flush** | `CAT_FLUSH = 6` | 5 cards of same suit, not consecutive |
| 5 | **Straight** | `CAT_STRAIGHT = 5` | 5 consecutive ranks, mixed suits |
| 6 | **Three of a Kind** | `CAT_TRIPS = 4` | 3 of one rank + 2 unrelated kickers |
| 7 | **Two Pair** | `CAT_TWO_PAIR = 3` | 2 of one rank + 2 of another + 1 kicker |
| 8 | **One Pair** | `CAT_PAIR = 2` | 2 of one rank + 3 unrelated kickers |
| 9 | **High Card** | `CAT_HIGH = 1` | Nothing above — ranked by all 5 cards |

**Note on "Royal Flush":** A royal flush is *not* a separate category — it is the specific straight flush A-K-Q-J-T. Internally it sits at the top of `CAT_STRAIGHT_FLUSH` because its straight-high rank is Ace (14), which is the largest possible value in that slot. The category-name lookup surfaces it as "Straight Flush" for brevity.

**Note on "Five of a Kind":** Only exists with wild cards. We do not play with wild cards. Not implemented.

---

## 3. Per-Category Tiebreakers

When both hands share a category, the rules below decide the winner. When all these ranks tie, the hands **chop** (split) — which in our scoring system awards 0 points for that matchup (neither player gets the tier's points).

### 3.1 Straight Flush
- Compared by the **high card of the straight**.
- **Wheel special case**: A-2-3-4-5 counts the Ace as LOW, so its high card is the 5 (rank 5, not 14). The wheel is the LOWEST straight flush. A 6-high straight flush (2-3-4-5-6) beats a steel wheel.
- A 7-high sf beats 6-high sf beats 5-high sf (steel wheel).

### 3.2 Four of a Kind (Quads)
- Compared by the **quad rank** first.
- If equal quads (only possible across different 7-card hands with the same 4-rank, e.g. board quads), compared by **kicker rank**.
- Example: A♠ A♥ A♦ A♣ 2♣ beats K♠ K♥ K♦ K♣ Q♣ (quad aces > quad kings).

### 3.3 Full House
- Compared by the **triplet rank** first.
- If equal triplets, compared by the **pair rank**.
- Example: A-A-A-K-K beats K-K-K-A-A (aces-full-of-kings > kings-full-of-aces).

### 3.4 Flush
- Compared **rank-by-rank from highest to lowest**, all 5 cards.
- Example: A-K-Q-J-9 of spades beats A-K-Q-J-8 of spades. If first 4 cards match, the 5th breaks the tie.
- Suits **do not** rank. Two flushes with identical ranks across different suits chop.

### 3.5 Straight
- Compared by the **high card of the straight**.
- Wheel special case: same as straight flush — A-2-3-4-5 is 5-high, the lowest straight.
- A broadway straight (A-K-Q-J-T) is the highest, 14-high.

### 3.6 Three of a Kind (Trips)
- Compared by **trip rank** first.
- Then by **highest kicker**.
- Then by **second-highest kicker**.

### 3.7 Two Pair
- Compared by **top pair rank** first.
- Then **bottom pair rank**.
- Then **fifth-card kicker**.
- Example: A-A-2-2-K beats K-K-Q-Q-J (top pair aces > top pair kings, ignore everything else).

### 3.8 One Pair
- Compared by **pair rank** first.
- Then **kicker 1 (highest of the 3)**.
- Then **kicker 2**.
- Then **kicker 3 (lowest)**.
- All three kickers matter — common source of "I thought I won" errors.

### 3.9 High Card
- Compared **rank-by-rank from highest to lowest**, all 5 cards.
- Example: A-K-Q-J-9 beats A-K-Q-J-8 beats A-K-Q-T-9.

---

## 4. Implementation Verification (as of 2026-04-17)

The implementation in `engine/src/hand_eval.rs` `compute_rank_5` encodes each hand into a `u32` whose bit layout is:

```
bits 24..28  category (1..9)
bits 20..24  primary rank (e.g. quad rank, trip rank, top pair)
bits 16..20  secondary rank (kicker, other pair, pair-in-boat)
bits 12..16  kicker 1
bits  8..12  kicker 2
bits  4.. 8  kicker 3
```

This gives direct integer comparison = poker rank comparison. Every tiebreaker rule in §3 follows from the ordering of fields in this layout.

**Exhaustive verification.** `engine/tests/hand_eval_tests.rs::table_lookup_matches_direct_on_every_hand` computes `compute_rank_5` for **every one of the 2,598,960 possible 5-card hands** and confirms the lookup table agrees. Because `compute_rank_5` is the reference implementation and it covers 100% of the hand space, any rule-violating bug in the 5-card layer would surface at build time.

**Tier-specific verification.**
- Top tier (`eval_top`): drops each of the 6 cards once (including the hole card, which produces the "play-the-board" subset). Correct for "may use 0 or 1 hole cards".
- Middle tier (`eval_middle`): drops every C(7,2) = 21 pair of indices. Includes (drop both hole cards → play the board), (drop one hole + one board → 1 hole card used), (drop two board → both hole cards used). Correct for "may use 0, 1, or 2".
- Omaha (`eval_omaha`): iterates the 6 fixed hole-pair indices × 10 board-drop pairs, producing exactly the 60 hands of form (2 hole + 3 board). Correct for the 2+3 rule.

**Targeted Omaha 2+3 tests** (`engine/tests/omaha_tests.rs`, 15 tests) lock down the most-frequent bug classes from §1.3:
- 4 suited hole + 3 suited board → flush legal
- 4 suited hole + 2 suited board → flush illegal
- 4-to-straight board + 1 connector → no straight
- 4-to-straight board + 2 connectors → straight
- Trips in hole → pair max (cannot use 3rd or 4th matching card)
- Four aces in hole → two pair max (cannot use 3rd or 4th)
- 1 hole ace + trip board aces → quads (1+3 = 4)
- 0 hole aces + trip board aces → trips (cannot pull the 4th ace from nowhere)
- Wheel via 2+3
- Straight flush via 2+3

---

## 5. Invariants

These must always hold:

1. `category(rank)` is exactly one of {1, 2, 3, 4, 5, 6, 7, 8, 9}.
2. For every two valid hand ranks `a` and `b`: `a > b` in u32 comparison iff `a` wins in poker.
3. A chop happens iff `a == b`.
4. The 5-card lookup table has exactly 2,598,960 entries; no hand is missing, no hand is duplicated.
5. The Omaha evaluator never returns a rank that requires using fewer or more than 2 hole cards + 3 board cards.
6. Royal flush is **not** a separate rank — it is always encoded as `(category=9, straight_high=14)`. The display-only `category_name` may surface "Royal Flush" but the comparison value is the straight-flush slot.

---

## 6. Non-Negotiable Correctness Requirements

(These are stated here so future sessions cannot relitigate them.)

- The Omaha 2+3 rule applies *strictly* to the bottom tier only. Top and middle tiers are Hold'em-style.
- The wheel straight (A-2-3-4-5) is the **lowest** straight, not ace-high.
- Flushes do **not** rank by suit. All suits are equal.
- Kickers matter — down to the 5th card in high-card and flush hands, down to the 4th in pair hands, down to the 3rd in trips.
- Playing the board is legal in Top and Middle tiers. Impossible in Omaha bottom.
- Chops award 0 points per tier, per board. A single chop in any of the 6 matchups invalidates the 20-point scoop.
