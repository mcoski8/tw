# Current: Sprint 8 — Session 54 ships **v39_dt as new ML champion via diagnostic-driven feature engineering — LARGEST ML retrain ship in project history**. v36_dt → v39_dt score: **$1,649 → $1,412 full / $891 → $801 prefix** (−$237 full / −$90 prefix). pct_opt 53.61% → 57.88% full / 62.61% → 64.55% prefix. **Pair zone within-category $1,604 → $1,097 (−$507, −32%); pair pct_opt 56.6% → 65.7% (+9.1%).** All other categories byte-identical to v36 (surgical via gating). Leaf count +43% (1.06M → 1.52M); depth saturation broke 33 → 36. 3 of 4 new features in top-30 importance. Cumulative v32 → v39 = −$303 full. Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). Origin: 4-phase plan executed — (Phase 1) Drills P + P2 identified $100/1000h whole-grid mismatch where v36 picks pair-mid_SS but oracle picks pair-bot_DS on 162,551 hands. (Phase 2 v0) v37 capacity sweep at depth=38 was byte-identical to v36 — confirmed saturation is a feature problem. (Phase 2 v1) v38 with 2 booleans was byte-identical to v36 — booleans redundant with existing suit features. (Phase 2 v2) v39 with 4 rank-valued conditional features describing the QUALITY of the pair-bot DS alternative — broke saturation (+43% leaves, depth 33 → 36) and shipped the +$237. Methodology breakthrough: at saturation, only NEW INFORMATION unlocks more leaves; rank-valued conditional features that describe alternative configurations encode information that suit-distribution features cannot derive.

> **🎯 IMMEDIATE NEXT ACTION (Session 55):**
>
>   **Apply the Session 54 diagnostic-driven feature engineering playbook to the next two ML residual zones:**
>
>   (A) **Trips_pair zone** — $909/1000h within-category in v39_dt. Same 4-phase plan: drill the v39 vs oracle mismatch matrix at the (trips_rank, pair_rank) cell level → hand-level inspection of top 20 → identify the under-modeled alternative configuration → design rank-valued conditional features (avoid the boolean trap) → train v40_dt.
>
>   (B) **Two_pair zone** — $918/1000h within-category in v39_dt. Same playbook. Likely target: alternatives that v39 systematically under-routes.
>
>   (C) **High_only zone** — $2,796/1000h (largest within-category). Different feature types likely needed (top-card placement, defensive triggers); not primarily a pair-state problem. Lower priority than (A), (B) until those land.
>
>   (D) **Rule chain — Rule 17 v2 / non-default top picks** — Q-high oracle picks J on top in 10% of cases. Drill O has the data. Lower priority than ML zones.
>
>   (E) **Composite within-class** — $960/1000h within-category in v39, but rare (small population). Lower priority.

> **✅ NEW SHIP (Session 54):** v39_dt replaces v36_dt as ML champion. **+$237 full / +$90 prefix.** Total project rule count: **17** (UNCHANGED — ML-only session). **2× the largest prior ML retrain ship** (v34_dt was −$34). The pair zone — dominant ML residual for sessions — was cracked.

