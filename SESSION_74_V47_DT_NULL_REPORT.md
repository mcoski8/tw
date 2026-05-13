# Session 74 — v47_dt NULL: H2 route-tradeoff comparator NULL-grades at depth=36 ml=1; "derivable in 2 splits" trap empirically confirmed; ML retrain track exhausted at v44 saturating regime

_Generated: 2026-05-13_

## TL;DR — H2 NULL; v47 byte-identical to v44 on prefix and effectively zero-delta on full grid; S71's "derivable in 2 splits" risk has materialized; ML feature-engineering track exhausted at saturating regime

S73 v46b_dt (H1 SS+ms route quality at depth=36 ml=1) landed +$5/1000h
full — PARTIAL POSITIVE but below the +$10 ship bar. S74 tested H2
(route-tradeoff comparator `ho_v7_route_tradeoff_joint_minus_nonjoint_g`,
1 signed scalar) at the SAME regime (depth=36 ml=1, LOCKED per S73
methodology lesson #1). Both tripwires fired STRONG NULL:

* **Feature importance:** #103 / 108 (0.01%) — deeper in tail than
  H1's #75/#105.
* **Leaf growth:** +1 vs v44's 2,248,173 — essentially zero. (H1
  was +12,354; v45 was +9 = prior NULL; v3 ship was +K-many.)

Prefix grader confirmed **byte-identical** to v44 on all 7 prefix
categories ($686 → $686). Full grader confirmed **$1,081/1000h identical
to v44** across all 8 per-category $/1000h values (high_only, pair,
two_pair, trips, trips_pair, three_pair, quads, composite — every
single one matches v44 to the dollar). pct_opt differs by 3 hands
out of 6,009,159 (3,893,731 → 3,893,734, +0.00005pp); p90 = 0.390 =
v44; p99 = 0.970 = v44. The +1 leaf signature manifests as 3-hand
divergence at zero net regret.

**Decision 109: NULL ship.** v44_dt remains ML champion at $1,081/1000h
full / $686 prefix. v56_trips_hybrid remains rule chain at $1,429 full
/ $794 prefix. Production state UNCHANGED for the third consecutive
session (S72 NULL, S73 PARTIAL POSITIVE NULL ship, S74 NULL).

The S71 author flagged this exact failure mode: "But could fall into
the 'derivable in 2 splits' trap." H2 is the comparator of two values
the DT already has access to (JOINT mid_high via ho_v3; non-max DS+ms
top via ho_v4) plus the broad DS_NONJOINT top — and at depth=36 with
saturating leaves (2.7 rows/leaf), the DT can already extract whatever
information the comparator compresses through axis-aligned splits.
v47's leaf count rising by exactly 1 leaf is the cleanest possible
empirical signature: the DT used the new feature for ONE split.

| Metric | v44_dt | v46b_dt (S73 H1) | v47_dt (S74 H2) | Δ v47 vs v44 |
|---|---:|---:|---:|---:|
| Full grid pct_opt | 64.80% | 64.92% | **64.80%** | **+0.00005pp (3 hands of 6M)** |
| Full grid $/1000h | $1,081 | $1,076 | **$1,081** | **+$0 (identical)** |
| Full grid p90 regret | 0.390 | 0.385 | **0.390** | tied |
| Full grid p99 regret | 0.970 | 0.970 | **0.970** | tied |
| Prefix grid $/1000h | $686 | $686 | **$686** | **+$0 (byte-identical)** |
| Leaves | 2,248,173 | 2,260,527 | **2,248,174** | **+1 only** |
| Features | 107 | 109 | 108 | +1 ho_v7 |
| Depth / ml | 36 / 1 | 36 / 1 | **36 / 1** | same as v44 |
| Training fit | — | 610.0s | 567.1s | — |
| Top-importance rank | n/a | #75 + #105 | **#103** | tail |

## Phase 1 — ho_v7 feature design + persistence (DONE)

**Spec** (per SESSION_71_V45_FEATURE_HYPOTHESES.md §6, originally
labeled H3; renumbered to H2 in S73 CURRENT_PHASE.md):

```
ho_v7_route_tradeoff_joint_minus_nonjoint_g    int8, range -14..+14
  = best_JOINT_mid_high  -  best_DS_NONJOINT_top

where:
  best_JOINT_mid_high  = max(mid_high) across (top=max_rank,
                          DS bot, ms mid) configs.  0 if none.
  best_DS_NONJOINT_top = max(top_rank) across (DS bot, NOT JOINT)
                          configs.  0 if none.
```

