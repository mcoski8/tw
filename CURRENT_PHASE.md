# Current: Sprint 8 — Session 79 label-noise measurement returned MIXED verdict; pre-committed shift-based criterion has a blind spot for v44's overfit-to-N=200-noise mode (oracle self-disagreement 32%, MATCH bucket loses 21.9pp, NOISE bucket gains 43.6pp); **S80 runs M2 (parallel A1 + C2 one-session experiments) to disambiguate label noise from memorization before committing to A-path or C-path for the next 3-5 sessions**

S78's NULL closed the single-model ML feature-engineering track at v44's saturating regime. S79 was a one-session measurement to decide between A-path (better labels via N=1000) and C-path (higher-capacity model) for the next 3-5 sessions of compute investment.

S79 ran `analysis/scripts/label_noise_measurement_S79.py` end-to-end on the existing 500K N=1000 prefix grid (FREE compute, no new oracle sampling — 68.8s wall, 7,263 hands/s). For each prefix hand it computed v44's pick, the N=200 argmax (from the full grid at the same canonical_id), the N=1000 argmax (from the prefix grid), the match flags, and the regret distributions.

**Headline numbers:**

| Metric | N=200 | N=1000 | Δ |
|---|---:|---:|---:|
| v44 match rate | 72.98% | 67.05% | **−5.93pp** |
| v44 mean regret | $703/1000h | $686/1000h | −$17 |
| Oracle self-agreement (N=200 argmax == N=1000 argmax) | — | — | **68.00%** |

