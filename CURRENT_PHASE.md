# Current: Sprint 1 — Hand Evaluator (Hold'em + Omaha) | READY TO START

> Updated: 2026-04-16
> Previous sprint: S0 Foundation — **COMPLETED**

---

## What Was Completed Last Session (2026-04-16)

Sprint 0 fully delivered. Every acceptance criterion met or exceeded.

- Rust engine scaffolded (`engine/`) with `card.rs`, `hand_eval.rs`, `lookup/mod.rs`, `setting.rs`, `lib.rs`, `main.rs`.
- 5-card hand evaluator correct for **all 2,598,960 hands** (exhaustive test `table_lookup_matches_direct_on_every_hand`).
- Benchmark: **5.4 ns per `eval_5`** (target was <50 ns).
- Lookup table serialized to `data/lookup_table.bin` (10.4 MB).
- CLI working: `cargo run --release -- eval --hand "As Kh Qd Jc Ts 9h 2d"` prints exactly 105 settings.
- `HandSetting` type + `all_settings()` verified — all 105 settings partition the input hand exactly.
- Project infra: `.gitignore`, `README.md`, `scripts/build.sh`, `analysis/` Python skeleton.
- Git initialized, first commit `f9f1e0d` landed.
- Decision 012 logged: colex lookup chosen over Cactus Kev.

Test totals: **38 tests, 0 failures.** Clean build in both debug and release.

---

## What's Currently In Progress

Nothing — Sprint 0 is closed. Sprint 1 has not started.

---

## What's Not Started Yet (Sprint 1)

- [ ] Top tier evaluator: best 5 of 6 (1 hole + 5 board) — 6 lookups
- [ ] Middle tier evaluator: best 5 of 7 (2 hole + 5 board) — 21 lookups (standard Hold'em)
- [ ] **Bottom (Omaha) evaluator: EXACTLY 2 from 4 + EXACTLY 3 from 5 — 60 lookups.** This is the #1 source of bugs in the project. Needs dedicated tests for the "4 suited hole cards", "4 cards to a straight on board", and "trips in hand" cases from `modules/hand-evaluation.md`.
- [ ] Scoring module: evaluate both players' settings across 2 boards, handle chops and 20-point scoop.
- [ ] Integration tests covering all three tier evaluators + full matchup scoring.
- [ ] Benchmark: top ~80 ns, middle ~250 ns, Omaha ~700 ns, full matchup ~2 µs.

---

## Blockers / Issues

None. Sprint 1 can start immediately — the 5-card evaluator and `HandSetting` type needed for Sprint 1 are both ready.

---

## Immediate Next Actions

1. Read `modules/hand-evaluation.md` tier-specific section and `modules/scoring-system.md` again.
2. Read `sprints/s1-hand-evaluator.md` for the explicit task list.
3. Create `engine/src/holdem_eval.rs` (top + middle) and `engine/src/omaha_eval.rs`.
4. Create `engine/src/scoring.rs` for the full settings-vs-settings-vs-two-boards scorer.
5. Write Omaha tests FIRST (test-driven) — the 2-from-hand rule is the easiest thing to get subtly wrong.

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- sprints/s1-hand-evaluator.md
- modules/hand-evaluation.md
- modules/scoring-system.md

Sprint 0 is complete. Sprint 1 starts now.

Begin Sprint 1: Hold'em (top + middle) and Omaha (bottom) evaluators, plus
the scoring module that compares two HandSettings against two community
boards and returns (p1_points, p2_points).

Critical: the Omaha evaluator MUST use exactly 2 from the 4-card hole and
exactly 3 from the 5-card board. Test against the 4-suited-hole, straight-
on-board, and trips-in-hand cases before anything else.

Use tw_engine::{Evaluator, Card, HandRank} from Sprint 0 — no need to
rebuild any of that. eval_5 is 5.4 ns per call.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
