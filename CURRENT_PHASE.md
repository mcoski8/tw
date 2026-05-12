# Current: Sprint 8 — Session 65 produced the canonical **`HIGH_ONLY_RULE_CATALOG.md`** aggregate synthesis. The catalog is now CLOSED on high_only. Five consecutive max-rank zone audits (S60–S64) produced ALL-T3 verdicts across 43 candidate rules; the entire $615/1000h WG high_only residual is formally labeled ML-only at the catalog's "one-sentence-statable" granularity. v44_dt holds $381/1000h WG of exclusive territory beyond what catalog refinement reached. The aggregate document assembles the five per-max-rank pages and adds six cross-cell structural findings: HIMID is the single most-validated rule-chain decision (5 zones); MS_ONLY drop-max gates universally over-fire at >80%; DS_NO_JOINT within-cell gap peaks at J then flattens; JOINT max-on-top boundary is at T-JOINT_MED specifically; best-candidate-capture trajectory jumps unexpectedly at J (21.54%) before falling; the two-track production divergence ($1,417/1000h) decomposes to $381 in high_only ML-only zone (27%). The ML-only boundary claim is formalized with the $615/$233/$381 decomposition. **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 full / $686 prefix). The two production tracks STILL diverge by $1,417/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 66): Pivot to the pair category — the largest remaining target ($396/1000h WG, 36.2% of canonical-grid).**
>
>   With high_only catalog closed as ML-only, the next-largest absolute WG residual zone is **pair** (n=2,800,512, 36.2% share, v44 within-cat $1,097, whole-grid $396/1000h). This is **a larger absolute target than high_only's $381 ML-only residual** — meaning a successful catalog effort on pair would unlock more rule-chain value than completely closing high_only's ML-only gap. Per `HIGH_ONLY_RULE_CATALOG.md` Part 4.1.
>
>   **3-PHASE PLAN (Session 66 — pair decision matrix first, audit later):**
>
>   **Phase 1 — Build `PAIR_DECISION_MATRIX.md` analogous to S58.** No rule shipping. Goal: stratify pair hands by (pair_rank × pair-placement × ms_mid achievability × DS bot achievability) with sub-stratification by max non-pair rank. Output the oracle's TOP/BOT/MID profile and v44's mismatch class per (pair_rank, cell). Same shape as `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md`. Reuse `oracle_grid_full_realistic_n200.bin` + `v44_dt`. Time: ~3–4 hours including cell-tagging design.
>
>   **Phase 2 — Identify whether existing pair rules (Rules 7–11 in v52) are catalog-auditable.** v52 currently includes pair-handling rules from S46 (Rule 11 J-pair pair-to-bot DS, Decision 079) and earlier sessions. Build a per-(pair_rank, cell) audit similar to S60's Phase 2 to check whether the existing pair rule chain leaves substantial within-cell residual that human-statable refinements could close. If yes → proceed to Phase 3 candidate sweep. If no (existing rules already near-oracle within cells) → recommend pivot to trips or three_pair.
>
>   **Phase 3 — Decide on continuation.** Three outcomes:
>     - **Pair has shippable refinement headroom:** spawn S67–S70 catalog pass mirroring S60–S64 (one pair_rank zone per session, falsifications accumulate to `PAIR_RULE_CATALOG.md`).
>     - **Pair is ML-only at the matrix level:** the high_only catalog's boundary claim generalizes to a multi-category claim. Document as `PAIR_DECISION_MATRIX.md` + appendix to `HIGH_ONLY_RULE_CATALOG.md` Part 4. Pivot to trips (n=328,185, $55 WG, v44 within-cat $1,194 — smaller population, larger per-hand gap).
>     - **Hybrid chain (`HIGH_ONLY_RULE_CATALOG.md` Part 4.3) is more tractable:** isolate v44_dt's high_only-specific decision tree, benchmark v52-non-high_only + v44_dt-high_only on held-out subset, ship as v53 if zero non-targeted regression on the rest of the grid.
>
>   **TIME BUDGET (S66):** Phase 1 (build decision matrix) = 3–4 hr; Phase 2 (audit existing pair rules) = 1 hr; Phase 3 (decide continuation) = 30 min; total ~5 hr. **Slower than per-zone S60-S64 sessions** — Phase 1 is fresh design work, not a copy of S58 (pair's cell-tagging is structurally different from high_only's 6-cell scheme).
>
>   **ALTERNATIVE (if user prefers): the hybrid chain experiment (4.3).** This is implementationally cheaper than building the pair matrix (~1 hr) and could ship as v53 if the held-out non-targeted regression check passes. The trade-off: a hybrid chain commits production to v44_dt for high_only forever (or until a replacement ML champion ships), while the pair catalog opens new rule-chain headroom that may unlock multiple shippable rules. **Recommended order if pursuing both: Phase 1 of pair matrix FIRST** (information value before committing to hybrid), then hybrid experiment as Phase 2 if pair shows similar ML-only ceiling.
>
>   **SUCCESS CRITERIA (S66 — Phase 1 minimum):**
>   - `PAIR_DECISION_MATRIX.md` produced as a single canonical document analogous to `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md`.
>   - Per-(pair_rank × cell) v44 residual + oracle pick profile documented across all 13 pair ranks.
>   - Top-3 mismatch class per cell identified with $/1000h within-cell magnitude.
>   - Recommendation issued for S67+ direction (catalog sweep / pivot / hybrid).

