# Module: Monte Carlo Engine

## Overview
Estimates the expected value (EV) of a hand setting by sampling random opponents and random boards.

## Algorithm
```
For each of N samples:
    1. From remaining deck (52 - 7 = 45 cards), deal 7 to opponent
    2. Opponent sets their hand using a strategy function
    3. From remaining deck (45 - 7 = 38 cards), deal 10 cards for 2 boards
    4. Score the matchup: my setting vs opponent setting on both boards
    5. Accumulate points

EV = total_points / N
```

## Opponent Strategies
The opponent's hand-setting strategy affects the computed EV. Options:

1. **MiddleFirst:** Best 2-card Hold'em hand in mid, highest remaining on top, rest to bottom. This is the strongest heuristic from our research.

2. **Random:** Uniformly random setting from the 105 options. Useful as baseline.

3. **Optimal (from solver):** Once we've computed best-response tables, opponents can use the computed optimal. This is needed for CFR convergence.

## Parallelization
Monte Carlo is embarrassingly parallel. Use rayon to:
- Parallelize samples within a single setting evaluation
- Parallelize across settings when evaluating all 105 for one hand
- Each thread gets its own RNG (seeded from thread ID for reproducibility)

## Convergence
Standard error of EV estimate: SE = σ / √N
where σ is the standard deviation of per-sample scores.

Typical σ for Taiwanese Poker: ~10-15 points per hand.
- N=100: SE ≈ 1.0-1.5 (rough)
- N=1,000: SE ≈ 0.3-0.5 (good)
- N=10,000: SE ≈ 0.1-0.15 (excellent)

For distinguishing between the best and second-best setting, we need SE small enough that the gap is statistically significant. Adaptive sampling can help: run N=100 first, identify top candidates, then run N=10,000 only on close decisions.
