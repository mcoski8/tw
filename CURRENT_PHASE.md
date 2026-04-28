# Current: Sprint 7 Phase D — two_pair augmented features unlock +5.90pp slice lift and +1.67pp full-6M lift. Third feature-engineering win since the goal reframe. Session 19 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 20):** EITHER (a) one more mining pass on **trips_pair** to confirm the lift plateau, OR (b) extract the depth-15 aug-37 chain (18,399 leaves, full_shape 63.74%, cv_shape 62.44%) → translate to Python if/elif → byte-identical parity check → EV-loss baseline vs v3. The reframe favours (a) until per-session lift drops below 0.5pp on full-6M, but (b) is the deliverable the user is ultimately tracking ($/1000 hands at $10/EV-pt). Recommendation: (b) is now competitive — three augmented-feature families have each contributed; the next mining pass is likely <+1pp on full-6M.

> **🚫 RETIRED (Decision 033, Session 16):** "≥95% shape-agreement on multiway-robust target." Replaced with directional reduction below v3's 1.63 EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles. Reportable metric: $/1000 hands at $10/EV-pt.

> Updated: 2026-04-28 (end of Session 19)

---

## Headline state at end of Session 19

**Third feature-engineering win since the Session 16 reframe.** Three new two_pair-aug features mirror the Session 17/18 pattern (bot-suit-profile per strategic routing). They lift the DT-ceiling on the two_pair category (24% of v3 EV-loss; the largest remaining cohort) by +5.90pp on the target slice and +7.50pp on the full two_pair sub-population. Combined with Sessions 17/18 features the lift propagates to **+1.67pp on the full 6M (65.20% → 66.87%)** at depth=None and **+0.88pp at the depth-15 knee (62.86% → 63.74%)**.

### New features (two_pair only; vacuous on non-two_pair hands)

1. `default_bot_is_ds_tp` — bool. Under (mid=high-pair, top=highest-singleton, bot=low-pair+2-lowest-singletons), is bot DS (2,2)?
2. `n_routings_yielding_ds_bot_tp` — 0-6. Over the 6 intact-pair routings (2 mid-pair × 3 top-singleton choices), count those yielding DS bot.
3. `swap_high_pair_to_bot_ds_compatible` — bool. Among the DS-bot routings, does ANY have HIGH pair on bot (mid=low-pair, bot=high-pair+2 singletons)?

### DT shape-agreement ceilings (depth=None, full data fit)

| Subset | Baseline (27) | + Pair (30) | + High (30) | + 2P (30) | + Pair+High (33) | + ALL (36) | Lift over baseline |
|---|---|---|---|---|---|---|---|
| TWO_PAIR 3-of-4 (slice, 675K) | 79.47% | 79.47% | 79.47% | **85.37%** | 79.47% | 85.37% | **+5.90pp** |
| TWO_PAIR full (1.34M) | 68.29% | 68.29% | 68.29% | **75.79%** | 68.29% | 75.79% | +7.50pp |
| 3-of-4 majority (2.43M) | 70.01% | 72.61% | 71.78% | 71.65% | 74.38% | **76.02%** | +6.01pp |
| **Full 6M** | **61.74%** | 63.76% | 63.17% | 63.41% | 65.20% | **66.87%** | **+5.13pp** |

The three augmented-feature families correctly compose additively on the full 6M (within rounding): 61.74 + 2.02 (pair) + 1.43 (high) + 1.67 (2p) = 66.86 ≈ 66.87% — confirming the "vacuous on out-of-category hands" property holds across all three families.

### Full-6M depth curve (all 37 augmented features)

