# Current: Sprint 8 — Session 78 v48_dt H6+H7+H8 pair feature pack CLEAN NULL ships at prefix grade (Δ +$2/1000h); single-model ML feature-engineering track formally CLOSED at v44 saturating regime; **user (S78 end-of-session) rejected "ship at 65%" path and chose A-path: S79 pivots to label-noise measurement on existing N=1000 prefix grid to decide A-path (better labels) vs C-path (bigger model) for the next 3-5 sessions**

S77 queued three pair-gated feature hypotheses (H6/H7/H8) for v48_dt retrain at the S73 regime (depth=36, ml=1). S78 executed Phase 1-5 as planned. Phase 1 implemented and sanity-tested H6 (`pair_pmid_ds_n_configs_g`, int8 0..5 — though actual reachable values are {0,1,3}), H7 (`pair_kicker_max_in_pair_suit_g`, bool 0/1), H8 (`pair_low_pmid_safety_g`, int8 0..5, LOW-pair-only). H8's inline cell logic cross-validated against S66's `compute_pair_structural` + `cell_for_pair_hand` on 23,377 random single-pair canonical hands with zero disagreements.

Phase 2 persisted all three gated parquet packs (~18.6 MB each) with verified zero-on-non-gated. Phase 3 smoke train (100K rows, 2.5s wall) placed H7 #51 / H8 #69 / H6 #73 — all below the top-30 ideal but above the rank-80 abort gate. Phase 4 full train (4.8M rows, 578s wall, 2.29M leaves, 1,285 MB) improved placements to H7 #43 / H8 #57 / H6 #68.

**Phase 5 prefix grade returned Δ +$2/1000h (v44 $686 → v48 $684).** Within-pair lift was +$5/1000h ($595→$590) on 215,162 prefix pair hands. All other categories byte-identical (gating works correctly; new features touch only pair hands as designed). Per S78 directive (`prefix Δ < +$5 → NULL ship`), Phase 6 (full grade) was SKIPPED.

**Production state UNCHANGED for the seventh consecutive session** (S72 NULL, S73 PARTIAL/NULL, S74 NULL, S75 boosting NULL, S76 diagnostic, S77 diagnostic, S78 NULL).

**Why the predicted lift didn't land — structural-redundancy NULL reconfirmed:** S77 budgeted 50% redundancy across H6+H7+H8 and predicted $30-45/1000h within-pair joint lift. Observed is ~$5 within-pair = effective 85-90% redundancy. Three contributors: H6 only emits {0,1,3} (deck structure caps partitioning surface at ~3 bits); H7's 1-bit signal is derivable in 2 splits from existing v44 features; H8's 5-split cell synthesis is reachable in 3-4 splits at v44's 2.25M-leaf capacity. The S74 redundancy doctrine — features derivable in <few splits at saturation get zero or near-zero lift — is empirically reconfirmed. S77's cleanest-diagnostic-in-the-project hypothesis methodology does NOT break the redundancy ceiling.

**Decision 112 (S77): pair drill diagnostic ship. Decision 113 (S78): v48_dt CLEAN NULL ship; single-model ML feature-engineering track formally CLOSED at v44 regime.**

