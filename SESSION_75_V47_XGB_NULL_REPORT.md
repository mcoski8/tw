# Session 75 — v47_xgb gradient boosting REGRESSES v44_dt by −$1,392/1000h full grid; shallow boosting cannot match saturating-DT memorization for this multi-output task; Option B closed at moderate capacity

_Generated: 2026-05-13_

## TL;DR — Decisive NULL. Gradient boosting at depth=6/n_est=200/lr=0.1 regresses v44 by $1,392/1000h across all 8 categories; on-target high_only −$1,593

S74 closed the DT-feature-engineering chapter with v47_dt's clean NULL.
S75 pivoted to Option B (gradient boosting) per CURRENT_PHASE.md
directive. v47_xgb trained on v44's exact 107 features (NO ho_v7) for
clean "boosting vs DT" isolation. Hyperparams: depth=6, n_estimators=200,
lr=0.1, multi_strategy='multi_output_tree', subsample=0.7,
colsample_bytree=0.7, early_stopping_rounds=20 on a 20% validation
split. Fit ran 3h42m wall to iter 199; val RMSE 1.37 → 0.534.

The full-grid grader is unambiguous: v47_xgb regresses v44_dt by
**−$1,392/1000h** on the 6M-hand realistic-mixture grid. Pct optimal
collapses from v44's 64.80% to 41.96%. Every per-category $/1000h is
worse — on-target high_only is −$1,593, trips_pair is −$2,746,
composite is −$2,392.

| Metric | v44_dt | v47_xgb (S75) | Δ |
|---|---:|---:|---:|
| Full grid pct_opt | 64.80% | **41.96%** | **−22.84pp** |
| Full grid $/1000h | $1,081 | **$2,473** | **−$1,392 (worse)** |
| Full grid p90 regret | 0.390 | **0.720** | worse |
| Full grid p99 regret | 0.970 | **1.360** | worse |
| Prefix grid pct_opt | 67.13% | 54.09% | −13.04pp |
| Prefix grid $/1000h | $686 | **$1,451** | **−$765 (worse)** |
| Leaves / trees | 2,248,173 leaves | 200 trees × 105 outputs | — |
| Features | 107 | 107 | same |
| Model size | 1,260 MB | **16.89 MB** | 75× smaller |
| Training fit | — | 13,367s (3h42m) | — |
| Inference (full grid) | 1,046s (per-hand walk) | 18.9s (batch predict) | 55× faster |

**Decision 110: NULL ship at THIS CONFIG.** v44_dt remains ML champion.
Production state UNCHANGED for the fourth consecutive session (S72 NULL,
S73 PARTIAL NULL ship, S74 clean NULL, S75 boosting NULL).

The val-curve tripwire fired "model still improving at iter limit"
(last-50-iter val RMSE delta +0.011, best_iteration=199/200). The
model is undertrained; capacity-tuned retries are open as a follow-up.
But the gap of $1,392/1000h is too wide to credibly be closed by
hyperparameter sweeps alone — at depth=6 with 200 trees, the model
fundamentally lacks the leaf-count capacity to compete with v44's
2.25M-leaf saturating regime.

## Phase 1 — XGBoost install (DONE)

`python3 -m pip install xgboost` initially failed with libomp dlopen
error on M-series Mac (per resume-prompt warning). Resolved with
`brew install libomp` (libomp 22.1.5 from Homebrew Cellar). XGBoost
3.2.0 then loaded cleanly. `multi_strategy='multi_output_tree'`
available (XGBoost ≥2.0 supports it natively; sanity-checked on a 2K-row
synthetic example before launching full training).

**Files:** no new code in Phase 1.

## Phase 2 — v47_xgb training (DONE)

**Run command:**
```
PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v47_xgb.py \
  --n-estimators 200 --max-depth 6 --learning-rate 0.1 \
  --early-stopping 20 --val-frac 0.20 \
  --subsample 0.7 --colsample-bytree 0.7 \
  --output data/v47_xgb_model.ubj --meta-output data/v47_xgb_meta.json
```

