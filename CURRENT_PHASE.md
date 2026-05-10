# Current: Sprint 8 — Session 55 ships **TWO ML champions in one session — v40_dt then v41_dt — via the Session 54 diagnostic-driven feature engineering playbook applied to TWO RESIDUAL ZONES**. v39_dt → v40_dt → v41_dt score: **$1,412 → $1,394 → $1,270 full / $801 → $772 → $686 prefix**. Cumulative session: **−$142 full / −$115 prefix.** pct_opt 57.88% → 62.18% full / 64.55% → 67.13% prefix. **Trips_pair within-category $909 → $281 (−$628, −69%); two_pair within-category $918 → $363 (−$555, −60%).** All non-targeted categories byte-identical to predecessor (surgical via gating). Leaf count v40: +3.4% (1.52M → 1.57M); v41: +32% (1.57M → 2.02M). Depth saturation 36 in all three. New features: 4 rank-valued tp_v2_* + 4 rank-valued t2p_v2_* = 8 new gated features over 87 base + 4 v5 from S54 = **95 total features in v41_dt**. Cumulative v32 → v41 = **−$445 full / −$218 prefix** (6 ML ships). Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). Methodology validation: the S54 4-phase playbook (drill → hand-level → design rank-valued conditional features → train) is now TRANSFERABLE across ML residual zones. Asymmetric existing features signal blind spots (two_pair had Layout B DS feature but no Layout C equivalent — pointed directly at the missing feature design).

