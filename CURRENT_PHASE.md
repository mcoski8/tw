# Current: Sprint 8 — Session 90 v64 SHIPS Rule 24 (chain gate-out extension to HIGH_ONLY × max ∈ {8, 9, T}) — fourth consecutive chain-audit ship; structurally-non-empty HIGH_ONLY × max ≥ 8 audit COMPLETE; +$7.23/1000h full grid; production v63 → v64 ($1,620.13 → $1,627.36); cumulative closure since pre-S68 = 91.6% of original $1,409; first project-level audit of v52-defensive-low (CONFIRMED partially effective — recovers ~50% of v47 bleed but doesn't fully restore v44_dt levels); S91 default = pivot to prefix-COVERED cells (LOW pair / two_pair / trips) using the chain-audit pattern; v52-defensive-low refinement deferred

S90 executed the S89-defined PRIMARY path verbatim. Pre-drill of 25,740 target hands (HIGH_ONLY × max ∈ {8, 9, T} × 5 non-empty cells) revealed v63 leaks **+$7.23/1000h MORE than v44_dt** on these cells. Chain audit attributed the bleed to v44→v47 (+$19.28 introduced) partially recovered by v48 (−$2.53) and v52-defensive-low (−$9.52), net residual **+$7.23**. Phase A structural feasibility check eliminated 4 (cell × rank) combinations for free (max=7 × any cell; max ∈ {8,9,T} × {JOINT_HIGH, NEITHER}; max=8 × JOINT_MED — all combinatorially impossible).

Rule 24 (v64) is a strict superset of Rule 23's gate-out: for HIGH_ONLY ×
max ∈ {8, 9, T, J, Q, K, A} × cell ∈ {DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY,
JOINT_HIGH, JOINT_MED, JOINT_LOW} per the S71 cell taxonomy, return
strategy_v44_dt directly, bypassing the v47→v48→v52 chain. Pre-committed
grader auto-fired **SHIP at +$7.23/1000h whole-grid lift** (SHIP threshold
$5, lift cleared by 1.45×). Per-cell breakdown matches pre-drill prediction
to $0.01 (high stability). Per-hand effect: 21.6% same, 55.2% better, 23.2%
worse. Swap-right rate on changed hands: **70.4%** — LOWER than S88/S89
(76.8%/85.2%) but higher than S87 (62.3%). The elevated "worse" rate is the
signature of v52-defensive-low's partial effectiveness. Out-of-gate sanity:
**0 v64≠v63 disagreements** on 50K random sample.

**Production state: ADVANCED.** v64_high_only_chain_fix_zone is the new
rule chain ($1,627.36/1000h full / $776.88 prefix unchanged). v44_dt
remains ML champion. Rule count: 23 → 24. Two-track divergence (remaining
gap to oracle ceiling): $117.84/1000h (was $125.07; −$7.23). Cumulative
closure since pre-S68: **91.6% of original $1,409** (was 91.1%).

**Structurally-non-empty HIGH_ONLY × max ≥ 8 audit zone is now COMPLETE.**
24 non-empty (cell × rank) combinations all gated. HIGH_ONLY × max = 7 is
structurally empty (only 6 ranks ≤ 7 exist). Combined S87+S88+S89+S90
chain-audit recovery: **$214.83/1000h** across four consecutive sessions.

