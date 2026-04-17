# Module: Scoring System

## Overview
Compares two players' hand settings against two community boards and computes point totals.

## Scoring Rules

### Per-Board, Per-Tier Matchups
Each tier is evaluated independently on each board:
- Top (1pt): Player 1's top card vs Player 2's top card, using the board
- Middle (2pt): Player 1's 2 mid cards vs Player 2's 2 mid cards, using the board
- Bottom (3pt): Player 1's 4 bot cards vs Player 2's 4 bot cards, using the board (Omaha rules)

### Outcomes Per Matchup
- **Win:** Player with higher HandRank gets the tier's point value
- **Lose:** Opponent gets the points
- **Chop:** Both hands evaluate to equal HandRank → 0 points for both

### Scoop Rule
If one player wins ALL 6 matchups (3 tiers × 2 boards) with ZERO chops:
- Winner gets 20 points total (not the normal 12)
- Loser loses 20 points
- ANY chop on ANY matchup invalidates the scoop → normal scoring applies

### Implementation
```
fn score_matchup(
    p1: &HandSetting,
    p2: &HandSetting,
    board1: &[Card; 5],
    board2: &[Card; 5],
) -> (i32, i32)  // (p1_points, p2_points)
```

1. Evaluate all 6 matchups (3 tiers × 2 boards)
2. Track p1_wins, p2_wins, chops for each
3. If p1_wins == 6 && chops == 0: return (20, -20)
4. If p2_wins == 6 && chops == 0: return (-20, 20)
5. Otherwise: sum up normal points per tier
