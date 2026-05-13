# Current: Sprint 8 — Session 70 SHIPS v56 trips hybrid (+$45/1000h full grid). Third consecutive Path-B hybrid ship; **closes trips category at v44 limits**. Cumulative S68+S69+S70 = $1,061/1000h (75% of pre-S68 two-track divergence). The largest 4 residual categories (high_only, pair, two_pair, trips = 94.7% of canonical grid) are now ALL closed at the limits achievable by current rule chain + v44_dt ML champion. **Architectural-routing headroom is largely exhausted; S71+ pivots to ML retrain (v45_dt+) — any v44 improvement now compounds 4× via v54+v55+v56.** Grader-confirmed v55 → v56: $1,473 → $1,429 full, $827 → $794 prefix; pct_opt 58.44% → 59.51% (+1.07pp). Within-trips $2,010 → $1,194 (-$816), 39.0% → 58.6% pct_opt (+19.6pp). All non-trips categories byte-identical (surgical via trips-blanket gate). Three-gate hybrid chain (pair-PBOT in v54 + two_pair in v55 + trips in v56) is now the project's cleanest architecture; structurally disjoint, zero conflict. Harness predicted +$44.61 WG; grader $+45; fidelity 0.87%.

> **🎯 IMMEDIATE NEXT ACTION (Session 71): ML retrain (v45_dt+) — high_only diagnostic-driven feature engineering.**
>
>   With high_only, pair, two_pair, and trips all CLOSED at v44 limits, the remaining structural-rule headroom is exhausted. The two-track divergence remaining ($348/1000h) is concentrated in:
>     - **trips_pair** ($155 WG, 2.9% of grid) — already collapsed S55a; minimal headroom.
>     - **three_pair** ($32 WG, 1.9% of grid) — smallest meaningful target.
>     - **v44's own residuals** — the ML champion still leaks $1,081/1000h full-grid; reducing this via retrain SHIFTS THE WHOLE HYBRID CHAIN downward.
>
>   The largest single-category v44 residual is **high_only at $3,014/1000h = $755 WG** (12.6% of grid). A v45_dt that reduces high_only by even 20% would ship ~$151 WG full-grid via the v54+v55+v56 chain — comparable to the early rule-era's biggest ships (Rule 6 +$113, Rule 14 +$131).
>
>   **PATH A (recommended) — high_only ML retrain (v45_dt)**: Diagnostic-driven feature engineering per S54 playbook. Mine v44's high_only mismatches; identify systematic miss patterns; build 4-8 new gated features; retrain DT at depth=32 ml=3 (project default); validate via grader. Expected ship: $50-200 WG full-grid (depending on how much high_only residual can be closed). Higher-effort path than Path-B hybrids (~2-3 sessions of compute + iteration), but the only meaningful remaining lift lever.
>
>   **PATH B (alternative) — three_pair / trips_pair audit**: Apply S69+S70 methodology to the remaining small categories. Expected ship: <$10 WG full-grid each. Quick (~1 session) but tiny lift.
>
>   **Recommended:** PATH A (v45_dt high_only retrain) for S71+. Higher-effort but the only direction with meaningful headroom.
>
>   **3-PHASE PLAN (Session 71 — ML retrain prep):**
>
>   **Phase 1a (S71 first ~1.5 hr)** — Diagnostic sweep: build `drill_v44_high_only_S71.py` mirroring S54-era diagnostic harnesses; mine v44's high_only mismatches at hand-level granularity; identify systematic structural patterns (per S54 playbook). Output: per-hand parquet + diagnostic report.
>   **Phase 1b (S71 ~1 hr)** — Hypothesis-list: from Phase 1a output, propose 4-8 candidate features targeting the largest mismatch classes. Document in `SESSION_71_V45_FEATURE_HYPOTHESES.md`.
>   **Phase 2 (S71 last ~1 hr)** — Implement 1-2 features as `*_aug_v3_features_gated.py`; smoke-test in isolation; queue full retrain for S72.
>
>   **SUCCESS CRITERIA (S71):**
>   - `drill_v44_high_only_S71.py` produced + diagnostic sweep complete.
>   - `SESSION_71_V45_FEATURE_HYPOTHESES.md` with 4-8 feature proposals.
>   - 1-2 features implemented + smoke-tested.
>   - S72 direction (full retrain) recommendation.

