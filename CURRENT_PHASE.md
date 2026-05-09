# Current: Sprint 8 — Session 48 ships **Rule 13 (three_pair all-intact + DS-bot, MM/HH only) as v44**. v43 → v44 score: $2,727 → $2,717 full, $1,550 → $1,522 prefix. **+$11/1000h whole-grid full + +$29/1000h whole-grid prefix.** Three_pair regret $2,268 → $1,696 (−$572 within three_pair, 25% reduction). **Three_pair pct_opt 51.5% → 59.3% (+7.8% — the largest single-category pct_opt jump from any rule ship in the project.)** pct_opt: 42.20% → 42.34% full / 52.61% → 53.06% prefix. Cumulative v39 → v44 = −$129 full / −$185 prefix. Origin: same suit-dominance lens applied to three_pair via Drill H (n=114,400, full pop). 50% of three_pair hands have ≥1 DS-intact-bot configuration. Three variants tested: V_MM_MID (+$2,463 within fires) and V_HH_MID (+$2,227) both win; **V_LL_MID is catastrophic at -$4,117/1000h** (LL in mid is too weak a Hold'em hand). Skip-the-trap design: explicitly exclude LL_mid-only cases (~30% of fires). Also Session 48: Rule 12 max≤Q extension (v43b) tested and DEFERRED — full +$14 but prefix regresses −$6 with pct_opt drop 52.61%→52.45%; passes strict 2x methodology gate (ratio 0.43x) but qualitative regression deferred. The S43-S48 suit-dominance arc has now shipped 5 production rules (v40b → v41 → v42 → v43 → v44) — the project's largest multi-rule family from a single methodology breakthrough (S44 within-hand pairwise).

> **🎯 IMMEDIATE NEXT ACTION (Session 49):**
>
>   (A) **Trips_pair within-class DS-bot.** Trips_pair (171,600 hands, 2.86% of grid) is the next pair-anchor population. Apply the Drill F/H lens: drill within-class DS configurations and find which structural arrangement wins. Trip + pair gives rich Omaha potential.
>
>   (B) **Composite (cat=7) within-class.** Smallest category but highest regret ($4,445/1000h); there might be quick wins. Cat=7 includes quads_pair, quads_trip, two_trips, etc. — Rule 8 + Rule 9 already handle subsets.
>
>   (C) **v44 ML retrain.** Capacity-only retrain of v34_dt against v44 residuals. Pattern: previous capacity retrains shipped +$15-58. With v44 fixing three_pair $572/1000h within category, the residual pattern has shifted significantly.
>
>   (D) **Two_pair max≤Q refinement.** v43b had +$14 full but -$6 prefix. Find a sharper gate that picks up the full lift WITHOUT regressing prefix (e.g., max=Q AND specific suit/connectivity profile).
>
>   (E) **Carryover deferred items:**
>     - Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
>     - T-low high_only naive top=lo rule
>     - Round-3 within-trips features
>     - Learned A-vs-C decision tree for Rule 6
>     - Trips_pair G3 oracle exploration (+$85 ceiling — relevant to (A))
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 48):** v44_rule13_three_pair_DS replaces v43 as production strategy of record. **+$11 full / +$29 prefix.** Three_pair pct_opt jump +7.8% is largest in project. Total project rule count: **13**.

