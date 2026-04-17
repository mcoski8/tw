# Sprint 0: Foundation + Lookup Tables

> **Phase:** Phase 1 - Engine Core
> **Status:** COMPLETED (2026-04-16)
> **Sprint File:** `docs/sprints/s0-foundation.md`

---

## Sprint Goals

1. Initialize Rust project with proper dependency management
2. Define core types: Card, Rank, Suit, Deck
3. Build 5-card hand evaluator with lookup table generation
4. Verify hand evaluator correctness against known hand rankings
5. Benchmark hand evaluation speed (target: <50ns per eval)
6. Define HandSetting type (top=1, mid=2, bot=4 from 7 cards)
7. Enumerate all 105 possible settings for a 7-card hand
8. First working binary that evaluates a hand from CLI
9. Initialize Python analysis project structure
10. Initialize documentation

---

## Tasks

### Rust Project Setup
| Task | Status | Notes |
|------|--------|-------|
| Create `engine/Cargo.toml` with dependencies | Done | rayon, rand, serde, clap, bincode; LTO + opt-level=3 for release |
| Define Card type (rank: u8, suit: u8) | Done | Packed u8 = (rank-2)*4 + suit, index in 0..52 |
| Define Rank enum (2-14, A=14) | Done | RANK_MIN=2, RANK_MAX=14 constants; char helpers |
| Define Suit enum (0-3) | Done | c/d/h/s enum + char helpers |
| Implement Deck: new(), shuffle(), deal() | Done | Vec-backed, rand::seq::SliceRandom shuffle |
| Implement Display traits for cards | Done | "As", "Kh", "2d" format |
| Parse cards from string ("As Kh Qd") | Done | FromStr for Card, parse_hand for whitespace list |

### 5-Card Hand Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Choose evaluation algorithm | Done | Colex-indexed lookup table (see Decision 012) |
| Implement 5-card hand rank computation | Done | compute_rank_5, u32 encoding: category in bits 24-27, kickers in 4-bit slots |
| Generate lookup table for all C(52,5) = 2,598,960 hands | Done | Evaluator::build(), ~1s in release |
| Serialize lookup table to binary file | Done | bincode to data/lookup_table.bin (10.4MB) |
| Load lookup table from file on startup | Done | Evaluator::load_or_build — builds + saves if missing |
| Verify: Royal flush > straight flush > quads > ... > high card | Done | category_ladder test + integration tests |
| Verify: A-2-3-4-5 is lowest straight (wheel) | Done | wheel_is_lowest_straight_not_ace_high, steel_wheel_is_lowest_straight_flush |
| Verify: Same hand ranks compare by kickers correctly | Done | Full cascade tests for flush, two pair, one pair, high card |
| Benchmark: target <50ns per evaluation | Done | **5.4 ns/eval** (criterion, rotating across categories) — ~10× target |

### Hand Setting Type
| Task | Status | Notes |
|------|--------|-------|
| Define HandSetting struct: top(Card), mid([Card;2]), bot([Card;4]) | Done | Stack-allocated, sorted descending within each tier for deterministic display |
| Implement `all_settings(hand: [Card;7]) -> Vec<HandSetting>` | Done | Returns exactly 105; debug_assert guards the count |
| Verify: all 105 settings use all 7 cards exactly once | Done | every_setting_partitions_the_seven_cards test |
| Implement Display for HandSetting | Done | `top [As]  mid [Kh Qd]  bot [Jc Ts 9h 2d]` |

