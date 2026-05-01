# Current: Sprint 7 Phase E — path-A target pivot tested. Cheap-test confirms +$13K hedge ceiling; per-profile ensemble (A.2) is a NULL RESULT. Session 21 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 22):** Path A.1 — DT regression on per-setting EV. The cheap-test (Decision 039) showed argmax_mean has +$12,949/1000h headroom over v5_dt at $10/EV-pt. Path A.2 (per-profile DT vote-ensemble, Decision 040) was a clean null: 90.25% choice-agreement with v5_dt and −$81/1000h on the mean. The hedge ceiling is real but a 105-class classifier on 37 features can't reach it. To capture the gap we need a per-setting EV regression target — which requires generating a new MC dataset (~50K hands × 105×4 EVs ≈ 14 hours overnight via the existing `cheap_test_oracle_hedges.py` harness). After that: train regression DTs, predict EV per setting at inference, argmax over 105.

> **🚫 RETIRED (Decision 033, Session 16):** "≥95% shape-agreement on multiway-robust target." Replaced with directional reduction below v3's EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles. Reportable metric: $/1000 hands at $10/EV-pt.

> **🚫 HALTED (Decision 037, Session 20):** trips_pair augmented-feature mining. Population share 2.97% × max realistic slice lift cannot exceed +0.5pp full-6M.

> **🚫 NULL RESULT (Decision 040, Session 21):** path A.2 per-profile DT ensemble. 90.25% choice-agreement with v5_dt; net −$81/1000h vs v5_dt and −$252/1000h vs v3. Voting 4 weak per-profile DTs (58–65% literal accuracy) cannot approximate oracle_argmax_mean.

> Updated: 2026-04-30 (end of Session 21)

---

## Headline state at end of Session 21

**Two artifacts shipped, one positive, one negative:**

1. **(positive) `cheap_test_oracle_hedges.py` quantified the hedge ceiling** at +$12,949/1000h vs v5_dt and +$14,074/1000h vs v3. The 4-step doctrine confirmed path A is empirically justified. `data/cheap_test_oracle_grid_200.npz` (218 KB) is the persisted 105×4×200 EV grid for re-analysis.
2. **(negative) `strategy_v6_ensemble` is a null result.** Despite training 4 strong per-profile DTs (each 58-65% literal-agreement on its target, byte-identical sklearn-vs-walk parity), the vote-ensemble has 90.25% choice-overlap with v5_dt and is slightly worse on every profile. Path A.2 is closed.

EV-loss baseline at hands=2000, samples=1000, seed=42 (same hands as v3 + v5_dt baselines):

| Profile     | v3 mean loss | v5_dt mean loss | v6_ensemble mean loss | $/1000h v6 vs v3 | $/1000h v6 vs v5 |
|-------------|--------------|-----------------|-----------------------|------------------|------------------|
| mfsuitaware | 1.3692       | 1.3283          | 1.3339                | +$353            | −$56             |
| **omaha**   | **1.1514**   | **1.3315**      | **1.3483**            | **−$1,969**      | **−$168**        |
| topdef      | 1.4385       | 1.3688          | 1.3739                | +$647            | −$51             |
| weighted    | 1.2221       | 1.2212          | 1.2259                | −$38             | −$47             |
| **mean**    | **1.2953**   | **1.3125**      | **1.3205**            | **−$252**        | **−$81**         |

Absolute mean EV per profile (positive = winning, negative = losing money):

| Profile      | v3 EV    | v5_dt EV | v6_ensemble EV | BR-omniscient EV |
|--------------|----------|----------|----------------|------------------|
| mfsuitaware  | −0.7779  | −0.7369  | −0.7426        | +0.5913          |
| omaha        | +1.0117  | +0.8316  | +0.8148        | +2.1632          |
| topdef       | −0.8846  | −0.8149  | −0.8200        | +0.5539          |
| weighted     | +0.3779  | +0.3788  | +0.3741        | +1.6000          |
| **mean**     | **−0.0682** | **−0.0853** | **−0.0934** | **+1.2271**     |

**Headline:** the EV ceiling we're chasing is +$13K/1000h. Path A.2 captured 0% of it. Path A.1 (regression on per-setting EV) is the recommended next attempt.

### Session 20 → Session 21 deltas

