# Current: Sprint 8 — Session 78 v48_dt H6+H7+H8 pair feature pack CLEAN NULL ships at prefix grade (Δ +$2/1000h; within-pair +$5/1000h); structural-redundancy doctrine empirically reconfirmed; single-model ML feature-engineering track formally CLOSED at v44 saturating regime; S79 pivots to Option D rule-chain extension on S77 LOW pair findings

S77 queued three pair-gated feature hypotheses (H6/H7/H8) for v48_dt retrain at the S73 regime (depth=36, ml=1). S78 executed Phase 1-5 as planned. Phase 1 implemented and sanity-tested H6 (`pair_pmid_ds_n_configs_g`, int8 0..5 — though actual reachable values are {0,1,3}), H7 (`pair_kicker_max_in_pair_suit_g`, bool 0/1), H8 (`pair_low_pmid_safety_g`, int8 0..5, LOW-pair-only). H8's inline cell logic cross-validated against S66's `compute_pair_structural` + `cell_for_pair_hand` on 23,377 random single-pair canonical hands with zero disagreements.

Phase 2 persisted all three gated parquet packs (~18.6 MB each) with verified zero-on-non-gated. Phase 3 smoke train (100K rows, 2.5s wall) placed H7 #51 / H8 #69 / H6 #73 — all below the top-30 ideal but above the rank-80 abort gate. Phase 4 full train (4.8M rows, 578s wall, 2.29M leaves, 1,285 MB) improved placements to H7 #43 / H8 #57 / H6 #68.

**Phase 5 prefix grade returned Δ +$2/1000h (v44 $686 → v48 $684).** Within-pair lift was +$5/1000h ($595→$590) on 215,162 prefix pair hands. All other categories byte-identical (gating works correctly; new features touch only pair hands as designed). Per S78 directive (`prefix Δ < +$5 → NULL ship`), Phase 6 (full grade) was SKIPPED.

**Production state UNCHANGED for the seventh consecutive session** (S72 NULL, S73 PARTIAL/NULL, S74 NULL, S75 boosting NULL, S76 diagnostic, S77 diagnostic, S78 NULL).

**Why the predicted lift didn't land — structural-redundancy NULL reconfirmed:** S77 budgeted 50% redundancy across H6+H7+H8 and predicted $30-45/1000h within-pair joint lift. Observed is ~$5 within-pair = effective 85-90% redundancy. Three contributors: H6 only emits {0,1,3} (deck structure caps partitioning surface at ~3 bits); H7's 1-bit signal is derivable in 2 splits from existing v44 features; H8's 5-split cell synthesis is reachable in 3-4 splits at v44's 2.25M-leaf capacity. The S74 redundancy doctrine — features derivable in <few splits at saturation get zero or near-zero lift — is empirically reconfirmed. S77's cleanest-diagnostic-in-the-project hypothesis methodology does NOT break the redundancy ceiling.

**Decision 112 (S77): pair drill diagnostic ship. Decision 113 (S78): v48_dt CLEAN NULL ship; single-model ML feature-engineering track formally CLOSED at v44 regime.**

