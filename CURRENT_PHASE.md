# Current: Sprint 8 — Session 47 ships **Rule 12 (J-low two_pair both-intact + DS-bot) as v43** — the largest single-rule full-grid lift since v33's Rule 6 (Session 37, +$113). v42 → v43 score: $2,763 → $2,727 full, $1,616 → $1,550 prefix. **+$35/1000h whole-grid full + +$66/1000h whole-grid prefix.** Two_pair regret $3,371 → $3,211 (−$160 within two_pair). pct_opt full: 41.93% → 42.20% (+0.27%); pct_opt prefix: 51.81% → 52.61% (+0.80%). Cumulative v39 → v43 = −$118 full / −$157 prefix. Origin: Drill B (Session 45) found B1−B2 = +$1,864/1000h within-hand at J-low two_pair. Drill F (Session 47) tested HH-to-bot vs LL-to-bot tie-breaks on the 262,080-hand pop: V_HH_BOT (+$1,808/1000h within fires) wins decisively over V_LL_BOT (+$1,044). Rule 12 is a hybrid: HH-to-bot preferred, LL-to-bot fallback, both-intact + DS-bot. Fires on 47.3% of J-low two_pair (2.01% of grid). 100% of fired picks correctly preserve both pairs intact + DS-bot. Also Session 47: Drill E (Rule 11 heuristic variant sweep, NEGATIVE) — v42's V_LOLO is empirically optimal among 6 simple tie-break variants; the +$1,794/1000h within-fires gap to A5 oracle requires more sophisticated logic, not simple sweeps.

> **🎯 IMMEDIATE NEXT ACTION (Session 48):**
>
>   (A) **Two_pair max≥Q extension.** Rule 12 currently scoped to max_rank ≤ J. Drill F's pattern likely extends to higher max_rank — does the same HH-to-bot + DS heuristic ship on the Q+ two_pair cells? Risks: at high max_rank, breaking a pair might happen anyway because singletons are stronger; need careful drill before extension.
>
>   (B) **Three_pair within-class DS-bot.** Three_pair is the next structural pair-anchor population (114,400 hands, 1.9% of grid). Apply the same lens: drill "DS premium within both/all-pairs-intact" for three_pair. Expected lift TBD but the pattern is consistent.
>
>   (C) **Rule 11 + Rule 12 unified pattern.** Could rewrite as a generic rule covering pair, J-pair, two_pair as a single rule family. Cosmetic but improves the rule chain's elegance for human-memorization.
>
>   (D) **v43 ML retrain.** Capacity-only retrain of v34_dt against v43 residuals. Pattern: previous capacity retrains shipped +$15-58. With v43 fixing two_pair $160/1000h, the residual pattern has shifted significantly.
>
>   (E) **Carryover deferred items:**
>     - Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
>     - T-low high_only naive top=lo rule
>     - Round-3 within-trips features
>     - Learned A-vs-C decision tree for Rule 6
>     - Trips_pair G3 oracle exploration
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 47):** v43_rule12_two_pair_DS_intact replaces v42 as production strategy of record. **+$35 full / +$66 prefix.** Largest single-rule full-grid lift since v33's Rule 6. Total project rule count: **12**.

> **🔬 ARTIFACTS (Session 47):**
> 1. **`analysis/scripts/drill_rule11_heuristic_sweep.py`** — Drill E (NEGATIVE; n=18,900)
> 2. **`analysis/scripts/drill_two_pair_DS_within_intact.py`** — Drill F (DEFINITIVE; n=262,080)
> 3. **`analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py`** — PRODUCTION
> 4. **`analysis/scripts/grade_v43_rule12_two_pair.py`** — grader vs v42
> 5. **`SESSION_47_RULE12_TWO_PAIR_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 47 NEW):**
> - **Cross-class within-pop rules from "DS premium within X" lens ship reliably across the pair/two_pair domain.** Three rules in S45-S47 arc share the same mechanism: Rule 10 v3, Rule 11, Rule 12. The "within-class DS premium" axis is the project's most productive rule-discovery lens.
> - **HH-to-bot wins over LL-to-bot for two_pair.** Counter to "lowest pair to bot for kicker preservation" intuition; HH in bot creates a stronger 2-pair-with-kicker Omaha hand.
> - **Cumulative ship arcs >$100/1000h come from structural-axis families.** v30→v34 was ML capacity arc; v39→v43 is suit-dominance arc. Both 4-session multi-rule ships from one methodology breakthrough.
> - **Simple tie-break sweeps cap quickly** (Drill E). Once 6 simple combinations are tested, further refinement requires structural complexity.

> Updated: 2026-05-09 (Session 47)

---

## Headline state at end of Session 47

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v43_rule12_two_pair_DS_intact** | **PRODUCTION strategy of record** (12 rules: v42 + Rule 12 J-low two_pair both-intact + DS-bot). +$35 full / +$66 prefix lift over v42. Cumulative v39→v43: +$118 full / +$157 prefix. | `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
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
| **v43_rule12_two_pair_DS_intact (+ Rule 12) — CURRENT PRODUCTION** | **$2,727** | **42.20%** | **−$306** |

