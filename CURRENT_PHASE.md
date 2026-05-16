# Current: Sprint 8 — Session 92 STRUCTURAL NULL on two_pair + trips chain audit; production v64 UNCHANGED; key finding: v55_two_pair_hybrid and v56_trips_hybrid blanket-route 100% of their target hands to v44_dt unconditionally, so v64 ≡ v44_dt by construction on every two_pair and trips hand and chain-audit produces ZERO candidates; biggest architectural snapshot to date — v44_RULE13 chain bleeds +$515.80/1000h on two_pair prefix (3× the LOW pair bleed, largest single-layer bleed identified in project) and +$33.21/1000h on trips prefix; v55 + v56 + v54 + Rule 29 absorb a cumulative $731/1000h of chain bleed across pair + two_pair + trips — the most load-bearing infrastructure in the project; CHAIN-AUDIT METHODOLOGY ARC COMPLETE across all four major hand-categories (5 sessions, 4 ships totaling $214.83/1000h, 2 NULLs at well-characterized boundaries); new chain-audit applicability prerequisite (NEW S92): production picks must differ from v44_dt on at least some audit cells, pre-flight code trace verifies in <5 min; S93 default plan pivots from chain-audit to Option C N=1000 oracle generator infrastructure (promoted from TERTIARY to PRIMARY)

S92 executed the S91-defined PRIMARY + SECONDARY paths verbatim. Pre-flight code trace of `strategy_v55_two_pair_hybrid` and `strategy_v56_trips_hybrid` revealed both contain a single binary gate routing 100% of target hands to `strategy_v44_dt` unconditionally — meaning production v64 picks ≡ v44_dt picks by construction on every two_pair and trips hand. The chain-audit pattern (= "find a layer where production bleeds vs v44_dt, gate it out") cannot find anything to gate because **production IS v44_dt for these categories**.

The audits proceeded anyway to (a) empirically confirm on all 1.34M two_pair hands and (b) produce the architectural snapshot.

**Two_pair audit results (204,275 prefix hands × 7 layer strategies):**

| layer | total prefix leak | Δ vs prior layer |
|---|---:|---:|
| v44_dt | $+270.70 | — |
| v44_RULE13 chain | $+786.50 | **+$515.80** (chain BLEEDS massively — 3× S91 LOW pair) |
| v54 (pair_hybrid) | $+786.50 | $+0.00 (inert) |
| **v55 (two_pair_hybrid)** | **$+270.70** | **-$515.80** (blanket routing ABSORBS 100%) |
| v56 / v57 / v64 | $+270.70 | $+0.00 (all inert) |

**Trips audit results (25,245 prefix hands × 7 layers):**

| layer | total prefix leak | Δ vs prior layer |
|---|---:|---:|
| v44_dt | $+54.85 | — |
| v44_RULE13 chain | $+88.06 | **+$33.21** (chain bleeds) |
| v54 / v55 | $+88.06 | $+0.00 (inert) |
| **v56 (trips_hybrid)** | **$+54.85** | **-$33.21** (blanket routing absorbs 100%) |
| v57 / v64 | $+54.85 | $+0.00 (inert) |

**Phase B addressability empirical check:** 0 mismatches between v64 and v44_dt across all 1,338,480 two_pair hands. Δ(v64 − v44_dt) = $0.00 on every (cell × max_sing) sub-cell. Same on trips by structural construction.

**Phase C grader: 0 candidates exist.** Pre-committed thresholds (SHIP ≥ $5 both grids, NULL ≤ $1 both grids) cannot be evaluated because the candidate set is empty. Mechanical verdict: STRUCTURAL NULL.

**Aggregate S92 verdict: STRUCTURAL NULL on both two_pair and trips.**

**Production state: UNCHANGED.** v64_high_only_chain_fix_zone remains the rule chain ($1,627.36/1000h full / $776.88/1000h prefix). v44_dt remains ML champion (20 sessions unchanged). Rule count: 24. Two-track divergence: $117.84/1000h. Cumulative closure since pre-S68: 91.6%. **Combined S87-S92 chain-audit recovery: $214.83/1000h** (S91 + S92 contribute $0).

