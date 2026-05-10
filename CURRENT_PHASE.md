# Current: Sprint 8 — Session 50 ships **Rule 14 (A-high no-pair, A-on-top + DS/SS HIMID) as v45 — LARGEST SINGLE-RULE LIFT IN PROJECT HISTORY (+$131/1000h whole-grid full)**. v44 → v45 score: $2,717 → $2,585 full, $1,522 → $1,522 prefix (UNCHANGED — high_only has zero prefix coverage). pct_opt: 42.34% → 43.05% full / 53.06% (unchanged) prefix. high_only category $4,082 → $3,439 (−$643 within high_only, 16% reduction). high_only pct_opt 19.8% → 23.3% (+3.5%). p90 regret IMPROVED 0.785→0.745. **Beats v33's Rule 6 (+$113, S37) which had held the single-rule record for 13 sessions.** Cumulative v39 → v45 = −$260 full / −$185 prefix. Origin: User direction to scale into the high_only category (largest unclaimed territory at $833/1000h whole-grid regret contribution); started with A-high no-pair (660,660 hands = 11% of grid). Drill K characterization found A-high contributes $412/1000h whole-grid regret; v44 over-DS's structurally simple cases, picks rainbow 13× too often, never picks 3+1. Drill L heuristic sweep found HIMID is the right tie-break (NOT HIBOT) — counter to "stack high cards in bot" intuition. With A on top, K+Q etc. belong in MID for Hold'em scoring; lower 4 cards form bot's Omaha play (suit > rank). Drill estimated +$10/1000h whole-grid; grader measured +$131 (13× the drill estimate). The S43-S50 arc has now shipped 6 production rules totaling −$260 full / −$185 prefix — the project's largest multi-rule family by both ship count and total lift.

> **🎯 IMMEDIATE NEXT ACTION (Session 51):**
>
>   (A) **K-high no-pair** — same Drill K + Drill L methodology applied to K-high (~290K hands, ~5% of grid). Likely needs different heuristic (K isn't always best on top — sometimes K-in-bot is right). Drill characterization first, then heuristic sweep.
>
>   (B) **Q-high no-pair** — ~150K hands, ~2.5% of grid. Borderline — Q wins top tier maybe 30% of the time vs random opponent. Might need a different setting structure entirely.
>
>   (C) **Trips_pair Rule 14 v2 (adaptive heuristic)** — still has +$1,992 oracle gap from S49 Drill I. Could combine with Session 50's HIMID insight.
>
>   (D) **v45 ML retrain** — capacity-only retrain of v34_dt against v45 residuals. v45 fixed high_only $643/1000h within category; the residual pattern has shifted SIGNIFICANTLY.
>
>   (E) **Carryover deferred items:**
>     - Composite (cat=7) within-class
>     - T-low high_only naive top=lo rule
>     - Round-3 within-trips features
>     - Learned A-vs-C decision tree for Rule 6
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 50):** v45_rule14_Ahigh_DS replaces v44 as production strategy of record. **+$131 full / $0 prefix.** LARGEST single-rule lift in project history. Total project rule count: **14**.