DS_NONJOINT mirrors drill_high_only_v43_threshold.py's binary
partition: "DS bot but NOT (top=max AND mid suited)". Broader than
ho_v4's `topNonMax_DS_ms` (which is the strict subset where mid IS
still suited but top ≠ max). The broad form is non-derivable from
v44+ho_v3+ho_v4.

**Files:**

* `analysis/scripts/high_only_aug_v7_features_gated.py` — 1 feature,
  signed int8. 5 smoke tests; all pass.
* `analysis/scripts/persist_high_only_aug_v7_gated.py` — 6,009,159
  canonical hands, 66.3s persist time, **18.59 MB** zstd parquet.

**Empirical distribution** (6M hands, parquet readback):

* 0: 5,063,643 hands (84.27%) — gated OR no DS achievable.
* −14: 415,800 (6.92%) — JOINT not achievable, top=A DS_NONJOINT.
* −13: 244,860 (4.07%) — JOINT not achievable, top=K DS_NONJOINT
  (or max_rank=K case).
* −12 to −1: 281,156 (4.67%) — graded negative.
* Positive values: **zero**.

The all-non-positive distribution confirms my Phase-1 design analysis:
in (4,2,0,0) and (2,2,2,0) suit structures where JOINT is achievable,
the best DS_NONJOINT top always reaches at least the JOINT mid_high;
in (2,2,1,1), (3,2,1,0), (3,3,0,0) structures, JOINT is not achievable
and DS_NONJOINT top = max_rank. Positive ho_v7 values require non-
canonical suit packings that high_only hands don't exhibit. The
feature carries information in the GRADIENT among negative values
(weak signal: ho_v7=−14 vs −1), not in a sign distinction.

## Phase 2 — v47_dt training at depth=36 ml=1 (DONE — NULL tripwires)

`PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v47_dt.py
--max-depth 36 --min-samples-leaf 1 --output data/v47_dt_model.npz`

* Fit time: 567.1s (vs v46b's 610.0s; same regime — v47 is FASTER
  because the DT essentially found no new splits to exploit).
