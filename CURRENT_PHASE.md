# Current: Sprint 8 — Session 63 produced the fourth page of the high_only rule catalog: **J-high cells are formally labeled ML-only.** All 7 candidate refinement rules tested against v52's residual failed Threshold 1, despite J-high having the most aggressive drop-max profile of all zones tested (oracle drops J off top 76% in DSnj vs Q 52%, K 34%, A 6%). **CRITICAL HARNESS CLARIFICATION:** Phase 2 sanity check uncovered that CURRENT_PHASE's previous "Rule 17 = +$17 shipped lift" attribution was a misread of the S53 OVERNIGHT REPORT — that +$17 is actually **v52's TOTAL over v47 across all high_only** (Rule 17 J-HIMID + Rules 22-28 defensive across J/T/9/8/7-high). Rule 17 ALONE on J-high (v48 vs v47) is +$5.48/1000h WG. The cross-check `sanity_v52_vs_v47_high_only.py` reproduces v52-vs-v47 = +$16.77 vs documented +$17 to **1.4% accuracy** — **fourth independent harness validation** joining Rule 14 (0.2%), Rule 15 (0.7%), Rule 16 (1.7%). The methodology lesson partially shifts at J: best-candidate capture% jumped to **21.54%** (vs A 5.45%, K 3.33%, Q 5.99%) — finally tracking drop-max rate growth. C_J1 (drop J to low top + DSms) shipped **+$6.44/1000h WG** — the BIGGEST single-candidate WG lift across the entire S60–S63 catalog, exceeding T2's $5/1000h bar in raw WG terms but missing T1's 40% gap-closure bar at 21.54%. C_J7 (HIBOT control) shipped −$6.56/1000h WG — **fourth retrospective HIMID validation. Rule 17's design empirically correct.** **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 full / $686 prefix). The two production tracks STILL diverge by $1,417/1000h. **77% of high_only's WG residual ($578 of $755) is now formally in the ML-only zone.**