> **🔬 ARTIFACTS (Session 48):**
> 1. **`analysis/scripts/drill_two_pair_DS_extension.py`** — Drill G (two_pair max≥Q sweep)
> 2. **`analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py`** — DEFERRED extension artifact
> 3. **`analysis/scripts/grade_v43b_rule12_extQ.py`** — DEFERRED grader
> 4. **`analysis/scripts/drill_three_pair_DS_within_intact.py`** — Drill H (DEFINITIVE)
> 5. **`analysis/scripts/strategy_v44_rule13_three_pair_DS.py`** — PRODUCTION
> 6. **`analysis/scripts/grade_v44_rule13_three_pair.py`** — grader
> 7. **`SESSION_48_RULE13_THREE_PAIR_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 48 NEW):**
> - **Within-class DS doesn't always favor "highest pairs in bot".** For two_pair (Drill F), HH-to-bot wins. For three_pair (Drill H), V_LL_MID (HH+MM in bot) is catastrophic. Mid-tier strength matters MORE when bot is already strong (three_pair).
> - **Skip-the-trap design pattern.** Rule 13 explicitly excludes LL_mid-only cases. Don't try to "fix" the trap; just don't fire on it.
> - **Within-category pct_opt jumps are a strong ship signal.** Three_pair pct_opt +7.8% justifies shipping even when whole-grid headline (+$11) is muted by category share.
> - **Extension rules require careful prefix-grid checking.** v43b passed strict 2x gate but had prefix pct_opt regression — deferred.
> - **The suit-dominance arc has now shipped 5 production rules** (Rule 10 v40b/v3 → Rule 11 → Rule 12 → Rule 13) — project's largest multi-rule family from a single methodology breakthrough.

> Updated: 2026-05-09 (Session 48)

---

## Headline state at end of Session 48

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v44_rule13_three_pair_DS** | **PRODUCTION strategy of record** (13 rules: v43 + Rule 13 three_pair all-intact + DS-bot, MM/HH only). +$11 full / +$29 prefix lift over v43. Cumulative v39→v44: +$129 full / +$185 prefix. | `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v43_rule12_two_pair_DS_intact | Predecessor production (Session 47 ship). | `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` |
| v43b_rule12_two_pair_extQ | DEFERRED — Session 48 max≤Q extension; +$14 full but −$6 prefix. | `analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py` |
| v42_rule11_jpair_pbot_ds | Predecessor production (Session 46 ship). | `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` |
| v41_rule10_v3_ds | Predecessor production (Session 45 ship). | `analysis/scripts/strategy_v41_rule10_v3_ds.py` |
| v40b_rule10_gated | Predecessor production (Session 43 ship). | `analysis/scripts/strategy_v40b_rule10_gated.py` |
| v40_rule10 | Simple variant of Rule 10 (sister, retained). | `analysis/scripts/strategy_v40_rule10.py` |
| v39_rule9 | Predecessor production (Session 42 overnight). | `analysis/scripts/strategy_v39_rule9.py` |
| v38_rule8_qp | Predecessor production. | `analysis/scripts/strategy_v38_rule8_qp.py` |
| v37_rule7_three_pair | Earlier production runtime. | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips. NOT runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` |
| v33_rule6_trips | Earlier production runtime. | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3). | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained. | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt. | `analysis/scripts/strategy_v36_rule7_high_only.py` |

**Capacity + feature progression — UNCHANGED:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| **v34** | **34 (33 actual)** | **2** | **83** | **874,548** | **$1,681** | **52.02%** | (latest) |

**Human-strategy progression (full grid, N=200) — production runtime:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rules 4 + 5) | $3,032 | 39.64% | −$1 |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8 quads_pair) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| v40_rule10 (+ Rule 10, simple) — sister | $2,824 | 41.15% | −$209 |
| v40b_rule10_gated (+ Rule 10 gated) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3 suit-aware) | $2,769 | 41.91% | −$264 |
| v42_rule11_jpair_pbot_ds (+ Rule 11) | $2,763 | 41.93% | −$270 |
| v43_rule12_two_pair_DS_intact (+ Rule 12) | $2,727 | 42.20% | −$306 |
| **v44_rule13_three_pair_DS (+ Rule 13) — CURRENT PRODUCTION** | **$2,717** | **42.34%** | **−$316** |

---

## What Session 48 produced

**Code:**
- 2 new drills (`drill_two_pair_DS_extension.py` Drill G, `drill_three_pair_DS_within_intact.py` Drill H)
- 1 new strategy DEFERRED (`strategy_v43b_rule12_two_pair_extQ.py`) — kept as artifact
- 1 new grader DEFERRED (`grade_v43b_rule12_extQ.py`) — artifact
- 1 new strategy (`strategy_v44_rule13_three_pair_DS.py`) — PRODUCTION
- 1 new grader (`grade_v44_rule13_three_pair.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 48 entry; front-matter "Last updated"; Part 5 production-of-record references
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 081 added
- `SESSION_48_RULE13_THREE_PAIR_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 49)

```
Resume Session 49 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 48)
- DECISIONS_LOG.md (latest: Decision 081 — Rule 13 ships as v44)
- SESSION_48_RULE13_THREE_PAIR_REPORT.md (Drill H + Rule 13 finding;
  also Drill G v43b deferral)
