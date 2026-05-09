# Session 48 — Rule 12 Q-extension (deferred) + Rule 13 (three_pair all-intact + DS) ships as v44

_Generated: 2026-05-09_

## TL;DR

Session 48 ran two extensions of the suit-dominance family:

**1. Rule 12 max≤Q extension (Drill G + v43b) — DEFERRED.** Tested
extending Rule 12 from max≤J to max≤Q. Drill G: V_HH_BOT lift at max=Q
is +$1,283/1000h within fires; max=K marginal; max=A catastrophic
(−$3,744). Designed v43b (max≤Q, HH-only at Q). Grade: full +$14, but
prefix REGRESSES −$6/1000h with pct_opt drop 52.61% → 52.45%. Ship
gate passes by ratio (−$6/+$14 = 0.43x, not >2x), but the prefix
regression undermines confidence. **Deferred.**

**2. Rule 13 — three_pair all-intact + DS-bot (Drill H + v44) — SHIPS.**
Same suit-dominance lens applied to three_pair. Findings: V_MM_MID
(+$2,463 within fires) and V_HH_MID (+$2,227) both strongly positive.
**V_LL_MID is catastrophic** (−$4,117) — putting weakest pair in mid
is worse than v43's existing pick. Rule 13 = MM_mid first, HH_mid
second, **skip LL_mid-only cases** (avoid the trap).

**v44 production:**

| Grid | v43 | v44 | Δ |
|---|---:|---:|---:|
| Full (N=200) | $2,727 | **$2,717** | **−$11/1000h** |
| Prefix (N=1000) | $1,550 | **$1,522** | **−$29/1000h** |

pct_opt full: 42.20% → 42.34% (+0.14%). pct_opt prefix: 52.61% → 53.06%
(+0.45%). **three_pair regret $2,268 → $1,696 (−$572 within three_pair,
25% reduction). three_pair pct_opt 51.5% → 59.3% (+7.8%, the largest
single-category pct_opt jump from any rule ship).** Cumulative v39 → v44
= −$129 full / −$185 prefix.

## Drill G — two_pair max≥Q extension (50K samples per cell)

`analysis/scripts/drill_two_pair_DS_extension.py` extended Drill F to
max=Q, K, A two_pair cells. V_HH_BOT and V_LL_BOT lifts vs v43:

| Cell | n_pop | n_fires | V_HH_BOT lift | V_LL_BOT lift | B1 oracle |
|---|---:|---:|---:|---:|---:|
| max=Q | 50,000 | 22,887 (45.8%) | **+$1,283** | −$289 | +$1,553 |
| max=K | 50,000 | 23,209 (46.4%) | −$133 | −$928 | +$544 |
| max=A | 50,000 | 23,000 (46.0%) | **−$3,744** | −$1,938 | **−$1,470** |

At max=A, even the B1 oracle LOSES to v43's pick. Mechanism: at A-high,
putting the A on top is more valuable than the pair-bot DS Omaha play.
Top-tier wins ~45% vs random opp's high card; the bot upgrade can't
compensate.

## v43b grade results (deferred)

`analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py` extends Rule 12
to max≤Q (HH-only at Q, since LL regresses there). Same as Rule 12 but
with the trigger gate widened.

| Grid | v43 | v43b | Δ | pct_opt |
|---|---:|---:|---:|---:|
| Full | $2,727 | $2,714 | **+$14** | 42.20% → 42.24% (+0.04%) |
| Prefix | $1,550 | $1,557 | **−$6** | 52.61% → **52.45%** (−0.16%) |

The full lift is solid (+$14/1000h, comparable to v34_dt's +$34 ship
arc) but the prefix regression and pct_opt drop undermine reliability.

**Decision: DEFER v43b.** The S42 methodology gate (prefix regression
must not exceed 2× full lift) technically passes (−$6/+$14 = 0.43x, well
under 2x), but the qualitative regression on prefix (a category we've
historically been strict about) doesn't justify shipping. Files retained
as artifacts for possible future refinement.

## Drill H — three_pair within-class DS variants (full pop, n=114,400)

`analysis/scripts/drill_three_pair_DS_within_intact.py`. Three_pair has
3 pairs (HH, MM, LL) + 1 singleton. All-pairs-intact configurations:
mid = 1 pair, bot = 2 pairs, top = singleton (deterministic). 3 choices
for which pair to mid: HH_mid, MM_mid, LL_mid.

