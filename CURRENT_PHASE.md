# Current: Sprint 8 — Session 46 ships **Rule 11 (J-pair pair-to-bot DS) as v42**, the project's first single-cell rule. v41 → v42 score: $2,769 → $2,763 full, $1,616 → $1,616 prefix (unchanged — Rule 11 fires on 0 prefix hands; J-pair-J has zero prefix coverage). **+$6/1000h whole-grid full + $0 prefix.** pct_opt full: 41.91% → 41.93%. Cumulative v39 → v42 = −$83 full / −$91 prefix. Origin: Drill A's per-pair-rank breakdown (Session 45) found A5−A2 = +$2,975/1000h at P=J specifically. Session 46 ran a focused J-pair-J drill (Drill D, n=34,272) to validate the apples-to-apples comparison: **A5−A1 = +$1,004/1000h** (pair-to-bot DS beats pair-mid DS even when both achievable). Drill D's "v41 vs best-in-class" view found A5 vs v41 = **+$3,769/1000h within fires** — the largest cross-class override at J-pair-J. v41 picks A5 0% of the time. Rule 11 design: both J's to BOT, pick 2 lowest-rank singletons completing 2+2 DS, TOP=lowest of remaining 3 singletons, MID=the other 2; fall through to v41 if no DS-pair-in-bot achievable. Heuristic captures 56% of A5's oracle ceiling — heuristic-sharpening queued for Session 47+.

> **🎯 IMMEDIATE NEXT ACTION (Session 47):**
>
>   (A) **Rule 11 heuristic refinement.** Currently captures 56% of the A5 oracle ceiling (+$3,769/1000h within fires). Sweep alternative tie-breaks: lowest-rank vs highest-rank singleton-pairs in bot; lowest-vs-middle-vs-highest top placement among the 3 remaining singletons; consider connectivity preferences. Expected residual: +$3-5/1000h whole-grid full.
>
>   (B) **Two_pair within-class suit-aware bot (B1−B2 = +$1,864/1000h).** Drill B's sister candidate from Session 45. Two_pair is "ML territory" cross-class but this within-class rule may be feasible. Requires a setting-builder for two_pair both-intact + DS-bot that selects which pair joins mid (vs bot) and which singletons fill the bot to form DS. Higher complexity than Rule 11.
>
>   (C) **Other A_i − v41 lift opportunities at J-pair-J.** Drill D showed A6 (pair-bot non-DS) vs v41 = +$734/1000h. If a refined Rule 11+ also picks pair-to-bot when DS not achievable, additional small lift may exist. Investigate.
>
>   (D) **v42 ML retrain.** Capacity-only retrain of v34_dt against v42 residuals. Pattern: previous capacity retrains shipped +$15-58.
>
>   (E) **Carryover deferred items:**
>     - Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
>     - T-low high_only naive top=lo rule (~+$8 full-only)
>     - Round-3 within-trips features (S42 carryover)
>     - Learned A-vs-C decision tree for Rule 6 (S38-40 carryover)
>     - Trips_pair G3 oracle exploration (+$85 ceiling)
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 46):** v42_rule11_jpair_pbot_ds replaces v41 as production strategy of record. **+$6 full / $0 prefix.** First single-cell rule of the project. Total project rule count: **11**.

