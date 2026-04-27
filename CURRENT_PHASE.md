# Current: Sprint 7 Phase C/C+ shipped — per-profile overlays + golden tests for v3 and overlays. Decision-tree extraction methodology agreed with Gemini 2.5 Pro; Phase D pipeline ready, blocked on macOS TCC permission glitch (transient).

> Updated: 2026-04-27 (end of Session 15)
> Previous sprint status: Session 14 finalized strategy_v3 at 56.16% multiway-robust shape-agreement and declared rule chain Phase-B-final at structural ceiling for opponent-agnostic 7-rule chain.

---

## Headline state at end of Session 15

| chain                      | overall multiway | vs MFSA | vs OmahaFirst | vs TopDef | vs RandWtd | rules |
|----------------------------|------------------|---------|---------------|-----------|------------|-------|
| **strategy_v3** (default)  | **56.16%**       | 55.51%  | 45.82%        | 46.12%    | 61.98%     | 7+2+1 |
| strategy_omaha_overlay     | 44.17%           | 43.57%  | **55.16%**    | 35.10%    | 47.49%     | 6     |
| strategy_topdef_overlay    | 53.76% (Phase C) → 57.34% (Phase C+) | 57.16%  | 38.92%        | **51.07%** | 59.75%     | 4     |

(Per-profile shape-agreement on 300K-hand random sample, rng seed 42.)

**Project goal reframed.** The published end product is a 5-10 rule chain matching the multiway-robust solver ≥95% of all 6M canonical hands. v3 is at 56.16% — 39pp short. Per-profile overlays were a tactical detour useful for the trainer; the GTO core is multiway-robust. **Session 16 starts with Phase D (decision-tree extraction).**

---

## What was completed this session (Session 15)

### Phase A — strategy_v3 golden tests (`d5ed9ff`)
- New file `analysis/scripts/test_strategy_v3_golden.py` — 13 tests (per-branch goldens × 9 dispatch branches, setting-104 layout sanity, 105-setting round-trip, v3≠v4 lockstep, 100-hand seed=42 SHA fixture).
- Locks current v3 behaviour as a regression gate.
- Negative-test verified: replacing strategy_v3 with strategy_v4 fires the lockstep + SHA tests.

### Phase C — Per-profile overlays (`a5df1d8`)
- **`strategy_omaha_overlay`** (5 rules) — 45.82% → 54.69% on br_omaha:
  - Single-pair → BOT when pair_rank ∈ {A, K, 2}; else MID (v3 default).
  - Two-pair: high pair → BOT when high_rank ≥ 13 OR both pairs in 10-12. Generalises v3's AAKK exception. premium+premium 73% bot/mid; premium+high 95%; high+high 74%.
  - High_only: re-tune `_hi_only_pick` weights — bot DS +5→+8, rundown ≥4 +2→+4.
- **`strategy_topdef_overlay`** (1 rule mod) — 46.12% → 50.14% on br_topdef:
  - `_topdef_top_pick`: top = highest singleton iff rank ≥ Q (12), else LOWEST singleton.
  - Threshold tuned: ≥ 13 caused -13.2pp regression on Q-singleton bucket; ≥ 12 captures Q without sacrifice.
  - Applied ONLY to single-pair and high_only branches; quads/trips/two_pair use v3 (initial scope caused -10pp regressions there).
- **`strategy_for_profile(hand, profile)`** dispatcher.
- `trainer/src/explain.py`: profile-aware. New `CHAIN_AGREEMENT_BY_PROFILE` table; `_chain_arrangement(hand, profile_id)` routes to right chain; `build_feedback(..., profile_id)` accepts the active profile.
- 7 overlay golden tests in `analysis/scripts/test_overlays_golden.py`.