> **🎯 IMMEDIATE NEXT ACTION (Session 79): Label-noise measurement via existing N=1000 prefix grid — answer "is the gap real or is it label noise?" before committing to N=1000 expansion vs higher-capacity model**
>
> **The strategic question after S78's NULL:** v44_dt is at ~65% match rate against the oracle (full grid pct_opt 64.80%). Goal is 95%+. After 7 consecutive sessions with UNCHANGED production state, the user (S78 end-of-session conversation) explicitly rejected the "ship at 65%" path and asked us to find the gap. The S78 NULL empirically closed the single-model feature-engineering door; the next strategic decision is whether to invest in (A) better labels via N=1000 oracle re-evaluation, or (C) higher-capacity boosting models. **Step 1 is measurement, not commitment** — we have a 500K-hand N=1000 prefix grid already (`data/oracle_grid_prefix500k_n1000.bin`), and we have the same 500K hands labeled at N=200 in the full grid (since the prefix IS the first 500K canonical IDs). Comparing v44's regret under both labelings tells us how much of v44's measured leak is *real model error* vs *N=200 sampling noise*.
>
> 1. **(PHASE 1 — ~30 min)** Write `analysis/scripts/label_noise_measurement_S79.py`. For each of the 500K prefix canonical hands:
>    - Read v44's pick (cached from prior grade run, or recompute).
>    - Read oracle's #1 pick at N=200 (full grid evs[i].argmax()).
>    - Read oracle's #1 pick at N=1000 (prefix grid evs[i].argmax()).
>    - Compute n200_regret = full_evs[i][n200_pick] − full_evs[i][v44_pick].
>    - Compute n1000_regret = prefix_evs[i][n1000_pick] − prefix_evs[i][v44_pick].
>    - **Critical:** the two regret numbers are measured on DIFFERENT sample sizes against DIFFERENT label sets — they're not directly subtractable, but the *distribution shift* between them quantifies label noise.
>
> 2. **(PHASE 2 — ~15 min)** Aggregate by setting-rank bucket (S71 lens) and per-category:
>    - % of hands where v44 matches oracle changes: v44=n200 vs v44=n1000.
>    - $/1000h aggregate regret: v44 vs n200 oracle, v44 vs n1000 oracle.
>    - Per-bucket NOISE / MID / STRUCTURE breakdown (S76 hypothesis: label noise concentrates in NOISE bucket).
>    - Per-category breakdown (pair, two_pair, trips, etc.).
>
> 3. **(PHASE 3 — ~15 min)** Decision criterion:
>    - **If pct_opt(v44 vs N=1000) − pct_opt(v44 vs N=200) ≥ +5pp on prefix:** label noise is materially shifting which setting is "optimal." Confirms N=1000 expansion is high-ROI. → Phase 4 plans the targeted N=1000 grid expansion.
>    - **If pct_opt shifts < +2pp:** the labels are mostly stable; the gap is genuine model error. → Phase 4 plans Option C (high-capacity gradient boosting at depth=10-12, n_est=1000+).
>    - **If +2pp ≤ shift < +5pp:** mixed result; document and discuss with user before committing.
>
> 4. **(PHASE 4 — ~30 min)** Plan the next ~3-5 sessions based on Phase 3 verdict:
>    - **A-path (label noise wins):** design targeted N=1000 expansion. Candidates: (a) full-grid N=1000 on STRUCTURE-bucket hands only (~25.8% of grid ≈ 1.55M hands, ~24 hr local compute); (b) extend N=1000 prefix from 500K → 2M hands sampled uniformly across grid; (c) full N=1000 on the 6M grid (~5 days local compute, may need cluster). Pick one based on Phase 3 magnitude.
>    - **C-path (real gap wins):** scope a high-capacity XGBoost retry. S75 used depth=6 / n_est=200; the new attempt uses depth=10-12 / n_est=1000-2000 / longer-run early stopping. Build a smoke + full plan for S80.
>
> 5. **(PHASE 5 — ~10 min)** Decision 114 + `SESSION_79_LABEL_NOISE_REPORT.md` + CURRENT_PHASE.md rewrite for S80 with concrete next-step plan.
>
> ACCEPTANCE for Session 79:
> - Label-noise measurement complete with quantified pct_opt shift and regret-distribution comparison.
> - Per-bucket and per-category breakdown produced.
> - Phase 3 decision criterion applied; A-path or C-path declared.
> - DECISIONS_LOG.md updated with Decision 114.
> - CURRENT_PHASE.md rewritten for S80 with concrete next-step plan.
>
> **NOTE: This session does NOT attempt a ship.** It is a one-session diagnostic to decide which long-arm investment (A vs C) gets the next 3-5 sessions of compute. No +$10 ship bar applies. The deliverable is a clean answer to "where does the remaining 35-percentage-point gap to oracle live."
>
> **📓 METHODOLOGY (Session 79+):**
>
> 1. **Measure before committing.** S77 spent 30 min on a diagnostic that justified 1 session of feature engineering (S78). S79 spends 1-2 hours on measurement that justifies 3-5 sessions of compute investment (A-path or C-path). The asymmetry is intentional — the next move is bigger than any prior move.
>
> 2. **Use what we already have before generating new data.** The N=1000 prefix grid already exists; comparing it to the N=200 full grid is FREE compute. This should have been the first move after S75's boosting NULL, not the eighth.
>
> 3. **Decision criterion lives BEFORE the measurement.** Pre-committing to "if shift ≥ +5pp → A-path; if < +2pp → C-path" prevents post-hoc rationalization of whatever the data shows.
>
> 4. **No production state change expected in S79.** v44_dt + v56_trips_hybrid remain authoritative. The session output is a strategy-direction decision, not a new model or rule.
>
> 5. **+$10 ship bar canonical (S73 codified, held S74-S78).** Eight consecutive sessions UNCHANGED. Bar still filters correctly; S79 just doesn't pass through it (measurement, not ship).
>
> 6. **"Speed is not necessary — clarity and perfection is."** S79 should produce one clear answer to one clear question, well-documented. Don't bundle multiple investigations.
>
> 7. **The 65%-vs-95% gap framing is the operative goal.** All future strategic decisions should map back to "does this close the gap to 95% match rate" — not "does this ship +$X/1000h." The dollar-regret metric correlates with but doesn't equal the headline goal.

