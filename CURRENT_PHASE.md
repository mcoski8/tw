# Current: Sprint 8 — Session 61 produced the second page of the high_only rule catalog: **K-high cells are formally labeled ML-only.** All 7 candidate refinement rules tested against Rule 15's residual failed Threshold 1, despite K-high having 5.6× A-high's drop-max rate (oracle drops K off top 34% in DSnj vs A's 6%). Most striking: C_K1 fired at **34.9%** — almost exactly oracle's drop-K rate — and was net **−$20/1000h WG**. The lesson from S60 (decision-matrix percentages tell you "oracle knows which q%", not "switching to that pick recovers EV") **generalizes from 6% to 34%**. C_K6 (HIBOT control) shipped −$22/1000h WG — empirical post-hoc validation that S51's HIMID design was correct. Two micro-positive candidates (C_K3 Q-on-top tight gate +$3.53; C_K7 top=2 surgical +$1.05) exist but combined ($+4.58/1000h WG) still under T2's $5/1000h bar. **The harness is now validated on TWO max-ranks** — Rule 14 (+$131) reproduced to 0.2% in S60, Rule 15 (+$51) reproduced to 0.7% in S61. Still reusable as-is for S62–S65. **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 / $686). The two production tracks STILL diverge by $1,417/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 62): Q-high cell-by-cell audit + candidates.**
>
>   Q-high is the right next zone: (a) 150,150 hands = 12.2% of high_only, third-largest after A and K; (b) Rule 16 (S52, Q-high HIMID) is +$19/1000h whole-grid when shipped (smaller than Rule 14's +$131 and Rule 15's +$51 → ergo proportionally even more headroom remaining); (c) Q has the **most aggressive drop-max profile** of the high zones tested so far — oracle drops Q off top **52% in DSnj** (vs K's 34%, A's 6%) and **20% in JOINT_HIGH** (vs K's 10%, A's 1%). If the rule-saturation pattern from S60+S61 generalizes (likely), Q-high also lands all-T3 and the ML-only zone grows. If a Q-high candidate clears T2 (unlikely given the trend), it's a major surprise that merits a drafted strategy_v53 + full grid grade.
>
>   **5-PHASE PLAN (Session 62 — mirror of S60/S61 structure):**
>
>   **Phase 1 — Reuse harness.** No new infrastructure required. `analysis/scripts/test_rule_catalog.py` is reusable verbatim; just import it. Optionally generalize the cell-classifier helpers from `candidates_K_high_S61.py` (rename internal `KING = 13` → `MAX = 12` and `_cell_for_hand_K` → `_cell_for_hand_Q`, OR refactor to a single `candidates_max_high.py` module parameterized by max-rank — recommended).
>
>   **Phase 2 — Sanity check + audit Rule 16 cell-by-cell.** Sanity check: Rule 16 (`strategy_v47_rule16_Qhigh_DS`) vs its pre-Rule-16 predecessor (`strategy_v46_rule15_Khigh_DS`) on Q-high cells (max=12). Expected total whole-grid lift ≈ +$19/1000h (S52 ship); acceptance window $17–$21. If outside, fix harness BEFORE proceeding. Then audit v52 cell-by-cell on Q-high: 6 cells (JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY; NEITHER empty). Expected dominant cell: Q × DS_NO_JOINT (n=94,500 = 62.9% of Q-high; S58 reported $44.37/1000h WG residual on v43; post-Rule-16 likely larger because oracle drops Q 52% but Rule 16 keeps Q on top 100%).
>
>   **Phase 3 — Propose Q-high candidate refinements.** Same template as S61 with Q-specific gating:
>     - C_Q1: `rule_Q_DSnj_drop_Q_low_top_DSms` — In Q × DSnj, drop Q to top ≤ 7 + DS bot + ms_mid_high ≥ J. (Mirror of C_K1; expected to fail with same pattern but useful for confirming the lesson.)
>     - C_Q2: `rule_Q_DSnj_take_Jtop_DSms` — Surgical: top=J + DS + ms_mid_high ≥ T. Mirrors C_K3's structural insight (Q-high JOINT_HIGH mid_high distribution: J:45%; ergo dropping Q to J on top might align with oracle frequently).
>     - C_Q3: `rule_Q_DSnj_drop_Q_when_Q_in_DSpair` — In Q × DSnj, when DS bot would contain Q as suited pair, take a non-Q top + ms_mid (analog of C_K2; S58 Observation 1 is even more relevant at Q given lower max-rank dominance).
>     - C_Q4: `rule_Q_DSnj_take_2top_DSms` — Surgical top=2 mirror of C_K7. Oracle picks top=2 16% in Q × DSnj (vs K's 7%) — bigger surface area for surgical capture.
>     - C_Q5: `rule_Q_MSonly_drop_Q` — Drop Q in MSonly (oracle drops 51% — the MSonly drop-max rate at Q is much higher than K's 22%).
>     - C_Q6: `rule_Q_DSnj_HIBOT_tiebreaker` — Negative control (expect to fail like C10/C_K6).
>   2–5 candidates per leaky cell, **cell-locally gated**.
>
>   **Phase 4 — Test against T1/T2/T3 thresholds.** Same definitions: T1 ≥40% gap closure within cell AND ≥+$3/1000h within-cell; T2 + ≥+$5/1000h whole-grid; T3 = no candidate clears T1.
>
>   **Phase 5 — Write `SESSION_62_Q_HIGH_CATALOG.md`.** Same template as `SESSION_60_A_HIGH_CATALOG.md` and `SESSION_61_K_HIGH_CATALOG.md`. If a T2-clearing rule emerges (unlikely): draft `strategy_v53_Q_high_handler.py` as `v52 + Rule 18` and grade vs v52 on full 6M grid (validating ZERO non-targeted regression). **More likely:** label all 6 cells ML-only and proceed.
>
>   **TIME BUDGET (S62):** Phase 1 (harness reuse + helper refactor) = 10 min; Phase 2 (sanity + audit on smaller 150K population) = 20 min; Phase 3 (candidates) = 45 min; Phase 4 (test 6–7 candidates) = 25 min; Phase 5 (catalog doc) = 30 min; total ~2 hr.
>
>   **SUCCESS CRITERIA (S62):**
>   - Rule 16 audit completed; remaining Q-high gap to oracle quantified per cell.
>   - At least 5 Q-specific candidate rules tested.
>   - Either ship at least one refinement (T2; unlikely) OR honestly label Q-high cells ML-only (T3).
>   - `SESSION_62_Q_HIGH_CATALOG.md` produced.

> **❌ NULL RESULT (Session 61 — for context):**
> - All 7 K-high candidates failed T1. K-high formally labeled ML-only at this catalog granularity.
> - C_K1 (DSnj_drop_K_low_top_DSms): −$20.08/1000h WG. Fired at 34.9% — almost exactly matching oracle's drop-K rate of 34% — but on the wrong subset.
> - C_K2 (DSnj_drop_K_when_K_in_DSpair): −$34.46/1000h WG (worst). The "K-in-DS-pair" structural axis from S58 fires too broadly.
> - C_K4 (DSnj_SSms_when_high): −$13.10/1000h WG. Mirror of A-high C2; same negative pattern even at higher oracle ms_mid rate (51% K vs 41% A).
> - C_K5 (MSonly_drop_K): −$21.48/1000h WG (catastrophic). Fired 82.7% — way over oracle's 22% drop-K rate.
> - C_K6 (DSnj_HIBOT_tiebreaker): −$21.73/1000h WG. **Confirmed Rule 15's HIMID design choice is empirically correct.**
> - C_K3 / C_K7: micro-positive (+$3.53 / +$1.05) but capture% (3.33% / 0.99%) far below T1's 40% bar.

> **✅ ARTIFACTS to reuse from S60+S61:**
> 1. **`analysis/scripts/test_rule_catalog.py`** (S60, validated S60+S61 to 0.7% accuracy on TWO independent shipped rules) — per-cell rule audit harness. Reusable verbatim for S62–S65.
> 2. **`analysis/scripts/candidates_K_high_S61.py`** (S61) — 7 K-high candidates. Useful as template for `candidates_Q_high_S62.py`. Generic helpers `_enumerate_max_on_top_configs(hand, max_rank)` and `_enumerate_nonMax_top_DSms(hand, max_rank)` already parameterized by max-rank.
> 3. **`analysis/scripts/candidates_A_high_S60.py`** (S60) — 10 A-high candidates. Older template still useful for the `_best_4fms_pick` helper not in K-high candidates.
> 4. **`analysis/scripts/audit_rule15_S61.py`** (S61) — Phase 2 sanity + audit driver. Adapt to Rule 16 sanity by substituting `strategy_v46_rule15_Khigh_DS` → `strategy_v47_rule16_Qhigh_DS` and the predecessor.
> 5. **`analysis/scripts/test_A_high_candidates_S60.py` + `test_K_high_candidates_S61.py`** — sweep drivers; copy-and-adapt for S62.
> 6. **`data/session_60_candidate_results.json` + `data/session_61_candidate_results.json`** — full results, T1/T2/T3 verdicts, full per-candidate metric breakdown.
> 7. **`SESSION_60_A_HIGH_CATALOG.md` + `SESSION_61_K_HIGH_CATALOG.md`** — A and K catalog pages. Templates for the Q/J/T/9/8 catalog pages.
> 8. **From S59:** `data/drill_ho_v44_per_hand_structural.parquet` (15 MB) — per-hand v44 residual structure with cell tags. **Still the foundation for catalog work in S62+.**
> 9. **From S58:** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` — per-max-rank × per-cell oracle TOP/BOT/MID profile. Use as the "what should the rule do?" reference when designing candidate rules, BUT treat the percentages as upper bounds on rule-recoverable EV (per S60 lesson, re-confirmed S61).

> **📓 METHODOLOGY (Session 62+):**
> - **Threshold definitions (unchanged from S60/S61):**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure between v52 and oracle ceiling within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (use existing 6-cell scheme):** JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER. Defined in `drill_high_only_v44_deepdive.cell_for_hand`.
> - **Always sanity-check the harness on the existing rule first.** Reproduce the rule's known shipped lift vs its pre-rule predecessor. For S62: Rule 16 (S52) vs `strategy_v46_rule15_Khigh_DS` should yield +$19/1000h on Q-high. ±10% acceptance window.
> - **Decision-matrix percentages are NOT directly recoverable.** S58's matrix says "oracle picks X q% in cell C" — this is what oracle achieves with FULL knowledge, not what a rule firing on "X is achievable" can recover. **Re-confirmed S61 at 34% drop-K rate.** Expect candidates to need TIGHT gating to clear thresholds.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60+S61.)
> - **Test candidates BOTH ways**: gate on cell predicate (cheap, exact), and gate on rule-pick-direction (e.g., "switch DS→SS only when SS_ms mid_high > DS bot pair_high AND DS bot pair is low"). The S60+S61 candidate sets were probably under-gated.

> Updated: 2026-05-11 (Session 61 end — K-high catalog page complete; pivot to Q-high)

---

## Headline state at end of Session 61 (UNCHANGED from S58/S59/S60)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v45_rule14_Ahigh_DS (Rule 14 standalone) | Rule 14 fired against v44_rule13 baseline. Predecessor in chain. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` |
| v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains for K/Q. **Rule 15 audited S61. Rule 16 is the S62 audit target.** | `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` / `strategy_v47_rule16_Qhigh_DS.py` |

**Per-category residuals (UNCHANGED from S58/S59/S60 since no production change in S61):**

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

**K-high catalog page produced in S61:** `SESSION_61_K_HIGH_CATALOG.md`. Verdict: all 6 K-high cells labeled ML-only. v44_dt is the best available approach on K-high's residual ($110.94/1000h WG remaining). The catalog methodology successfully **falsified** the S58 decision-matrix-derived expectation that K's structurally larger drop-max rate (34% vs A's 6%) would yield Threshold-2 shippable rules. **Two-thirds of high_only's WG residual ($457 of $755) is now formally in the ML-only zone.**

**Existing high_only rules and their whole-population shipped lifts:**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S62 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 | **AUDITED S60: ALL CELLS ML-ONLY.** Harness reproduces lift to 0.2%. |
| K | Rule 15 | S51 | +$51 | **AUDITED S61: ALL CELLS ML-ONLY.** Harness reproduces lift to 0.7%. |
| Q | Rule 16 | S52 | +$19 | **S62 TARGET.** Cell-level audit not yet done. |
| J/T/9/8 (defensive) | Rule 17 / v52 | S53 | +$17 | Cell-level audit pending (S63/64). |

**Two production tracks at end of S61 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h.

---

## Session 60+ catalog sequence (updated)

| Session | Max-rank focus | Existing rule | Population | $/1000h WG residual after current rule | Outcome |
|---|---|---|---|---:|---|
| **60** | A-high | Rule 14 | 660,660 (53.8%) | $281.2 (vs oracle); $182.5 (vs v44) | **NULL — all cells ML-only** |
| **61** | **K-high** | **Rule 15** | **330,330 (26.9%)** | **$176.4 (vs oracle); $110.9 (vs v44)** | **NULL — all cells ML-only** |
| 62 | Q-high | Rule 16 | 150,150 (12.2%) | TBD per Phase 2 audit | TBD |
| 63 | J-high | Rule 17 (HIMID branch) | 60,060 (4.9%) | TBD | TBD |
| 64 | T/9/8 combined | Rule 17 (defensive branch) | 25,740 (2.1%) | TBD | TBD |
| 65 | Aggregate + cross-cell rules | All | All high_only | Synthesis | Final catalog |

The S61 confirmation of the S60 null is BIG SIGNAL for the project: **two-of-two max-ranks tested have produced ALL-T3 verdicts**, and the structural opportunity (drop-max rate) at K was 5.6× larger than at A. This strongly suggests the entire $755/1000h WG high_only residual is genuinely ML-only territory — validating v44_dt as the ceiling rule-chain strategies can approach but not pass. If S62 produces a third ML-only verdict at Q (where drop-max is 52%), the case will be effectively closed.

---

## Resume Prompt (Session 62 — Q-high catalog audit)

```
Resume Session 62 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S61 — K-high NULL; Q-high next)
- DECISIONS_LOG.md (latest: Decision 096 — S61 K-high catalog NULL)
- SESSION_60_A_HIGH_CATALOG.md and SESSION_61_K_HIGH_CATALOG.md
  (the first two pages of HIGH_ONLY_RULE_CATALOG.md and the templates
  for Q/J/T/9/8 pages)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (oracle decisions per max × cell)
- analysis/scripts/test_rule_catalog.py (the validated harness — reuse verbatim)
- analysis/scripts/candidates_K_high_S61.py (template for candidates_Q_high_S62.py;
  helpers already parameterized by max_rank)
- analysis/scripts/audit_rule15_S61.py (template for audit_rule16_S62.py)
- analysis/scripts/strategy_v52_full_high_only_handler.py (current v52 chain)
- analysis/scripts/strategy_v47_rule16_Qhigh_DS.py (Rule 16 standalone — audit target)
- analysis/scripts/strategy_v46_rule15_Khigh_DS.py (Rule 15 — Rule 16's predecessor for sanity check)
- analysis/scripts/strategy_v44_dt.py (ML champion benchmark)

State (end of Session 61):
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- A-high catalog page produced S60: all 6 A-high cells labeled ML-only.
- K-high catalog page produced S61: all 6 K-high cells labeled ML-only.
- Harness `test_rule_catalog.py` validated to 0.2% (S60 / Rule 14)
  and 0.7% (S61 / Rule 15) — TWO independent reproductions of shipped lifts.
- All 7 K-high candidates tested fell below Threshold 1.
- Methodology lesson re-confirmed at K: decision-matrix percentages
  overstate rule-recoverable EV, EVEN AT 34% drop-K rate (5.6× A).
- Q-high structural opportunity: oracle drops max off top 52% in
  Q × DSnj (vs K's 34%, A's 6%); 20% in Q × JOINT_HIGH (vs K's 10%,
  A's 1%). MOST aggressive drop-max profile of zones tested so far.

USER DIRECTIVE (S59/S60/S61 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- Build the catalog over 5–6 sessions; A and K pages produced in S60+S61.

DIRECTION FOR SESSION 62 (Q-high catalog audit + harness reuse):

5-PHASE PLAN — same shape as S60/S61:

Phase 1 — Reuse harness. No new infrastructure. Optionally refactor
candidates_K_high_S61.py to a single candidates_max_high.py module
parameterized by max_rank.

Phase 2 — Sanity-check Rule 16 cell-by-cell on Q-high. Expect harness
to reproduce Rule 16's documented +$19/1000h whole-grid shipped lift
vs its pre-Rule-16 predecessor (strategy_v46_rule15_Khigh_DS).
Acceptance window: $17–$21. Then audit v52 cell-by-cell on Q-high.
Identify leaky cells (likely Q × DS_NO_JOINT dominant; expected
larger residual than K's $105.94/1000h WG given oracle's 52% drop-Q).

Phase 3 — Propose Q-specific candidates. Listed in CURRENT_PHASE.md
"Direction for Session 62" section. ~6 candidates concentrating on
the drop-Q-off-top play.

Phase 4 — Test each candidate via test_rule_on_cell with baseline=v52.
Apply T1/T2/T3 thresholds.

Phase 5 — Write SESSION_62_Q_HIGH_CATALOG.md (mirror of
SESSION_61_K_HIGH_CATALOG.md). If at least one candidate clears T2
(unlikely): draft strategy_v53_Q_high_handler.py and grade vs v52
on full 6M grid (validating ZERO non-targeted regression).

ACCEPTANCE for Session 62:
- Sanity check on Rule 16 + harness reproduces +$19/1000h ±10%.
- All 6 Q-high cells audited.
- At least 5 Q-specific candidates tested.
- Either at least one T2-shipping rule OR honest ML-only labeling
  for all leaky Q-high cells.
- SESSION_62_Q_HIGH_CATALOG.md produced.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- PYTHONUNBUFFERED=1 or python3 -u for long scripts.
- Reuse data/drill_ho_v44_per_hand_structural.parquet for cell tags.
- Reuse data/oracle_grid_full_realistic_n200.bin for EV evaluation.
- Don't propose candidates without first auditing the existing
  rule (Rule 16) for that cell.
- Treat S58 decision-matrix percentages as upper bounds on
  rule-recoverable EV, not direct targets (S60+S61 lesson).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