### Project Infrastructure
| Task | Status | Notes |
|------|--------|-------|
| Create .gitignore | Done | target/, data/*.bin, .env, Python/OS artifacts |
| Create README.md | Done | Project overview + getting started |
| Create scripts/build.sh | Done | Auto-adds ~/.cargo/bin to PATH; builds + caches lookup table |
| Initialize Python analysis project | Done | pyproject.toml skeleton, src/__init__.py (filled in later sprints) |
| Verify all docs/ files in place | Done | CLAUDE.md, CURRENT_PHASE.md, modules/, sprints/ present |
| First git commit | Done | commit f9f1e0d on main |

---

## Acceptance Criteria

- [x] `cargo test` passes with all hand evaluation tests green — 15/15 pass, incl. exhaustive 2,598,960-hand roundtrip
- [x] `cargo bench` shows <50ns per 5-card evaluation — **5.4 ns**
- [x] CLI can parse "As Kh Qd Jc Ts 9h 2d" and display all 105 settings — verified
- [x] Lookup table generates and loads correctly — 10.4MB at data/lookup_table.bin, roundtrip tested
- [x] Documentation complete — this file + CURRENT_PHASE.md + MASTER_HANDOFF + DECISIONS_LOG updated

---

## Session Log

### Session 2026-04-16 — Sprint 0 fully completed

**Delivered files (engine/):**
- `Cargo.toml` — deps: rayon 1.10, rand 0.8, serde 1, bincode 1.3, clap 4.5, criterion 0.5 (dev). Release profile LTO + opt-level=3.
- `src/card.rs` — `Card(u8)` packed representation, Rank/Suit constants, `Deck`, `parse_hand`, `FromStr`/`Display`. 5 unit tests.
- `src/lookup/mod.rs` — colex indexing over 5-card combinations. Precomputed `BINOM[52][6]` via const fn. `NUM_5CARD = 2_598_960`. 4 unit tests including full bijection check.
- `src/hand_eval.rs` — `HandRank` u32 encoding, 9 category constants, `compute_rank_5` direct poker-rank function used at table-build time + as test reference, `Evaluator` struct with `build` / `load_or_build` / `eval_5`. `eval_5` is pure: array lookup, no alloc. 10 unit tests.
- `src/setting.rs` — `HandSetting { top, mid[2], bot[4] }`, `all_settings(hand)` enumerating all 105, `NUM_SETTINGS=105`. 3 unit tests.
- `src/lib.rs` + `src/main.rs` — library surface and `eval` / `build-lookup` CLI subcommands.
- `tests/hand_eval_tests.rs` — 15 integration tests. Includes `table_lookup_matches_direct_on_every_hand` which iterates all 2,598,960 5-card hands and asserts `Evaluator::eval_5 == compute_rank_5`. Runs in ~0.12s.
- `benches/eval_bench.rs` — criterion bench rotating across 8 hands covering all categories. **5.40 ns ± 0.01 ns per `eval_5`.**

**Delivered files (root):**
- `.gitignore`, `README.md`, `scripts/build.sh` (executable, auto-adds `~/.cargo/bin` to PATH).
- `analysis/pyproject.toml` + `analysis/src/__init__.py` skeleton.

**Verification:**
- `cargo build` — clean
- `cargo test --release` — 23 unit + 15 integration + 0 doc = **38 tests pass, 0 fail**
- `cargo bench` — `eval_5_rotating` time: `[5.4001 ns 5.4117 ns 5.4235 ns]`
- CLI: `cargo run --release -- eval --hand "As Kh Qd Jc Ts 9h 2d"` prints exactly 105 settings
- Lookup table: `data/lookup_table.bin` = 10,395,848 bytes (2,598,960 × 4 bytes + bincode overhead)

**Decisions made this session:**
- Decision 012: Colex-indexed array lookup chosen over Cactus Kev's prime-hash. See DECISIONS_LOG.md.

**Gotchas hit:**
- Initial doc comment in `setting.rs` embedded `C(7,1) × C(6,2)` math with the × symbol. rustdoc tried to compile it as Rust code. Fixed by moving the formula into prose rather than an indented block.

**Git:**
- Repo initialized at `/Users/michaelchang/Documents/claudecode/taiwanese/`.
- Commit `f9f1e0d` — "Sprint 0: foundation + 5-card hand evaluator".
- Not pushed (no remote configured yet).
