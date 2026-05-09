# Session 45 — Rule 10 v3 ships (suit-aware bot) + drills A/B/C synthesis

_Generated: 2026-05-09_

## TL;DR

Session 44 produced a definitive priority hierarchy for J-low NO-PAIR
bot construction (suit dominates connectivity universally). Session 45
extended the investigation to **paired** weak hands per the user's verbatim
direction: does the suit-dominance pattern justify breaking the pair to
enable a DS bot?

Three drills ran, all using S44's within-hand pairwise methodology:

- **Drill A — J-low single-pair DS-break.** Catastrophic loss for pair-break
  (A3−A2 = −$10,304/1000h). Pair-anchor dominates suit. **BUT** keeping
  pair-in-mid AND choosing singletons that form a DS bot is +$2,756/1000h
  within-hand vs the best non-DS pair-mid pick.
- **Drill B — J-low two_pair DS-break.** Same answer, even larger margins.
  Splitting either pair for DS loses by −$9K to −$23K/1000h. Suit-aware
  bot WITHIN both-pairs-intact is +$1,864/1000h within-hand.
- **Drill C — DS one-gap-4 vs DS run-4 across categories.** S44's
  +$376/1000h finding does NOT robustly generalize. Sign flips by
  category (high_only −$233, pair +$344, two_pair +$361, trips −$518).
  S44's result was likely inside noise on its sample (n=1,680).

Drill A's A1−A2 finding led directly to **Rule 10 v3** — same trigger and
gate as v40b, but pick the singleton-to-drop-as-TOP that yields a DS bot
when achievable. Tie-break by lowest singleton (preserves v40b's weak-hand
top-inversion principle).

**Production strategy of record advances v40b → v41:**

| Grid | v40b | v41 | Δ | pct_opt |
|---|---:|---:|---:|---:|
| Full (N=200) | $2,798 | **$2,769** | **−$29/1000h** | 41.48% → 41.91% |
| Prefix (N=1000) | $1,670 | **$1,616** | **−$54/1000h** | 50.64% → 51.81% |

Cumulative v39 → v41 = +$77 full / +$91 prefix. Both grids ship clean.
Prefix lift > full lift is consistent with J-low pair being heavily
represented in the prefix population.

## What was tested

User's verbatim direction (Session 45 resume prompt):

> Now that we have a definitive answer for defensive J-high no-pair hands,
> we need to compare that to J-high hands with a pair and see how to play
> these. Do we favor the pair in the middle still? What about if it breaks
> double-suited on bottom? Does that mean DS on bottom even at the cost of
> breaking a pair is our best option?

Three drills mapped to: (A) J-low single-pair, (B) J-low two_pair, (C)
DS one-gap-4 vs DS run-4 generalization carryover.

## Drill A — J-low single-pair DS-break (definitive)

`analysis/scripts/drill_J_low_pair_DS_break.py` — within-hand pairwise on
all 342,720 J-low single-pair hands. Six classes (pair_state × bot_suit):

| Class | Description | Achievability |
|---|---|---:|
| A1 | pair-mid + DS-bot | 47.8% |
| A2 | pair-mid + non-DS-bot | 100.0% |
| A3 | pair-split + DS-bot | 91.9% |
| A4 | pair-split + non-DS-bot | 100.0% |
| A5 | pair-bot + DS-bot | 55.1% |
| A6 | pair-bot + non-DS-bot | 100.0% |

### Headline pairwise lift (full grid, n=342,720):

| Comparison | Lift ($/1000h) | Verdict |
|---|---:|---|
| **A3 − A2** (DS via pair-break vs non-DS pair-anchor) | **−$10,304** | catastrophic LOSS |
| **A5 − A2** (DS via pair-to-bot vs non-DS pair-anchor) | **+$8.9** | basically TIED |
| **A1 − A2** (DS premium WITHIN pair-mid) | **+$2,756** | **DS-aware bot wins** |
| A4 − A2 (pair-split non-DS vs pair-mid non-DS) | −$11,878 | pair-anchor cost |
| A6 − A2 (pair-bot non-DS vs pair-mid non-DS) | −$2,294 | pair-bot loses without DS |
| A1 vs A2 by P-rank | +$2,756 average | always positive |

### Per-pair-rank tipping (A5 − A2):

P=2: −$312, P=3: −$580, P=4: −$206, P=5: +$430, P=6: −$171, P=7: −$836,
P=8: −$1,131, P=9: −$710, P=T: +$630, **P=J: +$2,975 (clear win)**

