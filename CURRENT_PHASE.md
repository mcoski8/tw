# Current: Sprint 8 — Session 71 Phase 1a/1b/2 COMPLETE. Diagnostic-driven ML retrain pivot to v46_dt is set up. The setting-rank diagnostic on v44_dt's high_only residual ($381.39 WG total, matches S59 HO11 to 4 decimals) partitions the leak into MATCH 41.8% / NOISE 20.9% / MID 40.4% / STRUCTURE 38.7%. **STRUCTURE-bucket leak ($147.59 WG, 11.2% of hands, rank ≥10 in oracle's sorted-EV list) is NOT noise** — gap_2nd ≈ 0.11-0.14 ($1,100-1,400 regret per hand) — i.e. testable feature-engineering headroom. The dominant STRUCTURE mismatch family across K/Q/J/A × DS_NO_JOINT is **`SS_mu → SS_ms`** ($10+ WG aggregate; v44 picks SS bot with unsuited mid, oracle picks SS bot with suited mid at same top). v44's 107 features have ZERO SS+ms enumeration features — clean non-derivability story. Phase 2 implements H1 as `high_only_aug_v6_features_gated.py` (2 features: `topMax_SS_ms_n_configs_g` + `topMax_SS_ms_max_mid_high_g`, direct SS-axis counterpart to ho_v3's DS-axis pair that shipped +$79 in S57). Smoke tests pass on 5 hand-crafted cases. Persist script ready; full retrain (v46_dt at depth=32 ml=3) queued for S72.

> **🎯 IMMEDIATE NEXT ACTION (Session 72): persist + train v46_dt.**
>
>   Phase 1: run `persist_high_only_aug_v6_gated.py` to write
>   `data/feature_table_high_only_aug_v6_gated.parquet` (~6 MB; 2
>   features × 6,009,159 canonical hands × int8). ~30 sec.
>
>   Phase 2: run `train_v46_dt.py` at **depth=32 ml=3** (project
>   default; v44 was depth=36 ml=1, v45 was depth=36 ml=1 NULL —
>   v46 deliberately switches regime to test whether the saturation
>   hypothesis is the binding constraint vs the feature-set
>   constraint). 107 + 2 = 109 features. Expected fit time ~10 min.
>
>   Phase 3: tripwire prediction BEFORE grading —
>     * v6 features rank inside top-50 importance (vs v5's #66/#97/...).
>     * Leaf count grows ≥10K above v44's 2.25M (vs v5's +9 NULL signal).
>     * Both → predict ship. Either alone → ambiguous.
>
>   Phase 4: grade v46_dt on prefix (500K, n=1000) then full (6M,
>   n=200). Compute within-cat WG delta on high_only specifically.
>
>   Phase 5: if v46_dt ships, harness-predict the v56 hybrid lift
>   (v44 invoked inside v54/v55/v56 across ~40% of canonical grid;
>   any v44 improvement compounds ~4×). If predicted lift >$20 WG,
>   build and ship v57_hybrid_chain = v56 with v46_dt replacing
>   v44_dt internally. Otherwise queue more features (H2/H3/H4/H5
>   from SESSION_71_V45_FEATURE_HYPOTHESES.md Section 6).
>
>   **PREDICTED SHIP RANGE** (per S71 Phase 1b analysis):
>   - If H1 closes 25% of `SS_mu→SS_ms` STRUCTURE+MID mismatches:
>     ~$2.5 WG within-cat → ~$10 WG full-grid via v56 chain.
>   - If H1 closes 50%: ~$5 WG within-cat → ~$20 WG full-grid.
>   - **Best plausible (75% close): ~$30 WG full-grid.**
>   - **NULL scenario:** features rank #50+ in importance + leaf
>     growth <1K. Confirms saturation hypothesis. Pivot to depth=36
>     ml=1 retry (v46b_dt) or gradient boosting.
>
>   **ACCEPTANCE for Session 72:**
>   - v46_dt trained + graded (prefix + full).
>   - Decision in DECISIONS_LOG.md: ship / NULL / partial.
>   - If ship: STRATEGY_GUIDE.md Part 1 entry; production state
>     update.
>   - If NULL: write SESSION_72 NULL report mirroring SESSION_59;
>     queue H2/H3 for S73 or pivot to model class.

