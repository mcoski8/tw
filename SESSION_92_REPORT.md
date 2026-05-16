# Session 92 — Chain-audit pattern pivots to two_pair + trips: v55/v56 blanket routing has already collapsed both chains to v44_dt, so chain-audit produces structural NULL by construction. **Production v64 UNCHANGED.**

_Generated 2026-05-15. S92 was the planned execution of the S91-defined PRIMARY path: pivot to two_pair chain audit (PRIMARY) and trips chain audit (SECONDARY). Pre-flight code trace of `strategy_v55_two_pair_hybrid` and `strategy_v56_trips_hybrid` revealed both strategies route 100% of their target hands to `strategy_v44_dt` unconditionally — meaning production v64 ≡ v44_dt on every two_pair and trips hand by construction. Phase B addressability drill empirically confirmed: 0 mismatches across 1,338,480 two_pair hands; Δ(v64−v44_dt) = $0.00 on every cell. Phase B+ chain audit (layer attribution) quantified the architectural snapshot: the rule-based `v44_RULE13` chain bleeds **+$515.80/1000h vs v44_dt on two_pair prefix** (3× the LOW pair bleed S91 found) and **+$33.21/1000h on trips prefix**; v55 + v56 absorb 100% of both. No per-sub-cell residual exists for chain-audit to gate out. Phase C grader: structural NULL — zero candidates. **Production v64 UNCHANGED. Second consecutive non-ship session in chain-audit run. CHAIN-AUDIT METHODOLOGY MILESTONE: pattern has now been applied to all four major hand-categories (HIGH_ONLY, single-pair, two_pair, trips); the lever is exhausted.**_

## TL;DR — Plain language

**What changed in your strategy of record:** Nothing. v64 from S90 remains production. Rule count stays at 24. ML champion v44_dt unchanged for a 20th consecutive session.

**Why we didn't ship:** Before any compute, I traced the code paths for `v55_two_pair_hybrid` and `v56_trips_hybrid`. Both contain a single binary check: "if hand matches my target category → return `v44_dt`'s pick." That's it — every two_pair hand and every trips hand has its production pick **defined by v44_dt**, with no chain machinery in between. The chain-audit pattern (= "find a layer where production bleeds vs v44_dt, gate it out") cannot find anything to gate because production IS v44_dt for these categories.

**What we still confirmed empirically:** We ran the audit anyway because (a) the empirical confirmation across all 1.34M hands is cheap (~4 min), and (b) the audit produces a useful architectural snapshot — how much WOULD production bleed if we undid v55's blanket routing?

  * **two_pair: v44_RULE13 chain bleeds +$515.80/1000h prefix vs v44_dt.** That's **3× the LOW pair bleed** S91 surfaced ($182.28). v55 absorbs 100% of it. v55 is even more load-bearing than S91 quantified for v54+Rule 29.
  * **trips: v44_RULE13 chain bleeds +$33.21/1000h prefix vs v44_dt.** Smaller than two_pair (trips is a smaller category), but the same structural pattern. v56 absorbs 100%.

So v55 and v56 are doing **enormous** load-bearing work. The session quantified just how much.

**What we discovered about the chain-audit methodology:**

  * **Two_pair and trips chain-audit is structurally NULL.** Not because production is good (it is — at the v44_dt level), but because the chain-audit pattern requires production picks to DIFFER from v44_dt on the audited cells, which is false here. A new third applicability prerequisite is now in the playbook.
  * **The chain-audit work on the four major hand-categories is COMPLETE.** HIGH_ONLY: 4 ships ($214.83/1000h). LOW single-pair: NULL (population-divergence noise). Two_pair: structural NULL. Trips: structural NULL. The lever has now been worked through every major category and is exhausted.

