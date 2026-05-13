# Current: Sprint 8 — Session 74 v47_dt clean NULL at depth=36 ml=1; DT-feature-engineering track exhausted; gradient boosting (Option B) queued for S75

S73 v46b_dt (H1 SS+ms route quality, 2 ho_v6 features) landed at
**+$5/1000h full** (PARTIAL POSITIVE / NULL ship per +$10 bar). S74
tested H2 (route-tradeoff comparator `ho_v7_route_tradeoff_joint_minus_
nonjoint_g`, 1 signed int8 feature) at the SAME regime (depth=36 ml=1,
LOCKED).

**Result: clean NULL. +$0/1000h full grid.** All 8 per-category
$/1000h match v44 to the dollar (including on-target high_only:
$1,868 → $1,868). pct_opt 64.80% → 64.80% (3-hand divergence of 6M).
Prefix grader byte-identical ($686 → $686 across all 7 categories).

Both tripwires concur NULL:
* Feature importance: **#103 / 108 (0.01%)** — deeper in tail than
  v46b's #75 (0.05%).
* Leaf growth: **+1 vs v44's 2,248,173** — cleanest "dead feature"
  signature in project history (v45 was +9 NULL; v46b was +12,354
  SHIP-but-PARTIAL).
* Training fit: 567s vs v46b's 610s at same regime — faster fit
  confirms DT scarcely used the new feature.

The S71-stated "derivable in 2 splits" trap is **empirically confirmed**:
at depth=36 with 2.25M leaves at 2.7 rows/leaf, the DT has ample
headroom to derive the comparator (best_JOINT_mid_high − best_DS_
NONJOINT_top) from existing features (ho_v3 max_mid_high + ho_v4
topNonMax_DS_ms_max_top_rank or similar) via axis-aligned splits.

Decision 109: **NULL ship per +$10 threshold AND +$5 PARTIAL bar.**
v44_dt remains ML champion; v56_trips_hybrid remains rule chain of
record. Production state UNCHANGED for the third consecutive session
(S72 NULL, S73 PARTIAL POSITIVE / NULL ship, S74 clean NULL).

**The DT-feature-engineering chapter is functionally closed at v44's
saturating regime.** Two consecutive sessions at the same 4-phase
playbook produce diminishing returns ($24 within-cat for H1, $0 for
H2). The +$10 ship bar excludes both. **S75 pivots to gradient
boosting (Option B).**

