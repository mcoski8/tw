# Current: All 4 production .bin files local + verified; Sprint 3 cloud production COMPLETE; Sprint 7 unblocked and first-pass results published

> Updated: 2026-04-26 (end of Session 11)
> Previous sprint status: Session 10 downloaded Models 1-3, ran 3-way cross-model, ran skill-gap on 3 profiles, scaffolded multiway UI. Session 11 finished the cloud project: pulled Model 4, terminated the pod, ran the full 4-way cross-model + 4-profile skill-gap, and shipped the first multiway-robust analysis answering the user's "weaker top, stronger mid+bot" hypothesis with data.

---

## Cloud production status (Sprint 3) — **COMPLETE**

- All 4 best-response files on Mac at `data/best_response_cloud/`. Each 54,082,463 bytes, 6,009,159 records, validation PASS.
- RunPod pod `0f8279f6fd0a` TERMINATED (not Stopped). Compute billing halted.
- Network volume `tw-solver-data` decision: user retained briefly; can be deleted any time once trainer use confirms .bin integrity in production.
- Total project compute time: ~6.9 days, ~$159 spent, ~$3+ residual credit.

| Profile | File | Mean EV | Setting 104 share |
|---|---|---|---|
| MiddleFirstSuitAware mixed90 | `mfsuitaware_mixed90.bin` | +0.533 | 19.70% |
| OmahaFirst mixed90 | `omahafirst_mixed90.bin` | +2.123 | 22.72% |
| TopDefensive mixed90 | `topdefensive_mixed90.bin` | +0.498 | 21.79% |
| RandomWeighted | `randomweighted.bin` | +1.547 | 16.26% |

Mean EV ranking: TopDef is the strongest opponent (lowest EV for us); OmahaFirst is the weakest (most exploitable).

---

## What was completed this session (Session 11)

### Model 4 download + full 4-way cross-model

- scp + inspect_br.py validation — clean, all expected fields decoded.
- Cross-model join with all 4 .bin files: **26.68% unanimity** (down from 30.99% with 3 models).
- Distinct-settings histogram: 26.68% unanimous, 49.96% have 2 distincts, 20.64% have 3, **2.71% have all 4 distinct (highly opponent-dependent)**.
- Pairwise agreement matrix confirmed **OmahaFirst is the structural outlier** — 33-43% with the others, vs 58-79% among the rest. The other three (MF-SA, TopDef, RandomWeighted) cluster together.

### Skill-gap analysis at production scale (definitive answer to "is this game just luck?")

- N=500 hands × 4 profiles × 1000 MC samples each = 2,000 trials.
- **Cross-profile mean gap: +1.538 EV per hand** in favor of optimizer over naive (setting 104 = highest-card-top + next-2-mid + lowest-4-bot).
- Per-hand variability: 1.66 EV. Hands-to-2σ confidence in skill edge: **~5**.
- **Naive play strictly beat optimal in 0 of 2,000 trials.** Tied on a few easy hands; lost on the rest.
- At $1/point, that's **+$153.80 of pure skill edge per 100 hands** vs naive play. Empirical rebuttal to "Taiwanese Poker is a glorified coin flip."
- `analysis/scripts/skill_gap.py` — filter previously hardcoded to 3 profiles; updated to all 4.

### Multiway analysis — first-pass empirical answer to user's hypothesis

- New script `analysis/scripts/multiway_analysis.py` — computes multiway-robust setting per canonical hand as the MODE of the 4 per-profile best-responses, then compares feature distributions (top rank, mid pair %, mid rank-sum, bot double-suited %, bot rank-sum) between multiway-robust and the average heads-up BR.
- 200K-hand sample. Agreement-class breakdown:
  - Unanimous: 26.6%
  - 3-of-4: 40.4%
  - 2-of-4 (2-1-1): 20.6%
  - 2-2 split: 9.6%
  - All distinct (1-1-1-1): 2.7%
  - **67% of hands have a clear majority answer** (unanimous + 3-of-4); 12.3% are genuinely contested.