> **✅ ARTIFACTS produced in S65:**
> 1. **`HIGH_ONLY_RULE_CATALOG.md`** — the canonical aggregate synthesis. Assembles S60-S64's five per-max-rank pages + adds six cross-cell findings + formalizes the ML-only boundary claim + recommends three concrete next-step paths.
> 2. **`DECISIONS_LOG.md`** — Decision 100 (S65 aggregate catalog + ML-only boundary claim).
> 3. **`CURRENT_PHASE.md`** — rewritten for S66 (this file).
> No new code/tests/data artifacts. Pure synthesis document work.

> **✅ ARTIFACTS preserved from S58+S59+S60+S61+S62+S63+S64 (reusable for S66+):**
> 1. **`analysis/scripts/test_rule_catalog.py`** (S60, validated S60+S61+S62+S63+S64 to <2% on FIVE independent shipped rules) — per-cell rule audit harness. **Structurally category-agnostic** — reusable for pair / trips / etc. once a new cell-tagging parquet is built.
> 2. **`analysis/scripts/sanity_v52_vs_v47_high_only.py`** (S63) — cross-check pattern for shipped-lift attribution.
> 3. **`analysis/scripts/audit_v52_T98_S64.py`** (S64) — Phase 2 sanity + per-(max, cell) audit driver template.
> 4. **`analysis/scripts/candidates_K_high_S61.py`** (S61) — generic helpers `_enumerate_max_on_top_configs(hand, max_rank)`, `_enumerate_nonMax_top_DSms`, `_enumerate_nonMax_top_anyBot_ms`.
> 5. **`analysis/scripts/candidates_T98_high_S64.py`** (S64) — generic `_enumerate_top_at_pos(hand, top_pos)` for lowest-on-top variants.
> 6. **`data/session_60/61/62/63/64_candidate_results.json`** — full per-candidate results across S60-S64.
> 7. **`SESSION_60_A_HIGH_CATALOG.md` – `SESSION_64_T98_HIGH_CATALOG.md`** — the five per-max-rank pages. Source-of-truth for per-zone numerical detail.
> 8. **`data/drill_ho_v44_per_hand_structural.parquet`** (S59) — per-hand v44 residual structure with cell tags. **High_only-specific** — a new parquet is needed for pair (S66 Phase 1 output).
> 9. **`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md`** — per-max-rank × per-cell oracle profile. **Template for S66's `PAIR_DECISION_MATRIX.md`.**

> **📓 METHODOLOGY (Session 66+):**
> - **Threshold definitions (carry over from S60–S64):**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (NEW for pair):** S58's 6-cell scheme (JOINT_HIGH/MED/LOW + DS_NO_JOINT + DS_NO_MAXTOP + MS_ONLY + NEITHER) is high_only-specific (assumes all 7 ranks distinct). Pair requires a fresh cell axis indexed on (pair_rank × pair-placement × ms_mid achievability × DS bot achievability), with sub-stratification by max non-pair rank. **Phase 1 of S66 is to design this taxonomy.**
> - **Always cross-check shipped-lift attribution.** S63 lesson; S64 confirmed: Rules 25/26/27 reproduced exactly to S53 documented values. Pair rule audits should run the same cross-check pattern before any candidate testing.
> - **Five-falsification methodology generalizes.** Each pair sub-zone gets one falsification attempt; ship verdicts accumulate to a canonical `PAIR_RULE_CATALOG.md` if rule space is rich enough.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60+S61+S62+S63+S64+S65.)

> Updated: 2026-05-12 (Session 65 end — HIGH_ONLY_RULE_CATALOG.md complete; ML-only boundary claim formalized; pivot to S66 pair category audit)

