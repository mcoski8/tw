# Current: Sprint 8 — Session 73 v46b_dt PARTIAL POSITIVE / NULL ship at depth=36 ml=1

S72 v46_dt at depth=32 ml=3 was NULL by −$256/1000h full. S73 retried
the same 2 ho_v6 SS+ms features at v44's saturating regime
(**depth=36 ml=1**), isolating feature effect from regime effect.

**Result: PARTIAL POSITIVE / NULL ship.** v46b lifts v44 by
**+$5/1000h full** (below the +$10 ship threshold). The within-cat
high_only delta is −$24/1000h better with surgical gating
**byte-identical to v44 on 7 of 8 categories**. The $261/1000h swing
from v46 (−$256) → v46b (+$5) is **entirely attributable to the
hyperparameter regime change** — empirically confirms the S72
regime-confound theory and the S72 methodology #3 byte-identity
prediction word-for-word.

Decision 108: **NULL ship per +$10 threshold** (user-confirmed). v44_dt
remains ML champion; v56_trips_hybrid remains rule-chain strategy of
record. Production state UNCHANGED.

> **🎯 IMMEDIATE NEXT ACTION (Session 74): H2 route-tradeoff comparator OR gradient boosting**
>
>   **Option A (PREFERRED) — H2 features at the S71/4-phase playbook:**
>
>   Phase 1 (S74 ~10 min): persist ho_v7 H2 feature(s) gated to
>   high_only. Per SESSION_71_V45_FEATURE_HYPOTHESES.md §6:
>   `ho_v7_route_tradeoff_joint_minus_nonjoint_g` ∈ −13..+13 — signed
>   comparator: best JOINT mid_high minus best DS_NONJOINT top.
>   Targets the drop-max-top decision directly. Implement
>   `analysis/scripts/high_only_aug_v7_features_gated.py` +
>   `persist_high_only_aug_v7_gated.py`.
>
>   Phase 2 (S74 ~12 min): train v47_dt at depth=36 ml=1 = v44 + 2
>   ho_v7 features. Inspect feature importance (target: top-50 = ship
>   signal) + leaf count vs v44 baseline.
>
>   Phase 3 (S74 ~3 min): prefix grade v47 vs v44 (byte-identity
>   sanity check; should be 0 if surgical gating is intact).
>
>   Phase 4 (S74 ~20 min): full grade v47 vs v44. If full Δ ≥
>   +$10/1000h → Decision 109 ships v47 as new ML champion; build
>   v57_v47_hybrid (v56 with v44 → v47 in trips/two_pair/pair-PBOT
>   routing). If +$5 ≤ Δ < +$10 → second PARTIAL POSITIVE; consider
>   batching H1 + H2 into v48 (4 features) for compound effect. If
>   Δ ≤ +$5 → pivot to Option B.
>
>   **Option B (SECONDARY) — Gradient boosting at full feature set:**
>
>   If H2 also lands sub-threshold (+$5 to +$10 partial-positive), pivot
>   to XGBoost / LightGBM on the existing 109-feature matrix. Single
>   experiment; ~30 min train + grade. Potentially much larger payoff
>   if the saturating-DT regime has hit a structural ceiling that
>   boosting can correct iteratively. This is a one-time infrastructure
>   investment with no dependency on additional feature engineering.

> **✅ ARTIFACTS produced in S73:**
> 1. **`analysis/scripts/strategy_v46b_dt.py`** — inference; loads
>    `data/v46b_dt_model.npz`; ho_v6 features wired through.
> 2. **`analysis/scripts/grade_v46b_dt.py`** — head-to-head grader
>    vs v44_dt (or v45_dt or v46_dt for direct comparison).
> 3. **`data/v46b_dt_model.npz`** (1,266.75 MB) — PARTIAL POSITIVE;
>    reference only, NOT production champion. 2,260,527 leaves at
>    depth=36 ml=1.
> 4. **`data/session73/train_v46b_dt.log`,
>    `data/session73/grade_v46b_prefix.log`,
>    `data/session73/grade_v46b_full.log`** — phase logs.
> 5. **`data/session72/grade_v46_full.log`** + duplicate
>    `data/session73/grade_v46_full.log` — S72 v46_dt full grader
>    completed retroactively in S73 (was deferred from S72 due to TCC
>    blocker; repo move to ~/CODE/taiwanese/ unblocked).
> 6. **`SESSION_73_V46B_DT_NULL_REPORT.md`** — full PARTIAL POSITIVE
>    retrospective + Decision 108 reference.
> 7. **`SESSION_72_V46_DT_NULL_REPORT.md`** — appended "Phase 4 — full
>    grader (S73 completion)" subsection with the v46 full-grid table.
> 8. **`DECISIONS_LOG.md`** — Decision 108 appended.
> 9. **`CURRENT_PHASE.md`** — rewritten for S74 (this file).
> 10. **`STRATEGY_GUIDE.md`** — Part 1 SKIPPED (no strategy of record
>     changed); Parts 2-6 front-matter date refresh only.

