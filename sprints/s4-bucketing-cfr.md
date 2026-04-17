# Sprint 4: Hand Bucketing + CFR

> **Phase:** Phase 2 - Solving
> **Status:** NOT STARTED

---

## Sprint Goals

Move from "best response to random" toward true Nash equilibrium using Counterfactual Regret Minimization (CFR) with hand abstraction (bucketing).

1. Define hand feature vector for bucketing
2. Cluster hands into buckets using k-means or similar
3. Implement CFR algorithm over bucketed game
4. Iterate until convergence (regret minimization)
5. Extract Nash equilibrium strategy (mixed strategy over settings per bucket)
6. Validate: CFR strategy vs best-response strategy performance comparison

---

## Tasks

### Hand Bucketing
| Task | Status | Notes |
|------|--------|-------|
| Define hand features: pair rank, pair count, high card, connectivity, suitedness, suited count, double suited | Pending | |
| Implement feature extraction for any 7-card hand | Pending | |
| Run k-means clustering with k=1000, 5000, 10000 | Pending | |
| Evaluate bucket quality: hands in same bucket should have similar optimal settings | Pending | |

### CFR Implementation
| Task | Status | Notes |
|------|--------|-------|
| Implement regret tracking per bucket per setting | Pending | 10,000 buckets × 105 settings = ~1M entries |
| Implement strategy update via regret matching | Pending | |
| Implement CFR iteration loop | Pending | |
| Convergence metric: average regret < threshold | Pending | |
| Run 10,000+ iterations | Pending | |
| Extract final strategy: probability distribution over settings per bucket | Pending | |

### Validation
| Task | Status | Notes |
|------|--------|-------|
| Compare CFR strategy vs best-response strategy | Pending | |
| Head-to-head: CFR vs MiddleFirst, 10K+ hands | Pending | |
| Head-to-head: CFR vs best-response, 10K+ hands | Pending | |
| Measure exploitability of CFR strategy | Pending | |

---

## Session Log