**Why this is still valuable:**
- **The "v44_RULE13 chain bleeds $515/1000h on two_pair, $33 on trips" finding is a project-level architectural snapshot.** Combined with S91's LOW pair $182/1000h finding, the cumulative chain bleed across pair+two_pair+trips is **$731/1000h** vs v44_dt. v54+v55+v56 absorb ~$700 of that. They are the most load-bearing infrastructure in the project.
- **Methodology refinement: chain-audit applicability has a NEW prerequisite (NEW S92).** Production picks must differ from v44_dt on at least some audit cells. If a prior router has collapsed the chain to v44_dt (= the v55/v56 blanket-routing pattern), chain-audit produces structural NULL by construction. Pre-flight code trace can detect this in <5 min.
- **The methodology arc on chain-audit is bounded.** Knowing where a lever runs out is as valuable as knowing where it works.

**The numbers:**
- Production v64: $1,627.36/1000h full / $776.88 prefix (**UNCHANGED** from S90)
- Rule count: 24 (**UNCHANGED**)
- v44_dt: $1,081 full / $686 prefix (**UNCHANGED** for 20 sessions, since v44 in S58)
- v44_RULE13 chain on two_pair prefix: $786.50/1000h (= **+$515.80** worse than v44_dt — biggest bleed identified to date)
- v44_RULE13 chain on trips prefix: $88.06/1000h (= **+$33.21** worse than v44_dt)
- v55 absorbs +$515.80 (blanket two_pair → v44_dt)
- v56 absorbs +$33.21 (blanket trips → v44_dt)
- Combined S87-S92 chain-audit ship recovery: $214.83/1000h (S91 + S92 contribute $0)
- Combined S87-S92 architectural snapshot of bleed magnitudes absorbed by infrastructure: pair $195 (v54+v57), two_pair $516 (v55), trips $33 (v56) = **$744/1000h of chain bleed neutralized by production infrastructure**

**What's NOT changing:** Production, ML champion, rule count, prefix score, full score. v60 from S86 still parked. The chain-audit lever, after 5 consecutive sessions of work (S87-S92), has now produced 4 ships + 2 NULLs and has been applied to all major categories. Time to consider alternative levers.

## The full story (compressed)

### Phase 0 — Pre-flight code trace (saved the session ~30+ min)

Before writing the addressability drill, I read `strategy_v55_two_pair_hybrid.py` and `strategy_v56_trips_hybrid.py`. Both contain a single binary gate:

```python
# v55 (two_pair_hybrid)
def strategy_v55_two_pair_hybrid(hand):
    if _is_two_pair(hand):
        return strategy_v44_dt(hand)
    return strategy_v54_pair_hybrid(hand)
```

This means **every two_pair hand has production pick ≡ v44_dt pick by construction**. v56 has the same pattern for trips. v57 (LOW single-pair Rule 29) and v64 (HIGH_ONLY gate-outs) do not fire on two_pair or trips (their gates exclude these categories).

Therefore: **chain-audit can find no per-cell Δ between production and v44_dt — the chain has been collapsed.** The pattern's productive zone is bounded.

Confirmed on a 50-hand sample: 50/50 v64 picks match v44_dt picks on two_pair. Same for trips.

This pre-flight trace cost ~5 min and correctly predicted the audit outcome. **PIVOT-GATE PATTERN REFINEMENT (NEW S92): pre-flight code-trace of chain layers should be standard before any chain-audit drill.**

### Phase A — structural / prefix coverage (two_pair)

Used `drill_two_pair_v44_per_hand_structural.parquet` (S69 drill output). Cell taxonomy:

