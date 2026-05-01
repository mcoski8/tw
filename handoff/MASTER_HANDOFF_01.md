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


---

### Session 11 — 2026-04-26 — Cloud production COMPLETE. Full 4-way analysis. Multiway hypothesis test.

**Scope:** Final session of Sprint 3 cloud production. Pulled Model 4 (`randomweighted`) to the Mac, validated, terminated the RunPod pod. Ran the first complete-data analyses: full 4-way cross-model join, full 4-profile skill-gap (definitive answer to "is this game skill-driven?"), and the first multiway-robust hypothesis test answering the user's "weaker top, stronger mid+bot in multiway" intuition with hard data. Sprint 3 declared complete; Sprint 7 unblocked.

**Pod termination flow (RunPod UX gotcha):**
- RunPod's UI doesn't expose a "Terminate" button directly; the action is two-step: **Stop Pod** first (halts compute billing immediately), then a **Delete Pod** option appears on the now-stopped pod. User had $3.76 in residual credit at termination; ~3+ remaining.
- The network volume `tw-solver-data` survives termination by default (cheap to keep, ~$0.07/GB-month for ~200 MB). Recommended retention for a few days as belt-and-suspenders backup; can delete once trainer confirms .bin integrity in production.

**Cross-model 4-way (all 4 profiles):**
- 26.68% unanimous (down from 30.99% with 3 profiles, 39.31% with 2). Each new profile cuts unanimity proportionally as you'd expect.
- 49.96% have 2 distinct settings, 20.64% have 3, **2.71% have all 4 distinct** — the "highly opponent-dependent" hands worth flagging in the trainer.
- Pairwise agreement matrix is the most insightful artifact. **OmahaFirst is the structural outlier** — agrees only 33-43% with each of the other 3. The other three (MF-SA, TopDef, RandomWeighted) cluster at 58-79% pairwise. This validates the user's reframe that opponent-strategy convergence is the signature of approaching equilibrium; OmahaFirst's distinct prioritization (loading the bottom Omaha tier) is what separates it.

**Skill-gap analysis at production scale (rebuttal to "game is just luck"):**
- N=500 canonical hands × 4 profiles × 1000 MC samples = 2,000 trials. Each trial compares the optimal best-response EV to the EV of always-playing-setting-104 (sort-cards-descending-and-slice).
- Cross-profile mean gap: **+1.538 EV per hand** in favor of optimizer. Per-hand variability sd ≈ 1.66. Hands-to-2σ confidence in skill edge: **~5**.
- Naive play strictly beat optimal in **0 of 2,000 trials.** Tied on a few easy hands. Lost on the rest.
- At $1/point stakes, optimizer extracts +$153.80 of pure skill edge per 100 hands vs naive play. The "glorified coin flip" claim is empirically falsified by orders of magnitude.

