# Current: Sprint 8 — Session 77 pair-first deep-drill ships; LOW pair (rank 2-7) identified as carrier of 74.6% of pair's STRUCTURE leak ($86.54 of $116.04/1000h); 5 LOW PMID/PBOT cells carry $84.56 with a single dominant mismatch pattern (v44 over-routes to SPLIT/PBOT, oracle keeps PMID); three feature hypotheses (H6/H7/H8) queued for S78 v48_dt retrain at depth=36 ml=1

S76 cross-category diagnostic identified pair as the highest-leverage next ML/rule target ($116.04/1000h STRUCTURE-bucket leak, never drilled with the setting-rank lens). S77 PHASE 1 designed `compute_hand_structural_minimal_pair()` combining S66's 6-cell structural taxonomy (PBOT_DS_JOINT / PBOT_DS_PARTIAL / PMID_DS_MAXTOP / PMID_DS_NOMAXTOP / PMID_SS_MAXTOP / PMID_OTHER) with S71's NOISE/MID/STRUCTURE setting-rank lens, plus pair_rank_tier (LOW 2-7 / MID 8-T / HIGH J-A) and non-pair-card structural axes.

S77 PHASE 2 ran `drill_v44_pair_S77.py` on the full 2,800,512 pair hands in **10.2 min wall** (~4,500 hands/sec). Total pair WG $511.16/1000h reconstituted exactly — validates the drill against v44_dt grade.

**Result: pair STRUCTURE leak concentrates in LOW tier with a single dominant mismatch pattern.** Production state UNCHANGED for the **sixth** consecutive session (S72 NULL, S73 PARTIAL/NULL ship, S74 clean NULL, S75 boosting NULL, S76 diagnostic ship, S77 diagnostic ship).

**Full-grid pair STRUCTURE decomposition by pair_rank_tier:**

| tier | pair ranks | n | STR $/1000h | STR/tier_total |
|---|---|---:|---:|---:|
| **LOW** | 22-77 | 1,292,544 | **$86.54** | **30.7%** |
| MID | 88-TT | 646,272 | $15.93 | 16.5% |
| HIGH | JJ-AA | 861,696 | $13.57 | 10.2% |
| TOTAL | — | 2,800,512 | $116.04 | 22.7% |

**Top 5 STRUCTURE-bucket cells (v48 target population):**

| rank | tier | cell | n_STR | STR $/1000h | gap_2nd_med |
|---:|---|---|---:|---:|---:|
| 1 | LOW | PMID_DS_NOMAXTOP | 11,884 | $31.00 | 0.1800 |
| 2 | LOW | PMID_DS_MAXTOP | 6,760 | $21.68 | **0.3850** |
| 3 | LOW | PMID_OTHER | 5,355 | $11.81 | 0.1850 |
| 4 | LOW | PBOT_DS_PARTIAL | 7,977 | $10.36 | 0.1150 |
| 5 | LOW | PMID_SS_MAXTOP | 4,484 | $9.71 | 0.1650 |
| **sum** | | | **36,460** | **$84.56** | — |

**Dominant mismatch pattern (the v44 systematic error):**

> **v44 systematically over-routes LOW pairs (2-7) to SPLIT (or PBOT) when oracle keeps the pair in MID.** Single largest mismatch class: `SPLIT_tmax_SS_mu → PMID_tmax_DS` in LOW × PMID_DS_MAXTOP, n=3,072 hands, $10.97/1000h on ONE class out of pair's $116 STR total. Cell 4 (LOW × PBOT_DS_PARTIAL) is the REVERSE exception (v44 stays PMID, oracle routes PBOT_DS); discriminator is kicker_max suit alignment with pair_suits.

**Three feature hypotheses queued for S78 v48_dt retrain:**

| H# | Feature | Type | Gate | Expected within-pair $ | Full-grid $ |
|---|---|---|---|---:|---:|
| **H6** | `pair_pmid_ds_n_configs_g` | int8 0..5 | single-pair | $15-26 | $7-12 |
| **H7** | `pair_kicker_max_in_pair_suit_g` | bool 0/1 | single-pair | $14-21 | $5-10 |
| **H8** | `pair_low_pmid_safety_g` | int8 0..5 | LOW pair only | $22-35 | $10-17 |
| **H6+H7+H8 joint (50% redundancy budget)** | | | | **$30-45** | **$14-22** |

**Decision 112: Diagnostic ship; H6/H7/H8 feature pack queued for S78.** Details in DECISIONS_LOG.md and `PAIR_S77_FEATURE_HYPOTHESES.md`.

