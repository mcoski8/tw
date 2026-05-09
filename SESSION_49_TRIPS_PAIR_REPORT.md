# Session 49 — Trips_pair within-class DS investigation (NO SHIP)

_Generated: 2026-05-09_

## TL;DR

Session 49 applied the suit-dominance "DS premium within X" lens to
trips_pair (cat=4, 171,600 hands, 2.86% of grid). Findings:

**Drill I — trips_pair within-class DS variant sweep (within-hand pairwise, n=171,600).**
v44 already picks pair-bot 85% of the time and DS-bot 75%. Within-class
findings:

| Comparison | Lift within fires | Verdict |
|---|---:|---|
| V3 − V5 (pair-bot DS vs pair-split DS) | **+$13,397** | row wins |
| V1 − V3 (pair-mid DS vs pair-bot DS) | −$6,778 | col wins |
| V1 − V2 (DS premium WITHIN pair-mid) | +$1,060 | row wins |
| V3 − V4 (DS premium WITHIN pair-bot) | +$468 | row wins |
| **v44 vs best-in-V3 (oracle within DS pair-bot)** | **+$1,992** | **oracle gap** |

**Structural conclusion:** pair-bot is universally optimal for trips_pair.
v44 already does this 85% of the time. The +$1,992 oracle gap is the
residual opportunity — capturing it would require a more adaptive
heuristic than v44's existing pick.

**Drill J — pair-bot DS sub-config sweep.** Tested 7 sub-config × top-pos
variants. **Methodology issue discovered:** the drill's per-variant lifts
were computed via cross-class means (variant's mean EV across hands where
that variant is achievable, vs v44's mean EV across ALL V3-achievable
hands). This is the S44 confounding pitfall — different subsets of
hands. The reported +$4,293 lift for V_B_TOP_SING_HI is NOT a true
within-hand lift.

**Rule 14 attempt — V_B_TOP_SING_HI (no-op).** Designed v45 to pick
V_B_TOP_SING_HI when achievable. Behavioral verification on 50K
trips_pair sample showed **0 picks differ from v44** (Rule 14 fires on
17,498 hands, all match v44 exactly). Grade confirmed: v45 vs v44 =
$0/1000h. **v44 already picks V_B_TOP_SING_HI when achievable** — the
proposed rule is a no-op.

**Decision: no ship this session.** The +$1,992 oracle gap from Drill I
is real but requires adaptive logic to capture. v45 files retained as
artifacts; Drill I and Drill J retained for methodology reference.

## Why Drill J's "winning variant" was misleading

Drill J's measurement loop:

```python
sum_ev_v44 += float(rowf[v44_pick])
n_v44 += 1  # ALL V3-achievable hands

for variant_name, predicate in variant_definitions:
    options = [s for s in settings if predicate(s)]
    if options:
        best_match = max(options, ...)
        sum_ev[variant_name] += float(rowf[best_match["idx"]])
        n_v[variant_name] += 1  # only hands where variant IS achievable
```

The reported lift was `(sum_ev[v] / n_v[v]) - (sum_ev_v44 / n_v44)`.
But `n_v[v]` counted only the variant's achievable subset (e.g., 60,060
for V_B_TOP_SING_HI), while `n_v44` counted all 128,700 V3-achievable
fires. Different subsets → different population means → confounded.

**S44 methodology rule violated:** "cross-class regret averaging is
confounded by hand-population differences. Always validate cross-class
comparisons via within-hand pairwise."

I should have computed `(sum_ev[v] - sum_v44_subset[v]) / n_v[v]` where
`sum_v44_subset[v]` = sum of v44 EVs across the SAME hands where variant
v is achievable. That's the proper within-hand pairwise comparison.

**The sanity-check 0-difference result confirms** v44 picks V_B_TOP_SING_HI
on every Rule 14 fire. The within-hand lift is exactly $0/hand.

## Why does v44 already pick V_B_TOP_SING_HI for trips_pair?

v44 falls through to v43 → ... → v3 (= v14_combined Rule 3) for trips_pair.
Rule 3 of v14_combined is "split the trips, keep the pair." Apparently
the existing implementation picks V_B_TOP_SING_HI configuration whenever
it's achievable — likely as a result of the suit-canonicalization plus
how the rule searches for the best top.

This is a HAPPY ACCIDENT that the +$2,000+/1000h opportunity (which
appears in the v3-vs-oracle gap) is mostly already captured by v3's
existing tie-break.

