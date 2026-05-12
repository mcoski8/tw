# Current: Sprint 8 — Session 60 produced the first page of the high_only rule catalog: **A-high cells are formally labeled ML-only.** All 10 candidate refinement rules tested against Rule 14's residual failed Threshold 1. Most striking: C1 ("switch DS_mu → SS_ms whenever achievable") was net **−$96.9/1000h whole-grid** in A × DS_NO_JOINT, even though oracle picks `tA_SS_ms` 27.9% of that cell. Lesson: decision-matrix percentages tell you "oracle knows which 28%", not "switching to that pick recovers EV." A deterministic gate firing on 93% of cell hurts the 72% where DS was correct. C10 (HIBOT tiebreaker replacing Rule 14's HIMID) shipped **−$40/1000h** — empirical post-hoc validation that S50's HIMID design was correct. **The harness (`test_rule_catalog.py`) is validated** (reproduced Rule 14's documented +$131.25/1000h shipped lift to 0.2%) and **reusable as-is for S61–S65**. **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 / $686). The two production tracks STILL diverge by $1,417/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 61): K-high cell-by-cell audit + candidates.**
>
>   K-high is the right next zone: (a) 330,330 hands = 26.9% of high_only, second-largest after A; (b) Rule 15 (S51, K-high HIMID) is +$51/1000h whole-grid when shipped (smaller than Rule 14's +$131 → ergo more headroom proportionally remaining); (c) structural decision conditions differ markedly from A-high — oracle drops max off top **34% in K × DS_NO_JOINT** vs 6% at A, and **22% in K × MS_ONLY** vs 2% at A. The "drop max off top" play is 5–11× more common at K. A candidate analogous to C9 (drop max for non-max-top DS_ms when bot pair_high ≥ J) catastrophically failed on A-high but may clear thresholds on K because the fire rate matches oracle behavior more naturally.
>
>   **5-PHASE PLAN (Session 61 — mirror of S60 structure):**
>
>   **Phase 1 — Reuse harness.** No new infrastructure required. `analysis/scripts/test_rule_catalog.py` is reusable verbatim; just import it. Optionally also import the cell-classifier helpers from `candidates_A_high_S60.py` (rename `_enumerate_A_on_top_configs` → generic `_enumerate_max_on_top_configs(hand, max_rank)` if the K version needs adaptation).
>
>   **Phase 2 — Audit Rule 15 cell-by-cell.** For each of K-high's 6 structural cells (JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY; NEITHER is empty), measure Rule 15's mean_ev vs oracle ceiling. Expected dominant cell: K × DS_NO_JOINT (n=207,900 = 62.9% of K-high; S58 reported $87.02/1000h WG within-cell residual on v43; the post-Rule-15 residual is likely larger because Rule 15 is "K on top + DS bot + HIMID" identical to Rule 14's structure but with K instead of A — and oracle drops K off top 34% of the time in this cell).
>
>   **Phase 3 — Propose K-high candidate refinements.** Same template as S60 but with K-specific gating:
>     - C_K1: `rule_K_DSnj_drop_K_to_lowtop_DSms` — In K × DS_NO_JOINT, if a (top=2 or 3 or 4, DS bot with K-pair-or-high-pair, ms_mid with mid_high ≥ J) config is achievable, take it. Mirrors S58's oracle picks of `t2_DS_ms` etc. (more common at K than A).
>     - C_K2: `rule_K_DSnj_drop_K_when_KQ_DSms` — Same but specifically when K pairs with Q in the bot (KQ-suited bot pair, suggests strong overall structure).
>     - C_K3: `rule_K_DSnj_take_QtopDSms` — When (top=Q, DS bot, ms_mid ≥ J) achievable, take it (Q-on-top is a known oracle move at K-high).
>     - C_K4: `rule_K_MSonly_drop_K` — Drop K off top in MS_ONLY (22% oracle drop rate vs 2% at A).
>     - C_K5: `rule_K_DSnj_HIBOT_tiebreaker` — Negative control (expect to fail like C10).
>   2–4 candidates per leaky cell, **cell-locally gated**.
>
>   **Phase 4 — Test against T1/T2/T3 thresholds.** Same definitions: T1 ≥40% gap closure within cell AND ≥+$3/1000h within-cell; T2 + ≥+$5/1000h whole-grid; T3 = no candidate clears T1.
>
>   **Phase 5 — Write `SESSION_61_K_HIGH_CATALOG.md`.** Same template as `SESSION_60_A_HIGH_CATALOG.md`. If a T2-clearing rule emerges, draft `strategy_v53_K_high_handler.py` as `v52 + Rule 18` and grade vs v52 on full 6M grid. Even one T2 ship would validate the catalog methodology produces shippable rules where ML saturated.
>
>   **TIME BUDGET (S61):** Phase 1 (harness reuse) = 5 min; Phase 2 (audit) = 30 min (smaller population than A-high); Phase 3 (candidates) = 45 min; Phase 4 (test 5–10 candidates) = 30 min; Phase 5 (catalog doc) = 30 min; total ~2.5 hr.
>
>   **SUCCESS CRITERIA (S61):**
>   - Rule 15 audit completed; remaining K-high gap to oracle quantified per cell.
>   - At least 5 K-specific candidate rules tested (drop-max focused).
>   - Either ship at least one refinement (T2) OR honestly label K-high cells ML-only (T3).
>   - `SESSION_61_K_HIGH_CATALOG.md` produced.

> **❌ NULL RESULT (Session 60 — for context):**
> - All 10 A-high candidates failed T1. A-high formally labeled ML-only at this catalog granularity.
> - C1 (DSnj_SSms_any): −$96.9/1000h WG (worst). Switching unconditionally hurts.
> - C4 (DSnj_SSms_beats_DSpair): 0% fires — structural gate too tight.
> - C9 (DSnj_drop_A_for_AK_DSms): −$284/1000h WG (catastrophic) — fired 51%, oracle wants A-on-top in 94% of cell.
> - C10 (DSnj_HIBOT_tiebreaker): −$40/1000h. **Confirmed Rule 14's HIMID design choice is empirically correct.**
> - C5/C6/C7/C8 (31_ms branches, DSnm and MSonly): tiny positive lift ($1–$2/1000h WG) — well under T1's $3 within-cell bar.

> **✅ ARTIFACTS to reuse from S60:**
> 1. **`analysis/scripts/test_rule_catalog.py`** (NEW, 7.2 KB) — per-cell rule audit harness. Reusable verbatim for S61–S65. Reports CatalogResult with within-cell + whole-grid lift, capture % vs baseline AND v44, % optimal, top mismatch classes.
> 2. **`analysis/scripts/candidates_A_high_S60.py`** (NEW, 10.7 KB) — 10 A-high candidates. Useful as a template for S61's `candidates_K_high_S61.py`.
> 3. **`analysis/scripts/test_A_high_candidates_S60.py`** (NEW) — driver: runs candidate sweep, scores T1/T2/T3, writes JSON.
> 4. **`data/session_60_candidate_results.json`** (NEW) — full results for C1–C8 (C9/C10 results in `/tmp/s60_candidates_pass2.log`).
> 5. **`SESSION_60_A_HIGH_CATALOG.md`** (NEW) — A-high catalog page. Template for the K/Q/J/T/9/8 catalog pages.
> 6. **From S59:** `data/drill_ho_v44_per_hand_structural.parquet` (15 MB) — per-hand v44 residual structure with cell tags. **Still the foundation for catalog work in S61+.**
> 7. **From S58:** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` — per-max-rank × per-cell oracle TOP/BOT/MID profile. Use as the "what should the rule do?" reference when designing candidate rules, BUT treat the percentages as upper bounds on rule-recoverable EV (per S60's methodology lesson — oracle knows which 28%, gates don't).

> **📓 METHODOLOGY (Session 61+):**
> - **Threshold definitions (unchanged from S60):**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure between v52 and oracle ceiling within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (use existing 6-cell scheme):** JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER. Defined in `drill_high_only_v44_deepdive.cell_for_hand`.
> - **Always sanity-check the harness on the existing rule first.** Reproduce the rule's known shipped lift vs its pre-rule predecessor (e.g., for K-high audit Rule 15 vs `strategy_v45_rule14_Ahigh_DS` — Rule 14 IS Rule 15's pre-Rule-15 baseline since Rule 15 fires for max=K only). Expect ~+$51/1000h whole-grid on K-high. If the sanity check is off by more than ±10%, fix the harness before proceeding.
> - **Decision-matrix percentages are NOT directly recoverable.** S58's matrix says "oracle picks X q% in cell C" — this is what oracle achieves with FULL knowledge, not what a rule firing on "X is achievable" can recover. A simple gate fires on a SUPERSET of oracle's q% and hurts the complement. Expect candidates to need TIGHT gating to clear thresholds.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60.)
> - **Test candidates BOTH ways**: gate on cell predicate (cheap, exact), and gate on rule-pick-direction (e.g., "switch DS→SS only when SS_ms mid_high > DS bot pair_high AND DS bot pair is low"). The S60 candidate set was probably under-gated.

> Updated: 2026-05-11 (Session 60 end — A-high catalog page complete; pivot to K-high)

---

## Headline state at end of Session 60 (UNCHANGED from S58/S59)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v45_rule14_Ahigh_DS (Rule 14 standalone) | Rule 14 fired against v44_rule13 baseline. Predecessor in chain. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` |
| v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains for K/Q. **The Rule 15 audit target for S61.** | `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` / `strategy_v47_rule16_Qhigh_DS.py` |

**Per-category residuals (UNCHANGED from S58/S59 since no production change in S60):**

| Category | n_hands | share | v44 within-cat | $/1000h whole-grid |
|---|---:|---:|---:|---:|
| **high_only** | 1,226,940 | 40.4% | $1,868 | $755 |
| pair | 2,800,512 | 36.2% | $1,097 | $396 |
| trips | 328,185 | 4.6% | $1,194 | $55 |
| two_pair | 1,338,480 | 14.5% | $363 | $52 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 |
| trips_pair | 171,600 | 1.8% | $281 | $5 |
| composite | 14,742 | 0.2% | $960 | $2 |
| quads | 14,300 | 0.1% | $545 | $1 |

**A-high catalog page produced in S60:** `SESSION_60_A_HIGH_CATALOG.md`. Verdict: all 6 A-high cells labeled ML-only. v44_dt is the best available approach on A-high's residual ($182.5/1000h WG remaining). The catalog methodology successfully **falsified** the S58 decision-matrix-derived expectation that simple deterministic switching rules would recover oracle's 27.9% `tA_SS_ms` picks.

**Existing high_only rules and their whole-population shipped lifts:**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S61 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 | **AUDITED S60: ALL CELLS ML-ONLY.** Harness reproduces lift to 0.2%. |
| K | Rule 15 | S51 | +$51 | **S61 TARGET.** Cell-level audit not yet done. |
| Q | Rule 16 | S52 | +$19 | Cell-level audit pending (S62). |
| J/T/9/8 (defensive) | Rule 17 / v52 | S53 | +$17 | Cell-level audit pending (S63/64). |

**Two production tracks at end of S60 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h.

---

## Session 60+ catalog sequence (updated)

| Session | Max-rank focus | Existing rule | Population | $/1000h WG residual after current rule | Outcome |
|---|---|---|---|---:|---|
| **60** | **A-high** | Rule 14 | **660,660 (53.8%)** | **$281.2 (vs oracle); $182.5 (vs v44)** | **NULL — all cells ML-only** |
| 61 | K-high | Rule 15 | 330,330 (26.9%) | TBD per Phase 2 audit | TBD |
| 62 | Q-high | Rule 16 | 150,150 (12.2%) | TBD | TBD |
| 63 | J-high | Rule 17 (HIMID branch) | 60,060 (4.9%) | TBD | TBD |
| 64 | T/9/8 combined | Rule 17 (defensive branch) | 25,740 (2.1%) | TBD | TBD |
| 65 | Aggregate + cross-cell rules | All | All high_only | Synthesis | Final catalog |

The S60 null is BIG SIGNAL for the project: if K-high's drop-max play (34% in DSnj) is similarly unrecoverable by simple rules, the entire $755/1000h WG high_only residual may be genuinely ML-only territory, validating v44_dt as the ceiling rule-chain strategies can approach but not pass. Conversely, if K-high yields T2 shippable rules, the catalog methodology proves it can crack high_only structurally where ML alone saturated.

---

## Resume Prompt (Session 61 — K-high catalog audit)

```
Resume Session 61 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S60 — A-high NULL; K-high next)
- DECISIONS_LOG.md (latest: Decision 095 — S60 A-high catalog NULL)
- SESSION_60_A_HIGH_CATALOG.md (the first page of HIGH_ONLY_RULE_CATALOG.md
  and the template for K/Q/J/T/9/8 pages)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (oracle decisions per max × cell)
- analysis/scripts/test_rule_catalog.py (the validated harness — reuse verbatim)
- analysis/scripts/candidates_A_high_S60.py (template for candidates_K_high_S61.py)
- analysis/scripts/strategy_v52_full_high_only_handler.py (current v52 chain)
- analysis/scripts/strategy_v46_rule15_Khigh_DS.py (Rule 15 standalone — audit target)
- analysis/scripts/strategy_v44_dt.py (ML champion benchmark)

State (end of Session 60):
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- A-high catalog page produced: all 6 A-high cells labeled ML-only.
- Harness `test_rule_catalog.py` validated to 0.2% accuracy.
- All 10 A-high candidates tested fell below Threshold 1.
- Methodology lesson: decision-matrix percentages overstate
  rule-recoverable EV (oracle knows WHICH q% to switch on).
- K-high structural opportunity: oracle drops max off top 34% in
  K × DSnj (vs 6% at A) and 22% in K × MS_ONLY (vs 2% at A).

USER DIRECTIVE (S59/S60 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- Build the catalog over 5–6 sessions; A-high page produced in S60.

DIRECTION FOR SESSION 61 (K-high catalog audit + harness reuse):

5-PHASE PLAN — same shape as S60:

Phase 1 — Reuse harness. No new infrastructure.

Phase 2 — Audit Rule 15 cell-by-cell on K-high. Sanity-check:
expect harness to reproduce Rule 15's documented +$51/1000h
whole-grid shipped lift vs its pre-Rule-15 predecessor
(strategy_v45_rule14_Ahigh_DS). Measure per-cell mean_ev gap to
oracle. Identify leaky cells (likely K × DS_NO_JOINT dominant).

Phase 3 — Propose K-specific candidates concentrating on the
drop-K-off-top play (S58 matrix: oracle drops K 34% in DSnj vs
6% at A). Candidates listed in CURRENT_PHASE.md "Direction for
Session 61" section. ~5 candidates.

Phase 4 — Test each candidate via test_rule_on_cell with
baseline=v52. Apply T1/T2/T3 thresholds.

Phase 5 — Write SESSION_61_K_HIGH_CATALOG.md (mirror of
SESSION_60_A_HIGH_CATALOG.md). If at least one candidate clears
T2: draft strategy_v53_K_high_handler.py and grade vs v52 on full
6M grid (validating ZERO non-targeted regression).

ACCEPTANCE for Session 61:
- Sanity check on Rule 15 + harness reproduces +$51/1000h ±10%.
- All 6 K-high cells audited.
- At least 5 K-specific candidates tested.
- Either at least one T2-shipping rule OR honest ML-only labeling
  for all leaky K-high cells.
- SESSION_61_K_HIGH_CATALOG.md produced.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- PYTHONUNBUFFERED=1 or python3 -u for long scripts.
- Reuse data/drill_ho_v44_per_hand_structural.parquet for cell tags.
- Reuse data/oracle_grid_full_realistic_n200.bin for EV evaluation.
- Don't propose candidates without first auditing the existing
  rule (Rule 15) for that cell.
- Treat S58 decision-matrix percentages as upper bounds on
  rule-recoverable EV, not direct targets (S60 lesson).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
