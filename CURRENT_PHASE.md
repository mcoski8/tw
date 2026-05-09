# Current: Sprint 8 — Session 45 ships **Rule 10 v3 (suit-aware bot construction) as v41**, the new production strategy of record. v40b → v41 score: $2,798 → $2,769 full, $1,670 → $1,616 prefix. **+$29/1000h whole-grid full + +$54/1000h whole-grid prefix**, both grids strongly positive with no per-category regression. pct_opt: 41.48% → 41.91% (full), 50.64% → 51.81% (prefix). Cumulative v39 → v41 = −$77 full / −$91 prefix. Three drills ran addressing the user's verbatim S44 closure direction. **Drill A (J-low single-pair DS-break, n=342,720)** answered the user's "should we break the pair to enable DS-bot?" question: **NO** (A3−A2 = −$10,304/1000h, catastrophic). The unambiguous opportunity: **A1−A2 = +$2,756/1000h** within-hand on the 47.8% of J-low pair hands where keeping pair-in-mid AND picking singletons that form DS-bot is achievable. This insight ships as Rule 10 v3. Per-pair-rank tipping: A5−A2 (pair-to-bot DS) flips positive at P=J (+$2,975/1000h) — Rule 11 candidate, deferred. **Drill B (J-low two_pair DS-break, n=262,080)** confirmed the same pattern with even larger margins: B3−B2 = −$9,030, B5−B2 = −$12,042, B7−B2 = −$23,165. Within-class B1−B2 = +$1,864 is a sister Rule 11+ candidate. The "two_pair is ML territory" verdict (S42 + S43, twice) holds for cross-class rules. **Drill C (S44 carryover validation)** showed DS one-gap-4 ≥ DS run-4 does NOT robustly generalize across categories — sign flips by category (high_only −$233, pair +$344, two_pair +$361, trips −$518). S44's +$376 (n=1,680) was likely inside noise.

> **🎯 IMMEDIATE NEXT ACTION (Session 46):**
>
>   (A) **Rule 11 candidate — J-pair pair-to-bot + DS.** Drill A's per-pair-rank breakdown showed A5−A2 = +$2,975/1000h for P=J specifically (vs −$300 to −$1,100 for P=2..9). For J-pair (max=J), pair-to-bot + DS-bot beats pair-mid + non-DS-bot by ~$3K within-hand. Implementing this requires a setting-builder that places both pair members in bot AND chooses 2 singletons to complete a DS pattern. Expected lift: P=J cell is 10% of J-low pair zone × 5.7% pair zone of grid × ~$3K within-hand × achievability fraction. Whole-grid: estimated +$10-20/1000h full. Worth a focused drill + grade.
>
>   (B) **Two_pair within-class suit-aware bot (B1−B2 = +$1,864/1000h).** Two_pair is "ML territory" cross-class but this within-class rule may be feasible. Requires a setting-builder for two_pair both-intact + DS that selects which pair joins mid (vs bot) and which singletons fill the bot to form DS. Higher complexity than Rule 10 v3 but larger pop coverage.
>
>   (C) **v41 ML retrain (feed v34_dt with v41 baseline residuals).** v34_dt was trained against v32 residuals. With v41 production fixing the J-low pair zone, the residual pattern has shifted. Capacity-only retrain at v41 baseline could ship +$15-30 (pattern: capacity retrains at v33/v34 shipped +$58 once before).
>
>   (D) **Carryover from Session 45 deferrals:**
>     - Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
>     - T-low high_only naive top=lo rule (~+$8 full-only)
>     - Round-3 within-trips features (S42 carryover)
>     - Learned A-vs-C decision tree for Rule 6 (S38-40 carryover)
>     - Trips_pair G3 oracle exploration (+$85 ceiling)
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NEW SHIP (Session 45):** v41_rule10_v3_ds replaces v40b as the production strategy of record. **+$29 full / +$54 prefix**. v40b retained for reference; v40 retained for human-memorization fork. Total project rule count remains **10** (Rule 10 evolved v40 → v40b → v41).

