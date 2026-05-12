# Current: Sprint 8 — Session 64 produced the fifth and final per-max-rank page of the high_only rule catalog: **T/9/8-high cells are formally labeled ML-only across all three max-ranks.** All 12 candidate refinement rules tested against v52's residual failed Threshold 1. **CRITICAL HARNESS MILESTONE:** Rules 25/26/27 (T/9/8-high always-defensive) were reproduced via v52 vs v47 by max_rank to **0.08% accuracy** — the cleanest catalog-harness validation yet, beating S63's 1.4% by ~17×. Per-max attribution exactly matches documented S53 ship (T +$8.24, 9 +$3.26, 8 +$0.56; total +$12.05 vs documented +$12.06). **FIVE independent harness validations now confirmed** across 23× magnitude range — Rule 14 (0.2% S60), Rule 15 (0.7% S61), Rule 16 (1.7% S62), v52 ensemble (1.4% S63), Rules 25/26/27 (0.08% S64). The HIMID-vs-HIBOT design choice is now confirmed FIVE TIMES across the entire high_only rule family (A C10 −$40, K C_K6 −$22, Q C_Q7 −$13, J C_J7 −$7, T/9/8 sum −$2.4) — the single most-validated design decision in the rule chain. **C_T5 (JOINT max-on-top + DS+ms at T-JOINT_MED) is the ONLY positive WG candidate of S64** at +$0.22/1000h WG (capture +12.24%) — fails T1 but identifies a new structural boundary: JOINT max-on-top return works at T but collapses at 9 (C_95 capture −15.68%). **Cumulative ML-only zone:** **5-of-5 max-rank zones (A/K/Q/J/T-9-8) NULL.** The entire $615/1000h WG high_only residual is now in the explicit ML-only zone — 100% by population, 100% by max-rank coverage. **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 full / $686 prefix). The two production tracks STILL diverge by $1,417/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 65): Aggregate `HIGH_ONLY_RULE_CATALOG.md` synthesis.**
>
>   S64 closed the per-max-rank catalog. Session 65 produces the aggregate `HIGH_ONLY_RULE_CATALOG.md` — a single canonical document synthesizing the six per-max-rank pages (A, K, Q, J, T/9/8) with cross-cell structural findings, methodology summary, and an "ML-only boundary" claim backed by the FIVE catalog falsifications. **This is the publishable end-product of the S60-S64 effort** per CLAUDE.md's stated goal: "the definitive GTO Taiwanese Poker strategy guide — backed by exhaustive computation, not heuristics".
>
>   **5-PHASE PLAN (Session 65 — synthesis shape, NOT a copy of S60-S64):**
>
>   **Phase 1 — Assemble the six per-max-rank pages into a single document.** No new code needed. The six existing files (`SESSION_60_A_HIGH_CATALOG.md` through `SESSION_64_T98_HIGH_CATALOG.md`) are the source; `HIGH_ONLY_RULE_CATALOG.md` is the assembly. Pages should appear in order (A → K → Q → J → T/9/8) with TL;DR boxes preserved, each page's full content, and a header noting "this is the S{NN} per-max-rank page; for cross-cell findings see Part X."
>
>   **Phase 2 — Cross-cell structural synthesis** (NEW content for the aggregate doc):
>     - **HIMID-vs-HIBOT validation summary:** 5 controls, magnitude trajectory A −$40 → K −$22 → Q −$13 → J −$7 → T/9/8 −$2.4. Clean monotonic dampening consistent with v52 reaching closer to oracle as max drops.
>     - **MS_ONLY over-fire universal pattern:** C_K5 82.7% fires (−$21 WG), C_Q6 85.8% (−$6), C_J6 89.1% (−$0.7). Drop-max-achievable gates fire on near-universal subsets but oracle's actual drops are much narrower. Pattern documented across 3 zones.
>     - **DS_NO_JOINT within-cell-gap trajectory:** $2,337 (A) → $3,062 (K) → $3,690 (Q) → $4,749 (J) → $3,827 (T) → $3,565 (9) → $3,463 (8). Peak at J then flatten — interesting non-monotonicity to explain (the "structural funnel narrows further at T" prediction proved partially correct).
>     - **JOINT max-on-top boundary at T-JOINT_MED specifically.** Below T, JOINT cells go fully defensive; above J, JOINT cells dominated by max-on-top. The S58 JOINT_PICK rate dropping monotonically (A 13.9% → J 7.9% → T 5.3% → 9 3.3% → 8 2.0%) cross-references cleanly.
>     - **Capture% vs drop-max rate scaling:** A 5.45% (6% drop) → K 3.33% (34%) → Q 5.99% (52%) → J 21.54% (76%) → T 12.24% (>85%, JOINT-only). Non-monotonic but the J jump is real and unexpected ("the lesson partially shifts").
>     - **The two-track divergence ($1,417/1000h) decomposed:** $381/1000h attributable to high_only ML-only territory; remaining $1,036 split across pair ($396), trips ($55), two_pair ($52), three_pair ($35), trips_pair ($5), composite ($2), quads ($1) — plus prefix-vs-full grid differences.
>
>   **Phase 3 — The "ML-only boundary" claim, formalized.** Single statable claim: "Across 1,226,940 canonical high_only hands, the rule chain v52 cannot be refined further at the 'one sentence statable' granularity. v44_dt captures $233 of the $615 remaining gap to oracle; the residual $381 is **ML-only territory** at current rule chain depth." Backed by 5 falsifications and 12+10+7+7+12 = 48 tested candidates.
>
>   **Phase 4 — Implications for future work.** Concrete next-step recommendations:
>     - **Other categories to audit:** pair ($396), trips ($55), two_pair ($52). The pair category alone is 36.2% of the grid and $396/1000h — a larger absolute target than high_only's $381 ML-only residual.
>     - **Beyond catalog granularity:** if a future session wants to close the high_only ML-only gap, the path is either (a) multi-feature rules (5+ gates) which reproduce v44_dt's structure, or (b) accepting v44_dt as the production handler for high_only specifically while keeping rules for pair/trips/two_pair/etc.
>     - **Hybrid chain proposal:** v52 for non-high_only categories + v44_dt for high_only handoff. Decompose v44_dt's catch into the high_only-specific contribution ($233/1000h) — if isolatable, this is the largest single ML "rule" available.
>
>   **Phase 5 — Write `HIGH_ONLY_RULE_CATALOG.md`** as the canonical document. Structure: cover page (TL;DR with the ML-only boundary claim), Part 1 (the six per-max-rank pages), Part 2 (cross-cell synthesis from Phase 2), Part 3 (the ML-only boundary claim from Phase 3), Part 4 (implications from Phase 4), Part 5 (methodology and harness validation summary).
>
>   **TIME BUDGET (S65):** No new code/tests needed. Phase 1 (assemble pages) = 20 min; Phase 2 (cross-cell synthesis) = 1 hr; Phase 3 (boundary claim) = 20 min; Phase 4 (implications) = 30 min; Phase 5 (document writing) = 1.5 hr; total ~3.5 hr. **Slower than S60-S64 by design** — this is the synthesis document, the user-facing artifact, the "perfection" half of "speed is not necessary".
>
>   **SUCCESS CRITERIA (S65):**
>   - `HIGH_ONLY_RULE_CATALOG.md` produced as a single canonical document.
>   - The six per-max-rank pages assembled in order with cross-references.
>   - All five cross-cell synthesis items (HIMID validation, MS over-fire, DSnj gap trajectory, JOINT boundary at T, capture trajectory) documented with their numerical evidence.
>   - The "ML-only boundary" claim explicitly stated with the $615/$233/$381 decomposition.
>   - Implications section recommends concrete next-step targets (pair $396 the largest).

