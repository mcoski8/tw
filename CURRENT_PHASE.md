# Current: Models 1+2+3 on Mac, Model 4 in progress; Sprint 5a trainer extended (profile + player-count selectors); skill-gap empirically quantified

> Updated: 2026-04-24 (end of Session 10)
> Previous sprint status: Session 09 built the Sprint 5a trainer foundation + cross-model join scaffolding. Session 10 downloaded Model 3, ran 3-way cross-model analysis, empirically settled the "is this game skill-driven?" question, scoped the heads-up vs multiway question as a Phase 2 priority, and scaffolded the trainer UI for multiway selection.

---

## Cloud production status (Sprint 3) — Models 1, 2, 3 DONE; Model 4 in progress

- **Model 1** `mfsuitaware_mixed90.bin` — DONE 2026-04-21. 6,009,159 records on Mac.
- **Model 2** `omahafirst_mixed90.bin` — DONE 2026-04-23. 6,009,159 records on Mac.
- **Model 3** `topdefensive_mixed90.bin` — DONE 2026-04-24 21:32 UTC. **Downloaded + validated this session**, mean EV +0.498 (between Model 1's +0.533 and Model 2's +2.123 — Top-Defensive is the second-strongest opponent of the three by raw exploitability).
- **Model 4** `randomweighted` — RUNNING. Auto-launched after Model 3 exit 0; at last check (2026-04-24 ~00:48 UTC) was at ~14% / 834,000 hands, ETA ~34.8 hours.
- **Projected full-project finish:** ~2026-04-26 ~08:30 UTC (1:30 AM PT Saturday).

---

## What was completed this session (Session 10)

### Cross-model 3-way analysis (with Models 1, 2, 3)
- 3-way unanimity dropped to **30.99%** (from 39.31% with 2 files).
- Pairwise agreement matrix revealed: **MiddleFirstSuitAware ↔ TopDefensive: 78.9%** — these two heuristic profiles are functionally similar in their effect on the optimal best-response. OmahaFirst is the outlier (~33% agreement with each of the other two). User reframed this as confirmation that strategies converge as players improve, not redundancy — the 21% disagreement zone is where SKILL matters and where the trainer should drill.
- Setting 104 dominates unanimous bucket at 31.28% (up from 28.6% with 2 models).
- 11.04% of hands had all 3 opponents picking different settings — those are the "highly opponent-dependent" hands.

### Setting 104 decoded
- Setting 104 = "highest card → top, next 2 → middle, lowest 4 → bottom" (the naive sort-and-slice). Optimal arrangement for **21% of all (hand × model) cells**, dominates unanimous bucket at 31%.
- Concrete: it's the most natural human heuristic, and it's right one-fifth of the time. The OTHER 79% is where the solver earns its keep.

### Skill-gap empirical analysis (**direct rebuttal to "this game is just luck"**)
- New script `analysis/scripts/skill_gap.py` — samples N canonical hands × P opponent profiles, runs MC for all 105 settings, reports the EV gap between optimal play and naive (setting 104) play.
- 100 hands × 3 profiles × 500 MC samples produced:
  - **Mean gap: +1.68 EV per hand** in favor of optimizer
  - Per-hand variability (sd of optimal EV across hands): 1.57
  - **Hands required for 2-sigma confidence in skill edge: ~3**
  - In 300 (hand × profile) trials, naive play was **never strictly better** than optimal — tied on a handful of "easy" hands, lost on the rest
- This is the empirical answer to the user's friends' "glorified coin flip" claim: the skill edge dwarfs variance after only a few hands. At $1/point, that's $168 of pure skill edge per 100 hands vs naive play.

### Socratic dialogue with Gemini 2.5 Pro on opponent-set design
- 3-turn substantive dialogue documenting:
  - Naive Sorter rejected as a production opponent (deterministic → no MC needed)
  - Hold'em Transplant rejected by user (his player population doesn't include this archetype — at his stake level, all opponents are competent at both Hold'em and PLO)
  - **Gambler (scoop-maximizer) accepted as future Phase 2 candidate** — the only archetype attacking the scoring structure rather than card valuations
  - Iterated Best Response acknowledged but rejected for this project — each round amplifies complexity, contradicting the trainer's learnable-rules goal
  - **CFR re-estimated**: not "months of compute" — Taiwanese Poker has no betting tree, so CFR on this game is a ONE-SHOT Bayesian decision problem. Realistic estimate: days, not months. Phase 3 candidate.

