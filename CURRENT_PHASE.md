# Current: Sprint 8 — Session 76 cross-category setting-rank diagnostic ships; identifies PAIR as the next ML/rule target ($116.04/1000h STRUCTURE-bucket leak, fresh territory); two_pair / three_pair / trips_pair empirically confirmed as noise-ceiling-limited (Option A candidates); S77 pivots to pair-first deep-drill

S75 closed Option B (gradient boosting at moderate capacity) with a
decisive NULL (−$1,392/1000h full grid). S76 PHASE 1 chose Option B
(categorical diagnostic refresh) as the pivot direction per the cost/
risk ordering (B → D → C → A) and the user directive "speed is not
necessary — clarity and perfection is." PHASE 2 ran a category-
AGNOSTIC setting-rank NOISE/MID/STRUCTURE diagnostic on v44_dt across
all 8 hand categories on the full 6M-hand realistic-mixture grid
(17.9 min wall).

**Result: empirically airtight cross-category partition with three
actionable findings.** Production state UNCHANGED for the **fifth**
consecutive session (S72 NULL, S73 PARTIAL/NULL ship, S74 clean NULL,
S75 boosting NULL, S76 diagnostic ship).

**Full-grid contribution × structure decomposition:**

| Category | v44 $/1000h contribution | STR $ | NOISE $ | STR/TOT |
|---|---:|---:|---:|---:|
| pair | $511.16 | **$116.04** | $206.73 | 22.7% |
| high_only | $381.39 | $147.59 | $79.54 | 38.7% |
| two_pair | $80.82 | $0.86 | $57.73 | **1.1%** |
| trips | $65.18 | $13.14 | $23.08 | 20.2% |
| three_pair | $30.70 | $0.78 | $21.78 | **2.6%** |
| trips_pair | $8.03 | $0.21 | $4.55 | **2.6%** |
| composite | $2.35 | $0.41 | $0.57 | 17.4% |
| quads | $1.30 | $0.20 | $0.40 | 15.4% |
| **TOTAL** | **$1,081.13** | **$279.23** | **$394.38** | **25.8%** |

**Three findings:**

1. **PAIR is the highest-leverage next ML/rule target.** $116.04/1000h STRUCTURE-bucket leak (second-largest absolute), 22.7% of pair's leak is structurally closeable, sharp gap_2nd of 0.2109 (sharper than high_only STR's 0.1063), 59,355 hands in STR bucket, **NEVER drilled with the setting-rank lens.** Pair contributes 47% of v44's total full-grid leak.

2. **two_pair / three_pair / trips_pair are noise-ceiling-limited.** STR/TOT < 3% each; combined NOISE-bucket leak $83.55/1000h. Option A (oracle N=1000 re-eval) is now empirically justified for these specifically (not speculative). Further single-model ML feature engineering on these categories is expected to NULL at the +$10 ship bar.

3. **high_only's STR leak ($147.59) is real but H1-H5 cascade exhausted.** A pair-first drill exploits cleaner residual signal without inheriting an exhausted hypothesis cascade. Marginal-return curve on high_only is diminishing.

**Decision 111: Diagnostic ship; pair-first deep-drill recommended
for S77.** Details in DECISIONS_LOG.md.