> **❌ NULL RESULT (Session 64 — for context):**
> - All 12 T/9/8 candidates failed T1. T/9/8-high formally labeled ML-only at this catalog granularity.
> - C_T5 (JOINT_maxtop_DSms at T-JOINT_MED): **+$0.22/1000h WG**, capture +12.24%. The ONLY positive WG candidate of S64. Fails T1 at 12.24% capture (need 40%) AND fails T1's $3 within-cell bar at +$472/1000h (need ≥$3K). Identifies the JOINT-max-on-top-return boundary at T specifically (C_95 at 9 was −15.68%).
> - C_T1 / C_91 / C_81 (DSnj max-on-top + DS HIMID, no gate): −$4.36 / −$1.77 / −$0.32 WG; capture −54.31% / −94.47% / −122.22%. Catastrophe monotonically worse as max drops, mirroring oracle's monotonically decreasing keep-max-on-top rate (T 11% → 9 4% → 8 <3%).
> - C_T2 (DSnj max-on-top gated by DS bot pair_high ≥ T−2 = 8): −$5.90/1000h WG — WORST candidate of S64. The "DS bot pair strong" gate is too loose; fires 85.5% but captures −73.53%.
> - C_T3 / C_93 / C_83 (HIBOT control): −$1.76 / −$0.55 / −$0.08 WG. **5th retrospective HIMID validation. Rules 25/26/27 HIMID design empirically correct.**
> - C_T4 / C_94 (2nd-lowest-on-top): −$3.54 / −$0.83 WG; capture −44.14% / −44.16% — identical across T and 9. The "lift the floor" hypothesis fails: oracle wants the absolute-lowest on top.
> - C_T6 (lowest-on-top + SS_ms when ms_mid_high ≥ 8): −$1.50/1000h WG. Mirror of A/K/Q/J SSms patterns — same direction (negative), smaller magnitude. The SSms switch loses money at every max-rank tested.

