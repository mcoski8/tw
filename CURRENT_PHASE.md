# Current: Sprint 8 — Session 91 CHAIN AUDIT NULL on LOW pair prefix-COVERED cells; production v64 UNCHANGED; key finding: v44_RULE13 rule-based chain bleeds $182/1000h vs v44_dt on LOW pair but v54+Rule 29 absorb 97% — three candidate v65 designs all FAIL two-grid SHIP standard (population-divergence noise dominates residual sub-cell bleeds); first non-ship in chain-audit run (breaks S87-S90 streak of four); methodology lesson: chain-audit on prefix-COVERED cells is dominated by population-divergence noise when residual bleeds are $<$5/1000h

S91 executed the S90-defined PRIMARY path verbatim. Pre-drill on all 1,292,544 LOW pair hands showed v64 LIFTS $92.41/1000h over v44_dt on full grid and $13.36/1000h on prefix — confirming production works as designed. Phase B+ chain audit revealed the architectural source: **v44_RULE13 (the rule-based chain) BLEEDS +$182.28/1000h vs v44_dt** — bigger than any chain bleed found in S87-S90. v54's PBOT_DS→v44_dt hybrid recovers $178.82; v57's Rule 29 recovers another $16.81; production v64 nets +$13.36 LIFT.

Five sub-cell residual bleeds were identified on the prefix grid (totaling +$14.24/1000h):

| Cell × max_sing | n_pref | v44_dt $ | v44_RULE $ | Δ (prefix bleed) | Full grid Δ | Two-grid? |
|---|---:|---:|---:|---:|---:|---|
| PMID_DS_NOMAXTOP × K | 10,080 | $15.32 | $20.14 | +$4.82 | -$6.85 LIFT | DISAGREE |
| PMID_DS_MAXTOP × J | 1,890 | $1.22 | $5.16 | +$3.95 | -$1.14 LIFT | DISAGREE |
| PMID_OTHER × J | 2,030 | $2.29 | $5.53 | +$3.24 | +$0.25 BLEED (weak) | AGREE (sign) |
| PMID_SS_MAXTOP × J | 1,260 | $1.22 | $2.59 | +$1.37 | -$0.46 LIFT | DISAGREE |
| PMID_DS_MAXTOP × T | 945 | $0.99 | $1.85 | +$0.86 | -$0.84 LIFT | DISAGREE |

Three candidate v65 designs were evaluated against pre-committed thresholds (SHIP requires prefix ≥ $5 AND full ≥ $5):

| Candidate | Prefix lift | Full lift | Verdict |
|---|---:|---:|---|
| A: route PMID_DS_NOMAXTOP × K → v44_dt | +$4.82 | -$6.85 | **NULL (grid negative)** |
| B: route {DS_MAXTOP, SS_MAXTOP, OTHER} × J → v44_dt | +$8.56 | -$1.35 | **MIXED (grids disagree)** |
| C: combined all sub-cell bleeds | +$14.24 | ~-$10.00 | **MIXED (grids disagree)** |

**Aggregate S91 verdict: NULL. No new ship.**

The grids disagree because prefix and full evaluate DIFFERENT canonical_id populations within the same nominal sub-cell (prefix is the first 500K canonical IDs — a non-random lower-cid slice). When per-hand effects are small ($0.04-$0.40/hand) and strategy picks correlate with canonical_id ordering, the per-sub-cell aggregate Δ can legitimately diverge in direction. This is "population-divergence noise" — distinct from N=200 winner's curse on the oracle.

**Production state: UNCHANGED.** v64_high_only_chain_fix_zone remains the rule chain ($1,627.36/1000h full / $776.88/1000h prefix). v44_dt remains ML champion (19 sessions unchanged). Rule count: 24. Two-track divergence: $117.84/1000h. Cumulative closure since pre-S68: 91.6%. **Combined S87+S88+S89+S90+S91 chain-audit recovery: $214.83/1000h** (S91 contributes $0).

