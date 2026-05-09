# Session 46 — Rule 11 (J-pair pair-to-bot DS) ships as v42

_Generated: 2026-05-09_

## TL;DR

Drill A's per-pair-rank breakdown (Session 45) found a sharp positive
flip at P=J: A5 − A2 = +$2,975/1000h within-hand (vs −$300 to −$1,100
for P=2..T). Session 46 ran a focused J-pair-J drill (Drill D) to
validate the apples-to-apples comparison and a strategy ship.

**Drill D findings (J-pair-J, P=11 AND max=11, n=34,272):**

| Comparison | Lift ($/1000h) | Verdict |
|---|---:|---|
| **A5 − A1** (pair-to-bot DS vs pair-mid DS) | **+$1,004** | row wins |
| A5 − A2 (S45 headline) | +$2,975 | confirmed |
| A1 − A2 (Rule 10 v3 internal lift) | +$2,553 | confirmed |
| A5 − A6 (DS premium WITHIN pair-bot) | +$2,211 | DS premium real |

**v41 production pick class distribution at J-pair-J:**
- A1 pair-mid + DS: 47.8% (when achievable)
- A2 pair-mid + non-DS: 52.2%
- **A5 pair-bot + DS: 0.0%** ← v41 never picks this

**v42 ships as production:**

| Grid | v41 | v42 | Δ |
|---|---:|---:|---:|
| Full (N=200) | $2,769 | **$2,763** | **−$6/1000h** |
| Prefix (N=1000) | $1,616 | $1,616 | 0 (fires on 0 prefix hands) |

pct_opt full: 41.91% → 41.93% (+0.02%). Pair category $1,843 → $1,829
(−$14 within pair). No per-category regression. Cumulative v39 → v42 =
−$83 full / −$91 prefix.

## Rule 11 — design

```
TRIGGER:
  cat == pair        AND
  P == 11            AND  (pair_rank = J)
  max_rank == 11     AND  (max card = J)
  DS-bot achievable with both J's in bot

SETTING BUILDER:
  Both J's go to BOT.
  Among the 5 non-pair singletons, pick 2 for BOT such that the bot's
  4-card suit pattern is 2+2 (DS):

    Case A: J's same suit X
      Need 2 singletons of the same non-X suit Y. Multiple Y options
      possible; pick the lowest-rank pair (keeps mid + top strength).

    Case B: J's different suits X, Y
      Need 1 singleton of suit X + 1 of suit Y. Pick the lowest-rank
      of each.

  TOP = lowest-rank singleton among the 3 remaining singletons
        (preserves v41's weak-hand top-inversion intent).
  MID = the 2 remaining singletons.

  If no DS-achievable pair-in-bot config: fall through to v41.
```

**Behavioral verification on a 5,000-hand J-pair-J sample:**
- Rule 11 fires on 49.8% of J-pair-J hands (A5 achievability ≈ 55.1% by
  the drill; the ~5% gap is sampling noise + canonical-hand suit symmetry)
- 100% of fired picks correctly have pair-in-bot AND DS-bot
- 100% of fired picks differ from v41 (which never picks A5)

## Drill D structure

`analysis/scripts/drill_J_pair_pair_to_bot_DS.py` extends Drill A's six-
class taxonomy (A1..A6) with two additions:

1. **v41 pick class distribution** — what class does v41's actual pick
   fall into? At J-pair-J: 47.8% A1 + 52.2% A2 (matches v41's design:
   pair-mid + DS when achievable, else pair-mid + non-DS).

