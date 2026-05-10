# Session 52 — Rule 16 (Q-high no-pair, Q-on-top + DS/SS HIMID) ships as v47

_Generated: 2026-05-09_

## TL;DR

Continued the high_only attack from Sessions 50-51. Applied the same Drill K + Drill L methodology to Q-high no-pair (the 3rd-largest high_only sub-population).

**v47 vs v46 = +$19/1000h whole-grid full / $0 prefix.**

| Grid | v46 → v47 | pct_opt | high_only $/1000h |
|---|---:|---:|---:|
| Full (N=200) | $2,534 → **$2,515** (−$19) | 43.24% → **43.30%** (+0.06%) | $3,187 → $3,096 (−$91, −2.9%) |
| Prefix (N=1000) | $1,522 → $1,522 ($0) | 53.06% (unchanged) | (no high_only in prefix) |

Cumulative v39 → v47 = **−$330 full / −$185 prefix** (8 production rules across S43-S52).
Cumulative v14_combined → v47 = **−$518 full**.

## Drill N — Q-high no-pair characterization (n=150,150)

`analysis/scripts/drill_Q_high_nopair_characterization.py`. Q-high
contributes $112/1000h whole-grid regret (smaller than A-high's $412
or K-high's $226 because Q-high pop is only 2.5% of grid).

**Critical finding: Q-on-top is borderline.** Oracle picks Q on top only
**49.37%** of the time (vs A-on-top 93%, K-on-top 66%). The other 51%
includes:
- J on top: 10.40%
- 2 on top (defensive): 15.69%
- T on top: 4.15%
- 3 on top: 7.79%

**v46 vs oracle pick distributions:**

| Aspect | v46 | Oracle | Notes |
|---|---:|---:|---|
| TOP = Q | 100% | 49.37% | v46 over-Q's; oracle splits 50/50 |
| TOP = 2 | 0% | 15.69% | significant defensive top inversion zone |
| BOT = DS | 59.8% | 58.9% | better aligned than A/K-high |
| BOT = rainbow | 11.1% | 0.31% | still 36× too often |
| BOT = 3+1 | 4.2% | 11.6% | UNDER-3+1 |

**Best-in-class minus v46 (S46 lens):**

| Class | n_co | Lift vs v46 within fires | Whole-grid contribution |
|---|---:|---:|---:|
| **DS** | 136,710 | **+$3,604** | **+$82** |
| SS | 136,710 | +$2,196 | +$50 |
| **3+1** | 127,890 | **+$502** | **+$11** ← positive for first time |
| rainbow | 73,500 | −$4,112 | −$50 |
| 4-flush | 47,250 | −$1,872 | −$15 |

3+1 turns positive at Q-high for the first time. A-high and K-high had negative 3+1 lift.

## Rule 16 design (parallel to Rules 14/15)

```
TRIGGER:
  cat == high_only           AND
  max_rank == 12 (Queen)     AND
  DS-bot OR SS-bot achievable with Q on top

SETTING BUILDER:
  TOP = the Queen (always — Rule 16 v1 doesn't address non-Q top picks).
  Try DS-bot first (HIMID — mid keeps highest 2 non-Q cards).
  Else try SS-bot (HIMID).
  Else fall through to v46.
```

**Behavioral verification on 50K Q-high sample:**
- Rule 16 fires on 97.2% of Q-high hands
- v47 differs from v46 on 58.5% of fires (lower than A/K-high but substantial)
- 100% Q-on-top, 80% DS bot, 20% SS bot fallback

## Grade results

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | high_only $/1000h | high_only pct_opt |
|---|---:|---:|---:|---:|
| v46 | $2,534 | 43.24% | $3,187 | 24.2% |
| **v47** | **$2,515** | **43.30%** | **$3,096** | **24.5%** |
| **Δ** | **−$19** | **+0.06%** | **−$91** (−2.9%) | **+0.3%** |

**Prefix grid:** $1,522 → $1,522 ($0 change, expected).

p90 regret: 0.730 → 0.725 (slight improvement). Max regret unchanged.

## Three-session high_only sub-arc (S50-S52)

| Session | Ship | Sub-pop | Pop % | Top oracle % | Δ Full |
|---|---|---|---:|---:|---:|
| S50 | v45 (Rule 14) | A-high | 11% | 93% | −$131 |
| S51 | v46 (Rule 15) | K-high | 5.5% | 66% | −$51 |
| S52 | **v47 (Rule 16)** | Q-high | 2.5% | 49% | **−$19** |
| **Combined** | **+3 rules** | A+K+Q-high | 19% of grid | — | **−$201** |

## Diminishing returns analysis

The pattern is clear:

| Sub-pop | Pop | $/1% pop | Top-oracle % | Per-fire DS lift |
|---|---:|---:|---:|---:|
| A-high | 11% | $11.9 | 93% | +$1,937 |
| K-high | 5.5% | $9.3 | 66% | +$2,999 |
| Q-high | 2.5% | $7.6 | 49% | +$3,604 |

- Per-fire DS lift INCREASES (the lower the top-card, the more "wrong" v44/v45/v46 was)
- But pop size DECREASES (smaller absolute opportunity)
- Top-oracle fraction DECREASES (higher mismatch on top-card)

Net: each successive sub-pop ships less whole-grid lift. J-high would be even smaller (~1.3% pop, oracle J-on-top probably ~30%); estimated +$8-12 whole-grid.

## Methodology lessons (Session 52)

1. **The high_only sub-arc has diminishing returns.** A-high, K-high, Q-high all use the same playbook with shrinking absolute lifts. J-high would yield ~$10/1000h; below that, the lift wouldn't justify the doc/commit overhead.

2. **3+1 transitions from negative to positive** at Q-high. As top-card oracle fraction drops, oracle considers more bot suit profiles. Future Rule v2's might add 3+1 fallback.

3. **The simple HIMID heuristic is a robust pattern across A/K/Q-high.** Same code structure with only the rank constant changing.

## Files produced

**Drills (1):**
- `analysis/scripts/drill_Q_high_nopair_characterization.py` (Drill N)

**Strategy + grader:**
- `analysis/scripts/strategy_v47_rule16_Qhigh_DS.py` (PRODUCTION)
- `analysis/scripts/grade_v47_rule16_Qhigh.py`

**Documentation:**
- `SESSION_52_RULE16_QHIGH_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 52 entry
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 085 added

## Why Rule 16 ships

- Both grids non-regressive (+$19 full / $0 prefix)
- pct_opt full: +0.06%; high_only sub-category +0.3%
- Within-category high_only regret: −2.9%
- p90 regret slight improvement (0.730 → 0.725)
- Max regret unchanged
- Mechanism: parallel to Rules 14/15

## What's queued for Session 53+

The high_only single-pop arc is hitting diminishing returns. Better targets:

- **Rule 14 v2 / Rule 15 v2 / Rule 16 v2** — address non-default top picks (the 7%/34%/51% of A/K/Q-high where oracle prefers a different top card). These could each add +$10-30/1000h.
- **Trips_pair Rule 14 v2 (adaptive heuristic)** — known +$1,992 oracle gap from S49.
- **v47 ML retrain** — capacity-only retrain of v34_dt against v47 residuals. With 3 high_only ships in 3 sessions, the ML residual pattern has shifted significantly. Pattern: previous capacity retrains shipped +$15-58.
- **J-high no-pair** — would ship ~$8-12 (smaller); skip in favor of larger targets.
- **Composite (cat=7) within-class** — small population, possible quick wins.

## Total project rule count: 16.
