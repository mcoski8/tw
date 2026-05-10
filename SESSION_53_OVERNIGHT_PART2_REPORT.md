# Session 53 OVERNIGHT PART 2 — v36_dt new ML champion + Rule 18 attempts (negative)

_Generated: 2026-05-10_

## TL;DR

After v52 (Rule 17 high_only handler) shipped, continued overnight work:

1. **v36_dt new ML champion ships +$33/1000h** vs v34_dt. Capacity-only
   retrain at depth=36 ml=1 (vs v34's depth=34 ml=2). 1.06M leaves
   (+22% over v34's 874K).

2. **Pair gap analysis revealed $852/1000h whole-grid residual** in pair
   category. Top cells: AA ($58), KK ($57), QQ ($49) on the diagonal
   (pair = max).

3. **Rule 18 attempts (HITOP and HIBOT tie-breaks) BOTH regressed.**
   v54 (HITOP, -$5) and v55 (HIBOT, -$42) confirm that the existing
   Rule 4 + Rule 5 are near-optimal for AA/KK/QQ. Forcing DS-bot via
   different singleton selection hurts on average.

## v36_dt — new ML champion

| Grid | v34_dt | v36_dt | Δ |
|---|---:|---:|---:|
| Full (N=200) | $1,681 | **$1,649** | **−$33** |
| Prefix (N=1000) | $889 | $891 | +$2 (slight) |

**pct_opt full: 52.02% → 53.61% (+1.59%)** — biggest ML champion jump
since v34's debut.

**Per-category full grid breakdown:**

| Category | v34_dt | v36_dt | Δ |
|---|---:|---:|---:|
| trips_pair | $1,057 | **$909** | **−$148** ← biggest gain |
| composite | $1,173 | **$960** | **−$213** |
| trips | $1,291 | $1,194 | −$97 |
| quads | $613 | $545 | −$68 |
| two_pair | $978 | $918 | −$60 |
| three_pair | $1,635 | $1,613 | −$22 |
| pair | $1,619 | $1,604 | −$15 |
| high_only | $2,806 | $2,796 | −$10 |

The capacity unlock helps rare-shape categories most (trips_pair,
composite, trips, quads). Common-shape categories (high_only, pair) get
small but positive gains.

**Methodology gate check:** prefix regression $2 vs full lift $33 = 0.06x
ratio (vs the 2x threshold from S42). Passes cleanly.

## Pair gap analysis

Per-(max, pair) cell breakdown for the 46.6% pair category:

| max | pair | n | mean_reg/1000h | whole-grid contrib |
|---|---:|---:|---:|---:|
| **A (14)** | **A (14)** | 215,424 | $1,612 | **+$57.78** |
| **K (13)** | **K (13)** | 125,664 | $2,703 | **+$56.52** |
| **Q (12)** | **Q (12)** | 68,544 | $4,339 | **+$49.49** |
| A | Q (12) | 89,760 | $1,801 | +$26.90 |
| K | Q (12) | 57,120 | $2,703 | +$25.70 |
| ... | ... | ... | ... | ... |
| **TOTAL pair** | — | 2,800,512 | $1,829 | **+$852.48** |

The diagonal (pair = max) for AA/KK/QQ totals **$164/1000h whole-grid**
— biggest unclaimed pair zone. Plus ~30% more in off-diagonal (e.g.,
K-pair-Q, A-pair-J, etc.).

## Rule 18 attempts (negative results)

Hypothesis: the AA/KK/QQ pair gap is suit-blind bot. Adding DS-aware
bot construction should help.

**v54 (Rule 18 with HITOP tie-break — TOP=highest non-pair singleton):**
- Fires on 47.8% of AA/KK/QQ (195,780 hands)
- 67.7% of fires differ from v52
- Grade vs v52: **−$5/1000h** (regression)
- pair: $1,829 → $1,840 (+$11 within pair)

**v55 (Rule 18 v2 with HIBOT tie-break — TOP=lowest non-pair singleton):**
- Same triggers and pop
- Grade vs v52: **−$42/1000h** (severe regression!)
- pair: $1,829 → $1,919 (+$90 within pair)
- pct_opt 43.34% → 42.88% (-0.46%)

**Diagnosis:** Rule 4 (existing v3 logic) + Rule 5 (KK/AA Rainbow override)
are already near-optimal for AA/KK/QQ. Forcing DS-bot via singleton
selection BREAKS the existing tie-breaks (which apparently approximate
oracle better than HITOP/HIBOT alone).

The pair gap requires more sophisticated logic than fixed tie-break
selection. Possibly:
- Adaptive tie-break by hand structure (suit alignment, connectivity)
- Conditional trigger (only when DS bot is structurally distinct from
  Rule 4's pick)
- Feature-based ML routing for the pair zone (which v36_dt's added
  capacity may already partially address — pair improved $1,619 → $1,604)

Defer Rule 18 attempts. The pair zone is ML territory at this point.

## Strategy state at end of overnight

**Two production tracks:**

| Track | Strategy | Score (full / prefix) |
|---|---|---:|
| Rule chain (human-memorizable) | **v52_full_high_only_handler** | $2,498 / $1,522 |
| ML champion | **v36_dt** (NEW) | $1,649 / $891 |

The rule chain still trails the ML by ~$849/1000h, but is the
human-readable strategy guide.

## Cumulative arcs

**Rule chain v39 → v52 (S43-S53 arc):** −$348 full / −$185 prefix.
**ML v32 → v36_dt:** v32 was $1,715 → v36_dt $1,649 = −$66/1000h cumulative.

## Files produced (overnight Part 2)

**ML retrain:**
- `data/v36_dt_model.npz` (640 MB, 1.06M leaves at depth=36 ml=1)
- `analysis/scripts/strategy_v36_dt.py` (PRODUCTION ML champion)
- `analysis/scripts/grade_v36_dt.py`

**Rule 18 attempts (sisters, both regressed, kept as artifacts):**
- `analysis/scripts/strategy_v54_rule18_high_pair_DS.py` (HITOP, −$5)
- `analysis/scripts/strategy_v55_rule18_hibot.py` (HIBOT, −$42)
- `analysis/scripts/grade_v54_rule18.py`
- `analysis/scripts/grade_v55_rule18_hibot.py`

**Documentation:**
- `SESSION_53_OVERNIGHT_PART2_REPORT.md` (this file)
- Updated CURRENT_PHASE.md, STRATEGY_GUIDE.md, DECISIONS_LOG.md (Decision 087)

## Total session 53 overnight ships

1. **v52 (Rule 17 comprehensive high_only handler)**: +$17 full / $0 prefix
2. **v36_dt (ML capacity retrain)**: +$33 full / -$2 prefix

Combined value: ~+$50/1000h whole-grid full (across both production tracks).

## Methodology lessons (Session 53 overnight Part 2)

1. **Capacity-only ML retrains can ship +$33** even when feature set is
   unchanged. v36_dt added 22% more leaves and gained −$33/1000h, mostly
   in rare-shape categories (trips_pair, composite, trips, quads).

2. **Pair AA/KK/QQ are ML territory.** Two attempts at suit-aware pair
   rules (v54, v55) both regressed. Existing Rule 4 + Rule 5 plus ML
   already capture the pair gap better than naive HITOP/HIBOT.

3. **The rule chain is approaching diminishing returns.** Easy wins are
   harvested. Future improvement requires:
   - More sophisticated heuristics (adaptive tie-breaks)
   - OR ML-based residual fitting on top of the rule chain
   - OR new feature engineering for the ML champion

## What's queued for Session 54+

- **More ML capacity:** depth=38 ml=1 retrain (next step)
- **Feature engineering for pair zone:** new gated features for AA/KK/QQ
  could unlock more pair lift via ML
- **Trips_pair Rule 14 v2 (S49 deferred):** the +$1,992 oracle gap remains
- **Composite (cat=7) within-class:** v36_dt already addresses some via
  capacity, but rule extraction may complement
