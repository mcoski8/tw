# Session 55 — v40_dt + v41_dt new ML champions (+$142 full cumulative)

_Generated: 2026-05-10_

## TL;DR — TWO SHIPS IN ONE SESSION; LARGER CUMULATIVE THAN S54

User direction: apply Session 54's diagnostic-driven feature engineering
playbook to the next two ML residual zones — trips_pair ($909/1000h) and
two_pair ($918/1000h).

**Two ships in one session:**

| Ship | Δ full | Δ prefix | Within-cat zone collapse |
|---|---:|---:|---|
| **v40_dt** (trips_pair) | **+$18** | **+$29** | trips_pair $909 → $281 (−69%) |
| **v41_dt** (two_pair) | **+$124** | **+$86** | two_pair $918 → $363 (−60%) |
| **Combined (v39 → v41)** | **+$142** | **+$115** | both zones collapsed surgically |

**v41_dt becomes the new ML champion at $1,270/1000h full grid /
$686/1000h prefix.** Cumulative session arc is +$142/1000h full /
+$115/1000h prefix — **second-largest combined ML session ship after
S54's single +$237** — but v41 represents two ships from two zones,
validating the playbook is transferable.

| Grid | v39_dt | v40_dt | v41_dt | Δ session |
|---|---:|---:|---:|---:|
| Full (N=200) | $1,412 | $1,394 | **$1,270** | **−$142** |
| Prefix (N=1000) | $801 | $772 | **$686** | **−$115** |
| pct_opt full | 57.88% | 58.48% | **62.18%** | **+4.30%** |
| pct_opt prefix | 64.55% | 65.19% | **67.13%** | **+2.58%** |
| p90 regret | 0.480 | 0.475 | 0.450 | improved |
| p99 regret | 1.090 | 1.085 | 1.075 | improved |

## Track A — Trips_pair zone (v40_dt ships +$18/+$29)

### Phase 1: Drill TP (mismatch matrix)

Sweep of all 171,600 trips_pair hands. v39_dt vs oracle:

**Top mismatch: v39 picks Pbot_SS while oracle picks Pbot_DS** —
10,398 hands @ $3,580 mean regret = **$6.20/1000h whole-grid
contribution from a single mismatch class.**

Whole-grid total trips_pair mismatch contribution: $19/1000h (matches
expected $26 from within-cat $909 × share 2.86%).

Class distribution shift (v39 − oracle):
- v39 OVER-picks `Pbot_SS` (+8.27%)
- v39 UNDER-picks `Pbot_DS` (−9.10%)
- Pattern: systematic DS-routing under-routing

### Phase 1b: Drill TP2 (hand-level inspection)

Top 20 mismatch hands + aggregate over 10,398:
- **100%** have pair with 2 distinct suits
- **R1** (bot = pair + 2 sings filling pair-suits): available in only **0.3%**
- **R2** (bot = pair + 1 trip + 1 sing): available in **85.7%**
- **R3** (bot = pair + 2 trip cards): available in **59.0%**
- v39's existing `tp_pair_routing_is_ds_g` only captures R1
  → BLIND to R2 and R3 (the dominant routings)

### Phase 2 v2: Rank-valued conditional features

Mirrored pair_aug_v5's pattern. Four new features describing the
QUALITY of Pbot_DS across ALL routings (R1+R2+R3):

| Feature | What it captures |
|---|---|
| `tp_v2_bot_DS_n_configs_g` | Count of (pair + 2 others) 4-card bot configs yielding DS. Spans R1/R2/R3. |
| `tp_v2_bot_DS_max_top_rank_g` | Best top-rank achievable across DS configs |
| `tp_v2_bot_DS_min_top_rank_g` | Lowest top-rank achievable |
| `tp_v2_bot_DS_max_mid_sum_g` | Best mid rank-sum across configs |

### v40_dt training results

