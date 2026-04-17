# Module: Trainer UI

## Overview
Interactive training tool where users practice setting Taiwanese Poker hands.

## Core Flow
1. Load optimal settings database (from engine output)
2. Deal random 7-card hand
3. Display hand to user with card graphics
4. User selects: which card on top, which 2 in middle, which 4 on bottom
5. Compare user's setting against computed optimal
6. Display result: correct/incorrect, EV difference, tier breakdown
7. Track statistics over time

## Display Format (CLI)
```
Your hand: K♠ J♥ T♠ T♥ 9♦ 8♣ 6♦

Set your hand:
  Top (1 card):    [user selects]
  Middle (2 cards): [user selects]
  Bottom (4 cards): [auto-filled]

Optimal: K top | TT mid | J986 bot
Your set: J top | KT mid | T986 bot
Result: SUBOPTIMAL (-$1.20 EV per hand)
  Top: J vs K → you lose $0.30
  Mid: KTo vs TT → you lose $0.60
  Bot: T986 vs J986 → you gain $0.10 but not enough
```

## Statistics Tracking
- Total hands played
- Accuracy rate (% matching optimal)
- Average EV loss when wrong
- Accuracy by hand type (pairs, trips, unpaired, etc.)
- Most common mistake categories
- Improvement trend over last 50/100/500 hands
