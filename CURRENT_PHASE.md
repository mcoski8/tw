# Current: Sprint 7 Phase D — single-pair augmented features unlock +5.85pp slice ceiling, +2.02pp full-6M ceiling. First feature-engineering win since the goal reframe. Session 17 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 18):** EITHER (a) repeat the mining-and-augment loop on **high_only** (12.6% of v3 EV-loss) to add 2-3 more features, OR (b) extract a depth-15 chain from the augmented full-6M tree (18,330 leaves, full_shape 61.96%) → translate to Python if/elif → byte-identical parity check → EV-loss baseline vs v3. (b) is the chain-shipping path; (a) is more discovery before commitment. Recommended: (a) first to lift the ceiling further, then (b) once the augmented-feature set has stabilised.

> **🚫 RETIRED (Decision 033, Session 16):** "≥95% shape-agreement on multiway-robust target." Replaced with directional reduction below v3's 1.63 EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles. Reportable metric: $/1000 hands at $10/EV-pt.

> Updated: 2026-04-28 (end of Session 17)

---

## Headline state at end of Session 17

**First feature-engineering win since the Session 16 reframe.** Three new
single-pair-only features encode bot-suit-profile per strategic routing —
information the original 27-feature set could not see. They lift the
DT-ceiling on the largest miss cohort (single-pair, 47% of EV-loss) by
+5.85pp; the lift propagates to +2.02pp on the full 6M.

### New features (single-pair only; vacuous on non-pair hands)

1. `default_bot_is_ds` — bool. Is the bot double-suited under v3-default
   routing (mid=pair, top=highest singleton, bot=4 lowest non-pair)?
2. `n_top_choices_yielding_ds_bot` — 0-5. How many of the 5 non-pair
   singleton positions yield a DS bot if used as top? (Captures
   "pair-on-mid is fine but top must be repaired" pattern.)
3. `pair_to_bot_alt_is_ds` — bool. Under alternative routing
   (pair→bot, mid=top-2 singletons, top=3rd-highest singleton), is bot DS?

### DT shape-agreement ceilings (depth=None, full data fit)

| Subset | Baseline (27 feat) | Augmented (30 feat) | Lift |
|---|---|---|---|
| Single-pair 3-of-4 (target slice, 1.08M) | 74.23% | **80.08%** | **+5.85pp** |
| Single-pair full (2.80M) | 68.49% | 72.83% | +4.34pp |
| 3-of-4 majority (2.43M) | 70.01% | 72.61% | +2.60pp |
| **Full 6M** | **61.74%** | **63.76%** | **+2.02pp** |

### Full-6M depth curve (augmented features)

| depth | leaves | cv_acc | cv_shape | full_acc | full_shape |
|---|---|---|---|---|---|
| 3 | 8 | 30.7% | 32.3% | 30.6% | 32.1% |
| 5 | 32 | 39.9% | 42.0% | 40.0% | 42.3% |
| 7 | 125 | 47.1% | 49.1% | 47.2% | 49.3% |
| 10 | 939 | 54.2% | 56.5% | 54.5% | 56.8% |
| **15** | **18,330** | **58.3%** | **60.7%** | **59.6%** | **62.0%** |
| 20 | 118,723 | 56.8% | 59.2% | 61.3% | 63.4% |
| None | 208,740 | 55.4% | 58.0% | 61.7% | 63.8% |

**The depth-15 augmented tree (62.0% full / 60.7% cv) MATCHES the baseline
unbounded-depth tree (61.7% full / 57.2% cv) at 9× fewer leaves AND with
better generalization (+3.5pp cv-shape).** Depth-15 is the clear knee
candidate for chain extraction.

v3 production rule chain: 56.16% — depth-10 augmented (56.8%) is barely
above v3 with only 939 leaves; depth-15 augmented (62.0%) is +5.8pp over v3.

### Drop-out ablation on the slice (depth=None)