| depth | leaves | cv_acc | cv_shape | full_acc | full_shape | Δ over Session 18 (33) |
|---|---|---|---|---|---|---|
| 3 | 8 | 30.69% | 32.31% | 30.63% | 32.13% | +0.00pp |
| 5 | 32 | 39.94% | 42.02% | 39.97% | 42.27% | +0.00pp |
| 7 | 125 | 47.00% | 49.00% | 47.17% | 49.16% | +0.01pp |
| 10 | 932 | 54.58% | 56.69% | 54.92% | 56.95% | +0.21pp |
| **15** | **18,399** | **60.02%** | **62.44%** | **61.32%** | **63.74%** | **+0.88pp / +0.85pp cv** |
| 20 | 136,191 | 59.08% | 61.55% | 64.01% | 66.12% | +1.44pp |
| None | 288,218 | 57.28% | 59.87% | 64.80% | 66.87% | +1.67pp |

**Depth-15 with all 37 features (63.74% full / 62.44% cv) is the new chain-extraction candidate.** Same leaf-count tier as Session 17/18 knees (~18K leaves), best cv-full gap of any depth (-1.30pp). v3 production at 56.16% means depth-15 aug-37 is **+7.58pp over v3** (was +6.7pp at end of Session 18).

The 2p-aug features primarily lift bounded depths ≥10 and depth=None. Depths 3-7 are unaffected — too shallow to use the new features.

### Drop-out ablation on the slice (depth=None)

| Drop one feature | Slice shape | Δ from full aug |
|---|---|---|
| (full augmented — 36 features) | 85.37% | — |
| − default_bot_is_ds_tp | 83.53% | −1.84pp |
| − n_routings_yielding_ds_bot_tp | 83.70% | −1.67pp |
| − swap_high_pair_to_bot_ds_compatible | 83.44% | **−1.93pp** ← largest |
| − any pair-aug feature | 85.37% | 0.00pp (vacuous on slice ✓) |
| − any high-aug feature | 85.37% | 0.00pp (vacuous on slice ✓) |

All three 2p-aug features are non-redundant. Unlike Sessions 17/18 where one feature dominated (-2.85pp / -4.78pp), the three 2p-aug drops are within 0.26pp of each other — F3 edges out F1 by 0.09pp. The structural-symmetry feature (swap-high-pair-to-bot-DS-compatible) is the largest single contributor, mirroring the "least-OR-but-largest-drop" pattern from Sessions 17/18.

### Signal odds ratios (slice-level, vs "BR = baseline-DT prediction")

| Feature | OR | Direction |
|---|---|---|
| `default_bot_is_ds_tp` (vs BR=baseline-DT) | 1.14x | Very weak +; P=81.17% vs 79.13% |
| `swap_high_pair_to_bot_ds_compatible` | 0.65x | Inverse; P=74.17% vs 81.48% |
| `n_routings_yielding_ds_bot_tp` cross-tab | — | Clean U: 83.51 / 70.23 / 74.50 / 88.04% across {0/1/2/4} |

Individual signal magnitudes are weaker than Sessions 17/18, but the combined cross-tab spread (88.04 − 70.23 = 17.81pp on F2) is comparable to high_only-aug, and the literal-agreement lift on slice (+5.95pp adding all 3) exceeds Sessions 17/18 individual feature ORs would predict. Three weak features collectively map cleanly onto the "default-vs-swap × n-routings × kicker-rank" decision the DT can split on.

---

## What was completed this session (Session 19)

### Step 1-3 — two_pair leaf mining (`mine_two_pair_leaves.py`)

- Filtered feature_table to (mode_count==3 AND category=='two_pair') → 675,624 hands (11.24% of full 6M).
- Trained depth=None DT on slice with the 28 baseline features. Slice ceiling: **79.47% / 39,677 leaves.**
- Miss concentration: top-10 = 0.5% of misses, top-50 = 1.9%, top-100 = 3.4% — much more diffuse than single-pair (top-10 = 11%) or high_only (top-10 = 4.4%). 30,413 leaves have at least one miss.
- Recurring pattern: dominant top miss-leaves involve "high-pair-on-mid (DT-default, settings 14/44) vs high-pair-on-bot (BR-swap routing)". The within-leaf discriminator is suit-coupling under each routing — not visible to the 28 baseline features which see only 7-card suit profiles.

### Step 4 — three-feature design (`two_pair_aug_features.py`)