> **📓 METHODOLOGY (Session 74+):**
> 1. **Regime-confound is the dominant axis of NULL postmortems.**
>    S73 produced the cleanest empirical demonstration in project
>    history: $261/1000h swing v46→v46b from hyperparameters alone,
>    feature set held identical. **NEVER change features AND hyperparams
>    in the same experiment**; always isolate via single-variable retry.
>    The S72 Phase-5 (regime-isolation retry) doctrine is now
>    empirically validated and permanent.
> 2. **Surgical gating's byte-identity guarantee is regime-locked.**
>    v46b restored byte-identity on 7/8 cats after v46 had broken it.
>    Same regime + same base features → byte-identity on gated-by-zero
>    categories. Future feature work aiming for surgical ships MUST
>    hold v44's regime (depth=36 ml=1) constant.
> 3. **Tripwire #1 (feature importance) > Tripwire #2 (leaf growth) at
>    saturating regime.** v46b leaves: +12K SHIP-signal; v46b
>    importance #75/#105 NULL-signal; the +$5 grader outcome confirmed
>    the importance signal. **Weight feature-importance tripwires more
>    heavily going forward; treat leaf growth as confirmatory only.**
> 4. **Diagnostic WG is ~10-20% recoverable per single-pair feature
>    retrain.** S71 said $147.59 WG STRUCTURE leak; H1 captured $24
>    (16%). Calibrate ship expectations: diagnostic identifies WHERE
>    leak is, not the magnitude that's recoverable per retrain.
>    Multi-feature batches or alternate-axis features (H2) may capture
>    the remaining $123 WG.
> 5. **+$10 ship threshold is canonical.** Codified in S73 (asked +
>    confirmed): features must net ≥+$10/1000h full grid to ship as
>    ML champion, regardless of within-cat magnitude or strictly-better
>    surgical-gating math. Rule 19's +$9 (S67) was a rule-chain ship
>    (different bar); ML-champion ships hold to +$10.
> 6. **"Speed is not necessary — clarity and perfection is."** S73
>    ran sequential graders (~50 min wall) to get definitive
>    within-cat data for both S72 v46 (NULL) and S73 v46b (PARTIAL).
>    The investment closed the door on H1 cleanly: no further re-runs
>    needed to know exactly where the SS+ms features stand.

> Updated: 2026-05-13 (Session 73 end — v46b_dt PARTIAL POSITIVE / NULL
> ship at +$5/1000h full grid; regime-confound theory confirmed; H2 or
> gradient boosting queued for S74)

---

## Headline state at end of Session 73

**Strategies of record (UNCHANGED from S72):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain (blanket trips → v44_dt; else → v55). **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S73 — pure ML retrain
attempt, PARTIAL POSITIVE / NULL ship result).

**S73 v46b_dt PARTIAL POSITIVE grade summary:**