**The criterion has a blind spot:** it was designed under the implicit assumption that match-rate shift cleanly indicates label-noise impact. The data refutes that assumption. Oracle self-disagreement of **32%** says labels are *not* stable. Bucket-level decomposition (S76 setting-rank lens) shows the MATCH bucket loses 21.9pp at N=1000 (v44 had memorized N=200 noise) while the NOISE bucket gains +43.6pp (most of v44's "rank 2-3" leak at N=200 was just label noise). Per-category, two_pair (−13.7pp) and trips_pair (−19.4pp) are most-overfit; pair (+2.1pp) and three_pair (+1.6pp) are least-overfit — meaning S77/S78's pair-focused feature work was in the *wrong* category for the memorization story.

**Mechanical verdict (script output): C_PATH** (shift < +2pp).
**Honest verdict (this writeup, per S79 directive's MIXED clause): MIXED.** The criterion cannot discriminate the label-noise-plus-memorization mode the data actually shows. Per the directive ("surface options; do NOT pre-commit"), the A/C/M decision is deferred to a measurement comparison in S80.

**Decision 114 (S79): MIXED verdict + criterion blind spot + S80 = M2 (parallel A1 + C2 one-session experiments).**

> **🎯 IMMEDIATE NEXT ACTION (Session 80): M2 — Run A1 and C2 one-session experiments in parallel to disambiguate label noise from memorization**
>
> Two ~30-min retrain experiments at the v44-architecture baseline (depth=36, ml=1, sklearn DecisionTreeClassifier, 4.8M canonical-hand training rows). Both grade against BOTH the N=200 full grid AND the N=1000 prefix grid. Same code path for both — the only knobs are train-labels and capacity.
>
> 1. **(PHASE 1 — ~5 min)** Confirm S79 outputs are committed & pushed; read `SESSION_79_LABEL_NOISE_REPORT.md` and `DECISIONS_LOG.md` Decision 114 for the M2 setup.
>
> 2. **(PHASE 2 — ~30 min, A1 experiment)** Write `analysis/scripts/train_v49_a1_dt.py`. Same training pipeline as `train_v44_dt.py`/`train_v48_dt.py`. ONE change: for the first 500K canonical hands (those that have N=1000 labels in `data/oracle_grid_prefix500k_n1000.bin`), use the N=1000 argmax as the training label instead of the N=200 argmax. For the remaining 4.3M hands, use N=200 labels as before. Train at depth=36, ml=1 (v44's hyperparams).
>
> 3. **(PHASE 3 — ~30 min, C2 experiment)** Write `analysis/scripts/train_v49_c2_dt.py`. Same training pipeline. ONE change vs v44: regularize. Set `max_leaf_nodes=500_000` (vs v44's effective ~2.25M) AND `min_samples_leaf=5` (vs v44's `1`). Training labels = N=200 (unchanged). Train at the same depth=36 cap.
>
> 4. **(PHASE 4 — ~15 min, grade both)** Write `analysis/scripts/grade_v49_experiments.py` that grades v44_dt (baseline), v49_a1_dt, v49_c2_dt against:
>    * The N=200 full grid (existing $/1000h regret metric)
>    * The N=1000 prefix grid (match rate AND regret)
>    Produce a 3-column table. Report whether match rate vs N=1000 lifts above v44's 67.05% for either or both.
>
> 5. **(PHASE 5 — ~15 min)** Decision matrix:
>    * **Both A1 and C2 lift N=1000 match rate** → S81 plans M1 hybrid: regularized DT trained on N=1000 labels for the prefix subset.
>    * **Only A1 lifts** → label noise is dominant → S81 plans A2 (targeted N=1000 expansion on two_pair + trips_pair, ~24-36 hr local compute).
>    * **Only C2 lifts** → memorization is dominant → S81 plans C1 (high-capacity well-regularized boosting at depth=10-12, n_est=1000-2000, ~3-6 hr compute).
>    * **Neither lifts** → 95% headline-goal recalibration: the 32% oracle self-disagreement may imply the goal is unattainable against any noisy oracle. Surface to user before committing more compute.
>
> 6. **(PHASE 6 — ~10 min)** Decision 115; `SESSION_80_M2_REPORT.md`; CURRENT_PHASE.md rewrite for S81 with the chosen path's concrete plan.
>
> ACCEPTANCE for Session 80:
> - `train_v49_a1_dt.py` runs end-to-end, produces `data/v49_a1_dt_model.npz`.
> - `train_v49_c2_dt.py` runs end-to-end, produces `data/v49_c2_dt_model.npz`.
> - `grade_v49_experiments.py` produces a 3-column comparison table (v44 / v49_a1 / v49_c2) against both grids.
> - Decision matrix declared per S80 Phase 5.
> - DECISIONS_LOG.md updated with Decision 115.
> - CURRENT_PHASE.md rewritten for S81 with concrete plan for whichever lever moved the needle.
>
> **+$10 ship bar STILL HOLDS for any future ship decisions.** S80 is a *measurement* session like S79 — it does NOT attempt a ship. The output is a sharper picture of where the 35pp gap to 95% match rate actually lives.
>
> **📓 METHODOLOGY (Session 80+):**
>
> 1. **Trust the bucket pattern over the headline number.** S79's overall shift was a small negative number that the mechanical criterion classified as C-PATH; the bucket-level signature (MATCH −22pp, NOISE +44pp) is what made the memorization story legible. Apply this lens to S80's experiments — don't read the single match-rate number; decompose by bucket and category.
>
> 2. **Target where the memorization is concentrated.** Two_pair and trips_pair show the largest negative shifts (−13.7pp, −19.4pp). Any future targeted N=1000 expansion or category-specific intervention should start there, not in pair (where v44 is already noise-stable).
>
> 3. **Free-compute moves first.** S79 was 69s of CPU on already-existing data. S80's experiments are ~1 hour total. The cluster-heavy A3 option (full 6M N=1000 grid, ~5 days) stays in reserve until S80 + S81 confirm the lever before committing serious compute.
>
> 4. **No ship attempt this session.** S80 is the second consecutive measurement-only session. The +$10 ship bar applies the moment any S81+ candidate strategy gets graded against the production v44_dt + v56_trips_hybrid stack. For S80 itself the question is "which lever moves match rate against N=1000 labels," not "does this ship."
>
> 5. **"Speed is not necessary — clarity and perfection is."** Both A1 and C2 experiments should run with the v44 training script as the template; do NOT introduce new feature engineering, NEW hyperparams beyond what S79 specified, or new architecture. The cleanest one-knob-at-a-time experimental design is the goal.
>
> 6. **Pre-commit the decision matrix BEFORE running the experiments.** S79's lesson was that the criterion has to anticipate all signs of the metric. The S80 decision matrix above pre-commits an interpretation for each of the four outcomes (both lift / only A1 / only C2 / neither). Stick to it; if a fifth outcome shows up, document it as a criterion-extension question for the user before improvising.
>
> 7. **The 65%-vs-95% gap framing is the operative goal — but the goal itself may need recalibration.** S79 revealed that N=200's own argmax is only 68% stable against N=1000. If the oracle is intrinsically noisy, 95% may not be a reachable target against ANY noisy oracle. If S80 returns "neither lever lifts", treat that as evidence to renegotiate the headline metric with the user, not as evidence that further investment is pointless.

> **✅ ARTIFACTS produced in S79:**
> 1. `analysis/scripts/label_noise_measurement_S79.py` — measurement script (500K hands × 2 grids in 69s wall).
> 2. `data/label_noise_S79_summary.json` — full summary breakdown (4.4 KB, gitignored per project convention).
> 3. `data/session79/label_noise_measurement_full.log` — full sweep log (gitignored).
> 4. `SESSION_79_LABEL_NOISE_REPORT.md` — Phase 1-5 report including plain-language TL;DR for non-technical user.
> 5. `DECISIONS_LOG.md` — Decision 114 (S79 MIXED verdict + criterion blind spot + S80 M2 plan).
> 6. `CURRENT_PHASE.md` — rewritten for S80 (this file).

> Updated: 2026-05-13 (Session 79 end — label-noise measurement diagnostic completed in 69s wall; pre-committed shift-based criterion read mechanically as C-PATH on shift = −5.93pp but the criterion's underlying assumption is refuted by 32% oracle self-disagreement and 21.9pp MATCH-bucket loss showing v44 is overfit to N=200 noise rather than measuring stable labels; honest verdict is MIXED per S79 directive's MIXED clause. **No production state change in S79 — eighth consecutive UNCHANGED session.** S80 plan: M2 = run A1 (retrain on N=1000 prefix labels) and C2 (regularize: max_leaf_nodes=500K, min_samples_leaf=5) as parallel one-session experiments; grade vs BOTH N=200 and N=1000 oracles; the 4-cell decision matrix in Phase 5 above chooses between A2 / C1 / M1 / headline-goal recalibration for S81.)

---

## Headline state at end of Session 79

**Strategies of record (UNCHANGED for the EIGHTH consecutive session):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion. $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S79 — pure measurement session; no model trained).

**S79 summary table:**

| Metric | Value | Notes |
|---|---:|---|
| Hands swept | 500,000 | First 500K canonical IDs (shared between prefix N=1000 and full N=200 grids) |
| Wall time | 68.8s | 7,263 hands/s |
| v44 match rate vs N=200 | 72.98% | Production-baseline lens |
| v44 match rate vs N=1000 | **67.05%** | **−5.93pp shift** |
| Oracle self-agreement (N=200 vs N=1000 argmax) | **68.00%** | **32% disagreement — labels not stable** |
| v44 regret vs N=200 | $703/1000h | — |
| v44 regret vs N=1000 | $686/1000h | $-17/1000h |
| MATCH bucket shift | **−21.89pp** | v44 was memorizing N=200 noise |
| NOISE bucket shift | **+43.58pp** | Most of v44's rank 2-3 "leak" was just label noise |
| two_pair category shift | **−13.69pp** | Most-overfit large category |
| trips_pair category shift | **−19.43pp** | Most-overfit overall |
| pair category shift | +2.10pp | Least-overfit (S77/S78 invested here — wrong category) |

---

## Hypothesis cascade status (updated after S79)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | **FORMALLY CLOSED (Decision 113).** |
| **S79 label-noise measurement** | Existing N=1000 prefix vs N=200 full | **MIXED — 32% oracle disagreement reveals criterion blind spot; M2 deferred to S80.** |
| **A1 (S80)** | Retrain v44 DT on N=1000 prefix labels (N=200 elsewhere) | **PRIORITIZED — one-session experiment.** |
| **C2 (S80)** | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | **PRIORITIZED — one-session experiment.** |
| A2 | Targeted N=1000 expansion on two_pair + trips_pair | Standby for S81 if A1 lifts. |
| A3 | Full 6M-hand N=1000 grid | Heavy compute; reserve. |
| C1 | High-capacity boosting (depth=10-12, n_est=1000-2000) | Standby for S81 if C2 lifts. |
| M1 | Hybrid: regularized DT trained on N=1000 prefix labels | Standby for S81 if both A1+C2 lift. |
| Option D | Rule-chain extension on S77 LOW pair findings | Latent — pair is the LEAST-overfit category; deprioritize. |

**Cascade verdict (updated post S79):** Single-model feature-engineering track stays CLOSED. Label-noise problem is empirically confirmed (32% oracle self-disagreement) AND v44 memorization is empirically confirmed (MATCH bucket loses 21.9pp at N=1000). S80 disambiguates which lever (better labels / regularization / both) moves the N=1000 match rate.

---

## Resume Prompt (Session 80 — M2: parallel A1 + C2 one-session experiments)

```
Resume Session 80 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S79 — S80 runs M2: parallel A1 + C2
  one-session experiments to disambiguate label noise from memorization)
- SESSION_79_LABEL_NOISE_REPORT.md (S79 label-noise measurement; MIXED
  verdict; criterion blind spot for v44 overfitting to N=200 noise)
- DECISIONS_LOG.md (latest: Decision 114 — S79 MIXED + S80 M2 plan)
- analysis/scripts/train_v44_dt.py (template for the v44-class DT
  training pipeline that both v49_a1 and v49_c2 will fork from)
- analysis/scripts/grade_v44_dt.py (template for grading against
  both grids)
- analysis/scripts/label_noise_measurement_S79.py (the S79 sweep —
  worth re-reading the bucket/category breakdown logic for the S80
  grader)

KEY DATA FILES (UNCHANGED from S79):
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/canonical_hands.bin — 6M canonical 7-card hands
- data/v44_dt_model.npz — production ML champion (baseline)
- data/label_noise_S79_summary.json — S79 results to compare against

STATE (end of S79):
- v44_dt match rate vs N=200: 72.98%
- v44_dt match rate vs N=1000: 67.05% (−5.93pp shift)
- Oracle self-agreement N=200 vs N=1000 argmax: 68.00% (32% disagreement)
- MATCH bucket loses 21.89pp at N=1000 (v44 memorizing N=200 noise)
- NOISE bucket gains 43.58pp at N=1000 (v44's "leak" was partly mislabeled)
- two_pair shift −13.69pp; trips_pair shift −19.43pp (most-overfit categories)
- pair shift +2.10pp (least-overfit; S77/S78 invested in wrong category)
- Production: v56_trips_hybrid ($1,429 full / $794 prefix) + v44_dt
  ($1,081 full / $686 prefix). UNCHANGED for eighth consecutive session.
- Single-model ML feature-engineering track formally CLOSED (Decision 113).
- S79 verdict: MIXED (Decision 114). Criterion blind spot for negative-shift
  case where v44 overfit to N=200 noise.

USER DIRECTIVE (S79 end-of-session — primary driver of S80):
- "Speed is not necessary — clarity and perfection is."
- The +$10 ship bar still holds for future ship decisions; S80 itself
  is measurement-only.
- Continue the A-path vs C-path discrimination one more session before
  committing to N=1000 expansion or higher-capacity boosting.

DIRECTION FOR SESSION 80 — M2: parallel A1 + C2 one-session experiments
to disambiguate label noise from memorization:

  PHASE 1 (S80 ~5 min) — Confirm S79 commit/push state; read S79 report
    + Decision 114 + label_noise_measurement_S79.py.

  PHASE 2 (S80 ~30 min) — A1 experiment.
    Write analysis/scripts/train_v49_a1_dt.py.
    Same pipeline as train_v44_dt.py. ONE change:
      for the first 500K canonical hands (those with N=1000 labels in
      data/oracle_grid_prefix500k_n1000.bin), use the N=1000 argmax as
      the training label.
      For the remaining 4.3M hands, use the N=200 argmax (unchanged).
    Hyperparams identical to v44: depth=36, min_samples_leaf=1.
    Output: data/v49_a1_dt_model.npz.

  PHASE 3 (S80 ~30 min) — C2 experiment.
    Write analysis/scripts/train_v49_c2_dt.py.
    Same pipeline. ONE change vs v44:
      max_leaf_nodes=500_000 (vs v44's effective 2.25M)
      min_samples_leaf=5 (vs v44's 1)
    Training labels = N=200 (unchanged from v44).
    Hyperparams: depth=36 (same cap as v44).
    Output: data/v49_c2_dt_model.npz.

  PHASE 4 (S80 ~15 min) — Grade both.
    Write analysis/scripts/grade_v49_experiments.py.
    For each of v44_dt (baseline), v49_a1_dt, v49_c2_dt:
      - Grade vs N=200 full grid (production-baseline regret/match)
      - Grade vs N=1000 prefix grid (match rate AND regret)
    Produce a 3-column comparison table. Bucket + category breakdown
    via the same lens as S79.

  PHASE 5 (S80 ~15 min) — Decision matrix:
    Threshold for "lifts": N=1000 match rate ≥ 70% (3pp above v44's 67.05%).
    - Both A1 AND C2 lift → S81 plans M1 hybrid.
    - Only A1 lifts → S81 plans A2 (targeted N=1000 on two_pair + trips_pair).
    - Only C2 lifts → S81 plans C1 (high-capacity boosting).
    - Neither lifts → headline-goal recalibration; surface to user.

  PHASE 6 (S80 ~10 min) — Decision 115; SESSION_80_M2_REPORT.md;
  CURRENT_PHASE.md rewritten for S81 with chosen path's concrete plan.

  ACCEPTANCE for Session 80:
  - train_v49_a1_dt.py runs end-to-end; v49_a1_dt_model.npz produced.
  - train_v49_c2_dt.py runs end-to-end; v49_c2_dt_model.npz produced.
  - grade_v49_experiments.py produces 3-column table across both grids.
  - Decision matrix declared per S80 Phase 5 (pre-committed thresholds).
  - Decision 115 documented.
  - CURRENT_PHASE.md rewritten for S81 with concrete plan.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- v44_dt model + features remain unchanged.
- This session is MEASUREMENT, not ship. The +$10 ship bar does not
  apply; the question is "which lever moves N=1000 match rate".
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; the session report should open with a
  plain-language summary of the decision-matrix outcome.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