Pair-to-bot DS wins for P=J specifically. Possible Rule 11 candidate
(deferred — exploring it requires a separate setting-builder for
pair-to-bot + DS).

### Translation

**The user's question answered: NO, do NOT break the pair to enable a
DS bot.** Pair-anchor dominates suit by ~$10K/1000h.

But there is unambiguous juice in **suit-aware bot construction WHILE
keeping pair-in-mid**: +$2,756/1000h on the 47.8% of J-low pair hands
where DS is achievable without breaking the pair. This translates into
the Rule 10 v3 design.

## Drill B — J-low two_pair DS-break (confirms drill A)

`analysis/scripts/drill_J_low_two_pair_DS_break.py` — within-hand pairwise
on all 262,080 J-low two_pair hands. Eight classes (pair_state × bot_suit).

### Headline pairwise lift (full grid, n=262,080):

| Comparison | Lift ($/1000h) | Verdict |
|---|---:|---|
| B3 − B2 (split-LL for DS) | **−$9,030** | catastrophic |
| B5 − B2 (split-HH for DS) | **−$12,042** | catastrophic |
| B7 − B2 (both-split for DS) | **−$23,165** | catastrophic |
| **B1 − B2** (DS premium WITHIN both-intact) | **+$1,864** | **suit-aware wins** |

Same structural answer as Drill A. **Pair structure dominates suit
universally** in the J-low pair / two_pair zones. The only juice from
suit-dominance is within the pairs-intact configuration.

The S42 + S43 verdict that "two_pair is ML territory" is reaffirmed for
cross-class structural rules. The within-class B1−B2 = +$1,864/1000h is
a Rule 11+ candidate but requires careful setting-builder design (which
pair stays intact in mid vs bot, which singletons fill bot for DS) and
two_pair was already declared ML territory twice — not a rush.

## Drill C — DS one-gap-4 vs DS run-4 (S44 finding does NOT generalize)

`analysis/scripts/drill_DS_one_gap_vs_run4_other_cats.py` — within-hand
pairwise across all 7 hand categories with 200K-per-category sample.

### Per-category lift (full grid, $/1000h):

| Category | n_co | EV(one-gap-4) − EV(run-4) |
|---|---:|---:|
| high_only | 5,237 | **−$233** (run-4 wins) |
| pair | 3,056 | **+$344** (one-gap-4 wins) |
| two_pair | 1,181 | +$361 |
| trips | 1,024 | **−$518** (run-4 wins) |

### Per-stratum (high_only by max_rank):