**Multiway hypothesis test (user's Sprint 7 P1 priority):**
- New script `analysis/scripts/multiway_analysis.py`. For each canonical hand, computes the multiway-robust setting as the MODE of the 4 per-profile best-responses (Decision 030 — see DECISIONS_LOG.md for the methodological choice + alternatives considered).
- 200K-hand random sample. Agreement-class breakdown:
  - Unanimous (4-of-4): 26.6%
  - 3-of-4 majority: 40.4%
  - 2-of-4 (2-1-1): 20.6%
  - 2-2 split: 9.6%
  - All distinct (1-1-1-1): 2.7%
  - **67% clear-majority hands; 12.3% genuinely contested.**
- Hypothesis "multiway favors weaker top, stronger mid+bot" tested on 5 axes:

| Δ axis | Effect | Direction | Verdict |
|---|---|---|---|
| Top rank | −0.18 | Lower in multiway | ✓ |
| Mid pair rate | +2.2 pp | More pairs | ✓ |
| Mid rank-sum | +0.22 | Higher | ✓ |
| Bot DS rate | +1.2 pp | More double-suited | ✓ |
| Bot rank-sum | −0.04 | Essentially zero | ✗ |

  4 of 5 axes directionally consistent with the user's intuition. The only axis where the intuition is wrong: bottom isn't higher-RANKED in multiway, it's better-STRUCTURED (more often double-suited). Stronger bot in the connectivity/suitedness sense, not the rank sense.

- **Unanimous-only subset shows the clean rule** the trainer can teach: mid pair rate jumps to **90.5%**, bot DS rate to **45.8%**, top rank UP at 12.65. When robust play is unambiguous, the structural rule is "high card top, pair middle, double-suited bottom" — same direction as setting 104 but more disciplined.

**Verified end-to-end this session:**
- Model 4 download via single scp, 100% in ~10 seconds. inspect_br.py PASS (54 MB, 6,009,159 records, opponent tag 6 = RandomWeighted).
- All 4 .bin files re-validated via batch inspector script.
- Pod terminated. Compute billing stopped.
- cargo build + cargo test green (Rust unchanged this session).
- Python tests green (settings 11/11, canonical 9/9, cross_model 9/9).
- Cross-model join with 4 files runs cleanly.
- Skill-gap script runs at N=500 × 4 profiles × 1000 samples in ~40 minutes (background) and produces stable numbers.
- Multiway analysis script runs at 200K-hand sample in ~2 minutes; produces all expected outputs.

**Gotchas this session:**
- Skill-gap script had a leftover hardcoded filter (`if p.id in ("mfsuitaware", "omaha", "topdef")`) from when only 3 .bin files existed. Updated to use all 4 production profiles. Worth checking similar filters in any other Sprint 7 scripts as they're written.
- Web-terminal multi-line copy/paste mangling continues to be reproducible. Status checks must be single-line `&&`-chained commands. `pgrep -af "tw-engine solve"` mangled into pgrep with no args, which then echoed the misleading "Job stopped." fallback. Workaround: cross-check against file mtimes and progress-log tails which are definitive.
- RunPod "Terminate" is a two-step Stop-then-Delete UX. Future sessions should document this in the pod-termination instructions if cloud runs resume.

**Carry-forward for Session 12 (Sprint 7 rule mining proper):**
1. Build `analysis/src/tw_analysis/features.py` — hand-feature extractor: pair count + ranks, top-card rank, suitedness, connectivity, hand category. Output Parquet/SQLite for fast queries.
2. Pattern mining toward 5-10 rule decision tree. Test rule candidates as predicates and measure agreement with multiway-robust mode setting on 6M hands.
3. Self-play break-even Nash check on the eventual rule strategy.
4. Trainer integration — swap explain.py from hand-written heuristics to mined rules; add "rule firing" view.
5. Optional: re-run multiway_analysis.py at full 6M hands for the published number (sample run is representative; full run for the publication).
6. Optional: scoop-frequency-by-player-count analysis (the deferred multiway question).


---

### Session 12 — 2026-04-26 — Sprint 7 Phase A: feature pipeline + rule encoding + first GTO baseline

**Scope:** Sprint 7 P1 (feature extractor + Parquet) and Sprint 7 P2 (pattern mining toward decision tree) — both delivered. Built end-to-end: scalar+vectorized feature extractor, comprehensive miner, encoded the 7 candidate rules as actual strategy functions, and measured shape-agreement vs the multiway-robust setting on all 6,009,159 canonical hands. Pulled in user's home-game **buyout option** as a new strategic dimension and quantified its applicability rate + signature. Mid-session Socratic dialogue with Gemini 2.5 Pro on the "encode-then-measure vs build-infrastructure-first" decision; integrated pushback as a hybrid path.

**What landed:**

1. **Feature extractor (`analysis/src/tw_analysis/features.py`)** — scalar reference + numpy-vectorized batch implementations of HAND_FEATURE_KEYS (n_pairs, pair_ranks, n_trips/quads, top/2nd/3rd rank, suit_max/2nd/3rd/4th, n_suits_present, is_monosuit, connectivity with wheel-low ace, n_broadway, n_low, category_id) and TIER_FEATURE_KEYS (top_rank, mid_is_pair/suited/high/low/sum, bot_suit_max/DS/n_pairs/pair_high/high/low/sum/n_broadway/connectivity). Multiway-robust mode resolver `compute_multiway_robust(per_profile)` returns (mode setting, agreement class, mode count) — vectorized via `((N,4)==(N,1,4)).sum(axis=2)` argmax. **Scalar/batch parity gate** (`assert_scalar_batch_parity`) per Decision 028 discipline; called inside `build_feature_table.py` on first chunk before anything trusts the batch path. 24 unit tests (`test_features.py`) covering all categories + wheel + monosuit + edge tier decompositions, all green.

2. **Feature table CLI (`build_feature_table.py`)** — streams canonical_hands.bin + 4 .bin files in 250K-row chunks, computes hand features + per-profile BR settings + multiway-robust setting + agreement class + per-profile EVs + ev_mean/ev_min/ev_max derived. Writes `data/feature_table.parquet` (208 MB zstd-compressed, 51 columns, 6,009,159 rows). Agreement-class breakdown matches the 200K-sample numbers from Session 11 to two decimals (26.68% / 40.48% / 20.64% / 9.48% / 2.71%) — confirmation that the sample was representative. EV columns added mid-session after the buyout question came up; rebuild is ~2 minutes end-to-end.

3. **Pattern mining (`probe_rules.py`, `mine_patterns.py`)** — 9-section comprehensive miner answering every question the user brainstormed:
   - Trips placement: pure trips → mid 93.8% (low 81%, high 99%)
   - Trips+pair quadrants: trips→mid wins 75-96% in three quadrants; **trips_low+pair_high is the only one where pair displaces trips ~37%**
   - Quads → split 2 mid + 2 bot, 80-95% climbing with rank, dips at quad-A (73.6% — ace probably wants top)
   - Three-pair → highest pair to mid 75.4%; mid is **always** a pair (0% miss)
   - 9+ pair → mid 93.5%; J+ pair 95%+; A-pair 99.65%
   - When mid locked AND DS feasible: DS bot beats connected bot ~1.8x
   - Top = highest rank: 67.4% overall. Failure mode is pair-preservation: when highest IS paired, only 1.6% follow; when highest isn't, 82.7% follow. The **actionable rule** is "top = highest UNPAIRED rank."
   - Garbage hands (no pair, ≥3 low, ≤2 broadway): 6.4% of hands, mean ev_mean −0.98, but only 1.1% qualify for buyout

4. **Buyout analysis (NEW, user's home-game variant):** Pay 4 points per willing opponent to fold. Empirical:
   - Per-profile heads-up buyout +EV rate: vs MFSA 0.37%, vs TopDef 0.37%, vs OmahaFirst 0.01%, vs RandomWeighted 0.05%
   - 4-profile-mean buyout rate: **0.09%** (~5,600 of 6M hands)
   - **Anti-intuitive signature: NOT garbage hands. It's harmful pair structure.** Quads of 2-7 (lift 117x), pure low trips (8x), trips+low-pair (6.6x). High_only/two_pair/three_pair: ~0% buyout share.
   - Total selective-buyout edge in 4-handed play: ~+0.56 points per 100 hands.
   - Caveat: rates based on `best_ev` (optimal play); naive players should buy out more often.

5. **Encoded rule chain + GTO baseline (`encode_rules.py`)** — three strategies (NAIVE_104, SIMPLE, REFINED) implemented as `apply_rules(hand) → setting_index`. Inverse-decoder helper `positions_to_setting_index` round-trip-verified for all 105 settings. Critical methodology insight: literal `setting_index ==` agreement is **dominated by suit-position tie-break artifacts** (e.g., 3 ways to put a "pair of 4s" in mid produce 3 different indices but same play). Added **shape agreement** (compare `(top_rank, sorted_mid_ranks, sorted_bot_ranks)` tuples) — the rule-correctness measure that actually matters.

   Headline measurements (full 6M):

   | metric | NAIVE_104 | SIMPLE = REFINED |
   |---|---|---|
   | Overall LITERAL agreement | 20.09% | 49.06% |
   | **Overall SHAPE agreement** | **21.77%** | **53.58%** |
   | Unanimous slice (26.7%) | 30.13% | 82.93% |
   | Quads | 23.14% | 79.20% |
   | Three-pair | 17.90% | 72.88% |
   | Pair | 19.09% | 65.02% |
   | Two-pair | 26.12% | 59.16% |
   | Trips | 30.57% | 56.39% |
   | Trips_pair | 32.64% | 46.16% |
   | **High_only (no pair)** | 19.50% | **19.50% — biggest gap** |

   Rule chain is **2.5x better than naive** but leaves 46.42% mismatch. The single biggest miss category is `high_only` (35% of all misses, 80.5% miss rate within category) where the rule chain currently falls back to NAIVE_104 — and that fallback is wrong 80% of the time.

6. **Gemini 2.5 Pro Socratic dialogue (continuation_id ec08b754-69f3-479d-bb5a-c15fee965876):**
   Question: "encode current rules and measure" vs "build feasibility-flag + category-fix infrastructure first"? Gemini argued the latter on the strength of section-5 mining (high-pair-to-bot correlates with bot-DS 62%) — encoding without DS-feasibility would be incomplete. Synthesis: hybrid Phase A — derive feasibility from existing columns (`can_make_ds_bot ≡ suit_2nd ≥ 2`, `can_make_4run_bot ≡ connectivity ≥ 4`) instead of extending features.py; encode multiple competing strategies; let the gap measurement tell us whether refinement helps. **Result: SIMPLE = REFINED at 53.58% — confirms Gemini's point that the current REFINED doesn't actually refine anything beyond SIMPLE; Phase B needs ACTUAL conditional refinement, not renamed strategies.**

**Verified end-to-end this session:**
- Rust `cargo build --release` clean (no Rust changes this session); existing tests still green by extension.
- Python tests: `test_features.py` 24/24, settings 11/11, canonical 9/9, cross_model 9/9.
- `build_feature_table.py` full 6M run completes cleanly in ~2 minutes; output Parquet validates against Session 11's agreement-class numbers.
- `mine_patterns.py` full run completes in ~75 seconds; produces all 9 sections.
- `encode_rules.py` full 6M run completes in ~3 minutes; literal + shape agreement reported per strategy + per category + per agreement_class.

**Gotchas this session:**
- **LITERAL vs SHAPE agreement.** Massive trap. First smoke test on 50K hands showed SIMPLE at 3.74% literal agreement — looked like a fundamental bug. Actually was just suit-position tie-break: 3 equivalent (rank-equal) mid arrangements produce 3 different setting indices, my strategy picks one specific tie-break and the canonical robust answer's MC-mode picks another. Shape-agreement on the same data was 42.82%. Always trust SHAPE. Memorialized in `project_taiwanese_rule_baseline.md`.
- **First 50K canonical hands are NOT representative.** They're sorted ascending by card byte = lowest-rank hands first, which loads up trips+trips, quads+trips, and other structural edge cases. Smoke tests on the head are misleading; need to run on the full 6M or stratified sample.
- **Trips+trips edge case is mis-bucketed as "trips".** Hand with two trips (e.g., 2-2-2-3-3-3-4) has `n_trips=2` but my category logic only checks `pairs_ranks` for the "trips_pair" branch — so it falls through to "trips". Multiway-robust on these correctly splits both trips into bot for a 2-2-3-3 Omaha two-pair structure, while my SIMPLE strategy puts the higher trips in mid as a pair. Affects ~0.02% of hands; deferred to a future category-bucketing pass.
- **`n_trips=2` (two distinct trips), `n_quads=1+pair=1` (quads+pair), `n_quads=1+trips=1` (quads+trips) all collapse into wrong category buckets.** Combined ~0.5% of hands. Listed as deferred work.

**Carry-forward for Session 13 (Sprint 7 Phase B):**
1. **Close the high_only gap.** 35% of all rule misses are no-pair hands; miss rate 80.5% within category. Run mining on the high_only subset specifically — top-card distribution, mid-card composition (do robust answers prefer suited/connected mid pairs?), bot-DS preference. Hypothesize 2-3 rules; encode; re-measure. Expected payoff: chain from 53.58% → ~70%.
2. **Make REFINED actually refined.** Add the conditionals mining surfaced: "9+ pair → mid UNLESS trips OR higher pair", "mid-locked + can_make_ds_bot → optimize bot for DS", "trips_low + pair_high: pair displaces trips 37%". Currently SIMPLE == REFINED, which means my "REFINED" is misnamed.
3. **Investigate 17.1% miss rate on UNANIMOUS hands** (~273K hands). These are pure rule-logic failures, not opponent-dependent. Should reveal one or two missing rules.
4. **Buyout integration.** Add buyout pre-step: "if ev_mean < -4 vs actual opponent type, recommend buyout." Trainer surfaces a "BUYOUT" badge.
5. **Self-play break-even Nash check (Sprint 7 P3, lower priority).** Once chain hits ~75-80% shape-agreement, run the rule strategy as both players in 100K hands; mean EV ≈ 0 measures Nash distance.

DEFERRED: per-tier EV decomposition (engine `matchup_breakdown` exposure — for trainer coaching, not rule mining), naive-distance metric (diagnostic only), category bucketing fix (affects <0.5% of hands).


---

### Session 13 — 2026-04-26 — Sprint 7 Phase B: high_only refinement, REFINED extension, unanimous diagnostic, buyout signature

**Scope:** Sprint 7 Phase B priorities 1-4. Built a high_only-focused miner; iterated three weight schemes for the search-based no-pair fallback (final: mid-first weighting); attempted top-search refinement for pair/two_pair/quads (no-op gain after analysis); deep-dive unanimous-miss investigation surfaced two_pair lower-pair-mid pattern; shipped a tightened buyout signature as `tw_analysis.buyout` module.

**What landed:**

1. **High_only deep mining (`mine_high_only.py`)** — 8 sections over 1.23M no-pair hands. Headlines:
   - top == hand top_rank: 83.05% (already in NAIVE_104).
   - mid is suited 58.4%, connected 85.13%; mid = (second, third) only 20.37% (NAIVE_104's mid-pick is wrong 80% of the time).
   - bot DS rate when feasible (suit_2nd ≥ 2): 55.44%.
   - 79% of NAIVE_104 misses are MID-tier wrong, only 21% are TOP-tier wrong.

2. **Search-based hi_only_search** (`encode_rules.py`) — 4 weight-scheme iterations:
   - V1 (composite, DS+8): 29.96% on high_only.
   - V2 (DS-required pool + low-mid tiebreak): 27.71% on high_only.
   - V3 (bot-first, DS+4 conn+4): 27.54% on high_only.
   - V4 (mid-first, suited+conn+6, DS+5): **31.01% on high_only.** Winner.
   - Overall: 53.58% → **55.93%** (+2.35pp).

3. **Inter-profile ceiling diagnostic (`diag_high_only_ceiling.py`)** — Critical reality check:
   - Only **8.62% of high_only hands are unanimous** (vs 26.7% overall).
   - Inter-profile shape-agreement on high_only: mfsa↔omaha 22.98%, mfsa↔topdef 66.55%, omaha↔topdef 21.80%, omaha↔weighted 15.48%. Mean ~36%.
   - **A single deterministic rule cannot exceed ~50% on high_only** because the right answer is opponent-dependent.
   - This insight reframes the 70% target as opponent-modelling work, not rule-mining work.

4. **REFINED_v2 with top-search** — extended to pair/two_pair/quads via `_best_top_for_locked_mid`. Composite: top=highest-singleton +5, bot DS +3, bot conn≥4 +1. **0pp gain over hi_only_search.** Why: highest singleton is correct in 77%+ of locked-mid hands, and the +5 preference dominates the +3 DS bonus. Forcing a different top would regress. Conclusion: the existing default IS the refined rule for top selection.

5. **Unanimous-miss investigation (`diag_unanimous_misses.py`)** — bucketed 273K unanimous misses, inspected 30 examples, then probed further:
   - **Major discovery: two_pair often picks LOWER pair → mid.** AAKK = 60.9% lower→mid; KKQQ = 33.3% lower→mid; even mid-rank adjacent pairs (8,7), (7,6) hit ~45% lower→mid.
   - For low two_pair (high ≤ 5): mid is "no pair at all" 30-50% of the time (both pairs to bot, mid = singleton-pair).
   - DECISION: documented but did not encode — each refinement adds <1pp and adds conditional complexity. Listed as Phase B+ candidate work.

6. **Buyout signature module (`tw_analysis.buyout`)** — tightened from initial broad rule (4% precision, 98% recall) to high-precision narrow rule:
   - **Quads of rank ≤ 5** → BUYOUT
   - **Trips ≤ 4 + pair ≤ 3** → BUYOUT
   - Validated on full 6M hands: precision 26.30%, recall 46.56%, F1 33.6% vs ground truth (ev_mean < -4).
   - Catches 99.4% of low-quads buyout cases. Misses pure-trips category (too noisy as single-feature rule; trainer should use ev_mean lookup for those).
   - Exported via `tw_analysis` package; trainer integration deferred.

**Verified end-to-end this session:**
- `cargo build --release` clean (no Rust changes).
- `cargo test --release`: all tests pass (omaha 15, scoring 6, hand_eval, integration).
- Python tests: `test_features.py` 24/24 still green after package additions.
- `encode_rules.py` full 6M run completes in ~5 minutes; 4 strategies scored.
- `buyout_signature.py` full 6M validation runs cleanly.
- All new diagnostic scripts produce expected output.

**Gotchas this session:**
- **First 200K canonical hands have NO high_only hands** (canonical sort puts them later — high_only requires 7 distinct ranks which is rare in low-byte canonical prefix). Smoke tests on `--limit 200000` were misleading; had to run full 6M to see high_only category at all.
- **Search-based refinement weights are surprisingly opinion-dependent.** First DS-heavy weights (DS+8) over-DSd the bot (77% vs robust 49%). Mid-first weights (DS+5, mid-suited+6) gave the +1.5pp gain over original. The "best" weights only work because they trade off the +9pp gain on DS-feasible hands against the -2pp loss on connectivity-preferred hands.
- **Top-search for pair/two_pair was a wash.** Initial expectation: would optimize bot DS by picking different top. Reality: top=highest-singleton is so dominant (77%+) that any deviation regresses the dominant case more than it helps the edge case.
- **Buyout precision-vs-recall tradeoff is steep.** Loose rule (quads ≤ 7, trips ≤ 5) hit 98% recall but 4% precision — too noisy. Tight rule hit 26% precision but only 47% recall. The middle ground doesn't exist as a clean cutoff — the EV distribution within each rank is wide.

**Carry-forward for Session 14 (Sprint 7 Phase B+):**
1. Wire buyout signature into trainer (`trainer/app.py`) with both signature-based BUYOUT badge AND ev_mean-lookup softer "consider buyout vs [profile]" for borderline cases.
2. (Optional) Encode the two_pair lower-pair-mid pattern. Each adds <1pp; only worth pursuing if 70% target is hard-required.
3. **Self-play break-even Nash check (Sprint 7 P3).** Encode `strategy_hi_only_search` as both players in 100K self-play hands; mean EV ≈ 0 measures Nash distance.
4. Trainer `explain.py` update — swap from hand-written heuristics to rule-chain-grounded explanations.
5. (If reaching for ≥60%) Bot-rundown detection, low-pair-to-bot rule, per-profile MFSA-only weight rebalancing.

DEFERRED: per-tier EV decomposition, naive-distance metric, category bucketing fix.

**Session conclusion:** Rule chain at 55.93%. The 70% target is reframed as opponent-modelling work given the inter-profile-disagreement diagnostic. The current chain is suitable as a "robust core strategy" for the trainer; opponent-dependent refinements belong in a separate exploit layer.


---

### Session 14 — 2026-04-26 — Sprint 7 Phase B+: full priority list cleared (buyout in trainer, two_pair v3, self-play, rule-grounded explain, weight-rebalance null result)

**Scope:** Sprint 7 Phase B+ priorities 1-5, end-to-end. Buyout signature wired into the trainer with both signature + soft-EV signals. Two_pair lower-pair-mid pattern encoded as `strategy_v3` (v3 wins multiway-robust at 56.16%). Self-play regret check shipped via new script. `trainer/src/explain.py` fully rewritten to compare USER vs CHAIN vs SOLVER. v4 weight rebalance attempted, no gain — accepted as evidence the 60% multiway-robust ceiling has been reached.

**What landed:**

1. **Buyout in trainer (`trainer/src/buyout_eval.py`, `trainer/app.py`, JS+CSS):**
   - `evaluate_buyout(hand_strs, best_ev=...)` returns `{signature, signature_reason, soft_recommend, expected_loss, cost, ...}`. Signature uses the validated `tw_analysis.buyout.buyout_signature_scalar`; soft_recommend = `best_ev < -BUYOUT_COST` (4.0).
   - `/api/score` includes a `buyout` block per profile; `/api/compare` includes hand-level signature + per-row `buyout_soft` + a `soft_profiles` list.
   - UI: red BUYOUT banner above result panel for signature hits; amber "consider buyout vs <profile>" for soft hits; per-row "buyout" tag in compare table.
   - Manual smoke verified: quad-2 hand fires signature with reason "Quads of deuces…"; AAKK case shows EV +5.2 and clean result; trips-3+pair-2 fires signature + soft on MFSA & TopDef.

2. **Strategy v3 — two_pair refinements (`encode_rules.py::strategy_v3`):**
   - AAKK (high=14, low=13) → KK in mid (60.9% of robust per probe_two_pair).
   - Low two_pair (high ≤ 5) → both pairs to bot, mid = highest 2 singletons (modal robust 41-56%).
   - All other two_pair → unchanged (high pair → mid).
   - Adjacent high pairs (KKQQ etc.) deliberately NOT changed — high → mid still wins ~67-69%.
   - Result: two_pair 59.16% → **60.20%**, overall **55.93% → 56.16%** (+0.23pp).

3. **Self-play regret check (`analysis/scripts/selfplay_check.py`):**
   - Documented in script docstring that pure symmetric self-play is trivially zero EV by construction; the useful measurement is exploitability gap to the per-profile best-response.
   - Engine subprocess per (hand, profile) MC; samples=1000; runs 200 hands × 4 profiles in ~50s.
   - Result on 200 hands: v3 BEATS every profile (mean EV +0.13 to +1.63), gap to solver-optimal 0.14-0.40 EV/hand. Solidly competitive, not Nash. Match% with per-profile solver: 47.5-62.5%.

4. **Rule-chain-grounded explain.py (`trainer/src/explain.py`):**
   - Three-way comparison USER ↔ CHAIN (via `strategy_v3`) ↔ SOLVER (live MC best). Five branches cover all relationships.
   - Category-level rule-chain accuracy is baked into the constants table `CATEGORY_AGREEMENT_V3`; each finding cites this prior ("matches the solver on X% of <category> hands").
   - Per-tier diff finding identifies tier-by-tier composition mismatch in plain rank notation ("top 9 | mid K-K | bot 3-5-A-A").
   - Kept the bottom-suit detector from v1 as a supplementary observation; dropped split-pair / wrong-top / tier-swap (subsumed by rule-chain comparison).
   - Verified on AAKK hand via curl: trainer correctly says "You followed the rule chain — this hand is one of its misses" with solver's preferred shape spelled out.

5. **Weight rebalance v4 — null result (`encode_rules.py::strategy_v4`):**
   - `_score_top_choice_v4`: bot DS 3 → 4, bot conn 1 → 2.
   - `_hi_only_pick_v4`: bot conn 2 → 3 (rundown bonus).
   - Result: **v4 = 56.12% (-0.04pp vs v3).** High_only 31.01% → 30.84%; pair, two_pair, trips unchanged.
   - Conclusion: at the structural ceiling for opponent-agnostic rule weights. Kept v4 in code so future sessions don't re-do the experiment.
   - Per-profile breakdown for v3: vs MFSuitAware 55.7%, vs OmahaFirst 45.9%, vs TopDefensive 46.3%, **vs RandomWeighted 62.0%** (already over 60% on the easiest opponent).

**Verified end-to-end this session:**
- `cargo build --release` clean.
- `cargo test --release`: 124 tests pass (88 unit + 15 omaha + 15 hand_eval + 6 scoring).
- Python tests: `test_features.py` 24/24, `test_canonical.py` 9/9, `test_settings.py` 11/11.
- `encode_rules.py` full 6M run completes in ~5 min; 7 strategies scored + per-profile breakdown.
- `selfplay_check.py --hands 200 --samples 1000` runs cleanly in ~50s.
- Trainer manual smoke covers quad-2 (signature), AA broadway (clean), trips-3+pair-2 (signature + soft), AAKK (rule-chain miss explanation).

**Gotchas this session:**
- **`tail -50` masks long-running output until exit.** First v3 run via `python3 ... | tail -50` had empty stdout file for 5 minutes — looked stuck but was just stdout buffering through tail. Switching to `python3 -u` or `TaskOutput` blocking on the underlying script fixed visibility.
- **Symmetric self-play is mathematically trivially zero.** Initial framing of "Nash break-even" implied a meaningful empirical test, but if both players use the same deterministic strategy on a uniform hand distribution, mean net EV is identically zero by symmetry. The actually informative measurement is exploitability (gap to per-profile best-response). selfplay_check.py docstring documents this.
- **Weight tweaks don't compound.** v4 bumped both DS and rundown weights independently expecting additive gain; got -0.04pp. The structural ceiling is real — DS-feasible hands and rundown-feasible hands overlap, and the weights interact non-linearly with top_pref.
- **Per-profile RandomWeighted is the easiest target.** v3 hits 62.0% against it without any RandomWeighted-specific tuning, because it's the closest profile to "no opponent model" — i.e., closest to the assumption the rule chain implicitly makes.

**Carry-forward for Session 15 (Sprint 7 Phase C? or Sprint 5b trainer work):**
1. **Per-profile rule overlays.** Build profile-specific rule chains for OmahaFirst (45.9%) and TopDefensive (46.3%). Surface in the trainer when the user picks that profile. Plausibly reaches 70%+ per-profile.
2. **Trainer accuracy tracking** (Sprint 5b). Persist user submissions, track accuracy by category, build "drill weak categories" mode.
3. **Decision-tree extraction for publication.** strategy_v3 in Python is the "code"; need a Markdown export for the human-readable strategy guide.
4. **Tighter buyout signature.** Precision 26% → can go higher with more feature buckets. Probe required.
5. **Rule chain golden tests.** Lock in v3 behavior with unit tests so refactors don't regress.

DEFERRED: per-tier EV decomposition, naive-distance metric, category bucketing fix.

**Session conclusion:** Sprint 7 Phase B+ complete. Production rule chain = `strategy_v3`. Trainer is feature-complete with rule-chain explanations + buyout signals. The 60% multiway-robust target is at the structural ceiling for opponent-agnostic rules; further gains require per-profile work or accepting the current chain as the publishable "robust core strategy."


---

### Session 15 — 2026-04-27 — Sprint 7 Phase C/C+: per-profile overlays + golden tests; Phase D methodology agreed (sklearn DT extraction)

**Scope:** Three commits across the session. (1) v3 golden tests (regression gate). (2) per-profile overlays for OmahaFirst & TopDefensive. (3) residual-mining rules tightened the overlays. Late-session pivot to the project's stated end goal — the 5-10 rule chain matching the multiway-robust solver ≥95% — landed on a sklearn decision-tree extraction methodology agreed via Socratic dialog with Gemini 2.5 Pro. Phase D execution blocked by transient macOS `tccd` permission glitch after a SIGKILL'd Python child poisoned the kernel TCC cache.

**What landed:**

1. **strategy_v3 golden tests** (`d5ed9ff`) — `analysis/scripts/test_strategy_v3_golden.py`:
   - 13 tests: per-branch goldens (9 dispatch branches), setting-104 layout sanity, 105-setting round-trip, v3≠v4 lockstep on a known divergent hand, 100-hand seed=42 SHA fixture.
   - Negative-test verified: replacing strategy_v3 with strategy_v4 fires the lockstep + SHA-fixture tests, both designed for that exact drift.

2. **Per-profile overlays — Phase C** (`a5df1d8`) — `analysis/scripts/encode_rules.py`:
   - `strategy_omaha_overlay` (5 rules): single-pair → BOT when pair_rank ∈ {A, K, 2}; two-pair high → BOT when high_rank ≥ 13 or both pairs in 10-12 (generalises AAKK exception); high_only weight rebalance (DS +5→+8, rundown ≥4 +2→+4); quads/trips/three_pair/low-two-pair via v3 default. **45.82% → 54.69% on br_omaha** (300K sample).
   - `strategy_topdef_overlay` (1 rule mod): `_topdef_top_pick` — top = highest singleton iff ≥ Q (12), else LOWEST singleton (sacrifice the top tier when no Q+ singleton). Applied ONLY to single-pair and high_only branches; quads/trips/two_pair/three_pair use v3 (initial-version applied broadly caused -10pp regressions). Threshold tuned: ≥ 13 caused -13.2pp regression on Q-singleton bucket; ≥ 12 captures Q. **46.12% → 50.14% on br_topdef** (300K sample).
   - `PROFILE_TO_STRATEGY` mapping + `strategy_for_profile(hand, profile)` dispatcher (option-c-routes-to-option-a per Gemini's earlier Socratic guidance).
   - Golden tests in `analysis/scripts/test_overlays_golden.py` (7 initially, 8 post-Phase-C+).
   - Trainer integration: `trainer/app.py` passes `profile_id` to `build_feedback`; `trainer/src/explain.py` rewritten with `CHAIN_AGREEMENT_BY_PROFILE` per-profile per-category table; `_chain_arrangement(hand, profile_id)` routes through dispatcher; explanation findings cite the right "matches solver on X% of <category> hands" prior for the active profile.

3. **Per-profile overlays — Phase C+ residual rules** (`5a815ce`):
   - **OmahaFirst three_pair premium-flip**: when high_pair ≥ 13, high → BOT, mid_pair → MID. three_pair 29.96% → 54.14% (+24.18pp on category, +0.47pp overall). Generalises premium-flip principle from two_pair to three_pair. Mining: prem-high three-pair shows B/M/B at 73% modal vs 4% v3-default M/B/B.
   - **TopDef premium-trips break-down**: when trip_rank ≥ 13, top = ONE trip card, mid = TWO trip cards. Applied to pure trips and trips_pair branches. Mining: 86% modal on premium trips. Lifts: trips 49.51% → 59.49% (+9.98pp); trips_pair 40.41% → 51.59% (+11.18pp).
   - **TopDef AAKK reverse**: removed v3's KK→MID exception in topdef overlay; AAKK falls through to default high→MID (TopDef's modal at 48% vs v3's bot/mid 30%).

4. **User-driven mid-session reframe**: Around the time we'd hit "55% on omaha, 51% on topdef," the user challenged that I was chasing the wrong metric. Per-profile agreement is a tactical detour useful for the trainer; the project's STATED end product (CLAUDE.md) is a 5-10 rule chain matching the multiway-robust solver ≥95% on all 6M canonical hands. v3 is at 56.16% — 39pp short, not 5pp. The 95% target is the headline; per-profile overlays are auxiliary.

5. **Phase D methodology — Socratic consult with Gemini 2.5 Pro** (continuation `97707ec2-1603-44d2-a534-236caa6e92a2`, NO commit yet):
   - Methodology decided: sklearn `DecisionTreeClassifier` on (hand_features, multiway_robust setting_index), scored by SHAPE-equivalence (collapses 105 setting_indexes to fewer strategic equivalents). Target = setting_index NOT shape-tuple (shape-tuple has 254K unique classes — the model would explode).
   - 4-phase pipeline: (a) ceiling curve — train at depths {3, 5, 7, 10, 15, 20, None} on 1M subsample with 3-fold CV; full-6M fit at chosen depth; (b) extract via sklearn `export_text` → translate to Python if/elif → verify byte-identical predictions on full 6M; (c) EV-loss backtest on 5-10K-hand sample × 4 profiles × 1000 MC samples (engine MC); (d) ship as `strategy_v5_dt` with golden tests + Markdown export of the tree.
   - Features: 21 hand-features + 6 boolean feasibility flags (`can_make_ds_bot`, `can_make_4run`, `has_high_pair`, `has_low_pair`, `has_premium_pair`, `has_ace_singleton`, `has_king_singleton`).
   - Validation: 3-fold CV for depth selection (full 6M is the population — CV is for robust depth choice, not generalization). Full-data train of chosen depth for final model + report. Manual inspection of misses for refinements.

6. **Phase D execution — BLOCKED**:
   - `analysis/scripts/dt_phase1.py` written and saved.
   - First run via my Bash tool started CV training, ran for ~1 minute, was SIGKILL'd by user interrupt (Exit code 137).
   - Post-SIGKILL: macOS `tccd` cached denied-path entries for `~/Documents/claudecode/taiwanese/`. EVERY subsequent file access from python3 (and intermittently from `ls`/`cat`) returned `PermissionError: [Errno 1] Operation not permitted` — BOTH from my Bash sandbox AND the user's own Terminal.
   - Diagnosed as transient kernel TCC cache poisoning (a known macOS bug after SIGKILL'd children).
   - Resolution: user toggled python3.13 + Terminal in System Settings → Privacy & Security → App Management. Quit Terminal completely (Cmd+Q) → reopen restored access. Permissions are now valid for next session.

**Verified end-to-end this session:**
- `cargo build --release` clean (no Rust changes).
- All Python tests green: 24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden = **74 tests**.
- Manual end-to-end smoke of profile-aware `build_feedback` confirmed correct routing across 5 profile_ids; on AAQQ test case, omaha overlay agrees with solver where v3 doesn't, and explanation correctly says "the rule chain matches the solver — you played differently."

**Gotchas this session:**
- **Initial unanimous-miss mining was MISREAD.** Bucketed only the ~30% of unanimous two_pair where v3 misses; the modal-flip pattern (high→BOT) applied only to that subset, not to all two_pair. I prototyped the flip rule and measured -27pp on two_pair before catching the analytical error. Lesson: when bucketing misses, also check the FULL distribution per cell to avoid generalising from the conditional distribution.
- **Threshold tuning matters.** TopDef top-sacrifice rule at threshold ≥ 13 caused -13.2pp on the Q-singleton bucket; ≥ 12 was right. The empirical mining that suggested "Q stays on top 28.9% of the time" was misleading without the alternative-distribution drill.
- **macOS TCC SIGKILL bug**: never SIGKILL a python3 child mid-execution if it's reading a TCC-protected directory. The kernel cache pessimistically denies subsequent access until permissions are re-toggled and Terminal is restarted. Workaround discovered: System Settings → App Management → toggle python3.13 + Terminal off, then on; Cmd+Q Terminal; relaunch.

**Carry-forward for Session 16 (Phase D execution proper):**
1. **Run `analysis/scripts/dt_phase1.py`** from project root in fresh Terminal session. Output is a 7-row depth-vs-agreement table. The unbounded (None) depth is the structural ceiling for our feature set — determines whether 95% is reachable.
2. **Pick depth** at the agreement-curve knee.
3. **Extract** the chosen tree via sklearn `export_text`; translate to Python if/elif chain; verify byte-identical predictions across all 6M hands.
4. **EV-loss backtest**: 5-10K hands × 4 profiles × 1000 MC samples via engine. Compute mean EV-loss per profile; compare v3, overlays, learned tree.
5. **Ship** as `strategy_v5_dt`. Add golden tests. Generate Markdown export of the tree as the publishable strategy artifact. Update `CHAIN_AGREEMENT_BY_PROFILE` in explain.py.

**Session conclusion:** Per-profile overlays delivered (Phase C/C+) for the trainer side. The strategic pivot — recognised mid-session — is that the published guide is the multiway-robust 95% target, and decision-tree extraction is the right methodology. Pipeline is designed and saved; one TCC-permission restart away from execution.

---

# Session 16 (2026-04-27) — Phase D ceiling-curve + EV-loss reframe

**Headline:** The 95% shape-agreement target is RETIRED. Replaced with a directional EV-loss reduction goal grounded in absolute profitability per opponent profile. v3 was empirically shown to LOSE money against strong opponents (-0.78 EV/hand vs MFSuitAware, -0.89 vs TopDef) despite being competitive on shape-agreement. Surgical patches (fall-through hypothesis, +5 Ace-on-top bias removal) were tested and refuted with empirical data.

## What was completed

1. **Phase D ceiling-curve** (`analysis/scripts/dt_phase1.py` executed):
   - Full 6M depth=None ceiling: **61.74% full / 57.24% CV shape**. Far below Gemini's earlier 83.2% napkin estimate.
   - Generalization peaks at depth 15 (cv_shape 59.57%), overfits beyond.
   - **The 27-feature set is structurally insufficient for the 95% target** — depth alone cannot break the ceiling.
   - v3 (56.16%) is competitive with depth-10 unified DT (56.29%), confirming hand-built per-category dispatch outperforms greedy Gini at low rule budgets.

2. **3-of-4 majority subset diagnostic** (`analysis/scripts/dt_phase1_3of4.py`):
   - Filtered to 2,432,648 hands where mode_count == 3 (clear-majority answer key, non-trivial).
   - Ceiling: **70.01% full / 65.86% CV** at depth=None. Even on unambiguous-but-non-trivial hands, features cap at ~70%.
   - Confirms feature set is the bottleneck, not target ambiguity (since this subset has unambiguous answers).

3. **v3 EV-loss baseline harness** (`analysis/scripts/v3_evloss_baseline.py`):
   - Reuses `trainer/src/engine.py` subprocess pattern (Decision 029).
   - 2000 random hands × 4 profiles × 1000 MC samples per setting; ~9-min wall.
   - Optional `--save data/<name>_records.parquet` persists per-hand records for downstream analysis.
   - `--strategy v3 | v3_no_top_bias` flag for variant comparisons.
   - Records saved: `data/v3_evloss_records.parquet` (v3 ground truth, seed=42), `data/v3_no_top_bias_records.parquet` (refuted patch).

4. **Per-profile EV-loss results (v3, N=2000)**:
   - mfsuitaware mean 1.37, omaha 1.15, topdef 1.44, weighted 1.22. Total max-loss across hands: 3,266 EV. Mean 1.63 per hand. 33.3% of hands are "blunders" (max-loss > 2.0).

5. **Absolute EV per profile (the actually important reframe — user's contribution)**:
   - **MFSuitAware: v3 mean EV = -0.78** → loses **$7,779/1000 hands** at $10/EV-pt
   - **TopDef: v3 mean EV = -0.89** → loses **$8,846/1000 hands**
   - Omaha: v3 mean +1.01 → wins +$10,117/1000 hands
   - Weighted: v3 mean +0.38 → wins +$3,779/1000 hands
   - **v3 is profitable vs weak opponents but LOSES money vs strong ones.** 72% of hands v3 loses money on against MFSuitAware. BR (optimal) is profitable vs all 4 profiles (+0.55 to +2.16 mean EV).

6. **Blunder analysis** (`analysis/scripts/v3_blunder_analysis.py`, Gemini's 3-test methodology):
   - Test 1 (isolate): 666 blunders / 2000, mean blunder loss 3.09 EV.
   - Test 2 (fall-through hypothesis): **OR=1.09, refuted.** v3 picks setting 102/104 at the same rate in blunders as non-blunders (36.9% vs 34.9%). My pre-inspection from the worst-15 list was confirmation bias.
   - Test 3 (multi-pair-with-Ace pattern): OR=2.54 for two_pair/three_pair + Ace singleton (real but narrow), OR=1.90 for trips_pair + Ace.
   - **Bonus EV-loss share**: Multi-pair-with-Ace cluster I focused on accounts for only 9.5% of total loss. **Ace-singleton across ALL categories accounts for 45.5%** — every Ace-cohort has 30-86% higher mean loss than its non-Ace counterpart. But structurally diffuse.

7. **+5 Ace-on-top bias patch test** (`strategy_v3_no_top_bias`):
   - Hypothesis: removing the `+5` highest-singleton bonus in `_score_top_choice_for_locked_mid` would close the Ace-singleton EV-loss.
   - Result: **net total loss INCREASED by +93 EV (3% worse)**. Only `pair + ace` cohort improved (-0.065 EV/hand). All other cohorts regressed (e.g., `pair (no ace)` got 0.119 EV/hand worse).
   - Interpretation: the +5 bonus is *load-bearing for non-Ace pair hands*. The Ace-singleton EV-loss problem is structurally diffuse — distributed across dispatch architecture, pair-breaking penalty, top-scoring logic. **Surgical patch path is dead.**

8. **Project goal officially RETIRED + reframed**:
   - Old: "5-10 rule chain ≥95% shape-agreement on multiway-robust target"
   - New: "Rule chain achieves directional reduction below v3's 1.63 EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles." Memorable measurement: *"$10/EV-point over 1000 hands — does the rule chain profit?"*
   - User accepted reframe AND opened the rule-count cap: more than 10 named heuristics is OK if EV gain is significant.

9. **Methodology doctrine locked in (4-step process for any future hypothesis)**:
   - Step 1: Hypothesize from qualitative observation
   - Step 2: Measure signal on representative sample (odds ratio, NOT visual inspection of worst-list)
   - Step 3: Measure impact (EV-loss share — does the pattern matter in aggregate?)
   - Step 4: Test cheaply (in silico/analytical proxy) BEFORE running new MC
   - Then act
   - Lesson: I burned 9 min of MC compute on the +5 patch hypothesis. An in silico test (Gemini's exact prescription) would have killed it in 30 seconds. **Don't repeat.**

## Files added this session

- `analysis/scripts/dt_phase1_3of4.py` — 3-of-4 majority subset diagnostic
- `analysis/scripts/v3_evloss_baseline.py` — EV-loss harness, supports `--strategy` flag and `--save` parquet
- `analysis/scripts/v3_blunder_analysis.py` — Gemini's 3 hypothesis tests + bonus EV-loss share computation
- `data/v3_evloss_records.parquet` — v3 baseline records (seed=42, N=2000)
- `data/v3_no_top_bias_records.parquet` — patch experiment records (seed=42, N=2000)

## Files modified this session

- `analysis/scripts/encode_rules.py` — added `_score_top_choice_no_top_bias`, `_best_top_for_locked_mid_no_bias`, `strategy_v3_no_top_bias` (refuted experimental variant; left in tree as a cautionary tale, not for production use)
- `CURRENT_PHASE.md` — rewritten

## Verified

- Rust: 124/124 tests pass. `cargo build --release` clean.
- Python: 74/74 tests pass.

## Gotchas + lessons

- **Confirmation bias from worst-list inspection cost 9 min of compute.** The visible pattern in worst-15 hands (all setting 104) didn't generalize to the full blunder population (OR 1.09). **Always use odds ratio over a representative sample, never eyeball the tail.**
- **Single-component heuristic patches don't work.** v3's `_score_top_choice_for_locked_mid` has interacting components: pair-break penalty (-10), highest-singleton bonus (+5), rank/100 tiebreaker, bot DS bonus (+3), bot connectivity bonus (+1). Removing one creates regressions elsewhere. The architecture is at its hand-engineered ceiling.
- **EV-loss alone hides whether a strategy profits.** Always report absolute EV per profile alongside EV-loss vs BR. The user's $10/point framing surfaced that v3 is actively losing money vs strong opponents — a fact the EV-loss-only view obscured.
- **Gemini correction**: Earlier I told Gemini "mode_count ≥ 3 = 90.4%" — that figure from Decision 030 was wrong. Actual: 4-of-4 = 26.68%, 3-of-4 = 40.48%, total ≥3 = 67.16%. Genuinely-ambiguous tie-break pool is 12.19% (2-2 + 1-1-1-1), not 73% as my earlier framing implied.

## Carry-forward for Session 17 (data-driven feature mining proper)

The path: pure data-driven distillation, no more surgical patches.

1. **Category-specific miss-driven mining on single-pair hands** (47% of total EV-loss, the largest cohort). Filter `data/feature_table.parquet` to `mode_count == 3 AND category == 'pair'`. Train depth=None DT on that slice with current 27 features. Mine impure leaves to find the structural patterns features can't distinguish.
2. **Engineer 2-3 new interaction features** from those clusters (likely candidates from manual inspection of worst hands: suited-broadway-pair flag, conditional-top-on-bot-DS-feasibility, multi-pair-rank-distribution features — but DON'T anchor on speculation; let the leaves drive it).
3. **Re-run Phase D ceiling** on the augmented feature set. Specifically the 3-of-4 ceiling — target lift from 70% toward 80%+.
4. **Repeat per category** for high_only (12.6% of loss), two_pair (24% of loss), trips_pair (small but high density).
5. **Train final depth-10 to depth-15 DT** on full 6M with augmented features, extract via sklearn `export_text`, translate to Python if/elif chain, byte-identical parity check.
6. **Re-baseline EV-loss** with `v3_evloss_baseline.py --strategy v5_dt`. Compare to v3 on identical hands at identical seed. Headline: per-profile absolute EV + $/1000 hands at $10/EV-pt.

**Discovery mode, not commitment.** Use the 4-step doctrine (signal → impact → in silico → act) for every hypothesis before running new MC.

## Decisions added this session

- **Decision 033** — 95% shape-agreement target retired; absolute EV per profile is the new headline; rule-count cap is soft.

## Resume prompt (next session)

```
Resume Session 17 of the Taiwanese Poker Solver project.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 16)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 033)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 13-16; Session 16 is the most consequential)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/v3_evloss_baseline.py (canonical evaluation harness)
- analysis/scripts/v3_blunder_analysis.py (3-test methodology)
- data/v3_evloss_records.parquet (ground-truth baseline records, seed=42)

State of the project (end of Session 16):
- 95% shape-agreement target RETIRED.
- New headline: per-profile absolute EV (does v3 profit?) AND mean EV-loss reduction below v3 baseline 1.63.
- v3 LOSES money vs strong opponents (MFSA -0.78, TopDef -0.89), profits vs weak (Omaha +1.01, Weighted +0.38).
- 27-feature DT ceiling is 61.74% on full 6M, 70.01% on 3-of-4 majority. Features ARE the bottleneck.
- Two surgical-fix hypotheses tested and refuted (fall-through: OR=1.09; +5 Ace-bonus removal: net loss +93 EV).
- All 124 Rust + 74 Python tests green.

User priorities (re-confirmed Session 16):
- Discovery mode, not production commitment. Don't set ultra-tight goals.
- Data/ML/AI drives discovery — user's example heuristics are arbitrary illustrations, not constraints or features to encode literally.
- Rule-count cap is soft — more than 10 named heuristics OK if EV gain is significant.
- Track results as $/1000 hands at $10/EV-point — non-technical-friendly framing.

IMMEDIATE NEXT ACTION:
Begin category-specific miss-driven feature mining on single-pair hands (47% of v3 EV-loss).
Steps:
1. Filter feature_table.parquet to (mode_count == 3) AND (category == 'pair').
2. Train depth=None DT on that slice with current 27 features.
3. Inspect impure leaves — what hand structures cluster there?
4. Engineer 2-3 new interaction features from the patterns; don't speculate.
5. Re-run 3-of-4 ceiling with augmented features. Target lift toward 80%+.

Apply the 4-step methodology doctrine for any hypothesis: signal (OR) → impact (EV-loss share) → in silico → only then run new MC.
```

---

# Session 17 (2026-04-27 → 2026-04-28) — Single-pair augmented features: first feature-engineering win since the goal reframe

**Headline:** Three new single-pair-only features encode bot-suit-profile per strategic routing — information the original 27-feature set could not see. They lift the DT shape ceiling on the largest miss cohort (single-pair, 47% of EV-loss) by **+5.85pp** (74.23% → 80.08% on the (mode_count==3, category=='pair') slice). The lift propagates: full-6M ceiling 61.74% → 63.76% (+2.02pp), 3-of-4 majority subset 70.01% → 72.61% (+2.60pp). Depth-15 augmented tree (62.0% full / 60.7% cv) matches the baseline unbounded ceiling at 9× fewer leaves and with +3.5pp better cv-shape generalization.

## What was completed

### Step 1-3 — single-pair leaf mining (`analysis/scripts/mine_pair_leaves.py`)

- Filtered `data/feature_table.parquet` to (mode_count==3 AND category=='pair') → **1,078,223 hands** (17.94% of full 6M).
- Trained depth=None DT on the slice with the 27 baseline features. Slice ceiling: **74.23% / 26,238 leaves** (vs the 70.01% subset-wide 3-of-4 ceiling — single-pair is structurally easier than the average).
- Ranked terminal leaves by absolute shape-miss count. Top-50 leaves cover only **3.5% of slice misses**; **22,031 leaves have ≥1 miss**. Misses are highly diffuse — no single dominant pattern.
- Identified the recurring blind spot from the top-10 miss-leaves: the bot-suit profile under specific routings. The 27-feature set can see `suit_2nd ≥ 2` ("some DS-bot is achievable from 7 cards") but cannot see "the SPECIFIC 4 cards that end up in the bot under a given (top, mid) choice".
- Patterns observed: (A) v3-default bot has a 3-of-a-suit problem → BR moves a non-default singleton to top to repair the bot; (B) low pair + 2 high singletons + DS-feasible-on-pair-route → BR routes pair→bot, mid=top-2 singletons.

### Step 4 — three-feature design (`analysis/scripts/pair_aug_features.py`)

Three features, all vacuous (0) on non-pair hands by design:
1. `default_bot_is_ds` (bool) — under v3-default routing (mid=pair, top=highest singleton, bot=4 lowest non-pair), is the bot DS?
2. `n_top_choices_yielding_ds_bot` (0-5) — out of 5 non-pair singletons used as top (pair on mid), how many yield a DS bot?
3. `pair_to_bot_alt_is_ds` (bool) — under alternative routing (pair→bot, mid=top-2 singletons, top=3rd-highest singleton), is the bot DS?

Spot-checked on 4 hand-picked cases from the leaf dump before batch.

### Step 4a — odds-ratio signal check (`analysis/scripts/dt_pair_aug_ceiling.py`)

Per the Session 16 4-step doctrine: signal-check before training. Outcome variable: "BR (multiway_robust) uses v3-default routing".

| Feature | OR | a (feat=1, BR=def) | b (feat=1, BR≠def) |
|---|---|---|---|
| `default_bot_is_ds` | 4.39 | 92,562 | 11,063 |
| `n_top_choices_yielding_ds_bot ≥ 1` | 0.90 | 321,330 | 161,668 |
| `n_top_choices_yielding_ds_bot ≥ 3` | 1.15 | 95,656 | 40,095 |
| `pair_to_bot_alt_is_ds` | 0.56 | 93,446 | 71,842 |

Signal direction matches mining observations.

### Step 5 — augmented-feature DT ceiling on multiple subsets (`analysis/scripts/dt_phase1_3of4_aug.py`)

depth=None DT comparison (baseline 27 features vs augmented 30 features):

| Subset | Baseline | Augmented | Lift |
|---|---|---|---|
| Single-pair 3-of-4 (target slice) | 74.23% | **80.08%** | **+5.85pp** |
| Single-pair full (2.80M) | 68.49% | 72.83% | +4.34pp |
| 3-of-4 majority (2.43M) | 70.01% | 72.61% | +2.60pp |
| Full 6M | 61.74% | 63.76% | +2.02pp |

Drop-out ablation on slice (depth=None):
- Drop `default_bot_is_ds`: −2.04pp
- Drop `n_top_choices_yielding_ds_bot`: −1.37pp
- Drop `pair_to_bot_alt_is_ds`: −2.85pp

All three features contribute. `pair_to_bot_alt_is_ds` is the largest contributor in drop-out, despite its weaker OR magnitude (0.56). **Signal magnitude ≠ contribution magnitude.**

### Step 6a — full-6M depth curve (`analysis/scripts/dt_phase1_aug.py`)

Identical methodology to Session 16's dt_phase1.py (3-fold CV on 1M subsample, full-6M fit at chosen depth) with the augmented 30-feature set.

| depth | leaves | cv_acc | cv_shape | full_acc | full_shape |
|---|---|---|---|---|---|
| 3 | 8 | 30.69% | 32.31% | 30.63% | 32.13% |
| 5 | 32 | 39.94% | 42.01% | 39.97% | 42.27% |
| 7 | 125 | 47.06% | 49.10% | 47.22% | 49.26% |
| 10 | 939 | 54.21% | 56.48% | 54.51% | 56.76% |
| **15** | **18,330** | **58.30%** | **60.71%** | **59.60%** | **61.96%** |
| 20 | 118,723 | 56.75% | 59.17% | 61.27% | 63.39% |
| None | 208,740 | 55.44% | 57.99% | 61.69% | 63.76% |

CV peak shifts from depth=15 cv_shape 59.57% (baseline) to depth=15 cv_shape 60.71% (augmented). **Depth-15 augmented (62.0% full / 60.7% cv) matches the baseline depth=None ceiling at 9× fewer leaves and +3.5pp better cv-shape generalization.** Depth-15 is the chain-extraction candidate.

### Augmented-feature persistence (`analysis/scripts/persist_aug_features.py`)

- `data/feature_table_aug.parquet` — 18.87 MB, joins `feature_table.parquet` on `canonical_id`.
- Distributions: `default_bot_is_ds` 1: 432,432 / 0: 5,576,727; `n_top_choices_yielding_ds_bot` 0/1/3: 4,670,679 / 926,640 / 411,840; `pair_to_bot_alt_is_ds` 1: 370,656.
- Future sessions read this directly instead of recomputing the 51s Python-loop augment over 6M.

## Files added this session

- `analysis/scripts/mine_pair_leaves.py` — Step 1-3 mining + leaf-rank dump
- `analysis/scripts/pair_aug_features.py` — feature module (scalar + batch)
- `analysis/scripts/dt_pair_aug_ceiling.py` — Step 4 + ablation
- `analysis/scripts/dt_phase1_3of4_aug.py` — Step 5 cross-subset comparison
- `analysis/scripts/dt_phase1_aug.py` — Step 6a depth curve on full 6M
- `analysis/scripts/persist_aug_features.py` — parquet persistence
- `data/feature_table_aug.parquet` — 18.87 MB augmented features (single-pair only)

## Files modified this session

- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 034
- `handoff/MASTER_HANDOFF_01.md` — appended this Session 17 entry

## Verified

- Rust: `cargo build --release` clean. `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **First feature mental-model was wrong.** Initial `default_bot_is_ds` candidate was the only feature, and it computed only the v3-default routing's DS status. But in the leaf dump, BR was using top=lowest (k=4 in the 5-singleton enumeration), not top=highest, for many hands. I caught this by manually checking 4 hand-picked cases from the leaf dump against expected feature values. Fixed by adding `n_top_choices_yielding_ds_bot` (0-5) — count, not "which" — so the DT can split on "≥1 routing yields DS" and learn the alternative-top patterns. **Lesson: spot-check ≥4 hand-picked cases against the source observation BEFORE batch.**
- **Per-feature drop-out is essential.** `pair_to_bot_alt_is_ds` looked weakest by OR magnitude (0.56 inverse), but contributed +2.85pp in drop-out — the largest of the three. **Signal magnitude is not contribution magnitude.** Always run drop-out ablation when claiming multiple features add up.
- **Augment compute is Python-loop bound.** 51s on 6M is the cost of per-hand bot-position enumeration. Acceptable as a once-per-session cost, but persist to parquet for downstream chain-extraction work.
- **Depth-15 generalization improves.** With augmented features, the bounded-depth-15 tree achieves 62.0% / 60.7% (full / cv), beating the baseline depth=None ceiling on full data while halving the cv-shape gap. This is the right depth for chain extraction.
- **The 3.5% top-50-leaf coverage of misses is itself diagnostic.** Misses are diffuse — no single dominant cluster. The augmented features don't fix any one cluster, they lift the *floor* across many clusters at once. Future feature ideas should be evaluated by aggregate lift (drop-out delta), not by visible inspection of any single leaf.

## Carry-forward for Session 18

The path forks. Choose:

(a) **RECOMMENDED — Continue mining other categories.** high_only (12.6% of EV-loss), two_pair (24% of EV-loss), trips_pair (small but high-density). Each category likely has its own bot-suit/strategic-routing features waiting to be mined. Bring full-6M ceiling toward 70%+ before extracting a chain. The augmented features module pattern is established and reusable.

(b) **Alternative — Extract chain from current augmented depth-15 tree.** Refit depth=15 DT on full 6M with the 30 features. sklearn `export_text` → translate to Python if/elif chain → byte-identical parity check on full 6M. Then run `analysis/scripts/v3_evloss_baseline.py --strategy v5_dt --hands 2000 --save data/v5_dt_records.parquet` and compare to v3 on per-profile absolute EV + $/1000 hands at $10/EV-pt.

(a) is more discovery before commitment; (b) gives an EV-loss measurement (the actual KPI). The reframe (Decision 033) favours (a) until the feature ceiling stops moving.

## Decisions added this session

- **Decision 034** — Three single-pair augmented features added to the production feature set (default_bot_is_ds, n_top_choices_yielding_ds_bot, pair_to_bot_alt_is_ds). Lifts: +5.85pp on target slice, +2.02pp on full 6M.

## Resume prompt (next session)

```
Resume Session 18 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 17)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 034 — single-pair augmented features)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 13-17; Session 17 is the most consequential since the reframe)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/pair_aug_features.py (Session 17 features module)
- analysis/scripts/dt_phase1_aug.py (Session 17 depth curve, full 6M)
- data/feature_table.parquet, data/feature_table_aug.parquet (joined on canonical_id)

State of the project (end of Session 17):
- Single-pair augmented features delivered +5.85pp on the target slice (74.23% → 80.08%)
  and +2.02pp on full 6M (61.74% → 63.76%) at depth=None.
- Depth-15 augmented tree: 62.0% full / 60.7% cv shape — matches baseline depth=None
  ceiling at 9× fewer leaves and +3.5pp better cv-shape generalization.
- v3 production: 56.16% (unchanged). Augmented depth-15 is +5.8pp over v3.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(a) RECOMMENDED — Continue mining other categories.
    1. Filter feature_table.parquet to (mode_count == 3 AND category == 'high_only')
       — 12.6% of v3 EV-loss; the second-largest cohort.
    2. Train depth=None DT on slice with augmented 30 features. Report ceiling.
    3. Mine impure leaves; engineer 1-3 high_only-specific features.
    4. Re-run depth curve on full 6M with all features. Lift?
    5. Repeat for two_pair (24% of EV-loss) and trips_pair if budget allows.

(b) Alternative — Extract chain from current augmented depth-15 tree.
    1. Refit depth=15 DT on full 6M with the 30 features.
    2. Use sklearn `export_text` → translate to Python if/elif chain.
    3. Verify byte-identical predictions on full 6M.
    4. Run v3_evloss_baseline.py --strategy v5_dt and compare to v3 on
       per-profile absolute EV + $/1000 hands at $10/EV-pt.

(a) is more discovery before commitment; (b) ships a chain. The reframe
favours (a) until the feature ceiling stops moving — but (b) gives an
EV-loss measurement that's the actual KPI.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.
```

---

### Session 18 — 2026-04-28 — Sprint 7 Phase D: high_only mining + 3 augmented features (path (a) executed)

**Scope:** Session 17's recommended path (a) — mine the high_only category (12.6% of v3 EV-loss; second-largest cohort after single-pair) and add routing-aware features mirroring the Decision 034 pattern. **Result: full-6M ceiling 63.76% → 65.20% (+1.44pp); high_only 3-of-4 slice 39.64% → 48.92% (+9.28pp); depth-15 knee 62.0% → 62.86% / 60.71% → 61.59% cv-shape.**

#### Step 1-3 — high_only leaf mining (`analysis/scripts/mine_high_only_leaves.py`)

- Filtered feature_table to (mode_count==3 AND category=='high_only') → 463,547 hands (7.71% of full 6M).
- Trained depth=None DT on slice with the 27 baseline features. Slice ceiling: **39.64% / 4,544 leaves.** Much lower than the single-pair 74.23% — confirms Session 13's "high_only is opponent-dependent" finding.
- Miss concentration: top-10 leaves cover 4.4% of misses; top-50 = 15.5%; top-100 = 24.7%. Diffuse across 4,176 miss-leaves (vs single-pair's 22,031), but the dominant top-15 leaves are unambiguously about bot-suit-profile-per-routing.
- Recurring pattern: under NAIVE_104 the bot is 3-suited (3 of the 4 lowest cards share a suit). BR demotes a same-suit broadway pair from mid → bot to repair the bot to DS. Example leaf-1 hand `2c 3c 6c 7d Jh Qh Ks` → NAIVE bot `2c 3c 6c 7d` = 3 clubs (NOT DS); BR routes Q-J→bot, mid=7-6, bot=`Qh Jh 3c 2c` = 2h+2c → DS.

#### Step 4 — three-feature design (`high_only_aug_features.py`)

- Module exposes `compute_high_only_aug_for_hand(hand)` (scalar) + `compute_high_only_aug_batch(hands, slice_mask)` (vectorised). Vacuous on non-high_only hands (returns 0).
- Features:
  1. `default_bot_is_ds_high` — bool. NAIVE_104 bot is DS (2,2)?
  2. `n_mid_choices_yielding_ds_bot` — 0-15. Top fixed at byte[6]; count of C(6,2) mid choices yielding DS bot.
  3. `best_ds_bot_mid_max_rank` — 0 or 4-14. Top fixed at byte[6]; among DS-bot-yielding mid choices, the maximum rank that can appear in mid. Encodes the "rank-cost of routing-for-DS-bot".
- 5 spot-checks pass against hand-picked cases from the leaf dump (per Session 17 lesson). f3=12 on the Leaf-5 hand correctly identifies that Q can stay in mid with a DS bot — the precise tradeoff the DT needs to encode.

#### Step 4a — odds-ratio signal check (`analysis/scripts/signal_or_high_only.py`)

| Feature | OR | Direction |
|---|---|---|
| `default_bot_is_ds_high` (vs BR=NAIVE) | 6.38x | + (P(=NAIVE | F1=1)=57.32% vs P(=NAIVE | F1=0)=17.40%) |
| `best_ds_bot_mid_max_rank` 4-8 vs 0 | — | 10.29% NAIVE (vs 36.09%) — clean U-shape |
| `best_ds_bot_mid_max_rank` 13-14 vs 4-8 | — | 42.36% NAIVE — broadway K/A in mid retains NAIVE |
| F1 × F2 cross-tab | — | F1=1 cells: 53-68% NAIVE; F1=0 cells: 12-36% NAIVE |

The U-shape on F3 is exactly the "tradeoff cost" signal: when F3 is high (broadway can stay in mid AND DS-bot), BR uses NAIVE; when F3 is low (DS-bot only with sacrifice), BR deviates; when F3 is 0 (no DS-bot achievable), BR settles for NAIVE. Strong, interpretable, non-redundant signal — signal magnitude high enough to justify training compute.

#### Step 5 — augmented-feature DT ceiling on multiple subsets (`analysis/scripts/dt_high_only_aug_ceiling.py`)

depth=None DT comparison across 4 feature sets × 4 subsets:

| Subset | Baseline (27) | + Pair-aug (30) | + High-aug (30) | All Aug (33) |
|---|---|---|---|---|
| HIGH_ONLY 3-of-4 (slice) | 39.64% | 39.64% (vacuous ✓) | **48.92%** | 48.92% |
| HIGH_ONLY full (1.23M) | 30.87% | 30.87% (vacuous ✓) | **37.89%** | 37.89% |
| 3-of-4 majority (2.43M) | 70.01% | 72.61% | 71.78% | **74.38%** |
| Full 6M (6.01M) | 61.74% | 63.76% | 63.17% | **65.20%** |

**Key result:** Full 6M ceiling lifts from 63.76% (Session 17 pair-aug-only) to **65.20% (+1.44pp)** with high_only-aug added. 3-of-4 majority ceiling lifts from 72.61% to **74.38% (+1.77pp)**. The high_only-aug features lift the high_only sub-population by +7-9pp, propagating to +1.4-1.8pp on the broader sets.

Drop-out ablation on slice (depth=None):
- Drop `default_bot_is_ds_high`: −3.15pp
- Drop `n_mid_choices_yielding_ds_bot`: −1.19pp
- Drop `best_ds_bot_mid_max_rank`: −4.78pp ← LARGEST (matches Decision 034's pattern: F3 had weaker individual OR than F1, but contributes most in drop-out)
- Drop any pair-aug feature: 0.00pp (vacuous on slice ✓)

All three high_only-aug features are non-redundant. Pair-aug features are correctly inert on this slice.

#### Step 6 — full-6M depth curve with all 33 features (`analysis/scripts/dt_phase1_aug2.py`)

Identical methodology to dt_phase1_aug.py (3-fold CV on 1M subsample, full-6M fit at chosen depth) with the union 33-feature set.

| depth | leaves | cv_acc | cv_shape | full_acc | full_shape |
|---|---|---|---|---|---|
| 3 | 8 | 30.69% | 32.31% | 30.63% | 32.13% |
| 5 | 32 | 39.94% | 42.01% | 39.97% | 42.27% |
| 7 | 125 | 46.99% | 48.98% | 47.16% | 49.15% |
| 10 | 939 | 54.42% | 56.51% | 54.72% | 56.74% |
| **15** | **18,354** | **59.17%** | **61.59%** | **60.44%** | **62.86%** |
| 20 | 122,596 | 57.75% | 60.11% | 62.56% | 64.68% |
| None | 229,271 | 56.10% | 58.60% | 63.12% | 65.20% |

**Depth-15 with 33 features (62.86% full / 61.59% cv) lifts the Session 17 depth-15 knee (62.0% / 60.7%) by +0.86pp / +0.92pp — and now sits +6.7pp over v3 production (56.16%).** Depth-15 remains the chain-extraction candidate (smallest cv-full gap; same leaf-count tier as Session 17). The lift is consistent across all bounded depths ≥10.

#### Augmented-feature persistence (`analysis/scripts/persist_high_only_aug.py`)

- `data/feature_table_high_only_aug.parquet` — 18.75 MB, joins `feature_table.parquet` on `canonical_id`.
- Distributions: `default_bot_is_ds_high` 1: 185,328 / 0: 5,823,831; `n_mid_choices_yielding_ds_bot` {0:5.06M, 1:309K, 3:515K, 6:77K, 9:51K} (discrete due to suit-profile symmetries); `best_ds_bot_mid_max_rank` ranges 0 (5.06M, no DS-bot) and 3-13 distributed across the rest.
- Compute is 43.2s on the 1.23M high_only sub-population. Future sessions read the parquet directly.

## Files added this session

- `analysis/scripts/mine_high_only_leaves.py` — Step 1-3 mining + leaf-rank dump
- `analysis/scripts/high_only_aug_features.py` — feature module (scalar + batch + 5 spot-check cases)
- `analysis/scripts/signal_or_high_only.py` — Step 4a OR + cross-tab signal test
- `analysis/scripts/dt_high_only_aug_ceiling.py` — Step 5 cross-subset comparison + drop-out ablation
- `analysis/scripts/dt_phase1_aug2.py` — Step 6 depth curve on full 6M with all 33 features
- `analysis/scripts/persist_high_only_aug.py` — parquet persistence
- `data/feature_table_high_only_aug.parquet` — 18.75 MB augmented features (high_only only)

## Files modified this session

- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 035
- `handoff/MASTER_HANDOFF_01.md` — appended this Session 18 entry

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **Slice ceiling of 39.64% on high_only is genuinely low — but the ceiling rises +9.28pp with the right features.** Session 13's "single deterministic rule cannot exceed ~50% on high_only because right answer is opponent-dependent" was empirical against rule-based strategies. A DT with routing-aware features pushes the slice ceiling to 48.92% — within 1pp of that empirical cap. The remaining gap is the intrinsic opponent-dependence; further features here will hit diminishing returns.
- **Diffuse miss concentration ≠ no signal.** high_only miss-leaves are spread across 4,176 with top-100 covering only 24.7% (vs single-pair's tighter top-50 cluster). But the dominant top-15 leaves all share the same structural pattern (bot-suit-under-default-routing). Diffuseness in the leaf graph does not contradict a clean structural signal — the features lift the floor across many small leaves uniformly.
- **F3 (best_ds_bot_mid_max_rank) is again the largest contributor — and again has the weakest stand-alone signal.** Repeating Decision 034's lesson: signal magnitude ≠ contribution magnitude. The single OR was modest (no clean +/- direction; U-shape across bins). But it captures the rank-cost-of-DS-bot tradeoff that the DT alone cannot derive. Always run drop-out ablation; never trust signal magnitude as a contribution proxy.
- **Pair-aug features are correctly vacuous on the high_only slice.** Drop-out delta = 0pp on all three pair-aug features when measured on the high_only slice. Confirms feature isolation by design (each augmented family fires only on its target category) and validates the additive composition: total full-6M lift +3.46pp ≈ pair-aug +2.02pp + high-aug +1.44pp.
- **Augment compute scales with slice size, not full N.** `compute_high_only_aug_batch` iterates `np.where(slice_mask)[0]` only — 43s for the 1.23M high_only rows. Future category-aug modules should follow the same pattern.

## Carry-forward for Session 19

The path forks again. Choose:

(a) **Continue mining other categories.** two_pair (24% of EV-loss; the largest remaining cohort after single-pair); trips_pair (small but high-density). Same template: leaf mining → routing-aware features → OR-test → spot-check → ablation → persist parquet → depth curve. Likely +0.5-1.5pp full-6M ceiling per category.

(b) **Extract chain from depth-15 aug-33 tree.** 18,354 leaves; 62.86% full / 61.59% cv; +6.7pp over v3. Refit → sklearn `export_text` → translate to Python if/elif → byte-identical parity check on full 6M. Then `v3_evloss_baseline.py --strategy v5_dt --hands 2000 --save` and compare to v3 on per-profile absolute EV + $/1000 hands at $10/EV-pt. **This is the chain-shipping path.**

The reframe (Decision 033) favours continued mining until the feature ceiling stops moving. Session 18 added +1.44pp at depth=None and +0.86pp at depth=15 — clear signal that more category-mining still has runway. Recommended: (a) for two_pair next; (b) once the augmented-feature lift plateaus.

## Decisions added this session

- **Decision 035** — Three high_only augmented features added to the production feature set (default_bot_is_ds_high, n_mid_choices_yielding_ds_bot, best_ds_bot_mid_max_rank). Lifts: +9.28pp on target slice, +1.44pp on full 6M, +1.77pp on 3-of-4 majority.

## Resume prompt (next session)

```
Resume Session 19 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 18)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 035 — high_only augmented features)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 16-18 since the goal reframe)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/pair_aug_features.py + high_only_aug_features.py (feature modules)
- analysis/scripts/dt_phase1_aug2.py (Session 18 depth curve, full 6M, 33 features)
- data/feature_table.parquet, data/feature_table_aug.parquet,
  data/feature_table_high_only_aug.parquet (joined on canonical_id)

State of the project (end of Session 18):
- Two augmented-feature families now live: pair-aug (Session 17) + high_only-aug (Session 18).
  Combined, they lift the full-6M depth=None ceiling from 61.74% (baseline) to 65.20% (+3.46pp)
  and the depth-15 knee from 61.96% to 62.86% / 61.59% cv-shape.
- v3 production: 56.16% (unchanged). Augmented depth-15 is +6.7pp over v3.
- High_only 3-of-4 slice ceiling lifted 39.64% → 48.92% (+9.28pp) — within ~1pp of the
  Session 13 empirical "opponent-dependent" cap.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(a) RECOMMENDED — Continue mining: two_pair next.
    1. Filter feature_table.parquet to (mode_count == 3 AND category == 'two_pair')
       — 24% of v3 EV-loss; the largest remaining cohort.
    2. Mine impure leaves with the existing 33 features (pair-aug fires partially
       — n_pairs==2 not 1, so feature semantics may need adapting; check first).
    3. Hypothesise 1-3 two_pair-specific features (likely: which-pair-on-bot,
       broadway-pair-vs-low-pair routing, pair-suit-coupling).
    4. OR-test → spot-check → batch + ablation → persist → depth curve.
    5. Optional: trips_pair after two_pair.

(b) Alternative — Extract chain from current augmented depth-15 tree (33 features).
    1. Refit depth=15 DT on full 6M with all 33 features.
    2. sklearn `export_text` → translate to Python if/elif chain.
    3. Verify byte-identical predictions on full 6M.
    4. Run v3_evloss_baseline.py --strategy v5_dt and compare to v3 on
       per-profile absolute EV + $/1000 hands at $10/EV-pt.

(a) is more discovery before commitment; (b) ships a chain.
The reframe favours (a) until the feature ceiling stops moving.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.
```

---

### Session 19 — 2026-04-28 — Sprint 7 Phase D: two_pair mining + 3 augmented features (path (a) executed)

**Scope:** Session 18's recommended path (a) — mine the two_pair category (24% of v3 EV-loss; the largest remaining cohort after single-pair, larger than high_only) and add routing-aware features mirroring the Decision 034/035 pattern. **Result: full-6M ceiling 65.20% → 66.87% (+1.67pp); two_pair 3-of-4 slice 79.47% → 85.37% (+5.90pp); two_pair full 68.29% → 75.79% (+7.50pp); depth-15 knee 62.86% → 63.74% / 61.59% → 62.44% cv-shape.**

#### Step 1-3 — two_pair leaf mining (`analysis/scripts/mine_two_pair_leaves.py`)

- Filtered feature_table to (mode_count==3 AND category=='two_pair') → 675,624 hands (11.24% of full 6M).
- Trained depth=None DT on slice with the 28 baseline features. Slice ceiling: **79.47% / 39,677 leaves.** Much higher than single-pair (74.23%) or high_only (39.64%) — two_pair has more clear-majority structure.
- Miss concentration: top-10 leaves cover 0.5% of misses; top-50 = 1.9%; top-100 = 3.4%. **Much more diffuse than prior categories** (vs single-pair 11%, high_only 4.4%). 30,413 of 39,677 leaves have at least one miss.
- Recurring pattern in dominant top miss-leaves: "high-pair-on-mid (DT-default, settings 14/44) vs high-pair-on-bot (BR-swap routing)". The within-leaf discriminator is suit-coupling under each routing — the 28 baseline features see only 7-card suit profiles, not per-routing bot suit profiles.
- Example Leaf-1 hand `2c 6c Jd Kh Ks Ac Ad`: DT picks mid=AA (high-pair-on-mid), bot=KK62; BR picks mid=KK (swap), bot=AA62. Two of the 6 intact-pair routings yield DS-bot — both via mid=KK swap.

#### Step 4 — three-feature design (`two_pair_aug_features.py`)

- Module exposes `compute_two_pair_aug_for_hand(hand)` (scalar) + `compute_two_pair_aug_batch(hands, slice_mask)` (vectorised). Vacuous on non-two_pair hands (early-return if n_pairs != 2 or singletons != 3).
- Features:
  1. `default_bot_is_ds_tp` — bool. Under (mid=high-pair, top=highest-singleton, bot=low-pair+2-lowest-singletons), is bot DS (2,2)?
  2. `n_routings_yielding_ds_bot_tp` — 0-6. Over the 6 intact-pair routings (2 mid-pair × 3 top-singleton choices), count those yielding DS bot.
  3. `swap_high_pair_to_bot_ds_compatible` — bool. Among DS-bot routings, does ANY have HIGH pair on bot (mid=low-pair)?
- 6 spot-checks pass against hand-picked cases from the leaf dump (Leaf-1, Leaf-2, Leaf-3 misses + 3 constructed cases including default-IS-DS, monosuit, swap-only-DS). Per Session 17/18 lesson: ≥4 spot-checks before batch.

#### Step 4a — odds-ratio + cross-tab signal check (`analysis/scripts/signal_or_two_pair.py`)

| Feature | OR / Spread | Direction |
|---|---|---|
| `default_bot_is_ds_tp` (vs BR=baseline-DT) | 1.14x | Very weak +; P=81.17% vs 79.13% |
| `swap_high_pair_to_bot_ds_compatible` | 0.65x | Inverse; P=74.17% vs 81.48% |
| `n_routings_yielding_ds_bot_tp` cross-tab | 17.81pp spread | Clean U: 83.51 / 70.23 / 74.50 / 88.04% across {0/1/2/4} |

Individual ORs much weaker than Sessions 17/18 (4.39x, 6.38x). However, the COMBINED literal-agreement lift on slice when adding all 3 features: 79.34% → 85.29% (+5.95pp). The U-shape on F2 + the binary-axis split on F1/F3 jointly map onto a multi-dimensional decision the DT can split on. Signal magnitude justified training compute despite weak individual ORs.

#### Step 5 — augmented-feature DT ceiling on multiple subsets (`analysis/scripts/dt_two_pair_aug_ceiling.py`)

depth=None DT comparison across 6 feature sets × 4 subsets:

| Subset | Baseline (27) | + Pair (30) | + High (30) | + 2P (30) | + Pair+High (33) | + ALL (36) |
|---|---|---|---|---|---|---|
| TWO_PAIR 3-of-4 (slice) | 79.47% | 79.47% (vacuous ✓) | 79.47% (vacuous ✓) | **85.37%** | 79.47% | 85.37% |
| TWO_PAIR full (1.34M) | 68.29% | 68.29% (vacuous ✓) | 68.29% (vacuous ✓) | **75.79%** | 68.29% | 75.79% |
| 3-of-4 majority (2.43M) | 70.01% | 72.61% | 71.78% | 71.65% | 74.38% | **76.02%** |
| Full 6M (6.01M) | 61.74% | 63.76% | 63.17% | 63.41% | 65.20% | **66.87%** |

**Key result:** Full 6M ceiling lifts from 65.20% (Session 18 pair+high) to **66.87% (+1.67pp)** with two_pair-aug added. 3-of-4 majority lifts from 74.38% to **76.02% (+1.64pp)**. The 2p-aug features lift the two_pair sub-population by +5.90-7.50pp, propagating to +1.6-1.7pp on the broader sets.

Drop-out ablation on slice (depth=None):
- Drop `default_bot_is_ds_tp`: −1.84pp
- Drop `n_routings_yielding_ds_bot_tp`: −1.67pp
- Drop `swap_high_pair_to_bot_ds_compatible`: −1.93pp ← LARGEST (matches Decisions 034/035 pattern: weakest individual OR but contributes most in drop-out — though here all three drops are within 0.26pp of each other, much more balanced than prior sessions).
- Drop any pair-aug feature: 0.00pp (vacuous on slice ✓)
- Drop any high-aug feature: 0.00pp (vacuous on slice ✓)

All three 2p-aug features are non-redundant. Pair-aug + high-aug features correctly inert on this slice. Three-family isolation-by-design property triple-validated.

**Three-family additive composition holds:** 61.74 (baseline) + 2.02 (pair) + 1.44 (high) + 1.67 (2p) = 66.87% — exactly the all-aug full-6M ceiling. Each family's vacuous-on-out-of-category property continues to behave as designed.

#### Step 6 — full-6M depth curve with all 37 features (`analysis/scripts/dt_phase1_aug3.py`)

Identical methodology to dt_phase1_aug2.py (3-fold CV on 1M subsample, full-6M fit at chosen depth) with the union 37-feature set.

| depth | leaves | cv_acc | cv_shape | full_acc | full_shape |
|---|---|---|---|---|---|
| 3 | 8 | 30.69% | 32.31% | 30.63% | 32.13% |
| 5 | 32 | 39.94% | 42.02% | 39.97% | 42.27% |
| 7 | 125 | 47.00% | 49.00% | 47.17% | 49.16% |
| 10 | 932 | 54.58% | 56.69% | 54.92% | 56.95% |
| **15** | **18,399** | **60.02%** | **62.44%** | **61.32%** | **63.74%** |
| 20 | 136,191 | 59.08% | 61.55% | 64.01% | 66.12% |
| None | 288,218 | 57.28% | 59.87% | 64.80% | 66.87% |

**Depth-15 with 37 features (63.74% full / 62.44% cv) lifts the Session 18 depth-15 knee (62.86% / 61.59%) by +0.88pp / +0.85pp — and now sits +7.58pp over v3 production (56.16%).** Depth-15 remains the chain-extraction candidate (smallest cv-full gap; same leaf-count tier as Sessions 17/18). The 2p-aug features primarily lift bounded depths ≥10 and depth=None; depths 3-7 unaffected.

#### Augmented-feature persistence (`analysis/scripts/persist_two_pair_aug.py`)

- `data/feature_table_two_pair_aug.parquet` — 18.89 MB, joins `feature_table.parquet` on `canonical_id`.
- Distributions: `default_bot_is_ds_tp` 1: 180,180 / 0: 5,828,979; `n_routings_yielding_ds_bot_tp` {0:5.39M, 1:232K, 2:347K, 4:39K}; `swap_high_pair_to_bot_ds_compatible` 1: 386K / 0: 5.62M.
- Compute is 26s on the 1.34M two_pair sub-population. Future sessions read the parquet directly.

## Files added this session

- `analysis/scripts/mine_two_pair_leaves.py` — Step 1-3 mining + leaf-rank dump
- `analysis/scripts/two_pair_aug_features.py` — feature module (scalar + batch + 6 spot-check cases)
- `analysis/scripts/signal_or_two_pair.py` — Step 4a OR + cross-tab signal test
- `analysis/scripts/dt_two_pair_aug_ceiling.py` — Step 5 cross-subset comparison + drop-out ablation
- `analysis/scripts/dt_phase1_aug3.py` — Step 6 depth curve on full 6M with all 37 features
- `analysis/scripts/persist_two_pair_aug.py` — parquet persistence
- `data/feature_table_two_pair_aug.parquet` — 18.89 MB augmented features (two_pair only; gitignored)

## Files modified this session

- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 036
- `handoff/MASTER_HANDOFF_01.md` — appended this Session 19 entry

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **Diffuse miss-leaves are NOT a contraindication.** two_pair top-10 miss-leaves cover only 0.5% of misses (vs single-pair 11%, high_only 4.4%). Initial worry was "no signal." But the +5.90pp slice lift confirms the structural pattern is real and spread uniformly across small leaves. Diffuseness in the leaf graph and feature lift are orthogonal — one decision axis can be tested across many small leaves and have aggregated impact.
- **Weak individual ORs don't preclude strong combined lift.** F1 OR=1.14x and F3 OR=0.65x are dramatically weaker than Sessions 17/18 (4.39x, 6.38x). But all three combined lifted the slice depth=None DT +5.90pp (shape) — comparable to single-pair's +5.85pp. Three features that each weakly discriminate one axis can collectively map onto a multi-dimensional decision the DT exploits. Lesson: do the cheap feature-add sanity check (ceiling lift) before deciding whether weak ORs justify continuing.
- **The three drop-outs are within 0.26pp of each other (1.67-1.93pp range).** Unlike Sessions 17/18 where one feature dominated (-2.85pp / -4.78pp), here all three 2p-aug features carry near-equal load. F3 (`swap_high_pair_to_bot_ds_compatible`) edges out by a hair. Each captures a different facet of the same routing decision; remove any one and the DT loses ~10% of the lift. This balanced contribution profile probably reflects the more symmetric two_pair structure (two pairs + 3 singletons vs single-pair's asymmetric 1 pair + 5 singletons).
- **The "27 baseline" label is actually 28 features.** Counting the list shows 28; X.shape outputs (e.g., `(675624, 28)`, `(6009159, 37)`) confirm. Sessions 17/18 docs all label it "27", an off-by-one inherited from earlier scoping. Session 19 docs continue the "27" labelling for cross-session compatibility. Zero impact on results — only column-count labels are mismatched.
- **Three-family additive composition holds within rounding** — 61.74 + 2.02 + 1.44 + 1.67 = 66.87%. Each family's vacuous-on-out-of-category property behaves exactly as designed across (single-pair, high_only, two_pair). Future families (trips_pair etc.) should land at similar vacuous boundaries.

## Carry-forward for Session 20

The path forks again. Choose:

(a) **One more mining pass — trips_pair.** Small but high-density cohort. All 3 aug-families likely vacuous on trips_pair (n_pairs==1 + n_trips==1 mismatches their slice predicates). Same template: leaf mining → routing-aware features → OR-test → spot-check → ablation → persist parquet → depth curve. Likely <+1pp on full-6M (per-session lift trend: pair +2.02, high +1.44, 2p +1.67, trips_pair likely <+1pp).

(b) **RECOMMENDED — Extract chain from depth-15 aug-37 tree.** 18,399 leaves; 63.74% full / 62.44% cv; **+7.58pp over v3.** Refit → sklearn `export_text` → translate to Python if/elif → byte-identical parity check on full 6M. Then `v3_evloss_baseline.py --strategy v5_dt --hands 2000 --save` and compare to v3 on per-profile absolute EV + $/1000 hands at $10/EV-pt. **This is the chain-shipping path and the deliverable the user is ultimately tracking.**

The reframe (Decision 033) favours continued mining until the feature ceiling stops moving. Session 19 added +1.67pp at depth=None and +0.88pp at depth=15 — still meaningful but the trend is diminishing. Three augmented-feature families have each contributed; the next mining pass is likely <+1pp. Recommended: (b).

## Decisions added this session

- **Decision 036** — Three two_pair augmented features added to the production feature set (default_bot_is_ds_tp, n_routings_yielding_ds_bot_tp, swap_high_pair_to_bot_ds_compatible). Lifts: +5.90pp on target slice, +1.67pp on full 6M, +1.64pp on 3-of-4 majority. Depth-15 knee +0.88pp / +0.85pp cv.

## Resume prompt (next session)

```
Resume Session 20 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 19)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 036 — two_pair augmented features)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 16-19 since the goal reframe)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/pair_aug_features.py + high_only_aug_features.py + two_pair_aug_features.py
  (3 augmented-feature modules)