**ARCHITECTURAL SNAPSHOT — cumulative chain bleed absorbed by infrastructure:**

| category | v44_RULE13 chain bleed vs v44_dt (prefix) | absorbed by | residual at production |
|---|---:|---|---:|
| LOW pair (S91) | $+182.28 | v54 + Rule 29 | -$13.36 (LIFT) |
| two_pair (S92) | $+515.80 | v55 | $+0.00 |
| trips (S92) | $+33.21 | v56 | $+0.00 |
| **TOTAL** | **$+731.29** | v54 + v55 + v56 + Rule 29 | **net LIFT** |

**Without v54/v55/v56/Rule 29, production would bleed $731/1000h vs v44_dt on the pair-family categories alone.** These are the most load-bearing pieces of infrastructure in the project.

**FIRST PROJECT-LEVEL FRAMING OF "CHAIN-AUDIT ARC COMPLETE."** The pattern has been applied across all four major hand-categories (HIGH_ONLY, LOW single-pair, two_pair, trips). Five sessions of work yielded four ships ($214.83/1000h) + two NULLs at well-characterized boundaries (S91 population-divergence noise on prefix-COVERED single-pair; S92 structural collapse on blanket-routed two_pair + trips). The lever is now bounded; new ships from chain-audit are not expected on current architecture.

