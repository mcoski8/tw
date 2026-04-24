# Sprint 5: Trainer Application

> **Phase:** Phase 3 - Trainer
> **Status:** Sprint 5a FOUNDATION COMPLETE (2026-04-24) — Sprint 5b (stats, difficulty modes, solver-derived explanations) pending

## Session 09 log — 2026-04-23/24

Sprint 5a vertical slice complete. Single opponent: Python-orchestrated Flask trainer with drag-and-drop UI, Rust subprocess for live MC (new `mc --tsv` flag), heuristic explanation layer v1. Multi-opponent: profile selector (4 production profiles) + "Compare across all profiles" with per-profile best-arrangement rendering. See `DECISIONS_LOG.md` Decision 029 and `handoff/MASTER_HANDOFF_01.md` Session 09 for full details. Files: `trainer/app.py`, `trainer/src/{dealer,engine,explain}.py`, `trainer/static/{index.html,style.css,app.js}`, `engine/src/main.rs` (--tsv flag).

---

## Sprint Goals

Build a user-facing training tool where users practice setting Taiwanese Poker hands and get instant feedback against the computed optimal.

1. Deal random 7-card hands to the user
2. User selects their setting (top/mid/bot)
3. Compare against computed optimal setting
4. Show EV difference and explain the reasoning
5. Track accuracy and improvement over time
6. Difficulty modes: easy (strong hands only), medium (mixed), hard (edge cases)

---

## Tasks

### Core Trainer
| Task | Status | Notes |
|------|--------|-------|
| Load optimal settings database from binary file | Pending | |
| Deal random hand, display to user | Pending | |
| Accept user input: select top card, mid cards, bot cards | Pending | |
| Look up optimal setting for this hand | Pending | |
| Compare user setting vs optimal | Pending | |
| Display: correct/incorrect, EV difference, explanation | Pending | |

### UI Options
| Task | Status | Notes |
|------|--------|-------|
| CLI version (terminal-based) | Pending | Minimum viable |
| Web version (HTML/JS served by Python) | Pending | Optional, nicer UX |
| Card display with suit symbols and colors | Pending | |
| Timer option (practice speed-setting) | Pending | |

### Statistics & Learning
| Task | Status | Notes |
|------|--------|-------|
| Track: hands played, correct %, avg EV loss | Pending | |
| Track: accuracy by hand type (pairs, trips, unpaired, etc.) | Pending | |
| Show: most common mistakes | Pending | |
| Difficulty filter: only deal hands where decision is close | Pending | |
| Spaced repetition: re-deal hands user got wrong | Pending | |

---

## Session Log
