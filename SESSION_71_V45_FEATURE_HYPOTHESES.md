# Session 71 — v46_dt feature hypotheses (high_only retrain)

*Generated 2026-05-12. Phase 1b deliverable per CURRENT_PHASE.md S71
direction. Reads `data/drill_v44_high_only_S71_per_hand.parquet` +
`data/drill_v44_high_only_S71_summary.json` produced by Phase 1a
(`drill_v44_high_only_S71.py`).*

> **NOTE ON NAMING:** v45_dt was already trained in S59 with 4
> ho_v5 features and NULL-graded (Decision 094, $0/1000h lift). The v45
> slot is preserved as historical record (model.npz + scripts retained,
> as append-only convention). The S71 retrain attempt ships under
> **v46_dt**, with new features in the
> **`high_only_aug_v6_features_gated.py`** lineage (next version after
> the v5 NULL).

## 1. Why retry the ML retrain after S59's NULL

S59 trained v45_dt with 4 ho_v5 features atop v44 and graded $0/1000h
lift. The S59 diagnosis: **DT saturation** at depth=36 ml=1 with 2.25M
leaves on 6M training rows. ho_v5 features were mathematically
*derivable* from v4 signals (linear combinations + bounded extensions);
the DT could already split correctly at non-saturated leaves.

S60–S64 then pivoted to per-max-rank rule catalog (Rules 14, 15, 16,
17–21), and S68–S70 closed the hybrid chain (v54+v55+v56). At end of
S70, the architectural-routing headroom is exhausted. v44's $1,081 ML
residual is amplified ~4× through the hybrid chain, so **any v44 lift
compounds via v54+v55+v56**. ML retrain is the only remaining big-lift
lever.

**S71's central question:** is the S59 NULL "feature redundancy at
saturation" the WHOLE story, or is there a portion of v44's high_only
residual that genuinely lacks structural signal — meaning new
*non-derivable* features CAN ship?

## 2. The new diagnostic — setting-rank partition

S58/S59 mined high_only at the **class-label** level (top_rank × bot_suit ×
mid_suited). That lens identified mismatch *kinds* but not mismatch
*severity*. The S71 drill (`drill_v44_high_only_S71.py`) partitions the
high_only residual by **v44's rank in oracle's sorted-EV list:**

| Bucket | Definition | Interpretation |
|---|---|---|
| **MATCH** | v44 picks rank 1 (== oracle) | no leak |
| **NOISE** | v44 picks rank 2–3 | small EV-gap; multiple near-optimal settings; new features cannot ship vs N=200 oracle noise |
| **MID** | v44 picks rank 4–9 | marginal feature potential |
| **STRUCTURE** | v44 picks rank ≥10 | v44 is far from the top-3 plateau; new features *could* re-route |

If STRUCTURE dominates, the S59 NULL was a *feature-design* failure;
new non-derivable features can ship. If NOISE dominates, the S59
hypothesis was right and ML retrain on high_only is futile.

## 3. Phase 1a headline findings — STRUCTURE is real and concentrated

**Grand partition of high_only residual** (1,226,940 canonical hands;
$381.39 WG total, matches S59 HO11 to 4 decimals):

| Bucket | hands | % | $ WG | % of WG |
|---|---:|---:|---:|---:|
| MATCH | 513,469 | 41.8% | $0.00 | 0.0% |
| NOISE (rank 2–3) | 308,313 | 25.1% | **$79.54** | 20.9% |
| MID (rank 4–9) | 267,161 | 21.8% | **$154.26** | 40.4% |
| STRUCTURE (rank ≥10) | 137,997 | 11.2% | **$147.59** | **38.7%** |

**Key finding: ~79% of high_only's WG residual is in MID + STRUCTURE
buckets — NOT pure noise.** The S59 NULL hypothesis is incomplete: a
non-trivial 38.7% of the residual ($147.59 WG) is structurally
addressable if new features can disambiguate the rank-10+ misses.

**EV-gap sharpness check (HO_S71_4):** STRUCTURE-bucket hands have
mean gap_2nd of 0.11–0.14 (translating to $1,100–1,400 regret per
hand). This is NOT a flat-plateau "many equally-good settings" zone;
the optima are sharp enough for a feature to ship lift.

**Per max_rank rollup** (sorted by STR $):

