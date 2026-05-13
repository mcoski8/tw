# Session 73 — v46b_dt PARTIAL POSITIVE / NULL ship: ho_v6 SS+ms features lift v44 by $5/1000h full at depth=36 ml=1 (within-cat high_only +$24); below +$10 ship threshold

_Generated: 2026-05-13_

## TL;DR — Regime-confound theory CONFIRMED; H1 features PARTIALLY PRODUCTIVE; net ship signal BELOW threshold

S72 v46_dt at depth=32 ml=3 regressed v44 by −$256/1000h (full). The
S73 retry — same 2 ho_v6 SS+ms features, **same hyperparameters as
v44** (depth=36 ml=1) — flips the verdict by **+$261/1000h** to land at
**+$5/1000h** full. The regime change ALONE accounted for the entire
S72 NULL signal.

But +$5 is exactly the user's stated NULL threshold (≤+$5 NULL,
≥+$10 ship). Decision 108 records this as **PARTIAL POSITIVE / NULL
ship**: H1 features are confirmed productive within-cat (+$24/1000h on
high_only), the regime-confound theory is empirically validated, but
the full-grid net lift is below the ship bar. v44_dt remains ML
champion; pivot to H2 (route-tradeoff comparator) or gradient boosting
in S74.

| Metric | v44_dt | v46_dt (S72 NULL) | v46b_dt (S73) | Δ v46b vs v44 |
|---|---:|---:|---:|---:|
| Full grid pct_opt | 64.80% | 55.94% | **64.92%** | **+0.12pp** |
| Full grid $/1000h | $1,081 | $1,337 | **$1,076** | **+$5 better** |
| Full grid p90 regret | 0.390 | 0.445 | **0.385** | **better** |
| Full grid p99 regret | 0.970 | 1.000 | 0.970 | tied |
| Leaves | 2,248,173 | 1,097,621 | **2,260,527** | **+12,354** |
| Features | 107 | 109 | 109 | +2 ho_v6 |
| Depth / ml | 36 / 1 | 32 / 3 | **36 / 1** | same as v44 |
| Training fit | — | 478.3s | 610.0s | — |

## Phase 1 — v46b_dt training at depth=36 ml=1 (DONE)

`PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v46_dt.py
--max-depth 36 --min-samples-leaf 1 --output data/v46b_dt_model.npz`