| Metric | v44_dt | v46_dt (S72) | v46b_dt (S73) | Δ v46b vs v44 |
|---|---:|---:|---:|---:|
| Prefix grid $/1000h | $686 | $718 | **$686** | **+$0 (byte-identical)** |
| Full grid $/1000h | $1,081 | $1,337 | **$1,076** | **+$5 better** |
| Full pct_opt | 64.80% | 55.94% | **64.92%** | **+0.12pp** |
| Full p90 regret | 0.390 | 0.445 | 0.385 | better |
| Within-cat high_only $/1000h | $1,868 | $2,119 | **$1,844** | **+$24 better** |
| Within-cat high_only pct_opt | 41.8% | 35.3% | **42.5%** | **+0.7pp** |
| Leaves | 2,248,173 | 1,097,621 | **2,260,527** | **+12,354** |
| Features | 107 | 109 | 109 | +2 ho_v6 |
| Depth / ml | 36 / 1 | 32 / 3 | **36 / 1** | same as v44 |

**Per-category full-grid (v46b vs v44):**

| category | n hands | v44 $/1000h | v46b $/1000h | Δ |
|---|---:|---:|---:|---:|
| **high_only** (gated target) | 1,226,940 | 1,868 | 1,844 | **−$24 better** |
| pair | 2,800,512 | 1,097 | 1,097 | **0 (byte-identical)** |
| two_pair | 1,338,480 | 363 | 363 | **0 (byte-identical)** |
| trips | 328,185 | 1,194 | 1,194 | **0 (byte-identical)** |
| trips_pair | 171,600 | 281 | 281 | **0 (byte-identical)** |
| three_pair | 114,400 | 1,613 | 1,613 | **0 (byte-identical)** |
| quads | 14,300 | 545 | 545 | **0 (byte-identical)** |
| composite | 14,742 | 960 | 960 | **0 (byte-identical)** |

Surgical gating PERFECT — entire effect concentrated in high_only.

**Regime-confound swing — empirical fingerprint:**

| comparison | full $/1000h Δ | mechanism |
|---|---:|---|
| v46 (depth=32 ml=3) vs v44 (depth=36 ml=1) | **−$256 worse** | regime change + features |
| v46b (depth=36 ml=1) vs v44 (depth=36 ml=1) | **+$5 better** | features only |
| **v46b vs v46 (same features)** | **+$261 swing** | **regime change alone** |

The 51% leaf collapse (2.25M → 1.10M → 2.26M) is the leading
indicator: capacity loss from depth+ml regime change dominated all
S72 metrics.

---

## Hypothesis cascade status (per SESSION_71_V45_FEATURE_HYPOTHESES.md §6)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | SS+ms route quality (2 ho_v6 features) | **TESTED → PARTIAL POSITIVE / NULL ship.** Within-cat $24/1000h on high_only (16% of S71's $147 diagnostic prediction); full-grid +$5/1000h (below +$10 ship bar). Regime-confound theory confirmed (S72 regime change accounted for the full $261/1000h swing). |
| **H2** | Route-tradeoff comparator (joint vs DS_NONJOINT signed delta) | **NEXT.** Queued for S74. Direct target on the drop-max-top decision. |
| H3 | SS+ms route VARIETY signal (max_top_suit_count) | UNTESTED. Lower priority — may combine with H1 if H1 ships later. |
| H4 | MS_ONLY discriminator (2 features) | UNTESTED. Smaller WG target ($4.39 WG by S71). |
| H5 | Drop-max signal | UNTESTED. Needs H2 comparator infrastructure to be useful. |

---

## Resume Prompt (Session 74 — H2 route-tradeoff comparator OR gradient boosting)