> **🎯 IMMEDIATE NEXT ACTION (Session 79): Option D rule-chain extension on S77 LOW pair findings, OR pivot to next-residual-category cross-product diagnostic**
>
> The S77 drill surfaced a clean 1-bit signal (kicker_max-in-pair-suit: 70% TRUE in LOW × PBOT_DS_PARTIAL vs 32-34% TRUE in LOW × PMID-target cells) that the v48_dt absorbed without producing ship-grade lift. **The redundancy ceiling does NOT apply at the rule layer** — the v54+v55+v56 hybrid stack routes through v44_dt only on specific category gates, and a surgical rule applied on top of those gates operates outside the DT's saturation regime. The S77 single-largest-mismatch class (`SPLIT_tmax_SS_mu → PMID_tmax_DS` in LOW × PMID_DS_MAXTOP, n=3,072 hands, $10.97/1000h on ONE class) is a candidate Option D target.
>
> 1. **(PHASE 1 — ~30 min)** Read S77 drill outputs (`data/drill_v44_pair_S77_summary.json`) and S77 hypotheses doc. Re-confirm the kicker_max-in-pair-suit discriminator and the SPLIT→PMID mismatch class fingerprint.
>
> 2. **(PHASE 2 — ~45 min)** Design a Rule 19 candidate targeting LOW × PMID_DS_MAXTOP with the kicker_max-in-pair-suit discriminator:
>    - Trigger: single-pair AND pair_rank ∈ {2,3,4,5,6,7} AND kicker_max NOT in pair_suits AND PMID_DS_w_maxtop achievable (n_PMID_DS_w_maxtop ≥ 1).
>    - Action: Force PMID_tmax_DS routing (pair in mid, top = max_sing, bot = 4 non-max singletons in 2+2 pattern).
>    - Acceptance: Rule applies to ~6,760 LOW × PMID_DS_MAXTOP STR hands × ~$22/1000h within-cell residual ≈ $15-22 WG if it captures the cell cleanly. Full-grid ≈ $5-8 — borderline for ship bar.
>
> 3. **(PHASE 3 — ~15 min)** Grader-confirm vs v56_trips_hybrid baseline. Apply +$10/1000h ship bar.
>    - Δ ≥ +$10 → SHIP v57; advance rule chain. 19th rule in project.
>    - Δ ∈ [+$5, +$10) → PARTIAL POSITIVE / NULL ship at bar per S73 codification.
>    - Δ < +$5 → CLEAN NULL ship; document; consider tighter-gated variant.
>
> 4. **(PHASE 4 — ~20 min)** If Rule 19 NULLs: pivot to next-residual cross-product diagnostic. Two_pair STRUCTURE-bucket WG ($66/1000h S76) and trips STRUCTURE-bucket WG ($21/1000h S76) haven't been probed with the S71-bucket × cell-decomposition product lens. Generate `drill_v44_two_pair_S79.py` mirroring S77's structure on two_pair.
>
> 5. **(PHASE 5 — ~10 min)** Decision 114 + SESSION_79_*_REPORT.md + CURRENT_PHASE.md rewrite for S80.
>
> ACCEPTANCE for Session 79:
> - EITHER Rule 19 candidate trained, graded, ship decision made
> - OR fresh diagnostic ship (e.g., two_pair S79 drill) with quantified hypothesis pack for S80
> - DECISIONS_LOG.md updated with Decision 114
> - CURRENT_PHASE.md rewritten for S80
>
> **📓 METHODOLOGY (Session 79+):**
>
> 1. **Redundancy ceiling escape — RULE LAYER, not feature layer.** S78 closed the single-model ML feature-engineering track. The path forward for residual-leak closure is the rule layer (v54+v55+v56 hybrid stack), where surgical category-gated rules apply BEFORE v44_dt routes the residual. Rules operate outside saturation.
>
> 2. **Decision 113 redundancy lesson — assume 80%+ default budget.** Any future feature-engineering hypothesis at v44 saturating regime should assume 80%+ redundancy until proven otherwise via empirical pre-flight (smoke train + per-category mini-grade, not just rank-importance check).
>
> 3. **Diagnostic precision is necessary but NOT sufficient.** S77 produced the project's cleanest diagnostic (sharp gap_2nd, single dominant mismatch class, structurally distinct signal); the features built from it captured 1/10 of predicted lift. **Stop equating diagnostic precision with feature lift.** They are orthogonal at saturation.
>
> 4. **Empirical value-distribution pre-flight.** H6's planned 0..5 reduces to {0,1,3} due to deck structure. A 5-minute simulation against canonical hands would have caught this. Future feature specs should include this check.
>
> 5. **Smoke + per-category mini-grade BEFORE full train.** Smoke train's rank-<80 abort gate is insufficient — v48's features all cleared smoke but yielded $2/1000h overall. Add a 5K-hand category-targeted prefix mini-grade to the smoke phase to detect feature-lift materialization (vs feature usage) before committing to the 10-30 min full train.
>
> 6. **+$10 ship bar canonical (S73 codified, held S74-S78).** Eight consecutive sessions UNCHANGED production state. The bar continues to filter noise from signal as designed.
>
> 7. **"Speed is not necessary — clarity and perfection is."** S78 executed Phases 1-5 cleanly with no short-cuts and produced an unambiguous NULL with full documentation of WHY. S79 should match this discipline.

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

> Updated: 2026-05-13 (Session 78 end — v48_dt H6+H7+H8 pair feature pack CLEAN NULL ship at prefix grade Δ +$2/1000h; within-pair +$5/1000h on 215K hands; structural-redundancy doctrine reconfirmed at v44 saturating regime; single-model ML feature-engineering track formally closed; production state UNCHANGED for the seventh consecutive session; S79 pivots to Option D rule-chain extension on S77 LOW pair kicker_max-in-pair-suit discriminator, OR fresh two_pair / trips cross-product diagnostic)

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
| Option A | Oracle-label N=1000 re-eval | GATED on cluster access. |
| Option C | Higher-capacity boosting | Deprioritized — 15-25 hr speculative. |
| **Option D (S79)** | Rule-chain extension on S77 LOW pair kicker_max discriminator | **PRIORITIZED for S79.** |

**Cascade verdict (updated):** Single-model ML feature-engineering track CLOSED at v44 regime. S79 pivots to either Option D (rule-chain extension — operates outside saturation) or a fresh cross-product diagnostic on the next-largest residual category.