max≤J: −$118 (vs S44's +$376), max≤Q: −$158, max≤K: −$235, max=A: −$368.

**S44's finding does not robustly replicate.** With 626 J-low high_only
co-achievable hands in this drill (vs S44's 1,680), the lift inverted
direction. Standard error on small samples is large enough that
S44's +$376 was likely inside the noise band.

The sign FLIPS between categories — confirming this isn't a universal
structural feature. Different categories have different bot-tier roles
(no-pair = pure Omaha gut-shot value vs pair = Omaha + 2-pair anchor),
which makes the connectivity premium category-dependent.

## Rule 10 v3 — design + ship

### Design

`analysis/scripts/strategy_v41_rule10_v3_ds.py`. Same trigger + gate as
v40b (cat=pair, max≤J, P≤6 OR P==max). The **change**: suit-aware bot
construction.

```
Algorithm:
  1. Identify the 5 non-pair singletons (sorted desc by rank).
  2. For each candidate TOP (each singleton in turn):
       - Compute the suit pattern of the remaining 4 (would-be bot).
       - If pattern == [2, 2] → DS achievable.
  3. If any DS-achievable TOP exists:
       Tie-break by LOWEST singleton (preserves v40b's top-inversion intent).
  4. Else: fall back to v40b's TOP = lowest singleton.
  5. MID = the pair (always); BOT = the remaining 4 singletons.
```

This is consistent with the **weak-hand top inversion principle** from
S43: dump a low singleton on top to free the higher singletons for bot.
v3 only deviates when a non-lowest TOP enables a DS bot.

### Behavioral verification

On a 50K J-low gated-pair sample:
- v40b picks DS bot on **15.7%** of hands (random hits, suit-blind)
- v41 picks DS bot on **47.4%** of hands (matches A1 achievability ≈ 47.8%)
- Picks differ on **31.8%** of hands

### Grader results (head-to-head vs v40b)

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | pair $/1000h |
|---|---:|---:|---:|
| v40b | $2,798 | 41.48% | $1,905 |
| **v41** | **$2,769** | **41.91%** | **$1,843** |
| **Δ** | **−$29** | **+0.43%** | **−$62** |

**Prefix grid (N=1000):**

| Strategy | $/1000h | pct_opt | pair $/1000h |
|---|---:|---:|---:|
| v40b | $1,670 | 50.64% | $1,143 |
| **v41** | **$1,616** | **51.81%** | **$1,019** |
| **Δ** | **−$54** | **+1.17%** | **−$124** |

Both grids strongly positive. Prefix > full because J-low pair is
heavily represented in prefix (~10% of prefix is J-pair=2 cells, where
the rule fires hardest).

### Cumulative arc

| Strategy | Full $/1000h | Prefix $/1000h | Δ vs prior |
|---|---:|---:|---:|
| v39_rule9 | $2,846 | $1,707 | baseline |
| v40b_rule10_gated | $2,798 | $1,670 | −$48 / −$37 |
| **v41_rule10_v3_ds** | **$2,769** | **$1,616** | **−$29 / −$54** |
| **v39 → v41 cumulative** | | | **−$77 / −$91** |

## Methodology lessons (Session 45 NEW)

1. **Pair structure dominates suit structure universally in J-low pair /
   two_pair zones.** Breaking a pair to enable DS-bot is catastrophic
   (−$10K to −$23K/1000h). The S44 within-hand pairwise methodology
   correctly identified the within-class DS premium without misleading
   the cross-class question.

2. **Within-class suit-aware bot is the right Rule 10 extension.** The
   structural insight from S44 (suit dominates connectivity) translates
   into a "DS-aware bot pick within pair-anchor preservation" rule that
   ships +$29 full / +$54 prefix.

3. **DS one-gap-4 ≥ DS run-4 (S44 finding) does NOT generalize.** The
   sign flips by category. This is category-specific noise + small
   structural effects, not a universal feature. Don't extract it as a
   universal rule.

4. **Tie-break by preserving prior intent.** Rule 10 v3 picks the lowest
   singleton among DS-achievable TOPs to preserve v40b's weak-hand
   top-inversion intent. Where multiple valid choices exist, prefer the
   one closest to the existing baseline.

5. **Pair-to-bot + DS at P=J is a real signal (+$2,975/1000h).** Not
   shipped this session — would require a separate setting-builder for
   pair-to-bot + DS. Queued as Rule 11 candidate for Session 46+.

## Files produced

**Drills (3):**
- `analysis/scripts/drill_J_low_pair_DS_break.py`
- `analysis/scripts/drill_J_low_two_pair_DS_break.py`
- `analysis/scripts/drill_DS_one_gap_vs_run4_other_cats.py`

**Strategy + grader:**
- `analysis/scripts/strategy_v41_rule10_v3_ds.py` (PRODUCTION)
- `analysis/scripts/grade_v41_rule10_v3_ds.py`

**Documentation:**
- `SESSION_45_RULE10_V3_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 45 entry
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 078 added

## Why Rule 10 v3 ships

- Both grids strongly positive (+$29 full / +$54 prefix), no regression.
- pct_opt improves on both grids (full +0.43%, prefix +1.17%).
- Per-category: pair regret drops on both grids (−$62 full, −$124 prefix);
  no other category degrades.
- Worst-case regret unchanged (max_regret = $5.74 same as v40b on full).
- Mechanism is interpretable and consistent with prior methodology
  (weak-hand top inversion + S44 suit-dominance).

## What's queued for Session 46+

- **Rule 11 candidate — J-pair pair-to-bot + DS.** A5−A2 = +$2,975/1000h
  for P=J specifically. Requires a setting-builder that places pair in
  bot and chooses 2 singletons to complete a DS pattern.
- **Two_pair within-class suit-aware bot (B1−B2 = +$1,864/1000h).**
  Two_pair is ML territory cross-class but this within-class rule may
  be feasible — needs a setting-builder for two_pair both-intact + DS.
- v40 / v41 ML retrain (feed v34_dt with v41 baseline residuals)
- Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
- Round-3 within-trips features (S42 carryover)
- Trips_pair G3 oracle exploration (+$85 ceiling)
- KK/AA single-suited Rule-4-bot residual

## Total project rule count: 10 (Rule 10 evolved v40 → v40b → v41).

The rule count stays at 10 because Rule 10 v3 is a refinement of
Rule 10's bot construction, not a separate rule.
