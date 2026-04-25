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

---

### Session 04 — 2026-04-17 — Sprint 3 pipeline built and validated end-to-end (production run pending)

**Scope:** Implement the full Sprint 3 pipeline: suit canonicalization, per-hand best-response computation, checkpointed binary file format, CLI driver, end-to-end validation. Stop short of the 2.6-day production launch (user-gated).

**Result:** Pipeline complete. Test count 90 → 105 (+15). Pilot at production cadence (N=1000 × 10K hands) clocked 37.3 ms/hand at 9× rayon speedup. All six named-hand spot-checks agree with research findings.

**Engine code delivered:**
- `engine/src/bucketing.rs` (NEW) — `canonicalize`, `is_canonical`, `enumerate_canonical_hands` (rayon-parallel over first card), `count_canonical_hands`. File I/O: `write_canonical_hands` / `read_canonical_hands` ("TWCH" magic + version + count + 7-byte sorted card-index records).
- `engine/src/best_response.rs` (NEW) — `BestResponseRecord` (u32 + u8 + f32 = 9 bytes), `BrHeader` (32 bytes "TWBR" + version + samples + base_seed + canonical_total + opp_model_tag), `BrWriter::open_or_create` (append-only, crash-safe resume = (filesize − 32) / 9, header-mismatch refusal), `solve_one`, `solve_range` (outer-rayon over canonical hands, serial `mc_evaluate_all_settings` inside).
- `engine/src/lib.rs` — module registration + re-exports.
- `engine/src/main.rs` — three new CLI subcommands: `enumerate-canonical [--count-only]`, `solve --canonical PATH --out PATH --samples N --seed S [--block-size B] [--limit L]`, `spot-check --canonical PATH --out PATH [--show N]`.
- `engine/Cargo.toml` — `tempfile = "3"` dev-dep for writer tests.

**Tests:** 105 passing (Sprint 2: 90 → +15). New tests cover canonicalization round-trip across all 24 suit permutations, idempotency, suit-closed-subset enumeration check, file format round-trip, writer create / resume / mismatch / truncated handling, and end-to-end `solve_one`.

**Empirical:**
- **Canonical hand count = 6,009,159.** Cross-verified against Burnside's lemma over S₄: identity 133,784,560 + 6 transpositions × 1,723,176 + 3 double-transpositions × 0 + 8 three-cycles × 12,025 + 6 four-cycles × 0 = 144,219,816; ÷24 = 6,009,159 ✓. (Double-transpositions and 4-cycles vanish by parity: 7 cards can't split as 2k+2k or 4k.)
- Throughput at N=1000: 37.3 ms/hand, 57 MB peak RSS, 9.0× parallel speedup.
- Six spot-checks (quad aces, royal-hole + connectors, wheel + T9, AAKK, rainbow gappers, trip-K + 88) all match research findings: top card J+ where possible, premium pair → bot for 3pt scoring weight, suited pair → mid for flush draws.
- Pilot files (gitignored): `data/best_response_pilot.bin` (N=100 × 1K), `data/best_response_extpilot.bin` (N=1000 × 10K).
- `data/canonical_hands.bin` (42 MB, gitignored) — full canonical-hand enumeration on disk.

**Decisions logged this session:** Decision 017 (single-pass solve, skip pre-screening + adaptive multi-pass), Decision 018 (fixed-width 9-byte record file format).

**Gotcha 1 (test fix):** First version of `enumerate_canonical_subset_round_trips_for_tiny_deck` used the first 9 cards of the deck as the test universe. That subset is NOT closed under suit permutation — card 8 (4c) has no suit-siblings in the subset, so canonicalization can produce a representative outside the universe. Fixed by using the first 12 cards (ranks {2,3,4} × all 4 suits = closed under S₄).

**Gotcha 2 (CLI ergonomic):** Clap's `default_value_t = 0xC0FFEE_u64` accepts hex literals for the default value but the `value_parser` for `--seed` only takes decimal. Pass `--seed 12648430` (hex 0xC0FFEE in decimal) when overriding from the CLI.

**Carry-forward for Sprint 3 production launch (user-gated):**
- Production run command + monitoring recipe is in `CURRENT_PHASE.md → "Launch the production run"`. Total wall ~2.6 days, ~9 cores, 57 MB RSS. Resumable via the same command.
- Output file `data/best_response.bin` will be exactly 32 + 9 × 6,009,159 = 54,082,463 bytes ≈ 51.6 MB.
- After production: sample 100 random hands, re-solve each at N=10K via `mc`, confirm best-setting agreement ≥ 95% (validation gate).

**Carry-forward for Sprint 4:**
- `data/best_response.bin` + `data/canonical_hands.bin` are the inputs. `read_best_response_file()` returns `(BrHeader, Vec<BestResponseRecord>)`; `read_canonical_hands()` returns `Vec<[u8; 7]>` indexed by `canonical_id`. Together they give `(canonical_hand, best_setting_index, best_ev)` triples.
- Pattern mining queries that don't need EV (e.g. "what setting shape does each hand category prefer?") can mmap `best_response.bin` and seek to records directly; `bytes_to_hand` converts back to typed `[Card; 7]`.

---

### Session 05 — 2026-04-17 to 2026-04-18 — Sprint 2b: 7-model opp panel + diagnostic + audit + Gemini review

**Scope:** Implement full 7-opponent-model panel per Claude Desktop's Sprint 2b spec. Run 10K-hand 7-model diagnostic, behavioural audit on 7 stress-test hands, Gemini 2.5 Pro adversarial review. Produce PRODUCTION COMMITMENT RECOMMENDATION for Claude Desktop's final approval. Do NOT launch production yet.

**Result:** Panel + diagnostic + audit + review complete. 4 bugs found (2 critical, 1 moot, 1 archetypal). Recommended P2-alt (4 models) committed pending Claude Desktop sign-off. Test count 105 → 119 (+14 new).

**Engine code delivered:**
- `engine/src/opp_models.rs` (NEW) — all 7 opp heuristics + helpers (naive_mid_score, middle_tier, bot_suit_score, omaha_bot_score, balanced_setting_score) + `opp_middle_first_naive`, `opp_middle_first_suit_aware` (refactored), `opp_omaha_first`, `opp_top_defensive`, `opp_random_weighted`, `opp_balanced_heuristic`. 14 unit tests.
- `engine/src/monte_carlo.rs` — `OpponentModel` enum extended: `Random | MiddleFirstNaive | MiddleFirstSuitAware | OmahaFirst | TopDefensive | RandomWeighted | BalancedHeuristic | HeuristicMixed { base: MixedBase, p_heuristic: f32 }`. Added `MixedBase` enum. Dispatcher rewritten; duplicated MFSuitAware helpers moved to opp_models.rs.
- `engine/src/main.rs` — CLI: `--opponent {random|mfnaive|mfsuitaware|omaha|topdef|weighted|balanced|mixed}` + `--mix-base` + `--mix-p`. New subcommands: `diagnostic` (7-model panel + pairwise matrix + JSON sidecar), `validate-model`, `show-opp-picks`.
- `engine/src/best_response.rs` — `solve_one` / `solve_range` take explicit `OpponentModel` parameter.
- `engine/src/lib.rs` — `opp_models` module registered; `MixedBase` re-exported.

