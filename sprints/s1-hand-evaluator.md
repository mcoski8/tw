# Sprint 1: Hand Evaluator (Hold'em + Omaha)

> **Phase:** Phase 1 - Engine Core
> **Status:** COMPLETED 2026-04-16

---

## Sprint Goals

Build the tier-specific evaluators on top of the 5-card lookup table:
1. Top tier evaluator: best 5 of 6 cards (1 hole + 5 board)
2. Middle tier evaluator: best 5 of 7 cards (2 hole + 5 board) — standard Hold'em
3. Bottom tier evaluator: Omaha — MUST use exactly 2 from 4 hole + 3 from 5 board
4. Full scoring system: compare two players' settings across two boards
5. Scoop detection (all 6 matchups won, zero chops)

---

## Tasks

### Top Tier Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Implement `eval_top(ev, card, board) -> HandRank` | **Completed** | `engine/src/holdem_eval.rs`; drops each of 6 cards once |
| Test: A with board KQJT2 = broadway straight | **Completed** | `holdem_eval::tests::top_ace_with_broadway_board_is_straight` |
| Test: 7 with board 77KQ3 = trips | **Completed** | `holdem_eval::tests::top_seven_with_77_board_is_trips` |
| Benchmark: target <100ns | **Completed** | Measured **26.5 ns** — ~3.7× better than target |

### Middle Tier Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Implement `eval_middle(ev, hole, board) -> HandRank` | **Completed** | Same file; drops 2 of 7 → C(7,2)=21 combos |
| Test: AA with board KQJ32 = pair of aces | **Completed** | `holdem_eval::tests::middle_aa_on_broadway_board_is_pair_of_aces` |
| Test: 87s with board 654AK = straight | **Completed** | `holdem_eval::tests::middle_87s_on_654ak_is_straight` |
| Benchmark: target <250ns | **Completed** | Measured **149 ns** — ~1.7× better than target |

### Bottom Tier (Omaha) Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Implement `eval_omaha(ev, hole, board) -> HandRank` | **Completed** | `engine/src/omaha_eval.rs`; const HOLE_PAIRS × BOARD_DROPS tables |
| **CRITICAL:** Verify exactly 2 from hand + 3 from board | **Completed** | Tests below enforce this |
| Test: 4-suited hole + 3-suited board → flush/SF allowed | **Completed** | `four_suited_hole_three_suited_board_allows_flush` |
| Test: 4-suited hole + <3-suited board → NO flush | **Completed** | `four_suited_hole_two_suited_board_is_NOT_flush` |
| Test: 4-to-straight board + 1-hole-connector → NO straight | **Completed** | `four_to_straight_on_board_one_hole_connector_does_not_make_straight` |
| Test: 4-to-straight board + 2-hole-connectors → straight | **Completed** | `four_to_straight_on_board_two_hole_connectors_makes_straight` |
| Test: Trips in hand (JJJ+5) → pair, NOT trips | **Completed** | `trips_in_hole_becomes_pair_not_trips` |
| Test: 4-of-a-kind in hand → two pair, NOT quads | **Completed** | `quads_in_hole_impossible_best_is_two_pair` |
| Test: 1 hole ace + trip board aces → quads | **Completed** | `one_ace_in_hole_plus_trip_board_gives_quads` (caught initial test-expectation bug) |
| Test: 0 hole aces + trip board aces → trips | **Completed** | `zero_aces_in_hole_and_trip_aces_on_board_is_trips_max` |
| Test: Wheel via 2+3 | **Completed** | `wheel_through_2_plus_3` |
| Benchmark: target <500-700ns | **Completed** | Measured **375 ns** — within target |

### Scoring System
| Task | Status | Notes |
|------|--------|-------|
| Implement `score_matchup` and `matchup_breakdown` | **Completed** | `engine/src/scoring.rs`; returns net points (sum to zero) |
| Implement scoop detection: 6 wins AND 0 chops → ±20 | **Completed** | `scoring::matchup_breakdown` |
| Implement chop handling: equal ranks → 0 for both | **Completed** | Chop variant on `Outcome` enum |
| Test: scoop triggers on 6/0 | **Completed** | `scoop_all_six_wins_zero_chops_pays_twenty` |
| Test: chop invalidates scoop | **Completed** | `chop_on_top_invalidates_scoop` — 4 wins + 2 chops → (10, −10), no scoop |
| Test: full chop → (0,0) | **Completed** | `all_six_chops_zero_points` |
| Test: end-to-end hand-checked matchup | **Completed** | `end_to_end_matchup_with_hand_checked_outcome` |
| Test: net points always sum to zero | **Completed** | `net_points_always_sum_to_zero` |