### Trainer UI extended
- Profile selector (4 production profiles): Middle-First Suit-Aware, Omaha-First, Top-Defensive, Random-Weighted
- Compare-across-all-profiles button + per-profile arrangement panel (mini tier layouts; "all 4 agree" banner when robust)
- **Player-count selector added**: heads-up (default), 3p, 4p, 5p. Currently informational — when user selects 3+, an amber banner appears explaining current scoring is heads-up-only and pointing them at the Compare button as the closest current proxy for multiway-robust play. Backend doesn't yet branch on this; the UI is scaffolded so Phase 2 multiway analysis can plug in cleanly.

### Multiway as Phase 2 data-driven priority (user-flagged as critical)
- User plays **mostly 3-5 player, sometimes heads-up** — and has explicit intuition that multiway should be played differently ("weaker top, stronger mid+bottom"). Strict ground rule: this question gets answered with **hard data**, not theory.
- Reasoning audit so far: scoop math compounds with more opponents (supports the intuition for stronger bottom) but per-opponent BR is independent and stronger competition argues for safer play (cuts against the "weaker top" piece). Net answer is empirical and Sprint 7 work.
- Tasks added to `checklist.md` Sprint 7 section: compute multiway-robust setting per canonical hand from N-way cross-model unanimity; quantify systematic top/mid/bot composition differences by player count; test the user's specific hypothesis with numbers; expose in trainer if confirmed.

---

## Files touched this session

**Added:**
- `analysis/scripts/skill_gap.py` — empirical skill-gap analysis tool

**Modified:**
- `trainer/static/index.html` — player-count selector + multiway info banner
- `trainer/static/style.css` — banner styling
- `trainer/static/app.js` — player-count state + change handler
- `checklist.md` — Sprint 7 multiway analysis tasks added
- `CURRENT_PHASE.md` — this file, rewritten

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt (next session — paused until Model 4 finishes)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md  (scan Decisions 028 + 029)
- handoff/MASTER_HANDOFF_01.md  (scan Sessions 09 + 10)
- analysis/scripts/skill_gap.py  (Session 10 skill-gap analysis tool)
- trainer/  (Sprint 5a foundation; player-count selector scaffolded for Phase 2)
- analysis/src/tw_analysis/cross_model.py  (Sprint 7 cross-model join)

Models 1, 2, 3 DONE and on Mac. Model 4 (randomweighted) was at ~14% with
~34h ETA at end of Session 10.

First-session-start tasks:
1. Pod status check. Single-line command (paste into RunPod web terminal):

   cd /workspace/tw && echo "=== Launcher ===" && tail -8 data/session06/production_launch.log && echo "" && echo "=== Model 4 (randomweighted) last 5 ===" && tail -5 data/session06/prod_randomweighted.log && echo "" && echo "=== Job running? ===" && (pgrep -af "tw-engine solve" || echo "Job stopped.") && echo "" && echo "=== Files ===" && ls -lh data/best_response/

2. If Model 4 is done, scp it to the Mac:
   scp -P 11400 root@205.196.19.130:/workspace/tw/data/best_response/randomweighted.bin /Users/michaelchang/Documents/claudecode/taiwanese/data/best_response_cloud/

3. After Model 4 download, validate:
   python3 analysis/scripts/inspect_br.py data/best_response_cloud/randomweighted.bin

4. When all 4 files are local: remind user to TERMINATE the RunPod pod.

5. Re-run cross-model join with all 4 files to get the true 4-way unanimity rate:
   python3 analysis/scripts/cross_model_join.py data/best_response_cloud/*.bin

6. Re-run skill_gap.py with all 4 profiles for the published number:
   python3 analysis/scripts/skill_gap.py --hands 500

7. Sprint 7 work formally unlocks. PRIORITIES IN ORDER:
   (a) MULTIWAY ANALYSIS — compute multiway-robust setting per canonical hand
       from 4-way cross-model unanimity. Quantify systematic differences in
       setting composition by player count. Test user's specific hypothesis
       ("weaker top, stronger mid+bot in multiway") with hard numbers.
   (b) Hand-feature extractor — pair count, top-rank, suitedness, connectivity.
   (c) Pattern mining toward 5-10 rule decision tree (user's stated rule budget).
   (d) Self-play "break-even against itself" Nash check on the resulting strategy.

USER PRIORITIES:
- 5-10 rules max. 100 rules is too many. Sprint 7 mining must compress.
- Multiway analysis is data-driven, not assumed. User explicit on this.
- HoldemTransplant rejected (not in user's player population).
- Gambler (scoop-maximizer) is the one Phase 2 opponent worth adding.
- CFR (Sprint 4 / Phase 3) revised down from "months" to "days" — interesting
  to user IF rule-based approach has gaps.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
