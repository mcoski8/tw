# Sprint 3: Best Response Computation (Multi-Pass Adaptive Solver)

> **Phase:** Phase 2 - Solving
> **Status:** IN PROGRESS — Pipeline built and validated; production run pending (Session 04, 2026-04-17)

---

## Sprint Goals

Compute the optimal setting for every possible 7-card hand using the adaptive multi-pass pipeline. This is THE sprint that solves the game.

1. Implement setting pre-screening (reduce 105 → ~25 viable settings per hand)
2. Implement 3-pass adaptive solver (quick scan → precision → final resolution)
3. Implement suit canonicalization to reduce ~133M hands to ~18M
4. Implement checkpoint/resume system for multi-week computation
5. Implement progress reporting with ETA
6. Run Pass 1 (~3 days), analyze results, run Passes 2-3 (~7-10 days)
7. Validate output against Monte Carlo spot-checks

See `docs/modules/compute-pipeline.md` for full technical spec including time estimates, memory requirements, and output format.

---

## Tasks

### Setting Pre-Screening
| Task | Status | Notes |
|------|--------|-------|
| Implement quick_score() for any HandSetting | Deferred | Decision 017 — single-pass at N=1000 across all 105, no pre-screen |
| Implement pre_screen(hand) → top 25 settings by quick_score | Deferred | Same — keep all 105 in MC scope |
| Validate: sample 10K hands, confirm true optimal is always in top 25 | Deferred | Not needed under single-pass |
| If validation fails: widen to top 30-35 or adjust weights | Deferred | Not needed under single-pass |

### Hand Canonicalization
| Task | Status | Notes |
|------|--------|-------|
| Implement suit permutation canonicalization | DONE | `engine/src/bucketing.rs` — `canonicalize`, `is_canonical` |
| Build canonical_index → hand mapping | DONE | Index = position in `enumerate_canonical_hands()` |
| Build hand → canonical_index mapping | Deferred | Not needed for solve; will add for Sprint 5 trainer |
| Count total canonical hands (expect ~15-20M) | DONE | **6,009,159** — Burnside-verified (matches exactly) |
| Verify: all suit permutations of a hand map to same canonical | DONE | Test `canonicalize_agrees_across_suit_permutations` |

### Single-Pass Production Solve (Decision 017)
| Task | Status | Notes |
|------|--------|-------|
| Implement per-hand `solve_one`: 105 settings × N=1000 vs Random opp | DONE | `engine/src/best_response.rs::solve_one` |
| Record `(canonical_id, best_setting_index, best_ev)` per hand | DONE | 9-byte fixed records |
| Outer rayon parallelization over canonical hands | DONE | `solve_range` — 9.0× measured speedup |
| Append-only checkpoint writer with crash-safe resume | DONE | `BrWriter`; resume = (filesize − 32) / 9 |
| Header mismatch refuse-to-append (samples / seed / model) | DONE | `BrError::HeaderMismatch` test |
| Progress reporting with ETA | DONE | One log line per block |
| Pilot run N=100 × 1K hands | DONE | 3.81 s, all settings sane (low-rank-cluster region) |
| Extended pilot N=1000 × 10K hands | DONE | 373 s = 37.3 ms/hand → 2.6-day projection for full run |
| Production run on all 6.01M canonical hands | **PENDING** | Recipe in CURRENT_PHASE.md; user-gated launch |
| Analyze: EV distribution + setting-frequency histogram | PENDING | After production completes |

### Output & Validation
| Task | Status | Notes |
|------|--------|-------|
| Write final results to binary file | DONE | `data/best_response.bin` will be ~54 MB |
| Generate summary statistics | PENDING | After production run |
| Spot-check: 100 random hands re-solved at N=10K, ≥95% agreement | PENDING | After production run |
| Spot-check: contemporaneous sanity at N=1000 on 6 named hands | DONE | All match research findings (see Session Log entry below) |

---

## Compute Budget (M4 Mac Mini, 8 effective cores)

Original adaptive multi-pass plan (kept for reference; superseded by Decision 017):

| Pass | Hands | Time Estimate |
|------|-------|---------------|
| Pass 1 | ~18M | 2-3 days |
| Pass 2 | ~1-2M | 4-6 days |
| Pass 3 | ~100K | 2-4 days |
| **Total** | | **8-12 days** |

Actual single-pass plan (Session 04 measurement):

| Step | Count | Wall time |
|------|-------|-----------|
| Canonical enumeration | 6,009,159 hands | 0.44 s |
| Pilot N=100 × 1K | 1K hands | 3.8 s |
| Extended pilot N=1000 × 10K | 10K hands | 373 s |
| **Production N=1000 × 6.01M (projected)** | **6,009,159 hands** | **~62 hours / 2.6 days** |

Canonical-hand count came in at **6.01M, not 18M** — Burnside lemma over S₄ gives a 22.26× reduction (vs the 5–10× ballpark in CLAUDE.md), making single-pass at N=1000 feasible in well under a week without adaptive refinement.

---

## Session Log

### Session 04 — 2026-04-17 — Sprint 3 pipeline built and validated end-to-end

**Scope:** Implement bucketing + best_response + CLI from scratch. Validate file format and parallelism. Run pilots. Spot-check named hands. Stop short of the 2.6-day production launch (user gate).

**Result:** Everything except the production run itself is done. Test count 90 → 105 (+15 new). Pilot at N=1000 × 10K hands hit 37.3 ms/hand at 9× parallel speedup.

**Code delivered:**
- `engine/src/bucketing.rs` — suit canonicalization, enumerate, count, file I/O. Burnside-verified count of 6,009,159 canonical hands.
- `engine/src/best_response.rs` — `BestResponseRecord` (9 bytes), `BrHeader` (32 bytes "TWBR"), `BrWriter` with append-only crash-safe resume (offset = (filesize − 32) / 9), `solve_one`, `solve_range` (outer-rayon).
- `engine/src/lib.rs` + `engine/src/main.rs` — module registration, three new CLI subcommands (`enumerate-canonical`, `solve`, `spot-check`).
- `engine/Cargo.toml` — `tempfile = "3"` dev-dep.

**Empirical:**
- 6,009,159 canonical hands. Cross-checked against Burnside's lemma:
  - Identity 133,784,560 + 6×1,723,176 + 0 + 8×12,025 + 0 = 144,219,816; ÷24 = 6,009,159 ✓.
- Throughput at N=1000 production cadence: 37.3 ms/hand; 57 MB peak RSS.
- Six spot-checks (quad aces, royal-hole + connectors, wheel + T9, AAKK, rainbow gappers, trip-K + 88) all produce settings consistent with research findings: top card J+ where possible, premium pair → bot for 3pt scoring weight, suited pair → mid for flush draws.

**Decisions logged this session:** 017 (single-pass solve, skip pre-screening + adaptive multi-pass), 018 (fixed-width 9-byte record file format).

**Gotchas:**
- First version of the canonical-enumeration round-trip test used a non-suit-closed subset (first 9 cards from the 52-card deck). Suit permutations can move cards outside such a subset, causing legitimate canonical forms to "escape" the test universe. Fixed by switching to a closed subset (first 12 cards = ranks {2,3,4} all four suits each).
- Clap doesn't accept hex literals like `0xC0FFEE` for `--seed` even when the default-value is given that way; pass decimal at the CLI (`12648430`).
