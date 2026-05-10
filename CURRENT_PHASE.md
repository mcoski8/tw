# Current: Sprint 8 — Session 53 OVERNIGHT ships **Rule 17 (comprehensive high_only generalized handler) as v52**. v47 → v52 score: $2,515 → $2,498 full, $1,522 → $1,522 prefix (UNCHANGED — high_only zero prefix coverage). **+$17/1000h whole-grid full + $0 prefix.** pct_opt: 43.30% → 43.34% full. high_only $3,096 → $3,014 (−$82 within high_only, −2.6%). p90 regret IMPROVED 0.725→0.720. Cumulative v39 → v52 = −$348 full / −$185 prefix; v14 → v52 = −$535 full. Origin: user-asked overnight investigation extended high_only HIMID family from A/K/Q-high (Rules 14/15/16) to ALL sub-pops AND added defensive top-inversion. Tested 3 strategies: v48 (HIMID alone, +$8), v50 (HIMID + A/K/Q/J defensive ≤ s2 8, regressed −$6 vs v48 because A-high defensive HURTS — A-on-top is right 91-94% even at s2 ≤ 8), v52 (smart combo skipping A defensive, always defensive max ≤ T, gated K/Q/J, +$17). Per-(max, s2) characterization revealed defensive dominates for max ≤ T (62-86% of hands), HIMID dominates for A-high (93%+), mixed for K/Q/J. v52 design covers all max ≥ 7 sub-pops with the right offensive/defensive structure per-cell.

> **🎯 IMMEDIATE NEXT ACTION (Session 54):**
>
>   The high_only family is now thoroughly covered (Rules 14-17). Remaining:
>
>   (A) **Rule 17 v2 — non-default top picks** (e.g., Q-high oracle picks J on top in 10% of cases when 2nd-high is J/T). Drill O has the data.
>
>   (B) **Trips_pair Rule 14 v2 (adaptive heuristic)** — known +$1,992 oracle gap from S49.
>
>   (C) **Composite (cat=7) within-class** — high regret per hand ($4,445/1000h).
>
>   (D) **v52 ML retrain** — capacity-only retrain of v34_dt against v52 residuals (significantly shifted with 4 high_only ships).
>
>   (E) **Investigate "where does v52 still differ from oracle"** to find the next high-leverage zone.

> **✅ NEW SHIP (Session 53 overnight):** v52_full_high_only_handler replaces v47 as production strategy of record. **+$17 full / $0 prefix.** Total project rule count: **17**.

> **🔬 ARTIFACTS (Session 53 overnight):**
> 1. **`analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py`** — sister, +$8 alone
> 2. **`analysis/scripts/strategy_v50_rules22_23_high_only_defensive.py`** — sister, regressed
> 3. **`analysis/scripts/strategy_v52_full_high_only_handler.py`** — PRODUCTION
> 4. **`analysis/scripts/strategy_v51_defensive_max_le_J.py`** — untested sister
> 5. **`analysis/scripts/strategy_v53_defensive_KQJ_only.py`** — untested sister
> 6. **`analysis/scripts/grade_v48_rules17_21.py`** + `grade_v50_defensive.py` + `grade_v52_full_handler.py`
> 7. **`analysis/scripts/drill_Q_high_non_Q_top_characterization.py`** — Drill O
> 8. **`SESSION_53_OVERNIGHT_REPORT.md`**

> **📓 METHODOLOGY LESSONS (Session 53 overnight NEW):**
> - **High-rank sub-pops (A/K) defy the defensive playbook.** Even at low s2, oracle still wants A-on-top (91-94%) and K-on-top (54-71%). Don't blindly extend defensive to all max ranks.
> - **Low-rank sub-pops (max ≤ T) overwhelmingly favor defensive.** For T-high through 8-high, oracle picks max-on-top only 3-15%. HIMID is wrong on 85-97% of these.
> - **Per-(max, s2) characterization is the right diagnostic.** Cell-level oracle distributions reveal the right gates.
> - **Layered ships can regress.** v50 added defensive overrides on top of v48 and regressed. Always test the layered combo, not just standalone components.

> Updated: 2026-05-10 (Session 53 overnight)

---