> **🎯 IMMEDIATE NEXT ACTION (Session 93): pivot to Option C N=1000 oracle generator infrastructure (PRIMARY, promoted from TERTIARY), OR rule-extraction on two_pair LAYOUT_A_SS residual (SECONDARY), OR headline-goal recalibration (TERTIARY)**
>
> Chain-audit is exhausted. S93 should pivot to a new lever. Default order:
>
> 1. **PRIMARY (PROMOTED FROM TERTIARY) — build Option C N=1000 oracle
>    generator infrastructure.** Modify `engine/src/main.rs` to add
>    `--id-list-file` option (read canonical IDs from file, only process
>    those, write per-hand N=1000 EVs). Engineering scope: ~30-60 min Rust
>    mod + ~10 min test. Unlocks:
>      (i) retroactive validation of v60 (S86 MIXED-by-methodology, still
>          unshipped after 7 sessions),
>      (ii) two-grid SHIP standard on arbitrary cell subsets at N=1000
>           quality,
>      (iii) future smaller-effect rule validation that the current
>            prefix grid + full N=200 grid can't handle.
>    With chain-audit exhausted, this is the natural next infrastructure
>    investment.
>
> 2. **SECONDARY — rule-extraction (Option D-revised) on within-v44_dt
>    residual leak.** Current v44_dt leak vs oracle by category:
>      LOW pair: $281.56 (S83-S86 partially addressed)
>      MID pair: TBD (S86 v60 candidate UNSHIPPED)
>      HIGH pair: TBD (not formally measured at category level)
>      two_pair: $80.82
>      trips: $65.18
>    Largest unaddressed cell: **two_pair LAYOUT_A_SS at $35.22/1000h on
>    437,580 hands** (the SS-bot two_pair layout — could be amenable to a
>    "drop max kicker into bot for DS-like SS structure" rule similar to
>    Rule 20's mechanism). S69 tested catalog candidates and confirmed
>    v44_dt dominates the AGGREGATE; individual sub-cells were not
>    exhaustively probed. Worth one drill.
>
> 3. **TERTIARY — headline-goal recalibration.** Make explicit that 95%
>    match% is unreachable from current architecture; reset target to
>    maximize $/1000h subject to current cascade. Affects how future
>    NULL ship sessions read (failures vs boundary-mapping wins).
>
> 4. **DEFERRED — ML retrain (A3 full 6M-hand N=1000 grid).** Formally
>    closed at v44 in S78 (Decision 113). Reopening requires either a
>    new feature family or A3 infrastructure.
>
> 5. **DEFERRED — v52-defensive-low partial-effectiveness exploit** (S90).
>    Speculative.
>
> 6. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56
>    absorbing the bleed on pair-family, replacing v44_RULE13 only
>    matters for HIGH_ONLY (already gated). Large engineering scope,
>    unclear payoff.

> **📓 METHODOLOGY (Session 93+ — refined through S92):**
>
> 1. **CHAIN-AUDIT APPLICABILITY TEST — 3-pronged (refined S92).** Most
>    productive when:
>      (a) target cells are prefix-SILENT → EFFECT-SIZE-DOMINANCE applies
>          (S87-S90), OR
>      (b) per-sub-cell residual ≥ $5/1000h on BOTH grids (S91), AND
>      (c) [NEW S92 PREREQUISITE] production picks must DIFFER from
>          v44_dt on at least some audit cells — otherwise the chain
>          has been collapsed by a prior router and there is nothing to
>          gate out (STRUCTURAL NULL).
>    Condition (c) is verifiable in ~5 min via pre-flight code trace.
>
> 2. **PRE-FLIGHT CODE TRACE AS PIVOT-GATE (NEW S92).** When the audit
>    target's production chain can be read in <100 lines of strategy
>    code, read it first. Cheaper than running a 5-30 min drill that
>    will return structural NULL.
>
> 3. **STRUCTURAL NULL vs POPULATION-DIVERGENCE NULL (NEW S92).** Two
>    distinct verdict patterns for chain-audit:
>      * S91 POPULATION-DIVERGENCE NULL: real candidates, grids
>        disagree on direction, two-grid bar correctly nulls.
>      * S92 STRUCTURAL NULL: no candidates exist by construction
>        because a prior router collapsed the chain.
>    Both honest; the path forward differs (S91 → tighter bars; S92
>    → pivot lever).
>
> 4. **TWO-CONSECUTIVE-NULL = LEVER SATURATION (NEW S92).** One NULL is
>    noise; two consecutive NULLs at the boundary of a methodology arc
>    is signal. After two consecutive NULLs on the same lever, the
>    default plan for the next session should PIVOT, not default to
>    "more of the same lever."
>
> 5. **CHAIN-AUDIT METHODOLOGY ARC COMPLETE (5 sessions, S87-S92).** Four
>    ships ($214.83/1000h) + two boundary NULLs. The arc is bounded;
>    future ships from this pattern require either a new chain layer
>    (e.g., post-ML-retrain) or new chain architecture.
>
> 6. **v54 + v55 + v56 + Rule 29 ARE THE MOST LOAD-BEARING INFRASTRUCTURE.**
>    They absorb $731/1000h of v44_RULE13 chain bleed across pair-family.
>    Treat as protected infrastructure; future work should not undo their
>    routing without quantifying the bleed magnitude they currently absorb.
>
> 7. **PIVOT-GATE METHODOLOGY COMPOUNDS.** S87 introduced pre-drill before
>    infrastructure; S92 extends to pre-flight code-trace before pre-drill.
>    Each layer of pivot-gate provides a cheaper falsifier of the premise
>    before committing more compute.

> **✅ ARTIFACTS produced in S92:**
> 1. `analysis/scripts/drill_v64_two_pair_addressability_S92.py` — Phase B pre-drill on all 1.34M two_pair hands (NEW)
> 2. `analysis/scripts/audit_v64_two_pair_chain_S92.py` — Phase B+ layer attribution v44_dt → v44_RULE → v54 → v55 → v56 → v57 → v64 (NEW)
> 3. `analysis/scripts/audit_v64_trips_chain_S92.py` — SECONDARY: same audit on trips (NEW)
> 4. `analysis/scripts/grade_v65_two_pair_trips_chain_candidates_S92.py` — Phase C structural-NULL grader (NEW)
> 5. `data/session92/drill_v64_two_pair_addressability.log`
> 6. `data/session92/audit_v64_two_pair_chain.log`
> 7. `data/session92/audit_v64_trips_chain.log`
> 8. `data/session92/grade_v65_two_pair_trips_chain_candidates.log`
> 9. `SESSION_92_REPORT.md` — session report with plain-language TL;DR + complete chain-audit applicability map (NEW)
> 10. `DECISIONS_LOG.md` — Decision 127 (STRUCTURAL NULL + 3-pronged applicability + methodology arc complete) appended
> 11. `CURRENT_PHASE.md` — this file, rewritten for S93
> 12. `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy change); front-matter "Last updated" line updated only

> Updated: 2026-05-15 (Session 92 end — STRATEGY OF RECORD UNCHANGED: v64 remains production. S92 was the planned execution of the S91-defined PRIMARY + SECONDARY paths: pivot to two_pair chain audit and trips chain audit. Pre-flight code trace of `strategy_v55_two_pair_hybrid` and `strategy_v56_trips_hybrid` revealed both blanket-route 100% of target hands → v44_dt, so production v64 ≡ v44_dt on every two_pair and trips hand by construction. Empirical confirmation: 0 mismatches across all 1,338,480 two_pair hands; Δ(v64 − v44_dt) = $0.00 on every cell. Chain audit produced the architectural snapshot: v44_RULE13 chain bleeds $+515.80/1000h prefix vs v44_dt on two_pair (3× the LOW pair bleed S91 found — largest single-layer bleed in project) and $+33.21 on trips. v55 absorbs $515.80 (blanket two_pair → v44_dt); v56 absorbs $33.21 (blanket trips → v44_dt). v54/v55/v56/Rule 29 cumulative absorption across pair-family: $731/1000h — most load-bearing infrastructure in the project. Phase C grader: 0 candidates exist (structural NULL distinct from S91's population-divergence NULL). Verdict: STRUCTURAL NULL on both targets. Second consecutive NULL session in chain-audit run. Decision 127 records the NULL + seven methodology refinements: (1) CHAIN-AUDIT APPLICABILITY MAP COMPLETE across all 4 major hand-categories (HIGH_ONLY/single-pair/two_pair/trips), (2) PRE-FLIGHT CODE TRACE AS PIVOT-GATE (NEW) — read strategy code before drilling, (3) STRUCTURAL NULL is distinct from POPULATION-DIVERGENCE NULL (NEW) — different mechanisms, different path forward, (4) v44_RULE13 chain bleed quantified across pair-family ($731 absorbed by infrastructure), (5) TWO-CONSECUTIVE-NULL is decision-relevant signal that lever is saturated (NEW), (6) chain-audit applicability test now 3-pronged with NEW condition (c) "production picks must differ from v44_dt", (7) NULL audits are still complete cycles + maintain methodology integrity. S93 default plan: pivot from chain-audit to Option C N=1000 oracle generator infrastructure (PROMOTED from TERTIARY to PRIMARY), OR rule-extraction on two_pair LAYOUT_A_SS residual (SECONDARY), OR headline-goal recalibration (TERTIARY). Engine cargo build + tests pre-flight clean (141 tests pass). v44_dt UNCHANGED for 20th consecutive session.)

---

## Headline state at end of Session 92 (UNCHANGED from S90/S91)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v64_high_only_chain_fix_zone** | PRODUCTION rule chain. **$1,627.36/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 20 sessions, since v44 in S58). $1,081/1000h full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$117.84/1000h (UNCHANGED).** Cumulative closure since pre-S68: $1,291.16 = **91.6% of original $1,409 (UNCHANGED).**

Production vs v44_dt: production outperforms ML by **$546/1000h** (UNCHANGED).

**Total project rule count: 24** (UNCHANGED).

**S92 results (STRUCTURAL NULL):**

| target | mechanism | v44_RULE13 chain bleed (prefix) | absorbed by | residual at production |
|---|---|---:|---|---:|
| two_pair (PRIMARY) | v55 blanket routing collapses chain | $+515.80 | v55 (100%) | $0.00 |
| trips (SECONDARY) | v56 blanket routing collapses chain | $+33.21 | v56 (100%) | $0.00 |

---

## Hypothesis cascade status (updated after S92)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8 + LOW pair under-coverage. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | FORMALLY CLOSED (Decision 113). |
| S79 label-noise measurement | Existing N=1000 prefix vs N=200 full | MIXED — 32% oracle disagreement reveals criterion blind spot (Decision 114). |
| A1 (S80) | Retrain v44 DT on N=1000 prefix labels | LIFTS +13.15pp on N=1000 match rate; in-sample evaluation caveat (Decision 115). |
| C2 (S80) | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | NULL −2.13pp on N=1000, −12.24pp on N=200 (Decision 115). |
| A2 (S81/S82) | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | CLEAN NULL — Lens-3 held-out 63.74% < 72.0% floor (Decision 117). |
| A-path (oracle-label-quality lever) | All variants tested at v44 capacity | FORMALLY CLOSED at v44 regime (Decision 117). |
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — not picked by user. |
| Headline-goal recalibration | Concede 95% match% as unreachable | OPEN AGAIN POST-S92 — chain-audit arc complete, extraction track diminishing returns, time to make recalibration explicit. |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). Re-confirmed via S91 layer attribution. |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86) | MID × PMID_DS_NOMAXTOP | MIXED-BY-METHODOLOGY — full +$6.43 SHIP, prefix silent; v60 still UNSHIPPED (Decision 121). |
| DAMAGE-CONTROL chain audit cell #1 (S87) | HIGH_ONLY × DS_NO_JOINT × {J-A} v52-chain regression | SHIPPED — Rule 21 + $98.67 full-grid (Decision 122). |
| DAMAGE-CONTROL chain audit cell #2 (S88) | HIGH_ONLY × {DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH} × {J-A} v47-chain regression | SHIPPED — Rule 22 + $98.84 full-grid (Decision 123). |
| DAMAGE-CONTROL chain audit cell #3 (S89) | HIGH_ONLY × {JOINT_MED, JOINT_LOW} × {J-A} v47-chain regression | SHIPPED — Rule 23 + $10.09 full-grid (Decision 124). |
| DAMAGE-CONTROL chain audit cell #4 (S90) | HIGH_ONLY × {5 cells} × {8, 9, T} v47-chain regression (first v52-defensive-low audit) | SHIPPED — Rule 24 + $7.23 full-grid (Decision 125). HIGH_ONLY × max ≥ 8 ZONE COMPLETE. |
| DAMAGE-CONTROL chain audit cell #5 (S91) | LOW pair PMID prefix-COVERED cells (FIRST prefix-COVERED chain audit) | NULL — three candidates all FAIL two-grid SHIP standard (Decision 126). v44_RULE13 chain bleeds $182/1000h but v54+Rule 29 absorb $195. POPULATION-DIVERGENCE NOISE methodology lesson identified. |
| **DAMAGE-CONTROL chain audit cell #6 + #7 (S92)** | **two_pair + trips chain audit** | **STRUCTURAL NULL — chain-audit candidate set EMPTY by construction (Decision 127). v55/v56 blanket routing has collapsed chain to v44_dt; production v64 ≡ v44_dt on every two_pair/trips hand. v44_RULE13 chain bleeds $+515.80 on two_pair + $+33.21 on trips, absorbed 100% by v55/v56. CHAIN-AUDIT METHODOLOGY ARC NOW COMPLETE across all 4 major hand-categories.** |
| **Chain-audit arc (S87-S92 closure)** | **5 sessions across HIGH_ONLY + single-pair + two_pair + trips** | **COMPLETE — 4 SHIPS ($214.83/1000h) + 2 NULLs at well-characterized boundaries. Lever is bounded; future ships require either a new chain layer or post-ML-retrain architecture change.** |
| Prefix-coverage methodology question (S86) | How to handle prefix-silent cells in two-grid SHIP standard | RESOLVED THROUGH S92 — EFFECT-SIZE-DOMINANCE rule (S87-S90), TWO-GRID standard for prefix-COVERED (S91), STRUCTURAL collapse detection (S92). 3-pronged applicability test defined. |
| **Option C N=1000 oracle generator infrastructure** | **modify engine to read --id-list-file** | **PROMOTED to S93 PRIMARY — was deferred since S87. Required for retroactive v60 validation and broader two-grid checking. Engineering scope: ~30-60 min Rust mod.** |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 on S90 target hands | DEFERRED — speculative. |

**Cascade verdict (post S92):** Two-track active but chain-audit ARC COMPLETE. v44_RULE13 confirmed as project's largest hidden net-negative layer ($731/1000h cumulative across pair-family). v54+v55+v56+Rule 29 confirmed as most load-bearing infrastructure. The chain-audit lever, after 5 sessions of work, is now bounded.

* **ML cascade:** EXHAUSTED at v44 saturating regime.
* **Rule-layer cascade:** Two patterns:
  - **Rule extraction (Option D-revised):** $16.81 prefix shipped across S83-S86 (1 SHIP, 2 MIXED, 1 MIXED-by-methodology). Diminishing returns; could re-attempt on two_pair LAYOUT_A_SS as S93 SECONDARY.
  - **Chain audit (S87-S92):** $214.83 full-grid shipped across S87-S90 (four consecutive ships); S91 + S92 NULLs at boundaries. ARC COMPLETE.
* **Infrastructure cascade (NEW S93 focus):** Option C N=1000 oracle generator — required to unlock two-grid SHIP standard on arbitrary cell subsets, validate parked v60 ship, enable future smaller-effect rule validation. With chain-audit exhausted, this is the natural next lever.

---

## Resume Prompt (Session 93 — pivot from chain-audit to Option C infrastructure / rule-extraction)

```
Resume Session 93 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S92 — opens with the S93 pivot plan
  + alternative-direction options)