> **🎯 IMMEDIATE NEXT ACTION (Session 77): Pair-first cell-taxonomy
> deep-drill**
>
> Apply the S71-style cell-taxonomy diagnostic to pair (analogous to
> drill_v44_high_only_S71.py for high_only):
>
> 1. Design a `compute_hand_structural_minimal_pair()` capturing
>    pair-relevant structural axes:
>    - pair_rank tier (low / mid / high broadway).
>    - pair color: same-suit (JOINT pair) vs different-suit pair.
>    - pair placement: which tier consumes the pair (mid for 5-card
>      hand-strength, bot for Omaha 2+3 leverage, or split).
>    - kicker quality: max non-pair rank and its suit relationship to
>      the pair.
>    - suitedness profile of the 5 non-pair cards (DS/SS/RB/4f).
>    - broadway / wheel structural axes on the 5 non-pair cards.
>
> 2. Cross-tabulate pair STRUCTURE-bucket hands (59,355 hands) against
>    the new cell taxonomy. Identify the top 3-5 cells carrying the
>    $116/1000h leak. Expected output format: per (pair_rank ×
>    pair_color × suitedness) cell, report n hands, total WG, and top
>    mismatch classes (what v44 picks vs oracle).
>
> 3. Hypothesize feature(s) targeting the surfaced cells — analogous
>    to ho_v6 H1 (SS+ms route quality) for high_only. Goal: a 2-3
>    feature pack that captures ≥$30/1000h within-cat lift on the
>    surfaced cells.
>
> 4. (S78 — if any hypothesis surfaces a clean ≥$30/1000h within-cat
>    target) Build feature pack, train v48_dt at depth=36 ml=1 (S73
>    regime LOCKED per S73 methodology lesson #1), grade vs v44 with
>    prefix + full grader. Apply +$10/1000h full-grid ship bar
>    (codified S73, held S74-S76).
>
> **📓 METHODOLOGY (Session 77+):**
>
> 1. **Category-agnostic setting-rank lens is portable.** No per-
>    category structural taxonomy needed for first-pass diagnostic.
>    The S76 drill identified the next target in 18 min wall.
>
> 2. **Full-grid CONTRIBUTION ordering ≠ within-category $/1000h
>    ordering.** Pair contributes $511 vs high_only $381 in
>    full-grid terms; within-category, high_only $1,868 > pair
>    $1,097. Future session-end summaries should report BOTH numbers
>    to keep priority calls calibrated.
>
> 3. **STR/TOT ratio separates closeable-signal from noise-ceiling
>    categories.** > 15% = closeable (high_only, pair, trips,
>    composite, quads); < 5% = noise-dominated (two_pair, three_pair,
>    trips_pair). Belongs as a per-category property in
>    STRATEGY_GUIDE.md going forward.
>
> 4. **gap_2nd × bucket combination is the sharpness metric.** Sharp
>    optimum + STRUCTURE bucket = high-confidence feature-engineering
>    target. Pair STR gap_2nd 0.21 > high_only STR gap_2nd 0.11.
>
> 5. **Plateau width 1.0-1.2 at EPS_REL=0.5% confirms argmax is
>    well-isolated at N=200.** Label noise lives in EV magnitude, not
>    in argmax determinacy. This refines the Option A hypothesis: N=1000
>    re-eval would tighten EV magnitude estimates (reducing noise-
>    bucket WG) but not change argmax structurally.
>
> 6. **+$10 ship bar canonical (S73 codified, held S74-S76).** Fifth
>    consecutive session UNCHANGED production state — the bar is
>    filtering noise from signal as designed.
>
> 7. **"Speed is not necessary — clarity and perfection is."** S76
>    spent 18 min wall on the diagnostic and produced data-supported
>    findings. Avoid the S57-S75 trap of sinking 12+ sessions into a
>    diminishing-return category (high_only H1-H5). The S76 cross-
>    category lens prevents this drift; future diagnostics should
>    re-check the lens after every 3 NULL/partial sessions on a single
>    category.

> **✅ ARTIFACTS produced in S76:**
> 1. `analysis/scripts/drill_v44_setting_rank_all_cats_S76.py` —
>    category-agnostic setting-rank diagnostic; single-pass
>    strategy_v44_dt walk over full 6M-hand grid with per-bucket
>    gap_2nd / plateau-width sampling.
> 2. `data/drill_v44_setting_rank_all_cats_S76_summary.json` (16.0 KB)
>    — per-category bucket distribution, WG decomposition, rank
>    histogram, gap_2nd stats, plateau width.
> 3. `data/session76/drill_v44_setting_rank_all_cats_S76.log`
>    — full console output.
> 4. `data/session76/drill_smoke_5k.log` — 5K-per-cat smoke validation.
> 5. `SESSION_76_DIAGNOSTIC_REPORT.md` — full retrospective +
>    Appendix A pair-first justification + Decision 111 pointer.
> 6. `DECISIONS_LOG.md` — Session 76 Pivot Preamble (Option B chosen)
>    + Decision 111 (diagnostic findings + S77 pair-first
>    recommendation).
> 7. `CURRENT_PHASE.md` — rewritten for S77 (this file).
> 8. `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record
>    changed); Parts 2-6 front-matter date refresh.

> Updated: 2026-05-13 (Session 76 end — cross-category setting-rank
> diagnostic ships; pair identified as next target with $116.04/1000h
> STRUCTURE-bucket leak; two_pair / three_pair / trips_pair confirmed
> noise-ceiling-limited; production state UNCHANGED for fifth
> consecutive session; S77 pivots to pair-first cell-taxonomy
> deep-drill)

---

## Headline state at end of Session 76

**Strategies of record (UNCHANGED from S75):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S76 — pure diagnostic
session, no model trained or rule shipped).

**S76 diagnostic summary:**

| Metric | Value | Notes |
|---|---:|---|
| Hands swept (full grid) | 6,009,159 | matches v44_dt grade scope |
| Wall time | 1,074.8s (17.9 min) | ~5,500 hands/sec steady-state |
| Total $/1000h reconstituted | $1,081.13 | matches v44_dt $/1000h (validates diagnostic) |
| Total STR-bucket $/1000h | $279.23 | 25.8% of total — closeable signal share |
| Total NOISE-bucket $/1000h | $394.38 | 36.5% of total — noise-ceiling share |
| Total MID-bucket $/1000h | $407.34 | 37.7% of total — marginal-headroom share |
| Top STR-bucket cat | high_only ($147.59) | exhausted H1-H5 |
| **Top fresh STR-bucket cat** | **pair ($116.04)** | **S77 target** |
| Top NOISE-bucket cat | pair ($206.73) | Option A also applies |
| Most noise-dominated cats (STR/TOT < 5%) | two_pair, three_pair, trips_pair | Option A territory |

---

## Hypothesis cascade status (updated after S76)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | high_only SS+ms route quality (2 ho_v6 features) | TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h (S73). |
| **H2** | high_only route-tradeoff comparator (1 ho_v7 feature) | TESTED → CLEAN NULL at +$0/1000h (S74). |
| **Option B (S75)** | Gradient boosting at v44 features (depth=6, n_est=200) | TESTED → DECISIVE NULL at −$1,392/1000h. Capacity mismatch. |
| **S76 Option B (this)** | Cross-category setting-rank diagnostic | **SHIPPED → identified pair-first as next target.** |
| H3 | high_only SS+ms route VARIETY signal | UNTESTED. Deprioritized — pair offers fresher signal. |
| H4 | high_only MS_ONLY discriminator | UNTESTED. Deprioritized — small WG target. |
| H5 | high_only Drop-max signal | UNTESTED. Dead (relied on H2 infrastructure). |
| **NEW H6** | **pair structural cell taxonomy** | **QUEUED for S77 PHASE 2.** |
| Option A (S77+) | Oracle-label N=1000 re-evaluation | Empirically justified for two_pair / three_pair / trips_pair specifically; **GATED on cluster access**. |
| Option C (S77+) | Higher-capacity gradient boosting (depth=8-10, n_est=1000+) | Deprioritized — 15-25 hours wall, speculative closure of $1,392 gap. |
| Option D (S77+) | Rule-chain extension (Rule 19) | LATENT — could ride on pair diagnostic findings if a clean cell surfaces. |

**Cascade verdict (updated):** S76 reframed the residual signal map. Pair is the cleanest fresh target; high_only's diminishing-return curve is data-confirmed; the noise-ceiling-limited trio (two_pair / three_pair / trips_pair) is empirically identified. **S77 pivots to pair-first cell-taxonomy deep-drill.**

---

## Resume Prompt (Session 77 — Pair-first cell-taxonomy deep-drill)

```
Resume Session 77 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S76 — pair identified as next
  target with $116.04/1000h STRUCTURE-bucket leak)