| cell_idx | name | n_full | n_prefix | cid_min | cid_max | v44 leak (full) |
|---:|---|---:|---:|---:|---:|---:|
| 0 | LAYOUT_A_DS | 257,400 | 39,318 | 41,701 | 6,008,277 | $+12.13 |
| 1 | LAYOUT_C_DS | 308,880 | 47,135 | 46,561 | 6,008,275 | $+5.66 |
| 2 | LAYOUT_B_DS | 231,660 | 35,345 | 46,560 | 6,008,261 | $+15.28 |
| 3 | LAYOUT_A_SS | 437,580 | 66,796 | 46,559 | 6,008,276 | $+35.22 |
| 4 | LAYOUT_C_SS_ONLY | 90,090 | 13,721 | 61,134 | 6,008,167 | $+12.38 |
| 5 | LAYOUT_B_SS_ONLY | 12,870 | 1,960 | 133,121 | 6,007,675 | $+0.13 |
| (6) | LAYOUT_OTHER | 0 | — | — | — | — (structurally empty) |
| **TOTAL** | | **1,338,480** | **204,275** | | | **$+80.82** |

All 6 non-empty cells are prefix-covered. Within-two_pair v44_dt leak vs oracle = **$80.82/1000h** (full grid). This is the **ML champion ceiling** — chain-audit cannot recover any of this (production already IS v44_dt).

### Phase B — addressability pre-drill (two_pair, 1,338,480 hands)

`drill_v64_two_pair_addressability_S92.py` (3.7 min wall, 6,000 hands/sec). Per-cell headline:

| cell | n | v44=v64 % | v44 leak | v64 leak | Δ (v64−v44) |
|---|---:|---:|---:|---:|---:|
| LAYOUT_A_DS | 257,400 | 100.0% | $+12.13 | $+12.13 | **$+0.00** |
| LAYOUT_C_DS | 308,880 | 100.0% | $+5.66 | $+5.66 | **$+0.00** |
| LAYOUT_B_DS | 231,660 | 100.0% | $+15.28 | $+15.28 | **$+0.00** |
| LAYOUT_A_SS | 437,580 | 100.0% | $+35.22 | $+35.22 | **$+0.00** |
| LAYOUT_C_SS_ONLY | 90,090 | 100.0% | $+12.38 | $+12.38 | **$+0.00** |
| LAYOUT_B_SS_ONLY | 12,870 | 100.0% | $+0.13 | $+0.13 | **$+0.00** |
| **TOTAL** | **1,338,480** | | $+80.82 | $+80.82 | **$+0.00** |

**Mismatch count: 0 / 1,338,480.** Production v64 ≡ v44_dt on every two_pair hand. Δ across all 66 (cell × max_sing) sub-cells: $0.00.

Prefix grid version: Δ = $0.00 across all 6 cells.

### Phase B+ — chain audit (layer attribution, prefix N=1000)

`audit_v64_two_pair_chain_S92.py` (3.3 min wall, 204,275 prefix two_pair hands × 7 strategies × 1,032 hands/sec). Layer-by-layer attribution:

| layer | total prefix leak | Δ vs prior |
|---|---:|---:|
| v44_dt | $+270.70 | — |
| v44_RULE13 chain | $+786.50 | **+$515.80** (chain BLEEDS massively) |
| v54 (pair_hybrid) | $+786.50 | $+0.00 (v54 inert on two_pair — single-pair-only gate) |
| **v55 (two_pair_hybrid)** | **$+270.70** | **-$515.80** (blanket routing ABSORBS 100% of chain bleed) |
| v56 (trips_hybrid) | $+270.70 | $+0.00 (trips-only gate inert) |
| v57 (+ Rule 29) | $+270.70 | $+0.00 (LOW single-pair gate inert) |
| v64 (production) | $+270.70 | $+0.00 (HIGH_ONLY gate inert) |

**Key architectural finding:** the v44_RULE13 chain — the same fallthrough layer that S91 quantified as bleeding $182.28/1000h on LOW pair — bleeds **$515.80/1000h on two_pair**. That is **2.83× the LOW pair bleed**, and the **largest single-layer bleed identified in the project to date**. v55's blanket routing absorbs 100% of it.

**Per-sub-cell residual:** Δ(v64 − v44_dt) is exactly $0.00 on every (cell × max_sing) combination. No chain-audit candidate exists.

### Phase A+B — addressability + chain audit (trips, 25,245 prefix hands)

