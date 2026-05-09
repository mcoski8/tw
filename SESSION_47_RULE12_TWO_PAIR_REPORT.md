# Session 47 — Rule 11 sweep (negative) + Rule 12 (two_pair both-intact + DS) ships as v43

_Generated: 2026-05-09_

## TL;DR

Session 47 ran two parallel investigations:

**1. Rule 11 heuristic sweep (Drill E) — NEGATIVE.** Tested 6 simple
tie-break combinations (low/high pair-singletons × low/mid/high top).
v42's V_LOLO is empirically optimal; no variant beats it. The +$1,794/1000h
within-fires gap to A5 oracle requires more sophisticated logic than
simple tie-breaks.

**2. Rule 12 — two_pair both-intact + DS-bot (Drill F) — SHIPS.**
Drill B's B1−B2 = +$1,864/1000h sister candidate validated.
HH-to-bot tie-break wins (+$1,808/1000h within fires) over LL-to-bot
(+$1,044/1000h). Hybrid (HH preferred, LL fallback) ships as v43.

**v43 production:**

| Grid | v42 | v43 | Δ |
|---|---:|---:|---:|
| Full (N=200) | $2,763 | **$2,727** | **−$35/1000h** |
| Prefix (N=1000) | $1,616 | **$1,550** | **−$66/1000h** |

pct_opt full: 41.93% → 42.20% (+0.27%). pct_opt prefix: 51.81% → 52.61%
(+0.80%). Two_pair category $3,371 → $3,211 (−$160 within two_pair).
**Largest single-rule full-grid lift since v33's Rule 6 (Session 37,
+$113).** Cumulative v39 → v43 = −$118 full / −$157 prefix.

## Drill E — Rule 11 heuristic sweep (negative result)

`analysis/scripts/drill_rule11_heuristic_sweep.py` — for each Rule 11
fire (J-pair-J + DS-achievable), evaluate 6 variants:

  V_{LO|HI}{LO|MID|HI} where:
  - First letter = LOW vs HIGH pair-of-bot-singletons (rank sum)
  - Second letter(s) = LOW vs MID vs HIGH top among remaining 3 sings

Results (n_fires = 18,900, full grid):

| Variant | Perfect% | Lift vs v41 | Whole-grid full | Gap to A5 |
|---|---:|---:|---:|---:|
| **V_LOLO (v42 current)** | **36.2%** | **+$1,975** | **+$6.21** | $1,794 |
| V_HILO | 25.5% | +$945 | +$2.97 | $2,824 |
| V_LOHI | 23.2% | +$736 | +$2.32 | $3,033 |
| V_LOMID | 13.2% | +$203 | +$0.64 | $3,566 |
| V_HIMID | 8.6% | −$1,419 | −$4.46 | $5,188 |
| V_HIHI | 9.5% | −$1,638 | −$5.15 | $5,407 |

**v42 (V_LOLO) wins decisively.** No alternative beats it. The remaining
+$1,794/1000h gap to A5 oracle would require more sophisticated logic
(connectivity-aware singleton selection, or oracle-mimicking enumeration).

## Drill F — two_pair within-class DS (HH-bot vs LL-bot)

`analysis/scripts/drill_two_pair_DS_within_intact.py` — for J-low
two_pair hands, enumerate all (mid_pair_choice, bot_singletons_choice)
combinations that yield both-intact + DS bot. Compare:

  V_LL_BOT  : LL-pair-to-bot; pick lowest-rank singletons completing DS
  V_HH_BOT  : HH-pair-to-bot; same singleton tie-break
  B1 oracle : best EV among all both-intact + DS settings (ceiling)

Results on full J-low two_pair pop (n=262,080, fires=120,960 = 46.2%):

| Variant | Perfect% | Lift vs v42 | Whole-grid full | Gap to B1 |
|---|---:|---:|---:|---:|
| **V_HH_BOT** | **69.1%** | **+$1,808** | **+$22.75** | $696 |
| V_LL_BOT | 65.6% | +$1,044 | +$13.14 | $1,460 |
| B1 oracle (ceiling) | 100% | +$2,505 | +$50.42 | $0 |

**V_HH_BOT wins.** HH-to-bot is +$764/1000h better than LL-to-bot within
fires.

**Achievability decomposition:**
- Total fires (≥1 of HH-bot or LL-bot DS achievable): 120,960
- HH-bot achievable: 75,600 (62.5% of fires)
- LL-bot achievable: 75,600 (62.5% of fires)
- Both achievable: 30,240 (25% of fires)
- HH-only: 45,360 (37.5% of fires)
- LL-only: 45,360 (37.5% of fires)

A hybrid rule covers all 120,960 fires:
- Use HH-bot when achievable (75,600 hands at +$1,808 each)
- Else use LL-bot (45,360 hands at +$1,044 each)

Estimated whole-grid lift: +$30/1000h. Measured (next section): +$35.

## Rule 12 design

```
TRIGGER:
  cat == two_pair       AND
  max_rank ≤ J          AND
  DS-bot achievable with both pairs intact (HH or LL to bot)

SETTING BUILDER:
  Try HH-to-bot first:
    pair-cards = the 2 HH cards
    Find 2 singletons completing 2+2 DS suit pattern with HH-suits.
    If found: use HH-to-bot.

  Else try LL-to-bot:
    pair-cards = the 2 LL cards
    Find 2 singletons completing 2+2 DS suit pattern with LL-suits.
    If found: use LL-to-bot.

  Else: fall through to v42.

  When valid (sing_a, sing_b) candidates exist:
    Tie-break by lowest rank-sum (preserves mid + top strength).

  Once pair-to-bot + sings chosen:
    BOT = chosen pair + 2 sings
    MID = the OTHER pair (pair-anchor in mid stays for Hold'em strength)
    TOP = the leftover singleton (no choice — only 1 sing left)
```