- **Cheap-test harness shipped.** `analysis/scripts/cheap_test_oracle_hedges.py` evaluates a 200-hand sample against all 4 profiles to get the full 105×4 EV grid, then computes 7 oracle strategies' grand-mean EV. Verifies the +$13K ceiling in ~50s wall time.
- **4 per-profile DTs trained and extracted.** `data/v6_per_profile_dts.npz` (0.55 MB) holds depth-15 DTs (18.3K-19.9K leaves each) for `br_mfsuitaware / br_omaha / br_topdef / br_weighted`. Byte-identical sklearn-vs-manual-walk parity on full 6M for all 4. `analysis/scripts/extract_v6_per_profile_dts.py` is the training + parity harness.
- **Ensemble strategy callable.** `strategy_v6_ensemble(hand)` walks 4 trees and votes (mode + mfsuitaware tiebreak). Wired into `STRATEGIES` dict in `v3_evloss_baseline.py`. Drop-in callable like `strategy_v3` and `strategy_v5_dt`.
- **EV-loss baseline run on 2000 hands.** `data/v6_ensemble_records.parquet` (apples-to-apples with v3 and v5_dt records) at hands=2000, samples=1000, seed=42. Total time 493.9s (4.05 hands/sec, slightly faster than v5_dt's 4.0 hands/sec because feature compute is shared and the 4 tree walks are cache-warm).
- **Side-by-side compare harness.** `analysis/scripts/compare_v3_v5_v6.py` reads the 3 records parquets and emits the absolute-EV / EV-loss / $/1000h tables shown above.
- **Disagreement diagnostic.** `analysis/scripts/diag_v5_v6_disagreement.py` shows that on the 9.75% of hands where v5_dt and v6 differ, v6 loses 61% / wins 39% of the time. Worst-10 and best-10 hand-by-hand tables saved as reference for Session 22 hybrid attempts.

---

## What was completed this session (Session 21)

### Step 0 — Cheap-test for the path-(A) target pivot (Decision 039)

Per the user's "Discovery + 4-step doctrine" stance from Decision 033, started with cheap-test before any training. `cheap_test_oracle_hedges.py` does:
1. Sample N hands using the same seed=42 RNG as v3_evloss_baseline.
2. For each hand, call `evaluate_all_profiles` once per profile (4 calls) to get all 105 EVs.
3. Compute grand-mean EV for 9 strategies: v3, v5_dt, oracle_BR_per_profile, oracle_argmax_mean (A.1 ceiling), oracle_minimax_loss, oracle_argmax_<each profile>.

Headline at N=200: oracle_argmax_mean grand mean = **+1.172** vs v5_dt **−0.123** = **+1.295 EV/hand** = **+$12,949 / 1000 hands** at $10/EV-pt. Profile-known ceiling (oracle_BR_per_profile) is +1.285, so the hedge that's blind to profile recovers 92% of profile-known headroom.

Margin diagnostics (cheap test): argmax_mean median margin (1st vs 2nd setting by mean-EV) = 0.245 EV/hand. Only 15% of hands have margin <0.05 — the argmax is well-defined and learnable in principle.

Choice-agreement diagnostics: argmax_mean overlaps with v3 only **14.5%** and with v5_dt only **14.0%** — both production strategies are FAR from the optimum. Per-profile-BR overlaps with argmax_mean: mfsuit 77.5% / omaha 49.5% / topdef 68.5% / weighted 77.0% (this last set was the warning sign that A.2 ensemble would not be sufficient).

### Step 1 — Per-profile DT extraction (`extract_v6_per_profile_dts.py`)

Trained 4 sklearn DecisionTreeClassifiers at depth=15 on full 6M canonical hands with the same 37 features as v5_dt but per-profile br_<profile> as the target. Per-profile literal-agreement: 60.78% / 63.81% / 58.07% / 64.74%. Saved tree arrays + metadata to `data/v6_per_profile_dts.npz` (0.55 MB). Vectorised manual-walk parity check on full 6M = 0 diffs vs sklearn `predict()` for all 4 trees.

Vote-distribution sample (100K rows): 22.94% all 4 unanimous, 50.79% 2 distinct votes, 23.31% 3 distinct votes, 2.97% 4 distinct votes. So 50% of hands have a 2-distinct-vote pattern that includes both 3-1 and 2-2 splits.

### Step 2 — Ensemble strategy (`strategy_v6_ensemble.py`)

`strategy_v6_ensemble(hand: np.ndarray) -> int` reuses `compute_feature_vector` from `strategy_v5_dt.py` (same 37 features), walks all 4 trees, votes mode-of-4. Tiebreak: 2-2 split or 4 distinct → fall back to mfsuitaware DT's vote (the most-common-profile-of-record per Decision 005, and the highest single-profile overlap with oracle_argmax_mean per the cheap test). Wired into `STRATEGIES` dict in `v3_evloss_baseline.py`.

### Step 3 — EV-loss baseline + side-by-side compare (Decision 040)

`v3_evloss_baseline.py --strategy v6_ensemble --hands 2000 --samples 1000 --seed 42 --save data/v6_ensemble_records.parquet`. Total time 493.9s. Same 2000 hands as v3 and v5_dt baselines (verified by hand_str overlap).

Result: v6 mean loss 1.3205 > v5_dt 1.3125 > v3 1.2953. **v6 is worse than both v5_dt and v3 on grand mean.** Per-profile losses on every profile are slightly worse than v5_dt; omaha is the single biggest absolute hit (−$168/1000h).

### Step 4 — Disagreement diagnostic (`diag_v5_v6_disagreement.py`)

The killer diagnostic: **v5_dt and v6_ensemble agree on 90.25% of the 2000 hands.** Of the 195 (9.75%) disagreement hands:
- v6 wins (lower mean loss):  76 (39.0%)
- v6 loses (higher mean loss): 119 (61.0%)

Worst-10 disagreement hands show patterns where v5_dt picks the right setting (e.g. setting 90 for `2d 3c 3s 4c 8h 9d 9h`) and v6 picks something significantly worse (setting 5, +1.79 mean loss delta). The mfsuitaware tiebreak is biased toward mfsuit-style settings even when omaha-style would be EV-better.

### Step 5 — Test suites

- Rust: `cargo test --release` → **124/124 pass** (88 + 15 + 15 + 6, unchanged from Session 20).
- Python: pytest on six test files → **74/74 pass** (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden, unchanged).

---

## Files added this session

- `analysis/scripts/cheap_test_oracle_hedges.py` — 200-hand cheap-test harness; computes 9 oracle strategies' grand-mean EV from full 105×4 EV grid; saves grid + choices to .npz.
- `analysis/scripts/extract_v6_per_profile_dts.py` — trains 4 depth-15 DTs on br_<profile> targets; saves `data/v6_per_profile_dts.npz`; runs sklearn-vs-walk parity check on full 6M for each tree.
- `analysis/scripts/strategy_v6_ensemble.py` — `strategy_v6_ensemble(hand)` callable; mode-of-4 vote with mfsuitaware tiebreak.
- `analysis/scripts/compare_v3_v5_v6.py` — reads v3 / v5_dt / v6_ensemble records parquets; prints absolute-EV / EV-loss / $/1000h tables.
- `analysis/scripts/diag_v5_v6_disagreement.py` — 90.25% agreement diagnostic; worst-10 / best-10 disagreement-hand tables; per-profile EV impact split.
- `data/cheap_test_oracle_grid_200.npz` — 218 KB. Full 105×4×200 EV grid + v3/v5_dt choices + per-hand argmax_mean / minimax_loss / per-profile BRs.
- `data/v6_per_profile_dts.npz` — 0.55 MB. 4 sklearn-tree arrays + cat_map + feature_columns + literal_acc per profile.
- `data/v6_ensemble_records.parquet` — 2000 hands × 4 profiles EV records under `strategy_v6_ensemble`. Same schema as v3 and v5_dt records.

## Files modified this session

- `analysis/scripts/v3_evloss_baseline.py` — added `from strategy_v6_ensemble import strategy_v6_ensemble` + registered in `STRATEGIES`.
- `CURRENT_PHASE.md` — rewritten.
- `DECISIONS_LOG.md` — appended Decision 039 (cheap-test) + Decision 040 (A.2 null result).
- `handoff/MASTER_HANDOFF_01.md` — appended Session 21 entry.

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass.
- `extract_v6_per_profile_dts.py`: 0 diffs sklearn-vs-manual-walk on full 6M for all 4 trees.
- `compare_v3_v5_v6.py`: hand_str overlap = 2000 of 2000 across v3/v5_dt/v6 records (apples-to-apples comparison confirmed).
- `diag_v5_v6_disagreement.py`: literal-agreement on agreement subset = 100.00% (Δ EV = 0.0000 across all 4 profiles, sanity check on the EV grid).

## Gotchas + lessons

- **Voting 4 weak classifiers is not enough to reach the hedge ceiling.** Each per-profile DT achieves only 58-65% literal accuracy on its own target. The modal vote often equals `multiway_robust` (because mode-of-4 ≈ mode-of-mode in shape distribution), so v6 mostly reproduces v5_dt's choice. The 50% of hands with a 2-2 tie pattern push v6 to the mfsuitaware fallback, which is biased away from omaha-favoring settings — and omaha is where v3 was already winning by hand-tuned overlay.
- **The cheap-test SAW the warning.** argmax_mean overlap with each per-profile BR ranged 49.5%-77.5%. We weighted this correctly as "per-profile DTs vote should ≈ argmax_mean," but the empirical result is closer to "per-profile DT votes ≈ multiway_robust" because of (a) DT noise compounding across 4 weak classifiers, and (b) the tiebreak heuristic biasing toward a single profile. The lesson: weak-classifier voting cannot reach an oracle ceiling that is structurally far from any single classifier's training target.
- **The 4-step doctrine continues to be a session-saver.** ~1 hour of total work (training + 8.3-min MC + diagnostics) produced a clean negative result for A.2. Without the doctrine, we might have committed the 14-hour MC to A.1 first based on the cheap-test alone, when A.2 was the cheaper test that could have been done first. The order — cheap-test → cheap-train → expensive-MC if needed — is the right cadence.
- **Choice-agreement is a leading indicator of EV impact.** v5_dt vs v6 = 90.25% literal-agreement → at most ~10% of EV impact is reachable by changing the rest. This is a useful heuristic for future strategy candidates: if a candidate has >85% choice-overlap with v5_dt, the maximum EV impact is bounded by what the candidate can do on the small disagreement subset.

---

## Resume Prompt (Session 22)

```
Resume Session 22 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 21)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decisions 039 + 040 — cheap-test + A.2 null result)
- handoff/MASTER_HANDOFF_01.md (Session 21 entry just added)
- analysis/scripts/cheap_test_oracle_hedges.py (oracle hedge harness)
- analysis/scripts/strategy_v5_dt.py (production v5_dt callable)
- analysis/scripts/strategy_v6_ensemble.py (null-result A.2 ensemble — for reference only)
- analysis/scripts/compare_v3_v5_v6.py (side-by-side comparison harness)
- data/cheap_test_oracle_grid_200.npz (105×4×200 EV grid)
- data/v3_evloss_records.parquet, data/v5_dt_records.parquet,
  data/v6_ensemble_records.parquet (apples-to-apples baselines)

State of the project (end of Session 21):
- Cheap-test confirmed argmax_mean ceiling = +$12,949/1000h vs v5_dt at $10/EV-pt.
- v6_ensemble (path A.2 per-profile DT vote) is a NULL RESULT:
  - 90.25% choice-agreement with v5_dt.
  - −$81/1000h vs v5_dt, −$252/1000h vs v3.
  - 4 per-profile DTs at 58-65% literal accuracy are too weak for voting.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(A.1) DT regression on per-setting EV. The cheap-test ceiling is real; the
      gap is in target type, not training algorithm. Path:
        1. Generate a per-setting × per-profile EV training set via MC. The
           existing cheap_test_oracle_hedges.py harness does this — extend
           it from 200 hands to 50K hands. Cost: ~14 hours overnight.
        2. Train 4 per-profile regression DTs (sklearn DecisionTreeRegressor)
           on (hand_features, setting_index) → ev_per_profile. At inference,
           predict EV for each of 105 settings × 4 profiles, average across
           profiles, argmax over 105.
        3. Evaluate via v3_evloss_baseline.py --strategy v7_regression
           --hands 2000 --samples 1000 --seed 42.
      Apply the 4-step doctrine BEFORE committing to the 14-hour MC: do a
      pilot at 5K hands (~1.4 hours), train, evaluate. If pilot shows EV
      gain over v5_dt, scale to 50K. Else pivot.

(B) Hybrid + EV-aware tiebreak. Cheaper than A.1 but smaller upside.
      1. For each canonical hand, compute the 4-DT ensemble prediction.
         If unanimous AND v5_dt agrees → keep v5_dt.
         If unanimous BUT v5_dt disagrees → switch to ensemble.
         If split → keep v5_dt.
      The asymmetric "trust unanimity, distrust 2-2 ties" rule could
      capture a portion of the +$13K ceiling without retraining.
      Estimated cost: ~1 hour implementation + 9-min MC.

(C) Larger cheap-test (1000 or 2000 hands) to reduce variance. The 200-hand
      argmax_mean estimate of +$12,949/1000h has SE ~ ±$1,500 at the noise
      level we're working with. A 2000-hand grid (cost ~33 min MC) would
      tighten the band to ±$500 and could verify whether the ceiling at
      scale exceeds Session 20's omaha asymmetry of −$1,801. ALSO this
      grid would be useful as a starter training set for path A.1.

The user has previously chosen (A)-paths and is in discovery mode. Path (A.1)
is recommended for Session 22, with the staged 5K-pilot-then-50K cadence
to honor the 4-step doctrine. Path (C) is a useful stepping stone — running
2000-hand cheap-test grid first gives both a tighter ceiling estimate AND
a starter training set, before committing to the 14-hour 50K MC.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.

Session-end protocol (mandatory): commit + push to origin/main per
session-end-prompt.md. Push is pre-authorized per persistent memory.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
