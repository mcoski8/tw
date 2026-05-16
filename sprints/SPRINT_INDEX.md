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
| S7 | Analytics + GTO Extraction | Phase 4: Analytics & Final Output | **Largely subsumed by S8** — v41_dt is current ML champion ($1,270/1000h full / $686 prefix; 2.02M leaves, 95 features at depth=36 ml=1). 11 gating-template wins shipped through S55. | 2026-05-02 | — |
| S8 | Methodology refinement + rule chain extension + diagnostic-driven feature engineering | Phase 4: Analytics & Final Output | **Active** — Sessions 36–55 produced 17 production rules in the human-memorizable chain (v52_full_high_only_handler at $2,498 full / $1,522 prefix) and 6 ML champion iterations (v32 → v34 → v36 → v39 → v40 → v41) totaling −$445 full / −$218 prefix cumulative. Major methodology breakthrough in S54: diagnostic-driven feature engineering (Phase 1 drill → Phase 1b hand-level → 4 rank-valued conditional features → train) shipped v39_dt +$237 over the pair zone. S55 validated the playbook is transferable: v40_dt (trips_pair, +$18 full / +$29 prefix, −69% within-cat) + v41_dt (two_pair, +$124 full / +$86 prefix, −60% within-cat) in one session. Other methodology rules established: prefix regression >2× the full-grid lift does NOT ship; boolean features redundant at ml=1 saturation; feature design beats hyperparameter tuning at saturation; asymmetric existing features signal blind spots. | 2026-05-04 | — |

> Active sprint at end of Session 55 (2026-05-10): **Sprint 8 — Methodology refinement + rule chain extension + diagnostic-driven feature engineering**. v41_dt is the current ML champion ($1,270 full / $686 prefix; 95 features, 2.02M leaves at depth=36 ml=1). v52_full_high_only_handler is the current production human strategy ($2,498 full / $1,522 prefix; 17 rules; UNCHANGED since S53). The two production tracks diverge by $1,228/1000h. Next-session target: **high_only zone** ($2,796/1000h within-cat × 40.4% share = $1,131 whole-grid = ~63% of v41's total regret). See CURRENT_PHASE.md for the Session 56 resume prompt.

> **End of Session 90 (2026-05-15) — Sprint 8 ACTIVE.** v44_dt is the current ML champion ($1,081 full / $686 prefix; 107 features, 2.25M leaves at depth=36 ml=1; UNCHANGED for 18 sessions, since S58). v64_high_only_chain_fix_zone is the current production rule chain ($1,627.36 full / $776.88 prefix; 24 rules). Production now beats v44_dt by $546/1000h (two tracks converged via v54/v55/v56 hybrid + Rules 21-24 chain gate-outs). Two-track divergence (gap to oracle): $117.84/1000h, cumulative closure since pre-S68 = 91.6% of original $1,409. Rule count: 24 (Rules 21-24 are chain gate-outs of the HIGH_ONLY × max ≥ 8 zone across S87-S90, combined recovery $214.83/1000h). Structurally-non-empty HIGH_ONLY × max ≥ 8 chain-audit zone COMPLETE. Next-session target: pivot to prefix-COVERED cells (LOW pair / two_pair / trips) — methodologically stronger with two-grid SHIP standard. See CURRENT_PHASE.md for the Session 91 resume prompt.

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
