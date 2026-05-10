# Session 50 — Rule 14 (A-high no-pair, A-on-top + DS/SS HIMID) ships as v45

_Generated: 2026-05-09_

## TL;DR — LARGEST SINGLE-RULE SHIP IN PROJECT HISTORY

User direction: scale into the high_only category (the largest unclaimed
territory at $833/1000h whole-grid regret contribution). Started with
A-high no-pair sub-population.

**v45 vs v44 = +$131/1000h whole-grid full.** Beats v33's Rule 6 ($113,
Session 37) which had held the record for 13 sessions. **All on a single
rule.** Prefix unchanged (high_only has zero prefix coverage — same
precedent as Rule 11).

| Grid | v44 → v45 | pct_opt | high_only $/1000h | high_only pct_opt |
|---|---:|---:|---:|---:|
| Full (N=200) | $2,717 → **$2,585** (−$131) | 42.34% → **43.05%** (+0.71%) | $4,082 → $3,439 (−$643, −16%) | 19.8% → **23.3%** (+3.5%) |
| Prefix (N=1000) | $1,522 → $1,522 (0) | 53.06% → 53.06% (0) | (no high_only in prefix) | (no high_only in prefix) |

Cumulative v39 → v45 = −$260 full / −$185 prefix.
Cumulative v14_combined → v45 = −$447 full / much larger.

## Drill K — A-high no-pair characterization (Phase 1, n=660,660)

`analysis/scripts/drill_A_high_nopair_characterization.py` — comprehensive
characterization of all 660,660 A-high no-pair hands (= 11% of grid).

**Headline findings:**
- Mean regret per hand: $3,752/1000h within A-high no-pair
- **Whole-grid contribution: $412.5/1000h** (single largest residual zone)
- v44 == oracle on only 22.2% of hands (vs 42% project-wide)

**v44 vs oracle pick distributions (where the leak is):**

| Aspect | v44 | Oracle | Gap |
|---|---:|---:|---|
| TOP = Ace | 100% | 93.13% | v44 over-Aces (rare K/Q/J/2 oracle picks) |
| BOT = DS | 59.27% | 47.99% | v44 OVER-DS by 11pp |
| BOT = SS | 24.97% | 35.00% | v44 UNDER-SS by 10pp |
| BOT = rainbow | 11.18% | 0.83% | **v44 picks rainbow 13× too often** |
| BOT = 3+1 | 4.30% | 14.11% | v44 UNDER-3+1 by 10pp |

The picture: v44 is *not actually* suit-aware here. It defaults to "highest
4 cards in bot" and the suit profile is whatever falls out — often rainbow.

**Best-in-class minus v44 (S46 lens):**

| Class | n_co | Lift vs v44 within fires | Whole-grid contribution |
|---|---:|---:|---:|
| **DS** | 601,524 | **+$1,937** | **+$194** |
| SS | 601,524 | +$1,377 | +$138 |
| 3+1 | 562,716 | −$1,233 | −$115 |
| rainbow | 323,400 | −$6,135 | −$330 |
| 4-flush | 207,900 | −$5,132 | −$178 |

DS-class oracle pick beats v44 by $1,937/1000h within fires on hands where
DS-bot is achievable. SS-class also strongly positive. Rainbow / 4-flush
oracle picks LOSE to v44 (because v44 already picks rainbow when it's bad,
and oracle would pick something different).

**Per-2nd-highest stratification:**

| 2nd-high | n | Regret/1000h | Oracle DS% | v44 DS% |
|---|---:|---:|---:|---:|
| K | 330,330 | $4,186 | 49.5% | 59.0% |
| Q | 180,180 | $3,576 | 47.5% | 59.3% |
| J | 90,090 | $3,091 | 45.7% | 59.8% |
| T | 40,040 | $2,926 | 44.5% | 60.4% |

The opportunity scales with 2nd-highest rank. K-2nd is the dominant zone
(50% of A-high pop) with $4,186/1000h regret.

## Drill L — A-on-top + bot heuristic sweep (Phase 2, 50K sample)

`analysis/scripts/drill_A_high_topA_bot_heuristic.py` — tested 7 deterministic
heuristics for "A on top + best DS/SS bot".

**Variant comparison (within-hand pairwise vs v44):**