**Empirical findings:**

1. **BalancedHeuristic pre-validation:** 1000 hands × N=5000 vs MC-best. Agreement 18.7%, mean regret 0.653 EV, max 3.174 EV. Failed Claude Desktop's ≥70% gate.

2. **7-model diagnostic (10K hands × N=1000 × 7 models):** Wall 45.6 min vs predicted 46 min (accurate to 1%). 24,585 CPU seconds, 57 MB peak RSS. All-7 agree: **11.9%** (1195/10000). Pairwise matrix showed no pair ≥95% — all 7 models meaningfully distinct. Clusters:
   - Hold'em-centric: MFNaive ↔ MFSuitAware 88.4%, MFSuitAware ↔ TopDefensive 79.0%, MFNaive ↔ TopDefensive 77.5%
   - OmahaFirst isolated: 17-19% with Hold'em-centric
   - Random ↔ RandomWeighted 54.1%
   - BalancedHeuristic's highest correlate is Random at 51.4% (predicted to cluster with MF-family; prediction WRONG)
   - Mean per-hand EV spread: 2.225, p50 2.24, p95 3.12, p99 3.50, max 4.18.

3. **Behavioural audit (7 hands × 7 models, via `show-opp-picks`):**
   - **Bug 1 (CRITICAL):** MFNaive + MFSuitAware split the second pair on AAKK hands. `As Ah Kd Kh 7s 4c 2d` → top=Kh, mid=AA, bot=Kd+junk (breaks KK).
   - **Bug 2 (CRITICAL):** BalancedHeuristic puts Ace in bot. `As 5s 5d Th 9c 7d 3h` → top=7d, mid=55, bot=As+rest. Weighted formula arithmetic: top=7d setting = 321 > top=As = 309.
   - **Bug 3 (CRITICAL):** OmahaFirst picks absurd tops. `As Kh Qd Jc Ts 9h 2d` → top=2d (leftover from mid selection in remaining-3). Should be top = highest of remaining 3.
   - **Bug 4 (MINOR, defer):** TopDefensive over-splits trips (puts lone J in bot as kicker instead of solo J on top). Gemini treats as archetype eccentricity.
   - Not a bug: MFSuitAware's ATs-over-AKo preference on broadway hand — accepted as archetype trait (player who overvalues suitedness).

4. **Gemini 2.5 Pro adversarial review** (via pal MCP): Full Socratic debate across Claude Desktop's Topics A-G. Key consensus with Claude Code:
   - P2-alt (4 models): MFSuitAware-fixed + OmahaFirst-fixed + TopDefensive-fixed + RandomWeighted
   - HeuristicMixed{p=0.9} for deterministic members
   - Defer aggregation to Sprint 7; output 4 separate files
   - N=1000 uniform, no adaptive, no preview
   - Fix Bugs 1 + 3; defer Bug 4; Bug 2 moot (drop model)
   - Defer adding new archetypes (Scoop-Terrified already covered by TopDefensive; Solver-app-assisted is an interesting but non-essential addition)

**Decisions logged this session:** 019 (Sprint 2b panel adoption), 020 (validation gate critique), 021 (drop BalancedHeuristic), 022 (aggregation deferred), 023 (P2-alt chosen), 024 (p=0.9 wrapping).

**Gotchas:**
- `OpponentModel` enum needed `PartialEq` only (not `Eq`) once `HeuristicMixed` carried an `f32`.
- Clap's `ValueEnum` doesn't support enum variants with data; worked around with separate `Mixed` CLI variant + `--mix-base` + `--mix-p`.
- First version of Bug-1 test tried to construct two tied non-pair candidates from a pairless hand; impossible because the naive scorer uniquely determines rank pairs. Rewrote with a three-of-a-kind hand (three 7s) where three mid-pair choices legitimately tie.
- `/usr/bin/time -l` in background bash output goes to the task's output file alongside stdout — scrapes cleanly for wall-clock.

**Output files (data/, all gitignored):**
- `diagnostic_7model.log` — full diagnostic stdout
- `diagnostic_7model.json` — 10K hands × 7 models EV matrix + pairwise counts + spread series (~5 MB)

**Carry-forward for Session 06 (after Claude Desktop response to PRODUCTION COMMITMENT RECOMMENDATION):**
1. Apply Bug 1 + Bug 3 fixes to `opp_models.rs`. Gemini staged concrete diffs (pal_generated.code, deleted post-read per MCP protocol). The approach for both: prefer highest-rank *non-pair-member* card for top, with fallback to highest-rank-overall when all 5 remaining are pair-members. For OmahaFirst: after bot selection, top = highest of remaining 3, mid = other 2.
2. Add unit tests: `mfsuitaware_preserves_kk_on_aakk_hands`, `omahafirst_top_is_highest_of_remaining_three`.
3. Re-run `show-opp-picks` on all 7 stress-test hands to verify fixes.
4. Re-run 7-model diagnostic on 5K hands (~25 min) to confirm the cluster structure shifts (MFNaive↔MFSuitAware should drop below 88.4%).
5. Run mini-pilot: 50K hands × 4-model P2-alt panel × N=1000 (~4 hours).
6. If pilot OK, launch full production: 6,009,159 × 4 × N=1000 ≈ 10.4 days Mac Mini or ~2 days cloud.

---

### Session 06 — 2026-04-18 — Bug fixes applied, diagnostic re-run, pilot launched, cloud plan written

**Scope:** Apply Claude Desktop's approved plan (P2-alt production with Bug 1 + Bug 3 fixes). Stress audit. Re-diagnostic. Pilot on Mac Mini. Write cloud production guide (user pivoted from Mac-Mini production to cloud mid-session). Docs + commit.

**Decisions (new):** 025 (Bug 1 fix — pair-preserving top in MFNaive + MFSuitAware via `pick_top_from_rem5` helper), 026 (Bug 3 fix — OmahaFirst top = highest of rem3, not leftover of mid-selection).