> **🎯 IMMEDIATE NEXT ACTION (Session 75): Gradient boosting (v47_xgb / v47_lgbm)**
>
>   PHASE 1 (S75 ~10 min) — Install xgboost or lightgbm in the venv:
>   ```
>   pip install xgboost
>   ```
>   Note: scikit-learn DT used `multi-output regression` natively
>   (Y is (n, 105) — one EV per setting per hand). XGBoost requires
>   either `multi_strategy='multi_output_tree'` (since v2.0) OR
>   training 105 separate regressors (slower at train but simpler).
>   Start with multi-output if XGBoost ≥2.0 is available; fall back
>   to 105 sequential regressors if not.
>
>   PHASE 2 (S75 ~20-40 min) — Train v47_xgb at v44's 107 features +
>   ho_v7 (1) = 108 features. Hyperparams (resume-prompt suggestion):
>   `n_estimators=500-1000, max_depth=8-12, learning_rate=0.05,
>   early stopping on validation split`. Save inference scaffolding
>   parallel to strategy_v47_dt.py.
>
>   **Alternative scope** — train v47_xgb on **v44's 107 features
>   alone** (no ho_v7). The H1+H2 NULL results have shown that ho_v6
>   and ho_v7 add diminishing-or-zero info at the DT regime; XGBoost
>   may benefit similarly little. Testing v44-only features isolates
>   "boosting vs single-tree" as the variable, with H1/H2 deferred to
>   v48_xgb if v47_xgb ships.
>
>   PHASE 3 (S75 ~3 min) — Prefix grade v47_xgb vs v44.
>
>   PHASE 4 (S75 ~30-40 min) — Full grade v47_xgb vs v44. Decision
>   matrix per S74 (canonical +$10 ship bar):
>     * Δ ≥ +$10/1000h full → Decision 110 ships v47_xgb as new ML
>       champion. Build v57_v47_xgb_hybrid per v56 template.
>     * +$5 ≤ Δ < +$10 → PARTIAL POSITIVE. Document; consider tuning
>       boosting hyperparams (depth=15, n_estimators=2000) in v48_xgb.
>     * Δ ≤ +$5 → boosting also caps at the v44 regime. The track is
>       **fully exhausted at v44 features**. Pivot to (a) grid label
>       re-evaluation at N=1000 (vs current N=200) — addresses
>       label-noise ceiling; ~10× compute cost. OR (b) categorical
>       diagnostic refresh — re-run drill_v44_high_only_S71.py to
>       identify a new feature-engineering target if the residual
>       structure has shifted.
>
> **📓 METHODOLOGY (Session 75+):**
>
> 1. **DT-feature-engineering at saturating regime is dead-end.** S73
>    (H1 ho_v6) and S74 (H2 ho_v7) both ran the canonical 4-phase
>    playbook at depth=36 ml=1; combined yield is $5/1000h (16% of
>    diagnostic $147.59 leak). Further single-feature-pair DT retrains
>    are not justified. **Do not run more DT-feature retrains at
>    saturating regime without a new diagnostic target or an
>    architectural change.**
>
> 2. **Leaf growth ≤+10 = NULL doctrine.** v47's +1 leaf is the new
>    floor for "DT didn't use the feature" detection. Tighter than
>    S59's "≤+1K = NULL" rule. The ≥+10K SHIP threshold remains.
>
> 3. **Fitter wall-time as 3rd tripwire.** Same-regime retrain that
>    fits FASTER than baseline = NULL signal (DT had fewer splits
>    to evaluate, so the new feature added little). Same-regime
>    retrain that fits SLOWER = SHIP signal (more candidate splits).
>    Read jointly with importance + leaf growth.
>
> 4. **"Derivable in N splits" is now a documented failure mode.**
>    Feature design must explicitly verify non-derivability before
>    investing in persistence + retrain cost. Going forward, any
>    candidate feature `f(hand)` whose computation can be expressed
>    as a binary combination of ≤3 existing features in the v44
>    taxonomy is high-risk for the "derivable in 2 splits" trap at
>    saturating regime.
>
> 5. **"Speed is not necessary — clarity and perfection is."** S74
>    closed the H2 chapter with maximal empirical clarity in ~50 min
>    wall. The clean NULL is more valuable than a fast PARTIAL would
>    have been; both tripwires + the prefix + full graders all concur,
>    and the hypothesis is falsified at the saturating regime
>    unambiguously.
>
> 6. **+$10 ship bar canonical (codified S73, held S74).** Third
>    consecutive session UNCHANGED production state — the bar is
>    doing its job, filtering noise from signal. ML-champion ships
>    must clear +$10/1000h full grid.