> **🎯 IMMEDIATE NEXT ACTION (Session 56):**
>
>   **Apply the same playbook to the largest remaining ML residual: high_only zone.**
>
>   (A) **High_only zone** — $2,796/1000h within-category in v41_dt (UNCHANGED from v39; 41% of population × $2,796 = $1,145/1000h whole-grid contribution = BY FAR the largest residual). Different feature types likely needed — not just suit-distribution-quality. Candidates:
>      - top-card placement features (when to play A or K on top)
>      - defensive-pair triggers (when to pair the top vs play sing)
>      - broadway connectivity (when the 7 cards form a near-straight)
>      - Run Phase 1 drill on high_only with a hand-structure classifier
>        (Hold'em-strength × bot suit profile)
>      - Phase 1b hand-level inspection of top mismatch
>      - Phase 2 v2 — design 4-6 rank-valued conditional features
>      - Train v42_dt
>
>   (B) **Trips zone** ($1,194/1000h, 4.6% share) — same playbook, smaller zone. Lower priority than high_only.
>
>   (C) **Three_pair zone** ($1,613/1000h, 2.2% share) — same playbook, smaller zone.
>
>   (D) **Composite zone** ($960/1000h, 0.2% share) — too small to matter.

> **✅ NEW SHIPS (Session 55):**
> 1. **v40_dt** replaces v39_dt as ML champion. **+$18 full / +$29 prefix.** Trips_pair zone collapse.
> 2. **v41_dt** replaces v40_dt as ML champion. **+$124 full / +$86 prefix.** Two_pair zone collapse.
> 3. **Cumulative session +$142 full / +$115 prefix.** Both new feature suites fully orthogonal — surgical gating preserves all other categories byte-identical.

> **🔬 ARTIFACTS (Session 55):**
> 1. **`analysis/scripts/drill_trips_pair_zone_v39_diagnostic.py`** — Drill TP (Phase 1)
> 2. **`analysis/scripts/drill_trips_pair_v39_mismatch_handlevel.py`** — Drill TP2 (Phase 1b)
> 3. **`analysis/scripts/trips_pair_aug_v2_features_gated.py`** + persist — PRODUCTION rank-valued features for trips_pair
> 4. **`analysis/scripts/train_v40_dt.py`** + `strategy_v40_dt.py` + `grade_v40_dt.py` — Track A ship
> 5. **`analysis/scripts/drill_two_pair_zone_v39_diagnostic.py`** — Drill T2P (Phase 1)
> 6. **`analysis/scripts/drill_two_pair_v39_mismatch_handlevel.py`** — Drill T2P2 (Phase 1b)
> 7. **`analysis/scripts/two_pair_aug_v2_features_gated.py`** + persist — PRODUCTION rank-valued features for two_pair
> 8. **`analysis/scripts/train_v41_dt.py`** + `strategy_v41_dt.py` + `grade_v41_dt.py` — Track B ship (FINAL ML CHAMPION)
> 9. **`data/v40_dt_model.npz`**, **`data/v41_dt_model.npz`** — saved models
> 10. **`data/feature_table_trips_pair_aug_v2_gated.parquet`**, **`data/feature_table_two_pair_aug_v2_gated.parquet`** — persisted feature tables
> 11. **`SESSION_55_V41_DT_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 55 NEW):**
> - **The diagnostic + rank-valued conditional feature playbook is transferable.** Two ships in one session validates the S54 methodology generalizes to other ML residual zones. Track A (trips_pair) and Track B (two_pair) used identical feature shapes (n_configs, max_top_rank, etc.) and identical training pipelines.
> - **Asymmetric existing features signal blind spots.** Two_pair had `t2p_n_layout_b_routings_ds_g` (Layout B DS routings) but no Layout C equivalent. That asymmetry pointed directly at the missing feature design. Audit existing features for missing-mirror gaps when searching for the next zone's blind spot.
> - **The playbook works at low individual-feature importance.** tp_v2 features ranked at #69-78 with 0.02-0.04% importance each, but v40 still shipped +$18 surgical to the trips_pair zone. Importance ≠ utility for gated features that touch a small population.
> - **Surgical gating is a force multiplier.** v40 + v41 ships are both byte-identical to predecessors in non-targeted categories. Gating discipline lets us stack ships without regression. Every gated feature module is purely additive.
> - **Leaf growth scales with feature information density × zone population.** v40's 4 features added +3.4% leaves over a 2.86%-population zone. v41's 4 features added +32% leaves over a 22.3%-population zone. Population size dominates leaf-growth potential when feature info content is high.
> - **Hand-level top-20 inspection is the source-of-truth.** Aggregate mismatch matrices identify the candidate; only hand-level inspection reveals the precise structural delta. Both Track A (R2/R3 routings) and Track B (Layout C asymmetry) required hand-level proof.

> Updated: 2026-05-10 (Session 55)

---

## Headline state at end of Session 55

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED from S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v41_dt** | **NEW ML champion (Session 55).** 2.02M leaves, 95 features at depth=36 ml=1; +$124 full / +$86 prefix vs v40_dt. | `analysis/scripts/strategy_v41_dt.py` + `data/v41_dt_model.npz` |
| v40_dt | Session 55 first ship; replaced by v41 within-session. 1.57M leaves, 91 features; +$18 full / +$29 prefix vs v39_dt. | `analysis/scripts/strategy_v40_dt.py` + `data/v40_dt_model.npz` |
| v39_dt | Predecessor ML champion (S54). 1.52M leaves, 87 features. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt | Older ML champion (S53 overnight; 1.06M leaves at depth=36 ml=1; $1,649 / $891). | `analysis/scripts/strategy_v36_dt.py` + `data/v36_dt_model.npz` |
| v34_dt | Older ML champion (874K leaves; $1,681 / $889). | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v47_rule16_Qhigh_DS / v46_rule15_Khigh_DS / v45_rule14_Ahigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier rule chains. | various |
| v32_dt | Older ML baseline. | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines. | various |

**Capacity + feature progression — NEW v41 ML champion:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h full | pct_opt full |
|---|---:|---:|---:|---:|---:|---:|
| v32 | 32 | 3 | 83 | 731,606 | $1,715 | 50.86% |
| v34 | 34 (33 actual) | 2 | 83 | 874,548 | $1,681 | 52.02% |
| v36 | 36 (33 actual) | 1 | 83 | 1,064,442 | $1,649 | 53.61% |
| v39 | 36 | 1 | 87 (83+4 pair_v5) | 1,518,368 | $1,412 | 57.88% |
| v40 | 36 | 1 | 91 (87+4 tp_v2) | 1,569,848 | $1,394 | 58.48% |
| **v41** | **36** | **1** | **95 (91+4 t2p_v2)** | **2,015,413** | **$1,270** | **62.18%** |

**Cumulative ML arc (v32 → v41):** −$445/1000h on full grid across 6 ships (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124). v39 still the largest single ship; v41 is second-largest.

**Per-category residuals (within-category, full grid) — END OF SESSION 55:**

| Category | n_hands | share | v41 within-cat | $/1000h whole-grid |
|---|---:|---:|---:|---:|
| **high_only** | 1,226,940 | 40.4% | **$2,796** | $1,131 |
| pair | 2,800,512 | 36.2% | $1,097 | $396 |
| **two_pair** (S55 collapsed) | 1,338,480 | 14.5% | $363 | $52 |
| trips | 328,185 | 4.6% | $1,194 | $55 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 |
| **trips_pair** (S55 collapsed) | 171,600 | 1.8% | $281 | $5 |
| composite | 14,742 | 0.2% | $960 | $2 |
| quads | 14,300 | 0.1% | $545 | $1 |

**high_only is now BY FAR the dominant residual** ($1,131/1000h whole-grid = ~63% of total v41 regret). Session 56's highest-leverage target.

**Human-strategy progression — UNCHANGED from end of S53:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| v40b_rule10_gated (+ Rule 10) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3) | $2,769 | 41.91% | −$264 |
| v42_rule11_jpair_pbot_ds (+ Rule 11) | $2,763 | 41.93% | −$270 |
| v43_rule12_two_pair_DS_intact (+ Rule 12) | $2,727 | 42.20% | −$306 |
| v44_rule13_three_pair_DS (+ Rule 13) | $2,717 | 42.34% | −$316 |
| v45_rule14_Ahigh_DS (+ Rule 14) | $2,585 | 43.05% | −$448 |
| v46_rule15_Khigh_DS (+ Rule 15) | $2,534 | 43.24% | −$499 |
| v47_rule16_Qhigh_DS (+ Rule 16) | $2,515 | 43.30% | −$518 |
| **v52_full_high_only_handler (+ Rule 17) — CURRENT PRODUCTION** | **$2,498** | **43.34%** | **−$535** |

**The two production tracks now diverge by $1,228/1000h** (v52 rule chain at $2,498; v41_dt at $1,270). The ML champion now beats the human-memorizable rule chain by nearly half its EV deficit.

---

## What Session 55 produced

**Code:**
- 4 drills (2 Phase 1 + 2 Phase 1b)
- 2 feature modules (trips_pair_v2 + two_pair_v2) + 2 persistence scripts
- 2 trainers (v40, v41) + 2 strategies + 2 graders
- All artifacts ship as production (v41 is the new ML champion)

**Documentation:**
- `STRATEGY_GUIDE.md` — Part 1 Session 55 entry appended; Part 2 ML champion table updated (v40 + v41 added, v39 marked superseded).
- `CURRENT_PHASE.md` — rewritten (this file).
- `DECISIONS_LOG.md` — Decisions 089 + 090 appended.
- `SESSION_55_V41_DT_REPORT.md` — repo-root standalone report.

**Models persisted:**
- `data/v40_dt_model.npz` (intermediate champion)
- `data/v41_dt_model.npz` (PRODUCTION ML champion)
- `data/feature_table_trips_pair_aug_v2_gated.parquet`
- `data/feature_table_two_pair_aug_v2_gated.parquet`

---

## Resume Prompt (Session 56)

```
Resume Session 56 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 55)
- DECISIONS_LOG.md (latest: Decisions 089 + 090 — v40_dt + v41_dt new ML champions)
- SESSION_55_V41_DT_REPORT.md
- STRATEGY_GUIDE.md (Session 55 entry in Part 1; updated ML champion table in Part 2)
- analysis/scripts/strategy_v41_dt.py — current ML champion
- analysis/scripts/trips_pair_aug_v2_features_gated.py — template feature suite (trips_pair)
- analysis/scripts/two_pair_aug_v2_features_gated.py — template feature suite (two_pair)
- analysis/scripts/drill_*_zone_v39_diagnostic.py — Phase 1 drill templates
- analysis/scripts/drill_*_v39_mismatch_handlevel.py — Phase 1b drill templates