For DS bot: the 2 pairs in bot must share IDENTICAL suit sets (each pair
has 2 suits; for 2+2 pattern they must match). 50% of three_pair hands
have ≥1 DS-intact configuration.

| Variant | Lift vs v43 within fires (full) | Whole-grid full | Prefix lift |
|---|---:|---:|---:|
| **V_MM_MID** (HH+LL in bot) | **+$2,463** | **+$9.38** | **+$2,787** |
| V_HH_MID (MM+LL in bot) | +$2,227 | +$8.48 | +$1,838 |
| **V_LL_MID** (HH+MM in bot) | **−$4,117** | **−$15.68** | **−$6,542** |
| B1 oracle (ceiling) | +$988 | +$9.40 | +$217 |

**Surprising finding: V_LL_MID is catastrophic.** Putting LL pair in mid
is a weak Hold'em hand and the HH+MM bot DS upgrade can't compensate
for the mid-tier loss. This is the OPPOSITE of two_pair (where Drill F
showed HH-to-bot wins). Mechanism: at three_pair, the "bigger bot"
upgrade replaces a 2-pair bot with a higher-2-pair bot — small marginal
gain — while the mid-tier downgrade from MM→LL is much larger.

**V_MM_MID and V_HH_MID both win solidly.** They're nearly tied
(+$2,463 vs +$2,227); V_MM_MID has slight edge.

**Achievability distribution:**
- HH_mid only achievable: 30% of fires (use V_HH_MID, +$2,227)
- MM_mid only: 30% of fires (use V_MM_MID, +$2,463)
- LL_mid only: 30% of fires (TRAP — skip; -$4,117)
- All 3: 10% of fires (use V_MM_MID by tie-break)

## Rule 13 design

```
TRIGGER:
  cat == three_pair                                      AND
  (MM_mid_DS achievable OR HH_mid_DS achievable)
  (skip when ONLY LL_mid is achievable — V_LL_MID trap)

SETTING BUILDER (priority order):
  1. If MM_mid_DS achievable:
       MID = MM pair, BOT = HH+LL pairs, TOP = singleton
     (V_MM_MID, +$2,463 expected lift)
  2. Else if HH_mid_DS achievable:
       MID = HH pair, BOT = MM+LL pairs, TOP = singleton
     (V_HH_MID, +$2,227 expected lift)
  3. Else: fall through to v43 (skip LL_mid-only trap).
```

