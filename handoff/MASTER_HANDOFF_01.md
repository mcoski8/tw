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