| max | hands | MATCH | NOISE $ | MID $ | STR $ | TOTAL $ | STR fraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| K | 330,330 | 39.3% | $18.58 | $39.75 | **$52.61** | $110.94 | **47.4%** |
| A | 660,660 | 44.9% | $50.30 | $88.70 | $43.51 | $182.51 | 23.8% |
| Q | 150,150 | 37.1% | $7.01 | $16.74 | **$31.49** | $55.24 | **57.0%** |
| J | 60,060 | 35.4% | $2.55 | $6.41 | **$14.47** | $23.43 | **61.8%** |
| T | 20,020 | 38.1% | $0.88 | $2.08 | $4.31 | $7.27 | 59.3% |
| 9 | 5,005 | 42.9% | $0.20 | $0.51 | $1.02 | $1.74 | 58.6% |
| 8 | 715 | 40.7% | $0.03 | $0.07 | $0.18 | $0.28 | 64.3% |

**K, Q, J, T, 9, 8 all have STRUCTURE ≥ MID** — they are STRUCTURALLY
mis-routed. Only A is dominated by NOISE+MID (its 44.9% match rate is
the highest; remaining leak is mostly rank-2-3 noise). **This refines
S58's "K/Q × DS_NO_JOINT is the deepest residual" with a stronger
claim: K/Q/J/T residuals are RANK-20+ structural misses, not flat-
plateau noise.**

**Top 8 STRUCTURE cells (83.6% of total STRUCTURE leak):**

| max | cell | n hands | STR n | STR $ WG | STR % of cell-WG |
|---|---|---:|---:|---:|---:|
| K | DS_NO_JOINT | 207,900 | 33,694 (16.2%) | **$36.63** | 48% |
| A | DS_NO_JOINT | 415,800 | 24,963 (6.0%) | $29.41 | 24% |
| Q | DS_NO_JOINT | 94,500 | 20,999 (22.2%) | $22.42 | 58% |
| J | DS_NO_JOINT | 37,800 | 9,631 (25.5%) | $10.23 | 63% |
| K | DS_NO_MAXTOP | 44,352 | 8,907 (20.1%) | $8.43 | 54% |
| A | DS_NO_MAXTOP | 88,704 | 7,264 (8.2%) | $6.87 | 29% |
| K | MS_ONLY | 29,568 | 5,358 (18.1%) | $4.76 | 47% |
| Q | DS_NO_MAXTOP | 20,160 | 4,756 (23.6%) | $4.68 | 52% |

## 4. The dominant STRUCTURE-bucket mismatch family — `SS_mu → SS_ms`

The HO_S71_3 mismatch tables reveal the top STRUCTURE mismatch in K,
Q, and J cells is the SAME shape: **v44 picks (top=max, SS bot, MU mid)
while oracle picks (top=max, SS bot, MS mid).** Same top rank, same
SS bot — v44 simply fails to suit the mid.

| Cell × bucket | Top mismatch | n hands | $ WG |
|---|---|---:|---:|
| K × DS_NO_JOINT × STR | `tK_SS_mu → tK_SS_ms` | 3,034 | **$3.40** |
| A × DS_NO_JOINT × STR | `tA_SS_mu → tA_SS_ms` | 4,418 | **$5.47** |
| Q × DS_NO_JOINT × STR | `tQ_SS_mu → tQ_SS_ms` | 1,026 | **$1.12** |
| J × DS_NO_JOINT × STR | `tJ_SS_mu → tJ_SS_ms` | 144 | $0.15 |

Total `SS_mu → SS_ms` STRUCTURE WG across these 4 cells: **~$10.14 WG**.
Combined with the MID-bucket sibling mismatches (which have the same
shape but smaller per-hand regret), the SS+ms family is the
single-largest addressable axis in v44's high_only residual.

**Why v44 misses these:** v44's 20 high_only-gated ho_v* features
enumerate (DS bot) configs at every shape (count, max/min top, max
mid_high, pair_high, 4-flush alt, non-max-top variants). **NONE
enumerate SS+ms configurations.** v44 sees individual settings'
bot_suit_profile (per-setting, 105 values) but has no hand-level
aggregate over SS+ms configs — which is precisely the information
needed to disambiguate "is the SS+ms route preferable to the SS+mu
route v44 currently picks?"

## 5. The S59 NULL postmortem (what to avoid)

Per S59 report:

1. **Mathematically redundant features fail at saturation.** ho_v5's
   `best_combined_q` = `max_top_rank + max_mid_high` (a sum of two v4
   signals). At depth=36 ml=1 saturation, the DT can already split on
   both axes; adding the sum provides no new partition.