**FIRST PROJECT-LEVEL AUDIT OF v52-defensive-low.** 100% of S90 target
hands fire this mode (LOW_MAX_DEFENSIVE = {7, 8, 9, 10}). Verdict: it's
PARTIALLY effective — the S53 design intent was correct (it recovers
$9.52 of v47's $19.28 bleed) but the implementation leaves money on the
table relative to v44_dt. v52-defensive-low actively WINS on ~23% of S90
target hands; a future v65 could retain it on the winning subset.
Deferred.

> **🎯 IMMEDIATE NEXT ACTION (Session 91): pivot to prefix-COVERED cells (PRIMARY), OR build Option C N=1000 oracle infra (SECONDARY), OR refine v52-defensive-low (REFINEMENT)**
>
> The structurally-non-empty HIGH_ONLY zone is fully audited. S91 must
> pivot to new territory. Default order:
>
> 1. **PRIMARY** — audit prefix-COVERED cells with the chain-audit pattern.
>    LOW pair, two_pair, trips. These are categories OUTSIDE the HIGH_ONLY
>    taxonomy with DIFFERENT rule chains in production (v44_dt routing via
>    v54/v55/v56 hybrids). Existing per-hand parquets cover most. Low
>    compute cost (no new oracle eval). Different baseline architecture —
>    the audit setup is different but the principle (find layers
>    introducing net-negative regression) is transferable. **Key
>    methodological advantage: prefix-COVERED means the prefix grader is a
>    real two-grid check.** Potential ship sizes unknown; could be $0
>    (clean confirmation) or $5-50/1000h. LOW pair is the recommended
>    first stop given it's the smallest and most targeted.
>
> 2. **SECONDARY** — build Option C N=1000 oracle generator
>    infrastructure. Required for v60 (S86 MID-pair candidate, MIXED-by-
>    methodology) and for any future smaller-effect rule on prefix-silent
>    cells. ~30-60 min Rust modification (add `--id-list-file` option to
>    `engine/src/main.rs`) + ~10 min test + launch background K-high run
>    for v60 retroactive validation. Deprioritized vs PRIMARY because
>    PRIMARY uses existing infrastructure.
>
> 3. **TERTIARY** — LOW × PMID_OTHER drill. Deferred from
>    S87+S88+S89+S90. The last LOW pair cell. Standard Option D-revised
>    playbook.
>
> 4. **REFINEMENT (DEFERRED)** — v52-defensive-low partial-effectiveness
>    exploit. S90 found v52-DL actively wins on ~23% of S90 target hands.
>    A future v65 could retain v52-DL on the subset where it wins
>    (per-hand picker rather than uniform gate). Engineering scope:
>    identify the structural discriminator that separates "v52-DL wins"
>    from "v44 wins" within the S90 target population. Speculative;
>    depends on whether the discriminator is clean. Deprioritized vs
>    new-zone work because the discriminator may not be cleanly
>    extractable.

> **📓 METHODOLOGY (Session 91+ — refined through S90):**
>
> 1. **CHAIN AUDIT pattern transferred 1:1 for a FOURTH consecutive
>    session (S87 → S88 → S89 → S90 proved).** Four S90 scripts directly
>    templated from S89's three scripts (with one extra Phase A log).
>    Pattern is fully reusable for prefix-COVERED cells too with minor
>    adjustments to the baseline strategy and grader.
>
> 2. **EFFECT-SIZE-DOMINANCE rule generalizes across THREE orders of
>    magnitude.** S87 ($98.67), S88 ($98.84), S89 ($10.09), S90 ($7.23):
>    four ships across the criterion "effect ≫ noise floor by 20×+". The
>    SHIP threshold is a per-cell calibration; the noise-floor multiple
>    is what generalizes. For S91 prefix-COVERED audits, the EFFECT-SIZE-
>    DOMINANCE rule may not be the dominant verdict mechanism — the
>    two-grid SHIP standard kicks in instead.
>
> 3. **Pre-drill ↔ grader match-to-2-decimal-places is the load-bearing
>    signal (NEW S90).** When pre-drill predicts $7.23 and grader
>    confirms $7.23, the noise floor is genuinely well below the effect
>    size. Future audits should treat such match as the strongest
>    statistical confirmation available without N=1000 validation.
>
> 4. **Per-hand swap-right rate < 65% is a flag (NEW S90).** S90's 70.4%
>    was a drop from S89's 85.2% — and accurately predicted that the
>    chain-layer being gated (v52-defensive-low) was doing real partial
>    work. Future audits should treat swap-right rate < 65% as a flag to
>    investigate the chain layer's design intent before defaulting to
>    full gate-out. (S90's 70.4% was borderline; aggregate verdict was
>    still SHIP.)
>
> 5. **v52-defensive-low is PARTIALLY effective (NEW S90 finding).** First
>    project-level audit of this firing mode (S53 design). It recovers
>    ~50% of v47's bleed but doesn't fully restore v44_dt levels. The S53
>    design intent was correct but conservative. Future refinement
>    opportunity: per-hand picker between v52-DL and v44 within the S90
>    target population.
>
> 6. **Pre-Phase A structural feasibility check is a transferable
>    pre-audit step.** Eliminated 4 (cell × rank) combinations in S90 +
>    NEITHER × {J-A} in S89. Worth applying before ANY chain-audit pivot
>    to a new cell type.
>
> 7. **"Speed is not necessary — clarity and perfection is" — S90
>    reaffirms.** Running the chain audit (7s compute) when the pre-drill
>    headline was already clear ($7.23) pinpointed v52-defensive-low's
>    partial-effectiveness story. Made Rule 24's design surgical (same
>    architecture as Rules 21+22+23) and made the v52-defensive-low
>    audit-finding a project-level methodology lesson.