**Behavioral verification on 30K J-low two_pair sample:**
- Rule 12 fires on 47.3% (matches Drill F's 46.2%; close)
- 100% of fires correctly produce DS bot
- 100% of fires correctly preserve both pairs intact (mid_is_pair == True)
- 27.6% of picks differ from v42

## Grade results

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | two_pair $/1000h |
|---|---:|---:|---:|
| v42 | $2,763 | 41.93% | $3,371 |
| **v43** | **$2,727** | **42.20%** | **$3,211** |
| **Δ** | **−$35** | **+0.27%** | **−$160** |

**Prefix grid (N=1000):**

| Strategy | $/1000h | pct_opt |
|---|---:|---:|
| v42 | $1,616 | 51.81% |
| **v43** | **$1,550** | **52.61%** |
| **Δ** | **−$66** | **+0.80%** |

## Cumulative arc (Session 45-47, all pair/two_pair domain)

| Strategy | Full | Prefix | Δ vs prior |
|---|---:|---:|---:|
| v39 (Session 42 overnight) | $2,846 | $1,707 | baseline |
| v40b (Session 43) | $2,798 | $1,670 | −$48 / −$37 |
| v41 (Session 45) | $2,769 | $1,616 | −$29 / −$54 |
| v42 (Session 46) | $2,763 | $1,616 | −$6 / $0 |
| **v43 (Session 47)** | **$2,727** | **$1,550** | **−$35 / −$66** |
| **v39 → v43 cumulative** | | | **−$119 / −$157** |

This is the largest 4-session cumulative arc since the v30 → v34 ML
progression (+$113 across S36-S38). The S45-S47 arc combines:
- Suit-aware bot construction (Rule 10 v3)
- Single-cell pair-to-bot DS at J-pair-J (Rule 11)
- Cross-class two_pair both-intact + DS (Rule 12)

All three rules share the same underlying mechanism: **the suit-dominance
finding (Session 44) applied within the right structural class**. Pairs
must stay anchored (Drills A + B confirmed); within that constraint, the
DS bot is universally the right pick when achievable.

## Methodology lessons (Session 47)

1. **Simple tie-break sweeps cap quickly.** Drill E showed v42's existing
   heuristic was already optimal among 6 simple variants. Further refinement
   requires structural complexity (connectivity, suit-aware mid placement).
   This is a hard-cap signal — don't burn cycles on more simple sweeps for
   Rule 11.

2. **Cross-class within-pop rules from drill B's "DS premium within X" lens
   ship reliably.** Drill A's A1−A2 = +$2,756 → Rule 10 v3 (+$29). Drill B's
   B1−B2 = +$1,864 → Rule 12 (+$35). Drill D's A5-vs-v41 → Rule 11 (+$6).
   The "within-class DS premium" lens is the project's most productive
   rule-discovery axis right now.

3. **HH-to-bot vs LL-to-bot tie-break: HH wins for two_pair.** Counter
   to "lowest pair to bot for kicker preservation" intuition. Mechanism:
   HH in bot creates a stronger 2-pair-with-kicker Omaha hand; LL in mid
   still anchors the Hold'em mid because pair-mid-anywhere beats most
   non-pair mid combos.

4. **Cumulative ship arcs >$100/1000h come from structural-axis families.**
   v30→v34 was the ML capacity arc. v39→v43 is the suit-dominance arc.
   Both are 4-session multi-rule ships sharing one underlying insight.

## Files produced

**Drills (2):**
- `analysis/scripts/drill_rule11_heuristic_sweep.py` (Drill E, NEGATIVE)
- `analysis/scripts/drill_two_pair_DS_within_intact.py` (Drill F, DEFINITIVE)

**Strategy + grader:**
- `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` (PRODUCTION)
- `analysis/scripts/grade_v43_rule12_two_pair.py`

**Documentation:**
- `SESSION_47_RULE12_TWO_PAIR_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 47 entry
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 080 added

## What's queued for Session 48+

- **Two_pair max≥Q extension.** Rule 12 currently scoped to max_rank ≤ J.
  Drill B's results extended to higher max_rank? May ship additional lift.
- **Rule 11 + Rule 12 unified pattern: "suit-aware bot for any pair-anchor"**.
  Could rewrite as a generic rule covering pair, J-pair, two_pair, etc.
- **v43 ML retrain.** Capacity-only retrain of v34_dt against v43 residuals.
  Pattern: previous capacity retrains shipped +$15-58.
- **Three_pair within-class DS-bot.** Three_pair is also a structural
  pair-anchor population — apply the same lens?
- **Carryover deferred items:**
  - Q5 J-high no-pair multi-feature deep dive
  - T-low high_only naive top=lo rule
  - Round-3 within-trips features
  - Learned A-vs-C decision tree for Rule 6
  - Trips_pair G3 oracle exploration
  - KK/AA single-suited Rule-4-bot residual

## Total project rule count: 12 (Rules 1-11 + Rule 12 = J-low two_pair both-intact + DS).

Rule 12 is the largest single-rule full-grid lift since v33's Rule 6
(Session 37, +$113). The S45-S47 arc combines three rules from the
suit-dominance family (Rule 10 v3, Rule 11, Rule 12) for −$119 full /
−$157 prefix cumulative — the project's third-largest 4-session arc
after v30→v34 (ML, +$113) and v25→v34 (gated features cascade, +$248).
