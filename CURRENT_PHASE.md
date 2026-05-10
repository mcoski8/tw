# Current: Sprint 8 — Session 52 ships **Rule 16 (Q-high no-pair, Q-on-top + DS/SS HIMID) as v47**, completing the A/K/Q-high HIMID family. v46 → v47 score: $2,534 → $2,515 full, $1,522 → $1,522 prefix (UNCHANGED — high_only zero prefix coverage). **+$19/1000h whole-grid full + $0 prefix.** pct_opt: 43.24% → 43.30% full. high_only $3,187 → $3,096 (−$91 within high_only, −2.9%). Cumulative v39 → v47 = −$330 full / −$185 prefix; cumulative v14 → v47 = −$518 full. The three-session high_only sub-arc (S50-S52) shows diminishing returns — A-high −$131 → K-high −$51 → Q-high −$19, totaling −$201 across A+K+Q (19% of grid). Per-fire DS lift INCREASES across sub-pops (lower top-card = worse baseline = bigger relative gap) but pop size DECREASES. J-high estimated +$8-12 — below threshold for further single-pop drills. Critical Q-high finding: oracle picks Q on top only 49% (vs A 93%, K 66%) — 51% non-Q-on-top sub-zone is a Rule 16 v2 candidate.

> **🎯 IMMEDIATE NEXT ACTION (Session 53):**
>
>   **The high_only single-pop arc is hitting diminishing returns. Better targets now:**
>
>   (A) **Rule 14 v2 / Rule 15 v2 / Rule 16 v2** — address non-default top picks (the 7%/34%/51% of A/K/Q-high where oracle prefers a different top card). These could each add +$10-30/1000h whole-grid. Highest leverage per investigation.
>
>   (B) **Trips_pair Rule 14 v2 (adaptive heuristic)** — known +$1,992/1000h oracle gap from S49 Drill I. Requires adaptive logic per S49 finding.
>
>   (C) **v47 ML retrain** — capacity-only retrain of v34_dt against v47 residuals. With 3 high_only ships (Rules 14/15/16), the ML residual pattern has shifted SIGNIFICANTLY. Pattern: previous capacity retrains shipped +$15-58.
>
>   (D) **Composite (cat=7) within-class** — small population (0.25%), high regret ($4,445/1000h). Possible quick wins on quads_trip / two_trips sub-shapes.
>
>   (E) **Carryover deferred items:**
>     - J-high no-pair (small, +$8-12 estimated)
>     - T-low high_only naive top=lo rule
>     - Round-3 within-trips features
>     - Learned A-vs-C decision tree for Rule 6
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 52):** v47_rule16_Qhigh_DS replaces v46 as production strategy of record. **+$19 full / $0 prefix.** Total project rule count: **16**. Completes the A/K/Q-high HIMID family.