> **🎯 IMMEDIATE NEXT ACTION (Session 78): Implement H6+H7+H8, train v48_dt at depth=36 ml=1, grade vs v44**
>
> 1. **(PHASE 1 — ~30 min)** Implement the 3 new pair-gated feature files:
>    - `analysis/scripts/pair_pmid_ds_features_gated.py` — H6: `pair_pmid_ds_n_configs_g` (int8 0..5).
>    - `analysis/scripts/pair_kicker_align_features_gated.py` — H7: `pair_kicker_max_in_pair_suit_g` (bool 0/1).
>    - `analysis/scripts/pair_low_pmid_safety_features_gated.py` — H8: `pair_low_pmid_safety_g` (int8 0..5; gated to LOW pair only).
>    - Each with sanity tests on canonical examples from `PAIR_S77_FEATURE_HYPOTHESES.md`.
>
> 2. **(PHASE 2 — ~5 min)** Persist gated parquet packs:
>    - `analysis/scripts/persist_pair_pmid_ds_gated.py`
>    - `analysis/scripts/persist_pair_kicker_align_gated.py`
>    - `analysis/scripts/persist_pair_low_pmid_safety_gated.py`
>    - Verify zero values on all non-pair hands (and non-LOW-pair hands for H8).
>
> 3. **(PHASE 3 — ~3-5 min)** Smoke train v48_dt on 100K rows:
>    - depth=36, ml=1, criterion=squared_error (S73 regime LOCKED).
>    - Verify H6/H7/H8 land in top-30 feature importance. If they don't, the new features are not being used by the saturating DT — likely redundancy-NULL; abort the full retrain and document.
>
> 4. **(PHASE 4 — ~25-40 min)** Full train v48_dt on 4.8M training rows. Expect ~2.25M leaves and a model ~1,260 MB (same scale as v44).
>
> 5. **(PHASE 5 — ~3 min)** Prefix grade v48 vs v44. Decision branches:
>    - prefix Δ ≥ +$5 → proceed to full grade.
>    - prefix Δ < +$5 → NULL ship; document the within-pair lift; consider pair-only sub-strategy.
>
> 6. **(PHASE 6 — ~18 min)** Full grade v48 vs v44 on 6M-hand realistic-mixture grid.
>    - Δ ≥ +$10/1000h → SHIP. Update v44_dt → v48_dt as ML champion.
>    - Δ ∈ [+$5, +$10) → PARTIAL POSITIVE; NULL ship at +$10 bar per S73 codification.
>    - Δ < +$5 → CLEAN NULL ship.
>
> 7. **(PHASE 7 — ~5 min)** Decision 113 in DECISIONS_LOG.md; SESSION_78_V48_DT_REPORT.md; CURRENT_PHASE.md rewritten for S79.
>
> **📓 METHODOLOGY (Session 78+):**
>
> 1. **S73 regime LOCKED for v48.** Do NOT sweep depth/ml; v44's parameters are the validated saturating regime. Sweeping consumes hours of compute and the S36 capacity-retest lesson (`feedback_taiwanese_capacity_retest.md`) only applies when feature count grows ≥10 above last sweep — three new features doesn't qualify.
>
> 2. **Smoke-train BEFORE full-train.** A 100K-row sanity smoke catches "new features not used" (= structural-redundancy NULL) and "DT mis-loads features" (= integration bug) in ~30 sec wall. v44 full retrain is ~30 min; smoke saves a full session's worth of compute if features are dead-on-arrival.
>
> 3. **Verify feature importance lands.** H6/H7/H8 should rank in the top-30 of v48 feature importance (v44's pair features rank ~30-50; new pair features should rank similarly if they're being used). If H6/H7/H8 rank ≥80, they're effectively unused — NULL is preordained.
>
> 4. **Reverse-direction mismatch caveat.** Cell 4 (LOW × PBOT_DS_PARTIAL) is the exception where v44 should route to PBOT, not PMID. H8 alone would push it the wrong way; H6+H7 are needed to give the DT room to learn the kicker_max alignment discriminator. NEVER ship H8 standalone.
>
> 5. **+$10 ship bar canonical (S73 codified, held S74-S77).** Sixth consecutive session UNCHANGED production state. The bar is filtering noise from signal as designed.
>
> 6. **"Speed is not necessary — clarity and perfection is."** S77 spent ~10 min wall on the drill and ~30 min on hypothesis documentation, producing a data-supported feature pack with quantified expected lift on the cleanest fresh signal target in the project. S78 should match that discipline: smoke-validate, single training run, single grade, decision.