> **✅ ARTIFACTS produced in S71:**
> 1. **`analysis/scripts/drill_v44_high_only_S71.py`** — Phase 1a
>    diagnostic sweep script (introduces setting-rank lens beyond S58/
>    S59's class-label lens).
> 2. **`data/drill_v44_high_only_S71_per_hand.parquet`** (16.2 MB) —
>    per-hand setting-rank, EV-gap structure, structural cell. 1.226M
>    rows.
> 3. **`data/drill_v44_high_only_S71_summary.json`** (248 KB) —
>    aggregated stats keyed by (max_rank, cell, bucket).
> 4. **`data/session71/drill_v44_high_only_S71.log`** — full console
>    output of HO_S71_1..4 tables.
> 5. **`SESSION_71_V45_FEATURE_HYPOTHESES.md`** — Phase 1b deliverable
>    with 5 hypotheses (H1-H5), implementation plan, S72 retrain queue,
>    NULL/ship/partial decision tree.
> 6. **`analysis/scripts/high_only_aug_v6_features_gated.py`** —
>    Phase 2 implementation. 2 features: `topMax_SS_ms_n_configs_g`
>    (0..15) + `topMax_SS_ms_max_mid_high_g` (0..14). Smoke tests
>    pass on 5 hand-crafted cases including gating (pair AA→0), rest
>    2+2+2 (SS+ms structurally impossible→0), rest 3+1+1+1 (→0),
>    rest 2+2+1+1 (→2 configs, max_mid_high=13).
> 7. **`analysis/scripts/persist_high_only_aug_v6_gated.py`** —
>    persistence harness (parallel to persist_high_only_aug_v3-v5).
>    Queued for S72.
> 8. **`DECISIONS_LOG.md`** — Decision 106 appended.
> 9. **`CURRENT_PHASE.md`** — rewritten for S72 (this file).
> 10. **`STRATEGY_GUIDE.md`** — Parts 2-6 updated front-matter date;
>    Part 1 SKIPPED per protocol (no strategy of record changed this
>    session).

> **📓 METHODOLOGY (Session 72+):**
> - **The setting-rank lens generalizes.** S71's NOISE/MID/STRUCTURE
>   partition can be applied to ANY category. After v46_dt grades on
>   high_only, applying the same lens to pair / two_pair / trips
>   residuals will identify their STRUCTURE concentrations and
>   non-derivable feature gaps. The lens is a permanent addition to
>   the diagnostic toolkit.
> - **The "non-derivable feature" rule** from S71 design:
>     1. Cannot be a linear combination of v44 features.
>     2. Cannot be a bounded extension of v44 features.
>     3. Must enumerate a structural axis with no representative in
>        v44's 20 ho_v* / pair_aug_v* / trips_aug_v* / etc. feature
>        family.
>   ho_v6 H1 satisfies all 3 (SS-axis is genuinely absent from v44).
>   This rule is the S59 NULL postmortem operationalized.
> - **Hyperparameter regime change is itself a hypothesis.** v44 +
>   v45 both used depth=36 ml=1 (saturation). v46_dt switches to
>   depth=32 ml=3 (project default). If v46 ships at depth=32 ml=3
>   but a hypothetical v46b at depth=36 ml=1 NULLs, the saturation
>   hypothesis is CONFIRMED and depth=32 ml=3 should become the new
>   default. If both ship, the regime change is harmless. If neither
>   ships, H1 itself was wrong.
> - **The v6 → v46_dt name pairing** is the project's standard
>   feature-batch → model-version naming. ho_v1/ho_v2/.../ho_v5 each
>   paired with a v* model; ho_v6 → v46_dt continues the chain.
>   v45_dt is preserved as historical NULL record.
> - **"Speed is not necessary — clarity and perfection is."**
>   S71's diagnostic took the time to introduce a new lens (setting-
>   rank) rather than re-running S58/S59's class-label lens. The new
>   lens revealed information the old one couldn't — STRUCTURE
>   isolation by rank. The lens was the deliverable; v46_dt is the
>   test of whether new features within that lens can ship.

> Updated: 2026-05-12 (Session 71 end — drill + hypothesis doc + ho_v6 features + smoke tests; v46_dt retrain queued for S72)

---

## Headline state at end of Session 71

**Strategies of record (UNCHANGED from S70):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain (blanket trips → v44_dt; else → v55). **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED; invoked inside v54+v55+v56 across ~40% of canonical grid). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: $348/1000h (no change in S71 — pure diagnostic
+ feature engineering session, no production strategy shipped).