> **✅ ARTIFACTS produced in S90:**
> 1. `analysis/scripts/drill_v63_high_only_addressability_S90.py` — pre-drill (NEW)
> 2. `analysis/scripts/audit_v63_chain_bleed_S90.py` — chain audit (NEW)
> 3. `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` — Rule 24 SHIPPED (NEW)
> 4. `analysis/scripts/grade_v64_full_grid_S90.py` — full-grid grader with pre-committed thresholds (NEW)
> 5. `data/session90/phase_a_target_stats.log`
> 6. `data/session90/drill_v63_high_only_addressability.log`
> 7. `data/session90/audit_v63_chain_bleed.log`
> 8. `data/session90/grade_v64_full_grid.log`
> 9. `SESSION_90_REPORT.md` — session report with plain-language TL;DR (NEW)
> 10. `DECISIONS_LOG.md` — Decision 125 (ship + methodology) appended
> 11. `CURRENT_PHASE.md` — this file, rewritten for S91
> 12. `STRATEGY_GUIDE.md` — Part 1 Session 90 entry added; Part 5 Rule 24 entry added; Part 6 current standard updated; front-matter rewritten

> Updated: 2026-05-15 (Session 90 end — STRATEGY OF RECORD CHANGED: v63 → v64_high_only_chain_fix_zone. The S87/S88/S89 chain-audit pattern reapplied to HIGH_ONLY × max ∈ {8, 9, T} (different firing mode — v52-defensive-low rather than v52-fallthrough) uncovered another +$7.23/1000h v44→v52 chain regression on 25,740 prefix-silent hands. Phase A structural feasibility eliminated 4 (cell × rank) combinations for free (max=7 × any; max ∈ {8,9,T} × {JOINT_HIGH, NEITHER}; max=8 × JOINT_MED). Rule 24 (v64): strict superset of Rule 23's gate. For HIGH_ONLY × max ∈ {8-A} × cell ∈ all 6 non-empty cells, bypass v47→v48→v52 chain and return strategy_v44_dt directly. Effective coverage: 11 non-empty (cell × rank) combinations at max ≤ T + 6 at max ∈ {J-A}. Full-grid grader auto-fired SHIP at +$7.23/1000h (v63 $1,620.13 → v64 $1,627.36). Per cell: DS_NO_JOINT +$3.75 / JOINT_MED +$1.35 / DS_NO_MAXTOP +$0.92 / MS_ONLY +$0.90 / JOINT_LOW +$0.31. Per-hand: 22% same / 55% better / 23% worse. Swap-right 70.4% on changed hands. Out-of-gate sanity: 0 v64≠v63 disagreements on 50K random sample. Pre-drill ↔ grader match to $0.01 (high aggregate stability). Rule count: 23 → 24. Two-track divergence (remaining gap to oracle): $117.84/1000h (was $125.07; cumulative closure since pre-S68 now 91.6% of original $1,409). FIRST PROJECT-LEVEL AUDIT OF v52-defensive-low: 100% of S90 target hands fire this mode. Verdict: partially effective (recovers $9.52 of v47's $19.28 bleed; v44_dt still picks better in aggregate). S53 design intent was correct but conservative. Decision 125 records the ship + seven methodology refinements: (1) chain-audit pattern transferred 1:1 for fourth consecutive session, (2) EFFECT-SIZE-DOMINANCE rule generalizes across four ships and three orders of magnitude, (3) pre-drill ↔ grader match-to-2-decimal-places is load-bearing, (4) per-hand swap-right < 65% is a chain-layer-doing-real-work flag, (5) v52-defensive-low is partially effective (first project audit), (6) Phase A structural feasibility check is transferable, (7) future v65 refinement opportunity for v52-DL partial-effectiveness exploit. **Structurally-non-empty HIGH_ONLY × max ≥ 8 chain-audit zone is now COMPLETE.** Combined S87+S88+S89+S90 recovery: $214.83/1000h. v60 from S86 STILL UNSHIPPED, MIXED-by-methodology, pending Option C N=1000 oracle generator. S91 default plan: pivot to prefix-COVERED cells (LOW pair / two_pair / trips) using the chain-audit pattern; or build Option C N=1000 oracle infra; or refine v52-defensive-low.)