`audit_v64_trips_chain_S92.py` (~12s wall, 25,245 prefix trips hands × 7 strategies). Trips cell taxonomy:

| cell_idx | name | n_full | n_prefix | v44 leak (full) |
|---:|---|---:|---:|---:|
| 0 | B_DS_AVAIL_HKR | 62,055 | 4,774 | $+10.65 |
| 1 | B_DS_AVAIL_LKR | 163,170 | 12,553 | $+38.34 |
| 2 | NO_BDS_CTOP | 20,592 | 1,584 | $+1.99 |
| 3 | NO_BDS_AKDOM | 82,368 | 6,334 | $+14.20 |
| **TOTAL** | | **328,185** | **25,245** | **$+65.18** |

Layer attribution (prefix N=1000):

| layer | total prefix leak | Δ vs prior |
|---|---:|---:|
| v44_dt | $+54.85 | — |
| v44_RULE13 chain | $+88.06 | **+$33.21** (chain bleeds) |
| v54 / v55 | $+88.06 | $+0.00 (inert on trips) |
| **v56 (trips_hybrid)** | **$+54.85** | **-$33.21** (blanket routing absorbs 100%) |
| v57 / v64 | $+54.85 | $+0.00 (inert on trips) |

Same architectural pattern as two_pair: chain bleeds, v56 absorbs entirely, production = v44_dt.

### Phase C — pre-committed grader

`grade_v65_two_pair_trips_chain_candidates_S92.py` LOCKED thresholds in code BEFORE evaluation (identical to S91):

- SHIP: prefix lift ≥ $5 AND full lift ≥ $5 (both grids clear AND agree on direction)
- NULL: both grids |lift| ≤ $1
- MIXED: one grid clears, other doesn't

**Candidate set: 0 candidates.** Because Δ(v64 − v44_dt) is structurally $0.00 on every sub-cell, no v65 candidate can be designed from chain-audit. Grader prints "STRUCTURAL NULL" verdict.

**Aggregate S92 verdict: NULL.** Production v64 unchanged.

### Why this is a STRUCTURAL NULL (distinct from S91's POPULATION-DIVERGENCE NULL)

S91's NULL was caused by **POPULATION-DIVERGENCE NOISE**: prefix and full grids evaluated different canonical_id populations within nominally identical sub-cells, so small per-sub-cell effects diverged in direction on the two grids — a real statistical phenomenon revealed when the two-grid SHIP standard was applied.

S92's NULL is **structural** at the strategy layer: production picks are byte-identical to v44_dt on every two_pair and trips hand. There is no per-cell Δ to evaluate, period. The two-grid standard never needs to be applied because the candidate set is empty.

**S91 NULL** = "we tried, the data didn't clear the bar."
**S92 NULL** = "there is nothing to try."

Both are honest. Both are useful. They map different shapes of the chain-audit applicability boundary.

### What this answers about the cascade

1. **CHAIN-AUDIT APPLICABILITY MAP IS NOW COMPLETE.** Five sessions (S87-S92) applied the pattern to all four major hand-categories:
   - **HIGH_ONLY** (S87-S90, 4 sessions): **SHIPPED $214.83/1000h** across Rules 21/22/23/24. Pattern transferred cleanly across all four prefix-silent cell zones.
   - **LOW single-pair** (S91): NULL due to POPULATION-DIVERGENCE NOISE on prefix-COVERED cells with small ($1-5/1000h) per-sub-cell residuals.
   - **Two_pair** (S92): STRUCTURAL NULL — v55's blanket routing collapsed the chain.
   - **Trips** (S92): STRUCTURAL NULL — v56's blanket routing collapsed the chain.

   **The chain-audit lever has been worked through every applicable zone and is exhausted.** Five consecutive sessions of work; four ships totaling $215; two NULLs at the boundaries.