> **✅ ARTIFACTS produced in S74:**
> 1. `analysis/scripts/high_only_aug_v7_features_gated.py` — 1 signed
>    int8 feature; 5 hand-crafted smoke tests; all pass.
> 2. `analysis/scripts/persist_high_only_aug_v7_gated.py` — emits
>    `data/feature_table_high_only_aug_v7_gated.parquet` (18.59 MB).
> 3. `analysis/scripts/train_v47_dt.py` — depth=36 ml=1 regime-locked.
> 4. `analysis/scripts/strategy_v47_dt.py` — inference for v47.
> 5. `analysis/scripts/grade_v47_dt.py` — head-to-head grader vs
>    v44/v45/v46/v46b.
> 6. `data/v47_dt_model.npz` (1,260.45 MB) — clean NULL; reference
>    only, NOT production champion.
> 7. `data/session74/persist_v7.log`, `train_v47_dt.log`,
>    `grade_v47_prefix.log`, `grade_v47_full.log` — phase logs.
> 8. `SESSION_74_V47_DT_NULL_REPORT.md` — full NULL retrospective +
>    Decision 109 reference.
> 9. `DECISIONS_LOG.md` — Decision 109 appended.
> 10. `CURRENT_PHASE.md` — rewritten for S75 (this file).
> 11. `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record
>     changed); Parts 2-6 front-matter date refresh only.

> Updated: 2026-05-13 (Session 74 end — v47_dt clean NULL at +$0/1000h
> full grid; DT-feature-engineering track exhausted at saturating
> regime; gradient boosting Option B queued for S75)

---

## Headline state at end of Session 74

**Strategies of record (UNCHANGED from S73):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S74 — clean NULL
ML retrain attempt).

**S74 v47_dt clean NULL grade summary:**

| Metric | v44_dt | v46b_dt (S73 H1) | v47_dt (S74 H2) | Δ v47 vs v44 |
|---|---:|---:|---:|---:|
| Prefix grid $/1000h | $686 | $686 | **$686** | **+$0 (byte-identical)** |
| Full grid $/1000h | $1,081 | $1,076 | **$1,081** | **+$0 (identical)** |
| Full pct_opt | 64.80% | 64.92% | **64.80%** | +0.00005pp (3 hands of 6M) |
| Full p90 regret | 0.390 | 0.385 | **0.390** | tied |
| Full p99 regret | 0.970 | 0.970 | **0.970** | tied |
| Within-cat high_only $/1000h | $1,868 | $1,844 | **$1,868** | **+$0** |
| Within-cat high_only pct_opt | 41.8% | 42.5% | **41.8%** | **+0** |
| Leaves | 2,248,173 | 2,260,527 | **2,248,174** | **+1 only** |
| Features | 107 | 109 | 108 | +1 ho_v7 |
| Depth / ml | 36 / 1 | 36 / 1 | **36 / 1** | same as v44 |
| Top-importance rank | n/a | #75 + #105 | **#103** | NULL |

**Per-category full-grid (v47 vs v44) — all 8 byte-identical:**

| category | n hands | v44 $/1000h | v47 $/1000h | Δ |
|---|---:|---:|---:|---:|
| high_only | 1,226,940 | 1,868 | 1,868 | **0** |
| pair | 2,800,512 | 1,097 | 1,097 | **0** |
| two_pair | 1,338,480 | 363 | 363 | **0** |
| trips | 328,185 | 1,194 | 1,194 | **0** |
| trips_pair | 171,600 | 281 | 281 | **0** |
| three_pair | 114,400 | 1,613 | 1,613 | **0** |
| quads | 14,300 | 545 | 545 | **0** |
| composite | 14,742 | 960 | 960 | **0** |

Including the on-target high_only category — where v46b (H1) earned
+$24/1000h within-cat. H2 generates **zero** within-cat lift.

---

## Hypothesis cascade status (per SESSION_71_V45_FEATURE_HYPOTHESES.md §6)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | SS+ms route quality (2 ho_v6 features) | **TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h full.** Within-cat $24/1000h on high_only (16% of S71's $147 diagnostic prediction). |
| **H2** | Route-tradeoff comparator (1 ho_v7 feature) | **TESTED → CLEAN NULL at +$0/1000h full.** +1 leaf, #103 importance. "Derivable in 2 splits" trap empirically confirmed. |
| H3 | SS+ms route VARIETY signal (max_top_suit_count) | UNTESTED. **Deprioritized** — expected similar saturation ceiling. |
| H4 | MS_ONLY discriminator (2 features) | UNTESTED. **Deprioritized** — smaller WG target ($4.39 WG by S71). |
| H5 | Drop-max signal | UNTESTED. **Deprioritized** — needed H2 comparator to be useful; H2 is dead. |

**Cascade verdict:** DT-feature-engineering track exhausted at v44's
saturating regime. **S75 pivots to gradient boosting (XGBoost/LightGBM)
to test whether iterative residual correction unlocks the structural
ceiling that the saturating-DT regime has hit.**

---

## Resume Prompt (Session 75 — Gradient boosting Option B)

```
Resume Session 75 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S74 — gradient boosting queued)
- SESSION_74_V47_DT_NULL_REPORT.md (clean NULL retrospective;
  "derivable in 2 splits" trap empirically confirmed)
- SESSION_73_V46B_DT_NULL_REPORT.md (H1 PARTIAL POSITIVE / NULL ship)
- DECISIONS_LOG.md (latest: Decision 109 — v47 clean NULL)
- analysis/scripts/train_v47_dt.py (template for train_v47_xgb.py —
  build_X function reusable; swap DecisionTreeRegressor for XGBoost)
