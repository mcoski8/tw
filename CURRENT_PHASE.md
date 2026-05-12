# Current: Sprint 8 — Session 62 produced the third page of the high_only rule catalog: **Q-high cells are formally labeled ML-only.** All 7 candidate refinement rules tested against Rule 16's residual failed Threshold 1, despite Q-high having the most aggressive drop-max profile of all zones tested so far (oracle drops Q off top 52% in DSnj vs K 34%, A 6%). The harness reproduced Rule 16's documented +$19/1000h shipped lift to **1.7% accuracy** ($18.67 vs $19) — **third independent reproduction** after Rule 14 (0.2%, S60) and Rule 15 (0.7%, S61). The methodology lesson now generalizes monotonically across the 6%→52% drop-max range: best-candidate capture barely shifts (5.45% A → 3.33% K → 5.99% Q) despite underlying drop-max opportunity growing 8.7×. C_Q7 (HIBOT control) shipped −$13.07/1000h WG — third retrospective validation that Rule 14/15/16's HIMID design is empirically correct. Two micro-positive candidates (C_Q1 drop_Q_low_top +$3.33; C_Q4 top=2 surgical +$3.48) but combined ($+6.81/1000h WG gross with overlap) still under T2's $5/1000h bar. **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 full / $686 prefix). The two production tracks STILL diverge by $1,417/1000h. **Three-quarters of high_only's WG residual ($531 of $755) is now formally in the ML-only zone.**