- Module exposes `compute_two_pair_aug_for_hand(hand)` (scalar) + `compute_two_pair_aug_batch(hands, slice_mask)` (vectorised). Vacuous on non-two_pair hands (early-return if n_pairs != 2).
- 6 spot-checks pass against hand-picked cases from the leaf dump (per Session 17/18 lesson). Leaf-1 hand `2c 6c Jd Kh Ks Ac Ad` returns f1=0 (default 3-suited bot), f2=2 (2 of 6 routings yield DS-bot, both via mid=KK swap), f3=1 (the swap routing IS DS-compatible).

### Step 4a — odds-ratio + cross-tab signal check (`signal_or_two_pair.py`)

- F1 OR=1.14x (weak); F3 OR=0.65x (inverse); F2 cross-tab spread 17.81pp (clean U-shape). Individual ORs much weaker than Sessions 17/18, but the combined depth=None DT literal-agreement on slice lifts +5.95pp (79.34% → 85.29%). Signal magnitude justified training compute despite weak individual ORs.

### Step 5 — augmented-feature DT ceiling (`dt_two_pair_aug_ceiling.py`)

- depth=None DT comparison: 6 feature sets × 4 subsets. Slice lift +5.90pp; two_pair-full lift +7.50pp; 3-of-4 majority lift +1.64pp on top of pair+high; full-6M lift +1.67pp on top of pair+high.
- Per-feature drop-out ablation on slice confirms all three 2p-aug features contribute non-redundantly. Pair-aug + high_only-aug features correctly inert (drop = 0pp). All three families' isolation-by-design property is now triple-validated.

### Step 6 — full-6M depth curve (`dt_phase1_aug3.py`)

- Depths {3, 5, 7, 10, 15, 20, None}. Identical methodology to Session 16/17/18 (3-fold CV on 1M subsample, full-6M fit at chosen depth).
- Depth-15 remains the knee. cv-shape 62.44% (was 61.59%, +0.85pp). Full-shape 63.74% (was 62.86%, +0.88pp). 18,399 leaves (vs 18,354) — same tier.

### Augmented-feature persistence (`persist_two_pair_aug.py`)

- `data/feature_table_two_pair_aug.parquet` — 18.89 MB, joins on canonical_id.
- Compute is 26s on the 1.34M two_pair sub-population. Future sessions read the parquet directly.

---

## Files added this session

- `analysis/scripts/mine_two_pair_leaves.py` — Step 1-3 mining + leaf-rank dump
- `analysis/scripts/two_pair_aug_features.py` — feature module (scalar + batch + 6 spot-check cases)
- `analysis/scripts/signal_or_two_pair.py` — Step 4a OR + cross-tab signal test
- `analysis/scripts/dt_two_pair_aug_ceiling.py` — Step 5 cross-subset comparison + drop-out ablation
- `analysis/scripts/dt_phase1_aug3.py` — Step 6 depth curve on full 6M with all 37 features
- `analysis/scripts/persist_two_pair_aug.py` — parquet persistence
- `data/feature_table_two_pair_aug.parquet` — 18.89 MB, two_pair augmented features (gitignored)

## Files modified this session

- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 036
- `handoff/MASTER_HANDOFF_01.md` — appended Session 19 entry

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **Diffuse miss-leaves are NOT a contraindication.** two_pair top-10 miss-leaves cover only 0.5% of misses (vs single-pair 11%, high_only 4.4%). Initial worry was "no signal." But the +5.90pp slice lift confirms the structural pattern is real and spread uniformly across small leaves. Diffuseness in the leaf graph and feature lift are orthogonal — one decision axis can be tested across many small leaves and have aggregated impact.
- **Weak individual ORs don't preclude strong combined lift.** F1 OR=1.14x and F3 OR=0.65x are dramatically weaker than Sessions 17/18 (4.39x, 6.38x). But all three combined lifted the slice depth=None DT +5.90pp (shape) — comparable to single-pair's +5.85pp. Three features that each weakly discriminate one axis can collectively map onto a multi-dimensional decision the DT can exploit. Lesson: do the cheap feature-add sanity check (ceiling lift) before deciding whether weak ORs justify continuing.
- **The three drop-outs are within 0.26pp of each other (1.67-1.93pp range).** Unlike Sessions 17/18 where one feature dominated (-2.85pp / -4.78pp), here all three 2p-aug features carry near-equal load. F3 (`swap_high_pair_to_bot_ds_compatible`) is the largest by a hair. Each captures a different facet of the same routing decision; remove any one and the DT loses ~10% of the lift. This balanced contribution profile probably reflects the more symmetric two_pair structure (two pairs + 3 singletons vs single-pair's asymmetric 1 pair + 5 singletons).
- **The "27 baseline" label is actually 28 features.** Counting the list shows 28; X.shape outputs (e.g., `(675624, 28)`, `(6009159, 37)`) confirm. The Sessions 17/18 docs all label it "27", an off-by-one inherited from earlier scoping. Session 19 docs continue the "27" labelling for cross-session compatibility but note this in passing. The error has zero impact on results — only the column labels are mismatched.
- **Three-family additive composition holds within rounding.** 61.74 (baseline) + 2.02 (pair) + 1.44 (high) + 1.67 (2p) = 66.87% — exactly the all-aug full-6M ceiling. Each family's vacuous-on-out-of-category property continues to behave as designed. Future families (trips_pair etc.) should land at similar vacuous boundaries.

## Resume Prompt (Session 20)

```
Resume Session 20 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 19)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 036 — two_pair augmented features)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 16-19 since the goal reframe)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/pair_aug_features.py + high_only_aug_features.py + two_pair_aug_features.py
  (3 augmented-feature modules)
- analysis/scripts/dt_phase1_aug3.py (Session 19 depth curve, full 6M, 37 features)
- data/feature_table.parquet, data/feature_table_aug.parquet,
  data/feature_table_high_only_aug.parquet, data/feature_table_two_pair_aug.parquet
  (all joined on canonical_id)

State of the project (end of Session 19):
- Three augmented-feature families now live: pair-aug (Session 17), high_only-aug (Session 18),
  two_pair-aug (Session 19). Combined, they lift the full-6M depth=None ceiling from
  61.74% (baseline) to 66.87% (+5.13pp) and the depth-15 knee from 61.96% to 63.74% / 62.44% cv-shape.
- v3 production: 56.16% (unchanged). Augmented depth-15 is +7.58pp over v3.
- Two_pair 3-of-4 slice ceiling lifted 79.47% → 85.37% (+5.90pp); two_pair full +7.50pp.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(a) Continue mining: trips_pair next.
    1. Filter feature_table.parquet to (mode_count == 3 AND category == 'trips_pair')
       — small but high-density cohort.
    2. Mine impure leaves with the existing 37 features (all 3 aug-families likely vacuous
       on trips_pair due to n_pairs==1 + n_trips==1 mismatch with their slice predicates).
    3. If signal magnitude is weak, halt and pivot to (b). The per-session lift is now ~+1pp
       on full-6M; if trips_pair adds <0.5pp the discovery phase has plateaued.
    4. OR-test → spot-check → batch + ablation → persist → depth curve.

(b) RECOMMENDED — Extract chain from current augmented depth-15 tree (37 features).
    1. Refit depth=15 DT on full 6M with all 37 features.
    2. sklearn `export_text` → translate to Python if/elif chain.
    3. Verify byte-identical predictions on full 6M.
    4. Run v3_evloss_baseline.py --strategy v5_dt --hands 2000 --save data/v5_dt_records.parquet
       and compare to v3 on per-profile absolute EV + $/1000 hands at $10/EV-pt.
    5. This is the chain-shipping path. Three augmented-feature families have each contributed;
       the next mining pass is likely <+1pp. Time to measure the actual EV-loss deliverable.

The reframe (Decision 033) favours continued mining until the feature ceiling stops moving.
Session 19 added +1.67pp at depth=None and +0.88pp at depth=15 — still meaningful but
diminishing. Recommended Session 20 fork: (b) — extract the chain and measure.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