> **✅ ARTIFACTS produced in S78:**
> 1. `analysis/scripts/pair_pmid_ds_features_gated.py` — H6 feature, 8 sanity tests pass.
> 2. `analysis/scripts/pair_kicker_align_features_gated.py` — H7 feature, 9 sanity tests pass.
> 3. `analysis/scripts/pair_low_pmid_safety_features_gated.py` — H8 feature, 12 sanity tests pass; inline cell logic cross-validated against S66 on 23,377 hands (0 disagreements).
> 4. `analysis/scripts/persist_pair_pmid_ds_gated.py` + parquet (18.69 MB, 0-on-non-gated verified).
> 5. `analysis/scripts/persist_pair_kicker_align_gated.py` + parquet (18.64 MB, 0-on-non-gated verified).
> 6. `analysis/scripts/persist_pair_low_pmid_safety_gated.py` + parquet (18.60 MB, 0-on-non-LOW-pair verified).
> 7. `analysis/scripts/train_v48_dt.py` — full + smoke train with --max-rows.
> 8. `analysis/scripts/strategy_v48_dt.py` — v44 strategy + 3 new feature blocks.
> 9. `analysis/scripts/grade_v48_dt.py` — v48 vs v44 prefix/full grader.
> 10. `data/v48_dt_smoke.npz` (32.90 MB) — 100K-row smoke model.
> 11. `data/v48_dt_model.npz` (1,285 MB) — full v48 DT (kept for audit; production UNCHANGED).
> 12. `data/session78/*.log` — persist + train + grade logs.
> 13. `SESSION_78_V48_DT_REPORT.md` — Phase 1-5 report.
> 14. `DECISIONS_LOG.md` — Decision 113 (S78 CLEAN NULL ship + ML feature-engineering track CLOSED).
> 15. `CURRENT_PHASE.md` — rewritten for S79 (this file).
> 16. `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record changed); Parts 2-6 front-matter date refresh.

> Updated: 2026-05-13 (Session 78 end + end-of-session user discussion — v48_dt H6+H7+H8 pair feature pack CLEAN NULL ship at prefix grade Δ +$2/1000h; structural-redundancy doctrine reconfirmed at v44 saturating regime; single-model ML feature-engineering track formally closed; production state UNCHANGED for the seventh consecutive session. **User flagged 7-session production stall and rejected the "ship at 65% match rate" path; explicitly chose A-path (N=1000 oracle re-evaluation) to find the 30+pp gap to the 95% goal.** S79 plan rewritten: one-session label-noise measurement using existing 500K-hand N=1000 prefix grid (FREE compute — no new oracle sampling needed) to decide between A-path (label noise dominant → invest in N=1000 expansion) and C-path (real model gap → invest in high-capacity gradient boosting). Pre-committed decision criterion: match-rate shift ≥+5pp → A-path; <+2pp → C-path; +2-5pp → MIXED.)

---

## Headline state at end of Session 78

**Strategies of record (UNCHANGED from S77):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion. $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S78 — pure feature-engineering NULL session; v48 not adopted).

**S78 summary table:**

| Metric | Value | Notes |
|---|---:|---|
| Features added (v44→v48) | 3 | H6, H7, H8 |
| Total features (v48) | 110 | up from v44's 107 |
| v48 leaves | 2,294,001 | +44,001 vs v44 (+1.96%) |
| v48 depth | 36 | identical to v44 |
| Full train wall | 578s (9.6 min) | sklearn DT depth=36 ml=1 |
| Model size (v48) | 1,285 MB | similar to v44 |
| Prefix Δ vs v44 | **+$2/1000h** | below +$5 abort threshold |
| Within-pair Δ vs v44 (prefix) | **+$5/1000h** | $595 → $590 on 215K hands |
| Non-pair categories Δ | 0 (byte-identical) | gating works correctly |
| Full grade | SKIPPED | per directive |
| Within-pair pct_opt lift | +0.1pp | 69.2% → 69.3% |

---

## Hypothesis cascade status (updated after S78)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | high_only SS+ms route quality (ho_v6, 2 features) | TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h (S73). |
| **H2** | high_only route-tradeoff comparator (ho_v7, 1 feature) | TESTED → CLEAN NULL at +$0/1000h (S74). |
| Option B (S75) | Gradient boosting at v44 features | TESTED → DECISIVE NULL at −$1,392/1000h. |
| S76 Option B | Cross-category setting-rank diagnostic | SHIPPED diagnostic → identified pair as next target. |
| S77 pair drill | Pair-only setting-rank × S66 cell deep-drill | SHIPPED diagnostic → identified H6/H7/H8 hypotheses. |
| **H6** | `pair_pmid_ds_n_configs_g` | **TESTED S78 → CLEAN NULL (within-pair $5 of $15-26 budget; rank #68 importance).** |
| **H7** | `pair_kicker_max_in_pair_suit_g` | **TESTED S78 → CLEAN NULL (rank #43 importance; saturation absorbs).** |
| **H8** | `pair_low_pmid_safety_g` | **TESTED S78 → CLEAN NULL (rank #57; derivable in 3-4 splits at saturation).** |
| H3 | high_only SS+ms VARIETY signal | UNTESTED. Deprioritized — same redundancy ceiling. |
| H4 | high_only MS_ONLY discriminator | UNTESTED. Deprioritized — small WG target. |
| H5 | high_only Drop-max signal | UNTESTED. Dead (relied on H2 infrastructure). |
| **Option A (S79)** | Oracle-label N=1000 re-eval | **PRIORITIZED — START with FREE measurement on existing 500K N=1000 prefix grid.** |
| Option C | Higher-capacity boosting (depth=10-12, n_est=1000-2000) | Standby — selected only if S79 label-noise measurement shows gap is real model error. |
| Option D | Rule-chain extension on S77 LOW pair kicker_max discriminator | Deferred — borderline at ship bar ($5-8 expected); revisit after S79 if A/C dry. |

**Cascade verdict (updated post user discussion S78 end):** Single-model ML feature-engineering track CLOSED at v44 regime. The 65%-vs-95% match-rate gap is the operative strategic goal (user, S78 end-of-session). User explicitly rejected the "ship at 65%" path. **S79 pivots to a one-session label-noise measurement using existing N=1000 prefix grid — answers whether next compute investment should go into A-path (better labels) or C-path (bigger model).**

---

## Resume Prompt (Session 79 — Label-noise measurement via existing N=1000 prefix grid)

```
Resume Session 79 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S78 — label-noise measurement
  diagnostic; A-path vs C-path decision session)