> **🎯 IMMEDIATE NEXT ACTION (Session 63): J-high cell-by-cell audit + candidates.**
>
>   J-high is the right next zone: (a) 60,060 hands = 4.9% of high_only, fourth-largest after A, K, Q; (b) Rule 17 (S53, J-high HIMID, in v52) is +$17/1000h whole-grid when shipped (slightly smaller than Rule 16's +$19 → still real ground); (c) J has the **most aggressive drop-max profile of all zones tested so far** — oracle drops J off top **76% in DSnj** (vs Q 52%, K 34%, A 6%) and **44% even in JOINT_MED** (vs Q 20% in JOINT_HIGH). If the rule-saturation pattern from S60+S61+S62 generalizes (extremely likely given monotone confirmation across three max-ranks), J-high also lands all-T3 and the ML-only zone grows to ~$600/$755.
>
>   **STRUCTURAL TWIST at J-high:** unlike A/K/Q where v52's defensive triggers (Rule 22/23/24, s2 ≤ 8) never fire because the population has s2 > 8 by no-pair construction with distinct ranks, **at J-high the defensive Rule 24 (J-high s2 ≤ 8) DOES fire** for the J-with-low-secondary subset (estimated ~30% of J-high). So v52 on J-high is **TWO different code paths**: Rule 17 (offensive HIMID) when s2 > 8, Rule 24 (defensive lowest-on-top) when s2 ≤ 8. The cell audit must respect this split — sanity-check needs to reproduce Rule 17's shipped lift on the s2 > 8 subset, not the whole J-high zone.
>
>   **5-PHASE PLAN (Session 63 — same shape as S60/S61/S62):**
>
>   **Phase 1 — Reuse harness.** No new infrastructure required. `analysis/scripts/test_rule_catalog.py` is reusable verbatim. Copy `candidates_Q_high_S62.py` → `candidates_J_high_S63.py`, change `QUEEN = 12` → `JACK = 11` in the helpers' wrappers (`_is_J_high_no_pair`, `_cell_for_hand_J`), and re-import the generic helpers from `candidates_K_high_S61`.
>
>   **Phase 2 — Sanity check + audit Rule 17 cell-by-cell.** Sanity check: Rule 17 (in `strategy_v48_J_high_himid` if it exists separately, otherwise via direct extraction from v52's offensive J-high path) vs its pre-Rule-17 predecessor (`strategy_v47_rule16_Qhigh_DS`) on the J-high s2 > 8 subset. Expected total whole-grid lift ≈ +$17/1000h (S53 ship); acceptance window $15.30–$18.70 (±10%). **First verify Rule 17 is the right strategy file** — it may be inlined into v52 only. If so, build a minimal `strategy_rule17_only.py` shim from v52's logic. Then audit v52 cell-by-cell on J-high: 6 cells (JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY). Expected dominant cell: J × DS_NO_JOINT (n=37,800 = 62.9% of J-high; S58 reported $18.75/1000h WG on v43; post-Rule-17 likely similar magnitude but with the defensive Rule 24 fire region carved out).
>
>   **Phase 3 — Propose J-high candidate refinements.** Same template as S62 with J-specific gating:
>     - C_J1: `rule_J_DSnj_drop_J_low_top_DSms` — In J × DSnj, drop J to top ≤ 7 + DS bot + ms_mid_high ≥ 9. (Mirror of C_K1/C_Q1; expected to fail with same pattern.)
>     - C_J2: `rule_J_DSnj_take_2top_DSms` — Surgical top=2 mirror of C_Q4 (oracle picks top=2 27% in J × DSnj per S58, vs Q's 15% — biggest surface yet).
>     - C_J3: `rule_J_DSnj_take_3top_DSms` — Surgical top=3 (oracle picks top=3 14% in J × DSnj — second biggest specific top after 2).
>     - C_J4: `rule_J_DSnj_drop_J_when_J_in_DSpair` — Mirror of C_K2/C_Q3 (S58 Obs 1: at J, JOINT rate when J-in-DSpair is 46.0% — strongest drop signal yet).
>     - C_J5: `rule_J_MSonly_drop_J` — Mirror of C_K5/C_Q6; expected catastrophic over-fire given Q/K precedent.
>     - C_J6: `rule_J_DSnj_HIBOT_tiebreaker` — Fourth retrospective HIMID validation.
>     - C_J7: `rule_J_DSnj_SSms_when_high` — Mirror of C_Q5; expected net-negative.
>   2–5 candidates per leaky cell, **cell-locally gated**.
>
>   **Phase 4 — Test each candidate via T1/T2/T3 thresholds.** Same definitions: T1 ≥40% gap closure within cell AND ≥+$3/1000h within-cell; T2 + ≥+$5/1000h whole-grid; T3 = no candidate clears T1.
>
>   **Phase 5 — Write `SESSION_63_J_HIGH_CATALOG.md`.** Same template as `SESSION_62_Q_HIGH_CATALOG.md`. If a T2-clearing rule emerges (very unlikely after three consecutive falsifications): draft `strategy_v53_J_high_handler.py` as `v52 + Rule 18` and grade vs v52 on full 6M grid (validating ZERO non-targeted regression). **Far more likely:** label all 6 cells ML-only and proceed.
>
>   **TIME BUDGET (S63):** Phase 1 (harness reuse) = 5 min; Phase 2 (sanity + audit on smaller 60K population) = 10 min; Phase 3 (candidates) = 30 min; Phase 4 (test 7 candidates) = 15 min; Phase 5 (catalog doc) = 25 min; total ~1.5 hr. Faster than S62 since infrastructure now stable.
>
>   **SUCCESS CRITERIA (S63):**
>   - Rule 17 audit completed; remaining J-high gap to oracle quantified per cell.
>   - At least 5 J-specific candidate rules tested.
>   - Either ship at least one refinement (T2; vanishingly unlikely) OR honestly label J-high cells ML-only (T3).
>   - `SESSION_63_J_HIGH_CATALOG.md` produced.

> **❌ NULL RESULT (Session 62 — for context):**
> - All 7 Q-high candidates failed T1. Q-high formally labeled ML-only at this catalog granularity.
> - C_Q1 (DSnj_drop_Q_low_top_DSms): +$3.33/1000h WG, capture +5.75%. Fires 37.2% — UNDER-fires relative to oracle's 52% drop rate, yet capture remains tiny. Most informative micro-positive.
> - C_Q2 (DSnj_take_Jtop_DSms): +$1.88/1000h WG, capture +3.24%. Surgical J-on-top tiny capture.
> - C_Q3 (DSnj_drop_Q_when_Q_in_DSpair): +$0.62/1000h WG, capture +1.06%. The S58 Obs 1 structural axis fires 41.5% but barely improves over v52 — gate over-fires.
> - C_Q4 (DSnj_drop_Q_to_2top_DSms): +$3.48/1000h WG, capture +5.99%. **Best Q-high candidate.** Targets oracle's 15% top=2 rate in Q × DSnj — bigger surface than K's C_K7 (top=2 at K, +$1.05).
> - C_Q5 (DSnj_SSms_when_high): −$2.02/1000h WG. Same negative pattern as C_K4 and A-high C2/C3.
> - C_Q6 (MSonly_drop_Q): −$6.06/1000h WG (catastrophic). Fires 85.8% — same over-fire pattern as C_K5 (82.7%) at K.
> - C_Q7 (DSnj_HIBOT_tiebreaker): −$13.07/1000h WG. **Third retrospective HIMID validation. Rule 16's design empirically correct.**

> **✅ ARTIFACTS to reuse from S60+S61+S62:**
> 1. **`analysis/scripts/test_rule_catalog.py`** (S60, validated S60+S61+S62 to within 0.2–1.7% on THREE independent shipped rules) — per-cell rule audit harness. Reusable verbatim for S63–S65.
> 2. **`analysis/scripts/candidates_K_high_S61.py`** (S61) — **generic helpers** `_enumerate_max_on_top_configs(hand, max_rank)`, `_enumerate_nonMax_top_DSms(hand, max_rank)`, `_enumerate_nonMax_top_anyBot_ms(hand, max_rank)`. **Import these directly into S63's candidates file**, like S62 did.
> 3. **`analysis/scripts/candidates_Q_high_S62.py`** (S62) — 7 Q-high candidates. Useful as template for `candidates_J_high_S63.py` (just swap `QUEEN = 12` → `JACK = 11` and adapt the rank thresholds for J's lower mid_high pool).
> 4. **`analysis/scripts/audit_rule16_S62.py`** (S62) — Phase 2 sanity + audit driver. Adapt to Rule 17 by substituting `strategy_v47_rule16_Qhigh_DS` → Rule 17 strategy and the predecessor.
> 5. **`analysis/scripts/test_K_high_candidates_S61.py` + `test_Q_high_candidates_S62.py`** — sweep drivers; copy-and-adapt for S63.
> 6. **`data/session_60_candidate_results.json` + `data/session_61_candidate_results.json` + `data/session_62_candidate_results.json`** — full results, T1/T2/T3 verdicts, full per-candidate metric breakdown.
> 7. **`SESSION_60_A_HIGH_CATALOG.md` + `SESSION_61_K_HIGH_CATALOG.md` + `SESSION_62_Q_HIGH_CATALOG.md`** — A, K, Q catalog pages. Templates for the J/T/9/8 catalog pages.
> 8. **From S59:** `data/drill_ho_v44_per_hand_structural.parquet` (15 MB) — per-hand v44 residual structure with cell tags. **Still the foundation for catalog work in S63+.**
> 9. **From S58:** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` — per-max-rank × per-cell oracle TOP/BOT/MID profile. Use as the "what should the rule do?" reference when designing candidate rules, BUT treat the percentages as upper bounds on rule-recoverable EV (per S60+S61+S62 lesson — re-confirmed monotonically across 6%→52% drop-max range).

> **📓 METHODOLOGY (Session 63+):**
> - **Threshold definitions (unchanged from S60/S61/S62):**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure between v52 and oracle ceiling within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (use existing 6-cell scheme):** JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER. Defined in `drill_high_only_v44_deepdive.cell_for_hand`.
> - **Always sanity-check the harness on the existing rule first.** Reproduce the rule's known shipped lift vs its pre-rule predecessor. For S63: Rule 17 (S53) vs `strategy_v47_rule16_Qhigh_DS` should yield ~+$17/1000h on J-high. ±10% acceptance window.
> - **Decision-matrix percentages are NOT directly recoverable.** S58's matrix says "oracle picks X q% in cell C" — this is what oracle achieves with FULL knowledge, not what a rule firing on "X is achievable" can recover. **Re-confirmed monotonically across THREE max-ranks: A 6%, K 34%, Q 52%.** Expect candidates to need TIGHT gating to clear thresholds.
> - **At J-high, account for Rule 24 defensive overlap.** Unlike A/K/Q where defensive rules never fire, at J-high about ~30% of hands have s2 ≤ 8 and Rule 24 fires (lowest-on-top + DS HIMID). The sanity check must reproduce Rule 17's shipped lift on the s2 > 8 subset only, OR the comparison must be carefully designed.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60+S61+S62.)
> - **Test candidates BOTH ways**: gate on cell predicate (cheap, exact), and gate on rule-pick-direction (e.g., "switch DS→SS only when SS_ms mid_high > DS bot pair_high AND DS bot pair is low"). The S60+S61+S62 candidate sets were probably under-gated.

> Updated: 2026-05-11 (Session 62 end — Q-high catalog page complete; pivot to J-high)

---

## Headline state at end of Session 62 (UNCHANGED from S58/S59/S60/S61)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v45_rule14_Ahigh_DS / v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains for A/K/Q. **Rules 14/15/16 audited S60/S61/S62. Rule 17 is the S63 audit target.** | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` / `v46_rule15_Khigh_DS.py` / `v47_rule16_Qhigh_DS.py` |

**Per-category residuals (UNCHANGED from S58/S59/S60/S61 since no production change in S62):**

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

**Q-high catalog page produced in S62:** `SESSION_62_Q_HIGH_CATALOG.md`. Verdict: all 6 Q-high cells labeled ML-only. v44_dt is the best available approach on Q-high's residual ($55.24/1000h WG remaining). The catalog methodology successfully **falsified the third hypothesis** — that Q's most aggressive drop-max profile (52%) would yield Threshold-2 shippable rules. **Three-of-three is now strong empirical evidence** that the entire $755/1000h WG high_only residual is genuinely ML-only territory at this catalog's "one-sentence-statable" granularity.

**Existing high_only rules and their whole-population shipped lifts:**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S63 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 | **AUDITED S60: ALL CELLS ML-ONLY.** Harness reproduces lift to 0.2%. |
| K | Rule 15 | S51 | +$51 | **AUDITED S61: ALL CELLS ML-ONLY.** Harness reproduces lift to 0.7%. |
| Q | Rule 16 | S52 | +$19 | **AUDITED S62: ALL CELLS ML-ONLY.** Harness reproduces lift to 1.7%. |
| J | Rule 17 | S53 | +$17 | **S63 TARGET.** Cell-level audit not yet done. Note Rule 24 defensive overlap. |
| T/9/8 (defensive) | Rule 25/26/27 / v52 | S53 | (~$10 combined) | Cell-level audit pending (S64). |

**Two production tracks at end of S62 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h.

---

## Session 60+ catalog sequence (updated)

| Session | Max-rank focus | Existing rule | Population | $/1000h WG residual after current rule | Outcome |
|---|---|---|---|---:|---|
| **60** | A-high | Rule 14 | 660,660 (53.8%) | $281.2 (vs oracle); $182.5 (vs v44) | **NULL — all cells ML-only** |
| **61** | K-high | Rule 15 | 330,330 (26.9%) | $176.4 (vs oracle); $110.9 (vs v44) | **NULL — all cells ML-only** |
| **62** | **Q-high** | **Rule 16** | **150,150 (12.2%)** | **$93.77 (vs oracle); $55.24 (vs v44)** | **NULL — all cells ML-only** |
| 63 | J-high | Rule 17 (HIMID branch) + Rule 24 (defensive) | 60,060 (4.9%) | TBD per Phase 2 audit | TBD |
| 64 | T/9/8 combined | Rule 25/26/27 (always defensive) | 25,740 (2.1%) | TBD | TBD |
| 65 | Aggregate + cross-cell rules | All | All high_only | Synthesis | Final catalog |

Three consecutive max-ranks (A, K, Q) have now produced ALL-T3 verdicts. The structural opportunity (drop-max rate) has grown monotonically (6% → 34% → 52%) yet best-candidate capture has stayed in the 3–6% range. **The hypothesis that high_only's residual is genuinely non-rule-shaped at the catalog granularity is now backed by three independent falsifications across an 8.7× range of drop-max opportunity.** If S63 produces a fourth ML-only verdict at J (where drop-max is 76%), the case is effectively closed.

---

## Resume Prompt (Session 63 — J-high catalog audit)

```
Resume Session 63 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S62 — Q-high NULL; J-high next)
- DECISIONS_LOG.md (latest: Decision 097 — S62 Q-high catalog NULL)
- SESSION_60_A_HIGH_CATALOG.md, SESSION_61_K_HIGH_CATALOG.md,
  and SESSION_62_Q_HIGH_CATALOG.md (the first three pages of
  HIGH_ONLY_RULE_CATALOG.md and the templates for J/T/9/8 pages)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (oracle decisions per max × cell)
- analysis/scripts/test_rule_catalog.py (the validated harness — reuse verbatim)
- analysis/scripts/candidates_Q_high_S62.py (template for candidates_J_high_S63.py;
  helpers already parameterized by max_rank, imported from candidates_K_high_S61)
- analysis/scripts/audit_rule16_S62.py (template for audit_rule17_S63.py)
- analysis/scripts/strategy_v52_full_high_only_handler.py (current v52 chain;
  J-high path is Rule 17 offensive + Rule 24 defensive)
- analysis/scripts/strategy_v47_rule16_Qhigh_DS.py (Rule 17's predecessor for
  sanity check)
- analysis/scripts/strategy_v44_dt.py (ML champion benchmark)

State (end of Session 62):
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- A-high catalog page produced S60: all 6 A-high cells labeled ML-only.
- K-high catalog page produced S61: all 6 K-high cells labeled ML-only.
- Q-high catalog page produced S62: all 6 Q-high cells labeled ML-only.
- Harness `test_rule_catalog.py` validated to 0.2% (S60 / Rule 14),
  0.7% (S61 / Rule 15), and 1.7% (S62 / Rule 16) — THREE independent
  reproductions of shipped lifts.
- All 7 Q-high candidates tested fell below Threshold 1.
- Methodology lesson re-confirmed at Q (52% drop-max): decision-matrix
  percentages overstate rule-recoverable EV across the entire
  6%→52% range tested so far.
- J-high structural opportunity: oracle drops max off top 76% in
  J × DSnj (vs Q 52%, K 34%, A 6%). MOST aggressive drop-max profile
  yet, but ALSO has Rule 24 defensive overlap (~30% of J-high has
  s2 ≤ 8, where v52 uses lowest-on-top instead of Rule 17 HIMID).

USER DIRECTIVE (S59-S62 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- Build the catalog over 5–6 sessions; A, K, Q pages produced S60-S62.

DIRECTION FOR SESSION 63 (J-high catalog audit + harness reuse):

5-PHASE PLAN — same shape as S60/S61/S62:

Phase 1 — Reuse harness. No new infrastructure. Copy candidates_Q_high_S62.py
to candidates_J_high_S63.py, swap QUEEN = 12 → JACK = 11.

Phase 2 — Sanity-check Rule 17 cell-by-cell on J-high. Expect harness to
reproduce Rule 17's documented +$17/1000h whole-grid shipped lift vs its
pre-Rule-17 predecessor (strategy_v47_rule16_Qhigh_DS), but the sanity
check must respect Rule 24's defensive fire region. Acceptance window:
$15.30–$18.70. If outside, investigate the Rule 17/Rule 24 split before
proceeding. Then audit v52 cell-by-cell on J-high. Identify leaky cells.

Phase 3 — Propose J-specific candidates. 7 candidates targeting J's
maximal drop-J profile (76% in DSnj).

Phase 4 — Test each candidate via test_rule_on_cell with baseline=v52.
Apply T1/T2/T3 thresholds.

Phase 5 — Write SESSION_63_J_HIGH_CATALOG.md (mirror of
SESSION_62_Q_HIGH_CATALOG.md). If at least one candidate clears T2
(vanishingly unlikely): draft strategy_v53_J_high_handler.py and grade
vs v52 on full 6M grid (validating ZERO non-targeted regression).

ACCEPTANCE for Session 63:
- Sanity check on Rule 17 + harness reproduces +$17/1000h ±10%.
- All 6 J-high cells audited; Rule 17 vs Rule 24 fire regions disambiguated.
- At least 5 J-specific candidates tested.
- Either at least one T2-shipping rule OR honest ML-only labeling
  for all leaky J-high cells.
- SESSION_63_J_HIGH_CATALOG.md produced.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- PYTHONUNBUFFERED=1 or python3 -u for long scripts.
- Reuse data/drill_ho_v44_per_hand_structural.parquet for cell tags.
- Reuse data/oracle_grid_full_realistic_n200.bin for EV evaluation.
- Don't propose candidates without first auditing the existing
  rule (Rule 17) for that cell.
- Treat S58 decision-matrix percentages as upper bounds on
  rule-recoverable EV, not direct targets (S60+S61+S62 lesson —
  three independent confirmations).
- At J-high, the s2 ≤ 8 defensive Rule 24 fire region is a structural
  twist not present at A/K/Q. Audit the s2 > 8 subset separately
  for the sanity check.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
