# Development Checklist - Taiwanese Poker Solver

> **Purpose:** Track all tasks by phase and sprint. Check off as completed.

---

## Phase 1: Engine Core

### Sprint 0: Foundation + Lookup Tables — COMPLETED 2026-04-16
- [x] Initialize Rust project (Cargo.toml, dependencies)
- [x] Define Card, Rank, Suit types
- [x] Implement Deck with shuffle and deal
- [x] Build 5-card hand evaluator
- [x] Generate lookup table for all 2,598,960 five-card hands
- [x] Serialize/deserialize lookup table to binary
- [x] Verify hand rankings with comprehensive tests
- [x] Benchmark: <50ns per 5-card evaluation — **5.4 ns achieved**
- [x] Define HandSetting struct (top=1, mid=2, bot=4)
- [x] Enumerate all 105 possible settings for a 7-card hand
- [x] CLI: parse hand string and display settings
- [x] Initialize Python analysis project
- [x] Initialize git, first commit
- [x] All documentation in place

### Sprint 1: Hand Evaluator (Hold'em + Omaha) — COMPLETED 2026-04-16
- [x] Top tier evaluator: best 5 of 6 (1 hole + 5 board) — 26.5 ns
- [x] Middle tier evaluator: best 5 of 7 (2 hole + 5 board) — 149 ns
- [x] Bottom tier evaluator: Omaha (exactly 2 from 4 + 3 from 5) — 375 ns
- [x] **VERIFY:** Omaha enforces exactly-2-from-hand rule — 15 targeted tests
- [x] Scoring system: compare two settings across two boards
- [x] Scoop detection: all 6 wins, 0 chops = 20 points
- [x] Chop handling: equal ranks = 0 points
- [x] Comprehensive test suite for all evaluators — 76 tests, 0 failures
- [x] Benchmark all evaluators meet performance targets — 3 of 4 on target, full matchup 7% over (see sprint log)

### Sprint 2: Monte Carlo Engine — COMPLETED 2026-04-17
- [x] Single-setting evaluation (N samples) — `mc_evaluate_setting`
- [x] All-105-settings evaluation for one hand — `mc_evaluate_all_settings` with common random numbers
- [x] Opponent modeling (Random shipped; MiddleFirst / BestResponse deferred — same enum slot)
- [x] Parallelization with rayon — `mc_evaluate_all_settings_par`, per-worker seeded SmallRng, split/reduce
- [x] Convergence testing (N=1000 vs N=10000 top-1 stable; documented in sprint log)
- [x] CLI: evaluate a hand with sample count — `tw-engine mc --hand ... --samples ... --parallel --show-top ...`
- [x] Performance: <500ms for 1 hand, 105 settings, 1000 samples — **270.77 ms serial, 46.18 ms parallel**

---

## Phase 2: Solving

### Sprint 3: Best Response Computation
- [ ] Enumerate all canonical 7-card hands
- [ ] Suit canonicalization (~5-10x reduction)
- [ ] Compute best setting for each hand via Monte Carlo
- [ ] Checkpoint/resume system for long runs
- [ ] Progress reporting with ETA
- [ ] Binary output format
- [ ] N=100 quick run (hours) — verify pipeline works
- [ ] N=1,000 production run (days)
- [ ] N=10,000 high-precision run (weeks, optional)
- [ ] Summary statistics and analysis

### Sprint 4: Hand Bucketing + CFR
- [ ] Hand feature extraction
- [ ] K-means bucketing (1K, 5K, 10K buckets)
- [ ] CFR algorithm implementation
- [ ] Convergence tracking
- [ ] Nash equilibrium extraction
- [ ] Comparison: CFR strategy vs best-response

---

## Phase 3: Trainer + Validation

### Sprint 5: Trainer Application
- [ ] Load optimal settings database
- [ ] Deal random hands to user
- [ ] Accept user hand setting input
- [ ] Compare user vs optimal, display results
- [ ] Track user accuracy statistics
- [ ] Difficulty modes

### Sprint 6: Validation & Comparison
- [ ] Heuristic vs computed optimal comparison
- [ ] Agreement rate calculation
- [ ] EV loss quantification
- [ ] Tournament simulation with computed strategy
- [ ] Final report generation

---

## Phase 4: Analytics & Final Output

### Sprint 7: Analytics Pipeline + GTO Strategy Extraction
- [ ] Export solver results with full feature extraction to Parquet/SQLite
- [ ] Extract hand features (pair count, ranks, suits, connectivity, category)
- [ ] Extract setting features (mid type, top rank, bot suitedness)
- [ ] Pattern mining: pair-in-mid % by hand category and pair rank
- [ ] Pattern mining: two pair — which pair goes where
- [ ] Pattern mining: trips — verify third card never goes top
- [ ] Pattern mining: unpaired — what 2-card combo goes mid
- [ ] Pattern mining: suitedness impact (DS vs SS vs rainbow EV by hand type)
- [ ] Pattern mining: when does optimal deviate from MiddleFirst? Full catalog
- [ ] Pattern mining: top card EV by rank across all hands
- [ ] Build decision tree: category → rank → suitedness → action
- [ ] Implement decision tree as code (JSON/rules engine)
- [ ] Validate decision tree on 100K+ random hands vs solver
- [ ] Iterate decision tree until 95%+ agreement
- [ ] Push toward 98%+ agreement with additional branches
- [ ] Agreement analysis: avg EV loss when tree disagrees
- [ ] Comparison report: pre-solver heuristic vs solver
- [ ] Catalog: top 100 most surprising solver decisions
- [ ] Catalog: hands where simple rules fail (edge cases)
- [ ] Quantify: EV gain of perfect play vs MiddleFirst
- [ ] Generate: one-page decision flowchart
- [ ] Generate: detailed rules per hand category with solver numbers
- [ ] Generate: final validated GTO strategy guide (HTML/PDF)
- [ ] Answer all 10 key questions from analytics-pipeline.md
- [ ] AI Consensus: prepare data packages for model analysis
- [ ] AI Consensus: compute statistical baseline (pure math ground truth)
- [ ] AI Consensus: run independent Claude analysis on solver data
- [ ] AI Consensus: run independent Gemini analysis on solver data
- [ ] AI Consensus: Round 2 — models challenge each other's findings
- [ ] AI Consensus: Round 3 — models defend against challenges
- [ ] AI Consensus: Round 4 — produce consensus decision tree
- [ ] AI Consensus: flag disputed rules with confidence levels
- [ ] AI Consensus: human review of consensus strategy
- [ ] AI Consensus: save full debate transcript
- [ ] AI Consensus: output structured strategy JSON with all rules

---

*Last updated: April 2026 (pre-build)*