### Phase C+ — Residual rules (`5a815ce`)
Targeted residual mining surfaced two additional rules:
- **OmahaFirst three_pair premium-flip**: when high_pair ≥ 13, high → BOT, mid_pair → MID. Lifted three_pair 29.96% → 54.14% (+24.18pp on category, +0.47pp overall). Generalises premium-flip principle to three_pair.
- **TopDef premium-trips break-down**: when trip_rank ≥ 13, top = ONE trip card, mid = TWO trip cards (instead of v3's trips→mid+1bot). Mining: 86% modal on premium trips. Applied to pure trips and trips_pair branches. Lifted trips 49.51% → 59.49%, trips_pair 40.41% → 51.59%.
- **TopDef AAKK reverse**: removed v3's KK→MID exception; AAKK falls through to default high→MID (TopDef's modal answer at 48% vs v3's bot/mid 30%).

### Phase D scoping — Methodology Socratic with Gemini 2.5 Pro (no commit)
- Multi-turn dialog (continuation `97707ec2-1603-44d2-a534-236caa6e92a2`).
- Decided: sklearn `DecisionTreeClassifier` on (hand_features, multiway_robust_setting), scored by shape-equivalence. Target = setting_index (105 classes), NOT shape-tuple (254K classes — would explode).
- Engineered 6 boolean feasibility features: `can_make_ds_bot`, `can_make_4run`, `has_high_pair`, `has_low_pair`, `has_premium_pair`, `has_ace_singleton`, `has_king_singleton`.
- 27-feature input vector ready; full 6M target shape pre-computed in 27s.
- Pipeline: 3-fold CV on 1M subsample for depth selection {3, 5, 7, 10, 15, 20, None} → full-6M fit at chosen depth → `export_text` → translate to Python → byte-identical parity check → EV-loss backtest on 5-10K sample × 4 profiles × 1000 MC.

### Phase D execution — BLOCKED (macOS TCC glitch)
- `analysis/scripts/dt_phase1.py` written and saved.
- First run via my Bash tool: ran for ~1 minute, started CV training, was SIGKILL'd mid-run by user interrupt (Exit code 137).
- After SIGKILL: macOS `tccd` got into stuck state. ALL access to `~/Documents/claudecode/taiwanese/` from python3 (and intermittently from `ls`/`cat`) returned `PermissionError: [Errno 1] Operation not permitted` from BOTH my Bash sandbox AND the user's own Terminal.
- Diagnosis: SIGKILL'd Python child process leaked TCC tokens; classic Apple `tccd` cache poisoning bug.
- Fix path: user toggled python3.13 + Terminal in System Settings → Privacy & Security → App Management. Quit Terminal completely (Cmd+Q) → reopen → permissions restored.

---

## Files touched this session

**Added:**
- `analysis/scripts/test_strategy_v3_golden.py` — 13 v3 golden tests
- `analysis/scripts/test_overlays_golden.py` — 8 overlay golden tests (including v3-divergence assertions)
- `analysis/scripts/dt_phase1.py` — Phase D ceiling-curve script (NOT YET RUN due to TCC glitch)

**Modified:**
- `analysis/scripts/encode_rules.py` — added `_hi_only_pick_omaha`, `_topdef_top_pick`, `_hi_only_pick_topdef`, `strategy_omaha_overlay`, `strategy_topdef_overlay`, `strategy_for_profile`, `PROFILE_TO_STRATEGY`, plus three_pair premium-flip and topdef premium-trips break-down rules.
- `trainer/app.py` — passes `profile_id` to `build_feedback`.
- `trainer/src/explain.py` — `CHAIN_AGREEMENT_BY_PROFILE` per-profile table; `_chain_arrangement(hand, profile_id)`; `build_feedback(..., profile_id)`.

**Verified end-to-end:**
- All 74 Python tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).
- `cargo build --release` clean (no Rust changes).
- 3 commits this session: `d5ed9ff`, `a5df1d8`, `5a815ce`.

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md` (Session 15 entry to be appended in this session-end)

---

## Resume Prompt (next session)

```
Resume Session 16 of the Taiwanese Poker Solver project.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md  (latest entry: Session 15 methodology decision)
- handoff/MASTER_HANDOFF_01.md  (scan Sessions 13-15)
- analysis/scripts/encode_rules.py  (current rule chain — 9 strategies including overlays)
- analysis/scripts/dt_phase1.py     (Phase D ceiling-curve script — NOT YET RUN)
- analysis/scripts/test_strategy_v3_golden.py
- analysis/scripts/test_overlays_golden.py

State of the project (end of Session 15):
- Production rule chain = `strategy_v3` (56.16% multiway-robust shape-agreement on 6M).
- Per-profile overlays shipped (omaha_overlay 54.69% vs br_omaha;
  topdef_overlay 50.14% vs br_topdef).
- Trainer is profile-aware via strategy_for_profile dispatcher.
- All goldens locked. 74 python tests + 124 rust tests green.
- Project goal: 5-10 rule chain at ≥95% multiway-robust shape-agreement
  on 6M canonical hands. v3 is 39pp short.

Methodology agreed with Gemini 2.5 Pro for Phase D:
1. ESTABLISH CEILING: train sklearn DecisionTreeClassifier on
   (27 hand_features, multiway_robust setting_index) at depths
   {3, 5, 7, 10, 15, 20, None}. 3-fold CV on 1M subsample for depth
   selection; full 6M fit for final reporting. Score by shape-equivalence.
2. PICK BUDGET: choose depth at the agreement-curve knee within "human
   memorizable" (5-10 rules ≈ depth 4-7).
3. EXTRACT: sklearn export_text → translate to Python if/elif → verify
   byte-identical predictions across all 6M.
4. EV BACKTEST: 5-10K random hands × 4 profiles × 1000 MC samples;
   compute mean EV-loss = (BR_ev - chain_ev) per profile; compare v3,
   overlays, learned tree.
5. SHIP: strategy_v5_dt in encode_rules.py; golden tests; markdown export.

IMMEDIATE NEXT ACTION: run `python3 analysis/scripts/dt_phase1.py` from
the project root. Output is a 7-row depth-vs-agreement table:
  depth  leaves   cv_acc  cv_shape  full_acc  full_shape  fit_s
The unbounded (None) depth is the structural ceiling for our feature set.
This determines whether the 95% target is reachable.

Was BLOCKED last session by macOS TCC permission glitch (transient,
caused by SIGKILL during heavy compute). User toggled python3 + Terminal
in System Settings → Privacy & Security → App Management and Cmd+Q'd
Terminal between sessions, which restored access.

PRIORITY FROM USER:
- The METHOD must be testable, repeatable, and provable.
- EV/$ backtest across 6M hands is the ground-truth metric (shape-
  agreement is the cheap proxy used for training).
- Don't iterate by hand-engineering rules — let the data speak.
- 5-10 rule budget; tree depth 4-7 is the sweet spot.
- Use SHAPE agreement, NOT literal setting_index.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
