# Current: Sprint 8 — Session 68 SHIPS v54 hybrid chain. **LARGEST SINGLE PRODUCTION SHIP IN PROJECT HISTORY: +$382/1000h full grid** (3× Rule 14's prior $131 record). Path B (cell-routed v44-on-PBOT + v53-elsewhere) captured the entire $382 WG matrix-predicted gap that S67's 12 catalog-blanket-rule candidates couldn't realize. Grader-confirmed v53 → v54: $2,490 → $2,108 full, $1,522 → $1,343 prefix; pct_opt 43.43% → 49.74% (+6.31pp). Within-pair $1,811 → $991 (-$820), 51.8% → 65.3% pct_opt (+13.5pp). All non-pair categories byte-identical (surgical via pair-PBOT gate). Two-track divergence v54 vs v44_dt: $1,409 → $1,027 (closed 27% in one ship). **Pair catalog is CLOSED**: v54 within $50 WG of v44-alone (= the matrix-predicted PMID-cell catch v54 preserves by routing PMID hands to v53). Combined with S65's high_only closure, the two largest residual categories (4M of 6M canonical hands = 67% of grid) are now both addressed. ML champion UNCHANGED at v44_dt.

> **🎯 IMMEDIATE NEXT ACTION (Session 69): two_pair audit (mirror S66-S67 methodology).**
>
>   With pair shipped and high_only catalog-closed, **two_pair is now the largest absolute residual target ($920 WG within v54)**. Apply the S66 Phase 1+2 + S67 candidate-sweep playbook:
>
>   **PHASE 1 (S69 ~3 hr)** — Two-pair decision matrix:
>   - Build `analysis/scripts/drill_two_pair_v44_S69.py` (mirror of `drill_pair_v44_S66.py`).
>   - Define two-pair-specific structural cell taxonomy (Layouts A/B/C × suit profiles × broken-pair states). The existing `t2p_v2_*` feature family in v44 hints at the natural axes.
>   - Sweep v44_dt vs oracle on all 1,338,480 two_pair canonical hands; output per-(max_pair_rank × low_pair_rank × cell) residuals.
>   - Phase 2: sweep v54 (= v52 + Rule 19; the rule chain handles two_pair the same as v52 → use v52 picks). Identify cells where v54→v44 gap is large.
>   - Output: `TWO_PAIR_DECISION_MATRIX.md` (the S66 analog).
>
>   **PHASE 2 (S69 last ~1 hr) or S70 if budget exhausts** — Candidate sweep + verdict:
>   - Reuse `test_rule_catalog_pair.py` pattern adapted for two_pair schema.
>   - Test ~5-10 candidates targeting the largest v54→v44 gap cells.
>   - Apply T1/T2/T3 thresholds.
>   - Likely outcomes (per S67's lesson):
>     1. Mostly ML-only at catalog granularity (likely if two_pair PBOT-routing is similarly selective).
>     2. Hybrid extension: if cells are clearly v44-favorable, extend v54 to route two_pair PBOT cells → v44 as well.
>
>   **Expected ship range:** v54→v55 (or no-ship if all-T3).
>     - If hybrid extension on two_pair PBOT cells: catalog ceiling ~$300-500 WG (= v52→v44 two_pair gap, which is $920 within-cat × 22.3% share / 1000 ≈ $205 WG). Realistic ship: $100-250 WG depending on cell selectivity.
>     - If purely catalog: $5-50 WG range (similar to S67's $9).
>
>   **3-PHASE PLAN (Session 69):**
>
>   **Phase 1a (S69 first ~1.5 hr)** — Phase 1 sweep on v44 vs oracle, building per-cell parquet.
>   **Phase 1b (S69 next ~1 hr)** — Phase 2 sweep on v54 baseline; produce decision matrix doc.
>   **Phase 2 (S69 last ~1.5 hr or S70)** — Candidate sweep + verdict + ship decision.
>
>   **ALTERNATIVE (lower priority):** **trips audit** ($110 WG residual, 6.6% of grid). Smaller absolute target but cleanest population. The trips category has the simplest structural axes (only 1 trip rank + 4 singletons; no pair-vs-no-pair confusion). Quick-win if S69's two_pair audit times out.
>
>   **SUCCESS CRITERIA (S69):**
>   - `drill_two_pair_v44_S69.py` produced + Phase 1 + Phase 2 sweeps complete.
>   - `TWO_PAIR_DECISION_MATRIX.md` produced (mirror of `PAIR_DECISION_MATRIX.md`).
>   - 3+ candidate verdicts assigned, OR ship decision on hybrid extension.
>   - S70 direction recommendation.

> **✅ ARTIFACTS produced in S68:**
> 1. **`SESSION_68_V54_HYBRID_CHAIN.md`** — full Phase 1-3 report, ship narrative, per-cell breakdown.
> 2. **`analysis/scripts/strategy_v54_pair_hybrid.py`** — **v54 PRODUCTION** (cell-routed hybrid).
> 3. **`analysis/scripts/validate_v54_routing_S68.py`** — pre-grader routing validation (predicted +$382.34 to 0.1% match).
> 4. **`analysis/scripts/grade_v54_pair_hybrid.py`** — head-to-head grader.
> 5. **`data/session68/`** — validation log + JSON + prefix + full grader outputs.
> 6. **`DECISIONS_LOG.md`** — Decision 103.
> 7. **`CURRENT_PHASE.md`** — rewritten for S69 (this file).
> 8. **`STRATEGY_GUIDE.md`** — Part 1 Session 68 append + front-matter update.

> **📓 METHODOLOGY (Session 69+):**
> - **The Path-B hybrid chain is now a validated production mechanism.** Future per-category audits should consider cell-routed hybrid as a first-class option alongside rule extension. The S67-S68 lesson: when blanket rules are T3-falsified but the matrix says headroom exists, the headroom is realizable via v44 cell-delegation, not via more rules.
> - **The catalog → matrix → audit → hybrid arc is a replicable methodology.** S66 (matrix) → S67 (candidate falsification) → S68 (hybrid ship) took 3 sessions and produced the largest ship in project history. The arc fits all subsequent per-category audits (two_pair, trips, three_pair).
> - **Harness-to-grader fidelity is excellent at the routing level.** v54's harness predicted +$382.34; grader returned +$382. 0.1% error. This means future hybrid-extension proposals can be cleanly pre-validated via the catalog harness BEFORE committing to a multi-hour grader run.
> - **"Speed is not necessary — clarity and perfection is."** S68 took ~4 hours including harness validation, prefix grader, full grader, and complete documentation. The end-to-end matrix → ship arc was 3 sessions (S66+S67+S68).

> Updated: 2026-05-12 (Session 68 end — v54 ships +$382/1000h; pair catalog CLOSED; S69 pivots to two_pair audit)

---

## Headline state at end of Session 68

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v54_pair_hybrid** | **PRODUCTION rule chain** (cell-routed: v44 on pair PBOT cells; v53 elsewhere). **$2,108 full / $1,343 prefix** (grader-confirmed). | `analysis/scripts/strategy_v54_pair_hybrid.py` |
| **v44_dt** | **PRODUCTION ML champion** (UNCHANGED; now also used inside v54 for pair PBOT cells). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: $1,409 → $1,027 (closed 27% in S68). v54 within $50 WG of v44-alone on pair (preserved by routing PMID hands to v53).

**Per-category residuals (v54 framing):**

| Category | n_hands | v54 within-cat | v54 WG | v44 WG | Status |
|---|---:|---:|---:|---:|---|
| high_only | 1,226,940 | $3,014 | $755 | $755 | ML-only, CLOSED S65 |
| **pair** | 2,800,512 | **$991** | **$462** | $511 | **HYBRID v54-PBOT-v44 + v54-PMID-v53. Within $50 of v44. CLOSED S68.** |
| two_pair | 1,338,480 | $3,211 | $920 | $363 | **S69 target — largest remaining absolute residual** |
| trips | 328,185 | $2,010 | $110 | $54 | S70+ target |
| trips_pair | 171,600 | $5,417 | $155 | $5 | Already collapsed S55a |
| three_pair | 114,400 | $1,696 | $32 | $35 | Small target |
| quads + composite | 29,042 | (rounding) | <$5 | <$5 | Negligible |

**Project ship records (after S68):**

| Ship | Lift WG | Session | Type |
|---|---:|---|---|
| **v54 hybrid** | **+$382** | **S68** | **Hybrid chain (NEW RECORD)** |
| v39_dt ML retrain | +$237 | S54 | ML champion |
| Rule 14 (A-high HIMID) | +$131 | S50 | Rule chain |
| Rule 6 (Q4) | +$113 | S37 | Rule chain |
| Rule 15 (K-high HIMID) | +$51 | S51 | Rule chain |
| Rule 12 (J-low two_pair DS) | +$35 | S47 | Rule chain |
| v54 hybrid (prefix) | +$179 | S68 | Hybrid chain |

---

## Resume Prompt (Session 69 — two_pair audit)

```
Resume Session 69 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S68 — two_pair audit mandated)
- SESSION_68_V54_HYBRID_CHAIN.md (v54 hybrid ship report)
- PAIR_DECISION_MATRIX.md (S66 — methodology template)
- DECISIONS_LOG.md (latest: Decision 103 — v54 ships +$382 hybrid chain)
- analysis/scripts/drill_pair_v44_S66.py (Phase 1 sweep template)
- analysis/scripts/sweep_v52_on_pair_S66.py (Phase 2 sweep template)
- analysis/scripts/strategy_v54_pair_hybrid.py (current production)

State (end of Session 68):
- v54 ships hybrid chain at +$382/1000h full grid grader-confirmed.
  LARGEST SINGLE PRODUCTION SHIP IN PROJECT HISTORY.
- Pair catalog CLOSED (v54 within $50 WG of v44-alone).
- High_only catalog CLOSED (S65, ML-only).
- Remaining residuals: two_pair $920 WG, trips $110, three_pair $32.
- Two-track divergence v54 vs v44_dt: $1,027/1000h.

USER DIRECTIVE (S59-S68 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 69 — two_pair audit:

  PHASE 1a (S69 ~1.5 hr) — Phase 1 sweep:
  - Build `analysis/scripts/drill_two_pair_v44_S69.py` mirroring
    drill_pair_v44_S66.py for two_pair schema.
  - Two_pair cell taxonomy: Layouts A/B/C × DS-bot achievability ×
    broken-pair states. Inspect v44's existing t2p_v2_* features for
    natural axes.
  - Sweep v44 vs oracle on all 1,338,480 two_pair canonical hands.
  - Output: per-hand parquet + summary JSON.

  PHASE 1b (S69 ~1 hr) — Phase 2 sweep + matrix doc:
  - Sweep v54 baseline on same hands (v54 on two_pair = v53 since the
    pair-PBOT gate excludes two_pair).
  - Compute per-cell v54→v44 gap; identify catalog-shippable cells.
  - Produce `TWO_PAIR_DECISION_MATRIX.md` (mirror of pair matrix).

  PHASE 2 (S69 last ~1.5 hr or S70) — Candidate sweep + verdict:
  - Test ~5-10 candidates per T1/T2/T3 thresholds.
  - If hybrid-extension on two_pair PBOT cells is favorable: build
    strategy_v55_two_pair_hybrid.py and grade.
  - Else: ship the largest catalog candidate that clears T2.

ACCEPTANCE for Session 69:
- TWO_PAIR_DECISION_MATRIX.md produced.
- 3+ candidate verdicts assigned OR hybrid-extension ship decision.
- S70 direction recommendation.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- The pair Phase 1/2 sweep scripts are the methodology template;
  adapt the cell taxonomy for two_pair's Layout A/B/C structure.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
