# Current: Sprint 7 Phase D — high_only augmented features unlock +9.28pp slice ceiling and +1.44pp full-6M ceiling. Second feature-engineering win since the goal reframe. Session 18 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 19):** EITHER (a) repeat the mining-and-augment loop on **two_pair** (24% of v3 EV-loss; largest remaining cohort), OR (b) extract a depth-15 chain from the augmented full-6M tree (18,354 leaves, full_shape 62.86%, cv_shape 61.59%) → translate to Python if/elif → byte-identical parity check → EV-loss baseline vs v3. (b) is the chain-shipping path; (a) is more discovery before commitment. Recommended: (a) first to lift the ceiling further, then (b) once the augmented-feature set has stabilised.

> **🚫 RETIRED (Decision 033, Session 16):** "≥95% shape-agreement on multiway-robust target." Replaced with directional reduction below v3's 1.63 EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles. Reportable metric: $/1000 hands at $10/EV-pt.

> Updated: 2026-04-28 (end of Session 18)

---

## Headline state at end of Session 18

**Second feature-engineering win since the Session 16 reframe.** Three new high_only-only features mirror the Session 17 pattern (bot-suit-profile per strategic routing). They lift the DT-ceiling on the high_only category (12.6% of EV-loss) by +9.28pp on the target slice; combined with the Session 17 pair-aug features the lift propagates to +1.44pp on the full 6M.

### New features (high_only only; vacuous on non-high_only hands)

1. `default_bot_is_ds_high` — bool. Under NAIVE_104 (top=byte[6], mid=bytes(4,5), bot=bytes(0..3)), is bot DS (2,2)?
2. `n_mid_choices_yielding_ds_bot` — 0-15. Top fixed at byte[6]; count of C(6,2) mid-pair choices from the remaining 6 that yield a DS bot.
3. `best_ds_bot_mid_max_rank` — 0 or 4-14. Top fixed at byte[6]; among DS-bot-yielding mid choices, the maximum rank that can appear in mid. Encodes the rank-cost of routing-for-DS-bot.

### DT shape-agreement ceilings (depth=None, full data fit)

| Subset | Baseline (27) | Pair-aug (30) | High-aug (30) | All Aug (33) | Lift over baseline |
|---|---|---|---|---|---|
| HIGH_ONLY 3-of-4 (target slice, 463K) | 39.64% | 39.64% | **48.92%** | 48.92% | **+9.28pp** |
| HIGH_ONLY full (1.23M) | 30.87% | 30.87% | 37.89% | 37.89% | +7.02pp |
| 3-of-4 majority (2.43M) | 70.01% | 72.61% | 71.78% | **74.38%** | +4.37pp |
| **Full 6M** | **61.74%** | **63.76%** | **63.17%** | **65.20%** | **+3.46pp** |

The pair-aug and high_only-aug feature families are correctly isolated by category — drop-out delta = 0pp on each family when measured outside its target slice. Feature lifts compose additively (~62% on full 6M from each family ≈ 65.20% − 61.74% = 3.46pp).

### Full-6M depth curve (all 33 augmented features)

| depth | leaves | cv_acc | cv_shape | full_acc | full_shape |
|---|---|---|---|---|---|
| 3 | 8 | 30.69% | 32.31% | 30.63% | 32.13% |
| 5 | 32 | 39.94% | 42.01% | 39.97% | 42.27% |
| 7 | 125 | 46.99% | 48.98% | 47.16% | 49.15% |
| 10 | 939 | 54.42% | 56.51% | 54.72% | 56.74% |
| **15** | **18,354** | **59.17%** | **61.59%** | **60.44%** | **62.86%** |
| 20 | 122,596 | 57.75% | 60.11% | 62.56% | 64.68% |
| None | 229,271 | 56.10% | 58.60% | 63.12% | 65.20% |

**Depth-15 with all 33 features (62.86% full / 61.59% cv) is the new chain-extraction candidate.** It lifts the Session 17 depth-15 knee (62.0% / 60.7%) by +0.86pp / +0.92pp, with the same leaf-count tier and best cv-full gap. v3 production at 56.16% means depth-15 aug-33 is **+6.7pp over v3.**

### Drop-out ablation on the slice (depth=None)

| Drop one feature | Slice shape | Δ from full aug |
|---|---|---|
| (full augmented — 33 features) | 48.92% | — |
| − default_bot_is_ds_high | 45.76% | −3.15pp |
| − n_mid_choices_yielding_ds_bot | 47.73% | −1.19pp |
| − best_ds_bot_mid_max_rank | 44.13% | **−4.78pp** ← largest |
| − any pair-aug feature | 48.92% | 0.00pp (vacuous on slice ✓) |