| Drop one feature | Slice shape | Δ from full aug |
|---|---|---|
| (full augmented — 30 features) | 80.08% | — |
| − default_bot_is_ds | 78.04% | −2.04pp |
| − n_top_choices_yielding_ds_bot | 78.71% | −1.37pp |
| − pair_to_bot_alt_is_ds | 77.24% | −2.85pp |

All three features contribute. `pair_to_bot_alt_is_ds` is the largest
single contributor — it captures the strategic family (low-pair → bot,
broadway-singletons → mid) the existing features cannot represent.

### Signal odds ratios (slice-level, vs "BR uses v3-default routing")

| Feature | OR | Direction |
|---|---|---|
| `default_bot_is_ds` | 4.39 | + (BR uses default when its bot is DS) |
| `n_top_choices_yielding_ds_bot ≥ 1` | 0.90 | ≈ neutral (composite signal) |
| `n_top_choices_yielding_ds_bot ≥ 3` | 1.15 | weak + |
| `pair_to_bot_alt_is_ds` | 0.56 | − (BR shifts AWAY from default when alt is DS) |

The OR sign on `pair_to_bot_alt_is_ds` is exactly what the model needs
to learn the alternative routing.

---

## What was completed this session (Session 17)

### Step 1-3 — single-pair leaf mining (`mine_pair_leaves.py`)

- Filtered feature_table to (mode_count==3 AND category=='pair') →
  1,078,223 hands (17.94% of full 6M).
- Trained depth=None DT on slice with the 27 baseline features. Slice
  ceiling: **74.23% / 26,238 leaves**.
- Ranked terminal leaves by absolute shape-miss count. Top-50 leaves
  cover only 3.5% of slice misses — misses are highly diffuse across
  22,031 leaves.
- Recurring structural blind spot identified: bot suit profile under
  specific routings. Existing `suit_2nd ≥ 2` only sees "some DS-bot is
  achievable from 7 cards"; cannot see "the SPECIFIC bot-4 chosen by a
  given (top, mid) is DS".

### Step 4 — three-feature design (`pair_aug_features.py`)

- Module exposes `compute_pair_aug_for_hand(hand)` (scalar) and
  `compute_pair_aug_batch(hands, slice_mask)` (vectorised).
- Spot-checked on hand-picked cases from the leaf dump.
- Vacuous on non-pair hands (returns 0); design choice keeps the rest of
  the population unaffected.

### Step 4a — odds-ratio signal check (per 4-step doctrine, before MC)

- Computed via `dt_pair_aug_ceiling.py` — confirmed signal direction and
  magnitude before training a tree. No MC compute spent on dead hypothesis.

### Step 5 — augmented-feature DT ceiling (`dt_pair_aug_ceiling.py`,
`dt_phase1_3of4_aug.py`)

- depth=None DT comparison across 4 subsets (full / 3-of-4 / single-pair
  full / single-pair 3-of-4). Lift table above.
- Per-feature drop-out ablation confirms all three features contribute.

### Step 6a — full-6M depth curve (`dt_phase1_aug.py`)

- Depths {3, 5, 7, 10, 15, 20, None}. Identical methodology to dt_phase1.py
  (3-fold CV on 1M subsample, full-6M fit at chosen depth).
- Depth-15 is the new knee. CV peak shifts up: 60.71% (was 59.57%, +1.14pp).

### Augmented-feature persistence (`persist_aug_features.py`)

- `data/feature_table_aug.parquet` — 18.87 MB, joins on canonical_id.
- Future sessions can read this directly instead of re-running the 51s
  Python-loop `compute_pair_aug_batch` over 6M hands.

---

## Files added this session