**FIRST PROJECT-LEVEL FRAMING OF v44_RULE13's role.** The rule-based chain (v44_rule13_three_pair_DS → v43_rule12_two_pair → v42_rule11_jpair_pbot_ds → …) is the fallthrough at the bottom of every project chain layer. It bleeds $182.28/1000h vs v44_dt on LOW pair PMID hands — the LARGEST single-layer bleed identified in the project. **v54 + Rule 29 are load-bearing: they recover $195.63/1000h of this bleed**. Without them, production would be $182 BELOW v44_dt on LOW pair.

> **🎯 IMMEDIATE NEXT ACTION (Session 92): pivot to two_pair chain audit (PRIMARY), OR trips chain audit (SECONDARY), OR build Option C N=1000 oracle infra (TERTIARY)**
>
> The LOW pair chain-audit closed with a clean NULL. S92 should pivot to
> two_pair or trips. Default order:
>
> 1. **PRIMARY** — audit two_pair cells with the chain-audit pattern.
>    Existing per-hand parquet `data/drill_two_pair_v44_per_hand_structural.parquet`
>    (1.34M hands, 7-cell taxonomy: LAYOUT_A_DS, LAYOUT_C_DS, LAYOUT_B_DS,
>    LAYOUT_A_SS, LAYOUT_C_SS_ONLY, LAYOUT_B_SS_ONLY, LAYOUT_OTHER). v55_two_pair_hybrid
>    is the dedicated chain layer (S82 era). Same audit setup as S91:
>    compute v44_dt, v44_RULE13 (= v43_rule12_two_pair_DS_intact), v55, v64
>    layer attributions on prefix grid; per-cell × hi_pair × max_sing
>    breakdown; pre-committed two-grid SHIP grader. Predictable outcome
>    if S91 pattern holds (v55 hybrid absorbs most of chain bleed):
>    residuals likely fail two-grid standard. Worth running once to
>    confirm and to extend the "chain-audit applicability" methodology
>    pattern. Estimated compute: ~5 min total.
>
> 2. **SECONDARY** — audit trips cells with the same pattern. Smaller
>    drill (2.97MB parquet vs 23.9MB for pair). v56_trips_hybrid is
>    the chain layer. ~3 min compute.
>
> 3. **TERTIARY** — build Option C N=1000 oracle generator infrastructure.
>    Required for v60 (S86 MID-pair candidate, MIXED-by-methodology).
>    Engineering scope: modify `engine/src/main.rs` to add `--id-list-file`
>    option (read canonical IDs from a file, only process those).
>    ~30-60 min Rust mod + ~10 min test + launch background K-high run
>    for v60 retroactive validation. Deferred since PRIMARY/SECONDARY
>    use existing infrastructure.
>
> 4. **REFINEMENT (DEFERRED)** — v52-defensive-low partial-effectiveness
>    exploit from S90 (per-hand picker between v52-DL and v44 on S90 target
>    hands). Still speculative.
>
> 5. **HYPOTHESIS (DEFERRED)** — extend Rule 29 gate from Q to K. S83
>    explicitly tested gate=K and chose Q. May be revisitable with the
>    chain-audit lens but unlikely to clear two-grid standard given the
>    S91 finding on PMID_DS_NOMAXTOP × K.