> **✅ ARTIFACTS produced in S70:**
> 1. **`SESSION_70_V56_TRIPS_HYBRID.md`** — full Phase 1-5 report, ship narrative, per-cell breakdown.
> 2. **`TRIPS_DECISION_MATRIX.md`** — Phase 1+2 matrix doc (analog of TWO_PAIR_DECISION_MATRIX.md).
> 3. **`analysis/scripts/strategy_v56_trips_hybrid.py`** — **v56 PRODUCTION** (blanket trips → v44 hybrid).
> 4. **`analysis/scripts/drill_trips_v44_S70.py`** — Phase 1 sweep (mirror of drill_two_pair_v44_S69.py).
> 5. **`analysis/scripts/sweep_v55_on_trips_S70.py`** — Phase 2 sweep (mirror of sweep_v54_on_two_pair_S69.py).
> 6. **`analysis/scripts/test_trips_catalog_candidates_S70.py`** — bundled candidate harness + 3-candidate verdict sweep.
> 7. **`analysis/scripts/validate_v56_routing_S70.py`** — pre-grader validation reusing existing parquet (predicted +$44.61 to 0.87% match).
> 8. **`analysis/scripts/grade_v56_trips_hybrid.py`** — head-to-head grader.
> 9. **`data/session70/`** — all phase logs + JSON summaries.
> 10. **`DECISIONS_LOG.md`** — Decision 105.
> 11. **`CURRENT_PHASE.md`** — rewritten for S71 (this file).
> 12. **`STRATEGY_GUIDE.md`** — Part 1 Session 70 append + front-matter update.

> **📓 METHODOLOGY (Session 71+):**
> - **The Path-B hybrid arc generalizes to small categories.** S68 (pair +$382) → S69 (two_pair +$634) → S70 (trips +$45). Cumulative $1,061/1000h. Trips's smaller absolute ship reflects smaller category share (5.5% of grid) AND smaller within-cat v55→v44 gap ($44 WG vs $634 for two_pair), not diminishing methodology returns.
> - **Methodology arcs compress to ~1 session per category once templates are in place.** S68 took 1 session (after pair-matrix S66+S67); S69 took 1 session (reusing S66+S68 templates); S70 took 1 session (reusing S66+S68+S69 templates). The structural-cell taxonomy and pre-grader validation harness now apply universally.
> - **Catalog candidates can be even MORE dominated than S69's pattern.** S69 found 3/5 cleared T2 vs baseline but all lose vs v44. S70 found 0/4 cleared even T1 vs baseline. The catalog-vs-hybrid dominance gap WIDENS as v44 gets more selective in smaller categories.
> - **Three-gate hybrid chain is the project's cleanest architecture.** pair-PBOT (v54) + two_pair (v55) + trips (v56) are structurally disjoint at the rank-count signature level. Zero conflict; surgical category routing. ~40% of canonical grid now routes through v44_dt.
> - **The architectural-routing headroom is largely exhausted.** Remaining catalog targets (trips_pair, three_pair) are small absolute ships (<$10 WG each predicted). **S71+ MUST pivot to ML retrain (v45_dt+) for meaningful lift.** Any v44 improvement now compounds 4× via the hybrid chain.
> - **"Speed is not necessary — clarity and perfection is."** S70 took ~3 hours including all phases (matrix, candidates, hybrid, two graders, full documentation). Trips's smaller scope let the methodology compress to a fast, clean ship.

> Updated: 2026-05-12 (Session 70 end — v56 ships +$45/1000h; trips catalog CLOSED; S71+ pivots to ML retrain v45_dt+)

---

## Headline state at end of Session 70

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | **PRODUCTION rule chain** (blanket trips → v44_dt; else → v55). **$1,429 full / $794 prefix** (grader-confirmed). | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | **PRODUCTION ML champion** (UNCHANGED; now invoked inside v56 for trips, inside v55 for two_pair, inside v54 for pair PBOT cells). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: $393 → **$348** (closed 11% in S70). Cumulative S68+S69+S70: $1,061/1000h (75% of original $1,409).

**Per-category residuals (v56 framing):**

| Category | n_hands | v56 within-cat | v56 WG | v44 WG | Status |
|---|---:|---:|---:|---:|---|
| high_only | 1,226,940 | $3,014 | $755 | $755 | ML-only, CLOSED S65 |
| pair | 2,800,512 | $991 | $462 | $511 | Hybrid v54-PBOT-v44 + v54-PMID-v53. CLOSED S68. |
| two_pair | 1,338,480 | $363 | $80.82 | $80.82 | Hybrid v55-blanket-v44. CLOSED S69 (= v44). |
| **trips** | 328,185 | **$1,194** | **$65.18** | **$65.18** | **Hybrid v56-blanket-v44. CLOSED S70 (= v44).** |
| trips_pair | 171,600 | $5,417 | $155 | $5 | Already collapsed S55a (small remaining target) |
| three_pair | 114,400 | $1,696 | $32 | $35 | Small target |
| quads + composite | 29,042 | (rounding) | <$5 | <$5 | Negligible |

