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
| S7 | Analytics + GTO Extraction | Phase 4: Analytics & Final Output | **In Progress** — v34_dt is current ML champion ($1,681/1000h on full grid, $889 on prefix; 874K leaves, 83 features at depth=34 ml=2). 9 gating-template wins shipped (high_only-via-suited/v20, trips_pair/v23, composite/v24, pair-v1/v25, two_pair/v26, high_only-direct/v27, pair-v2/v29, trips/v30, trips_v2/v32) plus 2 capacity-only ships (v31, v34). v38_rule8_qp is current production human strategy ($2,868 full grid). v35_rule6_v3 is the human-guide strategy of record for trips. | 2026-05-02 | — |
| S8 | Methodology refinement + rule chain extension | Phase 4: Analytics & Final Output | **Active** — Sessions 36–42 produced Rule 6 (+$112/1000h vs v28), Rule 7 (three_pair, +$43), Rule 8 (composite quads_pair, +$9.42 — both grids positive), four ML champion iterations (v30 → v34), and the Session 42 prefix-regression-as-generalization-gate methodology rule (a rule with prefix loss >2× the full-grid lift does NOT ship, even with a clean per-cell breakdown). | 2026-05-04 | — |

> Active sprint at end of Session 42 (2026-05-08): **Sprint 8 — Methodology refinement + rule chain extension**. v34_dt is the current ML champion. v38_rule8_qp is the current production human strategy (Decision 074, +$9.42/1000h vs v37 on full grid + +$19/1000h on prefix). A two_pair Rule 8 candidate (+$197 full, -$512 prefix) was DEFERRED. New methodology rule: a rule with prefix regression >2× the full-grid lift does NOT ship. See CURRENT_PHASE.md for the Session 43 resume prompt.

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