> **📓 METHODOLOGY (Session 92+ — refined through S91):**
>
> 1. **TWO-GRID SHIP STANDARD applied to prefix-COVERED audits for the
>    first time (S91).** S87-S90 used the EFFECT-SIZE-DOMINANCE exception
>    on prefix-SILENT cells. S91 was the first session to apply the
>    proper two-grid standard. The standard correctly NULLed three
>    candidates that would have shipped on prefix-only — confirming the
>    two-grid bar prevents false ships.
>
> 2. **POPULATION-DIVERGENCE NOISE (NEW S91).** Prefix and full grids
>    evaluate DIFFERENT canonical_id populations within the same nominal
>    sub-cell. Prefix is the first 500K canonical IDs — a non-random
>    lower-cid slice. When per-hand effects are small ($0.04-$0.40/hand)
>    and strategy picks correlate with canonical_id ordering, the per-
>    sub-cell aggregate Δ on the two grids can legitimately diverge in
>    DIRECTION. NOT winner's curse on the oracle — strategy-level
>    population effect. The pre-drill ↔ grader match-to-2-decimals signal
>    from S90 only worked because the effect size was large enough to
>    dominate this noise.
>
> 3. **CHAIN-AUDIT APPLICABILITY TEST (NEW S91).** The chain-audit pattern
>    is most productive when EITHER:
>      (a) target cells are prefix-SILENT → EFFECT-SIZE-DOMINANCE
>          exception applies (S87-S90 ships), OR
>      (b) per-sub-cell residual bleeds are ≥ $5/1000h on BOTH grids →
>          population-divergence noise doesn't dominate.
>    On LOW pair PMID cells, neither condition holds, hence NULL.
>
> 4. **v44_RULE13 IS THE PROJECT'S LARGEST HIDDEN NET-NEGATIVE LAYER
>    (NEW S91).** The rule-based chain at the bottom of every project
>    fallthrough bleeds $182.28/1000h vs v44_dt on LOW pair alone.
>    v54's PBOT_DS hybrid routing + v57's Rule 29 are LOAD-BEARING:
>    they recover $195.63/1000h, more than fully compensating for the
>    chain bleed. Future audits should not undo v54's routing.
>
> 5. **PRE-COMMITTED-THRESHOLD PATTERN IS CRITICAL for honest verdicts.**
>    Without locking $5 thresholds in code BEFORE evaluation, the
>    temptation to ship $4.82 prefix bleed (Candidate A) would have been
>    real. The mechanical NULL is the right call.
>
> 6. **A NULL audit session is still a complete cycle.** S87/S88/S89/S90
>    each shipped; S91 doesn't. The methodology produced an honest answer.
>    Worth the session.
>
> 7. **The chain-audit pattern transferred to a DIFFERENT chain architecture
>    (the v54/v55/v56 hybrid + v44_RULE13 fallthrough) but produced a
>    NULL.** The pattern is robust enough to apply cleanly; the cells
>    aren't ripe for new ships under the two-grid standard.

