# Session 54 — v39_dt new ML champion (+$237 full / +$90 prefix)

_Generated: 2026-05-10_

## TL;DR — LARGEST ML RETRAIN SHIP IN PROJECT HISTORY

User direction: tackle the pair zone ($852/1000h whole-grid residual in
v36_dt). 4-phase plan: diagnose → design features → retrain → ship.

**v39_dt SHIPS as new ML champion. +$237/1000h full / +$90 prefix.**
2× larger than any prior ML retrain. Pair zone within-category regret
dropped −$507/1000h (32% reduction).

| Grid | v36_dt | v39_dt | Δ |
|---|---:|---:|---:|
| Full (N=200) | $1,649 | **$1,412** | **−$237** |
| Prefix (N=1000) | $891 | **$801** | **−$90** |
| pct_opt full | 53.61% | **57.88%** | **+4.27%** |
| pct_opt prefix | 62.61% | **64.55%** | **+1.94%** |
| p90 regret | 0.535 | 0.480 | improved |
| p99 regret | 1.185 | 1.090 | improved |

## Phase 1: Diagnostic (Drill P + P2)

Drilled 2.8M pair hands. v36 == oracle on only 56.6% of pair hands.
**Top mismatch: v36 picks "mid_SS" while oracle picks "bot_DS"** —
162,551 hands at $3,693 mean regret = **$100/1000h whole-grid contribution
from a single mismatch**. Hand-level inspection of top 20 mismatches
revealed:
- 100% of mismatch hands have pair with 2 distinct suits
- 100% have ≥2 singletons matching pair-suits
- v36 lacks features describing "what pair-bot DS would look like"

## Phase 2 v1: Boolean features (FAILED)

Added 2 booleans (`pair_aug_v4_bot_DS_achievable_g`, `n_sings_in_pair_suits_g`).
v38_dt training: same 1.06M leaves as v36_dt (saturation), features at #51
and #56 importance.

**v38_dt grade: literally identical to v36_dt** (every metric same to
multiple decimals). Diagnosis: booleans were redundant with existing
suit-distribution features (`suit_2nd`, etc.); the DT could already
derive achievability without the new features.

## Phase 2 v2: Rank-valued conditional features (SUCCESS)

Replaced booleans with 4 rank-valued features that encode the QUALITY of
the pair-bot DS option:

| Feature | What it captures |
|---|---|
| `pair_aug_v5_bot_DS_n_configs_g` | count of distinct pair-bot DS configurations (0..N) |
| `pair_aug_v5_bot_DS_max_top_rank_g` | best top-rank achievable across DS configs |
| `pair_aug_v5_bot_DS_min_top_rank_g` | min top-rank achievable across DS configs |
| `pair_aug_v5_bot_DS_max_mid_sum_g` | best (mid rank-sum) across DS configs |

These encode information **NOT derivable from existing features** — they
require enumerating pair-bot DS configurations and selecting the best
across them.