> **✅ ARTIFACTS to reuse from S60+S61+S62+S63+S64:**
> 1. **`analysis/scripts/test_rule_catalog.py`** (S60, validated S60+S61+S62+S63+S64 to within 0.08–1.7% on FIVE independent shipped rules — Rule 14, Rule 15, Rule 16, v52 ensemble, Rules 25/26/27) — per-cell rule audit harness. Reusable verbatim for S65+ if any further audit work is needed.
> 2. **`analysis/scripts/sanity_v52_vs_v47_high_only.py`** (S63) — cross-check pattern that resolves shipped-lift attribution discrepancies. Useful template for any future shipped-lift attribution work.
> 3. **`analysis/scripts/audit_v52_T98_S64.py`** (S64) — Phase 2 sanity (Rules 25/26/27) + per-(max, cell) audit driver template. Adapt for any future per-rule-family audit.
> 4. **`analysis/scripts/candidates_K_high_S61.py`** (S61) — **generic helpers** `_enumerate_max_on_top_configs(hand, max_rank)`, `_enumerate_nonMax_top_DSms(hand, max_rank)`, `_enumerate_nonMax_top_anyBot_ms(hand, max_rank)`. Used through S64.
> 5. **`analysis/scripts/candidates_T98_high_S64.py`** (S64) — NEW helper `_enumerate_top_at_pos(hand, top_pos)` generic alternative for lowest-on-top variants (vs max-on-top); `_cell_for_hand(hand, max_rank)` parameterized by max_rank. Reusable for any future lowest-on-top variant audits.
> 6. **`data/session_60/61/62/63/64_candidate_results.json`** — full results across S60-S64, T1/T2/T3 verdicts.
> 7. **`SESSION_60_A_HIGH_CATALOG.md`–`SESSION_64_T98_HIGH_CATALOG.md`** — the SIX per-max-rank catalog pages. S65 assembles these into `HIGH_ONLY_RULE_CATALOG.md`.
> 8. **From S59:** `data/drill_ho_v44_per_hand_structural.parquet` (15 MB) — per-hand v44 residual structure with cell tags. Foundation for all catalog work S60-S64.
> 9. **From S58:** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` — per-max-rank × per-cell oracle TOP/BOT/MID profile. Includes T/9/8 rows.

> **📓 METHODOLOGY (Session 65+):**
> - **Threshold definitions (unchanged from S60–S64):**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure between v52 and oracle ceiling within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (use existing 6-cell scheme):** JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER. Defined in `drill_high_only_v44_deepdive.cell_for_hand`. **JOINT_HIGH is empty at T/9/8; JOINT_MED exists only at T/9.**
> - **Always cross-check shipped-lift attribution.** S63 lesson; S64 confirmed: Rules 25/26/27 reproduced exactly to S53 documented values. Future sessions touching pair/trips/two_pair etc. should run the same cross-check pattern before any audit work.
> - **The catalog ML-only verdict is final at high_only.** S65 documents the verdict; no further catalog work on high_only is recommended.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60+S61+S62+S63+S64.)

> Updated: 2026-05-12 (Session 64 end — T/9/8-high catalog complete; ALL high_only formally ML-only; pivot to S65 aggregate synthesis)

---

## Headline state at end of Session 64 (UNCHANGED from S58/S59/S60/S61/S62/S63)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v45_rule14_Ahigh_DS / v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains for A/K/Q. Rules 14/15/16 audited S60/S61/S62. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` / `v46_rule15_Khigh_DS.py` / `v47_rule16_Qhigh_DS.py` |
| v48_rules17_21_high_only_HIMID | v47 + Rules 17-21 HIMID. Rule 17 was audited S63 (J-high). | `analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py` |