> **🔬 ARTIFACTS (Session 54):**
> 1. **`analysis/scripts/drill_pair_zone_v36_diagnostic.py`** — Phase 1 Drill P (per-(max, pair) cell mismatch matrix)
> 2. **`analysis/scripts/drill_pair_v36_mismatch_handlevel.py`** — Phase 1 Drill P2 (hand-level inspection of top 20)
> 3. **`analysis/scripts/pair_aug_v4_features_gated.py`** + `persist_pair_aug_v4_gated.py` — sister boolean features (v38, no lift)
> 4. **`analysis/scripts/pair_aug_v5_features_gated.py`** + `persist_pair_aug_v5_gated.py` — PRODUCTION rank-valued features
> 5. **`analysis/scripts/train_v38_dt.py`** + `strategy_v38_dt.py` + `grade_v38_dt.py` — sister Phase 2 v1 boolean features (byte-identical to v36)
> 6. **`analysis/scripts/train_v39_dt.py`** + `strategy_v39_dt.py` + `grade_v39_dt.py` — PRODUCTION ML champion
> 7. **`data/v38_dt_model.npz`**, **`data/v39_dt_model.npz`** — saved models
> 8. **`data/feature_table_pair_aug_v4_gated.parquet`**, **`data/feature_table_pair_aug_v5_gated.parquet`** — persisted feature tables
> 9. **`SESSION_54_V39_DT_REPORT.md`** — repo-root standalone report
> 10. (Reference: `analysis/scripts/strategy_v37_dt_SATURATED.py` from Session 53 overnight Part 5 had already established capacity saturation at 83 features; informed S54's pivot to feature design over hyperparameter tuning.)

> **📓 METHODOLOGY LESSONS (Session 54 NEW):**
> - **Diagnostic-first feature engineering at saturation works.** Per-(max, pair) cell mismatch matrix + hand-level inspection of top 20 mismatches identifies the exact blind spot. Without that data, the right feature design isn't clear.
> - **Boolean features are usually redundant** with existing suit-distribution features at ml=1 saturation. The DT can already derive booleans from existing splits. v38's null result confirmed this empirically.
> - **Rank-valued conditional features unlock saturation.** Features describing "what's achievable across alternative configurations" encode information not derivable from any existing feature. v39's features broke depth saturation 33 → 36 and added +43% leaves.
> - **Feature design beats hyperparameter tuning at saturation.** v37 (depth=38 ml=1) was byte-identical to v36 — same features, same leaves. v39 added 4 features at the SAME hyperparams and gained +$237. Capacity saturation is a feature problem, not a hyperparameter problem.
> - **Conditional features should describe ALTERNATIVE configurations, not the chosen configuration.** The model already has features for the "default" pick; adding features that describe the ALTERNATIVE gives the DT info to compare options.
> - **The 4-phase playbook is now transferable** to other ML residual zones: trips_pair and two_pair queued for Session 55.

> Updated: 2026-05-10 (Session 54)

---

## Headline state at end of Session 54

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED from S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v39_dt** | **NEW ML champion** (Session 54). 1.52M leaves, 87 features at depth=36 ml=1; +$237 full / +$90 prefix vs v36_dt. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt | Predecessor ML champion (S53 overnight; 1.06M leaves at depth=36 ml=1; $1,649 / $891). | `analysis/scripts/strategy_v36_dt.py` + `data/v36_dt_model.npz` |
| v34_dt | Older ML champion (874K leaves; $1,681 / $889). | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v38_dt | Sister, S54 (2 booleans, byte-identical to v36 — boolean trap). | `analysis/scripts/strategy_v38_dt.py` + `data/v38_dt_model.npz` |
| v37_dt_SATURATED | Sister, S53 overnight Part 5 (depth=38 capacity sweep, byte-identical to v36 — confirmed saturation). | `analysis/scripts/strategy_v37_dt_SATURATED.py` |
| v47_rule16_Qhigh_DS / v46_rule15_Khigh_DS / v45_rule14_Ahigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier rule chains. | various |
| v32_dt | Older ML baseline. | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines. | various |

**Capacity + feature progression — NEW v39 ML champion:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt |
|---|---:|---:|---:|---:|---:|---:|
| v32 | 32 | 3 | 83 | 731,606 | $1,715 | 50.86% |
| v34 | 34 (33 actual) | 2 | 83 | 874,548 | $1,681 | 52.02% |
| v36 | 36 (33 actual) | 1 | 83 | 1,064,442 | $1,649 | 53.61% |
| v37 (S53 P5) | 38 (33 actual) | 1 | 83 | 1,064,442 | $1,649 | 53.61% (byte-id to v36) |
| v38 (S54 P2v1) | 36 (33 actual) | 1 | 85 (83+2 bool) | 1,064,442 | $1,649 | 53.61% (byte-id to v36) |
| **v39** | **36** | **1** | **87 (83+4 rank-valued)** | **1,518,368** | **$1,412** | **57.88%** |

**Cumulative ML arc (v32 → v39):** −$303/1000h on full grid across 4 ships (v34: −$34, v36: −$33, v39: −$237; v37 + v38 were $0 saturation/redundancy controls). v39 is the dominant ship.

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

**The two production tracks now diverge by $1,086/1000h** (v52 is the human-memorizable rule chain at $2,498; v39_dt is the ML optimum at $1,412). v39_dt cannot be expressed as a small set of human-memorizable rules — it's 1.52M decision tree leaves.

---

## What Session 54 produced

**Code:**
- 2 drills (Drill P + Drill P2 — Phase 1 diagnostic)
- 2 feature modules (v4 sister boolean, v5 PRODUCTION rank-valued) + 2 persistence scripts
- 2 trainers (v38 sister, v39 PRODUCTION) + 2 strategies + 2 graders
- v38 is a sister artifact confirming Session 54's boolean-redundancy lesson
- v39 is the PRODUCTION ML champion
- (v37 saturation control was Session 53 overnight Part 5; informed S54's approach)

**Documentation:**
- `STRATEGY_GUIDE.md` — Part 1 Session 54 entry appended; Part 2 ML champion table updated (v36 marked superseded, v37/v38 added as ARCHIVED, v39 added as CURRENT ML CHAMPION); front-matter "Last updated" refreshed.
- `CURRENT_PHASE.md` — rewritten (this file).
- `DECISIONS_LOG.md` — Decision 088 appended.
- `SESSION_54_V39_DT_REPORT.md` — repo-root standalone report.

**Models persisted:**
- `data/v37_dt_model.npz` (sister, byte-identical to v36)
- `data/v38_dt_model.npz` (sister, byte-identical to v36)
- `data/v39_dt_model.npz` (PRODUCTION, 1.52M leaves)
- `data/feature_table_pair_aug_v4_gated.parquet` (intermediate)
- `data/feature_table_pair_aug_v5_gated.parquet` (PRODUCTION)

---

## Resume Prompt (Session 55)

```
Resume Session 55 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 54)
- DECISIONS_LOG.md (latest: Decision 088 — v39_dt new ML champion +$237 full / +$90 prefix)
- SESSION_54_V39_DT_REPORT.md (Phase 1 diagnostic + Phase 2 v1 fail + Phase 2 v2 ship)
- STRATEGY_GUIDE.md (Session 54 entry in Part 1; updated ML champion table in Part 2)
- analysis/scripts/strategy_v39_dt.py — current ML champion
- analysis/scripts/pair_aug_v5_features_gated.py — production rank-valued features (template for next zone)
- analysis/scripts/drill_pair_zone_v36_diagnostic.py + drill_pair_v36_mismatch_handlevel.py — Phase 1 diagnostic templates

State (end of Session 54):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED) at
  $2,498 full / $1,522 prefix.
- ML champion: v39_dt (NEW) at $1,412 full / $801 prefix; 1.52M leaves at
  depth=36 ml=1; 87 features (83 base + 4 pair_aug_v5 rank-valued).
- Cumulative v32 → v39 = −$303 full / −$103 prefix.
- The two production tracks diverge by $1,086/1000h.
- Pair zone gap collapsed from $1,604 → $1,097 within-category (−$507, −32%).

USER-PRIORITY DIRECTION FOR SESSION 55:

Apply the Session 54 diagnostic-driven feature engineering playbook to the
next two ML residual zones in priority order:

(A) **Trips_pair zone** — $909/1000h within-category in v39_dt. Run the same
    4-phase plan:
    Phase 1: Drill the v39 vs oracle mismatch matrix at (trips_rank, pair_rank)
             cell level (analogue to Drill P).
    Phase 1b: Hand-level inspection of top 20 mismatches (analogue to Drill P2)
             to identify the under-modeled alternative configuration.
    Phase 2 v0: Optionally test capacity at depth=38 (likely byte-identical
             since 87-feature v39 is at depth-36 saturation; skip unless data
             suggests it).
    Phase 2 v1: SKIP boolean features — Session 54 lesson is they're redundant
             at ml=1 saturation.
    Phase 2 v2: Design 4-6 rank-valued conditional features describing the
             QUALITY of the alternative configuration (NOT just achievability).
             Train v40_dt.

(B) **Two_pair zone** — $918/1000h within-category in v39_dt. Same playbook.
    Likely target: alternatives v39 systematically under-routes.

(C) **High_only zone** — $2,796/1000h (largest within-category). Different
    feature types likely needed (top-card placement, defensive triggers);
    not primarily a pair-state problem. Lower priority than (A), (B).

(D) Rule chain — Rule 17 v2 / non-default top picks. Drill O has data. Lower
    priority than ML zones.

(E) Composite within-class — $960/1000h, small population, lower priority.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Methodology rule (Session 54 NEW): diagnostic-first feature engineering
  works at saturation — per-cell mismatch matrix + hand-level top-20
  inspection identifies the blind spot.
- Methodology rule (Session 54 NEW): boolean features are usually redundant
  with existing suit-distribution features at ml=1 saturation.
- Methodology rule (Session 54 NEW): rank-valued conditional features
  describing ALTERNATIVE configurations unlock saturation.
- Methodology rule (Session 54 NEW): feature design beats hyperparameter
  tuning at saturation. v37 depth=38 was byte-identical to v36.
- Methodology rule (Session 54 NEW): conditional features should describe
  alternative configs, not the chosen one — gives DT info to compare options.
- Methodology rule (Session 53 NEW): high-rank sub-pops defy defensive;
  low-rank sub-pops favor defensive; per-(max, s2) cells reveal the right gates.
- Methodology rule (Session 53 NEW): layered ships can regress; always test
  the combo not just components.
- Methodology rule (Session 49 NEW): sanity-check pick-difference rate BEFORE
  grading.
- Methodology rule (Session 47 NEW): cross-class within-pop "DS premium" lens
  ships rules reliably.
- Methodology rule (Session 46 NEW): drill "best-in-class minus production
  pick" to discover ship targets.
- Methodology rule (Session 44): cross-class regret averaging is confounded;
  use within-hand pairwise.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2
  (now updated for 87-feature v39: depth=36 ml=1 saturated at 36).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