**v39_dt training:**
- 87 features (83 + 4)
- depth=36, ml=1
- **1,518,368 leaves (+43% over v36's 1.06M)**
- **Depth saturated at 36** (vs v36's 33) — the new features broke the
  saturation wall
- 3 of 4 new features ranked in top-30 importance:
  - #19 `pair_aug_v5_bot_DS_min_top_rank_g` (0.50%)
  - #22 `pair_aug_v5_bot_DS_max_mid_sum_g` (0.34%)
  - #29 `pair_aug_v5_bot_DS_max_top_rank_g` (0.19%)

## Per-category breakdown (full grid)

| Category | v36_dt | v39_dt | Δ |
|---|---:|---:|---:|
| **pair** | **$1,604** | **$1,097** | **−$507** (−32%) |
| pair pct_opt | 56.6% | **65.7%** | **+9.1%** |
| (all other categories unchanged) | — | — | $0 |

**The new features are surgical:** they only affect the pair zone (as
designed by the gating). Other categories (high_only, two_pair, trips,
etc.) are byte-identical to v36_dt. This is exactly what good gated
feature engineering should produce.

## Cumulative arc

ML champion progression (capacity-only retrains + feature additions):

| Strategy | Session | Hyperparams | Features | Leaves | Full $/1000h |
|---|---|---|---:|---:|---:|
| v30 | S36 | depth=30 ml=5 | 79 | 493K | $1,794 |
| v31 | S36 overnight | depth=32 ml=3 | 79 | 700K | $1,736 |
| v32 | S37 | depth=32 ml=3 | 83 | 732K | $1,715 |
| v34 | S38 | depth=34 ml=2 | 83 | 875K | $1,681 |
| v36 | S53 overnight | depth=36 ml=1 | 83 | 1.06M | $1,649 |
| **v39** | **S54** | **depth=36 ml=1** | **87** | **1.52M** | **$1,412** |

**Cumulative v32 → v39: −$303/1000h on full grid. v39 is the largest
single retrain in this 4-step ML arc.**

## Methodology lessons (Session 54)

1. **The diagnostic-first approach works.** Phase 1's per-(max, pair)
   cell mismatch matrix + hand-level inspection identified the exact
   blind spot. Without that data, the right features wouldn't have
   been clear.

2. **Boolean features are usually redundant** with existing
   suit-distribution features. v38's flat result confirmed: at depth=33
   saturation, the DT can already derive booleans from existing splits.

3. **Rank-valued conditional features unlock saturation.** v39's features
   describe "what's achievable across all DS configs of pair-bot" —
   information not derivable from any existing feature set. This created
   +43% new leaves and broke the depth=33 ceiling.

4. **Feature design beats hyperparameter tuning at saturation.** v37
   (depth=38 ml=1) was identical to v36 — same features, same leaves.
   v39 added 4 features at SAME hyperparams and gained +$237. Capacity
   saturation is a feature problem, not a hyperparameter problem.

5. **Conditional features should describe alternative configurations,
   not the chosen configuration.** The model already has features for
   the "default" Rule-4-style pair-mid pick. Adding features that
   describe the ALTERNATIVE (pair-bot DS) gives the DT the information
   to compare options.

## Files produced

**Features + persist:**
- `pair_aug_v4_features_gated.py` (booleans, sister — produced no lift)
- `persist_pair_aug_v4_gated.py`
- `pair_aug_v5_features_gated.py` (rank-valued, **shipped**)
- `persist_pair_aug_v5_gated.py`

**Training + grading:**
- `train_v38_dt.py` (sister — identical to v36)
- `strategy_v38_dt.py` (sister)
- `grade_v38_dt.py`
- `train_v39_dt.py` (PRODUCTION ML champion)
- `strategy_v39_dt.py`
- `grade_v39_dt.py`

**Drills:**
- `drill_pair_zone_v36_diagnostic.py` (Phase 1)
- `drill_pair_v36_mismatch_handlevel.py` (Phase 1 deep-dive)

**Documentation:**
- `SESSION_54_V39_DT_REPORT.md` (this file)
- Updated CURRENT_PHASE.md, STRATEGY_GUIDE.md, DECISIONS_LOG.md

## State at end of Session 54

- Rule chain production: **v52** at $2,498 full / $1,522 prefix (UNCHANGED)
- ML champion: **v39_dt** at **$1,412 full / $801 prefix** (NEW)
- Cumulative ML v32 → v39: −$303 full
- v39's pair zone gap: $1,604 → $1,097 = $507/1000h within-category recovery
- Remaining residuals: pair zone now $1,097 (was $1,604), high_only $2,796,
  two_pair $918, trips $1,194, trips_pair $909

## What this enables for future work

1. **Trips_pair zone:** still $909/1000h within-category. If similar
   diagnostic + rank-valued conditional feature pattern works there,
   could ship another big retrain.

2. **two_pair zone:** $918/1000h within-category. Untouched ML-wise.
   Same feature engineering pattern likely applies.

3. **high_only zone:** $2,796/1000h (largest within-category). Not
   primarily a pair-state problem; probably needs different feature
   types (top-card placement features, defensive triggers).

4. **Total potential:** if applying the same diagnostic + rank-valued-
   feature methodology to trips_pair and two_pair yields similar lift
   ratios, could ship another +$200-400 cumulative.

This is genuinely a methodology breakthrough — the pair zone was the
dominant ML residual for sessions, and we cracked it cleanly with
diagnostic-driven feature design.