- analysis/scripts/strategy_v47_dt.py (template for strategy_v47_xgb.py)
- analysis/scripts/grade_v47_dt.py (template for grade_v47_xgb.py)

State (end of S74):
- v47_dt CLEAN NULL at +$0/1000h full grid (109 features, ho_v7
  comparator added zero signal; +1 leaf delta; #103 importance).
- "Derivable in 2 splits" trap empirically confirmed at depth=36 ml=1.
- DT-feature-engineering track exhausted at v44's saturating regime
  (S73 H1 PARTIAL +$5, S74 H2 clean NULL $0 — chapter closed).

USER DIRECTIVE (S59-S74 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship threshold canonical (codified S73, held S74).

DIRECTION FOR SESSION 75 — Option B (gradient boosting):

  PHASE 1 (S75 ~5-10 min) — Install xgboost in venv:
    pip install xgboost
  Verify XGBoost ≥2.0 (for `multi_strategy='multi_output_tree'`).
  Fall back to 105 sequential regressors if <2.0 (slower but works).

  PHASE 2 (S75 ~20-40 min) — Train v47_xgb at v44's 107 features
  (NOT 108 — exclude ho_v7; isolate "boosting vs DT" as the only
  variable; defer feature additions to v48_xgb if v47_xgb ships).
  Hyperparams: n_estimators=500-1000, max_depth=8-12,
  learning_rate=0.05, early stopping on 20% validation split,
  tree_method='hist'. Save inference scaffolding parallel to
  strategy_v47_dt.py. Tripwires:
    * Validation curve: does the boosting model continue to improve
      past iteration 500? If yes, the single-DT's saturation ceiling
      WAS the binding constraint. If no, the ceiling is label-noise.
    * Inference cost: per-hand time vs DT. XGBoost multi-output may
      be 2-10× slower than DT depending on n_estimators.

  PHASE 3 (S75 ~3-5 min) — Prefix grade v47_xgb vs v44_dt.

  PHASE 4 (S75 ~30-40 min) — Full grade v47_xgb vs v44_dt. Decision
  matrix:
    * Δ ≥ +$10/1000h full → Decision 110 ships v47_xgb as ML
      champion. Build v57_xgb_hybrid per v56 template.
    * +$5 ≤ Δ < +$10 → PARTIAL POSITIVE. Document; consider tuning
      (depth=15, n_estimators=2000) in v48_xgb.
    * Δ ≤ +$5 → boosting also caps at v44. Track exhausted at
      current features. Pivot to (a) grid label N=1000 re-eval, OR
      (b) new diagnostic to find next feature-engineering target.

  ALTERNATIVE — if XGBoost install proves complex (M-series Mac
  compile issues common), try LightGBM as a one-liner alternative
  (`pip install lightgbm`). LightGBM's `MultiOutputRegressor`
  wrapper is the standard multi-output path.

  ACCEPTANCE for Session 75:
  - At minimum: v47_xgb (or v47_lgbm) fully tested through prefix +
    full grader.
  - Decision 110 in DECISIONS_LOG.md: ship / NULL / partial.
  - If ship: STRATEGY_GUIDE.md Part 1 entry + v57 hybrid build.
  - If NULL/partial: SESSION_75 report mirroring SESSION_74 structure.
  - Two-track divergence may change if v47_xgb ships and feeds
    v54/v55/v56 hybrids — recompute.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- For boosting hyperparams, do NOT vary regime + features in same
  experiment (S73 methodology lesson #1). Lock features at v44's 107
  for first XGBoost run; add ho_v6/ho_v7 in subsequent experiments if
  boosting clears the ship bar.
- Leaf-growth tripwire is DT-specific and does NOT apply to boosting.
  For XGBoost, the closest analog is `train_logloss` curve flattening
  vs val_logloss continuing to improve.
- Feature importance tripwire DOES apply to boosting (XGBoost has
  `feature_importances_`). Same thresholds: top-50 SHIP, #50-100
  AMBIGUOUS, #100+ NULL.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