> **🔬 ARTIFACTS (Session 50):**
> 1. **`analysis/scripts/drill_A_high_nopair_characterization.py`** — Drill K (DEFINITIVE Phase 1 characterization, n=660,660)
> 2. **`analysis/scripts/drill_A_high_topA_bot_heuristic.py`** — Drill L (DEFINITIVE Phase 2 heuristic sweep)
> 3. **`analysis/scripts/strategy_v45_rule14_Ahigh_DS.py`** — PRODUCTION
> 4. **`analysis/scripts/grade_v45_rule14_Ahigh.py`** — grader vs v44
> 5. **`SESSION_50_RULE14_AHIGH_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 50 NEW):**
> - **High_only is the project's biggest residual zone.** $412/1000h whole-grid contribution from A-high alone, $833/1000h from total high_only.
> - **HIMID > HIBOT for A-high.** Counter to "stack high cards in bot for kicker strength" intuition. With A on top, Hold'em mid value > Omaha bot kicker rank.
> - **Drill estimates can underpredict actual ship lift.** Drill L estimated +$10; grader measured +$131. Always validate via grade.
> - **S49 sanity-check (pick-difference rate vs production) is project's most important diagnostic.** v45 differs from v44 on 72.2% of fires (vs S49 no-op 0%). Always verify before grading.
> - **Largest residuals come from previously unrepresented categories.** Where else has no rule coverage? K-high no-pair (next session target), trips_pair (only Rule 3 baseline).

> Updated: 2026-05-09 (Session 50)

---

## Headline state at end of Session 50

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v45_rule14_Ahigh_DS** | **PRODUCTION strategy of record (LARGEST SINGLE-RULE LIFT)** (14 rules: v44 + Rule 14). +$131 full / $0 prefix vs v44. Cumulative v39→v45: +$260 full / +$185 prefix. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v44_rule13_three_pair_DS | Predecessor production (Session 48). | `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` |
| v45 (S49 no-op artifact) | NO-OP from S49; do not confuse with current v45 above. | `analysis/scripts/strategy_v45_rule14_trips_pair_DS.py` |
| v43_rule12_two_pair_DS_intact | Predecessor production (Session 47). | `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` |
| v43b_rule12_two_pair_extQ | DEFERRED — Session 48 max≤Q extension. | `analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py` |
| v42_rule11_jpair_pbot_ds | Predecessor production (Session 46). | `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` |
| v41_rule10_v3_ds | Predecessor production (Session 45). | `analysis/scripts/strategy_v41_rule10_v3_ds.py` |
| v40b_rule10_gated | Predecessor production (Session 43). | `analysis/scripts/strategy_v40b_rule10_gated.py` |
| v40_rule10 | Simple variant of Rule 10 (sister, retained). | `analysis/scripts/strategy_v40_rule10.py` |
| v39_rule9 | Predecessor production (Session 42 overnight). | `analysis/scripts/strategy_v39_rule9.py` |
| v38_rule8_qp / v37_rule7_three_pair / v35_rule6_v3 / v33_rule6_trips | Earlier productions. | various |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3). | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained. | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt. | `analysis/scripts/strategy_v36_rule7_high_only.py` |

**Capacity + feature progression — UNCHANGED (ML champion since S38):**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt |
|---|---:|---:|---:|---:|---:|---:|
| **v34** | **34 (33 actual)** | **2** | **83** | **874,548** | **$1,681** | **52.02%** |

**Human-strategy progression (full grid, N=200) — production runtime:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| v40b_rule10_gated (+ Rule 10 gated) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3) | $2,769 | 41.91% | −$264 |
| v42_rule11_jpair_pbot_ds (+ Rule 11) | $2,763 | 41.93% | −$270 |
| v43_rule12_two_pair_DS_intact (+ Rule 12) | $2,727 | 42.20% | −$306 |
| v44_rule13_three_pair_DS (+ Rule 13) | $2,717 | 42.34% | −$316 |
| **v45_rule14_Ahigh_DS (+ Rule 14) — CURRENT PRODUCTION** | **$2,585** | **43.05%** | **−$448** |

---

## What Session 50 produced

**Code:**
- 2 new drills (`drill_A_high_nopair_characterization.py` Drill K Phase 1, `drill_A_high_topA_bot_heuristic.py` Drill L Phase 2)
- 1 new strategy (`strategy_v45_rule14_Ahigh_DS.py`) — PRODUCTION
- 1 new grader (`grade_v45_rule14_Ahigh.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 50 entry; front-matter "Last updated"; Part 5 production-of-record references
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 083 added
- `SESSION_50_RULE14_AHIGH_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 51)

```
Resume Session 51 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 50)
- DECISIONS_LOG.md (latest: Decision 083 — Rule 14 ships as v45,
  LARGEST single-rule lift in project history)
- SESSION_50_RULE14_AHIGH_REPORT.md (Rule 14 finding)
- STRATEGY_GUIDE.md (Session 50 entry in Part 1)
- analysis/scripts/strategy_v45_rule14_Ahigh_DS.py — current production
- analysis/scripts/drill_A_high_nopair_characterization.py — Drill K template
- analysis/scripts/drill_A_high_topA_bot_heuristic.py — Drill L template

State (end of Session 50):
- Production: v45_rule14_Ahigh_DS (14 rules: v44 + Rule 14 A-high
  no-pair + DS/SS HIMID). +$131 full / $0 prefix vs v44 — LARGEST
  single-rule lift in project history.
- Cumulative v39 → v45: +$260 full / +$185 prefix.
- The S43-S50 arc has shipped 6 production rules.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).

USER-PRIORITY DIRECTION FOR SESSION 51:

(A) K-high no-pair drill — apply same Drill K (characterization) + Drill L
    (heuristic sweep) methodology to K-high no-pair (~290K hands,
    ~5% of grid). May need different heuristic (K isn't always best on
    top — sometimes K-in-bot for trip-K Omaha is right).

(B) Q-high no-pair — ~150K hands, ~2.5% of grid. Borderline territory.

(C) Trips_pair Rule 14 v2 (adaptive heuristic) — still has +$1,992
    oracle gap from S49.

(D) v45 ML retrain — capacity-only retrain of v34_dt against v45
    residuals. The residual pattern has shifted significantly.

(E) Carryover (Session 45+ deferrals):
    - Composite (cat=7) within-class
    - T-low high_only naive top=lo rule
    - Round-3 within-trips features
    - Learned A-vs-C decision tree for Rule 6
    - KK/AA single-suited Rule-4-bot residual

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ALL rules on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN PREFIX COVERAGE EXISTS. high_only category has ZERO prefix.
- Methodology rule (Session 50 NEW): high_only is the project's biggest
  residual zone; defensive arc covered pair/two_pair/three_pair, but
  unpaired hands (high_only) had no coverage and yielded biggest ship.
- Methodology rule (Session 50 NEW): HIMID > HIBOT for A-high.
- Methodology rule (Session 50 NEW): drill estimates can underpredict
  actual ship lift; always validate via grade.
- Methodology rule (Session 49 NEW): sanity-check pick-difference rate
  BEFORE grading.
- Methodology rule (Session 47 NEW): cross-class within-pop "DS premium
  within X" lens ships rules reliably.
- Methodology rule (Session 46 NEW): drill "best-in-class minus
  production pick" to discover ship targets.
- Methodology rule (Session 44): cross-class regret averaging is
  confounded; use within-hand pairwise.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