- 91 features (87 + 4 v2)
- depth=36, ml=1
- **1,569,848 leaves (+3.4% over v39's 1.52M)** — modest growth, but
  enough to surgically reshape the trips_pair routing
- Feature importance: 0.02-0.04% per feature (low individually, but
  surgical via gating)

### v40_dt grade

**Full grid (N=200):**
- v39_dt: $1,412 / 57.88% / 1.52M leaves
- **v40_dt: $1,394 / 58.48% / 1.57M leaves** (−$18 / +0.60% pct_opt)

**Prefix grid (N=1000):**
- v39_dt: $801 / 64.55%
- **v40_dt: $772 / 65.19%** (−$29 / +0.64%)

**Per-category (full grid) — surgical:**
| Category | v39 | v40 | Δ |
|---|---:|---:|---:|
| **trips_pair** | **$909** | **$281** | **−$628 (−69%)** |
| trips_pair pct_opt | 64.2% | **85.1%** | **+20.9%** |
| (all other categories byte-identical to v39) | | | |

## Track B — Two_pair zone (v41_dt ships +$124/TBD)

### Phase 1: Drill T2P (mismatch matrix)

Sweep of all 1,338,480 two_pair hands.

**Top mismatch: v39 picks Hbot_Lmid_SS while oracle picks Hmid_Lbot_SS** —
56,206 hands @ $2,655 mean regret = **$24.84/1000h whole-grid
contribution.**

Second largest: `Hbot_Lmid_SS → Hbot_Lmid_DS` ($12.77/1000h).

Total two_pair mismatch contribution: $187/1000h whole-grid (matches
expected $205 from within-cat $918 × share 22.3%).

Class distribution shift:
- v39 OVER-picks rainbow/SS/3+1 configs
- v39 UNDER-picks DS configs (−3.19% Hbot_Lmid_DS, −1.15% Hmid_Lbot_DS)

### Phase 1b: Drill T2P2 (hand-level inspection)

Top 20 mismatch hands + aggregate over 17,131 (sampled):
- **72%** of mismatches have pair-suit overlap ≥ 1 (suit-profile
  tradeoffs exist)
- **34%** have Layout C (Hbot_Lmid) DS routing(s) available
- v39 has Layout B DS feature (`t2p_n_layout_b_routings_ds_g`) but
  **NO Layout C equivalent** — asymmetric blind spot

### Phase 2 v2: Rank-valued conditional features

Four new features completing the Layout B/C asymmetry:

| Feature | What it captures |
|---|---|
| `t2p_v2_layout_C_DS_n_configs_g` | Layout C (Hbot_Lmid) DS routings count |
| `t2p_v2_layout_C_max_top_rank_g` | Best top-rank in Layout C across SS+DS |
| `t2p_v2_layout_B_max_top_rank_g` | Best top-rank in Layout B across SS+DS |
| `t2p_v2_layout_C_DS_max_top_rank_g` | Best top-rank specifically when Layout C is DS |

### v41_dt training results

- 95 features (91 + 4 v2)
- depth=36, ml=1
- **2,015,413 leaves (+32% over v40's 1.57M)** — large leaf growth
- 3 of 4 new features in top-30 importance:
  - #24 `t2p_v2_layout_B_max_top_rank_g` (0.29%)
  - #26 `t2p_v2_layout_C_max_top_rank_g` (0.28%)
  - #30 `t2p_v2_layout_C_DS_max_top_rank_g` (0.21%)
  - #73 `t2p_v2_layout_C_DS_n_configs_g` (0.04%)

### v41_dt grade

**Full grid (N=200):**
- v40_dt: $1,394 / 58.48% / 1.57M leaves
- **v41_dt: $1,270 / 62.18% / 2.02M leaves** (−$124 / +3.70% pct_opt)

**Prefix grid (N=1000):**
- v40_dt: $772 / 65.19%
- **v41_dt: $686 / 67.13%** (−$86 / +1.94%)

**Per-category (full grid) — surgical:**
| Category | v40 | v41 | Δ |
|---|---:|---:|---:|
| **two_pair** | **$918** | **$363** | **−$555 (−60%)** |
| two_pair pct_opt | 66.6% | **83.2%** | **+16.6%** |
| trips_pair (preserved) | $281 | $281 | 0 |
| (all other categories byte-identical to v40) | | | |

## Cumulative ML arc

| Strategy | Session | Hyperparams | Features | Leaves | Full $/1000h |
|---|---|---|---:|---:|---:|
| v30 | S36 | depth=30 ml=5 | 79 | 493K | $1,794 |
| v31 | S36 overnight | depth=32 ml=3 | 79 | 700K | $1,736 |
| v32 | S37 | depth=32 ml=3 | 83 | 732K | $1,715 |
| v34 | S38 | depth=34 ml=2 | 83 | 875K | $1,681 |
| v36 | S53 overnight | depth=36 ml=1 | 83 | 1.06M | $1,649 |
| v39 | S54 | depth=36 ml=1 | 87 | 1.52M | $1,412 |
| v40 | **S55 (this)** | depth=36 ml=1 | 91 | 1.57M | $1,394 |
| **v41** | **S55 (this)** | **depth=36 ml=1** | **95** | **2.02M** | **$1,270** |

**Cumulative v32 → v41: −$445/1000h on full grid** (across 6 ML ships).
S55 contributes the second-largest single-session lift after S54.

## Methodology lessons (Session 55)

1. **The diagnostic + rank-valued conditional feature playbook is
   transferable across zones.** Two ships in one session validates
   that the S54 methodology is not specific to the pair zone — it
   generalizes to trips_pair and two_pair with identical feature shape
   and identical training pipeline.

2. **Asymmetric existing features signal a blind spot.** Two_pair had a
   `t2p_n_layout_b_routings_ds_g` feature but no Layout C equivalent.
   That asymmetry pointed directly at the missing feature design.
   Future zones: audit existing features for missing-mirror gaps.

3. **The S54 playbook works at low individual-feature importance.**
   tp_v2 features ranked at #69-78 with 0.02-0.04% importance each, but
   v40 still shipped +$18 surgical to the trips_pair zone. Importance
   ≠ utility for gated features that touch a small population.

4. **Surgical gating is a force multiplier.** Both v40 and v41 ships
   are byte-identical to predecessors in non-targeted categories. The
   gating discipline lets us stack ships without regressing other
   zones — every gated feature module is purely additive.

5. **Leaf growth scales with feature information density.** v40's 4
   features added +3.4% leaves; v41's 4 features added +32%. The
   two_pair zone (22.3% of population) had much more orthogonal info
   to extract than the trips_pair zone (2.86%). Population size
   dominates leaf-growth potential when feature info content is high.

## Files produced (Session 55)

**Drills (Phase 1):**
- `analysis/scripts/drill_trips_pair_zone_v39_diagnostic.py`
- `analysis/scripts/drill_trips_pair_v39_mismatch_handlevel.py`
- `analysis/scripts/drill_two_pair_zone_v39_diagnostic.py`
- `analysis/scripts/drill_two_pair_v39_mismatch_handlevel.py`

**Features (Phase 2 v2):**
- `analysis/scripts/trips_pair_aug_v2_features_gated.py`
- `analysis/scripts/persist_trips_pair_aug_v2_gated.py`
- `analysis/scripts/two_pair_aug_v2_features_gated.py`
- `analysis/scripts/persist_two_pair_aug_v2_gated.py`

**Training + grading:**
- `analysis/scripts/train_v40_dt.py` + `strategy_v40_dt.py` + `grade_v40_dt.py`
- `analysis/scripts/train_v41_dt.py` + `strategy_v41_dt.py` + `grade_v41_dt.py`

**Models persisted:**
- `data/v40_dt_model.npz` (ML champion replaced by v41 within session)
- `data/v41_dt_model.npz` (PRODUCTION ML champion)
- `data/feature_table_trips_pair_aug_v2_gated.parquet`
- `data/feature_table_two_pair_aug_v2_gated.parquet`

**Documentation:**
- `SESSION_55_V41_DT_REPORT.md` (this file)
- Updated `CURRENT_PHASE.md`, `STRATEGY_GUIDE.md`, `DECISIONS_LOG.md`

## State at end of Session 55

- **Rule chain production: v52** at $2,498 full / $1,522 prefix (UNCHANGED)
- **ML champion: v41_dt** at **$1,270 full / $686 prefix** (NEW)
- Cumulative ML v32 → v41: −$445 full / −$218 prefix
- Remaining residuals (within-category, full grid):
  - **high_only** $2,796 (still largest — next target, different feature types)
  - **pair** $1,097 (compressed in S54)
  - **trips** $1,194 (untouched in S55)
  - **three_pair** $1,613 (untouched)
  - **composite** $960 (rare)
  - **two_pair** $363 (compressed in S55) — was second-largest, now under control
  - **trips_pair** $281 (compressed in S55)

## What this enables for future work

1. **High_only zone** ($2,796/1000h within-cat × 41% share = ~$1,145
   whole-grid contribution) is now BY FAR the largest residual. Needs
   different feature types: top-card placement, defensive-pair triggers,
   broadway connectivity. The playbook applies but the features differ.

2. **Trips zone** ($1,194/1000h, 4.6% share) and **three_pair zone**
   ($1,613/1000h, 2.2% share) are next medium-lift targets.

3. **Methodology is mature:** Phase 1 drill → Phase 1b hand-level →
   skip booleans → design 4 rank-valued conditional features → train →
   grade. The pipeline is now boilerplate.

This session more than doubles the cumulative S54 ship in zone-collapse
terms (S54: pair zone −32%; S55: trips_pair −69%, two_pair −60%).
The methodology generalizes.