> **🔬 ARTIFACTS (Session 46):**
> 1. **`analysis/scripts/drill_J_pair_pair_to_bot_DS.py`** — focused J-pair-J within-hand pairwise + v41 class distribution + v41-vs-best-in-class lifts (DEFINITIVE; n=34,272)
> 2. **`analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py`** — PRODUCTION
> 3. **`analysis/scripts/grade_v42_rule11_jpair_pbot_ds.py`** — grader vs v41
> 4. **`SESSION_46_RULE11_JPAIR_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 46 NEW):**
> - **Single-cell rules ship at <$10/1000h whole-grid lift when within-fires lift is large.** Rule 11 fires on 0.285% of grid; within-fires lift is +$2,105/1000h. Both numbers are meaningful for different audiences.
> - **Single-cell rules at extreme P-rank cells have natural prefix immunity.** J-pair-J has zero prefix coverage; Rule 11 fires on 0 prefix hands; prefix score guaranteed unchanged. Same precedent as S41/S43 high_only-zero-prefix.
> - **Drill the "best-in-class minus production pick" lens to discover single-cell rules.** Drill D's table directly identified A5's +$3,769 as 6× the next-best class. Use this for future single-cell discovery.
> - **Don't hold rules for "perfect heuristic-vs-oracle".** v42's 56%-of-ceiling capture is a clean ship; the remaining ~+$5/1000h is queued as a separate refinement.

> Updated: 2026-05-09 (Session 46)

---

## Headline state at end of Session 46

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v42_rule11_jpair_pbot_ds** | **PRODUCTION strategy of record** (11 rules: v41 + Rule 11 J-pair pair-to-bot DS, first single-cell rule). +$6 full / $0 prefix lift over v41. Cumulative v39→v42: +$83 full / +$91 prefix. | `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v41_rule10_v3_ds | Predecessor production (Session 45 ship). Retained for reference. | `analysis/scripts/strategy_v41_rule10_v3_ds.py` |
| v40b_rule10_gated | Predecessor production (Session 43 ship). Retained for reference. | `analysis/scripts/strategy_v40b_rule10_gated.py` |
| v40_rule10 | Simple variant of Rule 10 (no gate, no suit-awareness). +$23 full / +$37 prefix vs v39. Retained for human-memorability fork. | `analysis/scripts/strategy_v40_rule10.py` |
| v39_rule9 | Predecessor production (Session 42 overnight ship) | `analysis/scripts/strategy_v39_rule9.py` |
| v38_rule8_qp | Predecessor production | `analysis/scripts/strategy_v38_rule8_qp.py` |
| v37_rule7_three_pair | Earlier production runtime | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips. NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` |
| v33_rule6_trips | Earlier production runtime | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt for high_only | `analysis/scripts/strategy_v36_rule7_high_only.py` |

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
| v40_rule10 (+ Rule 10, simple) — sister candidate | $2,824 | 41.15% | −$209 |
| v40b_rule10_gated (+ Rule 10 gated) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3 suit-aware) | $2,769 | 41.91% | −$264 |
| **v42_rule11_jpair_pbot_ds (+ Rule 11) — CURRENT PRODUCTION** | **$2,763** | **41.93%** | **−$270** |

---

## What Session 46 produced

**Code:**
- 1 new drill (`drill_J_pair_pair_to_bot_DS.py`) — focused J-pair-J within-hand pairwise
- 1 new strategy (`strategy_v42_rule11_jpair_pbot_ds.py`) — PRODUCTION
- 1 new grader (`grade_v42_rule11_jpair_pbot_ds.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 46 entry; front-matter "Last updated"; Part 5 production-of-record references
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 079 added
- `SESSION_46_RULE11_JPAIR_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 47)

```
Resume Session 47 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 46)
- DECISIONS_LOG.md (latest: Decision 079 — Rule 11 ships as v42)
- SESSION_46_RULE11_JPAIR_REPORT.md (J-pair pair-to-bot DS finding)
- SESSION_45_RULE10_V3_REPORT.md (Rule 10 v3 finding)
- STRATEGY_GUIDE.md (Session 46 entry in Part 1; Part 5 + 6 updated)
- analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py — current production
- analysis/scripts/drill_J_pair_pair_to_bot_DS.py — Drill D (definitive)

State (end of Session 46):
- Production: v42_rule11_jpair_pbot_ds (11 rules: v41 + Rule 11 J-pair
  pair-to-bot DS — first single-cell rule). +$6 full / $0 prefix vs v41.
  Cumulative v39 → v42: +$83 full / +$91 prefix.
- v41 retained as predecessor reference.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).
- Drill D definitively confirmed Rule 11 (A5 vs A1 = +$1,004 within-hand,
  A5 vs v41 = +$3,769 within fires).
- v42 heuristic captures 56% of A5 oracle ceiling — refinement queued.

USER-PRIORITY DIRECTION FOR SESSION 47 (recommended):

(A) Rule 11 heuristic refinement. Sweep tie-breaks for singleton-pair
    selection and top placement to capture more of the +$3,769/1000h
    within-fires ceiling. Currently captures 56% (~+$2,105 within fires);
    the gap is +$1,664/1000h within fires ≈ +$5/1000h whole-grid full.
    If positive, ship as v42b.

(B) Two_pair within-class suit-aware bot (B1−B2 = +$1,864/1000h).
    Drill B's sister candidate. Setting-builder for two_pair both-intact
    + DS-bot. Higher complexity than Rule 11 but larger pop coverage
    (262K hands).

(C) Other A_i − v41 lift opportunities at J-pair-J (e.g., A6 +$734).
    Investigate whether there are additional residual single-cell wins.

(D) v42 ML retrain. Capacity-only retrain of v34_dt against v42 residuals.

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
  WHEN PREFIX COVERAGE EXISTS. Rule 11's J-pair-J has zero prefix
  coverage — same precedent as high_only.
- Methodology rule (Session 46 NEW): single-cell rules ship at <$10/1000h
  whole-grid lift when within-fires lift is large.
- Methodology rule (Session 46 NEW): drill "best-in-class minus
  production pick" to discover single-cell rules.
- Methodology rule (Session 45 NEW): pair structure dominates suit
  structure universally in J-low pair/two_pair.
- Methodology rule (Session 45 NEW): within-class suit-aware bot is a
  generalizable rule pattern.
- Methodology rule (Session 45 NEW): small-sample within-hand findings
  need replication before being elevated to "rules".
- Methodology rule (Session 44): cross-class regret averaging is
  confounded; use within-hand pairwise.
- Methodology rule (Session 43 NEW): weak-hand top inversion.
- Methodology rule (Session 42 NEW): a rule with prefix regression
  >2× the full-grid lift does NOT ship.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