2. **v44_RULE13 IS QUANTIFIED ACROSS ALL THREE PAIR-FAMILY CATEGORIES.** Cumulative chain bleed vs v44_dt on the prefix grid:
   - LOW pair (S91): $182.28/1000h
   - two_pair (S92): $515.80/1000h
   - trips (S92): $33.21/1000h
   - **TOTAL chain bleed absorbed by v54/v55/v56/v57: ~$731/1000h.**

   This makes v54+v55+v56+Rule 29 the most load-bearing infrastructure in the project. Without them, production would bleed >$700/1000h on the pair-family categories alone.

3. **CHAIN-AUDIT APPLICABILITY TEST is now 3-pronged (NEW S92 prerequisite).** The pattern is most productive when:
   - **(a)** target cells are prefix-SILENT → EFFECT-SIZE-DOMINANCE applies (S87-S90 ships), OR
   - **(b)** per-sub-cell residual ≥ $5/1000h on BOTH grids → population-divergence noise doesn't dominate (S91 finding), AND
   - **(c)** [NEW S92 PREREQUISITE] production picks must DIFFER from v44_dt on at least some audit cells — otherwise chain has been collapsed and audit is moot.

   Pre-flight code trace of chain layers can verify (c) in <5 min before committing to compute.

4. **The pivot-gate methodology was validated again.** S87 introduced the pattern (cheap pre-drill before expensive infrastructure). S92 extended it: pre-flight code trace BEFORE the pre-drill itself, since the strategy code is the most authoritative source for "can this audit possibly produce a non-trivial Δ?" The cost is ~5 min of reading; the savings can be 30+ min when the answer is "no."

5. **Where next?** With chain-audit exhausted, the natural S93+ candidates are:
   - **Option C N=1000 oracle generator** (TERTIARY from S91, still deferred): unlocks N=1000 evaluation of any canonical_id subset, enabling retroactive validation of v60 (S86 MIXED) and broader two-grid checking on smaller-effect rules. ~30-60 min Rust mod.
   - **Rule-extraction within v44_dt's residual leak** on two_pair ($80.82/1000h) and trips ($65.18/1000h) and LOW pair ($281.56/1000h). This is the Option D-revised pattern (rule beats v44_dt on sub-cell). S69 and S83-S85 explored this; diminishing returns but not formally closed.
   - **ML retrain** (formally closed at v44 in S78 / Decision 113, but a fresh attempt with a richer feature set or A3 full 6M-hand N=1000 grid would reopen). Would shift v44 → v44+, propagating through v54/v55/v56/v57 since they all route to v44_dt.
   - **Headline-goal recalibration** (concede 95% match% as unreachable). The extraction track has shown diminishing returns over S91+S92; some explicit recalibration may sharpen S93+ priorities.

### Methodology lessons (Session 92)

1. **CHAIN-AUDIT APPLICABILITY MAP IS COMPLETE (NEW S92).** Five sessions have mapped the lever's productive zone. New ships from this pattern are not expected on current architecture. Future ships would require either (a) a new chain layer to audit (no candidates), or (b) a richer ML champion that exposes new chain bleeds (open question).

2. **PRE-FLIGHT CODE TRACE AS PIVOT-GATE (NEW S92).** When the audit target's production chain can be read in <100 lines of strategy code, read it first. If the chain has been collapsed by a prior router to v44_dt (the v55/v56 blanket pattern), audit is moot and a structural NULL is the expected outcome — save the 5-30 min drill.

3. **STRUCTURAL NULL is a distinct verdict from POPULATION-DIVERGENCE NULL (NEW S92).** S91 NULL came from grid disagreement on real per-cell effects. S92 NULL came from the candidate set being empty by construction. Both are honest; both map the boundary of chain-audit; the right path forward differs (S91 → tighter bars or new methodology; S92 → pivot to a different lever).

4. **v44_RULE13 chain bleed quantified across pair-family.** $182 LOW pair + $516 two_pair + $33 trips = **$731/1000h** absorbed by v54/v55/v56/Rule 29. This is the architectural snapshot: how much production would bleed if the hybrid routing layer were removed.