- DECISIONS_LOG.md (latest: Decision 127 — S92 STRUCTURAL NULL on two_pair
  + trips chain audit; v55/v56 blanket routing collapsed chain to v44_dt;
  v44_RULE13 chain bleed magnitudes quantified: $515.80 two_pair + $33.21
  trips; cumulative chain bleed absorbed by v54+v55+v56+Rule 29 = $731;
  CHAIN-AUDIT METHODOLOGY ARC COMPLETE across all 4 major hand-categories;
  3-pronged applicability test with NEW condition (c); two-consecutive-NULL
  signal of lever saturation)
- SESSION_92_REPORT.md (S92 STRUCTURAL NULL, plain-language TL;DR, complete
  chain-audit applicability map, architectural snapshot of $731 absorbed
  bleed)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_pair_v44_per_hand_structural.parquet — pair per-hand
  (audited S91)
- data/drill_two_pair_v44_per_hand_structural.parquet — two_pair per-hand
  (audited S92)
- data/drill_trips_v44_per_hand_structural.parquet — trips per-hand
  (audited S92)
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 20 sessions)
- data/session87/*.log through data/session92/*.log — S87-S92 drill +
  audit + grader logs

STATE (end of S92):
- Production rule chain UNCHANGED at v64_high_only_chain_fix_zone
  ($1,627.36 full / $776.88 prefix). Second consecutive non-ship session
  in chain-audit run.
- ML champion v44_dt UNCHANGED (20 sessions).
- Two-track divergence (remaining gap to oracle): $117.84/1000h (UNCHANGED).
- Rule count: 24 (UNCHANGED).
- Cumulative closure since pre-S68: 91.6% of original $1,409 (UNCHANGED).
- Combined S87-S92 chain-audit recovery: $214.83/1000h
  (S91 + S92 contribute $0).
- v60 from S86 STILL UNSHIPPED, MIXED-by-methodology; waits on Option C
  N=1000 oracle generator (now PROMOTED to S93 PRIMARY).
- KEY S92 ARCHITECTURAL FINDING: v44_RULE13 chain bleeds $+515.80/1000h
  on two_pair prefix (3× the LOW pair bleed S91 found, largest single-
  layer bleed identified in project) and $+33.21 on trips; v55 + v56
  blanket-route 100% to v44_dt and absorb all of it. Cumulative chain
  bleed absorbed by v54+v55+v56+Rule 29 across pair-family: $731/1000h.
  These are the most load-bearing pieces of infrastructure in the project.
- KEY S92 METHODOLOGY FINDING: CHAIN-AUDIT METHODOLOGY ARC COMPLETE.
  5 sessions (S87-S92), 4 SHIPS ($214.83), 2 NULLs at well-characterized
  boundaries (S91 population-divergence noise, S92 structural collapse).
  Pattern has been applied across all 4 major hand-categories. Future
  ships from chain-audit require either a new chain layer or post-ML-
  retrain architecture change.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard." (Strategic priority anchor — see memory
  project_taiwanese_damage_control_priority.md.)
- User is non-technical; any strategic discussion / session report must
  lead with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 93 — pivot from chain-audit to infrastructure / extraction:

  PRIMARY (S93 default plan, PROMOTED from TERTIARY):
  Build Option C N=1000 oracle generator infrastructure.

  Engineering scope: modify engine/src/main.rs to add --id-list-file
  option. The CLI should:
    1. Accept a path to a text file with one canonical_id per line.
    2. Only process those canonical IDs (skip the sequential range
       sweep).
    3. Run the existing N=1000 MC sampler on each.
    4. Write output to a per-cell parquet (per existing oracle grid
       format) or a new sparse format.

  Rationale: chain-audit is exhausted; Option C unlocks (i) retroactive
  validation of v60 from S86 (still MIXED-by-methodology since S86), (ii)
  two-grid SHIP standard on arbitrary cell subsets at N=1000 quality, (iii)
  future smaller-effect rule validation. This is the natural infrastructure
  next-step after the chain-audit work.

  Phase A: read engine/src/main.rs + understand current CLI structure
    (Rust mod). Map out which args/sub-args control the sequential range
    sweep. Identify the cleanest insertion point for --id-list-file.

  Phase B: implement --id-list-file. Test on a small (~1000-id) sample
    first to validate correctness against existing prefix grid.

  Phase C: launch retroactive v60 validation run. v60 from S86 targets
    MID pair × PMID_DS_NOMAXTOP (cid_min 593,072, outside prefix). Run
    N=1000 on a sampled subset of that cell.

  Phase D: session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
    rewrite. End with verbatim resume prompt.

  ALTERNATIVE DIRECTIONS:

  (a) Rule-extraction on two_pair LAYOUT_A_SS (SECONDARY).
      Largest unaddressed within-v44_dt sub-cell: two_pair LAYOUT_A_SS
      at $35.22/1000h on 437,580 hands. Could be amenable to a "drop
      max kicker into bot for DS-like SS structure" rule similar to
      Rule 20's mechanism. S69 tested catalog candidates at aggregate
      but per-sub-cell extraction not exhaustively probed.

  (b) Headline-goal recalibration (TERTIARY).
      Make explicit that 95% match% is unreachable from current
      architecture; reset goal to maximize $/1000h subject to current
      cascade. Affects future NULL-session interpretation.

  (c) v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).

  (d) v44_RULE13 fallthrough replacement (DEFERRED).

  (e) ML retrain — formally closed at v44 (DEFERRED).

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (20 sessions).
- v64_high_only_chain_fix_zone is the production rule chain.
- v55_two_pair_hybrid + v56_trips_hybrid blanket-route their targets to
  v44_dt unconditionally — DO NOT undo this routing without quantifying
  the $515+$33 bleed they currently absorb.
- v54 + Rule 29 absorb $195 of chain bleed on LOW pair (S91 quantified).
- v44_RULE13 chain is the bottom-of-cascade fallthrough; bleeds heavily
  vs v44_dt on pair-family ($731/1000h cumulative); already mostly
  contained by v54/v55/v56/Rule 29.
- The pre-committed-verdict pattern is project standard.
- The 3-pronged CHAIN-AUDIT APPLICABILITY TEST: (a) prefix-silent OR
  (b) ≥$5 both-grid residual, AND (c) production picks differ from
  v44_dt on at least some audit cells [NEW S92].
- The PIVOT GATE pattern (NEW S87, extended S92): cheap pre-drill
  before infrastructure (S87); pre-flight code-trace before pre-drill
  (S92). Each layer of pivot-gate is a cheaper falsifier.
- The STRUCTURAL FEASIBILITY CHECK: for any pivot to a new cell type,
  do a quick combinatorial/code-trace check on whether the cell or
  audit is achievable at all.
- The TWO-CONSECUTIVE-NULL signal (NEW S92): one NULL is noise, two is
  signal of lever saturation; default next-session plan should pivot,
  not default to "more of the same lever."
- A NULL audit session is a COMPLETE cycle. Worth the time.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
