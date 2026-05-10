# Current: Sprint 8 — Session 51 ships **Rule 15 (K-high no-pair, K-on-top + DS/SS HIMID) as v46 — 3rd-LARGEST single-rule lift in project history (+$51/1000h whole-grid full)**. v45 → v46 score: $2,585 → $2,534 full, $1,522 → $1,522 prefix (UNCHANGED — high_only zero prefix coverage). pct_opt: 43.05% → 43.24% full / 53.06% (unchanged) prefix. high_only $3,439 → $3,187 (−$252 within high_only, −7.3%). high_only pct_opt 23.3% → 24.2% (+0.9%). p90 regret IMPROVED 0.745→0.730. Cumulative v39 → v46 = −$311 full / −$185 prefix. Origin: continued the high_only attack from Session 50; same Drill K + Drill L methodology applied to K-high (the 2nd-largest residual zone after A-high). Drill M characterization (n=330,330 = 5.5% of grid) found K-high contributes $226/1000h whole-grid regret. Critical difference vs A-high: oracle picks K on top only 66% of the time (vs A on top 93%) — the 34% non-K-on-top sub-zone is a known Rule 15 v2 candidate. Best-in-DS vs v45 = +$2,999/1000h within fires (LARGER per-fire than A-high). The S43-S51 arc has now shipped 7 production rules totaling −$311 full / −$185 prefix — average ship −$44/1000h per rule.

> **🎯 IMMEDIATE NEXT ACTION (Session 52):**
>
>   (A) **Q-high no-pair drill** — same playbook (~150K hands, ~2.5% of grid). Q is borderline for top tier (loses to A or K, ~30% top win rate). Oracle likely picks Q-on-top even less often than K. May need different heuristic structure (Q-in-bot for trip-Q Omaha?).
>
>   (B) **J-low high_only no-pair (defensive zone)** — currently uncovered for high_only; S43 deferred this. Different mechanism (weak-hand top inversion).
>
>   (C) **Rule 14 v2 / Rule 15 v2 — address non-A/non-K top picks** in the existing rules. Both have known gaps where oracle prefers a different card on top.
>
>   (D) **Trips_pair Rule 14 v2 (adaptive heuristic)** — still has +$1,992 oracle gap from S49.
>
>   (E) **v46 ML retrain** — capacity-only retrain of v34_dt against v46 residuals. v46 fixed high_only $895/1000h within category cumulatively (Rules 14+15); residual pattern has shifted significantly.
>
>   (F) **Carryover deferred items:**
>     - Composite (cat=7) within-class
>     - T-low high_only naive top=lo rule
>     - Round-3 within-trips features
>     - Learned A-vs-C decision tree for Rule 6
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 51):** v46_rule15_Khigh_DS replaces v45 as production strategy of record. **+$51 full / $0 prefix.** 3rd-LARGEST single-rule lift in project history. Total project rule count: **15**.

> **🔬 ARTIFACTS (Session 51):**
> 1. **`analysis/scripts/drill_K_high_nopair_characterization.py`** — Drill M (DEFINITIVE, n=330,330)
> 2. **`analysis/scripts/strategy_v46_rule15_Khigh_DS.py`** — PRODUCTION
> 3. **`analysis/scripts/grade_v46_rule15_Khigh.py`** — grader vs v45
> 4. **`SESSION_51_RULE15_KHIGH_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 51 NEW):**
> - **The Drill K + Drill L playbook generalizes across high-card sub-pops.** Same methodology produces parallel rules for A-high, K-high, and likely Q-high.
> - **High-rank sub-pops have known coverage gaps.** Rule 15 v1 addresses ~66% of K-high optimally; 34% "non-K-on-top" residual remains for Rule 15 v2.
> - **Per-fire lift can exceed prior sub-pop's** even with smaller whole-grid lift, due to population size.

> Updated: 2026-05-09 (Session 51)

---

## Headline state at end of Session 51

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v46_rule15_Khigh_DS** | **PRODUCTION strategy of record (3rd-LARGEST single-rule lift)** (15 rules: v45 + Rule 15). +$51 full / $0 prefix vs v45. Cumulative v39→v46: +$311 full / +$185 prefix. | `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
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
| **v46_rule15_Khigh_DS (+ Rule 15) — CURRENT PRODUCTION** | **$2,534** | **43.24%** | **−$499** |

---

## What Session 51 produced

**Code:**
- 1 new drill (`drill_K_high_nopair_characterization.py` Drill M)
- 1 new strategy (`strategy_v46_rule15_Khigh_DS.py`) — PRODUCTION
- 1 new grader (`grade_v46_rule15_Khigh.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 51 entry; front-matter "Last updated"
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 084 added
- `SESSION_51_RULE15_KHIGH_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 52)

```
Resume Session 52 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 51)
- DECISIONS_LOG.md (latest: Decision 084 — Rule 15 ships as v46)
- SESSION_51_RULE15_KHIGH_REPORT.md
- SESSION_50_RULE14_AHIGH_REPORT.md
- STRATEGY_GUIDE.md (Sessions 50-51 entries in Part 1)
- analysis/scripts/strategy_v46_rule15_Khigh_DS.py — current production
- analysis/scripts/drill_K_high_nopair_characterization.py — Drill M template

State (end of Session 51):
- Production: v46_rule15_Khigh_DS (15 rules: v45 + Rule 15 K-high
  no-pair + DS/SS HIMID). +$51 full / $0 prefix vs v45.
- Cumulative v39 → v46: +$311 full / +$185 prefix.
- The S43-S51 arc has shipped 7 production rules.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).

USER-PRIORITY DIRECTION FOR SESSION 52:

(A) Q-high no-pair drill — same playbook applied to Q-high (~150K hands).
    Q is borderline (loses to A or K, ~30% top win rate). May need
    different heuristic.

(B) J-low / T-low high_only — defensive territory, S43 deferred. Different
    mechanism (weak-hand top inversion).

(C) Rule 14 v2 / Rule 15 v2 — address non-A/non-K top picks (the 34%
    of K-high where oracle picks something else).

(D) Trips_pair Rule 14 v2 (adaptive heuristic) — +$1,992 oracle gap
    from S49.

(E) v46 ML retrain — capacity-only retrain of v34_dt against v46 residuals.

(F) Carryover (Session 45+ deferrals):
    - Composite (cat=7) within-class
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
- Methodology rule (Session 51 NEW): the Drill K + Drill L playbook
  generalizes across high-card sub-pops; produces parallel rules.
- Methodology rule (Session 51 NEW): high-rank sub-pops have known
  coverage gaps; Rule v1's address main top-card; v2's needed for
  non-default top placements.
- Methodology rule (Session 50 NEW): high_only is the project's biggest
  residual zone.
- Methodology rule (Session 50 NEW): HIMID > HIBOT for A-high (and K-high).
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