- Fit time: 610.0s (vs v46's 478.3s; deeper depth + ml=1 cost ~2 min).
- Leaves: **2,260,527** (vs v44's 2,248,173 → **+12,354 leaves**).
- Depth: 36.
- Model file: 1,266.75 MB (zstd-compressed npz; 2× v46's 691.97 MB
  because of the leaf-count delta).

**Tripwire #1 — feature importance (NULL signal):**

```
#75  ho_v6_topMax_SS_ms_max_mid_high_g       0.05%   (v46 was #79)
#105 ho_v6_topMax_SS_ms_n_configs_g          0.01%   (v46 was #105)
```

Both features remain deep in the importance tail (S71 prediction:
top-50 = ship, #50+ = ambiguous, #100+ = NULL). The placements barely
moved from v46's #79/#105; the regime change did NOT promote them into
the top-50.

**Tripwire #2 — leaf growth (SHIP signal):**

v44: 2,248,173 leaves. v46b: 2,260,527 leaves. **+12,354 leaves
(≥10K threshold).**

The leaf-growth tripwire fires SHIP at v44's saturating regime — the
features ARE prying open new splits, just at low frequency. v46 at
depth=32 ml=3 collapsed leaves by 51% because the depth+ml constraint
binds before the new features can route. v46b restores tree capacity
and absorbs +12K leaves of new splits.

**Mixed tripwire verdict:** features ARE used (+12K leaves) but at LOW
WEIGHT (#75/#105 importance) — productive but not transformative. The
prefix + full grader resolved this.

## Phase 2 — v46b inference + grader scaffolding (DONE)

* `analysis/scripts/strategy_v46b_dt.py` — copy of strategy_v46_dt.py
  with MODEL_PATH → v46b_dt_model.npz; function renamed to
  strategy_v46b_dt; 16-block gated-feature index dispatch unchanged.
* `analysis/scripts/grade_v46b_dt.py` — copy of grade_v46_dt.py with
  baseline choices extended to include v46 (for direct v46b vs v46
  comparison if needed) and import switched to strategy_v46b_dt.

## Phase 3 — prefix grader (DONE — BYTE-IDENTITY)

**v46b vs v44 on prefix grid (500K canonical hands, n=1000 oracle):**

| strategy | pct_opt | $/1000h | p90 | wall |
|---|---:|---:|---:|---:|
| v44_dt (baseline) | 67.13% | $686 | 0.264 | 67s |
| v46b_dt | **67.13%** | **$686** | **0.264** | 70s |
| **Δ** | **0.00pp** | **+$0** | tied | — |

**Per-category prefix breakdown — BYTE-IDENTICAL:**

| category | n hands | v44 $/1000h | v46b $/1000h | Δ |
|---|---:|---:|---:|---:|
| pair | 215,162 | 595 | 595 | 0 |
| two_pair | 204,275 | 663 | 663 | 0 |
| trips | 25,245 | 1,086 | 1,086 | 0 |
| trips_pair | 25,943 | 727 | 727 | 0 |
| three_pair | 25,614 | 1,143 | 1,143 | 0 |
| quads | 1,100 | 783 | 783 | 0 |
| composite | 2,661 | 1,226 | 1,226 | 0 |

The prefix grid contains 0 high_only canonical IDs (per S72 finding),
so the gated ho_v6 features evaluate to 0 for all 500K hands. With
**same regime + same base features**, the v46b tree topology is
byte-identical to v44 on the non-high_only categories — exactly the
S72 methodology #3 prediction: "the byte-identity guarantee requires
same hyperparameters AND same base feature set."

**Surgical gating WORKS at v44's regime.** S72's v46 broke this
because regime change altered tree topology. v46b restores it.

## Phase 4 — full grader (DONE — DECISIVE)

`PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v46b_dt.py
--grid full --baseline v44` (data/session73/grade_v46b_full.log).

**v46b vs v44 full grid (6,009,159 hands, n=200 realistic 70/25/5):**

| strategy | pct_opt | $/1000h | p90 | p99 | wall |
|---|---:|---:|---:|---:|---:|
| v44_dt (baseline) | 64.80% | $1,081 | 0.390 | 0.970 | 1023s |
| v46b_dt | **64.92%** | **$1,076** | **0.385** | 0.970 | 1075s |
| **Δ** | **+0.12pp** | **+$5 better** | better | tied | — |

**Per-category full-grid breakdown:**

| category | n hands | v44 $/1000h | v46b $/1000h | Δ | pct_opt v44 → v46b |
|---|---:|---:|---:|---:|---|
| **high_only** (on-target) | 1,226,940 | 1,868 | **1,844** | **−$24 better** | 41.8% → 42.5% (+0.7pp) |
| pair | 2,800,512 | 1,097 | 1,097 | 0 | 65.7% → 65.7% |
| two_pair | 1,338,480 | 363 | 363 | 0 | 83.2% → 83.2% |
| trips | 328,185 | 1,194 | 1,194 | 0 | 58.6% → 58.6% |
| trips_pair | 171,600 | 281 | 281 | 0 | 85.1% → 85.1% |
| three_pair | 114,400 | 1,613 | 1,613 | 0 | 58.6% → 58.6% |
| quads | 14,300 | 545 | 545 | 0 | 75.6% → 75.6% |
| composite | 14,742 | 960 | 960 | 0 | 67.0% → 67.0% |

**Surgical gating PERFECT on full grid as well: 7 of 8 categories
byte-identical to v44.** The entire effect of the 2 ho_v6 features
+ 12,354 new leaves is concentrated in high_only, exactly the gated
target. Net contribution to full-grid mean regret:

  high_only share × within-cat lift = 20.4% × $24/1000h = $4.90/1000h
  ≈ matches the observed $+5/1000h full-grid lift (within rounding).

The "lift is concentrated entirely on the target category" is the
canonical signature of a clean feature ship.

## Phase 5 — Decision 108: PARTIAL POSITIVE / NULL ship

**v46b_dt does NOT replace v44_dt as ML champion.** Production state
unchanged: v56_trips_hybrid as rule chain, v44_dt as ML champion.

**Reasoning:**

1. **Below ship threshold.** Resume-prompt criteria: ≥+$10 = ship,
   ≤+$5 = NULL. Observed: +$5 exactly. Per the stated bar, NULL ship.
2. **No collateral damage.** Surgical gating delivered the
   byte-identity guarantee on 7 of 8 categories. Within-cat high_only
   lift of $24/1000h is real and structurally concentrated.
3. **Strictly-better model.** v46b is ≥ v44 on every category (7
   tied, 1 better). A no-risk +$5/1000h gain would be a defensible
   ship — but at the +$10 bar the user explicitly set, it does not
   clear. NULL recorded per the stated threshold.
4. **Regime-confound theory confirmed.** S72 v46 at depth=32 ml=3
   was −$256/1000h; v46b at depth=36 ml=1 is +$5/1000h. The
   $261/1000h swing is **entirely attributable to the
   hyperparameter regime change**, with feature set held identical.
   This is now the cleanest empirical demonstration of the regime-
   sensitivity principle in the project's history.
5. **H1 SS+ms hypothesis is PARTIALLY CORRECT, NOT WRONG.** The
   S71 setting-rank diagnostic ($147.59 WG STRUCTURE-bucket leak)
   pointed in the right direction; the features ARE addressing real
   leak; they just realize ~16% of the diagnostic-predicted WG
   ($24/$147.59 ≈ 16%). Not enough to ship as a champion, but valid
   signal.

### Hypothesis cascade status (updated)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | SS+ms route quality (2 ho_v6 features) | **TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h full.** Within-cat $24/1000h on high_only; surgical gating perfect; regime-confound theory confirmed. Below +$10 ship bar. |
| H2 | Route-tradeoff comparator (joint vs DS_NONJOINT signed delta) | UNTESTED. Queued for S74. |
| H3 | SS+ms route VARIETY signal (max_top_suit_count) | UNTESTED. Lower priority. |
| H4 | MS_ONLY discriminator (2 features) | UNTESTED. Smaller WG target ($4.39 WG by S71). |
| H5 | Drop-max signal | UNTESTED. Needs H2 comparator to be useful. |

### S74 prescribed direction

**Option A (PREFERRED): H2 route-tradeoff comparator.**
Per SESSION_71_V45_FEATURE_HYPOTHESES.md §6: `ho_v6_route_tradeoff_
joint_minus_nonjoint_g` ∈ −13..+13 signed comparator. The S71
diagnostic identified $147.59 WG STRUCTURE-bucket leak; H1
captured ~16% of it ($24). The remaining ~84% may live in the
joint-vs-nonjoint tradeoff decision, which H2 targets directly. Same
infrastructure (persist → train at depth=36 ml=1 → grade prefix +
full → decision). Expected ~70 min wall.

**Option B (SECONDARY): Gradient boosting (XGBoost / LightGBM)
single-experiment retrain at full feature set.**
Single-tree DT at depth=36 ml=1 may have hit a structural ceiling
where 109 features absorb a 2.26M-leaf tree but additional features
can't add information without restructuring the lower nodes.
Boosting can correct residuals iteratively; this is a one-time
infrastructure investment with potentially much larger payoff than
incremental DT feature engineering. Recommended next-next step if
H2 NULLs.

**Recommended S74 plan:** Option A first (H2 features at S71-style
4-phase playbook). If H2 also lands in "partial positive but
sub-threshold" territory, pivot to Option B.

## Methodology lessons (Session 73)

1. **Regime-confound is the dominant axis of NULL postmortems.**
   v46 NULL at $256 — v46b lift at $5 = a $261 swing from
   hyperparameters alone. The S72 4-phase + new Phase 5 (regime-
   isolation retry) doctrine is empirically validated. **NEVER
   change features AND hyperparams in the same experiment.**
2. **Surgical gating's byte-identity guarantee is regime-locked.**
   v46b confirms the S72 methodology #3 prediction word-for-word:
   "same hyperparameters AND same base feature set" → byte-identity.
   Change either → topology drift. Future feature work that aims
   to ship surgically MUST hold v44's regime constant.
3. **The +$10 ship threshold is conservative but principled.**
   v46b's +$5 lift is technically strictly-better with zero
   downside — and per memory the user's prior shipping bar was as
   low as Rule 19's +$9 (S67). At +$5 we sit just below that, and
   the user (asked) confirmed: hold to +$10 threshold. This codifies
   the bar going forward: feature work must clear +$10 net WG to
   ship as an ML champion, regardless of within-cat magnitude.
4. **Tripwire #1 (feature importance) is more reliable than
   Tripwire #2 (leaf growth) at the saturating regime.** v46b
   leaves: +12,354 (SHIP). v46b feature importance: #75/#105
   (NULL). The grader confirms the feature-importance signal:
   features ARE used (+12K leaves) but at LOW WEIGHT, so the lift
   is small even when the tree absorbs them. **Going forward,
   weight feature-importance tripwires more heavily; treat leaf
   growth as confirmatory only.**
5. **Diagnostic-predicted WG can recover ~10-20%, not 100%.**
   S71 said $147.59 WG STRUCTURE-bucket leak. H1 captured $24
   within-cat = 16%. The diagnostic identifies WHERE the leak is;
   it does NOT promise the magnitude is fully recoverable with
   one feature pair. Calibrate ship expectations to ~20% of
   diagnostic WG for single-pair-feature retrains.
6. **"Speed is not necessary — clarity and perfection is."**
   S73 ran two full graders sequentially (S72 v46 full + S73
   v46b full), each ~17 min wall. Total wall ~50 min for the
   definitive S72+S73 verdict pair. The full-grader within-cat
   data closes the door on S72/S73 — no further re-runs needed
   to know exactly where H1 stood.

## Files (Session 73)

**New code:**
* `analysis/scripts/strategy_v46b_dt.py` — inference; loads
  `data/v46b_dt_model.npz`.
* `analysis/scripts/grade_v46b_dt.py` — head-to-head grader vs v44_dt
  (or v45_dt or v46_dt for direct comparison).

**Data (gitignored, local-only):**
* `data/v46b_dt_model.npz` (1,266.75 MB) — PARTIAL POSITIVE; kept
  as reference; NOT production champion.
* `data/session72/grade_v46_full.log` — S72 v46_dt full grader
  result captured at S73 start (was deferred from S72).
* `data/session73/train_v46b_dt.log`
* `data/session73/grade_v46b_prefix.log`
* `data/session73/grade_v46b_full.log`
* `data/session73/grade_v46_full.log` — duplicate of session72/ copy
  (the in-S73 fresh run, in the S73 directory for completeness).

**Documentation:**
* `SESSION_73_V46B_DT_NULL_REPORT.md` (this file)
* `SESSION_72_V46_DT_NULL_REPORT.md` — appended "Phase 4 — full
  grader (S73 completion)" subsection with the S72 v46_dt
  full-grid table.
* `DECISIONS_LOG.md` — Decision 108 appended.
* `CURRENT_PHASE.md` — rewritten for S74.
* `STRATEGY_GUIDE.md` — Parts 2-6 front-matter date refresh
  (Part 1 SKIPPED; no strategy of record changed this session).

**Production state at end of S73:** UNCHANGED from S72.
* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix).
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h.
* Project rule count: **18**.
* Diagnostic continues: H1 PARTIAL POSITIVE recorded; H2 queued S74.

## Appendix A — Decision 108 text (appended to DECISIONS_LOG.md)

See DECISIONS_LOG.md for the canonical text.

## Appendix B — Why we did NOT ship v46b despite "strictly-better"

A reasonable counter-argument: v46b is mathematically ≥ v44 on every
category (7 tied byte-identical, 1 better). Why not ship the
strictly-better model?

**Answer:** Two reasons, recorded for future calibration.

1. **The +$10 bar exists to filter noise from signal.** n=200
   oracle samples have measurable variance; +$5/1000h is within
   plausible measurement-noise envelope at the per-hand level even
   if the structural improvement is real. The +$10 bar is the
   project's accepted noise margin. Shipping at +$5 sets a
   precedent for "ship anything strictly-better"; that precedent
   would erode the ship bar over many sessions.
2. **Inference cost of 2 extra features + 12K extra leaves is not
   zero.** v46b's npz is 1,266.75 MB vs v44's similar size, and
   it requires the ho_v6 persistence parquet (18.69 MB) to be
   computed per-hand at inference time. For +$5/1000h, this is a
   poor ROI. v44 is sufficient for production until features clear
   the meaningful-improvement bar.

The PARTIAL POSITIVE classification documents the value of the
result for methodology learning (regime-confound confirmed; surgical
gating verified) without contaminating the production strategy of
record.