- SESSION_76_DIAGNOSTIC_REPORT.md (cross-category setting-rank
  diagnostic findings + Appendix A pair-first justification)
- SESSION_75_V47_XGB_NULL_REPORT.md (decisive boosting NULL, capacity
  mismatch confirmed)
- DECISIONS_LOG.md (latest: Decision 111 — S76 diagnostic + pair-first
  recommendation)
- analysis/scripts/drill_v44_high_only_S71.py (template — adapt for pair)
- analysis/scripts/drill_v44_setting_rank_all_cats_S76.py (S76
  diagnostic for reference)

State (end of S76):
- Cross-category setting-rank diagnostic ran on full 6M-hand grid
  (17.9 min wall). Total v44 leak ($1,081/1000h) decomposes as:
  STRUCTURE $279 (25.8%), NOISE $394 (36.5%), MID $407 (37.7%).
- Pair carries $116.04/1000h STRUCTURE-bucket leak (22.7% of pair's
  total) with sharp gap_2nd 0.2109 (sharper than high_only STR's
  0.1063). 59,355 hands in pair STR bucket. NEVER drilled with the
  setting-rank lens.
- two_pair / three_pair / trips_pair are noise-ceiling-limited
  (STR/TOT < 3% each; combined $83.55/1000h NOISE-bucket leak that
  Option A could partially unlock).