> **✅ ARTIFACTS produced in S77:**
> 1. `analysis/scripts/drill_v44_pair_S77.py` — pair-only setting-rank deep-drill, combines S66 6-cell taxonomy with S71 bucket lens + pair_rank_tier + non-pair-card structural axes.
> 2. `data/drill_v44_pair_S77_summary.json` (216.7 KB) — per (tier, cell, bucket) WG decomposition, gap_2nd / plateau width stats, top mismatch classes, fingerprint distributions.
> 3. `data/session77/drill_v44_pair_S77.log` — full console output (10.2 min wall, 4,500 hands/sec).
> 4. `data/session77/drill_smoke_5k.log` — 5K-hand smoke validation.
> 5. `PAIR_S77_FEATURE_HYPOTHESES.md` — H6/H7/H8 feature definitions, derivation arguments, expected lift estimates, redundancy risk assessments.
> 6. `DECISIONS_LOG.md` — Decision 112 (S77 diagnostic findings + H6/H7/H8 hypothesis pack).
> 7. `CURRENT_PHASE.md` — rewritten for S78 (this file).
> 8. `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record changed); Parts 2-6 front-matter date refresh.

> Updated: 2026-05-13 (Session 77 end — pair-first deep-drill ships; LOW tier carries 74.6% of pair's STRUCTURE leak; 5 LOW cells × 36,460 hands × $84.56/1000h identified as the v48 target population; dominant mismatch pattern is v44 over-routing LOW pairs to SPLIT/PBOT when oracle keeps PMID; H6/H7/H8 feature pack queued for S78; production state UNCHANGED for the sixth consecutive session)

---

## Headline state at end of Session 77

**Strategies of record (UNCHANGED from S76):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion. $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S77 — pure diagnostic session, no model trained or rule shipped).

**S77 diagnostic summary:**

| Metric | Value | Notes |
|---|---:|---|
| Pair hands swept | 2,800,512 | full pair sub-grid |
| Wall time | 614.5s (10.2 min) | ~4,500 hands/sec steady-state |
| Total $/1000h reconstituted | $511.16 | matches v44_dt pair contribution exactly |
| STRUCTURE-bucket $ | $116.04 | matches S76 exactly |
| NOISE-bucket $ | $206.73 | matches S76 exactly |
| MID-bucket $ | $188.38 | matches S76 exactly |
| Top tier carrier | LOW (74.6% of STR leak) | $86.54/1000h |
| Top single STR cell | LOW × PMID_DS_NOMAXTOP | $31.00 / 11,884 hands |
| Sharpest STR cell | LOW × PMID_DS_MAXTOP | gap_2nd_med 0.3850 |
| Single largest mismatch class | `SPLIT_tmax_SS_mu → PMID_tmax_DS` | n=3,072, $10.97/1000h |

---

## Hypothesis cascade status (updated after S77)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | high_only SS+ms route quality (2 ho_v6 features) | TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h (S73). |
| **H2** | high_only route-tradeoff comparator (1 ho_v7 feature) | TESTED → CLEAN NULL at +$0/1000h (S74). |
| Option B (S75) | Gradient boosting at v44 features (depth=6, n_est=200) | TESTED → DECISIVE NULL at −$1,392/1000h. |
| S76 Option B | Cross-category setting-rank diagnostic | SHIPPED → identified pair-first as next target. |
| **S77 pair drill** | Pair-only setting-rank × S66 cell deep-drill | **SHIPPED → identified H6/H7/H8 feature hypotheses.** |
| H3 | high_only SS+ms route VARIETY signal | UNTESTED. Deprioritized — pair offers fresher signal. |
| H4 | high_only MS_ONLY discriminator | UNTESTED. Deprioritized — small WG target. |
| H5 | high_only Drop-max signal | UNTESTED. Dead (relied on H2 infrastructure). |
| **NEW H6** | `pair_pmid_ds_n_configs_g` — PMID DS-bot path count | **QUEUED for S78 PHASE 1.** |
| **NEW H7** | `pair_kicker_max_in_pair_suit_g` — kicker-max suit alignment | **QUEUED for S78 PHASE 1.** |
| **NEW H8** | `pair_low_pmid_safety_g` — LOW-pair S66 cell categorical | **QUEUED for S78 PHASE 1.** |
| Option A (S78+) | Oracle-label N=1000 re-evaluation | Empirically justified for two_pair / three_pair / trips_pair specifically; **GATED on cluster access**. |
| Option C (S78+) | Higher-capacity gradient boosting (depth=8-10, n_est=1000+) | Deprioritized — 15-25 hours wall, speculative closure of $1,392 gap. |
| Option D (S78+) | Rule-chain extension targeting LOW pair PMID-vs-SPLIT routing | LATENT — could ride on S77 drill findings if v48_dt NULLs. |

**Cascade verdict (updated):** S77 produced the cleanest fresh feature-pack hypothesis the project has surfaced since the S33-S35 pair_aug_v2 work. H6/H7/H8 jointly expected to clear the +$10 ship bar with moderate margin (estimated $14-22 full-grid lift at 50% redundancy budget). **S78 will test the pair-feature track at v44 saturation; either ships v48 or definitively closes pair feature engineering at v44's regime.**

---

## Resume Prompt (Session 78 — Implement H6+H7+H8, train v48_dt, grade vs v44)

```
Resume Session 78 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S77 — H6/H7/H8 pair feature pack
  queued for v48_dt retrain)