- **Hypothesis test (user's "weaker top, stronger mid+bot in multiway"):**
  - Δ top rank: **−0.18** (lower in multiway) → SUPPORTS "weaker top"
  - Δ mid pair rate: **+2.2 pp** → SUPPORTS "stronger mid"
  - Δ mid rank-sum: +0.22 → supports stronger mid
  - Δ bot DS rate: **+1.2 pp** (more often double-suited) → SUPPORTS "stronger bot (structurally)"
  - Δ bot rank-sum: −0.04 → bot is NOT higher-ranked, just better-coordinated
  - **4 of 5 axes directionally consistent with intuition.** Wrong on bot-rank, right on bot-structure.
- **Unanimous-only subset (the cleanest signal): mid pair rate jumps to 90.5%, bot DS rate to 45.8%, top rank UP at 12.65** — when robust play is unambiguous, the structural rule is "high card top, pair middle, double-suited bottom." Same direction as setting 104 but more disciplined.

---

## Files touched this session

**Added:**
- `data/best_response_cloud/randomweighted.bin` (52 MB, gitignored)
- `analysis/scripts/multiway_analysis.py` — Sprint 7 multiway hypothesis test

**Modified:**
- `analysis/scripts/skill_gap.py` — filter expanded from 3 profiles to all 4
- `checklist.md` — Sprint 7 multiway analysis tasks marked complete with measured outcomes
- `CURRENT_PHASE.md` — this file (rewritten)
- `handoff/MASTER_HANDOFF_01.md` — Session 11 entry appended
- `DECISIONS_LOG.md` — Decision 030 appended (multiway-robust = mode methodology)

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt (next session — Sprint 7 rule mining proper)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md  (scan Decisions 028, 029, 030)
- handoff/MASTER_HANDOFF_01.md  (scan Sessions 09, 10, 11)
- analysis/scripts/skill_gap.py + multiway_analysis.py (Session 11 outputs)
- trainer/  (Sprint 5a foundation; player-count selector scaffolded)
- analysis/src/tw_analysis/cross_model.py  (Sprint 7 cross-model join)

State of the project:
- All 4 production .bin files on Mac at data/best_response_cloud/. Pod terminated.
- Cloud production COMPLETE. Total ~6.9 days, ~$159 spent.
- Skill-gap: optimizer +1.538 EV/hand vs naive across 4 profiles; naive strictly
  better on 0 of 2000 trials. Game is provably skill-driven, not luck.
- Multiway hypothesis test: user's "weaker top, stronger mid+bot" intuition
  empirically supported on 4 of 5 axes (top rank −0.18, mid pair +2.2pp,
  bot DS +1.2pp; bot rank-sum essentially zero — wrong on rank, right on
  structure).
- Cross-model 4-way: 26.68% unanimous, 67% clear-majority, OmahaFirst is
  the structural outlier.

Sprint 7 PRIORITIES IN ORDER:

1. **Hand feature extractor** — build `tw_analysis/features.py` that turns a
   canonical 7-card hand into a feature vector: pair count + ranks, top-card
   rank, suitedness profile, connectivity, hand category (pair / two-pair /
   trips / quads / flush-potential / straight-potential / high-card-only).
   Join to per-profile BR settings + multiway-robust setting. Output a
   Parquet/SQLite file for fast queries.

2. **Pattern mining toward 5-10 rule decision tree** (user's stated rule
   budget). Look for compressible patterns. Examples to test empirically:
     - "If you have a pair of 9+, put it in middle" — true for what %?
     - "If a double-suited bottom is achievable, take it" — what % robust?
     - "Top is the highest single card" — when does that fail?
     - "When in doubt, sort and slice (setting 104)" — when does that win?
   Each candidate rule: measure agreement % with multiway-robust on 6M hands.

3. **Self-play break-even Nash check** — once a candidate rule set is in
   place, encode it as a strategy function. Simulate (rule_strategy vs
   rule_strategy) for 100k hands. Mean EV should be ≈ 0; deviation from 0
   measures distance from Nash. Single-script, ~150 lines.

4. **Trainer integration** — once rules are confident, swap trainer/src/explain.py
   from hand-written heuristics to the mined rule set. Add a "current rule
   firing" view to the trainer ("you violated rule 3 — pair to middle").

PRIORITY FROM USER:
- 5-10 rules max. 100 too many. Compression is non-negotiable.
- Multiway analysis was Sprint 7 P1 — first pass done, follow-up is full-6M
  re-run + scoop-frequency-by-player-count question.
- HoldemTransplant rejected. Gambler is the one Phase 2 opponent worth adding.
- CFR (Phase 3) revised to "days, not months" — interesting if rules approach
  has gaps.

Suggested starting point for next session: build features.py + Parquet export,
then iteratively test rule candidates against multiway-robust mode setting.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