- SESSION_78_V48_DT_REPORT.md (S78 NULL ship; ML feature-engineering
  track CLOSED at v44 saturating regime)
- DECISIONS_LOG.md (latest: Decision 113 — S78 v48 NULL + track CLOSED)
- analysis/src/tw_analysis/oracle_grid.py (read_oracle_grid API; both
  prefix and full grids load the same way)
- analysis/scripts/grade_v44_dt.py (template for the canonical/grid
  read pattern; the S79 measurement script borrows from this)

KEY DATA FILES:
- data/oracle_grid_prefix500k_n1000.bin — 500K hands × 105 settings at
  N=1000 samples. Prefix = first 500K canonical IDs.
- data/oracle_grid_full_realistic_n200.bin — 6M hands × 105 settings
  at N=200 samples. First 500K canonical IDs of this grid are the SAME
  hands as the prefix, but labeled at lower fidelity.
- data/canonical_hands.bin — 6M canonical 7-card hands.

STATE (end of S78):
- v44_dt match rate vs full-grid oracle: 64.80% (35.2pp gap to 95% goal).
- Production: v56_trips_hybrid ($1,429 full / $794 prefix) + v44_dt
  ($1,081 full / $686 prefix). UNCHANGED for seventh consecutive session.
- Single-model ML feature-engineering track formally CLOSED (S72-S78
  six consecutive NULL ships).

