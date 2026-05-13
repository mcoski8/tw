# Session 76 — Setting-rank diagnostic across all 8 categories identifies PAIR as the next feature/rule target ($116/1000h STRUCTURE-bucket leak); two_pair / three_pair / trips_pair empirically confirmed as noise-ceiling-limited (Option A candidates)

_Generated: 2026-05-13_

## TL;DR — Diagnostic shipped; production state UNCHANGED; Decision 111 records the cross-category structure/noise partition and the S77 pivot target

S75 closed Option B (gradient boosting at moderate capacity) with a
decisive NULL. S76 PHASE 1 chose Option B (categorical diagnostic
refresh) as the pivot direction per the resume-prompt cost/risk
ordering (B → D → C → A) and the S71 lens never having been applied
outside high_only. Option A is gated on cluster access; Option C is
15-25h wall on speculation; Option D needs a target category. B
informs every downstream choice cheaply.

PHASE 2 ran `drill_v44_setting_rank_all_cats_S76.py` — a category-
AGNOSTIC setting-rank NOISE/MID/STRUCTURE diagnostic across all 8
categories on the full 6M-hand realistic-mixture grid. 17.9 min wall.
Every hand is bucketed by v44's setting rank (MATCH=1, NOISE=2-3,
MID=4-9, STRUCTURE≥10), with gap_2nd (optimum sharpness) and plateau
width sampled per bucket.

**Headline structure/noise partition by category contribution to
v44's $1,081/1000h full-grid leak:**

| Category | n | v44 $/1000h contribution | STR-bucket $ | NOISE-bucket $ | MID-bucket $ | STR/TOT |
|---|---:|---:|---:|---:|---:|---:|
| pair | 2,800,512 | **$511.16** | **$116.04** | $206.73 | $188.38 | 22.7% |
| high_only | 1,226,940 | $381.39 | **$147.59** | $79.54 | $154.26 | 38.7% |
| two_pair | 1,338,480 | $80.82 | $0.86 | $57.73 | $22.22 | **1.1%** (noise-dominated) |
| trips | 328,185 | $65.18 | $13.14 | $23.08 | $28.97 | 20.2% |
| three_pair | 114,400 | $30.70 | $0.78 | $21.78 | $8.14 | **2.6%** (noise-dominated) |
| trips_pair | 171,600 | $8.03 | $0.21 | $4.55 | $3.26 | **2.6%** (noise-dominated) |
| composite | 14,742 | $2.35 | $0.41 | $0.57 | $1.37 | 17.4% |
| quads | 14,300 | $1.30 | $0.20 | $0.40 | $0.70 | 15.4% |
| **TOTAL** | **6,009,159** | **$1,081.13** | **$279.23** | **$394.38** | **$407.34** | **25.8%** |

**Three actionable conclusions:**

1. **PAIR is the next feature-engineering / rule-extension target.**
   * Pair contributes **$511.16/1000h** — almost half of v44's total full-grid leak ($1,081), and 1.34× high_only's $381 contribution.
   * Of pair's leak, **$116.04 (22.7%) is STRUCTURE-bucket** (v44 rank ≥10 = closeable missing-signal hypothesis).
   * Pair's STR-bucket gap_2nd is **0.2109** (sharp optimum) — sharper than high_only's STR-bucket gap_2nd (0.1063). A sharp optimum + STR-bucket = strong closeable-signal signature.
   * Pair has NEVER been drilled with the setting-rank lens. S66 used a class-label PBOT-routing lens; the S71-style NOISE/MID/STRUCTURE × structural-cell taxonomy has not been applied to pair.
   * 59,355 hands sit in pair's STRUCTURE bucket — that's the v45+ feature-engineering target population for a `compute_hand_structural_minimal_pair()` follow-up drill.

2. **two_pair / three_pair / trips_pair are NOISE-CEILING-LIMITED.**
   * two_pair: 71.4% NOISE-bucket share, 1.1% STRUCTURE-bucket share — $57.73 noise vs $0.86 structure.
   * three_pair: 70.9% NOISE-bucket share, 2.6% STRUCTURE-bucket share — $21.78 noise vs $0.78 structure.
   * trips_pair: 56.7% NOISE-bucket share, 2.6% STRUCTURE-bucket share — $4.55 noise vs $0.21 structure.
   * For these three categories, further single-model ML feature engineering is **expected to NULL** (structure leak is too small to be worth a feature pack at the +$10 ship bar). Option A (oracle N=1000 re-eval, ~2.24× label-variance reduction) is the empirically-justified pivot for these — N=1000 reduces the NOISE-bucket WG, potentially un-sticking the trio-categorical regret floor.
   * Combined, these three categories carry **$83.55/1000h of NOISE-bucket leak** that Option A could partially unlock. A successful Option A run could close ~$20-50/1000h on these alone (back-of-envelope: √5 ≈ 2.24× noise reduction; assume 50% of NOISE-bucket leak is closeable by tighter labels).