**Project ship records (after S70):**

| Ship | Lift WG | Session | Type |
|---|---:|---|---|
| v55 two_pair hybrid | +$634 | S69 | Hybrid chain (largest single ship) |
| v54 pair hybrid | +$382 | S68 | Hybrid chain |
| v39_dt ML retrain | +$237 | S54 | ML champion |
| Rule 14 (A-high HIMID) | +$131 | S50 | Rule chain |
| Rule 6 (Q4) | +$113 | S37 | Rule chain |
| Rule 15 (K-high HIMID) | +$51 | S51 | Rule chain |
| **v56 trips hybrid** | **+$45** | **S70** | **Hybrid chain (closes trips category)** |
| Rule 12 (J-low two_pair DS) | +$35 | S47 | Rule chain |
| v55 hybrid (prefix) | +$516 | S69 | Hybrid chain (prefix) |
| v54 hybrid (prefix) | +$179 | S68 | Hybrid chain (prefix) |

---

## Resume Prompt (Session 71 — ML retrain pivot)

```
Resume Session 71 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S70 — ML retrain pivot mandated)
- SESSION_70_V56_TRIPS_HYBRID.md (v56 trips hybrid ship report)
- TRIPS_DECISION_MATRIX.md (S70 — methodology template, now applied 3 times)
- DECISIONS_LOG.md (latest: Decision 105 — v56 ships +$45 hybrid chain;
  trips closed)
- analysis/scripts/strategy_v56_trips_hybrid.py (current production)
- SESSION_54_V39_DT_REPORT.md (last ML retrain playbook — read carefully)

State (end of Session 70):
- v56 ships hybrid chain at +$45/1000h full grid grader-confirmed.
  Third consecutive Path-B hybrid ship; closes trips category.
- Cumulative S68+S69+S70 = $1,061/1000h closed (75% of pre-S68
  divergence).
- FOUR largest residual categories now ALL closed at v44 limits:
  high_only (S65), pair (S68), two_pair (S69), trips (S70).
- Remaining residuals: trips_pair $155, three_pair $32 (small),
  composite + quads negligible.
- Two-track divergence v56 vs v44_dt: $348/1000h.
- **Architectural-routing headroom is largely exhausted.**

USER DIRECTIVE (S59-S70 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 71 — ML retrain (v45_dt+) PIVOT:

  PATH A (recommended) — v45_dt high_only retrain (diagnostic-driven):

    PHASE 1a (S71 ~1.5 hr) — Diagnostic sweep:
    - Build `analysis/scripts/drill_v44_high_only_S71.py` mirroring
      S54-era diagnostic harnesses. Mine v44's high_only mismatches at
      hand-level granularity; identify systematic structural patterns
      (per S54 playbook).
    - High_only is currently v44's largest single-category residual:
      $3,014/1000h within-cat = $755 WG (12.6% of grid).
    - Output: per-hand parquet + diagnostic report.

    PHASE 1b (S71 ~1 hr) — Hypothesis-list:
    - From Phase 1a output, propose 4-8 candidate features targeting
      the largest mismatch classes.
    - Document in `SESSION_71_V45_FEATURE_HYPOTHESES.md`.

    PHASE 2 (S71 last ~1 hr) — Implement + smoke-test:
    - Implement 1-2 features as `ho_aug_v3_features_gated.py` (next
      version in the gated-feature family).
    - Smoke-test against handful of hands; queue full retrain for S72.

  PATH B (alternative) — three_pair / trips_pair audit:
    - Apply S69+S70 methodology to remaining small categories.
    - Expected ship: <$10 WG full-grid each.
    - Quick (~1 session) but tiny lift; NOT recommended given Path A
      headroom is much larger.

ACCEPTANCE for Session 71:
- drill_v44_high_only_S71.py + diagnostic sweep complete.
- SESSION_71_V45_FEATURE_HYPOTHESES.md with 4-8 feature proposals.
- 1-2 features implemented + smoke-tested.
- S72 direction (full retrain) recommendation.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- The S54 diagnostic playbook is the template for Phase 1a — re-read
  SESSION_54_V39_DT_REPORT.md before building drill scripts.
- ML retrain hyperparams default: depth=32 ml=3 (verified S36+S58).
- Re-test depth=34 ml=2 when feature count grows ≥10 above last sweep.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