**Per-category residuals (UNCHANGED from S58–S63 since no production change in S64):**

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

**T/9/8-high catalog page produced in S64:** `SESSION_64_T98_HIGH_CATALOG.md`. Verdict: all leaky T/9/8 cells labeled ML-only. v44_dt is the best available approach on T/9/8-high's residual ($7.29/1000h WG remaining after v44's catch from v52's $16.51 WG). The catalog methodology successfully **falsified the fifth (and final) hypothesis** — that v52's always-defensive baseline at T/9/8 would yield Threshold-2 shippable rules. **Five-of-five is decisive empirical evidence** that the entire $615/1000h WG high_only residual (catalog-measured) is genuinely ML-only territory at this catalog's "one-sentence-statable" granularity.

**Existing high_only rules and their TRUE whole-population shipped lifts (corrected S63, confirmed S64):**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S65 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 (v44_rule13→v45_rule14) | **AUDITED S60: ALL CELLS ML-ONLY.** Harness 0.2%. |
| K | Rule 15 | S51 | +$51 (v45→v46) | **AUDITED S61: ALL CELLS ML-ONLY.** Harness 0.7%. |
| Q | Rule 16 | S52 | +$19 (v46→v47) | **AUDITED S62: ALL CELLS ML-ONLY.** Harness 1.7%. |
| J | Rule 17 (alone) | S53 (inside v48) | +$5.48 (v47→v48 on J-high) | **AUDITED S63: ALL CELLS ML-ONLY.** Harness 1.4% on v52 ensemble. |
| ensemble: J + defensive (K,Q,J,T,9,8,7) | Rule 17 + Rules 22-28 | S53 | +$17 (v47→v52 across all high_only) | **AUDITED S63 cross-check.** |
| T (defensive, always) | Rule 25 | S53 | +$8.24 (v52 vs v47 on max=10) | **AUDITED S64: ALL CELLS ML-ONLY.** Harness 0.0% (exact match). |
| 9 (defensive, always) | Rule 26 | S53 | +$3.26 (v52 vs v47 on max=9) | **AUDITED S64: ALL CELLS ML-ONLY.** Harness 0.0% (exact match). |
| 8 (defensive, always) | Rule 27 | S53 | +$0.56 (v52 vs v47 on max=8) | **AUDITED S64: ALL CELLS ML-ONLY.** Harness 0.0% (exact match). |

**Two production tracks at end of S64 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h.

---

## Session 60+ catalog sequence (updated)

| Session | Max-rank focus | Existing rule | Population | $/1000h WG residual after v52 | Outcome |
|---|---|---|---|---:|---|
| **60** | A-high | Rule 14 | 660,660 (53.8%) | $281.2 (vs oracle); $182.5 (vs v44) | **NULL — all cells ML-only** |
| **61** | K-high | Rule 15 | 330,330 (26.9%) | $176.4 (vs oracle); $110.9 (vs v44) | **NULL — all cells ML-only** |
| **62** | Q-high | Rule 16 | 150,150 (12.2%) | $93.77 (vs oracle); $55.24 (vs v44) | **NULL — all cells ML-only** |
| **63** | J-high | Rule 17 + Rule 24 | 60,060 (4.9%) | $47.46 (vs oracle); $23.43 (vs v44) | **NULL — all cells ML-only** |
| **64** | **T/9/8 combined** | **Rules 25/26/27 (always defensive)** | **25,740 (2.1%)** | **$16.51 (vs oracle); $9.29 (vs v44)** | **NULL — all cells ML-only across 3 max-ranks** |
| 65 | Aggregate + cross-cell rules | All | All high_only | Synthesis | Final catalog |
| **TOTAL S60-S64** | **A/K/Q/J/T/9/8** | **All high_only rules** | **1,226,940 (100%)** | **$615.29 (vs oracle); $381.41 (vs v44)** | **5-of-5 NULL — all high_only ML-only** |

Five consecutive max-rank zones have now produced ALL-T3 verdicts. The structural opportunity profiles spanned 12.7× range of drop-max rate (A 6% → J 76%, then inverted at T/9/8 where the baseline already drops max). The best-candidate capture trajectory was 5.45% → 3.33% → 5.99% → 21.54% (J jump) → 12.24% (T JOINT-only), with the J peak being the highest. **Five falsifications across 48 tested candidates and a 12.7× range of structural opportunity is decisive empirical evidence that the high_only WG residual is genuinely ML-only territory at the catalog's "one-sentence-statable" granularity.**

