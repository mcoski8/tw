# Current: Sprint 8 — Session 49 was a NO-SHIP investigation. Trips_pair within-class DS was investigated but yielded a no-op rule. v44 remains production strategy of record (cumulative v39 → v44 = −$129 full / −$185 prefix from the S43-S48 suit-dominance arc).

> **Session 49 findings (NO PRODUCTION CHANGE):**
>
> **Drill I (within-hand pairwise, n=171,600) — DEFINITIVE.** v44 already picks pair-bot 85% of fires for trips_pair, DS-bot 75%. V3 (pair-bot DS) is universally optimal: V3 vs V5 (pair-split DS) = +$13,397/1000h within fires. **v44 vs best-in-V3 = +$1,992/1000h within fires** — the residual oracle gap.
>
> **Drill J (sub-config sweep) — POPULATION-CONFOUNDED methodology error.** Tested 7 sub-config variants. Reported V_B_TOP_SING_HI as +$4,293/1000h winner, but the comparison was confounded (variant's mean on its achievability subset vs v44's mean on full V3 subset). S44 methodology rule violated.
>
> **Rule 14 attempt (v45) — NO-OP.** Designed v45 to pick V_B_TOP_SING_HI when achievable. Sanity check: Rule 14 fires on 17,498 of 50K trips_pair hands but **differs from v44's pick on 0 of them**. Grade confirmed v45 vs v44 = $0/1000h. v44's existing pick (via v3's Rule 3 fall-through) ALREADY picks V_B_TOP_SING_HI when achievable.
>
> **The +$1,992 oracle gap is real but requires adaptive logic to capture, not a fixed-variant heuristic.** v45 retained as artifact for reference; deferred for Session 50+ refinement.

> **🎯 IMMEDIATE NEXT ACTION (Session 50):**
>
>   (A) **Trips_pair Rule 14 v2 (adaptive heuristic).** Target the +$1,992 oracle gap by identifying WHICH V3 sub-config the oracle picks on hands where v44's pick differs from oracle. Likely depends on suit alignment between trip / pair / sings. Drill: per-hand v44-vs-oracle comparison, classify the oracle pick's structural features, find a heuristic that captures more of the gap.
>
>   (B) **Composite (cat=7) within-class DS-bot.** Smallest category (14,742 hands, 0.25%) but highest regret ($4,445/1000h). Cat=7 = quads_pair, quads_trip, two_trips, T2P, plain quads. Rules 8 (quads_pair) and 9 (T2P, TT, plain quads) handle subsets — drill the residual sub-shapes.
>
>   (C) **v44 ML retrain.** Capacity-only retrain of v34_dt against v44 residuals. Pattern: previous capacity retrains shipped +$15-58. With v44 fixing three_pair $572/1000h within category, the residual pattern has shifted significantly.
>
>   (D) **Two_pair max≤Q refinement.** v43b had +$14 full but -$6 prefix. Find a sharper gate that picks up the full lift WITHOUT regressing prefix.
>
>   (E) **Carryover deferred items:**
>     - Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
>     - T-low high_only naive top=lo rule
>     - Round-3 within-trips features
>     - Learned A-vs-C decision tree for Rule 6
>     - KK/AA single-suited Rule-4-bot residual

> **❌ NO SHIP (Session 49):** v44 remains production. v45 designed but is a no-op vs v44 (sanity check found 0 picks differ on 17,498 fires). Total project rule count UNCHANGED at **13**.

> **🔬 ARTIFACTS (Session 49):**
> 1. **`analysis/scripts/drill_trips_pair_DS_within_intact.py`** — Drill I (DEFINITIVE within-hand pairwise; reveals +$1,992 oracle gap)
> 2. **`analysis/scripts/drill_trips_pair_pbot_DS_subconfig.py`** — Drill J (POPULATION-CONFOUNDED; kept for diagnostic / methodology reference)
> 3. **`analysis/scripts/strategy_v45_rule14_trips_pair_DS.py`** — NO-OP artifact
> 4. **`analysis/scripts/grade_v45_rule14_trips_pair.py`** — grader (confirms 0 lift)
> 5. **`SESSION_49_TRIPS_PAIR_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 49 NEW):**
> - **Cross-class means are CONFOUNDED — always within-hand pairwise.** Re-iterating S44 lesson because I violated it in Drill J.
> - **Sanity-check pick-difference rate BEFORE grading.** A simple "does the rule actually pick differently from production?" test catches no-op rules early.
> - **The right ship target is "where production differs from oracle"**, not "pick variant X when achievable". Some upstream tie-breaks already match the candidate variant.
> - **Happy-accident upstream tie-breaks can already capture optimization potential.** v3's Rule 3 trips_pair logic apparently was picking V_B_TOP_SING_HI all along.

> Updated: 2026-05-09 (Session 49)

---

## Headline state at end of Session 49 (UNCHANGED from end of Session 48)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v44_rule13_three_pair_DS** | **PRODUCTION strategy of record** (13 rules: v43 + Rule 13). +$11 full / +$29 prefix vs v43. Cumulative v39→v44: +$129 full / +$185 prefix. | `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v45 | NO-OP artifact (Session 49); same picks as v44 on every fire. | `analysis/scripts/strategy_v45_rule14_trips_pair_DS.py` |
| v43_rule12_two_pair_DS_intact | Predecessor production (Session 47). | `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` |
| v43b_rule12_two_pair_extQ | DEFERRED — Session 48 max≤Q extension; +$14 full but −$6 prefix. | `analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py` |
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

**Capacity + feature progression — UNCHANGED:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt |
|---|---:|---:|---:|---:|---:|---:|
| **v34** | **34 (33 actual)** | **2** | **83** | **874,548** | **$1,681** | **52.02%** |

**Human-strategy progression (full grid, N=200) — production runtime UNCHANGED:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8 quads_pair) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| v40b_rule10_gated (+ Rule 10 gated) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3 suit-aware) | $2,769 | 41.91% | −$264 |
| v42_rule11_jpair_pbot_ds (+ Rule 11) | $2,763 | 41.93% | −$270 |
| v43_rule12_two_pair_DS_intact (+ Rule 12) | $2,727 | 42.20% | −$306 |
| **v44_rule13_three_pair_DS (+ Rule 13) — CURRENT PRODUCTION** | **$2,717** | **42.34%** | **−$316** |

