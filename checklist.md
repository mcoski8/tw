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
- [x] Enumerate all canonical 7-card hands — 6,009,159 (Burnside-verified)
- [x] Suit canonicalization (~5-10x reduction) — 22.26× actual
- [x] Compute best setting for each hand via Monte Carlo — `solve_one` / `solve_range`
- [x] Checkpoint/resume system for long runs — append-only `BrWriter`
- [x] Progress reporting with ETA — per-block log lines
- [x] Binary output format — 9-byte fixed records, "TWBR" magic
- [x] N=100 quick run (hours) — verify pipeline works (3.8 s for 1K hands)
- [ ] N=1,000 production run (days) — P2-alt panel pending Claude Desktop approval (~10.4 days)
- [ ] N=10,000 high-precision run (weeks, optional)
- [ ] Summary statistics and analysis

### Sprint 2b: Multi-Archetype Opponent Panel (inserted into Sprint 3)
- [x] 7 opponent-model implementations — `engine/src/opp_models.rs` + tests (119 tests green)
- [x] OpponentModel enum extended with 7 variants + HeuristicMixed wrapper
- [x] CLI: --opponent flag for all 7 variants + mixed wrapping
- [x] Diagnostic subcommand: 7-model panel + pairwise matrix + JSON sidecar
- [x] validate-model subcommand
- [x] show-opp-picks audit subcommand
- [x] BalancedHeuristic pre-validation — 18.7% (failed ≥70% gate; validation gate itself critiqued)
- [x] 10K-hand 7-model diagnostic — 45.6 min wall, 11.9% all-agree, no pair ≥95%
- [x] Behavioural audit on 7 stress-test hands — 4 bugs identified
- [x] Gemini 2.5 Pro adversarial review via pal MCP
- [x] PRODUCTION COMMITMENT RECOMMENDATION document drafted for Claude Desktop
- [x] Claude Desktop approval of P2-alt panel — 2026-04-18 Session 06
- [x] Apply Bug 1 + Bug 3 fixes to opp_models.rs — Decisions 025, 026
- [x] Add 4 unit tests for the fixes (mfnaive/mfsuitaware KK preservation, topdef AAKK redux, omahafirst highest-of-rem3) — 124 tests green
- [x] Stress-test audit on 7 hands (show-opp-picks) — all 4 production models archetype-correct
- [ ] Re-run 5K diagnostic to verify bug-fix impact — IN PROGRESS
- [ ] Run mini-pilot: 50K hands × 4 models × N=1000 (~2 hours)
- [ ] Launch full production: 6,009,159 × 4 × N=1000 (~10.4 days)

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

#### Sprint 5a — foundation (Session 09 — 2026-04-23/24)
- [x] Engine CLI: `mc --tsv` emits all 105 settings with EVs in machine-readable TSV
- [x] Trainer dealer: random 7-card hand
- [x] Trainer engine wrapper: subprocess `tw-engine mc --tsv` with LRU cache per (hand, profile)
- [x] Trainer explain layer v1: heuristic detectors (split-pair, isolated-bottom-suit, wrong-top-card, tier-swap) + EV-delta severity
- [x] Flask backend: `/api/deal`, `/api/score`, `/api/profiles`, `/api/compare`
- [x] Web UI: drag-and-drop, click-to-fill, per-tier + clear-all buttons, submit/score flow
- [x] Profile selector (4 production profiles) + compare-across view with per-profile best arrangements
- [ ] Track user accuracy statistics (Sprint 5b)
- [ ] Difficulty modes (Sprint 5b)
- [ ] Solver-derived explanation rules (gated on Sprint 7 pattern mining)

### Sprint 6: Validation & Comparison
- [ ] Heuristic vs computed optimal comparison
- [ ] Agreement rate calculation
- [ ] EV loss quantification
- [ ] Tournament simulation with computed strategy
- [ ] Final report generation

---

## Phase 4: Analytics & Final Output

### Sprint 7: Analytics Pipeline + GTO Strategy Extraction

#### Python analysis infrastructure (Session 08 — 2026-04-21)
- [x] Read binary solver output into Python — `tw_analysis.br_reader` (numpy dtype, load + memmap)
- [x] Read canonical-hand file into Python — `tw_analysis.canonical` (`CanonicalHands.hand_cards(id)`)
- [x] Setting-index decoder — `tw_analysis.settings.decode_setting(hand_7, index)` mirrors Rust enumeration
- [x] Canonicalize + is_canonical in Python — mirrors `engine/src/bucketing.rs`
- [x] Inverse hand→canonical_id lookup — binary search over tobytes() rows
- [x] Full-file validation on real Model 1 data — ordering, ranges, finite EV, header fields
- [x] Byte-identical Rust parity — `diff` of `tw-engine spot-check --show 500` vs Python 519-line rendering passes (Decision 028)
- [x] Python unit tests — 11 settings + 9 canonical, all green

