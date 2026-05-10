# Session 53 OVERNIGHT — Rule 17 (comprehensive high_only handler) ships as v52

_Generated: 2026-05-10_

## TL;DR

User asked for high-leverage overnight work. Investigated extending the
high_only HIMID family from A/K/Q-high (Rules 14/15/16) to ALL high_only
no-pair sub-pops, AND adding defensive top-inversion for the weak-hand
zones.

**v52 ships +$17/1000h whole-grid full / $0 prefix.** Smaller than the
+$50-160 estimate but still meaningful. Path of investigation revealed
critical insights:

| Strategy | Description | Δ vs v47 |
|---|---|---:|
| v48 | v47 + HIMID for J/T/9/8/7-high | +$8 |
| v50 | v48 + defensive A/K/Q/J at 2nd-high ≤ 8 | +$2 (regressed −$6 vs v48!) |
| **v52** | **smart combo: J-HIMID + max≤T always defensive + K/Q/J defensive when s2≤8** | **+$17** |

The v50 regression revealed that A-high defensive HURTS — A-on-top is
right 91-94% even at s2 ≤ 8. v52 corrects by:
1. Skipping A-high defensive entirely
2. Always-defensive for max ≤ T (where defensive dominates 62-86%)
3. Gated defensive for K/Q/J at s2 ≤ 8 only

## Methodology investigation: per-(max, s2) characterization

Detailed per-cell sweep revealed oracle top-pick distribution by max:

| max | max-on-top% | top=2 (defensive)% | top=3-4 (also defensive)% | combined defensive% |
|---|---:|---:|---:|---:|
| A | 93% | 0.3% | <1% | <2% |
| K | 66% | 7% | ~5% | ~12% |
| Q | 49% | 16% | ~12% | ~28% |
| J | 27% | 28% | ~21% | **~49%** |
| T | 15% | 35% | ~28% | **~63%** |
| 9 | 7% | 42% | ~32% | **~74%** |
| 8 | 3% | 45% | ~41% | **~86%** |

**Critical finding:** for max ≤ T, defensive (lowest-on-top) is the right
structure on 62-86% of hands. v48's HIMID (forcing max-on-top) was wrong
on the majority of these.

## v52 design — comprehensive high_only handler

Rule chain for high_only no-pair (in priority order):

1. **Defensive zones (lowest-on-top + DS-bot HIMID, with SS fallback):**
   - max ∈ {T, 9, 8, 7}: ALWAYS defensive (no s2 gate — defensive dominates)
   - max ∈ {J, Q, K}: defensive ONLY when 2nd-highest ≤ 8 (weak-hand gate)
   - max = A: skip defensive (A-on-top is universally right)