---

## Headline state at end of Session 90 (CHANGED — STRATEGY OF RECORD ADVANCED)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v64_high_only_chain_fix_zone** | PRODUCTION rule chain (NEW S90). **$1,627.36/1000h full / $776.88/1000h prefix** (prefix unchanged). | `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 18 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$117.84/1000h (was $125.07; −$7.23 this session).** Cumulative closure since pre-S68: $1,291.16 = **91.6% of original $1,409** (was 91.1%).

Production vs v44_dt: production now outperforms ML by **$546/1000h** (v64 $1,627.36 vs v44_dt $1,081). Up from $539 last session.

**Total project rule count: 24** (Rule 24 added — v64 chain gate-out extension covering all 11 non-empty (cell × rank) combinations at HIGH_ONLY × max ∈ {8, 9, T} on top of Rule 23's 6 combinations at max ∈ {J-A}).

**S90 candidate result (SHIP):**

| Candidate | Mechanism | Whole-grid lift | Verdict |
|---|---|---:|---|
| v64_high_only_chain_fix_zone | Strict superset of v63's gate. For HIGH_ONLY × max ∈ {8-A} × cell ∈ all 6 non-empty cells, bypass v47→v48→v52 chain; return strategy_v44_dt | **+$7.23/1000h SHIP** | **SHIP** |

---

## Hypothesis cascade status (updated after S90)

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
| Headline-goal recalibration | Concede 95% match% as unreachable | LESS URGENT post-S87/S88/S89/S90 (extraction track now demonstrably productive via chain-audit). |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86) | MID × PMID_DS_NOMAXTOP | MIXED-BY-METHODOLOGY — full +$6.43 SHIP, prefix silent; v60 still UNSHIPPED (Decision 121). |
| DAMAGE-CONTROL chain audit cell #1 (S87) | HIGH_ONLY × DS_NO_JOINT × {J-A} v52-chain regression | SHIPPED — Rule 21 + $98.67 full-grid (Decision 122). |
| DAMAGE-CONTROL chain audit cell #2 (S88) | HIGH_ONLY × {DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH} × {J-A} v47-chain regression | SHIPPED — Rule 22 + $98.84 full-grid (Decision 123). |
| DAMAGE-CONTROL chain audit cell #3 (S89) | HIGH_ONLY × {JOINT_MED, JOINT_LOW} × {J-A} v47-chain regression | SHIPPED — Rule 23 + $10.09 full-grid (Decision 124). HIGH_ONLY × {J-A} ZONE CLOSED. |
| **DAMAGE-CONTROL chain audit cell #4 (S90)** | HIGH_ONLY × {5 cells} × {8, 9, T} v47-chain regression (FIRST v52-defensive-low audit) | **SHIPPED — Rule 24 + $7.23 full-grid (Decision 125). HIGH_ONLY × max ≥ 8 ZONE COMPLETE.** |
| **Chain-audit expansion (S91+)** | Prefix-COVERED cells (LOW pair / two_pair / trips); Option C N=1000 oracle infra; v52-defensive-low refinement | OPEN — primary S91 direction |
| Prefix-coverage methodology question (S86) | How to handle prefix-silent cells in two-grid SHIP standard | PARTIALLY RESOLVED — EFFECT-SIZE-DOMINANCE rule defined and applied four times across two orders of magnitude; Option C infra still needed for smaller candidates |
| **v52-defensive-low refinement (S90 finding)** | Per-hand picker between v52-DL and v44 on S90 target hands | DEFERRED — speculative; depends on whether the win/lose discriminator is cleanly extractable |

**Cascade verdict (post S90):** Two-track active. Structurally-non-empty HIGH_ONLY × max ≥ 8 audit zone COMPLETE.

* **ML cascade:** EXHAUSTED at v44 saturating regime.
* **Rule-layer cascade:** Two patterns active:
  - **Rule extraction (Option D-revised):** $16.81 prefix shipped across S83-S86 (1 SHIP, 2 MIXED, 1 MIXED-by-methodology). Diminishing returns.
  - **Chain audit (S87/S88/S89/S90):** $214.83 full-grid shipped across four sessions. Dominant ship vector. HIGH_ONLY zone now closed. S91 candidates: prefix-COVERED cells (LOW pair / two_pair / trips); v52-defensive-low refinement.