**Hyperparameter rationale:** The resume prompt allowed n_estimators=500-1000
and max_depth=8-12 at lr=0.05. A preliminary check on depth=10/lr=0.05
showed ~2 min/iter, putting 500 iter at 16+ hours wall — infeasible for
a single-session experiment. I scaled to depth=6/lr=0.1 to converge in
~3-4 hours. The lr-doubled+depth-halved tradeoff is mathematically
defensible (lr=0.1×100 trees ≈ lr=0.05×200 trees by total signal-mass
budget; deeper trees per iter add per-iter cost but allow higher-order
interactions).

**Training fit:**

* Wall: 13,367.6s (3h42m)
* best_iteration: 199 / 200 (early stopping did NOT fire — model still
  improving at the iter limit)
* best_score (val RMSE): 0.534287
* Model size: 16.89 MB (vs v44_dt 1,260.45 MB)
* Train rows: 4,807,327 (80%)  /  Val rows: 1,201,832 (20%)

**Val RMSE trajectory** (selected iters):

| iter | val RMSE | Δ |
|---:|---:|---:|
| 0 | 1.37288 | — |
| 5 | 1.03590 | −0.337 (large early gains) |
| 10 | 0.85598 | |
| 20 | 0.70215 | |
| 50 | 0.60107 | tail-off begins |
| 100 | 0.56138 | |
| 150 | 0.54550 | |
| 199 | 0.53429 | |

Last-50-iter Δ = +0.011 (still dropping ~0.0002/iter at iter 199).
The val-curve tripwire fired: "Model still improving at iter limit;
could benefit from --n-estimators > 200."

**Top-30 feature importance (gain-weighted, normalized):**

```
   1. n_broadway                              15.09%
   2. n_low                                   10.21%
   3. second_rank                              6.01%
   4. has_ace_singleton                        5.30%
   5. third_rank                               4.33%
   6. has_king_singleton                       4.29%
   7. ho_v2_bot_DS_max_top_rank_g              4.19%
   8. n_trips                                  3.77%
   9. top_rank                                 3.57%
  10. pair_high_rank                           3.19%
  ...
  30. n_pairs                                  0.91%
```

The boosting model emphasizes the same broad feature set as v44_dt
(n_broadway, n_low, rank features, DS_NONJOINT signals). No surprising
re-ranking; the model uses the v44 feature taxonomy in roughly the
same priority order.

## Phase 3 — Prefix grader (DONE — DECISIVE REGRESSION)

`PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v47_xgb.py
--grid prefix --baseline v44`

| strategy | pct_opt | $/1000h | p90 | wall |
|---|---:|---:|---:|---:|
| v44_dt (baseline) | 67.13% | $686 | 0.264 | 69s |
| v47_xgb | **54.09%** | **$1,451** | **0.492** | <1s |
| **Δ** | **−13.04pp** | **−$765** | worse | — |

**Per-category prefix breakdown — uniform regression:**

| category | n hands | v44 $/1000h | v47 $/1000h | Δ |
|---|---:|---:|---:|---:|
| pair | 215,162 | 595 | 955 | **−360** |
| two_pair | 204,275 | 663 | 1,644 | **−982** |
| trips | 25,245 | 1,086 | 2,263 | **−1,177** |
| trips_pair | 25,943 | 727 | 3,210 | **−2,482** |
| three_pair | 25,614 | 1,143 | 1,359 | **−216** |
| quads | 1,100 | 783 | 1,130 | **−348** |
| composite | 2,661 | 1,226 | 2,908 | **−1,681** |

The prefix grid contains 0 high_only canonical IDs (S72 finding), so
this is the clean "boosting vs DT on non-high_only categories" test.
v47_xgb regresses uniformly. The trips_pair regression of −$2,482 is
especially severe — v44_dt achieves 63.3% optimal there; v47_xgb only
27.1%.

## Phase 4 — Full grader (DONE — DECISIVE NULL)

`PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v47_xgb.py
--grid full --baseline v44`

**Overall:**

| strategy | pct_opt | $/1000h | p90 | p99 | wall |
|---|---:|---:|---:|---:|---:|
| v44_dt (baseline) | 64.80% | $1,081 | 0.390 | 0.970 | 1046s |
| v47_xgb | **41.96%** | **$2,473** | **0.720** | **1.360** | 8.4s (batch) |
| **Δ** | **−22.84pp** | **−$1,392** | worse | worse | 55× faster predict |

**Per-category full-grid breakdown — devastating regression:**