- high_only STR leak ($147.59) remains but H1-H5 cascade exhausted;
  pair offers fresher territory.
- Production UNCHANGED for fifth consecutive session.

USER DIRECTIVE (S59-S76 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship threshold canonical (codified S73, held S74-S76).

DIRECTION FOR SESSION 77 — Pair-first deep-drill:

  PHASE 1 (S77 ~30-45 min) — Design `compute_hand_structural_minimal_pair()`
  capturing pair-relevant axes:
    - pair_rank tier (low / mid / high broadway)
    - pair color (JOINT pair = same suit; non-JOINT = different suits)
    - pair placement option: mid for 5-card Hold'em strength vs bot for
      Omaha 2+3 leverage vs split-pair placements
    - kicker quality: max non-pair rank + its suit relationship to pair
    - suitedness profile of the 5 non-pair cards
    - broadway / wheel axes on the 5 non-pair cards

  PHASE 2 (S77 ~20-40 min) — Adapt drill_v44_high_only_S71.py to
  drill_v44_pair_S77.py. Run on the 2,800,512 pair hands (will be
  faster than high_only's 17.9 min full grid since pair-only is 47%
  of the grid). Output: per (cell × bucket) WG decomposition, top
  mismatch classes, gap_2nd by bucket.

  PHASE 3 (S77 ~10 min) — Hypothesize feature(s) for the top 3-5
  STRUCTURE-bucket cells. Document as PAIR_S77_FEATURE_HYPOTHESES.md
  with: H6 / H7 / H8 candidate definitions, expected within-cat lift,
  derivation arguments, redundancy-with-v44 risk assessment.

  PHASE 4 (S77 ~5 min) — Decision 112 in DECISIONS_LOG.md; CURRENT_PHASE.md
  rewritten for S78 (v48_dt training).

  ACCEPTANCE for Session 77:
  - Pair structural cell taxonomy designed and validated.
  - drill_v44_pair_S77.py shipped with summary JSON + log.
  - Top 3-5 STRUCTURE-bucket cells identified, each with explicit
    n hands + WG + top mismatch class.
  - At least one feature hypothesis (H6) with expected within-cat
    lift ≥$30/1000h queued for S78 v48_dt retrain.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- v44_dt model + features remain unchanged; pair_aug feature packs
  (pair_aug, pair_aug_v2, pair_aug_v5) are reference for the feature-
  taxonomy design.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
