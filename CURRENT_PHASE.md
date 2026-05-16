# Current: Sprint 8 — Session 88 v62 SHIPS Rule 22 (chain gate-out extension to DS_NO_MAXTOP + MS_ONLY + JOINT_HIGH on HIGH_ONLY × {J-A}) — back-to-back $98+ production ship (+$98.84/1000h full grid); production v61 → v62 ($1,511.20 → $1,610.04); cumulative closure since pre-S68 = 90.4% of original $1,409; S89 default = continue chain-audit expansion to JOINT_MED/JOINT_LOW/NEITHER × {J-A} OR pivot to HIGH_ONLY × max ∈ {7-T} OR audit prefix-COVERED cells

S88 executed the S87-defined PRIMARY path verbatim. Pre-drill of 357,504
target hands (DS_NO_MAXTOP × {K,A}, MS_ONLY × {J-A}, JOINT_HIGH × {K,A})
revealed v61 leaks **+$98.84/1000h MORE than v44_dt** on these cells —
virtually identical magnitude to S87's $98.67 finding on DS_NO_JOINT. Chain
audit attributed 99.7% of the bleed to the v44→v47 transition; same
culprit as S87 (Rules 13-16, the Q-high DS chain).

Rule 22 (v62) is a strict superset of Rule 21's gate-out: for HIGH_ONLY ×
max ∈ {J,Q,K,A} × cell ∈ {DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH}
per the S71 cell taxonomy, return strategy_v44_dt directly, bypassing the
v47→v48→v52 chain. Pre-committed grader auto-fired **SHIP at +$98.84/1000h
whole-grid lift**. Per-cell breakdown matches audit prediction exactly.
Per-hand effect: 31.3% same, 52.8% better, 15.9% worse. Swap-right rate on
changed hands: **76.8%** (better than S87's 62.3%). Out-of-gate sanity:
**0 v62≠v61 disagreements** on 50K random sample.

**Production state: ADVANCED.** v62_high_only_chain_fix is the new rule
chain ($1,610.04/1000h full / $776.88 prefix unchanged). v44_dt remains ML
champion. Rule count: 21 → 22. Two-track divergence (remaining gap to
oracle ceiling): $135/1000h (was $234, −$98). Cumulative closure since
pre-S68: **90.4% of original $1,409** (was 83%).

**Combined S87+S88 chain-audit recovery: $197.51/1000h.** Bigger than every
value-extraction ship from S71-S86 combined ($16.81 prefix from Rule 20 was
the only SHIP across that 16-session window). The chain-audit lever is now
the project's dominant ship vector.

> **🎯 IMMEDIATE NEXT ACTION (Session 89): continue chain-audit expansion to the remaining prefix-silent HIGH_ONLY cells, OR pivot to one of three alternative audit zones**
>
> The dominant lever is the chain-audit pattern. v47 is now empirically
> net-negative across the entire HIGH_ONLY × {J-A} zone we've audited;
> remaining unaudited zones likely also bleed. Four workstreams identified
> for S89. Default order:
>
> 1. **PRIMARY** — expand chain audit to JOINT_MED + JOINT_LOW + NEITHER ×
>    {J-A} (the remaining prefix-silent HIGH_ONLY × {J-A} cells). Combined
>    n hands ~100-200K; v44_dt baseline leak ~$5-20/1000h (smaller than
>    S87/S88 targets). If audit positive, another $5-20/1000h is
>    recoverable. Methodology directly transfers from S88 scripts. Compute
>    ~5-10 min total.
>
> 2. **SECONDARY** — pivot to HIGH_ONLY × max ∈ {7-T}. Different firing
>    mode (v52-defensive-low rather than v52-fallthrough). UNKNOWN whether
>    v47 chain bleed extends here. Could be a third $50-100/1000h ship or
>    a clean null. Worth a pre-drill (~5 min). The defensive-low handler
>    was specifically designed for these hands and may not carry the
>    same v47 regression.
>
> 3. **TERTIARY** — audit prefix-COVERED cells with the chain-audit
>    pattern. LOW pair, two_pair, trips. Existing per-hand parquets cover
>    most. Low compute cost (no new oracle eval), potentially high
>    information value if buried regressions exist outside HIGH_ONLY.
>
> 4. **OPTIONAL** — build Option C N=1000 oracle generator infrastructure.
>    Required for v60 (S86 MID-pair candidate, MIXED-by-methodology) and
>    for any future smaller-effect rule on prefix-silent cells. ~30-60 min
>    Rust mod + test + launch. Deprioritized vs PRIMARY/SECONDARY because
>    audit pattern delivers larger ships per session.

> **📓 METHODOLOGY (Session 89+ — refined through S88):**
>
> 1. **CHAIN AUDIT pattern is transferable infrastructure (S87 → S88
>    proved).** Three scripts (pre-drill, chain audit, grader) template
>    1:1 across cell sets. Rebind target cells + baseline strategy +
>    pre-committed thresholds; everything else stays the same. Infra
>    cost ~10 min per ship.
>
> 2. **EFFECT-SIZE-DOMINANCE rule replicates cleanly.** S87 shipped at
>    $98.67 under the prefix-silent exception; S88 ships at $98.84.
>    Criterion is well-calibrated for prefix-silent gate-out rules with
>    effect ≫ noise floor by 20×+.
>
> 3. **Diffuse class-label mismatch directions do NOT predict chain
>    net-negative status (NEW S88).** S71 class-label fingerprints were
>    diffuse on DS_NO_MAXTOP and MS_ONLY (no single direction dominates).
>    The chain was still massively net-negative on these cells. PIVOT
>    GATE pre-drill catches what S71 class-label analysis misses. Run the
>    pre-drill even when class-label patterns look diffuse.
>
> 4. **The pre-committed-grader pattern + pre-committed-cell-set pattern
>    combine to make $98+ ships boringly mechanical.** S88 had zero
>    narrative friction from pre-drill to ship.
>
> 5. **Audit-pattern infrastructure is more valuable than any single rule
>    it produces (NEW S88).** Rule 21 ships $98.67. Rule 22 ships $98.84
>    because the audit infrastructure existed to find it. Future infra
>    investments should be evaluated on what audit patterns they unlock.
>
> 6. **Pre-committed grader thresholds in code** — still standard.
>    v62 SHIP threshold $30 in code, grader auto-fired at $98.84. No
>    narrative arbitrage.
>
> 7. **"Speed is not necessary — clarity and perfection is" — S88
>    reaffirms.** Running the chain audit (75s compute) when the pre-drill
>    headline was already clear pinpointed v47 vs v52 attribution and
>    confirmed the same v44→v47 hot transition as S87. Made Rule 22's
>    design surgical (return v44_dt directly, no further refinement).
>
> 8. **Two-track divergence terminology needs unification (NEW S88).** The
>    grader's "two-track divergence" computed production − v44_dt baseline
>    = $529. The project's historical "two-track divergence" is remaining
>    gap to oracle ceiling = $135. Future graders should use clearer
>    labels ("production vs v44_dt" vs "remaining gap to oracle").

> **✅ ARTIFACTS produced in S88:**
> 1. `analysis/scripts/drill_v61_high_only_addressability_S88.py` — pre-drill (NEW)
> 2. `analysis/scripts/audit_v61_chain_bleed_S88.py` — chain audit (NEW)
> 3. `analysis/scripts/strategy_v62_high_only_chain_fix.py` — Rule 22 SHIPPED (NEW)
> 4. `analysis/scripts/grade_v62_full_grid_S88.py` — full-grid grader with pre-committed thresholds (NEW)
> 5. `data/session88/drill_v61_high_only_addressability.log`
> 6. `data/session88/audit_v61_chain_bleed.log`
> 7. `data/session88/grade_v62_full_grid.log`
> 8. `SESSION_88_REPORT.md` — session report with plain-language TL;DR (NEW)
> 9. `DECISIONS_LOG.md` — Decision 123 (ship + methodology) appended
> 10. `CURRENT_PHASE.md` — this file, rewritten for S89
> 11. `STRATEGY_GUIDE.md` — Part 1 Session 88 entry added; Part 5 Rule 21 + Rule 22 entries added; Part 6 current standard updated; front-matter rewritten

> Updated: 2026-05-15 (Session 88 end — STRATEGY OF RECORD CHANGED: v61 → v62_high_only_chain_fix. The S87 chain-audit pattern reapplied to three more prefix-silent HIGH_ONLY × {J-A} cells (DS_NO_MAXTOP × {K,A}, MS_ONLY × {J-A}, JOINT_HIGH × {K,A}, 357,504 hands total) uncovered a SECOND $98.84/1000h v47-chain bleed — back-to-back $98+ ships from the same architectural diagnosis. Combined S87+S88 chain-audit recovery: $197.51/1000h, bigger than every value-extraction ship from S71-S86 combined. Rule 22 (v62): strict superset of Rule 21's gate. For HIGH_ONLY × max ∈ {J,Q,K,A} × cell ∈ {DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH}, bypass v47→v48→v52 chain and return strategy_v44_dt. Full-grid grader auto-fired SHIP at +$98.84/1000h (v61 $1,511.20 → v62 $1,610.04). Per-cell: DS_NO_MAXTOP +$52.88 / MS_ONLY +$31.51 / JOINT_HIGH +$14.45. Swap-right 76.8% on 245K changed hands. Out-of-gate sanity: 0 v62≠v61 disagreements on 50K random sample. Rule count: 21 → 22. Two-track divergence (remaining gap to oracle): $135/1000h (was $234; cumulative closure since pre-S68 now 90.4% of original $1,409). Decision 123 records the ship + four methodology refinements: (1) chain-audit pattern is transferable infrastructure, (2) EFFECT-SIZE-DOMINANCE rule replicates cleanly, (3) diffuse class-label directions don't predict chain net-negative, (4) audit infra is more valuable than any single rule it produces. v60 from S86 STILL UNSHIPPED, MIXED-by-methodology, pending Option C N=1000 oracle generator. S89 default plan: continue chain-audit expansion to JOINT_MED/JOINT_LOW/NEITHER × {J-A} (remaining prefix-silent HIGH_ONLY zones); or pivot to HIGH_ONLY × max ∈ {7-T} (different firing mode, unknown bleed status); or audit prefix-COVERED cells.)

---

## Headline state at end of Session 88 (CHANGED — STRATEGY OF RECORD ADVANCED)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v62_high_only_chain_fix** | PRODUCTION rule chain (NEW S88). **$1,610.04/1000h full / $776.88/1000h prefix** (prefix unchanged). | `analysis/scripts/strategy_v62_high_only_chain_fix.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 16 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$135/1000h (was $234; −$98.84 this session).** Cumulative closure since pre-S68: $1,273.84 = **90.4% of original $1,409** (was 83%).

Production vs v44_dt: production now outperforms ML by **$529/1000h** (v62 $1,610.04 vs v44_dt $1,081). Up from $430 last session.

**Total project rule count: 22** (Rule 22 added — v62 chain gate-out extension covering DS_NO_MAXTOP + MS_ONLY + JOINT_HIGH on top of Rule 21's DS_NO_JOINT, all within HIGH_ONLY × {J-A}).

**S88 candidate result (SHIP):**

| Candidate | Mechanism | Whole-grid lift | Verdict |
|---|---|---:|---|
| v62_high_only_chain_fix | Strict superset of v61's gate. For HIGH_ONLY × max ∈ {J,Q,K,A} × cell ∈ {DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH}, bypass v47→v48→v52 chain; return strategy_v44_dt | **+$98.84/1000h SHIP** | **SHIP** |

---

## Hypothesis cascade status (updated after S88)

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
| Headline-goal recalibration | Concede 95% match% as unreachable | LESS URGENT post-S87/S88 (extraction track now demonstrably productive via chain-audit). |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86) | MID × PMID_DS_NOMAXTOP | MIXED-BY-METHODOLOGY — full +$6.43 SHIP, prefix silent; v60 still UNSHIPPED (Decision 121). |
| DAMAGE-CONTROL chain audit cell #1 (S87) | HIGH_ONLY × DS_NO_JOINT × {J-A} v52-chain regression | SHIPPED — Rule 21 + $98.67 full-grid (Decision 122). |
| **DAMAGE-CONTROL chain audit cell #2 (S88)** | HIGH_ONLY × {DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH} × {J-A} v47-chain regression | **SHIPPED — Rule 22 + $98.84 full-grid (Decision 123).** |
| **Chain-audit expansion (S89+)** | JOINT_MED/JOINT_LOW/NEITHER × {J-A}; HIGH_ONLY × max ∈ {7-T}; prefix-COVERED cells | OPEN — primary S89 direction |
| Prefix-coverage methodology question (S86) | How to handle prefix-silent cells in two-grid SHIP standard | PARTIALLY RESOLVED — EFFECT-SIZE-DOMINANCE rule defined and applied twice; Option C infra still needed for smaller candidates |

**Cascade verdict (post S88):** Two-track active and accelerating.

* **ML cascade:** EXHAUSTED at v44 saturating regime.
* **Rule-layer cascade:** Two patterns active:
  - **Rule extraction (Option D-revised):** $16.81 prefix shipped across S83-S86 (1 SHIP, 2 MIXED, 1 MIXED-by-methodology). Diminishing returns.
  - **Chain audit (S87/S88):** $197.51 full-grid shipped across two sessions. Dominant ship vector. v47 confirmed net-negative across the entire HIGH_ONLY × {J-A} weak-hand zone.

---

## Resume Prompt (Session 89 — continue chain-audit expansion or pivot to new audit zone)

```
Resume Session 89 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S88 — opens with the S89 chain-audit
  expansion plan + alternative-direction options)
- DECISIONS_LOG.md (latest: Decision 123 — S88 v62 SHIPS Rule 22 at
  +$98.84/1000h on HIGH_ONLY × {J-A} × {DS_NO_JOINT, DS_NO_MAXTOP,
  MS_ONLY, JOINT_HIGH}; back-to-back $98+ ships from the same v47-chain
  diagnosis; combined S87+S88 chain-audit recovery = $197.51/1000h;
  methodology refinements: chain-audit pattern transferable as infra,
  diffuse class-label directions don't predict chain net-negative status)
- SESSION_88_REPORT.md (S88 SHIP verdict, plain-language TL;DR,
  back-to-back-$98 framing, methodology refinements)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_v44_high_only_S71_per_hand.parquet — per-hand HIGH_ONLY drill
  data, includes canonical_id + max_rank + cell_idx + v44/oracle picks +
  gap metrics. SUBSTRATE FOR FUTURE CHAIN-AUDIT EXPANSIONS.
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 16 sessions)
- data/session87/*.log — S87 drill + audit + grader logs
- data/session88/*.log — S88 drill + audit + grader logs

STATE (end of S88):
- Production rule chain ADVANCED to v62_high_only_chain_fix
  ($1,610.04 full / $776.88 prefix). Last strategy-of-record change was
  THIS SESSION (back-to-back changes — S87 v61, S88 v62).
- ML champion v44_dt UNCHANGED.
- Two-track divergence (remaining gap to oracle): $135/1000h (was $234; −$98.84).
- Rule count: 22 (Rule 22 added — chain gate-out extension covering
  DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH on top of Rule 21's DS_NO_JOINT).
- Cumulative closure since pre-S68: 90.4% of original $1,409 (was 83%).
- Combined S87+S88 chain-audit recovery: $197.51/1000h (bigger than every
  value-extraction ship from S71-S86 combined).
- v60 from S86 STILL UNSHIPPED, MIXED-by-methodology; waits on Option C
  N=1000 oracle generator (still deferred).
- v47's "offensive value-add" rules (Rules 13-16, S52) now CONFIRMED
  net-negative across the entire HIGH_ONLY × {J-A} zone we've audited.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard." (Strategic priority anchor — see memory
  project_taiwanese_damage_control_priority.md.)
- User is non-technical; any strategic discussion / session report must
  lead with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 89 — continue chain-audit expansion OR pivot to new audit zone:

  PRIMARY (S89 default plan):
  Apply the S87/S88 chain-audit pattern to the remaining prefix-silent
  HIGH_ONLY × {J-A} cells. Use S88 scripts as templates:
    drill_v61_high_only_addressability_S88.py  (template for pre-drill)
    audit_v61_chain_bleed_S88.py               (template for chain audit)
    grade_v62_full_grid_S88.py                 (template for grader)

  Target cells (in descending leak order, all prefix-silent, all unaudited):
    - HIGH_ONLY × JOINT_MED × {J-A}: ~$5-10/1000h v44 STRUCTURE
    - HIGH_ONLY × JOINT_LOW × {J-A}: ~$3-7/1000h v44 STRUCTURE
    - HIGH_ONLY × NEITHER × {J-A}: residual

  Combined potential: another $5-20/1000h if audit positive. Smaller than
  S87/S88 individually, but if all three audit positive the aggregate
  closes the project toward the oracle ceiling.

  PHASE A (~5 min): query S71 cell stats for these cells. Check v44
    STRUCTURE leaks survive under v62 (production now). Verify cells are
    still prefix-silent.
  PHASE B (~3-5 min): pre-drill — re-evaluate v62 on each target cell.
    Identify v62 vs v44 delta.
  PHASE B+ (~3 min): chain audit — layer-by-layer attribution.
  PHASE C: design v63 = v62 + extended gate-out on confirmed regressions.
    Pre-committed thresholds (SHIP ≥ $5 whole-grid since these cells are
    smaller individually; the aggregate might still be significant).
  PHASE D: session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
    rewrite. End with verbatim resume prompt.

  ALTERNATIVE DIRECTIONS:

  (a) Pivot to HIGH_ONLY × max ∈ {7-T}. DIFFERENT firing mode
      (v52-defensive-low rather than v52-fallthrough). UNKNOWN whether
      v47 chain bleed extends here. Could be a third $50-100/1000h ship
      or a clean null. ~5 min pre-drill answers definitively.

  (b) Audit prefix-COVERED cells with the chain-audit pattern. LOW pair,
      two_pair, trips. Existing per-hand parquets cover most. Low compute,
      potentially high information value if buried regressions exist
      outside HIGH_ONLY. Different oracle eval baseline (v62 vs v44_dt on
      prefix-covered cells, with prefix grader as a real two-grid check).

  (c) Build Option C N=1000 oracle generator infrastructure.
      Engineering scope: modify engine/src/main.rs to add --id-list-file
      option (read canonical IDs from a file, only process those).
      ~30-60 min Rust mod + ~10 min test + launch background K-high
      run for v60 retroactive validation. Required for any future
      smaller-effect rule on prefix-silent cells.

  (d) LOW × PMID_OTHER drill (deferred from S87/S88). Last LOW pair cell,
      methodology question is the standard Option D-revised playbook.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- v62_high_only_chain_fix is the production rule chain.
- The pre-committed-verdict pattern is project standard.
- The EFFECT-SIZE-DOMINANCE exception for prefix-silent cells:
  effect ≫ noise floor by 20×+ AND rule is a gate-out → bypass two-grid
  standard with documentation. Below threshold: two-grid standard rules.
  S87 + S88 BOTH shipped under this exception; criterion is calibrated.
- The CHAIN AUDIT pattern: layer-by-layer attribution against v44_dt
  baseline; identify the regression-introducing transition. v47 has been
  the culprit in both S87 and S88; check first for new audits.
- The PIVOT GATE pattern: cheap pre-drill (≤5 min) BEFORE
  committing to expensive infrastructure or pivots.
- NEW S88 lesson — diffuse class-label mismatch patterns do NOT predict
  chain net-negative status. Run the pre-drill even when S71 class-label
  fingerprints look variance-shaped rather than direction-shaped.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
