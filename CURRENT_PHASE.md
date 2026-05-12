# Current: Sprint 8 — Session 66 produced `PAIR_DECISION_MATRIX.md`, the canonical pair-category Phase 1+2 audit. Pair category v44_dt→oracle residual decomposes into a 6-cell pair-specific taxonomy across 2.8M canonical hands; v52 (rule chain) leaves **$341/1000h WG more residual than v44 on pair**, concentrated entirely in **PBOT cells ($391 WG of catalog-shippable headroom)** where six pair_ranks (A, K, 6, 7, 8, 9) have ZERO PBOT-routing rule in v52. The dominant Phase 3 target is a generalized pair-to-bot DS rule extending v9_2/Rule 11 to cover the six uncovered ranks; ceiling estimates per candidate range $28-89/1000h WG. **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498 full / $1,522 prefix); v44_dt ($1,081 full / $686 prefix). Two-track divergence $1,417/1000h. Pair Phase 3 candidates are SIZED with catalog-shippable WG ceilings.

> **🎯 IMMEDIATE NEXT ACTION (Session 67): Phase 3 candidate sweep — start with the highest-EV PBOT-take rule (C_PAIR_3: 6/7/8/9-pair PBOT-take, $89/1000h WG ceiling).**
>
>   Per `PAIR_DECISION_MATRIX.md` Phase 2 + Phase 3 sections, five concrete catalog candidates are sized:
>
>   | ID | Candidate | Fire region | Catalog ceiling (WG) |
>   |---|---|---|---:|
>   | **C_PAIR_3** | **6/7/8/9-pair PBOT-take rule** | 4 ranks × PBOT cells (~475K hands) | **$88.71/1000h WG** |
>   | C_PAIR_5 | Q-pair PBOT_DS_PARTIAL refinement | Q-pair × PBOT_DS_PARTIAL (~90K) | $41.20/1000h WG |
>   | C_PAIR_1 | K-pair PBOT-take rule | K-pair × PBOT cells (~119K) | $35.60/1000h WG |
>   | C_PAIR_4 | Drop "single Ace" predicate from v9_2 | 3× wider v9_2 fire region | ~$30-50/1000h WG estimate |
>   | C_PAIR_2 | A-pair PBOT-take rule | A-pair × PBOT cells (~119K) | $28.39/1000h WG |
>
>   Even at 40-60% capture rates (lower than Rule 14's A-high record 70%+), each clears T2's $5 WG bar by 5-15×.
>
>   **3-PHASE PLAN (Session 67 — start the candidate sweep):**
>
>   **Phase 1 (S67 first ~1 hr)** — Build pair-specific catalog harness `test_rule_catalog_pair.py` by adapting `test_rule_catalog.py` for the pair parquet schema (cell_idx, pair_rank instead of max_rank). Reuse the per-hand parquet at `data/drill_pair_v44_per_hand_structural.parquet`. Sanity-check by reproducing the shipped lift of Rule 11 (J-pair-J pair-to-bot DS): v52 vs v52-minus-Rule-11 on J-pair hands should match Decision 080's +$11/1000h WG estimate (with the caveat that the original measurement was on full N=200 grid, same as our oracle grid, so should match to <5%).
>
>   **Phase 2 (S67 second ~2 hr)** — Test C_PAIR_3 candidates. Three sub-variants:
>     - C_PAIR_3a: simple "if pair_rank ∈ {6,7,8,9} AND PBOT_DS achievable → take PBOT-HIMID setting"
>     - C_PAIR_3b: gated variant with PBOT bot_pair_high ≥ T threshold
>     - C_PAIR_3c: PBOT_DS_JOINT only (most surgical, smallest fire-region)
>
>   For each: measure within-cell + WG lift vs v52 baseline. T1 = ≥40% capture within fire-region cell; T2 = ≥+$5/1000h WG + zero non-targeted regression.
>
>   **Phase 3 (S67 closing ~30 min)** — Decision on continuation: if C_PAIR_3 ships clean → ship as v53, queue C_PAIR_1/C_PAIR_2/C_PAIR_5 for S68. If C_PAIR_3 falsifies (T3 verdict) → falls back to C_PAIR_5 (smaller fire region, larger per-hand lift) as the next falsification attempt.
>
>   **TIME BUDGET (S67):** ~3-4 hours total. Phase 1 harness adaptation is structural; reuses pair Phase 1 parquet. Phase 2 measurement is 3 candidates × ~15-30 min each = ~1 hr; bulk of time is harness setup and reasoning.
>
>   **ALTERNATIVE (if user prefers): the hybrid chain experiment.** Per `PAIR_DECISION_MATRIX.md` Recommendation Path B, a cell-routed hybrid (v44 on PBOT cells, v52 on PMID cells) captures $390 WG improvement on pair vs v52 alone, $49 WG vs v44 alone. Implementationally simpler than rule extension. The trade-off: hybrid commits production to v44_dt on PBOT pair cells forever (or until an alternate ML champion).
>
>   **RECOMMENDED ORDER: C_PAIR_3 candidate sweep FIRST.** A successful rule ship is more durable than the hybrid chain (the rule is portable, interpretable, and validatable); the hybrid is a fallback if rules fail catalog ship thresholds.
>
>   **SUCCESS CRITERIA (S67 — Path A minimum):**
>   - `test_rule_catalog_pair.py` harness produced and Rule 11 shipped-lift reproduced to <5% error.
>   - 3+ C_PAIR_3 sub-variants tested; verdicts assigned per T1/T2/T3.
>   - If any sub-variant clears T2: candidate proceeds to non-targeted-regression check on full grid.
>   - S68 direction recommendation (Phase 3 sweep continuation OR pivot to C_PAIR_5 / hybrid).

> **✅ ARTIFACTS produced in S66:**
> 1. **`PAIR_DECISION_MATRIX.md`** — the canonical pair Phase 1+2 audit document. Headlines + per-(pair_rank, cell) v44 residual + oracle pick profile + v52 vs v44 comparison + existing-rule coverage check + Phase 3 candidate sizing with quantified WG ceilings.
> 2. **`analysis/scripts/drill_pair_v44_S66.py`** — pair-specific deep-dive sweep (Phase 1).
> 3. **`analysis/scripts/sweep_v52_on_pair_S66.py`** — v52 sweep on pair hands (Phase 2).
> 4. **`data/drill_pair_v44_per_hand_structural.parquet`** (22.8 MB) — per-hand v44/oracle picks + 6-cell structural tag. Foundation for S67+ catalog harness.
> 5. **`data/drill_pair_v44_summary.json`** (390 KB) — aggregate stats keyed by (pair_rank, cell). Source for matrix doc tables.
> 6. **`data/drill_pair_v52_per_hand.parquet`** (12.0 MB) — v52 picks joined on canonical_id.
> 7. **`data/drill_pair_v52_summary.json`** (45 KB) — v52 per-(pair_rank, cell) aggregates.
> 8. **`DECISIONS_LOG.md`** — Decision 101 (this session's analysis + recommendation).
> 9. **`CURRENT_PHASE.md`** — rewritten for S67 (this file).
>
> No new code, tests, or production state changes. Pure analysis + documentation work, mirroring S58/S65's pattern.

> **📓 METHODOLOGY (Session 67+):**
> - **Threshold definitions carry over from S60-S65:**
>   - **T1 (Catalog-worthy):** ≥ 40% gap closure within cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **T2 (Production ship):** T1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **T3 (ML-only):** No candidate clears T1 → cell formally labeled ML-only.
> - **Pair cell taxonomy (6 cells):** PBOT_DS_JOINT / PBOT_DS_PARTIAL / PMID_DS_MAXTOP / PMID_DS_NOMAXTOP / PMID_SS_MAXTOP / PMID_OTHER. Defined in `analysis/scripts/drill_pair_v44_S66.py:cell_for_pair_hand`. **Cell distribution is canonical-symmetric** (same n_hands per cell across all 13 pair_ranks).
> - **Catalog harness must be adapted for pair schema.** `test_rule_catalog.py` uses (max_rank, cell) keys; pair version needs (pair_rank, cell). Cell tagging is pre-computed in the parquet (`cell_idx` column). Reuse otherwise verbatim.
> - **Cross-check shipped-lift attribution.** Reproduce Rule 11 (+$11/1000h WG per Decision 080) within <5% before testing new candidates. This is the pair analog of S60-S64's harness validation pattern.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59, re-confirmed S60-S66.)

> Updated: 2026-05-12 (Session 66 end — `PAIR_DECISION_MATRIX.md` complete; Phase 3 candidate sweep mandated for S67)

---

## Headline state at end of Session 66 (UNCHANGED from S65)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion** (UNCHANGED). $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

**Per-category residuals (UNCHANGED from S58–S65; pair now characterized in detail):**

| Category | n_hands | share | v44 within-cat | $/1000h whole-grid | Status |
|---|---:|---:|---:|---:|---|
| high_only | 1,226,940 | 40.4% | $1,868 | $755 | CATALOG CLOSED S65 — ML-only at human granularity |
| **pair** | 2,800,512 | 36.2% | $1,097 | $396 | **PHASE 1+2 COMPLETE S66 — $341 WG catalog-shippable in PBOT cells** |
| trips | 328,185 | 4.6% | $1,194 | $55 | S68+ target (after pair Phase 3 ships) |
| two_pair | 1,338,480 | 14.5% | $363 | $52 | Mid-priority |
| three_pair | 114,400 | 2.2% | $1,613 | $35 | Larger per-hand gap, smaller population |
| trips_pair | 171,600 | 1.8% | $281 | $5 | Already collapsed S55a |
| composite | 14,742 | 0.2% | $960 | $2 | Rounding-error scale |
| quads | 14,300 | 0.1% | $545 | $1 | Rounding-error scale |

**`PAIR_DECISION_MATRIX.md` produced in S66:** canonical synthesis of the pair Phase 1 (v44_dt vs oracle descriptive matrix per (pair_rank × cell)) + Phase 2 (v52 audit revealing the $391 WG PBOT-cell gap) + Phase 3 candidate sizing. The matrix is the source-of-truth for pair-category numerical detail and the basis for S67+ Phase 3 candidate work.

**Pair category catalog headroom decomposition:**

| Cell | v52 WG | v44 WG | v52→v44 gap (catalog ceiling) |
|---|---:|---:|---:|
| PBOT_DS_JOINT | $150.51 | $42.40 | **$108.11** |
| PBOT_DS_PARTIAL | $455.82 | $173.09 | **$282.73** ← largest |
| PMID_DS_MAXTOP | $15.16 | $42.14 | −$26.98 (v52 wins) |
| PMID_DS_NOMAXTOP | $142.28 | $152.82 | −$10.55 (v52 wins) |
| PMID_SS_MAXTOP | $38.11 | $44.42 | −$6.31 (v52 wins) |
| PMID_OTHER | $50.60 | $56.28 | −$5.68 (v52 wins) |
| **PBOT subtotal** | **$606.33** | **$215.49** | **+$390.84** catalog-shippable |
| **PMID subtotal** | **$246.15** | **$295.66** | **−$49.51** (v52 already correct) |
| **TOTAL** | **$852.48** | **$511.16** | **+$341.33** v52→v44 |

**Existing pair rules and their coverage:**

| Rule | Source | Fire region | Coverage of PBOT cells |
|---|---|---|---|
| Rule 5 (KK/AA + rainbow bot) | v28 (S26) | pair_rank ∈ {K, A} AND bot rainbow | Narrow sub-cell |
| Rule 10 (J-low pair defensive) | v41 (S43) | pair_rank ≤ J AND max_rank ≤ J | PMID cell, lowest-singleton-on-top |
| Rule 11 (J-pair pair-to-bot DS) | v42 (S46) | pair_rank = J AND max_rank = J | Narrow (J-pair-J only, ~2% pair) |
| v9_2 (pair-to-bot DS) | v14_combined → v8_hybrid (S26) | pair_rank ∈ {2-5, T-J-Q} AND single Ace AND DS feasible | Covers 7/13 ranks AT FIRE-REGION rate ~42-58% |
| (none) | | **pair_rank ∈ {6, 7, 8, 9, A, K}** | **ZERO PBOT routing** ← S67 target |

---

## Session 60+ catalog sequence (S66 added)

| Session | Focus | Existing rule | Population | Outcome |
|---|---|---|---|---|
| 60 | A-high catalog | Rule 14 | 660,660 | NULL — all cells ML-only |
| 61 | K-high catalog | Rule 15 | 330,330 | NULL — all cells ML-only |
| 62 | Q-high catalog | Rule 16 | 150,150 | NULL — all cells ML-only |
| 63 | J-high catalog | Rule 17 + 24 | 60,060 | NULL — all cells ML-only |
| 64 | T/9/8-high catalog | Rules 25/26/27 | 25,740 | NULL — all cells ML-only |
| 65 | high_only aggregate synthesis | All high_only | 1,226,940 | `HIGH_ONLY_RULE_CATALOG.md` produced; ML-only boundary formalized |
| **66** | **Pair Phase 1+2 audit** | **All pair (Rules 5/10/11, v9_2)** | **2,800,512** | **`PAIR_DECISION_MATRIX.md` produced; PBOT cells = $391 WG catalog-shippable headroom** |

S66 is the first per-category audit to produce **non-T3 verdicts** since S64 — pair PBOT cells are CATALOG-SHIPPABLE at the matrix's quantified ceilings.

---

## Resume Prompt (Session 67 — pair PBOT-rule candidate sweep)

```
Resume Session 67 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S66 — pair PBOT-rule candidate sweep)
- PAIR_DECISION_MATRIX.md (the S66 Phase 1+2 audit — Phase 3 candidate
  sizing is in the "Recommendation" section near the end)
- DECISIONS_LOG.md (latest: Decision 101 — S66 pair matrix produced;
  pair category opens with $341/1000h WG catalog-shippable headroom)
- HIGH_ONLY_RULE_CATALOG.md (the S65 high_only synthesis for methodology
  reference — the test_rule_catalog.py harness pattern + threshold defs
  carry over verbatim)
- analysis/scripts/test_rule_catalog.py (the high_only catalog harness;
  needs adaptation for pair schema in S67 Phase 1)

State (end of Session 66):
- PAIR_DECISION_MATRIX.md complete. Pair category audit Phase 1 (v44_dt vs
  oracle descriptive matrix) AND Phase 2 (v52 rule-chain audit) finished.
- Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix).
- ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix).
- Per-category WG residual (UNCHANGED):
  - high_only: $755 (catalog CLOSED S65)
  - pair: $396 (catalog OPEN, $341/1000h WG catalog-shippable headroom in PBOT cells)
  - trips: $55, two_pair: $52, three_pair: $35

USER DIRECTIVE (S59-S66 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 67 — Phase 3 candidate sweep on pair:

  PHASE 1 (S67 ~1 hr) — Build catalog harness for pair.
  Adapt analysis/scripts/test_rule_catalog.py for the pair schema:
  - Load data/drill_pair_v44_per_hand_structural.parquet
  - Filter by (pair_rank, cell) instead of (max_rank, cell)
  - Cell index is in parquet column `cell_idx`; cells_order in script
  - Sanity-check: reproduce Rule 11 shipped lift to <5% error
    (Decision 080: +$11/1000h WG on J-pair-J)
  - Output: analysis/scripts/test_rule_catalog_pair.py

  PHASE 2 (S67 ~2 hr) — Test C_PAIR_3 (highest-EV candidate):
  Three sub-variants of "6/7/8/9-pair PBOT-take rule":
  - C_PAIR_3a: simple "pair_rank ∈ {6,7,8,9} AND PBOT_DS achievable
               → take PBOT-HIMID setting"
  - C_PAIR_3b: gated variant with PBOT bot_pair_high ≥ T threshold
  - C_PAIR_3c: PBOT_DS_JOINT only (most surgical)

  For each: measure within-cell + WG lift vs v52 baseline.
    T1 ≥ 40% capture within fire-region cell
    T2 ≥ +$5/1000h WG + zero non-targeted regression
    Catalog ceiling: $88.71/1000h WG total for C_PAIR_3 family

  PHASE 3 (S67 ~30 min) — Decision on continuation.
  - If C_PAIR_3 ships clean → ship as v53; queue C_PAIR_1/C_PAIR_2/C_PAIR_5
    for S68 sweep.
  - If C_PAIR_3 falsifies (all T3) → fall back to C_PAIR_5 (Q-pair
    PBOT_DS_PARTIAL refinement, smaller fire region, $41.20 WG ceiling).

ACCEPTANCE for Session 67 (Path A minimum):
- test_rule_catalog_pair.py harness produced and Rule 11 reproduction
  <5% error confirmed.
- C_PAIR_3a/b/c verdicts assigned per T1/T2/T3.
- If any sub-variant clears T2: non-targeted regression check on full grid
  before shipping as v53.
- S68 direction recommendation issued.

ALTERNATIVE (if user prefers): hybrid chain experiment.
Per PAIR_DECISION_MATRIX.md Recommendation Path B, a cell-routed hybrid
(v44 on PBOT cells, v52 on PMID cells) captures $390 WG improvement on
pair vs v52 alone. Implementationally simpler than rule extension.
The trade-off: hybrid commits production to v44_dt on PBOT pair cells.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- The pair Phase 1 parquet (data/drill_pair_v44_per_hand_structural.parquet,
  22.8 MB) is the foundation for the pair catalog harness.
- 6-cell pair taxonomy: PBOT_DS_JOINT / PBOT_DS_PARTIAL / PMID_DS_MAXTOP /
  PMID_DS_NOMAXTOP / PMID_SS_MAXTOP / PMID_OTHER.
- "Speed is not necessary — clarity and perfection is." — S67 candidates
  are concrete with quantified ceilings; no fresh design work needed.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