- analysis/scripts/dt_phase1_aug3.py (Session 19 depth curve, full 6M, 37 features)
- data/feature_table.parquet, data/feature_table_aug.parquet,
  data/feature_table_high_only_aug.parquet, data/feature_table_two_pair_aug.parquet
  (all joined on canonical_id)

State of the project (end of Session 19):
- Three augmented-feature families now live: pair-aug (Session 17), high_only-aug (Session 18),
  two_pair-aug (Session 19). Combined, they lift the full-6M depth=None ceiling from
  61.74% (baseline) to 66.87% (+5.13pp) and the depth-15 knee from 61.96% to 63.74% / 62.44% cv-shape.
- v3 production: 56.16% (unchanged). Augmented depth-15 is +7.58pp over v3.
- Two_pair 3-of-4 slice ceiling lifted 79.47% → 85.37% (+5.90pp); two_pair full +7.50pp.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(a) Continue mining: trips_pair next.
    1. Filter feature_table.parquet to (mode_count == 3 AND category == 'trips_pair').
    2. Mine impure leaves with the existing 37 features (all 3 aug-families likely vacuous
       on trips_pair due to n_pairs==1 + n_trips==1 mismatch with their slice predicates).
    3. If signal magnitude is weak, halt and pivot to (b). Per-session lift is now ~+1pp
       on full-6M; if trips_pair adds <0.5pp the discovery phase has plateaued.
    4. OR-test → spot-check → batch + ablation → persist → depth curve.