### Benchmarks
| Task | Status | Notes |
|------|--------|-------|
| `engine/benches/tier_bench.rs` with rotating inputs | **Completed** | 4 benches: top, mid, omaha, full matchup |
| Full matchup bench (3 tiers × 2 boards + scoop) | **Completed** | **2.14 µs** — 7% over <2 µs target; see Session Log |

---

## Session Log

### Session 02 — 2026-04-16 — Sprint 1 delivered

**Scope.** Full Sprint 1: top/middle/Omaha tier evaluators, scoring module with
scoop + chop handling, comprehensive tests, benchmarks.

**Engine code delivered:**
- `engine/src/holdem_eval.rs` — `eval_top` (6 lookups), `eval_middle` (21 lookups)
- `engine/src/omaha_eval.rs` — `eval_omaha` with const `HOLE_PAIRS` + `BOARD_DROPS` tables, unrolled 60-lookup loop
- `engine/src/scoring.rs` — `score_matchup`, `matchup_breakdown`, `MatchupBreakdown`, `Outcome`, net-points encoding
- `engine/tests/omaha_tests.rs` — 15 Omaha 2+3 rule tests
- `engine/tests/scoring_tests.rs` — 6 scoring tests including scoop fixture + chop-invalidates-scoop
- `engine/benches/tier_bench.rs` — 4 criterion benches with rotating inputs
- `engine/src/lib.rs` + `engine/Cargo.toml` — module registration + bench declaration

**Correctness:** 76 tests pass, 0 failures.
- 40 unit tests (card, hand_eval, holdem_eval, lookup, omaha_eval, scoring, setting)
- 15 hand_eval integration tests (carried from Sprint 0, all still pass)
- 15 omaha integration tests
- 6 scoring integration tests

**Performance (release mode, `cargo bench --bench tier_bench`):**

| Bench | Measured | Target | Margin |
|-------|----------|--------|--------|
| `eval_top` | 26.5 ns | <100 ns | 3.7× better |
| `eval_middle` | 149 ns | <250 ns | 1.7× better |
| `eval_omaha` | 375 ns | <500-700 ns | within target |
| `matchup_breakdown` | 2.14 µs | <2 µs | 7% over |

The full matchup is slightly over the 2 µs budget: 2 × 6 tier evaluations + scoop
logic. Decision 012 flagged a two-plus-two 7-card lookup as the escape hatch
for middle + Omaha when this becomes a Monte Carlo bottleneck. For Sprint 2 the
current number is fine: at 2.14 µs per matchup, 1,000 samples × 105 settings =
~224 ms per hand, well within the <500 ms budget for Monte Carlo (S2).

**Decisions logged:** Decision 013 (net-points scoring encoding) — see
`DECISIONS_LOG.md`.

**Gotchas / corrections:**
- Wrote a test `set_on_board_with_unmatched_hole_is_trips_not_quads` asserting
  that 1 hole ace + trip board aces = trips. Test failed (actual: quads). The
  test-expectation was wrong: Omaha 2+3 lets you pick 2 hole = {ace, any kicker}
  and 3 board = all 3 aces, giving 4 aces total. Split into two tests:
  `one_ace_in_hole_plus_trip_board_gives_quads` and
  `zero_aces_in_hole_and_trip_aces_on_board_is_trips_max`. This is exactly the
  class of 2+3-rule confusion the sprint warned about, caught by the test
  loop before anything landed on main.
- `holdem_eval::eval_middle` enumerates by "drop 2 of 7" rather than "choose 5
  of 7" — equivalent C(7,2)=21 combos but with cleaner iteration.

**Deferred:** CLI update to print tier ranks for each setting given a board.
Not needed for Sprint 2 (Monte Carlo takes settings + boards directly, not via
the CLI), so keeping the current Sprint 0 CLI surface untouched. Will revisit
when the trainer UI (S5) needs it.

**Carry-forward for Sprint 2:** None blocking. `matchup_breakdown` is the
drop-in primitive Monte Carlo will call once per sample.