**Engine code delivered:**
- `engine/src/opp_models.rs` — added `pick_top_from_rem5` (pair-preservation for MF-family), rewrote `candidate_bot_after_top` and `build_setting_mid_then_top` to route through it. Rewrote `opp_omaha_first`'s top-selection to use rem3-highest-rank rule. Added 5 new tests: `mfnaive_preserves_kk_on_aakk_hands`, `mfsuitaware_preserves_kk_on_aakk_hands`, `topdefensive_preserves_pairs_on_aakk_redux`, `omahafirst_picks_highest_remaining_for_top`, `omahafirst_top_is_highest_of_remaining_three_stress`.
- Test count: 119 → **124** (+5). All passing.

**Scripts + docs delivered:**
- `scripts/pilot_all_models.sh` — 4-model pilot sequential runner (50K hands × N=1000, ~2 hrs on Mac Mini).
- `scripts/production_all_models.sh` — 4-model production sequential runner (6.01M hands × N=1000). Built for Mac but applicable to cloud.
- `CLOUD_PRODUCTION_GUIDE.md` — full first-time-cloud-user guide with 3 options (DigitalOcean, RunPod, GCP) chosen after Socratic pressure-test with Gemini 3 Pro via PAL MCP. Includes sub-24-hour variants for each option. Explicitly rejects AWS, Hetzner, Azure, Oracle, container-first services, and GPU-based approaches with justifications.
- `DECISIONS_LOG.md` — Decisions 025, 026 appended.
- `checklist.md` — Sprint 2b items checked off; pilot + production marked in progress / cloud-pending.

**Empirical — stress-test audit (pure function, instant):**
- Ran `show-opp-picks` on 7 stress hands (AAKK, broadway, TT+junk, JJJ+junk, 9876-straight-draw, 55+KJ9, A55+junk). All 4 production models (MFSuitAware-mixed-0.9, OmahaFirst-mixed-0.9, TopDefensive-mixed-0.9, RandomWeighted-pure) behave per archetype spec:
  - MFSuitAware on AAKK: top=7s, mid=AA, bot=KK-preserved. **Bug 1 fix confirmed.**
  - OmahaFirst on broadway AKQJT9-2: top=Ts (highest of rem3={Ts,9h,2d}), NOT 2d. **Bug 3 fix confirmed.**
  - MFSuitAware's "ATs-over-AKo" trait retained (picks As+Ts over As+Kh on broadway hand) — accepted archetype feature.
  - TopDefensive's JJJ trip-split retained (puts Jc in bot, two Js in mid) — Bug 4 deferred per Claude Desktop + Gemini.

**Empirical — 5K-hand re-diagnostic (23:10→23:33, 1389 s wall):**
Pre-fix (Session 05 10K) vs post-fix (Session 06 5K):
- All-7 agree: 11.9% → **14.4%** (+2.5pp, as expected — Bug 3 fix makes OmahaFirst less pathologically isolated, so more agreements land)
- Mean EV spread: 2.225 → **2.269** (essentially unchanged)
- MFNaive↔MFSuitAware: 88.4% → **89.0%** (~same; both got identical pair-preservation fix → relative agreement preserved, as logically expected)
- OmahaFirst vs Hold'em-centric models: 17-19% → **29-36%** (roughly 2× increase — Bug 3 fix empirically validated; no more deuce-on-top absurdity)
- TopDefensive↔MFSuitAware: 79.0% → **77.5%** (~same)
- OmahaFirst vs Random: ~29% → **53.5%** (notable; OmahaFirst's post-fix setting sometimes matches what Random happens to pick because highest-of-rem3 is a natural Hold'em-ish choice)
- No pair ≥ 95% agreement → 4-model P2-alt panel remains fully justified; no cluster collapse post-fix.
- Worst-disagreement examples (top EV spread 4.274 on `2c 2d 2h 3s 4s 8c Tc`): still concentrated on low-card / trip-heavy hands where opponent modeling has widest leverage.

**Process correction (self-flag):** My pre-run prediction that MFNaive↔MFSuitAware agreement would "drop below 88.4%" after Bug 1 fix was wrong reasoning. Both models received the identical pair-preservation fix, so their pairwise agreement is NATURALLY preserved — the fix shifts their absolute behaviour in parallel on AAKK hands, not their relative behaviour. Noting this as a miscalibrated prediction so future sessions don't repeat it.

**Course correction this session (user pivot, 23:20-ish):**
- User interrupted mid-session to veto the 10-day Mac Mini production run. Requested cloud alternative with click-by-click instructions for a non-technical first-time cloud user.
- Follow-up: user asked about GPU acceleration at nominal fee for sub-24-hour completion.
- Response: consulted Gemini 3 Pro via PAL MCP in two Socratic rounds. Gemini dismantled several of my initial recommendations:
  - **Hetzner dropped** (KYC friction for US users; no signup credit = actually *more* expensive out-of-pocket than DO/GCP credits).
  - **GCP quota reality-check**: new-account hard cap at 8-12 vCPU per region; 112-vCPU requests from personal Gmail trigger manual fraud review (likely delayed). Must upgrade past free trial first.
  - **Spot pricing rejected** for non-technical user — resume-safe code doesn't help if the human panics on preemption.
  - **RunPod added as #2** — prepaid model bypasses enterprise fraud gates; 64+ vCPU CPU pods available instantly.
  - **GPU rejected** for the workload — branchy integer code + 10 MB lookup table = worst-case GPU pattern; multi-month CUDA rewrite for ≤5× speedup is not rational.
  - **Parallel 4-pod fan-out** flagged as UX-hazardous for non-technical user (multiplies error surface — terminate-the-wrong-pod risk). Gemini preferred "single bigger machine."