> **🔬 ARTIFACTS (Session 45):**
> 1. **`analysis/scripts/drill_J_low_pair_DS_break.py`** — within-hand pairwise A1..A6 (DEFINITIVE; n=342,720)
> 2. **`analysis/scripts/drill_J_low_two_pair_DS_break.py`** — within-hand pairwise B1..B8 (DEFINITIVE; n=262,080)
> 3. **`analysis/scripts/drill_DS_one_gap_vs_run4_other_cats.py`** — S44 generalization check (200K/cat sample)
> 4. **`analysis/scripts/strategy_v41_rule10_v3_ds.py`** — PRODUCTION
> 5. **`analysis/scripts/grade_v41_rule10_v3_ds.py`** — grader vs v40b
> 6. **`SESSION_45_RULE10_V3_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 45 NEW):**
> - **Pair structure dominates suit structure universally in J-low pair / two_pair zones.** Breaking a pair to enable DS-bot is catastrophic (−$10K to −$23K/1000h within-hand).
> - **Within-class suit-aware bot is the right Rule 10 extension.** S44's suit-dominance insight translates into a "DS-aware bot pick within pair-anchor preservation" rule that ships +$29 full / +$54 prefix.
> - **DS one-gap-4 ≥ DS run-4 (S44) does NOT generalize.** Sign flips by category. Don't extract small-sample within-hand findings as universal rules without replication on larger samples.
> - **Tie-break by preserving prior intent.** Where multiple valid choices exist, prefer the one closest to existing baseline (Rule 10 v3 picks lowest singleton among DS-achievable TOPs).
> - **Pair-to-bot + DS at P=J is a real Rule 11 candidate** (+$2,975/1000h) but requires a separate setting-builder.

> Updated: 2026-05-09 (Session 45)

---

## Headline state at end of Session 45

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v41_rule10_v3_ds** | **PRODUCTION strategy of record** (10 rules: v39 + Rule 10 v3 with suit-aware bot). +$29 full / +$54 prefix lift over v40b. Cumulative v39→v41: +$77 full / +$91 prefix. | `analysis/scripts/strategy_v41_rule10_v3_ds.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v40b_rule10_gated | Predecessor production (Session 43 ship). Retained for reference. | `analysis/scripts/strategy_v40b_rule10_gated.py` |
| v40_rule10 | Simple variant of Rule 10 (no gate, no suit-awareness). +$23 full / +$37 prefix vs v39. Retained for human-memorability fork. | `analysis/scripts/strategy_v40_rule10.py` |
| v39_rule9 | Predecessor production (Session 42 overnight ship) | `analysis/scripts/strategy_v39_rule9.py` |
| v38_rule8_qp | Predecessor production | `analysis/scripts/strategy_v38_rule8_qp.py` |
| v37_rule7_three_pair | Earlier production runtime | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips (sharper Rule 6 boundary). NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` |
| v33_rule6_trips | Earlier production runtime | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. Confirmed ML-only twice. | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
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
| v40_rule10 (+ Rule 10, simple variant) — sister candidate | $2,824 | 41.15% | −$209 |
| v40b_rule10_gated (+ Rule 10 gated) | $2,798 | 41.48% | −$235 |
| **v41_rule10_v3_ds (+ Rule 10 v3 suit-aware) — CURRENT PRODUCTION** | **$2,769** | **41.91%** | **−$264** |

---

## What Session 45 produced

**Code:**
- 3 new drill scripts (`drill_J_low_pair_DS_break.py`, `drill_J_low_two_pair_DS_break.py`, `drill_DS_one_gap_vs_run4_other_cats.py`)
- 1 new strategy (`strategy_v41_rule10_v3_ds.py`) — PRODUCTION
- 1 new grader (`grade_v41_rule10_v3_ds.py`)

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 45 entry; front-matter "Last updated"; Part 5 production-of-record references
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 078 added
- `SESSION_45_RULE10_V3_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 46)

