# Current: Sprint 7 Phase E — chain extracted; shape-target → EV mismatch quantified. trips_pair mining halted at Step 3 (4-step doctrine). Session 20 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 21):** Pivot the training target from `multiway_robust` (mode-of-4-profiles) to per-profile EV-aware. The depth-15 chain (37 features, 18,399 leaves, +7.57pp shape over v3) **loses money** in dollars at $10/EV-pt: −$1,801/1000h vs omaha-first profile while gaining only +$409 / +$697 / +$9 against the other three. Net mean across 4 profiles: **−$172/1000h**. Two paths: (i) train DT on regression target = per-profile EV (or mean EV) instead of classification target = mode-setting; or (ii) ensemble = pick the profile-conditioned setting at inference time given a known opponent. The user's reframe (Decision 033) explicitly retired shape-agreement as the goal — Session 20 confirmed empirically that shape-agreement and EV are not the same thing.

> **🚫 RETIRED (Decision 033, Session 16):** "≥95% shape-agreement on multiway-robust target." Replaced with directional reduction below v3's EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles. Reportable metric: $/1000 hands at $10/EV-pt.

> **🚫 HALTED (Decision 037, Session 20):** trips_pair augmented-feature mining. Population share 2.97% × max realistic slice lift cannot exceed +0.5pp full-6M (the user's halt threshold).

> Updated: 2026-04-30 (end of Session 20)

---

## Headline state at end of Session 20

**The depth-15 augmented DT chain is live as `strategy_v5_dt`, byte-identical to the trained sklearn DT on the full 6M.** Shape-agreement on full 6M = 63.21% literal / **63.73% shape (+7.57pp over v3's 56.16%)**. EV-loss baseline at hands=2000, samples=1000, seed=42 (same hands as v3 baseline, identical RNG):

| Profile      | v3 mean loss | v5_dt mean loss | Δ EV       | $/1000h at $10/pt |
|--------------|--------------|-----------------|------------|---------------------|
| mfsuitaware  | 1.3692       | 1.3283          | +0.0409    | +$409.31            |
| **omaha**    | **1.1514**   | **1.3315**      | **−0.1801**| **−$1,800.89**      |
| topdef       | 1.4385       | 1.3688          | +0.0697    | +$697.44            |
| weighted     | 1.2221       | 1.2212          | +0.0009    | +$8.82              |
| **mean**     | **1.2953**   | **1.3125**      | **−0.0172**| **−$171.83**        |

Absolute mean EV per profile (positive = v5 ahead, negative = v5 behind):

| Profile      | v3 EV    | v5_dt EV | Δ        | BR EV   |
|--------------|----------|----------|----------|---------|
| mfsuitaware  | −0.7779  | −0.7369  | +0.0409  | +0.5913 |
| omaha        | +1.0117  | +0.8316  | −0.1801  | +2.1632 |
| topdef       | −0.8846  | −0.8149  | +0.0697  | +0.5539 |
| weighted     | +0.3779  | +0.3788  | +0.0009  | +1.6000 |

**Headline: shape-target trained DT is a net EV loss in dollars.** v5_dt picked up shape-agreement on three profiles by sacrificing the omaha-first-profile setting where the four-way mode disagreed. v3 was hand-tuned with stronger omaha-favoring rules (its no_top_bias variant was created exactly for this asymmetry); the DT inherited none of that bias. Session 20 confirmed empirically what Decision 033 asserted in theory: **shape-agreement and EV are not the same thing.**

### Session 19 → Session 20 deltas

- **chain extracted:** `data/v5_dt_model.npz` (133 KB, gzip'd npz). Tree arrays — `children_left`, `children_right`, `feature`, `threshold`, `value_argmax`, `classes`, plus `feature_columns` and `cat_map` for from-hand feature compute.
- **byte-identical parity (sklearn vs manual walk):** 0 diffs across all 6,009,159 canonical hands.
- **byte-identical from-hand parity:** 0 cell diffs across 50K random rows × 37 features (50,000 × 37 = 1.85M cells); 0 prediction diffs after walking the tree.
- **trips_pair mining halted:** slice ceiling 86.18% (vs two_pair 79.47%), miss-leaf concentration top-10 = 1.2% (more diffuse than two_pair's 0.5%), population share 2.97%, EV-loss share 2.5%. Even +7.50pp full-cohort lift (Session 19 magnitude) projects to +0.22pp full-6M — below halt threshold.

---

## What was completed this session (Session 20)

### Step 0 — 4-step doctrine on trips_pair (Decision 037)

Before designing features, ran Steps 2-3-4 of the 4-step hypothesis doctrine on trips_pair as a sanity check:

- **Step 2 (signal):** baseline DT on slice (28 features) ceiling = 86.18% — the baseline is already strong, leaving only 13.82pp of headroom on the slice. Compare to two_pair's 79.47% / 20.53pp room.
- **Step 3 (impact):** trips_pair share of v3 EV-loss = **2.5%** (n=39 of 2000 in `v3_evloss_records.parquet`, `loss_weighted` weighted). Population share 2.97% (178K of 6M). Pre-mining math: even a +7.5pp full-cohort lift (Session 19 magnitude on two_pair) projects to +0.22pp full-6M shape — **below the +0.5pp halt threshold from the resume prompt.**
- **Step 4 (cheap test):** miss-leaf concentration top-10 = 1.2%, top-50 = 4.7%, top-100 = 8.1% across 4,778 distinct miss-leaves — even more diffuse than two_pair (0.5/3.4/—). Top miss-leaves recurringly show the "trip-on-bot vs pair-on-bot" routing decision the 28 baseline features can't see, mirroring the two_pair structural blind spot. The pattern exists but the cohort is too small for the chain-extraction to benefit.

**Decision: HALT mining at Step 4.** No feature module written for trips_pair. Discovery phase has plateaued for additional cohorts.

### Step 1 — Chain extraction (`extract_v5_dt.py`)

- Trained depth=15 DT on full 6M with all 37 augmented features (28 baseline + 3 pair-aug + 3 high_only-aug + 3 two_pair-aug). Fit time: 14.5s. n_leaves: 18,399. n_nodes: 36,797.
- Saved sklearn tree arrays as `data/v5_dt_model.npz`: `children_left`, `children_right`, `feature`, `threshold`, `value_argmax`, `classes`, plus metadata (`feature_columns`, `cat_map`, `depth`, `n_leaves`).
- Vectorised manual tree-walk (numpy chunked, ≤20 levels deep) on the full 6M produced byte-identical predictions to `dt.predict(X)` — **0 diffs across 6,009,159 rows.**
- Literal-agreement on full 6M: 61.32% (matches Session 19 depth-15 reference).

### Step 2 — From-hand strategy module (`strategy_v5_dt.py`)

- `strategy_v5_dt(hand: np.ndarray) -> int` — drop-in replacement for `strategy_v3` callable. Computes the 37 features from raw hand bytes, walks the saved tree, returns setting_index in 0..104.
- Feature compute uses `tw_analysis.features.hand_features_scalar` for 28 baseline features, plus the 3 aug compute functions. Two correctness gotchas captured:
  1. **Category-id remapping.** `dt_phase1_aug3.py` builds `cat_map = sorted(unique(category))` (alphabetical: high_only=0, pair=1, quads=2, three_pair=3, trips=4, trips_pair=5, two_pair=6) — this differs from the natural `CATEGORY_TO_ID` ordering in `tw_analysis.features` (high_only=0, pair=1, two_pair=2, three_pair=3, trips=4, trips_pair=5, quads=6). The strategy module overrides via the saved `cat_map`.
  2. **Aug-call gating.** Each `persist_*_aug.py` script applies a `category == 'X'` mask; out-of-category rows are zero. The aug compute functions don't all early-return on out-of-category hands (notably `compute_high_only_aug_for_hand` assumes the caller filters). The strategy module gates each aug call by category string (`pa = compute_pair_aug_for_hand(hand) if cat_str == CATEGORY_PAIR else (0,0,0)`, etc.) to be byte-identical with the persisted parquets.

### Step 3 — Full-pipeline parity check (`verify_v5_dt_parity.py`)

- Sampled 50,000 random canonical hands. Built parquet-derived feature matrix (extract_v5_dt logic) and from-hand-bytes feature matrix (strategy_v5_dt logic) for the same indices.
- **Byte-identical: 0 cell-level diffs across all 37 features × 50K rows = 1.85M cells.**
- **0 prediction diffs after walking the tree on both matrices.**
- Shape-agreement on the 50K sample: **63.73%** — matches Session 19's depth-15 reference of 63.74% within sampling noise. v3 production at 56.16% means **v5_dt is +7.57pp over v3.**

### Step 4 — EV-loss baseline (`v3_evloss_baseline.py --strategy v5_dt`)

- Registered `strategy_v5_dt` in the `STRATEGIES` dict alongside `v3` and `v3_no_top_bias`.
- Ran `--hands 2000 --samples 1000 --seed 42 --save data/v5_dt_records.parquet`. Total time: 527.6s (4.0 hands/sec, 4 profiles per hand × 1000 MC samples).
- Same 2000 hands as `data/v3_evloss_records.parquet` (verified by hand_str overlap = 2000 of 2000). Apples-to-apples comparison across the four profiles plus the average.

### Step 5 — Test suites

- Rust: `cargo test --release` → **124/124 pass** (88 + 15 + 15 + 6, unchanged from Session 19).
- Python: pytest on six test files → **74/74 pass** (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden, unchanged).

---

## Files added this session

- `analysis/scripts/mine_trips_pair_leaves.py` — Step 1-3 trips_pair mining (slice ceiling, leaf-rank dump). Confirmed halt decision.
- `analysis/scripts/extract_v5_dt.py` — fit depth-15 DT on full 6M with 37 features, save tree arrays + metadata to `data/v5_dt_model.npz`, run sklearn-vs-manual-walk parity check on full 6M.
- `analysis/scripts/strategy_v5_dt.py` — `strategy_v5_dt(hand)` callable, `compute_feature_vector(hand, model)` from-hand feature compute, `predict_many_from_hands(hands)` for batch parity work, plus 5 hand-picked smoke tests in `__main__`.
- `analysis/scripts/verify_v5_dt_parity.py` — full-pipeline parity check on 50K random canonical hands. Asserts byte-identical features, byte-identical predictions, reports shape-agreement.
- `data/v5_dt_model.npz` — 0.13 MB. Tree arrays + feature column order + cat_map. Loaded once by `strategy_v5_dt` and cached.
- `data/v5_dt_records.parquet` — 2000-hand × 4-profile EV records under `strategy_v5_dt`. Same schema as `data/v3_evloss_records.parquet` (column names retain `v3_*` prefixes from the report-style; values are v5_dt's choices).

## Files modified this session

- `analysis/scripts/v3_evloss_baseline.py` — added `from strategy_v5_dt import strategy_v5_dt` + registered in `STRATEGIES` dict.
- `CURRENT_PHASE.md` — rewritten.
- `DECISIONS_LOG.md` — appended Decision 037 (trips_pair halt) + Decision 038 (chain extraction + EV-loss measurement).
- `handoff/MASTER_HANDOFF_01.md` — appended Session 20 entry.

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass.
- `verify_v5_dt_parity.py`: 0 feature diffs / 0 prediction diffs on 50K random rows.
- `extract_v5_dt.py`: 0 diffs sklearn-vs-manual-walk on full 6M.

## Gotchas + lessons

- **Shape-agreement is NOT EV.** v5_dt has +7.57pp shape lift over v3 but loses $172/1000h on average (driven by $1,801 loss against omaha-first). The gap exists because v5_dt was trained to predict the **mode** of the 4 BR profiles, which can disagree with any single profile. v3 was hand-tuned to favor omaha because that profile produces the largest EV swings. Lesson confirmed: Decision 033's reframe was correct — the deliverable metric must be EV in dollars, not shape-agreement.
- **The "27 baseline" label is actually 28 features (still).** Session 20 carries the off-by-one forward unchanged. X.shape outputs in `extract_v5_dt.py` confirm 37 columns total = 28 + 3 + 3 + 3.
- **Aug-call gating must be enforced at inference.** First parity attempt failed with 69,234 cell diffs because `compute_high_only_aug_for_hand` does not early-return on non-high_only hands (the function assumes the caller filters). Strategy module must gate each aug call by category string to match what the persisted parquets did. Saved as a hard rule in the strategy module.
- **Category-id alphabetical vs natural-order.** `dt_phase1_aug3.py`'s `cat_map = sorted(unique(category))` differs from `tw_analysis.features.CATEGORY_TO_ID`. The strategy module saves and loads its own `cat_map` rather than relying on the in-tree mapping. If a future session moves to a per-feature-pipeline canonical mapping, this can be removed.
- **trips_pair mining was a productive halt, not a failure.** The 4-step doctrine surfaced "this cohort cannot reach the halt threshold even with peak prior-session lift" before any feature design / OR test / batch persist. ~12 minutes of mining + math vs the alternative of designing and building 3 features then discovering the lift is too small.
- **The DT chain itself is portable.** `data/v5_dt_model.npz` is 133 KB. The strategy module needs only numpy + the existing aug feature modules. No sklearn at inference time. Future deployments to the trainer or to a non-Python frontend can re-implement the tree walk in any language.

---

## Resume Prompt (Session 21)

```
Resume Session 21 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 20)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decisions 037 + 038 — trips_pair halt + chain extraction)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 16-20 since the goal reframe)
- analysis/scripts/strategy_v5_dt.py (production strategy callable)
- analysis/scripts/extract_v5_dt.py (tree training + extraction harness)
- analysis/scripts/verify_v5_dt_parity.py (parity test for any future re-extract)
- analysis/scripts/v3_evloss_baseline.py (now supports --strategy v5_dt)
- data/v5_dt_model.npz (frozen tree at end of Session 20)
- data/v5_dt_records.parquet vs data/v3_evloss_records.parquet
  (apples-to-apples 2000-hand × 4-profile EV records)

State of the project (end of Session 20):
- v5_dt chain LIVE: depth-15 DT, 18,399 leaves, 37 features, byte-identical parity
  with sklearn at full 6M and at 50K from-hand-bytes sample.
- v5_dt shape-agreement: 63.73% (full 6M) — +7.57pp over v3's 56.16%.
- v5_dt EV-loss vs v3 (mean of 4 profiles): −$172/1000h at $10/EV-pt.
  - mfsuitaware: +$409/1000h
  - omaha:       −$1,801/1000h ← the killer
  - topdef:      +$697/1000h
  - weighted:    +$9/1000h
- trips_pair mining halted at Step 3 of the 4-step doctrine. No feature module written.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(A) Pivot training target from `multiway_robust` to per-profile EV-aware.
    The clearest signal from Session 20: training on mode-of-4-profiles loses
    money against the profile with the most extreme EV swings (omaha). Two
    sub-paths:
      A.1 — train DT REGRESSION on `ev_mean` (or per-profile `ev_omaha`) and
            pick the setting with highest predicted EV. Higher inference cost
            (105 settings × predict per hand) but directly optimises the
            user's metric.
      A.2 — train one DT per profile on its own BR target, ensemble at
            inference: pick per-profile setting if profile is known, or
            averaged-EV setting if not. Closer in spirit to v3+overlays.

(B) Reconcile the omaha asymmetry without retraining. Inspect WHY v5_dt's
    omaha-loss is concentrated. Compare v3's strategy_omaha_overlay choices
    on the worst-omaha hands to v5_dt's choices. Possibly hybrid: use v5_dt
    when all 4 profiles' BR agrees (the 'mode' was unanimous); fall back to
    v3 + overlays when profiles split.

(C) Re-target the chain at depth=20 or depth=None (vs current depth=15).
    Session 19 showed depth=None at 66.87% / 64.80% literal — +1.67pp shape
    over depth=15. If shape-target HAD correlated with EV, going deeper
    would have helped. Given Session 20's finding that shape ≠ EV, this is
    likely diminishing returns, but the measurement is cheap (~30 min).

The user has previously chosen (a)-paths over (b/c)-style hybrid work. (A) is
recommended for Session 21. The 4-step doctrine still applies — measure
signal + impact + cheap test BEFORE training.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