---

## Resume Prompt (Session 79 — Option D rule extension OR fresh diagnostic)

```
Resume Session 79 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S78 — Option D rule-chain extension
  on S77 LOW pair findings, OR fresh two_pair/trips cross-product
  diagnostic)
- SESSION_78_V48_DT_REPORT.md (Phase 1-5 details for the CLEAN NULL ship)
- DECISIONS_LOG.md (latest: Decision 113 — S78 v48 NULL + ML
  feature-engineering track CLOSED)
- PAIR_S77_FEATURE_HYPOTHESES.md (re-read for the LOW × PMID_DS_MAXTOP
  cell fingerprint and the SPLIT_tmax_SS_mu → PMID_tmax_DS class)
- data/drill_v44_pair_S77_summary.json (per-cell × per-bucket WG and
  mismatch class data)
- analysis/scripts/strategy_v56_trips_hybrid.py (production rule chain;
  any Rule 19 extension wires in here)
- analysis/scripts/drill_v44_pair_S77.py (S77 drill — template for any
  S79 two_pair/trips analog if Option D NULLs)

State (end of S78):
- v48_dt CLEAN NULL ship at prefix grade Δ +$2/1000h. Single-model ML
  feature-engineering track formally CLOSED at v44 saturating regime.
- Within-pair lift was +$5/1000h ($595 → $590) on 215K prefix pair
  hands. All other categories byte-identical (gating correct).
- v48_dt model saved at data/v48_dt_model.npz (1,285 MB) — kept for
  audit only; production UNCHANGED.
- Production: v56_trips_hybrid ($1,429 full / $794 prefix) + v44_dt
  ($1,081 full / $686 prefix). Two-track divergence $348/1000h.
- Seventh consecutive session with production state UNCHANGED.

USER DIRECTIVE (S59-S78 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship threshold canonical (codified S73, held S74-S78).

DIRECTION FOR SESSION 79 — Option D rule-chain extension OR fresh diagnostic:

  PHASE 1 (S79 ~30 min) — Re-read S77 drill outputs; confirm the
  kicker_max-in-pair-suit discriminator (70% TRUE in LOW × PBOT_DS_PARTIAL
  vs 32-34% in LOW × PMID-target cells) and the SPLIT_tmax_SS_mu →
  PMID_tmax_DS mismatch class (n=3,072 hands, $10.97/1000h on one class
  out of pair's $116 STR total).

  PHASE 2 (S79 ~45 min) — Design Rule 19 candidate:
    - Trigger: single-pair AND pair_rank ∈ {2,3,4,5,6,7} AND
      kicker_max NOT in pair_suits AND n_PMID_DS_w_maxtop ≥ 1.
    - Action: Force PMID_tmax_DS routing.
    - Expected: ~6,760 LOW × PMID_DS_MAXTOP STR hands × ~$22 within-cell
      residual ≈ $15-22 WG if rule captures cell cleanly. Full-grid
      ≈ $5-8 — borderline at ship bar.

  PHASE 3 (S79 ~15 min) — Grader-confirm v57 (rule 19 + v56) vs
  v56_trips_hybrid baseline.
    Δ ≥ +$10 → SHIP v57 (rule 19); 19th rule in project.
    Δ ∈ [+$5, +$10) → PARTIAL POSITIVE / NULL ship at +$10 bar.
    Δ < +$5 → CLEAN NULL ship.

  PHASE 4 (S79 ~20 min) — If Rule 19 NULLs: pivot to fresh diagnostic.
    Two_pair STRUCTURE WG ($66/1000h S76) and trips STRUCTURE WG
    ($21/1000h S76) haven't been probed with S71-bucket × cell lens.
    Generate drill_v44_two_pair_S79.py mirroring S77's structure.

  PHASE 5 (S79 ~10 min) — Decision 114; SESSION_79_*_REPORT.md;
  CURRENT_PHASE.md rewritten for S80.

  ACCEPTANCE for Session 79:
  - EITHER Rule 19 trained, graded, ship decision made
  - OR fresh diagnostic ship with quantified hypothesis pack for S80
  - Decision 114 documented in DECISIONS_LOG.md
  - CURRENT_PHASE.md rewritten for S80

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- v44_dt model + features remain unchanged; v48 retained for audit only.
- "Speed is not necessary — clarity and perfection is."
- Option D operates at the rule layer (outside DT saturation) — the
  redundancy ceiling that NULLed H6/H7/H8 does NOT apply here. Rules
  apply BEFORE v44_dt routes the residual.
- If Rule 19 NULLs, the diagnostic pivot (two_pair / trips
  cross-product) is the second-priority path; the third is Option A
  (oracle-label N=1000 re-eval, gated on cluster access).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