`best_ds_bot_mid_max_rank` is the largest contributor — repeating Decision 034's lesson that signal magnitude ≠ contribution magnitude. F3's stand-alone OR was the weakest of the three (U-shape across bins, no clean +/-), but it captures the rank-cost-of-DS-bot tradeoff that the DT alone cannot derive.

### Signal odds ratios (slice-level, vs "BR uses NAIVE_104 routing")

| Feature | OR | Direction |
|---|---|---|
| `default_bot_is_ds_high` (vs BR=NAIVE) | 6.38x | + (P(NAIVE\|F1=1)=57.32% vs 17.40%) |
| `best_ds_bot_mid_max_rank` 0 (no DS-bot) | — | 36.09% NAIVE (settle) |
| `best_ds_bot_mid_max_rank` 4-8 (low-mid sacrifice) | — | 10.29% NAIVE (deviate) |
| `best_ds_bot_mid_max_rank` 11-12 (broadway J/Q OK) | — | 23.45% NAIVE |
| `best_ds_bot_mid_max_rank` 13-14 (broadway K/A OK) | — | 42.36% NAIVE (keep) |

The U-shape on F3 is exactly the "tradeoff cost" decision: when DS-bot is achievable AND broadway can stay in mid, BR uses NAIVE; when DS-bot requires sacrificing broadway, BR deviates.

### Slice ceiling vs Session 13's "~50% opponent-dependent cap"

The slice ceiling of 48.92% lands within ~1pp of Session 13's empirical "single deterministic rule cannot exceed ~50% on high_only" finding. Further high_only-specific feature engineering will hit diminishing returns on the multiway-robust target — the remaining gap is intrinsic opponent-dependence. Future high_only gains likely require a per-profile chain or weighted ensemble rather than more features.

---

## What was completed this session (Session 18)

### Step 1-3 — high_only leaf mining (`mine_high_only_leaves.py`)

- Filtered feature_table to (mode_count==3 AND category=='high_only') → 463,547 hands (7.71% of full 6M).
- Trained depth=None DT on slice with the 27 baseline features. Slice ceiling: **39.64% / 4,544 leaves.**
- Miss concentration: top-10 = 4.4% of misses, top-50 = 15.5%, top-100 = 24.7%. Diffuse across 4,176 miss-leaves but the dominant top-15 share the same structural pattern.
- Recurring blind spot: bot suit profile under NAIVE_104. Existing `suit_2nd ≥ 2` only sees "DS-bot achievable somewhere"; cannot see "the SPECIFIC bot under default routing is 3-suited and BR demotes broadway from mid → bot to repair it".

### Step 4 — three-feature design (`high_only_aug_features.py`)