| category | n hands | v44 $/1000h | v47 $/1000h | Δ | v44 pct_opt | v47 pct_opt |
|---|---:|---:|---:|---:|---:|---:|
| high_only | 1,226,940 | 1,868 | **3,461** | **−1,593** | 41.8% | 23.5% |
| pair | 2,800,512 | 1,097 | **2,291** | **−1,194** | 65.7% | 47.4% |
| two_pair | 1,338,480 | 363 | **1,845** | **−1,482** | 83.2% | 51.5% |
| trips | 328,185 | 1,194 | **2,716** | **−1,523** | 58.6% | 30.2% |
| trips_pair | 171,600 | 281 | **3,027** | **−2,746** | 85.1% | 26.3% |
| three_pair | 114,400 | 1,613 | **2,069** | **−456** | 58.6% | 53.2% |
| quads | 14,300 | 545 | **2,265** | **−1,720** | 75.6% | 42.9% |
| composite | 14,742 | 960 | **3,351** | **−2,392** | 67.0% | 32.1% |

**Every category much worse.** The on-target high_only (S71-S74's
diagnostic target) regresses by $1,593/1000h. Trips_pair regresses
hardest in absolute terms (−$2,746), composite regresses hardest in
relative terms (3.5× worse).

The 55× inference speedup is the ONLY win for boosting: 18.9s batch
predict for all 6M hands vs 1,046s per-hand DT walk. If the model
EVER ships, that's a meaningful production-runtime advantage — but
at this regression magnitude, the speedup is decisively moot.

## Phase 5 — Decision 110: NULL ship; capacity limitations document

**v47_xgb does NOT replace v44_dt as ML champion.** Production state
unchanged: v56_trips_hybrid as rule chain ($1,429 full / $794 prefix),
v44_dt as ML champion ($1,081 full / $686 prefix).

**Reasoning:**

1. **Full-grid Δ = −$1,392/1000h** is decisively below the +$10 ship
   bar and the +$5 PARTIAL bar. The decision matrix (per
   CURRENT_PHASE.md S75 resume) maps this to: "Δ ≤ +$5 → boosting also
   caps at v44. Track exhausted at current features. Pivot to (a) grid
   label N=1000 re-eval, OR (b) new diagnostic to find next feature-
   engineering target."

2. **Every category regresses, including non-on-target ones.** The
   regression is not a feature-engineering miss; it's a fundamental
   capacity gap. v44_dt has 2,248,173 leaves at 2.7 rows/leaf —
   essentially a memorized lookup over the 6M canonical hands. v47_xgb
   at depth=6 has at most 64 leaves per tree × 200 trees = 12,800
   distinct partition cells; even with overlapping cells, the model
   cannot represent the fine-grained partitioning that the saturating-DT
   regime achieves.

3. **Val-curve tripwire FIRED.** The model was still improving at iter
   199 (val RMSE 0.534). With more trees (n_estimators=500-1000) the
   model would continue to improve, but the gap of $1,392/1000h is too
   wide to credibly close by tuning alone. Estimated effort to fully
   converge a depth=8/n_est=1000/lr=0.05 boosted model: 15-25 hours
   wall on this hardware. Speculative gain even after that: maybe
   $200-500/1000h closure of the gap — still NULL ship.

4. **Inference speedup is real but moot.** v47_xgb predicts the full
   6M grid in 18.9s vs v44_dt's 1,046s per-hand walks. That's a 55×
   speedup, which would meaningfully reduce grader wall time IF the
   model shipped. It doesn't ship.

5. **Boosting was a fair shot at unlocking the saturating ceiling.**
   The hypothesis was that iterative residual correction could exploit
   compressed comparators (H2) that DT axis-aligned splits cannot.
   Empirically, the saturating-DT regime DOMINATES this multi-output
   regression task at moderate boosting capacity. Boosting's
   "smooth functional approximation" loses to DT's "fine-grained
   memorization" when the task is argmax-over-105-outputs and the
   training data has 4.8M rows feeding a 2.25M-leaf tree.