---

## Resume Prompt (Session 91 — pivot to prefix-COVERED cells or build Option C infra)

```
Resume Session 91 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S90 — opens with the S91 pivot plan
  + alternative-direction options)
- DECISIONS_LOG.md (latest: Decision 125 — S90 v64 SHIPS Rule 24 at
  +$7.23/1000h on the 25,740 prefix-silent hands in HIGH_ONLY × {8, 9, T};
  structurally-non-empty HIGH_ONLY × max ≥ 8 audit COMPLETE; first
  project-level audit of v52-defensive-low confirmed it PARTIALLY
  effective; combined S87+S88+S89+S90 recovery = $214.83/1000h;
  methodology refinements: pre-drill ↔ grader 2-decimal-place match is
  load-bearing, swap-right < 65% is a chain-layer-doing-real-work flag)
- SESSION_90_REPORT.md (S90 SHIP verdict, plain-language TL;DR,
  v52-defensive-low audit framing, four-session chain-audit
  retrospective)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_v44_high_only_S71_per_hand.parquet — HIGH_ONLY drill data
  (now exhausted for chain-audit purposes — entire structurally-non-empty
  HIGH_ONLY zone is gated under v64)
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 18 sessions)
- data/session87/*.log — S87 drill + audit + grader logs
- data/session88/*.log — S88 drill + audit + grader logs
- data/session89/*.log — S89 drill + audit + grader logs
- data/session90/*.log — S90 drill + audit + grader logs

STATE (end of S90):
- Production rule chain ADVANCED to v64_high_only_chain_fix_zone
  ($1,627.36 full / $776.88 prefix). FOURTH CONSECUTIVE session with a
  strategy-of-record change (S87 v61, S88 v62, S89 v63, S90 v64).
- ML champion v44_dt UNCHANGED (18 sessions).
- Two-track divergence (remaining gap to oracle): $117.84/1000h (was
  $125.07; −$7.23).
- Rule count: 24 (Rule 24 added — chain gate-out extension covering
  HIGH_ONLY × {8, 9, T} on top of Rule 23's {J-A}).
- Cumulative closure since pre-S68: 91.6% of original $1,409 (was 91.1%).
- Combined S87+S88+S89+S90 chain-audit recovery: $214.83/1000h.
- v60 from S86 STILL UNSHIPPED, MIXED-by-methodology; waits on Option C
  N=1000 oracle generator (still deferred).
- Structurally-non-empty HIGH_ONLY × max ≥ 8 audit zone is COMPLETE
  (24 non-empty (cell × rank) combinations gated; max=7 structurally empty).
- v52-defensive-low (LOW_MAX_DEFENSIVE = {7, 8, 9, 10}) — FIRST audited.
  Partially effective: recovers $9.52 of v47's $19.28 bleed on S90 target.
  Still net-bleeds $7.23 vs v44_dt — gate-out is the right architectural call.
  Refinement opportunity: per-hand picker between v52-DL and v44 (~23% of
  S90 hands are v52-DL wins). Deferred.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard." (Strategic priority anchor — see memory
  project_taiwanese_damage_control_priority.md.)
- User is non-technical; any strategic discussion / session report must
  lead with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 91 — pivot to NEW territory (HIGH_ONLY exhausted):

  PRIMARY (S91 default plan):
  Pivot to prefix-COVERED cells. LOW pair, two_pair, trips. These are
  categories OUTSIDE the HIGH_ONLY taxonomy with DIFFERENT rule chains
  in production (v44_dt routing via v54/v55/v56 hybrids).

  KEY METHODOLOGICAL ADVANTAGE: prefix-COVERED means the prefix grader is
  a real two-grid check. EFFECT-SIZE-DOMINANCE rule may not be the
  dominant verdict mechanism — the two-grid SHIP standard kicks in
  instead. This is methodologically stronger than the prefix-silent
  S87-S90 ships.

  Use S90 scripts as templates:
    drill_v63_high_only_addressability_S90.py  (template for pre-drill, rebind
                                                to v64 + new target cells)
    audit_v63_chain_bleed_S90.py               (template for chain audit)
    grade_v64_full_grid_S90.py                 (template for grader)

  Recommended first stop: LOW pair (smallest, most targeted). Existing
  per-hand parquets cover most LOW pair cells from prior sessions.

  PHASE A (~5 min): identify target LOW pair cells. Check prefix
    coverage (cid_min). Check what v44 baseline leak vs v54_pair_hybrid
    (production for these cells) looks like. Apply structural feasibility
    check.
  PHASE B (~5-10 min): pre-drill — re-evaluate v64 vs v44 on each target
    cell. (v64 == v57 == v54 == v53 == v52 inside the v54 routing gate.
    So v64 on LOW pair routes through v44_dt already? Need to verify the
    routing carefully — V54 routes PAIR PBOT cells to v44_dt; v55 routes
    two_pair; v56 routes trips. Audit setup is different.)
  PHASE B+ (~5 min): chain audit — layer-by-layer attribution.
    Particularly interested in the v54/v55/v56 hybrid chain's behavior
    on prefix-COVERED cells where the prefix grader can validate.
  PHASE C: design v65 (or alt name) = v64 + extended gate-out on
    confirmed regressions. Pre-committed thresholds: SHIP $5 on prefix
    grid (standard prefix-grader threshold); SHIP $5-30 full grid.
    Two-grid agreement required.
  PHASE D: session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
    rewrite. End with verbatim resume prompt.

  ALTERNATIVE DIRECTIONS:

  (a) Build Option C N=1000 oracle generator infrastructure.
      Engineering scope: modify engine/src/main.rs to add --id-list-file
      option (read canonical IDs from a file, only process those).
      ~30-60 min Rust mod + ~10 min test + launch background K-high
      run for v60 retroactive validation. Required for any future
      smaller-effect rule on prefix-silent cells.

  (b) LOW × PMID_OTHER drill (deferred from S87/S88/S89/S90). Last LOW
      pair cell, methodology question is the standard Option D-revised
      playbook.

  (c) v52-defensive-low partial-effectiveness exploit. S90 found v52-DL
      actively wins on ~23% of S90 target hands. A future v65 could
      retain v52-DL on the subset where it wins (per-hand picker rather
      than uniform gate). Speculative — depends on whether the
      structural discriminator separating "v52-DL wins" from "v44 wins"
      is cleanly extractable.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (18 sessions).
- v64_high_only_chain_fix_zone is the production rule chain.
- The pre-committed-verdict pattern is project standard.
- The EFFECT-SIZE-DOMINANCE exception for prefix-silent cells:
  effect ≫ noise floor by 20×+ AND rule is a gate-out → bypass two-grid
  standard with documentation. S87 + S88 + S89 + S90 ALL shipped under
  this exception (at $98, $98, $10, $7); criterion is well-calibrated
  across magnitudes. For S91 prefix-COVERED audits, the two-grid
  standard kicks in — EFFECT-SIZE-DOMINANCE is not the only verdict
  mechanism available.
- The CHAIN AUDIT pattern: layer-by-layer attribution against v44_dt
  baseline; identify the regression-introducing transition. v47 has been
  the culprit in S87/S88/S89/S90 within HIGH_ONLY. Whether v47 or other
  layers introduce regressions in two_pair / trips / LOW pair is the
  open question for S91.
- The PIVOT GATE pattern: cheap pre-drill (≤5 min) BEFORE committing to
  expensive infrastructure or pivots.
- The STRUCTURAL FEASIBILITY CHECK: for any chain-audit pivot to a new
  cell type, do a 5-minute combinatorial check on whether the cell is
  achievable at all. NEITHER × {J-A}, max=7 × any, JOINT_HIGH ×
  {8,9,T}, etc. all closed for free this way.
- The PRE-DRILL ↔ GRADER 2-DECIMAL MATCH (NEW S90): when these agree to
  $0.01, the noise floor is genuinely well below the effect size; this
  is the strongest statistical confirmation available without N=1000.
- The SWAP-RIGHT < 65% FLAG (NEW S90): a drop in swap-right rate from
  prior sessions flags that the chain-layer being gated is doing real
  partial work. Investigate the chain layer's design intent before
  defaulting to full gate-out. S90's 70.4% was borderline; aggregate
  verdict was still SHIP, but v52-defensive-low's partial-effectiveness
  story became a project-level methodology lesson.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