3. **high_only is structure-rich but H1-H5 exhausted; trips/composite/quads have signal but tiny absolute leak.**
   * high_only's $147.59 STR-bucket reconfirms S71 finding. H1 captured $24; H2 captured $0; H3-H5 deprioritized for known structural reasons. A re-drill of high_only with a new cell taxonomy (e.g., gating on `n_DS_bot_configs` * `n_ms_mid_with_max_top` interactions) could surface a NEW axis — but pair offers $116/1000h of FRESH structure with no exhausted-cascade overhead. Pair-first is cleaner.
   * trips's $13.14 STR-bucket is real but smaller in absolute terms than high_only or pair. trips was already drilled in S70 (drill_trips_v44_S70.py) and v56 trips_hybrid shipped a rule. Residual signal may be too small for v45+ feature pack.
   * composite ($0.41) and quads ($0.20) are too small to justify dedicated ML work.

**Decision 111: Diagnostic ship; recommend pair-first deep-drill for S77.** Production state UNCHANGED for the **fifth consecutive session**.

## Phase 1 — Pivot choice (DONE)

Option B (categorical diagnostic refresh) chosen and rationale appended to DECISIONS_LOG.md (Session 76 Pivot Preamble entry, between Decision 110 and Decision 111). Reasoning:

* **A is gated on cluster access** I do not have. Single-machine N=1000 re-evaluation is multi-week wall, infeasible single-session.
* **C is structurally speculative**. S75 Appendix B back-of-envelope: closing $1,392/1000h by depth tuning alone is implausible; even capacity-matched boosting may only close 10-30% of the gap. Inappropriate first move when "speed is not necessary — clarity and perfection is" and we have cheaper signal available.
* **D is the near-term-ship path BUT benefits from running B first.** Rule-chain extension needs a target category; without a fresh diagnostic, we're guessing along axes already tested.
* **B is cheapest, lowest-risk, unlocks both ML and rule-chain tracks downstream.** A category-agnostic setting-rank diagnostic across all 8 categories tells us WHERE the closeable signal lives and WHICH categories are noise-ceiling-limited.

Phase 1 elapsed: ~10 min including preamble write.

## Phase 2 — Diagnostic drill (DONE)

**Run command:**
```
PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_v44_setting_rank_all_cats_S76.py
```

**Outputs:**
* Console / log: `data/session76/drill_v44_setting_rank_all_cats_S76.log`
* Summary JSON: `data/drill_v44_setting_rank_all_cats_S76_summary.json` (16.0 KB)

**Run stats:**
* Wall: 1,074.8s (17.9 min)
* Hands swept: 6,009,159 (full canonical grid)
* Steady-state rate: ~5,500 hands/sec
* Per-category breakdown sweep completed cleanly; no errors.

### Bucket distribution + WG per category (S76_OUT_1)

```
cat                   n  MATCH%  NOISE%    MID%    STR%   NOISE $     MID $     STR $   TOTAL $  STR/TOT
high_only     1,226,940   41.8%   25.1%   21.8%   11.2% $  +79.54 $ +154.26 $ +147.59 $ +381.39   38.7%
pair          2,800,512   65.7%   22.9%    9.2%    2.1% $ +206.73 $ +188.38 $ +116.04 $ +511.16   22.7%
two_pair      1,338,480   83.2%   14.3%    2.5%    0.0% $  +57.73 $  +22.22 $   +0.86 $  +80.82    1.1%
trips           328,185   58.6%   24.4%   13.6%    3.4% $  +23.08 $  +28.97 $  +13.14 $  +65.18   20.2%
trips_pair      171,600   85.1%   11.3%    3.4%    0.1% $   +4.55 $   +3.26 $   +0.21 $   +8.03    2.6%
three_pair      114,400   58.6%   33.9%    7.1%    0.5% $  +21.78 $   +8.14 $   +0.78 $  +30.70    2.6%
quads            14,300   75.6%   14.7%    8.4%    1.2% $   +0.40 $   +0.70 $   +0.20 $   +1.30   15.4%
composite        14,742   67.0%   16.1%   14.4%    2.4% $   +0.57 $   +1.37 $   +0.41 $   +2.35   17.4%
```