- `analysis/scripts/mine_pair_leaves.py` — Step 1-3 mining with leaf-rank dump
- `analysis/scripts/pair_aug_features.py` — feature module (scalar + batch)
- `analysis/scripts/dt_pair_aug_ceiling.py` — Step 4 + ablation
- `analysis/scripts/dt_phase1_3of4_aug.py` — Step 5 cross-subset comparison
- `analysis/scripts/dt_phase1_aug.py` — Step 6a depth curve on full 6M
- `analysis/scripts/persist_aug_features.py` — parquet persistence
- `data/feature_table_aug.parquet` — 18.87 MB, single-pair augmented features

## Files modified this session

- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 034
- `handoff/MASTER_HANDOFF_01.md` — appended Session 17 entry

## Verified

- Rust: `cargo build --release` clean. `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical +
  9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **First feature mental-model was wrong.** Initial `default_bot_is_ds`
  candidate computed routing assuming top = highest non-pair card; that's
  the v3 default. But in the leaf dump, BR was using top=lowest (k=4 in
  the 5-singleton enumeration), not top=highest. I caught this by
  spot-checking 4 hand-picked cases against the leaf dump. The fix:
  `n_top_choices_yielding_ds_bot` (0-5) — count, not "which".
  **Lesson: spot-check candidate features against ≥4 hand-picked cases
  from the source observation BEFORE running batch.**
- **Per-feature drop-out is essential.** `pair_to_bot_alt_is_ds` looked
  weakest by signal OR magnitude (0.56 inverse), but contributed +2.85pp
  in drop-out — the largest of the three. **Signal magnitude is not
  contribution magnitude.** Always run drop-out ablation when claiming
  multiple features add up.
- **Augment compute is Python-loop bound.** 51s on 6M is the cost of
  per-hand bot-position enumeration. Acceptable as a once-per-session cost,
  but persist to parquet for downstream chain-extraction work.
- **Depth-15 generalization improves.** With augmented features, the
  bounded-depth-15 tree achieves 62.0% / 60.7% (full / cv), beating the
  baseline depth=None ceiling on full data while halving the cv-shape gap.
  This is the right depth for chain extraction.

## Resume Prompt (Session 18)

```
Resume Session 18 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 17)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 034 — single-pair augmented features)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 13-17; Session 17 is the most consequential since the reframe)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/pair_aug_features.py (Session 17 features module)
- analysis/scripts/dt_phase1_aug.py (Session 17 depth curve, full 6M)
- data/feature_table.parquet, data/feature_table_aug.parquet (joined on canonical_id)

State of the project (end of Session 17):
- Single-pair augmented features delivered +5.85pp on the target slice (74.23% → 80.08%)
  and +2.02pp on full 6M (61.74% → 63.76%) at depth=None.
- Depth-15 augmented tree: 62.0% full / 60.7% cv shape — matches baseline depth=None
  ceiling at 9× fewer leaves and +3.5pp better cv-shape generalization.
- v3 production: 56.16% (unchanged). Augmented depth-15 is +5.8pp over v3.
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed):
- Discovery mode, not production commitment.
- Data/ML/AI drives discovery — let the leaves speak; don't anchor on speculation.
- Rule-count cap is soft.
- Track results as $/1000 hands at $10/EV-point.
- Always report BOTH absolute EV per profile AND EV-loss vs BR.

IMMEDIATE NEXT ACTIONS (pick one):

(a) RECOMMENDED — Continue mining other categories.
    1. Filter feature_table.parquet to (mode_count == 3 AND category == 'high_only')
       — 12.6% of v3 EV-loss; the second-largest cohort.
    2. Train depth=None DT on slice with augmented 30 features. Report ceiling.
    3. Mine impure leaves; engineer 1-3 high_only-specific features.
    4. Re-run depth curve on full 6M with all features. Lift?
    5. Repeat for two_pair (24% of EV-loss) and trips_pair if budget allows.

(b) Alternative — Extract chain from current augmented depth-15 tree.
    1. Refit depth=15 DT on full 6M with the 30 features.
    2. Use sklearn `export_text` → translate to Python if/elif chain.
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