---

## What Session 47 produced

**Code:**
- 2 new drills (`drill_rule11_heuristic_sweep.py` NEGATIVE, `drill_two_pair_DS_within_intact.py` DEFINITIVE)
- 1 new strategy (`strategy_v43_rule12_two_pair_DS_intact.py`) — PRODUCTION
- 1 new grader (`grade_v43_rule12_two_pair.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 47 entry; front-matter "Last updated"; Part 5 production-of-record references
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 080 added
- `SESSION_47_RULE12_TWO_PAIR_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 48)

```
Resume Session 48 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 47)
- DECISIONS_LOG.md (latest: Decision 080 — Rule 12 ships as v43)
- SESSION_47_RULE12_TWO_PAIR_REPORT.md (Drill F + Rule 12 finding)
- SESSION_46_RULE11_JPAIR_REPORT.md (Rule 11 finding)
- SESSION_45_RULE10_V3_REPORT.md (Rule 10 v3 finding)
- STRATEGY_GUIDE.md (Session 47 entry in Part 1; Part 5 + 6 updated)
- analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py — current production
- analysis/scripts/drill_two_pair_DS_within_intact.py — Drill F (definitive)

State (end of Session 47):
- Production: v43_rule12_two_pair_DS_intact (12 rules: v42 + Rule 12
  J-low two_pair both-intact + DS-bot via HH-to-bot tie-break with LL fallback).
  +$35 full / +$66 prefix vs v42.
- Cumulative v39 → v43: +$118 full / +$157 prefix.
- The S45-S47 suit-dominance arc has shipped 4 rules (Rule 10 v3,
  Rule 11, Rule 12) totaling −$118 full / −$157 prefix.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).

USER-PRIORITY DIRECTION FOR SESSION 48 (recommended):

(A) Two_pair max≥Q extension. Rule 12 currently scoped to max_rank ≤ J.
    Drill the same HH-to-bot heuristic on Q-, K-, A-high two_pair cells.
    Expected: similar pattern but possibly smaller because high singletons
    have higher top equity (less weak-hand top-inversion benefit).

(B) Three_pair within-class DS-bot. Three_pair (114,400 hands, 1.9% of
    grid) is the next pair-anchor population. Apply the Drill F lens.

(C) Unified pair-DS rule family. Combine Rule 10 v3, Rule 11, Rule 12
    into a single generic "suit-aware bot within pair-anchor" rule for
    human-memorization elegance.

(D) v43 ML retrain. Capacity-only retrain of v34_dt against v43 residuals.

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
- Methodology rule (Session 47 NEW): cross-class within-pop "DS premium
  within X" lens ships rules reliably across pair/two_pair domain.
- Methodology rule (Session 47 NEW): HH-to-bot wins over LL-to-bot for
  two_pair (counter to kicker-preservation intuition).
- Methodology rule (Session 47 NEW): cumulative ship arcs >$100/1000h
  come from structural-axis families (v39→v43 is the suit-dominance arc).
- Methodology rule (Session 47 NEW): simple tie-break sweeps cap quickly.
- Methodology rule (Session 46 NEW): single-cell rules ship at <$10/1000h
  whole-grid lift when within-fires lift is large.
- Methodology rule (Session 46 NEW): drill "best-in-class minus production
  pick" to discover single-cell rules.
- Methodology rule (Session 45 NEW): pair structure dominates suit
  structure universally in J-low pair/two_pair.
- Methodology rule (Session 44): cross-class regret averaging is
  confounded; use within-hand pairwise.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