| Variant | Lift within fires | Whole-grid full | Notes |
|---|---:|---:|---|
| **H2_DS_HIMID** (DS bot, mid keeps highest 2 non-A) | **+$1,016** | **+$6.56** | only winning DS heuristic |
| H1_DS_HIBOT (DS bot, highest 4 in bot) | −$847 | −$5.47 | LOSS |
| H3_DS_HIRUN (DS bot, best connectivity) | +$86 | +$0.55 | barely positive |
| H4_DS_LOMID | −$847 | −$5.47 | identical to HIBOT (4-card bot ⟹ same setting) |
| H1_SS_HIBOT (SS bot, highest 4) | −$5,479 | −$39.44 | catastrophic |
| H_BEST_DS oracle | +$1,970 | +$12.72 | upper bound |
| H_BEST_SS oracle | +$1,720 | +$12.38 | upper bound |
| **HYBRID HIMID** (DS-HIMID, SS-HIMID fallback) | **+$1,245** | **+$10.06** | best simple rule |
| HYBRID ORACLE | +$2,505 | +$20.26 | upper bound |

**Critical finding: HIMID, not HIBOT.** The right heuristic keeps the 2
highest non-A cards in MID (forming a strong Hold'em mid like K+Q),
while pushing the lower 4 cards into the bot. This is OPPOSITE the
intuitive "stack high cards in bot for kicker strength" idea.

Mechanism: the A-on-top + K+Q-in-mid combination is *huge* for Hold'em
top + mid scoring. Bot's Omaha play depends more on suit (DS) than
absolute kicker rank.

## Rule 14 design

```
TRIGGER:
  cat == high_only        AND
  max_rank == 14 (Ace)    AND
  DS-bot OR SS-bot achievable with A on top

SETTING BUILDER:
  TOP = the Ace (always).

  Try DS-bot first:
    Among the 15 A-on-top settings, find those with bot suit profile = DS.
    Pick the DS-setting whose MID has the highest rank-sum
    (= keeps the 2 strongest non-A cards in mid).

  Else try SS-bot:
    Same HIMID tie-break among A-on-top settings with SS bot.

  Else: fall through to v44 (rainbow / 3+1 / 4-flush bot — let v44 handle).

  MID = the 2 highest-rank non-A cards (subject to suit constraint).
  BOT = the remaining 4 non-A cards (forming DS or SS).
```

**Behavioral verification on 50K A-high no-pair sample:**
- Rule 14 fires on **93.6%** of A-high no-pair hands (vs 78% expected DS coverage — SS fallback adds 16%)
- **v45 differs from v44 on 72.2% of fires** (vs S49's 0% no-op disaster)
- 100% of fires correctly produce A-on-top
- 78% DS bot, 22% SS bot fallback, 0% other suit profile
- Sanity check passes — this is NOT a no-op.

## Grade results

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | high_only $/1000h | high_only pct_opt |
|---|---:|---:|---:|---:|
| v44 | $2,717 | 42.34% | $4,082 | 19.8% |
| **v45** | **$2,585** | **43.05%** | **$3,439** | **23.3%** |
| **Δ** | **−$131** | **+0.71%** | **−$643** (−16%) | **+3.5%** |

**Prefix grid (N=1000):**

| Strategy | $/1000h | pct_opt |
|---|---:|---:|
| v44 | $1,522 | 53.06% |
| v45 | $1,522 | 53.06% |
| Δ | **$0** | **0** |

Prefix unchanged — high_only has zero prefix coverage (S43 finding).
Rule 14 fires on 0 prefix hands → prefix score guaranteed unchanged.
Same precedent as Rule 11 (J-pair-J zero-prefix-coverage).

**Side metrics:**
- p90 regret: 0.785 → 0.745 (improved)
- max regret: 5.74 → 5.74 (unchanged, no scoop induction)

## Cumulative arc

| Strategy | Full $/1000h | Prefix $/1000h | Δ vs v39 |
|---|---:|---:|---:|
| v39 (Sept '25 baseline) | $2,846 | $1,707 | baseline |
| v40b (S43, Rule 10 gated) | $2,798 | $1,670 | −$48 / −$37 |
| v41 (S45, Rule 10 v3) | $2,769 | $1,616 | −$77 / −$91 |
| v42 (S46, Rule 11) | $2,763 | $1,616 | −$83 / −$91 |
| v43 (S47, Rule 12) | $2,727 | $1,550 | −$118 / −$157 |
| v44 (S48, Rule 13) | $2,717 | $1,522 | −$129 / −$185 |
| **v45 (S50, Rule 14)** | **$2,585** | **$1,522** | **−$260 / −$185** |

The S43-S50 arc has now shipped 6 production rules totaling −$260 full /
−$185 prefix. Rule 14 alone contributed −$131 full — more than the
combined S43-S48 arc.

**Single-rule whole-grid lift records (project history):**

| Rank | Rule | Session | Full lift |
|---|---|---|---:|
| 1 | **Rule 14 (A-high HIMID)** | **S50** | **+$131** |
| 2 | Rule 6 (pure trips, v33) | S37 | +$113 |
| 3 | Rule 10 (J-low pair, v40b) | S43 | +$48 |
| 4 | Rule 7 (three_pair, v37) | S41 | +$43 |
| 5 | Rule 12 (J-low two_pair, v43) | S47 | +$35 |

## Methodology lessons (Session 50)

1. **High_only is the project's biggest residual zone.** $412/1000h
   whole-grid contribution from A-high alone, $833/1000h from total
   high_only. The defensive arc (Rules 10-13) opened paired weak hands;
   the offensive arc on high_only opens unpaired strong hands.

2. **HIMID > HIBOT for A-high.** Counter to the obvious "high cards in
   bot for kicker strength" intuition. With A on top, the next-best 2
   cards (K+Q etc.) belong in MID for strong Hold'em scoring; the lower
   4 cards form the bot's Omaha play (where suit matters more than rank).

3. **The S46 "best-in-class minus production pick" lens is the project's
   most productive discovery method.** Drill K's per-class table directly
   identified DS and SS as the two opportunity zones; rainbow/3+1/4-flush
   oracle picks LOSE vs v44 (don't try to ship those).

4. **S49's sanity-check methodology was pivotal.** v45 differs from v44
   on 72.2% of fires (vs S49's no-op 0%). Always verify pick-difference
   rate BEFORE grading. This caught the S49 trips_pair no-op early; this
   session it confirmed Rule 14 was real.

5. **Largest residuals come from previously unrepresented categories.**
   The S43-S48 arc covered the defensive zone (max ≤ J pair/two_pair/three_pair).
   high_only had no rules at all — and yielded the project's biggest single
   ship. **Where else has no rule coverage?** trips_pair has only Rule 3
   (a baseline Rule 14-equivalent search would be the next big drill).

## Files produced

**Drills (2):**
- `analysis/scripts/drill_A_high_nopair_characterization.py` (Drill K — Phase 1 characterization)
- `analysis/scripts/drill_A_high_topA_bot_heuristic.py` (Drill L — Phase 2 heuristic sweep)

**Strategy + grader:**
- `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` (PRODUCTION)
- `analysis/scripts/grade_v45_rule14_Ahigh.py`

**Documentation:**
- `SESSION_50_RULE14_AHIGH_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 50 entry; front-matter "Last updated"
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 083 added

## Why Rule 14 ships

- **Largest full-grid lift in project history (+$131/1000h)**
- pct_opt full: +0.71% (largest single-ship pct_opt jump since v33)
- pct_opt prefix: unchanged (no risk on prefix — fires on 0 prefix hands)
- high_only category: −$643/1000h (16% reduction); high_only pct_opt +3.5%
- p90 regret improved (0.785 → 0.745)
- max regret unchanged (no scoop induction)
- No regression on any other category

## What's queued for Session 51+

The high_only territory is huge. A-high (this session) was just the first
sub-pop. Remaining:

- **K-high no-pair** (~290K hands, ~5% of grid, $4,500+/1000h regret)
- **Q-high no-pair** (~150K hands, ~2.5% of grid)
- **J-high no-pair** (already partially covered by Rule 10's defensive zone)
- **T-low no-pair** (defensive territory)

Each likely needs its own drill + heuristic. Mechanism may differ per
sub-pop (HIMID may not be best for K-high if K can sometimes win top tier).

Other carryover:
- **Trips_pair Rule 14 v2 (adaptive heuristic)** — still has +$1,992
  oracle gap from S49 Drill I
- **Composite (cat=7) within-class** — small population, high regret
- **v45 ML retrain** — capacity-only retrain of v34_dt against v45 residuals
- **Two_pair max≤Q refinement** — v43b had +$14 full / -$6 prefix

## Total project rule count: 14 (Rules 1-13 + Rule 14 = A-high no-pair + DS/SS HIMID).

The **S43-S50 arc** now has 6 rules totaling −$260 full / −$185 prefix,
making it the project's largest multi-rule family by both ship count and
total lift. The methodology breakthroughs (S44 within-hand pairwise + S46
best-in-class minus production + S49 sanity-check) compose to enable
finding offensive ships outside the original defensive zone.