#### Cross-model tooling (Session 09 — 2026-04-23)
- [x] `tw_analysis.cross_model` — join N BrFiles by canonical_id, settings/EV matrices, unanimity mask, pairwise agreement, consensus histograms
- [x] `analysis/scripts/cross_model_join.py` — CLI report
- [x] `analysis/scripts/test_cross_model.py` — 9 unit tests, all green
- [x] First real cross-model finding on 2 models: 39.31% unanimous hands, setting 104 dominates unanimous bucket (28.6%)

#### Multiway analysis (Sprint 7 — data-driven, post-Model-4) — Session 11 first pass complete

- [x] Compute multiway-robust setting per canonical hand from 4-way cross-model unanimity (mode of per-profile BRs) — `analysis/scripts/multiway_analysis.py`
- [x] Quantify systematic differences in setting composition (top rank, mid pair rate, mid rank-sum, bot DS%, bot rank-sum) between heads-up BR and multiway-robust — done at N=200K-hand sample
- [x] Test user's hypothesis ("weaker top, stronger mid+bot") with data: 4 of 5 axes directionally support it (Δ top rank −0.18, Δ mid pair rate +2.2pp, Δ bot DS rate +1.2pp); bot rank-sum essentially unchanged (intuition wrong on rank, right on structure)
- [x] Empirical skill-gap finalized at N=500 × 4 profiles: optimizer +1.538 EV/hand vs naive (idx 104), naive 0/2000 strict wins, hands-to-2σ ~5
- [ ] Quantify scoop-frequency change with player count — when does scoop value justify variance?
- [ ] Run multiway analysis at full 6M hands (sample run is representative; full run for the published number)
- [ ] Player-count-aware UI: surface "robust play" when 3+ players selected, with the unanimous-only structural rule (high card top, pair middle, double-suited bottom)

- [x] Export solver results with full feature extraction to Parquet/SQLite — `analysis/scripts/build_feature_table.py` → `data/feature_table.parquet` (6M hands × 51 cols, 208 MB) (Session 12)
- [x] Extract hand features (pair count, ranks, suits, connectivity, category) — `tw_analysis.features.hand_features_batch` (Session 12)
- [x] Extract setting features (mid type, top rank, bot suitedness) — `tier_features_batch` (Session 12)
- [x] Pattern mining: pair-in-mid % by hand category and pair rank — `mine_patterns.py` section 5 (9+ pair → mid 93.5%; J+ 95%, A 99.65%) (Session 12)
- [x] Pattern mining: two pair — which pair goes where — covered in three-pair section (`mid = highest pair` 75.4%) (Session 12)
- [x] Pattern mining: trips — placement by rank — section 1 of `mine_patterns.py` (trips→mid 81% low rank, 99% high rank) (Session 12)
- [x] Pattern mining: unpaired — top-card distribution measured (section 6 of `mine_patterns.py`) — but a focused mine on the no-pair (high_only) decision is Phase B priority
- [x] Pattern mining: suitedness — DS vs connectivity tiebreaker measured (section 7); DS wins 1.8x when both feasible (Session 12)
- [x] Pattern mining: top card cutoff by rank (section 6) (Session 12)
- [x] Build decision tree (first cut): 7-rule chain in `analysis/scripts/encode_rules.py` (Session 12)
- [x] Implement decision tree as code — `apply_rules(hand) → setting_index` in `encode_rules.py` (Session 12)
- [x] Validate decision tree on 6M canonical hands vs multiway-robust — **53.58% shape-agreement** baseline; naive_104 baseline 21.77% (Session 12)
- [ ] Iterate decision tree until 70%+ agreement (Phase B target — close `high_only` gap, the biggest miss category at 35% of all misses)
- [ ] Push toward 95%+ agreement with conditional refinements
- [ ] Agreement analysis: avg EV loss when tree disagrees
- [ ] Comparison report: pre-solver heuristic vs solver
- [ ] Catalog: top surprising solver decisions
- [ ] Catalog: hands where simple rules fail (edge cases)

#### Buyout option analysis (Session 12)
- [x] Empirical buyout-rate per opponent profile — vs MFSA 0.37%, vs TopDef 0.37%, vs OmahaFirst 0.01%, vs RandomWeighted 0.05%
- [x] Mean-EV buyout rate (4-profile-mean < -4): 0.09% of hands
- [x] Feature signature of buyout candidates — quads of 2-7 (lift 117x), pure low trips (8x), trips+low-pair (6.6x). NOT garbage hands (those are mildly bad, not catastrophic)
- [x] 4-handed selective-buyout edge measurement: ~+0.56 points per 100 hands
- [ ] Trainer integration: surface BUYOUT badge in trainer when ev_mean < -4 vs the active opponent profile

#### Encode-then-measure methodology (Session 12)
- [x] Inverse decoder `positions_to_setting_index` (round-trip-verified for all 105 settings)
- [x] Shape-agreement metric (compare `(top_rank, sorted_mid_ranks, sorted_bot_ranks)`) — corrects for suit-position tie-break artifacts in literal `setting_index` comparison. Always use SHAPE for rule evaluation.
- [x] Gemini Socratic dialogue on encode-vs-build-infrastructure-first (continuation_id ec08b754-69f3-479d-bb5a-c15fee965876); synthesized hybrid path
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