2. **Booleans fail vs existing suit-distribution features.** ho_v3's
   v1 design was booleans → re-shipped as rank-valued in S57 (v3).
3. **Low feature importance + zero leaf growth = NULL signal.** v5's 4
   features ranked #66/#97/#106/#110 (max importance 0.07%) AND
   training added only +9 leaves over v44's 2.25M.

**S71 design constraints to avoid the NULL trap:**

* Feature must encode information NOT derivable from v44's 107
  features via linear/bounded operations.
* Feature must target STRUCTURE-bucket mismatches (rank ≥10), not
  NOISE-bucket (rank 2–3). The NOISE bucket has zero feature lift
  potential.
* Feature must describe a structural axis v4/v5 do not enumerate
  (Section 4 establishes SS+ms enumeration as a genuine gap).

## 6. Candidate feature hypotheses (5 proposals)

### H1 — SS+ms route quality (PRIMARY S71 IMPLEMENTATION — 2 features)

**Target:** the `SS_mu → SS_ms` STRUCTURE mismatch family ($10+ WG).

**Proposed features:**

```
ho_v6_topMax_SS_ms_n_configs_g       0..15
ho_v6_topMax_SS_ms_max_mid_high_g    0..14
```

For each hand: enumerate all (top=max_rank, SS bot, ms mid) settings
— there are up to C(6,2)=15 (mid_pair × leftover bot). Track:
* `n_configs`: count of configurations meeting all 3 conditions.
* `max_mid_high`: best higher-of-suited-mid rank across them.

Direct counterparts to **ho_v3**'s `topMax_DS_ms_n_configs_g` /
`topMax_DS_ms_max_mid_high_g`, but with **SS bot** in place of DS bot.

**Why non-derivable:**
* v44 has `bot_suit_profile` per-setting (105 values per hand), but no
  hand-level aggregate over (top=max ∧ bot=SS ∧ mid=suited). At
  depth=36 with 2.7 rows per leaf, no leaf can split on 105 distinct
  values to derive this count.
* v3's `topMax_DS_ms_*` features explicitly enumerate the DS variant
  — and v3 shipped +$79 (S57). The SS variant is the exact same shape
  on a parallel suit-profile axis that's GUARANTEED non-derivable
  (different suit-counting math entirely).
* No ho_v* feature mentions SS in its name. The DT has the
  per-setting suit_profile only — not the hand-level count.

**Expected STRUCTURE-bucket addressable population:** ~$10 WG SS_mu→
SS_ms across K/Q/J/A × DS_NO_JOINT. If even a quarter of MID+STRUCTURE
SS-family mismatches re-route, the v46_dt could ship $30–60 WG on
high_only — amplified ~4× through v54+v55+v56 hybrid chain.

### H2 — SS+ms route VARIETY signal (deferred to S72 if v46 NULL)

Adds:
```
ho_v6_topMax_SS_ms_max_top_suit_count_g   0..3
```
= count of cards in the top-suit when (top=max, SS bot, ms mid)
configuration uses max-rank's suit for the SS bot's singleton pair.
Captures whether the SS bot can be reinforced with max-rank as
support.

### H3 — Route trade-off (joint vs DS_NONJOINT comparator, deferred)

```
ho_v6_route_tradeoff_joint_minus_nonjoint_g   -13..+13
```
= signed comparison of best JOINT mid_high vs best DS_NONJOINT top.
v44 has both axes; the COMPARISON might compress them at saturation.
But could fall into the "derivable in 2 splits" trap; defer to S72
if v46_dt with H1 alone NULL-grades.

### H4 — MS_ONLY discriminator (deferred)

```
ho_v6_MS_ONLY_best_SS_ms_max_top_g    0..14
ho_v6_MS_ONLY_best_31_ms_max_top_g    0..14
```
Targets A × MS_ONLY × STRUCTURE ($4.39 WG) and parallel cells. Lower
priority than H1 (smaller WG target). Defer.

### H5 — Drop-max signal (deferred)

`tA_SS_mu → tK_DS_ms` and similar "abandon max on top" mismatches.
S58's identified target; S59's v5 features partially addressed; NULL.
Likely needs the H3 trade-off comparator to be useful. Defer.

## 7. Phase 2 — S71 implementation: H1 only

**Rationale:** H1 is the cleanest non-derivability story AND targets
the largest single mismatch family. Adding only 2 features keeps total
at 107+2 = 109, well under the depth=34 ml=2 re-test threshold
(CURRENT_PHASE.md S70 memo: re-test depth=34 ml=2 when feature count
grows ≥10 above last sweep — last sweep was v45 at 111 features so
v46 at 109 is BELOW that threshold; depth=32 ml=3 is the right
hyperparams).

