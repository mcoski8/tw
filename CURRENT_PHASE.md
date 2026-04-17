# Current: Sprint 3 — Best Response Computation | READY TO START

> Updated: 2026-04-17
> Previous sprint: S2 Monte Carlo Engine — **COMPLETED**

---

## What Was Completed Last Session (2026-04-17, Session 03)

Sprint 2 fully delivered. Monte Carlo engine is the drop-in primitive Sprint 3 will call 133M times.

- `engine/src/monte_carlo.rs` (NEW) — `OpponentModel::Random`, `McResult`, `McSummary`, `mc_evaluate_setting`, `mc_evaluate_all_settings` (common random numbers), `mc_evaluate_all_settings_par` (rayon split/reduce over sample chunks)
- `engine/src/lib.rs` — registered module + re-exports
- `engine/src/main.rs` — new `mc` CLI subcommand with `--hand --samples --opponent --parallel --seed --show-top`
- `engine/Cargo.toml` — `rand` with `small_rng` feature; new `[[bench]] mc_bench`
- `engine/benches/mc_bench.rs` — 3 criterion benches: single-setting, all-settings serial, all-settings parallel
- 9 new `monte_carlo::tests` covering sampling correctness, reproducibility, parallel ≡ serial at 1 worker, convergence (top-1 stable from N=1000)

**Test totals: 90 tests, 0 failures** (Sprint 1: 81 → +9 new).

**Performance (criterion, release):**

| Bench | Measured | Target |
|-------|----------|--------|
| `mc_single_setting/N=1000` | 6.11 ms | <5 ms (soft, 22% over — expected) |
| `mc_all_settings_serial/105×1000` | **270.77 ms** | **<500 ms ✓ (headline)** |
| `mc_all_settings_parallel/105×1000` | 46.18 ms | — (5.9× speedup) |

The 500 ms headline target is met at 54% of the budget on single thread.

**Empirical sanity** on `As Kh Qd Jc Ts 9h 2d` at N=5000 parallel: top three EVs all place the J on top, matching research findings (top card J+ ideal). Best EV +3.402 vs worst +0.352; gap(1→2) = 0.073 (close at this N).

---

## What's Currently In Progress

Nothing — Sprint 2 is closed. Sprint 3 has not started.

---

## What's Not Started Yet (Sprint 3)

See `sprints/s3-best-response.md`. Key items:

- [ ] Suit canonicalization — reduce 133M hands to ~15-25M via Decision 006 (~5-10×)
- [ ] Canonical-hand enumerator + reverse index (canonical → representative 7-card concrete form)
- [ ] Per-hand best-response computation using `mc_evaluate_all_settings_par(..., OpponentModel::Random, ...)`
- [ ] Checkpoint/resume system (flat-file append + offset index); a multi-day run must survive OS reboots and Cargo rebuilds
- [ ] Progress reporting with ETA
- [ ] Binary output format for (canonical_hand_id, top_setting_index, ev)
- [ ] Short pilot: N=100 samples on ~1000 canonical hands (minutes) to verify pipeline shape
- [ ] Production run: N=1000 samples on all canonical hands (hours-to-days, parallel)
- [ ] Summary statistics + spot checks on known-easy hands

---

## Blockers / Issues

**None blocking.** Two known items to resolve early in Sprint 3:

1. **Per-hand cost budget.** Current: `mc_evaluate_all_settings_par` at N=1000 ≈ 46 ms on this machine. Naïve: 133M × 46 ms ≈ 70 days single-machine. After suit canonicalization (~8× expected): ~9 days. Acceptable with a weekend + one workday if we start a checkpointed long run. If we target the CLAUDE.md "<1 week single machine" line, we're within 25-30% already and canonicalization closes the gap.
2. **Opponent model.** Sprint 2 ships `OpponentModel::Random` only. Sprint 3's best response is against this random opponent (Decision 003 + CLAUDE.md Tier 1 plan). `MiddleFirst` is still deferred and lives behind the same enum for a later sprint (CFR, Sprint 4, will introduce mixed strategies anyway).

---

## Immediate Next Actions

1. Read `sprints/s3-best-response.md` for the explicit task list.
2. Read `modules/hand-bucketing.md` (suit canonicalization section) for the Decision 006 plan.
3. Design canonical-hand enumeration. Likely approach: for each multiset of rank-suit-pattern classes, pick a lex-smallest representative; store a `u32` canonical index per hand.
4. Pilot run: N=100 samples × 1000 canonical hands. Validate output file format and checkpoint code before any multi-hour run.
5. After pilot: spot-check 5-10 "known-answer" hands (pocket aces, broadway, wheel) against intuition + our research findings.

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY — canonical rules, rankings, tiebreakers)
- sprints/s3-best-response.md
- modules/hand-bucketing.md   (suit canonicalization section)
- DECISIONS_LOG.md   (scan for 001, 003, 005, 006)

Sprint 2 is complete (90 tests pass; `mc_evaluate_all_settings_par` hits 46 ms
per hand at N=1000 on this machine; Random opponent model). Sprint 3 starts now.

Begin Sprint 3: Best Response Computation. For each of the 133M possible
7-card hands — reduced to ~15-25M via Decision 006 suit canonicalization —
compute the best-response setting and its EV against OpponentModel::Random
using `mc_evaluate_all_settings_par`. Write results to a checkpointed binary
file: (canonical_hand_id: u32, best_setting_index: u8, best_ev: f32).

Order of operations:
  1. Suit canonicalization — enumerate canonical 7-card hand space, assign
     u32 indices, verify count and round-trip.
  2. Output file format + append-only checkpoint writer.
  3. Pilot run: N=100 samples × 1000 canonical hands.
  4. Spot check outputs on 5-10 known-answer hands.
  5. Production run: N=1000 samples on everything, rayon-parallel outer loop
     over canonical hands (not samples — inner MC is already parallel, we
     want coarser chunks for the outer loop).

Performance target: pilot in <30 minutes; production in <1 week single
machine (CLAUDE.md performance table). No UX work in this sprint — outputs
are raw binaries for Sprint 4+ to consume.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