2. **HIMID zones (max-on-top + DS/SS HIMID — handled by v47 + Rule 17):**
   - max = A (Rule 14, via v47)
   - max = K (Rule 15, via v47)
   - max = Q (Rule 16, via v47)
   - max = J (Rule 17, NEW — fires when defensive doesn't)

The chain order: defensive triggers first; if not, HIMID for max=J;
fall through for max ∈ {Q, K, A} → v47's existing rules.

## Grade results

**Full grid (N=200):**

| Strategy | $/1000h | pct_opt | high_only $/1000h |
|---|---:|---:|---:|
| v47 | $2,515 | 43.30% | $3,096 |
| **v52** | **$2,498** | **43.34%** | **$3,014** |
| **Δ** | **−$17** | **+0.04%** | **−$82** (−2.6%) |

**Prefix grid:** $1,522 unchanged ($0 — high_only zero prefix coverage).

p90 regret: 0.725 → 0.720 (improved). Max regret unchanged.

## Cumulative arc (now S43-S53)

| Strategy | Full $/1000h | Δ vs v39 |
|---|---:|---:|
| v39 | $2,846 | baseline |
| ... (S43-S52 ships) | ... | ... |
| v47 (S52, Rule 16 Q-high) | $2,515 | −$331 |
| **v52 (S53, Rule 17+...)** | **$2,498** | **−$348** |

**Cumulative v14_combined → v52: −$535/1000h.**

## Other findings (negative results, kept for reference)

- **v48 (HIMID for all of J-7-high)** ships only +$8 because it's wrong
  on the dominant defensive zones for low-max sub-pops.
- **v50 (v48 + defensive A/K/Q/J at s2 ≤ 8)** regressed −$6 vs v48. The
  A-high defensive override forces lowest-on-top on hands where A-on-top
  is right 91-94% of the time. Massive per-hand loss outweighed gains.
- **Diagnosis from v50:** must exclude A-high from defensive triggers.
  v52 incorporates this lesson.

## Methodology lessons (Session 53 overnight)

1. **High-rank sub-pops (A/K) defy the defensive playbook.** Even when
   2nd-high is low, oracle still wants A-on-top (and to a lesser extent
   K-on-top). The defensive "dump weakest" intuition fails here because
   the high card has too much top-tier equity.

2. **Low-rank sub-pops (max ≤ T) overwhelmingly favor defensive.** For
   T-high through 8-high, oracle picks max-on-top only 3-15% of the time.
   The HIMID heuristic (max-on-top) is wrong on 85-97% of these hands.

3. **The per-(max, s2) characterization is the right diagnostic.** Without
   the cell-level breakdown, the right gate ("max ≤ T always; max ∈ {J,Q,K}
   gated by s2 ≤ 8; max = A never") would have been hard to find.

4. **Layered ships can regress.** v50 (v48 + defensive overrides) regressed
   vs v48. Adding rules without isolating their effect is risky. Always
   test the layered combo, not just the standalone components.

## Files produced (overnight)

**Strategy attempts (only v52 ships):**
- `analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py` (sister: HIMID for J-7, +$8)
- `analysis/scripts/strategy_v50_rules22_23_high_only_defensive.py` (sister: HIMID + defensive A/K/Q/J ≤8, regressed −$6 vs v48)
- `analysis/scripts/strategy_v51_defensive_max_le_J.py` (sister: defensive only for max ≤ J, untested)
- `analysis/scripts/strategy_v52_full_high_only_handler.py` (PRODUCTION)
- `analysis/scripts/strategy_v53_defensive_KQJ_only.py` (sister: KQJ defensive without max ≤ T, untested)

**Graders:**
- `analysis/scripts/grade_v48_rules17_21.py`
- `analysis/scripts/grade_v50_defensive.py`
- `analysis/scripts/grade_v52_full_handler.py`

**Drills:**
- `analysis/scripts/drill_Q_high_non_Q_top_characterization.py` (Drill O — Q-high non-Q-on-top)

**Documentation:**
- `SESSION_53_OVERNIGHT_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 53 entry; front-matter
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 086 added

## Why v52 ships

- **+$17/1000h whole-grid full**, $0 prefix (high_only zero prefix)
- pct_opt full: +0.04%; high_only sub-category −2.6% (better)
- p90 regret IMPROVED 0.725 → 0.720
- Max regret unchanged
- Mechanism: comprehensive high_only handler covering all max ≥ 7 sub-pops
  with the right offensive vs defensive structure per-cell

## Single-rule lift records (UPDATED with v52 = "Rule 17 generalized")

| Rank | Rule | Session | Full lift |
|---|---|---|---:|
| 1 | Rule 14 (A-high HIMID) | S50 | +$131 |
| 2 | Rule 6 (pure trips, v33) | S37 | +$113 |
| 3 | Rule 15 (K-high HIMID) | S51 | +$51 |
| 4 | Rule 10 (J-low pair, v40b) | S43 | +$48 |
| 5 | Rule 7 (three_pair, v37) | S41 | +$43 |
| 6 | Rule 12 (J-low two_pair, v43) | S47 | +$35 |
| 7 | **Rule 17 (high_only generalized)** | **S53 overnight** | **+$17** |
| 8 | Rule 16 (Q-high HIMID) | S52 | +$19 |

## What's still on the table (Session 54+)

The user's question about going down to lower max-ranks is now addressed
(max ∈ {7, 8, 9, T, J} all covered by v52's defensive zones).

Remaining opportunities:
- **Rule 17 v2: address Q-high non-Q-on-top better.** Drill O showed
  10% of Q-high oracle picks J on top (Q-anchor in mid). Could be a Rule 18.
- **Trips_pair Rule 14 v2 (adaptive heuristic)** — known +$1,992 oracle
  gap from S49.
- **v52 ML retrain** — capacity-only retrain of v34_dt against v52
  residuals.
- **Composite (cat=7) within-class** — high regret per hand.
- **Rule 14/15 v2** — non-default top picks (smaller gaps).

## Total project rule count: 17 (v52 = "Rule 17 high_only generalized handler" supersedes Rules 17-21 from v48 attempt).