---

## Headline state at end of Session 65 (UNCHANGED from S58/S59/S60/S61/S62/S63/S64)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v45_rule14_Ahigh_DS / v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains for A/K/Q. Rules 14/15/16 audited S60/S61/S62. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` / `v46_rule15_Khigh_DS.py` / `v47_rule16_Qhigh_DS.py` |
| v48_rules17_21_high_only_HIMID | v47 + Rules 17-21 HIMID. Rule 17 was audited S63 (J-high). | `analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py` |

**Per-category residuals (UNCHANGED from S58–S64 since no production change in S65):**

| Category | n_hands | share | v44 within-cat | $/1000h whole-grid | Status |
|---|---:|---:|---:|---:|---|
| **high_only** | 1,226,940 | 40.4% | $1,868 | $755 | **CATALOG CLOSED S65 — ML-only at human granularity** |
| **pair** | 2,800,512 | 36.2% | $1,097 | $396 | **S66 IMMEDIATE TARGET (largest remaining)** |
| trips | 328,185 | 4.6% | $1,194 | $55 | Next-best target after pair |
| two_pair | 1,338,480 | 14.5% | $363 | $52 | Mid-priority |
| three_pair | 114,400 | 2.2% | $1,613 | $35 | Larger per-hand gap, smaller population |
| trips_pair | 171,600 | 1.8% | $281 | $5 | Already collapsed S55a |
| composite | 14,742 | 0.2% | $960 | $2 | Rounding-error scale |
| quads | 14,300 | 0.1% | $545 | $1 | Rounding-error scale |

**`HIGH_ONLY_RULE_CATALOG.md` produced in S65:** the canonical synthesis of S60-S64's five per-max-rank pages plus six cross-cell findings plus the formal ML-only boundary claim ($615 catalog v52→oracle gap / $233 v44 catch / $381 ML-only residual) plus implications for future work. The catalog methodology successfully **falsified five hypotheses across 43 tested candidates and a 12.7× range of structural opportunity** — decisive empirical evidence that the high_only residual is genuinely ML-only at the catalog's "one-sentence-statable" granularity.

**Existing high_only rules and their TRUE whole-population shipped lifts (corrected S63, confirmed S64, summarized S65):**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S66 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 (v44_rule13→v45_rule14) | AUDITED S60: ALL CELLS ML-ONLY. Harness 0.2%. |
| K | Rule 15 | S51 | +$51 (v45→v46) | AUDITED S61: ALL CELLS ML-ONLY. Harness 0.7%. |
| Q | Rule 16 | S52 | +$19 (v46→v47) | AUDITED S62: ALL CELLS ML-ONLY. Harness 1.7%. |
| J | Rule 17 (alone) | S53 (inside v48) | +$5.48 (v47→v48 on J-high) | AUDITED S63: ALL CELLS ML-ONLY. Harness 1.4% on v52 ensemble. |
| ensemble: J + defensive (K,Q,J,T,9,8,7) | Rule 17 + Rules 22-28 | S53 | +$17 (v47→v52 across all high_only) | AUDITED S63 cross-check. |
| T (defensive, always) | Rule 25 | S53 | +$8.24 (v52 vs v47 on max=10) | AUDITED S64: ALL CELLS ML-ONLY. Harness 0.0% (exact match). |
| 9 (defensive, always) | Rule 26 | S53 | +$3.26 (v52 vs v47 on max=9) | AUDITED S64: ALL CELLS ML-ONLY. Harness 0.0% (exact match). |
| 8 (defensive, always) | Rule 27 | S53 | +$0.56 (v52 vs v47 on max=8) | AUDITED S64: ALL CELLS ML-ONLY. Harness 0.0% (exact match). |

**Two production tracks at end of S65 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h. Of the $1,417 gap: $381/1000h (27%) is now formally in high_only ML-only territory per S65's catalog.

---

## Session 60+ catalog sequence (final, post-S65)