## Headline state at end of Session 53 (overnight)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION** (17 rules: v47 + Rule 17 = comprehensive high_only). +$17 full / $0 prefix vs v47. Cumulative v39→v52: +$348 full / +$185 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v47_rule16_Qhigh_DS | Predecessor production (Session 52). | `analysis/scripts/strategy_v47_rule16_Qhigh_DS.py` |
| v46_rule15_Khigh_DS | Predecessor production (Session 51). | `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` |
| v45_rule14_Ahigh_DS | Predecessor production (Session 50, LARGEST single-rule lift +$131). | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` |
| v48_rules17_21_high_only_HIMID | Sister, S53 overnight (+$8 alone, superseded). | `analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py` |
| v50_rules22_23_high_only_defensive | Sister, S53 overnight (regressed −$6 vs v48). | `analysis/scripts/strategy_v50_rules22_23_high_only_defensive.py` |
| v51_defensive_max_le_J | Sister untested. | `analysis/scripts/strategy_v51_defensive_max_le_J.py` |
| v53_defensive_KQJ_only | Sister untested. | `analysis/scripts/strategy_v53_defensive_KQJ_only.py` |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier productions | various |
| v32_dt | Predecessor ML | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines | various |
| v38_rule8_two_pair_DEFERRED, v45 (S49 no-op), v36_rule7_high_only | Various deferred/archived | various |

**Capacity + feature progression — UNCHANGED:**

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
| v40b_rule10_gated (+ Rule 10) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3) | $2,769 | 41.91% | −$264 |
| v42_rule11_jpair_pbot_ds (+ Rule 11) | $2,763 | 41.93% | −$270 |
| v43_rule12_two_pair_DS_intact (+ Rule 12) | $2,727 | 42.20% | −$306 |
| v44_rule13_three_pair_DS (+ Rule 13) | $2,717 | 42.34% | −$316 |
| v45_rule14_Ahigh_DS (+ Rule 14) | $2,585 | 43.05% | −$448 |
| v46_rule15_Khigh_DS (+ Rule 15) | $2,534 | 43.24% | −$499 |
| v47_rule16_Qhigh_DS (+ Rule 16) | $2,515 | 43.30% | −$518 |
| **v52_full_high_only_handler (+ Rule 17) — CURRENT PRODUCTION** | **$2,498** | **43.34%** | **−$535** |

---

## What Session 53 (overnight) produced

**Code:**
- 5 strategies (v48, v50, v51, v52 PRODUCTION, v53)
- 3 graders (v48, v50, v52)
- 1 drill (Drill O — Q-high non-Q-on-top characterization)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 53 entry; front-matter "Last updated"
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 086 added
- `SESSION_53_OVERNIGHT_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 54)

```
Resume Session 54 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 53 overnight)
- DECISIONS_LOG.md (latest: Decision 086 — Rule 17 ships as v52)
- SESSION_53_OVERNIGHT_REPORT.md
- STRATEGY_GUIDE.md (Session 53 entry in Part 1)
- analysis/scripts/strategy_v52_full_high_only_handler.py — current production
- analysis/scripts/drill_Q_high_non_Q_top_characterization.py — Drill O

State (end of Session 53 overnight):
- Production: v52_full_high_only_handler (17 rules: v47 + Rule 17 =
  comprehensive high_only generalized handler). +$17 full / $0 prefix.
- Cumulative v39 → v52: +$348 full / +$185 prefix.
- Cumulative v14 → v52: +$535 full.
- The S43-S53 arc has shipped 9 production rules.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).
- The high_only family (Rules 14-17) is now thoroughly covered.

USER-PRIORITY DIRECTION FOR SESSION 54:

(A) Rule 17 v2 — address non-default top picks. Q-high oracle picks
    J on top 10%, T on top 4%, etc. Could be next sub-rule.

(B) Trips_pair Rule 14 v2 (adaptive heuristic) — known +$1,992 oracle
    gap from S49.

(C) Composite (cat=7) within-class — high regret per hand ($4,445/1000h).

(D) v52 ML retrain — capacity-only retrain of v34_dt against v52
    residuals (significantly shifted with 4 high_only ships).

(E) "Where does v52 still differ from oracle?" — characterization to
    find next high-leverage zone.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Methodology rule (Session 53 NEW): high-rank sub-pops defy defensive;
  low-rank sub-pops favor defensive; per-(max, s2) cells reveal the
  right gates.
- Methodology rule (Session 53 NEW): layered ships can regress;
  always test the combo not just components.
- Methodology rule (Session 52 NEW): the high_only single-pop arc has
  diminishing returns.
- Methodology rule (Session 50 NEW): HIMID > HIBOT for A-high.
- Methodology rule (Session 50 NEW): drill estimates can underpredict
  actual ship lift.
- Methodology rule (Session 49 NEW): sanity-check pick-difference rate
  BEFORE grading.
- Methodology rule (Session 47 NEW): cross-class within-pop "DS premium"
  lens ships rules reliably.
- Methodology rule (Session 46 NEW): drill "best-in-class minus
  production pick" to discover ship targets.
- Methodology rule (Session 44): cross-class regret averaging is
  confounded; use within-hand pairwise.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
