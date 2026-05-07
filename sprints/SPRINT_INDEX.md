# Sprint Index - Taiwanese Poker Solver

> **Purpose:** Quick overview of all sprints. Read CURRENT_PHASE.md for active work context.

---

## Sprint Status

| Sprint | Name | Phase | Status | Started | Completed |
|--------|------|-------|--------|---------|-----------|
| S0 | Foundation + Lookup Tables | Phase 1: Engine Core | **Completed** | 2026-04-16 | 2026-04-16 |
| S1 | Hand Evaluator (Holdem + Omaha) | Phase 1: Engine Core | **Completed** | 2026-04-16 | 2026-04-16 |
| S2 | Monte Carlo Engine | Phase 1: Engine Core | **Completed** | 2026-04-17 | 2026-04-17 |
| S3 | Best Response Computation | Phase 2: Solving | **Completed** (Full Oracle Grid 6M × N=200 + 500K-prefix N=1000) | 2026-04-17 | 2026-05-02 |
| S4 | Hand Bucketing + CFR | Phase 2: Solving | Deferred (oracle-grid + DT pipeline supersedes for Tier-1 best-response goal) | — | — |
| S5 | Trainer Application | Phase 3: Trainer | Not Started | — | — |
| S6 | Validation + Comparison | Phase 3: Trainer | Not Started | — | — |
| S7 | Analytics + GTO Extraction | Phase 4: Analytics & Final Output | **In Progress** — v34_dt is current ML champion ($1,681/1000h on full grid, $889 on prefix; 874K leaves, 83 features at depth=34 ml=2). 9 gating-template wins shipped (high_only-via-suited/v20, trips_pair/v23, composite/v24, pair-v1/v25, two_pair/v26, high_only-direct/v27, pair-v2/v29, trips/v30, trips_v2/v32) plus 2 capacity-only ships (v31, v34). v33_rule6_trips is current production human strategy ($2,920 full grid). v35_rule6_v3 is the human-guide strategy of record (oracle-bound ceiling +$8.12/1000h vs v33). | 2026-05-02 | — |
| S8 | Methodology refinement + rule chain extension | Phase 4: Analytics & Final Output | **Active** — Sessions 36–39 produced Rule 6 (largest single rule ship in project history at +$112/1000h vs v28), four ML champion iterations (v30 → v34), and the Session 39 two-track-ship methodology (human guide can be sharper than production bot when heuristic is rate-limiting). | 2026-05-04 | — |

> Active sprint at end of Session 39 (2026-05-07): **Sprint 8 — Methodology refinement + rule chain extension**. v34_dt is the current ML champion. v35_rule6_v3 ships in STRATEGY_GUIDE.md as the human strategy of record (Decision 071); production runtime keeps v33 until a learned A-variant heuristic closes the heuristic-A gap (Priority C in CURRENT_PHASE.md). New methodology rule: human strategy guide can be sharper than production heuristic when heuristic-A is the rate-limiting step. See CURRENT_PHASE.md for the Session 40 resume prompt.

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