```
Resume Session 46 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 45)
- DECISIONS_LOG.md (latest: Decision 078 — Rule 10 v3 ships as v41)
- SESSION_45_RULE10_V3_REPORT.md (standalone report on the suit-aware bot finding)
- SESSION_44_SUIT_CONNECTIVITY_REPORT.md (S44 within-hand pairwise drill)
- STRATEGY_GUIDE.md (Session 45 entry in Part 1; Part 5 + 6 updated)
- analysis/scripts/strategy_v41_rule10_v3_ds.py — current production
- analysis/scripts/drill_J_low_pair_DS_break.py — Drill A (definitive)
- analysis/scripts/drill_J_low_two_pair_DS_break.py — Drill B (definitive)

State (end of Session 45):
- Production: v41_rule10_v3_ds (10 rules: v39 + Rule 10 v3 suit-aware bot).
  +$29 full / +$54 prefix vs v40b.
- v40b retained as predecessor reference.
- v34_dt remains ML champion ($1,681 full / $889 prefix; 874K leaves).
- Drill A definitively answered "don't break the pair to enable DS-bot".
- Drill B confirmed same answer for two_pair with even larger margins.
- Drill C invalidated S44's "DS one-gap-4 ≥ DS run-4" generalization.
- Per-pair-rank A5 finding: pair-to-bot DS WINS at P=J by +$2,975/1000h
  (Rule 11 candidate; deferred — needs separate setting-builder).

USER-PRIORITY DIRECTION FOR SESSION 46 (recommended):

(A) Rule 11 candidate — J-pair pair-to-bot + DS. The P=J cell shows
    A5−A2 = +$2,975/1000h within-hand. Implement a setting-builder that
    places the pair in bot AND picks 2 singletons (from the remaining
    5) to complete a DS pattern. Trigger: cat=pair AND P=11 AND max=11.
    Drill within-hand vs v41 production pick. If positive, ship.

(B) Two_pair within-class suit-aware bot (B1−B2 = +$1,864/1000h).
    Setting-builder for two_pair both-intact + DS-bot. Higher complexity
    than Rule 11A but larger population (262K hands). Two_pair was
    declared "ML territory" cross-class — within-class may be exempt.

(C) v41 ML retrain. Capacity-only retrain of v34_dt against v41
    residuals. Pattern: previous capacity retrains shipped +$15-58.

Carryover from Session 45 (lower priority):
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
  WHEN PREFIX COVERAGE EXISTS. high_only category has ZERO prefix.
- Methodology rule (Session 45 NEW): pair structure dominates suit
  structure universally in J-low pair/two_pair (don't break pairs for DS).
- Methodology rule (Session 45 NEW): within-class suit-aware bot is a
  generalizable rule pattern (Rule 10 v3 ship; B1−B2 sister candidate).
- Methodology rule (Session 45 NEW): small-sample within-hand findings
  need replication at higher sample sizes before being elevated to "rules".
- Methodology rule (Session 44): cross-class regret averaging is
  confounded by hand-population differences. Always validate cross-class
  comparisons via within-hand pairwise.
- Methodology rule (Session 44): suit dominates connectivity at every
  level (J-low no-pair). No tipping point.
- Methodology rule (Session 43 NEW): weak-hand top inversion.
- Methodology rule (Session 43 NEW): high_only zero prefix coverage.
- Methodology rule (Session 43 NEW): high-card-to-bot-for-flush is
  a losing trade.
- Methodology rule (Session 42 NEW): a rule with prefix regression
  >2× the full-grid lift does NOT ship.
- Methodology rule (Session 42 overnight NEW): suit-aware "non-X-suit"
  insight is a generalizable rule family.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