**S71 diagnostic findings on v44_dt's high_only residual:**

| Bucket | Definition | hands | % of hands | $ WG | % of WG |
|---|---|---:|---:|---:|---:|
| MATCH | rank 1 (==oracle) | 513,469 | 41.8% | $0.00 | 0.0% |
| NOISE | rank 2-3 | 308,313 | 25.1% | $79.54 | 20.9% |
| MID | rank 4-9 | 267,161 | 21.8% | $154.26 | 40.4% |
| STRUCTURE | rank ≥10 | 137,997 | 11.2% | **$147.59** | **38.7%** |
| **TOTAL** | | **1,226,940** | | **$381.39** | |

**Top STRUCTURE concentration cells (83.6% of STR leak):**

1. K × DS_NO_JOINT: $36.63 WG (16.2% STR rate)
2. A × DS_NO_JOINT: $29.41 WG (6.0% STR rate)
3. Q × DS_NO_JOINT: $22.42 WG (22.2% STR rate)
4. J × DS_NO_JOINT: $10.23 WG (25.5% STR rate)
5. K × DS_NO_MAXTOP: $8.43 WG (20.1% STR rate)
6. A × DS_NO_MAXTOP: $6.87 WG (8.2% STR rate)
7. K × MS_ONLY: $4.76 WG (18.1% STR rate)
8. Q × DS_NO_MAXTOP: $4.68 WG (23.6% STR rate)

