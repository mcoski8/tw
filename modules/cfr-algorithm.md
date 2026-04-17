# Module: Counterfactual Regret Minimization (CFR)

## Overview
CFR is the standard algorithm for computing Nash equilibria in poker. It iteratively self-plays, tracks regret for each action, and converges to equilibrium strategy.

## Taiwanese Poker CFR

### Game Structure
- Simultaneous move game (both players set hands at the same time)
- Each player has 105 possible actions (settings)
- Payoff determined by settings + random boards

### For simultaneous games, CFR simplifies to:
```
For each iteration:
    For each player:
        For each hand bucket:
            Compute strategy from regrets (regret matching)
            For each action (setting):
                Compute expected payoff of this action vs opponent's current strategy
            Update regrets: regret[action] += payoff[action] - expected_payoff
    
    Average strategy over all iterations → Nash equilibrium
```

### Regret Matching
```
strategy[action] = max(0, regret[action]) / sum(max(0, regret[a]) for a in actions)
```
If all regrets are negative, use uniform random strategy.

### Storage
- Regret table: num_buckets × 105 floats = ~600K entries for 6K buckets
- Strategy table: same size
- Total: ~5MB. Easily fits in memory.

### Convergence
- Exploitability decreases as 1/√T where T is number of iterations
- Typical: 10,000-100,000 iterations for good convergence
- Monitor: average regret per bucket per iteration