> **✅ ARTIFACTS produced in S91:**
> 1. `analysis/scripts/drill_v64_lo_pair_addressability_S91.py` — Phase A+B pre-drill on full grid (NEW)
> 2. `analysis/scripts/drill_v64_lo_pair_prefix_breakdown_S91.py` — Phase B+ prefix per-sub-cell breakdown (NEW)
> 3. `analysis/scripts/audit_v64_lo_pair_chain_S91.py` — Phase B+ layer attribution (v44_dt → v44_RULE → v54 → v57 → v64) (NEW)
> 4. `analysis/scripts/grade_v65_lo_pair_chain_candidates_S91.py` — Phase C pre-committed grader on 3 candidates (NEW)
> 5. `data/session91/drill_v64_lo_pair_addressability.log`
> 6. `data/session91/drill_v64_lo_pair_prefix_breakdown.log`
> 7. `data/session91/audit_v64_lo_pair_chain.log`
> 8. `data/session91/grade_v65_lo_pair_chain_candidates.log`
> 9. `SESSION_91_REPORT.md` — session report with plain-language TL;DR (NEW)
> 10. `DECISIONS_LOG.md` — Decision 126 (NULL ship + methodology) appended
> 11. `CURRENT_PHASE.md` — this file, rewritten for S92
> 12. `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy change); front-matter "Last updated" line updated only

> Updated: 2026-05-15 (Session 91 end — STRATEGY OF RECORD UNCHANGED: v64 remains production. S91 was the planned execution of the S90-defined PRIMARY path: pivot to LOW pair prefix-COVERED cells with the chain-audit pattern. Phase A confirmed all 6 LOW pair cells are prefix-covered (cid_min 61,085-62,041). Phase B pre-drill on all 1,292,544 LOW pair hands: v64 LIFTS $92.41/1000h over v44_dt on full grid and $13.36 on prefix — production works as designed. Phase B+ chain audit identified the architectural source: v44_RULE13 (the rule-based chain) BLEEDS $182.28/1000h vs v44_dt on LOW pair — biggest single-layer bleed in the project. v54's PBOT_DS hybrid routing + v57's Rule 29 absorb $195.63 of this. Residual sub-cell bleeds totaling $14.24/1000h on prefix DISAGREE with full grid on direction (population-divergence noise — prefix is a non-random lower-cid subset, not a uniform random sample). Three v65 candidates evaluated against pre-committed two-grid thresholds: all FAIL ($5 SHIP bar not cleared on full grid for any). Verdict: NULL — production v64 UNCHANGED. First non-ship in chain-audit run (S87/88/89/90 streak of four broken cleanly). Decision 126 records the NULL + seven methodology refinements: (1) two-grid SHIP standard applied to prefix-COVERED for first time, (2) population-divergence noise is the load-bearing failure mode (NEW), (3) chain-audit applicability test: needs prefix-silent OR ≥$5 per-cell bleed on both grids, (4) v44_RULE13 is project's largest hidden net-negative layer at $182/1000h on LOW pair, (5) v54+Rule 29 are load-bearing (recover $195.63), (6) pre-committed-threshold pattern critical for honest verdicts, (7) NULL audit is a complete cycle. S92 default plan: pivot to two_pair chain audit (PRIMARY), OR trips chain audit (SECONDARY), OR build Option C N=1000 oracle infra (TERTIARY).)

---

## Headline state at end of Session 91 (UNCHANGED from S90)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v64_high_only_chain_fix_zone** | PRODUCTION rule chain. **$1,627.36/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 19 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$117.84/1000h (UNCHANGED).** Cumulative closure since pre-S68: $1,291.16 = **91.6% of original $1,409 (UNCHANGED).**

Production vs v44_dt: production outperforms ML by **$546/1000h** (UNCHANGED).

**Total project rule count: 24** (UNCHANGED).

**S91 candidate result (NULL):**

| Candidate | Mechanism | Prefix lift | Full lift | Verdict |
|---|---|---:|---:|---|
| A: extend v54 routing to LOW × PMID_DS_NOMAXTOP × max_sing=K | gate-out sub-cell to v44_dt | +$4.82 | -$6.85 | **NULL** |
| B: extend v54 routing to LOW × {DS_MAXTOP, SS_MAXTOP, OTHER} × max_sing=J | gate-out 3 sub-cells | +$8.56 | -$1.35 | **MIXED→NULL** |
| C: combined — all sub-cell residuals | gate-out 5 sub-cells | +$14.24 | ~-$10.00 | **MIXED→NULL** |

---

## Hypothesis cascade status (updated after S91)

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
| Headline-goal recalibration | Concede 95% match% as unreachable | LESS URGENT post-S87-S90 (extraction track demonstrably productive via chain-audit), reaffirmed by S91 (chain-audit applicability has limits on prefix-COVERED cells). |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). Re-confirmed via S91 layer attribution. |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86) | MID × PMID_DS_NOMAXTOP | MIXED-BY-METHODOLOGY — full +$6.43 SHIP, prefix silent; v60 still UNSHIPPED (Decision 121). |
| DAMAGE-CONTROL chain audit cell #1 (S87) | HIGH_ONLY × DS_NO_JOINT × {J-A} v52-chain regression | SHIPPED — Rule 21 + $98.67 full-grid (Decision 122). |
| DAMAGE-CONTROL chain audit cell #2 (S88) | HIGH_ONLY × {DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH} × {J-A} v47-chain regression | SHIPPED — Rule 22 + $98.84 full-grid (Decision 123). |
| DAMAGE-CONTROL chain audit cell #3 (S89) | HIGH_ONLY × {JOINT_MED, JOINT_LOW} × {J-A} v47-chain regression | SHIPPED — Rule 23 + $10.09 full-grid (Decision 124). |
| DAMAGE-CONTROL chain audit cell #4 (S90) | HIGH_ONLY × {5 cells} × {8, 9, T} v47-chain regression (first v52-defensive-low audit) | SHIPPED — Rule 24 + $7.23 full-grid (Decision 125). HIGH_ONLY × max ≥ 8 ZONE COMPLETE. |
| **DAMAGE-CONTROL chain audit cell #5 (S91)** | **LOW pair PMID prefix-COVERED cells (FIRST prefix-COVERED chain audit)** | **NULL — three candidates all FAIL two-grid SHIP standard (Decision 126). v44_RULE13 chain bleeds $182/1000h but v54+Rule 29 absorb $195. POPULATION-DIVERGENCE NOISE methodology lesson identified.** |
| Chain-audit expansion (S92+) | two_pair / trips cells with the chain-audit pattern | OPEN — primary S92 direction |
| Prefix-coverage methodology question (S86) | How to handle prefix-silent cells in two-grid SHIP standard | PARTIALLY RESOLVED — EFFECT-SIZE-DOMINANCE rule defined and applied four times (S87-S90); S91 extended the methodology to prefix-COVERED with POPULATION-DIVERGENCE NOISE finding. |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 on S90 target hands | DEFERRED — speculative. |

**Cascade verdict (post S91):** Two-track active. Chain-audit pattern transferred to a FIFTH session but NULLed cleanly. v44_RULE13 confirmed as the project's largest hidden net-negative layer.

* **ML cascade:** EXHAUSTED at v44 saturating regime.
* **Rule-layer cascade:** Two patterns active:
  - **Rule extraction (Option D-revised):** $16.81 prefix shipped across S83-S86 (1 SHIP, 2 MIXED, 1 MIXED-by-methodology). Diminishing returns.
  - **Chain audit (S87-S91):** $214.83 full-grid shipped across S87-S90 (four consecutive ships); S91 NULL on first prefix-COVERED pivot. S92 candidates: two_pair / trips cells.

---

## Resume Prompt (Session 92 — pivot to two_pair / trips chain audit)

```
Resume Session 92 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S91 — opens with the S92 pivot plan
  + alternative-direction options)
