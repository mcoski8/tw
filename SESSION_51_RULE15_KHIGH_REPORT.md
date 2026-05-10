# Session 51 — Rule 15 (K-high no-pair, K-on-top + DS/SS HIMID) ships as v46

_Generated: 2026-05-09_

## TL;DR — 3rd-LARGEST SINGLE-RULE LIFT IN PROJECT HISTORY

Continued the high_only attack from Session 50 — applied the same Drill K
+ Drill L methodology to K-high no-pair (the 2nd-largest residual zone
after A-high). Rule 15 ships as v46.

**v46 vs v45 = +$51/1000h whole-grid full / $0 prefix.**

| Grid | v45 → v46 | pct_opt | high_only $/1000h |
|---|---:|---:|---:|
| Full (N=200) | $2,585 → **$2,534** (−$51) | 43.05% → **43.24%** (+0.19%) | $3,439 → $3,187 (−$252, −7.3%) |
| Prefix (N=1000) | $1,522 → $1,522 ($0) | 53.06% (unchanged) | (no high_only in prefix) |

Cumulative v39 → v46 = **−$311 full / −$185 prefix** (7 production rules
across S43-S51).

**Updated single-rule lift records:**

| Rank | Rule | Session | Full lift |
|---|---|---|---:|
| 1 | Rule 14 (A-high) | S50 | +$131 |
| 2 | Rule 6 (pure trips, v33) | S37 | +$113 |
| 3 | **Rule 15 (K-high)** | **S51** | **+$51** |
| 4 | Rule 10 (J-low pair, v40b) | S43 | +$48 |
| 5 | Rule 7 (three_pair, v37) | S41 | +$43 |

## Drill M — K-high no-pair characterization (Phase 1, n=330,330)

`analysis/scripts/drill_K_high_nopair_characterization.py` — same
methodology as Drill K (A-high) applied to K-high (5.5% of grid).