- PAIR_S77_FEATURE_HYPOTHESES.md (full hypothesis definitions, expected
  lifts, redundancy risk assessments)
- SESSION_76_DIAGNOSTIC_REPORT.md + drill_v44_pair_S77 outputs
  (data/drill_v44_pair_S77_summary.json) for the underlying data
- DECISIONS_LOG.md (latest: Decision 112 — S77 pair drill + H6/H7/H8 plan)
- analysis/scripts/pair_aug_v5_features_gated.py (template for H6 feature
  code; mirror the file structure)
- analysis/scripts/strategy_v44_dt.py (feature loader; H6/H7/H8 need new
  _PAIR_*_NAMES entries + index_in_full)

State (end of S77):
- Pair drill complete (10.2 min wall, 2.8M hands swept). LOW tier (2-7)
  carries 74.6% of pair's STRUCTURE-bucket leak ($86.54 of $116.04/1000h).
- Top 5 LOW cells × 36,460 hands × $84.56/1000h identified as v48 target
  population. Dominant mismatch pattern: v44 over-routes LOW pairs to
  SPLIT/PBOT, oracle keeps PMID.
- H6 (`pair_pmid_ds_n_configs_g`, int8 0..5, single-pair gated): expected
  $7-12/1000h full-grid.
- H7 (`pair_kicker_max_in_pair_suit_g`, bool 0/1, single-pair gated):
  expected $5-10/1000h full-grid.
- H8 (`pair_low_pmid_safety_g`, int8 0..5, LOW-pair-only gated): expected
  $10-17/1000h full-grid.
- H6+H7+H8 joint expected lift (50% redundancy budget): $14-22/1000h
  full-grid — clears the +$10 ship bar with moderate margin.
- Production state UNCHANGED for the sixth consecutive session.

USER DIRECTIVE (S59-S77 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship threshold canonical (codified S73, held S74-S77).

DIRECTION FOR SESSION 78 — Implement H6+H7+H8, train v48_dt, grade vs v44:

  PHASE 1 (S78 ~30 min) — Implement 3 new pair-gated feature files:
    - analysis/scripts/pair_pmid_ds_features_gated.py
    - analysis/scripts/pair_kicker_align_features_gated.py
    - analysis/scripts/pair_low_pmid_safety_features_gated.py
    With sanity tests on canonical examples from
    PAIR_S77_FEATURE_HYPOTHESES.md.

  PHASE 2 (S78 ~5 min) — Persist gated parquet packs.
    Verify zero values on non-pair hands (and non-LOW-pair for H8).

  PHASE 3 (S78 ~3-5 min) — Smoke-train v48_dt on 100K rows at depth=36
  ml=1. Verify H6/H7/H8 in top-30 feature importance. If they're not
  used, abort the full retrain — likely structural-redundancy NULL.

  PHASE 4 (S78 ~25-40 min) — Full-train v48_dt at depth=36 ml=1 on
  4.8M training rows. S73 regime LOCKED; no hyperparameter sweep.

  PHASE 5 (S78 ~3 min) — Prefix grade vs v44.
    Δ ≥ +$5 → proceed to full grade.
    Δ < +$5 → NULL ship; document pair-only sub-strategy alternative.

  PHASE 6 (S78 ~18 min) — Full grade on 6M-hand realistic-mixture grid.
    Δ ≥ +$10 → SHIP. v44_dt → v48_dt as ML champion.
    Δ ∈ [+$5, +$10) → PARTIAL; NULL ship at +$10 bar.
    Δ < +$5 → CLEAN NULL ship.

  PHASE 7 (S78 ~5 min) — Decision 113; SESSION_78_V48_DT_REPORT.md;
  CURRENT_PHASE.md rewritten for S79.

  ACCEPTANCE for Session 78:
  - 3 new feature files implemented with sanity tests passing.
  - Gated parquet packs persisted with zero-on-non-gated verification.
  - Smoke train completes; H6/H7/H8 importance verified.
  - v48_dt full-trained, prefix + full graded vs v44.
  - Ship decision made and documented in Decision 113.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- v44_dt model + features remain unchanged unless v48 ships.
- "Speed is not necessary — clarity and perfection is."
- Reverse-direction caveat: LOW × PBOT_DS_PARTIAL cell is where v44
  should route to PBOT (not PMID). H6+H7 must let the DT learn the
  kicker_max-alignment discriminator. NEVER ship H8 standalone.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