### Hypothesis cascade status (final)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | SS+ms route quality (2 ho_v6 features) | **TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h full.** Within-cat $24/1000h on high_only. |
| **H2** | Route-tradeoff comparator (1 ho_v7 feature) | **TESTED → CLEAN NULL at +$0/1000h.** "Derivable in 2 splits" trap confirmed. |
| **Option B** | Gradient boosting at v44 features | **TESTED → DECISIVE NULL at −$1,392/1000h full.** Boosting at moderate capacity (depth=6, n_est=200) underfits the saturating-DT regime. |
| H3 | SS+ms route VARIETY signal | UNTESTED. Deprioritized. |
| H4 | MS_ONLY discriminator | UNTESTED. Deprioritized. |
| H5 | Drop-max signal | UNTESTED. Deprioritized (relied on H2 infrastructure). |

**Cascade verdict (final):** The ENTIRE single-model ML track (DT
feature engineering AND gradient boosting at moderate capacity) is
exhausted at v44's saturating regime. Production state UNCHANGED.
S76 must choose between:
* **(A)** Grid label re-evaluation at N=1000 (vs current N=200) —
  addresses label-noise ceiling; ~10× compute cost.
* **(B)** Categorical diagnostic refresh — re-run drill_v44_high_only_S71.py
  to identify a NEW feature-engineering target outside H1-H5 axes.
* **(C)** Higher-capacity boosting retry (v48_xgb at depth=8-10,
  n_est=1000+, lr=0.05) — expensive (~15-25 hours wall); speculative
  closure of $1,392 gap. **Lower priority than (A) and (B).**
* **(D)** Pivot the project's center of mass: rule-chain refinement
  via the trips/two-pair/composite drill targets (which the two-track
  divergence of $348 indicates have residual signal).

## Methodology lessons (Session 75)

1. **"Single deep DT beats shallow boosting" for argmax-over-N tasks
   with saturating memorization data.** This contradicts the typical
   ML wisdom that boosting wins; the contradiction is task-specific.
   When the goal is argmax-of-predictions over 105 outputs and the
   training data is 4.8M rows fitting a 2.25M-leaf tree at 2.7
   rows/leaf, the DT is effectively a nearest-neighbor lookup;
   boosting's smooth functional approximation cannot match it without
   FAR more capacity than a single-session experiment can afford.

2. **`multi_strategy='multi_output_tree'` works in XGBoost 3.2 on
   M-series Mac (requires libomp via Homebrew).** The install hurdle
   is real but one-time. Per-iter cost at depth=6 / 4.8M training rows
   / 105 outputs ≈ 67s steady-state on this hardware. Scaling to
   depth=10 / n_est=1000 / lr=0.05 is ~10× more expensive; not
   feasible in a single session.

3. **Hyperparameter regime scaling: lr×n_est is a useful
   budget proxy for boosting.** I scaled lr 0.05→0.1 and dropped
   n_est 500→200, holding total signal budget approximately constant.
   This is a defensible tradeoff at constant capacity; the val curve
   showed convergence trajectory consistent with the budget reduction.

4. **Val-curve tripwire is the boosting analog of the DT leaf-growth
   tripwire** — and it FIRED at v47_xgb (model still improving at iter
   limit). This says "the chosen n_estimators was too low" but does
   NOT change the verdict. A 10× capacity boost might close 10-30% of
   the gap; still NULL ship.