(b) RECOMMENDED — Extract chain from current augmented depth-15 tree (37 features).
    1. Refit depth=15 DT on full 6M with all 37 features.
    2. sklearn `export_text` → translate to Python if/elif chain.
    3. Verify byte-identical predictions on full 6M.
    4. Run v3_evloss_baseline.py --strategy v5_dt --hands 2000 --save data/v5_dt_records.parquet
       and compare to v3 on per-profile absolute EV + $/1000 hands at $10/EV-pt.
    5. This is the chain-shipping path. Three augmented-feature families have each contributed;
       the next mining pass is likely <+1pp. Time to measure the actual EV-loss deliverable.

The reframe favours continued mining until the feature ceiling stops moving.
Session 19 added +1.67pp at depth=None and +0.88pp at depth=15 — still meaningful but
diminishing. Recommended Session 20 fork: (b) — extract the chain and measure.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.
```

---

### Session 20 — 2026-04-30 — Sprint 7 Phase E (chain extraction + EV-loss measurement; trips_pair halt)

**User directive at session open:** "go to documents > claudecode > taiwanese and find out where we are" → "lets do a [trips_pair mining] first and then extract the chian". So: Path (a) trips_pair mining FIRST, then path (b) chain extraction.

**Halt decision on path (a) — trips_pair (Decision 037):** ran the 4-step doctrine BEFORE designing features.
- **Step 2 (signal):** baseline DT on slice (28 features) ceiling = 86.18% / 17,503 leaves on 54,163 hands. trips_pair's baseline is already strong, leaving 13.82pp slice headroom (vs two_pair's 20.53pp).
- **Step 3 (impact):** trips_pair share of v3 EV-loss = 2.5% (n=39 of 2000 in v3_evloss_records, sum of `loss_weighted` per cohort). Population share 2.97% of full 6M.
- **Step 4 (cheap test):** miss-leaf concentration top-10 = 1.2%, top-50 = 4.7%, top-100 = 8.1% across 4,778 distinct miss-leaves — even more diffuse than two_pair (0.5/3.4/—). For trips_pair to add ≥+0.5pp full-6M shape (the user's halt threshold), the cohort must lift +16.8pp on full — unprecedented. Even at Session 19 magnitude (+7.5pp full-cohort), full-6M projects to +0.22pp.
- Recurring qualitative pattern in top miss-leaves IS visible (trip-on-bot vs pair-on-bot routing decision, mirroring two_pair's high-pair-on-mid vs high-pair-on-bot), but the cohort is too small to move the headline metric. **HALTED at Step 4. No feature module written.** ~12 minutes saved a session of work.

**Path (b) — chain extraction + EV-loss baseline (Decision 038):**

Step 1 — `extract_v5_dt.py`: trained depth=15 DT on full 6M with all 37 features (28 baseline + 3 pair-aug + 3 high_only-aug + 3 two_pair-aug). Fit time 14.5s. n_leaves = 18,399 (matches Session 19). Saved sklearn tree arrays to `data/v5_dt_model.npz` (133 KB, gzip'd npz): `children_left`, `children_right`, `feature`, `threshold`, `value_argmax`, `classes`, plus `feature_columns` and `cat_map`. Vectorised manual numpy tree-walk on full 6M: **0 diffs vs sklearn `dt.predict(X)` across 6,009,159 rows.**

Step 2 — `strategy_v5_dt.py`: production strategy callable. `strategy_v5_dt(hand: np.ndarray) -> int` mirrors `strategy_v3` interface. Computes 37 features from raw 7-byte hand using `tw_analysis.features.hand_features_scalar` for baseline + 3 aug compute functions, then walks the saved tree. ~50µs per hand. Two correctness gotchas captured in DECISIONS_LOG (Decision 038 §6):
1. **Category-id alphabetical vs natural-order.** `dt_phase1_aug3.py` uses `cat_map = sorted(unique(category))` (alphabetical: high_only=0/pair=1/quads=2/three_pair=3/trips=4/trips_pair=5/two_pair=6) — this differs from `tw_analysis.features.CATEGORY_TO_ID` (high_only=0/pair=1/two_pair=2/three_pair=3/trips=4/trips_pair=5/quads=6). Strategy module saves and loads its own cat_map.
2. **Aug-call gating.** Each `persist_*_aug.py` script uses a `category == 'X'` mask; out-of-category rows are zero. The aug compute functions don't all early-return on out-of-category hands (notably `compute_high_only_aug_for_hand`). First parity attempt failed with 69,234 cell diffs concentrated in the 3 high_only-aug columns. Fix: gate each aug call by category string in the strategy module.

Step 3 — `verify_v5_dt_parity.py`: full-pipeline parity check on 50K random canonical hands. Built parquet-derived feature matrix (extract_v5_dt logic) and from-hand-bytes feature matrix (strategy_v5_dt logic) for the same indices. **0 cell diffs across 37 features × 50K = 1.85M cells. 0 prediction diffs after walking the tree.** Shape-agreement on the 50K sample = **63.73%**, matching Session 19's depth-15 reference of 63.74% within sampling noise. v3 production at 56.16% means **v5_dt is +7.57pp over v3 on shape**.

Step 4 — `v3_evloss_baseline.py --strategy v5_dt --hands 2000 --samples 1000 --seed 42 --save data/v5_dt_records.parquet`: registered `strategy_v5_dt` in the `STRATEGIES` dict, ran 2000 hands × 4 profiles. Total time 527.6s (4.0 hands/sec). Hand overlap with v3 baseline: 2000 of 2000 (same RNG seed produces same deal sequence).

**Headline numbers (the deliverable the user has been tracking):**

| Profile      | v3 mean loss | v5_dt mean loss | Δ EV       | $/1000h at $10/pt |
|--------------|--------------|-----------------|------------|---------------------|
| mfsuitaware  | 1.3692       | 1.3283          | +0.0409    | +$409.31            |
| **omaha**    | **1.1514**   | **1.3315**      | **−0.1801**| **−$1,800.89**      |
| topdef       | 1.4385       | 1.3688          | +0.0697    | +$697.44            |
| weighted     | 1.2221       | 1.2212          | +0.0009    | +$8.82              |
| **mean**     | **1.2953**   | **1.3125**      | **−0.0172**| **−$171.83**        |

**Headline finding: shape-target trained DT is a NET EV LOSS in dollars.** v5_dt has +7.57pp shape lift over v3 but loses $172/1000h on average. The loss is concentrated on the omaha-first profile (−$1,801/1000h), where v5_dt sacrifices the omaha-favored setting in favor of the multiway-mode setting (which is right for 3 of 4 profiles but wrong for omaha). Decision 033's reframe was empirically validated: shape-agreement and EV are not the same thing.

**Files added:** `analysis/scripts/mine_trips_pair_leaves.py`, `analysis/scripts/extract_v5_dt.py`, `analysis/scripts/strategy_v5_dt.py`, `analysis/scripts/verify_v5_dt_parity.py`, `data/v5_dt_model.npz`, `data/v5_dt_records.parquet`. **Files modified:** `analysis/scripts/v3_evloss_baseline.py` (added v5_dt to STRATEGIES dict), `CURRENT_PHASE.md` (rewritten), `DECISIONS_LOG.md` (Decisions 037 + 038), this file.

**Tests:** Rust 124/124 ✓ (88 + 15 + 15 + 6, unchanged), Python 74/74 ✓ (24 + 11 + 9 + 9 + 13 + 8, unchanged).

**Session 21 fork:** **(A) pivot training target to per-profile EV-aware** is the recommended path. Either A.1 (DT regression on `ev_mean` or `ev_omaha` directly, then argmax over 105 settings at inference) or A.2 (per-profile DT ensemble, profile-conditioned at inference). The chain is shippable as the shape-target benchmark; the next iteration must change the target to match the user's dollar metric.


---

### Session 21 — 2026-04-30 — Sprint 7 Phase E (path-A target pivot tested; A.2 per-profile ensemble is a NULL RESULT)

**User directive at session open:** Resume prompt from Session 20 picked path (A) target-pivot as recommended. User in "discovery mode" + "data drives discovery" + 4-step doctrine before new MC.

**Step 0 — cheap-test of the path-(A) hedge ceiling (Decision 039):** before training anything, ran `analysis/scripts/cheap_test_oracle_hedges.py` on 200 random hands (seed=42, samples=1000). Each hand evaluates against all 4 profiles via existing `evaluate_all_profiles`, capturing the FULL 105×4 EV grid. 50s total wall time. Computed grand-mean EV for 9 candidate strategies including 7 oracles. Headline: **oracle_argmax_mean grand mean = +1.172 vs v5_dt −0.123 = +$12,949/1000h ceiling at $10/EV-pt.** Profile-known ceiling (oracle_BR_per_profile) is +1.285, so the hedge captures 92% of profile-known headroom with no profile knowledge. Choice-overlap with each per-profile BR: mfsuit 77.5% / omaha 49.5% / topdef 68.5% / weighted 77.0% (the latter set was the warning sign that A.2 ensemble would not be sufficient — but A.2 was still cheaper to test than A.1, so we ran it first).

**Step 1 — train 4 per-profile DTs (Decision 040 setup):** `analysis/scripts/extract_v6_per_profile_dts.py` trains 4 sklearn DecisionTreeClassifiers at depth=15 on full 6M canonical hands with the same 37 features as v5_dt, but per-profile br_<profile> targets:
- br_mfsuitaware: 60.78% literal (18,282 leaves)
- br_omaha: 63.81% literal (19,936 leaves)
- br_topdef: 58.07% literal (18,551 leaves)
- br_weighted: 64.74% literal (18,605 leaves)

All 4 byte-identical sklearn-vs-manual-walk parity (0 diffs / 6,009,159 rows each). Saved tree arrays + metadata to `data/v6_per_profile_dts.npz` (0.55 MB). Vote-distribution sample on 100K rows: 22.94% / 50.79% / 23.31% / 2.97% across 1/2/3/4-distinct-vote bins.

**Step 2 — strategy_v6_ensemble:** `analysis/scripts/strategy_v6_ensemble.py` reuses `compute_feature_vector` from `strategy_v5_dt.py`, walks all 4 trees, votes mode-of-4. Tiebreak (2-2 split or 4 distinct → mfsuitaware DT's vote). Wired into `STRATEGIES` dict in `v3_evloss_baseline.py`.

**Step 3 — EV-loss baseline (Decision 040):** `v3_evloss_baseline.py --strategy v6_ensemble --hands 2000 --samples 1000 --seed 42`. Total time 493.9s (4.05 hands/sec, slightly faster than v5_dt's 4.0 hands/sec). Results:

| Profile     | v3 mean loss | v5_dt mean loss | v6_ensemble mean loss | $/1000h v6 vs v3 | $/1000h v6 vs v5 |
|-------------|--------------|-----------------|-----------------------|------------------|------------------|
| mfsuitaware | 1.3692       | 1.3283          | 1.3339                | +$353            | −$56             |
| **omaha**   | **1.1514**   | **1.3315**      | **1.3483**            | **−$1,969**      | **−$168**        |
| topdef      | 1.4385       | 1.3688          | 1.3739                | +$647            | −$51             |
| weighted    | 1.2221       | 1.2212          | 1.2259                | −$38             | −$47             |
| **mean**    | **1.2953**   | **1.3125**      | **1.3205**            | **−$252**        | **−$81**         |

**Headline finding: v6_ensemble is a NULL RESULT.** Worse than both v5_dt and v3 on grand mean. Per-profile losses on every profile are slightly worse than v5_dt; omaha is the single biggest absolute hit (−$168/1000h). Decision 040 closes off path A.2.

**Step 4 — disagreement diagnostic (`diag_v5_v6_disagreement.py`):** the killer diagnostic. **v5_dt vs v6_ensemble = 90.25% choice-agreement on the 2000 hands.** Of the 195 (9.75%) disagreement hands: v6 wins 76 (39%), loses 119 (61%). The 4-DT vote-ensemble is essentially v5_dt with a 9.75% noise overlay. Worst-10 disagreement-hand table preserved in script output for future reference. The mfsuitaware tiebreak biases against omaha-style settings, which is exactly where v3 was previously winning by hand-tuned overlay (Decision 032).

**Step 5 — side-by-side compare:** `analysis/scripts/compare_v3_v5_v6.py` reads the 3 records parquets and emits absolute-EV / EV-loss / $/1000h tables. Hand_str overlap = 2000 of 2000 across all three (apples-to-apples confirmed).

**Why the null result (lessons):**
1. Each per-profile DT achieves only 58-65% literal accuracy on its own br target. When 4 such weak classifiers vote, the modal vote often equals `multiway_robust` (the mode-of-4 target v5_dt was trained on) — so v6 mostly reproduces v5_dt's choice.
2. The 50% of hands with a 2-distinct-vote pattern (3-1 splits + 2-2 ties combined) push v6 to the mfsuitaware fallback, which is biased away from omaha-favoring settings. The ensemble cannot reach the hedge ceiling because the tiebreak heuristic concentrates loss on the highest-EV-variance profile.
3. The cheap-test SAW the warning: argmax_mean overlap with each per-profile BR ranged 49.5%-77.5%. A weak-classifier vote can't reach an oracle ceiling that's structurally far from any single classifier's training target.
4. Choice-agreement (90.25%) is a leading indicator of EV impact: at most ~10% of EV impact is reachable by changing only the 9.75% disagreement hands. This is a useful heuristic for future strategy candidates.

**Files added:** `analysis/scripts/cheap_test_oracle_hedges.py`, `analysis/scripts/extract_v6_per_profile_dts.py`, `analysis/scripts/strategy_v6_ensemble.py`, `analysis/scripts/compare_v3_v5_v6.py`, `analysis/scripts/diag_v5_v6_disagreement.py`, `data/cheap_test_oracle_grid_200.npz`, `data/v6_per_profile_dts.npz`, `data/v6_ensemble_records.parquet`. **Files modified:** `analysis/scripts/v3_evloss_baseline.py` (added v6_ensemble to STRATEGIES dict), `CURRENT_PHASE.md` (rewritten), `DECISIONS_LOG.md` (Decisions 039 + 040), this file.

**Tests:** Rust 124/124 ✓ (88 + 15 + 15 + 6, unchanged), Python 74/74 ✓ (24 + 11 + 9 + 9 + 13 + 8, unchanged).

**Session 22 fork:** **(A.1)** DT regression on per-setting EV is the recommended path. The cheap-test ceiling is real; the gap is in target type and feature representation, not training algorithm. Cost: ~14 hours overnight MC for a 50K-hand × 105×4 EV training grid (extension of `cheap_test_oracle_hedges.py`). Apply the 4-step doctrine: run a 5K-hand pilot first (~1.4 hours), evaluate, then commit to the 50K scale only if pilot shows positive EV gain. **Alternative (B):** asymmetric hybrid that trusts ensemble unanimity but defaults to v5_dt on splits — testable in <1 hour with no new MC. **Alternative (C):** 2000-hand cheap-test for tighter ceiling estimate AND starter training set (~33 min) before committing to A.1's 50K scale.


---

### Session 22 — 2026-05-01 — CRITICAL str-sort BUGFIX + v7_regression beats v3 + v8_hybrid champion + pair-to-bot pattern discovery

**This session has two narrative beats. The first re-frames everything from sessions 16-21. The second produces the first deterministic strategy that actually beats v3.**

**Beat 1 — str-sort bug discovered (Decision 041):** during user pushback on v3's "pair → mid" rule, traced strategy_v3 on hand `Ks Qs 8h 8d 7d 5h Ac` and found v3 returns setting_index 99 with byte-sort interpretation = "top=Ac, mid=88, bot=KsQs7d5h" (correct!). But the engine MC reports setting 99 = "top=Qs, mid=88, bot=AcKs7d5h" — a completely different setting. Root cause: `trainer/src/engine.py` `evaluate_hand()` did `tuple(sorted(hand_strs))` which is Python str-sort, not byte-sort. Setting_index space differed for ~94% of random hands.

Fix: 1-line change in `trainer/src/engine.py` line 222 (commit `39a4528`). Sort by `_card_byte()` instead of str.

Impact:
- v3 grand mean EV pre-fix: −0.068. Post-fix: +0.985 (50K-hand tournament).
- Apparent v3-to-BR-ceiling gap shrunk from $13,941/1000h to $2,542/1000h.
- v3 vs argmax_mean choice agreement jumped from 14% to 59%.
- Sessions 16-21 EV claims all need re-verification. Buggy records archived as `*_buggy.parquet`. All four strategies (v3, v5_dt, v6_ensemble, v7_regression) re-run post-fix.

**Beat 2 — v7_regression baseline + v8_hybrid champion (Decision 042):** with the bug fixed, the previously-killed overnight chain re-launched. 50K MC sweep (~3.5h) + train v7 multi-output regression DT + run v7 baseline at 2000-hand seed=42.

Tournament results (50K hands, all 4 profiles):

| Strategy | mfsuit | omaha | topdef | weighted | grand | $/1000h vs v3 |
|----------|--------|-------|--------|----------|-------|----------------|
| v3 | +0.350 | +1.713 | +0.241 | +1.390 | +0.924 | 0 |
| v5_dt | +0.378 | +1.510 | +0.312 | +1.357 | +0.889 | −$344 |
| v6_ensemble | +0.379 | +1.497 | +0.313 | +1.361 | +0.887 | −$363 |
| **v7_regression** | +0.389 | +1.775 | +0.307 | +1.401 | +0.968 | **+$445** |
| **v8_hybrid** | +0.398 | +1.757 | +0.289 | +1.442 | **+0.971** | **+$478** |
| oracle_argmax_mean | +0.498 | +1.849 | +0.415 | +1.500 | +1.066 | +$1,421 |
| oracle_BR (cheats) | +0.538 | +2.124 | +0.503 | +1.546 | +1.178 | +$2,542 |

v7_regression is the FIRST learned strategy to beat v3 since the project began. v8_hybrid (v7 + v3 fallback for high_only and one_pair categories) extends the win and is much more opponent-balanced (every cell ≥ +$438/1000h).

**Categorical decomposition of v7 vs v3:**

| Category | n share | $/1000h | weighted contribution |
|----------|---------|---------|----------------------|
| trips | 4.5% | +$3,575 | +$163 |
| two_pair | 20.9% | +$739 | +$155 |
| trips_pair | 1.9% | +$4,030 | +$79 |
| high_only | 20.8% | −$203 | **−$42** ← v7 worse |
| pair | 49.4% | −$50 | **−$24** ← v7 worse |
| trips_pair, three_pair, quads | rare | +$1,470 to +$7,372 | +$130 |

The v7 win comes entirely from multi-pair routing. v8_hybrid keeps that, swaps back to v3 on high_only + pair, gains +$66/1000h.

**AAKK patch (v7_patched):** v3's hand-coded AAKK rule (KK-to-mid, AA-to-bot, low singleton on top) ties the oracle on test hand `Ac Ad Kc Kh 7s 5d 2h` at +3.366 EV/hand. v7 missed it (picked AA-to-mid for +3.330). Patch is correct but rare hand (~0.2%) so impact at 50K-scale is −$4/1000h (noise). Kept inside v8_hybrid.

**Pair-to-bot pattern discovered:** mining the 50K oracle grid showed:

| pair_rank | % oracle routes pair → BOT |
|-----------|---------------------------|
| 22 | 32.4% |
| 33-55 | ~24% |
| 66 | 16% |
| 77 | 9% |
| 88+ | < 5% |

For pair_rank ≤ 5 (the lowest 4 ranks of pair), routing pair-to-bot is EV-correct ~25% of the time. Targeted MC on `Jd Td 9c 4h 2c 2d 6s` showed all of v3, v7 pick "top=Jd, mid=22, bot=T-9-6-4" (-$1.732 mean EV) but the oracle picks "top=Jd, mid=6-4 (junk!), bot=T-9-2-2" (-$1.395 mean EV). Same mean-EV gain on `22 + Ah Kc unsuited highs`: +$4,124/1000h.

**Estimated headroom for v9 that adds pair-to-bot trigger rule: +$50-150/1000h on top of v8_hybrid.**

**Files added (commit `40f60b0`):**
- `analysis/scripts/strategy_v7_patched.py`
- `analysis/scripts/strategy_v8_hybrid.py` (champion)
- `analysis/scripts/tournament_50k.py` (per-strategy × per-profile leaderboard)
- `analysis/scripts/inspect_v7_tree.py`
- `analysis/scripts/distill_v7.py` (depth-5 distillation only 57% v7-agreement)
- `analysis/scripts/where_v7_beats_v3.py`
- `analysis/scripts/mine_pair_to_bot_50k.py`
- `analysis/scripts/probe_high_only_misses.py`
- `analysis/scripts/probe_low_pair_vs_connectors.py`
- `analysis/scripts/probe_user_hand.py` (extended with v7)
- `data/oracle_grid_50k.npz` (50K-hand × 4-profile × 105-setting grid; replaces post-bugfix)
- `data/v7_regression_model.npz`, `data/v7_regression_records.parquet`
- All buggy v3/v5_dt/v6_ensemble records archived as `*_buggy.parquet`

**Files modified:**
- `trainer/src/engine.py` (str-sort bugfix)
- `analysis/scripts/v3_evloss_baseline.py` (registered v7_patched + v8 hybrids)
- `CURRENT_PHASE.md` (rewritten)
- `DECISIONS_LOG.md` (Decisions 041 + 042)
- this file

**Tests:** Rust 124/124 ✓ (88 + 15 + 15 + 6, unchanged), Python 74/74 ✓ (24 + 11 + 9 + 9 + 13 + 8, unchanged).

**Doctrine update:** future verification step before chasing a counterintuitive negative result — audit the eval pipeline matches the strategy convention. The str-sort bug went unnoticed for 5+ sessions because the negative result reinforced the project's stated direction (Decision 033 reframe), not because any test caught it.

**Session 23 priorities:**
1. **Mine pair-to-bot trigger conditions** — for pair_rank ≤ 5 hands, what combination of features (suit profile, connectivity, broadway count) discriminates "oracle picks pair-to-bot" vs "oracle picks pair-to-mid"? Target: +$50-150/1000h v9 strategy.
2. **Attempt v7's "high-impact path" distillation** — extract the leaves where v7 differs from v3 AND the v7-pick is significantly better. Aggregate into ~5-10 new memorable rules to add to v3.
3. **Tournament expansion** — re-run tournament_50k with new strategies as they're built.
4. **Round-trip test** — add an automated check that strategy_v3(hand)'s setting_index, when looked up via mc.settings, returns the (top, mid, bot) cards strategy_v3 intended. Will catch any future str-sort-class regression.