The remaining +$1,992 oracle gap is on hands where:
- V3 is achievable (pair-bot + DS exists somehow)
- V_B_TOP_SING_HI is NOT achievable (47% of V3-achievable hands)
- Some OTHER V3 variant exists

On those hands, v44's pick may be V3 (matching some other sub-config) or
not-V3 (e.g., V5 pair-split). The ORACLE pick is the best V3 variant
present. Capturing this gap requires identifying the right V3 sub-config
per hand.

This is harder than a simple fixed heuristic. Defer.

## Methodology lessons (Session 49)

1. **Cross-class means are CONFOUNDED — always within-hand pairwise.** Re-iterating
   the S44 lesson because I violated it again in Drill J. The variant's
   mean EV cannot be compared to v44's mean EV unless both are computed
   on the SAME population (within-hand or restricted to the same
   achievability subset).

2. **Sanity-check pick-difference rate before grading.** A simple test
   ("does the rule actually pick differently from production on its
   trigger hands?") would have caught the no-op early. Rule 14 fires
   on 17,498 hands but differs from v44 on 0. That's a no-op signal,
   not a candidate ship.

3. **A sub-pop where the heuristic doesn't already match production is
   the right ship target.** Instead of "pick V_B_TOP_SING_HI when
   achievable", a Rule 14 v2 should target "v44 picks something other
   than the oracle's best V3" — i.e., the residual subset.

4. **Drill methodology — measure WHERE production picks differ from each
   variant** before declaring a winner. If production already matches
   the candidate variant, there's no ship in that variant.

5. **"Happy accidents" in upstream rule chains can already capture some
   of a category's optimization potential.** v3's Rule 3 trips_pair
   logic was apparently picking V_B_TOP_SING_HI all along. This is
   ground truth — don't try to ship a rule that does the same thing.

## Files produced

**Drills (2, both retained as methodology references):**
- `analysis/scripts/drill_trips_pair_DS_within_intact.py` (Drill I — DEFINITIVE within-hand pairwise; reveals +$1,992 oracle gap)
- `analysis/scripts/drill_trips_pair_pbot_DS_subconfig.py` (Drill J — POPULATION-CONFOUNDED sub-config sweep; cross-class mean comparison; produced misleading +$4,293 number)

**Strategy + grader (no-op artifacts):**
- `analysis/scripts/strategy_v45_rule14_trips_pair_DS.py` (no-op vs v44)
- `analysis/scripts/grade_v45_rule14_trips_pair.py`

**Documentation:**
- `SESSION_49_TRIPS_PAIR_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 49 entry (no production change)
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 082 added (negative)

## Production state UNCHANGED

v44_rule13_three_pair_DS remains the strategy of record:
- Full grid: $2,717/1000h, 42.34% pct_opt
- Prefix grid: $1,522/1000h, 53.06% pct_opt
- Cumulative since v39: −$129 full / −$185 prefix

The S43-S48 suit-dominance arc has shipped 5 rules (Rule 10 v40b → v3 →
Rule 11 → Rule 12 → Rule 13). Session 49 does not extend that arc.

## What's queued for Session 50+

- **Trips_pair Rule 14 v2 (adaptive heuristic).** Target the +$1,992
  oracle gap on hands where v44's V3 pick differs from the best V3
  pick. Requires identifying the right sub-config per hand (e.g., based
  on suit profile of trip vs pair vs sings).
- **Composite (cat=7) within-class.** Smallest category but highest
  regret ($4,445/1000h); Rule 8 (quads_pair) and Rule 9 (T2P, TT, plain
  quads) handle subsets. The remaining residual is the unstructured
  composite shapes (quads_trip, etc.).
- **v44 ML retrain.** Capacity-only retrain of v34_dt against v44
  residuals.
- **Two_pair max≤Q refinement.** v43b had +$14 full / -$6 prefix —
  find a sharper gate that doesn't regress prefix.
- **Carryover deferred items:**
  - Q5 J-high no-pair multi-feature deep dive
  - T-low high_only naive top=lo rule
  - Round-3 within-trips features
  - Learned A-vs-C decision tree for Rule 6
  - KK/AA single-suited Rule-4-bot residual

## Total project rule count: 13 (UNCHANGED).

The trips_pair within-class opportunity is real but requires a more
sophisticated heuristic than the simple V_B_TOP_SING_HI fixed tie-break.
v3's Rule 3 logic apparently already achieves this when achievable —
respecting that, don't try to re-ship the same setting.