```
Resume Session 74 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S73 — H2 features queued)
- SESSION_73_V46B_DT_NULL_REPORT.md (PARTIAL POSITIVE retrospective;
  regime-confound theory confirmation; +$10 ship threshold codified)
- SESSION_71_V45_FEATURE_HYPOTHESES.md (H2 spec in §6)
- DECISIONS_LOG.md (latest: Decision 108 — v46b PARTIAL POSITIVE)
- analysis/scripts/high_only_aug_v6_features_gated.py (template for
  ho_v7 — H2 route-tradeoff comparator)
- analysis/scripts/persist_high_only_aug_v6_gated.py (persistence
  harness template)
- analysis/scripts/train_v46_dt.py (template for train_v47_dt.py —
  depth=36 ml=1 saturating regime, NEVER change regime + features
  together)

State (end of S73):
- v46b_dt PARTIAL POSITIVE / NULL ship at +$5/1000h full
  (below +$10 ship bar; user-confirmed adherence to threshold).
- Within-cat high_only: −$24/1000h better, +0.7pp pct_opt;
  byte-identical to v44 on 7 of 8 other categories.
- Regime-confound theory empirically confirmed via $261/1000h
  v46→v46b swing from hyperparameters alone.
- S72 full grader completed retroactively (was TCC-blocked): v46
  $-256/1000h full, broad-based regression including +$251 on
  on-target high_only.

USER DIRECTIVE (S59-S73 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship threshold codified (asked + confirmed S73).

DIRECTION FOR SESSION 74 — H2 route-tradeoff comparator (Option A
PREFERRED) OR gradient boosting (Option B SECONDARY):

  Option A — H2 features (PREFERRED; first attempt):

    PHASE 1 (S74 ~10 min) — Implement + persist ho_v7 H2 feature(s)
    gated to high_only. Spec in
    SESSION_71_V45_FEATURE_HYPOTHESES.md §6:
    `ho_v7_route_tradeoff_joint_minus_nonjoint_g` ∈ −13..+13
    signed comparator: best JOINT mid_high minus best DS_NONJOINT
    top. Targets the drop-max-top decision directly. New files:
    `analysis/scripts/high_only_aug_v7_features_gated.py` and
    `analysis/scripts/persist_high_only_aug_v7_gated.py`. Wire
    smoke tests (5+) and verify gating-by-zero on non-high_only.

    PHASE 2 (S74 ~12 min) — Train v47_dt at depth=36 ml=1 (DO NOT
    change regime). Inspect feature importance:
      - top-50 → SHIP signal (proceed)
      - #50-100 → AMBIGUOUS (proceed cautiously)
      - #100+ → NULL signal (consider H2 dead; pivot to Option B)
    Inspect leaf count: ≥+10K vs v44's 2,248,173 = confirmation.

    PHASE 3 (S74 ~3 min) — Prefix grade v47 vs v44. Expect 0 delta
    on 7 non-high_only categories (byte-identity sanity check).

    PHASE 4 (S74 ~20 min) — Full grade v47 vs v44. Decision matrix:
      * Δ ≥ +$10/1000h full → Decision 109 ships v47 as new ML
        champion. Build v57_v47_hybrid per S70 v56 template.
      * +$5 ≤ Δ < +$10 → PARTIAL POSITIVE (like H1). Document; H2
        is mildly productive but below ship bar. Consider batching
        H1+H2 into v48 (4 features) for compound effect — could
        bring net to >+$10 full.
      * Δ ≤ +$5 → H2 dead. Pivot to Option B (gradient boosting).

  Option B — Gradient boosting (SECONDARY; if H2 NULLs):

    PHASE 1 (S74 if pivoting; ~30 min) — Install xgboost or lightgbm
    in the venv. Train v47_xgb (or v47_lgbm) at 109-feature X +
    105-target Y matrix. Hyperparams: n_estimators=500-1000,
    max_depth=8-12, learning_rate=0.05, early stopping on validation
    split. Expected ~10 min training.

    PHASE 2 (S74 ~3 min) — Inference scaffolding parallel to
    strategy_v46b_dt.py. Phase 3+4 grading per S74 Option A template.

    Decision matrix as above; ship at +$10/1000h.

  ACCEPTANCE for Session 74:
  - At least one of H2 (Option A) or gradient boosting (Option B)
    fully tested through prefix + full grader.
  - Decision 109 in DECISIONS_LOG.md: ship / NULL / partial.
  - If ship: STRATEGY_GUIDE.md Part 1 entry + v57 hybrid build.
  - If NULL/partial: SESSION_74 report mirroring SESSION_73 structure.
  - If H2 lands partial-positive and Option B has time → run both;
    compare net WG; ship the larger if either clears +$10.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- Hyperparam choice: depth=36 ml=1 for all DT retrains (regime locked
  at v44's saturating regime). DO NOT vary regime in same experiment
  as feature changes.
- Tripwire weighting: feature importance > leaf growth at saturating
  regime (S73 lesson).
- +$10 net WG = ship bar (canonical; codified S73). Within-cat
  improvements + strictly-better gating do NOT override the bar.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