USER DIRECTIVE (S78 end-of-session conversation — primary driver of S79):
- User rejected "ship at 65%" path; wants to find the 30+pp gap to 95%.
- User explicitly chose A-path (N=1000) over shipping.
- "Speed is not necessary — clarity and perfection is."
- The +$10 ship bar still holds for future ship decisions; S79 itself
  is measurement-only and does NOT attempt a ship.

DIRECTION FOR SESSION 79 — Label-noise measurement on existing N=1000
prefix grid; one-session A-path-vs-C-path decision:

  PHASE 1 (S79 ~30 min) — Write analysis/scripts/label_noise_measurement_S79.py.
    For each of the 500K prefix canonical hands:
      • v44_pick = strategy_v44_dt(hand)  (or load cached)
      • n200_pick = argmax of full_grid.evs[i] (N=200 labels)
      • n1000_pick = argmax of prefix_grid.evs[i] (N=1000 labels)
      • n200_match = (v44_pick == n200_pick)
      • n1000_match = (v44_pick == n1000_pick)
      • n200_regret_internal = full_evs[i][n200_pick] − full_evs[i][v44_pick]
      • n1000_regret_internal = prefix_evs[i][n1000_pick] − prefix_evs[i][v44_pick]
    The match-rate shift n1000_match − n200_match is the load-bearing
    metric; the regret deltas are descriptive.

  PHASE 2 (S79 ~15 min) — Aggregate breakdowns:
    • Overall: pct(n200_match), pct(n1000_match), shift.
    • By setting-rank bucket (S71 lens):
      - NOISE bucket (rank ≤3 of 105): expected to show largest shift
        if label noise is dominant.
      - MID bucket (rank 4-9).
      - STRUCTURE bucket (rank ≥10): should be most stable.
    • By hand category (pair, two_pair, trips, trips_pair, three_pair,
      quads, composite, high_only) per existing categorize_hands().
    • Save summary JSON: data/label_noise_S79_summary.json.

  PHASE 3 (S79 ~15 min) — Apply pre-committed decision criterion:
    If (n1000_match − n200_match) ≥ +5pp on prefix:
      A-PATH VERDICT — label noise is materially shifting "optimal."
      Phase 4 plans targeted N=1000 expansion.
    If (n1000_match − n200_match) < +2pp:
      C-PATH VERDICT — labels are stable; gap is real model error.
      Phase 4 plans high-capacity gradient boosting retry.
    If +2pp ≤ shift < +5pp:
      MIXED — document; surface options to user; do NOT pre-commit.

  PHASE 4 (S79 ~30 min) — Plan the next 3-5 sessions based on verdict:
    A-PATH plan options:
      (a) N=1000 on full-grid STRUCTURE-bucket hands only (~25.8% of grid
          ≈ 1.55M hands; estimate ~24 hr local compute).
      (b) Extend N=1000 prefix from 500K → 2M uniformly sampled hands.
      (c) Full N=1000 on 6M grid (~5 days local; may need cluster).
    C-PATH plan:
      Scope XGBoost retry at depth=10-12, n_est=1000-2000, longer
      early-stopping window. Smoke + full plan for S80.

  PHASE 5 (S79 ~10 min) — Decision 114; SESSION_79_LABEL_NOISE_REPORT.md;
  CURRENT_PHASE.md rewritten for S80 with the chosen path's concrete plan.

  ACCEPTANCE for Session 79:
  - label_noise_measurement_S79.py runs end-to-end; summary JSON written.
  - Match-rate shift computed and bucketed.
  - A-path or C-path declared per pre-committed criterion (or MIXED
    verdict with options presented).
  - Decision 114 documented.
  - CURRENT_PHASE.md rewritten for S80 with the chosen path's plan.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- v44_dt model + features remain unchanged.
- This session is MEASUREMENT, not ship. The +$10 ship bar does not
  apply; the question is "where does the 35pp gap live."
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; the measurement output and verdict should
  be summarized in plain language at the top of the session report.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
