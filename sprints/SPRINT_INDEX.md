# Sprint Index - Taiwanese Poker Solver

> **Purpose:** Quick overview of all sprints. Read CURRENT_PHASE.md for active work context.

---

## Sprint Status

| Sprint | Name | Phase | Status | Started | Completed |
|--------|------|-------|--------|---------|-----------|
| S0 | Foundation + Lookup Tables | Phase 1: Engine Core | **Completed** | 2026-04-16 | 2026-04-16 |
| S1 | Hand Evaluator (Holdem + Omaha) | Phase 1: Engine Core | Not Started | — | — |
| S2 | Monte Carlo Engine | Phase 1: Engine Core | Not Started | — | — |
| S3 | Best Response Computation | Phase 2: Solving | Not Started | — | — |
| S4 | Hand Bucketing + CFR | Phase 2: Solving | Not Started | — | — |
| S5 | Trainer Application | Phase 3: Trainer | Not Started | — | — |
| S6 | Validation + Comparison | Phase 3: Trainer | Not Started | — | — |
| S7 | Analytics + GTO Extraction | Phase 4: Analytics & Final Output | Not Started | — | — |

---

## Phase Overview

### Phase 1: Engine Core (S0-S2)
Build the fundamental computation engine — card types, hand evaluation (5-card lookup, Hold'em, Omaha), scoring system, and Monte Carlo simulation. This is the foundation everything else depends on. Must be FAST and CORRECT.

### Phase 2: Solving (S3-S4)
Use the engine to compute optimal strategies. S3 computes the best response to a uniform random opponent for all 133M hands — this alone is groundbreaking for Taiwanese Poker. S4 attempts to converge on Nash equilibrium via CFR with hand bucketing.

### Phase 3: Trainer + Validation (S5-S6)
Build the user-facing trainer tool and validate computed strategies against our heuristic strategy guide and against Monte Carlo simulation.

### Phase 4: Analytics & Final Output (S7) — THE ENDGAME
**This is why we built everything else.** The solver produces raw data (133M hands × optimal settings). Sprint 7 transforms that data into the actual solved strategy: pattern mining across every hand category, decision tree construction, validation against the solver (95%+ agreement target), edge case cataloging, and the final GTO strategy guide. Without this phase, the solver is just a database. This phase is what actually solves the game for human use.

---

*Update this file when a sprint's status changes.*