**Behavioral verification on 50K three_pair sample:**
- Rule 13 fires on 35.1% (matches Drill H's 50% × (1 − 30% LL-only) = 35%)
- 100% of fires correctly produce DS-bot
- 100% of fires correctly preserve all 3 pairs intact (mid_is_pair == True)
- 17.4% of picks differ from v43

## v44 grade results

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | three_pair $/1000h | three_pair pct_opt |
|---|---:|---:|---:|---:|
| v43 | $2,727 | 42.20% | $2,268 | 51.5% |
| **v44** | **$2,717** | **42.34%** | **$1,696** | **59.3%** |
| **Δ** | **−$11** | **+0.14%** | **−$572** | **+7.8%** |

**Prefix grid (N=1000):**

| Strategy | $/1000h | pct_opt |
|---|---:|---:|
| v43 | $1,550 | 52.61% |
| **v44** | **$1,522** | **53.06%** |
| **Δ** | **−$29** | **+0.45%** |

The within-category improvements are striking: three_pair regret drops
−25% (-$572 / $2,268), and three_pair pct_opt jumps +7.8% — the largest
single-category pct_opt jump from any rule ship in the project.

The whole-grid headline of +$11 full is muted because three_pair is only
1.9% of grid. But the within-category win is decisive.

## Cumulative arc (Session 43-48)

| Strategy | Full | Prefix | Cumulative since v39 |
|---|---:|---:|---:|
| v39 (Session 42 overnight) | $2,846 | $1,707 | baseline |
| v40b (S43) | $2,798 | $1,670 | -$48 / -$37 |
| v41 (S45) | $2,769 | $1,616 | -$77 / -$91 |
| v42 (S46) | $2,763 | $1,616 | -$83 / -$91 |
| v43 (S47) | $2,727 | $1,550 | -$118 / -$157 |
| **v44 (S48)** | **$2,717** | **$1,522** | **-$129 / -$185** |

The suit-dominance arc has now shipped 5 production rules across 6
sessions, all stemming from S44's within-hand pairwise methodology
breakthrough:
- Rule 10 v40b → suit-aware top inversion (J-low pair defensive)
- Rule 10 v3 (v41) → suit-aware bot WITHIN pair-mid
- Rule 11 (v42) → pair-to-bot DS at J-pair-J (single-cell)
- Rule 12 (v43) → both-intact + DS for J-low two_pair
- **Rule 13 (v44) → all-intact + DS for three_pair (MM/HH only)**

## Methodology lessons (Session 48)

1. **Within-class DS doesn't always favor "highest pairs in bot".** For
   two_pair (Drill F), HH-to-bot wins. For three_pair (Drill H), the
   HH+MM-to-bot variant (V_LL_MID) is catastrophic — putting LL in mid
   is a weak Hold'em hand. The mid-tier strength matters MORE for
   three_pair because three_pair already has a strong bot regardless.

2. **Skip-the-trap design pattern.** Rule 13 explicitly excludes
   LL_mid-only cases (the catastrophic 30% of fires). Don't try to
   "fix" the trap; just don't fire on it. Same pattern as Rule 12's
   max≤J gate (avoiding max=A where pair-bot loses).

3. **Within-category pct_opt jumps are a strong ship signal.** Three_pair
   pct_opt 51.5% → 59.3% (+7.8%) is the largest single-category jump
   from any rule ship. The whole-grid headline (+$11) is muted by
   category share but the within-category quality is decisive.

4. **Extension rules require careful prefix-grid checking.** Rule 12
   max≤Q extension (v43b) showed +$14 full but −$6 prefix; deferred
   despite passing the strict 2x ratio gate. Be conservative on
   extensions when the prefix signal is mixed.

5. **The suit-dominance arc has now shipped 5 rules.** v40b → v44 across
   6 sessions = -$129 full / -$185 prefix cumulative. This is now the
   project's largest multi-session arc by ship count, even with the
   v43b deferral.

## Files produced

**Drills (2):**
- `analysis/scripts/drill_two_pair_DS_extension.py` (Drill G)
- `analysis/scripts/drill_three_pair_DS_within_intact.py` (Drill H)

**Strategy + grader (production + deferred artifact):**
- `analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py` (DEFERRED — kept as artifact)
- `analysis/scripts/grade_v43b_rule12_extQ.py` (artifact)
- `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` (PRODUCTION)
- `analysis/scripts/grade_v44_rule13_three_pair.py`

**Documentation:**
- `SESSION_48_RULE13_THREE_PAIR_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 48 entry
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 081 added

## What's queued for Session 49+

- **Trips_pair within-class DS-bot.** trips_pair (171,600 hands, 2.86%
  of grid) — apply the same lens. Trip + pair structure has rich Omaha
  potential.
- **Quads_pair refinement.** Already has Rule 8; check if there's a
  within-class DS opportunity not captured.
- **Composite (cat=7) within-class.** Smallest category but the regret
  is highest ($4,445/1000h); there might be quick wins.
- **v44 ML retrain.** Capacity-only retrain of v34_dt against v44
  residuals. Pattern: previous capacity retrains shipped +$15-58.
- **Two_pair max≤Q (v43b refinement).** If we can find a sharper gate
  that picks up the +$14 full WITHOUT regressing prefix, ship it.
- **Carryover deferred items:**
  - Q5 J-high no-pair multi-feature deep dive
  - T-low high_only naive top=lo rule
  - Round-3 within-trips features
  - Learned A-vs-C decision tree for Rule 6
  - Trips_pair G3 oracle exploration
  - KK/AA single-suited Rule-4-bot residual

## Total project rule count: 13 (Rules 1-12 + Rule 13 = three_pair all-intact + DS, MM/HH only).

The S43-S48 suit-dominance arc has now shipped 5 production rules
(Rule 10 v40b/v3, Rule 11, Rule 12, Rule 13). This is the project's
largest multi-rule family from a single methodology breakthrough.