| Session | Max-rank focus | Existing rule | Population | $/1000h WG residual after v52 | Outcome |
|---|---|---|---|---:|---|
| **60** | A-high | Rule 14 | 660,660 (53.8%) | $281.2 (vs oracle); $182.5 (vs v44) | **NULL — all cells ML-only** |
| **61** | K-high | Rule 15 | 330,330 (26.9%) | $176.4 (vs oracle); $110.9 (vs v44) | **NULL — all cells ML-only** |
| **62** | Q-high | Rule 16 | 150,150 (12.2%) | $93.77 (vs oracle); $55.24 (vs v44) | **NULL — all cells ML-only** |
| **63** | J-high | Rule 17 + Rule 24 | 60,060 (4.9%) | $47.46 (vs oracle); $23.43 (vs v44) | **NULL — all cells ML-only** |
| **64** | T/9/8 combined | Rules 25/26/27 (always defensive) | 25,740 (2.1%) | $16.51 (vs oracle); $9.29 (vs v44) | **NULL — all cells ML-only across 3 max-ranks** |
| **65** | **Aggregate synthesis** | **All high_only rules** | **All high_only** | **Synthesis only** | **`HIGH_ONLY_RULE_CATALOG.md` produced; ML-only boundary claim formalized** |
| **TOTAL S60-S65** | **A/K/Q/J/T/9/8 + synthesis** | **All high_only rules** | **1,226,940 (100%)** | **$615.29 (vs oracle); $381.41 (vs v44)** | **5-of-5 NULL — all high_only ML-only at catalog granularity** |

Five consecutive max-rank zones produced ALL-T3 verdicts across 43 tested candidates and a 12.7× range of structural opportunity (drop-max rate 6%→76% plus inverted-defensive at T/9/8). The aggregate document `HIGH_ONLY_RULE_CATALOG.md` is the publishable end-product of S60–S65 per CLAUDE.md's stated end-product goal.

---

## Resume Prompt (Session 66 — pair category audit OR hybrid chain)

```
Resume Session 66 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S65 — pair category audit OR hybrid chain)
- HIGH_ONLY_RULE_CATALOG.md (the S60-S65 canonical synthesis — the
  publishable end-product. Especially Part 4 (implications) for the
  pair / hybrid-chain trade-off.)
- DECISIONS_LOG.md (latest: Decision 100 — S65 aggregate catalog + ML-only
  boundary claim formalized)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (template for S66 Phase 1 —
  the per-(pair_rank × cell) decision matrix to build)

State (end of Session 65):
- HIGH_ONLY_RULE_CATALOG.md complete. Catalog closed on high_only as
  ML-only at human granularity.
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- Two production tracks diverge by $1,417/1000h; $381 in high_only ML-only.
- Per-category residuals (descending by WG):
  - pair: $396/1000h (36.2% share) ← LARGEST REMAINING TARGET
  - trips: $55, two_pair: $52, three_pair: $35, trips_pair: $5
  - composite: $2, quads: $1

USER DIRECTIVE (S59-S65 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 66 — TWO PATHS, USER PICKS:

PATH A — Pair category audit (RECOMMENDED for catalog completeness):

  Phase 1 — Build PAIR_DECISION_MATRIX.md analogous to S58. No rule
  shipping. Stratify pair hands by (pair_rank × pair-placement × ms_mid
  achievability × DS bot achievability). Output oracle TOP/BOT/MID profile
  and v44 mismatch class per (pair_rank, cell). Same shape as
  SESSION_58_HIGH_ONLY_DECISION_MATRIX.md. Time: ~3-4 hours.

  Phase 2 — Audit existing pair rules (Rules 7-11 in v52) cell-by-cell.
  Identify whether they leave substantial within-cell residual that
  human-statable refinements could close. Time: ~1 hour.

  Phase 3 — Decide on continuation: catalog sweep / pivot / hybrid.

PATH B — Hybrid chain experiment (FASTER, COMMITS production to v44_dt
on high_only):

  Isolate v44_dt's high_only-specific decision tree. Benchmark
  v52-non-high_only + v44_dt-high_only on held-out subset. Ship as v53 if
  zero non-targeted regression. Estimated lift on rule chain: ~$200-300/1000h
  whole-grid. Time: ~1 hour.

RECOMMENDED ORDER: Phase 1 of Path A FIRST (information value before
committing to hybrid), then hybrid experiment as Path B if pair shows
similar ML-only ceiling. If user prefers Path B alone, that's tractable
in ~1 hour.

ACCEPTANCE for Session 66 (Path A minimum):
- PAIR_DECISION_MATRIX.md produced.
- Per-(pair_rank × cell) v44 residual + oracle pick profile documented.
- Top-3 mismatch class per cell identified with $/1000h within-cell.
- Recommendation issued for S67+ direction.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- The catalog harness (analysis/scripts/test_rule_catalog.py) is
  STRUCTURALLY CATEGORY-AGNOSTIC. Reusable for pair after building a
  new cell-tagging parquet.
- "Speed is not necessary — clarity and perfection is." — S66 Phase 1
  is fresh design work, not a copy of S58.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