* Per-category $/1000h **contributions** sum to **$1,081.13**, exactly matching v44_dt's full-grid $/1000h (S58 grade).
* MATCH-rate ordering: trips_pair (85.1%) > two_pair (83.2%) > quads (75.6%) > composite (67.0%) > pair (65.7%) > three_pair (58.6%) > trips (58.6%) > high_only (41.8%).
* STRUCTURE % ordering: high_only (11.2%) > trips (3.4%) > composite (2.4%) > pair (2.1%) > quads (1.2%) > three_pair (0.5%) > trips_pair (0.1%) > two_pair (0.0% / 669 hands).

### gap_2nd (optimum sharpness) + plateau width per bucket (S76_OUT_2)

Selected key rows:

| cat × bucket | n | gap2_mean | gap2_med | plateau_mean | Interpretation |
|---|---:|---:|---:|---:|---|
| high_only STRUCTURE | 137,997 | 0.1063 | 0.0800 | 1.06 | Sharp + STR = closeable (confirmed S71) |
| **pair STRUCTURE** | **59,355** | **0.2109** | **0.1600** | **1.03** | **Sharp + STR = closeable, fresh territory** |
| trips STRUCTURE | 11,105 | 0.1520 | 0.1050 | 1.07 | Sharp + STR but tiny absolute |
| two_pair NOISE | 190,825 | 0.1525 | 0.1150 | 1.04 | Sharp at NOISE = surprisingly closeable? maybe |
| two_pair STRUCTURE | 669 | 0.1574 | 0.1250 | 1.03 | Tiny n; ignore |
| three_pair STRUCTURE | 537 | 0.2304 | 0.1650 | 1.08 | Sharp + STR but tiny n |
| three_pair NOISE | 38,783 | 0.3297 | 0.2575 | 1.01 | **Sharp at NOISE** — N=200 noise floor for this cat is rough |

