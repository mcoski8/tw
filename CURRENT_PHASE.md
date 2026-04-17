# Current: Sprint 2 — Monte Carlo Engine | READY TO START

> Updated: 2026-04-16
> Previous sprint: S1 Hand Evaluator — **COMPLETED**

---

## What Was Completed Last Session (2026-04-16 → 2026-04-17, Session 02)

Sprint 1 fully delivered, plus a mid-session rules-verification pass that produced the new authoritative rules doc.

- `engine/src/holdem_eval.rs` — `eval_top` (6 lookups, **26.5 ns**), `eval_middle` (21 lookups, **149 ns**)
- `engine/src/omaha_eval.rs` — `eval_omaha` with const hole-pair/board-drop tables, **375 ns** per call
- `engine/src/scoring.rs` — `matchup_breakdown` + `score_matchup`; scoop (20pt) and chop handling; net-points encoding; **2.14 µs** for full 2-player matchup
- `engine/tests/omaha_tests.rs` — 15 tests covering every known 2+3-rule trap (4-suited hole with/without enough board spades, 4-to-straight boards with 1 vs 2 connectors, trips-in-hand, quads-in-hand, wheel, etc.)
- `engine/tests/scoring_tests.rs` — 6 tests including scoop fixture (P1 strictly dominates all 6) and chop-invalidates-scoop
- `engine/benches/tier_bench.rs` — 4 rotating-input criterion benches
- **`modules/game-rules.md` (NEW)** — canonical, citation-backed rules authority. Cross-referenced from `CLAUDE.md` (now mandatory in the session-start reading order) and `modules/hand-evaluation.md`. Covers tier card-usage rules, 9-category hand ranking + every tiebreaker, invariants, non-negotiable correctness requirements. Rules verified against Wikipedia on 2026-04-17.
- 5 additional play-the-board / Omaha-forbidden-shortcut tests added to pin down the rule assertions in game-rules.md.

Test totals: **81 tests, 0 failures.** Release build clean.

---

## What's Currently In Progress

Nothing — Sprint 1 is closed. Sprint 2 has not started.

---

## What's Not Started Yet (Sprint 2)

See `sprints/s2-monte-carlo.md`. Key items:

- [ ] `monte_carlo.rs`: single-setting EV (N samples) and all-105-settings EV
- [ ] Opponent modeling: uniform-random (start here) and MiddleFirst heuristic
- [ ] rayon-parallelized outer loop over hands × settings
- [ ] Convergence test: N=100 vs N=1000 vs N=10000, check that best-setting ranking stabilizes
- [ ] CLI: `tw-engine mc --hand "As Kh ..." --samples 1000`
- [ ] Performance: <500ms for 1 hand × 105 settings × 1000 samples

---

## Blockers / Issues

None. `matchup_breakdown` is the exact primitive Monte Carlo needs.

Known (non-blocking) tension: `matchup_breakdown` bench is 2.14 µs vs <2 µs target. At 1,000 samples × 105 settings that's 224 ms/hand — within the <500 ms Monte Carlo budget, so Sprint 2 can proceed without optimizing the tier evaluators. If Monte Carlo ends up tight, Decision 012 documents the two-plus-two 7-card lookup as the escape hatch.

---

## Immediate Next Actions

1. Read `sprints/s2-monte-carlo.md` for the explicit task list.
2. Read `modules/monte-carlo-engine.md` for sampling design + opponent model interface.
3. Create `engine/src/monte_carlo.rs` with a single-thread prototype first, then wire up rayon.
4. Validate convergence: the EV ranking of the top-5 settings should be stable across N=100 and N=1000 for a handful of random hands.

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
- sprints/s2-monte-carlo.md
- modules/monte-carlo-engine.md

Sprint 1 is complete (81 tests pass, tier evaluators + scoring at target
speed; modules/game-rules.md is the authoritative rules doc). Sprint 2
starts now.

Begin Sprint 2: Monte Carlo engine. For a given 7-card hand and a specific
HandSetting, estimate the EV against a uniform-random opponent by sampling:
draw opponent's 7 cards from the remaining 45 cards, deal two 5-card boards
from the remaining 38, enumerate opponent's 105 settings to find their best
response (or a heuristic MiddleFirst setting — start random, add MiddleFirst
later), score the matchup, accumulate. Repeat N times, average.

Target: <500ms for 1 hand × 105 settings × 1000 samples (single-thread is
fine to start — add rayon for parallelism once the math is right).

Use `matchup_breakdown` from Sprint 1 as the inner scoring primitive —
benchmarked at 2.14 µs per call.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