**Headline:**
- Mean regret: $4,114/1000h within K-high → **$226/1000h whole-grid
  contribution** (2nd-largest residual after A-high's $412)
- v45 == oracle on only 18.6% of K-high hands

**Critical difference vs A-high:**

| Aspect | v45 | Oracle | Notes |
|---|---:|---:|---|
| TOP = K | 100% | **66.23%** | Oracle keeps K elsewhere 34% of the time! |
| TOP = Q | 0% | 12.40% | v45 misses the Q-on-top sub-zone |
| TOP = J | 0% | 4.88% | also missed |
| TOP = 2 (defensive) | 0% | 6.69% | weak-hand top inversion territory |
| BOT = DS | 59.5% | 55.0% | similar to A-high |
| BOT = rainbow | 11.2% | 0.47% | **24× too often** (vs A-high's 13×) |
| BOT = 3+1 | 4.2% | 12.3% | UNDER-3+1 |

K-on-top is borderline (K loses to A but wins vs Q-or-lower); oracle
sometimes prefers Q-on-top + K-in-bot for a stronger 2-pair Omaha.

**Best-in-class minus v45 (S46 lens):**

| Class | n_co | Lift vs v45 within fires | Whole-grid contribution |
|---|---:|---:|---:|
| **DS** | 300,762 | **+$2,999** | **+$150** |
| SS | 300,762 | +$1,790 | +$90 |
| 3+1 | 281,358 | −$70 | −$3 |
| rainbow | 161,700 | −$4,838 | −$130 |
| 4-flush | 103,950 | −$2,765 | −$48 |

K-high DS lens shows even larger per-fire lift than A-high (+$2,999 vs
A-high's +$1,937). The whole-grid potential is +$150 from DS alone.

**Per-2nd-highest stratification:**

| 2nd-high | n | Regret/1000h | Oracle K-on-top % | Oracle DS% |
|---|---:|---:|---:|---:|
| Q | 180,180 | $4,408 | 63.9% | 55.8% |
| J | 90,090 | $3,803 | 70.7% | 54.3% |
| T | 40,040 | $3,689 | 68.8% | 53.8% |
| 9 | 15,015 | $3,602 | 65.6% | 53.2% |

K-Q-high is the dominant zone (55% of K-high pop) with the highest
regret. Oracle picks K-on-top only 64% there — meaning Q sometimes wins
the top tier honor.

## Rule 15 design

```
TRIGGER:
  cat == high_only           AND
  max_rank == 13 (King)      AND
  DS-bot OR SS-bot achievable with K on top

SETTING BUILDER (parallel to Rule 14):
  TOP = the King (always — Rule 15 v1 doesn't address Q-on-top sub-zone).
  Try DS-bot first (HIMID — mid keeps highest 2 non-K cards).
  Else try SS-bot (HIMID).
  Else fall through to v45.
```

**Behavioral verification on 50K K-high sample:**
- Rule 15 fires on **95.8%** of K-high hands
- **v46 differs from v45 on 65.6% of fires** (similar to Rule 14's 72.2%)
- 100% K-on-top, 79% DS bot, 21% SS bot fallback

**Limitations (known gaps for Rule 15 v2):**
- Doesn't address the 34% of hands where oracle prefers non-K on top
  (Q-on-top + K-in-bot scenarios)
- Doesn't address weak-hand top inversion (2-on-top defensive picks at
  3.16% of K-high oracle picks)

These are queued for a Rule 15 v2 (or Rule 16) — would require a
secondary trigger or branching logic.

## Grade results

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | high_only $/1000h | high_only pct_opt |
|---|---:|---:|---:|---:|
| v45 | $2,585 | 43.05% | $3,439 | 23.3% |
| **v46** | **$2,534** | **43.24%** | **$3,187** | **24.2%** |
| **Δ** | **−$51** | **+0.19%** | **−$252** (−7.3%) | **+0.9%** |

**Prefix grid (N=1000):**

| Strategy | $/1000h | pct_opt |
|---|---:|---:|
| v45 | $1,522 | 53.06% |
| v46 | $1,522 | 53.06% |
| Δ | **$0** | 0 |

Prefix unchanged (high_only zero prefix coverage — same precedent as v45).

p90 regret IMPROVED: 0.745 → 0.730 (consistent positive distributional shift).
Max regret unchanged at $5.74.

## Cumulative arc

| Strategy | Full $/1000h | Prefix $/1000h | Δ vs v39 |
|---|---:|---:|---:|
| v39 | $2,846 | $1,707 | baseline |
| v40b (S43) | $2,798 | $1,670 | −$48 / −$37 |
| v41 (S45) | $2,769 | $1,616 | −$77 / −$91 |
| v42 (S46) | $2,763 | $1,616 | −$83 / −$91 |
| v43 (S47) | $2,727 | $1,550 | −$118 / −$157 |
| v44 (S48) | $2,717 | $1,522 | −$129 / −$185 |
| v45 (S50) | $2,585 | $1,522 | −$260 / −$185 |
| **v46 (S51)** | **$2,534** | **$1,522** | **−$311 / −$185** |

The S43-S51 arc has now shipped 7 production rules totaling −$311 full /
−$185 prefix. The high_only sub-arc (S50-S51, Rules 14-15) alone
contributed −$182 full / $0 prefix.

## Methodology lessons (Session 51)

1. **The Drill K + Drill L playbook generalizes.** Same methodology that
   produced Rule 14 (A-high) produced Rule 15 (K-high) with similar
   structure: characterization drill → "best-in-class minus production"
   identifies DS/SS as targets → HIMID heuristic ships.

2. **K-high has known coverage gaps.** Oracle picks non-K on top 34% of
   the time (vs A-high's 7%). Rule 15 v1 doesn't address those — leaves
   meaningful residual on the table for a future Rule 15 v2.

3. **Per-fire lift can exceed A-high's** (best-in-DS K-high = +$2,999 vs
   A-high +$1,937) but whole-grid lift is smaller because population is
   smaller (5.5% vs 11%) and rule fires on smaller zone.

4. **The S43-S51 arc continues to compound.** 7 production rules, all
   from the same methodology family (within-hand pairwise + best-in-class
   lens). Average ship: −$44/1000h per rule.

## Files produced

**Drills (1):**
- `analysis/scripts/drill_K_high_nopair_characterization.py` (Drill M)

**Strategy + grader:**
- `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` (PRODUCTION)
- `analysis/scripts/grade_v46_rule15_Khigh.py`

**Documentation:**
- `SESSION_51_RULE15_KHIGH_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 51 entry; front-matter
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 084 added

## Why Rule 15 ships

- 3rd-largest single-rule lift in project history (+$51/1000h)
- pct_opt full: +0.19%; high_only sub-category +0.9%
- Within-category high_only regret: −7.3%
- p90 regret IMPROVED (0.745 → 0.730)
- Max regret unchanged
- Prefix unchanged (zero high_only prefix coverage)
- Mechanism interpretable + parallel to Rule 14

## What's queued for Session 52+

- **Q-high no-pair drill** — same playbook (~150K hands, ~2.5% of grid).
  Q is borderline for top tier (loses to A or K, ~30% top win rate).
  May need different heuristic.
- **Rule 14 v2 / Rule 15 v2: address non-A/non-K top picks.** Both rules
  have known gaps where oracle prefers a different card on top. Refining
  these may yield small additional ships.
- **Trips_pair Rule 14 v2 (adaptive heuristic)** — still has +$1,992
  oracle gap from S49.
- **v46 ML retrain** — capacity-only retrain of v34_dt against v46 residuals.
- **Carryover deferred items:**
  - Composite (cat=7) within-class
  - T-low high_only naive top=lo rule
  - Round-3 within-trips features
  - Learned A-vs-C decision tree for Rule 6
  - KK/AA single-suited Rule-4-bot residual

## Total project rule count: 15.