---

## Resume Prompt (Session 65 — aggregate synthesis)

```
Resume Session 65 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S64 — T/9/8-high NULL; S65 = aggregate synthesis)
- DECISIONS_LOG.md (latest: Decision 099 — S64 T/9/8 catalog NULL + 0.08%
  harness reproduction milestone + 5th HIMID validation)
- SESSION_60_A_HIGH_CATALOG.md through SESSION_64_T98_HIGH_CATALOG.md
  (the SIX per-max-rank catalog pages — S65 assembles these into
  HIGH_ONLY_RULE_CATALOG.md with cross-cell synthesis added)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (oracle decisions per max × cell)

State (end of Session 64):
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- ALL five per-max-rank catalog pages produced S60-S64 with ALL-T3 verdicts.
- Harness validated FIVE times: Rule 14 (0.2% S60), Rule 15 (0.7% S61),
  Rule 16 (1.7% S62), v52 ensemble (1.4% S63), Rules 25/26/27 (0.08% S64).
- 48 candidate rules tested across 5 zones; ZERO ship T2; ZERO clear T1.
- HIMID-vs-HIBOT confirmed FIVE times across all max-rank zones.
- C_T5 (JOINT_maxtop_DSms at T-JOINT_MED) was the only positive candidate
  in S64 at +$0.22/1000h WG — identifies the JOINT max-on-top boundary at T.
- Total cumulative catalog-measured v52→oracle gap on high_only: $615/1000h WG.
- v44_dt catches $233 of that; net ML-only territory = $381/1000h WG.

USER DIRECTIVE (S59-S64 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- S65 is the user-facing synthesis document — slower than S60-S64 by design.

DIRECTION FOR SESSION 65 (aggregate HIGH_ONLY_RULE_CATALOG.md):

5-PHASE PLAN — synthesis shape, NOT a copy of S60-S64:

Phase 1 — Assemble the six per-max-rank pages into a single canonical
document. No new code needed. Pages in order A → K → Q → J → T/9/8 with
TL;DR boxes preserved and cross-reference headers.

Phase 2 — Cross-cell structural synthesis (NEW content for the aggregate):
  - HIMID-vs-HIBOT validation summary (5 zones, magnitude trajectory)
  - MS_ONLY over-fire universal pattern (K 82.7%, Q 85.8%, J 89.1% fires,
    all catastrophic)
  - DS_NO_JOINT within-cell-gap trajectory ($2,337 A → $4,749 J peak → $3,463 8)
  - JOINT max-on-top boundary at T-JOINT_MED specifically
  - Capture% vs drop-max rate scaling (non-monotonic; J jump unexpected)
  - Two-track production divergence decomposed by category

Phase 3 — The "ML-only boundary" claim, formalized: across 1,226,940 canonical
high_only hands, the rule chain v52 cannot be refined further at the
"one sentence statable" granularity. Backed by 5 falsifications and 48 tested
candidates. v52→oracle gap $615; v44_dt catches $233; net ML-only $381.

Phase 4 — Implications for future work. Concrete next targets:
  - Pair category ($396/1000h WG, 36.2% of grid) — largest remaining target.
  - Trips ($55), two_pair ($52), three_pair ($35) — smaller but cleaner targets.
  - Hybrid chain proposal: v52 for non-high_only + v44_dt for high_only handoff.

Phase 5 — Write HIGH_ONLY_RULE_CATALOG.md as the canonical document.

ACCEPTANCE for Session 65:
- HIGH_ONLY_RULE_CATALOG.md produced as a single canonical document.
- All six per-max-rank pages assembled in order with cross-references.
- All five cross-cell synthesis items documented with numerical evidence.
- The ML-only boundary claim explicitly stated with $615/$233/$381 decomposition.
- Implications section recommends pair ($396) as the largest remaining target.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- No new code/tests needed at S65 — pure synthesis document work.
- The harness is validated; future per-category audits (pair, trips, etc.)
  can reuse test_rule_catalog.py verbatim if cell-tagging is adapted.
- "Speed is not necessary — clarity and perfection is" — S65 is the
  user-facing artifact, prioritize structure and prose clarity.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