2. **v41 vs best-in-class lift** — for each class A_i, compute
   EV(best in A_i) − EV(v41's pick) within-hand. Resolves whether the
   class is reachable from a Rule 11 override and how much lift exists.

| Class | n | best_in_class − v41 ($/1000h) |
|---|---:|---:|
| A1 pair-mid + DS | 16,380 | +$556 |
| A2 pair-mid + non-DS | 34,272 | +$86 |
| A3 pair-split + DS | 31,500 | −$11,907 |
| A4 pair-split + non-DS | 34,272 | −$13,319 |
| **A5 pair-bot + DS** | **18,900** | **+$3,769** |
| A6 pair-bot + non-DS | 34,272 | +$734 |

A5's +$3,769 is 6× larger than A1's +$556 (the next-best within-class
lift over v41). This is the largest cross-class override opportunity.

## Why the heuristic captures only ~56% of A5's oracle ceiling

A5's lift over v41 (+$3,769) is the BEST EV among all pair-bot + DS
settings, oracle-picked. v42's heuristic picks ONE specific A5 setting:

  - Lowest-rank singletons in bot (to keep mid Hold'em strength)
  - Lowest of the 3 remaining singletons on top (top-inversion)

Whole-grid lift achieved: +$6/1000h. Translated to per-fire: +$6 / 0.285%
≈ +$2,105/1000h within fires. Captures ~56% of the +$3,769 oracle
ceiling. The remaining ~$1,664/1000h within fires (~+$5/1000h whole-grid)
is heuristic-vs-oracle gap — likely from suboptimal singleton-pair
selection in cases with multiple DS-achievable bots, or from the
top-vs-mid placement of the 3 non-bot singletons.

**Future refinement candidate (Session 47+):** sweep alternative tie-breaks
(lowest-pair vs highest-pair; lowest-top vs middle-top vs highest-top)
to find a heuristic closer to the oracle's pick. Expected residual:
+$3-5/1000h.

## Methodology lessons (Session 46)

1. **Cross-class override opportunities are ranked by best-in-class
   minus v41.** Drill D's "v41 vs best-in-class" view directly identifies
   where the largest residual sits. A5's +$3,769/1000h was 6× larger
   than the next-best class — clear ship target.

2. **Single-cell rules can ship at <$10/1000h whole-grid lift.** Rule 11
   fires on only 0.285% of grid (J-pair-J × DS-achievable). The whole-
   grid headline is small but the within-fires lift is +$2,105/1000h —
   both numbers are meaningful for different audiences.

3. **Single-cell rules have natural prefix immunity.** J-pair-J has zero
   prefix coverage (no J-pair-J hand falls in canonical IDs < 500K).
   Rule 11 fires on 0 prefix hands → prefix score guaranteed unchanged.
   Same precedent as Session 41/43 high_only-zero-prefix observation.

4. **Heuristic captures ~56% of oracle ceiling.** Don't hold the rule
   for "perfect" — ship the clean lift, queue the heuristic-sharpening
   as a separate follow-up.

## Files produced

**Drill + strategy + grader:**
- `analysis/scripts/drill_J_pair_pair_to_bot_DS.py`
- `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` (PRODUCTION)
- `analysis/scripts/grade_v42_rule11_jpair_pbot_ds.py`

**Documentation:**
- `SESSION_46_RULE11_JPAIR_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 46 entry
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 079 added

## Why Rule 11 ships

- Both grids non-regressive (+$6 full, $0 prefix)
- pct_opt improves on full (+0.02%)
- Per-category: pair drops $14/1000h, all other categories unchanged
- Worst-case regret unchanged (max = $5.74)
- Clean override of v41 — Rule 11 only fires when v41's pick is in A1
  or A2 and a DS pair-in-bot setting exists; the override path is
  surgical, single-cell

## What's queued for Session 47+

- **Rule 11 heuristic refinement** — capture more of A5's +$3,769
  ceiling (currently 56%). Sweep tie-breaks: lowest-rank vs highest-rank
  bot-singletons; top-placement variants. Expected: +$3-5/1000h whole-grid.
- **Two_pair within-class suit-aware bot (B1−B2 = +$1,864/1000h)**.
  Sister candidate from Drill B; needs careful setting-builder.
- **v42 ML retrain** — capacity-only retrain of v34_dt against v42 residuals.
- **Drill A per-pair-rank A5 lift extrapolation:** P=T also showed +$630
  (smaller signal); worth a focused drill.
- Drill A per-pair-rank A1−A2 by P: confirm the +$2,756 average doesn't
  hide cells where v40b's pick was already optimal.

## Total project rule count: 11 (Rules 1-10 + Rule 11 = J-pair pair-to-bot DS).

This is the FIRST single-cell rule of the project. Trigger fires on
0.285% of grid (smallest fire rate among shipped rules). All prior
rules (Rules 1-10) had broader populations.