* Leaves: **2,248,174** (vs v44's 2,248,173 → **+1 leaf**).
* Depth: 36.
* Model file: **1,260.45 MB** (vs v46b's 1,266.75 MB; ~6 MB smaller,
  confirming the +1-leaf signature).

**Tripwire #1 — feature importance (NULL signal):**

```
#103 ho_v7_route_tradeoff_joint_minus_nonjoint_g       0.01%
```

Deeper in the tail than v46b's #75 (and tied with #105 in absolute
%). At the S71-stated tripwire threshold (top-50 = ship, #50-100 =
ambiguous, #100+ = NULL), v47 falls firmly into the NULL range.
S73 methodology lesson #3 ("weight feature-importance tripwires more
heavily; treat leaf growth as confirmatory only") gets confirmed
here: the tripwires now CONCUR, both NULL.

**Tripwire #2 — leaf growth (NULL signal):**

v44: 2,248,173 leaves. v47: 2,248,174 leaves. **+1 leaf.**

This is the single most decisive leaf-growth signature in the
project's history of feature-design retrains:

| Retrain | New leaves vs v44 | Tripwire |
|---|---:|---|
| v3 (ho_v3 DS+ms, S57) | +K-many | SHIP (+$79) |
| v45 (ho_v5 broadway pairs, S60) | +9 | NULL |
| v46 (ho_v6 SS+ms, depth=32 ml=3) | n/a (1.10M total) | regime confound |
| v46b (ho_v6 SS+ms, depth=36 ml=1) | +12,354 | SHIP (but full +$5 PARTIAL) |
| **v47 (ho_v7 comparator, depth=36 ml=1)** | **+1** | **NULL** |

A +1 leaf delta means the DT found exactly one split where the
comparator gave it new partitioning power. Across 2.25M leaves, this
is structural background noise.

The 567s fit time vs v46b's 610s is itself a tripwire signal: a feature
that opens many new splits SLOWS fitting (more nodes to evaluate);
v47's faster fit confirms the DT scarcely used the new feature.

## Phase 3 — prefix grader v47 vs v44 (DONE — BYTE-IDENTITY)

**v47 vs v44 on prefix grid (500K canonical hands, n=1000 oracle):**

| strategy | pct_opt | $/1000h | p90 | wall |
|---|---:|---:|---:|---:|
| v44_dt (baseline) | 67.13% | $686 | 0.264 | 70s |
| v47_dt | **67.13%** | **$686** | **0.264** | 71s |
| **Δ** | **0.00pp** | **+$0** | tied | — |

**Per-category prefix breakdown — BYTE-IDENTICAL:**

| category | n hands | v44 $/1000h | v47 $/1000h | Δ |
|---|---:|---:|---:|---:|
| pair | 215,162 | 595 | 595 | 0 |
| two_pair | 204,275 | 663 | 663 | 0 |
| trips | 25,245 | 1,086 | 1,086 | 0 |
| trips_pair | 25,943 | 727 | 727 | 0 |
| three_pair | 25,614 | 1,143 | 1,143 | 0 |
| quads | 1,100 | 783 | 783 | 0 |
| composite | 2,661 | 1,226 | 1,226 | 0 |

The prefix grid contains 0 high_only canonical IDs (S72 finding),
so ho_v7 evaluates to 0 for all 500K hands. With +1 leaf and same
regime + same base features, the v47 tree topology is byte-identical
to v44 on prefix categories. Surgical gating's byte-identity
guarantee holds — but here the guarantee is a *floor*, not a ceiling:
v47 doesn't BREAK byte-identity, but the +1 leaf hint shows it also
adds essentially nothing.

## Phase 4 — full grader v47 vs v44 (DONE — DECISIVE NULL)

**v47 vs v44 full grid (6,009,159 hands, n=200 realistic 70/25/5):**

`PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v47_dt.py --grid full
--baseline v44` (data/session74/grade_v47_full.log).

| strategy | pct_opt | $/1000h | p90 | p99 | wall |
|---|---:|---:|---:|---:|---:|
| v44_dt (baseline) | 64.80% | $1,081 | 0.390 | 0.970 | 1059s |
| v47_dt | **64.80%** | **$1,081** | **0.390** | **0.970** | 1137s |
| **Δ** | **+0.00005pp** | **+$0** | tied | tied | — |

The 3-hand pct_opt delta (3,893,731 → 3,893,734) is the empirical
fingerprint of the +1 leaf: a handful of hands route slightly
differently through the new leaf branch, but the routing change
produces zero net regret. The +1 leaf is structurally inert at the
grader resolution.

**Per-category full-grid breakdown — EFFECTIVELY BYTE-IDENTICAL:**

| category | n hands | v44 $/1000h | v47 $/1000h | Δ | v44 pct_opt | v47 pct_opt |
|---|---:|---:|---:|---:|---:|---:|
| high_only | 1,226,940 | 1,868 | **1,868** | **0** | 41.8% | 41.8% |
| pair | 2,800,512 | 1,097 | **1,097** | **0** | 65.7% | 65.7% |
| two_pair | 1,338,480 | 363 | **363** | **0** | 83.2% | 83.2% |
| trips | 328,185 | 1,194 | **1,194** | **0** | 58.6% | 58.6% |
| trips_pair | 171,600 | 281 | **281** | **0** | 85.1% | 85.1% |
| three_pair | 114,400 | 1,613 | **1,613** | **0** | 58.6% | 58.6% |
| quads | 14,300 | 545 | **545** | **0** | 75.6% | 75.6% |
| composite | 14,742 | 960 | **960** | **0** | 67.0% | 67.0% |

**Every per-category $/1000h matches v44 to the dollar.** Including
the on-target high_only category — where v46b (H1) earned a $24/1000h
within-cat lift. H2 generates **zero** within-cat lift on high_only.

This is the cleanest possible empirical NULL: the DT didn't just
fail to clear the +$10 ship bar — it generated zero signal on the
gated target category itself.

## Phase 5 — Decision 109: NULL ship; H2 dead; pivot direction

**v47_dt does NOT replace v44_dt as ML champion.** Production state
unchanged: v56_trips_hybrid as rule chain, v44_dt as ML champion.

**Reasoning:**

1. **Both tripwires NULL** — first time in the diagnostic sequence
   that feature importance AND leaf growth signals concur. v45 had
   +9 leaves but feature importance was higher; v46/v46b had mixed
   signals. v47's +1 leaf + #103 importance is unambiguous.
2. **Prefix grader byte-identical** to v44 — confirms zero net signal
   in the 7 non-high_only categories (which all evaluate ho_v7 to 0).
3. **Full grader $0 delta** — Δ = +$0 ≤ +$5 confirms H2 dead per
   the stated decision matrix. Within-cat high_only: $1,868 → $1,868
   (zero lift on the gated target). v46b earned +$24 within-cat at
   the same regime with the H1 features — H2 captures zero.
4. **"Derivable in 2 splits" trap empirically confirmed.** S71 wrote:
   "the COMPARISON might compress them at saturation. But could fall
   into the 'derivable in 2 splits' trap." The v47 result is exactly
   that — at the saturating regime, the DT has ample headroom (depth=36,
   2.25M leaves, 2.7 rows/leaf) to extract whatever the comparator
   compresses by combining axis-aligned splits on existing features
   (ho_v3 max_mid_high, ho_v4 topNonMax_DS_ms_max_top_rank, etc.).
   The +1 leaf delta is the empirical fingerprint of "comparator
   compresses zero new information beyond 2 existing splits."
5. **H2 hypothesis FALSIFIED at saturating-DT regime.** The route-
   tradeoff comparator is not productive as a DT feature. It may
   still be productive in a gradient-boosting regime where iterative
   residual correction can exploit compressed comparators that DT
   axis-aligned splits cannot.

### Hypothesis cascade status (updated)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | SS+ms route quality (2 ho_v6 features) | **TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h full.** Within-cat $24/1000h. |
| **H2** | Route-tradeoff comparator (1 ho_v7 feature) | **TESTED → NULL at +1 leaf, #103 importance. Derivability trap confirmed.** |
| H3 | SS+ms route VARIETY signal (max_top_suit_count) | UNTESTED. Lower priority — likely similar saturation ceiling. |
| H4 | MS_ONLY discriminator (2 features) | UNTESTED. Smaller WG target ($4.39 WG by S71). |
| H5 | Drop-max signal | UNTESTED. Needed H2 comparator infrastructure — but H2 is dead, so H5 dies too. |

**Cascade verdict:** The DT-with-engineered-features track is
exhausted at v44's saturating regime. H1 captured 16% of diagnostic
WG; H2 captured 0%; H3/H4/H5 are likely <H1's already-marginal payoff.
**Pivot is mandatory.**

### S75 prescribed direction — Option B (gradient boosting)

The S74 acceptance criteria allowed deferring Option B to a later
session if H2 was tested fully. H2 is now tested fully and dead.
S75 pivots to gradient boosting:

**v47_xgb / v47_lgbm**, single-experiment retrain at v44's feature
set (107 features) + ho_v7 (1 feature) = 108-feature X, 105-target Y.
Hyperparameters: n_estimators=500-1000, max_depth=8-12,
learning_rate=0.05, early stopping on validation split.

Hypothesis: boosting's iterative residual correction can exploit
the comparator (and possibly the SS+ms features) that DT axis-aligned
splits cannot. A single boosting model with ~108-110 features may
unlock the structural ceiling that the saturating DT has hit.

**Alternate path** (lower priority): grid label re-evaluation at
N=1000 (vs current N=200). If the saturating DT has hit a label-noise
ceiling, more oracle samples per hand may un-stick the regret floor.
~10× compute cost; defer.

## Methodology lessons (Session 74)

1. **Both tripwires concur for NULL at +1 leaf + tail importance.**
   v47 is the cleanest "dead feature" signal in the project's history.
   The +1 leaf delta is so small that it likely came from random tie-
   breaking in the DT splitter on a single decision; literally any
   feature would have produced ≥1 leaf delta. **Going forward, treat
   ≤+10 leaves as NULL signal at saturating regime** (was ≤+1K in
   the S59 doctrine; tightening to ≤+10 captures the v47 fingerprint).
2. **"Derivable in 2 splits" trap is now a confirmed failure mode.**
   Comparator features that combine two existing axes via subtraction
   add no information at saturating DT regime. v44's 2.25M leaves
   at 2.7 rows/leaf give the DT ample headroom to combine 2 splits
   axis-by-axis. Future feature design must target NON-derivable
   axes (e.g., H1's SS+ms which was a genuinely new suit-counting
   primitive) — or pivot to a non-DT model class.
3. **Fitter wall-time IS a tripwire.** v47 fit 567s vs v46b's 610s
   (same regime). A new feature that the DT scarcely uses SPEEDS
   fitting (fewer candidate splits to evaluate per node); a feature
   that opens many new splits SLOWS fitting. Going forward, fit-time
   delta vs the previous baseline at same regime is a 3rd tripwire,
   read jointly with feature importance and leaf growth.
4. **The H1→H2 cascade confirms diminishing returns on alternate-
   axis feature engineering at the saturating regime.** H1 (genuinely
   new SS axis): +12K leaves, +$5 full (PARTIAL). H2 (comparator on
   existing axes): +1 leaf, $0 prefix (NULL). H3/H4/H5 are predicted
   to fall between these two — i.e., either NULL or partial-positive
   sub-threshold. **No further single-DT feature work is justified
   without a major architectural change** (different feature primitives
   from a different diagnostic, OR pivot to boosting).
5. **The S73 "+$10 ship bar" combined with the saturating-DT track's
   marginal returns has effectively closed the DT-feature-engineering
   chapter.** Two consecutive sessions (S73, S74) have run the full
   4-phase playbook — one PARTIAL POSITIVE / NULL ship, one clean
   NULL. The +$10 bar excludes both. Continuing this track would burn
   ~70 min/session for diminishing-or-zero return. S75 must pivot.
6. **"Speed is not necessary — clarity and perfection is."** The
   sequential prefix + full grader at the v44 saturating regime
   produced an empirically airtight NULL verdict in S74. No re-runs
   needed; the case for H2 is closed.

## Files (Session 74)

**New code:**

* `analysis/scripts/high_only_aug_v7_features_gated.py` — 1 feature,
  signed int8; 5 smoke tests.
* `analysis/scripts/persist_high_only_aug_v7_gated.py`
* `analysis/scripts/train_v47_dt.py` — depth=36 ml=1 (regime LOCKED).
* `analysis/scripts/strategy_v47_dt.py` — inference; loads v47_dt_model.npz.
* `analysis/scripts/grade_v47_dt.py` — head-to-head grader vs v44/v45/v46/v46b.

**Data (gitignored, local-only):**

* `data/feature_table_high_only_aug_v7_gated.parquet` (18.59 MB).
* `data/v47_dt_model.npz` (1,260.45 MB) — NULL ship; reference only;
  NOT production champion.
* `data/session74/persist_v7.log`
* `data/session74/train_v47_dt.log`
* `data/session74/grade_v47_prefix.log`
* `data/session74/grade_v47_full.log`

**Documentation:**

* `SESSION_74_V47_DT_NULL_REPORT.md` (this file)
* `DECISIONS_LOG.md` — Decision 109 appended.
* `CURRENT_PHASE.md` — rewritten for S75.
* `STRATEGY_GUIDE.md` — Part 1 SKIPPED (no strategy of record changed);
  Parts 2-6 front-matter date refresh only.

**Production state at end of S74:** UNCHANGED from S73.

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix).
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h (no change).
* Project rule count: **18** (no change).
* DT-feature-engineering track exhausted at saturating regime; S75
  pivots to gradient boosting (Option B per S73→S74 CURRENT_PHASE.md).