---

## What Session 49 produced

**Code:**
- 2 new drills (`drill_trips_pair_DS_within_intact.py` Drill I — DEFINITIVE; `drill_trips_pair_pbot_DS_subconfig.py` Drill J — POPULATION-CONFOUNDED retained for methodology reference)
- 1 new strategy NO-OP (`strategy_v45_rule14_trips_pair_DS.py`) — same picks as v44 on every fire
- 1 new grader (`grade_v45_rule14_trips_pair.py`) — confirms 0 lift

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 49 entry; "Last updated" pointer unchanged from Session 48 since no production change
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 082 added (negative)
- `SESSION_49_TRIPS_PAIR_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 50)

```
Resume Session 50 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 49)
- DECISIONS_LOG.md (latest: Decision 082 — Session 49 NO SHIP)
- SESSION_49_TRIPS_PAIR_REPORT.md (negative finding + methodology lesson)
- SESSION_48_RULE13_THREE_PAIR_REPORT.md (Rule 13 finding)
- SESSION_47_RULE12_TWO_PAIR_REPORT.md (Rule 12 finding)
- STRATEGY_GUIDE.md (Session 48 entry in Part 1; Session 49 added but production unchanged)
- analysis/scripts/strategy_v44_rule13_three_pair_DS.py — CURRENT production
- analysis/scripts/drill_trips_pair_DS_within_intact.py — Drill I (definitive)

State (end of Session 49):
- Production: v44_rule13_three_pair_DS (UNCHANGED). +$129 full / +$185
  prefix cumulative since v39.
- Session 49 was a no-ship investigation: trips_pair within-class DS
  yielded a no-op rule (v45 = v44).
- The +$1,992 oracle gap from Drill I is real but requires adaptive
  logic, not fixed-variant selection.
- v45 retained as artifact for methodology reference.

USER-PRIORITY DIRECTION FOR SESSION 50:

(A) Trips_pair Rule 14 v2 (adaptive heuristic). Target the +$1,992
    oracle gap by drilling per-hand v44-vs-oracle comparisons and
    extracting a heuristic that captures more of the gap.

(B) Composite (cat=7) within-class DS-bot. Smallest category
    (0.25% of grid) but highest regret ($4,445/1000h). Cat=7 =
    quads_pair + quads_trip + two_trips + T2P + plain quads. Rules 8, 9
    handle subsets — drill the residual.

(C) v44 ML retrain. Capacity-only retrain of v34_dt against v44 residuals.

(D) Two_pair max≤Q refinement. v43b had +$14 full / -$6 prefix —
    find a sharper gate.

(E) Carryover (Session 45+ deferrals):
    - Q5 J-high no-pair multi-feature deep dive
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
  WHEN PREFIX COVERAGE EXISTS.
- Methodology rule (Session 49 NEW): cross-class means are CONFOUNDED —
  always within-hand pairwise (re-iterating S44 lesson).
- Methodology rule (Session 49 NEW): sanity-check pick-difference rate
  BEFORE grading; catches no-op rules early.
- Methodology rule (Session 49 NEW): the right ship target is "where
  production differs from oracle", not "pick variant X when achievable".
- Methodology rule (Session 48 NEW): within-class DS doesn't always
  favor "highest pairs in bot" — depends on whether bot is already strong.
- Methodology rule (Session 48 NEW): skip-the-trap design pattern.
- Methodology rule (Session 47 NEW): cross-class within-pop "DS premium
  within X" lens ships rules reliably across pair/two_pair/three_pair.
- Methodology rule (Session 46 NEW): single-cell rules ship at <$10/1000h
  whole-grid lift when within-fires lift is large.
- Methodology rule (Session 44): cross-class regret averaging is
  confounded; use within-hand pairwise.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
