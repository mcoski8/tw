# Module: Hand Evaluation

> **Rules authority:** this module documents the *implementation*. The
> *rules* — which hole cards may/must be used per tier, full tiebreaker
> hierarchy, all invariants — live in [`modules/game-rules.md`][rules].
> If this doc disagrees with game-rules.md, game-rules.md wins.
>
> [rules]: ./game-rules.md

## Overview
The hand evaluator is the innermost loop of the entire solver. It must be extremely fast (<50ns for a 5-card eval) because it runs billions of times during Monte Carlo and CFR computation.

## 5-Card Evaluation
Use a pre-computed lookup table mapping every possible 5-card hand to a rank integer. Higher integer = stronger hand.

**Hand ranking (highest to lowest):**
1. Royal Flush (10)
2. Straight Flush (9)
3. Four of a Kind (8)
4. Full House (7)
5. Flush (6)
6. Straight (5)
7. Three of a Kind (4)
8. Two Pair (3)
9. One Pair (2)
10. High Card (1)

Within each category, hands are sub-ranked by relevant card values (e.g., pair of Aces beats pair of Kings; AAKK2 beats AAQQ2).

**Lookup table construction:**
- Enumerate all C(52,5) = 2,598,960 five-card combinations
- Compute hand rank for each using standard poker rules
- Store as array indexed by a hash of the 5 cards
- Two-plus-two style: use sequential card indexing for O(1) lookup

**Special cases:**
- A-2-3-4-5 (wheel) is the lowest straight, NOT ace-high
- Suits are irrelevant for ranking EXCEPT for flush detection
- All suits are equal (no suit ranking for non-flush hands)

## Tier-Specific Evaluation

### Top Tier (1 card + 5 board)
```
eval_top(hole: Card, board: [Card;5]) -> HandRank
```
6 total cards. Try all C(6,5) = 6 five-card combinations. Return the best.

### Middle Tier (2 cards + 5 board)
```
eval_middle(hole: [Card;2], board: [Card;5]) -> HandRank
```
7 total cards. Try all C(7,5) = 21 five-card combinations. Return the best.
Standard Texas Hold'em evaluation.

### Bottom Tier — OMAHA (4 cards + 5 board)
```
eval_omaha(hole: [Card;4], board: [Card;5]) -> HandRank
```
**CRITICAL: Must use EXACTLY 2 from hole and EXACTLY 3 from board.**
- Enumerate all C(4,2) = 6 two-card combos from hole
- For each, enumerate all C(5,3) = 10 three-card combos from board
- Total: 6 × 10 = 60 five-card hands to evaluate
- Return the best

**Common Omaha mistakes to test against:**
- Player has 4 spades, board has 3 spades → flush ONLY if 2 of player's spades + 3 board spades form 5 suited cards
- Player has 4 cards to a straight on board → straight ONLY if 2 from hand + 3 from board form the straight
- Player has trips in hand (e.g., JJJ + 5) → can only use 2 jacks from hand, so best is JJ + 3 board cards

## Performance Requirements
| Operation | Target | Method |
|-----------|--------|--------|
| 5-card lookup | <50ns | Hash table lookup |
| Top eval (6 cards) | <100ns | 6 lookups |
| Middle eval (7 cards) | <200ns | 21 lookups |
| Omaha eval (9 cards) | <500ns | 60 lookups |