5. **The methodology arc on chain-audit is BOUNDED in 5 sessions.** S87-S92. Four ships. Two NULLs at well-characterized boundaries. The boundary mapping is itself an outcome — future levers should be selected with this map in hand rather than re-running the same pattern.

6. **A second consecutive NULL session in chain-audit is decision-relevant.** S91 + S92 together = clear signal that the pattern is at saturation. The signal would not have been clear after S91 alone (could have been a one-off). After S92, the project should pivot — and the resume prompt for S93 should lead with that pivot, not default to "more chain audit."

## Headline state at end of S92 (UNCHANGED from S90/S91)

| Strategy | Use case | Where it lives |
|---|---|---|
| **v64_high_only_chain_fix_zone** | PRODUCTION rule chain. **$1,627.36/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 20 sessions, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 24** (UNCHANGED).
* **Cumulative closure since pre-S68: $1,291.16 of $1,409 = 91.6%** (UNCHANGED).
* **Remaining gap to oracle ceiling: $117.84/1000h** (UNCHANGED).
* **Production vs v44_dt: $546.36/1000h** (UNCHANGED).
* **Combined S87-S92 chain-audit recovery: $214.83/1000h** (S91 + S92 contribute $0).
* **Combined v44_RULE13 chain bleed absorbed by v54/v55/v56/Rule 29 infrastructure (architectural snapshot): ~$731/1000h** across pair + two_pair + trips.
* **CHAIN-AUDIT METHODOLOGY ARC: complete across all four major hand-categories.**

## What's on the table for S93

1. **PRIMARY — Option C N=1000 oracle generator infrastructure.** Promoted from TERTIARY to PRIMARY because chain-audit is exhausted. Modify `engine/src/main.rs` to add `--id-list-file` option (read canonical IDs from file, only process those). ~30-60 min Rust mod + ~10 min test. Unlocks: (i) retroactive validation of v60 from S86 (MIXED-by-methodology), (ii) two-grid SHIP standard on arbitrary cell subsets at N=1000 prefix-equivalent quality, (iii) future smaller-effect rule validation.

2. **SECONDARY — rule-extraction (Option D-revised) on within-v44_dt residual leak.** Current category-level v44_dt leaks vs oracle: LOW pair $281, MID pair (TBD), HIGH pair (TBD), two_pair $80.82, trips $65.18. S83/S84/S85/S86 explored MID-pair extraction (1 SHIP, 2 MIXED, 1 MIXED-by-methodology). The pattern shows diminishing returns but is not formally closed. Could re-attempt on two_pair LAYOUT_A_SS (largest unaddressed leak, $35.22/1000h on 437K hands) or trips B_DS_AVAIL_LKR ($38.34 on 163K hands).

3. **TERTIARY — Headline-goal recalibration.** Make explicit that 95% match% is unreachable from current architecture; re-set the goal to maximize $/1000h subject to current cascade. Affects how to read future "NULL ship" sessions: are they failures or boundary-mapping wins?

4. **DEFERRED — ML retrain.** Formally closed at v44 in S78 (Decision 113). Reopening requires either a new feature family or full-6M N=1000 oracle (A3, deprioritized). Not productive without infrastructure investment.

5. **DEFERRED — v52-defensive-low partial-effectiveness exploit** (S90 finding). Still speculative.

6. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing 100% of the chain bleed on pair-family categories, replacing v44_RULE13 itself only matters for HIGH_ONLY (which is already gated by v52 + the S87-S90 rules). Engineering scope is large; payoff unclear.

The dominant lever for the project — "find and remove chain regressions" — has been worked through five sessions (S87-S92) and is now bounded. **The next productive lever is most likely Option C N=1000 oracle infrastructure**, which unlocks honest two-grid evaluation on smaller-effect candidates including the v60 ship that's been parked since S86.