> **🔬 ARTIFACTS (Session 52):**
> 1. **`analysis/scripts/drill_Q_high_nopair_characterization.py`** — Drill N (n=150,150)
> 2. **`analysis/scripts/strategy_v47_rule16_Qhigh_DS.py`** — PRODUCTION
> 3. **`analysis/scripts/grade_v47_rule16_Qhigh.py`** — grader vs v46
> 4. **`SESSION_52_RULE16_QHIGH_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 52 NEW):**
> - **The high_only single-pop arc has diminishing returns.** Each successive sub-pop ships less whole-grid lift. Future v2 rules (addressing non-default top picks) likely yield more than continuing single-pop drills.
> - **3+1 transitions from negative to positive at Q-high.** As top-card oracle fraction drops, oracle uses more bot suit profiles. Rule v2's might add 3+1 fallback.
> - **The simple HIMID heuristic is a robust pattern across A/K/Q-high.** Same code structure with only the rank constant changing.

> Updated: 2026-05-09 (Session 52)

---

## Headline state at end of Session 52

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v47_rule16_Qhigh_DS** | **PRODUCTION strategy of record** (16 rules: v46 + Rule 16). +$19 full / $0 prefix vs v46. Cumulative v39→v47: +$330 full / +$185 prefix. | `analysis/scripts/strategy_v47_rule16_Qhigh_DS.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v46_rule15_Khigh_DS | Predecessor production (Session 51, 3rd-largest single-rule lift). | `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` |
| v45_rule14_Ahigh_DS | Predecessor production (Session 50, LARGEST single-rule lift). | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` |
| v44_rule13_three_pair_DS | Predecessor production (Session 48). | `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` |
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
| v45 (S49 no-op artifact) | NO-OP from S49 trips_pair attempt; do not confuse with v45 production above. | `analysis/scripts/strategy_v45_rule14_trips_pair_DS.py` |

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
| v45_rule14_Ahigh_DS (+ Rule 14) | $2,585 | 43.05% | −$448 |
| v46_rule15_Khigh_DS (+ Rule 15) | $2,534 | 43.24% | −$499 |
| **v47_rule16_Qhigh_DS (+ Rule 16) — CURRENT PRODUCTION** | **$2,515** | **43.30%** | **−$518** |

---

## What Session 52 produced

**Code:**
- 1 new drill (`drill_Q_high_nopair_characterization.py` Drill N)
- 1 new strategy (`strategy_v47_rule16_Qhigh_DS.py`) — PRODUCTION
- 1 new grader (`grade_v47_rule16_Qhigh.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 52 entry; front-matter "Last updated"
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 085 added
- `SESSION_52_RULE16_QHIGH_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 53)

```
Resume Session 53 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 52)
- DECISIONS_LOG.md (latest: Decision 085 — Rule 16 ships as v47)
- SESSION_52_RULE16_QHIGH_REPORT.md
- SESSION_51_RULE15_KHIGH_REPORT.md
- SESSION_50_RULE14_AHIGH_REPORT.md
- STRATEGY_GUIDE.md (Sessions 50-52 entries in Part 1)
- analysis/scripts/strategy_v47_rule16_Qhigh_DS.py — current production
- analysis/scripts/drill_Q_high_nopair_characterization.py — Drill N

State (end of Session 52):
- Production: v47_rule16_Qhigh_DS (16 rules: v46 + Rule 16 Q-high
  no-pair + DS/SS HIMID). +$19 full / $0 prefix vs v46.
- Cumulative v39 → v47: +$330 full / +$185 prefix.
- Cumulative v14 → v47: +$518 full.
- The S43-S52 arc has shipped 8 production rules.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).
- The high_only single-pop arc (Rules 14/15/16) is hitting diminishing
  returns: A-high −$131 → K-high −$51 → Q-high −$19.

USER-PRIORITY DIRECTION FOR SESSION 53 (recommended):

(A) Rule 14/15/16 v2 — address non-default top picks. The 7%/34%/51%
    of A/K/Q-high where oracle prefers a non-A/K/Q on top is a known
    coverage gap. May yield +$10-30 each.

(B) Trips_pair Rule 14 v2 (adaptive heuristic) — known +$1,992/1000h
    oracle gap from S49 Drill I.

(C) v47 ML retrain — capacity-only retrain of v34_dt against v47
    residuals. The residual pattern has shifted significantly with
    3 high_only ships.

(D) Composite (cat=7) within-class — small pop, high regret.

(E) J-high no-pair (small, +$8-12 estimated; below threshold).

(F) Carryover (Session 45+ deferrals):
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
- Methodology rule (Session 52 NEW): the high_only single-pop arc has
  diminishing returns; future v2 rules likely more productive than
  continuing single-pop drills.
- Methodology rule (Session 52 NEW): 3+1 transitions from negative to
  positive at Q-high — Rule v2's might add 3+1 fallback.
- Methodology rule (Session 51 NEW): the Drill K + Drill L playbook
  generalizes across high-card sub-pops.
- Methodology rule (Session 50 NEW): high_only is the project's biggest
  residual zone.
- Methodology rule (Session 50 NEW): HIMID > HIBOT for A-high (and K/Q-high).
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