**Per-max-rank rollup** (highlighting K/Q/J/T's STRUCTURE-dominance):

| max | hands | MATCH | NOISE $ | MID $ | STR $ | TOTAL $ | STR fraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 660,660 | 44.9% | $50.30 | $88.70 | $43.51 | $182.51 | 23.8% |
| K | 330,330 | 39.3% | $18.58 | $39.75 | **$52.61** | $110.94 | **47.4%** |
| Q | 150,150 | 37.1% | $7.01 | $16.74 | **$31.49** | $55.24 | **57.0%** |
| J | 60,060 | 35.4% | $2.55 | $6.41 | **$14.47** | $23.43 | **61.8%** |
| T | 20,020 | 38.1% | $0.88 | $2.08 | $4.31 | $7.27 | 59.3% |
| 9 | 5,005 | 42.9% | $0.20 | $0.51 | $1.02 | $1.74 | 58.6% |
| 8 | 715 | 40.7% | $0.03 | $0.07 | $0.18 | $0.28 | 64.3% |

**Dominant STRUCTURE-bucket mismatch family (`SS_mu → SS_ms`):**

| Cell × bucket | Top mismatch class | n hands | $ WG |
|---|---|---:|---:|
| A × DS_NO_JOINT × STR | `tA_SS_mu → tA_SS_ms` | 4,418 | $5.47 |
| K × DS_NO_JOINT × STR | `tK_SS_mu → tK_SS_ms` | 3,034 | $3.40 |
| Q × DS_NO_JOINT × STR | `tQ_SS_mu → tQ_SS_ms` | 1,026 | $1.12 |
| J × DS_NO_JOINT × STR | `tJ_SS_mu → tJ_SS_ms` | 144 | $0.15 |

Same top rank, same SS bot suit profile — only difference is whether
the mid pair shares a suit. **v44 has no SS+ms enumeration features
of any kind** (zero ho_v* features mention SS). H1's 2 features
(`topMax_SS_ms_n_configs_g`, `topMax_SS_ms_max_mid_high_g`) fill this
gap.

---

## Resume Prompt (Session 72 — train v46_dt)

```
Resume Session 72 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S71 — v46_dt retrain queued)
- SESSION_71_V45_FEATURE_HYPOTHESES.md (5 hypotheses, H1 selected)
- DECISIONS_LOG.md (latest: Decision 106 — S71 diagnostic + ho_v6
  feature plan)
- analysis/scripts/high_only_aug_v6_features_gated.py (ho_v6 H1
  features, smoke-tested)
- analysis/scripts/persist_high_only_aug_v6_gated.py (ready to run)
- analysis/scripts/train_v45_dt.py (template for train_v46_dt.py;
  same shape, swap ho_v5 → ho_v6, switch hyperparams to depth=32 ml=3)
- SESSION_54_V39_DT_REPORT.md (rank-valued feature shipping playbook)
- SESSION_59_V45_DT_REPORT.md (NULL retrospective — what to avoid)

State (end of Session 71):
- Diagnostic complete (Phase 1a): setting-rank lens partitions
  high_only $381 WG into MATCH 41.8% / NOISE 20.9% / MID 40.4% /
  STRUCTURE 38.7%. Top STRUCTURE cells: K/A/Q/J × DS_NO_JOINT
  account for $98.69 WG = 66.9% of all STRUCTURE leak.
- Hypothesis doc complete (Phase 1b): 5 hypotheses; H1 (SS+ms route
  quality) selected for S71 implementation.
- Features implemented + smoke-tested (Phase 2):
  high_only_aug_v6_features_gated.py with 2 features
  (`topMax_SS_ms_n_configs_g`, `topMax_SS_ms_max_mid_high_g`). Direct
  SS-axis counterpart to ho_v3's DS-axis pair (which shipped +$79
  in S57). 5 smoke tests pass.
- Persist script ready: persist_high_only_aug_v6_gated.py.

USER DIRECTIVE (S59-S71 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 72 — train + grade v46_dt:

  PHASE 1 (S72 ~5 min) — Persist features:
  - Run `python3 analysis/scripts/persist_high_only_aug_v6_gated.py`.
  - Verify `data/feature_table_high_only_aug_v6_gated.parquet`
    written (~6 MB).
  - Distribution sanity: most hands should have 0 SS+ms configs;
    moderate fraction (~20-40%) should have ≥1 config; max
    n_configs ~3-5 in practice.

  PHASE 2 (S72 ~15 min) — Train v46_dt at depth=32 ml=3:
  - Build `analysis/scripts/train_v46_dt.py` mirroring train_v45_dt.py
    structure. FEATURE_COLUMNS = V44_COLUMNS + HO_V6_COLUMNS (107+2
    = 109). Default args: --max-depth 32 --min-samples-leaf 3
    (project default per CURRENT_PHASE.md S70 memo; v44/v45 used
    depth=36 ml=1, so this is a deliberate regime change to test
    whether saturation was the binding constraint).
  - Run training. Save to `data/v46_dt_model.npz`.
  - Inspect feature importance: ho_v6 features inside top-50 → ship
    signal; rank #50+ → ambiguous; rank #100+ → NULL signal.
  - Inspect leaf count: ≥10K growth above v44's 2.25M → ship signal;
    <1K growth → NULL signal (like v45's +9).

  PHASE 3 (S72 ~10 min) — Build inference + grader:
  - `analysis/scripts/strategy_v46_dt.py` mirroring strategy_v45_dt.py
    structure; load v46_dt_model.npz; expose strategy_v46_dt(hand).
  - `analysis/scripts/grade_v46_dt.py` mirroring grade_v45_dt.py.

  PHASE 4 (S72 ~20 min) — Grade prefix + full:
  - Prefix grader (500K hands, n=1000) — fast sanity.
  - Full grader (6M hands, n=200) — definitive within-cat
    high_only WG delta vs v44.
  - Compute per-category byte-identity check (other 7 categories
    should be byte-identical to v44 if gating is surgical, mirroring
    the ho_v3-v5 pattern).

  PHASE 5 (S72 last ~30 min) — Decision + hybrid extension:
  - If v46_dt ships ≥$10 WG full-grid: build
    `analysis/scripts/strategy_v57_v46_hybrid.py` mirroring v56 with
    v46_dt as the ML champion inside trips/two_pair/pair-PBOT
    routing. Pre-grader harness predicts v57 lift from v46's
    high_only improvement × 4 (hybrid chain compounding).
  - If v46_dt NULL-grades: write SESSION_72 NULL report mirroring
    SESSION_59. Queue depth=36 ml=1 retry (v46b_dt) or pivot to H2
    (route-tradeoff comparator) or H4 (MS_ONLY discriminator).

  ACCEPTANCE for Session 72:
  - v46_dt trained + graded.
  - Decision 107 in DECISIONS_LOG.md: ship / NULL / partial.
  - If ship: STRATEGY_GUIDE.md Part 1 entry + v57 hybrid build.
  - If NULL: SESSION_72_V46_DT_NULL_REPORT.md mirroring S59.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- Hyperparam choice: depth=32 ml=3 (NOT v44/v45's depth=36 ml=1).
  This is deliberate — testing whether the saturation hypothesis was
  the binding constraint.
- Tripwire prediction (S59 lesson): low feature importance + zero
  leaf growth = strong NULL signal. Check both BEFORE running grader
  to avoid wasted compute.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