> **🎯 IMMEDIATE NEXT ACTION (Session 64): T/9/8-high combined cell-by-cell audit.**
>
>   T/9/8-high is the final residual zone (combined n=25,740 = 2.1% of high_only). v52 fires Rules 25/26/27 (always-defensive lowest-on-top + DS/SS HIMID) — a fundamentally different strategy than the J-and-above max-on-top + DS HIMID family. Predicted ~$20–30/1000h WG total residual. If T/9/8 lands ML-only (extremely likely after four consecutive falsifications), the entire $755/1000h high_only residual is formally ML-only and Session 65 produces the aggregate catalog.
>
>   **STRUCTURAL INVERSION at T/9/8:** v52 ALREADY drops max by default (lowest-on-top is the rule, not the exception). So candidates can't explore "drop max" play — that's the baseline. The candidate space inverts: explore lowest-on-top *tiebreaker* refinements, DS-vs-SS bot preference gates, mid_high quality gates, etc. This makes the catalog structure different from A/K/Q/J pages.
>
>   **5-PHASE PLAN (Session 64 — adapted shape):**
>
>   **Phase 1 — Adapt harness for the always-defensive baseline.** No new infrastructure required. `analysis/scripts/test_rule_catalog.py` is reusable verbatim. Build `candidates_T98_high_S64.py` from scratch (NOT a copy of `candidates_J_high_S63.py`) since the candidate space is fundamentally different.
>
>   **Phase 2 — Sanity check Rules 25/26/27 + cell-by-cell audit on T/9/8.** Use the now-validated cross-check pattern: v52 vs v51 (the immediate pre-defensive predecessor) on max ∈ {10, 9, 8}. Expected total whole-grid lift ≈ +$11.50/1000h (S53 OVERNIGHT report line 20 says v52 = +$17 total over v47 across all high_only; subtracting Rule 17's +$5.48 J-contribution leaves ~$11.50 attributable to Rules 22-28 across K/Q defensive + T/9/8/7 always-defensive, of which T/9/8 contributes ~$10 per S53 final summary). Acceptance window ±10%. Then audit v52 cell-by-cell on T/9/8 (combined and separately). Identify leaky cells.
>
>   **Phase 3 — Propose T/9/8-specific candidates.** Candidate ideas:
>     - C_T1: lowest-on-top tiebreaker — break ties between equally-low ranks by suit profile (e.g., prefer the low rank that pairs with a DS bot).
>     - C_T2: switch lowest-on-top → second-lowest when the second-lowest enables a higher-quality DS bot pair.
>     - C_T3: keep T on top in T-high JOINT cells (if any exist — extrapolation says JOINT_HIGH is empty at T as it was at J).
>     - C_T4: 31-bot promotion when no DS available (S58 says oracle prefers 31 over SS in some T-high subsets).
>     - C_T5: HIBOT vs HIMID — same retrospective HIMID validation pattern (expected 5th confirmation).
>     - C_98: mirror of best T candidate adapted for max=9 and max=8.
>   3–5 candidates per leaky cell, **cell-locally gated**.
>
>   **Phase 4 — Test each candidate via T1/T2/T3 thresholds.** Same definitions: T1 ≥40% gap closure within cell AND ≥+$3/1000h within-cell; T2 + ≥+$5/1000h whole-grid; T3 = no candidate clears T1.
>
>   **Phase 5 — Write `SESSION_64_T98_HIGH_CATALOG.md`.** Mirrors S63 structure but with three sub-pops (T, 9, 8) rather than one. If a T2-clearing rule emerges (very unlikely after four consecutive falsifications): draft strategy_v53. **Far more likely:** label all 6+ cells ML-only across all three max-ranks.
>
>   **TIME BUDGET (S64):** Phase 1 (candidates from scratch) = 30 min; Phase 2 (cell audit on 25.7K hands, very fast) = 5 min; Phase 3 (additional candidates) = 30 min; Phase 4 (test ~6 candidates) = 10 min; Phase 5 (catalog doc) = 30 min; total ~1.75 hr.
>
>   **SUCCESS CRITERIA (S64):**
>   - Rules 25/26/27 audit completed; remaining T/9/8 gap to oracle quantified per cell.
>   - At least 5 T/9/8-specific candidate rules tested.
>   - Either ship at least one refinement (T2; vanishingly unlikely) OR honestly label T/9/8 cells ML-only (T3).
>   - `SESSION_64_T98_HIGH_CATALOG.md` produced.

> **❌ NULL RESULT (Session 63 — for context):**
> - All 7 J-high candidates failed T1. J-high formally labeled ML-only at this catalog granularity.
> - C_J1 (DSnj_drop_J_low_top_DSms): **+$6.44/1000h WG**, capture +21.54%. Fires 39.8% — partially tracks oracle's 76% drop-J rate. **Biggest single-candidate WG lift across S60–S63.** Exceeds T2's $5 bar in raw WG but misses T1's 40% gap-closure bar.
> - C_J2 (DSnj_take_2top_DSms): +$2.61/1000h WG, capture +8.73%. Surgical top=2 tiny capture.
> - C_J3 (DSnj_take_3top_DSms): +$1.98/1000h WG, capture +6.61%. Surgical top=3 even tinier.
> - C_J4 (DSnj_drop_J_when_J_in_DSpair): **+$4.59/1000h WG**, capture +15.35%. Fires 43.9% (biggest gate of any candidate across S60-S63). Second-best J candidate.
> - C_J5 (DSnj_SSms_when_high): −$0.22/1000h WG. Negative but smaller than at Q (−$2.02) and K (−$13.10).
> - C_J6 (MSonly_drop_J): −$0.70/1000h WG. Fires 89.1% — same over-fire pattern as C_K5 (82.7%) and C_Q6 (85.8%) across K/Q/J.
> - C_J7 (DSnj_HIBOT_tiebreaker): −$6.56/1000h WG. **Fourth retrospective HIMID validation. Rule 17's design empirically correct.**

> **✅ ARTIFACTS to reuse from S60+S61+S62+S63:**
> 1. **`analysis/scripts/test_rule_catalog.py`** (S60, validated S60+S61+S62+S63 to within 0.2–1.7% on FOUR independent shipped rules — Rule 14, Rule 15, Rule 16, v52 ensemble) — per-cell rule audit harness. Reusable verbatim for S64–S65.
> 2. **`analysis/scripts/sanity_v52_vs_v47_high_only.py`** (S63) — **cross-check pattern that resolves shipped-lift attribution discrepancies.** Reuse the by-max_rank decomposition template at S64 to sanity-check v52's contribution at T/9/8.
> 3. **`analysis/scripts/candidates_K_high_S61.py`** (S61) — **generic helpers** `_enumerate_max_on_top_configs(hand, max_rank)`, `_enumerate_nonMax_top_DSms(hand, max_rank)`, `_enumerate_nonMax_top_anyBot_ms(hand, max_rank)`. **Note:** at T/9/8 these helpers are LESS USEFUL since the strategy is lowest-on-top, not max-on-top. S64 likely needs new enumeration helpers for lowest-on-top configs.
> 4. **`analysis/scripts/candidates_J_high_S63.py`** (S63) — 7 J-high candidates. **NOT a direct template for S64** — T/9/8 candidate space is fundamentally different (defensive baseline).
> 5. **`analysis/scripts/audit_rule17_S63.py`** (S63) — Phase 2 sanity + audit driver. Adapt the structure for Rules 25/26/27 audit (much shorter since there's no per-rule shipped attribution to cross-check beyond the v52 ensemble).
> 6. **`data/session_60/61/62/63_candidate_results.json`** — full results, T1/T2/T3 verdicts.
> 7. **`SESSION_60_A_HIGH_CATALOG.md`–`SESSION_63_J_HIGH_CATALOG.md`** — A, K, Q, J catalog pages. Structure templates for S64.
> 8. **From S59:** `data/drill_ho_v44_per_hand_structural.parquet` (15 MB) — per-hand v44 residual structure with cell tags. **Still the foundation for catalog work in S64+.**
> 9. **From S58:** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` — per-max-rank × per-cell oracle TOP/BOT/MID profile. Includes T/9/8 rows.

> **📓 METHODOLOGY (Session 64+):**
> - **Threshold definitions (unchanged from S60/S61/S62/S63):**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure between v52 and oracle ceiling within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (use existing 6-cell scheme):** JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER. Defined in `drill_high_only_v44_deepdive.cell_for_hand`. **Note:** at T/9/8, JOINT_HIGH and JOINT_MED are likely empty (since max non-max rank is ≤ 9), so cells reduce to JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER.
> - **Always cross-check shipped-lift attribution.** S63 lesson: CURRENT_PHASE's rolled-up "shipped lift per rule" table can be wrong; always reproduce against the immediate predecessor strategy and verify against the original session-end report.
> - **Decision-matrix percentages are partially recoverable at extreme rates but still below T1.** S63 lesson: at J's 76% drop-max rate, best-candidate capture jumps to 21.54% (vs A 5.45%, K 3.33%, Q 5.99%) — finally tracking surface growth. But still half the T1 bar. Expect T/9/8 to push capture further IF the rule structure aligns with the defensive baseline.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60+S61+S62+S63.)

> Updated: 2026-05-12 (Session 63 end — J-high catalog page complete; pivot to T/9/8-high)

---

## Headline state at end of Session 63 (UNCHANGED from S58/S59/S60/S61/S62)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v45_rule14_Ahigh_DS / v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains for A/K/Q. Rules 14/15/16 audited S60/S61/S62. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` / `v46_rule15_Khigh_DS.py` / `v47_rule16_Qhigh_DS.py` |
| v48_rules17_21_high_only_HIMID | v47 + Rules 17-21 HIMID. Rule 17 was audited S63 (J-high). | `analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py` |

**Per-category residuals (UNCHANGED from S58/S59/S60/S61/S62 since no production change in S63):**

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

**J-high catalog page produced in S63:** `SESSION_63_J_HIGH_CATALOG.md`. Verdict: all 5 active J-high cells labeled ML-only (JOINT_HIGH is empty at J). v44_dt is the best available approach on J-high's residual ($23.43/1000h WG remaining after v44's catch from v52's $47.46). The catalog methodology successfully **falsified the fourth hypothesis** — that J's 76% drop-max profile would yield Threshold-2 shippable rules. **Four-of-four is decisive empirical evidence** that the entire $755/1000h WG high_only residual is genuinely ML-only territory at this catalog's "one-sentence-statable" granularity.

**Existing high_only rules and their TRUE whole-population shipped lifts (corrected):**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S64 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 (v44_rule13→v45_rule14) | **AUDITED S60: ALL CELLS ML-ONLY.** Harness 0.2%. |
| K | Rule 15 | S51 | +$51 (v45→v46) | **AUDITED S61: ALL CELLS ML-ONLY.** Harness 0.7%. |
| Q | Rule 16 | S52 | +$19 (v46→v47) | **AUDITED S62: ALL CELLS ML-ONLY.** Harness 1.7%. |
| J | Rule 17 (alone) | S53 (inside v48) | **+$5.48 (v47→v48 on J-high)** — **NOT +$17 as previously listed** | **AUDITED S63: ALL CELLS ML-ONLY.** Harness 1.4% on v52 ensemble. |
| ensemble: J + defensive (K,Q,J,T,9,8,7) | Rule 17 + Rules 22-28 | S53 | **+$17 (v47→v52 across all high_only)** — the actual published S53 ship | **AUDITED S63 cross-check.** |
| T (defensive, always) | Rule 25 | S53 | +$8.24 J-equivalent on T-pop (v52 vs v47 on max=10) | **S64 TARGET.** |
| 9 (defensive, always) | Rule 26 | S53 | +$3.26 (v52 vs v47 on max=9) | **S64 TARGET.** |
| 8 (defensive, always) | Rule 27 | S53 | +$0.56 (v52 vs v47 on max=8) | **S64 TARGET.** |

**Two production tracks at end of S63 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h.

---

## Session 60+ catalog sequence (updated)

| Session | Max-rank focus | Existing rule | Population | $/1000h WG residual after v52 | Outcome |
|---|---|---|---|---:|---|
| **60** | A-high | Rule 14 | 660,660 (53.8%) | $281.2 (vs oracle); $182.5 (vs v44) | **NULL — all cells ML-only** |
| **61** | K-high | Rule 15 | 330,330 (26.9%) | $176.4 (vs oracle); $110.9 (vs v44) | **NULL — all cells ML-only** |
| **62** | Q-high | Rule 16 | 150,150 (12.2%) | $93.77 (vs oracle); $55.24 (vs v44) | **NULL — all cells ML-only** |
| **63** | **J-high** | **Rule 17 + Rule 24** | **60,060 (4.9%)** | **$47.46 (vs oracle); $23.43 (vs v44)** | **NULL — all cells ML-only** |
| 64 | T/9/8 combined | Rule 25/26/27 (always defensive) | 25,740 (2.1%) | TBD | TBD |
| 65 | Aggregate + cross-cell rules | All | All high_only | Synthesis | Final catalog |

Four consecutive max-ranks (A, K, Q, J) have now produced ALL-T3 verdicts. The structural opportunity (drop-max rate) has grown monotonically (6% → 34% → 52% → 76%) and best-candidate capture finally tracked it at J (21.54% from the 3–6% plateau at A/K/Q). **The hypothesis that high_only's residual is genuinely non-rule-shaped at the catalog granularity is now backed by four independent falsifications across a 12.7× range of drop-max opportunity.** If S64 produces a fifth ML-only verdict at T/9/8, the case is effectively closed for the entire high_only zone.

---

## Resume Prompt (Session 64 — T/9/8-high catalog audit)

```
Resume Session 64 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S63 — J-high NULL; T/9/8 next)
- DECISIONS_LOG.md (latest: Decision 098 — S63 J-high catalog NULL +
  Rule 17 +$17 attribution correction)
- SESSION_60_A_HIGH_CATALOG.md, SESSION_61_K_HIGH_CATALOG.md,
  SESSION_62_Q_HIGH_CATALOG.md, and SESSION_63_J_HIGH_CATALOG.md
  (the first four pages of HIGH_ONLY_RULE_CATALOG.md and the templates
  for T/9/8 pages — but note the structural inversion at T/9/8)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (oracle decisions per max × cell;
  includes T/9/8 rows)
- analysis/scripts/test_rule_catalog.py (the validated harness — reuse verbatim)
- analysis/scripts/sanity_v52_vs_v47_high_only.py (S63 cross-check —
  reuse the per-max-rank decomposition template)
- analysis/scripts/strategy_v52_full_high_only_handler.py (current v52 chain;
  T/9/8 path is Rules 25/26/27 always-defensive)
- analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py (predecessor —
  fires HIMID for J/T/9/8/7-high; for T/9/8 was SUPERSEDED by v52's defensive)

State (end of Session 63):
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- A-high, K-high, Q-high, J-high catalog pages produced S60-S63.
- Harness validated FOUR times: Rule 14 (0.2% S60), Rule 15 (0.7% S61),
  Rule 16 (1.7% S62), v52 ensemble (1.4% S63).
- S63 found and corrected the "Rule 17 = +$17" attribution: that's the
  v52 TOTAL over v47, not Rule 17 alone (which is +$5.48 on J-high).
- All 7 J-high candidates tested fell below Threshold 1.
- C_J1 (drop J low top + DSms) is biggest single-candidate WG lift across
  S60-S63 at +$6.44/1000h WG — exceeds T2's $5 raw bar but misses T1's
  40% gap-closure bar at 21.54%.
- T/9/8-high structural inversion: v52 ALREADY drops max by default
  (Rules 25/26/27 always-defensive). Candidates must explore lowest-on-top
  tiebreaker / DS-vs-SS bot preference / mid_high quality gates rather
  than max-on-top alternatives.

USER DIRECTIVE (S59-S63 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- Build the catalog over 5–6 sessions; A, K, Q, J pages produced S60-S63.

DIRECTION FOR SESSION 64 (T/9/8 combined catalog audit):

5-PHASE PLAN — adapted shape (NOT a copy of S63):

Phase 1 — Build candidates_T98_high_S64.py FROM SCRATCH. NOT a copy of
candidates_J_high_S63.py (which assumed max-on-top baseline). T/9/8
candidates target lowest-on-top tiebreaker refinements and DS/SS bot
preference gates. Likely need new enumeration helpers for lowest-on-top
configs (vs candidates_K_high_S61's max-on-top helpers).

Phase 2 — Cross-check Rules 25/26/27 lift via v52 vs v47 by max_rank
(reuse the S63 cross-check pattern). Expected: T ~+$8, 9 ~+$3, 8 ~+$0.6
(from S63's sanity_v52_vs_v47 output). Then audit v52 cell-by-cell on
max ∈ {10, 9, 8}. Note: JOINT_HIGH and likely JOINT_MED are empty.

Phase 3 — Propose 5–6 candidates targeting lowest-on-top refinements
and DS-vs-SS bot preference.

Phase 4 — Test each candidate via test_rule_on_cell with baseline=v52.
Apply T1/T2/T3 thresholds.

Phase 5 — Write SESSION_64_T98_HIGH_CATALOG.md. Address all three
max-ranks in one document. If at least one candidate clears T2
(vanishingly unlikely): draft strategy_v53. Otherwise label cells
ML-only.

ACCEPTANCE for Session 64:
- v52's T/9/8 contribution sanity-checked to within ±10% via
  sanity_v52_vs_v47_high_only.py decomposition.
- All cells audited at T, 9, 8.
- At least 5 T/9/8-specific candidates tested.
- Either at least one T2-shipping rule OR honest ML-only labeling
  for all leaky T/9/8 cells.
- SESSION_64_T98_HIGH_CATALOG.md produced.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- PYTHONUNBUFFERED=1 or python3 -u for long scripts.
- Reuse data/drill_ho_v44_per_hand_structural.parquet for cell tags.
- Reuse data/oracle_grid_full_realistic_n200.bin for EV evaluation.
- T/9/8 candidates are NOT a copy-template from J — design fresh.
- Treat S58 decision-matrix percentages as upper bounds on
  rule-recoverable EV; S63 lesson: capture can finally track surface
  growth at extreme drop-max rates, but T1 (40% gap-closure) bar holds.
- Cross-check shipped-lift attribution against original session-end
  reports, not rolled-up tables (S63 lesson).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
