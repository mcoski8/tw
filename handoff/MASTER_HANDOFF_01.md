# Taiwanese Poker Solver - Master Handoff 01

> **Covers:** Sessions 1-onwards
> **Project:** TW Poker Solver
> **Stack:** Rust (engine) + Python (analysis/trainer)

## Project Identity
- **What:** Compute Nash equilibrium for Taiwanese Poker
- **Engine:** Rust — hand evaluation, Monte Carlo, CFR
- **Analysis/Trainer:** Python
- **Scale:** 133M+ hands, 105 settings each

## Critical Rules
1. Omaha bottom: MUST use exactly 2 from hand + 3 from board
2. Two 5-card community boards
3. Scoop = 20pts (win ALL 6, zero chops)
4. No fouling, no royalties
5. Double suited bottom ideal, 3+ of suit is BAD

## Research Findings
- MiddleFirst is dominant strategy
- Middle tier has widest equity spreads
- Top card: J+ ideal, T+ ok
- Pairs TT+ elite mid; below 88 marginal vs real opponents
- Double suited bottom worth ~$0.50/hand over rainbow

## Session Log
*Appended as sessions occur.*

---

### Session 01 — 2026-04-16 — Sprint 0 Foundation (COMPLETED)

**Scope:** All of Sprint 0. Rust engine scaffold, 5-card evaluator, lookup table, HandSetting + all_settings, tests, bench, CLI, project infra, first commit.

**Result:** 100% of Sprint 0 acceptance criteria met.

**Engine code delivered:**
- `engine/src/card.rs` — Card/Rank/Suit/Deck, packed u8 representation, FromStr + Display, parse_hand helper
- `engine/src/lookup/mod.rs` — colex indexing over C(52,5), precomputed BINOM table via const fn
- `engine/src/hand_eval.rs` — HandRank encoding, compute_rank_5 reference implementation, Evaluator with build/load/save/eval_5
- `engine/src/setting.rs` — HandSetting struct, all_settings(hand) -> 105 arrangements
- `engine/src/{lib,main}.rs` — library surface + clap CLI (eval, build-lookup)
- `engine/tests/hand_eval_tests.rs` — 15 integration tests
- `engine/benches/eval_bench.rs` — criterion bench

**Correctness:** `table_lookup_matches_direct_on_every_hand` iterates all 2,598,960 five-card combinations and verifies the stored LUT rank equals a fresh direct-compute rank on every one. 23 unit tests + 15 integration tests + 0 doctests = 38 passing, 0 failures.

**Performance:** `eval_5` benchmarks at **5.4 ns** per call (target <50 ns). Sort 5 bytes + 5 table adds + 1 memory load. Pure function — no alloc, no side effects — so the same eval path can back CPU rayon + CUDA backends later.

**Infra delivered:**
- `.gitignore` (target/, data/*.bin, .env, Python artifacts)
- `README.md`
- `scripts/build.sh` (executable; auto-adds ~/.cargo/bin to PATH for non-interactive shells)
- `analysis/pyproject.toml` + `analysis/src/__init__.py` skeleton
- `data/lookup_table.bin` auto-generated on first CLI run (10.4 MB)

**Git:** Repo initialized at project root. Commit `f9f1e0d` landed with full Sprint 0 work. No remote configured yet.

**Decisions logged this session:** Decision 012 (evaluator implementation choice).

**Gotcha:** rustdoc tried to compile a `C(n,k)` math formula in `setting.rs` module doc as Rust code. Fixed by moving the formula into prose instead of an indented block. Keep math notation out of module doc comments unless fenced as ```text.

**Carry-forward for Sprint 1:** None. All Sprint 0 capability is ready to consume. `tw_engine::Evaluator` is a drop-in dependency for the top/middle/Omaha evaluators.

---

### Session 02 — 2026-04-16 — Sprint 1 Hand Evaluator (COMPLETED)

**Scope:** All of Sprint 1. Top/middle/Omaha tier evaluators, scoring module with scoop + chop handling, integration tests, tier benchmarks.

**Result:** 100% of Sprint 1 acceptance criteria met; one perf target 7% soft (see below).

**Engine code delivered:**
- `engine/src/holdem_eval.rs` — `eval_top` (drops 1 of 6), `eval_middle` (drops 2 of 7)
- `engine/src/omaha_eval.rs` — `eval_omaha` using const `HOLE_PAIRS` (6) × `BOARD_DROPS` (10) tables = 60 `eval_5` lookups. Hole pair is hoisted out of the inner loop per compute-pipeline.md optimization note
- `engine/src/scoring.rs` — `matchup_breakdown` runs all 6 matchups, detects scoop (6 wins ∧ 0 chops), returns `MatchupBreakdown {outcomes, p1_points, p2_points, scooped}`. `score_matchup` is a (i32, i32) thin wrapper. Points are net-form so the pair always sums to zero
- `engine/src/lib.rs` — registered new modules + re-exports
- `engine/Cargo.toml` — added `[[bench]] name="tier_bench"`
- `engine/tests/omaha_tests.rs` — 15 integration tests targeting every 2+3-rule trap
- `engine/tests/scoring_tests.rs` — 6 integration tests including hand-crafted scoop fixture and chop-invalidates-scoop

**Correctness:** 76 tests pass, 0 failures.
- 40 unit tests (inc. 6 holdem_eval, 10 omaha_eval, 2 scoring)
- 15 hand_eval integration tests (Sprint 0, still pass)
- 15 omaha integration tests
- 6 scoring integration tests

**Performance (release-mode criterion):**

| Bench | Measured | Target |
|-------|----------|--------|
| `eval_top` | **26.5 ns** | <100 ns ✓ |
| `eval_middle` | **149 ns** | <250 ns ✓ |
| `eval_omaha` | **375 ns** | <500-700 ns ✓ |
| `matchup_breakdown` | **2.14 µs** | <2 µs (7% over) |

The 7% overshoot is comfortably within Monte Carlo's budget: 2.14 µs × 105 settings × 1000 samples = 224 ms/hand, vs Sprint 2's <500 ms target. Decision 012 flagged the two-plus-two 7-card lookup as the optimization to pull in if Monte Carlo ends up tight later.

**Decisions logged this session:** Decision 013 (net-points scoring encoding).

**Gotcha:** Initially wrote an Omaha test asserting "1 hole ace + 3 board aces → trips". Test failed in CI because it's actually quads: 2+3 allows picking Ac + any kicker from hole (2 cards) + all 3 board aces (3 cards) = 4 aces total. Fix: split into two tests, one asserting quads (1 hole A + trip board), one asserting trips (0 hole A + trip board). This is exactly the class of 2+3 confusion the sprint doc warned about — caught by the test loop before merging, which is the whole point of writing tests first.

**Deferred:** CLI update to print tier ranks for each of the 105 settings against a board. Not a Sprint 2 dependency (Monte Carlo calls the Rust evaluators directly), so keeping Sprint 0's CLI surface unchanged until the trainer (S5) needs it.

**Carry-forward for Sprint 2:** `matchup_breakdown` is the drop-in primitive for Monte Carlo's inner loop. The `Deck::shuffle` + `deal` API from Sprint 0 is ready for generating random opponent hands and board runouts.