## Appendix A — Decision 109 text (appended to DECISIONS_LOG.md)

See DECISIONS_LOG.md for the canonical text.

## Appendix B — Why the H2 hypothesis was worth testing despite the S71-stated risk

S71 §6 H3 (=now H2) carried the explicit warning: "could fall into
the 'derivable in 2 splits' trap; defer to S72 if v46_dt with H1
alone NULL-grades." We tested it in S74 anyway. Why?

1. **The risk was unverified.** S71 wrote it as a hypothesis-level
   concern, not a proven failure. The empirical test is the only way
   to know whether the saturating DT can actually derive the
   comparator in 2 splits, or whether it falls into a different
   failure mode (e.g., the comparator IS valuable but only in some
   region the DT can't reach).
2. **The diagnostic WG was real.** S71's $147.59 STRUCTURE-bucket
   leak is empirically present in v44's high_only residual. H1
   captured $24 of it; the remaining $123 has to live SOMEWHERE.
   H2 was the most direct candidate aimed at the drop-max-top
   decision.
3. **The cost was low.** S74 ran end-to-end in ~50 min wall (Phase 1
   ~10 min, Phase 2 ~10 min, Phase 3 ~3 min, Phase 4 ~30 min). At
   v44's saturating regime, the entire experiment was scriptable
   from existing templates. Cost-vs-knowledge-gained: well worth it.
4. **The result has methodological value.** Confirming the
   derivability trap empirically calibrates future feature design:
   prefer non-derivable axes; treat axis-comparison features as
   suspect at saturating regime. Without S74, the chapter would have
   ended with H1 PARTIAL POSITIVE and ambiguity about whether H2-style
   features could close the gap.

The NULL result is a clean methodological success: H2 is FALSIFIED
at the saturating DT regime, and the diagnostic-WG calibration for
single-feature retrains is now firmly at ~16% of S71's WG prediction
(H1) → ~0% (H2). The chapter closes. S75 opens a new chapter.