State (end of Session 55):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED) at
  $2,498 full / $1,522 prefix.
- ML champion: v41_dt (NEW) at $1,270 full / $686 prefix; 2.02M leaves at
  depth=36 ml=1; 95 features (83 base + 4 pair_v5 + 4 tp_v2 + 4 t2p_v2).
- Cumulative ML v32 → v41 = −$445 full / −$218 prefix.
- Trips_pair zone gap collapsed from $909 → $281 (−$628, −69%).
- Two_pair zone gap collapsed from $918 → $363 (−$555, −60%).

USER-PRIORITY DIRECTION FOR SESSION 56:

Apply the now-proven 4-phase playbook to the largest remaining ML
residual zone:

(A) **High_only zone** — $2,796/1000h within-category, 40.4% of
    population. Whole-grid contribution $1,131/1000h = ~63% of v41's
    total regret. BY FAR the highest-leverage target.

    Different feature types likely needed (NOT primarily a suit-routing
    problem):
    - Top-card placement features (when to play A vs K on top)
    - Defensive-pair triggers (when pairing the top is right)
    - Broadway connectivity (when 7 cards form a near-straight)
    - Three-of-a-suit clustering quality (when 3+ broadway in one suit)

    4-phase plan:
    Phase 1: Drill high_only mismatch matrix. Classifier candidates:
             (top_rank × bot_suit × middle_strength). Stratify by
             (top_rank, second_rank).
    Phase 1b: Hand-level top-20 inspection. Identify the structural
             delta (which top card oracle picks differently, what mid
             structure it favors).
    Phase 2 v2: SKIP booleans. Design 4-6 rank-valued conditional
             features. Train v42_dt.

(B) **Trips zone** — $1,194/1000h, 4.6% share. Same playbook. Smaller.

(C) **Three_pair zone** — $1,613/1000h, 2.2% share. Same playbook.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Methodology rule (Session 55 NEW): the playbook is now TRANSFERABLE.
  Same shape (n_configs, max_top_rank, etc.) works across zones.
- Methodology rule (Session 55 NEW): asymmetric existing features
  (Layout B feature with no Layout C equivalent) signal blind spots.
- Methodology rule (Session 55 NEW): low individual feature importance
  (0.02-0.04%) can still ship lift via surgical gating.
- Methodology rule (Session 54): diagnostic-first feature engineering
  works at saturation.
- Methodology rule (Session 54): boolean features are redundant at
  ml=1 saturation.
- Methodology rule (Session 54): rank-valued conditional features
  describing ALTERNATIVE configurations unlock saturation.
- Methodology rule (Session 54): feature design beats hyperparameter
  tuning at saturation.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