- Module exposes `compute_high_only_aug_for_hand(hand)` (scalar) and `compute_high_only_aug_batch(hands, slice_mask)` (vectorised). Vacuous on non-high_only hands.
- 5 spot-checks pass against hand-picked cases from the leaf dump (per Session 17 lesson). The Leaf-1 hand `2c 3c 6c 7d Jh Qh Ks` returns f1=0 (default 3-suited), f2=3 (3 mid choices yield DS bot — manual verification confirms), f3=7 (best mid-max with DS bot is 7-rank → BR's actual choice).

### Step 4a — odds-ratio + cross-tab signal check (`signal_or_high_only.py`)

- F1 OR=6.38x; F3 clean U-shape across bins. F1 × F2 cross-tab cleanly separates 12% vs 53-68% NAIVE-rate. Signal magnitude justified training compute.

### Step 5 — augmented-feature DT ceiling (`dt_high_only_aug_ceiling.py`)

- depth=None DT comparison: 4 feature sets × 4 subsets. Slice lift +9.28pp; full-6M lift +1.44pp; 3-of-4 majority lift +1.77pp.
- Per-feature drop-out ablation on slice confirms all three high_only-aug features contribute non-redundantly. Pair-aug features correctly inert (drop = 0pp).

### Step 6 — full-6M depth curve (`dt_phase1_aug2.py`)

- Depths {3, 5, 7, 10, 15, 20, None}. Identical methodology to Session 16/17 (3-fold CV on 1M subsample, full-6M fit at chosen depth).
- Depth-15 remains the knee. cv-shape 61.59% (was 60.71%, +0.92pp). Full-shape 62.86% (was 61.96%, +0.86pp).

### Augmented-feature persistence (`persist_high_only_aug.py`)

- `data/feature_table_high_only_aug.parquet` — 18.75 MB, joins on canonical_id.
- Compute is 43.2s on the 1.23M high_only sub-population. Future sessions read the parquet directly.

---

## Files added this session

- `analysis/scripts/mine_high_only_leaves.py` — Step 1-3 mining + leaf-rank dump
- `analysis/scripts/high_only_aug_features.py` — feature module (scalar + batch + 5 spot-check cases)
- `analysis/scripts/signal_or_high_only.py` — Step 4a OR + cross-tab signal test
- `analysis/scripts/dt_high_only_aug_ceiling.py` — Step 5 cross-subset comparison + drop-out ablation
- `analysis/scripts/dt_phase1_aug2.py` — Step 6 depth curve on full 6M with all 33 features
- `analysis/scripts/persist_high_only_aug.py` — parquet persistence
- `data/feature_table_high_only_aug.parquet` — 18.75 MB, high_only augmented features

## Files modified this session

- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 035
- `handoff/MASTER_HANDOFF_01.md` — appended Session 18 entry

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **Slice ceiling of 39.64% on high_only is genuinely low — but routing-aware features lift it +9.28pp.** Session 13's empirical "~50% cap on high_only" was against rule-based strategies. A DT with the right features approaches that cap. Further high_only-specific features hit diminishing returns; remaining gap is intrinsic opponent-dependence.
- **Diffuse miss concentration ≠ no signal.** high_only miss-leaves are spread across 4,176 with top-100 covering only 24.7% (vs single-pair's tighter cluster). But the dominant top-15 leaves share one structural pattern (bot-suit-under-default-routing). Diffuseness in the leaf graph does not contradict a clean structural signal — features lift the floor uniformly.
- **F3 (best_ds_bot_mid_max_rank) is again the largest contributor — and again has the weakest stand-alone signal.** Repeating Decision 034's lesson: signal magnitude ≠ contribution magnitude. Always run drop-out ablation; never trust signal magnitude as a contribution proxy.
- **Pair-aug features are correctly vacuous on the high_only slice.** Drop-out delta = 0pp on all three pair-aug features when measured on the high_only slice. Confirms feature isolation by design and validates additive composition: total full-6M lift +3.46pp ≈ pair-aug +2.02pp + high-aug +1.44pp.
- **Augment compute scales with slice size.** `compute_high_only_aug_batch` iterates `np.where(slice_mask)[0]` only — 43s for 1.23M high_only rows. Future category-aug modules should follow the same pattern.

## Resume Prompt (Session 19)

```
Resume Session 19 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 18)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 035 — high_only augmented features)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 16-18 since the goal reframe)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/pair_aug_features.py + high_only_aug_features.py (feature modules)
- analysis/scripts/dt_phase1_aug2.py (Session 18 depth curve, full 6M, 33 features)
- data/feature_table.parquet, data/feature_table_aug.parquet,
  data/feature_table_high_only_aug.parquet (joined on canonical_id)

State of the project (end of Session 18):
- Two augmented-feature families now live: pair-aug (Session 17) + high_only-aug (Session 18).
  Combined, they lift the full-6M depth=None ceiling from 61.74% (baseline) to 65.20% (+3.46pp)
  and the depth-15 knee from 61.96% to 62.86% / 61.59% cv-shape.
- v3 production: 56.16% (unchanged). Augmented depth-15 is +6.7pp over v3.
- High_only 3-of-4 slice ceiling lifted 39.64% → 48.92% (+9.28pp) — within ~1pp of the
  Session 13 empirical "opponent-dependent" cap.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(a) RECOMMENDED — Continue mining: two_pair next.
    1. Filter feature_table.parquet to (mode_count == 3 AND category == 'two_pair')
       — 24% of v3 EV-loss; the largest remaining cohort.
    2. Mine impure leaves with the existing 33 features (pair-aug fires partially
       — n_pairs==2 not 1, so feature semantics may need adapting; check first).
    3. Hypothesise 1-3 two_pair-specific features (likely: which-pair-on-bot,
       broadway-pair-vs-low-pair routing, pair-suit-coupling).
    4. OR-test → spot-check → batch + ablation → persist → depth curve.
    5. Optional: trips_pair after two_pair.

(b) Alternative — Extract chain from current augmented depth-15 tree (33 features).
    1. Refit depth=15 DT on full 6M with all 33 features.
    2. sklearn `export_text` → translate to Python if/elif chain.
    3. Verify byte-identical predictions on full 6M.
    4. Run v3_evloss_baseline.py --strategy v5_dt and compare to v3 on
       per-profile absolute EV + $/1000 hands at $10/EV-pt.

(a) is more discovery before commitment; (b) ships a chain. The reframe
favours (a) until the feature ceiling stops moving — but (b) gives an
EV-loss measurement that's the actual KPI.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
