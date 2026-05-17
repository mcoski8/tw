# Camera App Project — Kickoff Document

> **Project codename (working):** TaiwanCam (placeholder — operator to confirm/rename)
>
> **Status:** Vision / kickoff document. The new project has not started yet. This document defines the scope, raises the core architectural questions, and proposes the documentation structure for Session 1.
>
> **Created:** 2026-05-16 (end of Taiwanese Poker Solver Session 98)
> **Authored by:** Claude (closing-session of the Taiwanese project)

---

## 1. Project Summary

A phone application that:
1. **Captures a 7-card Taiwanese Poker hand** via the device camera (cards photographed in any orientation, any order).
2. **Recognizes the 7 cards** (rank + suit per card) using computer vision.
3. **Computes the optimal setting** — which card → top, which 2 → mid, which 4 → bot — based on the production v65 strategy chain from the Taiwanese Poker Solver project.
4. **Displays the recommendation** with an explanation of WHY this setting is optimal (which rule fires).
5. **Optionally tracks the user's accuracy over time** — when they set their hand differently from the optimal, log the deviation and EV cost.

**Educational use only. NOT a cheating tool.** The app exists to:
- Test what's possible to code (image recognition + strategy backtest in real-time)
- Backtest the V4/V5 Lean strategy guide against real played hands
- Give learners instant feedback on their hand-setting decisions
- Validate the operator's hands-per-hour assumption against actual play time

## 2. What this is NOT

