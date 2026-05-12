# Current: Sprint 8 — Session 67 candidate sweep on pair PBOT cells. **12 candidates tested; 11 T3 net-negative. Only one ships clean: Rule 19 (Q-pair × PBOT_DS_JOINT) at +$8.50/1000h WG.** v53 = v52 + Rule 19 (**grader-confirmed +$9/1000h full grid**; $2,498 → $2,490). **Strategy of record ADVANCES to v53** (first rule chain ship since v52 in S53; ~6 months wall-clock). PAIR_DECISION_MATRIX.md's "$391 WG catalog-shippable PBOT-cell headroom" claim is **decisively falsified** for blanket-rule realization — only $8.50/1000h is actually catalog-shippable; the remaining $341 WG headroom is v44's *selective* catch, mirroring high_only's S60-S64 ML-only outcome. **Pair PBOT-routing is mostly ML-only at catalog granularity.** ML champion UNCHANGED at v44_dt.

> **🎯 IMMEDIATE NEXT ACTION (Session 68): Path B (hybrid chain) experiment — cell-routed v52-PMID + v44-PBOT routing.**
>
>   Per `PAIR_DECISION_MATRIX.md` Recommendation Path B (validated by S67's catalog-falsification result):
>
>   - **Hybrid design:** route pair hands through v52 when cell ∈ PMID_*; route through v44_dt when cell ∈ PBOT_* (PBOT_DS_JOINT + PBOT_DS_PARTIAL).
>   - **Expected lift on pair category:** v44 PBOT $215 WG + v52 PMID $246 WG = $462 WG total residual. vs v52-alone $852: **+$390 WG**. vs v44-alone $511: **+$49 WG**.
>   - **Implementational cost:** the structural cell taxonomy is pre-computed in `data/drill_pair_v44_per_hand_structural.parquet` (Phase 1 artifact). Cell tagging can be vectorized at inference time using `_enumerate_pbot_ds` (S67 artifact).
>   - **Trade-off:** v53 production state COMMITS to v44_dt on PBOT pair cells. ML champion retraining could shift this gate's optimum.
>
>   **3-PHASE PLAN (Session 68):**
>
>   **Phase 1 (S68 first ~1 hr)** — Build hybrid strategy file `strategy_v54_pair_hybrid.py`:
>   - Detect pair hand + compute cell tag at inference
>   - Route to v44_dt on PBOT cells, v52 on PMID cells (+ all non-pair categories)
>   - Verify with smoke tests + harness
>
>   **Phase 2 (S68 next ~2 hr)** — Grade v54 vs v53 head-to-head on full + prefix grids:
>   - Expected full-grid: v54 ≈ $2,100 (= v52 $2,498 − $390 hybrid lift) — would be the LARGEST single-rule-ish lift since v45→v46 (Rule 14, +$131).
>   - Verify per-cell behavior with `sweep_v54_on_pair_S68.py` (mirror sweep_v52_on_pair_S66.py).
>
>   **Phase 3 (S68 ~30 min)** — Decision:
>   - If v54 ships clean (+$200+ WG): v54 is the new production rule chain. S69 audits trips ($55), two_pair ($52), three_pair ($35) for additional hybrid candidates.
>   - If v54 underperforms (likely cause: oracle picks PBOT 50%+ in cells where the rule-chain v52 also picks PBOT, so the hybrid's PBOT-cell gain is offset by PMID-cell loss): pivot to Path A C_PAIR_4 (broaden v9_2's gate by dropping the Ace predicate; tested for ship via the S67 harness).
>
>   **ALTERNATIVE (lower priority): C_PAIR_4 — Drop "single Ace" predicate from v9_2.** Currently v9_2 fires only when pair_rank ∈ {2-5, T-J-Q} AND an Ace is present. Removing the Ace predicate broadens v9_2's fire region 3×. Estimated $30-50 WG ceiling per PAIR_DECISION_MATRIX.md. **BUT:** the Ace predicate likely encodes a "trust the DS-bot when PMID-mid is strong enough" signal, and removing it may regress (same C_PAIR_3 selectivity problem). Reasonable to test in S68 as the Path A fallback if hybrid underperforms.
>
>   **SUCCESS CRITERIA (S68):**
>   - `strategy_v54_pair_hybrid.py` produced + smoke tests pass.
>   - v54 full-grid grader confirms positive lift vs v53.
>   - If v54 ≥ +$100 WG: SHIPS. If +$5-100 WG: catalog-worthy ship. If T3: pivot to C_PAIR_4 or new direction.

> **✅ ARTIFACTS produced in S67:**
> 1. **`SESSION_67_C_PAIR_3_AUDIT.md`** — pair Phase 3 candidate sweep + verdict.
> 2. **`analysis/scripts/test_rule_catalog_pair.py`** — pair catalog harness (mirror of `test_rule_catalog.py` for pair schema; pre-computed v52 baseline). Rule 11 sanity validated to 3.5% error.
> 3. **`analysis/scripts/strategy_v53_c_pair_3.py`** — shared PBOT_DS enumeration + C_PAIR_3 sub-variants + the helper `_enumerate_pbot_ds` reused by v53.
> 4. **`analysis/scripts/strategy_v53_qpair_joint_pbot.py`** — **v53 PRODUCTION** (v52 + Rule 19).
> 5. **`analysis/scripts/audit_c_pair_3_S67.py`** — Phase 2 audit driver (3a/3b/3c on 4×2 cells).
> 6. **`analysis/scripts/audit_c_pair_fallback_S67.py`** — Phase 3 fallback driver (3b at higher thresholds + C_PAIR_5).
> 7. **`analysis/scripts/regression_check_c_pair_5_S67.py`** — full pair-category regression check on Rule 19.
> 8. **`analysis/scripts/grade_v53_qpair_joint_pbot.py`** — v53 vs v52 head-to-head grader.
> 9. **`data/session67/`** — audit logs, summaries, and grader outputs.
> 10. **`DECISIONS_LOG.md`** — Decision 102.
> 11. **`CURRENT_PHASE.md`** — rewritten for S68 (this file).

> **📓 METHODOLOGY (Session 68+):**
> - **Catalog ceilings from PAIR_DECISION_MATRIX.md must be re-interpreted.** The matrix's per-cell "v52→v44 gap" is NOT the catalog-shippable headroom — it includes v44's *selective* catch which a blanket rule cannot replicate. S67 falsified 11 of 12 such candidates. Treat matrix ceilings as upper bounds on capacity, not on realizable rule lifts.
> - **Pair PBOT-routing is mostly ML-only at catalog granularity.** Confirmed by C_PAIR_3 (4 ranks) + C_PAIR_5_simple (Q-pair PARTIAL) all-T3 verdicts. The Q-pair × PBOT_DS_JOINT cell is the lone exception — admits a clean +$8.50 rule because oracle PBOT preference at Q-pair-JOINT is structurally maximal (53% PBOT vs ~30% at lower ranks).
> - **Cell-routed hybrid chains are now the preferred Path-B mechanism.** Cleaner than rule extension when cells are clearly ML-favorable.
> - **Pair catalog harness is reusable.** Future pair-cell experiments should use `test_rule_catalog_pair.py` directly; the pre-computed v52 parquet makes per-cell measurement ~30× faster than calling v52 per hand.
> - **"Speed is not necessary — clarity and perfection is."** S67 took ~3.5 hours including harness build, 12-candidate sweep, regression check, v53 implementation, and prefix grader confirmation. The C_PAIR_3 falsification was clean and required no rework; the C_PAIR_5_joint discovery was the single positive finding.

> Updated: 2026-05-12 (Session 67 end — v53 ships subject to full grader; Path B mandated for S68)

---

## Headline state at end of Session 67

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v53_qpair_joint_pbot** | **PRODUCTION rule chain** (18 rules; v52 + Rule 19). **$2,490 full / $1,522 prefix (grader-confirmed)**. | `analysis/scripts/strategy_v53_qpair_joint_pbot.py` |
| **v44_dt** | **PRODUCTION ML champion** (UNCHANGED). $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: $1,417 → $1,409 (slight tightening from Rule 19).

**Per-category residuals (v53 framing, projecting v52−$8.50):**

| Category | n_hands | v44 within-cat | v53 $/1000h whole-grid | Status |
|---|---:|---:|---:|---|
| high_only | 1,226,940 | $1,868 | $755 | CATALOG CLOSED S65 |
| pair | 2,800,512 | $1,097 | $388 ← was $396 | **PHASE 3 CLOSED S67 — only Q-pair × JOINT shippable; rest ML-only** |
| trips | 328,185 | $1,194 | $55 | S69+ target |
| two_pair | 1,338,480 | $363 | $52 | Mid-priority |
| three_pair | 114,400 | $1,613 | $35 | Smaller per-hand gap |
| trips_pair | 171,600 | $281 | $5 | Collapsed S55a |
| composite | 14,742 | $960 | $2 | Rounding scale |
| quads | 14,300 | $545 | $1 | Rounding scale |

**Pair Phase 3 candidate verdicts (S67):**

| Candidate | Fire region (proposed) | Capture | WG lift | Verdict |
|---|---|---:|---:|---|
| C_PAIR_3a (simple 6-9) | 6/7/8/9 × {JOINT, PARTIAL} | -202% | -$315.39 | T3 |
| C_PAIR_3b (mid≥J) | 6/7/8/9 × {JOINT, PARTIAL} + mid≥J | -106% | -$165.20 | T3 |
| C_PAIR_3b (mid≥Q) | 6/7/8/9 × {JOINT, PARTIAL} + mid≥Q | -73% | -$114.04 | T3 |
| C_PAIR_3b (mid≥K) | 6/7/8/9 × {JOINT, PARTIAL} + mid≥K | -31% | -$48.71 | T3 |
| C_PAIR_3b (mid≥A) | 6/7/8/9 × {JOINT, PARTIAL} + mid≥A | (0 fires) | $0 | T3 (gate too tight) |
| C_PAIR_3c (joint-only 6-9) | 6/7/8/9 × JOINT | -12% | -$17.92 | T3 |
| C_PAIR_5 simple (Q-all) | Q × {JOINT, PARTIAL} | -25% | -$17.44 | T3 |
| **C_PAIR_5_joint** | **Q × JOINT only** | **+53% (within fire-cell)** | **+$8.50** | **T2 → SHIPS as v53 Rule 19** |

---

## Resume Prompt (Session 68 — hybrid chain experiment)

```
Resume Session 68 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S67 — Path B hybrid chain mandated)
- SESSION_67_C_PAIR_3_AUDIT.md (Phase 3 candidate sweep verdict)
- PAIR_DECISION_MATRIX.md (S66 — Recommendation Path B for hybrid design)
- DECISIONS_LOG.md (latest: Decision 102 — v53 ships Rule 19)
- analysis/scripts/test_rule_catalog_pair.py (the pair harness; reuse for hybrid sweep)
- analysis/scripts/strategy_v53_qpair_joint_pbot.py (current production)

State (end of Session 67):
- v53 ships Rule 19 (Q-pair JOINT PBOT-DS). +$8.50/1000h WG vs v52 (full grader pending at session close).
- Pair catalog harness operational. Reuse for any future pair-cell sweeps.
- C_PAIR_3 family decisively falsified (11/12 candidates T3). Pair PBOT-routing
  on 6/7/8/9 and on Q-pair × PARTIAL is ML-only at catalog granularity.
- Per-category WG residual (v53 framing): high_only $755 (closed), pair $388 (mostly ML-only),
  trips $55, two_pair $52, three_pair $35.

USER DIRECTIVE (S59-S67 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 68 — Hybrid chain experiment:

  PHASE 1 (S68 ~1 hr) — Build strategy_v54_pair_hybrid.py:
  - At inference: detect if hand is pair-category, compute cell tag
    (PBOT_DS_JOINT/PBOT_DS_PARTIAL/PMID_*), and route:
       - Pair PBOT cells → v44_dt
       - All other (pair PMID, non-pair) → v53
  - Reuse _enumerate_pbot_ds from strategy_v53_c_pair_3.py for cell tagging.
  - Smoke test: pick a few hands and verify routing.

  PHASE 2 (S68 ~2 hr) — Grade v54 vs v53 head-to-head:
  - Use grade_v53_qpair_joint_pbot.py as template.
  - Expected lift: ~+$200-390/1000h WG (per PAIR_DECISION_MATRIX.md Path B).
  - If grader confirms ≥+$100 WG → ship as v54.
  - If grader returns +$5-100 WG → catalog-worthy ship.
  - If T3 → pivot to C_PAIR_4 (drop Ace predicate from v9_2).

  PHASE 3 (S68 ~30 min) — Decision + S69 recommendation:
  - Ship v54 OR pivot to C_PAIR_4.
  - If pair direction is exhausted, queue trips/two_pair/three_pair audits.

ACCEPTANCE for Session 68:
- strategy_v54_pair_hybrid.py produced + smoke tests pass.
- Full-grid grader run on v54.
- Ship decision OR clear pivot.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- The pair catalog harness (test_rule_catalog_pair.py) is reusable; the
  v52 parquet pre-load makes per-cell measurement fast.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