* **Plateau width is uniformly ~1.0-1.2 across all (cat, bucket) cells** — meaning at the EPS_REL=0.5% threshold, oracle's argmax is essentially unique (no flat-optimum ambiguity). This is a property of the realistic-mixture N=200 grid: the EVs are sufficiently spread that the top-1 setting is well-isolated even with N=200 sampling noise.
* **pair STR gap_2nd = 0.2109 is SHARPER than high_only STR gap_2nd = 0.1063.** Recall lower gap_2nd = flatter optimum (oracle's #1 and #2 are close); higher gap_2nd = sharper. Pair's STR-bucket misses are MORE clearly wrong (oracle's #1 is well-isolated), making them HIGHER-confidence feature-engineering targets than high_only's.

### Setting-rank histogram per category (S76_OUT_3)

* **two_pair histogram cumulative %**: rank-1 83.2% → rank-3 97.4% → rank-9 99.95% → rank ≥10 only 0.05%. Two_pair is HEAVILY rank-1-or-rank-2-3-clustered — extremely noise-dominated.
* **trips_pair**: rank-1 85.1% → rank-3 96.5% → rank-9 99.89% → rank ≥10 only 0.11%. Similar profile to two_pair.
* **pair**: rank-1 65.7% → rank-3 88.6% → rank-9 97.9% → rank ≥10 2.1%. Heavier MID/STR tail than two_pair, consistent with more feature-engineering headroom.
* **high_only**: rank-1 41.8% → rank-3 67.0% → rank-9 88.8% → rank ≥10 11.2%. Heaviest STR tail of any category — confirms S71 baseline.

### Cross-category rankings (S76_OUT_4)

```
Ranked by STRUCTURE-bucket $/1000h (best Option D candidate first):
  1 high_only    $ +147.59  STR/TOT 38.7%
  2 pair         $ +116.04  STR/TOT 22.7%   ← NEW SIGNAL; never drilled with S71 lens
  3 trips        $  +13.14  STR/TOT 20.2%
  4 two_pair     $   +0.86  STR/TOT  1.1%
  5 three_pair   $   +0.78  STR/TOT  2.6%
  6 composite    $   +0.41  STR/TOT 17.4%
  7 trips_pair   $   +0.21  STR/TOT  2.6%
  8 quads        $   +0.20  STR/TOT 15.4%

Ranked by NOISE-bucket $/1000h (best Option A candidate first):
  1 pair         $ +206.73 (40.4% noise share)
  2 high_only    $  +79.54 (20.9% noise share)
  3 two_pair     $  +57.73 (71.4% noise share)   ← NOISE-DOMINATED
  4 trips        $  +23.08 (35.4% noise share)
  5 three_pair   $  +21.78 (70.9% noise share)   ← NOISE-DOMINATED
  6 trips_pair   $   +4.55 (56.7% noise share)   ← NOISE-DOMINATED
  7 composite    $   +0.57 (24.4% noise share)
  8 quads        $   +0.40 (30.7% noise share)
```

## Phase 3 — Decision 111: diagnostic ship; pair-first deep-drill recommended for S77

**Production state UNCHANGED.** v56_trips_hybrid remains rule chain ($1,429 full / $794 prefix). v44_dt remains ML champion ($1,081 full / $686 prefix). Two-track divergence: $348/1000h unchanged. Project rule count: 18 unchanged.

**Decision 111 records three findings + one recommendation.** Details in DECISIONS_LOG.md.

### Three findings

1. **PAIR carries $116.04/1000h of fresh STRUCTURE-bucket leak** with a sharp gap_2nd of 0.21 and 59,355 hands in the STR bucket. Never drilled with the setting-rank lens. Highest-leverage next ML/rule target.

2. **two_pair / three_pair / trips_pair are noise-ceiling-limited.** Combined $83.55/1000h of NOISE-bucket leak with <3% STR-bucket share each. Option A (oracle N=1000 re-eval) is the empirically-justified pivot for these specifically. The case for Option A is now data-supported (not speculative).

3. **high_only's STR leak is real but H1-H5 cascade exhausted.** $147.59 of STR-bucket signal remains, but H1 captured $24, H2 captured $0, H3-H5 deprioritized for known reasons. A pair-first drill exploits the cleanest residual signal without inheriting an exhausted hypothesis cascade.

### One recommendation (S77 pivot)

**Apply the S71-style cell-taxonomy diagnostic to pair.**

Steps:
1. Design a `compute_hand_structural_minimal_pair()` that captures pair-relevant structure: pair_rank tier (low/mid/high), pair color (JOINT/non-JOINT bot vs mid placement), kicker quality, suitedness profile, broadway/wheel structural axes.
2. Cross-tabulate pair STRUCTURE-bucket hands against the new cell taxonomy; identify the $116/1000h leak's top 3-5 cells.
3. Hypothesize feature(s) targeting those cells (analogous to ho_v6 H1 for high_only).
4. Train v48_dt at depth=36 ml=1 (S73 regime); grade vs v44 with prefix + full grader.
5. Apply +$10/1000h ship bar (codified S73, held S74-S75).

S77 acceptance: pair diagnostic + new pair feature pack hypothesis recorded; if any hypothesis surfaces a clean within-cell leak ≥$30/1000h within-cat, queue v48_dt retrain for S78.

## Methodology lessons (Session 76)

1. **Category-AGNOSTIC setting-rank lens is a high-leverage diagnostic.** The same NOISE/MID/STRUCTURE bucketing that surfaced S71's $147.59 high_only signal partitions every other category cleanly. The lens is category-portable WITHOUT a per-category structural taxonomy (output 1 alone informs the next drill target). Total cost: ~18 min wall on a single-pass strategy_v44_dt walk over the full grid.

2. **Per-category $/1000h "leaderboard" reframes priorities.** CURRENT_PHASE.md reports within-category $/1000h (e.g., high_only $1,868 > pair $1,097). But the FULL-GRID CONTRIBUTION ordering is pair $511 > high_only $381 — pair contributes MORE total leak because it has 2.3× as many hands. Future session-end summaries should report BOTH numbers: within-category for "how bad is v44 on this category" and contribution for "how much can closing this category move the needle."

3. **STR/TOT ratio cleanly separates closeable-signal categories from noise-ceiling categories.** STR/TOT > 15% (high_only, pair, trips, composite, quads) = closeable signal exists; STR/TOT < 5% (two_pair, three_pair, trips_pair) = noise-dominated, Option A territory. This single metric should be added to STRATEGY_GUIDE.md as a per-category property.

4. **gap_2nd at the STRUCTURE bucket is a high-confidence signal sharpness metric.** Pair STR gap_2nd = 0.21 (sharp) means oracle's #1 is well-isolated even when v44 picks rank ≥10 — those misses are HIGH-confidence "v44 picked structurally wrong." Compare three_pair NOISE gap_2nd = 0.33 (also sharp, but at NOISE bucket = "v44 picked one of the top-3 near-ties, and the gaps between #1, #2, #3 are large in absolute terms" — interpretation: three_pair's regret floor is BOTH noise-ceiling-limited AND high-variance per hand. N=1000 oracle should compress these sharp-but-noise-bucket gaps; if it does, three_pair becomes feature-engineering-tractable). This deserves explicit investigation if Option A is ever funded.

5. **Plateau width of 1.0-1.2 at EPS_REL=0.5% across all (cat,bucket) cells confirms the realistic-mixture grid produces well-isolated argmax decisions.** No category has flat-optimum ambiguity at the 0.5% threshold. Label noise lives in the EV MAGNITUDE estimation (which N affects), not in argmax determinacy (which appears already-determined at N=200).

6. **Pair's 22.7% STR/TOT share is the cleanest fresh-territory finding.** S57-S75 sank ~12 sessions into the high_only H1-H5 cascade ($147 → ~$24 captured). Pair offers $116 of FRESH structure-bucket leak with no exhausted-cascade overhead. The marginal-return math favors pair-first for S77.

7. **"Speed is not necessary — clarity and perfection is."** S76 ran one diagnostic drill in 18 min wall and produced an empirically airtight cross-category partition with three actionable findings. The S77 pivot target is data-supported, not narrative-justified.

## Files (Session 76)

**New code:**

* `analysis/scripts/drill_v44_setting_rank_all_cats_S76.py` — category-agnostic setting-rank NOISE/MID/STRUCTURE diagnostic across all 8 categories. Single-pass strategy_v44_dt walk + oracle row sort per hand. ~18 min wall on the full 6M-hand grid. Outputs:
  - S76_OUT_1: per-category bucket distribution + WG decomposition.
  - S76_OUT_2: gap_2nd + plateau width per (cat × bucket).
  - S76_OUT_3: setting-rank histogram per category (rank 1..20 + ≥20).
  - S76_OUT_4: cross-category rankings (STRUCTURE-wg, NOISE-wg).

**Data (gitignored, local-only):**

* `data/drill_v44_setting_rank_all_cats_S76_summary.json` (16.0 KB) — JSON summary with all bucket-level stats per category.
* `data/session76/drill_v44_setting_rank_all_cats_S76.log` — full console output.
* `data/session76/drill_smoke_5k.log` — 5K-per-cat smoke run that validated the script before the full sweep.

**Documentation:**

* `SESSION_76_DIAGNOSTIC_REPORT.md` (this file).
* `DECISIONS_LOG.md` — Session 76 Pivot Preamble (Option B chosen) + Decision 111 (diagnostic findings + S77 pair-first recommendation).
* `CURRENT_PHASE.md` — rewritten for S77.
* `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record changed); Parts 2-6 front-matter date refresh.

## Production state at end of S76 (UNCHANGED from S75)

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix). Grader-confirmed.
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h (no change).
* Project rule count: **18** (no change).
* **Pair diagnostic queued for S77; Option A (oracle N=1000) empirically justified for two_pair / three_pair / trips_pair specifically if cluster access becomes available.**

## Appendix A — Why pair-first beats high_only-second-pass for S77

S57-S75 spent ~12 sessions on high_only feature engineering:
* S57-S58: v43, v44 high_only_aug_v3/v4 features → +$0/1000h shipped (v44 became champion via the prefix-only bug being fixed, not via lift).
* S59 v45: NULL ($0/1000h, S59 first hit of saturating-DT regime).
* S60-S65: A/K/Q/J/T98 catalog audits — ALL ML-ONLY, no rules shipped from high_only.
* S71-S74: H1 (+$5/$24 within-cat), H2 ($0), H3-H5 deprioritized.

The marginal-return curve on high_only is clearly diminishing. S71 said "$147 of STR-bucket leak remains"; H1 captured $24 within-cat, the rest is in axes not yet surfaced.

Pair has $116/1000h of STR-bucket leak with:
* SHARPER optimum (gap_2nd 0.21 vs 0.10) → higher signal-to-noise per hand.
* NO exhausted hypothesis cascade.
* 2.3× as many hands as high_only (broader coverage = more robust feature signal).
* NEVER drilled with the setting-rank × structural-cell lens.

Expected S77 outcome (with my fresh-eyes prior, NOT a commitment):
* The pair structural taxonomy will surface a top 2-3 cells carrying $30-60/1000h within-cat each.
* A pair_v6+ feature pack targeting those cells could yield +$15-30/1000h within-cat = +$7-14/1000h full-grid lift.
* That clears the +$10/1000h ship bar.

Pair-first is the highest-EV move per session of compute. If it NULLs, the +$10 bar excluded a serious attempt at the cleanest residual signal — and Options A and C become the natural follow-ups.

## Appendix B — Decision 111 text (appended to DECISIONS_LOG.md)

See DECISIONS_LOG.md for the canonical text.