- ❌ NOT a real-time table assistant during live play
- ❌ NOT a hand-history database that uploads to a server for analysis
- ❌ NOT a multiplayer game (that's the existing TaiwanAPP project)
- ❌ NOT a Taiwanese rules tutorial (assumes user knows the rules)

The use case is **between hands at a home game, OR studying alone with a deck**, the user photographs their 7 cards, sees the optimal setting, learns by reviewing the rule that fired.

---

## 3. The Core Architectural Question (Session 1 must decide)

### Option A — Heuristic engine on device

Port `strategy_v65_mid_pair_chain_extend.py` from the Taiwanese project to mobile-native code (Swift / Kotlin / JS depending on stack). Run the 25-rule chain on-device, producing the optimal setting for any 7-card hand in microseconds.

**Pros:**
- Tiny binary footprint (a few KB of code)
- Works offline
- Easy to update if strategy changes
- Latency: <1 ms per hand
- Mirrors V5 Lean's 10 rules → small, auditable code path

**Cons:**
- Must port + maintain the strategy logic on each platform (Swift + Kotlin if going native)
- ML fallback (v44_dt) requires shipping a 2.25M-leaf decision tree (~10-50 MB) on-device OR using a cloud lookup, OR accepting reduced accuracy

### Option B — Database lookup table

Pre-compute the optimal setting for all **6,009,159 canonical 7-card hands** (the suit-canonicalized count — *not* 1.5M; the operator was off in casual conversation). Store as a flat lookup table. App canonicalizes the recognized hand → looks up → returns setting.

**Pros:**
- Zero strategy logic on device — just a function call
- Provably correct (returns whatever the project pre-computed)
- Trivially fast (constant-time lookup)
- Can include v44_dt's ML refinements for the 4 ML-handled categories — no decision tree on device needed

**Cons:**
- Lookup table size: 6M entries × few bytes each. Setting index is 0-104 (1 byte). Plus the canonical hand key (~7 bytes for sorted card indices). Plus optional EV (4 bytes float). **~30-80 MB compressed.** Significant for a mobile app.
- Hand canonicalization on-device requires implementing the suit-permutation logic
- Updating the strategy requires regenerating + redistributing the table

### Option C — Hybrid (recommended for evaluation)

- **On-device:** the V5 Lean 10-rule heuristic engine (small, fast, audits well)
- **Optionally:** a small lookup table for the ML-handled categories (no-pair, two-pair, single-pair-PBOT-DS, trips) — maybe 2-4 MB if compressed to setting-index only
- **Optionally:** server-side oracle lookup as a "second opinion" feature

**Pros:**
- Combines the best of A + B
- Heuristic engine handles 99% of hands instantly
- ML lookup catches the marginal EV the rules miss
- Smaller footprint than full DB

**Cons:**
- Most engineering complexity
- Two systems to maintain

### Recommendation

**Start with Option A (pure heuristic).** It's the smallest, simplest, fastest path to a working app. Measure latency and footprint in real testing. If the operator wants higher accuracy in the ML-handled categories, add Option C's selective lookup table in a future sprint.

The 6M-hand full DB (Option B) is over-engineered for v1 unless the operator wants offline-perfect-play (no heuristic involved). Decide in Session 1.

---

## 4. Image Recognition — the Other Hard Problem

Recognizing 7 playing cards from a photo requires:

| Capability | Options |
|---|---|
| **Card detection** (find the cards in the image) | OpenCV contour detection / Vision framework (iOS) / ML Kit (Android) |
| **Card classification** (rank + suit per card) | Pre-trained model on playing-card images (e.g., YOLOv8 or MobileNet trained on PlayingCards dataset) / Custom train if needed |
| **Orientation / occlusion handling** | Detect rotation; require user to lay cards face-up flat with separation |
| **Multi-card recognition** | Detect all card bounding boxes; classify each; verify exactly 7 detected; warn if mismatch |

### Realistic UX

1. User photographs 7 cards laid out (any order, any rotation, no overlap)
2. App detects 7 card bounding boxes
3. For each box, runs rank+suit classifier
4. Shows the user the 7 detected cards for confirmation (the user can correct any misclassifications by tapping)
5. Once confirmed: compute optimal setting → display

**Confidence threshold:** if any card is detected with <90% confidence, prompt the user to retake or manually edit.

### Stack options for image recognition

- **iOS native:** Vision framework + Core ML model
- **Android native:** ML Kit + TensorFlow Lite
- **Cross-platform (RN):** TensorFlow Lite with `react-native-fast-tflite`, or call a native module
- **Web app (simpler):** `getUserMedia` + canvas + a JS-loadable model

Given the operator already runs **TaiwanAPP in React Native** at `/Users/michaelchang/CODE/TaiwanAPP/`, RN + TensorFlow Lite is the most likely stack.

---

## 5. Proposed Stack (Session 1 to confirm)

| Layer | Choice (default) | Alternative |
|---|---|---|
| App framework | React Native (operator's existing stack) | Native iOS+Android (more performance, more code) |
| Image recognition | TensorFlow Lite + pre-trained card classifier (download or train) | Native Vision frameworks (platform-specific) |
| Strategy engine | Port `strategy_v65` to JS/TS (Option A) | Pre-computed lookup table (Option B) |
| State management | Whatever TaiwanAPP uses | New if greenfield |
| Backend (optional) | None for v1 (offline-first) | Supabase if user-history tracking is wanted |
| Card image dataset | Public PlayingCards dataset on Kaggle / Roboflow | Custom data collection |

---

## 6. Proposed Documentation Structure (matching Taiwanese project style)

For the new project, create at the repo root:

| File | Purpose | Update cadence |
|---|---|---|
| `CLAUDE.md` | Project summary, scope, rules, what-this-is-not, file structure overview | Append-only for major decisions |
| `CURRENT_PHASE.md` | What's happening NOW in the current session — full state of progress, blockers, immediate next actions | REWRITTEN every session |
| `DECISIONS_LOG.md` | Settled decisions, numbered, with date + rationale + what-it-does-not-change | APPEND-ONLY |
| `checklist.md` | Per-task checklist; check off as completed | Updated as work progresses |
| `SPRINT_INDEX.md` | High-level sprint progression with start/end dates and status | Updated at sprint boundaries |
| `session-end-prompt.md` | The template for end-of-session work (mirrors Taiwanese's version) | Static template |
| `RESUME.md` | Quick-access resume prompt for the next session | Updated at session end |
| `sprints/sN-name.md` | Per-sprint task tracking and session logs | Updated during the sprint |

Plus working artifacts:
- `STRATEGY_GUIDE.md` (if applicable — for a camera app, this might be replaced by the existing Taiwanese guide, referenced from there)
- Strategy code (will be ported V5 Lean rules in JS/TS)
- Image recognition models / training data

## 7. Initial Sprint Structure (proposed for Session 1 to refine)

| Sprint | Name | Phase | Goal |
|---|---|---|---|
| S0 | Foundation + decision | Phase 1: Setup | Make the Option A/B/C architectural call; pick stack; set up repo scaffolding; copy V5 Lean into the new repo as the reference strategy |
| S1 | Strategy engine port | Phase 2: Strategy | Port `strategy_v65` (or V5 Lean equivalent) to JS/TS. Unit-test against ground-truth EVs from the Taiwanese 50K grid |
| S2 | Image recognition (basic) | Phase 3: CV | Detect + classify 7 cards from a controlled photo (cards laid flat, no overlap). Confidence-gated UX |
| S3 | Integration + UX | Phase 4: App | Camera capture → recognition → confirmation → optimal-setting display |
| S4 | Edge cases + polish | Phase 5: Robustness | Lighting / rotation / partial-occlusion handling; correction-by-tap UI |
| S5 | History tracking (optional) | Phase 6: Analytics | If desired: track user's actual settings vs optimal, EV-loss aggregate, learning curve graph |

## 8. Open Questions for Session 1

1. **Architectural choice:** Option A (heuristic), B (lookup), or C (hybrid)?
2. **Stack:** React Native (leverages TaiwanAPP investment) or native iOS+Android?
3. **Card recognition model:** train custom, or use a pre-trained one from Roboflow / PlayingCards dataset?
4. **Offline-first?** (Default: yes. Server-side optional for future user-history features.)
5. **Repo location?** `/Users/michaelchang/CODE/taiwan-camera/` (sibling to `taiwanese/` and `TaiwanAPP/`)?
6. **Code-name?** TaiwanCam? TaiwanLearn? Something else?
7. **Does this replace, complement, or coexist with TaiwanAPP?** (TaiwanAPP is the multiplayer game; this is the trainer/recognition tool.)

---

## 9. What to Leverage from the Taiwanese Poker Solver Project

The Taiwanese project produced reusable artifacts directly applicable here:

| Artifact | Reuse path |
|---|---|
| **`strategy_v65_mid_pair_chain_extend.py`** | Port to JS/TS — this is the optimal-setting function |
| **`TEMP_PLAY_GUIDE_BY_SHAPE_V5_LEAN.md`** | The 10-rule reference for the strategy implementation |
| **`data/lookup_table.bin`** (5-card hand-rank table) | Reuse for any tie-breaking / hand-strength display |
| **`data/oracle_grid_50k.npz`** (50K random hands with EVs vs 4 profiles) | Unit-test ground truth for the ported strategy |
| **`analysis/scripts/mc_simulate_v4_*.py`** (MC simulator) | Future "backtest your decisions vs the simulator" feature |
| **`MEMORY.md`** entries: `project_taiwanese_stake.md`, `project_taiwanese_bankroll_hourly.md` | Carry forward the operator's preferences and economic context |

---

## 10. The Session 1 Resume Prompt (template — will be refined in Session 1)

```
Start the TaiwanCam project (codename TBD — operator to confirm).

Context: this is a NEW project building on the closed Taiwanese Poker Solver
project (CODE/taiwanese/, sessions 0-98). The vision document is at
/Users/michaelchang/CODE/taiwanese/CAMERA_APP_PROJECT_KICKOFF.md.

Session 1 goals:
1. Read the kickoff document end-to-end
2. Decide with the operator on the architectural choice (heuristic engine
   vs database lookup vs hybrid) — Section 3 of the kickoff doc
3. Decide stack (React Native leveraging TaiwanAPP, or native, or web)
4. Decide repo location + name; create the repo with the proposed
   documentation structure (CLAUDE.md, CURRENT_PHASE.md, DECISIONS_LOG.md,
   checklist.md, SPRINT_INDEX.md, session-end-prompt.md)
5. Define Sprint S0 (Foundation + Decision) with concrete tasks
6. Output a Session 2 resume prompt

Persistent directives (from Taiwanese project):
- User is non-technical; lead with plain-language framing
- "Speed is not necessary — clarity and perfection is."
- Session-end commit + push is pre-authorized
- This project is educational / strategy-test; NOT a cheating tool

Do not start writing code in Session 1. The deliverable is the decision +
documentation structure that allows Session 2 to begin development.
```

---

## 11. Memory note for Claude

When the new project starts:
1. Create a `project_taiwancam.md` memory entry pointing to the new repo
2. Carry forward `project_taiwanese_stake.md` and `project_taiwanese_bankroll_hourly.md` as relevant context (operator's home-game economics still apply to this project's evaluation criteria)
3. Add a `feedback_taiwancam_commits.md` if the operator wants commit-+-push every session (likely yes given Taiwanese precedent)

---

*This document is the bridge between the closed Taiwanese Poker Solver project and the new camera-app project. When the new project starts, this file can be moved to the new repo and renamed (`PROJECT_VISION.md` or similar) as the canonical kickoff record.*