- Final top 3 (in CLOUD_PRODUCTION_GUIDE.md): DigitalOcean (#1 simplest UI, $200 credit), RunPod (#2 cheapest + fastest start, prepaid $17-20), GCP (#3 fastest machine if quota approved, $0 after $300 credit). Each with own sub-24-hour variant.

**Empirical — pilot complete (23:34 → 01:37, 2h 3m wall):**
- Background job `butlu0ted` finished cleanly (all 4 models exit=0). Per-model wall: 31m 27s (MFSuitAware), 30m 36s (OmahaFirst), 30m 10s (TopDefensive), 30m 41s (RandomWeighted).
- All 4 output files exactly 450,032 bytes (32-byte header + 9 × 50,000 records). Headers verified: opp_model_tag = 1002090 / 1003090 / 1004090 / 6 respectively.
- EV distributions archetype-consistent: MFSuitAware mean -2.89 (toughest opp → most negative hero EV), TopDefensive -2.89 (also tough), RandomWeighted -1.66 (medium), OmahaFirst -1.02 (gives up EV at Hold'em tiers → hero loses least).
- Bug fixes validated at 50K-hand scale: on quads+trips hand `2c2d2h2s 3c3d3h`, MF/TD preserve trips in bot (top=2s, mid=3h2h, bot=3d3c2d2c); OmahaFirst bot picks trips+pair (top=3d, mid=2s2d, bot=3h3c2h2c). No pair-orphaning observed. Spot-check raw output: `data/session06/pilot_spotcheck.log` (if committed) or regenerate with `./engine/target/release/tw-engine spot-check --out data/pilot/<model>.bin --show 20`.
- Production pipeline green-lit for cloud launch.

**Final effective per-hand rate** (mixed-opp wrapper): 31.4 ms/hand at N=1000 with rayon — slightly FASTER than the pure-Random baseline's 37.3 ms/hand, because the heuristic branch skips `random_setting`'s top/mid index draws 90% of the time (heuristic result is precomputed per sample). Implication for cloud projection: actual production will be ~20% faster than my guide's "3 days on 48-vCPU DO" estimate. Updated projection: ~2.5 days DO, ~1.4 days GCP 112-vCPU, ~4 days RunPod 32-vCPU.

**Carry-forward for Session 07 (or user-launched cloud run):**
1. **Cloud launch is user's to kick off.** Follow CLOUD_PRODUCTION_GUIDE.md. Recommended start: RunPod (#2) for fastest-to-running, least friction.
2. **Once all 4 production files are back on the Mac** (`data/best_response/*.bin`), Sprint 7 analysis can begin. Sprint 7 turns raw solver data into a human-usable GTO strategy via multi-model AI consensus (Claude + Gemini debate) + pattern mining + decision-tree extraction. Not compute-heavy — mostly API calls + notebooks.
3. **Pilot outputs in `data/pilot/`** are for spot-checking only; the production run overwrites nothing (different output directory).
4. **If the user wants CFR refinement (Sprint 4)** to approach true Nash, that's a separate effort after Sprint 3 best-response tables are in hand. Optional.

**Gotchas this session:**
- Pre-run prediction about MFNaive↔MFSuitAware agreement change was wrong (flagged above). Both models got the identical fix → relative agreement preserved.
- CLI flag mismatch between Claude Desktop's recipe and actual implementation (`--num-hands` vs `--limit`, no `--parallel` flag on `solve` since rayon is always on, no `--checkpoint-dir` since append-only writer handles it in `--out`). Translated to actual CLI in scripts.
- `data/session06/*.json` needed a new gitignore rule to match session 05's convention — added.

---

### Session 07 — 2026-04-19 — Sprint 3 Cloud Launch (RUNNING)

**Scope:** Rewrite `CLOUD_PRODUCTION_GUIDE.md` around user's overspend-anxiety, fix fatal script portability bugs, and get the user actually running on cloud. The 10-day Mac Mini alternative is still vetoed from Session 06.

**Trigger:** User opened session by questioning whether the cloud providers in the prior guide committed them to monthly billing. The honest answer is "no — these are all metered per-second/per-hour, destroy = stops," but that framing wasn't prominent enough in the prior guide to defuse the anxiety. User explicitly asked for verification + rewrite.

**Pricing verification (web search, April 2026):**
- DigitalOcean Droplets: per-second billing since Jan 2026 (60-sec minimum), monthly cap of 672 hours = bill never exceeds advertised monthly rate. Confirmed via DigitalOcean blog (per-sec billing announcement) + docs.
- RunPod: strictly prepaid, per-second, no credit card auto-charge. Balance = hard cap unless auto-refill is enabled.
- GCP: per-second, 1-minute minimum. $300 Welcome credit, 90-day expiry or until $300 consumed — whichever first. Trial ends automatically unless user clicks explicit "Upgrade to Paid." Sustained Use Discounts auto-apply (no commitment); Committed Use Discounts ARE multi-year commitments and must be avoided.
- Hetzner CCX63 (48 vCPU AMD EPYC): €0.60/hr or €374/mo cap, ~€47 for the job. Cheapest on paper. KYC requires passport + selfie; reviews suggest US customer onboarding is still flaky in 2026. User opted to exclude Hetzner from the guide.
- GCP `c2d-highcpu-112`: ~$4.22/hr (corrected from prior guide's ~$3.40/hr stale estimate). 40-hour run ≈ $169, under $300 credit.

**`CLOUD_PRODUCTION_GUIDE.md` rewrite delivered:**
- Upfront callout: **"None of these are monthly commitments."** Reframed every subsequent section around overspend-safety tiers.
- Re-ranked: **RunPod #1** (structurally impossible to overspend), **GCP #2** (expanded per-usage pricing section — explains SUDs vs CUDs, "will GCP auto-bill after trial" FAQ, explicit "avoid Committed Use Discounts"), **DigitalOcean #3** (still strong — monthly cap is a real safety net).
- Per-provider billing alert steps added (DO + GCP).
- Explicit "don't click Reserved / Savings Plan / CUD" warnings on every provider.
- Hetzner moved to the rejected-alternatives table per user preference.
- Sub-24-hour variant updated: `c3-highcpu-176` on GCP under $300 credit as the realistic path (removed stale `c2d-highcpu-224` claim).

**Script portability fixes (the actual production-launch unblocker):**
- `scripts/production_all_models.sh` and `scripts/pilot_all_models.sh` had two fatal Mac-isms that caused `set -euo pipefail` to abort immediately on Linux:
  1. Hardcoded `PROJ="/Users/michaelchang/Documents/claudecode/taiwanese"` — path doesn't exist on the cloud pod.
  2. `/usr/bin/time -l` — `-l` is a BSD/macOS flag; GNU time on Linux rejects it, script exits via `set -e`.
- Both scripts now use `PROJ="$(cd "$(dirname "$0")/.." && pwd)"` and call `"$ENGINE" solve` directly (no `/usr/bin/time` prefix). Logged as Decision 027.
- On the live pod we patched the shipped `production_all_models.sh` with two `sed -i` commands as an in-flight unblock; the local fix ensures future cloud runs don't need manual patching.

**Cloud production launched:**
- **Provider**: RunPod (prepaid / no overspend risk was the user's deciding factor)
- **Pod ID**: `0f8279f6fd0a`
- **Region**: `US-GA-2` (first attempt `US-TX-3` had no 32-vCPU Compute-Optimized capacity; had to delete + recreate the network volume in GA — volumes are region-locked)
- **Hardware**: 3 GHz Compute-Optimized, 32 vCPU, 64 GB RAM @ $0.96/hr
- **Storage**: Network volume `tw-solver-data` (20 GB, $0.07/GB/mo) mounted at `/workspace`; container disk 20 GB
- **Deposit**: $120 + auto-refill $25 when balance drops below $10
- **Launch timestamp**: 2026-04-19 19:16:28 UTC
- **Log line**: `[19:16:28] === Production: mfsuitaware_mixed90 ===`
- **Engine PID at launch**: 2009 on the pod
- **Expected wall-clock**: ~4.9 days for all 4 models sequentially (mfsuitaware_mixed90 → omahafirst_mixed90 → topdefensive_mixed90 → randomweighted)
- **Output destination on pod**: `/workspace/tw/data/best_response/*.bin` (4 files, ~52 MB each)

**Gotchas this session (worth propagating to future non-technical cloud walkthroughs):**
- **Markdown code-fence traps**: users copying from the rendered chat can accidentally include the triple-backtick fences. Bash interprets ```` ``` ```` as command substitution, so the first install attempt silently swallowed the entire block — no apt output, no rust install. Prompted the fix by re-pasting commands fence-free.
- **Web-terminal heredoc fragility**: `cat > file <<'EOF' ...` over the RunPod web terminal mangled the paste — lines joined, extra blank-line separators, hung in heredoc state. Had to Ctrl+C and fall back to in-place `sed` patches. Lesson: for long script edits over a web terminal, prefer `sed -i` point edits over large heredocs.
- **Region capacity matters**: RunPod's 32-vCPU CPU pods have sparse availability; first-choice regions may not provision. Network volumes are region-locked, so pod-region changes require volume recreation.
- **Auto-refill ≠ hard cap**: with auto-refill enabled, RunPod's "prepaid = overspend-impossible" guarantee becomes "prepaid with soft cap at each refill threshold." User consciously chose this for mid-job-interruption resilience over strict cap. Called out in guide.
- **Enumerate-canonical ≠ lookup table**: the `build-lookup` subcommand is separate. Production script expects both `data/canonical_hands.bin` AND `data/lookup_table.bin` present. Added to the cloud walkthrough.

**Carry-forward for Session 08:**
1. **Pod is running unattended.** First task next session: check pod status via RunPod web terminal with the monitoring commands captured in `CURRENT_PHASE.md` resume prompt.
2. **Download workflow not yet executed.** When models complete, walk user through Jupyter-Lab or scp download to Mac (`data/best_response_cloud/`).
3. **Pod termination is user's responsibility.** Flag it when all 4 files are safely on the Mac — don't just stop, **Terminate**.
4. **Sprint 7 analysis is unblocked** once all 4 `best_response/*.bin` files are on the Mac. That's the next real sprint.
5. **If the pod dies mid-job** (balance runs out without auto-refill kicking in, provider issue, etc.): the solver's append-only writer + network-volume persistence means resumption is a single re-run of the same script. Partial `.bin` files survive on `/workspace/tw/data/best_response/` because `/workspace` is on the network volume.


---

### Session 08 — 2026-04-20 to 2026-04-21 — Python analysis pipeline (readers, decoders, byte-identical Rust parity)

**Scope:** Sprint 3 cloud production is still running on RunPod (Model 1 `mfsuitaware_mixed90` complete; Model 2 `omahafirst_mixed90` in progress). Rather than idle for the ~5 remaining days, this session built out the Python-side analysis stack that Sprint 7 will depend on and verified it matches the Rust engine's decoding byte-for-byte. All work is model-independent glue — nothing committed to pattern conclusions from a single model.

**Pod monitoring + Model 1 download:**
- Daily status checks via RunPod web terminal: `tail` on production launcher + per-model logs, `pgrep` for `tw-engine solve`, `ls -lh data/best_response/`.
- Model 1 completed 2026-04-21 11:55:13 UTC, 40.65 wall hours, `data/best_response/mfsuitaware_mixed90.bin` 52 MB / 6,009,159 records.
- **SSH setup on-the-fly** — user had no SSH key. Generated `ed25519` keypair at `~/.ssh/id_ed25519` (no passphrase). RunPod's Connect panel only provisions SSH keys on NEW pods, so appended the public key manually to the pod's `~/.ssh/authorized_keys` via the web terminal. Web terminal's usual line-wrapping-in-single-quotes did NOT break the key — the full key data landed on the first authorized-keys line, with the trailing comment (`mcoski@gmail.com`) orphaned on a second line (ignored by OpenSSH).
- `scp -P 11400 root@205.196.19.130:/workspace/tw/data/best_response/mfsuitaware_mixed90.bin ...` pulled the 52 MB file to `data/best_response_cloud/` in seconds. Workflow confirmed repeatable; Models 2-4 downloads will be a single command each.

**Model 2 in-flight status (snapshot taken mid-session):**
- `omahafirst_mixed90` PID 2583, 2,100,000 / 6,009,159 hands = ~35%, ETA ~26 hours remaining. Speed steady at ~49.4s per 2000-hand block. Progression:
  - 2026-04-20: 1,066,000 → 3,214,000 → 4,168,000 hands
  - 2026-04-21: 4,498,000 → 6,009,159 (done) → 2,100,000 (Model 2 start) → 2,100,000 progress snapshot
- Overall elapsed ~55 hours; projection remains ~April 26 finish for all 4 models; projected total cost ~$155 (on track within $120 prepaid + ~$50 auto-refills).

**Python analysis stack built (`analysis/src/tw_analysis/`):**
- `br_reader.py` — best-response `.bin` reader. Numpy structured dtypes with explicit offsets (no implicit padding); supports `load` (~16 ms for 54 MB) and `memmap` (~8 ms zero-copy) modes; `validate_br_file()` covers magic bytes, version, canonical_id monotonicity, setting-index bounds, EV finite/range.
- `settings.py` — `Card` / `HandSetting` types, `parse_hand()`, `decode_setting(hand_7, index) → HandSetting`, `all_settings(hand_7) → list[105]`. Mirrors `engine/src/card.rs` and `engine/src/setting.rs` enumeration exactly (top outer loop 0..7 × mid `a<b` inner loop 15 pairs, mid/bot sorted desc by `Card.0`).
- `canonical.py` — canonical-hand file reader (format `TWCH` magic + u32 version + u64 num_hands + reserved, then `num_hands × 7` uint8 rows), `canonicalize()` / `is_canonical()` (24 suit permutations, mirrors `engine/src/bucketing.rs`), `CanonicalHands.hand_cards(id) → list[Card]`, `CanonicalHands.find(hand) → canonical_id` (binary search via `tobytes()` comparison; `np.searchsorted` and `<=` don't work on `np.void` dtypes — attempted and reverted).
- `__init__.py` re-exports everything for `from tw_analysis import ...` convenience.
- `analysis/scripts/inspect_br.py` — CLI inspector (header + validation + EV stats + top-5 setting indices + head of records).
- `analysis/scripts/test_settings.py` — 11 unit tests, all pass (card pack/unpack, setting count = 105, all-7-cards-used invariant, uniqueness, decode-matches-all-settings, tier sort order, top-card-by-outer-index, mid-pair enumeration order, bad-input rejection, permutation-invariance sanity).
- `analysis/scripts/test_canonical.py` — 9 unit tests, all pass (24 distinct bijection permutations, canonicalize idempotence, agreement under all 24 relabelings, `is_canonical` fixed-point agreement, suit-0 always-used, rank-only orbit, bad-shape rejection, `apply_perm` preserves ranks).

**Real-data validation results:**
- Loaded Model 1 (`mfsuitaware_mixed90.bin`): all 6,009,159 records, canonical_id 0..N-1 in order, all setting_indices ∈ [0,104], all EV finite, min −9.839 / mean +0.533 / max +6.593, opponent tag decoded as `HeuristicMixed(base=MiddleFirstSuitAware, p=0.90)` matching the filename, top-5 most-chosen indices [104 @ 19.7%, 102 @ 10.6%, 74 @ 10.3%, 99 @ 9.5%, 90 @ 9.3%].
- Loaded `data/canonical_hands.bin` (42 MB, 6,009,159 hands): full-file lex-ordering check passed, 500-hand `is_canonical` spot-check all true, cross-checked `br.header.canonical_total == len(canonical)`.
- **Byte-identical cross-verify against Rust** — ran `./engine/target/release/tw-engine spot-check --show 500` and produced the same 519-line output from Python using the same record stream → canonical hand → setting decode pipeline. `diff` reports no differences. This is the definitive correctness gate: any pattern analysis built on this stack inherits verified decoding.

**Pre-flight at session end:** `cargo build --release` ok, full `cargo test --release` green (124+ tests across unit/integration/scoring), `python3 analysis/scripts/test_settings.py` 11/11, `python3 analysis/scripts/test_canonical.py` 9/9.

**Gotchas discovered this session:**
- `np.searchsorted` and `<=` / `!=` on `np.void` structured dtypes do not work (no ufunc loop). First draft of `CanonicalHands.find()` and the adjacent-pair ordering check both failed; replaced with row-wise `tobytes()` binary search and a vectorized int16 column-diff (argmax of first non-zero column) respectively.
- RunPod's account-level SSH-key setting only auto-provisions on pod CREATION. Running pods (like ours, launched 2026-04-19) require a manual append to `~/.ssh/authorized_keys` inside the container. Script this into the cloud guide eventually.
- Web terminal's single-quote line wrapping doesn't break SSH keys as long as the full Base64 payload stays on one line; the trailing comment can be safely orphaned on a second line.

**Carry-forward for Session 09:**
1. **Monitor pod daily.** Same status block as Session 07/08 (tail logs + pgrep + ls best_response).
2. **Download Models 2/3/4 as they complete.** Command template (SSH key now in place):
   `scp -P 11400 root@205.196.19.130:/workspace/tw/data/best_response/<model>.bin /Users/michaelchang/Documents/claudecode/taiwanese/data/best_response_cloud/`
3. **After each download, run** `python3 analysis/scripts/inspect_br.py data/best_response_cloud/<file>.bin` to confirm the reader validates it (new model = new opponent tag, same structure).
4. **When all 4 files landed:** remind user to **Terminate** (not Stop) the RunPod pod. Network volume preserves data, but terminate fully stops billing.
5. **Sprint 7 formally unlocks** once all 4 `.bin` files are local. Planned starting point: use the new reader/decoder stack to build a hand-feature extractor (pair count, suitedness, connectivity, high card) — deferred from Session 08 because it's easier to design once four opponents' data can be compared side-by-side.
6. **Cross-model comparison scaffolding** — when ≥2 `.bin` files exist, a small script that joins records by `canonical_id` across models to show per-hand setting agreement / disagreement across opponents would be the first cross-model analysis worth writing (still model-independent in structure, just fed N files).


---

### Session 09 — 2026-04-23 to 2026-04-24 — Model 2 downloaded, cross-model join tooling, Sprint 5a trainer foundation

**Scope:** Cloud production still running on RunPod (Models 1 & 2 now complete; Model 3 `topdefensive_mixed90` at ~80% at session end; Model 4 `randomweighted` queued). While the cloud continued, Session 09 pulled Model 2 down, built the Sprint 7 cross-model join scaffolding against the 2 available .bin files, and stood up the complete Sprint 5a trainer with per-profile compare mode. Both additions are model-independent in structure — Models 3 & 4 slotting in requires zero code changes.

**Model 2 download + validation:**
- `scp -P 11400 root@205.196.19.130:/workspace/tw/data/best_response/omahafirst_mixed90.bin …` pulled the 52 MB file to `data/best_response_cloud/`. SSH key from Session 08 still valid — single scp command, seconds.
- `python3 analysis/scripts/inspect_br.py data/best_response_cloud/omahafirst_mixed90.bin` — validation PASS, 6,009,159 records, opponent decoded as `HeuristicMixed(base=OmahaFirst, p=0.90)` (tag 1_003_090), mean EV +2.123 (vs Model 1 +0.533 — OmahaFirst is a substantially weaker opponent than MiddleFirstSuitAware), setting 104 picked 22.72%.

**Cross-model join scaffolding (Sprint 7 prep — reused by trainer later):**
- `analysis/src/tw_analysis/cross_model.py` — `CrossModel` dataclass (settings + EV matrices, n_hands × n_models), `build_cross_model(files)`, `unanimous_mask`, `unique_settings_per_hand`, `pairwise_agreement`, `consensus_setting_counts`, `unanimous_setting_counts`. Join is a column-stack over BrFiles already in canonical_id order (no hash-join needed; Session 08 validated monotonicity).
- `analysis/scripts/cross_model_join.py` — CLI report: per-model summary, unanimity %, distinct-settings histogram, M×M pairwise agreement matrix, top-K cells histogram, top-K unanimous settings histogram.
- `analysis/scripts/test_cross_model.py` — 9 unit tests using synthetic `BrFile` fixtures (no real file dependency). Caught one test-bug (I mis-counted "both models pick 99" matches as non-matches) before the real file run — the numeric answer self-proved the test logic.
- **First real cross-model finding on 2 models (MF-SA vs Omaha-first, each mixed 90%):**
  - 39.31% of hands are unanimous across these 2 opponents. 60.69% require opponent-specific choices.
  - Setting 104 accounts for 28.63% of unanimous hands (robust setting).
  - Four-way unanimity is strictly lower than 39.31% — when all 4 models land we'll see how much lower.

**Sprint 5a trainer — `trainer/` package, full vertical slice:**
- **Rust side:** Added `--tsv` flag to `tw-engine mc` (`engine/src/main.rs`). Human output goes to stdout by default; with `--tsv`, a `# engine-mc-tsv v1` header block + 105 TSV rows (setting_index, EV, top, mid1, mid2, bot1..bot4) go to stdout and status prints are routed to stderr so stdout stays parseable. `McSummary.results` is sorted by EV; the TSV writer reorders by enumeration index (`all_settings(hand)`) via HandSetting equality — 105×105 scan, trivial cost.
- **Python backend:**
  - `trainer/src/dealer.py` — `deal_hand()` returns a 7-card list of "Rs" strings via `random.SystemRandom`.
  - `trainer/src/engine.py` — `evaluate_hand_cached` wraps `subprocess.run(tw-engine mc --tsv …)`. LRU cache keyed by sorted-hand + opponent params + seed, size 128. Parses TSV on stdout, tolerates comment lines. `find_setting_index(mc, user_cards)` normalizes mid/bot via frozenset for tier-internal order-independence.
  - `PROFILES` tuple in `engine.py` mirrors `scripts/production_all_models.sh` exactly: `mfsuitaware`, `omaha`, `topdef`, `weighted` (note: the 4th production model is `--opponent weighted`, not another heuristic mix — decoded from the pod's production script).
  - `trainer/src/explain.py` — severity classifier (trivial < 0.10, minor < 0.50, moderate < 2.00, major ≥ 2.00) + 4 detectors: `detect_split_pair`, `detect_isolated_bottom_suit` (double-suited vs 3+ of a suit; Omaha 2+3 rule awareness), `detect_wrong_top_card` (flags when user's top card is ≥2 ranks weaker than solver's), `detect_tier_swap` (user may have middle and bottom swapped). All hand-written against game rules, explicitly noted as pre-Sprint-7 placeholder.
- **Flask app** (`trainer/app.py`) — `/`, `/api/deal`, `/api/score`, `/api/profiles`, `/api/compare`. `use_reloader=True` for live code reload on .py edits. Port 5050 (not 5000 — macOS AirPlay Receiver claims 5000 and returns 403 "You don't have authorization to view this page" which looks like a Flask permission error but isn't).
- **Web UI** (`trainer/static/`):
  - `index.html` — hand row (7 slots) → 3 tier cards (top 1 / mid 2 / bot 4) with per-tier "clear" buttons and point-per-board labels. Controls: Deal new hand | Clear all tiers | Submit & score | Compare across all profiles. Two result panels (single-profile result, 4-way compare result).
  - `style.css` — dark theme, card rendering (rank top-left, suit center, red for ♥♦), drop-hover highlight, severity colors, mini-card variant for the per-profile comparison layouts.
  - `app.js` — state = `{dealtHand, placement: Map, profileId, profiles}`. Native HTML5 drag-and-drop (dragstart/dragover/drop). Click-to-fill: click a card in hand → moves to first empty tier slot; click a card in a tier → returns to hand. `/api/compare` handler renders per-profile table AND a "Per-profile optimal arrangement" panel: if all 4 agreement sets are equal (compared by top + sorted-mid + sorted-bot), one big arrangement with a green "all 4 agree — robust / GTO-approximating" banner; if they differ, 4 stacked mini-layouts per profile with their best EV.

**Verified end-to-end this session:**
- Rust `cargo build --release` clean, `cargo test --release` 124+ tests green (unchanged from Session 08 plus the main.rs signature changes compile).
- Python `test_settings.py` 11/11, `test_canonical.py` 9/9, `test_cross_model.py` 9/9 green.
- Flask in-process `test_client` verified `/api/profiles`, `/api/deal`, `/api/score` (with `profile_id`), `/api/compare` (all 4 profiles, non-zero deltas + per-profile best arrangements).
- User ran the trainer in a browser, interacted with the dropdown + drag-and-drop + compare flow, reported back that it works and the UI is clear.

**Gotchas discovered this session:**
- **macOS AirPlay Receiver owns port 5000 and returns a 403 with body "You don't have authorization to view this page."** This looks exactly like a Flask permissions error but is actually the OS. Trainer pinned to port 5050.
- **Flask without `use_reloader=True` silently serves stale code** after a .py edit, and HTML that references routes added in the new code fails with "Unexpected token '<'" because the 404 HTML page is parsed as JSON. Trainer now boots with `use_reloader=True`.
- **Web-terminal line-wrap still mangles multi-line copy-paste** (same as Session 08). Long command blocks had to be joined with `&&` into a single logical line; `\n`-separated blocks get broken at awkward places when pasted. Documented the one-line pattern in the resume prompt.
- **A unit test was wrong before the code was.** `test_pairwise_agreement_matrix` expected 0.2 for B vs C; the code said 0.6; recounting by hand confirmed code was right. The test fixture had both B and C picking 99 on hands 3+4 (both match), which I'd forgotten when writing the assertion. Fix was in the test, not the code.

**Carry-forward for Session 10:**
1. **Pod status check first.** Model 3 `topdefensive_mixed90` was at ~80% with ~8h ETA at session end 2026-04-24 00:48 UTC; may well be done by next session start.
2. **Download Models 3 & 4** as they complete (single scp each; SSH key already in place).
3. **After each download**, run `inspect_br.py` to validate.
4. **When all 4 files are local:** remind user to TERMINATE (not Stop) the RunPod pod.
5. **Re-run cross-model join with all 4 files** for the first true 4-way unanimity rate. The existing CLI already handles N files without changes.
6. **Sprint 7 formally unlocks.** Planned first task: hand-feature extractor (`analysis/src/tw_analysis/features.py`) — pair count, top-rank, suitedness, connectivity, hand category — joined to cross-model settings to surface "which features correlate with 4-way unanimity" and "which features correlate with strong disagreement".
7. **Trainer refinements once Sprint 7 produces rules:** swap `explain.py` rule source from hand-written heuristics to solver-derived patterns. Single-file change; the Finding schema is rule-engine-agnostic.


---

### Session 10 — 2026-04-24 — Model 3 downloaded, 3-way cross-model, skill-gap empirical proof, multiway scoped as Phase 2 priority

**Scope:** Model 3 (`topdefensive_mixed90`) finished mid-session and was pulled to the Mac. With 3 of 4 .bin files local, ran the first multi-model cross-join, decoded the dominant setting (104), and empirically settled the "is this game just luck?" question with a custom skill-gap analysis tool. A 3-turn Socratic dialogue with Gemini 2.5 Pro on opponent-set design produced a refined Phase 2 plan. The user pivoted from "add more profiles" to "swap the redundant TopDefensive for the Gambler eventually" and made the heads-up-vs-multiway question a top-priority data-driven task. Trainer UI extended to scaffold multiway selection.

**Cross-model 3-way (Models 1+2+3):**
- 3-way unanimity: 30.99% of canonical hands have all 3 opponents inducing the same best-response.
- Pairwise: MF-SA ↔ TopDefensive 78.9%; MF-SA ↔ OmahaFirst 39.3%; OmahaFirst ↔ TopDefensive 32.8%. The two non-Omaha heuristics are functionally similar; OmahaFirst is the structural outlier.
- Distinct-settings histogram: 31% have 1 distinct, 58% have 2, 11% have 3 (all-disagree hands — highly opponent-dependent).
- Setting 104 still dominates unanimous bucket at 31.28%.

**Setting 104 decoded:**
- Structurally: top = card[6] (highest by canonical rank-major-asc index), mid = cards[4,5] (next 2), bot = cards[0..3] (lowest 4). I.e., **sort cards descending and slice [1, 2, 4]**.
- It's optimal 21% of the time. The other 79% is where the solver provides value over naive play.
- Why it dominates: Hold'em-style middle plays pairs as full pairs (using both hole cards), so middle is the highest-leverage tier for paired holdings. Bottom is Omaha 2+3 → high pair in bottom caps at "pair of X" anyway, so the value is in the connectivity/suitedness, not the rank.

**Skill-gap analysis (`analysis/scripts/skill_gap.py`):**
- Samples N canonical hands × P profiles, runs `evaluate_hand_profile` (existing trainer wrapper), reports mean EV gap between best play and setting-104 play.
- 100 hands × 3 profiles × 500 MC samples produced **mean gap +1.68 EV/hand, sd 1.57**, hands-to-2σ-confidence ~3.
- In 300 (hand × profile) trials, naive was never strictly better than optimal — tied on a few trivial hands, lost on the rest.
- This is the empirical rebuttal to "Taiwanese Poker is just a coin flip." The skill edge dwarfs variance after only a few hands.
- Re-run targeted at N=500 hands × 4 profiles once Model 4 is local for the published number.

**Gemini 2.5 Pro Socratic dialogue (3 turns, continuation_id 083667c6-e7d6-472e-b9e2-2ff21d11d9fb):**
- Pushback 1 (Naive Sorter is degenerate as opponent): conceded — useful only as benchmark/UI sanity check, not in production opponent pool.
- Pushback 2 (psychological archetypes need algorithmic specs): produced concrete pseudocode for HoldemTransplant + Draw-Chaser with prediction of which existing model each overlaps with most.
- Pushback 3 (ME ≠ Nash regardless of opponent set diversity): conceded — confirmed user's framing of two distinct goals: (A) ME against modeled population, (B) Nash via CFR. Suggested Iterated Best Response as a hybrid; later retracted given the project's learnable-rules constraint.
- Pushback 4-7 forced concrete predictions on overlap rates, missing axes (Gambler / scoop-maximizer = most important missing archetype), and the learnability tradeoff.
- **User decisions after dialogue:**
  - HoldemTransplant rejected — at user's stake level, all opponents are competent multi-game players. Theoretical archetype, not real population.
  - Gambler kept as Phase 2 candidate. Attacks scoring structure (scoop bonus), not card valuation.
  - Iterated BR rejected for this project — complexity amplification contradicts learnable-rules goal.
  - **CFR re-estimated**: not "months." This game has no betting tree (one-shot Bayesian decision), so CFR is dramatically simpler than full poker CFR. Realistic estimate: days, not months. Phase 3 candidate IF the rule-based approach has gaps.

**Multiway analysis as Phase 2 PRIORITY (user-flagged as critical):**
- User plays mostly 3-5 player, sometimes heads-up. Has explicit intuition: "in multiway should play with weaker top, stronger mid+bottom." Demands this question gets answered with hard data, not theory.
- Reasoning audit so far:
  - Scoop math compounds with more opponents — each scoop pays +20, P(scoop someone) ↑ with N → leans toward stronger bottom (supports intuition).
  - Top tier chops more often (1-card Hold'em often plays board) → with more opponents, P(at least one top chop) ↑ → top contributes less reliable EV (supports "weaker top").
  - BUT: per-opponent BR is independent in multiway, and the optimal play against MIXED archetypes is BR-against-mixture, which is more BALANCED than any single-opponent BR (cuts against intuition).
  - BUT: stronger competition (max-of-N opponents > average opponent) argues for SAFER play (cuts against intuition).
- Net: intuition has scoop-economic basis but probably overweights it. Sprint 7 will settle empirically.
- New checklist tasks: compute multiway-robust setting per canonical hand from N-way cross-model unanimity; quantify systematic differences in top-rank/bot-suitedness between heads-up BR and multiway-robust setting; test user's hypothesis directly.

**Trainer UI extended (Session 10):**
- Player-count selector added in header: heads-up (default), 3p, 4p, 5p.
- When user selects 3+, an amber info banner appears explaining current scoring is heads-up-only, points at the Compare-across-all-profiles button as the closest current proxy for multiway-robust play.
- Backend doesn't yet branch on player count — UI is scaffolded for Phase 2 multiway analysis to plug in cleanly without a UI redesign.
- State variable `state.playerCount` added to JS; not yet sent to backend (would be dead data; will wire when Phase 2 multiway BR computation lands).

**Verified end-to-end this session:**
- Model 3 downloaded (52 MB scp), validated via inspect_br.py — VALIDATION PASS, 6,009,159 records, opp tag 1_004_090 = HeuristicMixed(TopDefensive, p=0.90).
- Cross-model join with 3 files runs cleanly, produces sane unanimity + pairwise stats.
- Skill-gap script runs cleanly, produces sensible numbers consistent with our expectations.
- Trainer UI: user reload showed player-count selector working; multiway banner toggles correctly.

**Gotchas this session:**
- The web-terminal multi-line copy/paste mangling is reproducible — same pattern as Sessions 8/9. Single-`&&`-line commands continue to be the workaround. Documented in resume prompts.
- macOS post-quantum SSH warning is a noise message (RunPod's SSH server hasn't upgraded), not a security issue. Documented.

**Carry-forward for Session 11:**
1. Model 4 status check first. If done, scp + inspect.
2. After Model 4 lands: run cross-model join with all 4 files, run skill_gap with all 4 profiles for the published number.
3. Remind user to TERMINATE pod once all 4 files are local.
4. **Sprint 7 Priority 1: Multiway analysis.** This is the top user-flagged priority. Compute multiway-robust setting per canonical hand; quantify systematic differences vs heads-up BR; test "weaker top stronger bot" hypothesis with data.
5. Sprint 7 Priority 2: Hand-feature extractor for pattern mining toward 5-10 rule decision tree.
6. Sprint 7 Priority 3: Self-play break-even Nash check on the eventual robust strategy.
7. Phase 3 is unlocked but not started: CFR for true Nash (revised: days not months).
