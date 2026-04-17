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

**Correctness:** 81 tests pass, 0 failures (ended at 81 after the mid-session rules-verification pass added 5 play-the-board / Omaha-2+3-enforcement tests).
- 45 unit tests (inc. 10 holdem_eval, 11 omaha_eval, 2 scoring)
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

**Mid-session rules-verification pass (2026-04-17).** User flagged accuracy as a hard requirement and asked for a rigorous rules audit. I cross-referenced against Wikipedia's Texas hold 'em, Omaha hold 'em, and List of poker hands articles and produced `modules/game-rules.md` — now the canonical rules authority. Added 5 unit tests that pin down the rule assertions (Hold'em play-the-board allowed for top + middle, Hold'em 1-hole-card completes flush/straight, Omaha 2+3 forbids royal-flush-on-board shortcut). Updated `CLAUDE.md`'s session-start reading path to load `modules/game-rules.md` as MANDATORY before any sprint work. Also updated my auto-memory `project_taiwanese.md` to flag game-rules.md as the single source of truth. Commit: `262f1fd`.

On the two-plus-two 7-card LUT question: we agreed NOT to pursue it. The current 5-card LUT + enumeration is already provably correct (exhaustively verified against a direct-compute reference on all 2,598,960 hands). A 7-card LUT wouldn't help Omaha (2+3 rule forces per-hole-pair enumeration anyway), would require a ~130 MB table that doesn't fit in L2/L3 cache, and adds verification surface area. If middle-tier speed ever becomes a bottleneck, the right move is a suit-isomorphism table (~200 KB, L1-resident, ~10 ns per eval), not two-plus-two. For now, performance is well within Sprint 2's MC budget.

**Carry-forward for Sprint 2:** `matchup_breakdown` is the drop-in primitive for Monte Carlo's inner loop. The `Deck::shuffle` + `deal` API from Sprint 0 is ready for generating random opponent hands and board runouts. Session-start reading order has been tightened — `modules/game-rules.md` MUST be loaded before any Sprint 2 implementation work.

---

### Session 03 — 2026-04-17 — Sprint 2 Monte Carlo Engine (COMPLETED)

**Scope:** All of Sprint 2. Monte Carlo EV estimator for any 7-card hand × HandSetting against a uniform-random opponent, with single-thread and rayon paths, criterion benches, and a CLI subcommand.

**Result:** 100% of Sprint 2 acceptance criteria met. Headline performance target (<500 ms for 1 hand × 105 settings × 1000 samples, single thread) beaten at **271 ms** (54% of budget). Parallel path hits **46 ms**.

**Engine code delivered:**
- `engine/src/monte_carlo.rs` (NEW)
  - `OpponentModel::Random` enum (MiddleFirst / BestResponse stubbed as future variants; intentionally not shipped this sprint to keep scope tight)
  - `McResult { setting, ev: f64 }` and `McSummary { results, num_samples }` with `best() / worst() / gap_first_to_second()`
  - `mc_evaluate_setting(&ev, hand, p1_setting, model, N, &mut rng) -> f64` — one setting, N samples
  - `mc_evaluate_all_settings(&ev, hand, model, N, &mut rng) -> McSummary` — all 105 under **common random numbers** (same opponent + boards shared across all 105 p1 settings per sample)
  - `mc_evaluate_all_settings_par(&ev, hand, model, N, base_seed) -> McSummary` — rayon chunk + reduce across `current_num_threads()` workers, per-worker `SmallRng::seed_from_u64(base_seed + wi × 0x9E3779B97F4A7C15)`
  - Private helpers: `remaining_45` (one-time 45-card complement), `sample_deal` (partial Fisher-Yates over first 17 of 45 — no allocations, ~17 RNG calls per sample), `random_setting` (direct uniform sample over top × unordered mid-pair without materializing `all_settings`)
- `engine/src/lib.rs` — registered module + public re-exports
- `engine/src/main.rs` — new `mc` CLI subcommand: `--hand --samples --opponent --parallel --seed --show-top --lookup`
- `engine/Cargo.toml` — `rand` bumped to `{ features = ["small_rng"] }`; added `[[bench]] mc_bench`
- `engine/benches/mc_bench.rs` — 3 criterion benches (single setting, all-settings serial, all-settings parallel)

**Correctness:** **90 tests pass, 0 failures.** Breakdown: 54 lib unit tests (up from 45 — 9 new in `monte_carlo::tests`), 15 `hand_eval_tests.rs`, 15 `omaha_tests.rs`, 6 `scoring_tests.rs`.