- DECISIONS_LOG.md (latest: Decision 126 — S91 NULL on LOW pair chain
  audit; v44_RULE13 chain bleeds $182/1000h vs v44_dt on LOW pair but
  v54+Rule 29 absorb $195.63; three v65 candidates failed two-grid SHIP
  standard due to population-divergence noise on prefix vs full grids;
  combined S87-S91 chain-audit recovery still $214.83/1000h; methodology
  refinements: chain-audit applicability test, population-divergence
  noise definition, two-grid SHIP standard reaffirmed)
- SESSION_91_REPORT.md (S91 NULL verdict, plain-language TL;DR,
  v44_RULE13 chain bleed framing, chain-audit applicability lesson)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_pair_v44_per_hand_structural.parquet — LOW pair per-hand
  (now audited)
- data/drill_two_pair_v44_per_hand_structural.parquet — two_pair per-hand
  drill (1.34M rows, 7-cell taxonomy: LAYOUT_A_DS, LAYOUT_C_DS, LAYOUT_B_DS,
  LAYOUT_A_SS, LAYOUT_C_SS_ONLY, LAYOUT_B_SS_ONLY, LAYOUT_OTHER) — S92
  PRIMARY target
- data/drill_trips_v44_per_hand_structural.parquet — trips per-hand
  drill (smaller; S92 SECONDARY target)
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 19 sessions)
- data/session87/*.log through data/session91/*.log — S87-S91 drill +
  audit + grader logs

STATE (end of S91):
- Production rule chain UNCHANGED at v64_high_only_chain_fix_zone
  ($1,627.36 full / $776.88 prefix). First non-ship in chain-audit run.
- ML champion v44_dt UNCHANGED (19 sessions).
- Two-track divergence (remaining gap to oracle): $117.84/1000h (UNCHANGED).
- Rule count: 24 (UNCHANGED).
- Cumulative closure since pre-S68: 91.6% of original $1,409 (UNCHANGED).
- Combined S87+S88+S89+S90+S91 chain-audit recovery: $214.83/1000h
  (S91 contributes $0).
- v60 from S86 STILL UNSHIPPED, MIXED-by-methodology; waits on Option C
  N=1000 oracle generator (still deferred).
- KEY S91 ARCHITECTURAL FINDING: v44_RULE13 rule-based chain bleeds
  $182.28/1000h vs v44_dt on LOW pair. v54's PBOT_DS hybrid routing
  + v57's Rule 29 absorb $195.63 — they are load-bearing.
- KEY S91 METHODOLOGY FINDING: POPULATION-DIVERGENCE NOISE between
  prefix and full grids prevents two-grid SHIP standard from
  triggering on small per-sub-cell bleeds ($1-5/1000h). Not winner's
  curse; strategy-level effect.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard." (Strategic priority anchor — see memory
  project_taiwanese_damage_control_priority.md.)
- User is non-technical; any strategic discussion / session report must
  lead with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 92 — pivot to two_pair / trips chain audit:

  PRIMARY (S92 default plan):
  Audit two_pair cells with the chain-audit pattern.

  Use S91 scripts as templates:
    drill_v64_lo_pair_addressability_S91.py  → drill_v64_two_pair_addressability_S92.py
    drill_v64_lo_pair_prefix_breakdown_S91.py → optional, mostly redundant
    audit_v64_lo_pair_chain_S91.py           → audit_v64_two_pair_chain_S92.py
    grade_v65_lo_pair_chain_candidates_S91.py → grade_v65_two_pair_chain_candidates_S92.py

  Phase A: load drill_two_pair_v44_per_hand_structural.parquet. Identify
    7 cells. Apply structural feasibility check. Check prefix coverage
    (cid_min per cell).

  Phase B: pre-drill — re-evaluate v64 vs v44 on every two_pair hand on
    full grid. Per-cell × hi_pair_rank × max_sing breakdown.

  Phase B+: chain audit — layer attribution v44_dt → v44_RULE (= chain
    fallthrough) → v55 (two_pair_hybrid) → v64. Identify sub-cells where
    chain bleeds vs v44_dt after v55's routing.

  Phase C: design v65 candidates if any sub-cell residual ≥ $5 on both
    grids. Pre-committed thresholds: SHIP $5 prefix AND $5 full
    (two-grid agreement required).

  Phase D: session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
    rewrite. End with verbatim resume prompt.

  ALTERNATIVE DIRECTIONS:

  (a) Audit trips cells with same pattern. Smaller drill (2.97MB parquet
      vs 10.8MB for two_pair). v56_trips_hybrid is the chain layer.
      ~3 min compute.

  (b) Build Option C N=1000 oracle generator infrastructure.
      Engineering scope: modify engine/src/main.rs to add --id-list-file
      option. ~30-60 min Rust mod + ~10 min test.

  (c) v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).

  (d) v44_RULE13 net-negative finding (NEW S91) — investigate whether
      a different rule-chain fallthrough could replace v44_RULE13 for
      pair cells. Speculative engineering.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (19 sessions).
- v64_high_only_chain_fix_zone is the production rule chain.
- v44_RULE13 is the rule-based fallthrough (NOT v44_dt) — bleeds $182/1000h
  on LOW pair PMID hands. v54 + Rule 29 absorb this. DO NOT undo v54's
  routing.
- The pre-committed-verdict pattern is project standard.
- The EFFECT-SIZE-DOMINANCE exception for prefix-silent cells:
  effect ≫ noise floor by 20×+ AND rule is a gate-out → bypass two-grid
  standard with documentation. S87-S90 all shipped under this; S91 had
  prefix-covered cells so the standard kicked in.
- The CHAIN AUDIT pattern: layer-by-layer attribution. v44_dt vs the
  rule-based v44_RULE13 chain is the key comparison for pair/two_pair/trips.
- The CHAIN-AUDIT APPLICABILITY TEST (NEW S91): pattern is most productive
  when EITHER (a) prefix-silent target (EFFECT-SIZE-DOMINANCE applies) OR
  (b) per-sub-cell residual ≥ $5/1000h on BOTH grids.
- The POPULATION-DIVERGENCE NOISE (NEW S91): prefix is a non-random
  lower-cid subset of full grid; per-sub-cell Δ can legitimately diverge
  in direction on small effects. NOT winner's curse — strategy-level
  effect.
- The PIVOT GATE pattern: cheap pre-drill (≤5 min) BEFORE committing to
  expensive infrastructure or pivots.
- The STRUCTURAL FEASIBILITY CHECK: for any chain-audit pivot to a new
  cell type, do a quick combinatorial check on whether the cell is
  achievable at all.
- A NULL audit session is a COMPLETE cycle. Worth the time.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