**Files to produce:**
* `analysis/scripts/high_only_aug_v6_features_gated.py`
* `analysis/scripts/persist_high_only_aug_v6_gated.py`
* Smoke-test embedded in `__main__` block.

(`train_v46_dt.py`, `strategy_v46_dt.py`, `grade_v46_dt.py` queued for
S72.)

## 8. Phase 2 — smoke-test plan

The `__main__` block of `high_only_aug_v6_features_gated.py` runs 5
hand-crafted assertions covering:

1. **Non-high_only hand** (has a pair) → returns (0, 0).
2. **A-high with both topMax_DS_ms AND topMax_SS_ms** achievable →
   verifies SS+ms enumeration correctness alongside the existing DS
   axis.
3. **A-high with NO topMax_SS_ms** achievable (suit counts force DS
   or RB) → returns (0, 0) for v6.
4. **K-high with multiple topMax_SS_ms configs** at varying mid_high
   → verifies `max_mid_high` correctly maxes across configs.
5. **High-only hand where max-rank's suit packing forces a specific
   SS+ms shape** → exhaustive enumeration check.

## 9. Phase 2 — S72 retrain queue

Once H1 smoke-passes:

1. `persist_high_only_aug_v6_gated.py` →
   `data/feature_table_high_only_aug_v6_gated.parquet` (~6 MB; 2
   features × 6M canonical hands × int8 + canonical_id u32 = ~12 MB
   pre-compression).
2. `train_v46_dt.py` at **depth=32 ml=3** (project default per
   CURRENT_PHASE.md). 107 + 2 = 109 features.
3. Compare v46_dt leaf count + feature importance vs v44 + v45
   baselines. **Tripwire prediction:**
   * v6 features rank inside top-50 importance (vs v5's #66/#97/...).
   * Leaf count grows ≥10K above v44's 2.25M (vs v5's +9).
   * Both signals together predict ship; either alone is ambiguous.
4. Grade v46_dt on prefix (500K) then full (6M).
5. **Hybrid pre-grader prediction:** if v46 reduces high_only WG by
   $X, the v56 chain compounds it to ~$X × 4 full-grid lift (since
   v44 is invoked inside v54/v55/v56 across 40% of canonical grid).

**Predicted ship range:** $30–80 WG full-grid (depending on how much
SS_mu→SS_ms STRUCTURE residual is closed, and whether the new SS-axis
feature helps adjacent MID-bucket mismatches as well).

## 10. Acceptance criteria check (CURRENT_PHASE.md S71)

| Criterion | Status |
|---|---|
| `drill_v44_high_only_S71.py` + diagnostic sweep complete | ✓ Phase 1a |
| `SESSION_71_V45_FEATURE_HYPOTHESES.md` with 4–8 hypotheses | ✓ This file (5 hypotheses) |
| 1–2 features implemented + smoke-tested | Phase 2 deliverable |
| S72 direction (full retrain) recommendation | ✓ Section 9 |

## 11. Open questions for S72 (if v46_dt grades)

1. **If v46_dt SHIPS** (>$20 WG full-grid): the saturation hypothesis
   was false at the SS axis. Queue H2+H3+H4+H5 for v47_dt at same
   hyperparams. Expected v47_dt ship: small incremental.
2. **If v46_dt NULL-grades** ($0/1000h): the saturation hypothesis is
   re-confirmed at depth=36 ml=1 — but this run is at depth=32 ml=3,
   a different regime. Try v46b_dt at depth=36 ml=1 with the same H1
   features to isolate the hyperparams effect from the feature effect.
   If still NULL, pivot to gradient boosting or grid label N=1000
   re-evaluation.
3. **If v46_dt ships small** (<$20 WG): the SS-axis adds new info
   but the saturation ceiling absorbs most of it. Consider depth=30
   ml=5 for v47_dt to deliberately under-fit and force generalization.

---

*"Speed is not necessary — clarity and perfection is."* — the
setting-rank diagnostic establishes a clean partition (NOISE/MID/STR);
the SS+ms axis is the largest non-derivable signal gap in v44's
high_only feature taxonomy; H1's 2 features encode it in the same
shape as v3's shipped DS-axis pair. Whether v46_dt ships or NULL-
grades, the experiment is well-posed and the next direction is clear.