- SESSION_47_RULE12_TWO_PAIR_REPORT.md (Rule 12 finding)
- STRATEGY_GUIDE.md (Session 48 entry in Part 1; Part 5 + 6 updated)
- analysis/scripts/strategy_v44_rule13_three_pair_DS.py — current production
- analysis/scripts/drill_three_pair_DS_within_intact.py — Drill H (definitive)

State (end of Session 48):
- Production: v44_rule13_three_pair_DS (13 rules: v43 + Rule 13 three_pair
  all-intact + DS-bot via MM_mid/HH_mid priority; LL_mid-only cases
  skipped to avoid the V_LL_MID trap).
  +$11 full / +$29 prefix vs v43. Three_pair pct_opt +7.8% (largest
  single-category jump in project).
- Cumulative v39 → v44: +$129 full / +$185 prefix.
- The S43-S48 suit-dominance arc has shipped 5 production rules.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).
- DEFERRED: v43b (Rule 12 max≤Q extension) — full +$14 but prefix
  regresses −$6 with pct_opt drop. Files retained for possible
  future refinement.

USER-PRIORITY DIRECTION FOR SESSION 49 (recommended):

(A) Trips_pair within-class DS-bot. Trips_pair (171,600 hands, 2.86%
    of grid) is the next pair-anchor population. Apply Drill F/H lens.

(B) Composite (cat=7) within-class. Smallest category but highest
    regret ($4,445/1000h). Cat=7 = quads_pair + quads_trip + two_trips
    + others. Rules 8, 9 handle subsets — drill the residual.

(C) v44 ML retrain. Capacity-only retrain of v34_dt against v44 residuals.

(D) Two_pair max≤Q refinement. v43b had +$14 full but -$6 prefix.
    Find a sharper gate that ships clean.

(E) Carryover (Session 45+ deferrals):
    - Q5 J-high no-pair multi-feature deep dive
    - T-low high_only naive top=lo rule
    - Round-3 within-trips features
    - Learned A-vs-C decision tree for Rule 6
    - Trips_pair G3 oracle exploration
    - KK/AA single-suited Rule-4-bot residual

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ALL rules on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN PREFIX COVERAGE EXISTS.
- Methodology rule (Session 48 NEW): within-class DS doesn't always
  favor "highest pairs in bot" — depends on whether bot is already strong.
- Methodology rule (Session 48 NEW): skip-the-trap design pattern
  (don't fire on cells where the variant regresses).
- Methodology rule (Session 48 NEW): within-category pct_opt jumps
  are a strong ship signal even when whole-grid headline is muted.
- Methodology rule (Session 47 NEW): cross-class within-pop "DS premium
  within X" lens ships rules reliably across pair/two_pair/three_pair.
- Methodology rule (Session 47 NEW): HH-to-bot wins for two_pair (but
  fails for three_pair — see S48).
- Methodology rule (Session 46 NEW): single-cell rules ship at <$10/1000h
  whole-grid lift when within-fires lift is large.
- Methodology rule (Session 45 NEW): pair structure dominates suit
  structure universally in J-low pair/two_pair.
- Methodology rule (Session 44): cross-class regret averaging is
  confounded; use within-hand pairwise.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