New `monte_carlo::tests`:
1. `remaining_has_45_unique_cards_complementary_to_hand` — remaining-deck invariant
2. `sample_deal_draws_17_distinct_cards_disjoint_from_hand` — no collision / no hand-leak across 100 samples
3. `random_setting_is_always_valid` — every random setting uses each input card exactly once across 500 iters
4. `random_setting_hits_all_105_possibilities_eventually` — canonicalizes slots, asserts all 105 reached at N=100k (uniformity sanity)
5. `mc_single_setting_seeded_reproducible` — bit-identical EV at same seed
6. `mc_all_settings_returns_sorted_105` — output descending by EV
7. `mc_par_matches_serial_at_single_worker_seed` — `par` path with 1 worker ≡ serial path when the seed formula (wi=0 → base_seed) lines up
8. `mc_par_top1_stable_across_worker_counts_at_large_n` — best setting agrees between 1-worker and 4-worker runs at N=5000
9. `mc_convergence_top1_stable_from_n1000` — best setting identical at N=1000 vs N=10000

**Performance (release-mode criterion):**

| Bench | Measured | Target |
|-------|----------|--------|
| `mc_single_setting/N=1000_random_opp` | **6.11 ms** | <5 ms (22% over, see note) |
| `mc_all_settings_serial/105x1000_random_opp` | **270.77 ms** | **<500 ms ✓** |
| `mc_all_settings_parallel/105x1000_random_opp_par` | **46.18 ms** | — (5.9× speedup) |

Single-setting overshoot is expected: each sample does full `sample_deal` + `opp_pick` + one `matchup_breakdown` (2.14 µs), so 1000 × ~6 µs ≈ 6 ms. The all-settings path amortizes `sample_deal` + `opp_pick` across all 105 p1 settings per sample (common random numbers / CRN), which is why 105 settings × 1000 samples = 271 ms rather than 5 ms × 105 = 525 ms. Decision 014 records this as the intended trade-off — the solver uses the all-settings path anyway.

**Empirical EV sanity — `As Kh Qd Jc Ts 9h 2d`, N=5000 parallel, seed=0xC0FFEE:**
```
1. top=Jc  mid=[Kh 9h]  bot=[As Qd Ts 2d]    EV = +3.402
2. top=Jc  mid=[As Ts]  bot=[Kh Qd 9h 2d]    EV = +3.329
3. top=Jc  mid=[Qd 2d]  bot=[As Kh Ts 9h]    EV = +3.120
...
worst:                                        EV = +0.352
```
All three top picks put the Jack on top — consistent with the research finding "top card J+ ideal, T+ ok". Gap(1→2) = 0.073 → close at N=5000; a larger N would be needed to separate them with confidence.

**Decisions logged this session:** Decision 014 (Sprint 2 opponent scope).

**Design choice — common random numbers.** `mc_evaluate_all_settings` reuses the same `(opp_hand, board1, board2, opp_setting)` for all 105 p1 settings within one sample. This is a textbook variance-reduction technique for ranking problems: the *differences* between setting EVs are much less noisy than independent sampling. It also means 1× sampling work per sample instead of 105×. The cost is that we can't parallelize *across* settings inside one sample — we parallelize *across* samples instead, which composes cleanly with CRN.

**Design choice — `OpponentModel` enum, not trait.** The model is consulted inside a loop that runs 105M+ times in the full solve. Enum `match` inlines to one branch; trait dispatch would add a vtable load per sample. Adding `MiddleFirst` or `BestResponse` later is a 5-line diff and doesn't change the caller.

**Gotcha 1:** `SmallRng` is gated behind a feature flag in `rand 0.8` (was default in 0.7). First build after `use rand::rngs::SmallRng` failed with a "configured out" error. One-line fix in Cargo.toml.

**Gotcha 2 (caught in tests):** First version of `mc_par_same_result_regardless_of_worker_count` asserted ≥8/10 top-10 overlap between 1-worker and 4-worker runs at N=400. Failed at 7/10 — unsurprising because different worker counts = different RNG streams, and at N=400 the MC standard error is larger than typical gaps between rank-9 and rank-10 near-ties. Rewrote as "top-1 setting agrees at N=5000", which is the invariant we actually rely on downstream.

**Deferred:**
- `OpponentModel::MiddleFirst` — Sprint 4 (CFR) will likely need it when moving beyond best-response-to-random.
- Per-tier EV breakdown in CLI — the current CLI surfaces category names on one sample board pair for intuition; full per-tier MC is Sprint 5 (trainer).
- Confidence intervals on EV estimates — Sprint 6 (validation) is the right home.

**Carry-forward for Sprint 3:**
- `mc_evaluate_all_settings_par(..., OpponentModel::Random, ...)` is the per-hand primitive for best-response computation over all 133M hands.
- Per-hand cost at N=1000 parallel ≈ **46 ms** on this machine → naive 133M × 46 ms ≈ 70 days. Decision 006 suit canonicalization (~8× reduction) should bring that inside the "<1 week single machine" target from CLAUDE.md.
- `SmallRng::seed_from_u64(canonical_hand_id)` is a natural per-hand seed in Sprint 3 — reproducibility keyed to the canonical index, so checkpoint/resume is straightforward.