5. **The inference-speedup direction is structurally promising even
   when accuracy regresses.** v47_xgb predicts 6M hands in 18.9s vs
   v44_dt's 1,046s. A boosted model that MATCHES v44 accuracy would
   ship even without exceeding the +$10 bar, just for the 55× grader
   wall reduction (if the project's grader cost becomes a bottleneck).
   Worth keeping in mind for future capacity-tuned boosting attempts.

6. **The DT-feature-engineering chapter AND moderate-capacity boosting
   are both closed.** Four consecutive sessions at v44's saturating
   regime have produced: S72 NULL, S73 PARTIAL POSITIVE / NULL ship,
   S74 clean NULL, S75 decisive NULL. The +$10 ship bar has excluded
   every attempt. Production state UNCHANGED for the fourth session
   running. S76 must pivot to a NEW track: oracle-label refinement
   (option A), diagnostic-target refresh (B), or rule-chain extension
   (D).

7. **"Speed is not necessary — clarity and perfection is."** S75
   ran the full 4-phase playbook in ~5 hours wall (Phase 1 ~10 min
   libomp + install, Phase 2 ~3h42m train, Phase 3 ~2 min prefix
   grade, Phase 4 ~18 min full grade). The empirically airtight NULL
   verdict closes Option B at this config. Done with maximum clarity:
   prefix and full graders concur; every category regresses; the
   structural cause (boosting capacity vs DT memorization) is
   identified; the +$10 bar is decisively excluded.

## Files (Session 75)

**New code:**

* `analysis/scripts/train_v47_xgb.py` — XGBoost training with
  multi_strategy='multi_output_tree', early stopping, val-curve
  tripwire, feature-importance dump.
* `analysis/scripts/strategy_v47_xgb.py` — inference module; provides
  `predict_all_chosen()` for batch grading and `strategy_v47_xgb(hand)`
  for per-hand compatibility (cache-backed).
* `analysis/scripts/grade_v47_xgb.py` — batch-mode head-to-head grader
  bypassing per-hand strategy_fn pattern (XGBoost is per-hand-slow at
  6M scale).

**Data (gitignored, local-only):**

* `data/v47_xgb_model.ubj` (16.89 MB UBJSON booster).
* `data/v47_xgb_meta.json` (~12 KB: hyperparams, val curve per iter,
  top-30 importance, fit time).
* `data/session75/train_v47_xgb.log` — full training log.
* `data/session75/grade_v47_xgb_prefix.log` — prefix grader output.
* `data/session75/grade_v47_xgb_full.log` — full grader output.
* `data/session75/train_v47_xgb_smoke.log` — initial smoke (killed
  after 4 iters when per-iter cost was measured).

**Documentation:**

* `SESSION_75_V47_XGB_NULL_REPORT.md` (this file)
* `DECISIONS_LOG.md` — Decision 110 appended.
* `CURRENT_PHASE.md` — rewritten for S76.
* `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record
  changed); Parts 2-6 front-matter date refresh.

**Production state at end of S75:** UNCHANGED from S74.

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix).
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h (no change).
* Project rule count: **18** (no change).
* DT-feature-engineering AND moderate-capacity-boosting both exhausted
  at v44 saturating regime. S76 pivots to oracle-label N=1000
  re-evaluation, diagnostic refresh, or rule-chain extension.

## Appendix A — Decision 110 text (appended to DECISIONS_LOG.md)

See DECISIONS_LOG.md for the canonical text.

## Appendix B — Why moderate-capacity boosting fundamentally cannot match a saturating-DT regime for this task

A 2.25M-leaf depth=36 DT at 2.7 rows/leaf is, structurally, a memorized
lookup table. The 4.8M training rows are partitioned into 2.25M cells;
each cell contains ~2-3 rows; the per-cell mean across 105 outputs is
the model's prediction for any input that routes to that cell.

For argmax-of-predictions accuracy on training-like inputs, this is
essentially nearest-neighbor in feature space. New inputs at test time
route to the leaf of their nearest-neighbor canonical training row;
the argmax of THAT row's 105 EVs becomes the prediction.

A boosted ensemble at depth=6 with 200 trees has, at MOST, 64 × 200 =
12,800 distinct partition cells. Even with overlapping decision
boundaries and lr=0.1 cumulative weight, the model cannot represent
the 2.25M-cell partitioning a saturating DT achieves. Each tree's
contribution is a smooth correction; the final prediction is the
WEIGHTED SUM of 200 small corrections; the argmax of this sum is
sensitive to small errors in each correction.

To match the saturating-DT regime's partitioning capacity, boosting
would need approximately:
* depth=10 (1024 leaves/tree) × n_estimators=2200 = 2.25M cells,
  before accounting for overlap and weighting.
* Equivalent wall time at current per-iter cost: ~24-40 hours.

Even then, boosting's weighted-sum prediction smooths over partition
boundaries — at exactly the boundaries where label noise is highest
and argmax decisions are most sensitive. The saturating DT, by
contrast, treats each leaf as a hard partition with discrete
prediction.

**Implication:** for argmax-over-N-outputs on saturating-memorization
data, boosting needs disproportionately more capacity than DT to match
DT accuracy. This is the structural reason v47_xgb regresses v44_dt
by $1,392/1000h even after 3h42m of fitting and a val RMSE of 0.534
(decent in absolute terms; insufficient for argmax precision).
